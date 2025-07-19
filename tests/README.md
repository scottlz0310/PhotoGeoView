# PhotoGeoView テストスイート

このディレクトリには、PhotoGeoViewアプリケーションのテストファイルが含まれています。

## 📋 テストルール

✅ **ルートにtestファイル、Debugファイルを置かない**
✅ **print文でdebugしない**
✅ **絶対パスで参照しない**

## 🧪 テストファイル構成

### 単体テスト
- `test_exif_parser.py` - EXIF解析モジュールのテスト
- `test_map_viewer.py` - 地図ビューアーモジュールのテスト
- `test_image_loader.py` - 画像ローダーモジュールのテスト
- `test_theme_manager.py` - テーママネージャーモジュールのテスト

### 統合テスト
- `integration_test.py` - 全モジュール統合テスト（GUIテスト）
- `simple_test.py` - 簡易統合テスト

### テストユーティリティ
- `run_tests.py` - テストランナー
- `test_config.json` - テスト用設定ファイル

## 🚀 テストの実行方法

### すべてのテストを実行
```bash
cd tests
python run_tests.py all
```

### 特定のテストを実行
```bash
cd tests
python run_tests.py specific test_exif_parser
python run_tests.py specific test_theme_manager.TestThemeManager
```

### 統合テストを実行
```bash
cd tests
python run_tests.py integration
```

### GUI統合テストを実行
```bash
cd tests
python integration_test.py
```

## 📊 テスト結果

テスト実行後、以下の情報が表示されます：
- 実行したテスト数
- 失敗したテスト数
- エラーが発生したテスト数
- スキップされたテスト数
- 詳細なエラー情報

## 🔧 テスト環境

### 必要な依存関係
- Python 3.8以上
- PyQt6
- unittest (標準ライブラリ)
- mock (標準ライブラリ)

### テスト用設定
- `test_config.json` - テスト専用の設定ファイル
- 一時ディレクトリを使用してファイル操作をテスト
- モックを使用して外部依存を分離

## 📝 テスト作成ガイドライン

### 新しいテストの追加
1. `test_<module_name>.py` の形式でファイル名を付ける
2. `unittest.TestCase` を継承したクラスを作成
3. `setUp()` と `tearDown()` メソッドでテスト環境を管理
4. 各テストメソッドは `test_` で始める
5. 適切なアサーションを使用して結果を検証

### モックの使用
```python
from unittest.mock import patch, MagicMock

# 外部依存をモック
with patch('module.function') as mock_function:
    mock_function.return_value = expected_value
    # テスト実行
```

### 一時ファイルの使用
```python
import tempfile
import shutil

def setUp(self):
    self.test_dir = tempfile.mkdtemp()

def tearDown(self):
    shutil.rmtree(self.test_dir, ignore_errors=True)
```

## 🐛 デバッグ

### ログ出力
- テスト実行時のログは `logs/test.log` に出力
- ログレベルは `DEBUG` に設定

### エラー情報
- 失敗したテストの詳細なトレースバックが表示
- エラーが発生したテストの特定が可能

## ✅ 品質保証

- すべてのテストが成功することを確認
- 新機能追加時は対応するテストを作成
- バグ修正時は回帰テストを追加
- テストカバレッジの維持

## 📚 参考資料

- [Python unittest ドキュメント](https://docs.python.org/3/library/unittest.html)
- [unittest.mock ドキュメント](https://docs.python.org/3/library/unittest.mock.html)
- [PyQt6 テストガイド](https://doc.qt.io/qtforpython-6/)
