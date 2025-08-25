# -*- coding: utf-8 -*-
"""
青森みちのく銀行カードローンスクレイピング

通常カードローンの情報を抽出
"""

import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AomorimichinokuCardScraper:
    """
    青森みちのく銀行のカードローン情報をHTMLから抽出するスクレイパー
    requests + BeautifulSoupによる実装
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def scrape_loan_info(self, url="https://www.am-bk.co.jp/kojin/loan/cardloan/"):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            item = {
                # financial_institutions テーブル用データ
                "institution_code": "0117",
                "institution_name": "青森みちのく銀行",
                "website_url": "https://www.am-bk.co.jp/",
                "institution_type": "銀行",
                # raw_loan_data テーブル用データ
                "source_url": url,
                "html_content": response.text,
                "extracted_text": soup.get_text().strip(),
                "content_hash": hashlib.md5(response.text.encode()).hexdigest(),
                "scraping_status": "success",
                "scraped_at": datetime.now().isoformat(),
                # loan_products テーブル用の基本データ
                "product_name": self._extract_product_name(soup),
                "loan_type": "カードローン",
                "category": "カードローン",
                "interest_type": "変動金利",
            }

            # 金利情報を抽出
            self._extract_interest_rates(soup, item)

            # 融資金額を抽出
            self._extract_loan_amounts(soup, item)

            # 融資期間を抽出
            self._extract_loan_periods(soup, item)

            # 年齢制限の抽出
            self._extract_age_requirements(soup, item)

            # 収入・保証人・商品特徴の抽出
            self._extract_detailed_requirements(soup, item)

            # 返済方法の抽出
            self._extract_repayment_method(soup, item)

            return item

        except requests.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            return {"scraping_status": "failed", "error": str(e)}
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return {"scraping_status": "failed", "error": str(e)}

    def _extract_product_name(self, soup):
        """商品名を抽出"""
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text().strip()
            if "カードローン" in title_text:
                return title_text

        h1_elem = soup.find("h1")
        if h1_elem:
            h1_text = h1_elem.get_text().strip()
            if "カードローン" in h1_text:
                return h1_text

        return "青森みちのくカードローン"

    def _extract_interest_rates(self, soup, item):
        """金利情報を抽出（カードローン特化）"""
        full_text = soup.get_text()

        # カードローン特有の金利パターンを検索
        rate_patterns = [
            (r"年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "基本金利範囲"),
            (r"(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "金利範囲"),
            (r"金利.*?(\d+\.\d+)\s*[%％].*?(\d+\.\d+)\s*[%％]", "金利テーブル"),
        ]

        for pattern, description in rate_patterns:
            match = re.search(pattern, full_text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    item["min_interest_rate"] = float(groups[0])
                    item["max_interest_rate"] = float(groups[1])
                    logger.info(
                        f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    return

        # テーブルから金利を抽出
        self._extract_rates_from_table(soup, item)

        # デフォルト値（カードローンの一般的な金利）
        if "min_interest_rate" not in item:
            item["min_interest_rate"] = 2.4
            item["max_interest_rate"] = 14.5
            logger.info("⚠️ 金利情報が取得できませんでした。デフォルト値を使用")

    def _extract_rates_from_table(self, soup, item):
        """テーブルから金利情報を抽出"""
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text().strip()
                    # 金利テーブルの検索
                    if "%" in cell_text:
                        rate_match = re.search(r"(\d+\.\d+)\s*[%％]", cell_text)
                        if rate_match:
                            rate = float(rate_match.group(1))
                            if "min_interest_rate" not in item:
                                item["min_interest_rate"] = rate
                                item["max_interest_rate"] = rate
                            else:
                                item["min_interest_rate"] = min(item["min_interest_rate"], rate)
                                item["max_interest_rate"] = max(item["max_interest_rate"], rate)

        if "min_interest_rate" in item:
            logger.info(
                f"✅ テーブルから金利抽出: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
            )

    def _extract_loan_amounts(self, soup, item):
        """融資金額を抽出（カードローン特化）"""
        full_text = soup.get_text()

        amount_patterns = [
            r"(\d+)\s*万円\s*[〜～]\s*(\d+(?:,\d{3})*)\s*万円",
            r"最高\s*(\d+(?:,\d{3})*)\s*万円",
            r"限度額\s*(\d+(?:,\d{3})*)\s*万円",
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                if len(match.groups()) == 2:
                    item["min_loan_amount"] = int(match.group(1).replace(",", "")) * 10000
                    item["max_loan_amount"] = int(match.group(2).replace(",", "")) * 10000
                else:
                    item["min_loan_amount"] = 100000  # 10万円
                    item["max_loan_amount"] = int(match.group(1).replace(",", "")) * 10000
                
                logger.info(
                    f"✅ 融資金額範囲: {item['min_loan_amount']:,}円 - {item['max_loan_amount']:,}円"
                )
                return

        # デフォルト値（カードローンの一般的な融資額）
        item["min_loan_amount"] = 100000  # 10万円
        item["max_loan_amount"] = 10000000  # 1,000万円
        logger.info("⚠️ 融資金額が取得できませんでした。デフォルト値を使用")

    def _extract_loan_periods(self, soup, item):
        """融資期間を抽出（カードローン特化）"""
        full_text = soup.get_text()

        # カードローンは通常3年自動更新
        period_patterns = [
            (r"(\d+)\s*年.*?自動更新", "自動更新期間"),
            (r"契約期間.*?(\d+)\s*年", "契約期間"),
            (r"(\d+)\s*年間", "年間契約"),
        ]

        for pattern, pattern_type in period_patterns:
            match = re.search(pattern, full_text)
            if match:
                years = int(match.group(1))
                item["min_loan_term_months"] = 12  # 最低1年
                item["max_loan_term_months"] = years * 12
                
                logger.info(
                    f"✅ 融資期間: {item.get('min_loan_term_months', 0)}ヶ月 - {item.get('max_loan_term_months', 0)}ヶ月 ({pattern_type})"
                )
                return

        # デフォルト値（カードローンの一般的な期間）
        item["min_loan_term_months"] = 12  # 1年
        item["max_loan_term_months"] = 36  # 3年（自動更新）
        logger.info("⚠️ 融資期間が取得できませんでした。デフォルト値を使用")

    def _extract_age_requirements(self, soup, item):
        """年齢制限を抽出"""
        full_text = soup.get_text()

        age_patterns = [
            r"満(\d+)歳以上.*?満(\d+)歳未満",
            r"満(\d+)歳以上.*?満(\d+)歳以下", 
            r"(\d+)歳以上.*?(\d+)歳以下",
            r"(\d+)歳[〜～](\d+)歳",
        ]

        for pattern in age_patterns:
            match = re.search(pattern, full_text)
            if match:
                item["min_age"] = int(match.group(1))
                max_age_value = int(match.group(2))
                
                # 「未満」の場合は-1する（75歳未満 = 74歳以下）
                if "未満" in pattern:
                    item["max_age"] = max_age_value - 1
                else:
                    item["max_age"] = max_age_value

                logger.info(f"✅ 年齢制限: {item['min_age']}歳 - {item['max_age']}歳")
                return

        # デフォルト値
        item["min_age"] = 20
        item["max_age"] = 75

    def _extract_detailed_requirements(self, soup, item):
        """収入条件、保証人要件、商品特徴を抽出（カードローン特化）"""
        full_text = soup.get_text()

        # 収入条件
        income_requirements = []
        if "安定した収入" in full_text:
            income_requirements.append("安定した収入があること")
        if "継続的な収入" in full_text:
            income_requirements.append("継続的な収入があること")

        item["income_requirements"] = "; ".join(income_requirements) if income_requirements else "安定した収入があること"

        # 保証人要件
        guarantor_text = ""
        if "保証人" in full_text and ("不要" in full_text or "エム・ユー信用保証" in full_text):
            guarantor_text = "原則不要（エム・ユー信用保証が保証）"
        elif "保証会社" in full_text:
            guarantor_text = "保証会社による保証"

        item["guarantor_requirements"] = guarantor_text

        # 商品特徴（カードローン特有）
        features = []
        if "ATM" in full_text:
            features.append("ATMでいつでも借入・返済可能")
        if "1,000円" in full_text:
            features.append("1,000円から借入可能")
        if "担保" in full_text and "不要" in full_text:
            features.append("担保・保証人不要")
        if "WEB" in full_text and ("申込" in full_text or "完結" in full_text):
            features.append("WEB申込対応")
        if "自動更新" in full_text:
            features.append("3年自動更新")
        if "カード" in full_text and "専用" in full_text:
            features.append("専用カード発行")
        if "月" in full_text and "2,000円" in full_text:
            features.append("月々2,000円からの返済")

        item["special_features"] = "; ".join(features)
        logger.info(f"✅ 商品特徴: {item['special_features']}")

    def _extract_repayment_method(self, soup, item):
        """返済方法を抽出（カードローン特化）"""
        full_text = soup.get_text()

        repayment_methods = []
        if "毎月" in full_text and "自動振替" in full_text:
            repayment_methods.append("毎月自動振替")
        if "残高" in full_text and "応じ" in full_text:
            repayment_methods.append("残高に応じた返済額")
        if "ATM" in full_text and "返済" in full_text:
            repayment_methods.append("ATMで随時返済可能")
        if "2,000円" in full_text:
            repayment_methods.append("最低返済額2,000円から")

        if not repayment_methods:
            repayment_methods.append("残高スライド返済（口座自動振替）")

        item["repayment_method"] = "; ".join(repayment_methods)
        logger.info(f"✅ 返済方法: {item['repayment_method']}")


def main():
    """テスト実行"""
    logging.basicConfig(level=logging.INFO)

    scraper = AomorimichinokuCardScraper()
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