import pytest
from bs4 import BeautifulSoup

from loanpedia_scraper.scrapers.aoimori_shinkin.html_parser import (
    extract_text,
    parse_product_name,
    detect_product_category,
    parse_interest_rates,
    parse_loan_amounts,
    parse_loan_terms,
    apply_category_defaults,
    validate_data,
    parse_html_document,
)


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_extract_text_basic():
    html = """
    <div>
      <h1>タイトル</h1>
      <p>年2.2% ～ 年3.25%</p>
    </div>
    """
    soup = make_soup(html)
    text = extract_text(soup)
    assert "タイトル" in text
    assert "年2.2%" in text
    assert "3.25%" in text


@pytest.mark.parametrize(
    "html, expected",
    [
        ("<h1>住宅ローン 住まいる</h1>", "住宅ローン 住まいる"),
        ("<h2>カーライフプラン プライム</h2>", "カーライフプラン プライム"),
        ("<title>フリーローンのご案内</title>", "フリーローンのご案内"),
    ],
)
def test_parse_product_name(html, expected):
    soup = make_soup(html)
    assert parse_product_name(soup) == expected


def test_parse_product_name_fallback():
    soup = make_soup("<div>商品名が見つかりません</div>")
    assert parse_product_name(soup) == "青い森信用金庫 ローン"


@pytest.mark.parametrize(
    "text, expected",
    [
        ("マイカー", "マイカー"),
        ("住宅", "住宅"),
        ("教育", "教育"),
        ("フリーローン", "フリー"),
        ("カードローン", "カード"),
        ("その他", "その他"),
    ],
)
def test_detect_product_category(text, expected):
    assert detect_product_category(text) == expected


def test_parse_interest_rates_range_with_year_prefix():
    text = "金利は 年2.20% ～ 年3.25% です。"
    result = parse_interest_rates(text)
    assert result["min_interest_rate"] == 2.20
    assert result["max_interest_rate"] == 3.25


def test_parse_interest_rates_range_without_year_prefix():
    text = "優遇後金利 2.30% ～ 3.10% を適用。"
    result = parse_interest_rates(text)
    assert result["min_interest_rate"] == 2.30
    assert result["max_interest_rate"] == 3.10


def test_parse_interest_rates_single_and_type_fixed_default():
    text = "金利は 年2.50% です。（固定／変動の表記なし）"
    result = parse_interest_rates(text)
    assert result["min_interest_rate"] == 2.50
    assert result["max_interest_rate"] == 2.50
    assert result["interest_rate_type"] == "固定金利"


def test_parse_interest_rates_type_variable():
    text = "当金利は変動金利で 年2.675% です。"
    result = parse_interest_rates(text)
    assert result["min_interest_rate"] == 2.675
    assert result["max_interest_rate"] == 2.675
    assert result["interest_rate_type"] == "変動金利"


# --------------------
# parse_loan_amounts
# --------------------
def test_parse_loan_amounts_range_million_yen():
    text = "ご融資金額は 10万円～1,000万円 の範囲です。"
    result = parse_loan_amounts(text)
    assert result["min_loan_amount"] == 10 * 10000
    assert result["max_loan_amount"] == 1000 * 10000


def test_parse_loan_amounts_upper_bound_only():
    text = "ご融資金額は 300万円以内。"
    result = parse_loan_amounts(text)
    assert result["min_loan_amount"] == 10000
    assert result["max_loan_amount"] == 300 * 10000


def test_parse_loan_amounts_upper_bound_with_saikou():
    text = "最高 800万円 まで。"
    result = parse_loan_amounts(text)
    assert result["min_loan_amount"] == 10000
    assert result["max_loan_amount"] == 800 * 10000


# --------------------
# parse_loan_terms
# --------------------
def test_parse_loan_terms_min_month_to_max_year():
    text = "ご融資期間は 6ヶ月～10年 まで。"
    result = parse_loan_terms(text)
    assert result["min_loan_term_months"] == 6
    assert result["max_loan_term_months"] == 10 * 12


def test_parse_loan_terms_max_only():
    text = "ご融資期間は 最長 15年。"
    result = parse_loan_terms(text)
    assert result["min_loan_term_months"] == 6
    assert result["max_loan_term_months"] == 15 * 12


def test_parse_loan_terms_range_year_year():
    text = "ご融資期間は 3年～7年。"
    result = parse_loan_terms(text)
    assert result["min_loan_term_months"] == 3 * 12
    assert result["max_loan_term_months"] == 7 * 12


# --------------------
# apply_category_defaults
# --------------------
@pytest.mark.parametrize(
    "category, expected_min_amount, expected_max_term",
    [
        ("マイカー", 10000, 180),
        ("住宅", 500000, 420),
        ("教育", 10000, 192),
        ("フリー", 10000, 120),
        ("カード", 10000, 120),
    ],
)
def test_apply_category_defaults_fill_missing(
    category, expected_min_amount, expected_max_term
):
    data = {}
    updated = apply_category_defaults(data, category)
    assert updated["min_loan_amount"] == expected_min_amount
    assert updated["max_loan_term_months"] == expected_max_term


def test_apply_category_defaults_do_not_overwrite_existing():
    data = {"min_loan_amount": 22222, "max_loan_term_months": 99}
    updated = apply_category_defaults(data, "マイカー")
    assert updated["min_loan_amount"] == 22222
    assert updated["max_loan_term_months"] == 99


# --------------------
# validate_data
# --------------------
def test_validate_data_swaps_inverted_ranges():
    data = {
        "min_interest_rate": 3.25,
        "max_interest_rate": 2.20,
        "min_loan_amount": 2000000,
        "max_loan_amount": 1000000,
        "min_loan_term_months": 200,
        "max_loan_term_months": 12,
    }
    validated = validate_data(data)
    assert validated["min_interest_rate"] == 2.20
    assert validated["max_interest_rate"] == 3.25
    assert validated["min_loan_amount"] == 1000000
    assert validated["max_loan_amount"] == 2000000
    assert validated["min_loan_term_months"] == 12
    assert validated["max_loan_term_months"] == 200


# --------------------
# parse_html_document（総合）
# --------------------
def test_parse_html_document_end_to_end_car():
    html = """
    <html>
      <head><title>カーライフプラン プライム</title></head>
      <body>
        <h1>カーライフプラン プライム</h1>
        <section>
          <p>金利は 年2.20%～年3.25% です。</p>
          <p>ご融資金額：10万円～1,000万円</p>
          <p>ご融資期間：6ヶ月～15年</p>
        </section>
      </body>
    </html>
    """
    soup = make_soup(html)
    result = parse_html_document(soup)

    assert result["product_name"].startswith("カーライフプラン")
    assert result["min_interest_rate"] == 2.20
    assert result["max_interest_rate"] == 3.25
    assert result["min_loan_amount"] == 10 * 10000
    assert result["max_loan_amount"] == 1000 * 10000
    assert result["min_loan_term_months"] == 6
    assert result["max_loan_term_months"] == 15 * 12
    assert result["interest_rate_type"] in ("固定金利", "変動金利")


def test_parse_html_document_defaults_applied_when_missing_fields():
    html = """
    <html>
      <head><title>住宅ローン 住まいる</title></head>
      <body>
        <h2>住宅ローン 住まいる</h2>
        <p>新規ご購入の方へ</p>
      </body>
    </html>
    """
    soup = make_soup(html)
    result = parse_html_document(soup)

    assert "住宅ローン" in result["product_name"]
    assert result["min_loan_amount"] == 500000
    assert result["max_loan_amount"] == 100000000
    assert result["min_loan_term_months"] == 12
    assert result["max_loan_term_months"] == 420
