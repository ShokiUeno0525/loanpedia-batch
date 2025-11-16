"""
青森みちのく銀行スクレイパーのユニットテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper import AomorimichinokuBankScraper


class TestAomorimichinokuBankScraper:
    """青森みちのく銀行スクレイパーのテストクラス"""

    def test_init_default(self):
        """デフォルト初期化テスト"""
        scraper = AomorimichinokuBankScraper()
        assert scraper.product_type == "general"
        assert scraper.institution_code == "0117"

    def test_init_with_product_type(self):
        """商品タイプ指定初期化テスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        assert scraper.product_type == "mycar"
        assert scraper.institution_code == "0117"

    def test_get_default_url_mycar(self):
        """マイカーローンURL取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        url = scraper.get_default_url()
        assert url == "https://www.am-bk.co.jp/kojin/loan/mycarloan/"

    def test_get_default_url_education(self):
        """教育ローンURL取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="education")
        url = scraper.get_default_url()
        assert url == "https://www.am-bk.co.jp/kojin/loan/kyouikuloan_hanpuku/"

    def test_get_default_url_unknown_type(self):
        """不明な商品タイプのURL取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="unknown")
        url = scraper.get_default_url()
        assert url == "https://www.am-bk.co.jp/kojin/loan/"

    def test_get_loan_type_mycar(self):
        """マイカーローンタイプ取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        loan_type = scraper.get_loan_type()
        assert loan_type == "マイカーローン"

    def test_get_loan_type_education(self):
        """教育ローンタイプ取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="education")
        loan_type = scraper.get_loan_type()
        assert loan_type == "教育ローン"

    def test_get_loan_type_unknown(self):
        """不明な商品タイプのローンタイプ取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="unknown")
        loan_type = scraper.get_loan_type()
        assert loan_type == "ローン"

    def test_get_loan_category_mycar(self):
        """マイカーローンカテゴリ取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        category = scraper.get_loan_category()
        assert category == "自動車"

    def test_get_loan_category_freeloan(self):
        """フリーローンカテゴリ取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="freeloan")
        category = scraper.get_loan_category()
        assert category == "多目的"

    def test_get_default_interest_rates_mycar(self):
        """マイカーローン金利取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        min_rate, max_rate = scraper._get_default_interest_rates()
        assert min_rate == 1.8
        assert max_rate == 3.8

    def test_get_default_interest_rates_freeloan(self):
        """フリーローン金利取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="freeloan")
        min_rate, max_rate = scraper._get_default_interest_rates()
        assert min_rate == 6.8
        assert max_rate == 14.5

    def test_get_default_interest_rates_unknown(self):
        """不明な商品タイプの金利取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="unknown")
        min_rate, max_rate = scraper._get_default_interest_rates()
        assert min_rate == 2.0
        assert max_rate == 14.5

    def test_get_default_loan_amounts_mycar(self):
        """マイカーローン融資額取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        min_amount, max_amount = scraper._get_default_loan_amounts()
        assert min_amount == 100000
        assert max_amount == 10000000

    def test_get_default_loan_amounts_education_card(self):
        """教育カードローン融資額取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="education_card")
        min_amount, max_amount = scraper._get_default_loan_amounts()
        assert min_amount == 100000
        assert max_amount == 3000000

    def test_get_default_loan_terms_mycar(self):
        """マイカーローン融資期間取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        min_term, max_term = scraper._get_default_loan_terms()
        assert min_term == 6
        assert max_term == 120

    def test_get_default_loan_terms_education_card(self):
        """教育カードローン融資期間取得テスト"""
        scraper = AomorimichinokuBankScraper(product_type="education_card")
        min_term, max_term = scraper._get_default_loan_terms()
        assert min_term == 12
        assert max_term == 36

    def test_all_product_types_coverage(self):
        """全商品タイプの網羅テスト"""
        product_types = [
            "mycar", "education", "education_deed", 
            "education_card", "freeloan", "omatomeloan"
        ]
        
        for product_type in product_types:
            scraper = AomorimichinokuBankScraper(product_type=product_type)
            
            # 各メソッドがエラーなく実行できることを確認
            url = scraper.get_default_url()
            loan_type = scraper.get_loan_type()
            category = scraper.get_loan_category()
            rates = scraper._get_default_interest_rates()
            amounts = scraper._get_default_loan_amounts()
            terms = scraper._get_default_loan_terms()
            
            assert isinstance(url, str)
            assert isinstance(loan_type, str)
            assert isinstance(category, str)
            assert len(rates) == 2
            assert len(amounts) == 2
            assert len(terms) == 2
            
            # 金利範囲の妥当性チェック
            assert 0 < rates[0] <= rates[1] <= 20.0
            
            # 融資額範囲の妥当性チェック
            assert 0 < amounts[0] <= amounts[1]
            
            # 融資期間範囲の妥当性チェック
            assert 0 < terms[0] <= terms[1] <= 420  # 35年 = 420ヶ月