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
        loan_keywords = ['金利', '融資', '借入', 'ローン', '年率', '条件']
        relevant_texts = [text.strip() for text in main_content 
                         if any(keyword in text for keyword in loan_keywords) and text.strip()]
        
        self.logger.info("Found loan-related content:")
        for i, text in enumerate(relevant_texts[:10]):  # 最初の10件のみ表示
            self.logger.info(f"{i+1}: {text}")
        
        # HTMLの一部を保存してデバッグ
        html_snippet = response.css('body').get()[:1000] if response.css('body').get() else ""
        self.logger.info(f"HTML snippet: {html_snippet}")
        
        # 詳細情報を抽出
        min_rate, max_rate = self.extract_interest_rates(response)
        loan_amount_min, loan_amount_max = self.extract_loan_amounts(response)
        loan_term_min, loan_term_max = self.extract_loan_terms(response)
        guarantor_fee = self.extract_guarantor_fee(response)
        application_conditions = self.extract_application_conditions(response)
        repayment_method = self.extract_repayment_method(response)
        
        # アコーディオン内の追加情報を抽出
        additional_info = self.extract_accordion_details(response)
        
        # 基本的なアイテムを作成
        item = LoanItem()
        item['institution_name'] = '青森みちのく銀行'
        item['institution_code'] = '0117'
        item['product_name'] = title or "青森みちのくマイカーローン"
        item['loan_category'] = 'マイカーローン'
        item['min_interest_rate'] = min_rate
        item['max_interest_rate'] = max_rate
        item['min_loan_amount'] = loan_amount_min
        item['max_loan_amount'] = loan_amount_max
        item['min_loan_period_months'] = loan_term_min
        item['max_loan_period_months'] = loan_term_max
        item['guarantor_fee'] = guarantor_fee
        item['application_conditions'] = application_conditions
        item['repayment_method'] = repayment_method
        
        # アコーディオン内の追加情報を設定
        if additional_info:
            item['prepayment_fee'] = additional_info.get('prepayment_fee')
            item['application_method'] = additional_info.get('application_method') 
            item['required_documents'] = additional_info.get('required_documents')
            item['guarantor_info'] = additional_info.get('guarantor_info')
            item['collateral_info'] = additional_info.get('collateral_info')
        
        item['source_url'] = response.url
        item['page_title'] = title
        item['html_content'] = response.text
        item['content_hash'] = hashlib.md5(response.text.encode()).hexdigest()
        item['scraped_at'] = datetime.now()
        
        yield item
    
    def extract_interest_rates(self, response):
        """金利情報を精密抽出"""
        import re
        
        # 1. 最優先: kinri-wrp要素から変動金利範囲を抽出
        kinri_elements = response.css('.kinri-wrp')
        for elem in kinri_elements:
            # 全テキストを取得（子要素も含む）
            all_text = elem.css('*::text').getall()
            full_text = ''.join(all_text)
            
            # "変動金利年2.1〜3.2％" パターン
            range_match = re.search(r'変動金利.*?(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)\s*[%％]', full_text)
            if range_match:
                min_rate = float(range_match.group(1))
                max_rate = float(range_match.group(2))
                self.logger.info(f"✅ kinri-wrp から金利範囲: {min_rate}% - {max_rate}%")
                return min_rate, max_rate
            
            # より直接的に<b>タグから抽出
            bold_text = elem.css('b::text').get()
            if bold_text and '〜' in bold_text:
                range_match = re.search(r'(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)', bold_text)
                if range_match:
                    min_rate = float(range_match.group(1))
                    max_rate = float(range_match.group(2))
                    self.logger.info(f"✅ kinri-wrp <b>タグから金利範囲: {min_rate}% - {max_rate}%")
                    return min_rate, max_rate
        
        # 2. テーブル詳細解析 - WEB完結型と来店型の比較
        tables = response.css('table')
        for table in tables:
            rows = table.css('tr')
            for row in rows:
                cells = row.css('td::text, th::text').getall()
                
                # 金利行を特定
                for i, cell in enumerate(cells):
                    if 'ローン金利' in cell:
                        # WEB完結型と来店型の金利を抽出
                        web_rate = None
                        visit_rate = None
                        
                        if i + 1 < len(cells):
                            web_rate_match = re.search(r'(\d+\.\d+)\s*[%％]', cells[i + 1])
                            if web_rate_match:
                                web_rate = float(web_rate_match.group(1))
                        
                        if i + 2 < len(cells):
                            visit_rate_match = re.search(r'(\d+\.\d+)\s*[%％]', cells[i + 2])
                            if visit_rate_match:
                                visit_rate = float(visit_rate_match.group(1))
                        
                        if web_rate and visit_rate:
                            min_rate = min(web_rate, visit_rate)
                            max_rate = max(web_rate, visit_rate)
                            self.logger.info(f"✅ テーブルから金利比較: WEB{web_rate}% 来店{visit_rate}%")
                            return min_rate, max_rate
                        elif web_rate:
                            self.logger.info(f"✅ テーブルからWEB金利: {web_rate}%")
                            return web_rate, web_rate
        
        # 3. より厳密な全文検索
        text = response.text
        
        # 精密パターンの順番で試行
        precise_patterns = [
            (r'変動金利\s*年?\s*(\d+\.\d+)\s*[%％]?\s*[〜～]\s*(\d+\.\d+)\s*[%％]', '変動金利範囲'),
            (r'年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]', '年率範囲'),
            (r'WEB完結型.*?(\d+\.\d+)\s*[%％]', 'WEB完結型金利'),
        ]
        
        for pattern, description in precise_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if len(matches[0]) == 2:  # 範囲パターン
                    min_rate = float(matches[0][0])
                    max_rate = float(matches[0][1])
                    self.logger.info(f"✅ {description}で金利範囲: {min_rate}% - {max_rate}%")
                    return min_rate, max_rate
                else:  # 単一パターン
                    rate = float(matches[0])
                    self.logger.info(f"✅ {description}で単一金利: {rate}%")
                    return rate, rate
        
        self.logger.warning("⚠️ 金利情報を抽出できませんでした")
        return None, None
    
    def extract_loan_amounts(self, response):
        """融資金額を抽出"""
        import re
        
        # 1. 商品概要アコーディオン内の融資金額を優先検索
        # 全てのc-text要素から融資金額パターンを探す
        c_text_elements = response.css('.c-text::text').getall()
        for text in c_text_elements:
            # "1万円以上1,000万円以内" パターン
            range_match = re.search(r'(\d+(?:,\d{3})*)\s*万円以上.*?(\d+(?:,\d{3})*)\s*万円以内', text)
            if range_match:
                min_amount = int(range_match.group(1).replace(',', '')) * 10000
                max_amount = int(range_match.group(2).replace(',', '')) * 10000
                self.logger.info(f"✅ c-text要素から融資金額範囲: {min_amount}円 - {max_amount}円")
                return min_amount, max_amount
            
            # "◯万円以内" パターン
            max_match = re.search(r'(\d+(?:,\d{3})*)\s*万円以内', text)
            if max_match:
                max_amount = int(max_match.group(1).replace(',', '')) * 10000
                self.logger.info(f"✅ c-text要素から最大融資金額: {max_amount}円")
                return None, max_amount
        
        # 2. アコーディオン構造での検索（バックアップ）
        accordion_items = response.css('.c-accordion__item')
        for item in accordion_items:
            header_text = item.css('.c-accordion__item-inner--parent::text').get()
            if header_text and '商品概要' in header_text:
                # アコーディオン内のテキストを取得
                content_texts = item.css('.c-text::text').getall()
                for text in content_texts:
                    # "1万円以上1,000万円以内" パターン
                    range_match = re.search(r'(\d+(?:,\d{3})*)\s*万円以上.*?(\d+(?:,\d{3})*)\s*万円以内', text)
                    if range_match:
                        min_amount = int(range_match.group(1).replace(',', '')) * 10000
                        max_amount = int(range_match.group(2).replace(',', '')) * 10000
                        self.logger.info(f"✅ 商品概要アコーディオンから融資金額範囲: {min_amount}円 - {max_amount}円")
                        return min_amount, max_amount

        # 2. テーブル内の融資金額を検索
        tables = response.css('table')
        for table in tables:
            rows = table.css('tr')
            for row in rows:
                cells = row.css('td::text, th::text').getall()
                for i, cell in enumerate(cells):
                    if '融資金額' in cell or '借入金額' in cell:
                        if i + 1 < len(cells):
                            amount_text = cells[i + 1]
                            # "10万円～500万円" パターン
                            range_match = re.search(r'(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円', amount_text)
                            if range_match:
                                min_amount = int(range_match.group(1)) * 10000
                                max_amount = int(range_match.group(2)) * 10000
                                self.logger.info(f"✅ テーブルから融資金額範囲: {min_amount}円 - {max_amount}円")
                                return min_amount, max_amount
        
        # 2. 全文検索で融資金額パターンを探す
        text = response.text
        patterns = [
            r'融資金額.*?(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円',  # 融資金額10万円～500万円
            r'借入金額.*?(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円',  # 借入金額10万円～500万円
            r'(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円',           # 10万円～500万円
            r'最高\s*(\d+)\s*万円',                         # 最高500万円
            r'最大\s*(\d+)\s*万円',                         # 最大500万円
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text)
            if matches:
                match = matches[0]
                if isinstance(match, tuple) and len(match) == 2:  # 範囲パターン
                    min_amount = int(match[0]) * 10000
                    max_amount = int(match[1]) * 10000
                    self.logger.info(f"✅ パターン{i+1}から融資金額範囲: {min_amount}円 - {max_amount}円")
                    return min_amount, max_amount
                else:  # 最大のみ
                    if isinstance(match, tuple):
                        max_amount = int(match[0]) * 10000
                    else:
                        max_amount = int(match) * 10000
                    self.logger.info(f"✅ パターン{i+1}から最大融資金額: {max_amount}円")
                    return None, max_amount
        
        self.logger.warning("⚠️ 融資金額情報を抽出できませんでした")
        return None, None
    
    def extract_loan_terms(self, response):
        """融資期間を抽出（アコーディオン内の詳細情報を優先）"""
        import re
        
        # 1. アコーディオン内の「商品概要」から融資期間を抽出
        accordion_items = response.css('.c-accordion__item')
        for item in accordion_items:
            header = item.css('.c-accordion__item-inner--parent')
            header_text = ''.join(header.css('*::text').getall()).strip()
            
            if '商品概要' in header_text:
                # アコーディオン内のテキスト全体を取得
                content_texts = item.css('.c-text::text, .c-table td::text, .c-table th::text').getall()
                all_text = ' '.join(content_texts)
                
                # 「6ヵ月以上15年以内」パターン
                range_match = re.search(r'(\d+)\s*[ヵヶ]\s*月以上.*?(\d+)\s*年以内', all_text)
                if range_match:
                    min_term = int(range_match.group(1))
                    max_term = int(range_match.group(2)) * 12
                    self.logger.info(f"✅ 商品概要アコーディオンから融資期間: {min_term}ヶ月 - {max_term}ヶ月")
                    return min_term, max_term
                
                # 「お借入期間」セクションを探す
                for i, text in enumerate(content_texts):
                    if 'お借入期間' in text or '借入期間' in text:
                        # 次のテキストから期間情報を抽出
                        if i + 1 < len(content_texts):
                            period_text = content_texts[i + 1]
                            # 「6ヵ月以上15年以内」パターン
                            range_match = re.search(r'(\d+)\s*[ヵヶ]\s*月以上.*?(\d+)\s*年以内', period_text)
                            if range_match:
                                min_term = int(range_match.group(1))
                                max_term = int(range_match.group(2)) * 12
                                self.logger.info(f"✅ お借入期間から融資期間: {min_term}ヶ月 - {max_term}ヶ月")
                                return min_term, max_term
        
        # 2. テーブル内の融資期間を検索
        tables = response.css('table')
        for table in tables:
            rows = table.css('tr')
            for row in rows:
                cells = row.css('td::text, th::text').getall()
                for i, cell in enumerate(cells):
                    if '融資期間' in cell or '借入期間' in cell:
                        if i + 1 < len(cells):
                            period_text = cells[i + 1]
                            # 「6ヵ月以上15年以内」パターン
                            range_match = re.search(r'(\d+)\s*[ヵヶ]\s*月以上.*?(\d+)\s*年以内', period_text)
                            if range_match:
                                min_term = int(range_match.group(1))
                                max_term = int(range_match.group(2)) * 12
                                self.logger.info(f"✅ テーブルから融資期間: {min_term}ヶ月 - {max_term}ヶ月")
                                return min_term, max_term
        
        # 3. 従来のパターンマッチング（バックアップ）
        text = response.text
        patterns = [
            r'(\d+)\s*[ヵヶ]\s*月以上.*?(\d+)\s*年以内',  # 6ヵ月以上15年以内
            r'(\d+)\s*年\s*[～〜]\s*(\d+)\s*年',         # 1年～15年
            r'最長\s*(\d+)\s*年',                      # 最長15年
            r'(\d+)\s*ヶ月\s*[～〜]\s*(\d+)\s*ヶ月',     # 6ヶ月～180ヶ月
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text)
            if matches:
                match = matches[0]
                if i == 0:  # 6ヵ月以上15年以内
                    min_term = int(match[0])
                    max_term = int(match[1]) * 12
                    self.logger.info(f"✅ パターン{i+1}から融資期間: {min_term}ヶ月 - {max_term}ヶ月")
                    return min_term, max_term
                elif '年' in pattern:
                    if isinstance(match, tuple) and len(match) == 2:  # 範囲
                        min_term = int(match[0]) * 12
                        max_term = int(match[1]) * 12
                        self.logger.info(f"✅ パターン{i+1}から融資期間: {min_term}ヶ月 - {max_term}ヶ月")
                        return min_term, max_term
                    else:  # 最長のみ
                        if isinstance(match, tuple):
                            max_term = int(match[0]) * 12
                        else:
                            max_term = int(match) * 12
                        self.logger.info(f"✅ パターン{i+1}から最長融資期間: {max_term}ヶ月")
                        return None, max_term
                else:  # ヶ月
                    min_term = int(match[0])
                    max_term = int(match[1])
                    self.logger.info(f"✅ パターン{i+1}から融資期間: {min_term}ヶ月 - {max_term}ヶ月")
                    return min_term, max_term
        
        self.logger.warning("⚠️ 融資期間情報を抽出できませんでした")
        return None, None
    
    def extract_guarantor_fee(self, response):
        """保証料情報を抽出"""
        import re
        
        text = response.text
        guarantor_fee = None
        
        # 保証料パターン
        guarantor_patterns = [
            r'保証料.*?(\d+(?:\.\d+)?)[%％]',
            r'保証料.*?無料',
            r'保証料.*?不要',
            r'保証料.*?なし',
        ]
        
        for pattern in guarantor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '無料' in match.group(0) or '不要' in match.group(0) or 'なし' in match.group(0):
                    guarantor_fee = 0.0
                    self.logger.info(f"✅ 保証料: 無料")
                else:
                    guarantor_fee = float(match.group(1))
                    self.logger.info(f"✅ 保証料: {guarantor_fee}%")
                break
        
        return guarantor_fee
    
    def extract_application_conditions(self, response):
        """申込条件・資格要件を抽出"""
        import re
        
        conditions = []
        text = response.text
        
        # 年齢条件
        age_patterns = [
            r'(\d+)歳以上.*?(\d+)歳以下',
            r'満(\d+)歳以上.*?満(\d+)歳以下',
            r'(\d+)歳以上',
            r'満(\d+)歳以上',
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:
                    conditions.append(f"年齢: {match.group(1)}歳以上{match.group(2)}歳以下")
                else:
                    conditions.append(f"年齢: {match.group(1)}歳以上")
                break
        
        # 年収条件
        income_patterns = [
            r'年収.*?(\d+)万円以上',
            r'年間収入.*?(\d+)万円以上',
            r'前年度年収.*?(\d+)万円以上',
        ]
        
        for pattern in income_patterns:
            match = re.search(pattern, text)
            if match:
                conditions.append(f"年収: {match.group(1)}万円以上")
                break
        
        # 勤続年数条件
        employment_patterns = [
            r'勤続.*?(\d+)年以上',
            r'継続勤務.*?(\d+)年以上',
        ]
        
        for pattern in employment_patterns:
            match = re.search(pattern, text)
            if match:
                conditions.append(f"勤続年数: {match.group(1)}年以上")
                break
        
        # その他の条件
        other_conditions = [
            r'安定.*?継続.*?収入',
            r'保証会社.*?保証.*?受けられる',
            r'当行.*?営業区域内.*?居住',
        ]
        
        for pattern in other_conditions:
            if re.search(pattern, text):
                if '安定' in pattern and '収入' in pattern:
                    conditions.append("安定継続した収入があること")
                elif '保証会社' in pattern:
                    conditions.append("保証会社の保証が受けられること")
                elif '営業区域' in pattern:
                    conditions.append("当行営業区域内に居住または勤務していること")
        
        condition_text = "、".join(conditions) if conditions else None
        if condition_text:
            self.logger.info(f"✅ 申込条件: {condition_text}")
        
        return condition_text
    
    def extract_repayment_method(self, response):
        """返済方法・返済日を抽出"""
        import re
        
        text = response.text
        repayment_info = []
        
        # 返済方法
        method_patterns = [
            r'元利均等返済',
            r'元金均等返済', 
            r'毎月返済',
            r'元利均等.*?毎月返済',
        ]
        
        for pattern in method_patterns:
            if re.search(pattern, text):
                repayment_info.append("元利均等毎月返済")
                break
        
        # 返済日
        date_patterns = [
            r'毎月(\d+)日',
            r'(\d+)日.*?返済',
            r'返済日.*?(\d+)日',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                repayment_info.append(f"毎月{match.group(1)}日返済")
                break
        
        # ボーナス併用
        if re.search(r'ボーナス.*?併用', text):
            repayment_info.append("ボーナス併用返済可能")
        
        repayment_text = "、".join(repayment_info) if repayment_info else None
        if repayment_text:
            self.logger.info(f"✅ 返済方法: {repayment_text}")
        
        return repayment_text
    
    def extract_accordion_details(self, response):
        """アコーディオン内の詳細情報を抽出"""
        import re
        
        text = response.text
        details = {}
        
        # 繰上返済手数料
        prepayment_patterns = [
            r'繰上返済.*?(無料|不要)',
            r'繰上返済.*?(\d+(?:,\d{3})*)\s*円',
            r'一部繰上返済.*?(無料|不要)',
        ]
        
        for pattern in prepayment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '無料' in match.group(1) or '不要' in match.group(1):
                    details['prepayment_fee'] = '無料'
                    self.logger.info(f"✅ 繰上返済手数料: 無料")
                else:
                    fee = match.group(1).replace(',', '')
                    details['prepayment_fee'] = f"{fee}円"
                    self.logger.info(f"✅ 繰上返済手数料: {fee}円")
                break
        
        # 申込方法
        application_methods = []
        method_patterns = [
            (r'WEB.*?申込', 'WEB申込'),
            (r'インターネット.*?申込', 'インターネット申込'),
            (r'来店.*?申込', '来店申込'),
            (r'郵送.*?申込', '郵送申込'),
            (r'電話.*?申込', '電話申込'),
        ]
        
        for pattern, method_name in method_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                application_methods.append(method_name)
        
        if application_methods:
            details['application_method'] = '、'.join(application_methods)
            self.logger.info(f"✅ 申込方法: {details['application_method']}")
        
        # 必要書類
        document_patterns = [
            r'運転免許証',
            r'健康保険証',
            r'収入証明書',
            r'源泉徴収票',
            r'住民票',
            r'印鑑証明書',
        ]
        
        required_docs = []
        for pattern in document_patterns:
            if re.search(pattern, text):
                required_docs.append(pattern)
        
        if required_docs:
            details['required_documents'] = '、'.join(required_docs[:5])  # 最初の5個まで
            self.logger.info(f"✅ 必要書類: {details['required_documents']}")
        
        # 保証人情報
        guarantor_patterns = [
            r'保証人.*?(不要|必要なし)',
            r'保証人.*?必要',
            r'連帯保証人.*?(不要|必要)',
        ]
        
        for pattern in guarantor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '不要' in match.group(0) or '必要なし' in match.group(0):
                    details['guarantor_info'] = '保証人不要'
                    self.logger.info(f"✅ 保証人: 不要")
                else:
                    details['guarantor_info'] = '保証人必要'
                    self.logger.info(f"✅ 保証人: 必要")
                break
        
        # 担保情報
        collateral_patterns = [
            r'担保.*?(不要|必要なし)',
            r'担保.*?必要',
            r'無担保',
        ]
        
        for pattern in collateral_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if '不要' in match.group(0) or '必要なし' in match.group(0) or '無担保' in match.group(0):
                    details['collateral_info'] = '担保不要'
                    self.logger.info(f"✅ 担保: 不要")
                else:
                    details['collateral_info'] = '担保必要'
                    self.logger.info(f"✅ 担保: 必要")
                break
        
        return details if details else None