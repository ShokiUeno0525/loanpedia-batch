# 要件定義書

## プロジェクト概要

金融機関のローン情報を自動収集・要約し、エンドユーザーが参照できるシステムの構築

## 機能要件

### 1. データ収集機能

- **機能**: バッチ処理により金融機関の Web サイトからローン情報を抽出
- **対象**: 各金融機関の公式サイト
- **データ**: 金利、借入限度額、返済条件、申込条件等のローン情報

### 2. データ処理機能

- **機能**: 収集したローン情報を生成 AI で要約
- **処理内容**:
  - 重要なポイントの抽出
  - ユーザーフレンドリーな形式への変換
  - 統一フォーマットでの整理

### 3. データ保存機能

- **機能**: 処理済みデータをデータベースに保存
- **保存内容**:
  - 元データ
  - 要約データ
  - 更新日時
  - データソース情報

### 4. データ参照機能

- **機能**: エンドユーザーが保存されたデータを参照可能
- **提供方法**: API、Web UI 等

## 非機能要件

### 性能要件

- バッチ処理は定期実行（月次想定）
- データ更新の適切な頻度での実行

### 可用性要件

- システムの安定稼働
- エラーハンドリング機能

### セキュリティ要件

- 適切なアクセス制御
- データの安全な保存

## 技術要件

### バッチ処理

- Web スクレイピング機能
- 定期実行スケジューリング

### 生成 AI

- ローン情報の要約処理
- 構造化データの生成

### データベース

- 効率的なデータ保存・検索
- データの永続化

### API/UI

- エンドユーザー向けインターフェース
- データ参照機能

## システム構成

```
[金融機関サイト] → [バッチ処理] → [生成AI] → [データベース] → [エンドユーザー]
```

## 想定される技術スタック

- バッチ処理: Python
- 生成 AI: BedRock API / その他 LLM
- データベース: MySQL
- API: PHP(Laravel)
- フロントエンド: React
