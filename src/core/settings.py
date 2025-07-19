"""
アプリケーション設定の管理を行うモジュール
PhotoGeoView プロジェクト用の設定機能を提供
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .logger import get_logger


class Settings:
    """アプリケーション設定管理クラス"""

    def __init__(self, config_path: str = "config/config.json"):
        """
        Settingsの初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.logger = get_logger(__name__)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """設定ファイルの読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self.logger.info(f"設定ファイルを読み込みました: {self.config_path}")
            else:
                self._create_default_config()
                self.logger.warning(f"設定ファイルが見つからないため、デフォルト設定を作成しました: {self.config_path}")
        except Exception as e:
            self.logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            self._create_default_config()

    def _create_default_config(self) -> None:
        """デフォルト設定の作成"""
        self._config = {
            "app": {
                "name": "PhotoGeoView",
                "version": "1.0.0",
                "theme": "dark",
                "language": "ja"
            },
            "ui": {
                "window": {
                    "width": 1200,
                    "height": 800,
                    "x": 100,
                    "y": 100,
                    "maximized": False
                },
                "panels": {
                    "left_panel_width": 300,
                    "right_panel_width": 400,
                    "thumbnail_size": 120
                },
                "theme_manager": {
                    "current_theme": "dark",
                    "available_themes": [
                        "dark", "light", "blue", "green", "purple", "orange",
                        "red", "pink", "yellow", "brown", "gray", "cyan",
                        "teal", "indigo", "lime", "amber"
                    ]
                }
            },
            "paths": {
                "last_directory": "",
                "thumbnail_cache": "cache/thumbnails",
                "logs": "logs"
            },
            "map": {
                "default_zoom": 10,
                "default_center": [35.6762, 139.6503],
                "tile_layer": "OpenStreetMap"
            },
            "logging": {
                "level": "INFO",
                "file_output": True,
                "console_output": True,
                "max_file_size": 10485760,
                "backup_count": 5
            }
        }
        self.save_config()

    def save_config(self) -> None:
        """設定ファイルの保存"""
        try:
            # 設定ディレクトリの作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"設定ファイルを保存しました: {self.config_path}")
        except Exception as e:
            self.logger.error(f"設定ファイルの保存に失敗しました: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値の取得

        Args:
            key: 設定キー（ドット区切りでネストしたキーも指定可能）
            default: デフォルト値

        Returns:
            設定値
        """
        try:
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        設定値の設定

        Args:
            key: 設定キー（ドット区切りでネストしたキーも指定可能）
            value: 設定値
        """
        try:
            keys = key.split('.')
            config = self._config

            # 最後のキー以外を辿る
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 最後のキーに値を設定
            config[keys[-1]] = value
            self.logger.debug(f"設定値を更新しました: {key} = {value}")
        except Exception as e:
            self.logger.error(f"設定値の設定に失敗しました: {key} = {value}, エラー: {e}")

    def get_window_settings(self) -> Dict[str, Any]:
        """
        ウィンドウ設定の取得

        Returns:
            ウィンドウ設定辞書
        """
        return self.get("ui.window", {})

    def set_window_settings(self, settings: Dict[str, Any]) -> None:
        """
        ウィンドウ設定の保存

        Args:
            settings: ウィンドウ設定辞書
        """
        self.set("ui.window", settings)
        self.save_config()

    def get_theme_settings(self) -> Dict[str, Any]:
        """
        テーマ設定の取得

        Returns:
            テーマ設定辞書
        """
        return self.get("ui.theme_manager", {})

    def set_current_theme(self, theme: str) -> None:
        """
        現在のテーマを設定

        Args:
            theme: テーマ名
        """
        self.set("ui.theme_manager.current_theme", theme)
        self.save_config()

    def get_last_directory(self) -> str:
        """
        最後に開いたディレクトリの取得

        Returns:
            ディレクトリパス
        """
        return self.get("paths.last_directory", "")

    def set_last_directory(self, directory: str) -> None:
        """
        最後に開いたディレクトリを設定

        Args:
            directory: ディレクトリパス
        """
        self.set("paths.last_directory", directory)
        self.save_config()

    def get_map_settings(self) -> Dict[str, Any]:
        """
        地図設定の取得

        Returns:
            地図設定辞書
        """
        return self.get("map", {})

    def get_thumbnail_size(self) -> int:
        """
        サムネイルサイズの取得

        Returns:
            サムネイルサイズ
        """
        return self.get("ui.panels.thumbnail_size", 120)

    def set_thumbnail_size(self, size: int) -> None:
        """
        サムネイルサイズを設定

        Args:
            size: サムネイルサイズ
        """
        self.set("ui.panels.thumbnail_size", size)
        self.save_config()


# グローバル設定インスタンス
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    設定インスタンスを取得する関数

    Returns:
        Settings: 設定インスタンス
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
