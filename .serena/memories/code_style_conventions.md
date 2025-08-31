# コードスタイルと規約

## コーディング規約

### 言語
- 日本語でのコメントとドキュメント
- 関数名・変数名は英語（例: `LoanScrapingOrchestrator`）
- ログメッセージは日本語

### Python規約
- Python 3.10以上を使用
- 型ヒント使用推奨（mypyによる型チェック）
- Pydanticモデルでデータ検証
- docstring形式：Google Style（日本語）

```python
def example_function(param: str) -> Dict:
    """
    関数の説明
    
    Args:
        param: パラメータの説明
        
    Returns:
        Dict: 戻り値の説明
    """
```

### ファイル構成規約
- パッケージ構造を重視
- `__init__.py`でモジュール公開
- 設定ファイルは環境変数 + `.env`ファイル

### エラーハンドリング
- ログ出力は日本語
- 例外処理は適切にキャッチ
- リトライメカニズムの実装

### データベース
- SQLAlchemy使用
- マイグレーション管理
- 接続プール設定

### AWS関連
- SAM CLI使用
- Lambda関数の適切な設定
- 環境変数での設定管理

## 命名規則
- クラス名: PascalCase (`LoanScrapingOrchestrator`)
- 関数名: snake_case (`run_all_scrapers`)
- 定数: UPPER_SNAKE_CASE (`DATABASE_AVAILABLE`)
- ファイル名: snake_case (`aoimori_shinkin.py`)