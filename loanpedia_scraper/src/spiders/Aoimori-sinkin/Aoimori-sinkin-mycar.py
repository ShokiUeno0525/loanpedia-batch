import scrapy
import hashlib
from datetime import datetime
from ...items import LoanItem
from io import BytesIO
from pdfminer.high_level import extract_text

class AoimoriSinkinMycarSpider(scrapy.Spider):
  name = "aomoimori_sinyoukinko"
  allowed_domains = ["https://www.aoimorishinkin.co.jp/"]
  start_urls = ["https://www.aoimorishinkin.co.jp/pdf/poster_mycarroan_241010.pdf"]

  def parse(self, response):
    self.logger.info(f"Parsing {response.url}")
    
    # PDFのバイナリデータからテキスト抽出
    pdf_text = extract_text(BytesIO(response.body))
    self.logger.info(f"PDF text: {pdf_text[:500]}")  # 最初の500文字だけログ出力
    
    # キーワード抽出
    loan_keywords = ['金利', '融資', '借入', 'ローン', '条件', '期間', '保証', '返済方法', '書類']
    relevant_texts = [line for line in pdf_text.splitlines() if any(k in line for k in loan_keywords)]

    self.logger.info("Found loan-related content:")
    for i, text in enumerate(relevant_texts[:10]):
        self.logger.info(f"{i+1}: {text}")

    # アイテム作成
    item = LoanItem()
    item['product_name'] = "マイカーローン"
    item['url'] = response.url
    item['scraped_at'] = datetime.now().isoformat()
    item['raw_html'] = pdf_text
    item['content_hash'] = hashlib.md5(pdf_text.encode()).hexdigest()

    yield item