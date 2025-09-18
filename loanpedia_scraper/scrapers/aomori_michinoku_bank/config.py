# loan_scraper/config.py
# -*- coding: utf-8 -*-
from urllib.parse import urlparse
from typing import Dict, Any

BASE = "https://www.am-bk.co.jp"
START = "https://www.am-bk.co.jp/kojin/loan/"
PDF_CATALOG_URL = "https://www.am-bk.co.jp/kojin/support/syouhingaiyou/"
HEADERS = {"User-Agent": "LoanScraper/1.0 (+https://example.com)"}

# 商品ごとの設定（固定PDFがある場合は pdf_url_override に指定）
profiles: Dict[str, Dict[str, Any]] = {
    "/kojin/loan/mycarloan/": {
        "product_name": "青森みちのくマイカーローン",
        "loan_type": "マイカーローン",
        "category": "自動車",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["車両", "中古車", "新車", "船舶", "借換"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-75.pdf"],
    },
    # 例: 固定PDF
    # "pdf_url_override": "https://www.am-bk.co.jp/kojin/support/syouhingaiyou/l-75.pdf",
    "/kojin/loan/kyouikuloan_hanpuku/": {
        "product_name": "青森みちのく教育ローン反復利用型",
        "loan_type": "教育ローン",
        "category": "教育",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": [
            "在学中据置",
            "学費",
            "入学金",
            "留学",
            "最長",
            "限度額",
            "何度でも",
        ],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-77.pdf"],
    },
    "/kojin/loan/certificate/": {
        "product_name": "青森みちのく教育ローン証書貸付型",
        "loan_type": "教育ローン",
        "category": "教育",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["在学中据置", "学費", "入学金", "留学", "最長"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-78.pdf"],
    },
    "/kojin/loan/kyouikuloan/": {
        "product_name": "青森みちのく教育カードローン",
        "loan_type": "教育ローン",
        "category": "教育",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["学費", "入学金", "授業料", "ローンカード"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-79.pdf"],
    },
    "/kojin/loan/freeloan/": {
        "product_name": "青森みちのくフリーローン",
        "loan_type": "フリーローン",
        "category": "多目的",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["お使いみちは自由", "最長"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-81.pdf"],
    },
    "/kojin/loan/omatomeloan/": {
        "product_name": "青森みちのくおまとめローン",
        "loan_type": "おまとめローン",
        "category": "多目的",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["借換", "おまとめ", "低金利"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-83.pdf"],
    },
    "/kojin/loan/freeloan/silverloan": {
        "product_name": "青森みちのくシルバーローン",
        "loan_type": "フリーローン",
        "category": "多目的",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["60歳以上", "年金受給者", "最長"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-85.pdf"],
    },
    "/kojin/loan/freeloan/support/": {
        "product_name": "青森みちのく住宅サポートローン",
        "loan_type": "住宅ローン",
        "category": "住宅",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["お使いみちは自由", "最長"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-86.pdf"],
    },
    "/kojin/loan/jutakuloan/": {
        "product_name": "青森みちのく住宅ローン （あおぎん信用保証型）",
        "loan_type": "住宅ローン",
        "category": "住宅",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["借換", "リフォーム", "新築", "中古", "増改築", "最長"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-94.pdf"],
    },
    "/kojin/loan/jutakuloan/": {
        "product_name": "青森みちのく住宅ローン （全国保証型）",
        "loan_type": "住宅ローン",
        "category": "住宅",
        "interest_type_hints": ["固定金利"],
        "special_keywords": [ "借換", "リフォーム", "新築", "中古", "増改築", "最長"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-95.pdf"],
    },
    "/kojin/loan/reform/": {
        "product_name": "青森みちのくリフォームローン",
        "loan_type": "住宅ローン",
        "category": "住宅",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["リフォーム", "増改築"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-87.pdf"],
    },
    "/kojin/loan/akiyarikatsuyouloan/": {
        "product_name": "青森みちのく空き家利活用ローン",
        "loan_type": "住宅ローン",
        "category": "住宅",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["借換", "リフォーム", "新築", "中古", "増改築", "最長"],
        "pdf_priority_fields": ["min_age", "max_age", "min_loan_term", "max_loan_term", "repayment_method"],
        "pdf_url_override": ["https://www.am-bk.co.jp/kojin/loan/pdf/l-88.pdf"],
    },
}


def pick_profile(url: str) -> Dict[str, Any]:
    path = urlparse(url).path
    candidates = [k for k in profiles if path.startswith(k)]
    if not candidates:
        return {
            "loan_type": None,
            "category": None,
            "interest_type_hints": [],
            "special_keywords": [],
            "pdf_priority_fields": [],
        }
    key = max(candidates, key=len)  # 最長一致
    return profiles[key]
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aomori_michinoku_bank/config.py
# スクレイパー設定（URL/セレクタ/しきい値）
# なぜ: 頻繁に変わる値をコードから分離するため
# 関連: product_scraper.py, rate_pages.py, html_parser.py
