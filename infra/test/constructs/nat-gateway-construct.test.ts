import { Template, Match } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { NatGatewayConstruct } from '../../lib/constructs/nat-gateway-construct';

describe('NatGatewayConstruct', () => {
  test('NAT GatewayとElastic IPが作成され、プライベートサブネットへのルートが設定される', () => {
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

    const publicSubnet = new ec2.PublicSubnet(stack, 'TestPublicSubnet', {
      vpcId: vpc.vpcId,
      cidrBlock: '10.16.0.0/20',
      availabilityZone: 'ap-northeast-1a',
      mapPublicIpOnLaunch: true,
    });

    const privateSubnet = new ec2.PrivateSubnet(stack, 'TestPrivateSubnet', {
      vpcId: vpc.vpcId,
      cidrBlock: '10.16.32.0/20',
      availabilityZone: 'ap-northeast-1a',
    });

    new NatGatewayConstruct(stack, 'TestNatGatewayConstruct', {
      publicSubnet,
      privateSubnet,
    });

    const template = Template.fromStack(stack);

    // Elastic IP作成
    template.resourceCountIs('AWS::EC2::EIP', 1);
    template.hasResourceProperties('AWS::EC2::EIP', {
      Domain: 'vpc',
    });

    // NAT Gateway作成
    template.resourceCountIs('AWS::EC2::NatGateway', 1);
    template.hasResourceProperties('AWS::EC2::NatGateway', {
      SubnetId: {
        Ref: Match.stringLikeRegexp('TestPublicSubnet'),
      },
      AllocationId: {
        'Fn::GetAtt': [Match.stringLikeRegexp('NatGatewayEIP'), 'AllocationId'],
      },
    });

    // ルート作成
    template.hasResourceProperties('AWS::EC2::Route', {
      DestinationCidrBlock: '0.0.0.0/0',
      NatGatewayId: {
        Ref: Match.stringLikeRegexp('NatGateway'),
      },
    });
  });
});
