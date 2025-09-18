"""
スクレイピングモジュール

requests + BeautifulSoupベースのシンプルなスクレイパー群
金融機関ごとにサブモジュール化
"""

from .aomori_michinoku_bank import AomorimichinokuBankScraper

__all__ = ['AomorimichinokuBankScraper']
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/__init__.py
# スクレイパー群のパッケージ初期化
# なぜ: スクレイパー間の共通設定/エクスポート点とするため
# 関連: main.py, */*, ../database/*
