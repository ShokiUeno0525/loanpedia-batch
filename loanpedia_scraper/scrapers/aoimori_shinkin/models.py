"""青い森信用金庫向けの軽量モデル/ビルダー"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime


def build_base_item() -> Dict[str, Any]:
    return {
        "institution_code": "0003",
        "institution_name": "青い森信用金庫",
        "website_url": "https://www.shinkin.co.jp/aoi/",
        "institution_type": "信用金庫",
        "scraped_at": datetime.now().isoformat(),
        "scraping_status": "success",
    }


def merge_product_fields(item: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out = dict(item)
    if extra:
        out.update(extra)
    return out
