"""
LoanScrapingOrchestratorのユニットテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from loanpedia_scraper.scrapers.main import LoanScrapingOrchestrator


class TestLoanScrapingOrchestrator:
    """LoanScrapingOrchestratorのテストクラス"""

    def test_init_with_database(self, mock_database_config):
        """データベース有効でのオーケストレーター初期化テスト"""
        with patch('loanpedia_scraper.scrapers.main.DATABASE_AVAILABLE', True), \
             patch('loanpedia_scraper.scrapers.main.get_database_config', return_value=mock_database_config):
            orchestrator = LoanScrapingOrchestrator(save_to_db=True)
            
            assert orchestrator.save_to_db is True
            assert len(orchestrator.scrapers) == 4
            assert 'aomori_michinoku' in orchestrator.scrapers
            assert 'aoimori_shinkin' in orchestrator.scrapers
            assert 'touou_shinkin' in orchestrator.scrapers
            assert 'aomoriken_shinyoukumiai' in orchestrator.scrapers

    def test_init_without_database(self):
        """データベース無効でのオーケストレーター初期化テスト"""
        orchestrator = LoanScrapingOrchestrator(save_to_db=False)
        
        assert orchestrator.save_to_db is False
        assert len(orchestrator.scrapers) == 4
        assert orchestrator.results == []
        assert orchestrator.errors == []

    def test_get_available_scrapers(self):
        """利用可能スクレイパー一覧取得テスト"""
        orchestrator = LoanScrapingOrchestrator()
        scrapers = orchestrator.get_available_scrapers()
        
        expected_scrapers = ['aomori_michinoku', 'aoimori_shinkin', 'touou_shinkin', 'aomoriken_shinyoukumiai']
        assert sorted(scrapers) == sorted(expected_scrapers)

    @patch('loanpedia_scraper.scrapers.main.logger')
    def test_run_single_scraper_success(self, mock_logger, mock_scraper_success):
        """単一スクレイパー実行成功テスト"""
        orchestrator = LoanScrapingOrchestrator()
        orchestrator.scrapers['test_bank'] = mock_scraper_success
        
        result = orchestrator.run_single_scraper('test_bank')
        
        assert result is not None
        assert result['status'] == 'success'
        mock_logger.info.assert_called()

    @patch('loanpedia_scraper.scrapers.main.logger')
    def test_run_single_scraper_failure(self, mock_logger, mock_scraper_failure):
        """単一スクレイパー実行失敗テスト"""
        orchestrator = LoanScrapingOrchestrator()
        orchestrator.scrapers['failing_bank'] = mock_scraper_failure
        
        result = orchestrator.run_single_scraper('failing_bank')
        
        assert result is None
        mock_logger.error.assert_called()

    @patch('loanpedia_scraper.scrapers.main.logger')
    def test_run_single_scraper_not_found(self, mock_logger):
        """存在しないスクレイパー指定テスト"""
        orchestrator = LoanScrapingOrchestrator()
        
        result = orchestrator.run_single_scraper('non_existent_bank')
        
        assert result is None
        mock_logger.error.assert_called_with('指定された金融機関が見つかりません: non_existent_bank')

    @patch('loanpedia_scraper.scrapers.main.logger')
    @patch('loanpedia_scraper.scrapers.main.datetime')
    def test_run_all_scrapers_success(self, mock_datetime, mock_logger):
        """全スクレイパー実行成功テスト"""
        # datetimeのモック設定
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 1, 30)
        mock_datetime.now.side_effect = [start_time, end_time]
        
        orchestrator = LoanScrapingOrchestrator()
        
        # 成功するモックスクレイパーを設定
        success_result = {'status': 'success', 'data': 'test'}
        for name in orchestrator.scrapers.keys():
            mock_scraper = Mock()
            mock_scraper.scrape_loan_info.return_value = success_result
            orchestrator.scrapers[name] = mock_scraper
        
        result = orchestrator.run_all_scrapers()
        
        assert result['success_count'] == 4
        assert result['error_count'] == 0
        assert result['duration_seconds'] == 90.0
        assert len(result['results']) == 4
        assert len(result['errors']) == 0

    @patch('loanpedia_scraper.scrapers.main.logger')
    @patch('loanpedia_scraper.scrapers.main.datetime')
    def test_run_all_scrapers_mixed_results(self, mock_datetime, mock_logger):
        """全スクレイパー実行（成功・失敗混在）テスト"""
        start_time = datetime(2024, 1, 1, 10, 0, 0)
        end_time = datetime(2024, 1, 1, 10, 2, 0)
        mock_datetime.now.side_effect = [start_time, end_time]
        
        orchestrator = LoanScrapingOrchestrator()
        
        # 成功と失敗のモックを混在させる
        scraper_names = list(orchestrator.scrapers.keys())
        for i, name in enumerate(scraper_names):
            mock_scraper = Mock()
            if i % 2 == 0:  # 偶数番目は成功
                mock_scraper.scrape_loan_info.return_value = {'status': 'success'}
            else:  # 奇数番目は失敗
                mock_scraper.scrape_loan_info.side_effect = Exception(f"エラー: {name}")
            orchestrator.scrapers[name] = mock_scraper
        
        result = orchestrator.run_all_scrapers()
        
        assert result['success_count'] == 2
        assert result['error_count'] == 2
        assert result['duration_seconds'] == 120.0
        assert len(result['results']) == 2
        assert len(result['errors']) == 2

    @patch('loanpedia_scraper.scrapers.main.logger')
    def test_run_all_scrapers_all_failures(self, mock_logger):
        """全スクレイパー実行全失敗テスト"""
        orchestrator = LoanScrapingOrchestrator()
        
        # 全て失敗するモックを設定
        for name in orchestrator.scrapers.keys():
            mock_scraper = Mock()
            mock_scraper.scrape_loan_info.side_effect = Exception(f"エラー: {name}")
            orchestrator.scrapers[name] = mock_scraper
        
        result = orchestrator.run_all_scrapers()
        
        assert result['success_count'] == 0
        assert result['error_count'] == 4
        assert len(result['results']) == 0
        assert len(result['errors']) == 4

    def test_orchestrator_state_management(self):
        """オーケストレーターの状態管理テスト"""
        orchestrator = LoanScrapingOrchestrator()
        
        # 初期状態の確認
        assert orchestrator.results == []
        assert orchestrator.errors == []
        
        # 結果を手動で追加
        orchestrator.results.append({'test': 'data'})
        orchestrator.errors.append('test error')
        
        assert len(orchestrator.results) == 1
        assert len(orchestrator.errors) == 1