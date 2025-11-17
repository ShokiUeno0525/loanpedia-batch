"""
青森県信用組合専用 Lambda ハンドラー
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
    青森県信用組合専用 Lambda ハンドラー関数
    
    Args:
        event: Lambda イベントデータ
        context: Lambda コンテキスト
        
    Returns:
        Dict[str, Any]: 実行結果
    """
    logger.info("青森県信用組合のスクレイピングを開始")
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")
    
    try:
        # 青森県信用組合スクレイパーをインポート
        from scrapers.aomoriken_shinyoukumiai import AomorikenShinyoukumiaiScraper
        
        # スクレイパーを初期化
        scraper = AomorikenShinyoukumiaiScraper()
        
        # スクレイピング実行
        result = scraper.scrape_loan_info()
        
        if result:
            response = {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'message': '青森県信用組合のスクレイピング成功',
                    'institution': 'aomoriken_shinyoukumiai',
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
            }
            logger.info("青森県信用組合のスクレイピング成功")
        else:
            response = {
                'statusCode': 500,
                'body': {
                    'success': False,
                    'message': '青森県信用組合のスクレイピング失敗',
                    'institution': 'aomoriken_shinyoukumiai',
                    'timestamp': datetime.now().isoformat()
                }
            }
            logger.error("青森県信用組合のスクレイピング失敗")
        
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
                'institution': 'aomoriken_shinyoukumiai',
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
                'institution': 'aomoriken_shinyoukumiai',
                'timestamp': datetime.now().isoformat()
            }
        }
#!/usr/bin/env python3
# /loanpedia_scraper/src/handlers/aomoriken_shinyoukumiai.py
# 青森県信用組合スクレイピング用のLambdaハンドラー
# なぜ: 機関ごとに責務を分離し変更影響範囲を限定するため
# 関連: ../../scrapers/*, ../services/*, ../../database/loan_database.py
