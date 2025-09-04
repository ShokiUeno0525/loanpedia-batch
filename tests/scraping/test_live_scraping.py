"""
スクレイピング動作テスト（モック中心）
"""
import pytest
import os
from unittest.mock import patch


@pytest.mark.skipif(
    os.getenv('SCRAPING_TEST_MODE') != 'true',
    reason="スクレイピング動作テストはSCRAPING_TEST_MODE=trueでのみ実行"
)
class TestScrapingBehavior:
    """スクレイピング動作テスト（モック使用）"""

    @patch('loanpedia_scraper.scrapers.aoimori_shinkin.http_client.get')
    def test_html_parsing_robustness(self, mock_get):
        """HTML解析の堅牢性テスト"""
        html_patterns = [
            "<html><body><div class='loan'>金利: 2.5%</div></body></html>",
            "<div class='loan'>金利: 2.5%</div>",
            "<html><body>金利：２．５％</body></html>",
            "<html><body></body></html>",
            "金利: 2.5%",
        ]

        try:
            from loanpedia_scraper.scrapers.aoimori_shinkin.product_scraper import AoimoriShinkinScraper

            scraper = AoimoriShinkinScraper(save_to_db=False)

            for i, html in enumerate(html_patterns):
                mock_response = MockResponse(html, 200)
                mock_get.return_value = mock_response

                try:
                    result = scraper.scrape_loan_info()
                    assert result is None or isinstance(result, dict)
                except Exception as e:
                    pytest.fail(f"HTMLパターン{i}でエラー: {e}")

        except ImportError:
            pytest.skip("AoimoriShinkinScraperが利用できません")

    @patch('loanpedia_scraper.scrapers.aoimori_shinkin.http_client.get')
    def test_network_error_handling(self, mock_get):
        """ネットワークエラーハンドリングテスト"""
        import requests

        error_patterns = [
            requests.exceptions.ConnectionError("接続エラー"),
            requests.exceptions.Timeout("タイムアウト"),
            requests.exceptions.HTTPError("HTTPエラー"),
            requests.exceptions.RequestException("リクエストエラー"),
        ]

        try:
            from loanpedia_scraper.scrapers.aoimori_shinkin.product_scraper import AoimoriShinkinScraper

            scraper = AoimoriShinkinScraper(save_to_db=False)

            for error in error_patterns:
                mock_get.side_effect = error
                result = scraper.scrape_loan_info()
                assert result is None or (isinstance(result, dict) and 'error' in result)

        except ImportError:
            pytest.skip("AoimoriShinkinScraperが利用できません")


class MockResponse:
    """テスト用HTTPレスポンスモック"""

    def __init__(self, text, status_code=200, url="https://example.com"):
        self.text = text
        self.content = text.encode('utf-8')
        self.status_code = status_code
        self.headers = {'content-type': 'text/html; charset=utf-8'}
        self.encoding = 'utf-8'
        self.url = url
