"""
統一された設定管理システム
アプリ設定、ユーザー設定、セッション設定を分離管理
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from platformdirs import user_config_dir

from .logger import get_logger


class ConfigManager:
    """統一設定管理クラス"""

    def __init__(self):
        """設定管理の初期化"""
        self.logger = get_logger(__name__)
        self.app_name = "PhotoGeoView"

        # ファイルパス設定
        self.app_config_path = Path("config/app_config.json")
        self.user_config_dir = Path(user_config_dir(self.app_name))
        self.user_settings_path = self.user_config_dir / "user_settings.json"
        self.session_cache_path = self.user_config_dir / "session_cache.json"

        # 設定データ
        self._app_config: Dict[str, Any] = {}
        self._user_settings: Dict[str, Any] = {}
        self._session_cache: Dict[str, Any] = {}

        # 設定読み込み
        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """全設定ファイルの読み込み"""
        self._load_app_config()
        self._load_user_settings()
        self._load_session_cache()

    def _load_app_config(self) -> None:
        """アプリケーション設定の読み込み"""
        try:
            if self.app_config_path.exists():
                with open(self.app_config_path, 'r', encoding='utf-8') as f:
                    self._app_config = json.load(f)
                self.logger.info(f"アプリ設定を読み込みました: {self.app_config_path}")
            else:
                self.logger.error(f"アプリ設定ファイルが見つかりません: {self.app_config_path}")
                self._app_config = {}
        except Exception as e:
            self.logger.error(f"アプリ設定の読み込みに失敗: {e}")
            self._app_config = {}

    def _load_user_settings(self) -> None:
        """ユーザー設定の読み込み"""
        try:
            if self.user_settings_path.exists():
                with open(self.user_settings_path, 'r', encoding='utf-8') as f:
                    self._user_settings = json.load(f)
                self.logger.debug(f"ユーザー設定を読み込みました: {self.user_settings_path}")
            else:
                self._user_settings = self._create_default_user_settings()
                self._save_user_settings()
                self.logger.info("デフォルトユーザー設定を作成しました")
        except Exception as e:
            self.logger.error(f"ユーザー設定の読み込みに失敗: {e}")
            self._user_settings = self._create_default_user_settings()

    def _load_session_cache(self) -> None:
        """セッションキャッシュの読み込み"""
        try:
            if self.session_cache_path.exists():
                with open(self.session_cache_path, 'r', encoding='utf-8') as f:
                    self._session_cache = json.load(f)
                self.logger.debug("セッションキャッシュを読み込みました")
            else:
                self._session_cache = {}
        except Exception as e:
            self.logger.warning(f"セッションキャッシュの読み込みに失敗: {e}")
            self._session_cache = {}

    def _create_default_user_settings(self) -> Dict[str, Any]:
        """デフォルトユーザー設定の作成"""
        app_defaults = self.get_app_config("ui.defaults", {})
        return {
            "ui": {
                "theme": app_defaults.get("theme", "dark"),
                "window": app_defaults.get("window", {
                    "width": 1200,
                    "height": 800,
                    "x": 100,
                    "y": 100,
                    "maximized": False
                }),
                "panels": app_defaults.get("panels", {
                    "left_panel_width": 300,
                    "right_panel_width": 400,
                    "thumbnail_size": 120
                }),
                "theme_manager": {
                    "current_theme": "dark",
                    "available_themes": [
                        "dark", "light", "blue", "green", "purple",
                        "orange", "red", "pink", "yellow", "brown",
                        "gray", "cyan", "teal", "indigo", "lime", "amber"
                    ]
                }
            }
        }

    def get_app_config(self, key: str, default: Any = None) -> Any:
        """アプリケーション設定の取得"""
        return self._get_nested_value(self._app_config, key, default)

    def get_user_setting(self, key: str, default: Any = None) -> Any:
        """ユーザー設定の取得"""
        return self._get_nested_value(self._user_settings, key, default)

    def set_user_setting(self, key: str, value: Any) -> None:
        """ユーザー設定の設定"""
        self._set_nested_value(self._user_settings, key, value)
        self._save_user_settings()

    def get_session_data(self, key: str, default: Any = None) -> Any:
        """セッションデータの取得"""
        return self._get_nested_value(self._session_cache, key, default)

    def set_session_data(self, key: str, value: Any) -> None:
        """セッションデータの設定"""
        self._set_nested_value(self._session_cache, key, value)
        self._save_session_cache()

    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """ネストされた辞書から値を取得"""
        keys = key.split('.')
        current: Any = data

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """ネストされた辞書に値を設定"""
        keys = key.split('.')
        current: Any = data

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def _save_user_settings(self) -> None:
        """ユーザー設定の保存"""
        try:
            self.user_config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.user_settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._user_settings, f, indent=4, ensure_ascii=False)
            self.logger.debug("ユーザー設定を保存しました")
        except Exception as e:
            self.logger.error(f"ユーザー設定の保存に失敗: {e}")

    def _save_session_cache(self) -> None:
        """セッションキャッシュの保存"""
        try:
            self.user_config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.session_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._session_cache, f, indent=4, ensure_ascii=False)
            self.logger.debug("セッションキャッシュを保存しました")
        except Exception as e:
            self.logger.error(f"セッションキャッシュの保存に失敗: {e}")


# グローバル設定管理インスタンス
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """設定管理インスタンスの取得"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
