#!/usr/bin/env python3
"""
PhotoGeoView アプリケーションのエントリーポイント
写真のEXIF情報から撮影場所を抽出し、地図上に表示する写真管理アプリケーション
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.core.logger import setup_logging, get_logger
from src.core.settings import get_settings
from src.ui.main_window import MainWindow


def main():
    """メイン関数"""
    # ログ設定の初期化
    setup_logging()
    logger = get_logger(__name__)

    try:
        logger.info("PhotoGeoView アプリケーションを開始します")

        # 設定の初期化
        settings = get_settings()
        logger.info("設定を読み込みました")

        # QApplicationの作成
        app = QApplication(sys.argv)
        app.setApplicationName("PhotoGeoView")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("PhotoGeoView Team")

        # アプリケーション設定
        # PyQt6では高DPI設定が自動的に処理されるため、明示的な設定は不要

        logger.info("QApplicationを初期化しました")

        # メインウィンドウの作成
        main_window = MainWindow()
        main_window.show()

        logger.info("メインウィンドウを表示しました")

        # イベントループの開始
        exit_code = app.exec()

        logger.info(f"アプリケーションを終了します（終了コード: {exit_code}）")
        return exit_code

    except Exception as e:
        logger.error(f"アプリケーションの起動に失敗しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
