# loanpedia_scraper/scrapers/touou_shinkin/config.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from urllib.parse import urlparse
from typing import Dict, Any, List

BASE_HOST = "https://www.shinkin.co.jp"
BASE_DIR  = "/toshin/jyoho/loan/"

# 実行対象PDF（必要に応じて ?ver=... のクエリは省略可）
PDF_URLS: List[str] = [
    f"{BASE_HOST}{BASE_DIR}carlife_s.pdf",
    f"{BASE_HOST}{BASE_DIR}kyoiku_s.pdf",
    f"{BASE_HOST}{BASE_DIR}newkyoiku_s.pdf",
    f"{BASE_HOST}{BASE_DIR}kyoikucl_s.pdf",
    f"{BASE_HOST}{BASE_DIR}free_s.pdf",
    f"{BASE_HOST}{BASE_DIR}silverlife_s.pdf",
    f"{BASE_HOST}{BASE_DIR}toshincl_s.pdf",
]

HEADERS = {"User-Agent": "LoanScraper/1.0 (+https://example.com)"}

INSTITUTION_INFO: Dict[str, Any] = {
    "institution_code": "0004",
    "institution_name": "東奥信用金庫",
    "institution_type": "信用金庫",
    "website_url": "https://www.shinkin.co.jp/toshin/",
}

# ─────────────────────────────────────────────────────────────
# am-bk スタイル互換：profiles + pick_profile
#   - キー：URL の path 最長一致で選択
#   - 値：商品ごとのヒント/優先抽出フィールド など
#   - pdf_url_override: 他所から拾いたい固定PDFがある場合に使える（今回の東しんは自前PDFを直接回すので省略可）
# ─────────────────────────────────────────────────────────────
profiles: Dict[str, Dict[str, Any]] = {
    # とうしんカーライフプラン
    f"{BASE_DIR}carlife_s.pdf": {
        "product_name": "とうしんカーライフプラン",
        "loan_type": "マイカーローン",
        "category": "自動車",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["新車", "中古車", "借換", "ロードサービス", "優遇"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "loan_amount_max_yen"],
        # "pdf_url_override": [...],  # 必要なら外部固定PDFを指定
    },

    # 教育ローン（通常）
    f"{BASE_DIR}kyoiku_s.pdf": {
        "product_name": "教育ローン",
        "loan_type": "教育ローン",
        "category": "教育",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["学費", "入学金", "授業料", "留学", "在学中", "据置"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "loan_amount_max_yen"],
    },

    # 新教育ローン（無担保など）
    f"{BASE_DIR}newkyoiku_s.pdf": {
        "product_name": "新教育ローン",
        "loan_type": "教育ローン",
        "category": "教育",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["無担保", "学費", "入学金", "授業料", "最長"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "loan_amount_max_yen"],
    },

    # 教育カードローン
    f"{BASE_DIR}kyoikucl_s.pdf": {
        "product_name": "教育カードローン",
        "loan_type": "カードローン",
        "category": "教育",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["極度額", "カード", "学費", "随時借入"],
        "pdf_priority_fields": ["loan_amount_max_yen"],
    },

    # フリーローン
    f"{BASE_DIR}free_s.pdf": {
        "product_name": "フリーローン",
        "loan_type": "フリーローン",
        "category": "多目的",
        "interest_type_hints": ["固定金利"],
        "special_keywords": ["使途自由", "おまとめ", "借換"],
        "pdf_priority_fields": ["loan_amount_max_yen", "min_loan_term", "max_loan_term"],
    },

    # シルバーライフローン
    f"{BASE_DIR}silverlife_s.pdf": {
        "product_name": "シルバーライフローン",
        "loan_type": "フリーローン",
        "category": "多目的",
        "interest_type_hints": ["固定金利"],
        "special_keywords": ["年金受給", "60歳以上", "医療", "介護"],
        "pdf_priority_fields": ["min_age", "max_age", "loan_amount_max_yen"],
    },

    # とうしんカードローン
    f"{BASE_DIR}toshincl_s.pdf": {
        "product_name": "とうしんカードローン",
        "loan_type": "カードローン",
        "category": "多目的",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["極度額", "キャッシング", "随時借入"],
        "pdf_priority_fields": ["loan_amount_max_yen"],
    },
}

def get_pdf_urls() -> List[str]:
    return list(PDF_URLS)

def _url_path(url: str) -> str:
    # クエリ（?ver=...）を除いた path を返す
    parsed = urlparse(url)
    return parsed.path

def pick_profile(url: str) -> Dict[str, Any]:
    """
    am-bk 互換：URL の path に対して profiles のキーを「最長一致」。
    見つからなければ空プロファイル（後段は本文抽出のみで頑張る）。
    """
    path = _url_path(url)
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
