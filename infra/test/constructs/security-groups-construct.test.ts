import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { SecurityGroupsConstruct } from '../../lib/constructs/security-groups-construct';

describe('SecurityGroupsConstruct', () => {
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

    // テスト用VPCを作成
    const vpc = new ec2.Vpc(stack, 'TestVpc', {
      cidr: '10.16.0.0/16',
      maxAzs: 1,
    });

    // Security Groups Constructを作成
    new SecurityGroupsConstruct(stack, 'SecurityGroups', {
      vpc,
    });

    template = Template.fromStack(stack);
  });

  describe('セキュリティグループ', () => {
    test('3個のセキュリティグループが作成される（ALB、ECS、RDS）', () => {
      // ALB + ECS + RDS = 3個（VPCデフォルトSGは含まれない）
      template.resourceCountIs('AWS::EC2::SecurityGroup', 3);
    });
  });

  describe('スナップショットテスト', () => {
    test('Security Groups Constructのスナップショットが一致する', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });
  });
});
