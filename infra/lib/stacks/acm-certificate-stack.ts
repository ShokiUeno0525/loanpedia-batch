import * as cdk from 'aws-cdk-lib';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { Construct } from 'constructs';

/**
 * ACM証明書スタック
 *
 * loanpedia.jpドメインのSSL/TLS証明書を発行する
 * - CloudFront用にus-east-1リージョンで作成
 * - DNS検証方式を使用
 * - 証明書の自動更新に対応
 */
export class AcmCertificateStack extends cdk.Stack {
  public readonly certificate: acm.Certificate;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // T006: Route53ホストゾーンの参照
    // 既存のloanpedia.jpホストゾーンを検索
    const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
      domainName: 'loanpedia.jp',
    });

    // T007: ACM証明書リソースの定義
    // CloudFront用の証明書をus-east-1リージョンで作成
    // DNS検証方式を使用して自動的に検証レコードを作成
    this.certificate = new acm.Certificate(this, 'Certificate', {
      domainName: 'loanpedia.jp',
      validation: acm.CertificateValidation.fromDns(hostedZone),
    });

    // T008: 証明書ARNのCloudFormation Output設定
    // 後続のタスク（CloudFront設定等）で使用するために出力
    new cdk.CfnOutput(this, 'CertificateArn', {
      value: this.certificate.certificateArn,
      description: 'ACM Certificate ARN for loanpedia.jp',
      exportName: 'LoanpediaCertificateArn',
    });

    new cdk.CfnOutput(this, 'DomainName', {
      value: 'loanpedia.jp',
      description: 'Domain name for the certificate',
      exportName: 'LoanpediaDomainName',
    });

    // タグ付け
    cdk.Tags.of(this).add('Project', 'Loanpedia');
    cdk.Tags.of(this).add('Environment', 'Production');
    cdk.Tags.of(this).add('ManagedBy', 'CDK');
  }
}
