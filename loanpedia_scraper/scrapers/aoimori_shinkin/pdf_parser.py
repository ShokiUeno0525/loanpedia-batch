"""PDF parsing utilities.

Thin wrapper around pdfplumber-based table extraction suitable for interest
rate tables. OCR is intentionally omitted to avoid extra dependencies.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
import io
import re
import os
import requests
import pdfplumber

from .extractors import z2h, clean_rate_cell

# Optional OCR stack
try:
    import pypdfium2 as pdfium  # type: ignore
    from PIL import Image  # pillow
    import pytesseract  # type: ignore
    HAS_OCR = True
except Exception:
    HAS_OCR = False


def guess_date(text: str) -> Optional[str]:
    text = z2h(text)
    m = re.search(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


HEADER_ALIASES = {
    "product_name": ["商品名", "商品", "プラン", "名称", "商品／プラン", "取扱商品"],
    "rate_campaign": ["キャンペーン", "金利優遇", "優遇後金利", "増額金利", "特別金利"],
    "rate_floating": ["変動金利", "基準金利", "通常金利", "店頭金利", "年利"],
    "rate_incl_guarantee": ["保証料込", "保証料込み", "保証料含む"],
}


def find_col_index(header_cells: List[str], candidates: List[str]) -> Optional[int]:
    for i, h in enumerate(header_cells):
        hh = z2h(h)
        if any(z2h(cand) in hh for cand in candidates):
            return i
    return None


def extract_tables_pdfplumber(pdf_bytes: bytes) -> List[Tuple[int, List[List[str]]]]:
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
    flat = " ".join(z2h(c) for row in table for c in row)
    score = 0.0
    for kw in ["金利", "％", "%", "保証", "年", "変動", "キャンペーン"]:
        score += flat.count(kw) * 1.0
    max_cols = max(len(r) for r in table) if table else 0
    score += max_cols * 0.2 + len(table) * 0.1
    return score


def pick_candidate_tables(tables: List[Tuple[int, List[List[str]]]], topk: int = 3):
    scored = [(pi, t, score_table(t)) for (pi, t) in tables if t and len(t) >= 2]
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:topk]


def table_to_records(table: List[List[str]], source_url: str, page_index: int, as_of: Optional[str]) -> List[Dict[str, Any]]:
    header = [z2h(c) for c in table[0]]
    rows = table[1:]

    idx_name = find_col_index(header, HEADER_ALIASES["product_name"]) or 0
    idx_camp = find_col_index(header, HEADER_ALIASES["rate_campaign"])  # may be None
    idx_float = find_col_index(header, HEADER_ALIASES["rate_floating"])  # may be None
    idx_incl = find_col_index(header, HEADER_ALIASES["rate_incl_guarantee"])  # may be None

    out: List[Dict[str, Any]] = []
    for r in rows:
        r = r + [""] * (len(header) - len(r))
        name = z2h(r[idx_name]) if idx_name < len(r) else ""
        camp = clean_rate_cell(r[idx_camp]) if idx_camp is not None and idx_camp < len(r) else None
        flt = clean_rate_cell(r[idx_float]) if idx_float is not None and idx_float < len(r) else None
        incl = clean_rate_cell(r[idx_incl]) if idx_incl is not None and idx_incl < len(r) else None

        if not name and all(v is None for v in [camp, flt, incl]):
            continue

        out.append(
            {
                "institution_name": "青い森信用金庫",
                "product_name": name or None,
                "rate_campaign": camp,
                "rate_floating": flt,
                "rate_incl_guarantee": incl,
                "source_url": source_url,
                "page_index": page_index,
                "as_of": as_of,
            }
        )
    return out


def extract_from_pdf_url(url: str) -> List[Dict[str, Any]]:
    pdf_bytes = requests.get(url, timeout=30).content

    as_of: Optional[str] = None
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            as_of = guess_date(all_text) or as_of
    except Exception:
        pass

    tables = extract_tables_pdfplumber(pdf_bytes)
    cands = pick_candidate_tables(tables, topk=4)

    records: List[Dict[str, Any]] = []
    for pi, tab, _score in cands:
        try:
            recs = table_to_records(tab, source_url=url, page_index=pi, as_of=as_of)
            records.extend(recs)
        except Exception:
            continue

    # OCR fallback when no records
    if not records and HAS_OCR and os.getenv("AOIMORI_SHINKIN_ENABLE_OCR", "false").lower() == "true":
        try:
            # Allow custom Tesseract path
            tess_cmd = os.getenv("TESSERACT_CMD")
            if tess_cmd:
                import pytesseract as _pt
                _pt.pytesseract.tesseract_cmd = tess_cmd
            texts: List[str] = []
            doc = pdfium.PdfDocument(io.BytesIO(pdf_bytes))
            for i in range(len(doc)):
                page = doc.get_page(i)
                bmp = page.render(scale=2.0)
                img = bmp.to_pil()
                t = pytesseract.image_to_string(img, lang=os.getenv("TESS_LANG", "jpn"))
                texts.append(t)
            # Aggregate parse over all text
            all_text = "\n".join(texts)
            # product name heuristic
            prod_name = None
            for ln in all_text.splitlines():
                l = z2h(ln)
                if any(k in l for k in ["マイカー", "カーライフ", "マイカーローン", "ローン"]):
                    prod_name = l
                    break
            if not prod_name:
                prod_name = "マイカーローン（ポスター）"

            # date (validate month/day)
            as_of = guess_date(all_text)
            if as_of:
                try:
                    y, m, d = map(int, as_of.split("-"))
                    if not (2000 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31):
                        as_of = None
                except Exception:
                    as_of = None

            # collect all percentages and clamp to plausible range
            nums = [float(x) for x in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*%", all_text)]
            nums = [x for x in nums if 0.01 <= x <= 20.0]
            if nums:
                rmin, rmax = min(nums), max(nums)
                # ensure reasonable ordering
                if rmin > rmax:
                    rmin, rmax = rmax, rmin
                records.append(
                    {
                        "institution_name": "青い森信用金庫",
                        "product_name": prod_name,
                        "min_interest_rate": round(rmin, 3),
                        "max_interest_rate": round(rmax, 3),
                        "source_url": url,
                        "page_index": None,
                        "as_of": as_of,
                    }
                )
        except Exception:
            pass

    dedup: List[Dict[str, Any]] = []
    seen = set()
    for r in records:
        key = (
            r.get("product_name"),
            r.get("rate_campaign"),
            r.get("rate_floating"),
            r.get("rate_incl_guarantee"),
        )
        if r.get("product_name") and key not in seen:
            seen.add(key)
            dedup.append(r)
    return dedup
