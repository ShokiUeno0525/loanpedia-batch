# -*- coding: utf-8 -*-
"""
青森県信用組合スクレイパー用Lambda/イベントハンドラー
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .product_scraper import AomoriShinkumiScraper

logger = logging.getLogger(__name__)


class AomoriShinkumiHandler:
    """青森県信用組合スクレイピング用ハンドラー"""

    def __init__(self):
        self.scraper = AomoriShinkumiScraper()

    def lambda_handler(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        AWS Lambda ハンドラー関数

        Args:
            event: Lambda イベントデータ
            context: Lambda コンテキスト

        Returns:
            Dict[str, Any]: 実行結果
        """
        logger.info("青森県信用組合スクレイピングバッチを開始")
        logger.info(f"Event: {json.dumps(event, ensure_ascii=False, default=str)}")

        try:
            # スクレイピング実行
            result = self.scraper.scrape_loan_info()

            if result and result.get("scraping_status") == "success":
                response = {
                    'statusCode': 200,
                    'body': {
                        'success': True,
                        'message': '青森県信用組合スクレイピング成功',
                        'institution_name': result.get('institution_name'),
                        'total_products': result.get('total_products', 0),
                        'success_rate': result.get('success_rate', 0),
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                logger.info(f"✅ スクレイピング成功: {result.get('total_products', 0)}商品取得")
            else:
                response = {
                    'statusCode': 500,
                    'body': {
                        'success': False,
                        'message': '青森県信用組合スクレイピング失敗',
                        'error': result.get('error') if result else 'No result returned',
                        'timestamp': datetime.now().isoformat()
                    }
                }
                logger.error("❌ スクレイピング失敗")

            return response

        except Exception as e:
            error_msg = f"予期しないエラー: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'statusCode': 500,
                'body': {
                    'success': False,
                    'error': 'UnexpectedError',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
            }

    def batch_handler(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        バッチ処理用ハンドラー

        Args:
            options: 実行オプション

        Returns:
            Dict[str, Any]: 実行結果
        """
        logger.info("青森県信用組合バッチ処理を開始")

        try:
            result = self.scraper.scrape_loan_info()

            if result and result.get("scraping_status") == "success":
                logger.info(f"✅ バッチ処理成功: {result.get('total_products', 0)}商品取得")
                return {
                    'success': True,
                    'institution': '青森県信用組合',
                    'products_count': result.get('total_products', 0),
                    'success_rate': result.get('success_rate', 0),
                    'details': result
                }
            else:
                logger.error("❌ バッチ処理失敗")
                return {
                    'success': False,
                    'institution': '青森県信用組合',
                    'error': result.get('error') if result else 'No result returned'
                }

        except Exception as e:
            logger.error(f"バッチ処理エラー: {e}", exc_info=True)
            return {
                'success': False,
                'institution': '青森県信用組合',
                'error': str(e)
            }

    def cli_handler(self, args: Optional[list] = None) -> None:
        """
        CLI実行用ハンドラー

        Args:
            args: コマンドライン引数
        """
        print("=== 青森県信用組合スクレイピング実行 ===")

        try:
            result = self.scraper.scrape_loan_info()

            if result and result.get("scraping_status") == "success":
                print(f"✅ 成功: {result.get('institution_name')}")
                print(f"取得商品数: {result.get('total_products', 0)}")
                print(f"成功率: {result.get('success_rate', 0):.1f}%")

                if result.get('failed_products'):
                    print(f"失敗商品: {result['failed_products']}")

                print("\n=== 商品一覧 ===")
                for i, product in enumerate(result.get('products', []), 1):
                    print(f"{i}. {product.get('name', 'N/A')} ({product.get('category', 'N/A')})")
                    print(f"   金利: {product.get('min_interest_rate', 'N/A')}% - {product.get('max_interest_rate', 'N/A')}%")
                    min_amount = product.get('min_loan_amount', 0)
                    max_amount = product.get('max_loan_amount', 0)
                    print(f"   融資額: {min_amount:,}円 - {max_amount:,}円")
                    if product.get('special_features'):
                        print(f"   特徴: {product['special_features']}")
                    print()

            else:
                print("❌ スクレイピング失敗")
                if result and result.get('error'):
                    print(f"エラー: {result['error']}")

        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            import traceback
            traceback.print_exc()


# Lambda関数エントリーポイント
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda エントリーポイント"""
    handler = AomoriShinkumiHandler()
    return handler.lambda_handler(event, context)


# CLI実行時のエントリーポイント
if __name__ == "__main__":
    import sys
    handler = AomoriShinkumiHandler()
    handler.cli_handler(sys.argv[1:])