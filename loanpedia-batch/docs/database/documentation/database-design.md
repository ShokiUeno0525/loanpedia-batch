# データベース設計書

## テーブル設計

### 1. マスターデータテーブル

#### 1.1 金融機関マスター (financial_institutions)

```sql
CREATE TABLE financial_institutions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    institution_code VARCHAR(10) UNIQUE NOT NULL COMMENT '金融機関コード',
    institution_name VARCHAR(100) NOT NULL COMMENT '金融機関名',
    institution_name_kana VARCHAR(100) COMMENT '金融機関名カナ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive') DEFAULT 'active',
    INDEX idx_status (status),
    FULLTEXT idx_search (institution_name, institution_name_kana)
) COMMENT '金融機関マスターテーブル';
```

#### 1.2 データソースマスター (data_sources)

```sql
CREATE TABLE data_sources (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    institution_id BIGINT NOT NULL COMMENT '金融機関ID',
    source_name VARCHAR(100) NOT NULL COMMENT 'データソース名',
    base_url VARCHAR(255) NOT NULL COMMENT 'ベースURL',
    target_urls JSON NOT NULL COMMENT '対象URL配列',
    scraping_config JSON NOT NULL COMMENT 'スクレイピング設定',
    loan_types JSON NOT NULL COMMENT '対象ローン種別',
    scrape_schedule VARCHAR(50) DEFAULT '0 2 1 * *' COMMENT 'cron形式スケジュール',
    retry_config JSON COMMENT 'リトライ設定',
    rate_limit_config JSON COMMENT 'レート制限設定',
    last_scraped_at TIMESTAMP COMMENT '最終取得日時',
    next_scrape_at TIMESTAMP COMMENT '次回取得予定日時',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('active', 'inactive', 'error') DEFAULT 'active',

    FOREIGN KEY (institution_id) REFERENCES financial_institutions(id),
    INDEX idx_institution (institution_id),
    INDEX idx_status (status),
    INDEX idx_next_scrape (next_scrape_at)
) COMMENT 'データソース管理テーブル';
```

### 2. 生データ管理テーブル

#### 2.1 生ローンデータ (raw_loan_data)

```sql
CREATE TABLE raw_loan_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    data_source_id BIGINT NOT NULL COMMENT 'データソースID',
    institution_id BIGINT NOT NULL COMMENT '金融機関ID',
    source_url TEXT NOT NULL COMMENT '取得元URL',
    page_title VARCHAR(200) COMMENT 'ページタイトル',
    html_content LONGTEXT COMMENT 'HTML内容',
    extracted_text MEDIUMTEXT COMMENT '抽出テキスト',
    structured_data JSON COMMENT '構造化データ',
    content_hash VARCHAR(64) COMMENT 'コンテンツハッシュ',
    content_length INT COMMENT 'コンテンツサイズ',
    http_status INT COMMENT 'HTTPステータス',
    response_headers JSON COMMENT 'レスポンスヘッダー',
    extraction_metadata JSON COMMENT '抽出メタデータ',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '取得日時',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (data_source_id) REFERENCES data_sources(id),
    FOREIGN KEY (institution_id) REFERENCES financial_institutions(id),
    INDEX idx_source_date (data_source_id, scraped_at),
    INDEX idx_institution_date (institution_id, scraped_at),
    INDEX idx_hash (content_hash),
    INDEX idx_scraped_date (scraped_at)
) COMMENT '生ローンデータテーブル';
```

### 3. AI 処理管理テーブル

#### 3.1 AI 処理済みデータ (processed_loan_data)

```sql
CREATE TABLE processed_loan_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    raw_data_id BIGINT NOT NULL COMMENT '生データID',
    institution_id BIGINT NOT NULL COMMENT '金融機関ID',
    ai_summary JSON NOT NULL COMMENT 'AI要約データ',
    ai_model VARCHAR(50) NOT NULL COMMENT 'AIモデル名',
    processing_version VARCHAR(20) COMMENT '処理バージョン',
    processing_status ENUM('pending', 'processing', 'completed', 'failed', 'retry') DEFAULT 'pending',
    validation_status ENUM('valid', 'warning', 'error') DEFAULT 'valid',
    validation_messages JSON COMMENT '検証メッセージ',
    error_message TEXT COMMENT 'エラーメッセージ',
    processed_at TIMESTAMP COMMENT 'AI処理完了日時',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (raw_data_id) REFERENCES raw_loan_data(id),
    FOREIGN KEY (institution_id) REFERENCES financial_institutions(id),
    INDEX idx_raw_data (raw_data_id),
    INDEX idx_institution_status (institution_id, processing_status),
    INDEX idx_status_date (processing_status, processed_at),
    INDEX idx_ai_model (ai_model)
) COMMENT 'AI処理済みデータテーブル';
```

### 4. 統合ローン情報テーブル

#### 4.1 統合ローン商品 (loan_products)

```sql
CREATE TABLE loan_products (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    processed_data_id BIGINT NOT NULL COMMENT '処理済みデータID',
    institution_id BIGINT NOT NULL COMMENT '金融機関ID',
    product_name VARCHAR(200) NOT NULL COMMENT '商品名',
    product_code VARCHAR(50) COMMENT '商品コード',
    loan_type VARCHAR(50) NOT NULL COMMENT 'ローン種別',
    loan_category ENUM('住宅ローン', 'マイカーローン', 'カードローン', 'フリーローン', '教育ローン', 'その他') NOT NULL,
    summary TEXT COMMENT '商品概要',
    interest_rate_min DECIMAL(6,4) COMMENT '最低金利',
    interest_rate_max DECIMAL(6,4) COMMENT '最高金利',
    interest_rate_type ENUM('固定金利', '変動金利', '金利選択型') COMMENT '金利種別',
    loan_amount_min BIGINT COMMENT '最小融資額',
    loan_amount_max BIGINT COMMENT '最大融資額',
    loan_amount_unit ENUM('円', '万円') DEFAULT '円' COMMENT '金額単位',
    loan_term_min INT COMMENT '最短融資期間',
    loan_term_max INT COMMENT '最長融資期間',
    loan_term_unit ENUM('月', '年') DEFAULT '年' COMMENT '期間単位',
    repayment_methods JSON COMMENT '返済方法',
    application_requirements JSON COMMENT '申込要件',
    features JSON COMMENT '商品特徴',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    data_updated_at TIMESTAMP COMMENT 'データ更新日時',

    FOREIGN KEY (processed_data_id) REFERENCES processed_loan_data(id),
    FOREIGN KEY (institution_id) REFERENCES financial_institutions(id),
    UNIQUE KEY uk_institution_product (institution_id, product_name, loan_type),
    INDEX idx_institution_category (institution_id, loan_category),
    INDEX idx_loan_type (loan_type),
    INDEX idx_interest_rate (interest_rate_min, interest_rate_max),
    INDEX idx_loan_amount (loan_amount_min, loan_amount_max),
    FULLTEXT idx_product_search (product_name, summary)
) COMMENT '統合ローン商品テーブル';
```

### 5. ローン商品変更履歴テーブル

#### 5.1 ローン商品変更履歴

```sql
CREATE TABLE loan_product_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    loan_product_id BIGINT NOT NULL,
    changed_fields JSON NOT NULL,
    old_values JSON,
    new_values JSON,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_product_id) REFERENCES loan_products(id),
    INDEX idx_product_date (loan_product_id, changed_at),
    INDEX idx_changed_date (changed_at)
)COMMENT 'ローン商品変更履歴テーブル';
```
