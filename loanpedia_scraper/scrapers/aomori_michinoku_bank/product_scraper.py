# loan_scraper/product_scraper.py
# -*- coding: utf-8 -*-
from typing import Tuple, Dict, Any, List, TYPE_CHECKING, cast
import time
from urllib.parse import urljoin
import re

try:
    # Try package-style imports first
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.http_client import fetch_html, fetch_bytes
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.config import START, pick_profile
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.html_parser import parse_common_fields_from_html, extract_interest_range_from_html
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.pdf_parser import pdf_bytes_to_text, extract_pdf_fields, extract_interest_range_from_pdf
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.extractors import interest_type_from_hints
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.hash_utils import sha_bytes
    # models imported separately via importlib below
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.rate_pages import (
        guess_rate_slug_from_url,
        fetch_interest_range_from_rate_page,
    )
except ImportError:
    # Fall back to direct module imports (Lambda environment)
    import http_client
    import config
    import html_parser
    import pdf_parser
    import extractors
    import hash_utils
    # models imported separately via importlib below
    
    fetch_html = http_client.fetch_html
    fetch_bytes = http_client.fetch_bytes
    START = config.START
    pick_profile = config.pick_profile
    parse_common_fields_from_html = html_parser.parse_common_fields_from_html
    extract_interest_range_from_html = html_parser.extract_interest_range_from_html
    pdf_bytes_to_text = pdf_parser.pdf_bytes_to_text
    extract_pdf_fields = pdf_parser.extract_pdf_fields
    extract_interest_range_from_pdf = pdf_parser.extract_interest_range_from_pdf
    interest_type_from_hints = extractors.interest_type_from_hints
    sha_bytes = hash_utils.sha_bytes
    # models module is imported via importlib below
    # Import rate_pages functions
    import rate_pages
    guess_rate_slug_from_url = rate_pages.guess_rate_slug_from_url
    fetch_interest_range_from_rate_page = rate_pages.fetch_interest_range_from_rate_page

# For type checking only, import model classes without affecting runtime
if TYPE_CHECKING:
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.models import LoanProduct, RawLoanData

# Resolve models module in both runtime environments without redefining imports
import importlib
try:
    models_module = importlib.import_module(
        "loanpedia_scraper.scrapers.aomori_michinoku_bank.models"
    )
except ImportError:
    models_module = importlib.import_module("models")


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


def _apply_sanity(merged: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """抽出結果の簡易妥当性チェックと補完"""
    out = dict(merged)

    # 金利: 0.3%〜20%に収まらない場合は破棄
    rmin = out.get("min_interest_rate")
    rmax = out.get("max_interest_rate")
    if rmin is not None and rmax is not None:
        if rmin > rmax or rmin < 0.003 or rmax > 0.2:
            out["min_interest_rate"], out["max_interest_rate"] = None, None

    # 金額: 上限のみ→最小を10万円で補完
    amin = out.get("min_loan_amount")
    amax = out.get("max_loan_amount")
    if amax and (not amin or amin > amax):
        out["min_loan_amount"] = min(amax, 100_000)

    # 期間: min>max の場合は入替
    tmin = out.get("min_loan_term")
    tmax = out.get("max_loan_term")
    if tmin and tmax and tmin > tmax:
        out["min_loan_term"], out["max_loan_term"] = tmax, tmin

    # 年齢: 既定補完
    ltype = (profile.get("loan_type") or "").strip()
    default_age = {
        "教育ローン": (20, 75),
        "マイカーローン": (18, 75),
        "フリーローン": (20, 80),
        "おまとめローン": (20, 69),
    }.get(ltype, (20, 75))

    agemin = out.get("min_age")
    agemax = out.get("max_age")
    if agemin is None and agemax is None:
        out["min_age"], out["max_age"] = default_age
    else:
        if agemin is None:
            out["min_age"] = default_age[0]
        if agemax is None:
            out["max_age"] = default_age[1]

    return out


def build_loan_product(
    fields: Dict[str, Any], profile: Dict[str, Any], source_ref: str, fin_id: int, variant: str | None = None
) -> "LoanProduct":
    itype = interest_type_from_hints(
        fields["extracted_text"], profile.get("interest_type_hints", [])
    )
    special = extract_specials(fields["extracted_text"], profile)
    if variant:
        tag = "WEB完結型" if variant == "web" else ("来店型" if variant == "store" else None)
        if tag:
            special = f"{special} / {tag}" if special else tag
    return cast("LoanProduct", models_module.LoanProduct(
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
    ))


def build_raw(
    html: str, extracted_text: str, content_hash: str, url: str, fin_id: int
) -> "RawLoanData":
    return cast("RawLoanData", models_module.RawLoanData(
        financial_institution_id=fin_id,
        source_url=url,
        html_content=html,
        extracted_text=extracted_text,
        content_hash=content_hash,
        scraping_status="success",
        scraped_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
    ))


def _choose_product_name(
    html_fields: Dict[str, Any], profile: Dict[str, Any], variant: str | None = None
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
    variant: str | None = None,  # 'web' or 'store'
) -> Tuple["LoanProduct", "RawLoanData"]:
    # 1) HTML
    html = fetch_html(url)
    html_fields = parse_common_fields_from_html(html)

    # 2) プロファイル＆名称
    profile = pick_profile(url)
    base_name = _choose_product_name(html_fields, profile, variant)
    if variant:
        suffix = "〈WEB完結型〉" if variant == "web" else ("〈来店型〉" if variant == "store" else "")
        product_name = f"{base_name}{suffix}" if base_name else base_name
    else:
        product_name = base_name
    html_fields["product_name"] = product_name

    # 3) 金利はHTML優先、なければPDFから補完
    rate_min, rate_max = extract_interest_range_from_html(html)

    # 4) PDF URL（固定のみ）
    # 固定運用: override優先 → プロファイルの固定PDF
    pdf_url = pdf_url_override or profile.get("pdf_url_override")
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

    # 7) 金利: HTML優先、未取得ならPDF→金利一覧ページで補完
    if rate_min is None and rate_max is None:
        pmin, pmax = extract_interest_range_from_pdf(pdf_text)
        rate_min, rate_max = pmin, pmax
    slug = guess_rate_slug_from_url(url)
    if rate_min is None and rate_max is None:
        if slug:
            rmin, rmax = fetch_interest_range_from_rate_page(slug)
            rate_min, rate_max = rmin, rmax
    # variant 指定があれば、rateページの該当区分で上書き（商品ページが単一値の場合の分離対応）
    if slug and variant:
        vrmin, vrmax = fetch_interest_range_from_rate_page(slug, variant=variant)
        if vrmin is not None and vrmax is not None:
            rate_min, rate_max = vrmin, vrmax
    fields["min_interest_rate"], fields["max_interest_rate"] = rate_min, rate_max

    # 7.5) 妥当性チェック/補完
    fields = _apply_sanity(fields, profile)

    # 8) 組み立て
    product = build_loan_product(fields, profile, pdf_url, fin_id, variant=variant)
    raw = build_raw(html, fields["extracted_text"], content_hash, url, fin_id)
    return product, raw


def discover_product_links(start_url: str = START) -> list[str]:
    html = fetch_html(start_url)
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    urls = set()
    for a in soup.select('a[href*="/kojin/loan/"]'):
        href_val = a.get("href")
        href = href_val if isinstance(href_val, str) else ""
        u = urljoin(start_url, href)
        if re.search(r"/kojin/loan/[^/]+/?$", u) and not u.rstrip("/").endswith("loan"):
            urls.add(u)
    return sorted(urls)
