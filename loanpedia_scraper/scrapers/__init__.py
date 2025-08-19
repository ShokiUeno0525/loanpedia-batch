"""
スクレイピングモジュール

requests + BeautifulSoupベースのシンプルなスクレイパー群
金融機関ごとにサブモジュール化
"""

from .aomori_michinoku_bank import AomorimichinokuBankScraper
from .aoimori_shinkin import AoimoriShinkinScraper
from .touou_shinkin import TououShinkinScraper
from .aomoriken_shinyoukumiai import AomorikenShinyoukumiaiScraper

__all__ = [
    'AomorimichinokuBankScraper',
    'AoimoriShinkinScraper', 
    'TououShinkinScraper',
    'AomorikenShinyoukumiaiScraper'
]