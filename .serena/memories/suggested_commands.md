# 推奨コマンド - Windows環境

## 開発環境のセットアップ
```bash
# プロジェクトルートでuvによる依存関係インストール
uv sync

# 仮想環境のアクティベート
source .venv/Scripts/activate  # GitBash
# または
.venv\Scripts\activate.bat     # CMD
# または  
.venv\Scripts\Activate.ps1     # PowerShell
```

## テスト関連コマンド
```bash
# すべてのテストを実行
pytest

# カバレッジ付きテスト実行
pytest --cov=loanpedia_scraper --cov-report=html

# 特定のテストファイルのみ実行
pytest tests/test_scrapers.py

# Verbose出力でテスト実行
pytest -v
```

## 型チェック・品質管理
```bash
# 型チェック実行
mypy loanpedia_scraper/

# 型チェック（全体）
mypy .
```

## AWS SAM関連
```bash
# SAM CLIバージョン確認
sam --version

# プロジェクトビルド
sam build --use-container

# ローカルテスト実行
sam local invoke AoimoriShinkinScraperFunction

# イベント付きテスト実行
sam local invoke AoimoriShinkinScraperFunction --event events/aoimori_shinkin_test.json

# デバッグモード
sam local invoke AoimoriShinkinScraperFunction --debug
```

## スクレイピング実行
```bash
# メインスクレイパー実行
python loanpedia_scraper/scrapers/main.py

# 特定機関のみスクレイピング
python -c "from loanpedia_scraper.scrapers.main import LoanScrapingOrchestrator; orchestrator = LoanScrapingOrchestrator(); orchestrator.run_single_scraper('aoimori_shinkin')"

# AI処理バッチ実行
python ai_processing_batch.py

# 商品統合バッチ実行
python product_integration_batch.py
```

## Docker関連
```bash
# Docker状態確認
docker --version

# Docker Compose起動
docker-compose up -d

# Docker Compose停止
docker-compose down
```

## ユーティリティコマンド（Windows）
```bash
# ディレクトリ一覧表示
dir         # CMD
ls          # GitBash/PowerShell

# ファイル内容表示
type filename.txt    # CMD
cat filename.txt     # GitBash
Get-Content filename.txt  # PowerShell

# プロセス検索
tasklist | findstr python

# ファイル検索
dir /s /b *.py  # CMD
find . -name "*.py"  # GitBash
Get-ChildItem -Recurse -Filter "*.py"  # PowerShell
```

## Git関連
```bash
# ステータス確認
git status

# 全体差分確認
git diff

# ブランチ作成・切替
git checkout -b feature/new-feature

# コミット作成
git add .
git commit -m "feat: 新機能を追加"

# プッシュ
git push origin feature/new-feature
```