from typing import Dict, Any, List
import os
import json
from urllib.parse import urlparse

BASE = "https://www.aoimorishinkin.co.jp"

# デフォルト値（マッチしなかった時）
_DEFAULT_PROFILE: Dict[str, Any] = {
    "loan_type": None,
    "category": None,
    "interest_type_hints": [],
    "pdf_priority_fields": [],
}

# 固定ページの profiles
profiles: Dict[str, Dict[str, Any]] = {
    "/loan/car/": {"loan_type": "car", "category": "auto"},
    "/loan/housing/": {"loan_type": "home", "category": "housing"},
    "/loan/education/": {"loan_type": "education", "category": "education"},
    "/loan/freeloan/": {"loan_type": "freeloan", "category": "multi-purpose"},
    "/loan/card/": {"loan_type": "card", "category": "card"},
}


def _normalize_path(url: str) -> str:
    """URLからpathを取り出して末尾/を必ずつける"""
    path = urlparse(url).path
    if not path.endswith("/"):
        path += "/"
    return path


def pick_profile(url: str) -> Dict[str, Any]:
    """URLに対応するprofileを返す（なければデフォルト）"""
    path = _normalize_path(url)
    return profiles.get(path, _DEFAULT_PROFILE)


def get_product_urls() -> List[str]:
    """環境変数から商品URL一覧を取得（JSON配列）"""
    data = os.getenv("AOIMORI_SHINKIN_PRODUCT_URLS")
    if not data:
        return []
    return json.loads(data)


def get_pdf_urls() -> List[str]:
    """環境変数で指定がなければデフォルトのPDFリストを返す"""
    override = os.getenv("AOIMORI_SHINKIN_PDF_URLS")
    if override:
        return json.loads(override)
    return [
        f"{BASE}/pdf/poster_mycarroan_241010.pdf",
        f"{BASE}/pdf/poster_myhomeroan_241010.pdf",
        f"{BASE}/pdf/kyouikuroan_241010.pdf",
    ]
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aoimori_shinkin/config.py
# スクレイパー設定（URL/セレクタ/閾値など）
# なぜ: 変更頻度の高い値をコードから分離するため
# 関連: product_scraper.py, rate_pages.py, html_parser.py
