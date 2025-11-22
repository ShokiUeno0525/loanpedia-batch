import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { FrontendBucket } from '../constructs/frontend-s3-bucket';

/**
 * S3バケットスタック（東京リージョン）
 *
 * @remarks
 * このスタックは以下のリソースを作成します：
 * - フロントエンド用S3バケット（プライベート）
 * - CloudFrontログ用S3バケット
 *
 * デプロイリージョン: ap-northeast-1（東京）
 *
 * 依存関係：
 * - なし（独立したスタック）
 *
 * 使用するスタック：
 * - FrontendStack（us-east-1）がこのスタックのS3バケットをクロスリージョン参照（crossRegionReferencesを使用）
 */
export class S3Stack extends cdk.Stack {
  /**
   * フロントエンドコンテンツ用S3バケット
   */
  public readonly frontendBucket: cdk.aws_s3.IBucket;

  /**
   * CloudFrontログ用S3バケット
   */
  public readonly logBucket: cdk.aws_s3.IBucket;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // フロントエンド用S3バケットとログバケットを作成
    const frontendBucketConstruct = new FrontendBucket(this, 'FrontendBucket');

    this.frontendBucket = frontendBucketConstruct.frontendBucket;
    this.logBucket = frontendBucketConstruct.logBucket;

    // CloudFormation Outputs（参照用、exportNameなし）
    // crossRegionReferences: trueを使用するため、exportNameは不要
    new cdk.CfnOutput(this, 'FrontendBucketName', {
      value: this.frontendBucket.bucketName,
      description: 'フロントエンド用S3バケット名',
    });

    new cdk.CfnOutput(this, 'FrontendBucketArn', {
      value: this.frontendBucket.bucketArn,
      description: 'フロントエンド用S3バケットARN',
    });

    new cdk.CfnOutput(this, 'FrontendBucketDomainName', {
      value: this.frontendBucket.bucketRegionalDomainName,
      description: 'フロントエンド用S3バケットのドメイン名',
    });

    new cdk.CfnOutput(this, 'LogBucketName', {
      value: this.logBucket.bucketName,
      description: 'CloudFrontログ用S3バケット名',
    });

    new cdk.CfnOutput(this, 'LogBucketArn', {
      value: this.logBucket.bucketArn,
      description: 'CloudFrontログ用S3バケットARN',
    });

    // タグ付け
    cdk.Tags.of(this).add('Project', 'Loanpedia');
    cdk.Tags.of(this).add('Environment', 'Production');
    cdk.Tags.of(this).add('ManagedBy', 'CDK');
    cdk.Tags.of(this).add('Region', 'ap-northeast-1');
  }
}
