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
    """生データ保存専用パイプライン"""
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
        """生データのみをデータベースに保存（AI処理は別バッチで実行）"""
        try:
            adapter = ItemAdapter(item)
            
            # 金融機関IDを取得または作成
            institution_id = self.get_or_create_institution(
                adapter.get('institution_code', ''),
                adapter.get('institution_name', '')
            )
            
            # 生データのみ保存
            raw_data_id = self.save_raw_data(adapter, institution_id)
            
            self.connection.commit()
            logger.info(f"Raw data saved: {adapter.get('source_url', 'Unknown URL')} -> ID: {raw_data_id}")
            
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
        """生データテーブルに保存（構造化抽出結果もJSONで保存）"""
        html_content = adapter.get('html_content', '')
        
        # Scrapyで抽出した構造化データを保存（AI処理前の状態）
        structured_data = {
            'product_name': adapter.get('product_name'),
            'loan_category': adapter.get('loan_category'),
            'min_interest_rate': adapter.get('min_interest_rate'),
            'max_interest_rate': adapter.get('max_interest_rate'),
            'min_loan_amount': adapter.get('min_loan_amount'),
            'max_loan_amount': adapter.get('max_loan_amount'),
            'min_loan_period_months': adapter.get('min_loan_period_months'),
            'max_loan_period_months': adapter.get('max_loan_period_months'),
            'guarantor_fee': adapter.get('guarantor_fee'),
            'application_conditions': adapter.get('application_conditions'),
            'repayment_method': adapter.get('repayment_method'),
            'prepayment_fee': adapter.get('prepayment_fee'),
            'application_method': adapter.get('application_method'),
            'required_documents': adapter.get('required_documents'),
            'guarantor_info': adapter.get('guarantor_info'),
            'collateral_info': adapter.get('collateral_info')
        }
        
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
                structured_data, content_hash, content_length, scraped_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        scraped_at = adapter.get('scraped_at', now)
        
        self.cursor.execute(insert_sql, (
            institution_id,
            adapter.get('source_url', ''),
            adapter.get('page_title', ''),
            html_content,
            json.dumps(structured_data, ensure_ascii=False),
            content_hash,
            len(html_content) if html_content else 0,
            scraped_at,
            now,
            now
        ))
        
        return self.cursor.lastrowid
    

class LoanpediaScraperPipeline:
    def process_item(self, item, spider):
        return item
