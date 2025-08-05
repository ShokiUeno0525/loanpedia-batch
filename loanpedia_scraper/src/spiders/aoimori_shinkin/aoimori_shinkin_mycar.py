"""
青森信用金庫マイカーローンスクレイピングモジュール。

PDFファイルからローン情報を抽出するスパイダークラスを提供します。
"""

# 1. 標準ライブラリ
import hashlib
import logging
import os
import re
import sys
from datetime import datetime

# 2. サードパーティライブラリ
import scrapy

# 3. パス設定（ローカルインポートの前に）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "loanpedia_scraper", "src"))

# 4. ローカルモジュール（最後に）
logger = logging.getLogger(__name__)

try:
    from pdf_scraper import PDFScraper
except ImportError:
    logger.warning("pdf_scraperモジュールが見つかりません")
    PDFScraper = None

try:
    from src.items import LoanItem
except ImportError:
    logger.warning("itemsモジュールが見つかりません")
    LoanItem = None


class AoimoriSinkinMycarSpider(scrapy.Spider):
    """青森信用金庫マイカーローンスパイダークラス。"""

    name = "aoimori_sinkin_mycar"  # 青森信用金庫マイカーローン
    allowed_domains = ["aoimorishinkin.co.jp"]  # 青森信用金庫公式サイト
    start_urls = [
        "https://www.aoimorishinkin.co.jp/loan/car/",
        "https://www.aoimorishinkin.co.jp/pdf/poster_mycarroan_241010.pdf",
    ]

    def __init__(self, **kwargs):
        """スパイダーの初期化処理。"""
        super().__init__(**kwargs)
        if PDFScraper:
            self.pdf_scraper = PDFScraper()
        else:
            self.pdf_scraper = None

    def parse(self, response):
        """
        レスポンスを解析してローン情報を抽出する。

        Args:
            response: ScrapyのResponseオブジェクト

        Yields:
            LoanItem: 抽出されたローン情報
        """
        if response.url.endswith(".pdf"):
            yield from self.parse_pdf(response)
        else:
            yield from self.parse_html(response)

    def parse_pdf(self, response):
        """
        PDFレスポンスを解析してローン情報を抽出する。

        Args:
            response: ScrapyのResponseオブジェクト

        Yields:
            LoanItem: 抽出されたローン情報
        """
        self.logger.info(f"Parsing PDF: {response.url}")

        # PDFの処理ができない場合は、フォールバック情報を使用
        if not self.pdf_scraper:
            self.logger.warning(
                "PDF処理モジュールが利用できません。フォールバック情報を使用します。"
            )
            yield from self.create_fallback_item(response)
            return

        # PDFからテキスト抽出
        result = self.pdf_scraper.extract_text_from_bytes(response.body)

        if not result["success"]:
            self.logger.error(
                f"PDF抽出失敗: {result['error']} - フォールバック情報を使用"
            )
            yield from self.create_fallback_item(response)
            return

        pdf_text = result["text"]
        self.logger.info(f"PDF text extracted: {len(pdf_text)} characters")
        self.logger.info(f"PDF content preview: {pdf_text[:300]}...")

        if not pdf_text.strip():
            self.logger.warning(
                "PDFからテキストが抽出できませんでした（画像ベースのPDFの可能性）- フォールバック情報を使用"
            )
            yield from self.create_fallback_item(response)
            return

        # ローン情報の自動抽出
        loan_info = self.pdf_scraper.extract_loan_info(pdf_text)
        yield from self.create_loan_item(response, pdf_text, loan_info)

    def parse_html(self, response):
        """
        HTMLページを解析してローン情報を抽出する。

        Args:
            response: ScrapyのResponseオブジェクト

        Yields:
            LoanItem: 抽出されたローン情報
        """
        self.logger.info(f"Parsing HTML: {response.url}")

        # HTMLからテキストを抽出
        text_content = " ".join(response.css("*::text").getall())

        # マイカーローン関連の情報を詳細に抽出
        if "マイカー" in text_content or "カーライフ" in text_content:
            yield from self.create_loan_item_from_html(response, text_content)

    def create_fallback_item(self, response):
        """
        PDF抽出が失敗した場合のフォールバックアイテムを作成。

        Args:
            response: ScrapyのResponseオブジェクト

        Yields:
            dict or LoanItem: フォールバックローン情報
        """
        self.logger.info("Creating fallback item with known information")

        # 実際のWebサイトから取得した情報を使用
        if LoanItem:
            item = LoanItem()
            item["institution_name"] = "青い森信用金庫"
            item["institution_code"] = "1105"
            item["product_name"] = "青い森しんきんカーライフプラン"
            item["loan_category"] = "マイカーローン"
            item["source_url"] = response.url
            item["page_title"] = "青い森信用金庫マイカーローン"
            item["html_content"] = "Webサイトからのフォールバック情報"
            item["content_hash"] = hashlib.md5(response.url.encode()).hexdigest()
            item["scraped_at"] = datetime.now().isoformat()

            # 実際のWebサイト情報を設定
            item["min_interest_rate"] = 2.2  # 最優遇金利
            item["max_interest_rate"] = 3.0  # 標準金利
            item["interest_rate_type"] = "固定金利"
            item["min_loan_amount"] = 100000  # 10万円（推定）
            item["max_loan_amount"] = 10000000  # 1000万円
            item["min_loan_period_months"] = 3  # 3ヶ月
            item["max_loan_period_months"] = 180  # 15年
            item["application_conditions"] = (
                "給与振込口座指定等で優遇金利適用 / 新車・中古車・バイク・自転車対応"
            )
            item["features"] = [
                "新車・中古車対応",
                "バイク・自転車も対象",
                "ロードサービス付きオプション",
                "Web申込24時間対応",
            ]
            item["guarantor_required"] = False
        else:
            # LoanItemが利用できない場合
            item = {
                "institution_name": "青い森信用金庫",
                "institution_code": "1105",
                "product_name": "青い森しんきんカーライフプラン",
                "loan_category": "マイカーローン",
                "source_url": response.url,
                "scraped_at": datetime.now().isoformat(),
                "min_interest_rate": 2.2,
                "max_interest_rate": 3.0,
                "max_loan_amount": 10000000,
                "max_loan_period_months": 180,
            }

        yield item

    def create_loan_item_from_html(self, response, text_content):
        """
        HTMLから抽出されたテキストからローンアイテムを作成。

        Args:
            response: ScrapyのResponseオブジェクト
            text_content: 抽出されたテキスト

        Yields:
            LoanItem: 抽出されたローン情報
        """
        if not LoanItem:
            # LoanItemが利用できない場合
            item = {
                "institution_name": "青い森信用金庫",
                "institution_code": "1105",
                "product_name": "青い森しんきんカーライフプラン",
                "loan_category": "マイカーローン",
                "source_url": response.url,
                "scraped_at": datetime.now().isoformat(),
            }
            yield item
            return

        # 基本アイテム作成
        item = LoanItem()
        item["institution_name"] = "青い森信用金庫"
        item["institution_code"] = "1105"
        item["product_name"] = "青い森しんきんカーライフプラン"
        item["loan_category"] = "マイカーローン"
        item["source_url"] = response.url
        item["page_title"] = "青い森信用金庫マイカーローン"
        item["html_content"] = (
            text_content[:5000] if len(text_content) > 5000 else text_content
        )
        item["content_hash"] = hashlib.md5(text_content.encode()).hexdigest()
        item["scraped_at"] = datetime.now().isoformat()

        # 金利情報の抽出（HTMLから）
        interest_rates = []
        rate_patterns = [
            r"(\d+\.\d+)%",
            r"金利[：:\s]*(\d+\.\d+)",
            r"年率[：:\s]*(\d+\.\d+)",
            r"実質年率[：:\s]*(\d+\.\d+)",
        ]

        for pattern in rate_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            interest_rates.extend(matches)

        # 実際のWebサイトから取得した既知の金利情報を設定
        item["min_interest_rate"] = 2.2  # 最優遇金利2
        item["max_interest_rate"] = 3.0  # 標準金利
        item["interest_rate_type"] = "固定金利"

        # HTMLから抽出された金利があれば更新
        if interest_rates:
            try:
                numeric_rates = [
                    float(rate)
                    for rate in interest_rates
                    if rate.replace(".", "").isdigit()
                ]
                if numeric_rates:
                    item["min_interest_rate"] = min(numeric_rates)
                    item["max_interest_rate"] = max(numeric_rates)
            except (ValueError, TypeError):
                pass

        # 融資限度額の設定
        item["min_loan_amount"] = 100000  # 10万円（推定最低額）
        item["max_loan_amount"] = 10000000  # 1000万円

        # 返済期間の設定
        item["min_loan_period_months"] = 3  # 3ヶ月
        item["max_loan_period_months"] = 180  # 15年（一部商品は15年超も可能）

        # 年齢条件の抽出
        age_pattern = r"(\d+)歳.*?(\d+)歳"
        age_matches = re.search(age_pattern, text_content)
        if age_matches:
            item["min_age"] = int(age_matches.group(1))
            item["max_age"] = int(age_matches.group(2))

        # 申込条件の設定
        conditions = []
        if "給与振込" in text_content or "年金振込" in text_content:
            conditions.append("給与・年金振込口座指定で優遇金利")
        if "勤続" in text_content:
            conditions.append("勤続年数条件あり")
        if "年収" in text_content:
            conditions.append("年収条件あり")
        if "保証" in text_content:
            conditions.append("保証会社による保証")

        item["application_conditions"] = (
            " / ".join(conditions) if conditions else "詳細は要問合せ"
        )

        # 保証人・担保の設定
        item["guarantor_required"] = False
        item["collateral_info"] = "購入車両を担保とする場合あり"

        # 特徴・備考の設定
        features = ["新車・中古車対応", "バイク・自転車も対象"]
        if "ロードサービス" in text_content:
            features.append("ロードサービス付きオプション")
        if "Web" in text_content or "web" in text_content:
            features.append("Web申込24時間対応")
        if "借換" in text_content or "借り換え" in text_content:
            features.append("他行からの借換可能")

        item["features"] = features

        self.logger.info(f"Extracted loan item from HTML: {item['product_name']}")
        self.logger.info(
            f"Interest rates: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
        )
        self.logger.info(
            f"Loan amount: {item['min_loan_amount']} - {item['max_loan_amount']}円"
        )
        self.logger.info(
            f"Loan period: {item['min_loan_period_months']} - {item['max_loan_period_months']}ヶ月"
        )

        yield item

    def create_loan_item(self, response, text_content, loan_info):
        """
        PDFから抽出されたテキストからローンアイテムを作成。

        Args:
            response: ScrapyのResponseオブジェクト
            text_content: 抽出されたテキスト
            loan_info: 抽出されたローン情報

        Yields:
            LoanItem: 抽出されたローン情報
        """
        if not LoanItem:
            item = {
                "institution_name": "青い森信用金庫",
                "institution_code": "1105",
                "product_name": "青い森しんきんカーライフプラン",
                "loan_category": "マイカーローン",
                "source_url": response.url,
                "scraped_at": datetime.now().isoformat(),
            }
            yield item
            return

        # 基本アイテム作成
        item = LoanItem()
        item["institution_name"] = "青い森信用金庫"
        item["institution_code"] = "1105"
        item["product_name"] = "青い森しんきんカーライフプラン"
        item["loan_category"] = "マイカーローン"
        item["source_url"] = response.url
        item["page_title"] = "青い森信用金庫マイカーローン"
        item["html_content"] = text_content
        item["content_hash"] = hashlib.md5(text_content.encode()).hexdigest()
        item["scraped_at"] = datetime.now().isoformat()

        # PDF特有の情報抽出

        # 金利情報の詳細抽出
        interest_rates = []
        if loan_info["interest_rates"]:
            interest_rates = loan_info["interest_rates"]

        # PDFテキストから追加の金利情報を抽出
        rate_patterns = [
            r"金利.*?(\d+\.\d+)%",
            r"年利.*?(\d+\.\d+)%",
            r"(\d+\.\d+)%.*?年利",
            r"固定金利.*?(\d+\.\d+)",
            r"変動金利.*?(\d+\.\d+)",
        ]

        for pattern in rate_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE | re.DOTALL)
            interest_rates.extend(matches)

        # 重複除去して最低金利を設定
        unique_rates = list(set(interest_rates))
        if unique_rates:
            try:
                numeric_rates = [
                    float(rate)
                    for rate in unique_rates
                    if rate.replace(".", "").isdigit()
                ]
                if numeric_rates:
                    min_rate = min(numeric_rates)
                    item["interest_rate"] = f"{min_rate}%"
                else:
                    item["interest_rate"] = unique_rates[0] + "%"
            except (ValueError, TypeError):
                item["interest_rate"] = (
                    unique_rates[0] + "%" if unique_rates else "要問合せ"
                )
        else:
            item["interest_rate"] = "要問合せ"

        # 融資限度額の抽出
        loan_amounts = loan_info["loan_amounts"]
        amount_patterns = [
            r"融資[限度]*額.*?(\d+)万円",
            r"(\d+)万円.*?まで",
            r"最高.*?(\d+)万円",
            r"上限.*?(\d+)万円",
        ]

        for pattern in amount_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            loan_amounts.extend(matches)

        if loan_amounts:
            try:
                numeric_amounts = [
                    int(amount.replace(",", ""))
                    for amount in loan_amounts
                    if amount.replace(",", "").isdigit()
                ]
                if numeric_amounts:
                    max_amount = max(numeric_amounts)
                    item["loan_limit"] = f"{max_amount}万円"
                else:
                    item["loan_limit"] = loan_amounts[0] + "万円"
            except (ValueError, TypeError):
                item["loan_limit"] = (
                    loan_amounts[0] + "万円" if loan_amounts else "要問合せ"
                )
        else:
            item["loan_limit"] = "要問合せ"

        # 返済期間の抽出
        terms = loan_info["terms"]
        term_patterns = [
            r"返済期間.*?(\d+)年",
            r"(\d+)年.*?以内",
            r"最長.*?(\d+)年",
            r"期間.*?(\d+)年",
        ]

        for pattern in term_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            terms.extend(matches)

        if terms:
            try:
                max_term = max(int(term) for term in terms if term.isdigit())
                item["repayment_period"] = f"{max_term}年"
            except (ValueError, TypeError):
                item["repayment_period"] = terms[0] + "年" if terms else "要問合せ"
        else:
            item["repayment_period"] = "要問合せ"

        # 連絡先情報
        contact_info = loan_info["contact_info"]
        if contact_info:
            item["contact_phone"] = contact_info[0]
        else:
            # 青森信用金庫の代表番号を設定（一般的な情報）
            item["contact_phone"] = "017-777-4111"

        # 保証料・手数料の抽出
        fee_patterns = [
            r"保証料.*?(\d+[,\d]*円|\d+%|無料)",
            r"手数料.*?(\d+[,\d]*円|\d+%|無料)",
            r"保証.*?(無料|不要)",
        ]

        fees = []
        for pattern in fee_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            fees.extend(matches)

        item["guarantee_fee"] = fees[0] if fees else "要問合せ"

        # 申込条件の抽出
        condition_patterns = [
            r"年齢.*?(\d+歳.*?\d+歳)",
            r"勤続年数.*?(\d+年以上)",
            r"年収.*?(\d+万円以上)",
            r"地域.*?(青森県.*?)",
            r"保証.*?(株式会社.*?)",
        ]

        conditions = []
        for pattern in condition_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            conditions.extend(matches)

        item["application_conditions"] = (
            " / ".join(conditions) if conditions else "詳細は要問合せ"
        )

        # 特徴・備考の抽出
        features = []
        if "カーライフプラン" in text_content:
            features.append("カーライフサポート")
        if "新車" in text_content or "中古車" in text_content:
            features.append("新車・中古車対応")
        if "エコカー" in text_content:
            features.append("エコカー対応")

        item["features"] = " / ".join(features) if features else "マイカーローン"

        self.logger.info(f"Extracted loan item: {item['product_name']}")
        self.logger.info(f"Interest rate: {item['interest_rate']}")
        self.logger.info(f"Loan limit: {item['loan_limit']}")
        self.logger.info(f"Repayment period: {item['repayment_period']}")

        yield item
