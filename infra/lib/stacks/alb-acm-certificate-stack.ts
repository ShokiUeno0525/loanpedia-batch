import * as cdk from 'aws-cdk-lib';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { Construct } from 'constructs';

/**
 * ALB用ACM証明書スタック
 *
 * ALB（Application Load Balancer）でHTTPS通信を実現するため、
 * api.loanpedia.jpドメインのSSL/TLS証明書をap-northeast-1リージョンで発行します。
 *
 * 作成されるリソース:
 * - ACM証明書（api.loanpedia.jp、ap-northeast-1）
 * - DNS検証用のRoute53レコード（自動作成）
 *
 * 注: CloudFront用証明書（us-east-1）とは別に、ALB用（ap-northeast-1）が必要です。
 */
export class AlbAcmCertificateStack extends cdk.Stack {
  /**
   * 作成されたACM証明書
   */
  public readonly certificate: acm.Certificate;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Route53 Stackからホストゾーンを参照
    const hostedZone = route53.HostedZone.fromHostedZoneAttributes(this, 'HostedZone', {
      hostedZoneId: cdk.Fn.importValue('LoanpediaHostedZoneId'),
      zoneName: 'loanpedia.jp',
    });

    // api.loanpedia.jp用のACM証明書を作成（ap-northeast-1）
    // DNS検証方式を使用し、Route53に検証用CNAMEレコードを自動追加
    this.certificate = new acm.Certificate(this, 'AlbCertificate', {
      domainName: 'api.loanpedia.jp',
      validation: acm.CertificateValidation.fromDns(hostedZone),
    });

    // CloudFormation Output: 証明書ARN
    new cdk.CfnOutput(this, 'CertificateArn', {
      value: this.certificate.certificateArn,
      description: 'ALB用ACM証明書ARN (api.loanpedia.jp)',
      exportName: 'LoanpediaAlbCertificateArn',
    });
  }
}
