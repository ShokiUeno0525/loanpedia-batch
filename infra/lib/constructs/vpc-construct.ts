import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { Tags } from 'aws-cdk-lib';

export interface VpcConstructProps {
  /**
   * VPCのCIDRブロック
   * @default '10.16.0.0/16'
   */
  readonly cidrBlock?: string;

  /**
   * 配置するアベイラビリティゾーンの最大数
   * @default 1 (シングルAZ)
   */
  readonly maxAzs?: number;
}

/**
 * VPCコンストラクト
 *
 * Loanpediaプロジェクト用のVPCを作成します。
 * シングルAZ構成で、CIDR 10.16.0.0/16のVPCを提供します。
 */
export class VpcConstruct extends Construct {
  /**
   * 作成されたVPC
   */
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props: VpcConstructProps = {}) {
    super(scope, id);

    const cidrBlock = props.cidrBlock ?? '10.16.0.0/16';
    const maxAzs = props.maxAzs ?? 1;

    // VPCを作成（サブネットは手動で作成するため、subnetConfiguration は空）
    this.vpc = new ec2.Vpc(this, 'LoanpediaVpc', {
      ipAddresses: ec2.IpAddresses.cidr(cidrBlock),
      maxAzs: maxAzs,
      natGateways: 0, // NAT Gateway は後続フェーズで手動作成
      subnetConfiguration: [], // サブネットは手動で作成
      enableDnsHostnames: true,
      enableDnsSupport: true,
    });

    // VPCに Name タグを追加
    Tags.of(this.vpc).add('Name', 'Loanpedia-Dev-VPC-Main');
  }
}
