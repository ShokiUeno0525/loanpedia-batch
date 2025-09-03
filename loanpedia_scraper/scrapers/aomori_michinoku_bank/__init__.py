"""青森みちのく銀行スクレイピングパッケージ。"""

try:
    from loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper import AomorimichinokuBankScraper, BaseLoanScraper
except ImportError:
    from . import base_scraper
    from .base_scraper import AomorimichinokuBankScraper, BaseLoanScraper

__all__ = [
    'AomorimichinokuBankScraper',
    'BaseLoanScraper',
]
