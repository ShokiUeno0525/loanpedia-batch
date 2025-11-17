"""東奥信用金庫スクレイパーモジュール"""

from .product_scraper import TououShinkinScraper

__all__ = ["TououShinkinScraper"]
#!/usr/bin/env python3
# /loanpedia_scraper/scrapers/touou_shinkin/__init__.py
# 東奥信用金庫スクレイパーパッケージ初期化
# なぜ: 構成要素の集約と参照点の明確化のため
# 関連: product_scraper.py, pdf_parser.py, html_parser.py, config.py
