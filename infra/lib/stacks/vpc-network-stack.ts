import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Tags } from 'aws-cdk-lib';
import { VpcConstruct } from '../constructs/vpc-construct';
import { SubnetConstruct } from '../constructs/subnet-construct';
import { InternetGatewayConstruct } from '../constructs/internet-gateway-construct';
import { NatGatewayConstruct } from '../constructs/nat-gateway-construct';

/**
 * VPCネットワークスタック
 *
 * 2AZ構成のVPCネットワーク基盤を構築します。
 * - VPC: 10.16.0.0/16
 * - パブリックサブネット: 10.16.0.0/20 (AZ-a)、10.16.16.0/20 (AZ-c)
 * - プライベートサブネット: 10.16.32.0/20 (AZ-a)
 * - アイソレートサブネット: 10.16.64.0/20 (AZ-a)
 *
 * 注: AZ-c用のパブリックサブネットはALB 2AZ要件を満たすためのダミー。
 *     プライベート・アイソレートサブネットはAZ-aのみに配置。
 */
export class VpcNetworkStack extends cdk.Stack {
  /**
   * 作成されたVPCコンストラクト
   */
  public readonly vpcConstruct: VpcConstruct;

  /**
   * 作成されたサブネットコンストラクト (AZ-a)
   */
  public readonly subnetConstruct: SubnetConstruct;

  /**
   * 作成されたサブネットコンストラクト (AZ-c)
   */
  public readonly subnetConstructC: SubnetConstruct;

  /**
   * AZ-c用のパブリックサブネット (ALB 2AZ要件のためのダミー)
   */
  public readonly publicSubnetC: ec2.PublicSubnet;

  /**
   * 作成されたInternet Gatewayコンストラクト
   */
  public readonly internetGatewayConstruct: InternetGatewayConstruct;

  /**
   * 作成されたNAT Gatewayコンストラクト
   */
  public readonly natGatewayConstruct: NatGatewayConstruct;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // スタックレベルで統一タグを適用
    Tags.of(this).add('Project', 'Loanpedia');
    Tags.of(this).add('Environment', 'Development');
    Tags.of(this).add('ManagedBy', 'CDK');
    Tags.of(this).add('Feature', '003-infra-vpc-network-setup');
    Tags.of(this).add('CostCenter', 'Loanpedia-Infrastructure');

    // VPCを作成 (CIDR: 10.16.0.0/16)
    this.vpcConstruct = new VpcConstruct(this, 'VpcConstruct', {
      cidrBlock: '10.16.0.0/16',
      maxAzs: 1, // シングルAZ構成
    });

    // サブネットを作成 (パブリック、プライベート、アイソレート)
    // 利用可能なAZの最初のものを取得
    const availabilityZone = cdk.Stack.of(this).availabilityZones[0];

    this.subnetConstruct = new SubnetConstruct(this, 'SubnetConstruct', {
      vpc: this.vpcConstruct.vpc,
      availabilityZone: availabilityZone,
    });

    // Internet Gatewayを作成してパブリックサブネットにルーティングを設定
    this.internetGatewayConstruct = new InternetGatewayConstruct(this, 'InternetGatewayConstruct', {
      vpc: this.vpcConstruct.vpc,
      publicSubnet: this.subnetConstruct.publicSubnet,
    });

    // NAT Gatewayを作成してプライベートサブネットにルーティングを設定
    this.natGatewayConstruct = new NatGatewayConstruct(this, 'NatGatewayConstruct', {
      publicSubnet: this.subnetConstruct.publicSubnet,
      privateSubnet: this.subnetConstruct.privateSubnet,
    });

    // AZ-c用のサブネットを作成 (RDS/ALB 2AZ要件のため)
    const availabilityZoneC = cdk.Stack.of(this).availabilityZones[2]; // ap-northeast-1c
    this.subnetConstructC = new SubnetConstruct(this, 'SubnetConstructC', {
      vpc: this.vpcConstruct.vpc,
      availabilityZone: availabilityZoneC,
      publicCidr: '10.16.16.0/20',
      privateCidr: '10.16.48.0/20',
      isolatedCidr: '10.16.80.0/20',
    });

    // ALB用にAZ-cのパブリックサブネットを参照（後方互換性のため）
    this.publicSubnetC = this.subnetConstructC.publicSubnet;

    // AZ-c用パブリックサブネットのルートテーブルにInternet Gatewayへのルートを追加
    // (ALB 2AZ要件のため)
    new ec2.CfnRoute(this, 'PublicSubnetCRoute', {
      routeTableId: this.publicSubnetC.routeTable.routeTableId,
      destinationCidrBlock: '0.0.0.0/0',
      gatewayId: this.internetGatewayConstruct.internetGateway.ref,
    });

    // CloudFormation Outputs
    new cdk.CfnOutput(this, 'VpcId', {
      value: this.vpcConstruct.vpc.vpcId,
      description: 'VPC ID',
      exportName: 'LoanpediaVpcId',
    });

    new cdk.CfnOutput(this, 'PublicSubnetAId', {
      value: this.subnetConstruct.publicSubnet.subnetId,
      description: 'AZ-a用パブリックサブネットID',
      exportName: 'LoanpediaPublicSubnetAId',
    });

    new cdk.CfnOutput(this, 'PublicSubnetCId', {
      value: this.publicSubnetC.subnetId,
      description: 'AZ-c用パブリックサブネットID (ALB 2AZ要件用)',
      exportName: 'LoanpediaPublicSubnetCId',
    });

    new cdk.CfnOutput(this, 'PrivateSubnetId', {
      value: this.subnetConstruct.privateSubnet.subnetId,
      description: 'プライベートサブネットID (AZ-a)',
      exportName: 'LoanpediaPrivateSubnetId',
    });

    new cdk.CfnOutput(this, 'IsolatedSubnetId', {
      value: this.subnetConstruct.isolatedSubnet.subnetId,
      description: 'アイソレートサブネットID (AZ-a)',
      exportName: 'LoanpediaIsolatedSubnetId',
    });

    new cdk.CfnOutput(this, 'IsolatedSubnetCId', {
      value: this.subnetConstructC.isolatedSubnet.subnetId,
      description: 'アイソレートサブネットID (AZ-c, RDS 2AZ要件用)',
      exportName: 'LoanpediaIsolatedSubnetCId',
    });
  }
}
