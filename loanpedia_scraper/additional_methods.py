def extract_fees(self, response):
    """保証料・手数料情報を抽出"""
    import re
    
    text = response.text
    guarantor_fee = None
    handling_fee = None
    
    # 保証料パターン
    guarantor_patterns = [
        r'保証料.*?(\d+(?:\.\d+)?)[%％]',
        r'保証料.*?無料',
        r'保証料.*?不要',
        r'保証料.*?なし',
    ]
    
    for pattern in guarantor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if '無料' in match.group(0) or '不要' in match.group(0) or 'なし' in match.group(0):
                guarantor_fee = 0.0
                self.logger.info(f"✅ 保証料: 無料")
            else:
                guarantor_fee = float(match.group(1))
                self.logger.info(f"✅ 保証料: {guarantor_fee}%")
            break
    
    # 手数料パターン  
    handling_patterns = [
        r'手数料.*?(\d+(?:,\d{3})*)\s*円',
        r'事務手数料.*?(\d+(?:,\d{3})*)\s*円',  
        r'手数料.*?無料',
        r'手数料.*?不要',
    ]
    
    for pattern in handling_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if '無料' in match.group(0) or '不要' in match.group(0):
                handling_fee = 0
                self.logger.info(f"✅ 手数料: 無料")
            else:
                fee_str = match.group(1).replace(',', '')
                handling_fee = int(fee_str)
                self.logger.info(f"✅ 手数料: {handling_fee}円")
            break
    
    return guarantor_fee, handling_fee

def extract_application_conditions(self, response):
    """申込条件・資格要件を抽出"""
    import re
    
    conditions = []
    text = response.text
    
    # 年齢条件
    age_patterns = [
        r'(\d+)歳以上.*?(\d+)歳以下',
        r'満(\d+)歳以上.*?満(\d+)歳以下',
        r'(\d+)歳以上',
        r'満(\d+)歳以上',
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:
                conditions.append(f"年齢: {match.group(1)}歳以上{match.group(2)}歳以下")
            else:
                conditions.append(f"年齢: {match.group(1)}歳以上")
            break
    
    # 年収条件
    income_patterns = [
        r'年収.*?(\d+)万円以上',
        r'年間収入.*?(\d+)万円以上',
        r'前年度年収.*?(\d+)万円以上',
    ]
    
    for pattern in income_patterns:
        match = re.search(pattern, text)
        if match:
            conditions.append(f"年収: {match.group(1)}万円以上")
            break
    
    # 勤続年数条件
    employment_patterns = [
        r'勤続.*?(\d+)年以上',
        r'継続勤務.*?(\d+)年以上',
    ]
    
    for pattern in employment_patterns:
        match = re.search(pattern, text)
        if match:
            conditions.append(f"勤続年数: {match.group(1)}年以上")
            break
    
    # その他の条件
    other_conditions = [
        r'安定.*?継続.*?収入',
        r'保証会社.*?保証.*?受けられる',
        r'当行.*?営業区域内.*?居住',
    ]
    
    for pattern in other_conditions:
        if re.search(pattern, text):
            if '安定' in pattern and '収入' in pattern:
                conditions.append("安定継続した収入があること")
            elif '保証会社' in pattern:
                conditions.append("保証会社の保証が受けられること")
            elif '営業区域' in pattern:
                conditions.append("当行営業区域内に居住または勤務していること")
    
    condition_text = "、".join(conditions) if conditions else None
    if condition_text:
        self.logger.info(f"✅ 申込条件: {condition_text}")
    
    return condition_text

def extract_repayment_method(self, response):
    """返済方法・返済日を抽出"""
    import re
    
    text = response.text
    repayment_info = []
    
    # 返済方法
    method_patterns = [
        r'元利均等返済',
        r'元金均等返済', 
        r'毎月返済',
        r'元利均等.*?毎月返済',
    ]
    
    for pattern in method_patterns:
        if re.search(pattern, text):
            repayment_info.append("元利均等毎月返済")
            break
    
    # 返済日
    date_patterns = [
        r'毎月(\d+)日',
        r'(\d+)日.*?返済',
        r'返済日.*?(\d+)日',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            repayment_info.append(f"毎月{match.group(1)}日返済")
            break
    
    # ボーナス併用
    if re.search(r'ボーナス.*?併用', text):
        repayment_info.append("ボーナス併用返済可能")
    
    repayment_text = "、".join(repayment_info) if repayment_info else None
    if repayment_text:
        self.logger.info(f"✅ 返済方法: {repayment_text}")
    
    return repayment_text