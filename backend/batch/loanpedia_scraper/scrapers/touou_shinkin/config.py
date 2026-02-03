#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/touou_shinkin/config.py
# 東奥信用金庫スクレイパーの設定（URL/セレクタ）
# なぜ: コードから切り離し変更追従を容易にするため
# 関連: product_scraper.py, web_parser.py, html_parser.py

from __future__ import annotations
import os
from urllib.parse import urlparse
from typing import Dict, Any, List

BASE_HOST = "https://www.shinkin.co.jp"
BASE_DIR = "/toshin/jyoho/loan/"
START = f"{BASE_HOST}{BASE_DIR}"

# テスト仕様でのBASE（末尾スラなし）
BASE = "https://www.shinkin.co.jp/toshin"

# 既定の対象PDF（テスト期待に合わせて6件）
_DEFAULT_PDFS: List[str] = [
    f"{BASE_HOST}{BASE_DIR}carlife_s.pdf",
    f"{BASE_HOST}{BASE_DIR}mycarplus_s.pdf",
    f"{BASE_HOST}{BASE_DIR}kyoiku_s.pdf",
    f"{BASE_HOST}{BASE_DIR}newkyoiku_s.pdf",
    f"{BASE_HOST}{BASE_DIR}kyoikucl_s.pdf",
    f"{BASE_HOST}{BASE_DIR}free_s.pdf",
]

HEADERS = {"User-Agent": "LoanScraper/1.0 (+https://example.com)"}

INSTITUTION_INFO: Dict[str, Any] = {
    # 従来フィールド（後方互換）
    "institution_code": "0004",
    "institution_name": "東奥信用金庫",
    "institution_type": "信用金庫",
    "website_url": "https://www.shinkin.co.jp/toshin/",
    # テスト期待フィールド
    "financial_institution": "東奥信用金庫",
    "location": "青森県",
    "website": BASE,
}

# プロファイルはファイル名（basename）でマッチ
profiles: Dict[str, Dict[str, Any]] = {
    "carlife_s.pdf": {
        "product_name": "カーライフローン",
        "loan_type": "car",
        "category": "auto",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["新車", "中古車", "借換", "ロードサービス", "優遇"],
        "pdf_priority_fields": [
            "min_loan_term",
            "max_loan_term",
            "min_loan_amount",
            "max_loan_amount",
            "min_interest_rate",
            "max_interest_rate",
        ],
    },
    "mycarplus_s.pdf": {
        "product_name": "マイカープラス",
        "loan_type": "car",
        "category": "auto",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["新車", "中古車", "借換"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "min_loan_amount", "max_loan_amount", "min_interest_rate", "max_interest_rate"],
    },
    "kyoiku_s.pdf": {
        "product_name": "教育ローン",
        "loan_type": "education",
        "category": "education",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["学費", "入学金", "授業料", "留学", "在学中", "据置"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "min_loan_amount", "max_loan_amount", "min_interest_rate", "max_interest_rate"],
    },
    "newkyoiku_s.pdf": {
        "product_name": "新教育ローン",
        "loan_type": "education",
        "category": "education",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["無担保", "学費", "入学金", "授業料", "最長"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "min_loan_amount", "max_loan_amount", "min_interest_rate", "max_interest_rate"],
    },
    "kyoikucl_s.pdf": {
        "product_name": "教育カードローン",
        "loan_type": "education",
        "category": "education",
        "interest_type_hints": ["固定金利", "変動金利"],
        "special_keywords": ["極度額", "カード", "学費", "随時借入"],
        "pdf_priority_fields": ["min_loan_amount", "max_loan_amount", "min_interest_rate", "max_interest_rate"],
    },
    "free_s.pdf": {
        "product_name": "フリーローン",
        "loan_type": "freeloan",
        "category": "multi-purpose",
        "interest_type_hints": ["固定金利"],
        "special_keywords": ["使途自由", "おまとめ", "借換"],
        "pdf_priority_fields": ["min_loan_term", "max_loan_term", "min_loan_amount", "max_loan_amount", "min_interest_rate", "max_interest_rate"],
    },
}


def get_pdf_urls() -> List[str]:
    """既定PDFの一覧。環境変数 TOUOU_SHINKIN_PDF_URLS があればそれを優先。"""
    data = os.getenv("TOUOU_SHINKIN_PDF_URLS")
    if data:
        try:
            import json
            parsed = json.loads(data)
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                return parsed
        except Exception:
            pass
    return list(_DEFAULT_PDFS)


def _url_basename(url: str) -> str:
    path = urlparse(url).path
    return path.rsplit("/", 1)[-1]


def pick_profile(url: str) -> Dict[str, Any]:
    """URLのファイル名でプロファイル選択（未知はデフォルト）"""
    name = _url_basename(url)
    prof = profiles.get(name)
    if prof:
        return prof
    return {
        "loan_type": None,
        "category": None,
        "interest_type_hints": [],
        "special_keywords": [],
        "pdf_priority_fields": [],
    }


def pick_profile_from_pdf(pdf_url: str) -> Dict[str, Any]:
    return pick_profile(pdf_url)


# 商品タイプ別のデフォルト金利範囲（PDF抽出失敗時のフォールバック）
DEFAULT_INTEREST_RATES: Dict[str, tuple[float, float]] = {
    "car": (2.0, 5.0),        # マイカーローン
    "education": (2.0, 4.0),  # 教育ローン
    "freeloan": (4.0, 14.0),  # フリーローン
    "default": (2.0, 14.0),   # その他
}


def get_default_interest_rate(slug: str) -> tuple[float, float]:
    """商品タイプに応じたデフォルト金利範囲を返す"""
    return DEFAULT_INTEREST_RATES.get(slug, DEFAULT_INTEREST_RATES["default"])
