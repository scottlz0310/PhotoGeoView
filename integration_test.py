#!/usr/bin/env python3
"""
PhotoGeoView Phase 3 統合テストアプリケーション
各モジュールの統合動作確認用
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
    QLabel,
    QPushButton,
    QSplitter,
    QFrame,
    QTextEdit,
    QProgressBar,
    QStatusBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.core.logger import setup_logging, get_logger
from src.core.settings import get_settings
from src.core.controller import PhotoGeoViewController
from src.ui.folder_navigator import FolderNavigator
from src.ui.thumbnail_grid import ThumbnailGrid
from src.modules.image_viewer import ImageViewer
from src.modules.map_viewer import MapViewer


class IntegrationTestWindow(QMainWindow):
    """統合テストウィンドウ"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # コントローラー
        self.controller = PhotoGeoViewController()

        # ウィンドウ設定
        self.setWindowTitle("PhotoGeoView - Phase 3 統合テスト")
        self.setGeometry(100, 100, 1400, 900)

        # UI初期化
        self._init_ui()
        self._init_connections()

        # 初期化
        self._init_components()

        self.logger.info("統合テストウィンドウを初期化しました")

    def _init_ui(self) -> None:
        """UIの初期化"""
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 左パネル（フォルダナビゲーション + サムネイル）
        self._init_left_panel()
        main_layout.addWidget(self.left_panel, 1)

        # 右パネル（画像表示 + 地図）
        self._init_right_panel()
        main_layout.addWidget(self.right_panel, 2)

        # ステータスバー
        self._init_status_bar()

    def _init_left_panel(self) -> None:
        """左パネルの初期化"""
        self.left_panel = QFrame()
        self.left_panel.setFrameStyle(QFrame.Shape.StyledPanel)

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # フォルダナビゲーター
        self.folder_navigator = FolderNavigator()
        left_layout.addWidget(self.folder_navigator, 1)

        # サムネイルグリッド
        self.thumbnail_grid = ThumbnailGrid()
        left_layout.addWidget(self.thumbnail_grid, 2)

    def _init_right_panel(self) -> None:
        """右パネルの初期化"""
        self.right_panel = QFrame()
        self.right_panel.setFrameStyle(QFrame.Shape.StyledPanel)

        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # 垂直スプリッター
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_layout.addWidget(self.right_splitter)

        # 画像ビューアー
        self.image_viewer = ImageViewer()
        self.right_splitter.addWidget(self.image_viewer)

        # 地図ビューアー
        self.map_viewer = MapViewer()
        self.right_splitter.addWidget(self.map_viewer)

        # スプリッターの比率を設定
        self.right_splitter.setSizes([400, 300])

    def _init_status_bar(self) -> None:
        """ステータスバーの初期化"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # 初期メッセージ
        self.status_bar.showMessage("準備完了")

    def _init_connections(self) -> None:
        """シグナル・スロット接続の初期化"""
        try:
            # フォルダナビゲーター接続
            self.folder_navigator.directory_changed.connect(self._on_directory_changed)

            # サムネイルグリッド接続
            self.thumbnail_grid.image_selected.connect(self._on_image_selected)
            self.thumbnail_grid.thumbnail_clicked.connect(self._on_thumbnail_clicked)

            # コントローラー接続
            self.controller.current_directory_changed.connect(
                self._on_controller_directory_changed
            )
            self.controller.image_list_updated.connect(self._on_image_list_updated)
            self.controller.selected_image_changed.connect(
                self._on_controller_image_selected
            )
            self.controller.thumbnail_loaded.connect(self._on_thumbnail_loaded)
            self.controller.image_loaded.connect(self._on_image_loaded)
            self.controller.exif_data_loaded.connect(self._on_exif_data_loaded)
            self.controller.gps_coordinates_found.connect(
                self._on_gps_coordinates_found
            )
            self.controller.loading_progress.connect(self._on_loading_progress)
            self.controller.loading_finished.connect(self._on_loading_finished)
            self.controller.error_occurred.connect(self._on_error_occurred)

            self.logger.debug("シグナル・スロット接続を初期化しました")

        except Exception as e:
            self.logger.error(f"シグナル・スロット接続の初期化に失敗しました: {e}")

    def _init_components(self) -> None:
        """コンポーネントの初期化"""
        try:
            # 初期ディレクトリを設定
            home_dir = str(Path.home())
            self.folder_navigator.set_directory(home_dir)

            self.logger.info("コンポーネントの初期化が完了しました")

        except Exception as e:
            self.logger.error(f"コンポーネントの初期化に失敗しました: {e}")

    def _on_directory_changed(self, directory_path: str) -> None:
        """
        ディレクトリ変更時の処理

        Args:
            directory_path: ディレクトリパス
        """
        try:
            self.logger.info(f"ディレクトリが変更されました: {directory_path}")

            # コントローラーにディレクトリを読み込ませる
            success = self.controller.load_directory(directory_path)

            if success:
                self.status_bar.showMessage(
                    f"ディレクトリを読み込みました: {directory_path}"
                )
            else:
                self.status_bar.showMessage(
                    f"ディレクトリの読み込みに失敗しました: {directory_path}"
                )

        except Exception as e:
            self.logger.error(f"ディレクトリ変更の処理に失敗しました: {e}")

    def _on_controller_directory_changed(self, directory_path: str) -> None:
        """
        コントローラーのディレクトリ変更時の処理

        Args:
            directory_path: ディレクトリパス
        """
        try:
            self.logger.debug(
                f"コントローラーのディレクトリが変更されました: {directory_path}"
            )

        except Exception as e:
            self.logger.error(
                f"コントローラーディレクトリ変更の処理に失敗しました: {e}"
            )

    def _on_image_list_updated(self, image_files: list) -> None:
        """
        画像リスト更新時の処理

        Args:
            image_files: 画像ファイルリスト
        """
        try:
            self.logger.info(f"画像リストが更新されました: {len(image_files)} ファイル")

            # サムネイルグリッドに画像リストを設定
            self.thumbnail_grid.set_image_files(image_files)

            self.status_bar.showMessage(
                f"画像ファイルを {len(image_files)} 個見つけました"
            )

        except Exception as e:
            self.logger.error(f"画像リスト更新の処理に失敗しました: {e}")

    def _on_image_selected(self, file_path: str) -> None:
        """
        画像選択時の処理

        Args:
            file_path: 画像ファイルパス
        """
        try:
            self.logger.info(f"画像が選択されました: {file_path}")

            # コントローラーに画像選択を通知
            self.controller.select_image(file_path)

        except Exception as e:
            self.logger.error(f"画像選択の処理に失敗しました: {e}")

    def _on_thumbnail_clicked(self, file_path: str) -> None:
        """
        サムネイルクリック時の処理

        Args:
            file_path: 画像ファイルパス
        """
        try:
            self.logger.debug(f"サムネイルがクリックされました: {file_path}")

        except Exception as e:
            self.logger.error(f"サムネイルクリックの処理に失敗しました: {e}")

    def _on_controller_image_selected(self, file_path: str) -> None:
        """
        コントローラーの画像選択時の処理

        Args:
            file_path: 画像ファイルパス
        """
        try:
            self.logger.debug(f"コントローラーで画像が選択されました: {file_path}")

        except Exception as e:
            self.logger.error(f"コントローラー画像選択の処理に失敗しました: {e}")

    def _on_thumbnail_loaded(self, file_path: str, pixmap) -> None:
        """
        サムネイル読み込み完了時の処理

        Args:
            file_path: 画像ファイルパス
            pixmap: サムネイルのQPixmap
        """
        try:
            self.logger.debug(f"サムネイルが読み込まれました: {file_path}")

            # サムネイルグリッドにサムネイルを追加
            self.thumbnail_grid.add_thumbnail(file_path, pixmap)

        except Exception as e:
            self.logger.error(f"サムネイル読み込み完了の処理に失敗しました: {e}")

    def _on_image_loaded(self, file_path: str, pixmap) -> None:
        """
        画像読み込み完了時の処理

        Args:
            file_path: 画像ファイルパス
            pixmap: 画像のQPixmap
        """
        try:
            self.logger.debug(f"画像が読み込まれました: {file_path}")

        except Exception as e:
            self.logger.error(f"画像読み込み完了の処理に失敗しました: {e}")

    def _on_exif_data_loaded(self, file_path: str, exif_data: dict) -> None:
        """
        EXIFデータ読み込み完了時の処理

        Args:
            file_path: 画像ファイルパス
            exif_data: EXIFデータ
        """
        try:
            self.logger.debug(f"EXIFデータが読み込まれました: {file_path}")

        except Exception as e:
            self.logger.error(f"EXIFデータ読み込み完了の処理に失敗しました: {e}")

    def _on_gps_coordinates_found(self, file_path: str, coordinates: tuple) -> None:
        """
        GPS座標発見時の処理

        Args:
            file_path: 画像ファイルパス
            coordinates: GPS座標 (緯度, 経度)
        """
        try:
            self.logger.info(f"GPS座標が発見されました: {file_path} - {coordinates}")

        except Exception as e:
            self.logger.error(f"GPS座標発見の処理に失敗しました: {e}")

    def _on_loading_progress(self, current: int, total: int) -> None:
        """
        読み込み進捗時の処理

        Args:
            current: 現在の進捗
            total: 全体の数
        """
        try:
            # プログレスバーを表示・更新
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

            # ステータスバーに進捗を表示
            self.status_bar.showMessage(f"読み込み中... {current}/{total}")

        except Exception as e:
            self.logger.error(f"読み込み進捗の処理に失敗しました: {e}")

    def _on_loading_finished(self) -> None:
        """読み込み完了時の処理"""
        try:
            # プログレスバーを非表示
            self.progress_bar.setVisible(False)

            # ステータスバーに完了メッセージを表示
            image_count = len(self.controller.get_image_files())
            self.status_bar.showMessage(f"読み込み完了: {image_count} ファイル")

        except Exception as e:
            self.logger.error(f"読み込み完了の処理に失敗しました: {e}")

    def _on_error_occurred(self, error_type: str, error_message: str) -> None:
        """
        エラー発生時の処理

        Args:
            error_type: エラータイプ
            error_message: エラーメッセージ
        """
        try:
            self.logger.error(f"エラーが発生しました: {error_type} - {error_message}")

            # ステータスバーにエラーメッセージを表示
            self.status_bar.showMessage(f"エラー: {error_message}")

        except Exception as e:
            self.logger.error(f"エラー発生の処理に失敗しました: {e}")

    def closeEvent(self, event) -> None:
        """クローズイベント"""
        try:
            # キャッシュをクリア
            self.controller.clear_cache()

            # 設定を保存
            self.settings.save()

            self.logger.info("統合テストウィンドウを終了します")

        except Exception as e:
            self.logger.error(f"クローズイベントの処理に失敗しました: {e}")

        super().closeEvent(event)


def main():
    """メイン関数"""
    # ログ設定の初期化
    setup_logging()
    logger = get_logger(__name__)

    try:
        logger.info("PhotoGeoView Phase 3 統合テストアプリケーションを開始します")

        # QApplicationの作成
        app = QApplication(sys.argv)
        app.setApplicationName("PhotoGeoView Integration Test")
        app.setApplicationVersion("1.0.0")

        logger.info("QApplicationを初期化しました")

        # 統合テストウィンドウの作成
        window = IntegrationTestWindow()
        window.show()

        logger.info("統合テストウィンドウを表示しました")

        # イベントループの開始
        exit_code = app.exec()

        logger.info(
            f"統合テストアプリケーションを終了します（終了コード: {exit_code}）"
        )
        return exit_code

    except Exception as e:
        logger.error(f"統合テストアプリケーションの起動に失敗しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
