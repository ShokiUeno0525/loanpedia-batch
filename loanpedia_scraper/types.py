"""
型定義モジュール

スクレイピングデータとAPI応答の型を定義
"""

from typing import TypedDict, Optional, List, Union
from datetime import datetime

# 基本的なローン情報の型
class LoanProductData(TypedDict, total=False):
    """ローン商品データの型定義"""
    # 基本情報
    institution_name: str
    institution_code: str
    product_name: str
    product_code: Optional[str]
    loan_category: str
    
    # 金利情報
    interest_rate_min: Optional[float]
    interest_rate_max: Optional[float]
    interest_rate_type: Optional[str]
    
    # 融資金額
    loan_amount_min: Optional[int]
    loan_amount_max: Optional[int]
    loan_amount_unit: str
    
    # 融資期間
    loan_term_min: Optional[int]
    loan_term_max: Optional[int]
    loan_term_unit: str
    
    # その他
    summary: Optional[str]
    features: Optional[List[str]]
    repayment_methods: Optional[List[str]]
    application_requirements: Optional[List[str]]
    
    # メタ情報
    source_url: str
    scraped_at: datetime
    content_hash: Optional[str]

# スクレイピング結果の型
class ScrapingResult(TypedDict):
    """スクレイピング結果の型定義"""
    success: bool
    institution_name: str
    data_count: int
    products: List[LoanProductData]
    error_message: Optional[str]
    execution_time: float
    timestamp: datetime

# API応答の型
class LambdaResponse(TypedDict):
    """Lambda応答の型定義"""
    statusCode: int
    body: Union[ScrapingResult, str]  # JSON文字列の場合もある

# データベース設定の型
class DatabaseConfig(TypedDict):
    """データベース設定の型定義"""
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str

# 抽出された構造化データの型
class ExtractedLoanData(TypedDict, total=False):
    """抽出されたローンデータの型定義"""
    interest_rates: Optional[List[float]]
    loan_amounts: Optional[List[int]]
    loan_periods: Optional[List[int]]
    age_requirements: Optional[List[int]]
    features: Optional[List[str]]
    raw_text: str

# スクレイピング設定の型
class ScrapingConfig(TypedDict, total=False):
    """スクレイピング設定の型定義"""
    timeout: int
    retry_count: int
    delay_seconds: float
    user_agent: str
    headers: dict[str, str]