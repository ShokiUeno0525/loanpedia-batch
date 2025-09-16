# tests/unit/test_touou_shinkin_extractors.py
import pytest
from decimal import Decimal
from loanpedia_scraper.scrapers.touou_shinkin.extractors import (
    zenkaku_to_hankaku,
    z2h,
    clean_rate_cell,
    extract_amount_from_text,
    extract_term_from_text,
)


# ------------------------------
# zenkaku_to_hankaku のテスト
# ------------------------------
def test_zenkaku_to_hankaku_basic():
    assert zenkaku_to_hankaku("１２３") == "123"
    assert zenkaku_to_hankaku("ａｂｃ") == "abc"
    assert zenkaku_to_hankaku("　　 テスト 　") == "テスト"


def test_zenkaku_to_hankaku_empty():
    assert zenkaku_to_hankaku("") == ""
    assert zenkaku_to_hankaku(None) == ""


def test_z2h_alias():
    # z2h is an alias for zenkaku_to_hankaku
    assert z2h("１２３") == zenkaku_to_hankaku("１２３")


# ------------------------------
# clean_rate_cell のテスト
# ------------------------------
@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("2.5%", Decimal("2.50")),
        ("２．５％", Decimal("2.50")),
        ("3.125%", Decimal("3.12")),  # 切り捨て
        ("1,500.75%", Decimal("1500.75")),
        ("無料", None),
        ("", None),
        (None, None),
        ("変動金利 2.3%", Decimal("2.30")),
    ],
)
def test_clean_rate_cell(input_text, expected):
    result = clean_rate_cell(input_text)
    assert result == expected


# ------------------------------
# extract_amount_from_text のテスト
# ------------------------------
@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("融資限度額：500万円", 5000000),
        ("限度額 1,000万円", 10000000),
        ("最大 300 万円まで", 3000000),
        ("１００万円", 1000000),
        ("500,000円", 500000),
        ("融資金額は特になし", None),
        ("", None),
    ],
)
def test_extract_amount_from_text(input_text, expected):
    result = extract_amount_from_text(input_text)
    assert result == expected


# ------------------------------
# extract_term_from_text のテスト
# ------------------------------
@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("返済期間：5年", 60),
        ("最長 10 年まで", 120),
        ("１５年以内", 180),
        ("36ヶ月", 36),
        ("24カ月", 24),
        ("２４ヶ月", 24),
        ("期間の定めなし", None),
        ("", None),
    ],
)
def test_extract_term_from_text(input_text, expected):
    result = extract_term_from_text(input_text)
    assert result == expected