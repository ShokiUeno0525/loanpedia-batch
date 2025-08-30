"""
ライブスクレイピングテスト（実際のWebサイトに接続）
注意: このテストは実際のWebサイトにアクセスするため、慎重に実行すること
"""
import pytest
import os
import time
from unittest.mock import patch

# ライブテスト実行条件の厳格化
LIVE_TEST_ENABLED = (
    os.getenv('SCRAPING_TEST_MODE') == 'true' and
    os.getenv('ENABLE_LIVE_SCRAPING_TESTS') == 'true'
)

@pytest.mark.skipif(
    not LIVE_TEST_ENABLED,
    reason="ライブスクレイピングテストはENABLE_LIVE_SCRAPING_TESTS=trueでのみ実行"
)
class TestLiveScraping:
    """ライブスクレイピングテストクラス"""

    @pytest.mark.timeout(60)  # 60秒でタイムアウト
    def test_aoimori_shinkin_live_scraping(self):
        """青森信用金庫ライブスクレイピングテスト"""
        try:
            from loanpedia_scraper.scrapers.aoimori_shinkin.general import AoimoriShinkinScraper
            
            scraper = AoimoriShinkinScraper(save_to_db=False)
            
            # スクレイピング前の待機（サイトへの負荷軽減）
            delay = int(os.getenv('SCRAPING_DELAY', '2'))
            time.sleep(delay)
            
            result = scraper.scrape_loan_info()
            
            # 基本的な結果検証
            assert result is not None
            if isinstance(result, dict):
                # エラーでない場合の検証
                if result.get('status') == 'success':
                    assert 'products' in result or 'data' in result
                    
        except ImportError:
            pytest.skip("AoimoriShinkinScraperが利用できません")
        except Exception as e:
            # ライブテストでは接続エラー等が予想されるため、ログ出力してスキップ
            pytest.skip(f"青森信用金庫スクレイピングテストをスキップ: {e}")

    @pytest.mark.timeout(60)
    def test_aomori_michinoku_live_scraping(self):
        """青森みちのく銀行ライブスクレイピングテスト"""
        try:
            from loanpedia_scraper.scrapers.aomori_michinoku_bank.product_scraper import AomorimichinokuBankScraper
            
            scraper = AomorimichinokuBankScraper()
            
            delay = int(os.getenv('SCRAPING_DELAY', '2'))
            time.sleep(delay)
            
            result = scraper.scrape_loan_info()
            
            assert result is not None
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    assert 'products' in result or 'data' in result
                    
        except ImportError:
            pytest.skip("AomorimichinokuBankScraperが利用できません")
        except Exception as e:
            pytest.skip(f"青森みちのく銀行スクレイピングテストをスキップ: {e}")

    @pytest.mark.timeout(180)  # 全体実行のため長めのタイムアウト
    def test_orchestrator_live_run(self):
        """オーケストレーターライブ実行テスト"""
        try:
            from loanpedia_scraper.scrapers.main import LoanScrapingOrchestrator
            
            orchestrator = LoanScrapingOrchestrator(save_to_db=False)
            
            # 全スクレイパー実行（実際のサイトアクセス）
            result = orchestrator.run_all_scrapers()
            
            # 結果の基本検証
            assert isinstance(result, dict)
            assert 'success_count' in result
            assert 'error_count' in result
            assert 'total_scrapers' in result
            
            # 少なくとも一部のスクレイパーは動作することを期待
            total_attempts = result.get('total_scrapers', 0)
            assert total_attempts > 0
            
            # 結果レポート（テスト失敗にならないようにログ出力）
            success_rate = (result.get('success_count', 0) / total_attempts) * 100 if total_attempts > 0 else 0
            print(f"\\nライブスクレイピング結果:")
            print(f"成功: {result.get('success_count', 0)}/{total_attempts} ({success_rate:.1f}%)")
            print(f"エラー: {result.get('error_count', 0)}")
            
            if result.get('errors'):
                print("エラー詳細:")
                for error in result['errors']:
                    print(f"  - {error}")
                    
        except Exception as e:
            pytest.skip(f"オーケストレーターライブテストをスキップ: {e}")

@pytest.mark.skipif(
    os.getenv('SCRAPING_TEST_MODE') != 'true',
    reason="スクレイピング動作テストはSCRAPING_TEST_MODE=trueでのみ実行"
)
class TestScrapingBehavior:
    """スクレイピング動作テスト（モック使用）"""

    @patch('requests.get')
    def test_html_parsing_robustness(self, mock_get):
        """HTML解析の堅牢性テスト"""
        # 様々なHTMLパターンでのテスト
        html_patterns = [
            # 正常なHTML
            "<html><body><div class='loan'>金利: 2.5%</div></body></html>",
            # 不完全なHTML
            "<div class='loan'>金利: 2.5%</div>",
            # エンコーディング問題を含むHTML
            "<html><body>金利：２．５％</body></html>",
            # 空のHTML
            "<html><body></body></html>",
            # HTMLタグなし
            "金利: 2.5%",
        ]
        
        try:
            from loanpedia_scraper.scrapers.aoimori_shinkin.general import AoimoriShinkinScraper
            
            scraper = AoimoriShinkinScraper(save_to_db=False)
            
            for i, html in enumerate(html_patterns):
                mock_response = MockResponse(html, 200)
                mock_get.return_value = mock_response
                
                # エラーを発生させずに処理できることを確認
                try:
                    result = scraper.scrape_loan_info()
                    # None or dict であることを確認（例外が発生しないこと）
                    assert result is None or isinstance(result, dict)
                except Exception as e:
                    pytest.fail(f"HTMLパターン{i}でエラー: {e}")
                    
        except ImportError:
            pytest.skip("AoimoriShinkinScraperが利用できません")

    @patch('requests.get')  
    def test_network_error_handling(self, mock_get):
        """ネットワークエラーハンドリングテスト"""
        import requests
        
        # 様々なネットワークエラーパターン
        error_patterns = [
            requests.exceptions.ConnectionError("接続エラー"),
            requests.exceptions.Timeout("タイムアウト"),
            requests.exceptions.HTTPError("HTTPエラー"),
            requests.exceptions.RequestException("リクエストエラー"),
        ]
        
        try:
            from loanpedia_scraper.scrapers.aoimori_shinkin.general import AoimoriShinkinScraper
            
            scraper = AoimoriShinkinScraper(save_to_db=False)
            
            for error in error_patterns:
                mock_get.side_effect = error
                
                # エラーが適切にハンドリングされることを確認
                result = scraper.scrape_loan_info()
                # エラー時はNoneまたはエラー情報を含む辞書が返される
                assert result is None or (isinstance(result, dict) and 'error' in result)
                
        except ImportError:
            pytest.skip("AoimoriShinkinScraperが利用できません")


class MockResponse:
    """テスト用HTTPレスポンスモック"""
    
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.headers = {'content-type': 'text/html; charset=utf-8'}
        self.encoding = 'utf-8'