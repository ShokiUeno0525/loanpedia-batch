# API仕様書

**ドキュメント種別**: API仕様書
**プロジェクト**: Loanpedia Batch Processing System
**作成日**: 2025-11-13
**ステータス**: Draft
**API基盤**: FastAPI + SQLAlchemy

## 概要

本ドキュメントは、Loanpedia Batch Processing SystemのREST APIエンドポイントを定義します。

関連ドキュメント:
- [要件定義書（機能概要）](features-overview.md)
- [プロダクトビジョン](vision.md)

---

## 目次

- [認証](#認証)
- [F01: データ収集・処理API](#f01-データ収集処理api)
- [F02: ユーザー管理API](#f02-ユーザー管理api)
- [F03: 検索・閲覧API](#f03-検索閲覧api)
- [F04: お気に入りAPI](#f04-お気に入りapi)

---

## 認証

### 認証方式

- **AWS Cognito JWT トークン認証**
- Authorizationヘッダーに`Bearer {token}`形式で指定

### 認証が必要なエンドポイント

- F04（お気に入り機能）の全エンドポイント
- F02（ユーザー管理）の一部エンドポイント

### 認証不要なエンドポイント

- F03（検索・閲覧機能）の全エンドポイント
- F02のユーザー登録・ログイン

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
| GET | /loan-products | ローン商品一覧取得（フィルタ、ソート、ページネーション） | 不要 |
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
| GET | /favorites | お気に入り一覧取得（ページネーション） | 必須 |
| POST | /favorites | お気に入り登録 | 必須 |
| DELETE | /favorites/{id} | お気に入り削除（お気に入りID指定） | 必須 |
| DELETE | /favorites/by-product/{loan_product_id} | お気に入り削除（商品ID指定） | 必須 |

---

## 補足事項

### レート制限

- **認証済みユーザー**: 1000リクエスト/時間
- **未認証ユーザー**: 100リクエスト/時間

### CORS設定

- 許可オリジン: フロントエンドドメイン（環境変数で設定）
- 許可メソッド: GET, POST, PUT, DELETE, OPTIONS

### HTTPステータスコード

| コード | 説明 |
|--------|------|
| 200 | OK - 成功 |
| 201 | Created - リソース作成成功 |
| 400 | Bad Request - リクエストが不正 |
| 401 | Unauthorized - 認証失敗 |
| 403 | Forbidden - 権限不足 |
| 404 | Not Found - リソースが見つからない |
| 422 | Unprocessable Entity - バリデーションエラー |
| 429 | Too Many Requests - レート制限超過 |
| 500 | Internal Server Error - サーバーエラー |
