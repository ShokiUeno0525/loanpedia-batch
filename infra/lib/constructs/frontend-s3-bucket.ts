import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

/**
 * FrontendBucket Constructプロパティ
 */
export interface FrontendBucketProps {
  /**
   * バケット名のプレフィックス
   * @default 'loanpedia-frontend'
   */
  readonly bucketPrefix?: string;
}

/**
 * フロントエンド用S3バケットのConstruct
 *
 * @remarks
 * このConstructは以下のリソースを作成します：
 * - フロントエンド静的コンテンツ用のプライベートS3バケット
 * - CloudFrontログ用のS3バケット
 *
 * セキュリティ設定：
 * - すべてのパブリックアクセスをブロック
 * - S3マネージド暗号化を有効化
 * - バージョニング有効化（本番環境のみ推奨）
 */
export class FrontendBucket extends Construct {
  /**
   * フロントエンドコンテンツ用S3バケット
   */
  public readonly frontendBucket: s3.Bucket;

  /**
   * CloudFrontログ用S3バケット
   */
  public readonly logBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props?: FrontendBucketProps) {
    super(scope, id);

    const bucketPrefix = props?.bucketPrefix || 'loanpedia-frontend';

    // T016: CloudFrontログ用S3バケットの作成
    // ログバケットは先に作成する必要がある（フロントエンドバケットのログ出力先として使用可能）
    this.logBucket = new s3.Bucket(this, 'LogBucket', {
      bucketName: 'loanpedia-cloudfront-logs',
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      // ログファイルは30日後に自動削除
      lifecycleRules: [
        {
          id: 'DeleteOldLogs',
          enabled: true,
          expiration: cdk.Duration.days(30),
        },
      ],
      // CloudFrontがログを書き込むために必要
      objectOwnership: s3.ObjectOwnership.OBJECT_WRITER,
      // 本番環境ではRETAINを推奨（ログの保持）
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // T015: フロントエンドコンテンツ用S3バケットの作成
    this.frontendBucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: bucketPrefix,
      // すべてのパブリックアクセスをブロック（CloudFront経由のみアクセス可能）
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      // S3マネージド暗号化を有効化
      encryption: s3.BucketEncryption.S3_MANAGED,
      // バージョニング有効化（誤削除からの復旧が可能）
      versioned: true,
      // 本番環境ではRETAINを推奨（誤削除防止）
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      // CloudFrontのアクセスログを有効化
      serverAccessLogsBucket: this.logBucket,
      serverAccessLogsPrefix: 's3-access/',
    });

    // CloudFrontからのアクセスを許可するバケットポリシーを追加
    // OAC経由でのみアクセス可能にする
    this.frontendBucket.addToResourcePolicy(
      new cdk.aws_iam.PolicyStatement({
        sid: 'AllowCloudFrontServicePrincipal',
        effect: cdk.aws_iam.Effect.ALLOW,
        principals: [new cdk.aws_iam.ServicePrincipal('cloudfront.amazonaws.com')],
        actions: ['s3:GetObject'],
        resources: [`${this.frontendBucket.bucketArn}/*`],
        conditions: {
          StringEquals: {
            'AWS:SourceAccount': cdk.Stack.of(this).account,
          },
        },
      })
    );

    // タグ付け
    cdk.Tags.of(this).add('Component', 'Frontend');
    cdk.Tags.of(this).add('Purpose', 'StaticContent');
  }
}
