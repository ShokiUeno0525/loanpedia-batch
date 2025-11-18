import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Tags } from 'aws-cdk-lib';

export interface NatGatewayConstructProps {
  /**
   * NAT Gatewayを配置するパブリックサブネット
   */
  readonly publicSubnet: ec2.PublicSubnet;

  /**
   * NAT Gatewayへのルーティングを設定するプライベートサブネット
   */
  readonly privateSubnet: ec2.PrivateSubnet;
}

/**
 * NAT Gatewayコンストラクト
 *
 * パブリックサブネットにNAT Gatewayを作成し、
 * プライベートサブネットからのインターネット向け通信をルーティングします。
 */
export class NatGatewayConstruct extends Construct {
  /**
   * NAT Gatewayに割り当てられたElastic IP
   */
  public readonly eip: ec2.CfnEIP;

  /**
   * 作成されたNAT Gateway
   */
  public readonly natGateway: ec2.CfnNatGateway;

  constructor(scope: Construct, id: string, props: NatGatewayConstructProps) {
    super(scope, id);

    const { publicSubnet, privateSubnet } = props;

    // Elastic IPを作成
    this.eip = new ec2.CfnEIP(this, 'NatGatewayEIP', {
      domain: 'vpc',
    });

    Tags.of(this.eip).add('Name', 'Loanpedia-Dev-NAT-EIP');

    // NAT Gatewayを作成
    this.natGateway = new ec2.CfnNatGateway(this, 'NatGateway', {
      subnetId: publicSubnet.subnetId,
      allocationId: this.eip.attrAllocationId,
    });

    Tags.of(this.natGateway).add('Name', 'Loanpedia-Dev-NAT-Gateway');

    // プライベートサブネットのルートテーブルにNAT Gatewayへのルートを追加
    new ec2.CfnRoute(this, 'PrivateSubnetRoute', {
      routeTableId: privateSubnet.routeTable.routeTableId,
      destinationCidrBlock: '0.0.0.0/0',
      natGatewayId: this.natGateway.ref,
    });
  }
}
