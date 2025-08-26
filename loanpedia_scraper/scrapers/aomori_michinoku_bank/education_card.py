# -*- coding: utf-8 -*-
"""
青森みちのく銀行教育カードローンスクレイピング

教育カードローンの情報を抽出（共通基盤版）
"""

from .base_scraper import BaseLoanScraper
from .extraction_utils import ExtractionUtils
import logging
import re

logger = logging.getLogger(__name__)


class AomorimichinokuEducationCardScraper(BaseLoanScraper):
    """
    青森みちのく銀行の教育カードローン情報をHTMLから抽出するスクレイパー
    共通基盤 BaseLoanScraper を継承
    """

    def get_default_url(self) -> str:
        return "https://www.am-bk.co.jp/kojin/loan/kyouikuloan/"
    
    def get_loan_type(self) -> str:
        return "教育ローン"
    
    def get_loan_category(self) -> str:
        return "教育カードローン"

    def _extract_product_name(self, soup):
        """商品名を抽出（教育カードローン特化）"""
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text().strip()
            if "教育カードローン" in title_text or "カードローン" in title_text:
                return title_text

        h1_elem = soup.find("h1")
        if h1_elem:
            h1_text = h1_elem.get_text().strip()
            if "教育カードローン" in h1_text or "カードローン" in h1_text:
                return h1_text

        return "青森みちのく教育カードローン"

    def _get_default_interest_rates(self):
        """教育カードローンのデフォルト金利範囲"""
        return (4.2, 4.9)

    def _get_default_loan_amounts(self):
        """教育カードローンのデフォルト融資金額範囲"""
        return (500000, 10000000)  # 50万円～1000万円

    def _get_default_min_loan_amount(self):
        """教育カードローンのデフォルト最小融資額"""
        return 500000  # 50万円

    def _get_default_loan_terms(self):
        """教育カードローンのデフォルト融資期間範囲（ヶ月）"""
        return (6, 114)  # 6ヶ月～9年6ヶ月

    def _get_default_min_loan_term(self):
        """教育カードローンのデフォルト最小融資期間（ヶ月）"""
        return 6  # 6ヶ月

    def _get_default_age_range(self):
        """教育カードローンのデフォルト年齢範囲"""
        return (20, 74)

    def _extract_interest_rates(self, soup, item):
        """教育カードローン特有の金利抽出"""
        full_text = soup.get_text()

        # 教育カードローン特有の複雑なパターン
        # 実際のパターン: "年4.2％" と "年5.4％から引下後年4.3％〜年4.9％"
        education_rate_patterns = [
            (r"年\s*(\d+\.\d+)\s*[%％].*?年\s*(\d+\.\d+)\s*[%％]\s*から\s*引下後\s*年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "WEB完結型・来店型金利"),
            (r"年\s*(\d+\.\d+)\s*[%％]\s*から\s*引下後\s*年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "引下後金利範囲"),
        ]

        for pattern, description in education_rate_patterns:
            match = re.search(pattern, full_text)
            if match:
                groups = match.groups()
                if len(groups) == 4:  # WEB完結型 + 来店型範囲
                    # 最初の金利（WEB完結型）を最低金利、最後を最高金利とする
                    item["min_interest_rate"] = float(groups[0])
                    item["max_interest_rate"] = float(groups[3])
                    logger.info(
                        f"✅ {description}: WEB完結型{groups[0]}%、来店型{groups[2]}%-{groups[3]}% → 統合: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    return
                elif len(groups) == 3:  # 引下後範囲
                    item["min_interest_rate"] = float(groups[1])
                    item["max_interest_rate"] = float(groups[2])
                    logger.info(
                        f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    return

        # 基底クラスの共通処理にフォールバック
        super()._extract_interest_rates(soup, item)

    def _extract_loan_amounts(self, soup, item):
        """教育カードローン特有の融資金額抽出"""
        full_text = soup.get_text()

        # 教育カードローン特有のパターン
        education_amount_patterns = [
            r"最大\s*(\d+(?:,\d{3})*)\s*万円.*?WEB完結型.*?上限\s*(\d+(?:,\d{3})*)\s*万円",
            r"最大\s*(\d+(?:,\d{3})*)\s*万円.*?WEB完結型.*?(\d+(?:,\d{3})*)\s*万円.*?上限",
        ]

        for pattern in education_amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                if len(match.groups()) == 2:
                    # WEB完結型の制限を考慮
                    max_amount = int(match.group(1).replace(",", ""))
                    web_limit = int(match.group(2).replace(",", ""))
                    item["min_loan_amount"] = 500000  # 50万円
                    # WEB完結型の制限がある場合は、より低い方を採用
                    item["max_loan_amount"] = min(max_amount, web_limit) * 10000
                    
                    logger.info(
                        f"✅ 融資金額範囲（WEB完結型考慮）: {item['min_loan_amount']:,}円 - {item['max_loan_amount']:,}円"
                    )
                    return

        # 基底クラスの共通処理にフォールバック
        super()._extract_loan_amounts(soup, item)

    def _extract_loan_periods(self, soup, item):
        """教育カードローン特有の融資期間抽出"""
        full_text = soup.get_text()

        # 教育カードローン特有のパターン
        education_period_patterns = [
            (r"最大\s*(\d+)\s*年\s*(\d+)\s*[ヵヶ]月", "年月形式"),
            (r"入学前\s*(\d+)\s*[ヵヶ]月.*?最大\s*(\d+)\s*年\s*(\d+)\s*[ヵヶ]月", "詳細期間"),
        ]

        for pattern, pattern_type in education_period_patterns:
            match = re.search(pattern, full_text)
            if match:
                if pattern_type in ["年月形式", "詳細期間"]:
                    if len(match.groups()) >= 2:
                        groups = match.groups()
                        years = int(groups[-2])  # 最後から2番目
                        months = int(groups[-1])  # 最後
                        max_months = years * 12 + months
                        item["min_loan_term_months"] = 6  # 最低6ヶ月
                        item["max_loan_term_months"] = max_months
                        
                        logger.info(
                            f"✅ 融資期間（教育カードローン）: {item.get('min_loan_term_months', 0)}ヶ月 - {item.get('max_loan_term_months', 0)}ヶ月"
                        )
                        return

        # 基底クラスの共通処理にフォールバック
        super()._extract_loan_periods(soup, item)

    def _extract_guarantor_requirements(self, full_text: str) -> str:
        """教育カードローンの保証人要件を抽出"""
        if "保証人" in full_text and ("不要" in full_text or "ジャックス" in full_text):
            return "原則不要（ジャックスが保証）"
        elif "ジャックス" in full_text:
            return "ジャックスが保証"
        return ""

    def _extract_special_features(self, full_text: str) -> str:
        """教育カードローン特有の商品特徴を抽出"""
        features = ExtractionUtils.extract_common_features(full_text)
        
        # 教育カードローン特有の特徴
        if "カードローン" in full_text:
            features.append("カードローン型（限度額内で自由利用）")
        if "ATM" in full_text and "1,000円" in full_text:
            features.append("ATMで1,000円から借入可能")
        if "在学中" in full_text and "利息のみ" in full_text:
            features.append("在学中は利息のみ返済可能")
        if "WEB完結" in full_text:
            features.append("WEB完結型利用可能")
        
        return "; ".join(features)

    def _get_default_repayment_method(self) -> str:
        """教育カードローンのデフォルト返済方法"""
        return "利息のみ毎月返済（口座自動振替）"

    def _extract_repayment_method(self, soup, item):
        """教育カードローン特有の返済方法を抽出"""
        full_text = soup.get_text()

        repayment_methods = []
        if "毎月" in full_text and "日" in full_text and "利息" in full_text:
            if "5日" in full_text:
                repayment_methods.append("毎月5日に利息を自動振替")
            else:
                repayment_methods.append("毎月利息を自動振替")
        if "契約期限時" in full_text and "残高" in full_text:
            repayment_methods.append("契約期限時の残高に応じた返済")
        if "ATM" in full_text and "随時返済" in full_text:
            repayment_methods.append("ATMで随時返済可能")

        if not repayment_methods:
            repayment_methods.append(self._get_default_repayment_method())

        item["repayment_method"] = "; ".join(repayment_methods)
        logger.info(f"✅ 返済方法: {item['repayment_method']}")


def main():
    """テスト実行"""
    import logging
    logging.basicConfig(level=logging.INFO)

    scraper = AomorimichinokuEducationCardScraper()
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