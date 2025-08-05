import json
import logging
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, Any

# Lambda環境でScrapyを動的インストール
def ensure_scrapy_installed():
    """Lambda環境でScrapyが使用可能かチェックし、必要に応じてインストール"""
    try:
        import scrapy
        logger.info("Scrapy は既にインストール済みです")
        
        # 追加で必要なライブラリもチェック
        missing_libs = []
        try:
            import pymysql
        except ImportError:
            missing_libs.append("pymysql>=1.1.0")
            
        try:
            import requests
        except ImportError:
            missing_libs.append("requests>=2.32.0")
            
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            missing_libs.append("beautifulsoup4>=4.12.0")
        
        # 不足ライブラリがあれば追加インストール
        if missing_libs:
            logger.info(f"不足ライブラリを追加インストール: {missing_libs}")
            install_path = "/tmp/python_modules"
            os.makedirs(install_path, exist_ok=True)
            
            install_cmd = [
                sys.executable, "-m", "pip", "install"
            ] + missing_libs + [
                "-t", install_path,
                "--no-cache-dir",
                "--disable-pip-version-check"
            ]
            
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=180)
            if result.returncode == 0:
                if install_path not in sys.path:
                    sys.path.insert(0, install_path)
                logger.info("不足ライブラリのインストール完了")
            else:
                logger.warning(f"不足ライブラリのインストール失敗: {result.stderr}")
        else:
            logger.info("必要なライブラリは全て利用可能です")
        
        return True
    except ImportError:
        logger.info("Scrapy がインストールされていません。動的インストールを試行...")
        
        try:
            # /tmp にライブラリをインストール（Lambdaで唯一の書き込み可能ディレクトリ）
            install_path = "/tmp/python_modules"
            os.makedirs(install_path, exist_ok=True)
            
            # pipで必要なライブラリを一括インストール
            install_cmd = [
                sys.executable, "-m", "pip", "install", 
                "scrapy>=2.11.2", 
                "twisted>=22.10.0",
                "lxml>=4.9.0",
                "pymysql>=1.1.0",
                "requests>=2.32.0",
                "beautifulsoup4>=4.12.0",
                "-t", install_path,
                "--no-cache-dir",
                "--disable-pip-version-check"
            ]
            
            logger.info(f"インストールコマンド実行: {' '.join(install_cmd)}")
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # インストールしたパッケージをPythonパスに追加
                if install_path not in sys.path:
                    sys.path.insert(0, install_path)
                
                # 再度インポートを試行
                import scrapy
                logger.info("Scrapy の動的インストールが成功しました")
                return True
            else:
                logger.error(f"Scrapy インストール失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"動的インストール中にエラー: {str(e)}")
            return False

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "loanpedia_scraper", "src"))

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class AoimoriShinkinHandler:
    """青い森信用金庫スクレイピング処理ハンドラー"""

    def __init__(self):
        self.institution_name = "青い森信用金庫"
        self.institution_code = "1250"
        self.base_url = "https://www.aoimorishinkin.co.jp/"
        self.spider_configs = {
            "aoimori_sinkin_mycar": {
                "name": "マイカーローン",
                "priority": 1,
                "required": True,
            }
        }

    def execute_scraping(self) -> Dict[str, Any]:
        """スクレイピング処理の実行（SAMローカルテスト対応）"""
        logger.info(f"{self.institution_name}のスクレイピング処理開始")

        results = {
            "institution": self.institution_name,
            "institution_code": self.institution_code,
            "started_at": datetime.now().isoformat(),
            "spiders": {},
            "total_spiders": len(self.spider_configs),
            "successful_spiders": 0,
            "failed_spiders": 0,
        }

        try:
            # SAMローカル環境では、subprocess でscrapyコマンドを実行
            import subprocess

            for spider_name, config in self.spider_configs.items():
                try:
                    logger.info(
                        f"スパイダー '{spider_name}' ({config['name']}) を実行開始"
                    )

                    # Scrapyコマンドを構築（デバッガー競合回避）
                    scrapy_cmd = [
                        "python",
                        "-Xfrozen_modules=off",  # frozen modules警告を回避
                        "-m",
                        "scrapy",
                        "crawl",
                        spider_name,
                        "-s",
                        "LOG_LEVEL=INFO",
                        "-s",
                        "TELNETCONSOLE_ENABLED=False",  # Telnetコンソール無効化
                    ]
                    
                    # デバッガー関連の環境変数を設定
                    env = os.environ.copy()
                    env['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
                    env['DEBUGPY_RUNNING'] = '0'
                    # デバッガーモジュールを完全に無効化
                    env.pop('DEBUGPY_LAUNCHER_HOST', None)
                    env.pop('DEBUGPY_LAUNCHER_PORT', None)
                    # Pythonパスからデバッガーを除外
                    if 'PYTHONPATH' in env:
                        python_paths = env['PYTHONPATH'].split(':')
                        env['PYTHONPATH'] = ':'.join([p for p in python_paths if 'debugpy' not in p])

                    # 作業ディレクトリをScrapyプロジェクトルートに設定
                    # Lambda環境では /var/task = loanpedia_scraperディレクトリ
                    current_working_dir = os.getcwd()
                    scrapy_project_dir = current_working_dir  # /var/task がScrapyプロジェクトルート

                    logger.info(f"実行コマンド: {' '.join(scrapy_cmd)}")
                    logger.info(f"作業ディレクトリ: {scrapy_project_dir}")
                    logger.info(f"ディレクトリ存在確認: {os.path.exists(scrapy_project_dir)}")
                    
                    # ディレクトリ内容を確認
                    if os.path.exists(scrapy_project_dir):
                        try:
                            contents = os.listdir(scrapy_project_dir)
                            logger.info(f"ディレクトリ内容: {contents}")
                        except Exception as e:
                            logger.error(f"ディレクトリ内容確認エラー: {str(e)}")
                    else:
                        # 代替パスを試す
                        alt_paths = [
                            "/var/task",
                            "/var/task/loanpedia_scraper", 
                            "/opt/python/loanpedia_scraper",
                            current_working_dir
                        ]
                        for alt_path in alt_paths:
                            if os.path.exists(alt_path):
                                alt_contents = os.listdir(alt_path) if os.path.isdir(alt_path) else "Not a directory"
                                logger.info(f"代替パス {alt_path}: {alt_contents}")
                        
                        # 最終的に現在の作業ディレクトリを使用
                        scrapy_project_dir = current_working_dir
                        logger.info(f"フォールバック: 作業ディレクトリを {scrapy_project_dir} に設定")

                    # Scrapyスパイダーを実行（環境変数付き）
                    result = subprocess.run(
                        scrapy_cmd,
                        cwd=scrapy_project_dir,
                        capture_output=True,
                        text=True,
                        timeout=600,  # 10分でタイムアウト
                        env=env  # デバッガー競合回避の環境変数
                    )

                    if result.returncode == 0:
                        logger.info(f"スパイダー '{spider_name}' 実行成功")
                        results["spiders"][spider_name] = {
                            "name": config["name"],
                            "status": "completed",
                            "priority": config["priority"],
                            "stdout": result.stdout[-500:]
                            if result.stdout
                            else "",  # 最後の500文字のみ
                            "stderr": result.stderr[-500:] if result.stderr else "",
                        }
                        results["successful_spiders"] += 1
                    else:
                        # Scrapyが失敗した場合、軽量な代替手段を試行
                        logger.warning(f"Scrapy実行失敗。代替手段を試行: {result.stderr}")
                        fallback_result = self.run_fallback_scraping(spider_name, config)
                        results["spiders"][spider_name] = fallback_result
                        
                        if fallback_result["status"] == "completed":
                            results["successful_spiders"] += 1
                        else:
                            results["failed_spiders"] += 1

                except subprocess.TimeoutExpired:
                    logger.error(f"スパイダー '{spider_name}' がタイムアウトしました")
                    results["spiders"][spider_name] = {
                        "name": config["name"],
                        "status": "timeout",
                        "error": "タイムアウト（10分）",
                    }
                    results["failed_spiders"] += 1

                except Exception as e:
                    logger.error(f"スパイダー '{spider_name}' の実行でエラー: {str(e)}")
                    results["spiders"][spider_name] = {
                        "name": config["name"],
                        "status": "error",
                        "error": str(e),
                    }
                    results["failed_spiders"] += 1

            results["completed_at"] = datetime.now().isoformat()

            if results["failed_spiders"] == 0:
                results["overall_status"] = "success"
            elif results["successful_spiders"] > 0:
                results["overall_status"] = "partial_success"
            else:
                results["overall_status"] = "error"

            return results

        except Exception as e:
            logger.error(f"スクレイピング処理全体でエラー: {str(e)}")
            results["completed_at"] = datetime.now().isoformat()
            results["overall_status"] = "error"
            results["error"] = str(e)
            return results

    def run_fallback_scraping(self, spider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrapyが使えない場合の軽量代替スクレイピング"""
        logger.info(f"軽量スクレイピングを実行: {spider_name}")
        
        try:
            # requestsとBeautifulSoupを使用した軽量スクレイピング
            import requests
            from bs4 import BeautifulSoup
            import hashlib
            
            # 青い森信用金庫の基本情報
            if spider_name == "aoimori_sinkin_mycar":
                urls = [
                    "https://www.aoimorishinkin.co.jp/loan/car/",
                    "https://www.aoimorishinkin.co.jp/"
                ]
                
                scraped_data = []
                
                for url in urls:
                    try:
                        logger.info(f"軽量スクレイピング実行: {url}")
                        response = requests.get(url, timeout=30)
                        response.raise_for_status()
                        
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # 基本的なデータ抽出
                        loan_data = {
                            "institution_name": "青い森信用金庫",
                            "institution_code": "1250", 
                            "product_name": "青い森しんきんカーライフプラン",
                            "loan_category": "マイカーローン",
                            "source_url": url,
                            "scraped_at": datetime.now().isoformat(),
                            "page_title": soup.title.string if soup.title else "N/A",
                            "method": "fallback_requests",
                            "content_hash": hashlib.md5(response.text.encode()).hexdigest(),
                            "raw_html": response.text  # HTMLコンテンツも保存
                        }
                        
                        # 金利情報の簡単な抽出
                        text_content = soup.get_text()
                        if "金利" in text_content or "%" in text_content:
                            import re
                            rates = re.findall(r'(\d+\.\d+)%', text_content)
                            if rates:
                                loan_data["interest_rates_found"] = rates[:5]  # 最初の5つまで
                        
                        scraped_data.append(loan_data)
                        
                    except Exception as e:
                        logger.warning(f"URL {url} のスクレイピング失敗: {str(e)}")
                        continue
                
                if scraped_data:
                    logger.info(f"軽量スクレイピング成功: {len(scraped_data)}件のデータを取得")
                    
                    # データベースに保存を試行
                    saved_count = self.save_to_database(scraped_data)
                    
                    return {
                        "name": config["name"],
                        "status": "completed",
                        "method": "fallback_requests",
                        "data_count": len(scraped_data),
                        "saved_to_db": saved_count,
                        "sample_data": scraped_data[0] if scraped_data else None
                    }
                else:
                    return {
                        "name": config["name"],
                        "status": "error", 
                        "error": "軽量スクレイピングでもデータ取得に失敗"
                    }
                    
        except ImportError:
            return {
                "name": config["name"],
                "status": "error",
                "error": "requestsまたはBeautifulSoupが利用できません"
            }
        except Exception as e:
            logger.error(f"軽量スクレイピングでエラー: {str(e)}")
            return {
                "name": config["name"],
                "status": "error", 
                "error": f"軽量スクレイピングエラー: {str(e)}"
            }
    
    def save_to_database(self, scraped_data: list) -> int:
        """軽量スクレイピングで取得したデータをデータベースに保存"""
        try:
            import pymysql
            import json
            from datetime import datetime
            
            # データベース設定（環境変数または設定から取得）
            db_config = {
                'host': os.environ.get('DATABASE_HOST', 'localhost'),
                'user': os.environ.get('DATABASE_USER', 'root'),
                'password': os.environ.get('DATABASE_PASSWORD', 'rootpassword'),
                'database': os.environ.get('DATABASE_NAME', 'app_db'),
                'port': int(os.environ.get('DATABASE_PORT', '3307')),
                'charset': 'utf8mb4'
            }
            
            logger.info(f"データベース接続試行: {db_config['host']}:{db_config['port']}")
            
            # データベース接続
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()
            
            saved_count = 0
            
            for data in scraped_data:
                try:
                    # 金融機関IDを取得または作成
                    institution_id = self.get_or_create_institution_direct(
                        cursor, 
                        data.get('institution_code', ''),
                        data.get('institution_name', '')
                    )
                    
                    # 生データを保存
                    html_content = data.get('raw_html', '')
                    content_hash = data.get('content_hash', '')
                    
                    # 重複チェック
                    check_sql = "SELECT id FROM raw_loan_data WHERE content_hash = %s"
                    cursor.execute(check_sql, (content_hash,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        logger.info(f"重複データのためスキップ: {content_hash[:8]}...")
                        continue
                    
                    # 新規保存
                    insert_sql = """
                        INSERT INTO raw_loan_data (
                            institution_id, source_url, page_title, html_content, 
                            structured_data, content_hash, content_length, scraped_at, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    now = datetime.now()
                    
                    cursor.execute(insert_sql, (
                        institution_id,
                        data.get('source_url', ''),
                        data.get('page_title', ''),
                        html_content,
                        json.dumps(data, ensure_ascii=False),
                        content_hash,
                        len(html_content) if html_content else 0,
                        data.get('scraped_at', now),
                        now,
                        now
                    ))
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"個別データ保存エラー: {str(e)}")
                    continue
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info(f"データベース保存完了: {saved_count}件")
            return saved_count
            
        except ImportError:
            logger.warning("pymysql が利用できないため、データベース保存をスキップ")
            return 0
        except Exception as e:
            logger.error(f"データベース保存エラー: {str(e)}")
            return 0
    
    def get_or_create_institution_direct(self, cursor, institution_code, institution_name):
        """直接データベース操作で金融機関IDを取得または作成"""
        if not institution_code and not institution_name:
            return None
            
        # 既存の金融機関を検索
        select_sql = """
            SELECT id FROM financial_institutions 
            WHERE institution_code = %s OR institution_name = %s
            LIMIT 1
        """
        cursor.execute(select_sql, (institution_code, institution_name))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # 新規作成
        insert_sql = """
            INSERT INTO financial_institutions (institution_code, institution_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
        """
        now = datetime.now()
        cursor.execute(insert_sql, (institution_code, institution_name, now, now))
        return cursor.lastrowid


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda用のメインハンドラー（SAMローカルテスト対応）

    使用方法:
    sam local invoke AoimoriShinkinScraperFunction
    sam local invoke AoimoriShinkinScraperFunction --event events/test_event.json

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Dict containing execution results
    """
    logger.info("青い森信用金庫ローン情報スクレイピング処理開始")
    logger.info(f"Event: {json.dumps(event, ensure_ascii=False)}")

    # 環境情報をログ出力（デバッグ用）
    logger.info(f"Python path: {sys.path[:3]}...")  # 最初の3つのパスのみ表示
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Handler file location: {__file__}")

    # Scrapyの動的インストールを確認
    if not ensure_scrapy_installed():
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Scrapyのインストールに失敗しました",
                "institution": "青い森信用金庫",
                "institution_code": "1250",
                "error": "Scrapy installation failed",
                "status": "error"
            }, ensure_ascii=False, indent=2)
        }

    try:
        # ハンドラーインスタンス作成
        handler = AoimoriShinkinHandler()

        # スクレイピング実行
        results = handler.execute_scraping()

        # レスポンス作成
        if results["overall_status"] == "success":
            status_code = 200
            message = f"{handler.institution_name}のローン情報スクレイピング処理が正常に完了しました"
        elif results["overall_status"] == "partial_success":
            status_code = 207  # Multi-Status
            message = (
                f"{handler.institution_name}のスクレイピング処理が部分的に完了しました"
            )
        else:
            status_code = 500
            message = (
                f"{handler.institution_name}のスクレイピング処理でエラーが発生しました"
            )

        response = {
            "statusCode": status_code,
            "body": json.dumps(
                {"message": message, "results": results}, ensure_ascii=False, indent=2
            ),
        }

        logger.info(f"レスポンス: {json.dumps(response, ensure_ascii=False, indent=2)}")
        return response

    except Exception as e:
        logger.error(f"Lambda handler でエラーが発生: {str(e)}")
        logger.error("エラー詳細: ", exc_info=True)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "青い森信用金庫のスクレイピング処理で予期しないエラーが発生しました",
                    "institution": "青い森信用金庫",
                    "institution_code": "1250",
                    "error": str(e),
                    "status": "error",
                },
                ensure_ascii=False,
                indent=2,
            ),
        }


# ローカル実行用（SAM外でのテスト）
if __name__ == "__main__":
    # ローカルテスト用
    test_event = {"test": True}
    test_context = None

    print("=== ローカルテスト実行 ===")
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2, ensure_ascii=False))
