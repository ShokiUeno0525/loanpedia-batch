#!/usr/bin/env python3
"""東奥信用金庫スクレイパーの実行スクリプト

このスクリプトは東奥信用金庫のPDFからローン商品情報を抽出します。
"""
import sys
import os
import json
from datetime import datetime

# プロジェクトのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from loanpedia_scraper.scrapers.touou_shinkin.product_scraper import TououShinkinScraper


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("東奥信用金庫 ローン商品情報抽出テスト")
    print("=" * 60)
    print(f"実行開始時刻: {datetime.now()}")
    print()

    try:
        # スクレイパー初期化
        scraper = TououShinkinScraper()

        # スクレイピング実行
        print("スクレイピング開始...")
        result = scraper.scrape_loan_info()

        # 結果表示
        print(f"\nスクレイピング状況: {result.get('scraping_status', 'unknown')}")
        print(f"金融機関名: {result.get('institution_name', 'N/A')}")
        print(f"抽出商品数: {len(result.get('products', []))}")
        print()

        # 商品詳細表示
        products = result.get('products', [])
        if products:
            print("=== 抽出された商品情報 ===")
            for i, product in enumerate(products, 1):
                print(f"\n{i}. 商品名: {product.get('product_name', 'N/A')}")
                print(f"   種別: {product.get('loan_type', 'N/A')}")
                print(f"   カテゴリ: {product.get('category', 'N/A')}")

                # 金利情報
                if product.get('interest_rate_floating'):
                    print(f"   変動金利: {product['interest_rate_floating']}%")
                if product.get('interest_rate_campaign'):
                    print(f"   キャンペーン金利: {product['interest_rate_campaign']}%")
                if product.get('interest_rate_with_guarantee'):
                    print(f"   保証料込み金利: {product['interest_rate_with_guarantee']}%")

                # その他情報
                if product.get('loan_limit_text'):
                    print(f"   融資限度額: {product['loan_limit_text']}")
                if product.get('loan_term_text'):
                    print(f"   融資期間: {product['loan_term_text']}")

                print(f"   ソースURL: {product.get('source_url', 'N/A')}")
                if product.get('pdf_page'):
                    print(f"   PDFページ: {product['pdf_page']}")
                if product.get('as_of_date'):
                    print(f"   現在日付: {product['as_of_date']}")
        else:
            print("商品情報が抽出されませんでした。")

        # JSON出力（オプション）
        if '--json' in sys.argv:
            output_file = f"touou_shinkin_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n結果をJSONファイルに保存しました: {output_file}")

        print(f"\n実行完了時刻: {datetime.now()}")
        print("=" * 60)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()