"""
スクレイピングモジュール

requests + BeautifulSoupベースのシンプルなスクレイパー群
金融機関ごとにサブモジュール化
"""

from .aomori_michinoku_bank import AomorimichinokuBankScraper

__all__ = ['AomorimichinokuBankScraper']
