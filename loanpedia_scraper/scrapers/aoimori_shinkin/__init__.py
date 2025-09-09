"""青い森信用金庫スクレイパーパッケージ

aomori_michinoku_bank に倣った3層構成:
- I/O: http_client, pdf_parser
- Domain: extractors, models
- Application: product_scraper (AoimoriShinkinScraper)
"""

from .product_scraper import AoimoriShinkinScraper  # re-export for handler
