import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { SubnetConstruct } from '../../lib/constructs/subnet-construct';

describe('SubnetConstruct', () => {
  test('3つのサブネット（パブリック、プライベート、アイソレート）が正しいCIDRブロックで作成される', () => {
    const app = new cdk.App();
    const stack = new cdk.Stack(app, 'TestStack', {
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });

    const vpc = new ec2.Vpc(stack, 'TestVpc', {
      ipAddresses: ec2.IpAddresses.cidr('10.16.0.0/16'),
      maxAzs: 1,
      subnetConfiguration: [],
    });

    new SubnetConstruct(stack, 'TestSubnetConstruct', {
      vpc,
      availabilityZone: 'ap-northeast-1a',
    });

    const template = Template.fromStack(stack);

    // サブネット総数
    template.resourceCountIs('AWS::EC2::Subnet', 3);

    // パブリックサブネット
    template.hasResourceProperties('AWS::EC2::Subnet', {
      CidrBlock: '10.16.0.0/20',
      MapPublicIpOnLaunch: true,
      AvailabilityZone: 'ap-northeast-1a',
    });

    // プライベートサブネット
    template.hasResourceProperties('AWS::EC2::Subnet', {
      CidrBlock: '10.16.32.0/20',
      AvailabilityZone: 'ap-northeast-1a',
    });

    // アイソレートサブネット
    template.hasResourceProperties('AWS::EC2::Subnet', {
      CidrBlock: '10.16.64.0/20',
      AvailabilityZone: 'ap-northeast-1a',
    });
  });
});
