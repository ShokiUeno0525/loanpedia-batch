# Loanpedia Batch Processing System

[![CI Tests](https://github.com/ShokiUeno0525/loanpedia-batch/actions/workflows/tests.yml/badge.svg)](https://github.com/ShokiUeno0525/loanpedia-batch/actions/workflows/tests.yml)

金融機関からローン情報を自動収集し、AI で処理してエンドユーザーに提供するローン情報集約システムです。

## プロジェクト構造

```
loanpedia-batch/
├── backend/              # バックエンド関連
│   ├── api/             # Laravel API（今後実装予定）
│   └── batch/           # バッチ処理システム
│       ├── loanpedia_scraper/  # Lambda関数（スクレイピング）
│       ├── scripts/            # デプロイ・実行スクリプト
│       ├── tests/              # テストコード
│       ├── events/             # Lambda テストイベント
│       ├── template.yaml       # AWS SAM テンプレート
│       ├── samconfig.toml      # SAM デプロイ設定
│       └── pyproject.toml      # Python プロジェクト設定
│
├── frontend/            # フロントエンド（React + Vite + TypeScript）
│   ├── src/             # ソースコード
│   ├── public/          # 静的ファイル
│   └── ...
│
├── infra/               # インフラストラクチャ（AWS CDK）
│   ├── lib/             # CDK スタック定義
│   ├── bin/             # CDK エントリーポイント
│   ├── docker/          # Docker 設定
│   └── ...
│
├── docs/                # ドキュメント
│   ├── requirements.md
│   ├── architecture.md
│   └── ...
│
├── specs/               # 機能仕様書
│
├── CLAUDE.md            # Claude Code 指示書
└── README.md            # このファイル
```

## CloudFront Basic認証

開発環境で CloudFront に Basic 認証が設定されています。

### 認証情報

認証情報はチームメンバーに直接共有されています。
**※ セキュリティのため、認証情報は本リポジトリには記載しません。**

必要な場合は、管理者またはチームリーダーに確認してください。

### 認証情報の変更

認証情報を変更する場合は、[infra/lib/constructs/basic-auth-function.ts](infra/lib/constructs/basic-auth-function.ts) の CloudFront Function コード内の認証情報を編集してください。変更後、CDK を再デプロイしてください。

## 詳細ドキュメント

- [プロジェクト概要](docs/vision.md)
- [アーキテクチャ](docs/architecture.md)
- [セットアップ手順](docs/setup-instructions.md)
- [開発ガイド](CLAUDE.md)