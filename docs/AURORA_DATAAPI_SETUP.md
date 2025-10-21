# Aurora Serverless v2 + Data API セットアップガイド

## 概要

このガイドでは、Aurora Serverless v2 + RDS Data API を使用したデータベース接続の設定方法を説明します。

### アーキテクチャ

```
Lambda (Python)
  ↓ boto3 (rds-data client)
  ↓ HTTPS
Aurora Serverless v2 (Data API有効)
  ↓ Secrets Manager
認証情報
```

### メリット

- **VPC不要**: LambdaをVPC内に配置する必要がない
- **接続プール不要**: HTTPベースのステートレス接続
- **PyMySQL不要**: boto3のみで動作
- **コスト削減**: アイドル時のACU最小化（0.5ACU）
- **自動スケーリング**: 負荷に応じて自動的にスケール

## 前提条件

- CDKでAurora Serverless v2クラスターがデプロイ済み
- Data APIが有効化されている
- Secrets Managerに認証情報が保存されている

## セットアップ手順

### 1. CDKでAuroraをデプロイ

このリポジトリの `cdk/` ディレクトリにCDKスタックが含まれています：

```bash
cd cdk

# 依存関係インストール
npm install

# 初回のみ: CDK Bootstrap
npx cdk bootstrap

# デプロイ
npx cdk deploy
```

デプロイ後、CloudFormation Outputsが表示されます：

```
Outputs:
LoanpediaAuroraStack.DbClusterArn = arn:aws:rds:ap-northeast-1:xxxx:cluster:xxxx
LoanpediaAuroraStack.DbSecretArn = arn:aws:secretsmanager:ap-northeast-1:xxxx:secret:xxxx
LoanpediaAuroraStack.DbName = loanpedia
```

これらの値は自動的にCloudFormation Exportsに登録され、SAMテンプレートで参照されます。

**注意**: Auroraのデプロイには15〜20分かかります。

### 2. SAMテンプレートの環境変数（自動設定済み）

`template.yaml` では、CDKのOutputsを自動的に参照するよう設定済み：

```yaml
Globals:
  Function:
    Environment:
      Variables:
        USE_DATA_API: "true"
        DB_ARN:
          Fn::ImportValue: LoanpediaDbClusterArn
        DB_SECRET_ARN:
          Fn::ImportValue: LoanpediaDbSecretArn
        DB_NAME:
          Fn::ImportValue: LoanpediaDbName
```

**手動設定は不要です！** CDKデプロイ後、SAMが自動的に値を取得します。

### 3. SAMでLambdaをデプロイ

```bash
# ビルド
sam build

# デプロイ
sam deploy --guided

# または既存の設定を使用
sam deploy
```

### 4. 動作確認

Lambda関数を手動実行してテスト：

```bash
# EventBridgeトリガーを一時的に有効化するか、手動実行
aws lambda invoke \
  --function-name sam-app-AomorimichinokuBankScraperFunction-xxx \
  --payload '{"test": true}' \
  response.json

# ログを確認
sam logs -n AomorimichinokuBankScraperFunction --tail
```

ログで以下を確認：
- `Using RDS Data API adapter` - Data APIが使用されている
- `Saved raw_loan_data with Data API: ID=xxx` - データ保存成功

## 混在運用

### PyMySQL（従来型）とData APIの切り替え

環境変数 `USE_DATA_API` で切り替え可能：

| 環境変数 | 使用アダプター | 必要なライブラリ | VPC必要 |
|---------|--------------|----------------|---------|
| `USE_DATA_API=false` | LoanDatabase (PyMySQL) | pymysql | Yes |
| `USE_DATA_API=true` | RDSDataAPIAdapter (boto3) | boto3 | No |

### ローカル開発

ローカル開発時はPyMySQL + docker-composeを使用：

```bash
# .env または環境変数
USE_DATA_API=false
DB_HOST=host.docker.internal
DB_PORT=3307
DB_USER=app_user
DB_PASSWORD=app_password
DB_NAME=app_db
```

### AWS環境

AWS環境ではData APIを使用：

```yaml
# template.yaml
Environment:
  Variables:
    USE_DATA_API: "true"
    DB_ARN: "arn:aws:rds:..."
    DB_SECRET_ARN: "arn:aws:secretsmanager:..."
    DB_NAME: "loanpedia"
```

## トラブルシューティング

### Data API接続エラー

```
ClientError: An error occurred (BadRequestException) when calling the ExecuteStatement operation
```

**原因**: DB_ARN または DB_SECRET_ARN が間違っている

**解決策**:
1. CDKのOutputsから正しいARNを確認
2. template.yamlの環境変数を更新
3. 再デプロイ: `sam deploy`

### IAM権限エラー

```
AccessDeniedException: User is not authorized to perform: rds-data:ExecuteStatement
```

**原因**: LambdaのIAMロールに権限がない

**解決策**: template.yamlの Policies セクションを確認（すでに追加済み）

### Secrets Manager権限エラー

```
AccessDeniedException: User is not authorized to perform: secretsmanager:GetSecretValue
```

**原因**: Secrets Managerへのアクセス権限がない

**解決策**: template.yamlの Policies セクションを確認（すでに追加済み）

## コスト最適化

### Aurora Serverless v2 のコスト

- **最小ACU**: 0.5 ACU（約$0.06/時間 = 約$43/月）
- **最大ACU**: 2 ACU（約$0.24/時間 = 約$172/月）
- **Data API**: 100万リクエストあたり$0.35

### 推奨設定

月次バッチ処理の場合：

```typescript
serverlessV2ScalingConfiguration: {
  minCapacity: 0.5,  // アイドル時のコストを最小化
  maxCapacity: 2,    // バースト時の上限を設定
}
```

## 参考資料

- [AWS RDS Data API Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html)
- [Aurora Serverless v2 Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html)
- [boto3 RDS Data API Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds-data.html)
