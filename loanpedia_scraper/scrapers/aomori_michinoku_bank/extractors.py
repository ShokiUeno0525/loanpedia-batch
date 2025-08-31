# loan_scraper/extractors.py
# -*- coding: utf-8 -*-
from typing import Tuple, Optional
import re
import unicodedata


def to_month_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    # 具体的な期間パターンを探す
    patterns = [
        r"(?:期間|返済期間|借入期間).*?(\d+)\s*年\s*以内",
        r"(?:期間|返済期間|借入期間).*?(\d+)\s*ヶ月\s*以内",
        r"(?:最長|最大).*?(\d+)\s*年",
        r"(?:最長|最大).*?(\d+)\s*ヶ月",
        r"(\d+)\s*年\s*以内",
        r"(\d+)\s*ヶ月\s*以内",
    ]
    
    months = []
    years = []
    
    # パターンベースの抽出
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            val = int(match)
            if "年" in pattern:
                if val <= 30:  # 妥当な年数範囲
                    years.append(val)
            elif "ヶ月" in pattern:
                if val <= 360:  # 妥当な月数範囲（30年以内）
                    months.append(val)
    
    # フォールバック: 一般的な期間パターン
    if not months and not years:
        month_matches = re.findall(r"(\d+)\s*ヶ月", text)
        year_matches = re.findall(r"(\d+)\s*年", text)
        
        months = [int(x) for x in month_matches if 1 <= int(x) <= 360]
        years = [int(x) for x in year_matches if 1 <= int(x) <= 30]
    
    # 候補を収集
    cands = []
    if months:
        cands.append((min(months), max(months)))
    if years:
        year_months = [y * 12 for y in years]
        cands.append((min(year_months), max(year_months)))
    
    if not cands:
        return None, None
    
    return min(c[0] for c in cands), max(c[1] for c in cands)


def to_yen_range(text: str):
    # 正規化
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[‐‑‒–—―−－]", "-", text)
    text = re.sub(r"[~〜～]", "〜", text)

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
    sep = r"[\-〜]"
    patterns = [
        # 上限表現（限度額/最大/最高/上限）
        rf"(?:最高|限度額|上限|最大)\s*(\d+(?:,\d+)?(?:\.\d+)?)(億|万)?円?",
        # 範囲（〜/～/-）
        rf"(\d+(?:,\d+)?(?:\.\d+)?)(億|万)?円?\s*{sep}\s*(\d+(?:,\d+)?(?:\.\d+)?)(億|万)?円?",
        # 融資〜まで表現
        r"融資.*?(\d+(?:,\d+)?)(万)円?\s*(?:まで|以下|以内)",
    ]

    nums = []
    matched_upper_only = False
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) == 2:  # 単一の金額（上限のみ等）
                val, unit = match
                parsed = _to_yen(f"{val}{unit}")
                if parsed and parsed > 10000:  # 1万円以上の妥当な金額のみ
                    nums.append(parsed)
                    matched_upper_only = True
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
    if not nums:
        return (None, None)

    mn, mx = (min(nums), max(nums))
    # 上限のみを拾ったと推測できる場合は既定の最小値（10万円）を補完
    if matched_upper_only and mn == mx:
        mn = min(mn, 100_000)
    return (mn, mx)


def extract_age(text: str) -> Tuple[Optional[int], Optional[int]]:
    text = unicodedata.normalize("NFKC", text)

    # 同行サイトで見られる代表的パターン
    # 下限
    m1 = re.search(r"満?\s*(\d{1,2})\s*歳\s*(?:以上|超)", text)

    # 上限（未満/以下/まで/完済時〜以下）
    m2 = re.search(r"完済時.*?満?\s*(\d{1,2})\s*歳\s*(以下|未満|まで)", text)
    m3 = re.search(r"満?\s*(\d{1,2})\s*歳\s*(以下|未満|まで|以内)", text)

    # 両端指定「xx歳以上yy歳以下」
    m4 = re.search(r"(\d{1,2})\s*歳\s*以上.*?(\d{1,2})\s*歳\s*(以下|未満|まで)", text)

    mn: Optional[int] = None
    mx: Optional[int] = None

    if m4:
        mn = int(m4.group(1))
        mx_val = int(m4.group(2))
        mx = mx_val - 1 if m4.group(3) == "未満" else mx_val
        return mn, mx

    if m1:
        mn = int(m1.group(1))
    if m2:
        val = int(m2.group(1))
        mx = val - 1 if m2.group(2) == "未満" else val
    elif m3:
        val = int(m3.group(1))
        mx = val - 1 if m3.group(2) == "未満" else val

    return mn, mx


def extract_repayment(text: str):
    m = re.search(r"(元利均等|元金均等).*?返済", text)
    return m.group(0) if m else None


def interest_type_from_hints(text: str, hints: list[str]):
    for h in hints or []:
        if h in text:
            if "固定" in h and "変動" not in h:
                return "固定金利"
            if "変動" in h:
                return "変動金利"
    return None
