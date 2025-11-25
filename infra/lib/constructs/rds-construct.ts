import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

export interface RdsConstructProps {
  /**
   * RDSインスタンスを配置するVPC
   */
  readonly vpc: ec2.IVpc;

  /**
   * RDS用セキュリティグループ
   */
  readonly securityGroup: ec2.ISecurityGroup;

  /**
   * アイソレートサブネット（複数AZ）
   * RDSサブネットグループには最低2つの異なるAZのサブネットが必要
   */
  readonly isolatedSubnets: ec2.ISubnet[];
}

/**
 * RDS MySQLコンストラクト
 *
 * Laravel API用のMySQL 8.0データベースインスタンスを作成します。
 *
 * 構成:
 * - エンジン: MySQL 8.0
 * - インスタンスタイプ: db.t3.micro
 * - ストレージ: gp3 20GB
 * - シングルAZ (ap-northeast-1a)
 * - 文字セット: utf8mb4
 * - 照合順序: utf8mb4_unicode_ci
 * - バックアップ保持期間: 7日間
 * - 認証情報: Secrets Manager自動生成
 */
export class RdsConstruct extends Construct {
  /**
   * 作成されたRDSインスタンス
   */
  public readonly instance: rds.DatabaseInstance;

  /**
   * RDS認証情報を格納するSecrets Manager
   */
  public readonly secret: secretsmanager.ISecret;

  constructor(scope: Construct, id: string, props: RdsConstructProps) {
    super(scope, id);

    const { vpc, securityGroup, isolatedSubnets } = props;

    // RDSパラメータグループ（utf8mb4設定）
    const parameterGroup = new rds.ParameterGroup(this, 'ParameterGroup', {
      engine: rds.DatabaseInstanceEngine.mysql({
        version: rds.MysqlEngineVersion.VER_8_0,
      }),
      parameters: {
        character_set_server: 'utf8mb4',
        collation_server: 'utf8mb4_unicode_ci',
        character_set_client: 'utf8mb4',
        character_set_connection: 'utf8mb4',
        character_set_database: 'utf8mb4',
        character_set_results: 'utf8mb4',
      },
      description: 'Loanpedia MySQL 8.0 parameter group with utf8mb4 settings',
    });

    // RDSサブネットグループ（アイソレートサブネット、複数AZ）
    const subnetGroup = new rds.SubnetGroup(this, 'SubnetGroup', {
      vpc,
      description: 'Loanpedia RDS subnet group (multi-AZ requirement)',
      vpcSubnets: {
        subnets: isolatedSubnets,
      },
    });

    // RDS MySQLインスタンス
    this.instance = new rds.DatabaseInstance(this, 'Instance', {
      engine: rds.DatabaseInstanceEngine.mysql({
        version: rds.MysqlEngineVersion.VER_8_0,
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
      vpc,
      subnetGroup,
      securityGroups: [securityGroup],
      parameterGroup,
      databaseName: 'loanpedia',
      storageType: rds.StorageType.GP3,
      allocatedStorage: 20,
      maxAllocatedStorage: 100, // 自動スケーリング上限
      multiAz: false, // シングルAZ（開発環境、コスト削減）
      deletionProtection: false, // 開発環境のため無効化
      backupRetention: cdk.Duration.days(7),
      preferredBackupWindow: '17:00-18:00', // JST 02:00-03:00
      preferredMaintenanceWindow: 'sun:18:00-sun:19:00', // JST 日曜03:00-04:00
      removalPolicy: cdk.RemovalPolicy.SNAPSHOT, // スタック削除時はスナップショット作成
    });

    // Secrets ManagerからRDS認証情報を取得
    if (!this.instance.secret) {
      throw new Error('RDS instance secret is not available');
    }
    this.secret = this.instance.secret;

    // CloudFormation Output: RDSエンドポイント
    new cdk.CfnOutput(scope, 'RdsEndpoint', {
      value: this.instance.dbInstanceEndpointAddress,
      description: 'RDS MySQLエンドポイント',
      exportName: 'LoanpediaRdsEndpoint',
    });

    // CloudFormation Output: RDSポート
    new cdk.CfnOutput(scope, 'RdsPort', {
      value: this.instance.dbInstanceEndpointPort,
      description: 'RDS MySQLポート',
      exportName: 'LoanpediaRdsPort',
    });

    // CloudFormation Output: Secrets Manager ARN
    new cdk.CfnOutput(scope, 'RdsSecretArn', {
      value: this.secret.secretArn,
      description: 'RDS認証情報Secrets Manager ARN',
      exportName: 'LoanpediaRdsSecretArn',
    });
  }
}
