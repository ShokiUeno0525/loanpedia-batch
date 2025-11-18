import { Template, Match } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { InternetGatewayConstruct } from '../../lib/constructs/internet-gateway-construct';

describe('InternetGatewayConstruct', () => {
  test('Internet GatewayがVPCにアタッチされ、パブリックサブネットへのルートが作成される', () => {
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

    new InternetGatewayConstruct(stack, 'TestInternetGatewayConstruct', {
      vpc,
      publicSubnet,
    });

    const template = Template.fromStack(stack);

    // Internet Gateway作成
    template.resourceCountIs('AWS::EC2::InternetGateway', 1);

    // VPCアタッチメント
    template.resourceCountIs('AWS::EC2::VPCGatewayAttachment', 1);
    template.hasResourceProperties('AWS::EC2::VPCGatewayAttachment', {
      VpcId: {
        Ref: Match.stringLikeRegexp('TestVpc'),
      },
      InternetGatewayId: {
        Ref: Match.stringLikeRegexp('InternetGateway'),
      },
    });

    // ルート作成
    template.hasResourceProperties('AWS::EC2::Route', {
      DestinationCidrBlock: '0.0.0.0/0',
      GatewayId: {
        Ref: Match.stringLikeRegexp('InternetGateway'),
      },
    });
  });
});
