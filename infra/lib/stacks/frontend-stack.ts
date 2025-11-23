import * as cdk from 'aws-cdk-lib';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as route53Targets from 'aws-cdk-lib/aws-route53-targets';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import { FrontendDistribution } from '../constructs/frontend-distribution';
import { WafCloudFront } from '../constructs/waf-cloudfront';
import { BasicAuthFunction } from '../constructs/basic-auth-function';

/**
 * FrontendStackのProps
 */
export interface FrontendStackProps extends cdk.StackProps {
  /**
   * フロントエンドコンテンツ用S3バケット（S3Stackから渡される）
   */
  readonly frontendBucket: s3.IBucket;

  /**
   * CloudFrontログ用S3バケット（S3Stackから渡される）
   */
  readonly logBucket: s3.IBucket;

  /**
   * ALBドメイン名（オプション）
   * /api/*ビヘイビアのオリジンとして使用
   */
  readonly albDomainName?: string;
}

/**
 * CloudFrontフロントエンド配信基盤スタック（us-east-1）
 *
 * @remarks
 * このスタックは以下のリソースを作成します：
 * - CloudFrontディストリビューション（OAC設定、HTTPS、カスタムドメイン）
 * - WAF WebACL（AWS Managed Rules）
 * - Route53 Aレコード（loanpedia.jp → CloudFront）
 *
 * デプロイリージョン: us-east-1（CloudFront/WAF要件）
 *
 * 依存関係：
 * - Route53ホストゾーン（既存）
 * - ACM証明書（既存、us-east-1リージョン）
 * - S3Stack（ap-northeast-1）からS3バケットをクロスリージョン参照（crossRegionReferencesを使用）
 *
 * ユーザーストーリー：
 * - US1: 基本的なフロントエンドコンテンツ配信
 * - US2: セキュアなコンテンツ配信（OAC、プライベートS3）
 * - US3: WAFによる保護
 * - US4: アクセスログの記録と監視
 */
export class FrontendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: FrontendStackProps) {
    super(scope, id, props);

    // T004: 既存のRoute53ホストゾーンを参照
    const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
      domainName: 'loanpedia.jp',
    });

    // T004: 既存のACM証明書を参照（us-east-1リージョンで作成済み）
    const certificate = acm.Certificate.fromCertificateArn(
      this,
      'Certificate',
      cdk.Fn.importValue('LoanpediaCertificateArn')
    );

    // S3バケットをクロスリージョン参照（propsから取得）
    // crossRegionReferences: trueにより、CDKが自動的にSSM ParameterまたはCustom Resourceを使用して参照を実現
    // 循環参照を避けるため、バケット名のみを使用して再度参照を作成
    const frontendBucket = s3.Bucket.fromBucketName(
      this,
      'FrontendBucketRef',
      props.frontendBucket.bucketName
    );
    const logBucket = s3.Bucket.fromBucketName(this, 'LogBucketRef', props.logBucket.bucketName);

    // T046: WAF WebACLを作成（User Story 3）
    // 注: WAFはus-east-1リージョンで作成する必要があるため、
    // このスタックもus-east-1リージョンにデプロイする必要がある
    const wafConstruct = new WafCloudFront(this, 'WafCloudFront');

    // Basic認証Functionを作成（開発環境用）
    const basicAuthFunction = new BasicAuthFunction(this, 'BasicAuthFunction').function;

    // CloudFrontディストリビューションを作成
    const distributionConstruct = new FrontendDistribution(this, 'FrontendDistribution', {
      frontendBucket: frontendBucket,
      logBucket: logBucket,
      certificate: certificate,
      domainName: 'loanpedia.jp',
      webAclArn: wafConstruct.webAcl.attrArn,
      basicAuthFunction: basicAuthFunction,
      albDomainName: props.albDomainName,
    });

    // T025: Route53 Aレコードを作成（loanpedia.jp → CloudFront）
    new route53.ARecord(this, 'AliasRecord', {
      zone: hostedZone,
      recordName: 'loanpedia.jp',
      target: route53.RecordTarget.fromAlias(
        new route53Targets.CloudFrontTarget(distributionConstruct.distribution)
      ),
      comment: 'Loanpediaフロントエンド用CloudFrontディストリビューション',
    });

    // T028: CloudFormation Outputs（contracts/cloudformation-outputs.yamlに従う）

    // CloudFrontディストリビューション関連
    new cdk.CfnOutput(this, 'DistributionId', {
      value: distributionConstruct.distribution.distributionId,
      description: 'CloudFrontディストリビューションID',
      exportName: 'LoanpediaCloudFrontDistributionId',
    });

    new cdk.CfnOutput(this, 'DistributionDomainName', {
      value: distributionConstruct.distribution.distributionDomainName,
      description: 'CloudFrontのデフォルトドメイン名',
      exportName: 'LoanpediaCloudFrontDomainName',
    });

    new cdk.CfnOutput(this, 'DistributionArn', {
      value: `arn:aws:cloudfront::${this.account}:distribution/${distributionConstruct.distribution.distributionId}`,
      description: 'CloudFrontディストリビューションARN',
      exportName: 'LoanpediaCloudFrontDistributionArn',
    });

    // T049: WAF関連のOutputs（User Story 3）
    new cdk.CfnOutput(this, 'WebAclId', {
      value: wafConstruct.webAcl.attrId,
      description: 'WAF WebACL ID',
      exportName: 'LoanpediaCloudFrontWebAclId',
    });

    new cdk.CfnOutput(this, 'WebAclArn', {
      value: wafConstruct.webAcl.attrArn,
      description: 'WAF WebACL ARN',
      exportName: 'LoanpediaCloudFrontWebAclArn',
    });

    // DNS関連（情報提供用）
    new cdk.CfnOutput(this, 'CustomDomainName', {
      value: 'loanpedia.jp',
      description: 'CloudFrontに設定されたカスタムドメイン名',
      exportName: 'LoanpediaCloudFrontCustomDomain',
    });

    new cdk.CfnOutput(this, 'Route53RecordName', {
      value: 'loanpedia.jp',
      description: '作成されたRoute53 Aレコード名',
      exportName: 'LoanpediaCloudFrontRoute53RecordName',
    });

    // T048: タグ付け
    cdk.Tags.of(this).add('Project', 'Loanpedia');
    cdk.Tags.of(this).add('Environment', 'Production');
    cdk.Tags.of(this).add('ManagedBy', 'CDK');
  }
}
