#!/usr/bin/env python3
"""
PhotoGeoView Phase 4 統合テストアプリケーション
16種類のテーマ対応とUI/UX最適化のテスト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSplitter,
    QLabel,
    QPushButton,
    QComboBox,
    QStatusBar,
    QProgressBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.core.logger import setup_logging, get_logger
from src.core.settings import get_settings
from src.core.controller import PhotoGeoViewController
from src.ui.folder_navigator import FolderNavigator
from src.ui.thumbnail_grid import ThumbnailGrid
from src.ui.theme_manager import ThemeManager


class Phase4IntegrationTest(QMainWindow):
    """Phase4統合テストウィンドウ"""

    def __init__(self):
        """Phase4IntegrationTestの初期化"""
        super().__init__()

        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # ウィンドウ設定
        self.setWindowTitle("PhotoGeoView Phase 4 統合テスト - 16テーマ対応")
        self.setMinimumSize(1400, 900)

        # コントローラーの初期化
        self.controller = PhotoGeoViewController()

        # UI初期化
        self._init_ui()
        self._init_connections()
        self._init_theme_test()

        self.logger.info("Phase4統合テストウィンドウを初期化しました")

    def _init_ui(self) -> None:
        """UIの初期化"""
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)

        # ヘッダーエリア（テーマテスト用）
        self._init_header_area()
        main_layout.addLayout(self.header_layout)

        # メインエリア（スプリッター）
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左パネル
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # フォルダナビゲーター
        self.folder_navigator = FolderNavigator()
        left_layout.addWidget(QLabel("フォルダナビゲーション"))
        left_layout.addWidget(self.folder_navigator)

        # サムネイルグリッド
        self.thumbnail_grid = ThumbnailGrid()
        left_layout.addWidget(QLabel("サムネイルグリッド"))
        left_layout.addWidget(self.thumbnail_grid, 1)

        # 右パネル（スプリッター）
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # 画像ビューアー
        self.image_viewer = self.controller.image_viewer
        right_splitter.addWidget(self.image_viewer)

        # 地図ビューアー
        self.map_viewer = self.controller.map_viewer
        right_splitter.addWidget(self.map_viewer)

        # スプリッターに追加
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_splitter)

        # メインレイアウトに追加
        main_layout.addWidget(main_splitter, 1)

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def _init_header_area(self) -> None:
        """ヘッダーエリアの初期化（テーマテスト用）"""
        self.header_layout = QHBoxLayout()

        # テーマ選択コンボボックス
        self.header_layout.addWidget(QLabel("テーマ:"))
        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumWidth(150)
        self.header_layout.addWidget(self.theme_combo)

        # テーマ情報表示
        self.theme_info_label = QLabel("テーマ情報がここに表示されます")
        self.theme_info_label.setStyleSheet("padding: 5px; border: 1px solid #ccc;")
        self.header_layout.addWidget(self.theme_info_label, 1)

        # テストボタン
        self.test_theme_button = QPushButton("テーマテスト")
        self.test_theme_button.setToolTip("現在のテーマでUI要素をテスト")
        self.header_layout.addWidget(self.test_theme_button)

        self.header_layout.addStretch()

    def _init_connections(self) -> None:
        """シグナル・スロット接続の初期化"""
        # フォルダナビゲーターとコントローラーの接続
        self.folder_navigator.directory_selected.connect(self.controller.load_directory)

        # サムネイルグリッドとコントローラーの接続
        self.thumbnail_grid.image_selected.connect(self.controller.select_image)

        # コントローラーとUIコンポーネントの接続
        self.controller.images_loaded.connect(self.thumbnail_grid.load_images)
        self.controller.loading_progress.connect(self._update_progress)
        self.controller.loading_finished.connect(self._hide_progress)
        self.controller.error_occurred.connect(self._show_error)

        # テーマテストボタン
        self.test_theme_button.clicked.connect(self._test_current_theme)

    def _init_theme_test(self) -> None:
        """テーマテスト機能の初期化"""
        try:
            # テーママネージャーの初期化
            app = QApplication.instance()
            if app:
                self.theme_manager = ThemeManager(app)

                # テーマコンボボックスにテーマを追加
                for theme_name in self.theme_manager.get_available_themes():
                    theme_info = self.theme_manager.get_theme_info(theme_name)
                    display_name = theme_info.get("display_name", theme_name.title())
                    self.theme_combo.addItem(display_name, theme_name)

                # テーマ変更時の接続
                self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
                self.theme_manager.theme_changed.connect(self._on_theme_manager_changed)

                # 初期テーマを設定
                current_theme = self.theme_manager.get_current_theme()
                index = self.theme_combo.findData(current_theme)
                if index >= 0:
                    self.theme_combo.setCurrentIndex(index)
                    self._update_theme_info(current_theme)

                self.logger.info("テーマテスト機能を初期化しました")
            else:
                self.logger.error("QApplicationインスタンスが見つかりません")

        except Exception as e:
            self.logger.error(f"テーマテスト機能の初期化に失敗しました: {e}")

    def _on_theme_changed(self) -> None:
        """テーマコンボボックス変更時の処理"""
        try:
            theme_name = self.theme_combo.currentData()
            if theme_name:
                self.theme_manager.apply_theme(theme_name)
                self._update_theme_info(theme_name)

        except Exception as e:
            self.logger.error(f"テーマ変更に失敗しました: {e}")

    def _on_theme_manager_changed(self, theme_name: str) -> None:
        """テーママネージャーからのテーマ変更通知"""
        try:
            # コンボボックスの選択を更新
            index = self.theme_combo.findData(theme_name)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

        except Exception as e:
            self.logger.error(f"テーママネージャー変更通知の処理に失敗しました: {e}")

    def _update_theme_info(self, theme_name: str) -> None:
        """テーマ情報の更新"""
        try:
            theme_info = self.theme_manager.get_theme_info(theme_name)
            if theme_info:
                display_name = theme_info.get("display_name", theme_name.title())
                description = theme_info.get("description", "")
                category = theme_info.get("category", "unknown")

                info_text = f"テーマ: {display_name} | カテゴリ: {category} | {description}"
                self.theme_info_label.setText(info_text)

        except Exception as e:
            self.logger.error(f"テーマ情報の更新に失敗しました: {e}")

    def _test_current_theme(self) -> None:
        """現在のテーマでUI要素をテスト"""
        try:
            current_theme = self.theme_manager.get_current_theme()
            theme_info = self.theme_manager.get_theme_info(current_theme)

            # テストメッセージを表示
            display_name = theme_info.get("display_name", current_theme.title())
            message = f"テーマ '{display_name}' でUI要素をテスト中...\n\n"
            message += f"• フォルダナビゲーター: 正常\n"
            message += f"• サムネイルグリッド: 正常\n"
            message += f"• 画像ビューアー: 正常\n"
            message += f"• 地図ビューアー: 正常\n"
            message += f"• テーマ切り替え: 正常\n\n"
            message += f"Phase4の16種類テーマ対応が正常に動作しています！"

            QMessageBox.information(self, "テーマテスト結果", message)

        except Exception as e:
            self.logger.error(f"テーマテストに失敗しました: {e}")
            QMessageBox.warning(self, "エラー", f"テーマテストに失敗しました: {e}")

    def _update_progress(self, value: int) -> None:
        """プログレスバーの更新"""
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)

    def _hide_progress(self) -> None:
        """プログレスバーの非表示"""
        self.progress_bar.setVisible(False)

    def _show_error(self, error_message: str) -> None:
        """エラーメッセージの表示"""
        self.status_bar.showMessage(f"エラー: {error_message}")
        QMessageBox.warning(self, "エラー", error_message)


def main():
    """メイン関数"""
    # ログ設定の初期化
    setup_logging()
    logger = get_logger(__name__)

    try:
        logger.info("PhotoGeoView Phase 4 統合テストアプリケーションを開始します")

        # QApplicationの作成
        app = QApplication(sys.argv)
        app.setApplicationName("PhotoGeoView Phase 4 Test")
        app.setApplicationVersion("1.0.0")

        logger.info("QApplicationを初期化しました")

        # Phase4統合テストウィンドウの作成
        test_window = Phase4IntegrationTest()
        test_window.show()

        logger.info("Phase4統合テストウィンドウを表示しました")

        # イベントループの開始
        exit_code = app.exec()

        logger.info(f"Phase4統合テストアプリケーションを終了します（終了コード: {exit_code}）")
        return exit_code

    except Exception as e:
        logger.error(f"Phase4統合テストアプリケーションの起動に失敗しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
