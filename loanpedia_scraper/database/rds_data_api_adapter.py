"""
RDS Data API アダプター - シンプル実装

Aurora Serverless v2 の Data API を使用したデータベースアクセス
boto3のrds-dataクライアントを使用してHTTPベースでクエリ実行
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# boto3は実行時に利用可能
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available")


class RDSDataAPIAdapter:
    """RDS Data API を使用したシンプルなデータベースアダプター"""

    def __init__(self):
        """初期化"""
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for RDS Data API")

        self.db_arn = os.getenv("DB_ARN")
        self.secret_arn = os.getenv("DB_SECRET_ARN")
        self.database = os.getenv("DB_NAME", "loanpedia")
        self.region = os.getenv("AWS_REGION", "ap-northeast-1")

        if not self.db_arn or not self.secret_arn:
            raise ValueError(
                "DB_ARN and DB_SECRET_ARN environment variables are required"
            )

        self.client = boto3.client("rds-data", region_name=self.region)
        logger.info(
            f"RDS Data API adapter initialized (database={self.database}, region={self.region})"
        )

    def connect(self) -> bool:
        """接続確認（Data APIでは常に利用可能）"""
        return True

    def disconnect(self) -> None:
        """切断（Data APIでは不要）"""
        pass

    def __enter__(self):
        """コンテキストマネージャー開始"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.disconnect()

    def execute_statement(
        self, sql: str, parameters: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        SQL文を実行

        Args:
            sql: 実行するSQL文
            parameters: パラメータ（RDS Data API形式）

        Returns:
            実行結果
        """
        try:
            params = {
                "resourceArn": self.db_arn,
                "secretArn": self.secret_arn,
                "database": self.database,
                "sql": sql,
            }

            if parameters:
                params["parameters"] = parameters

            response = self.client.execute_statement(**params)
            return response

        except ClientError as e:
            logger.error(f"Failed to execute statement: {e}")
            raise

    def get_or_create_institution(
        self, institution_code: str, institution_name: str
    ) -> Optional[int]:
        """
        金融機関IDを取得または作成

        Args:
            institution_code: 金融機関コード
            institution_name: 金融機関名

        Returns:
            金融機関ID
        """
        try:
            # 既存チェック
            sql = "SELECT id FROM financial_institutions WHERE institution_code = :code"
            params = [{"name": "code", "value": {"stringValue": institution_code}}]

            response = self.execute_statement(sql, params)

            if response.get("records"):
                institution_id = response["records"][0][0]["longValue"]
                logger.info(
                    f"Found existing institution: {institution_name} (ID={institution_id})"
                )
                return institution_id

            # 新規作成
            sql = """
                INSERT INTO financial_institutions (institution_code, institution_name)
                VALUES (:code, :name)
            """
            params = [
                {"name": "code", "value": {"stringValue": institution_code}},
                {"name": "name", "value": {"stringValue": institution_name}},
            ]

            response = self.execute_statement(sql, params)
            institution_id = response.get("generatedFields", [{}])[0].get("longValue")

            logger.info(
                f"Created new institution: {institution_name} (ID={institution_id})"
            )
            return institution_id

        except Exception as e:
            logger.error(f"Failed to get or create institution: {e}")
            return None

    def save_loan_data(self, loan_data: Dict[str, Any]) -> Optional[int]:
        """
        ローンデータを保存（raw_loan_dataテーブル）

        Args:
            loan_data: ローンデータ

        Returns:
            保存したレコードのID
        """
        try:
            # 金融機関IDを取得または作成
            institution_id = self.get_or_create_institution(
                loan_data.get("institution_code", ""),
                loan_data.get("institution_name", ""),
            )

            if not institution_id:
                logger.error("Failed to get institution_id")
                return None

            # structured_dataにすべての商品情報を格納
            structured_data = {
                "product_name": loan_data.get("product_name"),
                "loan_category": loan_data.get("loan_category"),
                "min_interest_rate": loan_data.get("min_interest_rate"),
                "max_interest_rate": loan_data.get("max_interest_rate"),
                "interest_rate_type": loan_data.get("interest_rate_type"),
                "min_loan_amount": loan_data.get("min_loan_amount"),
                "max_loan_amount": loan_data.get("max_loan_amount"),
                "min_loan_period_months": loan_data.get("min_loan_period_months"),
                "max_loan_period_months": loan_data.get("max_loan_period_months"),
                "min_age": loan_data.get("min_age"),
                "max_age": loan_data.get("max_age"),
                "repayment_method": loan_data.get("repayment_method"),
                "application_conditions": loan_data.get("application_conditions"),
                "features": loan_data.get("features"),
            }

            # raw_loan_dataに保存
            sql = """
                INSERT INTO raw_loan_data (
                    institution_id,
                    source_url,
                    page_title,
                    html_content,
                    extracted_text,
                    structured_data,
                    content_hash,
                    scraped_at
                ) VALUES (
                    :institution_id,
                    :source_url,
                    :page_title,
                    :html_content,
                    :extracted_text,
                    :structured_data,
                    :content_hash,
                    NOW()
                )
            """

            params = [
                {"name": "institution_id", "value": {"longValue": institution_id}},
                {
                    "name": "source_url",
                    "value": {"stringValue": loan_data.get("source_url", "")},
                },
                {
                    "name": "page_title",
                    "value": {"stringValue": loan_data.get("product_name", "")},
                },
                {
                    "name": "html_content",
                    "value": {"stringValue": loan_data.get("html_content", "")[:65535]},  # TEXT型の制限
                },
                {
                    "name": "extracted_text",
                    "value": {"stringValue": loan_data.get("extracted_text", "")[:65535]},
                },
                {
                    "name": "structured_data",
                    "value": {
                        "stringValue": json.dumps(structured_data, ensure_ascii=False)
                    },
                },
                {
                    "name": "content_hash",
                    "value": {"stringValue": loan_data.get("content_hash", "")},
                },
            ]

            response = self.execute_statement(sql, params)
            raw_data_id = response.get("generatedFields", [{}])[0].get("longValue")

            logger.info(f"Saved raw_loan_data with Data API: ID={raw_data_id}")
            return raw_data_id

        except Exception as e:
            logger.error(f"Failed to save loan data via Data API: {e}")
            logger.exception(e)
            return None
