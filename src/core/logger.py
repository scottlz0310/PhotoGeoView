"""
ログ設定と管理を行うモジュール
PhotoGeoView プロジェクト用のログ機能を提供
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional


class LoggerManager:
    """ログ管理クラス"""

    def __init__(self, config_path: Optional[str] = None):
        """
        LoggerManagerの初期化

        Args:
            config_path: ログ設定ファイルのパス
        """
        self.config_path = config_path or "config/logging.json"
        self._setup_logging()

    def _setup_logging(self) -> None:
        """ログ設定の初期化"""
        try:
            # ログディレクトリの作成
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # 設定ファイルが存在する場合は読み込み
            if os.path.exists(self.config_path):
                import json
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # ログファイルパスの調整
                for handler in config.get('handlers', {}).values():
                    if 'filename' in handler:
                        handler['filename'] = str(Path(handler['filename']))

                logging.config.dictConfig(config)
                logging.getLogger(__name__).info("ログ設定を読み込みました")
            else:
                # デフォルト設定
                self._setup_default_logging()
                logging.getLogger(__name__).warning("ログ設定ファイルが見つからないため、デフォルト設定を使用します")

        except Exception as e:
            # フォールバック設定
            self._setup_fallback_logging()
            logging.getLogger(__name__).error(f"ログ設定の初期化に失敗しました: {e}")

    def _setup_default_logging(self) -> None:
        """デフォルトログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/app.log', encoding='utf-8')
            ]
        )

    def _setup_fallback_logging(self) -> None:
        """フォールバックログ設定"""
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )

    def get_logger(self, name: str) -> logging.Logger:
        """
        指定された名前のロガーを取得

        Args:
            name: ロガー名

        Returns:
            logging.Logger: ロガーインスタンス
        """
        return logging.getLogger(name)


# グローバルロガーマネージャーインスタンス
_logger_manager: Optional[LoggerManager] = None


def get_logger(name: str) -> logging.Logger:
    """
    ロガーを取得する関数

    Args:
        name: ロガー名

    Returns:
        logging.Logger: ロガーインスタンス
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager.get_logger(name)


def setup_logging(config_path: Optional[str] = None) -> None:
    """
    ログ設定を初期化する関数

    Args:
        config_path: ログ設定ファイルのパス
    """
    global _logger_manager
    _logger_manager = LoggerManager(config_path)
