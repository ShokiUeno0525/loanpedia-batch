# -*- coding: utf-8 -*-
"""
スクレイパー共通ユーティリティ関数

複数の金融機関スクレイパーで共通して使用する関数を集約
"""

from typing import Dict, Any, List, Optional


def merge_fields(
    html_fields: Dict[str, Any],
    pdf_fields: Dict[str, Any],
    priority_keys: List[str],
) -> Dict[str, Any]:
    """
    HTMLとPDFから抽出したフィールドをマージする

    Args:
        html_fields: HTMLから抽出したフィールド
        pdf_fields: PDFから抽出したフィールド
        priority_keys: PDFを優先するキーのリスト

    Returns:
        マージされたフィールド辞書
    """
    merged = dict(html_fields)
    for k in priority_keys or []:
        if pdf_fields.get(k) is not None:
            merged[k] = pdf_fields[k]
    return merged


def apply_sanity(merged: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    抽出結果の妥当性チェックと補完

    Args:
        merged: マージ済みのフィールド辞書
        profile: 商品プロファイル設定

    Returns:
        妥当性チェック・補完後のフィールド辞書
    """
    out = dict(merged)

    # 金利: 0.3%〜20%に収まらない場合は破棄
    rmin = out.get("min_interest_rate")
    rmax = out.get("max_interest_rate")
    if rmin is not None and rmax is not None:
        if rmin > rmax or rmin < 0.003 or rmax > 0.2:
            out["min_interest_rate"], out["max_interest_rate"] = None, None

    # 金額: 上限のみ→最小を10万円で補完
    amin = out.get("min_loan_amount")
    amax = out.get("max_loan_amount")
    if amax and (not amin or amin > amax):
        out["min_loan_amount"] = min(amax, 100_000)

    # 期間: min>max の場合は入替
    tmin = out.get("min_loan_term")
    tmax = out.get("max_loan_term")
    if tmin and tmax and tmin > tmax:
        out["min_loan_term"], out["max_loan_term"] = tmax, tmin

    # 年齢: 既定補完
    ltype = (profile.get("loan_type") or "").strip()
    default_age = {
        "教育ローン": (20, 75),
        "マイカーローン": (18, 75),
        "フリーローン": (20, 80),
        "おまとめローン": (20, 69),
    }.get(ltype, (20, 75))

    agemin = out.get("min_age")
    agemax = out.get("max_age")
    if agemin is None and agemax is None:
        out["min_age"], out["max_age"] = default_age
    else:
        if agemin is None:
            out["min_age"] = default_age[0]
        if agemax is None:
            out["max_age"] = default_age[1]

    return out


def extract_specials(text: str, profile: Dict[str, Any]) -> Optional[str]:
    """
    テキストから特徴キーワードを抽出する

    Args:
        text: 検索対象テキスト
        profile: special_keywordsを含むプロファイル

    Returns:
        マッチしたキーワードを " / " で連結した文字列、またはNone
    """
    kws = profile.get("special_keywords") or []
    found = [kw for kw in kws if kw in text]
    return " / ".join(sorted(set(found))) or None
