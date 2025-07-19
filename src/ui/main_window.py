"""
メインウィンドウの実装
PhotoGeoView のメインウィンドウクラス
"""

import sys
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QPushButton,
    QLineEdit,
    QTreeView,
    QListView,
    QTextEdit,
    QFrame,
    QApplication,
    QFileDialog,
    QMessageBox,
    QMenu,
    QToolBar,
    QStatusBar,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.core.utils import ensure_directory_exists
from src.core.controller import PhotoGeoViewController
from .theme_manager import ThemeManager
from .folder_navigator import FolderNavigator
from .thumbnail_grid import ThumbnailGrid


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""

    # シグナル定義
    file_selected = pyqtSignal(str)  # ファイル選択時に発信
    directory_changed = pyqtSignal(str)  # ディレクトリ変更時に発信

    def __init__(self):
        """MainWindowの初期化"""
        super().__init__()

        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # ウィンドウ設定
        self.setWindowTitle("PhotoGeoView")
        self.setMinimumSize(1200, 800)

        # コントローラーの初期化
        self.controller = PhotoGeoViewController()

        # ウィジェット初期化
        self._init_widgets()
        self._init_layout()
        self._init_connections()
        self._init_theme()

        # ウィンドウ状態の復元
        self._restore_window_state()

        self.logger.info("メインウィンドウを初期化しました")

    def _init_widgets(self) -> None:
        """ウィジェットの初期化"""
        # 中央ウィジェット
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # メインレイアウト
        self.main_layout = QVBoxLayout(self.central_widget)

        # メインエリア（スプリッター）
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左パネル
        self._init_left_panel()

        # 右パネル（スプリッター）
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self._init_right_panels()

        # ステータスバー
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # メニューバー
        self._init_menu_bar()

        # ツールバー
        self._init_tool_bar()

    def _init_header_area(self) -> None:
        """ヘッダーエリアの初期化"""
        # ヘッダーフレーム
        self.header_frame = QFrame()
        self.header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.header_layout = QHBoxLayout(self.header_frame)

        # アドレスバー
        self.address_label = QLabel("アドレス:")
        self.address_edit = QLineEdit()
        self.address_edit.setReadOnly(True)
        self.address_edit.setPlaceholderText("フォルダを選択してください")

        # フォルダ選択ボタン
        self.folder_button = QPushButton("フォルダ選択")
        self.folder_button.setIcon(QIcon("assets/icons/folder.png"))

        # ナビゲーションボタン
        self.back_button = QPushButton("←")
        self.back_button.setToolTip("戻る")
        self.forward_button = QPushButton("→")
        self.forward_button.setToolTip("進む")
        self.up_button = QPushButton("↑")
        self.up_button.setToolTip("上位フォルダ")

        # テーマ切り替えボタン
        self.theme_button = QPushButton("テーマ")
        self.theme_button.setToolTip("テーマ切り替え（右クリックで選択）")

        # ヘッダーレイアウトに追加
        self.header_layout.addWidget(self.address_label)
        self.header_layout.addWidget(self.address_edit, 1)
        self.header_layout.addWidget(self.folder_button)
        self.header_layout.addWidget(self.back_button)
        self.header_layout.addWidget(self.forward_button)
        self.header_layout.addWidget(self.up_button)
        self.header_layout.addWidget(self.theme_button)

        # メインレイアウトに追加
        self.main_layout.addWidget(self.header_frame)

    def _init_left_panel(self) -> None:
        """左パネルの初期化"""
        # 左パネルフレーム
        self.left_panel = QFrame()
        self.left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        self.left_layout = QVBoxLayout(self.left_panel)

        # フォルダナビゲーター
        self.folder_navigator = FolderNavigator()

        # サムネイルグリッド
        self.thumbnail_grid = ThumbnailGrid()

        # 詳細情報パネル
        self.info_panel = QTextEdit()
        self.info_panel.setMaximumHeight(150)
        self.info_panel.setReadOnly(True)

        # 左パネルレイアウトに追加
        self.left_layout.addWidget(QLabel("フォルダナビゲーション"))
        self.left_layout.addWidget(self.folder_navigator)
        self.left_layout.addWidget(QLabel("サムネイル"))
        self.left_layout.addWidget(self.thumbnail_grid, 1)
        self.left_layout.addWidget(QLabel("詳細情報"))
        self.left_layout.addWidget(self.info_panel)

        # メインスプリッターに追加
        self.main_splitter.addWidget(self.left_panel)

    def _init_right_panels(self) -> None:
        """右パネルの初期化"""
        # 画像プレビューパネル
        self._init_image_panel()

        # 地図パネル
        self._init_map_panel()

        # 右スプリッターに追加
        self.right_splitter.addWidget(self.image_panel)
        self.right_splitter.addWidget(self.map_panel)

        # メインスプリッターに追加
        self.main_splitter.addWidget(self.right_splitter)

    def _init_image_panel(self) -> None:
        """画像プレビューパネルの初期化"""
        self.image_panel = QFrame()
        self.image_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        self.image_layout = QVBoxLayout(self.image_panel)

        # 画像パネルヘッダー
        self.image_header = QHBoxLayout()
        self.image_header.addWidget(QLabel("画像プレビュー"))
        self.image_header.addStretch()

        # フルスクリーンボタン
        self.image_fullscreen_button = QPushButton("全画面")
        self.image_fullscreen_button.setToolTip("画像を全画面表示")
        self.image_header.addWidget(self.image_fullscreen_button)

        # 画像ビューアー（コントローラーから取得）
        self.image_viewer = self.controller.image_viewer

        # 画像パネルレイアウトに追加
        self.image_layout.addLayout(self.image_header)
        self.image_layout.addWidget(self.image_viewer)

    def _init_map_panel(self) -> None:
        """地図パネルの初期化"""
        self.map_panel = QFrame()
        self.map_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        self.map_layout = QVBoxLayout(self.map_panel)

        # 地図パネルヘッダー
        self.map_header = QHBoxLayout()
        self.map_header.addWidget(QLabel("地図"))
        self.map_header.addStretch()

        # フルスクリーンボタン
        self.map_fullscreen_button = QPushButton("全画面")
        self.map_fullscreen_button.setToolTip("地図を全画面表示")
        self.map_header.addWidget(self.map_fullscreen_button)

        # 地図ビューアー（コントローラーから取得）
        self.map_viewer = self.controller.map_viewer

        # 地図パネルレイアウトに追加
        self.map_layout.addLayout(self.map_header)
        self.map_layout.addWidget(self.map_viewer)

    def _init_menu_bar(self) -> None:
        """メニューバーの初期化"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        open_folder_action = QAction("フォルダを開く(&O)", self)
        open_folder_action.setShortcut(QKeySequence.StandardKey.Open)
        open_folder_action.triggered.connect(self._open_folder)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 表示メニュー
        view_menu = menubar.addMenu("表示(&V)")

        theme_menu = view_menu.addMenu("テーマ(&T)")
        # テーマメニューは後で動的に追加

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")

        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_tool_bar(self) -> None:
        """ツールバーの初期化"""
        toolbar = self.addToolBar("メインツールバー")
        toolbar.setMovable(False)

        # フォルダ選択アクション
        open_folder_action = QAction("フォルダを開く", self)
        open_folder_action.triggered.connect(self._open_folder)
        toolbar.addAction(open_folder_action)

        toolbar.addSeparator()

        # ナビゲーションアクション
        back_action = QAction("戻る", self)
        back_action.triggered.connect(self._go_back)
        toolbar.addAction(back_action)

        forward_action = QAction("進む", self)
        forward_action.triggered.connect(self._go_forward)
        toolbar.addAction(forward_action)

        up_action = QAction("上位フォルダ", self)
        up_action.triggered.connect(self._go_up)
        toolbar.addAction(up_action)

    def _init_layout(self) -> None:
        """レイアウトの初期化"""
        # メインレイアウトにスプリッターを追加
        self.main_layout.addWidget(self.main_splitter, 1)

        # スプリッターの初期サイズ設定
        self.main_splitter.setSizes([300, 700])
        self.right_splitter.setSizes([400, 300])

    def _init_connections(self) -> None:
        """シグナル・スロット接続の初期化"""
        # フォルダナビゲーターとコントローラーの接続
        self.folder_navigator.directory_selected.connect(self.controller.load_directory)
        self.folder_navigator.directory_selected.connect(self._update_address_bar)

        # サムネイルグリッドとコントローラーの接続
        self.thumbnail_grid.image_selected.connect(self.controller.select_image)
        self.thumbnail_grid.image_double_clicked.connect(self._show_image_fullscreen)

        # コントローラーとUIコンポーネントの接続
        self.controller.images_loaded.connect(self.thumbnail_grid.load_images)
        self.controller.image_selected.connect(self._update_info_panel)
        self.controller.exif_parsed.connect(self._update_info_panel)
        self.controller.map_marker_added.connect(self._update_status)
        self.controller.loading_progress.connect(self._update_progress)
        self.controller.loading_finished.connect(self._hide_progress)
        self.controller.error_occurred.connect(self._show_error)

        # 全画面ボタン
        self.image_fullscreen_button.clicked.connect(self._toggle_image_fullscreen)
        self.map_fullscreen_button.clicked.connect(self._toggle_map_fullscreen)

    def _init_theme(self) -> None:
        """テーマの初期化"""
        try:
            app = QApplication.instance()
            if app:
                self.theme_manager = ThemeManager(app)
                self.theme_manager.theme_changed.connect(self._on_theme_changed)
                self.logger.info("テーママネージャーを初期化しました")
            else:
                self.logger.error("QApplicationインスタンスが見つかりません")
        except Exception as e:
            self.logger.error(f"テーママネージャーの初期化に失敗しました: {e}")

    def _restore_window_state(self) -> None:
        """ウィンドウ状態の復元"""
        try:
            window_settings = self.settings.get_window_settings()

            # ウィンドウサイズと位置
            width = window_settings.get("width", 1200)
            height = window_settings.get("height", 800)
            x = window_settings.get("x", 100)
            y = window_settings.get("y", 100)

            self.resize(width, height)
            self.move(x, y)

            # 最大化状態
            if window_settings.get("maximized", False):
                self.showMaximized()

            # スプリッターサイズ
            left_width = window_settings.get("left_panel_width", 300)
            right_width = window_settings.get("right_panel_width", 400)

            self.main_splitter.setSizes([left_width, right_width])

            self.logger.debug("ウィンドウ状態を復元しました")

        except Exception as e:
            self.logger.error(f"ウィンドウ状態の復元に失敗しました: {e}")

    def _save_window_state(self) -> None:
        """ウィンドウ状態の保存"""
        try:
            window_settings = {
                "width": self.width(),
                "height": self.height(),
                "x": self.x(),
                "y": self.y(),
                "maximized": self.isMaximized(),
                "left_panel_width": self.main_splitter.sizes()[0],
                "right_panel_width": self.main_splitter.sizes()[1],
            }

            self.settings.set_window_settings(window_settings)
            self.logger.debug("ウィンドウ状態を保存しました")

        except Exception as e:
            self.logger.error(f"ウィンドウ状態の保存に失敗しました: {e}")

    def _open_folder(self) -> None:
        """フォルダを開く"""
        try:
            last_dir = self.settings.get_last_directory()
            folder_path = QFileDialog.getExistingDirectory(
                self, "フォルダを選択", last_dir
            )

            if folder_path:
                self.settings.set_last_directory(folder_path)
                self.folder_navigator.set_current_directory(folder_path)
                self.directory_changed.emit(folder_path)
                self.logger.info(f"フォルダを開きました: {folder_path}")

        except Exception as e:
            self.logger.error(f"フォルダの選択に失敗しました: {e}")
            QMessageBox.warning(self, "エラー", f"フォルダの選択に失敗しました: {e}")

    def _go_back(self) -> None:
        """戻る"""
        self.logger.debug("戻るボタンがクリックされました")
        # TODO: 履歴機能の実装

    def _go_forward(self) -> None:
        """進む"""
        self.logger.debug("進むボタンがクリックされました")
        # TODO: 履歴機能の実装

    def _go_up(self) -> None:
        """上位フォルダ"""
        self.logger.debug("上位フォルダボタンがクリックされました")
        # TODO: 上位フォルダ移動機能の実装

    def _cycle_theme(self) -> None:
        """テーマを切り替え"""
        try:
            if hasattr(self, "theme_manager"):
                new_theme = self.theme_manager.cycle_theme()
                self.logger.info(f"テーマを切り替えました: {new_theme}")
        except Exception as e:
            self.logger.error(f"テーマの切り替えに失敗しました: {e}")

    def _show_theme_menu(self, position) -> None:
        """テーマ選択メニューを表示"""
        try:
            if hasattr(self, "theme_manager"):
                menu = QMenu(self)

                for theme_name in self.theme_manager.get_available_themes():
                    action = QAction(theme_name, self)
                    action.triggered.connect(
                        lambda checked, tn=theme_name: self._select_theme(tn)
                    )
                    menu.addAction(action)

                menu.exec(self.theme_button.mapToGlobal(position))
        except Exception as e:
            self.logger.error(f"テーマメニューの表示に失敗しました: {e}")

    def _select_theme(self, theme_name: str) -> None:
        """テーマを選択"""
        try:
            if hasattr(self, "theme_manager"):
                self.theme_manager.apply_theme(theme_name)
                self.logger.info(f"テーマを選択しました: {theme_name}")
        except Exception as e:
            self.logger.error(f"テーマの選択に失敗しました: {e}")

    def _on_theme_changed(self, theme_name: str) -> None:
        """テーマ変更時の処理"""
        self.logger.debug(f"テーマが変更されました: {theme_name}")
        # TODO: テーマ変更時の追加処理

    def _toggle_image_fullscreen(self) -> None:
        """画像パネルの全画面切り替え"""
        self.logger.debug("画像パネルの全画面切り替え")
        # TODO: 全画面表示機能の実装

    def _toggle_map_fullscreen(self) -> None:
        """地図パネルの全画面切り替え"""
        self.logger.debug("地図パネルの全画面切り替え")
        # TODO: 全画面表示機能の実装

    def _update_address_bar(self, directory: str) -> None:
        """アドレスバーの更新"""
        self.folder_navigator.set_current_directory(directory)

    def _update_info_panel(self, data: dict) -> None:
        """詳細情報パネルの更新"""
        if not data:
            self.info_panel.setText("画像を選択してください")
            return

        info_text = ""

        # ファイル情報
        if "file_path" in data:
            info_text += f"ファイル: {data['file_path']}\n"
        if "file_size" in data:
            info_text += f"サイズ: {data['file_size']}\n"
        if "dimensions" in data:
            info_text += f"サイズ: {data['dimensions']}\n"

        # EXIF情報
        if "exif_data" in data and data["exif_data"]:
            exif = data["exif_data"]
            info_text += "\n=== EXIF情報 ===\n"
            if "DateTime" in exif:
                info_text += f"撮影日時: {exif['DateTime']}\n"
            if "Make" in exif:
                info_text += f"カメラ: {exif['Make']}\n"
            if "Model" in exif:
                info_text += f"モデル: {exif['Model']}\n"
            if "GPSLatitude" in exif and "GPSLongitude" in exif:
                info_text += f"緯度: {exif['GPSLatitude']}\n"
                info_text += f"経度: {exif['GPSLongitude']}\n"

        self.info_panel.setText(info_text)

    def _update_status(self, message: str) -> None:
        """ステータスバーの更新"""
        self.status_bar.showMessage(message)

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

    def _show_image_fullscreen(self, image_path: str) -> None:
        """画像の全画面表示"""
        self._toggle_image_fullscreen()

    def _show_about(self) -> None:
        """バージョン情報を表示"""
        QMessageBox.about(
            self,
            "バージョン情報",
            "PhotoGeoView v1.0.0\n\n"
            "写真のEXIF情報から撮影場所を抽出し、\n"
            "地図上に表示する写真管理アプリケーションです。",
        )

    def closeEvent(self, event) -> None:
        """ウィンドウクローズ時の処理"""
        try:
            self._save_window_state()
            self.logger.info("アプリケーションを終了します")
            event.accept()
        except Exception as e:
            self.logger.error(f"アプリケーション終了時の処理に失敗しました: {e}")
            event.accept()
