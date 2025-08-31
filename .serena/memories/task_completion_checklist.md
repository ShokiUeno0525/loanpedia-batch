# タスク完了時のチェックリスト

## 開発完了後に実行すべきコマンド

### 1. 型チェック実行
```bash
# 型チェック実行
mypy loanpedia_scraper/
mypy .
```

### 2. テスト実行
```bash
# 全テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=loanpedia_scraper --cov-report=html

# 詳細出力でテスト
pytest -v
```

### 3. SAMビルドテスト（該当する場合）
```bash
# SAMビルド確認
sam build --use-container

# ローカルテスト実行
sam local invoke AoimoriShinkinScraperFunction --event events/aoimori_shinkin_test.json
```

### 4. Docker環境テスト（該当する場合）
```bash
# Docker Compose起動確認
docker-compose up -d

# 動作確認後停止
docker-compose down
```

## コミット前チェック

### 1. ファイルの整理
- 不要なファイルの削除
- `.gitignore`の確認
- 機密情報の除外確認

### 2. コミットメッセージ規約
```
種別: 概要（50文字以内）

詳細説明（必要に応じて）
- 変更内容の詳細
- 変更理由
- 影響範囲
```

### 3. ブランチ戦略確認
- `main`ブランチへの直接プッシュ禁止
- フィーチャーブランチからのプルリクエスト作成

## デプロイ前チェック

### 1. 環境変数確認
- `.env.example`の更新
- 本番環境用の設定確認

### 2. 依存関係確認
```bash
# 依存関係の最新化
uv sync

# セキュリティチェック（推奨）
pip audit
```

### 3. ドキュメント更新
- README.mdの更新（必要に応じて）
- API仕様書の更新（該当する場合）