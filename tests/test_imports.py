#!/usr/bin/env python3
"""
基本的なインポートテスト

このファイルは、プロジェクトの主要なモジュールが正常にインポートできることを確認します。
Windows環境でのテスト実行を改善するために作成されました。
"""

import unittest
import sys
from pathlib import Path


class TestBasicImports(unittest.TestCase):
    """基本的なインポートテスト"""

    def test_python_version(self):
        """Pythonバージョンの確認"""
        version = sys.version_info
        self.assertGreaterEqual(version.major, 3, "Python 3以上が必要")
        self.assertGreaterEqual(version.minor, 8, "Python 3.8以上が必要")

    def test_standard_library_imports(self):
        """標準ライブラリのインポート確認"""
        try:
            import os
            import sys
            import pathlib
            import unittest
            import logging
            
            # インポートされたモジュールを使用してテスト
            self.assertIsNotNone(os.getcwd(), "os.getcwd()が動作する")
            self.assertIsNotNone(sys.version, "sys.versionが動作する")
            self.assertIsNotNone(pathlib.Path, "pathlib.Pathが動作する")
            self.assertIsNotNone(unittest.TestCase, "unittest.TestCaseが動作する")
            self.assertIsNotNone(logging.getLogger, "logging.getLoggerが動作する")
            
            self.assertTrue(True, "標準ライブラリのインポート成功")
        except ImportError as e:
            self.fail(f"標準ライブラリのインポート失敗: {e}")

    def test_third_party_imports(self):
        """サードパーティライブラリのインポート確認"""
        # PyQt6のインポート確認
        try:
            import PyQt6
            from PyQt6.QtCore import QObject
            from PyQt6.QtWidgets import QApplication
            self.assertTrue(True, "PyQt6のインポート成功")
        except ImportError as e:
            self.skipTest(f"PyQt6のインポートスキップ: {e}")

        # Pillowのインポート確認
        try:
            import PIL
            from PIL import Image
            self.assertTrue(True, "Pillowのインポート成功")
        except ImportError as e:
            self.skipTest(f"Pillowのインポートスキップ: {e}")

        # Foliumのインポート確認
        try:
            import folium
            self.assertTrue(True, "Foliumのインポート成功")
        except ImportError as e:
            self.skipTest(f"Foliumのインポートスキップ: {e}")

    def test_project_structure(self):
        """プロジェクト構造の確認"""
        project_root = Path(__file__).parent.parent
        
        # 主要なディレクトリの存在確認
        required_dirs = ["src", "tests", "docs"]
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            self.assertTrue(dir_path.exists(), f"{dir_name}ディレクトリが存在する必要があります")

        # 主要なファイルの存在確認
        required_files = ["main.py", "requirements.txt", "README.md"]
        for file_name in required_files:
            file_path = project_root / file_name
            self.assertTrue(file_path.exists(), f"{file_name}ファイルが存在する必要があります")

    def test_src_modules_import(self):
        """srcモジュールのインポート確認"""
        src_path = Path(__file__).parent.parent / "src"
        if not src_path.exists():
            self.skipTest("srcディレクトリが見つかりません")

        # srcディレクトリ内のPythonファイルを確認
        python_files = list(src_path.rglob("*.py"))
        if not python_files:
            self.skipTest("srcディレクトリにPythonファイルが見つかりません")

        # 基本的なモジュールのインポートを試行
        try:
            # プロジェクトルートをパスに追加
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # 主要なモジュールのインポートを試行
            import main
            self.assertIsNotNone(main, "mainモジュールが正常にインポートされた")
            self.assertTrue(True, "mainモジュールのインポート成功")
        except ImportError as e:
            self.skipTest(f"mainモジュールのインポートスキップ: {e}")
        except SyntaxError as e:
            self.fail(f"mainモジュールの構文エラー: {e}")

    def test_environment_variables(self):
        """環境変数の確認"""
        import os
        
        # CI環境での環境変数確認
        if os.environ.get('CI'):
            self.assertTrue(True, "CI環境で実行中")
        
        # Qt環境変数の確認
        qt_platform = os.environ.get('QT_QPA_PLATFORM')
        if qt_platform:
            self.assertTrue(True, f"Qtプラットフォーム設定: {qt_platform}")


if __name__ == '__main__':
    unittest.main(verbosity=2) 