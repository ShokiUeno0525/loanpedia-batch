"""
スクレイピングモジュール

requests + BeautifulSoupベースのシンプルなスクレイパー群
金融機関ごとにサブモジュール化
"""

from .aomori_michinoku_bank import AomorimichinokuBankScraper
_HAS_TOUOU = False
try:  # optional import
    from .touou_shinkin import TououShinkinScraper  # type: ignore[import-not-found]
    _HAS_TOUOU = True
except Exception:
    pass

_HAS_AOMORIKEN = False
try:  # optional import
    from .aomoriken_shinyoukumiai import AomorikenShinyoukumiaiScraper  # type: ignore[import-not-found]
    _HAS_AOMORIKEN = True
except Exception:
    pass

# オプション: 青い森信用金庫（未実装/不要なら無視）
try:  # pragma: no cover - optional import
    from .aoimori_shinkin import AoimoriShinkinScraper  # type: ignore[import-not-found]
    _HAS_AOIMORI = True
except Exception:
    _HAS_AOIMORI = False

__all__ = ['AomorimichinokuBankScraper']
if _HAS_TOUOU:
    __all__.append('TououShinkinScraper')
if _HAS_AOMORIKEN:
    __all__.append('AomorikenShinyoukumiaiScraper')
if _HAS_AOIMORI:
    __all__.append('AoimoriShinkinScraper')
