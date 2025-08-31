#!/usr/bin/env python3
"""
データベース初期化スクリプト
テーブル作成とサンプルデータの投入を行います。
"""

import sys
import os
import pymysql
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class DatabaseInitializer:
    def __init__(self, host='localhost', user='root', password='rootpassword', database='app_db', port=3307):
        self.connection_params = {
            'host': host,
            'user': user,
            'password': password,
            'port': port,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self.database = database
        self.port = port
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """データベースに接続（データベースが存在しない場合は作成）"""
        try:
            # まずデータベースなしで接続
            self.connection = pymysql.connect(**self.connection_params)
            self.cursor = self.connection.cursor()
            
            # データベースを作成
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            self.cursor.execute(f"USE {self.database}")
            
            print(f"✓ データベース '{self.database}' に接続しました")
            return True
            
        except Exception as e:
            print(f"✗ データベース接続エラー: {e}")
            return False
    
    def close(self):
        """データベース接続を閉じる"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✓ データベース接続を閉じました")
    
    def execute_sql_file(self, sql_file_path):
        """SQLファイルを実行"""
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            # SQLをステートメントごとに分割して実行
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    self.cursor.execute(statement)
            
            self.connection.commit()
            print(f"✓ SQLファイル '{sql_file_path}' を実行しました")
            return True
            
        except Exception as e:
            print(f"✗ SQLファイル実行エラー: {e}")
            self.connection.rollback()
            return False
    
    def check_tables(self):
        """テーブルの存在確認"""
        try:
            self.cursor.execute("SHOW TABLES")
            tables = [row[f'Tables_in_{self.database}'] for row in self.cursor.fetchall()]
            
            expected_tables = [
                'financial_institutions',
                'data_sources',
                'raw_loan_data',
                'processed_loan_data',
                'loan_products',
                'loan_product_history'
            ]
            
            print("\\n📋 テーブル一覧:")
            for table in expected_tables:
                if table in tables:
                    # レコード数を取得
                    self.cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = self.cursor.fetchone()['count']
                    print(f"  ✓ {table} ({count} records)")
                else:
                    print(f"  ✗ {table} (not found)")
            
            return len([t for t in expected_tables if t in tables]) == len(expected_tables)
            
        except Exception as e:
            print(f"✗ テーブル確認エラー: {e}")
            return False
    
    def test_connection(self):
        """接続テスト"""
        try:
            self.cursor.execute("SELECT 1 as test")
            result = self.cursor.fetchone()
            if result['test'] == 1:
                print("✓ データベース接続テスト成功")
                return True
            return False
        except Exception as e:
            print(f"✗ 接続テストエラー: {e}")
            return False

def main():
    print("🚀 ローンペディア データベース初期化開始\\n")
    
    # データベース接続情報（環境変数から取得可能）
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'rootpassword'),
        'database': os.getenv('DB_NAME', 'app_db'),
        'port': int(os.getenv('DB_PORT', '3307'))
    }
    
    print("📊 データベース設定:")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  User: {db_config['user']}")
    print(f"  Database: {db_config['database']}")
    print()
    
    # 初期化実行
    initializer = DatabaseInitializer(**db_config)
    
    try:
        # 1. データベース接続
        if not initializer.connect():
            return False
        
        # 2. 接続テスト
        if not initializer.test_connection():
            return False
        
        # 3. SQLファイル実行
        sql_file = Path(__file__).parent / 'create_tables.sql'
        if not sql_file.exists():
            print(f"✗ SQLファイルが見つかりません: {sql_file}")
            return False
        
        if not initializer.execute_sql_file(sql_file):
            return False
        
        # 4. テーブル確認
        if not initializer.check_tables():
            print("\\n⚠️  一部のテーブルが作成されていません")
            return False
        
        print("\\n🎉 データベース初期化が完了しました！")
        print("\\n📝 次のステップ:")
        print("  1. docker-compose up -d でMySQLを起動")
        print("  2. スクレイピングを実行: cd loanpedia_scraper && scrapy crawl spider_name")
        print("  3. データが正常に保存されることを確認")
        
        return True
        
    except Exception as e:
        print(f"\\n💥 予期せぬエラーが発生しました: {e}")
        return False
        
    finally:
        initializer.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)