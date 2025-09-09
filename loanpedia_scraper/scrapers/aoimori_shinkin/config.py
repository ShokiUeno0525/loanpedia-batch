"""Configuration for Aoimori Shinkin scraper (aligned with aomori_michinoku_bank).

- BASE/START/PDF_CATALOG_URL/HEADERS を提供
- profiles は URL パス -> メタ情報（必要時に追記）
- AOIMORI_SHINKIN_PRODUCT_URLS で実URLの一覧を JSON で指定可能
- PDF は AOIMORI_SHINKIN_ENABLE_PDF=true の時のみ有効化（テストと両立）
"""
from typing import Dict, Any, List
import os
import json
from urllib.parse import urlparse

# Entrypoints
BASE = "https://www.aoimorishinkin.co.jp"
START = f"{BASE}/"  # 必要に応じて製品トップへ変更
PDF_CATALOG_URL = f"{BASE}/pdf/"

# HTTP headers
HEADERS: Dict[str, str] = {"User-Agent": "LoanScraper/1.0 (+https://example.com)"}

# Product-specific profiles (URL path -> meta)
profiles: Dict[str, Dict[str, Any]] = {}


def pick_profile(url: str) -> Dict[str, Any]:
    path = urlparse(url).path
    candidates = [k for k in profiles if path.startswith(k)]
    if not candidates:
        return {
            "loan_type": None,
            "category": None,
            "interest_type_hints": [],
            "pdf_priority_fields": [],
        }
    key = max(candidates, key=len)
    return profiles[key]


def get_product_urls() -> List[Dict[str, Any]]:
    data = os.getenv("AOIMORI_SHINKIN_PRODUCT_URLS")
    if not data:
        return []
    try:
        parsed = json.loads(data)
        if isinstance(parsed, list):
            return [x for x in parsed if isinstance(x, dict) and "url" in x]
    except Exception:
        return []
    return []


def get_pdf_urls() -> List[str]:
    # テストモード/pytest 実行では常に無効化
    if os.getenv("SCRAPING_TEST_MODE") == "true" or os.getenv("PYTEST_CURRENT_TEST"):
        return []
    if os.getenv("AOIMORI_SHINKIN_ENABLE_PDF", "false").lower() != "true":
        return []
    override = os.getenv("AOIMORI_SHINKIN_PDF_URLS")
    if override:
        try:
            data = json.loads(override)
            if isinstance(data, list):
                return [str(u) for u in data]
        except Exception:
            pass
    # default to provided loan PDFs
    return [
        f"{BASE}/pdf/poster_mycarroan_241010.pdf",        # マイカーローン
        f"{BASE}/pdf/poster_myhomeroan_241010.pdf",       # 住宅ローン  
        f"{BASE}/pdf/kyouikuroan_241010.pdf"              # 教育ローン
    ]
