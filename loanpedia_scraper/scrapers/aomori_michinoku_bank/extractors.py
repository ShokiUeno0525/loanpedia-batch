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


def to_yen_range(text: str):
    def _to_yen(tok: str):
        tok = tok.replace(",", "").replace("円", "")
        m = re.match(r"(\d+(?:\.\d+)?)(億|万)?", tok)
        if not m:
            return None
        v, u = float(m.group(1)), m.group(2)
        if u == "億":
            return int(v * 100_000_000)
        if u == "万":
            return int(v * 10_000)
        return int(v)

    # より具体的な融資額パターンを探す
    patterns = [
        r"(\d+(?:,\d+)?(?:\.\d+)?)(億|万)円?\s*(?:まで|以下|以内)",
        r"(\d+(?:,\d+)?(?:\.\d+)?)(億|万)円?\s*～\s*(\d+(?:,\d+)?(?:\.\d+)?)(億|万)円?",
        r"融資.*?(\d+(?:,\d+)?)(万)円?\s*(?:まで|以下|以内)",
        r"最高.*?(\d+(?:,\d+)?)(万|億)円?",
        r"最大.*?(\d+(?:,\d+)?)(万|億)円?",
    ]
    
    nums = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) == 2:  # 単一の金額
                val, unit = match
                parsed = _to_yen(f"{val}{unit}")
                if parsed and parsed > 10000:  # 1万円以上の妥当な金額のみ
                    nums.append(parsed)
            elif len(match) == 4:  # 範囲
                val1, unit1, val2, unit2 = match
                parsed1 = _to_yen(f"{val1}{unit1}")
                parsed2 = _to_yen(f"{val2}{unit2}")
                if parsed1 and parsed1 > 10000:
                    nums.append(parsed1)
                if parsed2 and parsed2 > 10000:
                    nums.append(parsed2)
    
    if not nums:
        # フォールバック: 一般的な数字パターン
        fallback_tokens = re.findall(r"(\d+(?:,\d+)?)(万|億)円?", text)
        for val, unit in fallback_tokens:
            parsed = _to_yen(f"{val}{unit}")
            if parsed and parsed >= 10000:  # 1万円以上
                nums.append(parsed)
    # 重複を除去して一意な金額数を確認
    unique = sorted(set(nums))
    if not unique:
        return (None, None)
    # 単一金額のみ検出された場合は上限のみとみなし、下限は未確定にする
    # （後段の妥当性補完で10万円などのデフォルト最小額を設定する）
    if len(unique) == 1:
        return (None, unique[0])
    return (min(unique), max(unique))


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
