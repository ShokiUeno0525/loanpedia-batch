"""
青森みちのく銀行スクレイピングモジュール
"""

from .mycar import AomorimichinokuBankScraper
from .education_repetition import AomorimichinokuEducationRepetitionScraper
from .education_deed import AomorimichinokuEducationDeedScraper

__all__ = [
    'AomorimichinokuBankScraper',
    'AomorimichinokuEducationRepetitionScraper',
    'AomorimichinokuEducationDeedScraper'
]