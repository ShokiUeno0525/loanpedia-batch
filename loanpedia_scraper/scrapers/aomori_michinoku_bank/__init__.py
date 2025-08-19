"""
青森みちのく銀行スクレイピングモジュール
"""

from .mycar import AomorimichinokuBankScraper
from .education import AomorimichinokuEducationScraper

__all__ = [
    'AomorimichinokuBankScraper',
    'AomorimichinokuEducationScraper'
]