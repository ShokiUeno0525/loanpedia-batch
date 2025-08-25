"""
青森みちのく銀行教育カードローンスクレイピング

教育カードローンの情報を抽出
"""

import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AomorimichinokuEducationCardScraper:
    """
    青森みちのく銀行の教育カードローン情報をHTMLから抽出するスクレイパー
    requests + BeautifulSoupによる実装
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def scrape_loan_info(self, url="https://www.am-bk.co.jp/kojin/loan/kyouikuloan/"):
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
                "loan_type": "教育ローン",
                "category": "教育カードローン",
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
            if "教育カードローン" in title_text or "カードローン" in title_text:
                return title_text

        h1_elem = soup.find("h1")
        if h1_elem:
            h1_text = h1_elem.get_text().strip()
            if "教育カードローン" in h1_text or "カードローン" in h1_text:
                return h1_text

        return "青森みちのく教育カードローン"

    def _extract_interest_rates(self, soup, item):
        """金利情報を抽出（カードローン特化）"""
        full_text = soup.get_text()

        # カードローン特有の金利パターンを検索
        # 実際のパターン: "年4.2％" と "年5.4％から引下後年4.3％〜年4.9％"
        rate_patterns = [
            (r"年\s*(\d+\.\d+)\s*[%％].*?年\s*(\d+\.\d+)\s*[%％]\s*から\s*引下後\s*年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "WEB完結型・来店型金利"),
            (r"年\s*(\d+\.\d+)\s*[%％]\s*から\s*引下後\s*年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "引下後金利範囲"),
            (r"年\s*(\d+\.\d+)\s*[%％].*?年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "基本金利範囲"),
            (r"年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "金利範囲"),
        ]

        for pattern, description in rate_patterns:
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
                elif len(groups) == 2:  # 基本範囲
                    item["min_interest_rate"] = float(groups[0])
                    item["max_interest_rate"] = float(groups[1])
                    logger.info(
                        f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    return

        # デフォルト値（教育カードローンの一般的な金利）
        item["min_interest_rate"] = 4.2
        item["max_interest_rate"] = 4.9
        logger.info("⚠️ 金利情報が取得できませんでした。デフォルト値を使用")

    def _extract_loan_amounts(self, soup, item):
        """融資金額を抽出（カードローン特化）"""
        full_text = soup.get_text()

        amount_patterns = [
            r"最大\s*(\d+(?:,\d{3})*)\s*万円.*?WEB完結型.*?上限\s*(\d+(?:,\d{3})*)\s*万円",
            r"最大\s*(\d+(?:,\d{3})*)\s*万円.*?WEB完結型.*?(\d+(?:,\d{3})*)\s*万円.*?上限",
            r"最高\s*(\d+(?:,\d{3})*)\s*万円",
            r"最大\s*(\d+(?:,\d{3})*)\s*万円",
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                if len(match.groups()) == 2:
                    # WEB完結型の制限を考慮
                    max_amount = int(match.group(1).replace(",", ""))
                    web_limit = int(match.group(2).replace(",", ""))
                    item["min_loan_amount"] = 500000  # 50万円
                    # WEB完結型の制限がある場合は、より低い方を採用
                    item["max_loan_amount"] = min(max_amount, web_limit) * 10000
                else:
                    item["min_loan_amount"] = 500000  # 50万円
                    item["max_loan_amount"] = int(match.group(1).replace(",", "")) * 10000
                
                logger.info(
                    f"✅ 融資金額範囲: {item['min_loan_amount']:,}円 - {item['max_loan_amount']:,}円"
                )
                return

        # デフォルト値（教育カードローンの一般的な融資額）
        item["min_loan_amount"] = 500000  # 50万円
        item["max_loan_amount"] = 10000000  # 1,000万円
        logger.info("⚠️ 融資金額が取得できませんでした。デフォルト値を使用")

    def _extract_loan_periods(self, soup, item):
        """融資期間を抽出（カードローン特化）"""
        full_text = soup.get_text()

        period_patterns = [
            (r"最大\s*(\d+)\s*年\s*(\d+)\s*[ヵヶ]月", "年月形式"),
            (r"入学前\s*(\d+)\s*[ヵヶ]月.*?最大\s*(\d+)\s*年\s*(\d+)\s*[ヵヶ]月", "詳細期間"),
            (r"最大\s*(\d+)\s*年", "最長年数"),
            (r"(\d+)\s*年\s*(\d+)\s*[ヵヶ]月", "年月形式"),
        ]

        for pattern, pattern_type in period_patterns:
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
                elif pattern_type == "最長年数":
                    item["min_loan_term_months"] = 6
                    item["max_loan_term_months"] = int(match.group(1)) * 12

                logger.info(
                    f"✅ 融資期間: {item.get('min_loan_term_months', 0)}ヶ月 - {item.get('max_loan_term_months', 0)}ヶ月"
                )
                return

        # デフォルト値（教育カードローンの一般的な期間）
        item["min_loan_term_months"] = 6  # 6ヶ月
        item["max_loan_term_months"] = 114  # 9年6ヶ月
        logger.info("⚠️ 融資期間が取得できませんでした。デフォルト値を使用")

    def _extract_age_requirements(self, soup, item):
        """年齢制限を抽出"""
        full_text = soup.get_text()

        age_patterns = [
            r"申込時.*?満(\d+)歳以上.*?完済時.*?年齢.*?満(\d+)歳未満",
            r"(\d+)歳以上.*?完済時.*?(\d+)歳未満",
            r"満(\d+)歳以上.*?満(\d+)歳未満",
            r"満(\d+)歳以上.*?満(\d+)歳以下",
            r"(\d+)歳以上.*?(\d+)歳以下",
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
        item["max_age"] = 74

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
        if "保証人" in full_text and ("不要" in full_text or "ジャックス" in full_text):
            guarantor_text = "原則不要（ジャックスが保証）"
        elif "ジャックス" in full_text:
            guarantor_text = "ジャックスが保証"

        item["guarantor_requirements"] = guarantor_text

        # 商品特徴（カードローン特有）
        features = []
        if "カードローン" in full_text:
            features.append("カードローン型（限度額内で自由利用）")
        if "ATM" in full_text and "1,000円" in full_text:
            features.append("ATMで1,000円から借入可能")
        if "在学中" in full_text and "利息のみ" in full_text:
            features.append("在学中は利息のみ返済可能")
        if "保証人" in full_text and "担保" in full_text and "不要" in full_text:
            features.append("保証人・担保不要")
        if "WEB完結" in full_text:
            features.append("WEB完結型利用可能")
        if "随時返済" in full_text:
            features.append("ATMで随時返済可能")

        item["special_features"] = "; ".join(features)
        logger.info(f"✅ 商品特徴: {item['special_features']}")

    def _extract_repayment_method(self, soup, item):
        """返済方法を抽出（カードローン特化）"""
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
        if "自動振替" in full_text:
            repayment_methods.append("口座自動振替")

        if not repayment_methods:
            repayment_methods.append("利息のみ毎月返済（口座自動振替）")

        item["repayment_method"] = "; ".join(repayment_methods)
        logger.info(f"✅ 返済方法: {item['repayment_method']}")


def main():
    """テスト実行"""
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
