"""
青森みちのく銀行マイカーローンスクレイピング（BeautifulSoup版）

Scrapyからrequests + BeautifulSoupに変更したシンプル版
"""

import hashlib
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AomorimichinokuBankScraper:
    """
    青森みちのく銀行のマイカーローン情報をHTMLから抽出するスクレイパー
    requests + BeautifulSoupによるシンプル実装
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_loan_info(self, url="https://www.am-bk.co.jp/kojin/loan/mycarloan/"):
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
            item = {
                "institution_name": "青森みちのく銀行",
                "institution_code": "0117",
                "product_name": soup.find('title').get_text() if soup.find('title') else "青森みちのくマイカーローン",
                "loan_category": "マイカーローン",
                "source_url": url,
                "html_content": response.text,
                "content_hash": hashlib.md5(response.text.encode()).hexdigest(),
                "scraped_at": datetime.now().isoformat()
            }
            
            # 金利情報を抽出（.kinri-wrp要素から）
            kinri_elements = soup.select('.kinri-wrp')
            for elem in kinri_elements:
                text = elem.get_text()
                
                # 変動金利範囲パターン
                range_match = re.search(r"変動金利.*?(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)\s*[%％]", text)
                if range_match:
                    item["min_interest_rate"] = float(range_match.group(1))
                    item["max_interest_rate"] = float(range_match.group(2))
                    logger.info(f"✅ 金利範囲: {item['min_interest_rate']}% - {item['max_interest_rate']}%")
                    break
                
                # <b>タグから直接抽出
                bold_elem = elem.find('b')
                if bold_elem and "〜" in bold_elem.get_text():
                    bold_text = bold_elem.get_text()
                    range_match = re.search(r"(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)", bold_text)
                    if range_match:
                        item["min_interest_rate"] = float(range_match.group(1))
                        item["max_interest_rate"] = float(range_match.group(2))
                        logger.info(f"✅ 金利範囲（bold）: {item['min_interest_rate']}% - {item['max_interest_rate']}%")
                        break
            
            # 融資金額を抽出（.c-text要素から）
            c_text_elements = soup.select('.c-text')
            for elem in c_text_elements:
                text = elem.get_text()
                # "1万円以上1,000万円以内" パターン
                range_match = re.search(r"(\d+(?:,\d{3})*)\s*万円以上.*?(\d+(?:,\d{3})*)\s*万円以内", text)
                if range_match:
                    item["min_loan_amount"] = int(range_match.group(1).replace(",", "")) * 10000
                    item["max_loan_amount"] = int(range_match.group(2).replace(",", "")) * 10000
                    logger.info(f"✅ 融資金額範囲: {item['min_loan_amount']}円 - {item['max_loan_amount']}円")
                    break
            
            # テーブルから情報を一括取得
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
            
            # 全文検索による追加抽出
            full_text = soup.get_text()
            
            # 金利が取得できてない場合
            if "min_interest_rate" not in item:
                rate_patterns = [
                    (r"変動金利\s*年?\s*(\d+\.\d+)\s*[%％]?\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "変動金利範囲"),
                    (r"年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "年率範囲"),
                ]
                
                for pattern, description in rate_patterns:
                    matches = re.findall(pattern, full_text)
                    if matches:
                        if len(matches[0]) == 2:
                            item["min_interest_rate"] = float(matches[0][0])
                            item["max_interest_rate"] = float(matches[0][1])
                            logger.info(f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%")
                        break
            
            # 融資期間を抽出
            period_patterns = [
                (r"(\d+)\s*年\s*～\s*(\d+)\s*年", "year_range"),
                (r"最長\s*(\d+)\s*年", "max_year"),
            ]
            
            for pattern, pattern_type in period_patterns:
                matches = re.findall(pattern, full_text)
                if matches:
                    if pattern_type == "year_range":
                        item["min_loan_period_months"] = int(matches[0][0]) * 12
                        item["max_loan_period_months"] = int(matches[0][1]) * 12
                        logger.info(f"✅ 融資期間範囲: {item['min_loan_period_months']}ヶ月 - {item['max_loan_period_months']}ヶ月")
                    elif pattern_type == "max_year":
                        item["max_loan_period_months"] = int(matches[0]) * 12
                        logger.info(f"✅ 最長融資期間: {item['max_loan_period_months']}ヶ月")
                    break
            
            return item
            
        except requests.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            return None
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            return None


def main():
    """テスト実行"""
    logging.basicConfig(level=logging.INFO)
    
    scraper = AomorimichinokuBankScraper()
    result = scraper.scrap_loan_info()
    
    if result:
        print("スクレイピング成功!")
        print(f"商品名: {result.get('product_name')}")
        print(f"金利: {result.get('min_interest_rate')}% - {result.get('max_interest_rate')}%")
        print(f"融資額: {result.get('min_loan_amount')}円 - {result.get('max_loan_amount')}円")
    else:
        print("スクレイピング失敗")


if __name__ == "__main__":
    main()