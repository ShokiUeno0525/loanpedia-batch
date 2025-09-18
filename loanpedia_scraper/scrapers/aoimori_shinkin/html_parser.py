"""青い森信用金庫向けのHTML解析ヘルパー

シンプル版：基本的な正規表現パターンマッチングで必要な情報を抽出
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup
from typing import Dict, Any

# 基本パターン
RATE_PATTERNS = [
    r"年\s*(\d+\.\d+)\s*[%％]\s*[〜~～]\s*年\s*(\d+\.\d+)\s*[%％]",
    r"(\d+\.\d+)\s*[%％]\s*[〜~～]\s*(\d+\.\d+)\s*[%％]",
    r"年\s*(\d+\.\d+)\s*[%％]",  # 単一金利
]

AMOUNT_PATTERNS = [
    r"(\d+(?:,\d{3})*)\s*万円[^\d]*?(\d+(?:,\d{3})*)\s*万円",
    r"(\d+(?:,\d{3})*)\s*万円以内",
    r"最高\s*(\d+(?:,\d{3})*)\s*万円",
]

TERM_PATTERNS = [
    r"(\d+)\s*ヶ?月[^\d]*?(\d+)\s*年",
    r"最長\s*(\d+)\s*年",
    r"(\d+)\s*年[^\d]*?(\d+)\s*年",
]

# 商品カテゴリ判定
PRODUCT_CATEGORIES = {
    "マイカー": ["マイカー", "カーライフ", "自動車", "車"],
    "住宅": ["住宅", "住まい", "マンション", "戸建"],
    "教育": ["教育", "学費", "入学"],
    "フリー": ["フリー", "暮らし", "使途自由"],
    "カード": ["カードローン", "極度額"],
}


def extract_text(soup: BeautifulSoup) -> str:
    """HTMLからテキストを抽出"""
    return soup.get_text()


def parse_product_name(soup: BeautifulSoup) -> str:
    """商品名を抽出"""
    for selector in ["h1", "h2", "title"]:
        element = soup.find(selector)
        if element:
            text = element.get_text(strip=True)
            if any(keyword in text for keyword in ["ローン", "カード", "プラン"]):
                return text
    return "青い森信用金庫 ローン"


def detect_product_category(text: str) -> str:
    """商品カテゴリを判定"""
    for category, keywords in PRODUCT_CATEGORIES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "その他"


def parse_interest_rates(text: str) -> Dict[str, Any]:
    """金利情報を抽出"""
    result = {}

    # 金利範囲を検索
    for pattern in RATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:  # 範囲
                min_rate, max_rate = float(match.group(1)), float(match.group(2))
                result["min_interest_rate"] = min(min_rate, max_rate)
                result["max_interest_rate"] = max(min_rate, max_rate)
                break
            else:  # 単一金利
                rate = float(match.group(1))
                result["min_interest_rate"] = rate
                result["max_interest_rate"] = rate
                break

    # 金利種別
    if "変動金利" in text:
        result["interest_rate_type"] = "変動金利"
    else:
        result["interest_rate_type"] = "固定金利"

    return result


def parse_loan_amounts(text: str) -> Dict[str, Any]:
    """融資金額を抽出"""
    result = {}

    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:  # 範囲
                min_amount = int(match.group(1).replace(",", "")) * 10000
                max_amount = int(match.group(2).replace(",", "")) * 10000
                result["min_loan_amount"] = min_amount
                result["max_loan_amount"] = max_amount
                break
            else:  # 単一金額（上限）
                max_amount = int(match.group(1).replace(",", "")) * 10000
                result["min_loan_amount"] = 10000  # デフォルト1万円
                result["max_loan_amount"] = max_amount
                break

    return result


def parse_loan_terms(text: str) -> Dict[str, Any]:
    """融資期間を抽出"""
    result = {}

    for pattern in TERM_PATTERNS:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:  # 範囲
                if "月" in match.group(0) and "年" in match.group(0):
                    min_months = int(match.group(1))
                    max_months = int(match.group(2)) * 12
                else:
                    min_months = int(match.group(1)) * 12
                    max_months = int(match.group(2)) * 12
                result["min_loan_term_months"] = min_months
                result["max_loan_term_months"] = max_months
                break
            else:  # 最長期間
                max_months = int(match.group(1)) * 12
                result["min_loan_term_months"] = 6  # デフォルト6ヶ月
                result["max_loan_term_months"] = max_months
                break

    return result


def apply_category_defaults(data: Dict[str, Any], category: str) -> Dict[str, Any]:
    """商品カテゴリ別のデフォルト値を適用"""
    defaults = {
        "マイカー": {
            "min_loan_amount": 10000,
            "max_loan_amount": 10000000,
            "min_loan_term_months": 3,
            "max_loan_term_months": 180,
        },
        "住宅": {
            "min_loan_amount": 500000,
            "max_loan_amount": 100000000,
            "min_loan_term_months": 12,
            "max_loan_term_months": 420,
        },
        "教育": {
            "min_loan_amount": 10000,
            "max_loan_amount": 10000000,
            "min_loan_term_months": 3,
            "max_loan_term_months": 192,
        },
        "フリー": {
            "min_loan_amount": 10000,
            "max_loan_amount": 3000000,
            "min_loan_term_months": 6,
            "max_loan_term_months": 120,
        },
        "カード": {
            "min_loan_amount": 10000,
            "max_loan_amount": 5000000,
            "min_loan_term_months": 1,
            "max_loan_term_months": 120,
        },
    }

    category_defaults = defaults.get(category, {})

    # デフォルト値で補完（既存値がない場合のみ）
    for key, default_value in category_defaults.items():
        if key not in data or not data[key]:
            data[key] = default_value

    return data


def validate_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """データの整合性チェックと修正"""
    # 金利の逆転修正
    if "min_interest_rate" in data and "max_interest_rate" in data:
        if data["min_interest_rate"] > data["max_interest_rate"]:
            data["min_interest_rate"], data["max_interest_rate"] = (
                data["max_interest_rate"], data["min_interest_rate"]
            )

    # 融資額の逆転修正
    if "min_loan_amount" in data and "max_loan_amount" in data:
        if data["min_loan_amount"] > data["max_loan_amount"]:
            data["min_loan_amount"], data["max_loan_amount"] = (
                data["max_loan_amount"], data["min_loan_amount"]
            )

    # 期間の逆転修正
    if "min_loan_term_months" in data and "max_loan_term_months" in data:
        if data["min_loan_term_months"] > data["max_loan_term_months"]:
            data["min_loan_term_months"], data["max_loan_term_months"] = (
                data["max_loan_term_months"], data["min_loan_term_months"]
            )

    return data


def parse_html_document(soup: BeautifulSoup) -> Dict[str, Any]:
    """メイン解析関数"""
    text = extract_text(soup)

    # 基本情報の抽出
    result = {
        "product_name": parse_product_name(soup),
    }

    # 商品カテゴリを判定
    category = detect_product_category(text)

    # 各情報を抽出
    result.update(parse_interest_rates(text))
    result.update(parse_loan_amounts(text))
    result.update(parse_loan_terms(text))

    # カテゴリ別デフォルト値を適用
    result = apply_category_defaults(result, category)

    # データ検証と修正
    result = validate_data(result)

    return result
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aoimori_shinkin/html_parser.py
# HTML解析と金利/条件/メタの抽出
# なぜ: 画面構造変化に強い抽出ロジックを分離するため
# 関連: product_scraper.py, rate_pages.py, extractors.py
