"""
ローンデータベース操作ライブラリ（BeautifulSoupスクレイパー用）

Scrapyパイプラインの機能をBeautifulSoupスクレイパーで使用できるよう移植
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    pymysql = None

logger = logging.getLogger(__name__)


class LoanDatabase:
    """ローンデータベース操作クラス"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初期化
        
        Args:
            db_config: データベース接続設定
                {
                    'host': 'localhost',
                    'user': 'root', 
                    'password': 'password',
                    'database': 'app_db',
                    'port': 3306,
                    'charset': 'utf8mb4'
                }
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
        if not PYMYSQL_AVAILABLE:
            logger.warning("pymysql not available, database operations will be skipped")
    
    def connect(self) -> bool:
        """データベースに接続"""
        if not PYMYSQL_AVAILABLE:
            logger.warning("pymysql not available, cannot connect to database")
            return False
            
        try:
            # cursorclassを接続時に設定
            config = self.db_config.copy()
            config['cursorclass'] = pymysql.cursors.DictCursor
            
            self.connection = pymysql.connect(**config)
            self.cursor = self.connection.cursor()
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """データベース接続を切断"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def __enter__(self):
        """コンテキストマネージャーの開始"""
        if self.connect():
            return self
        else:
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了"""
        if exc_type:
            if self.connection:
                self.connection.rollback()
                logger.error(f"Database transaction rolled back due to error: {exc_val}")
        else:
            if self.connection:
                self.connection.commit()
        self.disconnect()
    
    def save_loan_data(self, loan_data: Dict[str, Any]) -> Optional[int]:
        """
        ローンデータを保存
        
        Args:
            loan_data: スクレイピングで取得したローンデータ
            
        Returns:
            保存されたraw_loan_dataのID、失敗時はNone
        """
        if not self.connection or not self.cursor:
            logger.warning("Database not connected, skipping save")
            return None
        
        try:
            # 金融機関IDを取得または作成
            institution_id = self.get_or_create_institution(
                loan_data.get('institution_code', ''),
                loan_data.get('institution_name', '')
            )
            
            # 生データを保存
            raw_data_id = self.save_raw_data(loan_data, institution_id)
            
            logger.info(f"Loan data saved: {loan_data.get('source_url', 'Unknown URL')} -> ID: {raw_data_id}")
            
            return raw_data_id
            
        except Exception as e:
            logger.error(f"Error saving loan data: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def get_or_create_institution(self, institution_code: str, institution_name: str) -> Optional[int]:
        """金融機関マスターからIDを取得、なければ作成"""
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
    
    def save_raw_data(self, loan_data: Dict[str, Any], institution_id: Optional[int]) -> int:
        """生データテーブルに保存"""
        html_content = loan_data.get('html_content', '')
        
        # 構造化データを準備
        structured_data = {
            'product_name': loan_data.get('product_name'),
            'loan_category': loan_data.get('loan_category'),
            'min_interest_rate': loan_data.get('min_interest_rate'),
            'max_interest_rate': loan_data.get('max_interest_rate'),
            'interest_rate_type': loan_data.get('interest_rate_type'),
            'min_loan_amount': loan_data.get('min_loan_amount'),
            'max_loan_amount': loan_data.get('max_loan_amount'),
            'min_loan_period_months': loan_data.get('min_loan_period_months'),
            'max_loan_period_months': loan_data.get('max_loan_period_months'),
            'min_age': loan_data.get('min_age'),
            'max_age': loan_data.get('max_age'),
            'guarantor_fee': loan_data.get('guarantor_fee'),
            'handling_fee': loan_data.get('handling_fee'),
            'prepayment_fee': loan_data.get('prepayment_fee'),
            'application_conditions': loan_data.get('application_conditions'),
            'repayment_method': loan_data.get('repayment_method'),
            'application_method': loan_data.get('application_method'),
            'required_documents': loan_data.get('required_documents'),
            'guarantor_info': loan_data.get('guarantor_info'),
            'guarantor_required': loan_data.get('guarantor_required'),
            'collateral_info': loan_data.get('collateral_info'),
            'features': loan_data.get('features')
        }
        
        # コンテンツハッシュを生成
        content_hash = hashlib.sha256(html_content.encode('utf-8')).hexdigest()
        
        # 重複チェック
        check_sql = "SELECT id FROM raw_loan_data WHERE content_hash = %s"
        self.cursor.execute(check_sql, (content_hash,))
        existing = self.cursor.fetchone()
        
        if existing:
            logger.info(f"Duplicate content found, updating: {content_hash[:8]}...")
            # 既存データを更新
            update_sql = """
                UPDATE raw_loan_data SET
                    structured_data = %s,
                    updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_sql, (
                json.dumps(structured_data, ensure_ascii=False),
                datetime.now(),
                existing['id']
            ))
            return existing['id']
        
        # 新規保存
        insert_sql = """
            INSERT INTO raw_loan_data (
                institution_id, source_url, page_title, html_content, 
                structured_data, content_hash, content_length, scraped_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        scraped_at_str = loan_data.get('scraped_at')
        if scraped_at_str:
            try:
                scraped_at = datetime.fromisoformat(scraped_at_str)
            except:
                scraped_at = now
        else:
            scraped_at = now
        
        self.cursor.execute(insert_sql, (
            institution_id,
            loan_data.get('source_url', ''),
            loan_data.get('page_title', ''),
            html_content,
            json.dumps(structured_data, ensure_ascii=False),
            content_hash,
            len(html_content) if html_content else 0,
            scraped_at,
            now,
            now
        ))
        
        return self.cursor.lastrowid
    
    def get_latest_data_by_institution(self, institution_code: str) -> Optional[Dict[str, Any]]:
        """指定金融機関の最新データを取得"""
        if not self.connection or not self.cursor:
            return None
            
        sql = """
            SELECT rld.*, fi.institution_name, fi.institution_code
            FROM raw_loan_data rld
            JOIN financial_institutions fi ON rld.institution_id = fi.id
            WHERE fi.institution_code = %s
            ORDER BY rld.created_at DESC
            LIMIT 1
        """
        
        self.cursor.execute(sql, (institution_code,))
        return self.cursor.fetchone()
    
    def get_all_institutions(self):
        """すべての金融機関を取得"""
        if not self.connection or not self.cursor:
            return []
            
        sql = "SELECT * FROM financial_institutions ORDER BY institution_name"
        self.cursor.execute(sql)
        return self.cursor.fetchall()


# データベース設定のデフォルト値
DEFAULT_DB_CONFIG = {
    'host': 'mysql',
    'user': 'app_user',
    'password': 'app_password',
    'database': 'app_db',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 60,
    'read_timeout': 30,
    'write_timeout': 30,
    'autocommit': True,
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    'local_infile': False,
    'use_unicode': True,
    'max_allowed_packet': 16777216
}


def get_database_config() -> Dict[str, Any]:
    """環境変数またはデフォルト設定からデータベース設定を取得"""
    import os
    
    return {
        'host': os.getenv('DB_HOST', DEFAULT_DB_CONFIG['host']),
        'user': os.getenv('DB_USER', DEFAULT_DB_CONFIG['user']),
        'password': os.getenv('DB_PASSWORD', DEFAULT_DB_CONFIG['password']),
        'database': os.getenv('DB_NAME', DEFAULT_DB_CONFIG['database']),
        'port': int(os.getenv('DB_PORT', DEFAULT_DB_CONFIG['port'])),
        'charset': os.getenv('DB_CHARSET', DEFAULT_DB_CONFIG['charset'])
    }


def test_database_connection():
    """データベース接続テスト"""
    config = get_database_config()
    
    with LoanDatabase(config) as db:
        if db:
            print("✅ データベース接続テスト成功")
            
            # 金融機関一覧を取得してテスト
            institutions = db.get_all_institutions()
            print(f"登録済み金融機関数: {len(institutions)}")
            
            for inst in institutions:
                print(f"  - {inst['institution_name']} ({inst['institution_code']})")
                
        else:
            print("❌ データベース接続テスト失敗")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    test_database_connection()