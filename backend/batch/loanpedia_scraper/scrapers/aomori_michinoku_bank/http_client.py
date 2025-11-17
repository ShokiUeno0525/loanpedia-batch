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
# /loanpedia_scraper/scrapers/aomori_michinoku_bank/http_client.py
# HTTP取得層（タイムアウト/UA/最小リトライ）
# なぜ: 取得責務を分離しテスト容易性を高めるため
# 関連: product_scraper.py, html_parser.py, rate_pages.py
