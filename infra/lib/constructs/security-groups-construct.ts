import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export interface SecurityGroupsConstructProps {
  /**
   * セキュリティグループを作成するVPC
   */
  readonly vpc: ec2.IVpc;
}

/**
 * セキュリティグループコンストラクト
 *
 * バックエンドインフラ用のセキュリティグループ（ALB、ECS、RDS）を作成します。
 *
 * セキュリティグループ間の通信:
 * - CloudFront → ALB (443)
 * - ALB → ECS (80)
 * - ECS → RDS (3306)
 * - ECS → 外部API (443、NAT Gateway経由)
 */
export class SecurityGroupsConstruct extends Construct {
  /**
   * ALB用セキュリティグループ
   *
   * インバウンド: CloudFrontマネージドプレフィックスリスト → 443
   * アウトバウンド: ECS SG → 80
   */
  public readonly albSg: ec2.SecurityGroup;

  /**
   * ECS用セキュリティグループ
   *
   * インバウンド: ALB SG → 80
   * アウトバウンド: RDS SG → 3306、0.0.0.0/0 → 443
   */
  public readonly ecsSg: ec2.SecurityGroup;

  /**
   * RDS用セキュリティグループ
   *
   * インバウンド: ECS SG → 3306
   * アウトバウンド: なし
   */
  public readonly rdsSg: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: SecurityGroupsConstructProps) {
    super(scope, id);

    const { vpc } = props;

    // ALB用セキュリティグループ
    this.albSg = new ec2.SecurityGroup(this, 'AlbSecurityGroup', {
      vpc,
      description: 'ALB用セキュリティグループ（CloudFrontからのHTTPSアクセスのみ許可）',
      allowAllOutbound: false,
    });

    // ECS用セキュリティグループ
    this.ecsSg = new ec2.SecurityGroup(this, 'EcsSecurityGroup', {
      vpc,
      description: 'ECS Fargate用セキュリティグループ（ALBからのHTTPアクセス、RDS・外部API接続）',
      allowAllOutbound: false,
    });

    // RDS用セキュリティグループ
    this.rdsSg = new ec2.SecurityGroup(this, 'RdsSecurityGroup', {
      vpc,
      description: 'RDS MySQL用セキュリティグループ（ECSからのMySQLアクセスのみ許可）',
      allowAllOutbound: false,
    });

    // ALB SG: CloudFrontマネージドプレフィックスリストからのHTTPSアクセスを許可
    this.albSg.addIngressRule(
      ec2.Peer.prefixList('pl-58a04531'), // CloudFront Managed Prefix List (Global)
      ec2.Port.tcp(443),
      'CloudFrontからのHTTPSアクセスを許可'
    );

    // ALB SG: ECS SGへのHTTPアウトバウンドを許可
    this.albSg.addEgressRule(this.ecsSg, ec2.Port.tcp(80), 'ECSへのHTTPアクセスを許可');

    // ECS SG: ALB SGからのHTTPインバウンドを許可
    this.ecsSg.addIngressRule(this.albSg, ec2.Port.tcp(80), 'ALBからのHTTPアクセスを許可');

    // ECS SG: RDS SGへのMySQLアウトバウンドを許可
    this.ecsSg.addEgressRule(this.rdsSg, ec2.Port.tcp(3306), 'RDSへのMySQLアクセスを許可');

    // ECS SG: 外部API（Cognito、BedRock等）へのHTTPSアウトバウンドを許可（NAT Gateway経由）
    this.ecsSg.addEgressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      '外部API（Cognito、BedRock等）へのHTTPSアクセスを許可'
    );

    // RDS SG: ECS SGからのMySQLインバウンドを許可
    this.rdsSg.addIngressRule(this.ecsSg, ec2.Port.tcp(3306), 'ECSからのMySQLアクセスを許可');
  }
}
