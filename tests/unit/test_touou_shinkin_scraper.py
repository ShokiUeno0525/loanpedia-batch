# tests/unit/test_touou_shinkin_scraper.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from loanpedia_scraper.scrapers.touou_shinkin.product_scraper import TououShinkinScraper


class TestTououShinkinScraper:

    def test_init_default(self):
        """初期化のテスト（デフォルト設定）"""
        scraper = TououShinkinScraper()
        assert scraper.save_to_db is False
        assert scraper.db_config is None
        assert scraper.session is not None

    def test_init_with_db_settings(self):
        """初期化のテスト（DB保存有効）"""
        db_config = {"host": "localhost", "database": "test"}
        scraper = TououShinkinScraper(save_to_db=True, db_config=db_config)
        assert scraper.save_to_db is True
        assert scraper.db_config == db_config

    @patch('loanpedia_scraper.scrapers.touou_shinkin.product_scraper.extract_from_pdf_url')
    @patch('loanpedia_scraper.scrapers.touou_shinkin.product_scraper.get_pdf_urls')
    def test_scrape_loan_info_basic(self, mock_get_pdf_urls, mock_extract_from_pdf_url):
        """基本的なスクレイピング動作のテスト"""
        # モックの設定
        mock_get_pdf_urls.return_value = [
            "https://example.com/carlife_s.pdf",
            "https://example.com/kyoiku_s.pdf"
        ]

        mock_extract_from_pdf_url.return_value = [
            {
                "product_name": "カーライフローン",
                "interest_rate_floating": 2.5,
                "source_url": "https://example.com/carlife_s.pdf"
            }
        ]

        # スクレイパー実行
        scraper = TououShinkinScraper()
        result = scraper.scrape_loan_info()

        # 結果検証
        assert result["scraping_status"] == "success"
        assert len(result["products"]) >= 1
        assert result["institution_name"] == "東奥信用金庫"
        assert result["institution_type"] == "信用金庫"

        # PDF URL がモックされた回数を確認
        assert mock_extract_from_pdf_url.call_count == 2

    @patch('loanpedia_scraper.scrapers.touou_shinkin.product_scraper.extract_from_pdf_url')
    def test_scrape_loan_info_with_specific_url(self, mock_extract_from_pdf_url):
        """特定のURLでのスクレイピング動作のテスト"""
        mock_extract_from_pdf_url.return_value = [
            {
                "product_name": "教育ローン",
                "interest_rate_floating": 1.8,
                "source_url": "https://example.com/kyoiku_s.pdf"
            }
        ]

        # 特定のURLでスクレイピング実行
        scraper = TououShinkinScraper()
        result = scraper.scrape_loan_info(url="https://example.com/kyoiku_s.pdf")

        # 結果検証
        assert result["scraping_status"] == "success"
        assert len(result["products"]) == 1
        assert result["products"][0]["product_name"] == "教育ローン"

        # 指定したURLでのみ呼び出されることを確認
        mock_extract_from_pdf_url.assert_called_once_with("https://example.com/kyoiku_s.pdf")

    @patch('loanpedia_scraper.scrapers.touou_shinkin.product_scraper.extract_from_pdf_url')
    @patch('loanpedia_scraper.scrapers.touou_shinkin.product_scraper.get_pdf_urls')
    def test_scrape_loan_info_no_results(self, mock_get_pdf_urls, mock_extract_from_pdf_url):
        """結果なしの場合のテスト"""
        mock_get_pdf_urls.return_value = ["https://example.com/empty.pdf"]
        mock_extract_from_pdf_url.return_value = []

        scraper = TououShinkinScraper()
        result = scraper.scrape_loan_info()

        # 空の結果でも成功とする
        assert result["scraping_status"] == "success"
        assert result["products"] == []

    @patch('loanpedia_scraper.scrapers.touou_shinkin.product_scraper.extract_from_pdf_url')
    @patch('loanpedia_scraper.scrapers.touou_shinkin.product_scraper.get_pdf_urls')
    def test_scrape_loan_info_with_error(self, mock_get_pdf_urls, mock_extract_from_pdf_url):
        """エラー発生時の処理テスト"""
        mock_get_pdf_urls.return_value = ["https://example.com/error.pdf"]
        mock_extract_from_pdf_url.side_effect = Exception("PDF parsing failed")

        scraper = TououShinkinScraper()
        result = scraper.scrape_loan_info()

        # エラーが発生しても処理が継続され、空の結果が返されることを確認
        assert result["scraping_status"] == "success"
        assert result["products"] == []

    def test_build_base_item_content(self):
        """ベースアイテムの内容テスト"""
        scraper = TououShinkinScraper()
        result = scraper.scrape_loan_info()

        # 基本項目の検証
        assert result["institution_code"] == "0004"
        assert result["institution_name"] == "東奥信用金庫"
        assert result["website_url"] == "https://www.shinkin.co.jp/toshin/"
        assert result["institution_type"] == "信用金庫"
        assert "scraped_at" in result
        assert result["financial_institution"] == "東奥信用金庫"
        assert result["location"] == "青森県"