# tests/unit/test_touou_shinkin_config.py
import json
import pytest
from loanpedia_scraper.scrapers.touou_shinkin.config import (
    pick_profile_from_pdf,
    get_pdf_urls,
    BASE,
    INSTITUTION_INFO,
)


# ------------------------------
# pick_profile_from_pdf のテスト
# ------------------------------
@pytest.mark.parametrize(
    "pdf_url,expected_type,expected_category,expected_name",
    [
        ("https://example.com/carlife_s.pdf", "car", "auto", "カーライフローン"),
        ("https://example.com/mycarplus_s.pdf", "car", "auto", "マイカープラス"),
        ("https://example.com/kyoiku_s.pdf", "education", "education", "教育ローン"),
        ("https://example.com/newkyoiku_s.pdf", "education", "education", "新教育ローン"),
        ("https://example.com/kyoikucl_s.pdf", "education", "education", "教育カードローン"),
        ("https://example.com/free_s.pdf", "freeloan", "multi-purpose", "フリーローン"),
    ],
)
def test_pick_profile_from_pdf_known_files(pdf_url, expected_type, expected_category, expected_name):
    prof = pick_profile_from_pdf(pdf_url)
    assert prof["loan_type"] == expected_type
    assert prof["category"] == expected_category
    assert prof["product_name"] == expected_name


def test_pick_profile_from_pdf_unknown_returns_default():
    prof = pick_profile_from_pdf("https://example.com/unknown.pdf")
    assert prof["loan_type"] is None
    assert prof["category"] is None
    assert "product_name" not in prof


# ------------------------------
# get_pdf_urls のテスト
# ------------------------------
def test_get_pdf_urls_default(monkeypatch):
    monkeypatch.delenv("TOUOU_SHINKIN_PDF_URLS", raising=False)
    urls = get_pdf_urls()
    assert len(urls) == 6
    assert all(u.endswith(".pdf") or ".pdf?" in u for u in urls)
    assert any("carlife_s.pdf" in url for url in urls)
    assert any("mycarplus_s.pdf" in url for url in urls)
    assert any("kyoiku_s.pdf" in url for url in urls)
    assert any("newkyoiku_s.pdf" in url for url in urls)
    assert any("kyoikucl_s.pdf" in url for url in urls)
    assert any("free_s.pdf" in url for url in urls)


def test_get_pdf_urls_override(monkeypatch):
    override = ["https://example.com/custom1.pdf", "https://example.com/custom2.pdf"]
    monkeypatch.setenv("TOUOU_SHINKIN_PDF_URLS", json.dumps(override))
    urls = get_pdf_urls()
    assert urls == override


# ------------------------------
# 定数のテスト
# ------------------------------
def test_base_url():
    assert BASE == "https://www.shinkin.co.jp/toshin"


def test_institution_info():
    assert INSTITUTION_INFO["financial_institution"] == "東奥信用金庫"
    assert INSTITUTION_INFO["institution_type"] == "信用金庫"
    assert INSTITUTION_INFO["location"] == "青森県"
    assert INSTITUTION_INFO["website"] == BASE