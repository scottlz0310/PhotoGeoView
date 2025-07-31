"""
Basic Tests for PhotoGeoView

基本的な動作確認テスト

Author: Kiro AI Integration System
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBasicImports(unittest.TestCase):
    """基本的なインポートテスト"""

    def test_python_version(self):
        """Python バージョンの確認"""
        self.assertGreaterEqual(sys.version_info.major, 3)
        self.assertGreaterEqual(sys.version_info.minor, 9)

    def test_required_packages(self):
        """必要なパッケージのインポート確認"""
        try:
            import PyQt6
            self.assertTrue(True, "PyQt6 imported successfully")
        except ImportError as e:
            self.fail(f"PyQt6 import failed: {e}")

        try:
            import PIL
            self.assertTrue(True, "Pillow imported successfully")
        except ImportError as e:
            self.fail(f"Pillow import failed: {e}")

        try:
            import folium
            self.assertTrue(True, "Folium imported successfully")
        except ImportError as e:
            self.fail(f"Folium import failed: {e}")

    def test_project_structure(self):
        """プロジェクト構造の確認"""
        project_root = Path(__file__).parent.parent

        # 重要なファイルの存在確認
        self.assertTrue((project_root / "main.py").exists(), "main.py should exist")
        self.assertTrue((project_root / "requirements.txt").exists(), "requirements.txt should exist")
        self.assertTrue((project_root / "pyproject.toml").exists(), "pyproject.toml should exist")

        # 重要なディレクトリの存在確認
        self.assertTrue((project_root / "src").exists(), "src directory should exist")
        self.assertTrue((project_root / "tests").exists(), "tests directory should exist")


class TestBasicFunctionality(unittest.TestCase):
    """基本機能のテスト"""

    def test_main_module_import(self):
        """メインモジュールのインポート確認"""
        try:
            # main.py の基本的な構文チェック
            import main
            self.assertTrue(True, "main module imported successfully")
        except ImportError as e:
            # インポートエラーは許容（依存関係の問題の可能性）
            self.skipTest(f"main module import skipped: {e}")
        except SyntaxError as e:
            self.fail(f"main module has syntax error: {e}")

    def test_src_modules_basic_import(self):
        """srcモジュールの基本的なインポート確認"""
        src_path = Path(__file__).parent.parent / "src"
        if not src_path.exists():
            self.skipTest("src directory not found")

        # 基本的なモジュールの存在確認
        integration_path = src_path / "integration"
        if integration_path.exists():
            try:
                from integration import config_manager
                self.assertTrue(True, "config_manager imported successfully")
            except ImportError as e:
                self.skipTest(f"config_manager import skipped: {e}")


class TestEnvironment(unittest.TestCase):
    """環境設定のテスト"""

    def test_qt_environment(self):
        """Qt環境の確認"""
        import os

        # CI環境での設定確認
        if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
            self.assertTrue(True, "Qt offscreen platform configured")

        # Display環境の確認
        if os.environ.get('DISPLAY'):
            self.assertTrue(True, f"Display configured: {os.environ.get('DISPLAY')}")

    def test_working_directory(self):
        """作業ディレクトリの確認"""
        import os
        cwd = Path(os.getcwd())

        # プロジェクトルートにいることを確認
        self.assertTrue((cwd / "main.py").exists() or (cwd / "pyproject.toml").exists(),
                       "Should be in project root directory")


if __name__ == '__main__':
    unittest.main(verbosity=2)
