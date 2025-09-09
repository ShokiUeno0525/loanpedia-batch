import os
import json
import importlib
import pytest

MODULE_PATH = "loanpedia_scraper.scrapers.aoimori_shinkin.config"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """各テスト前に関連環境変数をクリーンにする"""
    keys = [
        "AOIMORI_SHINKIN_PRODUCT_URLS",
        "AOIMORI_SHINKIN_ENABLE_PDF",
        "AOIMORI_SHINKIN_PDF_URLS",
        "SCRAPING_TEST_MODE",
        "PYTEST_CURRENT_TEST",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    yield
    for key in keys:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def mod(monkeypatch):
    """テストごとに新しいモジュールオブジェクトを用意"""
    module = importlib.import_module(MODULE_PATH)

    module = importlib.reload(module)
    return module


def test_pick_profile_returns_default_when_no_match(monkeypatch, mod):
    # profilesを空に
    mod.profile.clear()
    url = "https://example.com/kojin/mycarloan/detail"
    prof = mod.pick_profile(url)
    assert prof["loan_type"] is None
    assert prof["category"] is None
    assert prof["interest_type_hints"] == []
    assert prof["pdf_priority_fields"] == []
