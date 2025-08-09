"""
青森県信用組合マイカーローンスクレイピング（requests + BeautifulSoup版）

HTMLページからローン情報を抽出
"""

import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AomorikenShinyoukumiaiScraper:
    """
    青森県信用組合のマイカーローン情報をHTMLから抽出するスクレイパー
    requests + BeautifulSoupによるシンプル実装
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_loan_info(self, url="https://www.aomoriken.shinkumi.co.jp/syouhin04.html#car"):
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
            title = soup.find('title').get_text() if soup.find('title') else "青森県信用組合マイカーローン"
            
            item = {
                "institution_name": "青森県信用組合",
                "institution_code": "2260",
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
            
            # マイカーローン特有のセクションを探す
            car_section = self._find_car_loan_section(soup)
            if car_section:
                section_text = car_section.get_text()
                self._extract_from_section(item, section_text)
            else:
                self._extract_from_full_content(item, main_content)
            
            return item
            
        except requests.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            return None
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return None

    def _find_car_loan_section(self, soup):
        """マイカーローンセクションを探す"""
        # IDやクラス名でマイカーローンセクションを探す
        car_keywords = ['car', 'マイカー', 'カー', '自動車']
        
        for keyword in car_keywords:
            # ID属性で探す
            section = soup.find(id=re.compile(keyword, re.IGNORECASE))
            if section:
                return section
            
            # テキスト内容で探す
            sections = soup.find_all(['div', 'section', 'article'])
            for section in sections:
                if keyword in section.get_text():
                    return section
        
        return None

    def _extract_from_section(self, item, section_text):
        """特定セクションから情報を抽出"""
        logger.info("マイカーローンセクションから情報抽出")
        
        # 金利情報の抽出
        rate_patterns = [
            r"年\s*(\d+\.\d+)\s*[%％]",
            r"金利\s*(\d+\.\d+)\s*[%％]",
            r"(\d+\.\d+)\s*[%％].*?年",
            r"固定.*?(\d+\.\d+)\s*[%％]",
            r"変動.*?(\d+\.\d+)\s*[%％]"
        ]
        
        self._extract_rates(item, section_text, rate_patterns)
        
        # 融資額情報の抽出
        amount_patterns = [
            r"融資.*?(\d+)\s*万円.*?(\d+)\s*万円",
            r"(\d+)\s*万円.*?以内",
            r"最高.*?(\d+)\s*万円"
        ]
        
        self._extract_amounts(item, section_text, amount_patterns)
        
        # 融資期間の抽出
        period_patterns = [
            r"(\d+)\s*年.*?以内",
            r"最長.*?(\d+)\s*年"
        ]
        
        self._extract_periods(item, section_text, period_patterns)

    def _extract_from_full_content(self, item, main_content):
        """全体コンテンツから情報を抽出"""
        logger.info("全体コンテンツから情報抽出")
        
        # より広範囲な検索パターンを使用
        rate_patterns = [
            r"年利\s*(\d+\.\d+)\s*[%％]",
            r"年\s*(\d+\.\d+)\s*[%％]",
            r"(\d+\.\d+)\s*[%％]"
        ]
        
        self._extract_rates(item, main_content, rate_patterns)
        
        amount_patterns = [
            r"(\d+)\s*万円",
            r"(\d+(?:,\d{3})*)\s*円"
        ]
        
        self._extract_amounts(item, main_content, amount_patterns)
        
        period_patterns = [
            r"(\d+)\s*年"
        ]
        
        self._extract_periods(item, main_content, period_patterns)

    def _extract_rates(self, item, text, patterns):
        """金利情報を抽出"""
        found_rates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
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

    def _extract_amounts(self, item, text, patterns):
        """融資額情報を抽出"""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if "万円" in pattern:
                        # 万円単位
                        amounts = [int(match.replace(",", "")) * 10000 for match in matches if match.replace(",", "").isdigit()]
                    else:
                        # 円単位
                        amounts = [int(match.replace(",", "")) for match in matches if match.replace(",", "").isdigit()]
                    
                    if amounts:
                        item["min_loan_amount"] = min(amounts)
                        item["max_loan_amount"] = max(amounts)
                        logger.info(f"✅ 融資額抽出: {item['min_loan_amount']}円 - {item['max_loan_amount']}円")
                        break
                except (ValueError, TypeError):
                    continue

    def _extract_periods(self, item, text, patterns):
        """融資期間を抽出"""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    years = [int(match) for match in matches if match.isdigit()]
                    if years:
                        max_years = max(years)
                        item["max_loan_period_months"] = max_years * 12
                        logger.info(f"✅ 融資期間抽出: 最長{max_years}年")
                        break
                except (ValueError, TypeError):
                    continue


def main():
    """テスト実行"""
    logging.basicConfig(level=logging.INFO)
    
    scraper = AomorikenShinyoukumiaiScraper()
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