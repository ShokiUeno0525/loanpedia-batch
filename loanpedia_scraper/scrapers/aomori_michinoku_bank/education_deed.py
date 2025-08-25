"""
青森みちのく銀行教育ローンスクレイピング（証書貸付型）

教育ローン〈証書貸付型〉の情報を抽出
"""

import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AomorimichinokuEducationDeedScraper:
    """
    青森みちのく銀行の教育ローン（証書貸付型）情報をHTMLから抽出するスクレイパー
    requests + BeautifulSoupによる実装
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def scrape_loan_info(self, url="https://www.am-bk.co.jp/kojin/loan/certificate/"):
        """
        指定URLから教育ローン（証書貸付型）情報をスクレイピング（データモデル準拠）

        Returns:
            dict: データモデルに準拠した抽出情報
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # データモデル準拠の基本情報
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
                "category": "教育ローン",
                "interest_type": "固定金利・変動金利",
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
            if "教育ローン" in title_text or "証書貸付" in title_text:
                return title_text

        h1_elem = soup.find("h1")
        if h1_elem:
            h1_text = h1_elem.get_text().strip()
            if "教育ローン" in h1_text or "証書貸付" in h1_text:
                return h1_text

        return "青森みちのく教育ローン〈証書貸付型〉"

    def _extract_interest_rates(self, soup, item):
        """金利情報を抽出（証書貸付型特化）"""
        full_text = soup.get_text()

        # 証書貸付型特有の金利パターンを検索
        rate_patterns = [
            (
                r"年\s*(\d+\.\d+)\s*[%％]\s*から\s*引下後\s*年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]",
                "優遇後金利範囲",
            ),
            (
                r"年\s*(\d+\.\d+)\s*[%％]\s*[〜～から]\s*[引下後]*\s*年\s*(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)\s*[%％]",
                "優遇後金利範囲",
            ),
            (
                r"変動金利.*?年\s*(\d+\.\d+)\s*[%％].*?年\s*(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)\s*[%％]",
                "変動金利範囲",
            ),
            (r"年\s*(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "基本金利範囲"),
        ]

        for pattern, description in rate_patterns:
            match = re.search(pattern, full_text)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # 基準金利 + 優遇後範囲
                    item["min_interest_rate"] = float(groups[1])
                    item["max_interest_rate"] = float(groups[2])
                    logger.info(
                        f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    return
                elif len(groups) == 2:  # 範囲のみ
                    item["min_interest_rate"] = float(groups[0])
                    item["max_interest_rate"] = float(groups[1])
                    logger.info(
                        f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    return

        # テーブルから金利を抽出
        self._extract_rates_from_table(soup, item)

        # デフォルト値（証書貸付型の一般的な金利）
        if "min_interest_rate" not in item:
            item["min_interest_rate"] = 1.8
            item["max_interest_rate"] = 3.0
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
                    if any(
                        keyword in cell_text for keyword in ["金利", "利率", "年利"]
                    ):
                        if i + 1 < len(cells):
                            next_cell = cells[i + 1].get_text().strip()
                            rate_match = re.search(
                                r"(\d+\.\d+)[〜～]?(\d+\.\d+)?[%％]", next_cell
                            )
                            if rate_match:
                                if rate_match.group(2):  # 範囲がある場合
                                    item["min_interest_rate"] = float(
                                        rate_match.group(1)
                                    )
                                    item["max_interest_rate"] = float(
                                        rate_match.group(2)
                                    )
                                else:  # 単一の値の場合
                                    item["min_interest_rate"] = float(
                                        rate_match.group(1)
                                    )
                                    item["max_interest_rate"] = float(
                                        rate_match.group(1)
                                    )
                                logger.info(
                                    f"✅ テーブルから金利抽出: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                                )
                                return

    def _extract_loan_amounts(self, soup, item):
        """融資金額を抽出（証書貸付型特化）"""
        full_text = soup.get_text()

        amount_patterns = [
            r"(\d+(?:,\d{3})*)\s*万円\s*以上\s*(\d+(?:,\d{3})*)\s*万円\s*以内",
            r"(\d+)\s*万円\s*～\s*(\d+(?:,\d{3})*)\s*万円",
            r"最高\s*(\d+(?:,\d{3})*)\s*万円",
            r"(\d+)\s*万円\s*まで",
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, full_text)
            if match:
                if len(match.groups()) == 2:
                    item["min_loan_amount"] = (
                        int(match.group(1).replace(",", "")) * 10000
                    )
                    item["max_loan_amount"] = (
                        int(match.group(2).replace(",", "")) * 10000
                    )
                else:
                    item["min_loan_amount"] = 100000  # 10万円
                    item["max_loan_amount"] = (
                        int(match.group(1).replace(",", "")) * 10000
                    )
                logger.info(
                    f"✅ 融資金額範囲: {item['min_loan_amount']:,}円 - {item['max_loan_amount']:,}円"
                )
                return

        # デフォルト値（証書貸付型の一般的な融資額）
        item["min_loan_amount"] = 100000  # 10万円
        item["max_loan_amount"] = 5000000  # 500万円
        logger.info("⚠️ 融資金額が取得できませんでした。デフォルト値を使用")

    def _extract_loan_periods(self, soup, item):
        """融資期間を抽出（証書貸付型特化）"""
        full_text = soup.get_text()

        period_patterns = [
            (r"(\d+)\s*[ヵヶ]月\s*以上\s*(\d+)\s*年\s*以内", "月年混合"),
            (r"(\d+)\s*年\s*以上\s*(\d+)\s*年\s*以内", "年範囲"),
            (r"最長\s*(\d+)\s*年", "最長年数"),
            (r"(\d+)\s*年\s*以内", "年以内"),
        ]

        for pattern, pattern_type in period_patterns:
            match = re.search(pattern, full_text)
            if match:
                if pattern_type == "月年混合":
                    item["min_loan_term_months"] = int(match.group(1))
                    item["max_loan_term_months"] = int(match.group(2)) * 12
                elif pattern_type == "年範囲":
                    item["min_loan_term_months"] = int(match.group(1)) * 12
                    item["max_loan_term_months"] = int(match.group(2)) * 12
                elif pattern_type in ["最長年数", "年以内"]:
                    item["min_loan_term_months"] = 6  # 最低6ヶ月
                    item["max_loan_term_months"] = int(match.group(1)) * 12

                logger.info(
                    f"✅ 融資期間: {item.get('min_loan_term_months', 0)}ヶ月 - {item.get('max_loan_term_months', 0)}ヶ月"
                )
                return

        # デフォルト値（証書貸付型の一般的な期間）
        item["min_loan_term_months"] = 6  # 6ヶ月
        item["max_loan_term_months"] = 180  # 15年
        logger.info("⚠️ 融資期間が取得できませんでした。デフォルト値を使用")

    def _extract_age_requirements(self, soup, item):
        """年齢制限を抽出"""
        full_text = soup.get_text()

        age_patterns = [
            r"満(\d+)歳以上.*?ご返済完了時の年齢が満(\d+)歳未満",
            r"満(\d+)歳以上.*?満(\d+)歳未満",
            r"満(\d+)歳以上.*?満(\d+)歳以下",
            r"(\d+)歳以上.*?(\d+)歳以下",
            r"(\d+)歳以上.*?(\d+)歳未満",
            r"年齢.*?(\d+)歳.*?(\d+)歳",
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
        item["max_age"] = 70

    def _extract_detailed_requirements(self, soup, item):
        """収入条件、保証人要件、商品特徴を抽出（証書貸付型特化）"""
        full_text = soup.get_text()

        # 収入条件
        income_requirements = []
        if "安定した収入" in full_text:
            income_requirements.append("安定した収入があること")
        if "継続的な収入" in full_text:
            income_requirements.append("継続的な収入があること")
        if "給与所得者" in full_text or "自営業者" in full_text:
            income_requirements.append("給与所得者または自営業者")

        item["income_requirements"] = "; ".join(income_requirements)

        # 保証人要件
        guarantor_text = ""
        if "保証人" in full_text:
            if "原則不要" in full_text or "原則として不要" in full_text:
                guarantor_text = "原則不要（保証会社が保証）"
            elif "保証会社" in full_text:
                guarantor_text = "保証会社による保証"
            else:
                guarantor_text = "保証会社の審査により決定"

        item["guarantor_requirements"] = guarantor_text

        # 商品特徴（証書貸付型特有）
        features = []
        if "証書貸付" in full_text:
            features.append("証書貸付型（一括借入・分割返済）")
        if "固定金利" in full_text and "変動金利" in full_text:
            features.append("固定金利・変動金利選択可能")
        if "在学中" in full_text and "利息のみ" in full_text:
            features.append("在学中は利息のみ返済可能")
        if "据置期間" in full_text:
            features.append("据置期間設定可能")
        if "繰上返済" in full_text:
            if "無料" in full_text:
                features.append("繰上返済手数料無料")
            else:
                features.append("繰上返済手数料あり")
        if "取引内容" in full_text and "金利優遇" in full_text:
            features.append("取引内容に応じた金利優遇")
        if "教育関連" in full_text:
            features.append("教育関連資金全般に利用可能")

        item["special_features"] = "; ".join(features)
        logger.info(f"✅ 商品特徴: {item['special_features']}")

    def _extract_repayment_method(self, soup, item):
        """返済方法を抽出（証書貸付型特化）"""
        full_text = soup.get_text()

        repayment_methods = []
        if "元利均等返済" in full_text:
            repayment_methods.append("元利均等返済")
        if "元金均等返済" in full_text:
            repayment_methods.append("元金均等返済")
        if "自動振替" in full_text or "口座振替" in full_text:
            repayment_methods.append("口座自動振替")
        if "ボーナス返済" in full_text:
            repayment_methods.append("ボーナス返済併用可能")
        if "据置期間" in full_text:
            repayment_methods.append("据置期間中は利息のみ返済")

        if not repayment_methods:
            repayment_methods.append("元利均等返済（口座自動振替）")

        item["repayment_method"] = "; ".join(repayment_methods)
        logger.info(f"✅ 返済方法: {item['repayment_method']}")


def main():
    """テスト実行"""
    logging.basicConfig(level=logging.INFO)

    scraper = AomorimichinokuEducationDeedScraper()
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
