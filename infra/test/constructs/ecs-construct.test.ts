import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { EcsConstruct } from '../../lib/constructs/ecs-construct';

describe('EcsConstruct', () => {
  let app: cdk.App;
  let stack: cdk.Stack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new cdk.Stack(app, 'TestStack', {
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });

    // テスト用リソース作成
    const vpc = new ec2.Vpc(stack, 'TestVpc', { maxAzs: 1 });
    const privateSubnet = vpc.privateSubnets[0];
    const securityGroup = new ec2.SecurityGroup(stack, 'TestSg', { vpc });
    const alb = new elbv2.ApplicationLoadBalancer(stack, 'TestAlb', { vpc, internetFacing: true });
    const targetGroup = new elbv2.ApplicationTargetGroup(stack, 'TestTg', {
      vpc,
      port: 80,
      targetType: elbv2.TargetType.IP,
    });

    const rdsSecret = new secretsmanager.Secret(stack, 'RdsSecret', {
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'admin' }),
        generateStringKey: 'password',
      },
    });

    const cognitoSecret = new secretsmanager.Secret(stack, 'CognitoSecret');

    const apiLogGroup = new logs.LogGroup(stack, 'ApiLogGroup');
    const migrationLogGroup = new logs.LogGroup(stack, 'MigrationLogGroup');

    const ecrApiRepository = new ecr.Repository(stack, 'ApiRepo');
    const ecrMigrationRepository = new ecr.Repository(stack, 'MigrationRepo');

    // ECS Construct作成
    new EcsConstruct(stack, 'Ecs', {
      vpc,
      privateSubnet,
      securityGroup,
      targetGroup,
      rdsSecret,
      cognitoSecret,
      apiLogGroup,
      migrationLogGroup,
      ecrApiRepository,
      ecrMigrationRepository,
    });

    template = Template.fromStack(stack);
  });

  describe('ECSクラスター', () => {
    test('ECSクラスターが1個作成される', () => {
      template.resourceCountIs('AWS::ECS::Cluster', 1);
    });
  });

  describe('タスク定義', () => {
    test('2個のタスク定義が作成される（API、マイグレーション）', () => {
      template.resourceCountIs('AWS::ECS::TaskDefinition', 2);
    });
  });

  describe('ECSサービス', () => {
    test('1個のECSサービスが作成される（API）', () => {
      template.resourceCountIs('AWS::ECS::Service', 1);
    });
  });

  describe('スナップショットテスト', () => {
    test('ECS Constructのスナップショットが一致する', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });
  });
});
