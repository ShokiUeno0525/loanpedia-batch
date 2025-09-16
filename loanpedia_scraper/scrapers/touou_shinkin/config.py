from typing import Dict, Any, List
import os
import json
from urllib.parse import urlparse

BASE = "https://www.shinkin.co.jp/toshin"

# デフォルト値（マッチしなかった時）
_DEFAULT_PROFILE: Dict[str, Any] = {
    "loan_type": None,
    "category": None,
    "interest_type_hints": [],
    "pdf_priority_fields": [],
}

# PDF URL と商品タイプのマッピング
pdf_profiles: Dict[str, Dict[str, Any]] = {
    "carlife_s.pdf": {"loan_type": "car", "category": "auto", "product_name": "カーライフローン"},
    "mycarplus_s.pdf": {"loan_type": "car", "category": "auto", "product_name": "マイカープラス"},
    "kyoiku_s.pdf": {"loan_type": "education", "category": "education", "product_name": "教育ローン"},
    "newkyoiku_s.pdf": {"loan_type": "education", "category": "education", "product_name": "新教育ローン"},
    "kyoikucl_s.pdf": {"loan_type": "education", "category": "education", "product_name": "教育カードローン"},
    "free_s.pdf": {"loan_type": "freeloan", "category": "multi-purpose", "product_name": "フリーローン"},
}


def pick_profile_from_pdf(pdf_url: str) -> Dict[str, Any]:
    """PDF URLに対応するprofileを返す（なければデフォルト）"""
    for filename, profile in pdf_profiles.items():
        if filename in pdf_url:
            return profile
    return _DEFAULT_PROFILE


def get_pdf_urls() -> List[str]:
    """環境変数で指定がなければデフォルトのPDFリストを返す"""
    override = os.getenv("TOUOU_SHINKIN_PDF_URLS")
    if override:
        return json.loads(override)
    return [
        f"{BASE}/jyoho/loan/carlife_s.pdf?ver=1758023056981",
        f"{BASE}/jyoho/loan/mycarplus_s.pdf",
        f"{BASE}/jyoho/loan/kyoiku_s.pdf?ver=1758023363658",
        f"{BASE}/jyoho/loan/newkyoiku_s.pdf",
        f"{BASE}/jyoho/loan/kyoikucl_s.pdf",
        f"{BASE}/jyoho/loan/free_s.pdf?ver=1758023427210",
    ]


# 東奥信用金庫の組織情報
INSTITUTION_INFO = {
    "financial_institution": "東奥信用金庫",
    "institution_type": "信用金庫",
    "location": "青森県",
    "website": BASE,
}