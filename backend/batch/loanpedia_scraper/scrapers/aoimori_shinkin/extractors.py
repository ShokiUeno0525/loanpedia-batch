from __future__ import annotations
import re
import logging
from typing import Optional
from unicodedata import normalize
from decimal import Decimal, ROUND_DOWN, InvalidOperation

logger = logging.getLogger(__name__)


def zenkaku_to_hankaku(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", normalize("NFKC", text)).strip()


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
        logger.warning(f"金利の抽出失敗: テキストから金利情報を検出できませんでした (入力: {text})")
        return None

    number_str = match.group(1).replace(",", "")  # 桁区切りカンマ削除

    try:
        return Decimal(number_str).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    except (InvalidOperation, ValueError):
        logger.warning(f"金利の変換失敗: 数値への変換に失敗しました (入力: {number_str})")
        return None
