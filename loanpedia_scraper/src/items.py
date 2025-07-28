# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join
import re

def clean_text(value):
    """テキストのクリーニング"""
    if value:
        return re.sub(r'\s+', ' ', value.strip())
    return value

def extract_number(value):
    """数値の抽出"""
    if value:
        numbers = re.findall(r'\d+\.?\d*', value.replace(',', ''))
        return float(numbers[0]) if numbers else None
    return None

class LoanItem(scrapy.Item):
    # 基本情報
    institution_code = scrapy.Field(output_processor=TakeFirst())
    institution_name = scrapy.Field(output_processor=TakeFirst())
    source_url = scrapy.Field(output_processor=TakeFirst())
    page_title = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    content_hash = scrapy.Field(output_processor=TakeFirst())
    
    # 商品情報
    product_name = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    loan_category = scrapy.Field(output_processor=TakeFirst())
    
    # 金利情報
    min_interest_rate = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    max_interest_rate = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    interest_rate_type = scrapy.Field(output_processor=TakeFirst())
    
    # 融資条件
    min_loan_amount = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    max_loan_amount = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    min_loan_period_months = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    max_loan_period_months = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    
    # 申込要件
    min_age = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    max_age = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    income_requirement = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    guarantor_required = scrapy.Field(output_processor=TakeFirst())
    
    # 手数料・保証料情報
    guarantor_fee = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    handling_fee = scrapy.Field(
        input_processor=MapCompose(extract_number),
        output_processor=TakeFirst()
    )
    application_conditions = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # アコーディオン内の詳細情報
    prepayment_fee = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    application_method = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    required_documents = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    guarantor_info = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    collateral_info = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # その他
    features = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(', ')
    )
    required_documents = scrapy.Field()
    application_method = scrapy.Field()
    repayment_method = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    
    # メタデータ
    html_content = scrapy.Field(output_processor=TakeFirst())
    extracted_text = scrapy.Field(output_processor=TakeFirst())
    scraped_at = scrapy.Field(output_processor=TakeFirst())