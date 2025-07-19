#!/usr/bin/env python3
"""
PhotoGeoView のシンプルなテストアプリケーション
基本動作確認用
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt

from src.core.logger import setup_logging, get_logger
from src.core.settings import get_settings


class SimpleTestWindow(QMainWindow):
    """シンプルなテストウィンドウ"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)

        # ウィンドウ設定
        self.setWindowTitle("PhotoGeoView - テスト")
        self.setGeometry(100, 100, 600, 400)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QVBoxLayout(central_widget)

        # タイトル
        title_label = QLabel("PhotoGeoView テストアプリケーション")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)

        # ステータス表示
        self.status_label = QLabel("初期化中...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # テストボタン
        test_button = QPushButton("設定テスト")
        test_button.clicked.connect(self._test_settings)
        layout.addWidget(test_button)

        # 初期化
        self._init_components()

    def _init_components(self):
        """コンポーネントの初期化"""
        try:
            # 設定のテスト
            settings = get_settings()
            app_name = settings.get("app.name", "Unknown")
            version = settings.get("app.version", "Unknown")

            self.status_label.setText(
                f"アプリケーション: {app_name} v{version}\n初期化完了"
            )
            self.logger.info("シンプルテストウィンドウを初期化しました")

        except Exception as e:
            self.status_label.setText(f"初期化エラー: {e}")
            self.logger.error(f"初期化に失敗しました: {e}")

    def _test_settings(self):
        """設定テスト"""
        try:
            settings = get_settings()

            # 設定値を取得
            theme = settings.get("ui.theme_manager.current_theme", "dark")
            thumbnail_size = settings.get("ui.panels.thumbnail_size", 120)

            self.status_label.setText(
                f"現在のテーマ: {theme}\nサムネイルサイズ: {thumbnail_size}"
            )
            self.logger.info("設定テストを実行しました")

        except Exception as e:
            self.status_label.setText(f"設定テストエラー: {e}")
            self.logger.error(f"設定テストに失敗しました: {e}")


def main():
    """メイン関数"""
    # ログ設定の初期化
    setup_logging()
    logger = get_logger(__name__)

    try:
        logger.info("PhotoGeoView テストアプリケーションを開始します")

        # QApplicationの作成
        app = QApplication(sys.argv)
        app.setApplicationName("PhotoGeoView Test")
        app.setApplicationVersion("1.0.0")

        logger.info("QApplicationを初期化しました")

        # テストウィンドウの作成
        window = SimpleTestWindow()
        window.show()

        logger.info("テストウィンドウを表示しました")

        # イベントループの開始
        exit_code = app.exec()

        logger.info(f"テストアプリケーションを終了します（終了コード: {exit_code}）")
        return exit_code

    except Exception as e:
        logger.error(f"テストアプリケーションの起動に失敗しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
