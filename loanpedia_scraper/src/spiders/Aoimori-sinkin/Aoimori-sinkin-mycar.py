import scrapy
import hashlib
from datetime import datetime
from ...items import LoanItem
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from pdf_scraper import PDFScraper

class AoimoriSinkinMycarSpider(scrapy.Spider):
    name = "aoimori_sinkin_mycar"
    allowed_domains = ["aoimorishinkin.co.jp"]
    start_urls = ["https://www.aoimorishinkin.co.jp/pdf/poster_mycarroan_241010.pdf"]

    def __init__(self):
        super().__init__()
        self.pdf_scraper = PDFScraper()

    def parse(self, response):
        self.logger.info(f"Parsing PDF: {response.url}")
        
        # PDFからテキスト抽出
        result = self.pdf_scraper._extract_text_from_bytes(response.body)
        
        if not result['success']:
            self.logger.error(f"PDF抽出失敗: {result['error']}")
            return
        
        pdf_text = result['text']
        self.logger.info(f"PDF text extracted: {len(pdf_text)} characters")
        self.logger.info(f"PDF content preview: {pdf_text[:300]}...")
        
        # ローン情報の自動抽出
        loan_info = self.pdf_scraper.extract_loan_info(pdf_text)
        
        # 基本アイテム作成
        item = LoanItem()
        item['institution_name'] = "青い森信用金庫"
        item['institution_code'] = "1105"
        item['product_name'] = "青い森しんきんカーライフプラン"
        item['loan_category'] = "マイカーローン"
        item['source_url'] = response.url
        item['page_title'] = "青い森信用金庫マイカーローン"
        item['html_content'] = pdf_text
        item['content_hash'] = hashlib.md5(pdf_text.encode()).hexdigest()
        item['scraped_at'] = datetime.now().isoformat()

        # PDF特有の情報抽出
        import re
        
        # 金利情報の詳細抽出
        interest_rates = []
        if loan_info['interest_rates']:
            interest_rates = loan_info['interest_rates']
        
        # PDFテキストから追加の金利情報を抽出
        rate_patterns = [
            r'金利.*?(\d+\.\d+)%',
            r'年利.*?(\d+\.\d+)%',
            r'(\d+\.\d+)%.*?年利',
            r'固定金利.*?(\d+\.\d+)',
            r'変動金利.*?(\d+\.\d+)'
        ]
        
        for pattern in rate_patterns:
            matches = re.findall(pattern, pdf_text, re.IGNORECASE | re.DOTALL)
            interest_rates.extend(matches)
        
        # 重複除去して最低金利を設定
        unique_rates = list(set(interest_rates))
        if unique_rates:
            try:
                min_rate = min([float(rate) for rate in unique_rates if rate.replace('.', '').isdigit()])
                item['interest_rate'] = f"{min_rate}%"
            except (ValueError, TypeError):
                item['interest_rate'] = unique_rates[0] + "%" if unique_rates else "要問合せ"
        else:
            item['interest_rate'] = "要問合せ"
        
        # 融資限度額の抽出
        loan_amounts = loan_info['loan_amounts']
        amount_patterns = [
            r'融資[限度]*額.*?(\d+)万円',
            r'(\d+)万円.*?まで',
            r'最高.*?(\d+)万円',
            r'上限.*?(\d+)万円'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, pdf_text, re.IGNORECASE)
            loan_amounts.extend(matches)
        
        if loan_amounts:
            try:
                max_amount = max([int(amount.replace(',', '')) for amount in loan_amounts if amount.replace(',', '').isdigit()])
                item['loan_limit'] = f"{max_amount}万円"
            except (ValueError, TypeError):
                item['loan_limit'] = loan_amounts[0] + "万円" if loan_amounts else "要問合せ"
        else:
            item['loan_limit'] = "要問合せ"
        
        # 返済期間の抽出
        terms = loan_info['terms']
        term_patterns = [
            r'返済期間.*?(\d+)年',
            r'(\d+)年.*?以内',
            r'最長.*?(\d+)年',
            r'期間.*?(\d+)年'
        ]
        
        for pattern in term_patterns:
            matches = re.findall(pattern, pdf_text, re.IGNORECASE)
            terms.extend(matches)
        
        if terms:
            try:
                max_term = max([int(term) for term in terms if term.isdigit()])
                item['repayment_period'] = f"{max_term}年"
            except (ValueError, TypeError):
                item['repayment_period'] = terms[0] + "年" if terms else "要問合せ"
        else:
            item['repayment_period'] = "要問合せ"
        
        # 連絡先情報
        contact_info = loan_info['contact_info']
        if contact_info:
            item['contact_phone'] = contact_info[0]
        else:
            # 青森信用金庫の代表番号を設定（一般的な情報）
            item['contact_phone'] = "017-777-4111"
        
        # 保証料・手数料の抽出
        fee_patterns = [
            r'保証料.*?(\d+[,\d]*円|\d+%|無料)',
            r'手数料.*?(\d+[,\d]*円|\d+%|無料)',
            r'保証.*?(無料|不要)'
        ]
        
        fees = []
        for pattern in fee_patterns:
            matches = re.findall(pattern, pdf_text, re.IGNORECASE)
            fees.extend(matches)
        
        item['guarantee_fee'] = fees[0] if fees else "要問合せ"
        
        # 申込条件の抽出
        condition_patterns = [
            r'年齢.*?(\d+歳.*?\d+歳)',
            r'勤続年数.*?(\d+年以上)',
            r'年収.*?(\d+万円以上)',
            r'地域.*?(青森県.*?)',
            r'保証.*?(株式会社.*?)'
        ]
        
        conditions = []
        for pattern in condition_patterns:
            matches = re.findall(pattern, pdf_text, re.IGNORECASE)
            conditions.extend(matches)
        
        item['application_conditions'] = ' / '.join(conditions) if conditions else "詳細は要問合せ"
        
        # 特徴・備考の抽出
        features = []
        if 'カーライフプラン' in pdf_text:
            features.append('カーライフサポート')
        if '新車' in pdf_text or '中古車' in pdf_text:
            features.append('新車・中古車対応')
        if 'エコカー' in pdf_text:
            features.append('エコカー対応')
        
        item['features'] = ' / '.join(features) if features else "マイカーローン"
        
        self.logger.info(f"Extracted loan item: {item['product_name']}")
        self.logger.info(f"Interest rate: {item['interest_rate']}")
        self.logger.info(f"Loan limit: {item['loan_limit']}")
        self.logger.info(f"Repayment period: {item['repayment_period']}")
        
        yield item