#!/usr/bin/env python3
"""
ローカルデータベース接続テスト
"""

import sys
import os
sys.path.insert(0, 'loanpedia_scraper')
sys.path.insert(0, 'loanpedia_scraper/database')

from database.loan_database import LoanDatabase

# データベース設定
db_config = {
    'host': 'localhost',
    'user': 'app_user', 
    'password': 'app_password',
    'database': 'app_db',
    'port': 3307,
    'charset': 'utf8mb4'
}

print("🔍 データベース接続テスト開始...")
print(f"接続先: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# データベース接続テスト
db = LoanDatabase(db_config)
if db.connect():
    print("✅ データベース接続成功")
    
    # サンプルデータで保存テスト
    test_data = {
        'institution_code': 'test_bank',
        'institution_name': 'テスト銀行',
        'source_url': 'https://test.example.com/loan',
        'html_content': '<html><body>テストローンページ</body></html>',
        'extracted_text': 'テストローン情報 金利2.5%',
        'content_hash': 'test_hash_123',
        'scraping_status': 'success',
        'scraped_at': '2025-08-30T10:00:00',
        'product_name': 'テストローン',
        'loan_type': 'フリーローン',
        'category': '多目的ローン',
        'min_interest_rate': 2.5,
        'max_interest_rate': 14.5,
        'interest_type': '変動金利',
        'min_loan_amount': 100000,
        'max_loan_amount': 5000000,
        'min_loan_term': 12,
        'max_loan_term': 84,
        'repayment_method': '元利均等返済',
        'min_age': 20,
        'max_age': 75,
        'special_features': 'WEB申込対応',
    }
    
    print("💾 サンプルデータ保存テスト...")
    if db.save_loan_data(test_data):
        print("✅ データ保存成功")
    else:
        print("❌ データ保存失敗")
    
    db.disconnect()
else:
    print("❌ データベース接続失敗")