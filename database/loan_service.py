"""
DB保存サービス層

ハンドラーから直接DB設定や接続処理を行わないためのユーティリティ。
環境変数から設定を集約し、リトライやデータ整形もここで行う。
"""

from typing import Dict, Any
import os
import time
import logging
from datetime import datetime

from .loan_database import LoanDatabase, get_database_config

logger = logging.getLogger(__name__)


def save_scraped_product(
    institution_code: str,
    institution_name: str,
    product_data: Dict[str, Any],
    raw_data_dict: Dict[str, Any],
) -> bool:
    """
    スクレイピング結果をDBへ保存（環境変数に基づきスキップ/リトライ）
    """
    save_to_db = os.getenv("SAVE_TO_DB", "true").lower()
    if save_to_db not in ("true", "1", "yes"):
        logger.info("SAVE_TO_DB is disabled, skipping database save")
        return True

    if os.getenv("DEBUG_SKIP_DB", "false").lower() in ("true", "1", "yes"):
        logger.info("DEBUG_SKIP_DB is enabled, skipping database save for debugging")
        return True

    # DB設定の取得（フォールバック込み）
    db_config = get_database_config()

    # リトライ設定
    retry_max = int(os.getenv("DB_RETRY_MAX", "5"))
    base_delay = float(os.getenv("DB_RETRY_BASE_DELAY", "1.0"))

    # LoanDatabaseの期待する形式に整形
    loan_data = {
        'institution_code': institution_code,
        'institution_name': institution_name,
        'source_url': raw_data_dict.get('source_url', product_data.get('source_reference', '')),
        'html_content': raw_data_dict.get('html_content', ''),
        'extracted_text': raw_data_dict.get('extracted_text', ''),
        'content_hash': raw_data_dict.get('content_hash', ''),
        'scraping_status': 'success',
        'scraped_at': datetime.now().isoformat(),
        'product_name': product_data.get('product_name'),
        'loan_type': product_data.get('loan_type'),
        'category': product_data.get('category'),
        'min_interest_rate': product_data.get('min_interest_rate'),
        'max_interest_rate': product_data.get('max_interest_rate'),
        'interest_type': product_data.get('interest_type'),
        'min_loan_amount': product_data.get('min_loan_amount'),
        'max_loan_amount': product_data.get('max_loan_amount'),
        'min_loan_term': product_data.get('min_loan_term'),
        'max_loan_term': product_data.get('max_loan_term'),
        'repayment_method': product_data.get('repayment_method'),
        'min_age': product_data.get('min_age'),
        'max_age': product_data.get('max_age'),
        'special_features': product_data.get('special_features'),
    }

    # 接続・保存（指数バックオフ）
    for attempt in range(retry_max):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info(f"Waiting {delay} seconds before retry {attempt + 1}")
                time.sleep(delay)

            db = LoanDatabase(db_config)
            if not db.connect():
                logger.warning(f"Database connection attempt {attempt + 1} failed (returned False)")
                continue

            try:
                saved_id = db.save_loan_data(loan_data)
                db.disconnect()
                if saved_id:
                    logger.info(f"Successfully saved to database (raw_loan_data ID={saved_id})")
                    return True
                else:
                    logger.error("Save returned None/False; will retry if attempts remain")
            except Exception:
                logger.exception("Save operation failed; will retry if attempts remain")
            finally:
                try:
                    db.disconnect()
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Database attempt {attempt + 1} failed with exception: {e}")

    logger.error("All database save attempts failed")
    return False

