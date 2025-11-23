import { Match, Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import { VpcNetworkStack } from '../lib/stacks/vpc-network-stack';

describe('VpcNetworkStack', () => {
  let app: cdk.App;
  let stack: VpcNetworkStack;
  let template: Template;

  beforeEach(() => {
    app = new cdk.App();
    stack = new VpcNetworkStack(app, 'TestVpcNetworkStack', {
      env: {
        account: '123456789012',
        region: 'ap-northeast-1',
      },
    });
    template = Template.fromStack(stack);
  });

  describe('VPC', () => {
    test('VPCが10.16.0.0/16のCIDRブロックで作成される', () => {
      template.resourceCountIs('AWS::EC2::VPC', 1);
      template.hasResourceProperties('AWS::EC2::VPC', {
        CidrBlock: '10.16.0.0/16',
        EnableDnsHostnames: true,
        EnableDnsSupport: true,
      });
    });
  });

  describe('サブネット', () => {
    test('4つのサブネットが作成される（パブリック×2、プライベート、アイソレート）', () => {
      // パブリックサブネット×2 + プライベート + アイソレート = 4つ
      template.resourceCountIs('AWS::EC2::Subnet', 4);
    });

    test('AZ-a用パブリックサブネット (10.16.0.0/20) が作成される', () => {
      template.hasResourceProperties('AWS::EC2::Subnet', {
        CidrBlock: '10.16.0.0/20',
        MapPublicIpOnLaunch: true,
      });
    });

    test('AZ-c用パブリックサブネット (10.16.16.0/20) が作成される', () => {
      template.hasResourceProperties('AWS::EC2::Subnet', {
        CidrBlock: '10.16.16.0/20',
        MapPublicIpOnLaunch: true,
      });
    });

    test('プライベートサブネット (10.16.32.0/20) が作成される', () => {
      template.hasResourceProperties('AWS::EC2::Subnet', {
        CidrBlock: '10.16.32.0/20',
      });
    });

    test('アイソレートサブネット (10.16.64.0/20) が作成される', () => {
      template.hasResourceProperties('AWS::EC2::Subnet', {
        CidrBlock: '10.16.64.0/20',
      });
    });
  });

  describe('Internet Gateway', () => {
    test('Internet Gatewayが作成され、パブリックサブネットからのルートが設定される', () => {
      template.resourceCountIs('AWS::EC2::InternetGateway', 1);

      template.hasResourceProperties('AWS::EC2::Route', {
        DestinationCidrBlock: '0.0.0.0/0',
        GatewayId: Match.objectLike({
          Ref: Match.stringLikeRegexp('InternetGateway'),
        }),
      });
    });
  });

  describe('NAT Gateway', () => {
    test('NAT GatewayとElastic IPが作成され、プライベートサブネットからのルートが設定される', () => {
      template.resourceCountIs('AWS::EC2::NatGateway', 1);
      template.resourceCountIs('AWS::EC2::EIP', 1);

      template.hasResourceProperties('AWS::EC2::Route', {
        DestinationCidrBlock: '0.0.0.0/0',
        NatGatewayId: Match.objectLike({
          Ref: Match.stringLikeRegexp('NatGateway'),
        }),
      });
    });
  });

  describe('ルートテーブル', () => {
    test('各サブネット用のルートテーブルが作成される', () => {
      // 4つのサブネット用ルートテーブル
      template.resourceCountIs('AWS::EC2::RouteTable', 4);
      template.resourceCountIs('AWS::EC2::SubnetRouteTableAssociation', 4);
    });
  });

  describe('CloudFormation Outputs', () => {
    test('PublicSubnetAIdとPublicSubnetCIdが出力される', () => {
      template.hasOutput('PublicSubnetAId', {
        Description: 'AZ-a用パブリックサブネットID',
        Export: {
          Name: 'LoanpediaPublicSubnetAId',
        },
      });

      template.hasOutput('PublicSubnetCId', {
        Description: 'AZ-c用パブリックサブネットID (ALB 2AZ要件用)',
        Export: {
          Name: 'LoanpediaPublicSubnetCId',
        },
      });
    });
  });

  describe('スナップショットテスト', () => {
    test('VPC Network Stackのスナップショットが一致する', () => {
      expect(template.toJSON()).toMatchSnapshot();
    });
  });
});
