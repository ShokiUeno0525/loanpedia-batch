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
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aomori_michinoku_bank/__init__.py
# 青森みちのく銀行スクレイパーパッケージ初期化
# なぜ: 構成モジュールの集約と公開のため
# 関連: product_scraper.py, html_parser.py, pdf_parser.py, config.py
