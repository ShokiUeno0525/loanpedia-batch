#!/usr/bin/env python3
"""
RDS Data API 接続テストスクリプト

使用方法:
  export USE_DATA_API=true
  export DB_ARN=arn:aws:rds:ap-northeast-1:xxxx:cluster:xxxx
  export DB_SECRET_ARN=arn:aws:secretsmanager:ap-northeast-1:xxxx:secret:xxxx
  export DB_NAME=loanpedia

  python scripts/test_data_api.py
"""
import os
import sys
import logging

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_data_api_connection():
    """Data API接続テスト"""
    try:
        from loanpedia_scraper.database.rds_data_api_adapter import (
            RDSDataAPIAdapter,
        )

        logger.info("Testing RDS Data API connection...")

        # アダプター初期化
        adapter = RDSDataAPIAdapter()
        logger.info("✓ Adapter initialized successfully")

        # 接続テスト
        if adapter.connect():
            logger.info("✓ Connection test passed")
        else:
            logger.error("✗ Connection test failed")
            return False

        # 簡単なクエリ実行
        logger.info("Executing test query: SELECT 1 as test")
        response = adapter.execute_statement("SELECT 1 as test")
        logger.info(f"✓ Query executed successfully: {response}")

        # financial_institutions テーブルのカウント
        logger.info("Querying financial_institutions table...")
        response = adapter.execute_statement(
            "SELECT COUNT(*) as count FROM financial_institutions"
        )
        if response.get("records"):
            count = response["records"][0][0].get("longValue", 0)
            logger.info(f"✓ Found {count} financial institutions")
        else:
            logger.info("✓ Query executed (no records)")

        logger.info("✓ All tests passed!")
        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        logger.exception(e)
        return False


def test_database_factory():
    """データベースファクトリーのテスト"""
    try:
        from loanpedia_scraper.database.db_factory import get_database_adapter

        logger.info("Testing database factory...")

        # USE_DATA_API環境変数の確認
        use_data_api = os.getenv("USE_DATA_API", "false")
        logger.info(f"USE_DATA_API={use_data_api}")

        # アダプター取得
        db = get_database_adapter()
        logger.info(f"✓ Got adapter: {type(db).__name__}")

        # 接続テスト
        if db.connect():
            logger.info("✓ Factory connection test passed")
            db.disconnect()
            return True
        else:
            logger.error("✗ Factory connection test failed")
            return False

    except Exception as e:
        logger.error(f"✗ Factory test failed: {e}")
        logger.exception(e)
        return False


def test_save_sample_data():
    """サンプルデータ保存テスト"""
    try:
        from loanpedia_scraper.database.db_factory import get_database_adapter

        logger.info("Testing sample data save...")

        db = get_database_adapter()
        if not db.connect():
            logger.error("✗ Failed to connect")
            return False

        # テストデータ
        loan_data = {
            "institution_code": "test_code_001",
            "institution_name": "テスト金融機関",
            "source_url": "https://example.com/test",
            "product_name": "テストローン商品",
            "loan_category": "マイカーローン",
            "min_interest_rate": 0.025,
            "max_interest_rate": 0.035,
            "interest_rate_type": "変動金利",
            "min_loan_amount": 100000,
            "max_loan_amount": 5000000,
            "min_loan_period_months": 12,
            "max_loan_period_months": 84,
            "html_content": "<html><body>Test</body></html>",
            "extracted_text": "Test loan product",
            "content_hash": "test_hash_123",
        }

        # 保存実行
        saved_id = db.save_loan_data(loan_data)
        db.disconnect()

        if saved_id:
            logger.info(f"✓ Sample data saved successfully (ID={saved_id})")
            return True
        else:
            logger.error("✗ Failed to save sample data")
            return False

    except Exception as e:
        logger.error(f"✗ Sample data save test failed: {e}")
        logger.exception(e)
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("RDS Data API Test Suite")
    logger.info("=" * 60)

    # 環境変数チェック
    required_vars = ["DB_ARN", "DB_SECRET_ARN", "DB_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("\nPlease set the following environment variables:")
        logger.info("  export USE_DATA_API=true")
        logger.info("  export DB_ARN=arn:aws:rds:ap-northeast-1:xxxx:cluster:xxxx")
        logger.info(
            "  export DB_SECRET_ARN=arn:aws:secretsmanager:ap-northeast-1:xxxx:secret:xxxx"
        )
        logger.info("  export DB_NAME=loanpedia")
        sys.exit(1)

    # テスト実行
    results = []
    results.append(("Data API Connection", test_data_api_connection()))
    results.append(("Database Factory", test_database_factory()))

    # サンプルデータ保存テスト（オプション）
    if os.getenv("TEST_SAVE", "false").lower() in ("true", "1", "yes"):
        results.append(("Sample Data Save", test_save_sample_data()))

    # 結果サマリー
    logger.info("\n" + "=" * 60)
    logger.info("Test Results")
    logger.info("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)
    logger.info("=" * 60)
    if all_passed:
        logger.info("✓ All tests passed!")
        sys.exit(0)
    else:
        logger.error("✗ Some tests failed")
        sys.exit(1)
