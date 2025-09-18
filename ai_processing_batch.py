#!/usr/bin/env python3
# /ai_processing_batch.py
# Bedrockを用いたAI処理バッチ（raw_loan_data → processed_loan_data）
# なぜ: 生データをAI要約・構造化し、統合処理の入力を作るため
# 関連: product_integration_batch.py, loanpedia_scraper/database/loan_database.py, template.yaml, docker-compose.yml
"""
AI処理バッチ: BedRock APIを使用してローンデータを要約・構造化
"""

import os
import sys
import json
import pymysql
import boto3
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
class RawLoanData:
    """生ローンデータ"""
    id: int
    institution_id: int
    institution_name: str
    source_url: str
    page_title: str
    html_content: str
    structured_data: dict
    scraped_at: datetime

class BedrockAIProcessor:
    """BedRock API を使用したAI処理クラス"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.bedrock = boto3.client('bedrock-runtime', region_name=region_name)
        self.model_id = 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    def summarize_loan_data(self, raw_data: RawLoanData) -> Dict:
        """ローンデータをAIで要約・構造化"""
        
        # プロンプト構築
        prompt = self._build_prompt(raw_data)
        
        try:
            # BedRock API呼び出し
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-25",
                    "max_tokens": 4000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            # レスポンス解析
            result = json.loads(response['body'].read())
            ai_summary_text = result['content'][0]['text']
            
            # JSON形式で構造化データを抽出
            ai_summary = self._parse_ai_response(ai_summary_text)
            
            return {
                'ai_summary': ai_summary,
                'ai_model': self.model_id,
                'processing_status': 'completed',
                'validation_status': 'valid',
                'raw_response': ai_summary_text
            }
            
        except Exception as e:
            logger.error(f"AI processing failed for raw_data_id {raw_data.id}: {e}")
            return {
                'ai_summary': {},
                'ai_model': self.model_id,
                'processing_status': 'failed',
                'validation_status': 'error',
                'error_message': str(e)
            }
    
    def _build_prompt(self, raw_data: RawLoanData) -> str:
        """商品要約用プロンプトを構築"""
        return f"""
あなたは金融商品の専門コンサルタントです。Scrapyで精密に抽出済みの構造化データを基に、顧客向けの商品要約と分析を行ってください。

## 入力データ
**金融機関**: {raw_data.institution_name}
**商品ページURL**: {raw_data.source_url}

**Scrapyで抽出済みの正確な構造化データ**:
```json
{json.dumps(raw_data.structured_data, ensure_ascii=False, indent=2)}
```

**補足情報** (ページタイトル): {raw_data.page_title}

## 分析要求
上記の構造化データは信頼できる正確な情報です。このデータを基に、以下のJSON形式で商品要約と分析を行ってください：

```json
{{
  "product_analysis": {{
    "executive_summary": "商品の核心を3-4行で要約",
    "competitive_advantages": ["この商品の強み1", "強み2", "強み3"],
    "potential_concerns": ["注意すべき点1", "注意点2"],
    "best_fit_customers": ["最適な顧客像1", "顧客像2", "顧客像3"]
  }},
  "customer_guide": {{
    "simple_explanation": "一般消費者向けの分かりやすい商品説明（200文字程度）",
    "key_benefits": ["顧客メリット1", "メリット2", "メリット3"],
    "application_difficulty": "申込の難易度（簡単/普通/やや難しい/難しい）",
    "recommended_use_cases": ["おすすめの利用場面1", "場面2", "場面3"]
  }},
  "market_positioning": {{
    "interest_rate_competitiveness": "金利の市場競争力評価（高い/普通/低い）",
    "unique_selling_points": ["他行との差別化ポイント1", "ポイント2"],
    "target_market_segment": "ターゲット市場セグメント（プレミアム/スタンダード/エコノミー）"
  }},
  "risk_assessment": {{
    "borrower_risks": ["借入者が注意すべきリスク1", "リスク2"],
    "flexibility_score": "借入条件の柔軟性スコア（1-10）",
    "total_cost_transparency": "総コストの透明性（高い/普通/低い）"
  }},
  "financial_summary": {{
    "validated_conditions": {{
      "interest_rate_range": "抽出データから確認済みの金利範囲",
      "loan_amount_range": "確認済みの融資額範囲", 
      "loan_period_range": "確認済みの融資期間",
      "key_requirements": "主要な申込条件のまとめ"
    }},
    "cost_simulation": {{
      "typical_case": "標準的なケースでの概算コスト例",
      "best_case": "最も有利な条件での概算コスト",
      "worst_case": "最も不利な条件での概算コスト"
    }}
  }},
  "actionable_insights": {{
    "pre_application_checklist": ["申込前に確認すべき項目1", "項目2", "項目3"],
    "negotiation_points": ["交渉可能と思われるポイント1", "ポイント2"],
    "alternative_considerations": ["検討すべき他の選択肢1", "選択肢2"]
  }},
  "data_confidence": {{
    "analysis_reliability": "分析の信頼度（1-10）",
    "missing_information": ["より詳細な分析に必要な追加情報"],
    "last_updated_estimate": "データの鮮度に関する評価"
  }}
}}
```

## 分析方針
1. **データの信頼**: 構造化データは正確なものとして扱い、再検証は不要
2. **付加価値の創出**: 単純な情報整理ではなく、顧客視点での価値ある分析を提供
3. **実用性重視**: 実際にローンを検討する顧客が意思決定に使える情報を生成
4. **バランス**: 商品の長所だけでなく、注意点やリスクも公平に評価
5. **具体性**: 抽象的な表現ではなく、具体的で行動可能な示唆を提供

## 重要事項
- 抽出済みデータの数値や事実は変更せず、そのまま使用してください
- 推測や憶測ではなく、データに基づいた分析を行ってください
- 顧客の立場に立った、実用的で価値のある要約を心がけてください
"""

    def _parse_ai_response(self, response_text: str) -> Dict:
        """AI応答からJSON構造化データを抽出"""
        try:
            # JSON部分を抽出（```json と ``` の間）
            start_marker = "```json"
            end_marker = "```"
            
            start_idx = response_text.find(start_marker)
            if start_idx != -1:
                start_idx += len(start_marker)
                end_idx = response_text.find(end_marker, start_idx)
                if end_idx != -1:
                    json_str = response_text[start_idx:end_idx].strip()
                    return json.loads(json_str)
            
            # JSONマーカーが見つからない場合、全体をJSONとして解析試行
            return json.loads(response_text.strip())
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            return {
                "raw_response": response_text,
                "parse_error": str(e)
            }

class AIProcessingBatch:
    """AI処理バッチメイン処理クラス"""
    
    def __init__(self):
        self.db_config = self._load_db_config()
        self.ai_processor = BedrockAIProcessor()
        self.connection = None
        self.cursor = None
    
    def _load_db_config(self) -> Dict:
        """データベース設定を読み込み（共通ユーティリティ使用）"""
        try:
            # ルート直下から database パッケージを参照
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
    
    def get_unprocessed_raw_data(self, limit: int = 10) -> List[RawLoanData]:
        """未処理の生データを取得"""
        sql = """
            SELECT 
                r.id, r.institution_id, r.source_url, r.page_title, 
                r.html_content, r.structured_data, r.scraped_at,
                f.institution_name
            FROM raw_loan_data r
            JOIN financial_institutions f ON r.institution_id = f.id
            LEFT JOIN processed_loan_data p ON r.id = p.raw_data_id
            WHERE p.id IS NULL
            ORDER BY r.scraped_at DESC
            LIMIT %s
        """
        
        self.cursor.execute(sql, (limit,))
        rows = self.cursor.fetchall()
        
        raw_data_list = []
        for row in rows:
            structured_data = {}
            if row['structured_data']:
                try:
                    structured_data = json.loads(row['structured_data'])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in structured_data for ID {row['id']}")
            
            raw_data_list.append(RawLoanData(
                id=row['id'],
                institution_id=row['institution_id'],
                institution_name=row['institution_name'],
                source_url=row['source_url'],
                page_title=row['page_title'],
                html_content=row['html_content'],
                structured_data=structured_data,
                scraped_at=row['scraped_at']
            ))
        
        return raw_data_list
    
    def save_processed_data(self, raw_data_id: int, institution_id: int, ai_result: Dict):
        """AI処理結果を保存"""
        sql = """
            INSERT INTO processed_loan_data (
                raw_data_id, institution_id, ai_summary, ai_model,
                processing_status, validation_status, validation_messages, 
                error_message, processed_at, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        now = datetime.now()
        validation_messages = None
        
        # データ品質情報があれば validation_messages に保存
        if 'ai_summary' in ai_result and 'data_quality' in ai_result['ai_summary']:
            validation_messages = json.dumps(ai_result['ai_summary']['data_quality'])
        
        self.cursor.execute(sql, (
            raw_data_id,
            institution_id,
            json.dumps(ai_result.get('ai_summary', {}), ensure_ascii=False),
            ai_result.get('ai_model', ''),
            ai_result.get('processing_status', 'completed'),
            ai_result.get('validation_status', 'valid'),
            validation_messages,
            ai_result.get('error_message'),
            now,
            now,
            now
        ))
        
        return self.cursor.lastrowid
    
    def run(self, batch_size: int = 5):
        """バッチ処理実行"""
        logger.info(f"AI Processing Batch started (batch_size: {batch_size})")
        
        try:
            self.connect_database()
            
            # 未処理データを取得
            raw_data_list = self.get_unprocessed_raw_data(batch_size)
            
            if not raw_data_list:
                logger.info("No unprocessed data found")
                return
            
            logger.info(f"Processing {len(raw_data_list)} items")
            
            processed_count = 0
            failed_count = 0
            
            for raw_data in raw_data_list:
                try:
                    logger.info(f"Processing raw_data_id: {raw_data.id} - {raw_data.institution_name}")
                    
                    # AI処理実行
                    ai_result = self.ai_processor.summarize_loan_data(raw_data)
                    
                    # 結果保存
                    processed_id = self.save_processed_data(
                        raw_data.id, 
                        raw_data.institution_id, 
                        ai_result
                    )
                    
                    self.connection.commit()
                    
                    if ai_result['processing_status'] == 'completed':
                        processed_count += 1
                        logger.info(f"✅ Successfully processed ID: {processed_id}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Processing failed for raw_data_id: {raw_data.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing raw_data_id {raw_data.id}: {e}")
                    self.connection.rollback()
                    failed_count += 1
                    continue
            
            logger.info(f"Batch processing completed: {processed_count} processed, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            raise
        finally:
            self.close_database()

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI処理バッチ')
    parser.add_argument('--batch-size', type=int, default=5, help='バッチサイズ (default: 5)')
    parser.add_argument('--region', type=str, default='us-east-1', help='AWS region (default: us-east-1)')
    
    args = parser.parse_args()
    
    # 環境変数チェック
    required_env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # バッチ処理実行
    batch = AIProcessingBatch()
    batch.run(batch_size=args.batch_size)

if __name__ == '__main__':
    main()
