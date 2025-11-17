#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青森みちのく銀行スクレイパー実行スクリプト
"""

import sys
import logging
import os

# プロジェクトルートをパスに追加
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper import AomorimichinokuBankScraper

def main():
    """メイン実行関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("青森みちのく銀行ローン情報スクレイピング実行")
    print("=" * 60)

    try:
        scraper = AomorimichinokuBankScraper()
        result = scraper.scrape_loan_info()

        print("\n=== Summary ===")
        if result:
            products = result.get("products") or []
            status = result.get("scraping_status") or result.get("status")
            print(f"status={status} products={len(products)}")

            if products:
                # 最初の1件だけ簡易表示
                p0 = products[0]
                name = p0.get("product_name")
                rmin = p0.get("min_interest_rate")
                rmax = p0.get("max_interest_rate")
                print(f"product[0]: name={name} rate={rmin}~{rmax}")
        else:
            print("スクレイピング失敗")

    except KeyboardInterrupt:
        print("\n処理が中断されました")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
