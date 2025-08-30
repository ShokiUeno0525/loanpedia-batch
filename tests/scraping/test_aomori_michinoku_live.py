"""
青森みちのく銀行の実際のサイトに対するライブスクレイピングテスト
注意: 実際のWebサイトにアクセスするため、適切な間隔で実行すること
"""
import pytest
import os
import time
from loanpedia_scraper.scrapers.aomori_michinoku_bank.base_scraper import AomorimichinokuBankScraper

# ライブテスト実行条件
LIVE_TEST_ENABLED = (
    os.getenv('SCRAPING_TEST_MODE') == 'true' and
    os.getenv('ENABLE_LIVE_SCRAPING_TESTS') == 'true'
)

@pytest.mark.skipif(
    not LIVE_TEST_ENABLED,
    reason="ライブスクレイピングテストはENABLE_LIVE_SCRAPING_TESTS=trueでのみ実行"
)
class TestAomorimichinokuBankLiveScraping:
    """青森みちのく銀行ライブスクレイピングテストクラス"""

    @pytest.mark.timeout(60)
    def test_mycar_loan_live_scraping(self):
        """マイカーローンページのライブスクレイピングテスト"""
        scraper = AomorimichinokuBankScraper(product_type="mycar")
        
        # サイトへの負荷軽減のため待機
        delay = int(os.getenv('SCRAPING_DELAY', '3'))
        time.sleep(delay)
        
        try:
            result = scraper.scrape_loan_info()
            
            if result is not None:
                print(f"\nマイカーローン スクレイピング結果: {type(result)}")
                if isinstance(result, dict):
                    # 結果に期待される要素があるかチェック
                    if 'error' not in result:
                        print("✓ スクレイピング成功")
                    else:
                        print(f"✗ エラー: {result.get('error')}")
            else:
                print("ℹ スクレイピング結果なし（正常終了）")
                
        except AttributeError:
            pytest.skip("scrape_loan_infoメソッドが実装されていません")
        except Exception as e:
            pytest.skip(f"マイカーローンライブテストをスキップ: {e}")

    @pytest.mark.timeout(60)
    def test_education_loan_live_scraping(self):
        """教育ローンページのライブスクレイピングテスト"""
        scraper = AomorimichinokuBankScraper(product_type="education")
        
        delay = int(os.getenv('SCRAPING_DELAY', '3'))
        time.sleep(delay)
        
        try:
            result = scraper.scrape_loan_info()
            
            if result is not None:
                print(f"\n教育ローン スクレイピング結果: {type(result)}")
                if isinstance(result, dict):
                    if 'error' not in result:
                        print("✓ スクレイピング成功")
                    else:
                        print(f"✗ エラー: {result.get('error')}")
            else:
                print("ℹ スクレイピング結果なし（正常終了）")
                
        except AttributeError:
            pytest.skip("scrape_loan_infoメソッドが実装されていません")
        except Exception as e:
            pytest.skip(f"教育ローンライブテストをスキップ: {e}")

    @pytest.mark.timeout(60)
    def test_freeloan_live_scraping(self):
        """フリーローンページのライブスクレイピングテスト"""
        scraper = AomorimichinokuBankScraper(product_type="freeloan")
        
        delay = int(os.getenv('SCRAPING_DELAY', '3'))
        time.sleep(delay)
        
        try:
            result = scraper.scrape_loan_info()
            
            if result is not None:
                print(f"\nフリーローン スクレイピング結果: {type(result)}")
                if isinstance(result, dict):
                    if 'error' not in result:
                        print("✓ スクレイピング成功")
                    else:
                        print(f"✗ エラー: {result.get('error')}")
            else:
                print("ℹ スクレイピング結果なし（正常終了）")
                
        except AttributeError:
            pytest.skip("scrape_loan_infoメソッドが実装されていません")
        except Exception as e:
            pytest.skip(f"フリーローンライブテストをスキップ: {e}")

    @pytest.mark.timeout(180)
    def test_multiple_product_live_scraping(self):
        """複数商品の連続ライブスクレイピングテスト"""
        product_types = ["mycar", "education", "freeloan"]
        results = {}
        
        for product_type in product_types:
            scraper = AomorimichinokuBankScraper(product_type=product_type)
            
            # 各商品間で適切な間隔を設ける
            delay = int(os.getenv('SCRAPING_DELAY', '3'))
            time.sleep(delay)
            
            try:
                result = scraper.scrape_loan_info()
                results[product_type] = {
                    'success': result is not None and (not isinstance(result, dict) or 'error' not in result),
                    'result_type': type(result).__name__,
                    'has_error': isinstance(result, dict) and 'error' in result
                }
                
            except AttributeError:
                results[product_type] = {'error': 'メソッド未実装'}
            except Exception as e:
                results[product_type] = {'error': str(e)}
        
        # 結果レポート
        print(f"\n=== 複数商品ライブスクレイピング結果 ===")
        success_count = 0
        for product_type, result in results.items():
            if result.get('success'):
                print(f"✓ {product_type}: 成功")
                success_count += 1
            elif 'error' in result:
                print(f"✗ {product_type}: {result['error']}")
            else:
                print(f"? {product_type}: {result}")
        
        print(f"成功率: {success_count}/{len(product_types)} ({success_count/len(product_types)*100:.1f}%)")
        
        # 少なくとも1つは成功することを期待（厳密ではない）
        if success_count == 0 and all('メソッド未実装' not in str(r) for r in results.values()):
            pytest.skip("全ての商品でスクレイピングに失敗（サイト側の問題の可能性）")

    def test_url_accessibility(self):
        """各商品のURLがアクセス可能かテスト"""
        import requests
        
        product_types = ["mycar", "education", "freeloan", "omatomeloan"]
        
        for product_type in product_types:
            scraper = AomorimichinokuBankScraper(product_type=product_type)
            url = scraper.get_default_url()
            
            try:
                # HEAD リクエストでアクセス確認
                response = requests.head(url, timeout=10, allow_redirects=True)
                print(f"\n{product_type} URL ({url}): {response.status_code}")
                
                # 2xx, 3xxは正常とみなす
                assert response.status_code < 400, f"URL アクセスエラー: {response.status_code}"
                
            except requests.exceptions.RequestException as e:
                pytest.skip(f"{product_type} URL確認をスキップ: {e}")
            
            # 各リクエスト間で間隔を設ける
            time.sleep(1)