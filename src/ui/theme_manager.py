"""
テーマ管理機能を提供するモジュール
Qt-Theme-Managerを使用した16種類のテーマ対応
"""

import sys
from typing import List, Optional, Dict, Any

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

        # 利用可能なテーマリスト（Qt-Theme-Manager対応）
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

        # テーマ情報辞書
        self.theme_info = {
            "dark": {
                "display_name": "ダーク",
                "description": "モダンなダークテーマ",
                "category": "dark",
            },
            "light": {
                "display_name": "ライト",
                "description": "クリーンなライトテーマ",
                "category": "light",
            },
            "blue": {
                "display_name": "ブルー",
                "description": "落ち着いたブルーテーマ",
                "category": "color",
            },
            "green": {
                "display_name": "グリーン",
                "description": "自然なグリーンテーマ",
                "category": "color",
            },
            "purple": {
                "display_name": "パープル",
                "description": "エレガントなパープルテーマ",
                "category": "color",
            },
            "orange": {
                "display_name": "オレンジ",
                "description": "温かみのあるオレンジテーマ",
                "category": "color",
            },
            "red": {
                "display_name": "レッド",
                "description": "情熱的なレッドテーマ",
                "category": "color",
            },
            "pink": {
                "display_name": "ピンク",
                "description": "可愛らしいピンクテーマ",
                "category": "color",
            },
            "yellow": {
                "display_name": "イエロー",
                "description": "明るいイエローテーマ",
                "category": "color",
            },
            "brown": {
                "display_name": "ブラウン",
                "description": "落ち着いたブラウンテーマ",
                "category": "color",
            },
            "gray": {
                "display_name": "グレー",
                "description": "シンプルなグレーテーマ",
                "category": "neutral",
            },
            "cyan": {
                "display_name": "シアン",
                "description": "爽やかなシアンテーマ",
                "category": "color",
            },
            "teal": {
                "display_name": "ティール",
                "description": "洗練されたティールテーマ",
                "category": "color",
            },
            "indigo": {
                "display_name": "インディゴ",
                "description": "深みのあるインディゴテーマ",
                "category": "color",
            },
            "lime": {
                "display_name": "ライム",
                "description": "フレッシュなライムテーマ",
                "category": "color",
            },
            "amber": {
                "display_name": "アンバー",
                "description": "温かみのあるアンバーテーマ",
                "category": "color",
            },
        }

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
                self.logger.info(
                    f"Qt-Theme-Managerでテーマを適用しました: {theme_name}"
                )
            else:
                # フォールバック: スタイルシートでテーマを適用
                self._apply_fallback_theme(theme_name)
                self.logger.info(f"フォールバックテーマを適用しました: {theme_name}")

            # 現在のテーマを更新
            self.current_theme = theme_name

            # 設定に保存
            self.settings.set("ui.theme_manager.current_theme", theme_name)

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
        # 16種類のテーマに対応したスタイルシート
        theme_styles = {
            "dark": """
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
            """,
            "light": """
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
                    border: 1px solid #b0b0b0;
                    color: #000000;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #c0c0c0;
                }
                QTreeView, QListView {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #b0b0b0;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #b0b0b0;
                }
            """,
            "blue": """
                QWidget {
                    background-color: #e3f2fd;
                    color: #1565c0;
                }
                QMainWindow {
                    background-color: #e3f2fd;
                }
                QMenuBar {
                    background-color: #bbdefb;
                    color: #1565c0;
                }
                QToolBar {
                    background-color: #bbdefb;
                    border: none;
                }
                QPushButton {
                    background-color: #90caf9;
                    border: 1px solid #64b5f6;
                    color: #1565c0;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #64b5f6;
                }
            """,
            "green": """
                QWidget {
                    background-color: #e8f5e8;
                    color: #2e7d32;
                }
                QMainWindow {
                    background-color: #e8f5e8;
                }
                QMenuBar {
                    background-color: #c8e6c9;
                    color: #2e7d32;
                }
                QToolBar {
                    background-color: #c8e6c9;
                    border: none;
                }
                QPushButton {
                    background-color: #a5d6a7;
                    border: 1px solid #81c784;
                    color: #2e7d32;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #81c784;
                }
            """,
            "purple": """
                QWidget {
                    background-color: #f3e5f5;
                    color: #7b1fa2;
                }
                QMainWindow {
                    background-color: #f3e5f5;
                }
                QMenuBar {
                    background-color: #e1bee7;
                    color: #7b1fa2;
                }
                QToolBar {
                    background-color: #e1bee7;
                    border: none;
                }
                QPushButton {
                    background-color: #ce93d8;
                    border: 1px solid #ba68c8;
                    color: #7b1fa2;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #ba68c8;
                }
            """,
            "orange": """
                QWidget {
                    background-color: #fff3e0;
                    color: #ef6c00;
                }
                QMainWindow {
                    background-color: #fff3e0;
                }
                QMenuBar {
                    background-color: #ffe0b2;
                    color: #ef6c00;
                }
                QToolBar {
                    background-color: #ffe0b2;
                    border: none;
                }
                QPushButton {
                    background-color: #ffcc02;
                    border: 1px solid #ffb74d;
                    color: #ef6c00;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #ffb74d;
                }
            """,
            "red": """
                QWidget {
                    background-color: #ffebee;
                    color: #c62828;
                }
                QMainWindow {
                    background-color: #ffebee;
                }
                QMenuBar {
                    background-color: #ffcdd2;
                    color: #c62828;
                }
                QToolBar {
                    background-color: #ffcdd2;
                    border: none;
                }
                QPushButton {
                    background-color: #ef9a9a;
                    border: 1px solid #e57373;
                    color: #c62828;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #e57373;
                }
            """,
            "pink": """
                QWidget {
                    background-color: #fce4ec;
                    color: #ad1457;
                }
                QMainWindow {
                    background-color: #fce4ec;
                }
                QMenuBar {
                    background-color: #f8bbd9;
                    color: #ad1457;
                }
                QToolBar {
                    background-color: #f8bbd9;
                    border: none;
                }
                QPushButton {
                    background-color: #f48fb1;
                    border: 1px solid #f06292;
                    color: #ad1457;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #f06292;
                }
            """,
            "yellow": """
                QWidget {
                    background-color: #fffde7;
                    color: #f57f17;
                }
                QMainWindow {
                    background-color: #fffde7;
                }
                QMenuBar {
                    background-color: #fff9c4;
                    color: #f57f17;
                }
                QToolBar {
                    background-color: #fff9c4;
                    border: none;
                }
                QPushButton {
                    background-color: #fff59d;
                    border: 1px solid #fff176;
                    color: #f57f17;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #fff176;
                }
            """,
            "brown": """
                QWidget {
                    background-color: #efebe9;
                    color: #5d4037;
                }
                QMainWindow {
                    background-color: #efebe9;
                }
                QMenuBar {
                    background-color: #d7ccc8;
                    color: #5d4037;
                }
                QToolBar {
                    background-color: #d7ccc8;
                    border: none;
                }
                QPushButton {
                    background-color: #bcaaa4;
                    border: 1px solid #a1887f;
                    color: #5d4037;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #a1887f;
                }
            """,
            "gray": """
                QWidget {
                    background-color: #fafafa;
                    color: #424242;
                }
                QMainWindow {
                    background-color: #fafafa;
                }
                QMenuBar {
                    background-color: #eeeeee;
                    color: #424242;
                }
                QToolBar {
                    background-color: #eeeeee;
                    border: none;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #bdbdbd;
                    color: #424242;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #bdbdbd;
                }
            """,
            "cyan": """
                QWidget {
                    background-color: #e0f2f1;
                    color: #00695c;
                }
                QMainWindow {
                    background-color: #e0f2f1;
                }
                QMenuBar {
                    background-color: #b2dfdb;
                    color: #00695c;
                }
                QToolBar {
                    background-color: #b2dfdb;
                    border: none;
                }
                QPushButton {
                    background-color: #80cbc4;
                    border: 1px solid #4db6ac;
                    color: #00695c;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #4db6ac;
                }
            """,
            "teal": """
                QWidget {
                    background-color: #e0f2f1;
                    color: #004d40;
                }
                QMainWindow {
                    background-color: #e0f2f1;
                }
                QMenuBar {
                    background-color: #b2dfdb;
                    color: #004d40;
                }
                QToolBar {
                    background-color: #b2dfdb;
                    border: none;
                }
                QPushButton {
                    background-color: #80cbc4;
                    border: 1px solid #4db6ac;
                    color: #004d40;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #4db6ac;
                }
            """,
            "indigo": """
                QWidget {
                    background-color: #e8eaf6;
                    color: #283593;
                }
                QMainWindow {
                    background-color: #e8eaf6;
                }
                QMenuBar {
                    background-color: #c5cae9;
                    color: #283593;
                }
                QToolBar {
                    background-color: #c5cae9;
                    border: none;
                }
                QPushButton {
                    background-color: #9fa8da;
                    border: 1px solid #7986cb;
                    color: #283593;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #7986cb;
                }
            """,
            "lime": """
                QWidget {
                    background-color: #f9fbe7;
                    color: #827717;
                }
                QMainWindow {
                    background-color: #f9fbe7;
                }
                QMenuBar {
                    background-color: #f0f4c3;
                    color: #827717;
                }
                QToolBar {
                    background-color: #f0f4c3;
                    border: none;
                }
                QPushButton {
                    background-color: #e6ee9c;
                    border: 1px solid #dce775;
                    color: #827717;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #dce775;
                }
            """,
            "amber": """
                QWidget {
                    background-color: #fff8e1;
                    color: #f57c00;
                }
                QMainWindow {
                    background-color: #fff8e1;
                }
                QMenuBar {
                    background-color: #ffecb3;
                    color: #f57c00;
                }
                QToolBar {
                    background-color: #ffecb3;
                    border: none;
                }
                QPushButton {
                    background-color: #ffd54f;
                    border: 1px solid #ffca28;
                    color: #f57c00;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #ffca28;
                }
            """,
        }

        # テーマスタイルを適用
        if theme_name in theme_styles:
            self.app.setStyleSheet(theme_styles[theme_name])
        else:
            # デフォルトはダークテーマ
            self.app.setStyleSheet(theme_styles["dark"])

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
