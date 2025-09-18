# loan_scraper/pdf_url_selector.py
# loan_scraper/http_client.py
# -*- coding: utf-8 -*-
import requests
try:
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.config import HEADERS
except ImportError:
    import config
    HEADERS = config.HEADERS


def fetch_html(url: str, timeout: int = 30) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.content
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/touou_shinkin/http_client.py
# HTTP取得層（UA/タイムアウト/最小限のリトライ）
# なぜ: ネットワーク依存の切り分けとテスト容易性のため
# 関連: product_scraper.py, web_parser.py, html_parser.py
