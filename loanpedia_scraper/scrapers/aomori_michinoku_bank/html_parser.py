# loan_scraper/html_parser.py
# -*- coding: utf-8 -*-
from typing import Tuple, Optional, Dict, List
import re
import unicodedata
from bs4 import BeautifulSoup
from .extractors import (
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
    """金利/利率の文脈に限定して%を抽出。割引/優遇の%は除外。"""
    soup = BeautifulSoup(html, "lxml")
    text = _clean_text(soup)

    # 金利関連要素を優先探索
    interest_nodes: List[str] = []
    keywords = ["金利", "利率", "実質年率"]
    exclude_tokens = ["引下げ", "引き下げ", "優遇", "割引", "最大引下げ", "キャンペーン", "ポイント", "保証料"]

    for el in soup.find_all(text=re.compile("|".join(map(re.escape, keywords)))):
        node_text = el.parent.get_text(" ", strip=True) if el and el.parent else str(el)
        node_text = _normalize_text(node_text)
        # 直近の行のみ評価
        interest_nodes.append(node_text)

    def pick_from_text(t: str) -> Tuple[Optional[float], Optional[float]]:
        # 除外語が入る文はスキップ
        if any(x in t for x in exclude_tokens):
            return (None, None)
        # レンジパターン
        m = re.search(r"(\d+(?:\.\d+)?)\s*[％%]\s*[\-〜]\s*(\d+(?:\.\d+)?)\s*[％%]", t)
        if m:
            a = float(m.group(1)) / 100.0
            b = float(m.group(2)) / 100.0
            if 0.003 <= min(a, b) <= max(a, b) <= 0.2:
                return (min(a, b), max(a, b))
        # 単一パターン（複数出現時はmin/max）
        vals = [float(x) / 100.0 for x in re.findall(r"(\d+(?:\.\d+)?)\s*[％%]", t)]
        vals = [v for v in vals if 0.003 <= v <= 0.2]
        if vals:
            return (min(vals), max(vals))
        return (None, None)

    # 1) 金利関連ノードから抽出
    for nt in interest_nodes:
        a, b = pick_from_text(nt)
        if a is not None or b is not None:
            return a, b

    # 2) フォールバック: 全文から。ただし除外語を含む行は外す
    lines = [ln for ln in text.split("\n") if ln.strip() and not any(x in ln for x in exclude_tokens)]
    for ln in lines:
        a, b = pick_from_text(ln)
        if a is not None or b is not None:
            return a, b

    return (None, None)
