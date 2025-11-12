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
- [共通仕様](#共通仕様)

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

### 概要

F01はバッチ処理機能のため、**エンドユーザー向けAPIは提供しません**。
内部的なバッチジョブとして実装されます。

---

## F02: ユーザー管理API

### POST /auth/register

ユーザー登録

**リクエスト:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "terms_accepted": true
}
```

**レスポンス（201 Created）:**
```json
{
  "user_id": "cognito-sub-uuid",
  "email": "user@example.com",
  "verification_status": "pending",
  "message": "確認メールを送信しました"
}
```

**エラー（400 Bad Request）:**
```json
{
  "error": "validation_error",
  "details": {
    "email": ["このメールアドレスは既に登録されています"],
    "password": ["パスワードは8文字以上必要です"]
  }
}
```

---

### POST /auth/login

ログイン

**リクエスト:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**レスポンス（200 OK）:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "cognito-sub-uuid",
    "email": "user@example.com"
  }
}
```

**エラー（401 Unauthorized）:**
```json
{
  "error": "authentication_failed",
  "message": "メールアドレスまたはパスワードが正しくありません"
}
```

---

### POST /auth/logout

ログアウト

**認証**: 必須

**リクエスト:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**レスポンス（200 OK）:**
```json
{
  "message": "ログアウトしました"
}
```

---

### POST /auth/refresh

トークンリフレッシュ

**リクエスト:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**レスポンス（200 OK）:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

### PUT /users/me/email

メールアドレス変更

**認証**: 必須

**リクエスト:**
```json
{
  "new_email": "newemail@example.com",
  "current_password": "SecurePass123!"
}
```

**レスポンス（200 OK）:**
```json
{
  "message": "確認メールを送信しました",
  "new_email": "newemail@example.com",
  "verification_status": "pending"
}
```

---

### PUT /users/me/password

パスワード変更

**認証**: 必須

**リクエスト:**
```json
{
  "current_password": "SecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

**レスポンス（200 OK）:**
```json
{
  "message": "パスワードを変更しました"
}
```

---

### POST /auth/password-reset/request

パスワードリセット要求

**リクエスト:**
```json
{
  "email": "user@example.com"
}
```

**レスポンス（200 OK）:**
```json
{
  "message": "パスワードリセット用の確認コードをメールで送信しました"
}
```

---

### POST /auth/password-reset/confirm

パスワードリセット確認

**リクエスト:**
```json
{
  "email": "user@example.com",
  "confirmation_code": "123456",
  "new_password": "NewSecurePass456!"
}
```

**レスポンス（200 OK）:**
```json
{
  "message": "パスワードをリセットしました"
}
```

---

## F03: 検索・閲覧API

### GET /loan-products

ローン商品一覧取得

**認証**: 不要

**クエリパラメータ:**
- `page` (integer, default: 1): ページ番号
- `per_page` (integer, default: 20, max: 100): 1ページあたりの件数
- `q` (string): 全文検索キーワード（商品名、概要）
- `institution_code` (string): 金融機関コード（例: 0117, 1250）
- `loan_type` (string): ローン種別（例: 住宅, 車, 教育）
- `interest_rate_min` (decimal): 最低金利（下限）
- `interest_rate_max` (decimal): 最高金利（上限）
- `loan_amount_min` (integer): 融資額（下限）
- `loan_amount_max` (integer): 融資額（上限）
- `repayment_period_min` (integer): 返済期間（下限、月単位）
- `repayment_period_max` (integer): 返済期間（上限、月単位）
- `sort_by` (string): ソート項目（interest_rate_min, loan_amount_max, updated_at）
- `sort_order` (string): ソート順（asc, desc）

**レスポンス（200 OK）:**
```json
{
  "data": [
    {
      "id": 1,
      "product_name": "みちのく住宅ローン",
      "product_code": "LOAN-0117-001",
      "institution_name": "青森みちのく銀行",
      "institution_code": "0117",
      "loan_type": "住宅",
      "interest_rate_min": 0.5,
      "interest_rate_max": 2.5,
      "interest_rate_type": "変動金利",
      "loan_amount_min": 1000000,
      "loan_amount_max": 100000000,
      "repayment_period_min": 12,
      "repayment_period_max": 420,
      "summary": "AI要約テキスト",
      "updated_at": "2025-11-13T10:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_items": 120,
    "total_pages": 6,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### GET /loan-products/{id}

ローン商品詳細取得

**認証**: 不要

**パスパラメータ:**
- `id` (integer): ローン商品ID

**レスポンス（200 OK）:**
```json
{
  "id": 1,
  "product_name": "みちのく住宅ローン",
  "product_code": "LOAN-0117-001",
  "institution_name": "青森みちのく銀行",
  "institution_code": "0117",
  "loan_type": "住宅",
  "loan_category": "新規購入",
  "interest_rate_min": 0.5,
  "interest_rate_max": 2.5,
  "interest_rate_type": "変動金利",
  "loan_amount_min": 1000000,
  "loan_amount_max": 100000000,
  "repayment_period_min": 12,
  "repayment_period_max": 420,
  "repayment_method": "元利均等返済、元金均等返済",
  "age_requirement_min": 20,
  "age_requirement_max": 65,
  "income_requirement": "安定した収入がある方",
  "guarantor_requirement": "保証会社利用可能",
  "special_features": "団体信用生命保険付き、繰上返済手数料無料",
  "summary": "AI要約テキスト",
  "source_url": "https://www.am-bk.co.jp/loan/housing",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-13T10:00:00Z"
}
```

**エラー（404 Not Found）:**
```json
{
  "error": "not_found",
  "message": "指定されたローン商品が見つかりません"
}
```

---

## F04: お気に入りAPI

### GET /favorites

お気に入り一覧取得

**認証**: 必須

**クエリパラメータ:**
- `page` (integer, default: 1): ページ番号
- `per_page` (integer, default: 20, max: 100): 1ページあたりの件数

**レスポンス（200 OK）:**
```json
{
  "data": [
    {
      "id": 1,
      "loan_product": {
        "id": 1,
        "product_name": "みちのく住宅ローン",
        "product_code": "LOAN-0117-001",
        "institution_name": "青森みちのく銀行",
        "institution_code": "0117",
        "loan_type": "住宅",
        "interest_rate_min": 0.5,
        "interest_rate_max": 2.5,
        "summary": "AI要約テキスト"
      },
      "created_at": "2025-11-13T10:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_items": 5,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

### POST /favorites

お気に入り登録

**認証**: 必須

**リクエスト:**
```json
{
  "loan_product_id": 1
}
```

**レスポンス（201 Created）:**
```json
{
  "id": 1,
  "loan_product_id": 1,
  "created_at": "2025-11-13T10:00:00Z",
  "message": "お気に入りに登録しました"
}
```

**エラー（400 Bad Request）:**
```json
{
  "error": "already_favorited",
  "message": "既にお気に入りに登録されています"
}
```

**エラー（400 Bad Request）:**
```json
{
  "error": "favorites_limit_exceeded",
  "message": "お気に入り登録数の上限（100件）に達しています"
}
```

**エラー（404 Not Found）:**
```json
{
  "error": "loan_product_not_found",
  "message": "指定されたローン商品が見つかりません"
}
```

---

### DELETE /favorites/{id}

お気に入り削除

**認証**: 必須

**パスパラメータ:**
- `id` (integer): お気に入りID

**レスポンス（200 OK）:**
```json
{
  "message": "お気に入りから削除しました"
}
```

**エラー（404 Not Found）:**
```json
{
  "error": "favorite_not_found",
  "message": "指定されたお気に入りが見つかりません"
}
```

---

### DELETE /favorites/by-product/{loan_product_id}

商品IDでお気に入り削除

**認証**: 必須

**パスパラメータ:**
- `loan_product_id` (integer): ローン商品ID

**レスポンス（200 OK）:**
```json
{
  "message": "お気に入りから削除しました"
}
```

**エラー（404 Not Found）:**
```json
{
  "error": "favorite_not_found",
  "message": "この商品はお気に入りに登録されていません"
}
```

---

## 共通仕様

### レスポンスフォーマット

#### 成功レスポンス

```json
{
  "data": {...},
  "meta": {...}
}
```

#### エラーレスポンス

```json
{
  "error": "error_code",
  "message": "エラーメッセージ",
  "details": {...}
}
```

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

### レート制限

- **認証済みユーザー**: 1000リクエスト/時間
- **未認証ユーザー**: 100リクエスト/時間

レート制限超過時のレスポンス:
```json
{
  "error": "rate_limit_exceeded",
  "message": "リクエスト制限を超えました。しばらく待ってから再試行してください",
  "retry_after": 3600
}
```

### CORS設定

- 許可オリジン: フロントエンドドメイン（環境変数で設定）
- 許可メソッド: GET, POST, PUT, DELETE, OPTIONS
- 許可ヘッダー: Content-Type, Authorization

### ページネーション

クエリパラメータ:
- `page`: ページ番号（1から開始）
- `per_page`: 1ページあたりの件数（デフォルト: 20, 最大: 100）

レスポンス内のpaginationオブジェクト:
```json
{
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_items": 120,
    "total_pages": 6,
    "has_next": true,
    "has_prev": false
  }
}
```

### タイムスタンプ形式

全てのタイムスタンプはISO 8601形式（UTC）:
```
2025-11-13T10:00:00Z
```

### バリデーションルール

#### メールアドレス
- RFC 5322準拠
- 最大254文字

#### パスワード
- 最小8文字
- 英数字記号混在を推奨（強制はしない）

#### 検索クエリ
- 最大200文字
- SQLインジェクション対策済み
