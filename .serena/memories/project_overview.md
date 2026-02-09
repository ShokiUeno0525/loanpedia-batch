# Loanpedia Batch Processing System - プロジェクト概要

## プロジェクトの目的
金融機関からローン情報を自動収集し、AI で処理してエンドユーザーに提供するローン情報集約システム。月次データ収集サイクルでバッチ処理アーキテクチャを採用している。

## 技術スタック
- **メイン言語**: Python 3.10以上
- **Webスクレイピング**: BeautifulSoup4, requests
- **AI処理**: AWS BedRock API
- **データベース**: MySQL (SQLAlchemy)
- **AWS**: SAM CLI, Lambda
- **テスト**: pytest, pytest-cov, pytest-mock
- **PDF処理**: PyPDF2, pdfplumber
- **その他**: Pydantic, python-dotenv, requests

## システムアーキテクチャ
システムは線形パイプラインの4つの主要コンポーネントで構成：

1. **データ収集** (Python): 金融機関のWebサイトからローン情報を抽出
2. **データ処理** (AI): BedRock APIを使用してローンデータを要約・構造化
3. **データ保存** (MySQL): 元データ、処理済み要約、タイムスタンプ、ソース情報を保存
4. **ユーザーインターフェース** (Python API + React): エンドユーザーがローンデータにアクセス

## 主要なコンポーネント

### スクレイパー
- `LoanScrapingOrchestrator`: 全金融機関のスクレイピングを統括するオーケストレーター
- 対応金融機関:
  - 青森信用金庫 (aoimori_shinkin)
  - 青森みちのく銀行 (aomori_michinoku)
  - 東奥信用金庫 (touou_shinkin)
  - 青森県信用組合 (aomoriken_shinyoukumiai)

### バッチ処理
- `ai_processing_batch.py`: AI要約・構造化処理
- `product_integration_batch.py`: 商品マスター構築

### データベース
- MySQL with SQLAlchemy
- テーブル構造: raw_loan_data, processed_loan_data, loan_products