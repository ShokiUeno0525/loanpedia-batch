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
├── infrastructure/       # インフラストラクチャ
│   ├── cdk/             # AWS CDK（RDS等）
│   └── docker/          # Docker設定
│
├── docs/                # ドキュメント
│   ├── requirements.md
│   ├── architecture.md
│   └── ...
│
├── CLAUDE.md           # Claude Code 指示書
└── README.md           # このファイル
```

## 詳細ドキュメント

- [プロジェクト概要](docs/vision.md)
- [アーキテクチャ](docs/architecture.md)
- [セットアップ手順](docs/setup-instructions.md)
- [開発ガイド](CLAUDE.md)