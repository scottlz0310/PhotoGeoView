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
    QDialog,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QFont

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.core.utils import ensure_directory_exists
from src.core.controller import PhotoGeoViewController
from .qt_theme_manager_adapter import QtThemeManagerAdapter
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

        # テーマ関連のUI要素を最終更新
        self._finalize_theme_ui()

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
        # メインスプリッターハンドルの幅を設定
        self.main_splitter.setHandleWidth(8)
        self.main_splitter.setChildrenCollapsible(False)

        # 左パネル
        self._init_left_panel()

        # 右パネル（スプリッター）
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        # 右スプリッターハンドルの幅を設定
        self.right_splitter.setHandleWidth(8)
        self.right_splitter.setChildrenCollapsible(False)
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

    def _init_left_panel(self) -> None:
        """左パネルの初期化"""
        # 左パネルフレーム
        self.left_panel = QFrame()
        self.left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        # 左パネルの適切な最小サイズを設定
        self.left_panel.setMinimumSize(250, 400)
        self.left_layout = QVBoxLayout(self.left_panel)

        # 左パネル用の縦スプリッター作成
        self.left_splitter = QSplitter(Qt.Orientation.Vertical)
        # スプリッターハンドルの幅を設定（ドラッグしやすくする）
        self.left_splitter.setHandleWidth(8)
        # スプリッターハンドルの見た目を改善
        self.left_splitter.setChildrenCollapsible(False)  # 子ウィジェットの完全な折りたたみを防ぐ

        # フォルダナビゲーター部分
        self.folder_section = QWidget()
        self.folder_section_layout = QVBoxLayout(self.folder_section)
        self.folder_section_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_section_layout.addWidget(QLabel("フォルダナビゲーション"))
        self.folder_navigator = FolderNavigator()
        # フォルダナビゲーションエリアに最小サイズを設定
        self.folder_section.setMinimumHeight(120)
        self.folder_section_layout.addWidget(self.folder_navigator)

        # サムネイルグリッド部分
        self.thumbnail_section = QWidget()
        self.thumbnail_section_layout = QVBoxLayout(self.thumbnail_section)
        self.thumbnail_section_layout.setContentsMargins(0, 0, 0, 0)
        self.thumbnail_section_layout.addWidget(QLabel("サムネイル"))
        self.thumbnail_grid = ThumbnailGrid()
        # サムネイルエリアに最小サイズを設定
        self.thumbnail_section.setMinimumHeight(200)
        self.thumbnail_section_layout.addWidget(self.thumbnail_grid)

        # 詳細情報部分
        self.info_section = QWidget()
        self.info_section_layout = QVBoxLayout(self.info_section)
        self.info_section_layout.setContentsMargins(0, 0, 0, 0)
        self.info_section_layout.addWidget(QLabel("詳細情報"))
        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        # 詳細情報エリアに最小サイズを設定
        self.info_section.setMinimumHeight(100)
        self.info_section_layout.addWidget(self.info_panel)

        # 左スプリッターに各セクションを追加
        self.left_splitter.addWidget(self.folder_section)
        self.left_splitter.addWidget(self.thumbnail_section)
        self.left_splitter.addWidget(self.info_section)

        # 初期サイズの設定（フォルダ：サムネイル：詳細情報 = 1:3:1の比率）
        self.left_splitter.setSizes([150, 450, 150])
        self.left_splitter.setStretchFactor(0, 0)  # フォルダ部分は固定的
        self.left_splitter.setStretchFactor(1, 1)  # サムネイル部分は拡縮可能
        self.left_splitter.setStretchFactor(2, 0)  # 詳細情報部分は固定的

        # 左パネルレイアウトに追加
        self.left_layout.addWidget(self.left_splitter)

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
        # 画像パネルの適切な最小サイズを設定
        self.image_panel.setMinimumSize(200, 150)
        self.image_layout = QVBoxLayout(self.image_panel)

        # 画像パネルヘッダー（ImageViewerタイトルと全画面ボタンのみ）
        self.image_header = QHBoxLayout()
        self.image_header.addWidget(QLabel("🖼️ ImageViewer"))
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
        # 地図パネルの適切な最小サイズを設定
        self.map_panel.setMinimumSize(200, 150)
        self.map_layout = QVBoxLayout(self.map_panel)

        # 地図パネルヘッダー（Map Viewerタイトルと全画面ボタンのみ）
        self.map_header = QHBoxLayout()
        self.map_header.addWidget(QLabel("🗺️ Map Viewer"))
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

        # テーマメニュー
        theme_menu = view_menu.addMenu("テーマ(&T)")

        # テーマ設定アクション
        theme_settings_action = QAction("テーマ設定(&S)...", self)
        theme_settings_action.setToolTip("使用するテーマを選択")
        theme_settings_action.triggered.connect(self._show_theme_settings)
        theme_menu.addAction(theme_settings_action)

        theme_menu.addSeparator()

        # 現在有効なテーマのクイック切り替えメニュー（動的生成）
        self.quick_theme_menu = theme_menu.addMenu("クイック切り替え(&Q)")
        self._update_quick_theme_menu()

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")

        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_tool_bar(self) -> None:
        """ツールバーの初期化（統合版）"""
        toolbar = self.addToolBar("メインツールバー")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # ボタンサイズ統一のための定数
        BUTTON_SIZE = 32

        # === 左側グループ: フォルダ操作 ===
        # フォルダ選択ボタン
        open_folder_action = QAction("📁", self)
        open_folder_action.setToolTip("フォルダを選択")
        open_folder_action.triggered.connect(self._open_folder)
        toolbar.addAction(open_folder_action)

        # パス表示・編集エリア
        self.address_edit = QLineEdit()
        self.address_edit.setMinimumWidth(300)
        self.address_edit.setPlaceholderText("フォルダを選択してください")
        self.address_edit.setToolTip("現在のフォルダパス（編集可能）")
        self.address_edit.returnPressed.connect(self._navigate_to_path)
        toolbar.addWidget(self.address_edit)

        # スペーサー
        spacer1 = QWidget()
        spacer1.setFixedWidth(20)
        toolbar.addWidget(spacer1)

        # === 中央グループ: ナビゲーション ===
        # 戻るボタン
        back_action = QAction("←", self)
        back_action.setToolTip("戻る")
        back_action.triggered.connect(self._go_back)
        toolbar.addAction(back_action)

        # 進むボタン
        forward_action = QAction("→", self)
        forward_action.setToolTip("進む")
        forward_action.triggered.connect(self._go_forward)
        toolbar.addAction(forward_action)

        # 上位フォルダボタン
        up_action = QAction("↑", self)
        up_action.setToolTip("上位フォルダ")
        up_action.triggered.connect(self._go_up)
        toolbar.addAction(up_action)

        # ナビゲーションボタンの参照を保存（状態更新用）
        self.back_action = back_action
        self.forward_action = forward_action
        self.up_action = up_action

        # 右側にストレッチを追加
        spacer2 = QWidget()
        spacer2.setSizePolicy(spacer2.sizePolicy().horizontalPolicy(), spacer2.sizePolicy().verticalPolicy())
        toolbar.addWidget(spacer2)

        # === 右側グループ: 設定・テーマ ===
        # 設定ボタン（将来の拡張用）
        settings_action = QAction("⚙️", self)
        settings_action.setToolTip("設定")
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)

        # テーマ切り替えボタン（QActionに変更してサイズを統一）
        self.theme_action = QAction("🌙", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(True)  # デフォルトでダークテーマ
        self.theme_action.setToolTip("テーマ切り替え（ダーク/ライト）")
        self.theme_action.triggered.connect(self._toggle_theme)
        toolbar.addAction(self.theme_action)

        # ヘルプボタン
        help_action = QAction("?", self)
        help_action.setToolTip("ヘルプ・バージョン情報")
        help_action.triggered.connect(self._show_about)
        toolbar.addAction(help_action)

        # ツールバー全体のスタイルシートでボタンサイズを統一
        if toolbar:
            toolbar.setStyleSheet(f"""
                QToolBar {{
                    spacing: 2px;
                }}
                QToolBar QToolButton {{
                    width: {BUTTON_SIZE}px;
                    height: {BUTTON_SIZE}px;
                    margin: 1px;
                    font-size: 14px;
                    font-weight: bold;
                    border: 1px solid #444;
                    border-radius: 4px;
                }}
                QToolBar QToolButton:hover {{
                    background-color: #555;
                }}
                QToolBar QToolButton:pressed {{
                    background-color: #777;
                }}
            """)

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
        self.folder_navigator.directory_selected.connect(self._update_navigation_buttons)  # ナビゲーションボタンの更新を追加

        # サムネイルグリッドとコントローラーの接続
        self.thumbnail_grid.image_selected.connect(self.controller.select_image)
        self.thumbnail_grid.image_double_clicked.connect(self._toggle_image_fullscreen)

        # コントローラーとUIコンポーネントの接続
        self.controller.images_loaded.connect(self.thumbnail_grid.load_images)
        self.controller.thumbnail_loaded.connect(self.thumbnail_grid.add_thumbnail)
        self.controller.image_selected.connect(self._update_info_panel)
        self.controller.map_marker_added.connect(self._update_status)
        self.controller.loading_progress.connect(self._update_progress)
        self.controller.loading_finished.connect(self._hide_progress)
        self.controller.error_occurred.connect(self._show_error)

        # 全画面ボタンのデバッグログ付き接続
        self.logger.debug("全画面ボタンの接続を設定中...")
        self.image_fullscreen_button.clicked.connect(self._debug_fullscreen_click)
        self.map_fullscreen_button.clicked.connect(self._toggle_map_fullscreen)

        # ImageViewer内の全画面ボタンの接続
        self.image_viewer.fullscreen_requested.connect(self._debug_fullscreen_request)
        self.map_viewer.fullscreen_requested.connect(self._toggle_map_fullscreen)

        # エスケープキーでの全画面解除
        self.image_viewer.escape_pressed.connect(self._debug_escape_key)

        self.logger.debug("シグナル・スロット接続が完了しました")

    def _init_theme(self) -> None:
        """テーマの初期化"""
        try:
            app = QApplication.instance()
            if app and isinstance(app, QApplication):
                self.theme_manager = QtThemeManagerAdapter(app)
                self.theme_manager.theme_changed.connect(self._on_theme_changed)
                # テーマボタンの初期化
                self._update_theme_button_icon(self.theme_manager.get_current_theme())
                # テーマメニューの初期化（メニューバーが既に初期化されている場合）
                if hasattr(self, 'quick_theme_menu'):
                    self._update_quick_theme_menu()
                self.logger.info("Qt-Theme-Managerアダプターを初期化しました")
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

            # 左パネル内スプリッターのサイズ復元
            left_splitter_sizes = window_settings.get("left_splitter_sizes", [150, 450, 150])
            if len(left_splitter_sizes) == 3:
                self.left_splitter.setSizes(left_splitter_sizes)

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
                "left_splitter_sizes": self.left_splitter.sizes(),
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
                self.folder_navigator.set_directory(folder_path)
                self.address_edit.setText(folder_path)  # ツールバーのパス表示を更新
                self.directory_changed.emit(folder_path)
                self.logger.info(f"フォルダを開きました: {folder_path}")

        except Exception as e:
            self.logger.error(f"フォルダの選択に失敗しました: {e}")
            QMessageBox.warning(self, "エラー", f"フォルダの選択に失敗しました: {e}")

    def _navigate_to_path(self) -> None:
        """アドレスバーのパスに移動"""
        try:
            path = self.address_edit.text().strip()
            if path and path != self.folder_navigator.get_current_directory():
                import os
                if os.path.exists(path) and os.path.isdir(path):
                    self.folder_navigator.set_directory(path)
                    self.settings.set_last_directory(path)
                    self.directory_changed.emit(path)
                    self.logger.info(f"パスに移動しました: {path}")
                else:
                    QMessageBox.warning(self, "エラー", f"指定されたパスが見つかりません: {path}")
                    # 現在のディレクトリに戻す
                    self.address_edit.setText(self.folder_navigator.get_current_directory())
        except Exception as e:
            self.logger.error(f"パス移動に失敗しました: {e}")
            QMessageBox.warning(self, "エラー", f"パス移動に失敗しました: {e}")

    def _show_settings(self) -> None:
        """設定ダイアログを表示"""
        try:
            from PyQt6.QtWidgets import QTabWidget

            # 設定ダイアログを作成
            settings_dialog = QDialog(self)
            settings_dialog.setWindowTitle("設定")
            settings_dialog.setModal(True)
            settings_dialog.resize(600, 400)

            layout = QVBoxLayout(settings_dialog)

            # タブウィジェット
            tab_widget = QTabWidget()
            layout.addWidget(tab_widget)

            # テーマ設定タブ
            theme_tab = QWidget()
            theme_layout = QVBoxLayout(theme_tab)

            # テーマ設定説明
            theme_desc = QLabel(
                "テーマ設定では、使用したいテーマを複数選択できます。\n"
                "ツールバーのテーマボタンで、選択されたテーマを順次切り替えます。"
            )
            theme_desc.setWordWrap(True)
            theme_layout.addWidget(theme_desc)

            # テーマ設定ボタン
            theme_settings_btn = QPushButton("テーマ設定を開く")
            theme_settings_btn.clicked.connect(self._show_theme_settings)
            theme_layout.addWidget(theme_settings_btn)

            theme_layout.addStretch()
            tab_widget.addTab(theme_tab, "テーマ")

            # その他の設定タブ（将来の実装予定）
            other_tab = QWidget()
            other_layout = QVBoxLayout(other_tab)
            other_label = QLabel("その他の設定は将来のバージョンで実装予定です。")
            other_layout.addWidget(other_label)
            other_layout.addStretch()
            tab_widget.addTab(other_tab, "その他")

            # ボタンパネル
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            close_btn = QPushButton("閉じる")
            close_btn.clicked.connect(settings_dialog.accept)
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

            # ダイアログを表示
            settings_dialog.exec()

        except Exception as e:
            self.logger.error(f"設定ダイアログの表示に失敗しました: {e}")
            # フォールバック：テーマ設定のみ表示
            QMessageBox.information(
                self,
                "設定",
                "設定機能を準備中です。\nテーマ設定は「表示」メニューから利用できます。"
            )

    def _toggle_theme(self) -> None:
        """テーマをループ切り替え（有効なテーマのみ）"""
        try:
            if hasattr(self, "theme_manager"):
                new_theme = self.theme_manager.cycle_theme()

                # アクションアイコンを更新
                self._update_theme_button_icon(new_theme)

                self.logger.info(f"テーマを切り替えました: → {new_theme}")
        except Exception as e:
            self.logger.error(f"テーマの切り替えに失敗しました: {e}")

    def _go_back(self) -> None:
        """戻る"""
        try:
            if hasattr(self, "folder_navigator"):
                if self.folder_navigator.go_back():
                    self._update_navigation_buttons()
                    self.logger.debug("戻る操作が完了しました")
                else:
                    self.logger.debug("戻ることができません")
        except Exception as e:
            self.logger.error(f"戻る操作に失敗しました: {e}")

    def _go_forward(self) -> None:
        """進む"""
        try:
            if hasattr(self, "folder_navigator"):
                if self.folder_navigator.go_forward():
                    self._update_navigation_buttons()
                    self.logger.debug("進む操作が完了しました")
                else:
                    self.logger.debug("進むことができません")
        except Exception as e:
            self.logger.error(f"進む操作に失敗しました: {e}")

    def _go_up(self) -> None:
        """上位フォルダ"""
        try:
            if hasattr(self, "folder_navigator"):
                if self.folder_navigator.go_up():
                    self._update_navigation_buttons()
                    self.logger.debug("上位フォルダ移動が完了しました")
                else:
                    self.logger.debug("上位フォルダに移動できません")
        except Exception as e:
            self.logger.error(f"上位フォルダ移動に失敗しました: {e}")

    def _update_navigation_buttons(self) -> None:
        """ナビゲーションボタンの状態を更新"""
        try:
            if hasattr(self, "folder_navigator") and hasattr(self, "back_action"):
                # 戻るボタンの状態
                self.back_action.setEnabled(self.folder_navigator.can_go_back())

                # 進むボタンの状態
                self.forward_action.setEnabled(self.folder_navigator.can_go_forward())

                # 上位フォルダボタンの状態（ルートディレクトリでない場合は有効）
                current_dir = self.folder_navigator.get_current_directory()
                from pathlib import Path
                can_go_up = bool(current_dir and Path(current_dir).parent != Path(current_dir))
                self.up_action.setEnabled(can_go_up)

        except Exception as e:
            self.logger.error(f"ナビゲーションボタンの更新に失敗しました: {e}")

    def _cycle_theme(self) -> None:
        """テーマを切り替え"""
        try:
            if hasattr(self, "theme_manager"):
                new_theme = self.theme_manager.cycle_theme()
                self.logger.info(f"テーマを切り替えました: {new_theme}")
        except Exception as e:
            self.logger.error(f"テーマの切り替えに失敗しました: {e}")

    def _on_theme_changed(self, theme_name: str) -> None:
        """テーマ変更時の処理"""
        self.logger.debug(f"テーマが変更されました: {theme_name}")
        try:
            # テーマボタンのアイコンを更新
            self._update_theme_button_icon(theme_name)

            # クイック切り替えメニューを更新（チェックマーク位置の変更）
            self._update_quick_theme_menu()

            # ウィンドウタイトルを更新
            theme_info = self.theme_manager.get_theme_info(theme_name)
            self.setWindowTitle(f"PhotoGeoView - {theme_info['display_name']}")

            # ステータスバーにメッセージを表示
            self.status_bar.showMessage(
                f"テーマを {theme_info['display_name']} に変更しました", 2000
            )

            # 設定を保存
            if hasattr(self, "settings"):
                self.settings.set("ui.theme_manager.current_theme", theme_name)

        except Exception as e:
            self.logger.error(f"テーマ変更時の処理に失敗しました: {e}")

    def _debug_fullscreen_click(self) -> None:
        """デバッグ用：全画面ボタンクリック"""
        self.logger.debug("画像全画面ボタンがクリックされました")
        self._toggle_image_fullscreen()

    def _debug_fullscreen_request(self) -> None:
        """デバッグ用：ImageViewerからの全画面リクエスト"""
        self.logger.debug("ImageViewerから全画面リクエストを受信")
        self._toggle_image_fullscreen()

    def _debug_escape_key(self) -> None:
        """デバッグ用：ESCキー処理"""
        self.logger.debug("ImageViewerからESCキーシグナルを受信")
        self._handle_escape_key()

    def _toggle_image_fullscreen(self) -> None:
        """画像パネルの全画面切り替え"""
        try:
            self.logger.debug(f"_toggle_image_fullscreen called. Current state: {getattr(self, '_image_fullscreen', 'undefined')}")
            if hasattr(self, "_image_fullscreen") and self._image_fullscreen:
                # 全画面モードを解除
                self.logger.debug("画像全画面モード解除を開始")
                self._image_fullscreen = False
                self._restore_image_normal_layout()
                self.image_fullscreen_button.setText("全画面")
                self.image_fullscreen_button.setToolTip("画像を全画面表示")
                self.logger.debug("画像パネルの全画面モードを解除しました")
            else:
                # 全画面モードを有効化
                self.logger.debug("画像全画面モード有効化を開始")
                self._image_fullscreen = True
                self._save_current_layout()
                self._show_image_fullscreen()
                self.image_fullscreen_button.setText("戻る")
                self.image_fullscreen_button.setToolTip("通常表示に戻る")
                self.logger.debug("画像パネルを全画面表示しました")
        except Exception as e:
            self.logger.error(f"画像パネルの全画面切り替えに失敗しました: {e}")
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")

    def _toggle_map_fullscreen(self) -> None:
        """地図パネルの全画面切り替え"""
        try:
            if hasattr(self, "_map_fullscreen") and self._map_fullscreen:
                # 全画面モードを解除
                self._map_fullscreen = False
                self._restore_map_normal_layout()
                self.map_fullscreen_button.setText("全画面")
                self.map_fullscreen_button.setToolTip("地図を全画面表示")
                self.logger.debug("地図パネルの全画面モードを解除しました")
            else:
                # 全画面モードを有効化
                self._map_fullscreen = True
                self._save_current_layout()
                self._show_map_fullscreen()
                self.map_fullscreen_button.setText("戻る")
                self.map_fullscreen_button.setToolTip("通常表示に戻る")
                self.logger.debug("地図パネルを全画面表示しました")
        except Exception as e:
            self.logger.error(f"地図パネルの全画面切り替えに失敗しました: {e}")

    def _handle_escape_key(self) -> None:
        """エスケープキーで全画面モードから戻る"""
        try:
            self.logger.debug("ESCキーが押されました")
            # 画像が全画面モードの場合
            if hasattr(self, "_image_fullscreen") and self._image_fullscreen:
                self.logger.debug("画像全画面モードからESCで戻ります")
                self._toggle_image_fullscreen()
            # 地図が全画面モードの場合
            elif hasattr(self, "_map_fullscreen") and self._map_fullscreen:
                self.logger.debug("地図全画面モードからESCで戻ります")
                self._toggle_map_fullscreen()
            else:
                self.logger.debug("全画面モードではありません")
        except Exception as e:
            self.logger.error(f"エスケープキー処理に失敗しました: {e}")

    def _save_current_layout(self) -> None:
        """現在のレイアウトを保存"""
        self._saved_central_widget = self.centralWidget()
        # スプリッターのサイズも保存
        self._saved_main_sizes = self.main_splitter.sizes()
        self._saved_right_sizes = self.right_splitter.sizes()

    def _show_image_fullscreen(self) -> None:
        """画像パネルを全画面表示"""
        try:
            self.logger.debug("画像全画面表示開始")

            # 左パネルと地図パネルを非表示にして、画像パネルを拡大
            self.left_panel.setVisible(False)
            self.map_panel.setVisible(False)

            # 画像パネルがright_splitterの唯一の可視子になるように調整
            # スプリッターのサイズを調整して画像パネルを最大化
            total_width = self.main_splitter.width()
            self.main_splitter.setSizes([0, total_width])  # 左パネル0, 右パネル全幅

            # 全画面表示後にウィンドウフィットを実行（少し遅延して）
            if hasattr(self.image_viewer, 'image_display'):
                QTimer.singleShot(100, self.image_viewer.image_display.fit_to_window)

        except Exception as e:
            self.logger.error(f"画像全画面表示エラー: {e}")

    def _show_map_fullscreen(self) -> None:
        """地図パネルを全画面表示"""
        try:
            self.logger.debug("地図全画面表示開始")

            # 左パネルと画像パネルを非表示にして、地図パネルを拡大
            self.left_panel.setVisible(False)
            self.image_panel.setVisible(False)

            # 地図パネルがright_splitterの唯一の可視子になるように調整
            total_width = self.main_splitter.width()
            self.main_splitter.setSizes([0, total_width])  # 左パネル0, 右パネル全幅

        except Exception as e:
            self.logger.error(f"地図全画面表示エラー: {e}")

    def _restore_image_normal_layout(self) -> None:
        """画像全画面から通常レイアウトに復元"""
        try:
            self.logger.debug("画像全画面から通常レイアウト復元開始")

            # 現在の状態をログ出力
            left_visible = self.left_panel.isVisible()
            image_visible = self.image_panel.isVisible()
            map_visible = self.map_panel.isVisible()
            main_sizes = self.main_splitter.sizes()
            right_sizes = self.right_splitter.sizes()

            self.logger.debug(f"復元前状態: left={left_visible}, image={image_visible}, map={map_visible}")
            self.logger.debug(f"復元前サイズ: main={main_sizes}, right={right_sizes}")

            # ウィジェットの更新を停止（パフォーマンス向上）
            self.setUpdatesEnabled(False)

            # すべてのパネルを表示
            self.left_panel.setVisible(True)
            self.image_panel.setVisible(True)
            self.map_panel.setVisible(True)
            self.logger.debug("すべてのパネルを表示に設定しました")

            # 【修正】適切な最小サイズを復元（0,0ではなく適切なサイズ）
            self.left_panel.setMinimumSize(250, 400)
            self.image_panel.setMinimumSize(200, 150)
            self.map_panel.setMinimumSize(200, 150)
            self.logger.debug("適切な最小サイズを復元しました")

            # レイアウト更新を強制
            QApplication.processEvents()

            # スプリッターのサイズを復元（簡略化版）
            if hasattr(self, "_saved_main_sizes") and hasattr(self, "_saved_right_sizes"):
                self.logger.debug(f"保存されたサイズを復元: main={self._saved_main_sizes}, right={self._saved_right_sizes}")

                # レイアウト更新を強制
                QApplication.processEvents()

                # サイズを復元
                self.main_splitter.setSizes(self._saved_main_sizes)
                self.right_splitter.setSizes(self._saved_right_sizes)

                # 復元後の確認用に少し待機
                QTimer.singleShot(50, lambda: QApplication.processEvents())
            else:
                # デフォルトサイズに戻す
                self.logger.debug("デフォルトサイズに設定")
                self.main_splitter.setSizes([300, 700])
                self.right_splitter.setSizes([400, 300])

            # ウィジェットの更新を再開
            self.setUpdatesEnabled(True)

            # 復元後の状態をログ出力
            main_sizes_after = self.main_splitter.sizes()
            right_sizes_after = self.right_splitter.sizes()
            self.logger.debug(f"復元後サイズ: main={main_sizes_after}, right={right_sizes_after}")

            # レイアウト復元後に画像をフィット（遅延実行で確実にフィット）
            def delayed_fit():
                if hasattr(self.image_viewer, 'image_display'):
                    self.logger.debug("画像フィット実行")
                    self.image_viewer.image_display.fit_to_window()
                    # フォーカスも設定
                    self.image_viewer.setFocus()

            QTimer.singleShot(200, delayed_fit)

            self.logger.debug("画像全画面から通常レイアウト復元完了")

        except Exception as e:
            self.logger.error(f"画像レイアウト復元エラー: {e}")
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")

    def _restore_map_normal_layout(self) -> None:
        """地図全画面から通常レイアウトに復元"""
        try:
            self.logger.debug("地図全画面から通常レイアウト復元開始")

            # すべてのパネルを表示
            self.left_panel.setVisible(True)
            self.image_panel.setVisible(True)
            self.map_panel.setVisible(True)

            # 【修正】適切な最小サイズを復元
            self.left_panel.setMinimumSize(250, 400)
            self.image_panel.setMinimumSize(200, 150)
            self.map_panel.setMinimumSize(200, 150)
            self.logger.debug("適切な最小サイズを復元しました")

            # スプリッターのサイズを復元
            if hasattr(self, "_saved_main_sizes"):
                self.main_splitter.setSizes(self._saved_main_sizes)
            else:
                self.main_splitter.setSizes([300, 700])

            if hasattr(self, "_saved_right_sizes"):
                self.right_splitter.setSizes(self._saved_right_sizes)
            else:
                self.right_splitter.setSizes([400, 300])

            self.logger.debug("地図全画面から通常レイアウト復元完了")

        except Exception as e:
            self.logger.error(f"地図レイアウト復元エラー: {e}")

    def _restore_normal_layout(self) -> None:
        """通常レイアウトに復元（汎用メソッド）"""
        try:
            self.logger.debug("通常レイアウト復元開始")

            # 現在の状態をログ出力
            left_visible = self.left_panel.isVisible()
            image_visible = self.image_panel.isVisible()
            map_visible = self.map_panel.isVisible()
            main_sizes = self.main_splitter.sizes()
            right_sizes = self.right_splitter.sizes()

            self.logger.debug(f"復元前状態: left={left_visible}, image={image_visible}, map={map_visible}")
            self.logger.debug(f"復元前サイズ: main={main_sizes}, right={right_sizes}")

            # すべてのパネルを表示
            self.left_panel.setVisible(True)
            self.image_panel.setVisible(True)
            self.map_panel.setVisible(True)
            self.logger.debug("すべてのパネルを表示に設定しました")

            # 【修正】適切な最小サイズを復元
            self.left_panel.setMinimumSize(250, 400)
            self.image_panel.setMinimumSize(200, 150)
            self.map_panel.setMinimumSize(200, 150)
            self.logger.debug("適切な最小サイズを復元しました")

            # スプリッターのサイズを復元
            if hasattr(self, "_saved_main_sizes"):
                self.logger.debug(f"保存されたメインサイズを復元: {self._saved_main_sizes}")
                self.main_splitter.setSizes(self._saved_main_sizes)
            else:
                # デフォルトサイズに戻す
                self.logger.debug("デフォルトメインサイズに設定: [300, 700]")
                self.main_splitter.setSizes([300, 700])

            if hasattr(self, "_saved_right_sizes"):
                self.logger.debug(f"保存された右サイズを復元: {self._saved_right_sizes}")
                self.right_splitter.setSizes(self._saved_right_sizes)
            else:
                # デフォルトサイズに戻す
                self.logger.debug("デフォルト右サイズに設定: [400, 300]")
                self.right_splitter.setSizes([400, 300])

            # 復元後の状態をログ出力
            main_sizes_after = self.main_splitter.sizes()
            right_sizes_after = self.right_splitter.sizes()
            self.logger.debug(f"復元後サイズ: main={main_sizes_after}, right={right_sizes_after}")

            # レイアウト復元後に画像をフィット（少し遅延して）
            if hasattr(self.image_viewer, 'image_display'):
                self.logger.debug("画像フィットをスケジュール")
                QTimer.singleShot(100, self.image_viewer.image_display.fit_to_window)

            self.logger.debug("通常レイアウト復元完了")

        except Exception as e:
            self.logger.error(f"レイアウト復元エラー: {e}")
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")

    def _animate_panel_transition(self, panel, show: bool) -> None:
        """
        パネルの表示/非表示アニメーション

        Args:
            panel: アニメーション対象のパネル
            show: 表示するかどうか
        """
        try:
            # 簡単なフェード効果
            if show:
                panel.setVisible(True)
                panel.setStyleSheet("QWidget { opacity: 0; }")
                # フェードイン効果（簡易版）
                panel.setStyleSheet("QWidget { opacity: 1; }")
            else:
                panel.setVisible(False)

        except Exception as e:
            self.logger.error(f"パネルアニメーションに失敗しました: {e}")

    def _optimize_performance(self) -> None:
        """パフォーマンス最適化"""
        try:
            # ウィジェットの更新を一時停止
            self.setUpdatesEnabled(False)

            # メモリ使用量の最適化
            self._clear_unused_resources()

            # ウィジェットの更新を再開
            self.setUpdatesEnabled(True)

        except Exception as e:
            self.logger.error(f"パフォーマンス最適化に失敗しました: {e}")

    def _clear_unused_resources(self) -> None:
        """未使用リソースのクリア"""
        try:
            # ガベージコレクションを実行
            import gc

            gc.collect()

            # キャッシュのクリア（必要に応じて）
            if hasattr(self, "controller"):
                self.controller.clear_cache()

        except Exception as e:
            self.logger.error(f"リソースクリアに失敗しました: {e}")

    def _show_loading_indicator(self, show: bool) -> None:
        """
        ローディングインジケーターの表示/非表示

        Args:
            show: 表示するかどうか
        """
        try:
            if show:
                self.progress_bar.setVisible(True)
                self.status_bar.showMessage("読み込み中...")
            else:
                self.progress_bar.setVisible(False)
                self.status_bar.clearMessage()

        except Exception as e:
            self.logger.error(f"ローディングインジケーターの制御に失敗しました: {e}")

    def _show_success_message(self, message: str) -> None:
        """
        成功メッセージの表示

        Args:
            message: 表示するメッセージ
        """
        try:
            self.status_bar.showMessage(f"✓ {message}", 3000)  # 3秒間表示

        except Exception as e:
            self.logger.error(f"成功メッセージの表示に失敗しました: {e}")

    def _show_error_message(self, message: str) -> None:
        """
        エラーメッセージの表示

        Args:
            message: 表示するエラーメッセージ
        """
        try:
            self.status_bar.showMessage(f"✗ {message}", 5000)  # 5秒間表示
            QMessageBox.warning(self, "エラー", message)

        except Exception as e:
            self.logger.error(f"エラーメッセージの表示に失敗しました: {e}")

    def _update_address_bar(self, directory: str) -> None:
        """アドレスバーの更新"""
        if hasattr(self, 'address_edit'):
            self.address_edit.setText(directory)
        self.folder_navigator.set_directory(directory)

    def _update_info_panel(self, data: dict) -> None:
        """詳細情報パネルの更新"""
        # デバッグ用: 画像パネルとビューアの状態をログ出力
        try:
            panel_visible = (
                self.image_panel.isVisible() if hasattr(self, "image_panel") else "N/A"
            )
            viewer_visible = (
                self.image_viewer.isVisible()
                if hasattr(self, "image_viewer")
                else "N/A"
            )
            has_image = (
                self.image_viewer.has_image()
                if hasattr(self.image_viewer, "has_image")
                else "N/A"
            )
            self.logger.debug(
                f"[DEBUG] image_panel.isVisible={panel_visible}, image_viewer.isVisible={viewer_visible}, image_viewer.has_image={has_image}"
            )
        except Exception as e:
            self.logger.error(f"[DEBUG] 画像パネル状態ログ出力失敗: {e}")

        if not data:
            self.info_panel.setText("画像を選択してください")
            return

        info_text = ""

        # ファイル情報
        if "file_path" in data:
            info_text += f"ファイル: {data['file_path']}\n"
        if "file_size" in data:
            size_mb = data["file_size"] / (1024 * 1024)
            info_text += f"サイズ: {size_mb:.2f} MB\n"

        # EXIF情報（ExifParserの実際の構造に対応）
        if "exif" in data and data["exif"]:
            exif = data["exif"]
            info_text += "\n=== EXIF情報 ===\n"

            # 撮影日時
            if "datetime_original" in exif and exif["datetime_original"]:
                info_text += f"撮影日時: {exif['datetime_original'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            elif "datetime" in exif and exif["datetime"]:
                info_text += f"撮影日時: {exif['datetime'].strftime('%Y-%m-%d %H:%M:%S')}\n"

            # カメラ情報
            if "make" in exif:
                info_text += f"メーカー: {exif['make']}\n"
            if "model" in exif:
                info_text += f"モデル: {exif['model']}\n"
            if "lens_model" in exif:
                info_text += f"レンズ: {exif['lens_model']}\n"

            # 撮影設定
            if "exposure_time" in exif:
                info_text += f"シャッター速度: {exif['exposure_time']}\n"
            if "f_number" in exif:
                info_text += f"F値: {exif['f_number']}\n"
            if "iso" in exif:
                info_text += f"ISO感度: {exif['iso']}\n"
            if "focal_length" in exif:
                info_text += f"焦点距離: {exif['focal_length']}\n"

            # 画像サイズ
            if "width" in exif and "height" in exif:
                info_text += f"解像度: {exif['width']} x {exif['height']}\n"

            # GPS情報
            if "gps" in exif:
                gps = exif["gps"]
                if "latitude" in gps and "longitude" in gps:
                    info_text += f"緯度: {gps['latitude']:.6f}\n"
                    info_text += f"経度: {gps['longitude']:.6f}\n"
                if "altitude" in gps:
                    info_text += f"高度: {gps['altitude']:.1f}m\n"
        else:
            info_text += "\nEXIF情報: なし\n"

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

    def _show_theme_settings(self) -> None:
        """テーマ設定ダイアログを表示"""
        try:
            from .theme_selection_dialog import ThemeSelectionDialog

            dialog = ThemeSelectionDialog(self.theme_manager, self)
            dialog.themes_applied.connect(self._on_themes_updated)

            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                self.logger.info("テーマ設定が更新されました")
                # クイック切り替えメニューを更新
                self._update_quick_theme_menu()

        except Exception as e:
            self.logger.error(f"テーマ設定ダイアログの表示に失敗しました: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"テーマ設定ダイアログの表示に失敗しました: {e}"
            )

    def _update_quick_theme_menu(self) -> None:
        """クイック切り替えメニューを更新"""
        try:
            if not hasattr(self, 'quick_theme_menu') or not hasattr(self, 'theme_manager'):
                return

            # 既存のアクションをクリア
            self.quick_theme_menu.clear()

            # 有効なテーマのアクションを作成
            enabled_themes = self.theme_manager.get_enabled_themes()
            current_theme = self.theme_manager.get_current_theme()

            if not enabled_themes:
                # 有効なテーマがない場合
                no_themes_action = QAction("有効なテーマがありません", self)
                no_themes_action.setEnabled(False)
                self.quick_theme_menu.addAction(no_themes_action)
                return

            for theme_name in enabled_themes:
                theme_info = self.theme_manager.get_theme_info(theme_name)
                action = QAction(theme_info["display_name"], self)
                action.setToolTip(theme_info["description"])

                # 現在のテーマにチェックマーク
                if theme_name == current_theme:
                    action.setCheckable(True)
                    action.setChecked(True)

                # クリック時の動作
                action.triggered.connect(
                    lambda checked, name=theme_name: self._apply_specific_theme(name)
                )

                self.quick_theme_menu.addAction(action)

        except Exception as e:
            self.logger.error(f"クイック切り替えメニューの更新に失敗しました: {e}")

    def _apply_specific_theme(self, theme_name: str) -> None:
        """指定したテーマを適用"""
        try:
            if hasattr(self, 'theme_manager'):
                self.theme_manager.apply_theme(theme_name)
                self.logger.info(f"テーマを適用しました: {theme_name}")
        except Exception as e:
            self.logger.error(f"テーマの適用に失敗しました: {theme_name}, エラー: {e}")

    def _update_theme_button_icon(self, theme_name: str) -> None:
        """テーマボタンのアイコンを更新"""
        try:
            if not hasattr(self, 'theme_action'):
                return

            # テーマに応じたアイコンマップ
            theme_icons = {
                "dark": "🌙",
                "light": "☀️",
                "blue": "🔵",
                "green": "🟢",
                "purple": "🟣",
                "orange": "🟠",
                "red": "🔴",
                "pink": "🩷",
                "yellow": "🟡",
                "brown": "🟤",
                "gray": "⚫",
                "cyan": "🔵",
                "teal": "🟢",
                "indigo": "🟣",
                "lime": "🟢",
                "amber": "🟠"
            }

            icon = theme_icons.get(theme_name, "🎨")
            theme_info = self.theme_manager.get_theme_info(theme_name)
            display_name = theme_info["display_name"]

            self.theme_action.setText(icon)
            self.theme_action.setToolTip(f"現在のテーマ: {display_name}\nクリックで次のテーマに切り替え")

        except Exception as e:
            self.logger.error(f"テーマボタンアイコンの更新に失敗しました: {e}")

    def _on_themes_updated(self, selected_themes: list) -> None:
        """テーマ設定更新時の処理"""
        try:
            self.logger.info(f"有効テーマが更新されました: {selected_themes}")
            # クイック切り替えメニューを更新
            self._update_quick_theme_menu()
            # テーマボタンアイコンを更新
            self._update_theme_button_icon(self.theme_manager.get_current_theme())

        except Exception as e:
            self.logger.error(f"テーマ更新処理に失敗しました: {e}")

    def _finalize_theme_ui(self) -> None:
        """テーマ関連UIの最終初期化"""
        try:
            if hasattr(self, 'theme_manager'):
                # テーマボタンのアイコンを更新
                current_theme = self.theme_manager.get_current_theme()
                self._update_theme_button_icon(current_theme)

                # クイック切り替えメニューを更新
                if hasattr(self, 'quick_theme_menu'):
                    self._update_quick_theme_menu()

                # ウィンドウタイトルにテーマ名を追加
                theme_info = self.theme_manager.get_theme_info(current_theme)
                self.setWindowTitle(f"PhotoGeoView - {theme_info['display_name']}")

                self.logger.debug("テーマUIの最終初期化が完了しました")

        except Exception as e:
            self.logger.error(f"テーマUI最終初期化に失敗しました: {e}")
