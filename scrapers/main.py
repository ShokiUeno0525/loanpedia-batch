"""
統合スクレイピング実行モジュール

全ての金融機関のスクレイピングを統合実行
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from aomori_michinoku import AomorimichinokuBankScraper
from aoimori_shinkin import AoimoriShinkinScraper
from touou_shinkin import TououShinkinScraper
from aomoriken_shinyoukumiai import AomorikenShinyoukumiaiScraper

logger = logging.getLogger(__name__)


class LoanScrapingOrchestrator:
    """
    全金融機関のローン情報スクレイピングを統括するオーケストレーター
    """
    
    def __init__(self):
        self.scrapers = {
            'aomori_michinoku': AomorimichinokuBankScraper(),
            'aoimori_shinkin': AoimoriShinkinScraper(),
            'touou_shinkin': TououShinkinScraper(),
            'aomoriken_shinyoukumiai': AomorikenShinyoukumiaiScraper()
        }
        self.results = []
        self.errors = []

    def run_all_scrapers(self) -> Dict:
        """
        全てのスクレイパーを実行
        
        Returns:
            Dict: 実行結果サマリー
        """
        logger.info("全金融機関のスクレイピングを開始")
        start_time = datetime.now()
        
        success_count = 0
        error_count = 0
        
        for institution_name, scraper in self.scrapers.items():
            try:
                logger.info(f"{institution_name} のスクレイピングを開始")
                result = scraper.scrape_loan_info()
                
                if result:
                    self.results.append(result)
                    success_count += 1
                    logger.info(f"✅ {institution_name} 成功")
                else:
                    error_count += 1
                    self.errors.append(f"{institution_name}: データ取得失敗")
                    logger.error(f"❌ {institution_name} データ取得失敗")
                    
            except Exception as e:
                error_count += 1
                self.errors.append(f"{institution_name}: {str(e)}")
                logger.error(f"❌ {institution_name} エラー: {e}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'total_scrapers': len(self.scrapers),
            'success_count': success_count,
            'error_count': error_count,
            'results': self.results,
            'errors': self.errors
        }
        
        logger.info(f"スクレイピング完了: 成功{success_count}件、エラー{error_count}件、実行時間{duration:.1f}秒")
        
        return summary

    def run_single_scraper(self, institution_name: str) -> Optional[Dict]:
        """
        指定した金融機関のスクレイパーのみ実行
        
        Args:
            institution_name: 金融機関名
            
        Returns:
            Optional[Dict]: スクレイピング結果
        """
        if institution_name not in self.scrapers:
            logger.error(f"指定された金融機関が見つかりません: {institution_name}")
            logger.info(f"利用可能な金融機関: {list(self.scrapers.keys())}")
            return None
            
        scraper = self.scrapers[institution_name]
        
        try:
            logger.info(f"{institution_name} のスクレイピングを開始")
            result = scraper.scrape_loan_info()
            
            if result:
                logger.info(f"✅ {institution_name} 成功")
                return result
            else:
                logger.error(f"❌ {institution_name} データ取得失敗")
                return None
                
        except Exception as e:
            logger.error(f"❌ {institution_name} エラー: {e}")
            return None

    def get_available_scrapers(self) -> List[str]:
        """
        利用可能なスクレイパー一覧を取得
        
        Returns:
            List[str]: スクレイパー名のリスト
        """
        return list(self.scrapers.keys())


def main():
    """メイン実行関数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    orchestrator = LoanScrapingOrchestrator()
    
    # 全スクレイパー実行
    summary = orchestrator.run_all_scrapers()
    
    print("\n" + "="*50)
    print("スクレイピング結果サマリー")
    print("="*50)
    print(f"実行時間: {summary['duration_seconds']:.1f}秒")
    print(f"成功: {summary['success_count']}件")
    print(f"エラー: {summary['error_count']}件")
    
    if summary['results']:
        print(f"\n取得データ:")
        for i, result in enumerate(summary['results'], 1):
            print(f"{i}. {result['institution_name']}: {result['product_name']}")
            if 'min_interest_rate' in result:
                print(f"   金利: {result['min_interest_rate']}% - {result.get('max_interest_rate', 'N/A')}%")
            if 'max_loan_amount' in result:
                print(f"   融資額: 最大{result['max_loan_amount']:,}円")
    
    if summary['errors']:
        print(f"\nエラー:")
        for error in summary['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    main()