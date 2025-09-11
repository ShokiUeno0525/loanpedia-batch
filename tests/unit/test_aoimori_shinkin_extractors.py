import pytest
from decimal import Decimal
from loanpedia_scraper.scrapers.aoimori_shinkin.extractors import (
    zenkaku_to_hankaku,
    clean_rate_cell,
)


# ------------------------------
# zenkaku_to_hankaku のテスト
# ------------------------------
@pytest.mark.parametrize(
    "input, expected",
    [
        (None, ""),
        ("", ""),
        ("ＡＢＣ　１２３", "ABC 123"),  # 全角数字と全角スペース
        (" 改行\nタブ\t混在 ", "改行 タブ 混在"),  # 空白・改行・タブをまとめる
    ],
)
def test_zenkaku_to_hankaku(input, expected):
    assert zenkaku_to_hankaku(input) == expected


# ------------------------------
# clean_rate_cell のテスト
# ------------------------------
@pytest.mark.parametrize(
    "input, expected",
    [
        ("２．５％", Decimal("2.50")),  # 全角混じり → 半角化
        ("年2.1099％", Decimal("2.10")),  # 小数第2位まで切り捨て
        ("1,200%", Decimal("1200.00")),  # カンマ桁区切り
        ("1.200%", Decimal("1.20")),  # 小数点として解釈
        ("金利なし", None),  # 数値なし
        (None, None),  # None入力
    ],
)
def test_clean_rate_cell(input, expected):
    out = clean_rate_cell(input)
    if expected is None:
        assert out is None
    else:
        assert isinstance(out, Decimal)
        assert out == expected
