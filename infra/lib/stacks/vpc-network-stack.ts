import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Tags } from 'aws-cdk-lib';
import { VpcConstruct } from '../constructs/vpc-construct';
import { SubnetConstruct } from '../constructs/subnet-construct';
import { InternetGatewayConstruct } from '../constructs/internet-gateway-construct';
import { NatGatewayConstruct } from '../constructs/nat-gateway-construct';

/**
 * VPCネットワークスタック
 *
 * シングルAZ構成のVPCネットワーク基盤を構築します。
 * - VPC: 10.16.0.0/16
 * - パブリックサブネット: 10.16.0.0/20
 * - プライベートサブネット: 10.16.32.0/20
 * - アイソレートサブネット: 10.16.64.0/20
 */
export class VpcNetworkStack extends cdk.Stack {
  /**
   * 作成されたVPCコンストラクト
   */
  public readonly vpcConstruct: VpcConstruct;

  /**
   * 作成されたサブネットコンストラクト
   */
  public readonly subnetConstruct: SubnetConstruct;

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
  }
}
