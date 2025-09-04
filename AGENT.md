**Purpose**
- Codex エージェント（CLI）用の運用ガイド。安全・確実にスクレイピング/バッチ処理コードの開発・検証を進めるための共通ルールと手順をまとめる。

**Operating Mode**
- 日本語で応対し、結果や差分の要点を簡潔に共有する。
- 変更は小さく段階的に。目的に関係ない修正は避ける。
- 重大変更や破壊的操作は事前に合意を取る。

**Project Context**
- 4 レイヤーの線形パイプライン: 収集(Python) → AI(Bedrock) → 保存(MySQL) → 提供(Laravel+React)。
- 月次のバッチ前提。スクレイピングは安定重視（エラーハンドリング/フォールバック/リトライ）。

**Safe Defaults**
- 外部サイトに依存するテストは原則スキップ。まずユニットテストから。
- スクレイピング先の仕様変更に備え、正規化・フォールバック（表/本文/PDF）を用意。
- Lambda/DB 統合はフラグ駆動（`save_to_db` 等）で局所的に検証可能にする。

**Setup**
- 依存同期: `uv sync`
- 実行環境: Python 3.10 以上
- 主要ライブラリ: `requests` `beautifulsoup4` `pdfplumber` `pytest`。
- タイムアウト: `pytest-timeout` を導入済（`--timeout=300` が利用可能）。

**Running Tests**
- ユニット: `uv run pytest tests/unit -q`
- オーケストレータ: `uv run pytest tests/unit/test_orchestrator.py -q`
- スクレイピング（ライブ）: `uv run pytest tests/scraping/ -v --timeout=300`
  - 環境やネットワーク状況により `skip` 条件あり。
  - 長時間・外部依存のため、必要時のみ実行。
- DB 統合: `tests/integration/test_database_integration.py`（`MYSQL_*` 環境変数が必要）
  - 既定値: host `127.0.0.1`, port `3306`, user `test_user`, password `test_password`, db `test_loanpedia`

**Coding Guidelines**
- 3 層の整理（I/O, Domain, Application）に従う。
  - I/O: HTTP クライアント、PDF/HTML パーサなど副作用境界
  - Domain: 抽出ロジック、正規化、モデル
  - Application: スクレイパー統合、オーケストレーション
- 既存スタイルに倣い、命名・ディレクトリ構造を踏襲。
- 型ヒントは可能な範囲で付与。例外は握り潰さず、文脈を含むログを残す。

**Scraping Guidelines**
- HTTP: セッション共通ヘッダ（UA）を使用。軽量なリトライ/タイムアウトを設定。
- HTML: まず構造化（テーブル/見出し）、なければ本文正規表現でフォールバック。
- PDF: `pdfplumber` で表抽出し、列見出しの同義語解決 → 正規化数値に変換。
- ロギング: 成功/フォールバック/デフォルト適用を INFO で記録。

**Aoimori Shinkin Package**
- 入口: `loanpedia_scraper/scrapers/aoimori_shinkin/`
- ファイル:
  - `config.py`: `BASE/START/PDF_URLS/HEADERS` を管理
  - `http_client.py`: UA 付き `requests.Session`
  - `html_parser.py`: 商品名と金利範囲の抽出
  - `pdf_parser.py`: `pdfplumber` ベースの表抽出
  - `extractors.py`: 正規化ユーティリティ
  - `models.py`: ベース項目ビルド/マージ
  - `product_scraper.py`: `AoimoriShinkinScraper` 本体（HTML/PDF を統合）
- 利用例:
  - `from loanpedia_scraper.scrapers.aoimori_shinkin import AoimoriShinkinScraper`
  - `AoimoriShinkinScraper(save_to_db=False).scrape_loan_info()`

**Orchestrator**
- 位置: `loanpedia_scraper/scrapers/main.py`
- `LoanScrapingOrchestrator` が各スクレイパーを集合実行。
- `aoimori_shinkin` 登録は段階的に差し替え可能（現状はダミー）。

**Git Workflow**
- ブランチ: `feature/*` `bugfix/*` で作業。`main` 直 push 禁止。
- コミットメッセージ（日本語）:
  - 形式: `種別: 概要（50文字以内）` + 必要に応じて詳細箇条書き
  - 種別: `feat` `fix` `docs` `refactor` `test` など

**Common Commands**
- 依存同期: `uv sync`
- テスト（短時間）: `uv run pytest tests/unit -q`
- テスト（ライブ/スクレイピング）: `uv run pytest tests/scraping/ -v --timeout=300`
- Mypy: `uv run mypy`

**Troubleshooting**
- `--timeout` 未認識: `pytest-timeout` を導入済。`pyproject.toml` の依存を確認。
- Lambda 相対 import: 絶対 import と `database` パッケージ化を優先（既存修正に倣う）。
- 外部先変更: 抽出を段階的に（本文 → 表 → PDF）切替え、最小限のデフォルトで継続。

