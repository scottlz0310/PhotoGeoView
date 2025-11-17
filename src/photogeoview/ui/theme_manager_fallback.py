"""
ThemeManager フォールバック実装

qt_theme_managerライブラリが利用できない場合の代替実装
"""

from typing import Dict

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class ThemeManagerFallback(QObject):
    """
    ThemeManager フォールバック実装

    qt_theme_managerが利用できない場合の代替実装
    """

    # シグナル
    theme_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = "default"
        self.themes = {
            "default": {
                "name": "Default Light",
                "description": "標準のライトテーマ",
                "style": self._get_light_style(),
            },
            "dark": {
                "name": "Dark",
                "description": "ダークテーマ",
                "style": self._get_dark_style(),
            },
            "photography": {
                "name": "Photography",
                "description": "写真閲覧用テーマ",
                "style": self._get_photography_style(),
            },
        }

    def get_available_themes(self) -> list[str]:
        """利用可能なテーマ一覧を取得"""
        return list(self.themes.keys())

    def get_current_theme(self) -> str:
        """現在のテーマを取得"""
        return self.current_theme

    def set_theme(self, theme_name: str) -> bool:
        """テーマを設定"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self._apply_theme_style(theme_name)
            self.theme_changed.emit(theme_name)
            return True
        return False

    def apply_theme(self, theme_name: str) -> bool:
        """テーマを適用"""
        return self.set_theme(theme_name)

    def get_theme_info(self, theme_name: str) -> Dict | None:
        """テーマ情報を取得"""
        return self.themes.get(theme_name)

    def _apply_theme_style(self, theme_name: str):
        """テーマスタイルを適用"""
        app = QApplication.instance()
        if app and theme_name in self.themes:
            style = self.themes[theme_name]["style"]
            app.setStyleSheet(style)

    def _get_light_style(self) -> str:
        """ライトテーマのスタイルを取得"""
        return """
        QWidget {
            background-color: #ffffff;
            color: #333333;
        }
        QMainWindow {
            background-color: #f8f9fa;
        }
        QPushButton {
            background-color: #e9ecef;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #dee2e6;
        }
        QPushButton:pressed {
            background-color: #ced4da;
        }
        QLabel {
            color: #495057;
        }
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 6px;
        }
        QTextEdit {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        """

    def _get_dark_style(self) -> str:
        """ダークテーマのスタイルを取得"""
        return """
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMainWindow {
            background-color: #1e1e1e;
        }
        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px 12px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #606060;
        }
        QLabel {
            color: #e0e0e0;
        }
        QLineEdit {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px;
            color: #ffffff;
        }
        QTextEdit {
            background-color: #404040;
            border: 1px solid #555555;
            border-radius: 4px;
            color: #ffffff;
        }
        """

    def _get_photography_style(self) -> str:
        """写真用テーマのスタイルを取得"""
        return """
        QWidget {
            background-color: #1a1a1a;
            color: #cccccc;
        }
        QMainWindow {
            background-color: #0d0d0d;
        }
        QPushButton {
            background-color: #333333;
            border: 1px solid #444444;
            border-radius: 4px;
            padding: 6px 12px;
            color: #cccccc;
        }
        QPushButton:hover {
            background-color: #444444;
        }
        QPushButton:pressed {
            background-color: #555555;
        }
        QLabel {
            color: #cccccc;
        }
        QLineEdit {
            background-color: #333333;
            border: 1px solid #444444;
            border-radius: 4px;
            padding: 6px;
            color: #cccccc;
        }
        QTextEdit {
            background-color: #333333;
            border: 1px solid #444444;
            border-radius: 4px;
            color: #cccccc;
        }
        """


# qt_theme_managerからのインポートを試行し、失敗した場合はフォールバックを使用
try:
    from qt_theme_manager import ThemeManager
except (ImportError, AttributeError):
    ThemeManager = ThemeManagerFallback
