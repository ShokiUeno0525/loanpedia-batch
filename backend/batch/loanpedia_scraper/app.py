#!/usr/bin/env python3
# /loanpedia_scraper/app.py
# AWS Lambdaメインハンドラー（全スクレイパーの統合実行）
# なぜ: 金融機関ごとのスクレイピングを一括起動・制御するため
# 関連: loanpedia_scraper/scrapers/main.py, template.yaml, docker-compose.yml, database/loan_database.py
"""
AWS Lambda メインハンドラー
全金融機関のローン情報スクレイピングを統合実行
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
    AWS Lambda メインハンドラー関数
    
    Args:
        event: Lambda イベントデータ
        context: Lambda コンテキスト
        
    Returns:
        Dict[str, Any]: 実行結果
    """
    logger.info("ローン情報スクレイピングバッチを開始")
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")
    
    try:
        # スクレイピングオーケストレーターをインポート
        from scrapers.main import LoanScrapingOrchestrator
        
        # データベース保存を有効化（AWS環境では通常有効）
        save_to_db = os.environ.get('SAVE_TO_DB', 'true').lower() == 'true'
        
        # オーケストレーターを初期化
        orchestrator = LoanScrapingOrchestrator(save_to_db=save_to_db)
        
        # イベントで特定の金融機関が指定されている場合
        institution = event.get('institution')
        if institution:
            logger.info(f"特定金融機関のスクレイピングを実行: {institution}")
            result = orchestrator.run_single_scraper(institution)
            
            if result:
                response = {
                    'statusCode': 200,
                    'body': {
                        'success': True,
                        'message': f'{institution} スクレイピング成功',
                        'institution': institution,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                response = {
                    'statusCode': 500,
                    'body': {
                        'success': False,
                        'message': f'{institution} スクレイピング失敗',
                        'institution': institution,
                        'timestamp': datetime.now().isoformat()
                    }
                }
        else:
            # 全スクレイパー実行
            logger.info("全金融機関のスクレイピングを実行")
            summary = orchestrator.run_all_scrapers()
            
            # 成功率を計算
            success_rate = (summary['success_count'] / summary['total_scrapers']) * 100 if summary['total_scrapers'] > 0 else 0
            
            response = {
                'statusCode': 200,
                'body': {
                    'success': True,
                    'message': 'スクレイピングバッチ完了',
                    'summary': summary,
                    'success_rate': round(success_rate, 2),
                    'timestamp': datetime.now().isoformat()
                }
            }
        
        logger.info(f"実行完了: {response['statusCode']}")
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
                'timestamp': datetime.now().isoformat()
            }
        }
