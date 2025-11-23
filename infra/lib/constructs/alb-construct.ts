import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as route53Targets from 'aws-cdk-lib/aws-route53-targets';
import { Construct } from 'constructs';

export interface AlbConstructProps {
  /**
   * VPC
   */
  readonly vpc: ec2.IVpc;

  /**
   * パブリックサブネット（AZ-a）
   */
  readonly publicSubnetA: ec2.ISubnet;

  /**
   * パブリックサブネット（AZ-c）
   */
  readonly publicSubnetC: ec2.ISubnet;

  /**
   * ALB用セキュリティグループ
   */
  readonly securityGroup: ec2.ISecurityGroup;

  /**
   * ACM証明書
   */
  readonly certificate: acm.ICertificate;

  /**
   * Route53ホストゾーン
   */
  readonly hostedZone: route53.IHostedZone;
}

/**
 * ALBコンストラクト
 *
 * Application Load Balancerを2AZ（パブリックサブネット）に配置し、
 * HTTPS通信（CloudFront→ALB→ECS）を実現します。
 *
 * 構成:
 * - スキーム: internet-facing
 * - 配置: 2AZ（パブリックサブネット: ap-northeast-1a、1c）
 * - HTTPリスナー: 80 → 443リダイレクト
 * - HTTPSリスナー: 443 → ターゲットグループ
 * - ターゲットグループ: タイプIP、プロトコルHTTP、ポート80
 * - ヘルスチェック: パス /health、間隔30秒、タイムアウト5秒、しきい値2回
 */
export class AlbConstruct extends Construct {
  /**
   * 作成されたApplication Load Balancer
   */
  public readonly alb: elbv2.ApplicationLoadBalancer;

  /**
   * 作成されたターゲットグループ
   */
  public readonly targetGroup: elbv2.ApplicationTargetGroup;

  constructor(scope: Construct, id: string, props: AlbConstructProps) {
    super(scope, id);

    const { vpc, publicSubnetA, publicSubnetC, securityGroup, certificate, hostedZone } = props;

    // Application Load Balancer作成
    this.alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
      vpc,
      vpcSubnets: {
        subnets: [publicSubnetA, publicSubnetC],
      },
      internetFacing: true,
      securityGroup,
      deletionProtection: false, // 開発環境のため無効化
    });

    // ターゲットグループ作成
    this.targetGroup = new elbv2.ApplicationTargetGroup(this, 'TargetGroup', {
      vpc,
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targetType: elbv2.TargetType.IP, // Fargate用
      healthCheck: {
        path: '/health',
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 2,
        healthyHttpCodes: '200',
      },
      deregistrationDelay: cdk.Duration.seconds(30),
    });

    // HTTPリスナー: 80 → 443リダイレクト
    this.alb.addListener('HttpListener', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      defaultAction: elbv2.ListenerAction.redirect({
        protocol: 'HTTPS',
        port: '443',
        permanent: true,
      }),
    });

    // HTTPSリスナー: 443 → ターゲットグループ
    this.alb.addListener('HttpsListener', {
      port: 443,
      protocol: elbv2.ApplicationProtocol.HTTPS,
      certificates: [certificate],
      defaultAction: elbv2.ListenerAction.forward([this.targetGroup]),
    });

    // Route53 Aレコード作成（api.loanpedia.jp → ALB）
    new route53.ARecord(this, 'AliasRecord', {
      zone: hostedZone,
      recordName: 'api',
      target: route53.RecordTarget.fromAlias(new route53Targets.LoadBalancerTarget(this.alb)),
    });

    // CloudFormation Output: ALB DNS名
    new cdk.CfnOutput(scope, 'AlbDnsName', {
      value: this.alb.loadBalancerDnsName,
      description: 'ALB DNS名',
      exportName: 'LoanpediaAlbDnsName',
    });

    // CloudFormation Output: ALB ARN
    new cdk.CfnOutput(scope, 'AlbArn', {
      value: this.alb.loadBalancerArn,
      description: 'ALB ARN',
      exportName: 'LoanpediaAlbArn',
    });

    // CloudFormation Output: ターゲットグループARN
    new cdk.CfnOutput(scope, 'TargetGroupArn', {
      value: this.targetGroup.targetGroupArn,
      description: 'ターゲットグループARN',
      exportName: 'LoanpediaTargetGroupArn',
    });
  }
}
