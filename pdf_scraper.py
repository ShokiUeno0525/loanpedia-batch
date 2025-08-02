#!/usr/bin/env python3
"""
PDF スクレイピングモジュール
PyPDF2を使用してPDFファイルからローン情報を抽出する
"""

import os
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
import PyPDF2
from io import BytesIO
import requests


class PDFScraper:
    """PDFファイルからテキストを抽出するクラス"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化
        
        Args:
            logger: ロガーインスタンス（省略時はデフォルトロガーを作成）
        """
        self.logger = logger or self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """デフォルトロガーのセットアップ"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def extract_text_from_file(self, file_path: Union[str, Path]) -> Dict[str, any]:
        """
        ローカルPDFファイルからテキストを抽出
        
        Args:
            file_path: PDFファイルのパス
            
        Returns:
            Dict: 抽出結果
                - success: 成功フラグ
                - text: 抽出されたテキスト
                - pages: ページ数
                - error: エラーメッセージ（失敗時）
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'ファイルが存在しません: {file_path}',
                    'text': '',
                    'pages': 0
                }
            
            if not file_path.suffix.lower() == '.pdf':
                return {
                    'success': False,
                    'error': f'PDFファイルではありません: {file_path}',
                    'text': '',
                    'pages': 0
                }
            
            with open(file_path, 'rb') as file:
                return self._extract_text_from_bytes(file.read())
                
        except Exception as e:
            self.logger.error(f"PDFファイル読み込みエラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'pages': 0
            }
    
    def extract_text_from_url(self, url: str, timeout: int = 30) -> Dict[str, any]:
        """
        URL経由でPDFファイルからテキストを抽出
        
        Args:
            url: PDFファイルのURL
            timeout: タイムアウト秒数
            
        Returns:
            Dict: 抽出結果
        """
        try:
            self.logger.info(f"PDF取得開始: {url}")
            
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            if 'application/pdf' not in response.headers.get('content-type', ''):
                return {
                    'success': False,
                    'error': f'PDFファイルではありません: {response.headers.get("content-type")}',
                    'text': '',
                    'pages': 0
                }
            
            return self._extract_text_from_bytes(response.content)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"PDF取得エラー: {e}")
            return {
                'success': False,
                'error': f'PDF取得エラー: {str(e)}',
                'text': '',
                'pages': 0
            }
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'pages': 0
            }
    
    def _extract_text_from_bytes(self, pdf_bytes: bytes) -> Dict[str, any]:
        """
        PDFバイトデータからテキストを抽出
        
        Args:
            pdf_bytes: PDFのバイトデータ
            
        Returns:
            Dict: 抽出結果
        """
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            
            if len(pdf_reader.pages) == 0:
                return {
                    'success': False,
                    'error': 'ページが見つかりません',
                    'text': '',
                    'pages': 0
                }
            
            extracted_text = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        extracted_text.append({
                            'page': page_num + 1,
                            'text': page_text.strip()
                        })
                    else:
                        self.logger.warning(f"ページ {page_num + 1}: テキストが抽出できませんでした")
                        
                except Exception as e:
                    self.logger.warning(f"ページ {page_num + 1} 処理エラー: {e}")
                    continue
            
            if not extracted_text:
                return {
                    'success': False,
                    'error': 'テキストが抽出できませんでした（スキャンされたPDFの可能性があります）',
                    'text': '',
                    'pages': len(pdf_reader.pages)
                }
            
            full_text = '\n\n'.join([page['text'] for page in extracted_text])
            
            self.logger.info(f"PDF処理完了: {len(pdf_reader.pages)}ページ, {len(full_text)}文字")
            
            return {
                'success': True,
                'text': full_text,
                'pages': len(pdf_reader.pages),
                'page_texts': extracted_text,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"PDFテキスト抽出エラー: {e}")
            return {
                'success': False,
                'error': f'PDFテキスト抽出エラー: {str(e)}',
                'text': '',
                'pages': 0
            }
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> Dict[str, any]:
        """
        PDFバイトデータからテキストを抽出（パブリックメソッド）
        
        Args:
            pdf_bytes: PDFのバイトデータ
            
        Returns:
            Dict: 抽出結果
        """
        return self._extract_text_from_bytes(pdf_bytes)
    
    def extract_loan_info(self, text: str) -> Dict[str, any]:
        """
        抽出されたテキストからローン情報を検索
        
        Args:
            text: 抽出されたテキスト
            
        Returns:
            Dict: ローン情報
        """
        import re
        
        loan_info = {
            'interest_rates': [],
            'loan_amounts': [],
            'terms': [],
            'conditions': [],
            'contact_info': []
        }
        
        # 金利情報の抽出
        interest_patterns = [
            r'(\d+\.\d+)%',
            r'金利[：:\s]*(\d+\.\d+)',
            r'年率[：:\s]*(\d+\.\d+)',
            r'実質年率[：:\s]*(\d+\.\d+)'
        ]
        
        for pattern in interest_patterns:
            matches = re.findall(pattern, text)
            loan_info['interest_rates'].extend(matches)
        
        # 融資金額の抽出
        amount_patterns = [
            r'(\d+)万円',
            r'(\d{1,3}(?:,\d{3})*)円',
            r'融資額[：:\s]*(\d+)',
            r'借入[：:\s]*(\d+)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            loan_info['loan_amounts'].extend(matches)
        
        # 期間の抽出
        term_patterns = [
            r'(\d+)年',
            r'(\d+)ヶ月',
            r'期間[：:\s]*(\d+)',
            r'返済期間[：:\s]*(\d+)'
        ]
        
        for pattern in term_patterns:
            matches = re.findall(pattern, text)
            loan_info['terms'].extend(matches)
        
        # 電話番号の抽出
        phone_pattern = r'(\d{2,4}-\d{2,4}-\d{4})'
        phone_matches = re.findall(phone_pattern, text)
        loan_info['contact_info'].extend(phone_matches)
        
        # 重複除去
        for key in loan_info:
            loan_info[key] = list(set(loan_info[key]))
        
        return loan_info


def main():
    """使用例"""
    scraper = PDFScraper()
    
    # ファイルから抽出する例
    # result = scraper.extract_text_from_file('sample.pdf')
    
    # URLから抽出する例
    # result = scraper.extract_text_from_url('https://example.com/loan_info.pdf')
    
    # if result['success']:
    #     print(f"抽出テキスト: {result['text'][:500]}...")
    #     
    #     # ローン情報の抽出
    #     loan_info = scraper.extract_loan_info(result['text'])
    #     print(f"ローン情報: {loan_info}")
    # else:
    #     print(f"エラー: {result['error']}")


if __name__ == '__main__':
    main()