import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

/**
 * RDS MySQL スタック
 *
 * ローン情報スクレイピングシステムのデータベース基盤
 * - db.t3.micro（無料枠対応）
 * - PyMySQL接続
 * - 自動バックアップとストレージ暗号化
 */
export class AuroraStack extends cdk.Stack {
  public readonly instance: rds.DatabaseInstance;
  public readonly secret: secretsmanager.ISecret;
  public readonly vpc: ec2.IVpc;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC作成（パブリックサブネットのみでコスト削減）
    this.vpc = new ec2.Vpc(this, 'LoanpediaVpc', {
      maxAzs: 2,
      natGateways: 0, // NAT不要
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: 'public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
      ],
      enableDnsHostnames: true,
      enableDnsSupport: true,
    });

    // RDS MySQL インスタンス（無料枠対応）
    this.instance = new rds.DatabaseInstance(this, 'MySQLInstance', {
      engine: rds.DatabaseInstanceEngine.mysql({
        version: rds.MysqlEngineVersion.VER_8_0_39,
      }),
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.MICRO, // 無料枠対応
      ),
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PUBLIC,
      },
      // パブリックアクセス有効化（Lambda VPC不要でコスト削減）
      publiclyAccessible: true,

      // 認証情報（Secrets Managerで自動管理）
      credentials: rds.Credentials.fromGeneratedSecret('admin', {
        secretName: 'loanpedia/rds/credentials',
      }),

      // データベース名
      databaseName: 'loanpedia',

      // ストレージ設定（無料枠：20GB）
      allocatedStorage: 20,
      maxAllocatedStorage: 100, // 自動スケーリング上限

      // バックアップ設定
      backupRetention: cdk.Duration.days(7),
      preferredBackupWindow: '03:00-04:00', // JST 12:00-13:00

      // メンテナンスウィンドウ
      preferredMaintenanceWindow: 'mon:04:00-mon:05:00', // JST 月曜13:00-14:00

      // ストレージ暗号化
      storageEncrypted: true,

      // 削除保護（本番環境では true にすることを推奨）
      deletionProtection: false,

      // リソース削除時の動作
      removalPolicy: cdk.RemovalPolicy.SNAPSHOT,

      // マルチAZ無効化（コスト削減）
      multiAz: false,
    });

    this.secret = this.instance.secret!;

    // セキュリティグループ設定：Lambda関数からのアクセスを許可
    this.instance.connections.allowDefaultPortFromAnyIpv4('Allow from Lambda');

    // CloudFormation Outputs（SAMで参照）
    new cdk.CfnOutput(this, 'DbInstanceEndpoint', {
      value: this.instance.dbInstanceEndpointAddress,
      description: 'RDS MySQL endpoint address',
      exportName: 'LoanpediaDbEndpoint',
    });

    new cdk.CfnOutput(this, 'DbInstancePort', {
      value: this.instance.dbInstanceEndpointPort,
      description: 'RDS MySQL port',
      exportName: 'LoanpediaDbPort',
    });

    new cdk.CfnOutput(this, 'DbSecretArn', {
      value: this.secret.secretArn,
      description: 'Database credentials secret ARN',
      exportName: 'LoanpediaDbSecretArn',
    });

    new cdk.CfnOutput(this, 'DbName', {
      value: 'loanpedia',
      description: 'Database name',
      exportName: 'LoanpediaDbName',
    });

    new cdk.CfnOutput(this, 'VpcId', {
      value: this.vpc.vpcId,
      description: 'VPC ID',
      exportName: 'LoanpediaVpcId',
    });

    // タグ付け
    cdk.Tags.of(this).add('Project', 'Loanpedia');
    cdk.Tags.of(this).add('Environment', 'Production');
    cdk.Tags.of(this).add('ManagedBy', 'CDK');
  }
}
