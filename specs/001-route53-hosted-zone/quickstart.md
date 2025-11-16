# Quickstart: Route53 パブリックホストゾーン作成

**Feature**: Route53 パブリックホストゾーン作成
**Date**: 2025-11-16
**Phase**: 1 - Design & Contracts

## 概要

このガイドでは、loanpedia.jpドメインのRoute53パブリックホストゾーンを作成し、お名前.comでネームサーバー設定を変更する手順を説明します。

## 前提条件

- AWS CDK環境がセットアップされている（`infra/` ディレクトリ）
- AWS認証情報が設定されている（GitHub OIDC認証またはローカルAWS CLI）
- お名前.comのアカウントとドメイン管理権限がある
- Node.js 18+ と npm がインストールされている

## ステップ1: 依存関係の確認

既存のCDKプロジェクトには必要なパッケージがインストール済みです。

```bash
cd infra/
npm list aws-cdk-lib
# 期待される出力: aws-cdk-lib@2.215.0
```

Route53モジュールは`aws-cdk-lib`に含まれているため、追加インストールは不要です。

## ステップ2: Route53スタックの作成

### 2-1. スタックファイルを作成

`infra/lib/route53-stack.ts` を作成：

```typescript
import * as cdk from 'aws-cdk-lib';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { Construct } from 'constructs';

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
    for (let i = 0; i < 4; i++) {
      new cdk.CfnOutput(this, `NameServer${i + 1}`, {
        value: cdk.Fn.select(i, hostedZone.hostedZoneNameServers!),
        description: `ネームサーバー ${i + 1}（お名前.comで設定）`,
      });
    }

    // ホストゾーンIDも出力（今後の参照用）
    new cdk.CfnOutput(this, 'HostedZoneId', {
      value: hostedZone.hostedZoneId,
      description: 'Route53 ホストゾーンID',
      exportName: 'LoanpediaHostedZoneId',
    });
  }
}
```

### 2-2. エントリポイントを更新

`infra/bin/loanpedia-app.ts` を更新して、Route53Stackをインスタンス化：

```typescript
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { GitHubOidcStack } from '../lib/github-oidc-stack';
import { Route53Stack } from '../lib/route53-stack';  // 追加

const app = new cdk.App();

// 既存のGitHub OIDC認証スタック
new GitHubOidcStack(app, 'GitHubOidcStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});

// Route53スタック（新規追加）
new Route53Stack(app, 'Route53Stack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});
```

## ステップ3: テストの作成（推奨）

`infra/test/route53-stack.test.ts` を作成：

```typescript
import { Template } from 'aws-cdk-lib/assertions';
import * as cdk from 'aws-cdk-lib';
import { Route53Stack } from '../lib/route53-stack';

describe('Route53Stack', () => {
  test('PublicHostedZone が作成される', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    // ホストゾーンが loanpedia.jp で作成されることを確認
    template.hasResourceProperties('AWS::Route53::HostedZone', {
      Name: 'loanpedia.jp.',
    });
  });

  test('ネームサーバー Outputs が存在する', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    // 4つのネームサーバーOutputが存在することを確認
    template.hasOutput('NameServer1', {});
    template.hasOutput('NameServer2', {});
    template.hasOutput('NameServer3', {});
    template.hasOutput('NameServer4', {});
  });

  test('HostedZoneId Output が存在する', () => {
    const app = new cdk.App();
    const stack = new Route53Stack(app, 'TestStack');
    const template = Template.fromStack(stack);

    template.hasOutput('HostedZoneId', {
      Export: {
        Name: 'LoanpediaHostedZoneId',
      },
    });
  });
});
```

## ステップ4: テスト実行

```bash
cd infra/
npm test
```

期待される出力:
```
PASS  test/route53-stack.test.ts
  Route53Stack
    ✓ PublicHostedZone が作成される
    ✓ ネームサーバー Outputs が存在する
    ✓ HostedZoneId Output が存在する
```

## ステップ5: CloudFormationテンプレートの確認

デプロイ前に、生成されるCloudFormationテンプレートを確認：

```bash
cd infra/
cdk synth Route53Stack
```

期待される出力（抜粋）:
```yaml
Resources:
  LoanpediaHostedZone:
    Type: AWS::Route53::HostedZone
    Properties:
      Name: loanpedia.jp.
      HostedZoneConfig:
        Comment: Loanpedia本番環境用パブリックホストゾーン

Outputs:
  NameServer1:
    Description: ネームサーバー 1（お名前.comで設定）
    Value: !Select
      - 0
      - !GetAtt LoanpediaHostedZone.NameServers
  ...
```

## ステップ6: デプロイ

Route53スタックをAWSにデプロイ：

```bash
cd infra/
cdk deploy Route53Stack
```

確認プロンプトが表示されます：
```
Do you wish to deploy these changes (y/n)? y
```

`y` を入力してデプロイを開始。

デプロイ完了後、Outputsが表示されます：
```
✅  Route53Stack

Outputs:
Route53Stack.NameServer1 = ns-1234.awsdns-12.com
Route53Stack.NameServer2 = ns-5678.awsdns-56.net
Route53Stack.NameServer3 = ns-9012.awsdns-90.org
Route53Stack.NameServer4 = ns-3456.awsdns-34.co.uk
Route53Stack.HostedZoneId = Z1234567890ABC
```

**重要**: これらのネームサーバー情報をコピーしてください。次のステップで使用します。

## ステップ7: お名前.comでネームサーバーを変更

### 7-1. お名前.comにログイン

1. [お名前.com](https://www.onamae.com/)にアクセス
2. お名前IDとパスワードでログイン

### 7-2. ネームサーバー設定を変更

1. 「ドメイン設定」タブをクリック
2. 「ネームサーバーの設定」→「ネームサーバーの変更」をクリック
3. `loanpedia.jp` を選択
4. 「他のネームサーバーを利用」を選択
5. ステップ6でコピーした4つのネームサーバーを入力：
   ```
   ネームサーバー1: ns-1234.awsdns-12.com
   ネームサーバー2: ns-5678.awsdns-56.net
   ネームサーバー3: ns-9012.awsdns-90.org
   ネームサーバー4: ns-3456.awsdns-34.co.uk
   ```
6. 「確認画面へ進む」をクリック
7. 内容を確認し、「設定する」をクリック

### 7-3. 設定完了の確認

お名前.comの画面に「ネームサーバーの変更を受け付けました」と表示されればOKです。

## ステップ8: DNS浸透の確認

ネームサーバー変更後、DNS浸透には通常1〜6時間、最大48時間かかります。

### 即座に確認（AWS Route53のネームサーバーに直接問い合わせ）

```bash
nslookup loanpedia.jp ns-1234.awsdns-12.com
```

期待される出力:
```
Server:  ns-1234.awsdns-12.com
Address:  xxx.xxx.xxx.xxx

Non-authoritative answer:
Name:    loanpedia.jp
```

### グローバルDNSでの浸透確認

```bash
nslookup loanpedia.jp
# または
dig loanpedia.jp NS
```

ネームサーバーがAWS Route53のものになっていればOK：
```
loanpedia.jp	nameserver = ns-1234.awsdns-12.com.
loanpedia.jp	nameserver = ns-5678.awsdns-56.net.
loanpedia.jp	nameserver = ns-9012.awsdns-90.org.
loanpedia.jp	nameserver = ns-3456.awsdns-34.co.uk.
```

## トラブルシューティング

### デプロイエラー: "HostedZone already exists"

既にloanpedia.jpのホストゾーンが存在する場合は、以下を確認：

```bash
aws route53 list-hosted-zones --query "HostedZones[?Name=='loanpedia.jp.']"
```

既存のホストゾーンを削除するか、CDKスタックをインポートする必要があります。

### お名前.comで設定できない

- ドメインロックが有効になっていないか確認
- ドメインの有効期限が切れていないか確認
- Whois情報公開代行設定が影響していないか確認

### DNS浸透が遅い

- 最大48時間待つ必要がある場合がある
- AWS Route53のネームサーバーに直接問い合わせることで、即座に確認可能
- `nslookup -type=NS loanpedia.jp 8.8.8.8` でGoogle DNSから確認

## 次のステップ

Route53ホストゾーンが正常に作成されたら、以下のインフラ構築に進めます：

1. **ACM証明書作成** - SSL/TLS証明書を取得（DNS検証）
2. **CloudFront設定** - CDN設定とAliasレコード追加
3. **ALB設定** - アプリケーションロードバランサーとAレコード追加

## 参考リンク

- [AWS CDK Route53 Documentation](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_route53-readme.html)
- [お名前.com ネームサーバー設定](https://www.onamae.com/guide/p/68)
- [Route53 料金](https://aws.amazon.com/jp/route53/pricing/)
