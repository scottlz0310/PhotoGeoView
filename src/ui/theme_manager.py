"""
テーマ管理機能を提供するモジュール
Qt-Theme-Managerを使用した16種類のテーマ対応
外部JSONファイルによるテーマ設定管理
"""

import json
import os
from typing import List, Dict
from pathlib import Path

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

        # テーマ設定ファイルのパス
        self.theme_config_path = Path(__file__).parent.parent.parent / "config" / "theme_styles.json"
        
        # テーマ設定を読み込み
        self.theme_config = self._load_theme_config()
        
        # 利用可能なテーマリストを設定から取得
        self.available_themes = list(self.theme_config.get("theme_styles", {}).keys())
        
        # テーマ情報辞書を設定ファイルから構築
        self.theme_info = self._build_theme_info()

        # 現在のテーマ
        self.current_theme = self.settings.get("ui.theme_manager.current_theme", "dark")

        # 有効なテーマリスト（設定から読み込み、デフォルトは全テーマ有効）
        self.enabled_themes = self.settings.get("ui.theme_manager.enabled_themes", self.available_themes.copy())

        # 有効なテーマリストの検証（不正なテーマ名を除去）
        self.enabled_themes = [theme for theme in self.enabled_themes if theme in self.available_themes]
        if not self.enabled_themes:  # 有効なテーマがない場合はダークテーマを強制追加
            self.enabled_themes = ["dark"]

        # Qt-Theme-Managerの初期化
        self._init_theme_manager()

        # 初期テーマの適用
        self.apply_theme(self.current_theme)

    def _load_theme_config(self) -> Dict:
        """テーマ設定ファイルを読み込み"""
        try:
            if self.theme_config_path.exists():
                with open(self.theme_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"テーマ設定ファイルを読み込みました: {self.theme_config_path}")
                return config
            else:
                self.logger.warning(f"テーマ設定ファイルが見つかりません: {self.theme_config_path}")
                return self._get_default_theme_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"テーマ設定ファイルのJSON解析に失敗しました: {e}")
            return self._get_default_theme_config()
        except Exception as e:
            self.logger.error(f"テーマ設定ファイルの読み込みに失敗しました: {e}")
            return self._get_default_theme_config()

    def _get_default_theme_config(self) -> Dict:
        """デフォルトのテーマ設定を返す"""
        return {
            "theme_styles": {
                "dark": {
                    "name": "ダーク",
                    "description": "モダンなダークテーマ",
                    "category": "dark",
                    "colors": {
                        "background": "#2b2b2b",
                        "foreground": "#ffffff",
                        "menu_background": "#3c3c3c",
                        "button_background": "#4a4a4a",
                        "button_hover": "#5a5a5a",
                        "border": "#555555",
                        "input_background": "#2b2b2b"
                    }
                },
                "light": {
                    "name": "ライト",
                    "description": "クリーンなライトテーマ",
                    "category": "light",
                    "colors": {
                        "background": "#f0f0f0",
                        "foreground": "#000000",
                        "menu_background": "#e0e0e0",
                        "button_background": "#d0d0d0",
                        "button_hover": "#c0c0c0",
                        "border": "#b0b0b0",
                        "input_background": "#ffffff"
                    }
                }
            },
            "default_stylesheet_template": "QWidget { background-color: {background}; color: {foreground}; }"
        }

    def _build_theme_info(self) -> Dict:
        """テーマ設定からテーマ情報辞書を構築"""
        theme_info = {}
        theme_styles = self.theme_config.get("theme_styles", {})
        
        for theme_name, theme_data in theme_styles.items():
            theme_info[theme_name] = {
                "display_name": theme_data.get("name", theme_name.title()),
                "description": theme_data.get("description", f"{theme_name}テーマ"),
                "category": theme_data.get("category", "color")
            }
        
        return theme_info

    def _init_theme_manager(self) -> None:
        """Qt-Theme-Managerの初期化"""
        try:
            # qt-theme-managerのインポート
            from theme_manager.qt.controller import ThemeController

            # テストスクリプトと同じ方法で初期化（デフォルト設定を使用）
            self.qt_theme_manager = ThemeController()
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
                success = self.qt_theme_manager.set_theme(theme_name)
                if success:
                    # アプリケーション全体にテーマを適用
                    self.qt_theme_manager.apply_theme_to_application()
                    self.logger.info(
                        f"Qt-Theme-Managerでテーマを適用しました: {theme_name}"
                    )
                else:
                    # テーマ適用に失敗した場合はフォールバックを使用
                    self._apply_fallback_theme(theme_name)
                    self.logger.warning(
                        f"Qt-Theme-Managerでのテーマ適用に失敗、フォールバックを使用: {theme_name}"
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
        JSONファイルから動的にスタイルシートを生成

        Args:
            theme_name: テーマ名
        """
        try:
            theme_styles = self.theme_config.get("theme_styles", {})
            
            if theme_name in theme_styles:
                theme_data = theme_styles[theme_name]
                colors = theme_data.get("colors", {})
                
                # カスタムテンプレートがあれば使用、なければデフォルトテンプレートを使用
                template = theme_data.get("stylesheet_template", 
                                        self.theme_config.get("default_stylesheet_template", ""))
                
                # カラー値でテンプレートを置換
                stylesheet = template.format(**colors)
                
                self.app.setStyleSheet(stylesheet)
                self.logger.debug(f"フォールバックテーマを適用しました: {theme_name}")
            else:
                # 指定されたテーマが見つからない場合はライトテーマにフォールバック
                self.logger.warning(f"テーマ '{theme_name}' が見つかりません。ライトテーマを使用します。")
                if "light" in theme_styles:
                    self._apply_fallback_theme("light")
                else:
                    # 最低限のスタイルを適用
                    self.app.setStyleSheet("QWidget { background-color: #f0f0f0; color: #000000; }")
                    
        except Exception as e:
            self.logger.error(f"フォールバックテーマの適用に失敗しました: {e}")
            # 緊急フォールバック: 最低限のスタイル
            self.app.setStyleSheet("QWidget { background-color: #f0f0f0; color: #000000; }")

    def cycle_theme(self) -> str:
        """
        有効なテーマを循環切り替え

        Returns:
            新しいテーマ名
        """
        try:
            # 有効なテーマのみを対象とする
            if not self.enabled_themes:
                self.logger.warning("有効なテーマがありません")
                return self.current_theme

            # 現在のテーマが有効リストにない場合は最初の有効テーマを選択
            if self.current_theme not in self.enabled_themes:
                new_theme = self.enabled_themes[0]
            else:
                current_index = self.enabled_themes.index(self.current_theme)
                next_index = (current_index + 1) % len(self.enabled_themes)
                new_theme = self.enabled_themes[next_index]

            self.apply_theme(new_theme)
            return new_theme

        except Exception as e:
            self.logger.error(f"テーマの循環切り替えに失敗しました: {e}")
            return self.current_theme

    def get_enabled_themes(self) -> List[str]:
        """
        有効なテーマリストを取得

        Returns:
            有効なテーマのリスト
        """
        return self.enabled_themes.copy()

    def set_enabled_themes(self, themes: List[str]) -> bool:
        """
        有効なテーマリストを設定

        Args:
            themes: 有効にするテーマのリスト

        Returns:
            設定成功の場合True
        """
        try:
            # 有効なテーマ名のみをフィルタリング
            valid_themes = [theme for theme in themes if theme in self.available_themes]

            if not valid_themes:
                self.logger.warning("有効なテーマが指定されていません。ダークテーマを追加します。")
                valid_themes = ["dark"]

            self.enabled_themes = valid_themes

            # 設定に保存
            self.settings.set("ui.theme_manager.enabled_themes", self.enabled_themes)

            # 現在のテーマが無効になった場合は最初の有効テーマに切り替え
            if self.current_theme not in self.enabled_themes:
                self.apply_theme(self.enabled_themes[0])

            self.logger.info(f"有効なテーマを設定しました: {valid_themes}")
            return True

        except Exception as e:
            self.logger.error(f"有効なテーマの設定に失敗しました: {e}")
            return False



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
                # 正しいメソッド名を使用
                success = self.qt_theme_manager.apply_theme_to_widget(widget)
                if not success:
                    # テーマを一時的に設定してからウィジェットに適用
                    self.qt_theme_manager.set_theme(theme_name, save_settings=False)
                    success = self.qt_theme_manager.apply_theme_to_widget(widget)
                return success
            else:
                # フォールバック: 現在のアプリケーションスタイルを適用
                # (個別ウィジェットへの適用は制限的)
                self._apply_fallback_theme(theme_name)
                return True

        except Exception as e:
            self.logger.error(f"ウィジェットへのテーマ適用に失敗しました: {e}")
            return False

    def get_theme_info(self, theme_name: str) -> Dict[str, str]:
        """
        テーマ情報を取得

        Args:
            theme_name: テーマ名

        Returns:
            テーマ情報辞書
        """
        if theme_name in self.theme_info:
            return self.theme_info[theme_name].copy()
        else:
            return {
                "display_name": theme_name.title(),
                "description": f"{theme_name}テーマ",
                "category": "unknown",
            }

    def _get_theme_display_name(self, theme_name: str) -> str:
        """
        テーマの表示名を取得

        Args:
            theme_name: テーマ名

        Returns:
            表示名
        """
        if theme_name in self.theme_info:
            return self.theme_info[theme_name]["display_name"]
        else:
            return theme_name.title()

    def _get_theme_description(self, theme_name: str) -> str:
        """
        テーマの説明を取得

        Args:
            theme_name: テーマ名

        Returns:
            説明文
        """
        if theme_name in self.theme_info:
            return self.theme_info[theme_name]["description"]
        else:
            return f"{theme_name}テーマ"

    def reload_theme_config(self) -> bool:
        """テーマ設定ファイルを再読み込み"""
        try:
            old_themes = set(self.available_themes)
            self.theme_config = self._load_theme_config()
            self.available_themes = list(self.theme_config.get("theme_styles", {}).keys())
            self.theme_info = self._build_theme_info()
            
            new_themes = set(self.available_themes)
            
            # 有効テーマリストを更新（削除されたテーマを除外）
            self.enabled_themes = [theme for theme in self.enabled_themes if theme in self.available_themes]
            if not self.enabled_themes:
                self.enabled_themes = ["dark"] if "dark" in self.available_themes else self.available_themes[:1]
            
            # 現在のテーマが無効になった場合は最初の有効テーマに切り替え
            if self.current_theme not in self.available_themes:
                self.apply_theme(self.enabled_themes[0])
            
            # 変更をログに記録
            added = new_themes - old_themes
            removed = old_themes - new_themes
            if added:
                self.logger.info(f"新しいテーマが追加されました: {added}")
            if removed:
                self.logger.info(f"テーマが削除されました: {removed}")
                
            self.logger.info("テーマ設定ファイルを再読み込みしました")
            return True
            
        except Exception as e:
            self.logger.error(f"テーマ設定ファイルの再読み込みに失敗しました: {e}")
            return False

    def get_theme_colors(self, theme_name: str) -> Dict[str, str]:
        """指定したテーマの色設定を取得"""
        theme_styles = self.theme_config.get("theme_styles", {})
        if theme_name in theme_styles:
            return theme_styles[theme_name].get("colors", {})
        return {}

    def save_custom_theme(self, theme_name: str, theme_data: Dict) -> bool:
        """カスタムテーマを設定ファイルに保存"""
        try:
            if "theme_styles" not in self.theme_config:
                self.theme_config["theme_styles"] = {}
                
            self.theme_config["theme_styles"][theme_name] = theme_data
            
            # ファイルに保存
            with open(self.theme_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.theme_config, f, ensure_ascii=False, indent=2)
                
            # メモリ内の設定を更新
            self.available_themes = list(self.theme_config.get("theme_styles", {}).keys())
            self.theme_info = self._build_theme_info()
            
            self.logger.info(f"カスタムテーマを保存しました: {theme_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"カスタムテーマの保存に失敗しました: {e}")
            return False
