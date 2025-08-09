"""
東奥信用金庫マイカーローンスクレイピング（requests + BeautifulSoup版）

HTMLページからローン情報を抽出
"""

import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TououShinkinScraper:
    """
    東奥信用金庫のマイカーローン情報をHTMLから抽出するスクレイパー
    requests + BeautifulSoupによるシンプル実装
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_loan_info(self, url="https://www.shinkin.co.jp/toshin/01-2-07.html"):
        """
        指定URLからローン情報をスクレイピング
        
        Returns:
            dict: 抽出されたローン情報
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 基本情報
            title = soup.find('title').get_text() if soup.find('title') else "東奥信用金庫マイカーローン"
            
            item = {
                "institution_name": "東奥信用金庫",
                "institution_code": "1251",
                "product_name": title,
                "loan_category": "マイカーローン",
                "source_url": url,
                "page_title": title,
                "html_content": response.text,
                "content_hash": hashlib.md5(response.text.encode()).hexdigest(),
                "scraped_at": datetime.now().isoformat()
            }
            
            # ページの内容からローン関連情報を抽出
            main_content = soup.get_text()
            
            # キーワード抽出
            loan_keywords = ['金利', '融資', '借入', 'ローン', '条件', '期間', '保証', '返済方法', '書類']
            relevant_texts = []
            
            for text in soup.stripped_strings:
                if any(keyword in text for keyword in loan_keywords) and text.strip():
                    relevant_texts.append(text.strip())
            
            logger.info(f"Found {len(relevant_texts)} loan-related content pieces")
            
            # 金利情報の抽出
            self._extract_interest_rates(item, main_content, relevant_texts)
            
            # 融資額情報の抽出
            self._extract_loan_amounts(item, main_content, relevant_texts)
            
            # 融資期間の抽出
            self._extract_loan_periods(item, main_content, relevant_texts)
            
            # その他の条件抽出
            self._extract_conditions(item, main_content, relevant_texts)
            
            return item
            
        except requests.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            return None
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return None

    def _extract_interest_rates(self, item, main_content, relevant_texts):
        """金利情報を抽出"""
        rate_patterns = [
            r"年\s*(\d+\.\d+)\s*[%％]",
            r"金利\s*(\d+\.\d+)\s*[%％]",
            r"(\d+\.\d+)\s*[%％].*?年",
            r"固定.*?(\d+\.\d+)\s*[%％]",
            r"変動.*?(\d+\.\d+)\s*[%％]"
        ]
        
        found_rates = []
        for pattern in rate_patterns:
            matches = re.findall(pattern, main_content, re.IGNORECASE)
            found_rates.extend(matches)
        
        if found_rates:
            try:
                numeric_rates = [float(rate) for rate in found_rates if rate.replace(".", "").isdigit()]
                if numeric_rates:
                    item["min_interest_rate"] = min(numeric_rates)
                    item["max_interest_rate"] = max(numeric_rates)
                    logger.info(f"✅ 金利抽出: {item['min_interest_rate']}% - {item['max_interest_rate']}%")
            except (ValueError, TypeError):
                pass

    def _extract_loan_amounts(self, item, main_content, relevant_texts):
        """融資額情報を抽出"""
        amount_patterns = [
            r"融資.*?(\d+)\s*万円.*?(\d+)\s*万円",
            r"(\d+)\s*万円.*?以内",
            r"最高.*?(\d+)\s*万円",
            r"(\d+)\s*万円.*?限度"
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, main_content, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple) and len(matches[0]) == 2:
                    # 範囲パターン
                    item["min_loan_amount"] = int(matches[0][0]) * 10000
                    item["max_loan_amount"] = int(matches[0][1]) * 10000
                else:
                    # 最大のみ
                    max_amount = int(matches[0] if isinstance(matches[0], str) else matches[0][0])
                    item["max_loan_amount"] = max_amount * 10000
                logger.info(f"✅ 融資額抽出: {item.get('min_loan_amount', 0)}円 - {item.get('max_loan_amount')}円")
                break

    def _extract_loan_periods(self, item, main_content, relevant_texts):
        """融資期間を抽出"""
        period_patterns = [
            r"(\d+)\s*年.*?以内",
            r"最長.*?(\d+)\s*年",
            r"期間.*?(\d+)\s*年",
            r"(\d+)\s*ヶ月.*?(\d+)\s*ヶ月"
        ]
        
        for pattern in period_patterns:
            matches = re.findall(pattern, main_content, re.IGNORECASE)
            if matches:
                if "年" in pattern:
                    max_years = int(matches[0] if isinstance(matches[0], str) else matches[0][0])
                    item["max_loan_period_months"] = max_years * 12
                    logger.info(f"✅ 融資期間抽出: 最長{max_years}年")
                else:
                    # 月単位
                    if isinstance(matches[0], tuple):
                        item["min_loan_period_months"] = int(matches[0][0])
                        item["max_loan_period_months"] = int(matches[0][1])
                    logger.info(f"✅ 融資期間抽出: {item.get('min_loan_period_months')}ヶ月 - {item.get('max_loan_period_months')}ヶ月")
                break

    def _extract_conditions(self, item, main_content, relevant_texts):
        """その他の条件を抽出"""
        # 年齢条件
        age_pattern = r"(\d+)歳.*?(\d+)歳"
        age_matches = re.search(age_pattern, main_content)
        if age_matches:
            item["min_age"] = int(age_matches.group(1))
            item["max_age"] = int(age_matches.group(2))
        
        # 申込条件
        conditions = []
        if "勤続" in main_content:
            conditions.append("勤続年数条件あり")
        if "年収" in main_content:
            conditions.append("年収条件あり")
        if "保証" in main_content:
            conditions.append("保証会社による保証")
        if "営業区域" in main_content or "居住" in main_content:
            conditions.append("営業区域内居住・勤務")
            
        item["application_conditions"] = " / ".join(conditions) if conditions else "詳細は要問合せ"
        
        # 保証人情報
        if "保証人" in main_content and "不要" in main_content:
            item["guarantor_required"] = False
        elif "保証人" in main_content:
            item["guarantor_required"] = True
        
        logger.info("✅ 条件抽出完了")


def main():
    """テスト実行"""
    logging.basicConfig(level=logging.INFO)
    
    scraper = TououShinkinScraper()
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