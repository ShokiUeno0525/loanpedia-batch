# -*- coding: utf-8 -*-
"""
青森県信用組合スクレイピング設定
"""

# 基本情報
INSTITUTION_CODE = "2020"  # 信用組合の金融機関コード
INSTITUTION_NAME = "青森県信用組合"
INSTITUTION_TYPE = "信用組合"
WEBSITE_URL = "https://www.shinao.jp/"

# ローン商品URL設定
LOAN_PRODUCTS = [
    {
        "product_id": "2030107",
        "name": "新フリーローン",
        "category": "フリー",
        "url": "https://www.shinkumi-loan.com/loan/detail/2030107.html?cat=05",
        "cat_code": "05"
    },
    {
        "product_id": "2030027",
        "name": "けんしんようミドルカードローン",
        "category": "カード",
        "url": "https://www.shinkumi-loan.com/loan/detail/2030027.html?cat=04",
        "cat_code": "04"
    },
    {
        "product_id": "2030120",
        "name": "多目的ローン",
        "category": "多目的",
        "url": "https://www.shinkumi-loan.com/loan/detail/2030120.html?cat=03",
        "cat_code": "03"
    }
]

# スクレイピング設定
SCRAPING_CONFIG = {
    "timeout": 10,
    "verify_ssl": False,  # SSL証明書の問題があるため
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "retry_count": 3,
    "retry_delay": 1
}

# カテゴリマッピング
CATEGORY_MAPPING = {
    "03": "多目的",
    "04": "カード",
    "05": "フリー"
}