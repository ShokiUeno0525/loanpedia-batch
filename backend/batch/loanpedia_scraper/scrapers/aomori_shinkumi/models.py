# -*- coding: utf-8 -*-
"""
青森県信用組合データモデル
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class LoanProduct:
    """ローン商品データモデル"""
    # 基本情報（必須フィールド）
    product_id: str
    name: str
    category: str
    min_interest_rate: float
    max_interest_rate: float
    min_loan_amount: int
    max_loan_amount: int

    # オプションフィールド（デフォルト値あり）
    interest_type: str = "変動金利"
    min_loan_term_months: Optional[int] = None
    max_loan_term_months: Optional[int] = None
    min_age: int = 20
    max_age: int = 80
    income_requirements: str = "継続した収入のある方"
    guarantor_requirements: str = "原則不要（保証会社の保証を受けられる方）"
    eligibility_requirements: Optional[str] = None
    fund_usage: Optional[str] = None
    special_features: str = ""
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoanProduct':
        """辞書から作成"""
        return cls(**data)


@dataclass
class FinancialInstitution:
    """金融機関データモデル"""
    institution_code: str
    institution_name: str
    institution_type: str
    website_url: str

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)


@dataclass
class ScrapingResult:
    """スクレイピング結果データモデル"""
    # 金融機関情報
    institution: FinancialInstitution

    # 商品リスト
    products: List[LoanProduct]

    # 実行情報
    scraping_status: str
    scraped_at: str
    total_products: int
    failed_products: List[str]
    success_rate: float

    # エラー情報（失敗時）
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            **self.institution.to_dict(),
            'products': [product.to_dict() for product in self.products],
            'scraping_status': self.scraping_status,
            'scraped_at': self.scraped_at,
            'total_products': self.total_products,
            'failed_products': self.failed_products,
            'success_rate': self.success_rate,
            'error': self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScrapingResult':
        """辞書から作成"""
        institution = FinancialInstitution(
            institution_code=data['institution_code'],
            institution_name=data['institution_name'],
            institution_type=data['institution_type'],
            website_url=data['website_url']
        )

        products = [
            LoanProduct.from_dict(product_data)
            for product_data in data.get('products', [])
        ]

        return cls(
            institution=institution,
            products=products,
            scraping_status=data['scraping_status'],
            scraped_at=data['scraped_at'],
            total_products=data['total_products'],
            failed_products=data.get('failed_products', []),
            success_rate=data.get('success_rate', 0.0),
            error=data.get('error')
        )