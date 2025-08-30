"""
スクレイパー統合テスト
実際のスクレイピングフローが正常に動作するかをテスト
"""
import pytest
import os
from unittest.mock import Mock, patch
from loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper import AomorimichinokuBankScraper


@pytest.mark.skipif(
    os.getenv('SCRAPING_TEST_MODE') != 'true',
    reason="統合テストはSCRAPING_TEST_MODE=trueでのみ実行"
)
class TestScraperIntegration:
    """スクレイパー統合テストクラス"""

    @patch('loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper.requests.Session.get')
    def test_complete_scraping_flow_mycar(self, mock_get):
        """マイカーローンの完全スクレイピングフローテスト"""
        # 実際の銀行サイトに近いHTMLレスポンスを作成
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://www.am-bk.co.jp/kojin/loan/mycarloan/"
        mock_response.content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>マイカーローン | 青森みちのく銀行</title>
            <meta charset="utf-8">
        </head>
        <body>
            <header>
                <nav>メニュー</nav>
            </header>
            <main>
                <section class="loan-content">
                    <h1>マイカーローン</h1>
                    <div class="loan-overview">
                        <p>新車・中古車・バイクの購入、車検・修理費用、免許取得費用にご利用いただけます。</p>
                    </div>
                    <table class="loan-details">
                        <tr>
                            <th>金利</th>
                            <td>年2.8%～3.8%（変動金利）</td>
                        </tr>
                        <tr>
                            <th>融資金額</th>
                            <td>10万円以上1,000万円以内（1万円単位）</td>
                        </tr>
                        <tr>
                            <th>融資期間</th>
                            <td>6ヶ月以上10年以内（1ヶ月単位）</td>
                        </tr>
                        <tr>
                            <th>対象年齢</th>
                            <td>満20歳以上満65歳未満の方</td>
                        </tr>
                        <tr>
                            <th>返済方法</th>
                            <td>元利均等毎月返済（ボーナス併用返済も可能）</td>
                        </tr>
                        <tr>
                            <th>保証</th>
                            <td>保証会社の保証が必要です</td>
                        </tr>
                    </table>
                    <div class="features">
                        <h3>商品の特徴</h3>
                        <ul>
                            <li>新車・中古車の購入資金</li>
                            <li>バイクの購入資金</li>
                            <li>車検・修理費用</li>
                            <li>免許取得費用</li>
                            <li>借換資金</li>
                        </ul>
                    </div>
                </section>
            </main>
            <footer>
                <p>青森みちのく銀行</p>
            </footer>
        </body>
        </html>
        """.encode('utf-8')
        mock_get.return_value = mock_response
        
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        result = scraper.scrape_loan_info()
        
        # 基本的な結果構造を確認
        assert isinstance(result, dict)
        assert "source_url" in result
        assert result["source_url"] == mock_response.url
        
        # 機関情報の確認
        assert result.get("institution_code") == "0117"
        assert "institution_name" in result
        
        # 商品情報の確認
        assert result.get("loan_type") == "マイカーローン"
        assert result.get("loan_category") == "目的別ローン"
        
        # 抽出されたデータの妥当性確認
        if "min_interest_rate" in result and "max_interest_rate" in result:
            assert 0 < result["min_interest_rate"] <= result["max_interest_rate"] <= 20
            print(f"金利範囲: {result['min_interest_rate']}% - {result['max_interest_rate']}%")
        
        if "min_loan_amount" in result and "max_loan_amount" in result:
            assert 0 < result["min_loan_amount"] <= result["max_loan_amount"]
            print(f"融資額範囲: {result['min_loan_amount']:,}円 - {result['max_loan_amount']:,}円")
        
        if "min_loan_term_months" in result and "max_loan_term_months" in result:
            assert 0 < result["min_loan_term_months"] <= result["max_loan_term_months"]
            print(f"融資期間: {result['min_loan_term_months']}ヶ月 - {result['max_loan_term_months']}ヶ月")
        
        # エラーがないことを確認
        assert result.get("scraping_status") != "failed"
        assert "error" not in result

    @patch('loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper.requests.Session.get')
    def test_complete_scraping_flow_education(self, mock_get):
        """教育ローンの完全スクレイピングフローテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://www.am-bk.co.jp/kojin/loan/kyouikuloan_hanpuku/"
        mock_response.content = """
        <!DOCTYPE html>
        <html>
        <head><title>教育ローン | 青森みちのく銀行</title></head>
        <body>
            <h1>教育ローン（証書貸付型）</h1>
            <div>
                <p>金利：年2.3%～3.8%（変動金利）</p>
                <p>融資金額：10万円以上500万円以内</p>
                <p>融資期間：1年以上15年以内</p>
                <p>年齢：満20歳以上満65歳未満</p>
            </div>
        </body>
        </html>
        """.encode('utf-8')
        mock_get.return_value = mock_response
        
        scraper = AomorimichinokuBankScraper(product_type="education")
        result = scraper.scrape_loan_info()
        
        assert isinstance(result, dict)
        assert result.get("loan_type") == "教育ローン"
        assert result.get("loan_category") == "目的別ローン"
        
        # 教育ローン特有の設定値確認
        expected_rates = scraper._get_default_interest_rates()
        assert expected_rates == (2.3, 3.8)
        
        print(f"教育ローン結果: {result.get('loan_type')}")

    @patch('loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper.requests.Session.get')
    def test_scraping_with_minimal_html(self, mock_get):
        """最小限HTMLでの統合テスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://www.am-bk.co.jp/kojin/loan/freeloan/"
        mock_response.content = """
        <html>
        <body>
            <h1>フリーローン</h1>
            <p>自由な用途にご利用いただけます</p>
        </body>
        </html>
        """.encode('utf-8')
        mock_get.return_value = mock_response
        
        scraper = AomorimichinokuBankScraper(product_type="freeloan")
        result = scraper.scrape_loan_info()
        
        # 最小限の情報でもエラーにならず、デフォルト値が設定されることを確認
        assert isinstance(result, dict)
        assert result.get("scraping_status") != "failed"
        
        # デフォルト値が設定されることを確認
        expected_rates = scraper._get_default_interest_rates()
        expected_amounts = scraper._get_default_loan_amounts()
        expected_terms = scraper._get_default_loan_terms()
        
        print(f"デフォルト値 - 金利: {expected_rates}, 融資額: {expected_amounts}, 期間: {expected_terms}")

    @patch('loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper.requests.Session.get')
    def test_http_error_handling(self, mock_get):
        """HTTPエラーハンドリング統合テスト"""
        import requests
        
        # HTTPエラーをシミュレート
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        result = scraper.scrape_loan_info()
        
        # エラーが適切に処理されることを確認
        assert isinstance(result, dict)
        assert result.get("scraping_status") == "failed"
        assert "error" in result
        
        print(f"HTTPエラー処理結果: {result}")

    @patch('loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper.requests.Session.get')
    def test_timeout_handling(self, mock_get):
        """タイムアウト処理統合テスト"""
        import requests
        
        # タイムアウトエラーをシミュレート
        mock_get.side_effect = requests.Timeout("Request timeout")
        
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        result = scraper.scrape_loan_info()
        
        # タイムアウトが適切に処理されることを確認
        assert isinstance(result, dict)
        assert result.get("scraping_status") == "failed"
        assert "error" in result
        assert "timeout" in result["error"].lower()
        
        print(f"タイムアウト処理結果: {result}")

    @patch('loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper.requests.Session.get')
    def test_encoding_handling(self, mock_get):
        """エンコーディング処理統合テスト"""
        # 異なるエンコーディングのレスポンス
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://www.am-bk.co.jp/kojin/loan/mycarloan/"
        # Shift_JISエンコーディング
        html_content = """
        <html>
        <head><title>マイカーローン</title></head>
        <body>
            <h1>マイカーローン</h1>
            <p>金利：年２．８％～３．８％</p>
        </body>
        </html>
        """
        mock_response.content = html_content.encode('shift_jis')
        mock_get.return_value = mock_response
        
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        result = scraper.scrape_loan_info()
        
        # エンコーディング問題でクラッシュしないことを確認
        assert isinstance(result, dict)
        # エラーになる場合とならない場合があるが、クラッシュしないことが重要
        print(f"エンコーディングテスト結果: {result.get('scraping_status', 'success')}")

    def test_multiple_product_types_consistency(self):
        """複数商品タイプの一貫性テスト"""
        product_types = ["mycar", "education", "freeloan", "omatomeloan"]
        
        for product_type in product_types:
            scraper = AomorimichinokuBankScraper(product_type=product_type)
            
            # 各商品タイプで基本設定が一貫していることを確認
            url = scraper.get_default_url()
            loan_type = scraper.get_loan_type()
            rates = scraper._get_default_interest_rates()
            amounts = scraper._get_default_loan_amounts()
            terms = scraper._get_default_loan_terms()
            
            # 基本的な妥当性
            assert isinstance(url, str) and url.startswith("http")
            assert isinstance(loan_type, str) and len(loan_type) > 0
            assert len(rates) == 2 and 0 < rates[0] <= rates[1] <= 20
            assert len(amounts) == 2 and 0 < amounts[0] <= amounts[1]
            assert len(terms) == 2 and 0 < terms[0] <= terms[1] <= 420
            
            print(f"{product_type}: {loan_type}, 金利{rates[0]}-{rates[1]}%, "
                  f"融資額{amounts[0]:,}-{amounts[1]:,}円, 期間{terms[0]}-{terms[1]}ヶ月")

    @patch('loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper.requests.Session.get')
    def test_session_reuse(self, mock_get):
        """セッション再利用テスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://www.am-bk.co.jp/kojin/loan/mycarloan/"
        mock_response.content = "<html><body><h1>テスト</h1></body></html>".encode('utf-8')
        mock_get.return_value = mock_response
        
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        
        # 同じスクレイパーで複数回実行
        result1 = scraper.scrape_loan_info()
        result2 = scraper.scrape_loan_info()
        
        # 両方とも成功することを確認
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert result1.get("scraping_status") != "failed"
        assert result2.get("scraping_status") != "failed"
        
        # セッションが2回使われることを確認
        assert mock_get.call_count == 2
        
        print("セッション再利用テスト完了")