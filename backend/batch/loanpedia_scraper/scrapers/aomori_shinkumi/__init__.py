# -*- coding: utf-8 -*-
"""
青森県信用組合スクレイピングモジュール
"""

from .product_scraper import AomoriShinkumiScraper
from .handler import AomoriShinkumiHandler, lambda_handler
from .models import LoanProduct, FinancialInstitution, ScrapingResult

__all__ = [
    'AomoriShinkumiScraper',
    'AomoriShinkumiHandler',
    'lambda_handler',
    'LoanProduct',
    'FinancialInstitution',
    'ScrapingResult'
]