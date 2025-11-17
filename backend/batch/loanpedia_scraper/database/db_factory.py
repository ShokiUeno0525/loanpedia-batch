"""
データベースファクトリー

環境変数に基づいて適切なデータベースアダプター（PyMySQL or Data API）を返す
"""
import logging
import os

logger = logging.getLogger(__name__)


def get_database_adapter():
    """
    環境変数 USE_DATA_API に基づいてデータベースアダプターを返す

    Returns:
        LoanDatabase または RDSDataAPIAdapter のインスタンス
    """
    use_data_api = os.getenv("USE_DATA_API", "false").lower() in ("true", "1", "yes")

    if use_data_api:
        logger.info("Using RDS Data API adapter")
        try:
            from loanpedia_scraper.database.rds_data_api_adapter import (
                RDSDataAPIAdapter,
            )

            return RDSDataAPIAdapter()
        except ImportError:
            # フォールバック用の相対インポート
            from database.rds_data_api_adapter import RDSDataAPIAdapter  # type: ignore

            return RDSDataAPIAdapter()
    else:
        logger.info("Using PyMySQL adapter (LoanDatabase)")
        try:
            from loanpedia_scraper.database.loan_database import LoanDatabase
            from loanpedia_scraper.database.db_config import get_database_config

            db_config = get_database_config()
            return LoanDatabase(db_config)
        except ImportError:
            # フォールバック用の相対インポート
            from database.loan_database import LoanDatabase  # type: ignore
            from database.db_config import get_database_config  # type: ignore

            db_config = get_database_config()
            return LoanDatabase(db_config)
