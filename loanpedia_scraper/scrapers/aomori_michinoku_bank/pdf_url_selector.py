# loan_scraper/pdf_url_selector.py
# -*- coding: utf-8 -*-
from typing import Optional, Dict


def select_overview_pdf_url(
    product_profile: Dict,
    override_pdf_url: Optional[str] = None,
) -> Optional[str]:
    """固定運用: override_pdf_url > product_profile['pdf_url_override']"""
    return override_pdf_url or product_profile.get("pdf_url_override")
