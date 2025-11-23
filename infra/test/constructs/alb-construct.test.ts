import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { AlbConstruct } from '../../lib/constructs/alb-construct';

describe('AlbConstruct', () => {
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

    // テスト用VPCとサブネット作成
    const vpc = new ec2.Vpc(stack, 'TestVpc', {
      maxAzs: 2,
    });

    const publicSubnetA = vpc.publicSubnets[0];
    const publicSubnetC = vpc.publicSubnets[1];

    // テスト用セキュリティグループ作成
    const securityGroup = new ec2.SecurityGroup(stack, 'TestSg', {
      vpc,
    });

    // テスト用ACM証明書作成
    const certificate = new acm.Certificate(stack, 'TestCert', {
      domainName: 'api.loanpedia.jp',
      validation: acm.CertificateValidation.fromDns(),
    });

    // テスト用ホストゾーン作成
    const hostedZone = new route53.PublicHostedZone(stack, 'TestZone', {
      zoneName: 'loanpedia.jp',
    });

    // ALB Construct作成
    new AlbConstruct(stack, 'Alb', {
      vpc,
      publicSubnetA,
      publicSubnetC,
      securityGroup,
      certificate,
      hostedZone,
    });

    template = Template.fromStack(stack);
  });

  describe('ALB', () => {
    test('ALBが1個作成される', () => {
      template.resourceCountIs('AWS::ElasticLoadBalancingV2::LoadBalancer', 1);
    });

    test('ALBがinternet-facingスキームで作成される', () => {
      template.hasResourceProperties('AWS::ElasticLoadBalancingV2::LoadBalancer', {
        Scheme: 'internet-facing',
        Type: 'application',
      });
    });
  });

  describe('ターゲットグループ', () => {
    test('ターゲットグループが1個作成される', () => {
      template.resourceCountIs('AWS::ElasticLoadBalancingV2::TargetGroup', 1);
    });

    test('ターゲットグループがIP型、HTTP、ポート80で作成される', () => {
      template.hasResourceProperties('AWS::ElasticLoadBalancingV2::TargetGroup', {
        TargetType: 'ip',
        Protocol: 'HTTP',
        Port: 80,
      });
    });
  });

  describe('リスナー', () => {
    test('2個のリスナーが作成される（HTTP、HTTPS）', () => {
      template.resourceCountIs('AWS::ElasticLoadBalancingV2::Listener', 2);
    });
  });

  describe('スナップショットテスト', () => {
    test('ALB Constructのスナップショットが一致する', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });
  });
});
