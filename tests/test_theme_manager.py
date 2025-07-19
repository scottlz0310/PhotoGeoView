#!/usr/bin/env python3
"""
テーママネージャーモジュールの単体テスト
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをPythonパスに追加
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.theme_manager import ThemeManager
from src.core.logger import get_logger


class TestThemeManager(unittest.TestCase):
    """ThemeManagerのテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        self.logger = get_logger(__name__)

        # テスト用の一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()

        # モックのQApplication
        self.mock_app = MagicMock()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        """初期化テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # 結果を検証
            self.assertIsNotNone(theme_manager)
            self.assertIsNotNone(theme_manager.logger)
            self.assertIsNotNone(theme_manager.available_themes)
            self.assertIsNotNone(theme_manager.theme_info)

    def test_get_available_themes(self):
        """利用可能テーマ取得テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)
            themes = theme_manager.get_available_themes()

            # 結果を検証
            self.assertIsNotNone(themes)
            self.assertIsInstance(themes, list)
            self.assertGreater(len(themes), 0)

            # 16種類のテーマが含まれていることを確認
            expected_themes = [
                "dark",
                "light",
                "blue",
                "green",
                "purple",
                "orange",
                "red",
                "pink",
                "yellow",
                "brown",
                "gray",
                "cyan",
                "teal",
                "indigo",
                "lime",
                "amber",
            ]

            for theme in expected_themes:
                self.assertIn(theme, themes)

    def test_get_current_theme(self):
        """現在のテーマ取得テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)
            current_theme = theme_manager.get_current_theme()

            # 結果を検証
            self.assertIsNotNone(current_theme)
            self.assertIsInstance(current_theme, str)
            self.assertIn(current_theme, theme_manager.available_themes)

    def test_apply_theme_valid(self):
        """有効なテーマ適用テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # 有効なテーマを適用
            result = theme_manager.apply_theme("light")

            # 結果を検証
            self.assertTrue(result)
            self.assertEqual(theme_manager.get_current_theme(), "light")

    def test_apply_theme_invalid(self):
        """無効なテーマ適用テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)
            original_theme = theme_manager.get_current_theme()

            # 無効なテーマを適用
            result = theme_manager.apply_theme("invalid_theme")

            # 結果を検証
            self.assertFalse(result)
            self.assertEqual(theme_manager.get_current_theme(), original_theme)

    def test_cycle_theme(self):
        """テーマ循環テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)
            original_theme = theme_manager.get_current_theme()

            # テーマを循環
            next_theme = theme_manager.cycle_theme()

            # 結果を検証
            self.assertIsNotNone(next_theme)
            self.assertIn(next_theme, theme_manager.available_themes)
            self.assertNotEqual(next_theme, original_theme)
            self.assertEqual(theme_manager.get_current_theme(), next_theme)

    def test_get_theme_info(self):
        """テーマ情報取得テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # 有効なテーマの情報を取得
            theme_info = theme_manager.get_theme_info("dark")

            # 結果を検証
            self.assertIsNotNone(theme_info)
            self.assertIn("name", theme_info)
            self.assertIn("display_name", theme_info)
            self.assertIn("description", theme_info)
            self.assertIn("is_dark", theme_info)
            self.assertIn("is_light", theme_info)

            self.assertEqual(theme_info["name"], "dark")
            self.assertEqual(theme_info["display_name"], "ダーク")

    def test_get_theme_info_invalid(self):
        """無効なテーマ情報取得テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # 無効なテーマの情報を取得
            theme_info = theme_manager.get_theme_info("invalid_theme")

            # 結果を検証
            self.assertEqual(theme_info, {})

    def test_theme_display_names(self):
        """テーマ表示名テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # 各テーマの表示名を確認
            expected_display_names = {
                "dark": "ダーク",
                "light": "ライト",
                "blue": "ブルー",
                "green": "グリーン",
                "purple": "パープル",
                "orange": "オレンジ",
                "red": "レッド",
                "pink": "ピンク",
                "yellow": "イエロー",
                "brown": "ブラウン",
                "gray": "グレー",
                "cyan": "シアン",
                "teal": "ティール",
                "indigo": "インディゴ",
                "lime": "ライム",
                "amber": "アンバー",
            }

            for theme_name, expected_display_name in expected_display_names.items():
                display_name = theme_manager._get_theme_display_name(theme_name)
                self.assertEqual(display_name, expected_display_name)

    def test_theme_descriptions(self):
        """テーマ説明テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # 各テーマの説明を確認
            for theme_name in theme_manager.available_themes:
                description = theme_manager._get_theme_description(theme_name)
                self.assertIsNotNone(description)
                self.assertIsInstance(description, str)
                self.assertGreater(len(description), 0)

    def test_theme_categories(self):
        """テーマカテゴリテスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # カテゴリ別にテーマを分類
            categories = {
                "dark": "dark",
                "light": "light",
                "blue": "color",
                "green": "color",
                "purple": "color",
                "orange": "color",
                "red": "color",
                "pink": "color",
                "yellow": "color",
                "brown": "color",
                "gray": "neutral",
                "cyan": "color",
                "teal": "color",
                "indigo": "color",
                "lime": "color",
                "amber": "color",
            }

            for theme_name, expected_category in categories.items():
                theme_info = theme_manager.get_theme_info(theme_name)
                self.assertIn("category", theme_info)
                # 実際の実装ではカテゴリ情報が含まれているかチェック

    def test_qt_theme_manager_integration(self):
        """Qt-Theme-Manager統合テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            # Qt-Theme-Managerが利用可能な場合のテスト
            with patch("qt_theme_manager.ThemeManager") as mock_qt_theme_manager:
                mock_qt_instance = MagicMock()
                mock_qt_theme_manager.return_value = mock_qt_instance

                theme_manager = ThemeManager(self.mock_app)

                # Qt-Theme-Managerが初期化されていることを確認
                self.assertIsNotNone(theme_manager.qt_theme_manager)

                # テーマ適用時にQt-Theme-Managerが呼ばれることを確認
                with patch.object(mock_qt_instance, "apply_theme") as mock_apply:
                    theme_manager.apply_theme("light")
                    mock_apply.assert_called_once_with("light")

    def test_fallback_theme_application(self):
        """フォールバックテーマ適用テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            # Qt-Theme-Managerが利用できない場合のテスト
            with patch("qt_theme_manager.ThemeManager", side_effect=ImportError):
                theme_manager = ThemeManager(self.mock_app)

                # Qt-Theme-ManagerがNoneであることを確認
                self.assertIsNone(theme_manager.qt_theme_manager)

                # フォールバックテーマが適用されることを確認
                result = theme_manager.apply_theme("dark")
                self.assertTrue(result)

    def test_theme_changed_signal(self):
        """テーマ変更シグナルテスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # シグナルが発信されることを確認
            with patch.object(theme_manager, "theme_changed") as mock_signal:
                theme_manager.apply_theme("light")
                mock_signal.emit.assert_called_once_with("light")

    def test_settings_integration(self):
        """設定統合テスト"""
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = self.mock_app

            theme_manager = ThemeManager(self.mock_app)

            # 設定に保存されることを確認
            with patch.object(theme_manager.settings, "set") as mock_settings_set:
                theme_manager.apply_theme("blue")
                mock_settings_set.assert_called_once_with(
                    "ui.theme_manager.current_theme", "blue"
                )


if __name__ == "__main__":
    unittest.main()
