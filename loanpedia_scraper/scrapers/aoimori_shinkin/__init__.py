"""Aoimori Shinkin scraper package.

3-layer structure inspired by aomori_michinoku_bank:
- I/O: http_client, pdf_parser
- Domain: extractors, models
- Application: product_scraper (AoimoriShinkinScraper)
"""

from .product_scraper import AoimoriShinkinScraper  # re-export for handler
