#!/usr/bin/env python3
"""
統合処理バッチ: AI処理済みデータから loan_products テーブルを構築
"""

import os
import json
import pymysql
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessedLoanData:
    """AI処理済みローンデータ"""
    id: int
    raw_data_id: int
    institution_id: int
    institution_name: str
    ai_summary: dict
    processing_status: str
    validation_status: str
    processed_at: datetime

class ProductIntegrationBatch:
    """統合処理バッチメイン処理クラス"""
    
    def __init__(self):
        self.db_config = self._load_db_config()
        self.connection = None
        self.cursor = None
    
    def _load_db_config(self) -> Dict:
        """データベース設定を読み込み（共通ユーティリティ使用）"""
        try:
            from database.loan_database import get_database_config
            return get_database_config()
        except Exception:
            # フォールバック（最小限）
            return {
                'host': os.getenv('DB_HOST', 'localhost'),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'app_db'),
                'port': int(os.getenv('DB_PORT', '3306')),
                'charset': 'utf8mb4'
            }
    
    def connect_database(self):
        """データベース接続"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            self.connection.cursorclass = pymysql.cursors.DictCursor
            self.cursor = self.connection.cursor()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_database(self):
        """データベース接続終了"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def get_unintegrated_processed_data(self, limit: int = 10) -> List[ProcessedLoanData]:
        """未統合のAI処理済みデータを取得"""
        sql = """
            SELECT 
                p.id, p.raw_data_id, p.institution_id, p.ai_summary,
                p.processing_status, p.validation_status, p.processed_at,
                f.institution_name
            FROM processed_loan_data p
            JOIN financial_institutions f ON p.institution_id = f.id
            LEFT JOIN loan_products lp ON p.id = lp.processed_data_id
            WHERE p.processing_status = 'completed' 
              AND lp.id IS NULL
            ORDER BY p.processed_at DESC
            LIMIT %s
        """
        
        self.cursor.execute(sql, (limit,))
        rows = self.cursor.fetchall()
        
        processed_data_list = []
        for row in rows:
            ai_summary = {}
            if row['ai_summary']:
                try:
                    ai_summary = json.loads(row['ai_summary'])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in ai_summary for ID {row['id']}")
            
            processed_data_list.append(ProcessedLoanData(
                id=row['id'],
                raw_data_id=row['raw_data_id'],
                institution_id=row['institution_id'],
                institution_name=row['institution_name'],
                ai_summary=ai_summary,
                processing_status=row['processing_status'],
                validation_status=row['validation_status'],
                processed_at=row['processed_at']
            ))
        
        return processed_data_list
    
    def extract_product_data(self, processed_data: ProcessedLoanData) -> Dict:
        """AI要約データから商品マスター用データを抽出"""
        ai_summary = processed_data.ai_summary
        
        try:
            # 新しいAI要約形式からデータを抽出
            product_analysis = ai_summary.get('product_analysis', {})
            customer_guide = ai_summary.get('customer_guide', {})
            market_positioning = ai_summary.get('market_positioning', {})
            risk_assessment = ai_summary.get('risk_assessment', {})
            financial_summary = ai_summary.get('financial_summary', {})
            actionable_insights = ai_summary.get('actionable_insights', {})
            
            # 元の構造化データから基本情報を取得（Scrapyで抽出済み）
            raw_data_id = processed_data.raw_data_id
            raw_structured_data = self._get_raw_structured_data(raw_data_id)
            
            # 基本商品情報（Scrapyデータを優先）
            product_name = raw_structured_data.get('product_name', '')
            loan_category = raw_structured_data.get('loan_category', '')
            
            # 金利情報（Scrapyデータを優先）
            min_rate = raw_structured_data.get('min_interest_rate')
            max_rate = raw_structured_data.get('max_interest_rate')
            
            # 融資金額（Scrapyデータを優先）
            min_amount = raw_structured_data.get('min_loan_amount')
            max_amount = raw_structured_data.get('max_loan_amount')
            
            # 融資期間（Scrapyデータを優先、月から年に変換）
            min_term_months = raw_structured_data.get('min_loan_period_months')
            max_term_months = raw_structured_data.get('max_loan_period_months')
            
            min_term_years = None
            max_term_years = None
            if min_term_months:
                min_term_years = max(1, int(min_term_months / 12))
            if max_term_months:
                max_term_years = max(1, int(max_term_months / 12))
            
            # AI要約から付加価値情報を抽出
            enhanced_features = {
                'competitive_advantages': product_analysis.get('competitive_advantages', []),
                'key_benefits': customer_guide.get('key_benefits', []),
                'unique_selling_points': market_positioning.get('unique_selling_points', []),
                'recommended_use_cases': customer_guide.get('recommended_use_cases', []),
                'market_segment': market_positioning.get('target_market_segment', ''),
                'application_difficulty': customer_guide.get('application_difficulty', ''),
                'flexibility_score': risk_assessment.get('flexibility_score', ''),
                'rate_competitiveness': market_positioning.get('interest_rate_competitiveness', '')
            }
            
            # 申込要件（Scrapyデータ + AI分析）
            application_requirements = {
                'basic_conditions': raw_structured_data.get('application_conditions', ''),
                'risk_factors': risk_assessment.get('borrower_risks', []),
                'pre_check_list': actionable_insights.get('pre_application_checklist', []),
                'required_documents': raw_structured_data.get('required_documents', ''),
                'guarantor_info': raw_structured_data.get('guarantor_info', ''),
                'collateral_info': raw_structured_data.get('collateral_info', '')
            }
            
            # 返済方法
            repayment_methods = [raw_structured_data.get('repayment_method', '')]
            
            return {
                'product_name': product_name,
                'product_code': None,
                'loan_type': loan_category,
                'loan_category': self._standardize_loan_category(loan_category),
                'summary': customer_guide.get('simple_explanation', product_analysis.get('executive_summary', '')),
                'interest_rate_min': min_rate,
                'interest_rate_max': max_rate,
                'interest_rate_type': '変動金利',  # Scrapyデータから取得可能であれば追加
                'loan_amount_min': min_amount,
                'loan_amount_max': max_amount,
                'loan_amount_unit': '円',
                'loan_term_min': min_term_years,
                'loan_term_max': max_term_years,
                'loan_term_unit': '年',
                'repayment_methods': json.dumps(repayment_methods, ensure_ascii=False),
                'application_requirements': json.dumps(application_requirements, ensure_ascii=False),
                'features': json.dumps(enhanced_features, ensure_ascii=False),
                'is_active': True,
                'data_updated_at': datetime.now(),
                # AI要約の付加価値情報
                'ai_analysis': json.dumps({
                    'executive_summary': product_analysis.get('executive_summary', ''),
                    'potential_concerns': product_analysis.get('potential_concerns', []),
                    'best_fit_customers': product_analysis.get('best_fit_customers', []),
                    'cost_simulation': financial_summary.get('cost_simulation', {}),
                    'negotiation_points': actionable_insights.get('negotiation_points', []),
                    'alternative_considerations': actionable_insights.get('alternative_considerations', [])
                }, ensure_ascii=False)
            }
            
        except Exception as e:
            logger.error(f"Error extracting product data from processed_id {processed_data.id}: {e}")
            return None
    
    def _get_raw_structured_data(self, raw_data_id: int) -> Dict:
        """生データから構造化データを取得"""
        try:
            sql = "SELECT structured_data FROM raw_loan_data WHERE id = %s"
            self.cursor.execute(sql, (raw_data_id,))
            result = self.cursor.fetchone()
            
            if result and result['structured_data']:
                return json.loads(result['structured_data'])
            return {}
            
        except Exception as e:
            logger.warning(f"Failed to get raw structured data for raw_data_id {raw_data_id}: {e}")
            return {}
    
    def _standardize_loan_category(self, category: str) -> str:
        """ローンカテゴリを標準化"""
        if not category:
            return 'その他'
        
        category_lower = category.lower()
        
        if 'マイカー' in category or '自動車' in category or 'カー' in category:
            return 'マイカーローン'
        elif '住宅' in category or 'ホーム' in category:
            return '住宅ローン'
        elif 'カード' in category:
            return 'カードローン'
        elif '教育' in category:
            return '教育ローン'
        elif 'フリー' in category or '多目的' in category:
            return 'フリーローン'
        else:
            return 'その他'
    
    def _standardize_rate_type(self, rate_type: str) -> str:
        """金利種別を標準化"""
        if not rate_type:
            return None
        
        rate_type_lower = rate_type.lower()
        
        if '固定' in rate_type_lower:
            return '固定金利'
        elif '変動' in rate_type_lower:
            return '変動金利'
        elif '選択' in rate_type_lower:
            return '金利選択型'
        else:
            return None
    
    def save_loan_product(self, processed_data: ProcessedLoanData, product_data: Dict) -> int:
        """統合ローン商品データを保存"""
        sql = """
            INSERT INTO loan_products (
                processed_data_id, institution_id, product_name, product_code, loan_type, 
                loan_category, summary, interest_rate_min, interest_rate_max, interest_rate_type,
                loan_amount_min, loan_amount_max, loan_amount_unit,
                loan_term_min, loan_term_max, loan_term_unit,
                repayment_methods, application_requirements, features,
                is_active, data_updated_at, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                product_name = VALUES(product_name),
                loan_type = VALUES(loan_type),
                summary = VALUES(summary),
                interest_rate_min = VALUES(interest_rate_min),
                interest_rate_max = VALUES(interest_rate_max),
                interest_rate_type = VALUES(interest_rate_type),
                loan_amount_min = VALUES(loan_amount_min),
                loan_amount_max = VALUES(loan_amount_max),
                loan_term_min = VALUES(loan_term_min),
                loan_term_max = VALUES(loan_term_max),
                repayment_methods = VALUES(repayment_methods),
                application_requirements = VALUES(application_requirements),
                features = VALUES(features),
                data_updated_at = VALUES(data_updated_at),
                updated_at = VALUES(updated_at)
        """
        
        now = datetime.now()
        
        self.cursor.execute(sql, (
            processed_data.id,
            processed_data.institution_id,
            product_data['product_name'],
            product_data['product_code'],
            product_data['loan_type'],
            product_data['loan_category'],
            product_data['summary'],
            product_data['interest_rate_min'],
            product_data['interest_rate_max'],
            product_data['interest_rate_type'],
            product_data['loan_amount_min'],
            product_data['loan_amount_max'],
            product_data['loan_amount_unit'],
            product_data['loan_term_min'],
            product_data['loan_term_max'],
            product_data['loan_term_unit'],
            product_data['repayment_methods'],
            product_data['application_requirements'],
            product_data['features'],
            product_data['is_active'],
            product_data['data_updated_at'],
            now,
            now
        ))
        
        return self.cursor.lastrowid
    
    def create_product_history(self, loan_product_id: int, changes: Dict):
        """商品変更履歴を記録"""
        if not changes:
            return
        
        sql = """
            INSERT INTO loan_product_history (
                loan_product_id, changed_fields, old_values, new_values, changed_at
            ) VALUES (%s, %s, %s, %s, %s)
        """
        
        self.cursor.execute(sql, (
            loan_product_id,
            json.dumps(list(changes.keys()), ensure_ascii=False),
            json.dumps(changes.get('old_values', {}), ensure_ascii=False),
            json.dumps(changes.get('new_values', {}), ensure_ascii=False),
            datetime.now()
        ))
    
    def run(self, batch_size: int = 10):
        """統合処理バッチ実行"""
        logger.info(f"Product Integration Batch started (batch_size: {batch_size})")
        
        try:
            self.connect_database()
            
            # 未統合のAI処理済みデータを取得
            processed_data_list = self.get_unintegrated_processed_data(batch_size)
            
            if not processed_data_list:
                logger.info("No unintegrated processed data found")
                return
            
            logger.info(f"Integrating {len(processed_data_list)} items")
            
            integrated_count = 0
            failed_count = 0
            
            for processed_data in processed_data_list:
                try:
                    logger.info(f"Integrating processed_id: {processed_data.id} - {processed_data.institution_name}")
                    
                    # 商品データ抽出
                    product_data = self.extract_product_data(processed_data)
                    
                    if not product_data:
                        logger.warning(f"Failed to extract product data for processed_id: {processed_data.id}")
                        failed_count += 1
                        continue
                    
                    # 商品データ保存
                    loan_product_id = self.save_loan_product(processed_data, product_data)
                    
                    self.connection.commit()
                    integrated_count += 1
                    
                    logger.info(f"✅ Successfully integrated: loan_product_id {loan_product_id}")
                    
                except Exception as e:
                    logger.error(f"Error integrating processed_id {processed_data.id}: {e}")
                    self.connection.rollback()
                    failed_count += 1
                    continue
            
            logger.info(f"Integration completed: {integrated_count} integrated, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Integration batch error: {e}")
            raise
        finally:
            self.close_database()

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='統合処理バッチ')
    parser.add_argument('--batch-size', type=int, default=10, help='バッチサイズ (default: 10)')
    
    args = parser.parse_args()
    
    # バッチ処理実行
    batch = ProductIntegrationBatch()
    batch.run(batch_size=args.batch_size)

if __name__ == '__main__':
    main()
