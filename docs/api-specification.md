# API仕様書

**ドキュメント種別**: API仕様書
**プロジェクト**: Loanpedia Batch Processing System
**作成日**: 2025-11-13
**ステータス**: Draft
**API基盤**: FastAPI + SQLAlchemy

## 概要

本ドキュメントは、Loanpedia Batch Processing SystemのREST APIエンドポイント一覧です。

関連ドキュメント:
- [要件定義書（機能概要）](features-overview.md)
- [プロダクトビジョン](vision.md)

---

## 目次

- [F01: データ収集・処理API](#f01-データ収集処理api)
- [F02: ユーザー管理API](#f02-ユーザー管理api)
- [F03: 検索・閲覧API](#f03-検索閲覧api)
- [F04: お気に入りAPI](#f04-お気に入りapi)

---

## F01: データ収集・処理API

F01はバッチ処理機能のため、**エンドユーザー向けAPIは提供しません**。

---

## F02: ユーザー管理API

| メソッド | エンドポイント | 説明 | 認証 |
|---------|---------------|------|------|
| POST | /auth/register | ユーザー登録 | 不要 |
| POST | /auth/login | ログイン | 不要 |
| POST | /auth/logout | ログアウト | 必須 |
| POST | /auth/refresh | トークンリフレッシュ | 不要 |
| PUT | /users/me/email | メールアドレス変更 | 必須 |
| PUT | /users/me/password | パスワード変更 | 必須 |
| POST | /auth/password-reset/request | パスワードリセット要求 | 不要 |
| POST | /auth/password-reset/confirm | パスワードリセット確認 | 不要 |

---

## F03: 検索・閲覧API

| メソッド | エンドポイント | 説明 | 認証 |
|---------|---------------|------|------|
| GET | /loan-products | ローン商品一覧取得 | 不要 |
| GET | /loan-products/{id} | ローン商品詳細取得 | 不要 |

### /loan-products のクエリパラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| page | integer | ページ番号（デフォルト: 1） |
| per_page | integer | 1ページあたりの件数（デフォルト: 20, 最大: 100） |
| q | string | 全文検索キーワード（商品名、概要） |
| institution_code | string | 金融機関コード（例: 0117, 1250） |
| loan_type | string | ローン種別（例: 住宅, 車, 教育） |
| interest_rate_min | decimal | 最低金利（下限） |
| interest_rate_max | decimal | 最高金利（上限） |
| loan_amount_min | integer | 融資額（下限） |
| loan_amount_max | integer | 融資額（上限） |
| repayment_period_min | integer | 返済期間（下限、月単位） |
| repayment_period_max | integer | 返済期間（上限、月単位） |
| sort_by | string | ソート項目（interest_rate_min, loan_amount_max, updated_at） |
| sort_order | string | ソート順（asc, desc） |

---

## F04: お気に入りAPI

| メソッド | エンドポイント | 説明 | 認証 |
|---------|---------------|------|------|
| GET | /favorites | お気に入り一覧取得 | 必須 |
| POST | /favorites | お気に入り登録 | 必須 |
| DELETE | /favorites/{id} | お気に入り削除（お気に入りID指定） | 必須 |
| DELETE | /favorites/by-product/{loan_product_id} | お気に入り削除（商品ID指定） | 必須 |
