import scrapy
import hashlib 
from datetime import datetime
from ...items import LoanItem
from io import BytesIO
from pdfminer.high_level import extract_text 

class TououSinkinMycarSpider(scrapy.Spider):
    name = "touou_sinkin_mycar"
    allowed_domains = ["https://www.shinkin.co.jp/toshin/index.html"]
    start_urls = ["https://www.shinkin.co.jp/toshin/01-2-07.html"]

    def parse(self, response):
        self.logger.info(f"Parsing {response.url}")

        # ページの基本情報を表示
        title = response.css('title::text').get()
        self.logger.info(f"Page title: {title}")

        # キーワード抽出
        main_content = response.css('body *::text').getall()
        loan_keywords = ['金利', '融資', '借入', 'ローン', '条件', '期間', '保証', '返済方法', '書類']
        relevant_texts = [text.strip () for text in main_content
                          if any(keyword in text for keyword in loan_keywords) and text.strip()]

        self.logger.info("Found loan-related content:")
        for i, text in enumerate(relevant_texts[:10]):
            self.logger.info(f"{i+1}: {text}")

        # アイテム作成
        item = LoanItem()
        item['product_name'] = title or "マイカーローン"
        item['url'] = response.url
        item['scraped_at'] = datetime.now().isoformat()
        item['raw_html'] = response.text
        item['content_hash'] = hashlib.md5(response.text.encode()).hexdigest()

        yield item