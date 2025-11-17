# loan_scraper/html_parser.py
# -*- coding: utf-8 -*-
from typing import Tuple, Optional, Dict
import re
import unicodedata
from bs4 import BeautifulSoup
try:
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.extractors import (
        to_month_range,
        to_yen_range,
        extract_age,
        extract_repayment,
    )
except ImportError:
    import extractors
    to_month_range = extractors.to_month_range
    to_yen_range = extractors.to_yen_range
    extract_age = extractors.extract_age
    extract_repayment = extractors.extract_repayment

def _normalize_text(s: str) -> str:
    """全角→半角、ダッシュ・波ダッシュの統一など簡易正規化"""
    if not s:
        return s
    t = unicodedata.normalize("NFKC", s)
    # ダッシュ/ハイフン類を半角ハイフンに統一
    t = re.sub(r"[‐‑‒–—―−－]", "-", t)
    # 波ダッシュ類を統一
    t = re.sub(r"[~〜～]", "〜", t)
    # 月表記ゆれ（か月/カ月/ヵ月/ケ月 → ヶ月）
    t = re.sub(r"(か月|カ月|ヵ月|ケ月)", "ヶ月", t)
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
    # 年X%〜年Y% のように「年」が挟まるケースも許容、カンマ小数も許容
    m = re.search(
        r"(?:年\s*)?(\d+(?:[\.,]\d+)?)\s*[％%]\s*[\-~〜～－–—]\s*(?:年\s*)?(\d+(?:[\.,]\d+)?)\s*[％%]",
        text,
    )
    if m:
        a = float(m.group(1).replace(",", ".")) / 100.0
        b = float(m.group(2).replace(",", ".")) / 100.0
        return (min(a, b), max(a, b))
    # フォールバック: %を含む数値を収集。ただし「引下げ」「▲」「最大」等の割引表現は除外
    nums = []
    for mm in re.finditer(r"(\d+(?:[\.,]\d+)?)\s*[％%]", text):
        s, e = mm.span()
        ctx = text[max(0, s - 16) : min(len(text), e + 16)]
        if any(k in ctx for k in ("引下げ", "▲", "最大", "割引")):
            continue
        try:
            nums.append(float(mm.group(1).replace(",", ".")) / 100.0)
        except Exception:
            pass
    if nums:
        return (min(nums), max(nums))
    return (None, None)
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/touou_shinkin/html_parser.py
# HTML解析ロジック（情報抽出と正規化）
# なぜ: 画面構造変化に耐える抽出の分離のため
# 関連: web_parser.py, product_scraper.py, extractors.py
