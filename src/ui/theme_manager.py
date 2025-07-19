"""
テーマ管理機能を提供するモジュール
Qt-Theme-Managerを使用した16種類のテーマ対応
"""

import sys
from typing import List, Optional

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.logger import get_logger
from src.core.settings import get_settings


class ThemeManager(QObject):
    """テーマ管理クラス"""

    # シグナル定義
    theme_changed = pyqtSignal(str)  # テーマ変更時に発信

    def __init__(self, app: QApplication):
        """
        ThemeManagerの初期化

        Args:
            app: QApplicationインスタンス
        """
        super().__init__()
        self.app = app
        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # 利用可能なテーマリスト
        self.available_themes = [
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

        # 現在のテーマ
        self.current_theme = self.settings.get("ui.theme_manager.current_theme", "dark")

        # Qt-Theme-Managerの初期化
        self._init_theme_manager()

        # 初期テーマの適用
        self.apply_theme(self.current_theme)

    def _init_theme_manager(self) -> None:
        """Qt-Theme-Managerの初期化"""
        try:
            # qt-theme-managerのインポート
            from qt_theme_manager import ThemeManager as QtThemeManager

            self.qt_theme_manager = QtThemeManager(self.app)
            self.logger.info("Qt-Theme-Managerを初期化しました")

        except ImportError as e:
            self.logger.error(f"Qt-Theme-Managerのインポートに失敗しました: {e}")
            self.qt_theme_manager = None
        except Exception as e:
            self.logger.error(f"Qt-Theme-Managerの初期化に失敗しました: {e}")
            self.qt_theme_manager = None

    def get_available_themes(self) -> List[str]:
        """
        利用可能なテーマリストを取得

        Returns:
            利用可能なテーマのリスト
        """
        return self.available_themes.copy()

    def get_current_theme(self) -> str:
        """
        現在のテーマを取得

        Returns:
            現在のテーマ名
        """
        return self.current_theme

    def apply_theme(self, theme_name: str) -> bool:
        """
        テーマを適用

        Args:
            theme_name: 適用するテーマ名

        Returns:
            適用成功の場合True
        """
        if theme_name not in self.available_themes:
            self.logger.warning(f"不明なテーマ名です: {theme_name}")
            return False

        try:
            if self.qt_theme_manager is not None:
                # Qt-Theme-Managerを使用してテーマを適用
                self.qt_theme_manager.apply_theme(theme_name)
                self.logger.info(f"テーマを適用しました: {theme_name}")
            else:
                # フォールバック: スタイルシートでテーマを適用
                self._apply_fallback_theme(theme_name)
                self.logger.info(f"フォールバックテーマを適用しました: {theme_name}")

            # 現在のテーマを更新
            self.current_theme = theme_name

            # 設定に保存
            self.settings.set_current_theme(theme_name)

            # シグナル発信
            self.theme_changed.emit(theme_name)

            return True

        except Exception as e:
            self.logger.error(f"テーマの適用に失敗しました: {theme_name}, エラー: {e}")
            return False

    def _apply_fallback_theme(self, theme_name: str) -> None:
        """
        フォールバックテーマの適用（Qt-Theme-Managerが利用できない場合）

        Args:
            theme_name: テーマ名
        """
        # 基本的なスタイルシートを適用
        if theme_name == "dark":
            self.app.setStyleSheet(
                """
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMainWindow {
                    background-color: #2b2b2b;
                }
                QMenuBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QToolBar {
                    background-color: #3c3c3c;
                    border: none;
                }
                QPushButton {
                    background-color: #4a4a4a;
                    border: 1px solid #555555;
                    color: #ffffff;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QTreeView, QListView {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
            """
            )
        elif theme_name == "light":
            self.app.setStyleSheet(
                """
                QWidget {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMainWindow {
                    background-color: #f0f0f0;
                }
                QMenuBar {
                    background-color: #e0e0e0;
                    color: #000000;
                }
                QToolBar {
                    background-color: #e0e0e0;
                    border: none;
                }
                QPushButton {
                    background-color: #d0d0d0;
                    border: 1px solid #a0a0a0;
                    color: #000000;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #c0c0c0;
                }
                QTreeView, QListView {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #a0a0a0;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #a0a0a0;
                }
            """
            )
        else:
            # その他のテーマはデフォルトスタイルを使用
            self.app.setStyleSheet("")

    def cycle_theme(self) -> str:
        """
        次のテーマに切り替え

        Returns:
            新しいテーマ名
        """
        current_index = self.available_themes.index(self.current_theme)
        next_index = (current_index + 1) % len(self.available_themes)
        next_theme = self.available_themes[next_index]

        self.apply_theme(next_theme)
        return next_theme

    def set_theme_for_widget(self, widget: QWidget, theme_name: str) -> bool:
        """
        特定のウィジェットにテーマを適用

        Args:
            widget: 対象ウィジェット
            theme_name: テーマ名

        Returns:
            適用成功の場合True
        """
        try:
            if self.qt_theme_manager is not None:
                # Qt-Theme-Managerを使用してウィジェット固有のテーマを適用
                self.qt_theme_manager.apply_theme_to_widget(widget, theme_name)
                self.logger.debug(f"ウィジェットにテーマを適用しました: {theme_name}")
                return True
            else:
                self.logger.warning(
                    "Qt-Theme-Managerが利用できないため、ウィジェット固有のテーマ適用をスキップしました"
                )
                return False

        except Exception as e:
            self.logger.error(f"ウィジェットへのテーマ適用に失敗しました: {e}")
            return False

    def get_theme_info(self, theme_name: str) -> dict:
        """
        テーマ情報を取得

        Args:
            theme_name: テーマ名

        Returns:
            テーマ情報辞書
        """
        if theme_name not in self.available_themes:
            return {}

        # テーマの基本情報
        theme_info = {
            "name": theme_name,
            "display_name": self._get_theme_display_name(theme_name),
            "description": self._get_theme_description(theme_name),
            "is_dark": theme_name
            in [
                "dark",
                "blue",
                "green",
                "purple",
                "red",
                "pink",
                "brown",
                "gray",
                "cyan",
                "teal",
                "indigo",
            ],
            "is_light": theme_name in ["light", "yellow", "lime", "amber"],
        }

        return theme_info

    def _get_theme_display_name(self, theme_name: str) -> str:
        """
        テーマの表示名を取得

        Args:
            theme_name: テーマ名

        Returns:
            表示名
        """
        display_names = {
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
        return display_names.get(theme_name, theme_name.title())

    def _get_theme_description(self, theme_name: str) -> str:
        """
        テーマの説明を取得

        Args:
            theme_name: テーマ名

        Returns:
            説明文
        """
        descriptions = {
            "dark": "ダークテーマ - 目に優しい暗い背景",
            "light": "ライトテーマ - 明るく清潔な背景",
            "blue": "ブルーテーマ - 落ち着いた青系の配色",
            "green": "グリーンテーマ - 自然を感じる緑系の配色",
            "purple": "パープルテーマ - 高級感のある紫系の配色",
            "orange": "オレンジテーマ - 温かみのあるオレンジ系の配色",
            "red": "レッドテーマ - 情熱的な赤系の配色",
            "pink": "ピンクテーマ - 可愛らしいピンク系の配色",
            "yellow": "イエローテーマ - 明るい黄色系の配色",
            "brown": "ブラウンテーマ - 落ち着いた茶色系の配色",
            "gray": "グレーテーマ - モノトーンのグレー系の配色",
            "cyan": "シアンテーマ - 爽やかな水色系の配色",
            "teal": "ティールテーマ - 深みのある青緑系の配色",
            "indigo": "インディゴテーマ - 神秘的な藍色系の配色",
            "lime": "ライムテーマ - 鮮やかな黄緑系の配色",
            "amber": "アンバーテーマ - 温かみのある琥珀色系の配色",
        }
        return descriptions.get(theme_name, f"{theme_name.title()}テーマ")
