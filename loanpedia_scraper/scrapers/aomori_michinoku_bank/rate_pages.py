# -*- coding: utf-8 -*-
"""
サポートサイトの金利一覧ページから金利範囲を取得
例: https://www.am-bk.co.jp/kojin/support/rate/mycar.html
"""
from __future__ import annotations
from typing import Optional, Tuple
import re

try:
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.http_client import fetch_html
except ImportError:
    # Lambda環境では相対インポートが失敗するため、直接モジュールインポートを使用
    import http_client
    fetch_html = http_client.fetch_html


BASE = "https://www.am-bk.co.jp"

SLUG_BY_URL_KEYWORD = [
    ("mycarloan", "mycar"),
    ("freeloan/silverloan", "free"),  # シルバーも free に含まれる
    ("freeloan/support", "reform"),   # 近似（住宅関連）
    ("freeloan", "free"),
    ("omatomeloan", "free"),
    ("cardloan", "card"),
    ("kyouikuloan_hanpuku", "tuition"),
    ("certificate", "tuition"),
    ("kyouikuloan/", "tuition"),
    ("akiyarikatsuyouloan", "akiyarikatsuyou"),
    ("jutakuloan", "housing"),
    ("housing", "housing"),
    ("reform", "reform"),
]


def guess_rate_slug_from_url(url: str) -> Optional[str]:
    u = url or ""
    for key, slug in SLUG_BY_URL_KEYWORD:
        if key in u:
            return slug
    return None


def _clean_text(html: str) -> str:
    # 簡易正規化（タグ除去はfetch側/呼び出し側で実施される想定だが、ここではテキスト前提）
    t = html
    t = re.sub(r"\r\n?|\n+", "\n", t)
    t = re.sub(r"[\u2010-\u2015\u2212\uFF0D]", "-", t)  # ダッシュ類
    t = re.sub(r"[~〜～]", "〜", t)
    return t


def extract_interest_from_rate_text(text: str) -> Tuple[Optional[float], Optional[float]]:
    """金利一覧テキストから範囲抽出。割引表現は除外。"""
    t = _clean_text(text or "")
    # 代表パターン1: 年X〜Y％ （前側に%なし）
    m = re.search(r"年\s*(\d+(?:[\.,]\d+)?)\s*[\-~〜]\s*(\d+(?:[\.,]\d+)?)\s*％", t)
    if m:
        a = float(m.group(1).replace(",", ".")) / 100.0
        b = float(m.group(2).replace(",", ".")) / 100.0
        return (min(a, b), max(a, b))
    # 代表パターン2: 年X％〜年Y％
    m = re.search(r"年\s*(\d+(?:[\.,]\d+)?)\s*％\s*[\-~〜]\s*年\s*(\d+(?:[\.,]\d+)?)\s*％", t)
    if m:
        a = float(m.group(1).replace(",", ".")) / 100.0
        b = float(m.group(2).replace(",", ".")) / 100.0
        return (min(a, b), max(a, b))

    # フォールバック: 近傍に割引語句がない%数値を収集
    nums = []
    for mm in re.finditer(r"(\d+(?:[\.,]\d+)?)\s*％", t):
        s, e = mm.span()
        ctx = t[max(0, s - 20) : min(len(t), e + 20)]
        if any(k in ctx for k in ("引下げ", "▲", "最大", "割引")):
            continue
        try:
            nums.append(float(mm.group(1).replace(",", ".")) / 100.0)
        except Exception:
            pass
    nums = [x for x in nums if 0.001 <= x <= 0.2]
    if len(nums) >= 2:
        return (min(nums), max(nums))
    return (None, None)


def fetch_interest_range_from_rate_page(slug: str, variant: str | None = None) -> Tuple[Optional[float], Optional[float]]:
    """金利一覧ページから金利範囲を取得。

    variant:
      - 'web': WEB完結型の近傍から抽出（なければ代表値）
      - 'store': 来店型の近傍から抽出（なければ代表値）
      - None: 代表値
    """
    url = f"{BASE}/kojin/support/rate/{slug}.html"
    html = fetch_html(url)
    if not variant:
        return extract_interest_from_rate_text(html)

    # variant別に近傍抽出
    key = "WEB完結型" if variant == "web" else "来店型"
    # テキストを行に分解し、ラベル区間ごとに抽出
    text = _clean_text(html)
    lines = text.split("\n")
    idxs = [i for i, ln in enumerate(lines) if key in ln]
    # 次のラベルの位置（区切り）を求める
    other_key = "来店型" if key == "WEB完結型" else "WEB完結型"
    other_idxs = [i for i, ln in enumerate(lines) if other_key in ln]

    for i in idxs:
        # このラベルから次のラベル直前までを区間とする（前方のみを見る）
        next_labels = [j for j in other_idxs if j > i]
        j = min(next_labels) if next_labels else len(lines)
        window = "\n".join(lines[i:j])
        r = extract_interest_from_rate_text(window)
        if all(x is not None for x in r):
            return r
    # 見つからなければ代表値
    return extract_interest_from_rate_text(html)
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aomori_michinoku_bank/rate_pages.py
# 金利ページのURL/抽出設定
# なぜ: ページ構成変化への追従と責務分離のため
# 関連: html_parser.py, product_scraper.py, config.py
