import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import { VpcConstruct } from '../../lib/constructs/vpc-construct';

describe('VpcConstruct', () => {
  test('デフォルト設定でVPCが作成される', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack');

    new VpcConstruct(stack, 'TestVpcConstruct');

    const template = Template.fromStack(stack);

    template.resourceCountIs('AWS::EC2::VPC', 1);
    template.hasResourceProperties('AWS::EC2::VPC', {
      CidrBlock: '10.16.0.0/16',
      EnableDnsHostnames: true,
      EnableDnsSupport: true,
    });
    template.resourceCountIs('AWS::EC2::NatGateway', 0);
  });

  test('カスタムCIDRブロックでVPCが作成される', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack');

    new VpcConstruct(stack, 'TestVpcConstruct', {
      cidrBlock: '10.0.0.0/16',
    });

    const template = Template.fromStack(stack);
    template.hasResourceProperties('AWS::EC2::VPC', {
      CidrBlock: '10.0.0.0/16',
    });
  });
});
