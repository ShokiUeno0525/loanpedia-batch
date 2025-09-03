"""
DB保存サービス層（パッケージ内）
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
    save_to_db = os.getenv("SAVE_TO_DB", "true").lower()
    if save_to_db not in ("true", "1", "yes"):
        logger.info("SAVE_TO_DB is disabled, skipping database save")
        return True

    if os.getenv("DEBUG_SKIP_DB", "false").lower() in ("true", "1", "yes"):
        logger.info("DEBUG_SKIP_DB is enabled, skipping database save for debugging")
        return True

    db_config = get_database_config()

    retry_max = int(os.getenv("DB_RETRY_MAX", "5"))
    base_delay = float(os.getenv("DB_RETRY_BASE_DELAY", "1.0"))

    def _normalize(pd: Dict[str, Any]) -> Dict[str, Any]:
        """スクレイパーごとの差異を統一キーへ正規化"""
        loan_category = pd.get('loan_category') or pd.get('category') or pd.get('loan_type')
        interest_rate_type = pd.get('interest_rate_type') or pd.get('interest_type')
        min_period = (
            pd.get('min_loan_period_months')
            or pd.get('min_loan_term_months')
            or pd.get('min_loan_term')
        )
        max_period = (
            pd.get('max_loan_period_months')
            or pd.get('max_loan_term_months')
            or pd.get('max_loan_term')
        )
        features = pd.get('features') or pd.get('special_features')

        return {
            'product_name': pd.get('product_name'),
            'loan_category': loan_category,
            'min_interest_rate': pd.get('min_interest_rate'),
            'max_interest_rate': pd.get('max_interest_rate'),
            'interest_rate_type': interest_rate_type,
            'min_loan_amount': pd.get('min_loan_amount'),
            'max_loan_amount': pd.get('max_loan_amount'),
            'min_loan_period_months': min_period,
            'max_loan_period_months': max_period,
            'min_age': pd.get('min_age'),
            'max_age': pd.get('max_age'),
            'repayment_method': pd.get('repayment_method'),
            'application_conditions': pd.get('application_conditions'),
            'application_method': pd.get('application_method'),
            'required_documents': pd.get('required_documents'),
            'guarantor_info': pd.get('guarantor_info'),
            'guarantor_required': pd.get('guarantor_required'),
            'collateral_info': pd.get('collateral_info'),
            'features': features,
        }

    norm = _normalize(product_data or {})

    # 互換目的で一部の別名も同梱（呼び出し側が旧キーで参照しても値があるように）
    loan_data = {
        'institution_code': institution_code,
        'institution_name': institution_name,
        'source_url': raw_data_dict.get('source_url', product_data.get('source_reference', '')),
        'html_content': raw_data_dict.get('html_content', ''),
        'extracted_text': raw_data_dict.get('extracted_text', ''),
        'content_hash': raw_data_dict.get('content_hash', ''),
        'scraping_status': 'success',
        'scraped_at': datetime.now().isoformat(),
        # 統一キー
        **norm,
        # 旧別名（必要に応じて）
        'category': norm['loan_category'],
        'interest_type': norm['interest_rate_type'],
        'min_loan_term': norm['min_loan_period_months'],
        'max_loan_term': norm['max_loan_period_months'],
        'special_features': norm['features'],
    }

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
                    # 主要項目を整形してログ出力
                    def _fmt(v, suf: str = "") -> str:
                        return (str(v) + suf) if v is not None and v != "" else "-"

                    def _fmt_percent(v) -> str:
                        if v is None or v == "":
                            return "-"
                        try:
                            pct = round(float(v) * 100.0, 3)  # 小数点第3位まで
                            s = f"{pct:.3f}".rstrip("0").rstrip(".")
                            return s + "%"
                        except Exception:
                            return _fmt(v)

                    # ログは統一キーを使用
                    features = loan_data.get('features')
                    if isinstance(features, (list, tuple)):
                        features_str = ", ".join([str(x) for x in features]) if features else "-"
                    else:
                        features_str = str(features) if features else "-"

                    logger.info(
                        "Saved elements | product=%s | interest=%s-%s (%s) | amount=%s-%s 円 | term=%s-%s ヶ月 | ages=%s-%s 歳 | repayment=%s | features=%s | conditions=%s | url=%s | id=%s",
                        _fmt(loan_data.get('product_name')),
                        _fmt_percent(loan_data.get('min_interest_rate')),
                        _fmt_percent(loan_data.get('max_interest_rate')),
                        _fmt(loan_data.get('interest_rate_type')),
                        _fmt(loan_data.get('min_loan_amount')),
                        _fmt(loan_data.get('max_loan_amount')),
                        _fmt(loan_data.get('min_loan_period_months')),
                        _fmt(loan_data.get('max_loan_period_months')),
                        _fmt(loan_data.get('min_age')),
                        _fmt(loan_data.get('max_age')),
                        _fmt(loan_data.get('repayment_method')),
                        features_str,
                        _fmt(loan_data.get('application_conditions')),
                        _fmt(loan_data.get('source_url')),
                        saved_id,
                    )
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
