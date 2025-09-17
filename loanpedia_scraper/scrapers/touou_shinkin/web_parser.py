# loan_scraper/web_parser.py
# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple, Optional
import re
import unicodedata
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """テキストを正規化（全角→半角変換など）"""
    if not text:
        return ""
    # Unicode正規化（全角→半角変換）
    text = unicodedata.normalize('NFKC', text)
    # 改行・空白の整理
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_amount_from_cell(text: str) -> Tuple[Optional[int], Optional[int]]:
    """融資金額セルから最小・最大値を抽出"""
    text = normalize_text(text)

    # 範囲パターン（X万円以上Y万円以内）
    range_pattern = r'(\d+(?:,\d+)?)\s*万円?\s*以上[^0-9]*(\d+(?:,\d+)?)\s*万円?\s*以内'
    range_match = re.search(range_pattern, text)

    if range_match:
        min_val = int(range_match.group(1).replace(',', '')) * 10000
        max_val = int(range_match.group(2).replace(',', '')) * 10000
        return (min_val, max_val)

    # 単一値パターン（X万円以内）
    single_pattern = r'(\d+(?:,\d+)?)\s*万円?\s*以内'
    single_match = re.search(single_pattern, text)

    if single_match:
        max_val = int(single_match.group(1).replace(',', '')) * 10000
        return (None, max_val)

    return (None, None)


def extract_term_from_cell(text: str) -> Tuple[Optional[int], Optional[int]]:
    """融資期間セルから最小・最大値を抽出（月単位）"""
    text = normalize_text(text)

    terms = []

    # 年数パターン
    year_patterns = [
        r'(\d+)\s*年\s*以内',
        r'(\d+)\s*年\s*以下',
        r'最長\s*(\d+)\s*年',
        r'(\d+)\s*年'
    ]

    for pattern in year_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            years = int(match)
            if 1 <= years <= 50:  # 妥当範囲
                terms.append(years * 12)

    # 月数パターン
    month_patterns = [
        r'(\d+)\s*ヶ月\s*以内',
        r'(\d+)\s*ヶ月\s*以下',
        r'(\d+)\s*ヶ月'
    ]

    for pattern in month_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            months = int(match)
            if 1 <= months <= 600:  # 妥当範囲
                terms.append(months)

    if not terms:
        return (None, None)

    # 最小値は通常6ヶ月と仮定、最大値は検出された値
    return (6, max(terms))


def parse_loan_products_from_web(html: str) -> List[Dict]:
    """WebページのHTMLからローン商品情報を抽出"""
    soup = BeautifulSoup(html, 'lxml')
    products = []

    # 各テーブルを処理
    tables = soup.find_all('table')

    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) < 2:  # ヘッダー + データが必要
            continue

        # ヘッダー行の確認
        header_row = rows[0]
        header_cells = header_row.find_all(['th', 'td'])
        if len(header_cells) < 3:  # 最低限の列数
            continue

        # ヘッダーから列の位置を特定（エンコーディング問題を考慮）
        header_texts = []
        for cell in header_cells:
            text = cell.get_text()
            # エンコーディング修正を試行
            try:
                # 破損したUTF-8をLatin-1として読み取ってUTF-8として再解釈
                if any(ord(c) > 127 for c in text):  # 非ASCII文字が含まれる場合
                    text = text.encode('latin-1').decode('utf-8')
            except:
                pass
            header_texts.append(normalize_text(text))

        name_col = -1
        amount_col = -1
        term_col = -1

        for i, header in enumerate(header_texts):
            if '商品名' in header:  # より具体的に
                name_col = i
            elif '融資金額' in header or (header.endswith('金額') and '融資' not in header):
                amount_col = i
            elif '融資期間' in header or '返済期間' in header:
                term_col = i

        # データ行を処理
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < max(name_col, amount_col, term_col) + 1:
                continue

            if name_col >= 0:
                # エンコーディング修正を適用
                product_name_text = cells[name_col].get_text()
                try:
                    if any(ord(c) > 127 for c in product_name_text):
                        product_name_text = product_name_text.encode('latin-1').decode('utf-8')
                except:
                    pass
                product_name = normalize_text(product_name_text)

                if not product_name or len(product_name) < 2:
                    continue

                # 該当する商品のみを抽出（より具体的な商品名で判定）
                target_products = [
                    'カーライフプラン', 'マイカーローン',
                    '教育プラン', '教育ローン', '新教育ローン', '教育カードローン',
                    'フリーローン', 'シルバーライフローン', 'カードローン'
                ]

                # 商品名が短く、対象商品名を含む場合のみ抽出
                if len(product_name) > 50:  # 説明文を除外
                    continue

                if not any(target in product_name for target in target_products):
                    continue

                product_data = {
                    'product_name': product_name,
                    'min_loan_amount': None,
                    'max_loan_amount': None,
                    'min_loan_term': None,
                    'max_loan_term': None,
                    'source': 'web_table',
                    'table_index': table_idx
                }

                # 融資金額の抽出
                if amount_col >= 0 and amount_col < len(cells):
                    amount_text_raw = cells[amount_col].get_text()
                    try:
                        if any(ord(c) > 127 for c in amount_text_raw):
                            amount_text_raw = amount_text_raw.encode('latin-1').decode('utf-8')
                    except:
                        pass
                    amount_text = normalize_text(amount_text_raw)
                    min_amount, max_amount = extract_amount_from_cell(amount_text)
                    product_data['min_loan_amount'] = min_amount
                    product_data['max_loan_amount'] = max_amount

                # 融資期間の抽出
                if term_col >= 0 and term_col < len(cells):
                    term_text_raw = cells[term_col].get_text()
                    try:
                        if any(ord(c) > 127 for c in term_text_raw):
                            term_text_raw = term_text_raw.encode('latin-1').decode('utf-8')
                    except:
                        pass
                    term_text = normalize_text(term_text_raw)
                    min_term, max_term = extract_term_from_cell(term_text)
                    product_data['min_loan_term'] = min_term
                    product_data['max_loan_term'] = max_term

                products.append(product_data)
                print(f"Webから抽出: {product_name}")  # loggingの代わりに直接print

    return products


def match_web_to_pdf_products(web_products: List[Dict], pdf_products: List[Dict]) -> List[Dict]:
    """WebとPDFの商品をマッチングして統合"""
    merged_products = []

    # 商品名のマッピング
    name_mapping = {
        'とうしんカーライフプラン': ['カーライフプラン', 'マイカーローン'],
        '教育ローン': ['教育プラン', '教育ローン'],
        '新教育ローン': ['新教育ローン'],
        '教育カードローン': ['教育カードローン'],
        'フリーローン': ['フリーローン'],
        'シルバーライフローン': ['シルバーライフローン'],
        'とうしんカードローン': ['カードローン']
    }

    for pdf_product in pdf_products:
        pdf_name = pdf_product.get('product_name', '')

        # 対応するWeb商品を検索
        web_match = None
        for web_product in web_products:
            web_name = web_product.get('product_name', '')

            # 直接マッチング
            if pdf_name in web_name or web_name in pdf_name:
                web_match = web_product
                break

            # マッピングテーブルを使用
            if pdf_name in name_mapping:
                for variant in name_mapping[pdf_name]:
                    if variant in web_name:
                        web_match = web_product
                        break
                if web_match:
                    break

        # 統合
        merged = dict(pdf_product)  # PDFベース

        if web_match:
            # Webの方が信頼性が高い項目で上書き
            if web_match.get('min_loan_amount') is not None:
                merged['min_loan_amount'] = web_match['min_loan_amount']
            if web_match.get('max_loan_amount') is not None:
                merged['max_loan_amount'] = web_match['max_loan_amount']
            if web_match.get('min_loan_term') is not None:
                merged['min_loan_term'] = web_match['min_loan_term']
            if web_match.get('max_loan_term') is not None:
                merged['max_loan_term'] = web_match['max_loan_term']

            merged['web_source'] = True
            logger.info(f"統合成功: {pdf_name} <- {web_match['product_name']}")
        else:
            merged['web_source'] = False
            logger.warning(f"Web商品が見つかりません: {pdf_name}")

        merged_products.append(merged)

    return merged_products