#!/usr/bin/env python3
"""
統合パイプライン実行スクリプト
推奨アーキテクチャに基づく3段階処理の実行
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from typing import Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoanPipelineRunner:
    """ローン情報収集パイプライン実行クラス"""
    
    def __init__(self):
        self.scrapy_project_path = "loanpedia_scraper"
        self.validate_environment()
    
    def validate_environment(self):
        """実行環境の検証"""
        required_env_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            logger.info("Please set the following environment variables:")
            for var in missing_vars:
                logger.info(f"  export {var}='your_value'")
            sys.exit(1)
        
        # AWS環境変数チェック（AI処理用）
        aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        missing_aws_vars = [var for var in aws_vars if not os.getenv(var)]
        
        if missing_aws_vars:
            logger.warning(f"Missing AWS environment variables: {missing_aws_vars}")
            logger.warning("AI processing batch will not work without AWS credentials")
    
    def run_scrapy_collection(self, spider_name: Optional[str] = None) -> bool:
        """Step 1: Scrapyによる生データ収集"""
        logger.info("=== Step 1: Scrapy Data Collection ===")
        
        try:
            os.chdir(self.scrapy_project_path)
            
            if spider_name:
                # 特定のスパイダーを実行
                cmd = ["scrapy", "crawl", spider_name, "-s", "LOG_LEVEL=INFO"]
                logger.info(f"Running spider: {spider_name}")
            else:
                # 全スパイダーを実行
                cmd = ["scrapy", "list"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                spider_list = result.stdout.strip().split('\n')
                
                logger.info(f"Found spiders: {spider_list}")
                
                for spider in spider_list:
                    if spider.strip():
                        logger.info(f"Running spider: {spider}")
                        spider_cmd = ["scrapy", "crawl", spider.strip(), "-s", "LOG_LEVEL=INFO"]
                        subprocess.run(spider_cmd, check=True)
                
                os.chdir("..")
                return True
            
            result = subprocess.run(cmd, check=True)
            os.chdir("..")
            
            logger.info("✅ Scrapy collection completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Scrapy collection failed: {e}")
            os.chdir("..")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in scrapy collection: {e}")
            os.chdir("..")
            return False
    
    def run_ai_processing(self, batch_size: int = 5) -> bool:
        """Step 2: AI処理バッチ実行"""
        logger.info("=== Step 2: AI Processing ===")
        
        try:
            cmd = ["python3", "ai_processing_batch.py", "--batch-size", str(batch_size)]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            logger.info("AI Processing Output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(line)
            
            if result.stderr:
                logger.warning("AI Processing Warnings:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.warning(line)
            
            logger.info("✅ AI processing completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ AI processing failed: {e}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in AI processing: {e}")
            return False
    
    def run_product_integration(self, batch_size: int = 10) -> bool:
        """Step 3: 商品統合処理実行"""
        logger.info("=== Step 3: Product Integration ===")
        
        try:
            cmd = ["python3", "product_integration_batch.py", "--batch-size", str(batch_size)]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            logger.info("Product Integration Output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(line)
            
            if result.stderr:
                logger.warning("Product Integration Warnings:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.warning(line)
            
            logger.info("✅ Product integration completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Product integration failed: {e}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in product integration: {e}")
            return False
    
    def run_full_pipeline(self, spider_name: Optional[str] = None, 
                         ai_batch_size: int = 5, integration_batch_size: int = 10) -> bool:
        """フルパイプライン実行"""
        logger.info("🚀 Starting Full Loan Data Pipeline")
        logger.info(f"Execution started at: {datetime.now()}")
        
        start_time = datetime.now()
        
        # Step 1: データ収集
        if not self.run_scrapy_collection(spider_name):
            logger.error("Pipeline failed at Step 1: Data Collection")
            return False
        
        # Step 2: AI処理
        if not self.run_ai_processing(ai_batch_size):
            logger.error("Pipeline failed at Step 2: AI Processing")
            return False
        
        # Step 3: 統合処理
        if not self.run_product_integration(integration_batch_size):
            logger.error("Pipeline failed at Step 3: Product Integration")
            return False
        
        # 完了
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 Full Pipeline Completed Successfully!")
        logger.info(f"Total execution time: {duration}")
        logger.info(f"Completed at: {end_time}")
        
        return True

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ローン情報収集パイプライン')
    parser.add_argument('--step', choices=['scrapy', 'ai', 'integration', 'full'], 
                       default='full', help='実行するステップ (default: full)')
    parser.add_argument('--spider', type=str, help='実行する特定のスパイダー名')
    parser.add_argument('--ai-batch-size', type=int, default=5, help='AI処理バッチサイズ (default: 5)')
    parser.add_argument('--integration-batch-size', type=int, default=10, help='統合処理バッチサイズ (default: 10)')
    
    args = parser.parse_args()
    
    runner = LoanPipelineRunner()
    
    if args.step == 'scrapy':
        success = runner.run_scrapy_collection(args.spider)
    elif args.step == 'ai':
        success = runner.run_ai_processing(args.ai_batch_size)
    elif args.step == 'integration':
        success = runner.run_product_integration(args.integration_batch_size)
    elif args.step == 'full':
        success = runner.run_full_pipeline(
            args.spider, 
            args.ai_batch_size, 
            args.integration_batch_size
        )
    else:
        logger.error(f"Unknown step: {args.step}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()