"""HTML parsing helpers for Aoimori Shinkin.

Keep simple: regex-based extraction for product name and basic rate ranges.
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, Tuple

RATE_PATTERNS = [
    r"年\s*(\d+\.\d+)\s*[%％]\s*[〜~～]\s*年\s*(\d+\.\d+)\s*[%％]",
    r"(\d+\.\d+)\s*[%％]\s*[〜~～]\s*(\d+\.\d+)\s*[%％]",
]

# 金額（万円/円）の範囲
AMOUNT_PATTERNS = [
    r"(\d{1,3}(?:,\d{3})*|\d+)(?:\s*万円|\s*万|\s*,?\s*円)[^\n～〜-]*[～〜-]\s*(\d{1,3}(?:,\d{3})*|\d+)(?:\s*万円|\s*万|\s*,?\s*円)",
    r"(\d{1,3}(?:,\d{3})*|\d+)\s*万円[^\n]*?(\d{1,3}(?:,\d{3})*|\d+)\s*万円",
]

# 期間（ヶ月/年）の範囲
TERM_PATTERNS = [
    r"(\d{1,2})\s*ヶ?月[^\n]*?[～〜-]\s*(\d{1,2})\s*ヶ?月",
    r"(\d{1,2})\s*年[^\n]*?[～〜-]\s*(\d{1,2})\s*年",
]

AGE_PATTERNS = [
    r"満?(\d{1,2})\s*歳以[上後][^\n]*?満?(\d{1,2})\s*歳以[下前]",
]


def extract_text(soup: BeautifulSoup) -> str:
    return soup.get_text("\n", strip=True)


def parse_product_name(soup: BeautifulSoup) -> str:
    for sel in ["h1", "h2", "title"]:
        el = soup.find(sel)
        if el:
            t = el.get_text(strip=True)
            if any(k in t for k in ["ローン", "カード", "プラン"]):
                return t
    return "青い森信用金庫 ローン"


def parse_rate_range_from_text(txt: str) -> Dict[str, Any]:
    for pat in RATE_PATTERNS:
        m = re.search(pat, txt)
        if m:
            return {
                "min_interest_rate": float(m.group(1)),
                "max_interest_rate": float(m.group(2)),
            }
    # single rate fallback
    m2 = re.search(r"(\d+\.\d+)\s*[%％]", txt)
    if m2:
        r = float(m2.group(1))
        return {"min_interest_rate": r, "max_interest_rate": r}
    return {}


def _to_yen(num_text: str) -> int:
    t = num_text.replace(",", "").strip()
    try:
        return int(t)
    except ValueError:
        return 0


def parse_amount_range_from_text(txt: str) -> Dict[str, Any]:
    # まず万円表記優先で処理
    for pat in AMOUNT_PATTERNS:
        m = re.search(pat, txt)
        if m:
            a, b = m.group(1), m.group(2)
            # 万円表記か円表記かざっくり判定
            segment = m.group(0)
            is_man = ("万" in segment)
            mul = 10000 if is_man else 1
            return {
                "min_loan_amount": _to_yen(a) * mul,
                "max_loan_amount": _to_yen(b) * mul,
            }
    return {}


def parse_term_range_from_text(txt: str) -> Dict[str, Any]:
    for pat in TERM_PATTERNS:
        m = re.search(pat, txt)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            # 年表記なら月へ換算
            if "年" in m.group(0):
                a *= 12
                b *= 12
            return {"min_loan_term_months": a, "max_loan_term_months": b}
    return {}


def parse_age_from_text(txt: str) -> Dict[str, Any]:
    for pat in AGE_PATTERNS:
        m = re.search(pat, txt)
        if m:
            return {"min_age": int(m.group(1)), "max_age": int(m.group(2))}
    return {}


def parse_html_document(soup: BeautifulSoup) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "product_name": parse_product_name(soup),
    }
    txt = extract_text(soup)
    item.update(parse_rate_range_from_text(txt))
    item.update(parse_amount_range_from_text(txt))
    item.update(parse_term_range_from_text(txt))
    item.update(parse_age_from_text(txt))
    return item
