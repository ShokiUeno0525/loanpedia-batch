import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { BackendStack } from '../lib/stacks/backend-stack';
import { VpcNetworkStack } from '../lib/stacks/vpc-network-stack';

describe('BackendStack', () => {
  let app: cdk.App;
  let vpcStack: VpcNetworkStack;
  let backendStack: BackendStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();

    // VPC Stackを作成（Backend Stackが依存）
    vpcStack = new VpcNetworkStack(app, 'TestVpcStack', {
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });

    // テスト用ACM証明書とRoute53ホストゾーン作成
    const certificate = new acm.Certificate(vpcStack, 'TestCert', {
      domainName: 'api.loanpedia.jp',
      validation: acm.CertificateValidation.fromDns(),
    });

    const hostedZone = new route53.PublicHostedZone(vpcStack, 'TestZone', {
      zoneName: 'loanpedia.jp',
    });

    // Backend Stackを作成
    backendStack = new BackendStack(app, 'TestBackendStack', {
      vpc: vpcStack.vpcConstruct.vpc,
      publicSubnetA: vpcStack.subnetConstruct.publicSubnet,
      publicSubnetC: vpcStack.publicSubnetC,
      privateSubnet: vpcStack.subnetConstruct.privateSubnet,
      isolatedSubnet: vpcStack.subnetConstruct.isolatedSubnet,
      isolatedSubnetC: vpcStack.subnetConstructC.isolatedSubnet,
      certificate,
      hostedZone,
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });

    template = Template.fromStack(backendStack);
  });

  describe('ECRリポジトリ', () => {
    test('2個のECRリポジトリが作成される', () => {
      template.resourceCountIs('AWS::ECR::Repository', 2);
    });

    test('loanpedia-apiリポジトリが作成される', () => {
      template.hasResourceProperties('AWS::ECR::Repository', {
        RepositoryName: 'loanpedia-api',
        ImageScanningConfiguration: {
          ScanOnPush: true,
        },
      });
    });

    test('loanpedia-migrationリポジトリが作成される', () => {
      template.hasResourceProperties('AWS::ECR::Repository', {
        RepositoryName: 'loanpedia-migration',
        ImageScanningConfiguration: {
          ScanOnPush: true,
        },
      });
    });
  });

  describe('RDS', () => {
    test('RDSインスタンスが1個作成される', () => {
      template.resourceCountIs('AWS::RDS::DBInstance', 1);
    });

    test('RDSインスタンスがMySQL 8.0で作成される', () => {
      template.hasResourceProperties('AWS::RDS::DBInstance', {
        Engine: 'mysql',
        EngineVersion: '8.0',
        DBInstanceClass: 'db.t3.micro',
        AllocatedStorage: '20',
        StorageType: 'gp3',
      });
    });
  });

  describe('Cognito', () => {
    test('Cognito User Poolが1個作成される', () => {
      template.resourceCountIs('AWS::Cognito::UserPool', 1);
    });

    test('Cognito User Pool Clientが1個作成される', () => {
      template.resourceCountIs('AWS::Cognito::UserPoolClient', 1);
    });
  });

  describe('CloudWatch Logs', () => {
    test('2個のロググループが作成される', () => {
      template.resourceCountIs('AWS::Logs::LogGroup', 2);
    });

    test('/ecs/loanpedia-apiロググループが作成される', () => {
      template.hasResourceProperties('AWS::Logs::LogGroup', {
        LogGroupName: '/ecs/loanpedia-api',
        RetentionInDays: 7,
      });
    });

    test('/ecs/loanpedia-migrationロググループが作成される', () => {
      template.hasResourceProperties('AWS::Logs::LogGroup', {
        LogGroupName: '/ecs/loanpedia-migration',
        RetentionInDays: 7,
      });
    });
  });

  describe('Secrets Manager', () => {
    test('2個のSecretが作成される（RDS、Cognito）', () => {
      template.resourceCountIs('AWS::SecretsManager::Secret', 2);
    });
  });

  describe('ALB', () => {
    test('ALBが1個作成される', () => {
      template.resourceCountIs('AWS::ElasticLoadBalancingV2::LoadBalancer', 1);
    });

    test('ターゲットグループが1個作成される', () => {
      template.resourceCountIs('AWS::ElasticLoadBalancingV2::TargetGroup', 1);
    });
  });

  describe('ECS', () => {
    test('ECSクラスターが1個作成される', () => {
      template.resourceCountIs('AWS::ECS::Cluster', 1);
    });

    test('タスク定義が2個作成される', () => {
      template.resourceCountIs('AWS::ECS::TaskDefinition', 2);
    });

    test('ECSサービスが1個作成される', () => {
      template.resourceCountIs('AWS::ECS::Service', 1);
    });
  });

  describe('スナップショットテスト', () => {
    test('Backend Stackのスナップショットが一致する', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });
  });
});
