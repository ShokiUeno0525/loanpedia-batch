# loan_scraper/pdf_url_selector.py
# loan_scraper/http_client.py
# -*- coding: utf-8 -*-
import requests
from loanpedia_scraper.scrapers.aomori_michinoku_bank.config import HEADERS


def fetch_html(url: str, timeout: int = 30) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.content
