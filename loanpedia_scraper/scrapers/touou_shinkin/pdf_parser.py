"""PDF解析ユーティリティ

pdfplumber による表抽出を中心とした薄いラッパー。金利表の抽出に適した実装。
依存を増やさないため OCR は既定で無効（環境変数で有効化可能）。
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
import io
import re
import os
import requests
import pdfplumber

from .extractors import z2h, clean_rate_cell

# 任意のOCRスタック（環境変数で有効化した場合のみ使用）
try:
    import pypdfium2 as pdfium  # type: ignore
    from PIL import Image  # pillow
    import pytesseract  # type: ignore
    HAS_OCR = True
except Exception:
    HAS_OCR = False


def guess_date(text: str) -> Optional[str]:
    """テキストから日付を推定"""
    text = z2h(text)
    m = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


HEADER_ALIASES = {
    "product_name": ["商品名", "商品", "プラン", "名称", "商品／プラン", "取扱商品", "ローン商品"],
    "rate_campaign": ["キャンペーン", "金利優遇", "優遇後金利", "増額金利", "特別金利", "優遇金利"],
    "rate_floating": ["変動金利", "基準金利", "通常金利", "店頭金利", "年利", "利率"],
    "rate_incl_guarantee": ["保証料込", "保証料込み", "保証料含む"],
    "loan_limit": ["融資限度額", "限度額", "融資額", "貸付限度額"],
    "loan_term": ["融資期間", "返済期間", "期間", "貸付期間"],
}


def find_col_index(header_cells: List[str], candidates: List[str]) -> Optional[int]:
    """ヘッダー行から指定されたキーワードに合致する列のインデックスを検索"""
    for i, h in enumerate(header_cells):
        hh = z2h(h)
        if any(z2h(cand) in hh for cand in candidates):
            return i
    return None


def extract_tables_pdfplumber(pdf_bytes: bytes) -> List[Tuple[int, List[List[str]]]]:
    """PDFから表を抽出"""
    results: List[Tuple[int, List[List[str]]]] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pi, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
            except Exception:
                tables = []
            for t in tables or []:
                norm = [[("" if c is None else str(c)) for c in row] for row in t]
                results.append((pi, norm))
    return results


def score_table(table: List[List[str]]) -> float:
    """表の有用性をスコアリング"""
    flat = " ".join(z2h(c) for row in table for c in row)
    score = 0.0
    for kw in ["金利", "％", "%", "保証", "年", "変動", "キャンペーン", "融資", "限度額"]:
        score += flat.count(kw) * 1.0
    max_cols = max(len(r) for r in table) if table else 0
    score += max_cols * 0.2 + len(table) * 0.1
    return score


def pick_candidate_tables(tables: List[Tuple[int, List[List[str]]]], topk: int = 3):
    """最も有用と思われる表を選択"""
    scored = [(pi, t, score_table(t)) for (pi, t) in tables if t and len(t) >= 2]
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:topk]


def table_to_records(table: List[List[str]], source_url: str, page_index: int, as_of: Optional[str]) -> List[Dict[str, Any]]:
    """表データを構造化レコードに変換"""
    header = [z2h(c) for c in table[0]]
    rows = table[1:]

    idx_name = find_col_index(header, HEADER_ALIASES["product_name"]) or 0
    idx_camp = find_col_index(header, HEADER_ALIASES["rate_campaign"])
    idx_float = find_col_index(header, HEADER_ALIASES["rate_floating"])
    idx_incl = find_col_index(header, HEADER_ALIASES["rate_incl_guarantee"])
    idx_limit = find_col_index(header, HEADER_ALIASES["loan_limit"])
    idx_term = find_col_index(header, HEADER_ALIASES["loan_term"])

    out: List[Dict[str, Any]] = []
    for r in rows:
        r = r + [""] * (len(header) - len(r))
        name = z2h(r[idx_name]) if idx_name < len(r) else ""

        # 空の行をスキップ
        if not name or name.strip() == "":
            continue

        record = {
            "product_name": name,
            "source_url": source_url,
            "pdf_page": page_index + 1,
            "as_of_date": as_of,
        }

        # 金利情報
        if idx_camp is not None and idx_camp < len(r):
            camp_rate = clean_rate_cell(r[idx_camp])
            if camp_rate is not None:
                record["interest_rate_campaign"] = camp_rate

        if idx_float is not None and idx_float < len(r):
            float_rate = clean_rate_cell(r[idx_float])
            if float_rate is not None:
                record["interest_rate_floating"] = float_rate

        if idx_incl is not None and idx_incl < len(r):
            incl_rate = clean_rate_cell(r[idx_incl])
            if incl_rate is not None:
                record["interest_rate_with_guarantee"] = incl_rate

        # 融資限度額
        if idx_limit is not None and idx_limit < len(r):
            limit_text = z2h(r[idx_limit])
            if limit_text:
                record["loan_limit_text"] = limit_text

        # 融資期間
        if idx_term is not None and idx_term < len(r):
            term_text = z2h(r[idx_term])
            if term_text:
                record["loan_term_text"] = term_text

        out.append(record)

    return out


def extract_from_pdf_url(pdf_url: str) -> List[Dict[str, Any]]:
    """PDF URLから表データを抽出して構造化"""
    try:
        resp = requests.get(pdf_url, timeout=30)
        resp.raise_for_status()

        tables = extract_tables_pdfplumber(resp.content)
        if not tables:
            return []

        # 全文からas_of_dateを推定
        as_of = None
        try:
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() or ""
                as_of = guess_date(full_text)
        except Exception:
            pass

        # 最も有用な表を選択
        candidates = pick_candidate_tables(tables, topk=2)

        results = []
        for page_index, table, score in candidates:
            records = table_to_records(table, pdf_url, page_index, as_of)
            results.extend(records)

        return results

    except Exception as e:
        print(f"PDF解析エラー ({pdf_url}): {e}")
        return []