"""青森みちのく銀行スクレイピングパッケージ。"""

try:
    # Lambda環境での絶対インポート
    from aomori_michinoku_bank.base_scraper import AomorimichinokuBankScraper, BaseLoanScraper
except ImportError:
    # 開発環境での相対インポート
    from .base_scraper import AomorimichinokuBankScraper, BaseLoanScraper

__all__ = [
    'AomorimichinokuBankScraper',
    'BaseLoanScraper',
]
