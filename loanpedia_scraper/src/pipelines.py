# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
import hashlib
import json
from datetime import datetime
from itemadapter import ItemAdapter
import logging

logger = logging.getLogger(__name__)

class MySQLPipeline:
    def __init__(self, mysql_settings):
        self.mysql_settings = mysql_settings
        self.connection = None
        self.cursor = None
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mysql_settings=crawler.settings.getdict("DATABASE")
        )
    
    def open_spider(self, spider):
        """スパイダー開始時にデータベース接続を開く"""
        try:
            self.connection = pymysql.connect(**self.mysql_settings)
            self.connection.cursorclass = pymysql.cursors.DictCursor
            self.cursor = self.connection.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close_spider(self, spider):
        """スパイダー終了時にデータベース接続を閉じる"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def process_item(self, item, spider):
        """アイテムを処理してデータベースに保存"""
        try:
            adapter = ItemAdapter(item)
            
            # 金融機関IDを取得または作成
            institution_id = self.get_or_create_institution(
                adapter.get('institution_code', ''),
                adapter.get('institution_name', '')
            )
            
            # 生データを保存
            raw_data_id = self.save_raw_data(adapter, institution_id)
            
            # 構造化データを保存
            if raw_data_id:
                self.save_structured_data(adapter, institution_id, raw_data_id)
            
            self.connection.commit()
            logger.info(f"Item saved successfully: {adapter.get('product_name', 'Unknown')}")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error processing item: {e}")
            raise
        
        return item
    
    def get_or_create_institution(self, institution_code, institution_name):
        """金融機関マスターから ID を取得、なければ作成"""
        if not institution_code and not institution_name:
            return None
            
        # 既存の金融機関を検索
        select_sql = """
            SELECT id FROM financial_institutions 
            WHERE institution_code = %s OR institution_name = %s
            LIMIT 1
        """
        self.cursor.execute(select_sql, (institution_code, institution_name))
        result = self.cursor.fetchone()
        
        if result:
            return result['id']
        
        # 新規作成
        insert_sql = """
            INSERT INTO financial_institutions (institution_code, institution_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
        """
        now = datetime.now()
        self.cursor.execute(insert_sql, (institution_code, institution_name, now, now))
        return self.cursor.lastrowid
    
    def save_raw_data(self, adapter, institution_id):
        """生データテーブルに保存"""
        html_content = adapter.get('html_content', '')
        extracted_text = adapter.get('extracted_text', '')
        
        # コンテンツハッシュを生成
        content_hash = hashlib.sha256(html_content.encode('utf-8')).hexdigest()
        
        # 重複チェック
        check_sql = "SELECT id FROM raw_loan_data WHERE content_hash = %s"
        self.cursor.execute(check_sql, (content_hash,))
        existing = self.cursor.fetchone()
        
        if existing:
            logger.info(f"Duplicate content found, skipping: {content_hash[:8]}...")
            return existing['id']
        
        # 新規保存
        insert_sql = """
            INSERT INTO raw_loan_data (
                institution_id, source_url, page_title, html_content, 
                extracted_text, content_hash, content_length, scraped_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        scraped_at = adapter.get('scraped_at', now)
        
        self.cursor.execute(insert_sql, (
            institution_id,
            adapter.get('source_url', ''),
            adapter.get('page_title', ''),
            html_content,
            extracted_text,
            content_hash,
            len(html_content) if html_content else 0,
            scraped_at,
            now,
            now
        ))
        
        return self.cursor.lastrowid
    
    def save_structured_data(self, adapter, institution_id, raw_data_id):
        """構造化データをloan_productsテーブルに保存"""
        # AI要約データ構造を作成
        ai_summary = {
            'product_name': adapter.get('product_name'),
            'loan_category': adapter.get('loan_category'),
            'interest_rates': {
                'min': adapter.get('min_interest_rate'),
                'max': adapter.get('max_interest_rate'),
                'type': adapter.get('interest_rate_type')
            },
            'loan_amounts': {
                'min': adapter.get('min_loan_amount'),
                'max': adapter.get('max_loan_amount')
            },
            'loan_periods': {
                'min_months': adapter.get('min_loan_period_months'),
                'max_months': adapter.get('max_loan_period_months')
            },
            'requirements': {
                'min_age': adapter.get('min_age'),
                'max_age': adapter.get('max_age'),
                'income': adapter.get('income_requirement'),
                'guarantor_required': adapter.get('guarantor_required')
            },
            'features': adapter.get('features'),
            'documents': adapter.get('required_documents'),
            'application_method': adapter.get('application_method'),
            'repayment_method': adapter.get('repayment_method')
        }
        
        # processed_loan_dataテーブルに保存
        processed_sql = """
            INSERT INTO processed_loan_data (
                raw_data_id, institution_id, ai_summary, ai_model, 
                processing_status, processed_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        self.cursor.execute(processed_sql, (
            raw_data_id,
            institution_id,
            json.dumps(ai_summary, ensure_ascii=False),
            'scrapy_parser_v1.0',
            'completed',
            now,
            now,
            now
        ))
        
        processed_id = self.cursor.lastrowid
        
        # loan_productsテーブルに保存
        product_sql = """
            INSERT INTO loan_products (
                processed_data_id, institution_id, product_name, loan_type, loan_category,
                interest_rate_min, interest_rate_max, interest_rate_type,
                loan_amount_min, loan_amount_max, loan_term_min, loan_term_max,
                repayment_methods, application_requirements, features,
                created_at, updated_at, data_updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                interest_rate_min = VALUES(interest_rate_min),
                interest_rate_max = VALUES(interest_rate_max),
                loan_amount_min = VALUES(loan_amount_min),
                loan_amount_max = VALUES(loan_amount_max),
                updated_at = VALUES(updated_at),
                data_updated_at = VALUES(data_updated_at)
        """
        
        # 期間を年に変換（月から）
        min_term_years = None
        max_term_years = None
        if adapter.get('min_loan_period_months'):
            min_term_years = int(adapter.get('min_loan_period_months') / 12)
        if adapter.get('max_loan_period_months'):
            max_term_years = int(adapter.get('max_loan_period_months') / 12)
        
        # JSONフィールドの準備
        repayment_methods = json.dumps([adapter.get('repayment_method')] if adapter.get('repayment_method') else [])
        requirements = json.dumps(ai_summary['requirements'])
        features_json = json.dumps([adapter.get('features')] if adapter.get('features') else [])
        
        self.cursor.execute(product_sql, (
            processed_id,
            institution_id,
            adapter.get('product_name', ''),
            adapter.get('loan_category', ''),
            adapter.get('loan_category', ''),
            adapter.get('min_interest_rate'),
            adapter.get('max_interest_rate'),
            adapter.get('interest_rate_type'),
            adapter.get('min_loan_amount'),
            adapter.get('max_loan_amount'),
            min_term_years,
            max_term_years,
            repayment_methods,
            requirements,
            features_json,
            now,
            now,
            now
        ))
        
        return self.cursor.lastrowid

class LoanpediaScraperPipeline:
    def process_item(self, item, spider):
        return item
