"""
Qt-Theme-Manager形式対応テーマ管理機能
新しいJSON形式（available_themes構造）に対応
"""

import json
import os
from typing import List, Dict, Optional, Any, Union
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.logger import get_logger
from src.core.settings import get_settings


class QtThemeManagerAdapter(QObject):
    """Qt-Theme-Manager形式対応テーマ管理クラス"""

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

        # Qt-Theme-Manager形式のファイルパス
        self.qt_theme_definitions_path = Path(__file__).parent.parent.parent / "config" / "qt_theme_definitions.json"
        self.qt_theme_user_settings_path = Path(__file__).parent.parent.parent / "config" / "qt_theme_user_settings.json"

        # レガシー統合設定ファイルパス（フォールバック用）
        self.qt_theme_config_path = Path(__file__).parent.parent.parent / "config" / "qt_theme_settings.json"

        # 従来形式の設定ファイルパス（フォールバック用）
        self.legacy_theme_config_path = Path(__file__).parent.parent.parent / "config" / "theme_styles.json"

        # テーマ設定を読み込み（分離型設定を使用）
        self.qt_theme_config = self._load_separated_theme_config()

        # 利用可能なテーマリストを設定から取得
        self.available_themes = list(self.qt_theme_config.get("available_themes", {}).keys())

        # テーマ情報辞書を設定ファイルから構築
        self.theme_info = self._build_qt_theme_info()

        # 現在のテーマ
        self.current_theme = self.qt_theme_config.get("current_theme", "dark")

        # 有効なテーマリスト
        self.enabled_themes = self.available_themes.copy()

        # Qt-Theme-Managerの初期化
        self._init_theme_manager()

        # 初期テーマの適用
        self.apply_theme(self.current_theme)

    def _load_separated_theme_config(self) -> Dict[str, Any]:
        """分離型設定ファイルを読み込み（定義ファイル + ユーザー設定ファイル）"""
        try:
            # テーマ定義ファイルを読み込み
            theme_definitions = self._load_theme_definitions()

            # ユーザー設定ファイルを読み込み
            user_settings = self._load_user_settings()

            # 統合設定を作成
            merged_config = {**user_settings, **theme_definitions}

            self.logger.info("分離型設定ファイルを読み込みました")
            return merged_config

        except Exception as e:
            self.logger.error(f"分離型設定の読み込みに失敗、フォールバックを使用: {e}")
            return self._load_qt_theme_config()

    def _load_theme_definitions(self) -> Dict[str, Any]:
        """テーマ定義ファイルを読み込み"""
        try:
            if self.qt_theme_definitions_path.exists():
                with open(self.qt_theme_definitions_path, 'r', encoding='utf-8') as f:
                    definitions = json.load(f)
                self.logger.debug(f"テーマ定義ファイルを読み込みました: {self.qt_theme_definitions_path}")
                return definitions
            else:
                self.logger.warning(f"テーマ定義ファイルが見つかりません: {self.qt_theme_definitions_path}")
                return {"available_themes": {}}
        except Exception as e:
            self.logger.error(f"テーマ定義ファイルの読み込みに失敗: {e}")
            return {"available_themes": {}}

    def _load_user_settings(self) -> Dict[str, Any]:
        """ユーザー設定ファイルを読み込み"""
        try:
            if self.qt_theme_user_settings_path.exists():
                with open(self.qt_theme_user_settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                self.logger.debug(f"ユーザー設定ファイルを読み込みました: {self.qt_theme_user_settings_path}")
                return settings
            else:
                # ユーザー設定ファイルが存在しない場合はデフォルト設定を作成
                default_settings = {
                    "current_theme": "dark",
                    "last_selected_theme": "dark",
                    "theme_switching_enabled": True,
                    "remember_theme_choice": True,
                    "version": "0.0.1"
                }
                self._save_user_settings(default_settings)
                return default_settings
        except Exception as e:
            self.logger.error(f"ユーザー設定ファイルの読み込みに失敗: {e}")
            return {
                "current_theme": "dark",
                "last_selected_theme": "dark",
                "theme_switching_enabled": True,
                "remember_theme_choice": True,
                "version": "0.0.1"
            }

    def _save_user_settings(self, settings: Dict[str, Any]) -> None:
        """ユーザー設定ファイルを保存"""
        try:
            with open(self.qt_theme_user_settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"ユーザー設定ファイルを保存しました: {self.qt_theme_user_settings_path}")
        except Exception as e:
            self.logger.warning(f"ユーザー設定ファイルの保存に失敗: {e}")

    def _load_qt_theme_config(self) -> Dict[str, Any]:
        """Qt-Theme-Manager形式の設定ファイルを読み込み"""
        try:
            if self.qt_theme_config_path.exists():
                with open(self.qt_theme_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"Qt-Theme-Manager形式設定ファイルを読み込みました: {self.qt_theme_config_path}")
                return config
            else:
                self.logger.warning(f"Qt-Theme-Manager形式設定ファイルが見つかりません: {self.qt_theme_config_path}")
                # 従来形式からの変換を試行
                return self._convert_legacy_to_qt_format()
        except json.JSONDecodeError as e:
            self.logger.error(f"Qt-Theme-Manager形式設定ファイルのJSON解析に失敗しました: {e}")
            return self._get_default_qt_theme_config()
        except Exception as e:
            self.logger.error(f"Qt-Theme-Manager形式設定ファイルの読み込みに失敗しました: {e}")
            return self._get_default_qt_theme_config()

    def _convert_legacy_to_qt_format(self) -> Dict[str, Any]:
        """従来形式からQt-Theme-Manager形式に変換"""
        try:
            if self.legacy_theme_config_path.exists():
                with open(self.legacy_theme_config_path, 'r', encoding='utf-8') as f:
                    legacy_config = json.load(f)

                self.logger.info("従来形式からQt-Theme-Manager形式に変換中...")
                return self._transform_legacy_themes(legacy_config)
            else:
                return self._get_default_qt_theme_config()
        except Exception as e:
            self.logger.error(f"従来形式の変換に失敗しました: {e}")
            return self._get_default_qt_theme_config()

    def _transform_legacy_themes(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """従来形式のテーマをQt-Theme-Manager形式に変換"""
        qt_config = {
            "current_theme": "dark",
            "last_selected_theme": "dark",
            "theme_switching_enabled": True,
            "remember_theme_choice": True,
            "version": "0.0.1",
            "available_themes": {}
        }

        theme_styles = legacy_config.get("theme_styles", {})

        for theme_name, theme_data in theme_styles.items():
            colors = theme_data.get("colors", {})

            # Qt-Theme-Manager形式に変換
            qt_theme = {
                "name": theme_name,
                "display_name": theme_data.get("name", theme_name.title()),
                "description": theme_data.get("description", f"{theme_name}テーマ"),
                "primaryColor": colors.get("background", "#ffffff"),
                "accentColor": colors.get("button_background", "#cccccc"),
                "backgroundColor": colors.get("background", "#ffffff"),
                "textColor": colors.get("foreground", "#000000"),
                "button": {
                    "background": colors.get("button_background", "#cccccc"),
                    "text": colors.get("foreground", "#000000"),
                    "hover": colors.get("button_hover", "#bbbbbb"),
                    "pressed": colors.get("button_hover", "#bbbbbb"),
                    "border": colors.get("border", "#aaaaaa")
                },
                "panel": {
                    "background": colors.get("background", "#ffffff"),
                    "border": colors.get("border", "#aaaaaa"),
                    "header": {
                        "background": colors.get("menu_background", "#eeeeee"),
                        "text": colors.get("foreground", "#000000"),
                        "border": colors.get("border", "#aaaaaa")
                    },
                    "zebra": {
                        "alternate": colors.get("zebra_alternate", colors.get("input_background", "#f5f5f5"))
                    }
                },
                "text": {
                    "primary": colors.get("foreground", "#000000"),
                    "secondary": colors.get("foreground", "#000000"),
                    "muted": colors.get("foreground", "#000000"),
                    "heading": colors.get("foreground", "#000000"),
                    "link": colors.get("button_background", "#cccccc"),
                    "success": "#68d391",
                    "warning": "#fbb948",
                    "error": "#fc8181"
                },
                "input": {
                    "background": colors.get("input_background", "#ffffff"),
                    "text": colors.get("foreground", "#000000"),
                    "border": colors.get("border", "#aaaaaa"),
                    "focus": colors.get("button_background", "#cccccc"),
                    "placeholder": colors.get("foreground", "#000000")
                },
                "list": {
                    "background": colors.get("input_background", "#ffffff"),
                    "text": colors.get("foreground", "#000000"),
                    "alternate": colors.get("zebra_alternate", colors.get("input_background", "#f5f5f5")),
                    "selection": colors.get("selection", colors.get("button_background", "#cccccc")),
                    "hover": colors.get("hover", colors.get("button_hover", "#bbbbbb")),
                    "border": colors.get("border", "#aaaaaa")
                },
                "menu": {
                    "background": colors.get("menu_background", "#eeeeee"),
                    "text": colors.get("foreground", "#000000"),
                    "hover": colors.get("button_hover", "#bbbbbb"),
                    "border": colors.get("border", "#aaaaaa")
                },
                "toolbar": {
                    "background": colors.get("menu_background", "#eeeeee"),
                    "text": colors.get("foreground", "#000000"),
                    "border": colors.get("border", "#aaaaaa")
                },
                "scrollbar": {
                    "background": colors.get("background", "#ffffff"),
                    "handle": colors.get("button_background", "#cccccc"),
                    "handle_hover": colors.get("button_hover", "#bbbbbb")
                }
            }

            qt_config["available_themes"][theme_name] = qt_theme

        return qt_config

    def _get_default_qt_theme_config(self) -> Dict[str, Any]:
        """デフォルトのQt-Theme-Manager形式設定を返す"""
        return {
            "current_theme": "dark",
            "last_selected_theme": "dark",
            "theme_switching_enabled": True,
            "remember_theme_choice": True,
            "version": "0.0.1",
            "available_themes": {
                "dark": {
                    "name": "dark",
                    "display_name": "ダーク",
                    "description": "モダンなダークテーマ",
                    "primaryColor": "#2b2b2b",
                    "accentColor": "#5a5a5a",
                    "backgroundColor": "#2b2b2b",
                    "textColor": "#ffffff",
                    "button": {
                        "background": "#4a4a4a",
                        "text": "#ffffff",
                        "hover": "#5a5a5a",
                        "pressed": "#5a5a5a",
                        "border": "#555555"
                    },
                    "panel": {
                        "background": "#2b2b2b",
                        "border": "#555555",
                        "header": {
                            "background": "#3c3c3c",
                            "text": "#ffffff",
                            "border": "#555555"
                        },
                        "zebra": {
                            "alternate": "#2d2d2d"
                        }
                    }
                },
                "light": {
                    "name": "light",
                    "display_name": "ライト",
                    "description": "クリーンなライトテーマ",
                    "primaryColor": "#f0f0f0",
                    "accentColor": "#c0c0c0",
                    "backgroundColor": "#f0f0f0",
                    "textColor": "#000000",
                    "button": {
                        "background": "#d0d0d0",
                        "text": "#000000",
                        "hover": "#c0c0c0",
                        "pressed": "#c0c0c0",
                        "border": "#b0b0b0"
                    },
                    "panel": {
                        "background": "#f0f0f0",
                        "border": "#b0b0b0",
                        "header": {
                            "background": "#e0e0e0",
                            "text": "#000000",
                            "border": "#b0b0b0"
                        },
                        "zebra": {
                            "alternate": "#f5f5f5"
                        }
                    }
                }
            }
        }

    def _build_qt_theme_info(self) -> Dict[str, Dict[str, str]]:
        """Qt-Theme-Manager形式設定からテーマ情報辞書を構築"""
        theme_info = {}
        available_themes = self.qt_theme_config.get("available_themes", {})

        for theme_name, theme_data in available_themes.items():
            theme_info[theme_name] = {
                "display_name": theme_data.get("display_name", theme_name.title()),
                "description": theme_data.get("description", f"{theme_name}テーマ"),
                "category": "color"  # Qt-Theme-Manager形式にはcategoryがないので固定
            }

        return theme_info

    def _init_theme_manager(self) -> None:
        """Qt-Theme-Managerの初期化"""
        try:
            # qt-theme-managerのインポート
            from theme_manager.qt.controller import ThemeController

            # Qt-Theme-Manager形式の設定ファイルを使用（パラメータを省略）
            self.qt_theme_manager = ThemeController()
            # 設定ファイルを個別に設定
            self.qt_theme_manager.load_config(str(self.qt_theme_config_path))
            self.logger.info("Qt-Theme-Manager（Qt形式対応）を初期化しました")

        except ImportError as e:
            self.logger.error(f"Qt-Theme-Managerのインポートに失敗しました: {e}")
            self.qt_theme_manager = None
        except Exception as e:
            self.logger.error(f"Qt-Theme-Managerの初期化に失敗しました: {e}")
            self.qt_theme_manager = None

    def apply_theme(self, theme_name: str) -> bool:
        """
        指定されたテーマを適用する

        Args:
            theme_name: 適用するテーマ名

        Returns:
            適用成功時True、失敗時False
        """
        if theme_name not in self.available_themes:
            self.logger.warning(f"無効なテーマ名です: {theme_name}")
            return False

        try:
            # Qt-Theme-Managerでテーマを適用
            if self.qt_theme_manager:
                success = self.qt_theme_manager.set_theme(theme_name)
                if success:
                    self.current_theme = theme_name
                    self.logger.info(f"Qt-Theme-Managerでテーマを適用しました: {theme_name}")

                    # 設定ファイルの current_theme を更新
                    self._update_current_theme_in_config(theme_name)

                    self.theme_changed.emit(theme_name)
                    return True
                else:
                    self.logger.warning(f"Qt-Theme-Managerでのテーマ適用に失敗、フォールバックを使用: {theme_name}")
                    return self._apply_fallback_theme(theme_name)
            else:
                # Qt-Theme-Managerが利用できない場合はフォールバック
                return self._apply_fallback_theme(theme_name)

        except Exception as e:
            self.logger.error(f"テーマ適用中にエラーが発生しました: {e}")
            return self._apply_fallback_theme(theme_name)

    def _update_current_theme_in_config(self, theme_name: str) -> None:
        """設定ファイルの current_theme を更新（ユーザー設定ファイルのみ）"""
        try:
            # 現在のユーザー設定を読み込み
            user_settings = self._load_user_settings()

            # テーマ設定を更新
            user_settings["current_theme"] = theme_name
            user_settings["last_selected_theme"] = theme_name

            # ユーザー設定ファイルのみを更新
            self._save_user_settings(user_settings)

            # メモリ上の統合設定も更新
            self.qt_theme_config["current_theme"] = theme_name
            self.qt_theme_config["last_selected_theme"] = theme_name

        except Exception as e:
            self.logger.warning(f"設定ファイルの更新に失敗しました: {e}")

    def _apply_fallback_theme(self, theme_name: str) -> bool:
        """フォールバックテーマを適用"""
        try:
            theme_data = self.qt_theme_config["available_themes"].get(theme_name)
            if not theme_data:
                return False

            # Qt-Theme-Manager形式からスタイルシートを生成
            stylesheet = self._generate_stylesheet_from_qt_theme(theme_data)

            if stylesheet:
                self.app.setStyleSheet(stylesheet)
                self.current_theme = theme_name
                self.logger.info(f"フォールバックテーマを適用しました: {theme_name}")
                self.theme_changed.emit(theme_name)
                return True
            else:
                self.logger.error(f"フォールバックテーマの適用に失敗しました: {theme_name}")
                return False

        except Exception as e:
            self.logger.error(f"フォールバックテーマ適用中にエラーが発生しました: {e}")
            return False

    def _generate_stylesheet_from_qt_theme(self, theme_data: Dict[str, Any]) -> str:
        """Qt-Theme-Manager形式のテーマデータからスタイルシートを生成"""
        try:
            # スタイルシートテンプレート
            template = """
QWidget {{
    background-color: {background};
    color: {text_color};
}}

QMainWindow {{
    background-color: {background};
}}

QMenuBar {{
    background-color: {menu_background};
    color: {menu_text};
    border: 1px solid {menu_border};
}}

QToolBar {{
    background-color: {toolbar_background};
    color: {toolbar_text};
    border: 1px solid {toolbar_border};
}}

QPushButton {{
    background-color: {button_background};
    color: {button_text};
    border: 1px solid {button_border};
    padding: 5px;
    border-radius: 3px;
}}

QPushButton:hover {{
    background-color: {button_hover};
}}

QPushButton:pressed {{
    background-color: {button_pressed};
}}

QTreeView, QListView {{
    background-color: {list_background};
    alternate-background-color: {list_alternate};
    color: {list_text};
    border: 1px solid {list_border};
    selection-background-color: {list_selection};
}}

QTreeView::item:alternate, QListView::item:alternate {{
    background-color: {list_alternate};
}}

QTreeView::item:selected, QListView::item:selected {{
    background-color: {list_selection};
}}

QTreeView::item:hover, QListView::item:hover {{
    background-color: {list_hover};
}}

QTextEdit, QLineEdit {{
    background-color: {input_background};
    color: {input_text};
    border: 1px solid {input_border};
    border-radius: 3px;
    padding: 3px;
}}

QTextEdit:focus, QLineEdit:focus {{
    border: 2px solid {input_focus};
}}

QScrollBar:vertical {{
    background-color: {scrollbar_background};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {scrollbar_handle};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {scrollbar_handle_hover};
}}
"""

            # テーマデータから値を抽出
            values = {
                'background': theme_data.get('backgroundColor', '#ffffff'),
                'text_color': theme_data.get('textColor', '#000000'),
                'menu_background': theme_data.get('menu', {}).get('background', '#eeeeee'),
                'menu_text': theme_data.get('menu', {}).get('text', '#000000'),
                'menu_border': theme_data.get('menu', {}).get('border', '#cccccc'),
                'toolbar_background': theme_data.get('toolbar', {}).get('background', '#eeeeee'),
                'toolbar_text': theme_data.get('toolbar', {}).get('text', '#000000'),
                'toolbar_border': theme_data.get('toolbar', {}).get('border', '#cccccc'),
                'button_background': theme_data.get('button', {}).get('background', '#cccccc'),
                'button_text': theme_data.get('button', {}).get('text', '#000000'),
                'button_border': theme_data.get('button', {}).get('border', '#aaaaaa'),
                'button_hover': theme_data.get('button', {}).get('hover', '#bbbbbb'),
                'button_pressed': theme_data.get('button', {}).get('pressed', '#bbbbbb'),
                'list_background': theme_data.get('list', {}).get('background', '#ffffff'),
                'list_alternate': theme_data.get('list', {}).get('alternate', '#f5f5f5'),
                'list_text': theme_data.get('list', {}).get('text', '#000000'),
                'list_border': theme_data.get('list', {}).get('border', '#cccccc'),
                'list_selection': theme_data.get('list', {}).get('selection', '#cccccc'),
                'list_hover': theme_data.get('list', {}).get('hover', '#dddddd'),
                'input_background': theme_data.get('input', {}).get('background', '#ffffff'),
                'input_text': theme_data.get('input', {}).get('text', '#000000'),
                'input_border': theme_data.get('input', {}).get('border', '#cccccc'),
                'input_focus': theme_data.get('input', {}).get('focus', '#0078d4'),
                'scrollbar_background': theme_data.get('scrollbar', {}).get('background', '#f0f0f0'),
                'scrollbar_handle': theme_data.get('scrollbar', {}).get('handle', '#cccccc'),
                'scrollbar_handle_hover': theme_data.get('scrollbar', {}).get('handle_hover', '#bbbbbb'),
            }

            return template.format(**values)

        except Exception as e:
            self.logger.error(f"スタイルシート生成中にエラーが発生しました: {e}")
            return ""

    # 他のメソッドは元のThemeManagerと同じ
    def get_available_themes(self) -> List[str]:
        """利用可能なテーマのリストを取得"""
        return self.available_themes.copy()

    def get_enabled_themes(self) -> List[str]:
        """有効なテーマのリストを取得"""
        return self.enabled_themes.copy()

    def set_enabled_themes(self, theme_names: List[str]) -> bool:
        """有効なテーマのリストを設定"""
        try:
            # 有効なテーマ名のみを受け入れ
            valid_themes = [name for name in theme_names if name in self.available_themes]
            self.enabled_themes = valid_themes
            self.logger.info(f"有効なテーマを設定しました: {valid_themes}")
            return True
        except Exception as e:
            self.logger.error(f"有効なテーマの設定に失敗しました: {e}")
            return False

    def get_current_theme(self) -> str:
        """現在のテーマを取得"""
        return self.current_theme

    def get_theme_info(self, theme_name: str) -> Dict[str, str]:
        """指定されたテーマの情報を取得"""
        return self.theme_info.get(theme_name, {})

    def set_theme(self, theme_name: str) -> bool:
        """テーマを設定（apply_themeのエイリアス）"""
        return self.apply_theme(theme_name)

    def cycle_theme(self) -> str:
        """テーマを循環切り替え"""
        try:
            current_index = self.available_themes.index(self.current_theme)
            next_index = (current_index + 1) % len(self.available_themes)
            next_theme = self.available_themes[next_index]

            if self.apply_theme(next_theme):
                return next_theme
            else:
                return self.current_theme
        except Exception as e:
            self.logger.error(f"テーマの循環切り替えに失敗しました: {e}")
            return self.current_theme

    def reload_themes(self) -> bool:
        """テーマ設定を再読み込み"""
        try:
            self.qt_theme_config = self._load_separated_theme_config()
            self.available_themes = list(self.qt_theme_config.get("available_themes", {}).keys())
            self.theme_info = self._build_qt_theme_info()
            self.enabled_themes = self.available_themes.copy()

            self.logger.info("テーマ設定を再読み込みしました")
            return True
        except Exception as e:
            self.logger.error(f"テーマ設定の再読み込みに失敗しました: {e}")
            return False
