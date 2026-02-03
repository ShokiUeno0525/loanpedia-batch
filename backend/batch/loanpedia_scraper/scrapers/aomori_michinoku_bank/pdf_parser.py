# loan_scraper/pdf_parser.py
# -*- coding: utf-8 -*-
from typing import Dict, Tuple, Optional
import io
import logging
import pdfplumber

logger = logging.getLogger(__name__)

try:
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.extractors import extract_age, to_month_range
except ImportError:
    import extractors
    extract_age = extractors.extract_age
    to_month_range = extractors.to_month_range


def pdf_bytes_to_text(b: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(b)) as pdf:
        for p in pdf.pages:
            pages.append(p.extract_text() or "")
    return "\n".join(pages)


def extract_pdf_fields(pdf_text: str) -> Dict:
    if not pdf_text:
        return {}
    agemin, agemax = extract_age(pdf_text)
    tmin, tmax = to_month_range(pdf_text)
    return {
        "min_age": agemin,
        "max_age": agemax,
        "min_loan_term": tmin,
        "max_loan_term": tmax,
    }


def extract_interest_range_from_pdf(pdf_text: str) -> Tuple[Optional[float], Optional[float]]:
    """PDF本文から金利範囲を抽出（%表記前提、表記揺れ対応）"""
    import re
    t = pdf_text or ""
    # 例: 1.20%〜2.15% / 1.2％ - 2.15％ / 実質年率1.2%～2.15%
    m = re.search(r"(\d+(?:\.\d+)?)\s*[％%]\s*[\-~〜～－–—]\s*(\d+(?:\.\d+)?)\s*[％%]", t)
    if m:
        a = float(m.group(1)) / 100.0
        b = float(m.group(2)) / 100.0
        return (min(a, b), max(a, b))
    nums = [float(x) / 100.0 for x in re.findall(r"(\d+(?:\.\d+)?)\s*[％%]", t)]
    if nums:
        return (min(nums), max(nums))
    logger.warning(f"PDF金利の抽出失敗: テキストから金利情報を検出できませんでした (サンプル: {t[:100] if t else ''}...)")
    return (None, None)
