import * as cdk from 'aws-cdk-lib';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { Construct } from 'constructs';

/**
 * Route53 パブリックホストゾーンスタック
 *
 * @remarks
 * このスタックはloanpedia.jpドメインのDNS管理をAWS Route53で行うための
 * パブリックホストゾーンを作成します。お名前.comで取得したドメインを
 * AWSインフラと統合し、今後のサービスデプロイメント（フロントエンド、API、
 * SSL証明書など）の基盤を整えます。
 *
 * 作成されるリソース:
 * - loanpedia.jp のパブリックホストゾーン
 * - ネームサーバー情報のCloudFormation Outputs（お名前.com設定用）
 * - HostedZoneIdのエクスポート（他のスタックからの参照用）
 */
export class Route53Stack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // loanpedia.jp のパブリックホストゾーンを作成
    const hostedZone = new route53.PublicHostedZone(this, 'LoanpediaHostedZone', {
      zoneName: 'loanpedia.jp',
      comment: 'Loanpedia本番環境用パブリックホストゾーン',
    });

    // ネームサーバー情報を個別に出力（お名前.comでの設定用）
    // AWS Route53は自動的に4つのネームサーバーを割り当てる
    // Fn.select を使用してトークンリストから各要素を取得
    const nameServers = hostedZone.hostedZoneNameServers || [];
    for (let i = 0; i < 4; i++) {
      new cdk.CfnOutput(this, `NameServer${i + 1}`, {
        value: cdk.Fn.select(i, nameServers),
        description: `ネームサーバー ${i + 1}（お名前.comで設定）`,
      });
    }

    // ホストゾーンIDを出力（将来の参照用：ACM証明書、CloudFrontなど）
    new cdk.CfnOutput(this, 'HostedZoneId', {
      value: hostedZone.hostedZoneId,
      description: 'Route53 ホストゾーンID（他のスタックから参照可能）',
      exportName: 'LoanpediaHostedZoneId',
    });
  }
}
