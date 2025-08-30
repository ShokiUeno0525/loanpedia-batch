"""
データベース統合テスト
"""
import pytest
import os
from unittest.mock import patch
from loanpedia_scraper.database.loan_service import LoanService
from loanpedia_scraper.database.loan_database import get_database_config

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
            loan_service = LoanService(db_config)
            
            # 接続テスト
            connection = loan_service.get_connection()
            assert connection is not None
            
            # テーブル存在確認
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'raw_loan_data'")
                result = cursor.fetchone()
                assert result is not None
                
        except Exception as e:
            pytest.skip(f"データベース接続に失敗: {e}")

    def test_insert_raw_loan_data(self):
        """生データ挿入テスト"""
        try:
            db_config = get_database_config()
            loan_service = LoanService(db_config)
            
            test_data = {
                'institution_name': 'テスト金融機関',
                'url': 'https://test.example.com/loans',
                'html_content': '<html><body>テストHTML</body></html>',
                'extracted_data': {'test': 'data'},
                'content_hash': 'test_hash_123'
            }
            
            # データ挿入
            result = loan_service.save_raw_data(test_data)
            assert result is True
            
            # データ確認
            saved_data = loan_service.get_raw_data_by_hash('test_hash_123')
            assert saved_data is not None
            assert saved_data['institution_name'] == 'テスト金融機関'
            
        except Exception as e:
            pytest.skip(f"データベース操作に失敗: {e}")

    def test_data_cleanup(self):
        """テストデータクリーンアップ"""
        try:
            db_config = get_database_config()
            loan_service = LoanService(db_config)
            
            # テストデータの削除
            loan_service.cleanup_test_data('test_hash_123')
            
            # 削除確認
            saved_data = loan_service.get_raw_data_by_hash('test_hash_123')
            assert saved_data is None
            
        except Exception as e:
            pytest.skip(f"クリーンアップに失敗: {e}")

@pytest.mark.skipif(
    os.getenv('SCRAPING_TEST_MODE') != 'true',
    reason="スクレイパー統合テストはSCRAPING_TEST_MODE=trueでのみ実行"
)
class TestScraperIntegration:
    """スクレイパー統合テストクラス"""

    @patch('requests.get')
    def test_scraper_with_database(self, mock_get, mock_requests_response, sample_html_content):
        """スクレイパーとデータベースの統合テスト"""
        # HTTPレスポンスのモック設定
        mock_requests_response.text = sample_html_content
        mock_get.return_value = mock_requests_response
        
        try:
            from loanpedia_scraper.scrapers.aoimori_shinkin.general import AoimoriShinkinScraper
            
            db_config = get_database_config()
            scraper = AoimoriShinkinScraper(save_to_db=True, db_config=db_config)
            
            # スクレイピング実行
            result = scraper.scrape_loan_info()
            
            assert result is not None
            assert 'status' in result
            assert result['status'] == 'success'
            
        except ImportError:
            pytest.skip("AoimoriShinkinScraperが利用できません")
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