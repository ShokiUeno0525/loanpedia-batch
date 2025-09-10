# tests/test_config_simple.py
import json
import pytest
from loanpedia_scraper.scrapers.aoimori_shinkin.config import (
    pick_profile,
    get_product_urls,
    get_pdf_urls,
    BASE,
)


# ------------------------------
# pick_profile のテスト
# ------------------------------
@pytest.mark.parametrize(
    "url,expected_type,expected_category",
    [
        ("https://example.com/loan/car/", "car", "auto"),
        ("https://example.com/loan/housing/", "home", "housing"),
        ("https://example.com/loan/education/", "education", "education"),
        ("https://example.com/loan/freeloan/", "freeloan", "multi-purpose"),
        ("https://example.com/loan/card/", "card", "card"),
    ],
)
def test_pick_profile_fixed_pages(url, expected_type, expected_category):
    prof = pick_profile(url)
    assert prof["loan_type"] == expected_type
    assert prof["category"] == expected_category


def test_pick_profile_unknown_returns_default():
    prof = pick_profile("https://example.com/loan/unknown/")
    assert prof["loan_type"] is None
    assert prof["category"] is None


# ------------------------------
# get_product_urls のテスト
# ------------------------------
def test_get_product_urls_empty(monkeypatch):
    monkeypatch.delenv("AOIMORI_SHINKIN_PRODUCT_URLS", raising=False)
    assert get_product_urls() == []


def test_get_product_urls_valid(monkeypatch):
    urls = [
        {"url": "https://example.com/loan/car/"},
        {"url": "https://example.com/loan/housing/"},
    ]
    monkeypatch.setenv("AOIMORI_SHINKIN_PRODUCT_URLS", json.dumps(urls))
    result = get_product_urls()
    assert result == urls


# ------------------------------
# get_pdf_urls のテスト
# ------------------------------
def test_get_pdf_urls_default(monkeypatch):
    monkeypatch.delenv("AOIMORI_SHINKIN_PDF_URLS", raising=False)
    urls = get_pdf_urls()
    assert len(urls) == 3
    assert all(u.endswith(".pdf") for u in urls)


def test_get_pdf_urls_override(monkeypatch):
    override = ["https://example.com/a.pdf", "https://example.com/b.pdf"]
    monkeypatch.setenv("AOIMORI_SHINKIN_PDF_URLS", json.dumps(override))
    urls = get_pdf_urls()
    assert urls == override
