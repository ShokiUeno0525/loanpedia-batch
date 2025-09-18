#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/touou_shinkin/extractors.py
# 値抽出ユーティリティ（正規表現/パターン）
# なぜ: HTML/PDF抽出の共通ロジックを再利用可能にするため
# 関連: html_parser.py, pdf_parser.py, product_scraper.py

from typing import Tuple, Optional
import re
import unicodedata
from decimal import Decimal, ROUND_DOWN


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

    # 妥当性フィルタ（最低3ヶ月を許容。東しん: 3ヶ月～の表記あり）
    valid = [m for m in all_months if 3 <= m <= 480]
    if valid:
        return min(valid), max(valid)
    # フィルタに全落ちの場合は非フィルタの範囲で返す
    return min(all_months), max(all_months)


def extract_touou_loan_amounts(text: str) -> Tuple[Optional[int], Optional[int]]:
    """東奥信用金庫の融資額パターンに特化した抽出

    既存の実装は『ご融資金額 10万円以上1,000万円以内』のような1行レンジ表記で
    先頭の『10万円』を上限として誤認する場合があったため、
    まずは『以上…以内/まで』のレンジを優先的にパースするよう改善する。
    """
    import unicodedata
    text = unicodedata.normalize('NFKC', text or "")

    min_amount: Optional[int] = None
    max_amount: Optional[int] = None

    def _to_yen(amount_str: str, unit: str) -> Optional[int]:
        try:
            amount = int(amount_str.replace(',', ''))
            if unit == '万':
                return amount * 10_000
            elif unit == '億':
                return amount * 100_000_000
            else:
                return amount
        except ValueError:
            return None

    # 文脈を「融資金額」周辺に限定して誤検出を低減
    lines = text.split('\n')
    for line in lines:
        if not re.search(r'(融資金額|ご融資金額|ご融資額|融資額|ご融資限度額|限度額)', line):
            continue

        # 1) 最優先：『A円以上 … B円以内/まで』のレンジを同一行から抽出
        range_pat = re.compile(
            r'(\d+(?:,\d+)?)\s*(万|億)?円\s*以上[^0-9]{0,20}(\d+(?:,\d+)?)\s*(万|億)?円\s*(?:以内|まで)'
        )
        m = range_pat.search(line)
        if m:
            amin = _to_yen(m.group(1), m.group(2) or '')
            amax = _to_yen(m.group(3), m.group(4) or '')
            if amin and (min_amount is None or amin < min_amount):
                min_amount = amin
            if amax and (max_amount is None or amax > max_amount):
                max_amount = amax
            # レンジが取れたらこの行は確定
            continue

        # 2) 片側のみ：『B円以内/まで』を優先的に上限として抽出（行内で最後の数値を優先）
        last_max = None
        for m in re.finditer(r'(\d+(?:,\d+)?)\s*(万|億)?円\s*(?:以内|まで)', line):
            last_max = _to_yen(m.group(1), m.group(2) or '')
        if last_max and 10_000 <= last_max <= 100_000_000:
            max_amount = last_max if (max_amount is None or last_max > max_amount) else max_amount

        # 3) 片側のみ：『A円以上』を下限として抽出（行内で最初の数値を優先）
        first_min = None
        for m in re.finditer(r'(\d+(?:,\d+)?)\s*(万|億)?円\s*以上', line):
            first_min = first_min or _to_yen(m.group(1), m.group(2) or '')
        if first_min and 10_000 <= first_min <= 100_000_000:
            min_amount = first_min if (min_amount is None or first_min < min_amount) else min_amount

        # 4) 従来パターン（最大/上限/限度額などの単独表記）もフォールバックで拾う
        for pat in [
            r'(?:最大|上限)[^0-9]{0,5}(\d+(?:,\d+)?)\s*(万|億)?円',
            r'(?:融資限度額|限度額)[^0-9]{0,10}(\d+(?:,\d+)?)\s*(万|億)?円',
        ]:
            m = re.search(pat, line)
            if m:
                val = _to_yen(m.group(1), m.group(2) or '')
                if val and 10_000 <= val <= 100_000_000:
                    max_amount = val if (max_amount is None or val > max_amount) else max_amount

    return (min_amount, max_amount)


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


def zenkaku_to_hankaku(text: Optional[str]) -> str:
    """全角→半角の簡易正規化。Noneは空文字。前後の空白を削る。"""
    if text is None:
        return ""
    s = unicodedata.normalize("NFKC", str(text))
    # 全角スペースを含む空白を正規化しstrip
    s = s.replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def z2h(text: Optional[str]) -> str:
    """全角→半角のエイリアス"""
    return zenkaku_to_hankaku(text)


def clean_rate_cell(text: Optional[str]) -> Optional[Decimal]:
    """金利文字列から数値をDecimal(小数2桁, 切り捨て)で返す。未検出はNone。"""
    if not text:
        return None
    s = zenkaku_to_hankaku(text)
    if any(x in s for x in ["無料", "なし"]):
        return None
    m = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*%?", s)
    if not m:
        return None
    val = m.group(1).replace(",", "")
    try:
        d = Decimal(val)
        return d.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    except Exception:
        return None


def extract_amount_from_text(text: Optional[str]) -> Optional[int]:
    """テキストから金額(円)を単一値で抽出（最も代表的な上限/記載値）。"""
    if not text:
        return None
    s = zenkaku_to_hankaku(text)
    # 優先: 『最大/上限/限度額/以内』の直後の金額
    patterns = [
        r"(?:最大|上限|限度額|融資限度額)[^0-9]{0,10}(\d+(?:,\d{3})*)\s*(万|億)?円",
        r"(\d+(?:,\d{3})*)\s*(万|億)?円(?:まで|以内)?",
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            num, unit = m.group(1), m.group(2) or ""
            n = int(num.replace(",", ""))
            if unit == "万":
                n *= 10_000
            elif unit == "億":
                n *= 100_000_000
            return n if n > 0 else None
    return None


def extract_term_from_text(text: Optional[str]) -> Optional[int]:
    """テキストから返済期間(月)を単一値で抽出（最長値）。"""
    if not text:
        return None
    s = zenkaku_to_hankaku(text)
    if "定めなし" in s or "特になし" in s:
        return None
    # 年・月の両方を探索し、最大月数を返す
    months = [int(x) for x in re.findall(r"(\d+)\s*(?:ヶ月|か月|カ月|ヵ月|ケ月)", s)]
    years = [int(x) for x in re.findall(r"(\d+)\s*年", s)]
    all_months = months + [y * 12 for y in years]
    return max(all_months) if all_months else None
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/touou_shinkin/extractors.py
# 値抽出ユーティリティ（正規表現/パターン）
# なぜ: HTML/PDF抽出の共通ロジックを再利用可能にするため
# 関連: html_parser.py, pdf_parser.py, product_scraper.py
