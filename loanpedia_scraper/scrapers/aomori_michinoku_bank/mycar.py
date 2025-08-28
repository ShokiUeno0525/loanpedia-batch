# -*- coding: utf-8 -*-
"""
青森みちのく銀行マイカーローンスクレイピング

マイカーローンの情報を抽出（共通基盤版）
"""

from .base_scraper import BaseLoanScraper
from .extraction_utils import ExtractionUtils
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AomorimichinokuBankScraper(BaseLoanScraper):
    """
    青森みちのく銀行のマイカーローン情報をHTMLから抽出するスクレイパー
    共通基盤 BaseLoanScraper を継承
    """

    def get_default_url(self) -> str:
        return "https://www.am-bk.co.jp/kojin/loan/mycarloan/"
    
    def get_loan_type(self) -> str:
        return "自動車ローン"
    
    def get_loan_category(self) -> str:
        return "マイカーローン"

    def _extract_product_name(self, soup):
        """商品名を抽出（マイカーローン特化）"""
        title_elem = soup.find('title')
        if title_elem:
            return title_elem.get_text().strip()
        
        # h1から抽出を試行
        h1_elem = soup.find('h1')
        if h1_elem:
            return h1_elem.get_text().strip()
            
        return "青森みちのくマイカーローン〈WEB完結型〉"

    def _get_default_interest_rates(self):
        """マイカーローンのデフォルト金利範囲"""
        return (1.8, 3.5)

    def _get_default_loan_amounts(self):
        """マイカーローンのデフォルト融資金額範囲"""
        return (100000, 10000000)  # 10万円～1000万円

    def _get_default_loan_terms(self):
        """マイカーローンのデフォルト融資期間範囲（ヶ月）"""
        return (12, 84)  # 1年～7年

    def _get_default_age_range(self):
        """マイカーローンのデフォルト年齢範囲"""
        return (18, 75)

    def _extract_interest_rates(self, soup, item):
        """マイカーローン特有の金利抽出"""
        # .kinri-wrp要素から金利を抽出
        kinri_elements = soup.select('.kinri-wrp')
        for elem in kinri_elements:
            text = elem.get_text()
            
            # 変動金利範囲パターン
            range_match = re.search(r"変動金利.*?(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)\s*[%％]", text)
            if range_match:
                item["min_interest_rate"] = float(range_match.group(1))
                item["max_interest_rate"] = float(range_match.group(2))
                logger.info(f"✅ 金利範囲: {item['min_interest_rate']}% - {item['max_interest_rate']}%")
                return
            
            # <b>タグから直接抽出
            bold_elem = elem.find('b')
            if bold_elem and "〜" in bold_elem.get_text():
                bold_text = bold_elem.get_text()
                range_match = re.search(r"(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)", bold_text)
                if range_match:
                    item["min_interest_rate"] = float(range_match.group(1))
                    item["max_interest_rate"] = float(range_match.group(2))
                    logger.info(f"✅ 金利範囲（bold）: {item['min_interest_rate']}% - {item['max_interest_rate']}%")
                    return

        # テーブルからWEB金利を抽出
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                
                for i, cell in enumerate(cells):
                    # 金利情報（まだ取得できてない場合）
                    if "ローン金利" in cell and "min_interest_rate" not in item:
                        if i + 1 < len(cells):
                            web_rate_match = re.search(r"(\d+\.\d+)\s*[%％]", cells[i + 1])
                            if web_rate_match:
                                web_rate = float(web_rate_match.group(1))
                                item["min_interest_rate"] = web_rate
                                item["max_interest_rate"] = web_rate
                                logger.info(f"✅ テーブルWEB金利: {web_rate}%")
                                return

        # 基底クラスの共通処理にフォールバック
        super()._extract_interest_rates(soup, item)

    def _extract_loan_amounts(self, soup, item):
        """マイカーローン特有の融資金額抽出"""
        # .c-text要素から融資金額を抽出
        c_text_elements = soup.select('.c-text')
        for elem in c_text_elements:
            text = elem.get_text()
            # "1万円以上1,000万円以内" パターン
            range_match = re.search(r"(\d+(?:,\d{3})*)\s*万円以上.*?(\d+(?:,\d{3})*)\s*万円以内", text)
            if range_match:
                item["min_loan_amount"] = int(range_match.group(1).replace(",", "")) * 10000
                item["max_loan_amount"] = int(range_match.group(2).replace(",", "")) * 10000
                logger.info(f"✅ 融資金額範囲: {item['min_loan_amount']}円 - {item['max_loan_amount']}円")
                return

        # 基底クラスの共通処理にフォールバック
        super()._extract_loan_amounts(soup, item)

    def _extract_loan_periods(self, soup, item):
        """マイカーローン特有の融資期間抽出"""
        full_text = soup.get_text()

        # マイカーローン特有のパターン
        period_patterns = [
            (r"(\d+)\s*年\s*～\s*(\d+)\s*年", "year_range"),
            (r"最長\s*(\d+)\s*年", "max_year"),
        ]
        
        for pattern, pattern_type in period_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                if pattern_type == "year_range":
                    item["min_loan_term_months"] = int(matches[0][0]) * 12
                    item["max_loan_term_months"] = int(matches[0][1]) * 12
                    logger.info(f"✅ 融資期間範囲: {item['min_loan_term_months']}ヶ月 - {item['max_loan_term_months']}ヶ月")
                elif pattern_type == "max_year":
                    item["min_loan_term_months"] = 12  # デフォルト最小1年
                    item["max_loan_term_months"] = int(matches[0]) * 12
                    logger.info(f"✅ 最長融資期間: {item['max_loan_term_months']}ヶ月")
                return

        # 基底クラスの共通処理にフォールバック
        super()._extract_loan_periods(soup, item)

    def _extract_guarantor_requirements(self, full_text: str) -> str:
        """マイカーローンの保証人要件を抽出"""
        if "保証人" in full_text:
            if "原則不要" in full_text or "原則として不要" in full_text:
                return "原則不要（保証会社が保証）"
            else:
                return "保証会社の審査により決定"
        return ""

    def _extract_special_features(self, full_text: str) -> str:
        """マイカーローン特有の商品特徴を抽出"""
        features = ExtractionUtils.extract_common_features(full_text)
        
        # マイカーローン特有の特徴
        if "WEB完結" in full_text:
            features.append("WEB完結対応")
        if "収入印紙代不要" in full_text:
            features.append("収入印紙代不要")
        if "繰上返済手数料無料" in full_text:
            features.append("繰上返済手数料無料")
        if "ボーナス返済" in full_text:
            features.append("ボーナス返済併用可能")
        
        return "; ".join(features)

    def _get_default_repayment_method(self) -> str:
        """マイカーローンのデフォルト返済方法"""
        return "元利均等返済（口座自動振替）"

    def _extract_repayment_method(self, soup, item):
        """マイカーローン特有の返済方法を抽出"""
        full_text = soup.get_text()
        
        repayment_methods = []
        if "元利均等返済" in full_text:
            repayment_methods.append("元利均等返済")
        if "自動振替" in full_text:
            repayment_methods.append("口座自動振替")
        if "ボーナス返済" in full_text:
            repayment_methods.append("ボーナス返済併用可能")
        
        if not repayment_methods:
            repayment_methods.append(self._get_default_repayment_method())
        
        item["repayment_method"] = "; ".join(repayment_methods)
        logger.info(f"✅ 返済方法: {item['repayment_method']}")


def main():
    """テスト実行"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    scraper = AomorimichinokuBankScraper()
    result = scraper.scrape_loan_info()
    
    if result:
        print("スクレイピング成功!")
        print(f"商品名: {result.get('product_name')}")
        print(f"金利: {result.get('min_interest_rate')}% - {result.get('max_interest_rate')}%")
        print(f"融資額: {result.get('min_loan_amount')}円 - {result.get('max_loan_amount')}円")
    else:
        print("スクレイピング失敗")


if __name__ == "__main__":
    main()