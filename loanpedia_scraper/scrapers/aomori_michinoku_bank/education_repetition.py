# -*- coding: utf-8 -*-
"""
青森みちのく銀行教育ローンスクレイピング（反復利用型）

教育ローン〈反復利用型〉の情報を抽出（共通基盤版）
"""

from .base_scraper import BaseLoanScraper
from .extraction_utils import ExtractionUtils
import logging

logger = logging.getLogger(__name__)


class AomorimichinokuEducationRepetitionScraper(BaseLoanScraper):
    """
    青森みちのく銀行の教育ローン（反復利用型）情報をHTMLから抽出するスクレイパー
    共通基盤 BaseLoanScraper を継承
    """

    def get_default_url(self) -> str:
        return "https://www.am-bk.co.jp/kojin/loan/kyouikuloan_hanpuku/"
    
    def get_loan_type(self) -> str:
        return "教育ローン"
    
    def get_loan_category(self) -> str:
        return "教育ローン（反復利用型）"

    def get_interest_type(self) -> str:
        return "変動金利"

    def _extract_product_name(self, soup):
        """商品名を抽出（反復利用型教育ローン特化）"""
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text().strip()
            if "教育ローン" in title_text or "反復利用" in title_text:
                return title_text

        h1_elem = soup.find("h1")
        if h1_elem:
            h1_text = h1_elem.get_text().strip()
            if "教育ローン" in h1_text or "反復利用" in h1_text:
                return h1_text

        return "青森みちのく教育ローン〈反復利用型〉"

    def _get_default_interest_rates(self):
        """教育ローン（反復利用型）のデフォルト金利範囲"""
        return (2.5, 5.5)

    def _get_default_loan_amounts(self):
        """教育ローン（反復利用型）のデフォルト融資金額範囲"""
        return (100000, 5000000)  # 10万円～500万円

    def _get_default_loan_terms(self):
        """教育ローン（反復利用型）のデフォルト融資期間範囲（ヶ月）"""
        return (12, 180)  # 1年～15年

    def _get_default_age_range(self):
        """教育ローン（反復利用型）のデフォルト年齢範囲"""
        return (20, 74)

    def _extract_guarantor_requirements(self, full_text: str) -> str:
        """教育ローン（反復利用型）の保証人要件を抽出"""
        if "保証人" in full_text and ("不要" in full_text or "ジャックス" in full_text):
            return "原則不要（ジャックスが保証）"
        elif "ジャックス" in full_text:
            return "ジャックスが保証"
        elif "保証会社" in full_text:
            return "保証会社による保証"
        return ""

    def _extract_special_features(self, full_text: str) -> str:
        """教育ローン（反復利用型）特有の商品特徴を抽出"""
        features = ExtractionUtils.extract_common_features(full_text)
        
        # 教育ローン（反復利用型）特有の特徴
        if "反復利用" in full_text or "繰返" in full_text:
            features.append("反復利用型（必要な時に繰り返し借入可能）")
        if "カードローン" in full_text:
            features.append("カードローン形式")
        if "在学中" in full_text and "利息のみ" in full_text:
            features.append("在学中は利息のみ返済可能")
        if "ATM" in full_text:
            features.append("ATMで借入・返済可能")
        if "元利均等" in full_text:
            features.append("元利均等返済選択可能")
        
        return "; ".join(features)

    def _get_default_repayment_method(self) -> str:
        """教育ローン（反復利用型）のデフォルト返済方法"""
        return "利息のみ返済または元利均等返済（口座自動振替）"


def main():
    """テスト実行"""
    import logging
    logging.basicConfig(level=logging.INFO)

    scraper = AomorimichinokuEducationRepetitionScraper()
    result = scraper.scrape_loan_info()

    if result and result.get("scraping_status") == "success":
        print("スクレイピング成功!")
        print(f"商品名: {result.get('product_name')}")
        print(
            f"金利: {result.get('min_interest_rate')}% - {result.get('max_interest_rate')}%"
        )
        print(
            f"融資額: {result.get('min_loan_amount'):,}円 - {result.get('max_loan_amount'):,}円"
        )
        print(
            f"融資期間: {result.get('min_loan_term_months')}ヶ月 - {result.get('max_loan_term_months')}ヶ月"
        )
        print(f"年齢: {result.get('min_age')}歳 - {result.get('max_age')}歳")
        print(f"特徴: {result.get('special_features')}")
    else:
        print("スクレイピング失敗")
        if result:
            print(f"エラー: {result.get('error')}")


if __name__ == "__main__":
    main()