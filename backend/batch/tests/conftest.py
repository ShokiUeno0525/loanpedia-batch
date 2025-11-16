"""
テスト設定とフィクスチャ定義
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

@pytest.fixture
def mock_database_config():
    """データベース設定のモックフィクスチャ"""
    return {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'test_user',
        'password': 'test_password',
        'database': 'test_loanpedia'
    }

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

@pytest.fixture(autouse=True)
def setup_test_logging():
    """テスト用ログ設定（全テスト自動適用）"""
    import logging
    
    # テスト時は警告レベル以上のみ表示
    logging.basicConfig(
        level=logging.WARNING,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    yield

# pytest設定
def pytest_configure(config):
    """pytest設定"""
    # カスタムマーカーの登録
    config.addinivalue_line(
        "markers", "unit: Unit tests - fast tests with mocks"
    )

# テストコレクション設定
def pytest_collection_modifyitems(config, items):
    """テストアイテムにマーカーを自動追加"""
    for item in items:
        # ファイルパスに基づいてマーカーを追加
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)