import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Tags } from 'aws-cdk-lib';

export interface InternetGatewayConstructProps {
  /**
   * Internet GatewayをアタッチするVPC
   */
  readonly vpc: ec2.IVpc;

  /**
   * Internet Gatewayへのルーティングを設定するパブリックサブネット
   */
  readonly publicSubnet: ec2.PublicSubnet;
}

/**
 * Internet Gatewayコンストラクト
 *
 * VPCにInternet Gatewayを作成し、パブリックサブネットからのルーティングを設定します。
 */
export class InternetGatewayConstruct extends Construct {
  /**
   * 作成されたInternet Gateway
   */
  public readonly internetGateway: ec2.CfnInternetGateway;

  constructor(scope: Construct, id: string, props: InternetGatewayConstructProps) {
    super(scope, id);

    const { vpc, publicSubnet } = props;

    // Internet Gatewayを作成
    this.internetGateway = new ec2.CfnInternetGateway(this, 'InternetGateway', {});

    Tags.of(this.internetGateway).add('Name', 'Loanpedia-Dev-IGW');

    // Internet GatewayをVPCにアタッチ
    new ec2.CfnVPCGatewayAttachment(this, 'VpcGatewayAttachment', {
      vpcId: vpc.vpcId,
      internetGatewayId: this.internetGateway.ref,
    });

    // パブリックサブネットのルートテーブルにInternet Gatewayへのルートを追加
    new ec2.CfnRoute(this, 'PublicSubnetRoute', {
      routeTableId: publicSubnet.routeTable.routeTableId,
      destinationCidrBlock: '0.0.0.0/0',
      gatewayId: this.internetGateway.ref,
    });
  }
}
