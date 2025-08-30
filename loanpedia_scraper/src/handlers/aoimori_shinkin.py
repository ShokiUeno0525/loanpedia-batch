"""
青い森信用金庫専用 Lambda ハンドラー
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートをパスに追加
sys.path.append('/var/task')
sys.path.append('/var/task/scrapers')
sys.path.append('/var/task/database')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    青い森信用金庫専用 Lambda ハンドラー関数
    
    Args:
        event: Lambda イベントデータ
        context: Lambda コンテキスト
        
    Returns:
        Dict[str, Any]: 実行結果
    """
    logger.info("青い森信用金庫のスクレイピングを開始")
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")
    
    try:
        # 青い森信用金庫スクレイパーをインポート
        from scrapers.aoimori_shinkin import AoimoriShinkinScraper

        # データベース保存を有効化（設定の詳細はスクレイパー側に委譲）
        save_to_db = os.environ.get('SAVE_TO_DB', 'true').lower() == 'true'

        # スクレイパーを初期化（db_configは内部で解決）
        scraper = AoimoriShinkinScraper(save_to_db=save_to_db)
        
        # スクレイピング実行
        result = scraper.scrape_loan_info()
        
        if result:
            response = {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'message': '青い森信用金庫のスクレイピング成功',
                    'institution': 'aoimori_shinkin',
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
            }
            logger.info("青い森信用金庫のスクレイピング成功")
        else:
            response = {
                'statusCode': 500,
                'body': {
                    'success': False,
                    'message': '青い森信用金庫のスクレイピング失敗',
                    'institution': 'aoimori_shinkin',
                    'timestamp': datetime.now().isoformat()
                }
            }
            logger.error("青い森信用金庫のスクレイピング失敗")
        
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
                'institution': 'aoimori_shinkin',
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
                'institution': 'aoimori_shinkin',
                'timestamp': datetime.now().isoformat()
            }
        }
