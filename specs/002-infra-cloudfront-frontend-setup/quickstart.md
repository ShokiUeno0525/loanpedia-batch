# Quickstart: CloudFront フロントエンド配信基盤

**対象**: 開発者・インフラエンジニア
**所要時間**: 約30分（CloudFrontデプロイ時間含む）
**前提条件**: AWS CLI、Node.js 20.x、AWS CDK 2.215.0以上

## 概要

このガイドでは、CloudFront + S3によるフロントエンド配信基盤をAWS CDKでデプロイし、テスト用のindex.htmlを表示するまでの手順を説明します。

## 前提条件の確認

### 必要なツール

```bash
# Node.jsバージョン確認
node --version  # v20.x 以上

# AWS CLIバージョン確認
aws --version   # aws-cli/2.x 以上

# AWS CDKバージョン確認
cdk --version   # 2.215.0 以上
```

### AWS認証情報の設定

```bash
# AWS認証情報が設定されていることを確認
aws sts get-caller-identity

# 出力例:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }
```

### 既存リソースの確認

以下のリソースが既にデプロイされている必要があります：

1. **Route53ホストゾーン**: loanpedia.jp
2. **ACM証明書**: loanpedia.jp（us-east-1リージョン）

```bash
# Route53ホストゾーンの確認
aws route53 list-hosted-zones --query "HostedZones[?Name=='loanpedia.jp.']"

# ACM証明書の確認（us-east-1リージョン）
aws acm list-certificates --region us-east-1 --query "CertificateSummaryList[?DomainName=='loanpedia.jp']"
```

## セットアップ手順

### Step 1: リポジトリのクローンとブランチ切り替え

```bash
# リポジトリのクローン（既にクローン済みの場合はスキップ）
git clone https://github.com/ShokiUeno0525/loanpedia-batch.git
cd loanpedia-batch

# 機能ブランチに切り替え
git checkout 001-cloudfront-frontend-setup
```

### Step 2: 依存関係のインストール

```bash
# infraディレクトリに移動
cd infra

# 依存関係のインストール
npm install
```

### Step 3: CDKブートストラップ（初回のみ）

CDKを初めて使用する場合、ブートストラップが必要です：

```bash
# ブートストラップの確認
aws cloudformation describe-stacks --stack-name CDKToolkit

# スタックが存在しない場合はブートストラップ実行
cdk bootstrap
```

### Step 4: CDKスタックの確認

```bash
# スタック一覧の確認
cdk list

# 出力例:
# GitHubOidcStack
# Route53Stack
# AcmCertificateStack
# CloudFrontFrontendStack  ← 今回デプロイするスタック
```

### Step 5: CDKスタックのシンセサイズ

CloudFormationテンプレートを生成して確認します：

```bash
# シンセサイズ実行
cdk synth CloudFrontFrontendStack

# 生成されたテンプレートの確認
less cdk.out/CloudFrontFrontendStack.template.json
```

### Step 6: 差分の確認

既存リソースとの差分を確認します：

```bash
# 差分確認
cdk diff CloudFrontFrontendStack

# 出力例:
# Stack CloudFrontFrontendStack
# Resources
# [+] AWS::S3::Bucket FrontendBucket FrontendBucket12345678
# [+] AWS::CloudFront::OriginAccessControl OAC OAC12345678
# [+] AWS::CloudFront::Distribution Distribution Distribution12345678
# [+] AWS::WAFv2::WebACL WebACL WebACL12345678
# [+] AWS::Route53::RecordSet CloudFrontARecord CloudFrontARecord12345678
# ...
```

### Step 7: デプロイ実行

```bash
# デプロイ実行（承認プロンプトあり）
cdk deploy CloudFrontFrontendStack

# 承認なしでデプロイする場合
cdk deploy CloudFrontFrontendStack --require-approval never
```

**注意**: CloudFrontディストリビューションのデプロイには15〜20分かかります。

デプロイ中の出力例：

```
CloudFrontFrontendStack: deploying...
CloudFrontFrontendStack: creating CloudFormation changeset...

 ✅  CloudFrontFrontendStack

Outputs:
CloudFrontFrontendStack.DistributionId = E1234567890ABC
CloudFrontFrontendStack.DistributionDomainName = d111111abcdef8.cloudfront.net
CloudFrontFrontendStack.FrontendBucketName = loanpedia-frontend-123456789012
CloudFrontFrontendStack.CustomDomainName = loanpedia.jp
...

Stack ARN:
arn:aws:cloudformation:ap-northeast-1:123456789012:stack/CloudFrontFrontendStack/...
```

### Step 8: デプロイ完了の確認

```bash
# スタックの状態確認
aws cloudformation describe-stacks \
  --stack-name CloudFrontFrontendStack \
  --query 'Stacks[0].StackStatus'

# 出力: "CREATE_COMPLETE" または "UPDATE_COMPLETE"
```

## テスト用コンテンツのデプロイ

### Step 9: テスト用index.htmlの作成

```bash
# テスト用のHTMLファイルを作成
cat > /tmp/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loanpedia - ローン情報集約サービス</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }
        h1 {
            color: #333;
        }
        .status {
            background: #e7f4e7;
            border: 2px solid #4caf50;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }
        .info {
            text-align: left;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>🎉 Loanpedia フロントエンド配信基盤</h1>
    <div class="status">
        <h2>✅ デプロイ成功！</h2>
        <p>CloudFront + S3による配信基盤が正常に動作しています。</p>
    </div>
    <div class="info">
        <h3>システム構成:</h3>
        <ul>
            <li>CloudFront ディストリビューション</li>
            <li>S3 バケット（プライベート、OAC経由でアクセス）</li>
            <li>WAF（AWS Managed Rules有効）</li>
            <li>Route53 DNSレコード（loanpedia.jp）</li>
            <li>CloudWatch Logsロギング</li>
        </ul>
    </div>
    <p><small>Deployed: <span id="timestamp"></span></small></p>
    <script>
        document.getElementById('timestamp').textContent = new Date().toLocaleString('ja-JP');
    </script>
</body>
</html>
EOF
```

### Step 10: S3バケットへのアップロード

```bash
# CloudFormation OutputsからS3バケット名を取得
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name CloudFrontFrontendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
  --output text)

echo "S3バケット名: $BUCKET_NAME"

# index.htmlをS3にアップロード
aws s3 cp /tmp/index.html s3://$BUCKET_NAME/index.html

# アップロード確認
aws s3 ls s3://$BUCKET_NAME/
```

## 動作確認

### Step 11: CloudFrontディストリビューション経由でアクセス

```bash
# ブラウザで以下のURLを開く
echo "https://loanpedia.jp"
```

ブラウザで https://loanpedia.jp にアクセスして、テスト用のindex.htmlが表示されることを確認します。

### Step 12: S3直接アクセスの拒否確認

```bash
# S3バケットの直接URLを取得
BUCKET_DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name CloudFrontFrontendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketDomainName`].OutputValue' \
  --output text)

echo "S3直接URL: https://$BUCKET_DOMAIN/index.html"

# curlで直接アクセスを試行（アクセス拒否されることを確認）
curl -I https://$BUCKET_DOMAIN/index.html

# 期待される出力: HTTP/1.1 403 Forbidden
```

### Step 13: CloudWatch Logsの確認

```bash
# ログバケット名を取得
LOG_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name CloudFrontFrontendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`LogBucketName`].OutputValue' \
  --output text)

# ログファイルの確認（数分後にログが作成される）
aws s3 ls s3://$LOG_BUCKET/cloudfront/ --recursive
```

### Step 14: WAFメトリクスの確認

```bash
# WAF WebACL IDを取得
WEB_ACL_ID=$(aws cloudformation describe-stacks \
  --stack-name CloudFrontFrontendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`WebAclId`].OutputValue' \
  --output text)

# CloudWatchメトリクスの確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name AllowedRequests \
  --dimensions Name=WebACL,Value=$WEB_ACL_ID Name=Region,Value=us-east-1 Name=Rule,Value=ALL \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## トラブルシューティング

### 問題1: CloudFrontデプロイが失敗する

**原因**: ACM証明書がus-east-1リージョンに存在しない

**解決策**:
```bash
# ACM証明書の確認（us-east-1リージョン）
aws acm list-certificates --region us-east-1

# 証明書が存在しない場合は、AcmCertificateStackをデプロイ
cdk deploy AcmCertificateStack
```

### 問題2: Route53レコード作成が失敗する

**原因**: ホストゾーンが存在しない

**解決策**:
```bash
# Route53ホストゾーンの確認
aws route53 list-hosted-zones

# ホストゾーンが存在しない場合は、Route53Stackをデプロイ
cdk deploy Route53Stack
```

### 問題3: S3へのアップロードが失敗する

**原因**: IAM権限不足

**解決策**:
```bash
# 現在のIAMユーザー/ロールを確認
aws sts get-caller-identity

# S3への書き込み権限を持つIAMポリシーを確認
aws iam get-user-policy --user-name your-user --policy-name your-policy
```

### 問題4: CloudFrontでコンテンツが表示されない

**原因**: キャッシュが古い、またはS3にファイルが存在しない

**解決策**:
```bash
# S3バケットのファイル確認
aws s3 ls s3://$BUCKET_NAME/

# CloudFrontのキャッシュ無効化
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name CloudFrontFrontendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

## クリーンアップ

スタックを削除する場合：

```bash
# S3バケットのコンテンツを削除（バケットが空でないと削除できない）
aws s3 rm s3://$BUCKET_NAME --recursive

# ログバケットのコンテンツを削除
aws s3 rm s3://$LOG_BUCKET --recursive

# CloudFormationスタックの削除
cdk destroy CloudFrontFrontendStack

# 確認プロンプトで "y" を入力
```

**注意**: CloudFrontディストリビューションの削除には時間がかかります（5〜10分）。

## 次のステップ

1. **バックエンドAPI統合**: ALBを構築して/apiビヘイビアを実装
2. **CI/CDパイプライン構築**: GitHub Actionsで自動デプロイ
3. **カスタムエラーページ**: 404、403エラー用のカスタムページを追加
4. **WAFルール追加**: レートリミット、GeoBlocking、IP制限を設定
5. **CloudWatch Alarmsの設定**: エラー率、レイテンシの監視

## 参考資料

- [AWS CDK公式ドキュメント](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [CloudFront OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [AWS WAF](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html)
- [プロジェクトドキュメント](../../../../README.md)
