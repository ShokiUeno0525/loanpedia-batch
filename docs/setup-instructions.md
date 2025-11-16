# AWS SAM CLI セットアップ手順

## 1. SAM CLIインストール

### Windows
```bash
# 方法1: winget（推奨）
winget install Amazon.SAM-CLI

# 方法2: Chocolatey
choco install aws-sam-cli

# 方法3: MSIダウンローダー
# https://github.com/aws/aws-sam-cli/releases/latest
```

### インストール確認
```bash
sam --version
# 期待する出力: SAM CLI, version 1.x.x
```

## 2. Dockerセットアップ

SAM CLIはDockerを使用してビルドします：

### Docker Desktopインストール
```bash
# https://www.docker.com/products/docker-desktop/
```

### Docker確認
```bash
docker --version
# 期待する出力: Docker version 20.x.x
```

## 3. プロジェクトビルド

```bash
# プロジェクトルートで実行
cd /mnt/c/Users/notai/loanpedia-batch

# 依存関係を含めてビルド
sam build --use-container

# 特定の関数のみビルド
sam build AoimoriShinkinScraperFunction --use-container
```

## 4. ローカルテスト実行

```bash
# 基本実行
sam local invoke AoimoriShinkinScraperFunction

# イベント付きで実行
sam local invoke AoimoriShinkinScraperFunction --event events/aoimori_shinkin_test.json

# デバッグモード
sam local invoke AoimoriShinkinScraperFunction --debug
```

## 5. トラブルシューティング

### よくある問題と解決法

1. **"sam: command not found"**
   - PATH環境変数にSAM CLIが追加されていない
   - PowerShellを再起動してください

2. **Docker関連エラー**
   - Docker Desktopが起動していない
   - Docker Desktopを起動してください

3. **依存関係エラー**
   - requirements.txtの場所を確認
   - Python 3.13対応バージョンを使用

## 6. 代替方法（SAM CLIが使えない場合）

### Python 3.11にダウングレード
```yaml
# template.yamlを修正
Runtime: python3.11
```

この方法なら確実に動作します。