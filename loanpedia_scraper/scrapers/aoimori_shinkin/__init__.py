# loanpedia_scraper/scrapers/aoimori_shinkin/__init__.py
"""Package init for aoimori_shinkin.

Avoid importing submodules at import time to prevent circular imports.
"""

__all__: list[str] = []
# どうしても re-export したければ遅延評価で:
# def get_scraper():
#     from .product_scraper import AoimoriShinkinScraper
#     return AoimoriShinkinScraper
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/aoimori_shinkin/__init__.py
# 青い森信用金庫スクレイパーパッケージ初期化
# なぜ: 構成要素（http/html/pdf/models/config）の集約と公開のため
# 関連: product_scraper.py, html_parser.py, pdf_parser.py, config.py
