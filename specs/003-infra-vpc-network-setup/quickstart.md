# クイックスタート: VPCネットワーク基盤のデプロイ

**Feature**: 003-infra-vpc-network-setup
**最終更新**: 2025-11-18

## 概要

このガイドでは、AWS CDK を使用して Loanpedia プロジェクトの VPC ネットワーク基盤をデプロイする手順を説明します。

## 前提条件

### 必須要件

- **Node.js**: v18.0.0 以上
- **npm**: v9.0.0 以上
- **AWS CLI**: v2.0.0 以上
- **AWS CDK**: v2.215.0 以上
- **AWS アカウント**: 有効なアカウントと適切な IAM 権限
- **Elastic IP 割り当て枠**: NAT Gateway 用に最低1つ

### 必要な IAM 権限

デプロイを実行するユーザー/ロールには以下の権限が必要です:

- `ec2:*` (VPC, サブネット, ゲートウェイの作成・管理)
- `cloudformation:*` (CDK が使用)
- `iam:*` (CDK 実行ロールの作成)
- `s3:*` (CDK アセットの保存)

推奨: `AdministratorAccess` または専用の CDK デプロイ用ロール

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd loanpedia-batch
git checkout 003-infra-vpc-network-setup
```

### 2. 依存関係のインストール

```bash
cd infrastructure
npm install
```

### 3. AWS 認証情報の設定

#### オプション A: AWS CLI プロファイルを使用

```bash
aws configure --profile loanpedia-dev
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: ap-northeast-1
# Default output format: json
```

#### オプション B: 環境変数を使用

```bash
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
export AWS_DEFAULT_REGION=ap-northeast-1
```

### 4. CDK のブートストラップ（初回のみ）

AWS アカウントで初めて CDK を使用する場合、ブートストラップが必要です:

```bash
cdk bootstrap aws://ACCOUNT-ID/ap-northeast-1 --profile loanpedia-dev
```

**注意**: `ACCOUNT-ID` は実際の AWS アカウント ID に置き換えてください。

## デプロイ手順

### 1. CloudFormation テンプレートの生成

デプロイ前に、生成される CloudFormation テンプレートを確認します:

```bash
cdk synth VpcNetworkStack --profile loanpedia-dev
```

出力例:
```yaml
Resources:
  LoanpediaVpc:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.16.0.0/16
      # ...
```

### 2. 差分の確認

既存のスタックとの差分を確認します（初回デプロイ時は全て新規作成）:

```bash
cdk diff VpcNetworkStack --profile loanpedia-dev
```

### 3. デプロイの実行

```bash
cdk deploy VpcNetworkStack --profile loanpedia-dev
```

デプロイには約 3-5 分かかります。以下のリソースが作成されます:

- VPC (10.16.0.0/16)
- Internet Gateway
- パブリックサブネット (10.16.0.0/20)
- プライベートサブネット (10.16.32.0/20)
- アイソレートサブネット (10.16.64.0/20)
- NAT Gateway + Elastic IP
- ルートテーブル x3

**確認プロンプト**:
```
Do you wish to deploy these changes (y/n)? y
```

### 4. デプロイの確認

デプロイが完了したら、スタック出力を確認します:

```bash
aws cloudformation describe-stacks \
  --stack-name VpcNetworkStack \
  --query 'Stacks[0].Outputs' \
  --profile loanpedia-dev
```

出力例:
```json
[
  {
    "OutputKey": "VpcId",
    "OutputValue": "vpc-0123456789abcdef0"
  },
  {
    "OutputKey": "PublicSubnetId",
    "OutputValue": "subnet-0123456789abcdef1"
  },
  {
    "OutputKey": "PrivateSubnetId",
    "OutputValue": "subnet-0123456789abcdef2"
  },
  {
    "OutputKey": "IsolatedSubnetId",
    "OutputValue": "subnet-0123456789abcdef3"
  }
]
```

## 動作確認

### 1. VPC の確認

```bash
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=Loanpedia-Dev-VPC-Main" \
  --profile loanpedia-dev
```

CIDR ブロックが `10.16.0.0/16` であることを確認してください。

### 2. サブネットの確認

```bash
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=<VPC_ID>" \
  --profile loanpedia-dev
```

3つのサブネットが存在し、CIDR が以下であることを確認:
- 10.16.0.0/20 (パブリック)
- 10.16.32.0/20 (プライベート)
- 10.16.64.0/20 (アイソレート)

### 3. NAT Gateway の確認

```bash
aws ec2 describe-nat-gateways \
  --filter "Name=vpc-id,Values=<VPC_ID>" \
  --profile loanpedia-dev
```

State が `available` であることを確認してください。

### 4. ルートテーブルの確認

```bash
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=<VPC_ID>" \
  --profile loanpedia-dev
```

各サブネットのルートテーブルに正しいルートが設定されていることを確認:
- パブリック: 0.0.0.0/0 → Internet Gateway
- プライベート: 0.0.0.0/0 → NAT Gateway
- アイソレート: VPC ローカルのみ

### 5. 接続テスト（オプション）

#### パブリックサブネットの接続確認

一時的な EC2 インスタンスを起動して、インターネット接続を確認します:

```bash
aws ec2 run-instances \
  --image-id ami-0d52744d6551d851e \
  --instance-type t2.micro \
  --subnet-id <PUBLIC_SUBNET_ID> \
  --associate-public-ip-address \
  --security-group-ids <SECURITY_GROUP_ID> \
  --key-name <YOUR_KEY_PAIR> \
  --profile loanpedia-dev
```

SSH でログインし、インターネット接続を確認:
```bash
ssh ec2-user@<PUBLIC_IP>
curl https://www.google.com
# 200 OK が返ることを確認
```

#### プライベートサブネットの接続確認

同様に、プライベートサブネットにインスタンスを起動し、NAT Gateway 経由の接続を確認します:

```bash
aws ec2 run-instances \
  --image-id ami-0d52744d6551d851e \
  --instance-type t2.micro \
  --subnet-id <PRIVATE_SUBNET_ID> \
  --no-associate-public-ip-address \
  --security-group-ids <SECURITY_GROUP_ID> \
  --profile loanpedia-dev
```

パブリックインスタンス経由で SSH:
```bash
ssh -J ec2-user@<PUBLIC_IP> ec2-user@<PRIVATE_IP>
curl https://www.google.com
# NAT Gateway 経由で接続できることを確認
```

**重要**: テスト後はインスタンスを必ず削除してください。

## トラブルシューティング

### エラー: "Resource limit exceeded: EIP"

**原因**: Elastic IP の割り当て上限に達しています。

**解決策**:
1. AWS コンソールで未使用の Elastic IP を確認
2. 不要な EIP を解放
3. または AWS サポートで上限緩和をリクエスト

### エラー: "Insufficient permissions"

**原因**: IAM 権限が不足しています。

**解決策**:
1. IAM ポリシーで必要な権限を確認
2. `AdministratorAccess` を一時的に付与（開発環境のみ）
3. 最小権限の CDK デプロイ用ロールを作成

### デプロイが "CREATE_IN_PROGRESS" で停止

**原因**: NAT Gateway の作成に時間がかかっています（通常 2-3 分）。

**解決策**:
- そのまま待機してください
- 5分以上経過してもステータスが変わらない場合は、AWS コンソールで確認

### "ROLLBACK_COMPLETE" 状態になった

**原因**: デプロイ中にエラーが発生しました。

**解決策**:
1. CloudFormation コンソールでエラーの詳細を確認
2. スタックを削除: `cdk destroy VpcNetworkStack --profile loanpedia-dev`
3. エラーを修正後、再度デプロイ

## クリーンアップ

### リソースの削除

VPC ネットワーク基盤を削除する場合:

```bash
cdk destroy VpcNetworkStack --profile loanpedia-dev
```

**警告**:
- VPC に依存するリソース（EC2, RDS など）が存在する場合、削除は失敗します
- 先にすべての依存リソースを削除してください
- NAT Gateway と Elastic IP の削除には数分かかります

### 削除の確認

```bash
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=Loanpedia-Dev-VPC-Main" \
  --profile loanpedia-dev
```

VPC が存在しないことを確認してください。

## コスト見積もり

### 月額コスト（ap-northeast-1 リージョン）

| リソース | 料金 | 月額概算 |
|----------|------|----------|
| VPC | 無料 | $0 |
| サブネット | 無料 | $0 |
| Internet Gateway | 無料 | $0 |
| NAT Gateway (時間) | $0.062/時間 | $45 |
| NAT Gateway (データ転送) | $0.062/GB | 従量制 |
| Elastic IP (NAT Gateway 用) | 無料（アタッチ済み） | $0 |

**合計**: 約 $45/月 + データ転送料

**コスト最適化のヒント**:
- 開発環境では NAT Gateway を必要時のみ起動
- VPC Endpoints（S3, DynamoDB）を使用してデータ転送料を削減
- 本番環境以外では夜間・週末に NAT Gateway を停止

## 次のステップ

VPC ネットワーク基盤のデプロイが完了したら、以下のリソースを追加できます:

1. **セキュリティグループの作成**
   - ALB, ECS, Lambda, RDS 用のセキュリティグループ

2. **Application Load Balancer (ALB) の配置**
   - パブリックサブネットに ALB を配置
   - HTTPS リスナーと証明書の設定

3. **ECS クラスタの作成**
   - プライベートサブネットに ECS タスクを配置
   - ALB からのルーティング設定

4. **RDS インスタンスの作成**
   - アイソレートサブネットに RDS を配置
   - ECS/Lambda からの接続設定

5. **Lambda 関数のデプロイ**
   - プライベートサブネットで VPC Lambda を実行
   - RDS と外部 API への接続

## リファレンス

### 関連ドキュメント

- [仕様書 (spec.md)](./spec.md)
- [実装計画 (plan.md)](./plan.md)
- [技術調査 (research.md)](./research.md)

### AWS ドキュメント

- [VPC とサブネット](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html)
- [NAT Gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [AWS CDK v2 ドキュメント](https://docs.aws.amazon.com/cdk/v2/guide/home.html)

### サポート

問題が発生した場合は、以下を確認してください:

1. [CloudFormation スタックイベント](https://console.aws.amazon.com/cloudformation/)
2. [VPC コンソール](https://console.aws.amazon.com/vpc/)
3. プロジェクトの Issue トラッカー
