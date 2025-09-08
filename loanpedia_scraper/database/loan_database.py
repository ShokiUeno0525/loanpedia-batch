"""
ローンデータベース操作ライブラリ（BeautifulSoupスクレイパー用）

Scrapyパイプラインの機能をBeautifulSoupスクレイパーで使用できるよう移植
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any, cast, TYPE_CHECKING

try:
    import pymysql
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False
    pymysql = cast(Any, None)

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
        # 明示的な属性型（mypy対策）
        self.connection: Optional[Any] = None
        self.cursor: Optional[Any] = None
        
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
    
    def __enter__(self) -> Optional["LoanDatabase"]:
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

            # 明示的にコミット（コンテキスト外利用時の未コミット対策）
            try:
                if self.connection:
                    self.connection.commit()
                    logger.info(
                        f"Committed loan data: {loan_data.get('source_url', 'Unknown URL')} -> ID: {raw_data_id}"
                    )
            except Exception as ce:
                logger.error(f"Commit failed, rolling back: {ce}")
                if self.connection:
                    self.connection.rollback()
                return None

            logger.info(
                f"Loan data saved: {loan_data.get('source_url', 'Unknown URL')} -> ID: {raw_data_id}"
            )

            return raw_data_id
            
        except Exception as e:
            logger.error(f"Error saving loan data: {e}")
            if self.connection:
                self.connection.rollback()
            return None
    
    def get_or_create_institution(self, institution_code: str, institution_name: str, institution_name_kana: str = '') -> Optional[int]:
        """金融機関マスターからIDを取得、なければ作成"""
        if not institution_code and not institution_name:
            return None
            
        # 既存の金融機関を検索
        assert self.cursor is not None
        select_sql = """
            SELECT id FROM financial_institutions 
            WHERE institution_code = %s OR institution_name = %s
            LIMIT 1
        """
        self.cursor.execute(select_sql, (institution_code, institution_name))
        result = self.cursor.fetchone()
        
        if result:
            return int(cast(Any, result['id']))
        
        # 新規作成
        insert_sql = """
            INSERT INTO financial_institutions (institution_code, institution_name, institution_name_kana, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        now = datetime.now()
        self.cursor.execute(insert_sql, (institution_code, institution_name, institution_name_kana, now, now))
        return int(cast(Any, self.cursor.lastrowid))
    
    def save_raw_data(self, loan_data: Dict[str, Any], institution_id: Optional[int]) -> int:
        """生データテーブルに保存"""
        assert self.cursor is not None
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

            # 更新時も明示コミット
            try:
                if self.connection:
                    self.connection.commit()
                    logger.info(
                        f"Committed update for existing raw_loan_data ID: {existing['id']}"
                    )
            except Exception as ce:
                logger.error(f"Commit failed after update, rolling back: {ce}")
                if self.connection:
                    self.connection.rollback()
                raise

            return int(cast(Any, existing['id']))
        
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
        
        return int(cast(Any, self.cursor.lastrowid))
    
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
        fetched = self.cursor.fetchone()
        return cast(Optional[Dict[str, Any]], fetched)
    
    def get_all_institutions(self):
        """すべての金融機関を取得"""
        if not self.connection or not self.cursor:
            return []
            
        sql = "SELECT * FROM financial_institutions ORDER BY institution_name"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def save_structured_loan_data(self, scraper_result: Dict[str, Any]) -> Dict[str, int]:
        """新しいテーブル構造に対応したローンデータ保存"""
        assert self.cursor is not None
        
        saved_ids = {
            'raw_data_ids': [],
            'processed_data_ids': [],
            'loan_product_ids': []
        }
        
        try:
            # 1. 金融機関の取得/作成
            institution_id = self.get_or_create_institution(
                scraper_result['institution_code'],
                scraper_result['institution_name'],
                scraper_result.get('institution_name_kana', '')
            )
            
            # 2. 各商品の処理
            for product in scraper_result.get('products', []):
                # 生データ保存 (raw_loan_data)
                raw_data_id = self._save_raw_loan_data_new(product, institution_id)
                saved_ids['raw_data_ids'].append(raw_data_id)
                
                # AI処理済みデータ保存 (processed_loan_data)
                processed_data_id = self._save_processed_loan_data(product, raw_data_id, institution_id)
                saved_ids['processed_data_ids'].append(processed_data_id)
                
                # ローン商品保存 (loan_products)
                loan_product_id = self._save_loan_product(product, processed_data_id, institution_id)
                saved_ids['loan_product_ids'].append(loan_product_id)
            
            # コミット
            if self.connection:
                self.connection.commit()
                logger.info(f"Successfully saved structured loan data: {saved_ids}")
            
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Error saving structured loan data: {e}")
            raise
        
        return saved_ids
    
    def _save_raw_loan_data_new(self, product_data: Dict[str, Any], institution_id: int) -> int:
        """新テーブル構造での生データ保存"""
        assert self.cursor is not None
        
        # 構造化データ準備
        structured_data = {
            'product_name': product_data.get('product_name'),
            'min_interest_rate': product_data.get('min_interest_rate'),
            'max_interest_rate': product_data.get('max_interest_rate'),
            'min_loan_term_months': product_data.get('min_loan_term_months'),
            'max_loan_term_months': product_data.get('max_loan_term_months'),
            'source_url': product_data.get('source_url'),
            'scraping_status': product_data.get('scraping_status'),
        }
        
        # コンテンツハッシュ生成
        content_str = json.dumps(structured_data, sort_keys=True, ensure_ascii=False)
        content_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        
        # 重複チェック
        check_sql = """
            SELECT id FROM raw_loan_data 
            WHERE content_hash = %s AND institution_id = %s
        """
        self.cursor.execute(check_sql, (content_hash, institution_id))
        existing = self.cursor.fetchone()
        
        if existing:
            logger.info(f"Raw data already exists: {existing['id']}")
            return int(existing['id'])
        
        # 新規挿入
        insert_sql = """
            INSERT INTO raw_loan_data (
                institution_id, source_url, page_title, html_content,
                extracted_text, structured_data, content_hash, content_length,
                http_status, scraped_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        scraped_at_str = product_data.get('scraped_at')
        scraped_at = datetime.fromisoformat(scraped_at_str) if scraped_at_str else now
        
        self.cursor.execute(insert_sql, (
            institution_id,
            product_data.get('source_url', ''),
            product_data.get('product_name', ''),
            '',  # html_content - 必要に応じて追加
            json.dumps(structured_data, ensure_ascii=False),  # extracted_text
            json.dumps(structured_data, ensure_ascii=False),  # structured_data
            content_hash,
            len(content_str),
            200,  # http_status
            scraped_at
        ))
        
        return int(self.cursor.lastrowid)
    
    def _save_processed_loan_data(self, product_data: Dict[str, Any], raw_data_id: int, institution_id: int) -> int:
        """AI処理済みデータ保存"""
        assert self.cursor is not None
        
        # AI要約データ準備
        ai_summary = {
            'product_name': product_data.get('product_name'),
            'loan_type': 'car_loan',  # マイカーローン
            'interest_rates': {
                'min': product_data.get('min_interest_rate'),
                'max': product_data.get('max_interest_rate'),
                'type': 'variable'  # 推定
            },
            'loan_terms': {
                'min_months': product_data.get('min_loan_term_months'),
                'max_months': product_data.get('max_loan_term_months')
            },
            'source_url': product_data.get('source_url'),
            'extraction_method': 'web_scraping'
        }
        
        insert_sql = """
            INSERT INTO processed_loan_data (
                raw_data_id, institution_id, ai_summary, ai_model,
                processing_version, processing_status, validation_status, processed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        self.cursor.execute(insert_sql, (
            raw_data_id,
            institution_id,
            json.dumps(ai_summary, ensure_ascii=False),
            'web_scraper_v1',
            '1.0',
            'completed',
            'valid',
            datetime.now()
        ))
        
        return int(self.cursor.lastrowid)
    
    def _save_loan_product(self, product_data: Dict[str, Any], processed_data_id: int, institution_id: int) -> int:
        """ローン商品保存"""
        assert self.cursor is not None
        
        # 重複チェック
        check_sql = """
            SELECT id FROM loan_products 
            WHERE institution_id = %s AND product_name = %s AND loan_type = %s
        """
        product_name = product_data.get('product_name', '自動車ローン')
        loan_type = 'car_loan'
        
        self.cursor.execute(check_sql, (institution_id, product_name, loan_type))
        existing = self.cursor.fetchone()
        
        if existing:
            # 既存データを更新
            update_sql = """
                UPDATE loan_products SET
                    processed_data_id = %s,
                    interest_rate_min = %s,
                    interest_rate_max = %s,
                    loan_term_min = %s,
                    loan_term_max = %s,
                    loan_term_unit = %s,
                    data_updated_at = %s,
                    updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_sql, (
                processed_data_id,
                product_data.get('min_interest_rate'),
                product_data.get('max_interest_rate'),
                product_data.get('min_loan_term_months'),
                product_data.get('max_loan_term_months'),
                '月',
                datetime.now(),
                datetime.now(),
                existing['id']
            ))
            return int(existing['id'])
        
        # 新規挿入
        insert_sql = """
            INSERT INTO loan_products (
                processed_data_id, institution_id, product_name, loan_type, loan_category,
                summary, interest_rate_min, interest_rate_max, interest_rate_type,
                loan_term_min, loan_term_max, loan_term_unit, data_updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        self.cursor.execute(insert_sql, (
            processed_data_id,
            institution_id,
            product_name,
            loan_type,
            'マイカーローン',
            f'{product_name}（金利: {product_data.get("min_interest_rate", 0)}%〜{product_data.get("max_interest_rate", 0)}%）',
            product_data.get('min_interest_rate'),
            product_data.get('max_interest_rate'),
            '変動金利',  # 推定
            product_data.get('min_loan_term_months'),
            product_data.get('max_loan_term_months'),
            '月',
            datetime.now()
        ))
        
        return int(self.cursor.lastrowid)


# データベース設定のデフォルト値（パッケージ内: コンテナ/Lambda想定）
DEFAULT_DB_CONFIG: Dict[str, Any] = {
    'host': 'mysql',
    'user': 'app_user',
    'password': 'app_password',
    'database': 'app_db',
    'port': 3306,
    'charset': 'utf8mb4'
}


def get_database_config() -> Dict[str, Any]:
    """環境変数またはデフォルト設定からデータベース設定を取得

    許容する環境変数のキー（優先順）:
      - DB_NAME / DB_DATABASE / MYSQL_DATABASE
      - DB_USER / DB_USERNAME / MYSQL_USER
      - DB_PASSWORD / MYSQL_PASSWORD
      - DB_HOST / MYSQL_HOST
      - DB_PORT / MYSQL_PORT
      - DB_CHARSET
    """
    import os

    host = (
        os.getenv('DB_HOST')
        or os.getenv('MYSQL_HOST')
        or DEFAULT_DB_CONFIG['host']
    )
    user = (
        os.getenv('DB_USER')
        or os.getenv('DB_USERNAME')
        or os.getenv('MYSQL_USER')
        or DEFAULT_DB_CONFIG['user']
    )
    password = (
        os.getenv('DB_PASSWORD')
        or os.getenv('MYSQL_PASSWORD')
        or DEFAULT_DB_CONFIG['password']
    )
    database = (
        os.getenv('DB_NAME')
        or os.getenv('DB_DATABASE')
        or os.getenv('MYSQL_DATABASE')
        or DEFAULT_DB_CONFIG['database']
    )
    port_env = os.getenv('DB_PORT') or os.getenv('MYSQL_PORT')
    try:
        port = int(port_env) if port_env else cast(int, DEFAULT_DB_CONFIG['port'])
    except Exception:
        port = cast(int, DEFAULT_DB_CONFIG['port'])
    # 余分な空白を除去（Windowsの set で末尾スペースが入る事故対策）
    host = str(host).strip()
    user = str(user).strip()
    password = str(password).strip()
    database = str(database).strip()

    charset = os.getenv('DB_CHARSET', DEFAULT_DB_CONFIG['charset']).strip()

    return {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': port,
        'charset': charset,
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
