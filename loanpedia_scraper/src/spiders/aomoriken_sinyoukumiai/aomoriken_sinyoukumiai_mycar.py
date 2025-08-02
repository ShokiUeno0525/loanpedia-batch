import scrapy
import hashlib
from datetime import datetime
from ...items import LoanItem

class AomorikenSinyoukumiaiMycarSpider(scrapy.Spider):
    name = "aomoriken_sinyoukumiai_mycar"
    allowed_domains = ["https://www.aomoriken.shinkumi.co.jp/index.html"]
    start_urls = ["https://www.aomoriken.shinkumi.co.jp/syouhin04.html#car"]

    def parse(self, response):
        self.logger.info(f"Parsing {response.url}")

        # ページの基本情報を表示
        title = response.css('title::text').get()
        self.logger.info(f"Page title: {title}")

        # アイテム作成
        item = LoanItem()
        item['product_name'] = title or "マイカーローン"
        item['url'] = response.url
        item['scraped_at'] = datetime.now().isoformat()
        item['raw_html'] = response.text
        item['content_hash'] = hashlib.md5(response.text.encode()).hexdigest()

        yield item
