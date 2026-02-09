# 推奨アーキテクチャ実装ガイド

## アーキテクチャ概要

```
1. Python スクレイパー → raw_loan_data (生データ収集)
2. AI処理バッチ → processed_loan_data (BedRock API要約)
3. 統合処理 → loan_products (商品マスター構築)
```

## データフロー

### Step 1: 生データ収集 (Python + requests/BeautifulSoup)
```python
# パイプライン: 生データのみ保存
スクレイパー → raw_loan_data テーブル

保存内容:
- HTML全文
- スクレイピング抽出結果 (JSON)
- メタデータ (URL, ハッシュ等)
```

### Step 2: AI処理 (BedRock API)
```python
# バッチ処理: AI要約・構造化
ai_processing_batch.py → processed_loan_data テーブル

処理内容:
- HTML + 抽出データを BedRock API に送信
- Claude で構造化要約を生成
- データ品質スコア付与
- エラーハンドリング
```

### Step 3: 統合処理 (商品マスター)
```python
# バッチ処理: 商品マスター構築
product_integration_batch.py → loan_products テーブル

処理内容:
- AI要約データから商品情報を抽出
- データ標準化・正規化
- 検索用インデックス構築
```

## 実行方法

### 環境変数設定
```bash
# データベース接続
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=app_db

# AWS設定 (AI処理用)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### 全パイプライン実行
```bash
python3 run_pipeline.py --step full
```

### 個別ステップ実行
```bash
# Step 1: データ収集のみ
python3 run_pipeline.py --step scrape

# Step 2: AI処理のみ
python3 run_pipeline.py --step ai --ai-batch-size 10

# Step 3: 統合処理のみ
python3 run_pipeline.py --step integration --integration-batch-size 20
```

### 特定金融機関のスクレイピング実行
```bash
python3 run_pipeline.py --step scrape --target aomorimichinoku_bank
```

## データベーステーブル構成

### 1. raw_loan_data (生データ)
- `html_content`: HTML全文
- `structured_data`: スクレイピング抽出結果 (JSON)
- `content_hash`: 重複チェック用ハッシュ
- `scraped_at`: 収集日時

### 2. processed_loan_data (AI処理済み)
- `ai_summary`: BedRock API による構造化要約 (JSON)
- `ai_model`: 使用AIモデル名
- `processing_status`: 処理状況
- `validation_status`: データ品質状況
- `confidence_score`: 信頼度スコア

### 3. loan_products (統合商品マスター)
- `product_name`: 商品名
- `loan_category`: 標準化されたローン種別
- `interest_rate_min/max`: 金利範囲
- `loan_amount_min/max`: 融資額範囲
- `loan_term_min/max`: 融資期間
- `application_requirements`: 申込条件 (JSON)
- `features`: 商品特徴 (JSON)

## 利点

### 1. 処理の分離
- 各段階で独立したエラーハンドリング
- ステップ単位での再実行が可能
- デバッグ・メンテナンスが容易

### 2. データの透明性
- 生データ → AI処理済み → 統合済みの履歴が追跡可能
- 各段階でのデータ品質評価
- 処理ログの詳細記録

### 3. スケーラビリティ
- バッチサイズによる処理量調整
- 並列処理への拡張が容易
- 各ステップの独立したスケーリング

### 4. 保守性
- BedRock API プロンプトの独立した調整
- 統合ロジックの柔軟な変更
- テスト・検証の段階的実施

## 監視・運用

### ログ確認
```bash
# 全ステップのログ確認
python3 run_pipeline.py --step full 2>&1 | tee pipeline.log

# AI処理の詳細ログ
python3 ai_processing_batch.py --batch-size 1
```

### データ品質チェック
```sql
-- 未処理データの確認
SELECT COUNT(*) FROM raw_loan_data r 
LEFT JOIN processed_loan_data p ON r.id = p.raw_data_id 
WHERE p.id IS NULL;

-- AI処理の成功率
SELECT processing_status, COUNT(*) 
FROM processed_loan_data 
GROUP BY processing_status;

-- 統合済み商品数
SELECT COUNT(*) FROM loan_products WHERE is_active = TRUE;
```

## トラブルシューティング

### よくある問題
1. **AI処理でエラー**: AWS認証情報を確認
2. **DB接続エラー**: 環境変数とDocker起動状況を確認  
3. **重複データ**: content_hash による自動重複排除を確認