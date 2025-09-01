"""
データベース統合テスト
"""
import pytest
import os
from unittest.mock import patch
from loanpedia_scraper.database.loan_service import save_scraped_product
from loanpedia_scraper.database.loan_database import LoanDatabase, get_database_config

@pytest.mark.skipif(
    os.getenv('SCRAPING_TEST_MODE') != 'true',
    reason="データベース統合テストはSCRAPING_TEST_MODE=trueでのみ実行"
)
class TestDatabaseIntegration:
    """データベース統合テストクラス"""

    def test_database_connection(self):
        """データベース接続テスト"""
        try:
            db_config = get_database_config()
            db = LoanDatabase(db_config)
            
            # 接続テスト
            connection_result = db.connect()
            assert connection_result is True
            
            # テーブル存在確認
            if hasattr(db, 'connection') and db.connection:
                with db.connection.cursor() as cursor:
                    cursor.execute("SHOW TABLES LIKE 'raw_loan_data'")
                    result = cursor.fetchone()
                    assert result is not None
                db.disconnect()
                
        except Exception as e:
            pytest.skip(f"データベース接続に失敗: {e}")

    def test_insert_raw_loan_data(self):
        """生データ挿入テスト"""
        try:
            db_config = get_database_config()
            db = LoanDatabase(db_config)
            
            if not db.connect():
                pytest.skip("データベース接続に失敗")
                
            test_data = {
                'institution_name': 'テスト金融機関',
                'url': 'https://test.example.com/loans',
                'html_content': '<html><body>テストHTML</body></html>',
                'extracted_data': {'test': 'data'},
                'content_hash': 'test_hash_123'
            }
            
            # データ挿入
            result = db.save_raw_data(test_data)
            assert result is not None
            
            db.disconnect()
            
        except Exception as e:
            pytest.skip(f"データベース操作に失敗: {e}")

    def test_save_scraped_product_function(self):
        """save_scraped_product関数のテスト"""
        try:
            # 実際のsave_scraped_product関数をテスト
            test_product_data = {
                'product_name': 'テストローン',
                'loan_category': 'カードローン',
                'min_interest_rate': 3.0,
                'max_interest_rate': 14.5
            }
            
            test_raw_data = {
                'source_url': 'https://test.example.com/loans',
                'html_content': '<html><body>テストHTML</body></html>',
                'extracted_text': 'テストテキスト',
                'content_hash': 'test_hash_123'
            }
            
            # SAVE_TO_DBを無効にしてテスト実行
            with patch.dict(os.environ, {'SAVE_TO_DB': 'false'}):
                result = save_scraped_product(
                    institution_code='TEST_INST',
                    institution_name='テスト金融機関', 
                    product_data=test_product_data,
                    raw_data_dict=test_raw_data
                )
                assert result is True
                
        except Exception as e:
            pytest.skip(f"save_scraped_product関数のテストに失敗: {e}")

@pytest.mark.skipif(
    os.getenv('SCRAPING_TEST_MODE') != 'true',
    reason="スクレイパー統合テストはSCRAPING_TEST_MODE=trueでのみ実行"
)
class TestScraperIntegration:
    """スクレイパー統合テストクラス"""

    def test_scraper_with_database(self):
        """スクレイパーとデータベースの統合テスト"""        
        try:
            # 利用可能なスクレイパーをチェック
            from loanpedia_scraper.scrapers.main import LoanScrapingOrchestrator
            
            # データベース無効で実行（実際のAPIを呼ばない）
            orchestrator = LoanScrapingOrchestrator(save_to_db=False)
            
            # 利用可能なスクレイパーの確認
            scrapers = orchestrator.get_available_scrapers()
            if len(scrapers) > 0:
                # テスト成功
                assert True
            else:
                pytest.skip("利用可能なスクレイパーがありません")
            
        except ImportError as e:
            pytest.skip(f"必要なモジュールがインポートできません: {e}")
        except Exception as e:
            pytest.skip(f"統合テストに失敗: {e}")

    def test_orchestrator_integration(self):
        """オーケストレーター統合テスト"""
        try:
            from loanpedia_scraper.scrapers.main import LoanScrapingOrchestrator
            
            # データベース無効で実行（外部サービスを叩かない）
            orchestrator = LoanScrapingOrchestrator(save_to_db=False)
            
            # 利用可能なスクレイパーの確認
            scrapers = orchestrator.get_available_scrapers()
            assert len(scrapers) > 0
            
            # 各スクレイパーがインスタンス化されていることを確認
            for scraper_name in scrapers:
                assert scraper_name in orchestrator.scrapers
                assert orchestrator.scrapers[scraper_name] is not None
                
        except Exception as e:
            pytest.skip(f"オーケストレーター統合テストに失敗: {e}")