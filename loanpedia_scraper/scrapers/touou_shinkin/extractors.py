# loan_scraper/extractors.py
# -*- coding: utf-8 -*-
from typing import Tuple, Optional
import re


def to_month_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    """返済期間の月数範囲を抽出（表記ゆれ対応）"""
    # 「ヶ月/か月/カ月/ヵ月/ケ月」表記を許容
    mon = r"(?:ヶ月|か月|カ月|ヵ月|ケ月)"

    # 具体的な期間パターンを広くカバー
    patterns = [
        rf"(?:期間|返済期間|借入期間)[^\n]{{0,20}}?(\d+)\s*年\s*(?:以内|まで|以下)?",
        rf"(?:期間|返済期間|借入期間)[^\n]{{0,20}}?(\d+)\s*{mon}\s*(?:以内|まで|以下)?",
        rf"(?:最長|最大)[^\n]{{0,10}}?(\d+)\s*年",
        rf"(?:最長|最大)[^\n]{{0,10}}?(\d+)\s*{mon}",
        r"(\d+)\s*年\s*(?:以内|まで|以下)",
        rf"(\d+)\s*{mon}\s*(?:以内|まで|以下)",
        r"(\d+)\s*年",
        rf"(\d+)\s*{mon}",
    ]

    months = []
    years = []

    for pattern in patterns:
        for m in re.findall(pattern, text):
            try:
                val = int(m)
            except Exception:
                continue
            if "年" in pattern:
                if 1 <= val <= 40:  # 上限やや広く
                    years.append(val)
            else:
                if 1 <= val <= 480:
                    months.append(val)

    # フォールバック
    if not months and not years:
        months = [int(x) for x in re.findall(rf"(\d+)\s*{mon}", text) if 1 <= int(x) <= 480]
        years = [int(x) for x in re.findall(r"(\d+)\s*年", text) if 1 <= int(x) <= 40]

    # すべての候補（月単位）
    all_months = list(months)
    if years:
        all_months += [y * 12 for y in years]

    if not all_months:
        return None, None

    # 妥当性フィルタ（最低6ヶ月を優先。一般的な無担保ローンの最短想定）
    valid = [m for m in all_months if 6 <= m <= 480]
    if valid:
        return min(valid), max(valid)
    # フィルタに全落ちの場合は非フィルタの範囲で返す
    return min(all_months), max(all_months)


def extract_touou_loan_amounts(text: str) -> Tuple[Optional[int], Optional[int]]:
    """東奥信用金庫の融資額パターンに特化した抽出"""
    import unicodedata
    text = unicodedata.normalize('NFKC', text or "")

    amounts = []

    def _to_yen(amount_str: str, unit: str) -> Optional[int]:
        try:
            amount = int(amount_str.replace(',', ''))
            if unit == '万':
                return amount * 10000
            elif unit == '億':
                return amount * 100000000
            else:
                return amount
        except ValueError:
            return None

    # 融資金額パターン
    patterns = [
        r'融資金額[^0-9]*(\d+(?:,\d+)?)\s*(万|億)円?\s*以内',
        r'(\d+(?:,\d+)?)\s*(万|億)円?\s*以内',
        r'最大\s*(\d+(?:,\d+)?)\s*(万|億)円?',
        r'限度額\s*(\d+(?:,\d+)?)\s*(万|億)円?'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for amount_str, unit in matches:
            amount = _to_yen(amount_str, unit)
            if amount and 10000 <= amount <= 100000000:  # 1万円〜1億円の妥当範囲
                amounts.append(amount)

    if amounts:
        # 重複除去
        amounts = sorted(set(amounts))
        if len(amounts) == 1:
            return (None, amounts[0])  # 上限のみ
        return (min(amounts), max(amounts))
    return (None, None)


def to_yen_range(text: str):
    """融資額抽出（東奥信用金庫特化版を優先使用）"""
    return extract_touou_loan_amounts(text)


def extract_age(text: str) -> Tuple[Optional[int], Optional[int]]:
    m1 = re.search(r"満?\s*(\d{1,2})\s*歳\s*以上", text)
    m2 = re.search(
        r"(?:満?\s*(\d{1,2})\s*歳\s*以下|完済時.*?満?\s*(\d{1,2})\s*歳以下)", text
    )
    mn = int(m1.group(1)) if m1 else None
    mx = int(m2.group(1) or m2.group(2)) if m2 else None
    return mn, mx


def extract_repayment(text: str):
    m = re.search(r"(元利均等|元金均等).*?返済", text)
    return m.group(0) if m else None


def interest_type_from_hints(text: str, hints: list[str]):
    """ヒントに依存しすぎず、本文に『固定』『変動』があれば推定"""
    t = text or ""
    # まず本文から直接推定
    if "固定" in t and "変動" not in t:
        return "固定金利"
    if "変動" in t:
        return "変動金利"
    # 本文から取れなければヒントで補完
    for h in hints or []:
        if "固定" in h and "変動" not in h:
            return "固定金利"
        if "変動" in h:
            return "変動金利"
    return None


def zenkaku_to_hankaku(text: str) -> str:
    """全角数字を半角数字に変換"""
    zenkaku = "０１２３４５６７８９"
    hankaku = "0123456789"
    for z, h in zip(zenkaku, hankaku):
        text = text.replace(z, h)
    return text


def z2h(text: str) -> str:
    """全角文字を半角文字に変換（簡易版）"""
    return zenkaku_to_hankaku(text)


def clean_rate_cell(text: str) -> str:
    """金利セルのテキストをクリーンアップ"""
    if not text:
        return ""
    # 改行を空白に変換
    text = text.replace("\n", " ").replace("\r", " ")
    # 複数の空白を単一空白に変換
    text = re.sub(r"\s+", " ", text)
    # 前後の空白を削除
    return text.strip()


def extract_amount_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """テキストから融資額の範囲を抽出"""
    return to_yen_range(text)


def extract_term_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """テキストから融資期間の範囲を抽出"""
    return to_month_range(text)