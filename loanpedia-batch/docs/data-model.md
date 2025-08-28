# データモデル設計書

## 概要

ローン情報集約システムのデータベース構造を定義します。
スクレイピングで収集したデータを基に、手動でローン商品情報を整理・提供するシンプルな構成です。

erDiagram
    financial_institutions {
        int id PK
        string institution_code "機関コード"
        string name "金融機関名"
        string website_url "公式サイトURL"
        string institution_type "機関種別(銀行/信金/信組)"
        datetime created_at
        datetime updated_at
    }
    raw_loan_data {
        int id PK
        int financial_institution_id FK
        string source_url "取得元URL"
        text html_content "HTML全文"
        text extracted_text "抽出テキスト"
        string content_hash "コンテンツハッシュ"
        string scraping_status "取得ステータス"
        datetime scraped_at "取得日時"
        datetime created_at
        datetime updated_at
    }
    loan_products {
        int id PK
        int financial_institution_id FK
        string product_code "商品コード"
        string product_name "商品名"
        string loan_type "ローン種別"
        string category "カテゴリ"
        decimal min_interest_rate "最低金利"
        decimal max_interest_rate "最高金利"
        string interest_type "金利種別"
        bigint min_loan_amount "最低融資額"
        bigint max_loan_amount "最高融資額"
        int min_loan_term "最短融資期間(月)"
        int max_loan_term "最長融資期間(月)"
        string repayment_method "返済方法"
        int min_age "最低年齢"
        int max_age "最高年齢"
        text income_requirements "収入条件"
        text guarantor_requirements "保証人要件"
        text special_features "商品特徴"
        string source_reference "参照元データID"
        boolean is_active "有効フラグ"
        datetime published_at "公開日"
        datetime created_at
        datetime updated_at
    }
    data_update_history {
        int id PK
        int financial_institution_id FK
        string update_type "更新種別(scraping/manual_entry)"
        int records_processed "処理件数"
        int success_count "成功件数"
        int error_count "エラー件数"
        text error_details "エラー詳細"
        datetime started_at "開始日時"
        datetime completed_at "完了日時"
        string status "ステータス"
        datetime created_at
    }
    financial_institutions ||--o{ raw_loan_data : "収集"
    financial_institutions ||--o{ loan_products : "提供"
    financial_institutions ||--o{ data_update_history : "更新履歴"


## 運用フロー

1. **データ収集**: バッチ処理で金融機関サイトをスクレイピング → `raw_loan_data`
2. **データ整理**: 収集データを参照して手動で商品情報を整理 → `loan_products`
3. **データ提供**: `loan_products`テーブルからLaravel APIでデータ提供
4. **履歴管理**: 各処理の実行状況を`data_update_history`で追跡