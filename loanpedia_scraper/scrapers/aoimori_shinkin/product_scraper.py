"""Product scraper entrypoint for Aoimori Shinkin."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from .config import HEADERS, START, get_product_urls, get_pdf_urls
from . import http_client
from .html_parser import parse_html_document
from .pdf_parser import extract_from_pdf_url
from .models import build_base_item, merge_product_fields

logger = logging.getLogger(__name__)


class AoimoriShinkinScraper:
    """
    High-level scraper that coordinates HTML page parsing and optional
    PDF rate-table extraction.
    """

    def __init__(self, save_to_db: bool = False, db_config: Optional[Dict[str, Any]] = None):
        self.save_to_db = save_to_db
        self.db_config = db_config
        self.session = http_client.build_session(HEADERS)

    def scrape_loan_info(self, url: Optional[str] = None) -> Dict[str, Any]:
        item = build_base_item()

        results: List[Dict[str, Any]] = []
        html_error: Optional[str] = None

        # 1) HTML pages: explicit url > configured product list > START fallback
        attempted = False
        if url:
            attempted = True
            try:
                resp = http_client.get(self.session, url, timeout=15)
                soup = BeautifulSoup(resp.content, "html.parser")
                html_part = parse_html_document(soup)
                results.append(merge_product_fields(item, {**html_part, "source_url": url}))
            except Exception as e:
                html_error = str(e)
                logger.warning(f"HTML parse skipped/failed: {e}")
        else:
            plist = get_product_urls()
            if plist:
                attempted = True
                for p in plist:
                    purl = p.get("url")
                    try:
                        resp = http_client.get(self.session, purl, timeout=15)
                        soup = BeautifulSoup(resp.content, "html.parser")
                        html_part = parse_html_document(soup)
                        item_with_name = {**html_part}
                        if p.get("name") and not item_with_name.get("product_name"):
                            item_with_name["product_name"] = p["name"]
                        results.append(merge_product_fields(item, {**item_with_name, "source_url": purl}))
                    except Exception as e:
                        html_error = str(e)
                        logger.warning(f"HTML parse skipped/failed for {purl}: {e}")
            elif START:
                attempted = True
                try:
                    resp = http_client.get(self.session, START, timeout=15)
                    soup = BeautifulSoup(resp.content, "html.parser")
                    html_part = parse_html_document(soup)
                    results.append(merge_product_fields(item, {**html_part, "source_url": START}))
                except Exception as e:
                    html_error = str(e)
                    logger.warning(f"HTML parse skipped/failed: {e}")

        # 2) PDF tables (enabled via env)
        for pdf_url in get_pdf_urls():
            try:
                pdf_rows = extract_from_pdf_url(pdf_url)
                for r in pdf_rows:
                    results.append(merge_product_fields(item, r))
            except Exception as e:
                logger.warning(f"PDF parse skipped/failed for {pdf_url}: {e}")

        # Error semantics: in test mode, any HTML error forces a failed result
        import os
        if os.getenv("SCRAPING_TEST_MODE") == "true" and html_error:
            return {**item, "status": "failed", "error": html_error}

        # Otherwise: if nothing collected, return empty success or failed if HTML error only
        if not results:
            if html_error:
                return {**item, "status": "failed", "error": html_error}
            # otherwise still signal success with empty products
            return {**item, "products": [], "scraping_status": "success"}

        return {**item, "products": results, "scraping_status": "success"}
