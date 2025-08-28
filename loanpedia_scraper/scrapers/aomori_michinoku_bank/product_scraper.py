# loan_scraper/product_scraper.py
# -*- coding: utf-8 -*-
from typing import Tuple, Dict, Any, List
import time
from urllib.parse import urljoin
import re

from .http_client import fetch_html, fetch_bytes
from .config import START, pick_profile
from .html_parser import parse_common_fields_from_html, extract_interest_range_from_html
from .pdf_parser import pdf_bytes_to_text, extract_pdf_fields
from .extractors import interest_type_from_hints
from .hash_utils import sha_bytes
from .pdf_url_selector import select_overview_pdf_url
from .models import LoanProduct, RawLoanData


def extract_specials(text: str, profile: Dict[str, Any]) -> str | None:
    kws = profile.get("special_keywords") or []
    found = [kw for kw in kws if kw in text]
    return " / ".join(sorted(set(found))) or None


def merge_fields(
    html_fields: Dict[str, Any], pdf_fields: Dict[str, Any], priority_keys: List[str]
) -> Dict[str, Any]:
    merged = dict(html_fields)
    for k in priority_keys or []:
        if pdf_fields.get(k) is not None:
            merged[k] = pdf_fields[k]
    return merged


def build_loan_product(
    fields: Dict[str, Any], profile: Dict[str, Any], source_ref: str, fin_id: int
) -> LoanProduct:
    itype = interest_type_from_hints(
        fields["extracted_text"], profile.get("interest_type_hints", [])
    )
    special = extract_specials(fields["extracted_text"], profile)
    return LoanProduct(
        financial_institution_id=fin_id,
        product_name=fields.get("product_name"),
        loan_type=profile.get("loan_type"),
        category=profile.get("category"),
        min_interest_rate=fields.get("min_interest_rate"),
        max_interest_rate=fields.get("max_interest_rate"),
        interest_type=itype,
        min_loan_amount=fields.get("min_loan_amount"),
        max_loan_amount=fields.get("max_loan_amount"),
        min_loan_term=fields.get("min_loan_term"),
        max_loan_term=fields.get("max_loan_term"),
        repayment_method=fields.get("repayment_method"),
        min_age=fields.get("min_age"),
        max_age=fields.get("max_age"),
        income_requirements=None,
        guarantor_requirements=None,
        special_features=special,
        source_reference=source_ref,
        is_active=True,
    )


def build_raw(
    html: str, extracted_text: str, content_hash: str, url: str, fin_id: int
) -> RawLoanData:
    return RawLoanData(
        financial_institution_id=fin_id,
        source_url=url,
        html_content=html,
        extracted_text=extracted_text,
        content_hash=content_hash,
        scraping_status="success",
        scraped_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
    )


def _choose_product_name(
    html_fields: Dict[str, Any], profile: Dict[str, Any]
) -> str | None:
    return (
        profile.get("product_name_override")
        or profile.get("product_name")
        or html_fields.get("product_name")
    )


def scrape_product(
    url: str,
    fin_id: int = 1,
    pdf_url_override: str | None = None,  # 固定PDFのみ。カタログ/ページ内探索は行わない
) -> Tuple[LoanProduct, RawLoanData]:
    # 1) HTML
    html = fetch_html(url)
    html_fields = parse_common_fields_from_html(html)

    # 2) プロファイル＆名称
    profile = pick_profile(url)
    product_name = _choose_product_name(html_fields, profile)
    html_fields["product_name"] = product_name

    # 3) 金利はHTML
    rate_min, rate_max = extract_interest_range_from_html(html)

    # 4) PDF URL（固定のみ）
    pdf_url = select_overview_pdf_url(
        product_profile=profile,
        override_pdf_url=pdf_url_override,
    )
    if pdf_url is None:
        raise ValueError(f"pdf_url_override is required for fixed-only mode: {url}")

    # 5) PDF取得/抽出
    pdf_bytes = fetch_bytes(pdf_url)
    pdf_text = pdf_bytes_to_text(pdf_bytes) or ""
    content_hash = sha_bytes(pdf_bytes)

    # 6) マージ（PDF優先キー）
    pdf_fields = extract_pdf_fields(pdf_text)
    fields = merge_fields(
        html_fields, pdf_fields, profile.get("pdf_priority_fields", [])
    )
    fields["extracted_text"] = pdf_text or fields["extracted_text"]

    # 7) 金利はHTML最終
    fields["min_interest_rate"], fields["max_interest_rate"] = rate_min, rate_max

    # 8) 組み立て
    product = build_loan_product(fields, profile, pdf_url, fin_id)
    raw = build_raw(html, fields["extracted_text"], content_hash, url, fin_id)
    return product, raw


def discover_product_links(start_url: str = START) -> list[str]:
    html = fetch_html(start_url)
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    urls = set()
    for a in soup.select('a[href*="/kojin/loan/"]'):
        href = a.get("href") or ""
        u = urljoin(start_url, href)
        if re.search(r"/kojin/loan/[^/]+/?$", u) and not u.rstrip("/").endswith("loan"):
            urls.add(u)
    return sorted(urls)
