# loan_scraper/models.py
# -*- coding: utf-8 -*-
from pydantic import BaseModel
from typing import Optional


class LoanProduct(BaseModel):
    financial_institution_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    loan_type: Optional[str] = None
    category: Optional[str] = None
    min_interest_rate: Optional[float] = None
    max_interest_rate: Optional[float] = None
    interest_type: Optional[str] = None
    min_loan_amount: Optional[int] = None
    max_loan_amount: Optional[int] = None
    min_loan_term: Optional[int] = None  # months
    max_loan_term: Optional[int] = None
    repayment_method: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    income_requirements: Optional[str] = None
    guarantor_requirements: Optional[str] = None
    special_features: Optional[str] = None
    source_reference: Optional[str] = None
    is_active: bool = True
    published_at: Optional[str] = None


class RawLoanData(BaseModel):
    financial_institution_id: int
    source_url: str
    html_content: str
    extracted_text: str
    content_hash: str
    scraping_status: str
    scraped_at: str