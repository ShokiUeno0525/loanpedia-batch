# loanpedia_scraper/scrapers/aoimori_shinkin/__init__.py
"""Package init for aoimori_shinkin.

Avoid importing submodules at import time to prevent circular imports.
"""

__all__: list[str] = []
# どうしても re-export したければ遅延評価で:
# def get_scraper():
#     from .product_scraper import AoimoriShinkinScraper
#     return AoimoriShinkinScraper
