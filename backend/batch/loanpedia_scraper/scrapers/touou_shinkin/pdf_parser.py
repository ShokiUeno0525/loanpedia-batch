# loan_scraper/pdf_parser.py
# -*- coding: utf-8 -*-
from typing import Dict, Tuple, Optional
import io
import re
import unicodedata
import logging
import pdfplumber

logger = logging.getLogger(__name__)

try:
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.extractors import extract_age, to_month_range
    from loanpedia_scraper.scrapers.touou_shinkin.extractors import extract_touou_loan_amounts
except ImportError:
    # 相対インポートにフォールバック（パッケージ内の実装を使用）
    from . import extractors  # type: ignore
    extract_age = extractors.extract_age  # type: ignore
    to_month_range = extractors.to_month_range  # type: ignore
    extract_touou_loan_amounts = extractors.extract_touou_loan_amounts  # type: ignore


def normalize_pdf_text(text: str) -> str:
    """PDFテキストを正規化（全角→半角変換など）"""
    if not text:
        return ""
    # Unicode正規化（全角→半角変換）
    text = unicodedata.normalize('NFKC', text)
    # 特殊な区切り文字を統一
    text = re.sub(r'[－–—]', '-', text)
    text = re.sub(r'[〜～]', '~', text)
    return text


def pdf_bytes_to_text(b: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(b)) as pdf:
        for p in pdf.pages:
            text = p.extract_text() or ""
            pages.append(normalize_pdf_text(text))
    return "\n".join(pages)


def extract_pdf_fields(pdf_text: str) -> Dict:
    if not pdf_text:
        return {}
    agemin, agemax = extract_age(pdf_text)
    tmin, tmax = to_month_range(pdf_text)
    amount_min, amount_max = extract_touou_loan_amounts(pdf_text)
    rate_min, rate_max = extract_touou_interest_rates(pdf_text)

    return {
        "min_age": agemin,
        "max_age": agemax,
        "min_loan_term": tmin,
        "max_loan_term": tmax,
        "min_loan_amount": amount_min,
        "max_loan_amount": amount_max,
        "min_interest_rate": rate_min,
        "max_interest_rate": rate_max,
    }


def extract_touou_interest_rates(pdf_text: str) -> Tuple[Optional[float], Optional[float]]:
    """東奥信用金庫の金利パターンに特化した抽出"""
    text = normalize_pdf_text(pdf_text or "")

    rates = []

    # 固定金利・変動金利パターン（最優先）
    fixed_match = re.search(r'固定金利\s*(\d+(?:\.\d+)?)\s*[％%]', text)
    if fixed_match:
        rates.append(float(fixed_match.group(1)))

    variable_match = re.search(r'変動金利\s*(\d+(?:\.\d+)?)\s*[％%]', text)
    if variable_match:
        rates.append(float(variable_match.group(1)))

    # 固定・変動金利が見つかった場合はそれを優先（パーセント→小数に変換）
    if rates:
        return (min(rates) / 100.0, max(rates) / 100.0)

    # 一般的な%パターン（遅延損害金等を除外）
    general_rates = [float(x) for x in re.findall(r'(\d+(?:\.\d+)?)\s*[％%]', text)]
    # 通常のローン金利範囲（0.5%～15%）に限定
    valid_rates = [r for r in general_rates if 0.5 <= r <= 15.0]

    if valid_rates:
        return (min(valid_rates) / 100.0, max(valid_rates) / 100.0)
    logger.warning(f"PDF金利の抽出失敗: テキストから金利情報を検出できませんでした (サンプル: {text[:100] if text else ''}...)")
    return (None, None)


def extract_interest_range_from_pdf(pdf_text: str) -> Tuple[Optional[float], Optional[float]]:
    """PDF本文から金利範囲を抽出（東奥信用金庫特化版）"""
    return extract_touou_interest_rates(pdf_text)
