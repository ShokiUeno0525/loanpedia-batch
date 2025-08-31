# -*- coding: utf-8 -*-
"""
青森みちのく銀行スクレイピング用ユーティリティ

共通の正規表現パターンと抽出ヘルパー関数を定義
"""

import re
from typing import Dict, List, Tuple, Optional, Any, cast

# 共通正規表現パターン定義
COMMON_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    # 金利パターン
    "interest_rates": [
        (r"年\s*(\d+\.\d+)\s*[%％]\s*[〜～]\s*年\s*(\d+\.\d+)\s*[%％]", "基本金利範囲"),
        (r"(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "金利範囲"),
        (r"金利.*?(\d+\.\d+)\s*[%％].*?(\d+\.\d+)\s*[%％]", "金利テーブル"),
        (r"変動金利.*?(\d+\.\d+)\s*[%％]\s*[〜～]\s*(\d+\.\d+)\s*[%％]", "変動金利"),
    ],
    
    # 融資金額パターン（card.pyの改良版）
    "loan_amounts": [
        # 「10万円～1,000万円」「10万～1000万円」形式
        (r"(\d+(?:,\d{3})*)\s*万円?\s*[〜～から]\s*(\d+(?:,\d{3})*)\s*万円", "範囲指定（万円単位）"),
        # 「100,000円～10,000,000円」形式 
        (r"(\d+(?:,\d{3})*)\s*円\s*[〜～から]\s*(\d+(?:,\d{3})*)\s*円", "範囲指定（円単位）"),
        # 「最高1,000万円」「限度額1000万円」形式
        (r"(?:最高|限度額|上限|最大)\s*(\d+(?:,\d{3})*)\s*万円", "上限のみ（万円単位）"),
        # 「最高10,000,000円」形式
        (r"(?:最高|限度額|上限|最大)\s*(\d+(?:,\d{3})*)\s*円", "上限のみ（円単位）"),
    ],
    
    # 融資期間パターン
    "loan_periods": [
        (r"(\d+)\s*年.*?自動更新", "自動更新期間"),
        (r"契約期間.*?(\d+)\s*年", "契約期間"),
        (r"最大\s*(\d+)\s*年\s*(\d+)\s*[ヵヶ]月", "年月形式"),
        (r"最大\s*(\d+)\s*年", "最長年数"),
        (r"(\d+)\s*年間", "年間契約"),
    ],
    
    # 年齢制限パターン
    "age_requirements": [
        r"満(\d+)歳以上.*?満(\d+)歳未満",
        r"満(\d+)歳以上.*?満(\d+)歳以下", 
        r"(\d+)歳以上.*?(\d+)歳以下",
        r"(\d+)歳[〜～](\d+)歳",
    ],
}

# 商品別デフォルト値
PRODUCT_DEFAULTS = {
    "カードローン": {
        "interest_rates": (2.4, 14.5),
        "loan_amounts": (100000, 10000000),  # 10万円〜1000万円
        "loan_terms": (12, 36),  # 1年〜3年
        "min_age": 20,
        "max_age": 75,
        "repayment_method": "残高スライド返済（口座自動振替）",
    },
    "教育ローン": {
        "interest_rates": (4.2, 4.9),
        "loan_amounts": (500000, 10000000),  # 50万円〜1000万円
        "loan_terms": (6, 114),  # 6ヶ月〜9年6ヶ月
        "min_age": 20,
        "max_age": 74,
        "repayment_method": "利息のみ毎月返済（口座自動振替）",
    },
    "マイカーローン": {
        "interest_rates": (1.8, 3.5),
        "loan_amounts": (100000, 10000000),  # 10万円〜1000万円
        "loan_terms": (12, 84),  # 1年〜7年
        "min_age": 18,
        "max_age": 75,
        "repayment_method": "元利均等返済（口座自動振替）",
    },
}


class ExtractionUtils:
    """スクレイピング抽出処理のユーティリティクラス"""
    
    @staticmethod
    def extract_with_patterns(text: str, patterns: List[Tuple[str, str]], 
                            converter_func=None) -> Optional[Dict[str, Any]]:
        """
        パターンリストを使って値を抽出
        
        Args:
            text: 検索対象テキスト
            patterns: (正規表現, 説明) のタプルリスト
            converter_func: マッチした値を変換する関数
            
        Returns:
            抽出した値の辞書、または None
        """
        for pattern, description in patterns:
            match = re.search(pattern, text)
            if match:
                result = {
                    "pattern_type": description,
                    "match_text": match.group(),
                    "groups": match.groups(),
                }
                
                if converter_func:
                    result.update(converter_func(match.groups(), pattern))
                
                return result
        
        return None
    
    @staticmethod
    def convert_interest_rates(groups: Tuple[str, ...], pattern: str) -> Dict[str, float]:
        """金利抽出結果を変換"""
        if len(groups) >= 2:
            return {
                "min_interest_rate": float(groups[0]),
                "max_interest_rate": float(groups[1])
            }
        return {}
    
    @staticmethod
    def convert_loan_amounts(groups: Tuple[str, ...], pattern: str) -> Dict[str, int]:
        """融資金額抽出結果を変換"""
        result = {}
        
        if len(groups) == 2:
            # 範囲指定の場合
            min_amount = int(groups[0].replace(",", ""))
            max_amount = int(groups[1].replace(",", ""))
            
            # 万円単位か円単位かで調整
            if "万円" in pattern:
                result["min_loan_amount"] = min_amount * 10000
                result["max_loan_amount"] = max_amount * 10000
            else:
                result["min_loan_amount"] = min_amount
                result["max_loan_amount"] = max_amount
                
        elif len(groups) == 1:
            # 上限のみの場合
            max_amount = int(groups[0].replace(",", ""))
            
            # 万円単位か円単位かで調整
            if "万円" in pattern:
                result["min_loan_amount"] = 100000  # デフォルト10万円
                result["max_loan_amount"] = max_amount * 10000
            else:
                result["min_loan_amount"] = 100000  # デフォルト10万円
                result["max_loan_amount"] = max_amount
        
        return result
    
    @staticmethod
    def convert_loan_periods(groups: Tuple[str, ...], pattern: str) -> Dict[str, int]:
        """融資期間抽出結果を変換"""
        result = {}
        
        if "年月形式" in pattern and len(groups) >= 2:
            years = int(groups[-2])  # 最後から2番目
            months = int(groups[-1])  # 最後
            max_months = years * 12 + months
            result["min_loan_term_months"] = 12  # デフォルト最低1年
            result["max_loan_term_months"] = max_months
        elif len(groups) >= 1:
            years = int(groups[0])
            result["min_loan_term_months"] = 12  # デフォルト最低1年
            result["max_loan_term_months"] = years * 12
        
        return result
    
    @staticmethod
    def convert_age_requirements(groups: Tuple[str, ...], pattern: str) -> Dict[str, int]:
        """年齢制限抽出結果を変換"""
        if len(groups) >= 2:
            min_age = int(groups[0])
            max_age_value = int(groups[1])
            
            # 「未満」の場合は-1する（75歳未満 = 74歳以下）
            if "未満" in pattern:
                max_age = max_age_value - 1
            else:
                max_age = max_age_value
            
            return {
                "min_age": min_age,
                "max_age": max_age
            }
        
        return {}
    
    @staticmethod
    def get_product_defaults(product_type: str) -> Dict[str, Any]:
        """商品タイプに応じたデフォルト値を取得"""
        return PRODUCT_DEFAULTS.get(product_type, PRODUCT_DEFAULTS["カードローン"])
    
    @staticmethod
    def extract_common_features(text: str) -> List[str]:
        """共通商品特徴を抽出"""
        features = []
        
        feature_patterns = [
            ("WEB.*?(?:申込|完結)", "WEB申込対応"),
            ("来店不要", "来店不要"),
            ("ATM.*?利用", "ATM利用可能"),
            ("担保.*?不要", "担保不要"),
            ("保証人.*?不要", "保証人不要"),
            ("随時返済", "随時返済可能"),
            ("繰上返済.*?手数料.*?無料", "繰上返済手数料無料"),
        ]
        
        for pattern, feature_name in feature_patterns:
            if re.search(pattern, text):
                features.append(feature_name)
        
        return features
    
    @staticmethod
    def extract_guarantor_info(text: str, product_type: str = "カードローン") -> str:
        """保証人情報を抽出"""
        if "エム・ユー信用保証" in text:
            return "原則不要（エム・ユー信用保証が保証）"
        elif "ジャックス" in text:
            return "原則不要（ジャックスが保証）"
        elif "保証人" in text and "不要" in text:
            return "原則不要（保証会社が保証）"
        elif "保証会社" in text:
            return "保証会社による保証"
        
        return ""


def extract_interest_rates(text: str) -> Optional[Dict[str, Any]]:
    """金利情報を抽出するヘルパー関数"""
    return ExtractionUtils.extract_with_patterns(
        text, 
        cast(List[Tuple[str, str]], COMMON_PATTERNS["interest_rates"]),
        ExtractionUtils.convert_interest_rates
    )


def extract_loan_amounts(text: str) -> Optional[Dict[str, Any]]:
    """融資金額を抽出するヘルパー関数"""
    return ExtractionUtils.extract_with_patterns(
        text,
        cast(List[Tuple[str, str]], COMMON_PATTERNS["loan_amounts"]),
        ExtractionUtils.convert_loan_amounts
    )


def extract_loan_periods(text: str) -> Optional[Dict[str, Any]]:
    """融資期間を抽出するヘルパー関数"""
    return ExtractionUtils.extract_with_patterns(
        text,
        cast(List[Tuple[str, str]], COMMON_PATTERNS["loan_periods"]),
        ExtractionUtils.convert_loan_periods
    )


def extract_age_requirements(text: str) -> Optional[Dict[str, Any]]:
    """年齢制限を抽出するヘルパー関数"""
    age_patterns = cast(List[str], COMMON_PATTERNS["age_requirements"])
    return ExtractionUtils.extract_with_patterns(
        text,
        [(p, f"年齢パターン{i+1}") for i, p in enumerate(age_patterns)],
        ExtractionUtils.convert_age_requirements
    )