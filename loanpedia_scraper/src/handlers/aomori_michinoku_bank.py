"""
青森みちのく銀行統合 Lambda ハンドラー
全商品（マイカーローン、教育ローン）を統合処理
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.append('/var/task')
sys.path.append('/var/task/scrapers')
sys.path.append('/var/task/database')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    青森みちのく銀行統合 Lambda ハンドラー関数
    
    Args:
        event: Lambda イベントデータ
               - product: 'all', 'mycar', 'education', 'education_deed', 'education_card' (デフォルト: 'all')
        context: Lambda コンテキスト
        
    Returns:
        Dict[str, Any]: 実行結果
    """
    logger.info("青森みちのく銀行の統合スクレイピングを開始")
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")
    
    # 対象商品を判定
    target_product = event.get('product', 'all')
    logger.info(f"対象商品: {target_product}")
    
    try:
        # スクレイパーをインポート
        from scrapers.aomori_michinoku_bank.mycar import AomorimichinokuBankScraper
        from scrapers.aomori_michinoku_bank.education_repetition import AomorimichinokuEducationRepetitionScraper
        from scrapers.aomori_michinoku_bank.education_deed import AomorimichinokuEducationDeedScraper
        from scrapers.aomori_michinoku_bank.education_card import AomorimichinokuEducationCardScraper
        
        # 利用可能なスクレイパーマッピング
        scrapers = {
            'mycar': {
                'class': AomorimichinokuBankScraper,
                'name': 'マイカーローン'
            },
            'education': {
                'class': AomorimichinokuEducationRepetitionScraper,
                'name': '教育ローン（反復利用型）'
            },
            'education_deed': {
                'class': AomorimichinokuEducationDeedScraper,
                'name': '教育ローン（証書貸付型）'
            },
            'education_card': {
                'class': AomorimichinokuEducationCardScraper,
                'name': '教育カードローン'
            }
        }
        
        results = []
        success_count = 0
        error_count = 0
        
        # 実行対象を決定
        if target_product == 'all':
            target_scrapers = scrapers
        elif target_product in scrapers:
            target_scrapers = {target_product: scrapers[target_product]}
        else:
            return {
                'statusCode': 400,
                'body': {
                    'success': False,
                    'error': 'InvalidProduct',
                    'message': f'指定された商品が無効です: {target_product}',
                    'available_products': list(scrapers.keys()),
                    'institution': 'aomori_michinoku',
                    'timestamp': datetime.now().isoformat()
                }
            }
        
        # 各スクレイパーを実行
        for product_key, scraper_info in target_scrapers.items():
            try:
                logger.info(f"{scraper_info['name']}のスクレイピングを開始")
                
                scraper = scraper_info['class']()
                result = scraper.scrape_loan_info()
                
                if result and result.get("scraping_status") == "success":
                    results.append({
                        'product': product_key,
                        'product_name': scraper_info['name'],
                        'success': True,
                        'result': result
                    })
                    success_count += 1
                    logger.info(f"✅ {scraper_info['name']}のスクレイピング成功")
                else:
                    error_msg = result.get('error', '不明なエラー') if result else 'スクレイパーからの結果なし'
                    results.append({
                        'product': product_key,
                        'product_name': scraper_info['name'],
                        'success': False,
                        'error': error_msg
                    })
                    error_count += 1
                    logger.error(f"❌ {scraper_info['name']}のスクレイピング失敗: {error_msg}")
                    
            except Exception as product_error:
                error_msg = f"{scraper_info['name']}で予期しないエラー: {str(product_error)}"
                results.append({
                    'product': product_key,
                    'product_name': scraper_info['name'],
                    'success': False,
                    'error': error_msg
                })
                error_count += 1
                logger.error(error_msg, exc_info=True)
        
        # 統合レスポンスを作成
        overall_success = success_count > 0 and error_count == 0
        status_code = 200 if overall_success else 207 if success_count > 0 else 500
        
        response = {
            'statusCode': status_code,
            'body': {
                'success': overall_success,
                'message': f'青森みちのく銀行統合スクレイピング完了: 成功{success_count}件、失敗{error_count}件',
                'institution': 'aomori_michinoku',
                'target_product': target_product,
                'summary': {
                    'total_products': len(target_scrapers),
                    'success_count': success_count,
                    'error_count': error_count
                },
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        logger.info(f"統合スクレイピング完了: 成功{success_count}件、失敗{error_count}件")
        return response
        
    except ImportError as e:
        error_msg = f"モジュールインポートエラー: {str(e)}"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'body': {
                'success': False,
                'error': 'ImportError',
                'message': error_msg,
                'institution': 'aomori_michinoku',
                'timestamp': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        error_msg = f"予期しないエラー: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': {
                'success': False,
                'error': 'UnexpectedError',
                'message': error_msg,
                'institution': 'aomori_michinoku',
                'timestamp': datetime.now().isoformat()
            }
        }

def get_available_products() -> List[str]:
    """利用可能な商品一覧を取得"""
    return ['mycar', 'education', 'education_deed', 'education_card']

def get_product_info() -> Dict[str, str]:
    """商品情報を取得"""
    return {
        'mycar': 'マイカーローン',
        'education': '教育ローン（反復利用型）',
        'education_deed': '教育ローン（証書貸付型）',
        'education_card': '教育カードローン'
    }


def main():
    """ローカルテスト用のメイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='青森みちのく銀行スクレイパー')
    parser.add_argument('--product', default='all', 
                       choices=['all', 'mycar', 'education', 'education_deed', 'education_card'],
                       help='対象商品 (デフォルト: all)')
    
    args = parser.parse_args()
    
    # ログ設定
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # テスト用イベント
    test_event = {
        'product': args.product
    }
    
    # ハンドラー実行
    result = lambda_handler(test_event, None)
    
    # 結果表示
    print("=" * 50)
    print("スクレイピング結果")
    print("=" * 50)
    print(f"ステータス: {result['statusCode']}")
    print(f"成功: {result['body']['success']}")
    print(f"メッセージ: {result['body']['message']}")
    print(f"実行サマリー: {result['body']['summary']}")
    
    for item in result['body']['results']:
        print(f"\n【{item['product_name']}】")
        if item['success']:
            data = item['result']
            print(f"  ✅ 成功")
            print(f"  商品名: {data.get('product_name')}")
            print(f"  金利: {data.get('min_interest_rate')}% - {data.get('max_interest_rate')}%")
            print(f"  融資額: {data.get('min_loan_amount'):,}円 - {data.get('max_loan_amount'):,}円")
            print(f"  期間: {data.get('min_loan_term_months')}ヶ月 - {data.get('max_loan_term_months')}ヶ月")
            print(f"  年齢: {data.get('min_age')}歳 - {data.get('max_age')}歳")
        else:
            print(f"  ❌ 失敗: {item['error']}")


if __name__ == "__main__":
    main()