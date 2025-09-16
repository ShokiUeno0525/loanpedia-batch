from __future__ import annotations
import re
from typing import Optional
from unicodedata import normalize
from decimal import Decimal, ROUND_DOWN, InvalidOperation


def zenkaku_to_hankaku(text: Optional[str]) -> str:
    """全角文字を半角文字に変換し、空白を正規化"""
    if not text:
        return ""
    return re.sub(r"\s+", " ", normalize("NFKC", text)).strip()


# 短縮形エイリアス
z2h = zenkaku_to_hankaku


def clean_rate_cell(text: Optional[str]) -> Optional[Decimal]:
    """
    金利表記から最初の数値を取り出し、
    Decimal で小数第2位まで『切り捨て』て返す
    """
    if not text:
        return None

    normalized_text = zenkaku_to_hankaku(text).replace("％", "%")
    match = re.search(r"([0-9][0-9,\.]*[0-9])\s*%?", normalized_text)
    if not match:
        return None

    number_str = match.group(1).replace(",", "")  # 桁区切りカンマ削除

    try:
        return Decimal(number_str).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    except (InvalidOperation, ValueError):
        return None


def extract_amount_from_text(text: str) -> Optional[int]:
    """テキストから金額を抽出（万円単位を円に変換）"""
    text = z2h(text)

    # 万円表記
    match = re.search(r"([0-9,]+)\s*万円", text)
    if match:
        amount_str = match.group(1).replace(",", "")
        try:
            return int(amount_str) * 10000
        except ValueError:
            pass

    # 円表記
    match = re.search(r"([0-9,]+)\s*円", text)
    if match:
        amount_str = match.group(1).replace(",", "")
        try:
            return int(amount_str)
        except ValueError:
            pass

    return None


def extract_term_from_text(text: str) -> Optional[int]:
    """テキストから期間を抽出（月単位）"""
    text = z2h(text)

    # 年表記
    match = re.search(r"([0-9]+)\s*年", text)
    if match:
        try:
            return int(match.group(1)) * 12
        except ValueError:
            pass

    # 月表記
    match = re.search(r"([0-9]+)\s*ヶ?月", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None