"""
テスト設定とフィクスチャ定義
実際の実装機能をテストするための設定
"""
import os
import pytest
import sys
from unittest.mock import Mock
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト環境の設定
os.environ['SCRAPING_TEST_MODE'] = 'true'
os.environ['MYSQL_HOST'] = os.getenv('MYSQL_HOST', '127.0.0.1')
os.environ['MYSQL_PORT'] = os.getenv('MYSQL_PORT', '3306')
os.environ['MYSQL_USER'] = os.getenv('MYSQL_USER', 'test_user')
os.environ['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'test_password')
os.environ['MYSQL_DATABASE'] = os.getenv('MYSQL_DATABASE', 'test_loanpedia')

@pytest.fixture
def mock_database_config():
    """データベース設定のモックフィクスチャ"""
    return {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', 'test_user'),
        'password': os.getenv('MYSQL_PASSWORD', 'test_password'),
        'database': os.getenv('MYSQL_DATABASE', 'test_loanpedia')
    }

@pytest.fixture
def mock_http_response():
    """HTTPレスポンスのモックフィクスチャ"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
    mock_response.encoding = 'utf-8'
    mock_response.url = "https://example.com/test"
    return mock_response

@pytest.fixture
def sample_mycar_html():
    """マイカーローンページのサンプルHTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>マイカーローン | 青森みちのく銀行</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>マイカーローン</h1>
        <div class="loan-details">
            <p>金利：年2.8%～3.8%（変動金利）</p>
            <p>融資金額：10万円以上1,000万円以内（1万円単位）</p>
            <p>融資期間：6ヶ月以上10年以内（1ヶ月単位）</p>
            <p>年齢：満20歳以上満65歳未満の方</p>
            <p>返済方法：元利均等毎月返済（ボーナス併用返済も可能）</p>
        </div>
        <div class="features">
            <h3>商品の特徴</h3>
            <ul>
                <li>新車・中古車の購入資金</li>
                <li>バイクの購入資金</li>
                <li>車検・修理費用</li>
                <li>免許取得費用</li>
            </ul>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def sample_education_html():
    """教育ローンページのサンプルHTML"""
    return """
    <html>
    <head><title>教育ローン | 青森みちのく銀行</title></head>
    <body>
        <h1>教育ローン（証書貸付型）</h1>
        <table>
            <tr><td>金利</td><td>年2.3%～3.8%（変動金利）</td></tr>
            <tr><td>融資金額</td><td>10万円以上500万円以内</td></tr>
            <tr><td>融資期間</td><td>1年以上15年以内</td></tr>
            <tr><td>年齢</td><td>満20歳以上満65歳未満</td></tr>
        </table>
    </body>
    </html>
    """

@pytest.fixture
def sample_freeloan_html():
    """フリーローンページのサンプルHTML"""
    return """
    <html>
    <body>
        <h1>フリーローン</h1>
        <div>
            <p>金利：年6.8%～14.5%</p>
            <p>融資額：10万円～500万円</p>
            <p>期間：6ヶ月～7年</p>
            <p>自由な用途にご利用いただけます</p>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def minimal_html():
    """最小限のHTMLコンテンツ"""
    return """
    <html>
    <body>
        <h1>テストローン</h1>
        <p>テスト用のローン商品です</p>
    </body>
    </html>
    """

@pytest.fixture
def malformed_html():
    """不正なHTMLコンテンツ"""
    return """
    <div>
        <h1>不完全なローン情報
        <p>金利：年
        <p>融資額：
    </div>
    """

@pytest.fixture
def empty_html():
    """空のHTMLコンテンツ"""
    return "<html><body></body></html>"

@pytest.fixture(autouse=True)
def setup_test_logging():
    """テスト用ログ設定（全テスト自動適用）"""
    import logging
    
    # テスト時は警告レベル以上のみ表示
    logging.basicConfig(
        level=logging.WARNING,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    # テスト対象モジュールのログレベルを設定
    test_loggers = [
        'loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper',
        'loanpedia_scraper.scrapers.aomori_michinoku_bank.html_parser'
    ]
    
    for logger_name in test_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
    
    yield

@pytest.fixture
def mock_scraper_success():
    """成功を返すスクレイパーモック"""
    m = Mock()
    m.scrape_loan_info.return_value = {'status': 'success'}
    return m

@pytest.fixture
def mock_scraper_failure():
    """例外を投げるスクレイパーモック"""
    m = Mock()
    m.scrape_loan_info.side_effect = Exception("mock failure")
    return m

@pytest.fixture
def mock_successful_response(sample_mycar_html):
    """成功するHTTPレスポンスのモック"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = sample_mycar_html.encode('utf-8')
    mock_response.url = "https://www.am-bk.co.jp/kojin/loan/mycarloan/"
    mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
    return mock_response

@pytest.fixture
def mock_error_response():
    """エラーレスポンスのモック"""
    import requests
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    return mock_response

@pytest.fixture
def mock_timeout_error():
    """タイムアウトエラーのモック"""
    import requests
    return requests.Timeout("Request timeout")

@pytest.fixture
def sample_loan_data():
    """サンプルローンデータ"""
    return {
        'institution_name': '青森みちのく銀行',
        'institution_code': '0117',
        'product_type': 'mycar',
        'product_name': 'マイカーローン',
        'loan_type': 'マイカーローン',
        'loan_category': '目的別ローン',
        'min_interest_rate': 2.8,
        'max_interest_rate': 3.8,
        'min_loan_amount': 100000,
        'max_loan_amount': 10000000,
        'min_loan_term_months': 6,
        'max_loan_term_months': 120,
        'min_age': 20,
        'max_age': 65,
        'repayment_method': '元利均等毎月返済'
    }

# pytest設定
def pytest_configure(config):
    """pytest設定"""
    # カスタムマーカーの登録
    config.addinivalue_line(
        "markers", "unit: Unit tests - fast tests with mocks"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests - may require database"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that may take longer to run"
    )

# テストコレクション設定
def pytest_collection_modifyitems(config, items):
    """テストアイテムにマーカーを自動追加"""
    for item in items:
        # ファイルパスに基づいてマーカーを追加
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "scraping" in str(item.fspath):
            item.add_marker(pytest.mark.slow)

# テスト実行前の追加検証
@pytest.fixture(autouse=True)
def validate_test_environment():
    """テスト環境の妥当性確認"""
    # 必要な環境変数が設定されていることを確認
    required_env_vars = ['SCRAPING_TEST_MODE']
    for var in required_env_vars:
        if not os.getenv(var):
            pytest.skip(f"Required environment variable {var} not set")
    
    # プロジェクト構造の基本確認
    if not (project_root / 'loanpedia_scraper').exists():
        pytest.skip("loanpedia_scraper directory not found")
    
    yield
