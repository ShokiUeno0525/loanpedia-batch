"""
スクレイピングモジュール

requests + BeautifulSoupベースのシンプルなスクレイパー群
金融機関ごとにサブモジュール化
"""

from .aomori_michinoku_bank import AomorimichinokuBankScraper
from .touou_shinkin import TououShinkinScraper
from .aomoriken_shinyoukumiai import AomorikenShinyoukumiaiScraper

# オプション: 青い森信用金庫（未実装/不要なら無視）
try:  # pragma: no cover - optional import
    from .aoimori_shinkin import AoimoriShinkinScraper  # type: ignore[import-not-found]
    _HAS_AOIMORI = True
except Exception:
    _HAS_AOIMORI = False

__all__ = [
    'AomorimichinokuBankScraper',
    'TououShinkinScraper',
    'AomorikenShinyoukumiaiScraper'
]
if _HAS_AOIMORI:
    __all__.append('AoimoriShinkinScraper')
