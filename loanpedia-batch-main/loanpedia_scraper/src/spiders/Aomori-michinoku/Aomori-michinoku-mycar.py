import scrapy
import hashlib
from datetime import datetime
from ...items import LoanItem


class AomorimichinokuBankSpider(scrapy.Spider):
    name = "aomorimichinoku_bank"
    allowed_domains = ["www.am-bk.co.jp"]
    start_urls = ["https://www.am-bk.co.jp/kojin/loan/mycarloan/"]

    def parse(self, response):
        self.logger.info(f"Parsing {response.url}")
        
        # ページの基本情報を表示
        title = response.css('title::text').get()
        self.logger.info(f"Page title: {title}")
        
        # 主要なテキスト内容を表示
        main_content = response.css('body *::text').getall()
        loan_keywords = ['金利', '融資', '借入', 'ローン', '条件', '期間', '保証', '返済方法', '書類']
        relevant_texts = [text.strip() for text in main_content 
                         if any(keyword in text for keyword in loan_keywords) and text.strip()]
        
        self.logger.info("Found loan-related content:")
        for i, text in enumerate(relevant_texts[:10]):  # 最初の10件のみ表示
            self.logger.info(f"{i+1}: {text}")
        
        # HTMLの一部を保存してデバッグ
        html_snippet = response.css('body').get()[:1000] if response.css('body').get() else ""
        self.logger.info(f"HTML snippet: {html_snippet}")
        
        # 基本的なアイテムを作成
        item = LoanItem()
        item['product_name'] = title or "マイカーローン"
        item['url'] = response.url
        item['scraped_at'] = datetime.now().isoformat()
        item['raw_html'] = response.text
        item['content_hash'] = hashlib.md5(response.text.encode()).hexdigest()
        
        yield item
