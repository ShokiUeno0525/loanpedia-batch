"""
東奥信用金庫専用 Lambda ハンドラー
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

def get_db_config_from_secrets() -> Dict[str, Any]:
    """Secrets Managerからデータベース認証情報を取得"""
    import boto3

    secret_arn = os.getenv('DB_SECRET_ARN')
    if not secret_arn:
        logger.warning("DB_SECRET_ARN not set, using environment variables")
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'loanpedia'),
            'charset': 'utf8mb4'
        }

    try:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretString'])

        return {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': secret.get('username'),
            'password': secret.get('password'),
            'database': os.getenv('DB_NAME', 'loanpedia'),
            'charset': 'utf8mb4'
        }
    except Exception as e:
        logger.error(f"Failed to get secrets: {e}")
        raise

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    東奥信用金庫専用 Lambda ハンドラー関数

    Args:
        event: Lambda イベントデータ
        context: Lambda コンテキスト

    Returns:
        Dict[str, Any]: 実行結果
    """
    logger.info("東奥信用金庫のスクレイピングを開始")
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")

    try:
        # 東奥信用金庫スクレイパーをインポート
        from scrapers.touou_shinkin import TououShinkinScraper

        # データベース保存フラグを環境変数から取得
        save_to_db = os.getenv('SAVE_TO_DB', 'false').lower() == 'true'

        # データベース設定を取得
        db_config = None
        if save_to_db:
            try:
                db_config = get_db_config_from_secrets()
                logger.info(f"Database config loaded: {db_config['host']}:{db_config['port']}/{db_config['database']}")
            except Exception as e:
                logger.error(f"Failed to load database config: {e}")
                save_to_db = False

        # スクレイパーを初期化
        scraper = TououShinkinScraper(save_to_db=save_to_db, db_config=db_config)

        # スクレイピング実行
        result = scraper.scrape_loan_info()
        
        if result:
            response = {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'message': '東奥信用金庫のスクレイピング成功',
                    'institution': 'touou_shinkin',
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
            }
            logger.info("東奥信用金庫のスクレイピング成功")
        else:
            response = {
                'statusCode': 500,
                'body': {
                    'success': False,
                    'message': '東奥信用金庫のスクレイピング失敗',
                    'institution': 'touou_shinkin',
                    'timestamp': datetime.now().isoformat()
                }
            }
            logger.error("東奥信用金庫のスクレイピング失敗")
        
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
                'institution': 'touou_shinkin',
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
                'institution': 'touou_shinkin',
                'timestamp': datetime.now().isoformat()
            }
        }
#!/usr/bin/env python3
# /loanpedia_scraper/src/handlers/touou_shinkin.py
# 東奥信用金庫スクレイピング用のLambdaハンドラー
# なぜ: 機能分離して関数単位での実行/運用を可能にするため
# 関連: ../../scrapers/touou_shinkin/*, ../services/*, ../../database/loan_database.py
