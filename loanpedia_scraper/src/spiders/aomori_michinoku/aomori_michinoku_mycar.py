# 標準ライブラリ
import hashlib
import os
import re
import sys
from datetime import datetime

# サードパーティライブラリ
import scrapy

# プロジェクト固有のインポート（パス設定）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, os.path.join(project_root, "loanpedia_scraper", "src"))

# プロジェクト内モジュール
try:
    from items import LoanItem
except ImportError:
    # フォールバック
    from loanpedia_scraper.src.items import LoanItem


class AomorimichinokuBankSpider(scrapy.Spider):
    """
    青森みちのく銀行のマイカーローン情報をHTMLから抽出するスパイダー

    ウェブページから金利、融資金額、融資期間、申込条件等の
    ローン商品詳細情報を自動抽出し、構造化されたデータとして出力する。
    """

    name = "aomorimichinoku_bank"
    allowed_domains = ["www.am-bk.co.jp"]
    start_urls = ["https://www.am-bk.co.jp/kojin/loan/mycarloan/"]

    def parse(self, response):
        self.logger.info(f"Parsing {response.url}")

        title = response.css("title::text").get()
        text = response.text
        self.logger.info(f"Page title: {title}")  # 基本アイテム作成

        item = LoanItem()
        item["institution_name"] = "青森みちのく銀行"
        item["institution_code"] = "0117"
        item["product_name"] = title or "青森みちのくマイカーローン"
        item["loan_category"] = "マイカーローン"
        item["source_url"] = response.url
        item["page_title"] = title
        item["html_content"] = response.text
        item["content_hash"] = hashlib.md5(response.text.encode()).hexdigest()
        item["scraped_at"] = datetime.now().isoformat()
        # === 金利情報を抽出 ===
        # 1. kinri-wrp要素から抽出（最優先）
        kinri_elements = response.css(".kinri-wrp")
        for elem in kinri_elements:
            all_text = "".join(elem.css("*::text").getall())

            # 変動金利範囲パターン
            range_match = re.search(
                r"変動金利.*?(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)\s*[%％]", all_text
            )
            if range_match:
                item["min_interest_rate"] = float(range_match.group(1))
                item["max_interest_rate"] = float(range_match.group(2))
                self.logger.info(
                    f"✅ 金利範囲（kinri-wrp）: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                )
                break

            # <b>タグから直接抽出
            bold_text = elem.css("b::text").get()
            if bold_text and "〜" in bold_text:
                range_match = re.search(r"(\d+\.\d+)\s*[〜～]\s*(\d+\.\d+)", bold_text)
                if range_match:
                    item["min_interest_rate"] = float(range_match.group(1))
                    item["max_interest_rate"] = float(range_match.group(2))
                    self.logger.info(
                        f"✅ 金利範囲（bold）: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                    )
                    break

        # 2. 金利が取得できてない場合、全文検索で抽出
        if "min_interest_rate" not in item:
            rate_patterns = [
                (
                    r"変動金利\s*年?\s*(\d+\.\d+)\s*[%％]?\s*[〜～]\s*(\d+\.\d+)\s*[%％]",
                    "変動金利範囲",
                ),
                (r"年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "年率範囲"),
                (r"WEB完結型.*?(\d+\.\d+)\s*[%％]", "WEB完結型金利"),
            ]

            for pattern, description in rate_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    if len(matches[0]) == 2:  # 範囲パターン
                        item["min_interest_rate"] = float(matches[0][0])
                        item["max_interest_rate"] = float(matches[0][1])
                        self.logger.info(
                            f"✅ {description}: {item['min_interest_rate']}% - {item['max_interest_rate']}%"
                        )
                    else:  # 単一パターン
                        rate = float(matches[0])
                        item["min_interest_rate"] = rate
                        item["max_interest_rate"] = rate
                        self.logger.info(f"✅ {description}: {rate}%")
                    break

        # === 融資金額を抽出 ===
        # c-text要素から融資金額を抽出
        c_text_elements = response.css(".c-text::text").getall()
        for text_elem in c_text_elements:
            # "1万円以上1,000万円以内" パターン
            range_match = re.search(
                r"(\d+(?:,\d{3})*)\s*万円以上.*?(\d+(?:,\d{3})*)\s*万円以内", text_elem
            )
            if range_match:
                item["min_loan_amount"] = (
                    int(range_match.group(1).replace(",", "")) * 10000
                )
                item["max_loan_amount"] = (
                    int(range_match.group(2).replace(",", "")) * 10000
                )
                self.logger.info(
                    f"✅ 融資金額範囲: {item['min_loan_amount']}円 - {item['max_loan_amount']}円"
                )
                break

            # "◯万円以内" パターン
            max_match = re.search(r"(\d+(?:,\d{3})*)\s*万円以内", text_elem)
            if max_match:
                item["min_loan_amount"] = None
                item["max_loan_amount"] = (
                    int(max_match.group(1).replace(",", "")) * 10000
                )
                self.logger.info(f"✅ 最大融資金額: {item['max_loan_amount']}円")
                break

        # === テーブルから金利・融資金額・その他情報を一括取得 ===
        tables = response.css("table")
        for table in tables:
            rows = table.css("tr")
            for row in rows:
                cells = row.css("td::text, th::text").getall()

                for i, cell in enumerate(cells):
                    # 金利情報（まだ取得できてない場合）
                    if "ローン金利" in cell and "min_interest_rate" not in item:
                        if i + 1 < len(cells):
                            web_rate_match = re.search(
                                r"(\d+\.\d+)\s*[%％]", cells[i + 1]
                            )
                            if web_rate_match:
                                web_rate = float(web_rate_match.group(1))

                                visit_rate = None
                                if i + 2 < len(cells):
                                    visit_rate_match = re.search(
                                        r"(\d+\.\d+)\s*[%％]", cells[i + 2]
                                    )
                                    if visit_rate_match:
                                        visit_rate = float(visit_rate_match.group(1))

                                if visit_rate:
                                    item["min_interest_rate"] = min(
                                        web_rate, visit_rate
                                    )
                                    item["max_interest_rate"] = max(
                                        web_rate, visit_rate
                                    )
                                    self.logger.info(
                                        f"✅ テーブル金利比較: WEB{web_rate}% 来店{visit_rate}%"
                                    )
                                else:
                                    item["min_interest_rate"] = web_rate
                                    item["max_interest_rate"] = web_rate
                                    self.logger.info(f"✅ テーブルWEB金利: {web_rate}%")

                    # 融資金額（まだ取得できてない場合）
                    elif (
                        "融資金額" in cell or "借入金額" in cell
                    ) and "max_loan_amount" not in item:
                        if i + 1 < len(cells):
                            amount_text = cells[i + 1]
                            range_match = re.search(
                                r"(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円", amount_text
                            )
                            if range_match:
                                item["min_loan_amount"] = (
                                    int(range_match.group(1)) * 10000
                                )
                                item["max_loan_amount"] = (
                                    int(range_match.group(2)) * 10000
                                )
                                self.logger.info(
                                    f"✅ テーブル融資金額: {item['min_loan_amount']}円 - {item['max_loan_amount']}円"
                                )

        # === 融資金額が取得できてない場合、全文検索 ===
        if "max_loan_amount" not in item:
            amount_patterns = [
                r"融資金額.*?(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円",
                r"借入金額.*?(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円",
                r"(\d+)\s*万円\s*[～〜]\s*(\d+)\s*万円",
                r"最高\s*(\d+)\s*万円",
                r"最大\s*(\d+)\s*万円",
            ]

            for i, pattern in enumerate(amount_patterns):
                matches = re.findall(pattern, text)
                if matches:
                    match = matches[0]
                    if isinstance(match, tuple) and len(match) == 2:  # 範囲パターン
                        item["min_loan_amount"] = int(match[0]) * 10000
                        item["max_loan_amount"] = int(match[1]) * 10000
                        self.logger.info(
                            f"✅ 融資金額範囲（パターン{i + 1}）: {item['min_loan_amount']}円 - {item['max_loan_amount']}円"
                        )
                    else:  # 最大のみ
                        try:
                            max_value = (
                                int(match[0])
                                if isinstance(match, tuple)
                                else int(match)
                            )
                            item["min_loan_amount"] = None
                            item["max_loan_amount"] = max_value * 10000
                        except (ValueError, IndexError):
                            self.logger.warning(f"融資金額の変換に失敗: {match}")
                        self.logger.info(
                            f"✅ 最大融資金額（パターン{i + 1}）: {item['max_loan_amount']}円"
                        )
                    break

        # === 融資期間を抽出 ===
        period_patterns = [
            (r"(\d+)\s*年\s*～\s*(\d+)\s*年", "year_range"),
            (r"最長\s*(\d+)\s*年", "max_year"),
            (r"(\d+)\s*ヶ月\s*～\s*(\d+)\s*ヶ月", "month_range"),
        ]

        for pattern, pattern_type in period_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if pattern_type == "year_range":
                    item["min_loan_period_months"] = int(matches[0][0]) * 12
                    item["max_loan_period_months"] = int(matches[0][1]) * 12
                    self.logger.info(
                        f"✅ 融資期間範囲: {item['min_loan_period_months']}ヶ月 - {item['max_loan_period_months']}ヶ月"
                    )
                elif pattern_type == "max_year":
                    item["min_loan_period_months"] = None
                    item["max_loan_period_months"] = int(matches[0]) * 12
                    self.logger.info(
                        f"✅ 最長融資期間: {item['max_loan_period_months']}ヶ月"
                    )
                elif pattern_type == "month_range":
                    item["min_loan_period_months"] = int(matches[0][0])
                    item["max_loan_period_months"] = int(matches[0][1])
                    self.logger.info(
                        f"✅ 融資期間範囲: {item['min_loan_period_months']}ヶ月 - {item['max_loan_period_months']}ヶ月"
                    )
                break

        # === 保証料を抽出 ===
        guarantor_patterns = [
            r"保証料.*?(\d+(?:\.\d+)?)[%％]",
            r"保証料.*?(無料|不要|なし)",
        ]

        for pattern in guarantor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(1) in ["無料", "不要", "なし"]:
                    item["guarantor_fee"] = 0.0
                    self.logger.info("✅ 保証料: 無料")
                else:
                    item["guarantor_fee"] = float(match.group(1))
                    self.logger.info(f"✅ 保証料: {item['guarantor_fee']}%")
                break

        # === 手数料を抽出 ===
        handling_patterns = [
            r"(?:事務)?手数料.*?(\d+(?:,\d{3})*)\s*円",
            r"(?:事務)?手数料.*?(無料|不要)",
        ]

        for pattern in handling_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.group(1) in ["無料", "不要"]:
                    item["handling_fee"] = 0
                    self.logger.info("✅ 手数料: 無料")
                else:
                    item["handling_fee"] = int(match.group(1).replace(",", ""))
                    self.logger.info(f"✅ 手数料: {item['handling_fee']}円")
                break

        # === 申込条件を抽出 ===
        conditions = []

        # 年齢条件
        age_match = re.search(r"(?:満)?(\d+)歳以上(?:.*?(?:満)?(\d+)歳以下)?", text)
        if age_match:
            if age_match.group(2):
                conditions.append(
                    f"年齢: {age_match.group(1)}歳以上{age_match.group(2)}歳以下"
                )
            else:
                conditions.append(f"年齢: {age_match.group(1)}歳以上")

        # 年収・勤続年数・その他条件
        condition_patterns = [
            (
                r"(?:年収|年間収入|前年度年収).*?(\d+)万円以上",
                lambda m: f"年収: {m.group(1)}万円以上",
            ),
            (
                r"(?:勤続|継続勤務).*?(\d+)年以上",
                lambda m: f"勤続年数: {m.group(1)}年以上",
            ),
            (r"安定.*?継続.*?収入", lambda m: "安定継続した収入があること"),
            (
                r"保証会社.*?保証.*?受けられる",
                lambda m: "保証会社の保証が受けられること",
            ),
            (
                r"当行.*?営業区域内.*?居住",
                lambda m: "当行営業区域内に居住または勤務していること",
            ),
        ]

        for pattern, formatter in condition_patterns:
            match = re.search(pattern, text)
            if match:
                conditions.append(formatter(match))

        item["application_conditions"] = "、".join(conditions) if conditions else None
        if item["application_conditions"]:
            self.logger.info(f"✅ 申込条件: {item['application_conditions']}")

        # === 返済方法を抽出 ===
        repayment_info = []
        if re.search(r"元利均等.*?毎月返済|元利均等返済|毎月返済", text):
            repayment_info.append("元利均等毎月返済")

        date_match = re.search(r"毎月(\d+)日|(\d+)日.*?返済|返済日.*?(\d+)日", text)
        if date_match:
            day = next((group for group in date_match.groups() if group), None)
            if day:
                repayment_info.append(f"毎月{day}日返済")

        if re.search(r"ボーナス.*?併用", text):
            repayment_info.append("ボーナス併用返済可能")

        item["repayment_method"] = "、".join(repayment_info) if repayment_info else None
        if item["repayment_method"]:
            self.logger.info(f"✅ 返済方法: {item['repayment_method']}")

        # === 追加情報を抽出 ===
        # 繰上返済手数料
        prepayment_match = re.search(
            r"繰上返済.*?(無料|不要|(\d+(?:,\d{3})*)\s*円)", text, re.IGNORECASE
        )
        if prepayment_match:
            if prepayment_match.group(1) in ["無料", "不要"]:
                item["prepayment_fee"] = "無料"
                self.logger.info("✅ 繰上返済手数料: 無料")
            else:
                fee = prepayment_match.group(2).replace(",", "")
                item["prepayment_fee"] = f"{fee}円"
                self.logger.info(f"✅ 繰上返済手数料: {fee}円")

        # 申込方法
        methods = []
        method_patterns = [
            (r"WEB.*?申込|インターネット.*?申込", "WEB申込"),
            (r"来店.*?申込", "来店申込"),
            (r"郵送.*?申込", "郵送申込"),
            (r"電話.*?申込", "電話申込"),
        ]

        for pattern, method_name in method_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                methods.append(method_name)

        if methods:
            item["application_method"] = "、".join(methods)
            self.logger.info(f"✅ 申込方法: {item['application_method']}")

        # 必要書類
        doc_patterns = [
            "運転免許証",
            "健康保険証",
            "収入証明書",
            "源泉徴収票",
            "住民票",
            "印鑑証明書",
        ]
        required_docs = [doc for doc in doc_patterns if re.search(doc, text)]

        if required_docs:
            item["required_documents"] = "、".join(required_docs[:5])
            self.logger.info(f"✅ 必要書類: {item['required_documents']}")

        # 保証人・担保情報
        if re.search(r"保証人.*?(不要|必要なし)", text, re.IGNORECASE):
            item["guarantor_info"] = "保証人不要"
            self.logger.info("✅ 保証人: 不要")
        elif re.search(r"保証人.*?必要", text, re.IGNORECASE):
            item["guarantor_info"] = "保証人必要"
            self.logger.info("✅ 保証人: 必要")

        if re.search(r"担保.*?(不要|必要なし)|無担保", text, re.IGNORECASE):
            item["collateral_info"] = "担保不要"
            self.logger.info("✅ 担保: 不要")
        elif re.search(r"担保.*?必要", text, re.IGNORECASE):
            item["collateral_info"] = "担保必要"
            self.logger.info("✅ 担保: 必要")

        # ログ出力による抽出結果の確認
        if "min_interest_rate" not in item:
            self.logger.warning("⚠️ 金利情報を抽出できませんでした")
        if "max_loan_amount" not in item:
            self.logger.warning("⚠️ 融資金額情報を抽出できませんでした")

        yield item
