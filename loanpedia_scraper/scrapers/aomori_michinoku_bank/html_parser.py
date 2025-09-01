# loan_scraper/html_parser.py
# -*- coding: utf-8 -*-
from typing import Tuple, Optional, Dict
import re
import unicodedata
from bs4 import BeautifulSoup
from loanpedia_scraper.scrapers.aomori_michinoku_bank.extractors import (
    to_month_range,
    to_yen_range,
    extract_age,
    extract_repayment,
)

def _normalize_text(s: str) -> str:
    """全角→半角、ダッシュ・波ダッシュの統一など簡易正規化"""
    if not s:
        return s
    t = unicodedata.normalize("NFKC", s)
    # ダッシュ/ハイフン類を半角ハイフンに統一
    t = re.sub(r"[‐‑‒–—―−－]", "-", t)
    # 波ダッシュ類を統一
    t = re.sub(r"[~〜～]", "〜", t)
    return t


def _clean_text(soup: BeautifulSoup) -> str:
    for t in soup(["script", "style", "noscript"]):
        t.extract()
    txt = soup.get_text("\n", strip=True)
    txt = _normalize_text(txt)
    return re.sub(r"\n{2,}", "\n", txt)


def parse_common_fields_from_html(html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")
    text = _clean_text(soup)
    h = soup.find(["h1", "h2"])
    name = _normalize_text(h.get_text(strip=True)) if h else None
    amin, amax = to_yen_range(text)
    tmin, tmax = to_month_range(text)
    agemin, agemax = extract_age(text)
    repay = extract_repayment(text)
    return {
        "product_name": name,
        "min_loan_amount": amin,
        "max_loan_amount": amax,
        "min_loan_term": tmin,
        "max_loan_term": tmax,
        "min_age": agemin,
        "max_age": agemax,
        "repayment_method": repay,
        "extracted_text": text,
        "soup": soup,
    }


def extract_interest_range_from_html(
    html: str,
) -> Tuple[Optional[float], Optional[float]]:
    soup = BeautifulSoup(html, "lxml")
    text = _clean_text(soup)
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*[％%]\s*[\-~〜～－–—]\s*(\d+(?:\.\d+)?)\s*[％%]", text
    )
    if m:
        a = float(m.group(1)) / 100.0
        b = float(m.group(2)) / 100.0
        return (min(a, b), max(a, b))
    nums = [float(x) / 100.0 for x in re.findall(r"(\d+(?:\.\d+)?)\s*[％%]", text)]
    if nums:
        return (min(nums), max(nums))
    return (None, None)
