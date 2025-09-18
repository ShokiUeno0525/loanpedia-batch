<!--
/AGENT.md
Codex CLI向け運用ガイドと作業規約
なぜ: 安全・確実・最小コストで開発/検証するため
関連: README_ARCHITECTURE.md, docs/requirements.md, docker-compose.yml, template.yaml
-->

# AGENT 運用ガイド（Vectal適用・最小版）

## 目的と原則
- シンプル・モジュール化・十分なコメント。要求内のみ実装（過剰設計禁止）。
- 80/20で最短ルート。命名と分割を丁寧に。迷ったらデータ鮮度と処理成功率を優先。

## プロジェクト概要（このリポジトリ）
- バッチ/スクレイピング/AI要約/統合を担う Lambda/Python リポジトリ。
- 全体像は `README_ARCHITECTURE.md` と `docs/requirements.md` を参照。

## 技術スタック
- バッチ/関数: Python 3.12 + AWS Lambda (SAM)
- スクレイピング: requests, BeautifulSoup4
- AI処理: Amazon Bedrock + boto3
- DB: MySQL 8.0 (pymysql)
- 補助: Docker Compose, LocalStack, SAM Local
- テスト: pytest

## 実行/開発コマンド
- 起動: `docker-compose up -d`
- テスト: `pytest -q`
- AI処理: `python ai_processing_batch.py --batch-size 5`
- 統合処理: `python product_integration_batch.py --batch-size 10`
- SAMビルド: `sam build --use-container`
- SAMローカル実行: `sam local invoke AoimoriShinkinScraperFunction --event events/aoimori_shinkin_test.json`
- Lambdaローカル一括: `./test-lambda.sh`
- デプロイ（確認付き）: `./deploy.sh`
- 参考: `setup_instructions.md`, `template.yaml`, `docker-compose.yml`

## データベース方針
- 段階保存（raw → processed → products）。重複はハッシュで排除。
- 主要テーブル: `raw_loan_data`, `processed_loan_data`, `loan_products`。
- スキーマ/初期化: `loanpedia_scraper/database/create_tables.sql`, `init_database.py`。
- 注意: DB変更はユーザーのみ実行可（提案OK・実行NG）。

## コメントとファイル分割
- 各ファイル冒頭に4行ヘッダー（必須/削除禁止）。
  1. ファイルの場所  2. 何をするか  3. なぜ存在するか  4. 関連2〜4ファイル
- 単一責務・300行以下/ファイル。大きくなったら `handlers / services / scrapers / database` に分割。

## KPI（このリポジトリで重視）
- Data Freshness（収集→反映の遅延）
- Coverage（対象機関/商品のカバー率）
- Processing Success Rate（各ステップの成功率）

## クイック＆ダーティー
- まず動く最小実装→学びを得る→必要箇所のみ強化。
- リスク/仮説はコメントで明文化。TODOで可視化。

## ユーザーの学び支援
- なぜこの設計/実装かを短く併記（入出力・前提・失敗時挙動）。

## Git 運用（簡潔版）
- ブランチ: `main`（安定）/ `feature/*`（開発）/ `hotfix/*`（緊急）。
- コミット: 小さく頻繁に。日本語OK。機密はコミット禁止。
- PR: 変更概要/理由/テスト方法/影響範囲を記載。テストが通ってから作成。
- 禁止: `main`直push、強制push、機密コミット、大量変更の単一コミット。

コミットメッセージ例:
```
feat: 東奥信用金庫のPDF抽出を追加

・金利表の表構造ゆらぎに対応（colspan補正）
・既存HTMLパーサーとI/Fを統一
テスト: 単体/ローカルLambdaでOK
影響: touou_shinkin系スクレイパーのみ
```

## セキュリティ/運用上の注意
- `.env` や資格情報はコミット禁止。LocalStackと実本番を混同しない。
- 依存は定期更新。失敗時は安全側に倒す（ロールバック/早期return）。

## 参照ファイル
- アーキ: `README_ARCHITECTURE.md`
- 要件: `docs/requirements.md`
- インフラ: `docker-compose.yml`, `template.yaml`, `deploy.sh`, `setup_instructions.md`, `test-lambda.sh`

## FAQ（抜粋）
- SAMが動かない: `setup_instructions.md` の手順とDocker起動を確認。
- DB接続失敗: `docker-compose.yml` の環境変数と `DB_HOST` の到達性を確認。
- Bedrock失敗: AWS認証/リージョン/レート制限。リトライは指数バックオフ。

---
本ガイドはVectalの方針（シンプル・最小・十分なコメント）を反映。範囲外の追加や重い処理はユーザー指示がある場合のみ実施。
