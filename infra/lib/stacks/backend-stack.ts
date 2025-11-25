import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { Construct } from 'constructs';
import { SecurityGroupsConstruct } from '../constructs/security-groups-construct';
import { RdsConstruct } from '../constructs/rds-construct';
import { CognitoConstruct } from '../constructs/cognito-construct';
import { AlbConstruct } from '../constructs/alb-construct';
import { EcsConstruct } from '../constructs/ecs-construct';

export interface BackendStackProps extends cdk.StackProps {
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
   * プライベートサブネット（AZ-a）
   */
  readonly privateSubnet: ec2.ISubnet;

  /**
   * アイソレートサブネット（AZ-a）
   */
  readonly isolatedSubnet: ec2.ISubnet;

  /**
   * アイソレートサブネット（AZ-c）
   */
  readonly isolatedSubnetC: ec2.ISubnet;

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
 * バックエンドスタック
 *
 * ローン情報集約システムのバックエンドインフラを構築します。
 *
 * 作成されるリソース:
 * - ECRリポジトリ（loanpedia-api、loanpedia-migration）
 * - RDS MySQL 8.0
 * - Cognito User Pool
 * - CloudWatch Logs（ECSタスク用）
 * - セキュリティグループ（ALB、ECS、RDS）
 */
export class BackendStack extends cdk.Stack {
  /**
   * ECR API リポジトリ
   */
  public readonly ecrApiRepository: ecr.Repository;

  /**
   * ECR マイグレーションリポジトリ
   */
  public readonly ecrMigrationRepository: ecr.Repository;

  /**
   * API用CloudWatch Logsロググループ
   */
  public readonly apiLogGroup: logs.LogGroup;

  /**
   * マイグレーション用CloudWatch Logsロググループ
   */
  public readonly migrationLogGroup: logs.LogGroup;

  /**
   * セキュリティグループコンストラクト
   */
  public readonly securityGroups: SecurityGroupsConstruct;

  /**
   * RDSコンストラクト
   */
  public readonly rds: RdsConstruct;

  /**
   * Cognitoコンストラクト
   */
  public readonly cognito: CognitoConstruct;

  /**
   * ALBコンストラクト
   */
  public readonly alb: AlbConstruct;

  /**
   * ECSコンストラクト
   */
  public readonly ecs: EcsConstruct;

  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);

    const {
      vpc,
      publicSubnetA,
      publicSubnetC,
      privateSubnet,
      isolatedSubnet,
      isolatedSubnetC,
      certificate,
      hostedZone,
    } = props;

    // ECRリポジトリ: loanpedia-api
    this.ecrApiRepository = new ecr.Repository(this, 'ApiRepository', {
      repositoryName: 'loanpedia-api',
      imageScanOnPush: true, // イメージスキャン有効化
      encryption: ecr.RepositoryEncryption.AES_256, // AES-256暗号化
      removalPolicy: cdk.RemovalPolicy.RETAIN, // リポジトリ保持
      lifecycleRules: [
        {
          description: '未タグイメージを30日後に削除',
          maxImageAge: cdk.Duration.days(30),
          tagStatus: ecr.TagStatus.UNTAGGED,
        },
      ],
    });

    // ECRリポジトリ: loanpedia-migration
    this.ecrMigrationRepository = new ecr.Repository(this, 'MigrationRepository', {
      repositoryName: 'loanpedia-migration',
      imageScanOnPush: true,
      encryption: ecr.RepositoryEncryption.AES_256,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [
        {
          description: '未タグイメージを30日後に削除',
          maxImageAge: cdk.Duration.days(30),
          tagStatus: ecr.TagStatus.UNTAGGED,
        },
      ],
    });

    // CloudWatch Logs: /ecs/loanpedia-api
    this.apiLogGroup = new logs.LogGroup(this, 'ApiLogGroup', {
      logGroupName: '/ecs/loanpedia-api',
      retention: logs.RetentionDays.ONE_WEEK, // 7日間保持
      removalPolicy: cdk.RemovalPolicy.DESTROY, // 開発環境のため削除
    });

    // CloudWatch Logs: /ecs/loanpedia-migration
    this.migrationLogGroup = new logs.LogGroup(this, 'MigrationLogGroup', {
      logGroupName: '/ecs/loanpedia-migration',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // セキュリティグループ作成
    this.securityGroups = new SecurityGroupsConstruct(this, 'SecurityGroups', {
      vpc,
    });

    // RDS MySQL作成
    this.rds = new RdsConstruct(this, 'Rds', {
      vpc,
      securityGroup: this.securityGroups.rdsSg,
      isolatedSubnets: [isolatedSubnet, isolatedSubnetC],
    });

    // Cognito User Pool作成
    this.cognito = new CognitoConstruct(this, 'Cognito');

    // ALB作成
    this.alb = new AlbConstruct(this, 'Alb', {
      vpc,
      publicSubnetA,
      publicSubnetC,
      securityGroup: this.securityGroups.albSg,
      certificate,
      hostedZone,
    });

    // ECS作成
    this.ecs = new EcsConstruct(this, 'Ecs', {
      vpc,
      privateSubnet,
      securityGroup: this.securityGroups.ecsSg,
      targetGroup: this.alb.targetGroup,
      rdsSecret: this.rds.secret,
      cognitoSecret: this.cognito.clientSecret,
      apiLogGroup: this.apiLogGroup,
      migrationLogGroup: this.migrationLogGroup,
      ecrApiRepository: this.ecrApiRepository,
      ecrMigrationRepository: this.ecrMigrationRepository,
    });

    // CloudFormation Outputs
    new cdk.CfnOutput(this, 'EcrApiRepositoryUri', {
      value: this.ecrApiRepository.repositoryUri,
      description: 'ECR APIリポジトリURI',
      exportName: 'LoanpediaEcrApiRepositoryUri',
    });

    new cdk.CfnOutput(this, 'EcrMigrationRepositoryUri', {
      value: this.ecrMigrationRepository.repositoryUri,
      description: 'ECRマイグレーションリポジトリURI',
      exportName: 'LoanpediaEcrMigrationRepositoryUri',
    });
  }
}
