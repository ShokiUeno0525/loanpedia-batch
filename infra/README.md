# Loanpedia Infrastructure (AWS CDK)

Loanpediaローン情報集約システムのAWSインフラストラクチャをAWS CDK (TypeScript)で定義しています。

## プロジェクト概要

このプロジェクトは、ローン情報集約システムのAWSインフラを構築するCDKアプリケーションです。

### 主要コンポーネント

#### フロントエンド基盤
- **CloudFront**: loanpedia.jp でのWebコンテンツ配信
- **S3**: 静的コンテンツ保存、CloudFrontログ保存
- **WAF**: AWS Managed Rulesによる保護
- **ACM証明書**: loanpedia.jp (us-east-1)
- **Route53**: DNSホストゾーン

#### バックエンド基盤
- **VPC**: 2AZ構成（ap-northeast-1a、1c）
  - パブリックサブネット×2（ALB配置用）
  - プライベートサブネット×1（ECS配置用）
  - アイソレートサブネット×1（RDS配置用）
- **ALB**: Application Load Balancer（2AZ、HTTPS）
- **ECS Fargate**: Web APIサービス（タスク数1）、マイグレーションタスク
- **RDS MySQL 8.0**: データベース（db.t3.micro、20GB）
- **Cognito User Pool**: ユーザー認証（EMAIL_OTP MFA）
- **ECR**: Dockerイメージリポジトリ（loanpedia-api、loanpedia-migration）
- **CloudWatch Logs**: ECSログ（7日間保持）
- **Secrets Manager**: RDS認証情報、Cognito認証情報
- **ACM証明書**: api.loanpedia.jp (ap-northeast-1)

## 前提条件

- Node.js 18以上
- AWS CLI設定済み
- お名前.comでloanpedia.jpドメイン取得済み

## セットアップ

```bash
# 依存関係インストール
npm install

# TypeScriptビルド
npm run build

# テスト実行
npm test
```

## デプロイ手順

### 1. Route53ホストゾーン作成

```bash
npx cdk deploy Route53Stack
```

デプロイ後、Outputsに表示されるネームサーバー情報をお名前.comで設定してください。

### 2. ACM証明書作成（CloudFront用）

```bash
npx cdk deploy AcmCertificateStack
```

証明書はDNS検証で自動的に検証されます（Route53ホストゾーン必須）。

### 3. VPCネットワーク基盤構築

```bash
npx cdk deploy VpcNetworkStack
```

### 4. ALB用ACM証明書作成

```bash
npx cdk deploy AlbAcmCertificateStack
```

api.loanpedia.jp用のACM証明書をap-northeast-1リージョンで作成します。

### 5. バックエンドスタック構築

```bash
npx cdk deploy BackendStack
```

以下のリソースが作成されます：
- ECRリポジトリ（loanpedia-api、loanpedia-migration）
- RDS MySQL 8.0
- Cognito User Pool
- ALB（2AZ配置）
- ECS Fargate（Web APIサービス、マイグレーションタスク）
- CloudWatch Logs
- Secrets Manager
- セキュリティグループ

### 6. S3バケット作成

```bash
npx cdk deploy S3Stack
```

### 7. CloudFrontフロントエンド配信基盤構築

```bash
npx cdk deploy FrontendStack
```

CloudFront、WAF、Route53 Aレコードが作成されます。

### 全スタック一括デプロイ

```bash
npx cdk deploy --all
```

## スタック構成

| スタック名 | リージョン | 説明 |
|---|---|---|
| GitHubOidcStack | ap-northeast-1 | GitHub Actions OIDC認証 |
| Route53Stack | グローバル | loanpedia.jpホストゾーン |
| AcmCertificateStack | us-east-1 | CloudFront用ACM証明書 |
| VpcNetworkStack | ap-northeast-1 | VPCネットワーク基盤 |
| AlbAcmCertificateStack | ap-northeast-1 | ALB用ACM証明書 |
| BackendStack | ap-northeast-1 | バックエンドインフラ |
| S3Stack | ap-northeast-1 | S3バケット |
| FrontendStack | us-east-1 | CloudFront配信基盤 |

## 開発コマンド

```bash
# TypeScriptビルド
npm run build

# ファイル監視モード
npm run watch

# テスト実行
npm test

# スナップショット更新
npm test -- -u

# CDKテンプレート生成
npx cdk synth

# デプロイ差分確認
npx cdk diff

# スタック削除
npx cdk destroy <StackName>
```

## アーキテクチャ

### ネットワーク構成

```
VPC: 10.16.0.0/16
├── パブリックサブネット（AZ-a）: 10.16.0.0/20  → ALB
├── パブリックサブネット（AZ-c）: 10.16.16.0/20 → ALB
├── プライベートサブネット（AZ-a）: 10.16.128.0/20 → ECS Fargate
└── アイソレートサブネット（AZ-a）: 10.16.192.0/20 → RDS
```

### 通信フロー

```
ユーザー
  ↓ HTTPS
CloudFront (loanpedia.jp)
  ├─ / → S3バケット（静的コンテンツ）
  └─ /api/* → ALB (api.loanpedia.jp)
       ↓ HTTPS
     ECS Fargate (Web API)
       ↓
     RDS MySQL 8.0
```

## セキュリティ

- **WAF**: AWS Managed Rulesによる保護
- **ALB**: CloudFront Managed Prefix Listからのみ許可
- **ECS**: プライベートサブネット配置、ALBからのみアクセス可能
- **RDS**: アイソレートサブネット配置、ECSからのみアクセス可能
- **Secrets Manager**: DB認証情報、Cognito認証情報を安全に管理
- **HTTPS**: 全通信をHTTPSで暗号化

## モニタリング

- **CloudWatch Logs**: ECSタスクログ（7日間保持）
- **CloudFront**: アクセスログをS3に保存
- **ALB**: アクセスログ（オプション）

## コスト最適化

- **ECS Container Insights**: 無効化（コスト削減）
- **RDS**: db.t3.micro、シングルAZ配置
- **CloudWatch Logs**: 7日間保持
- **CloudFront**: Price Class 200（北米、ヨーロッパ、アジア）

## トラブルシューティング

### ACM証明書検証が完了しない

Route53ホストゾーンが正しく設定されているか確認してください。DNS検証レコードは自動的に追加されます。

### ECSタスクが起動しない

- ECRリポジトリにDockerイメージがプッシュされているか確認
- CloudWatch Logsでエラーログを確認
- Secrets Managerの認証情報が正しいか確認

### ALBヘルスチェックが失敗する

- ECSタスクが `/health` エンドポイントを実装しているか確認
- セキュリティグループでALB→ECSの通信が許可されているか確認

## ライセンス

MIT
