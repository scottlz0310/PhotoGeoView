"""
Enhanced Folder Navigator for AI Integration - 拡張フォルダナビゲーター

CursorBLDの直感的なフォルダナビゲーションとKiroの最適化を組み合わせた
高機能フォルダナビゲーターコンポーネント。

主な機能:
- CursorBLD: 直感的なフォルダブラウジングと履歴管理
- Kiro: パフォーマンス最適化、エラーハンドリング、アクセシビリティ対応
- 統合ファイル検出サービスとの連携
- リアルタイムファイルシステム監視
- 日本語エラーメッセージとユーザーフィードバック

技術仕様:
- PyQt6ベースの高性能UI
- FileDiscoveryServiceとの統合による高速画像検出
- FileSystemWatcherによるリアルタイム更新
- 設定可能なフォルダ履歴とブックマーク機能
- アクセシビリティ対応とキーボードナビゲーション

UI構成:
- ナビゲーションコントロール（戻る、進む、上へ、ホーム）
- アドレスバーによる直接パス入力
- 履歴ドロップダウンとブックマーク機能
- フォルダツリービューによる階層表示

Author: Kiro AI Integration System
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QModelIndex, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..services.file_discovery_service import FileDiscoveryService
from ..services.file_system_watcher import FileChangeType, FileSystemWatcher
from ..state_manager import StateManager


class EnhancedFolderNavigator(QWidget):
    """
    Enhanced folder navigator combining CursorBLD navigation with Kiro optimization

    Features:
    - CursorBLD's intuitive folder browsing and history
    - Kiro's performance optimization and error handling
    - Accessibility enhancements and responsive design
    - Smart folder filtering and bookmarks
    """

    # Signals
    folder_selected = pyqtSignal(Path)
    folder_changed = pyqtSignal(Path)
    navigation_error = pyqtSignal(str, str)  # error_type, message
    status_message = pyqtSignal(str, int)  # message, timeout_ms

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
    ):
        """
        Initialize the enhanced folder navigator

        Args:
            config_manager: Configuration manager instance
            state_manager: State manager instance
            logger_system: Logging system instance
        """
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Navigation state
        self.current_folder: Optional[Path] = None
        self.folder_history: List[Path] = []
        self.bookmarks: List[Path] = []
        self.max_history = 20

        # File discovery service for image detection
        self.file_discovery_service = FileDiscoveryService(
            logger_system=self.logger_system
        )

        # File system watcher for real-time updates
        self.file_system_watcher = FileSystemWatcher(
            logger_system=self.logger_system, enable_monitoring=True
        )

        # Add change listener for file system events
        self.file_system_watcher.add_change_listener(self._on_file_system_change)

        # UI components
        self.address_bar: Optional[QLineEdit] = None
        self.folder_tree: Optional[QTreeView] = None
        self.file_system_model: Optional[QFileSystemModel] = None
        self.history_combo: Optional[QComboBox] = None

        # Performance optimization
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._delayed_folder_update)

        # Initialize UI
        self._initialize_ui()
        self._load_settings()
        self._connect_signals()

        self.logger_system.log_ai_operation(
            AIComponent.CURSOR,
            "folder_navigator_init",
            "Enhanced folder navigator initialized",
        )

    def _initialize_ui(self):
        """Initialize the user interface"""

        try:
            # Main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(5)

            # Create navigation controls
            self._create_navigation_controls()
            main_layout.addWidget(self.nav_controls)

            # Create folder tree
            self._create_folder_tree()
            main_layout.addWidget(self.folder_tree, 1)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "folder_navigator_ui_init"},
                AIComponent.CURSOR,
            )

    def _create_navigation_controls(self):
        """Create navigation controls (CursorBLD style)"""

        self.nav_controls = QFrame()
        self.nav_controls.setFrameStyle(QFrame.Shape.StyledPanel)
        self.nav_controls.setMaximumHeight(80)

        nav_layout = QVBoxLayout(self.nav_controls)
        nav_layout.setContentsMargins(5, 5, 5, 5)
        nav_layout.setSpacing(5)

        # First row: navigation buttons and address bar
        first_row = QHBoxLayout()

        # Navigation buttons
        self.back_btn = QPushButton("←")
        self.back_btn.setMaximumWidth(30)
        self.back_btn.setToolTip("Go back")
        self.back_btn.clicked.connect(self._go_back)
        first_row.addWidget(self.back_btn)

        self.forward_btn = QPushButton("→")
        self.forward_btn.setMaximumWidth(30)
        self.forward_btn.setToolTip("Go forward")
        self.forward_btn.clicked.connect(self._go_forward)
        first_row.addWidget(self.forward_btn)

        self.up_btn = QPushButton("↑")
        self.up_btn.setMaximumWidth(30)
        self.up_btn.setToolTip("Go up one level")
        self.up_btn.clicked.connect(self._go_up)
        first_row.addWidget(self.up_btn)

        self.home_btn = QPushButton("🏠")
        self.home_btn.setMaximumWidth(30)
        self.home_btn.setToolTip("Go to home directory")
        self.home_btn.clicked.connect(self._go_home)
        first_row.addWidget(self.home_btn)

        # Address bar
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Enter folder path...")
        self.address_bar.returnPressed.connect(self._navigate_to_address)
        first_row.addWidget(self.address_bar, 1)

        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.open_folder_dialog)
        first_row.addWidget(browse_btn)

        nav_layout.addLayout(first_row)

        # Second row: history and bookmarks
        second_row = QHBoxLayout()

        # History dropdown
        history_label = QLabel("Recent:")
        second_row.addWidget(history_label)

        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(200)
        self.history_combo.currentTextChanged.connect(self._navigate_to_history)
        second_row.addWidget(self.history_combo, 1)

        # Bookmark button
        bookmark_btn = QPushButton("★")
        bookmark_btn.setMaximumWidth(30)
        bookmark_btn.setToolTip("Bookmark current folder")
        bookmark_btn.clicked.connect(self._bookmark_current_folder)
        second_row.addWidget(bookmark_btn)

        nav_layout.addLayout(second_row)

    def _create_folder_tree(self):
        """Create folder tree view (CursorBLD design with Kiro optimization)"""

        try:
            # Create tree view
            self.folder_tree = QTreeView()
            self.folder_tree.setHeaderHidden(True)
            self.folder_tree.setRootIsDecorated(True)
            self.folder_tree.setAlternatingRowColors(True)

            # Create file system model
            self.file_system_model = QFileSystemModel()
            self.file_system_model.setRootPath("")
            # Fix: Use QDir.Filter instead of model.Filter
            from PyQt6.QtCore import QDir
            self.file_system_model.setFilter(
                QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot
            )

            # Set model to tree view
            self.folder_tree.setModel(self.file_system_model)

            # Hide unnecessary columns
            for i in range(1, self.file_system_model.columnCount()):
                self.folder_tree.hideColumn(i)

            # Connect selection signal
            self.folder_tree.clicked.connect(self._on_tree_item_clicked)
            self.folder_tree.doubleClicked.connect(self._on_tree_item_double_clicked)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "folder_tree_create"},
                AIComponent.CURSOR,
            )

    def _load_settings(self):
        """Load settings and restore state"""

        try:
            # Load folder history
            history_data = self.config_manager.get_setting("ui.folder_history", [])
            self.folder_history = [Path(p) for p in history_data if Path(p).exists()]

            # Load bookmarks
            bookmarks_data = self.config_manager.get_setting("ui.bookmarks", [])
            self.bookmarks = [Path(p) for p in bookmarks_data if Path(p).exists()]

            # Load current folder
            current_folder_str = self.config_manager.get_setting("ui.current_folder")
            if current_folder_str:
                current_folder = Path(current_folder_str)
                if current_folder.exists():
                    self.navigate_to_folder(current_folder)
                else:
                    self.navigate_to_folder(Path.home())
            else:
                self.navigate_to_folder(Path.home())

            # Update UI
            self._update_history_combo()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "settings_load"},
                AIComponent.CURSOR,
            )

    def _connect_signals(self):
        """Connect internal signals"""

        # Connect state manager changes
        self.state_manager.add_change_listener(
            "current_folder", self._on_current_folder_changed
        )

    # File discovery methods

    def _discover_images_in_folder(self, folder_path: Path) -> List[Path]:
        """
        指定されたフォルダ内の画像ファイルを検出する

        FileDiscoveryServiceを使用してフォルダ内の画像ファイルを検出し、
        適切なエラーハンドリングとユーザーフィードバックを提供します。

        処理フロー:
        1. FileDiscoveryServiceによる画像ファイル検出
        2. 検出結果のログ記録
        3. 画像が見つからない場合のユーザー通知
        4. エラー発生時の適切なハンドリング

        Args:
            folder_path (Path): 検索対象のフォルダパス

        Returns:
            List[Path]: 検出された画像ファイルのパスリスト

        Note:
            - 対応形式: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp
            - 画像が見つからない場合は日本語メッセージを表示
            - エラー時は詳細な日本語エラーメッセージを表示
            - 全ての処理が統合ログシステムに記録される
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_image_discovery",
                f"フォルダ内画像検出開始: {folder_path}",
                level="DEBUG",
            )

            # FileDiscoveryServiceを使用してファイル検出
            discovered_images = self.file_discovery_service.discover_images(folder_path)

            # 画像が見つからない場合の処理
            if not discovered_images:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "no_images_found",
                    f"画像ファイルが見つかりませんでした: {folder_path}",
                    level="INFO",
                )
                self._show_no_images_status(folder_path)
            else:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_image_discovery_complete",
                    f"画像検出完了: {len(discovered_images)}個のファイルを検出 - {folder_path}",
                )

            return discovered_images

        except Exception as e:
            # エラーハンドリングメソッドを使用
            self._handle_discovery_error(e, folder_path)

            # 統合エラーハンドラーにも記録
            self.error_handler.handle_error(
                e,
                ErrorCategory.FILE_ERROR,
                {
                    "operation": "discover_images_in_folder",
                    "folder_path": str(folder_path),
                    "user_action": "フォルダ内画像検出",
                },
                AIComponent.CURSOR,
            )
            return []

    def _clear_previous_folder_data(self, previous_folder: Optional[Path]):
        """
        前のフォルダのデータをクリアする

        Args:
            previous_folder: 前のフォルダのパス
        """
        try:
            if previous_folder:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_data_clear",
                    f"前のフォルダのデータをクリア: {previous_folder}",
                    level="DEBUG",
                )

                # 前のフォルダのキャッシュデータをクリア
                # (FileDiscoveryServiceが内部的にキャッシュを持っている場合の対応)
                # 現在の実装では特別なクリア処理は不要だが、将来の拡張に備えて準備

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_data_clear_complete",
                    f"フォルダデータクリア完了: {previous_folder}",
                    level="DEBUG",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "clear_previous_folder_data",
                    "previous_folder": (
                        str(previous_folder) if previous_folder else "None"
                    ),
                    "user_action": "フォルダ変更時のデータクリア",
                },
                AIComponent.CURSOR,
            )

    def _handle_discovery_error(self, error: Exception, folder_path: Path):
        """
        ファイル検出エラーを処理し、ユーザーに分かりやすい日本語メッセージを表示する

        エラーの種類を自動判別し、ユーザーが理解しやすい日本語メッセージと
        適切な対処法を提示します。

        エラー分類と対応:
        - PermissionError: アクセス権限エラー → 管理者権限での実行を提案
        - FileNotFoundError: フォルダ不存在 → フォルダの移動・削除を通知
        - TimeoutError: 読み込みタイムアウト → ネットワーク接続確認を提案
        - その他: 一般的なエラー → 詳細情報と共に表示

        Args:
            error (Exception): 発生したエラー
            folder_path (Path): エラーが発生したフォルダのパス

        Note:
            - 全てのエラーメッセージは日本語で表示
            - エラー詳細は統合ログシステムに記録
            - ユーザーには適切な対処法を提示
            - エラー統計情報も自動更新
        """
        try:
            # エラーの種類に応じて適切な日本語メッセージを生成
            error_type = type(error).__name__
            folder_name = folder_path.name if folder_path else "不明なフォルダ"

            if "Permission" in error_type or "Access" in error_type:
                error_message = f"フォルダ '{folder_name}' へのアクセス権限がありません。\n管理者権限で実行するか、フォルダの権限設定を確認してください。"
                user_message = "アクセス権限エラー"
            elif "FileNotFound" in error_type or "NotFound" in error_type:
                error_message = f"フォルダ '{folder_name}' が見つかりません。\nフォルダが移動または削除された可能性があります。"
                user_message = "フォルダが見つかりません"
            elif "Timeout" in error_type:
                error_message = f"フォルダ '{folder_name}' の読み込みがタイムアウトしました。\nネットワークドライブの場合は接続を確認してください。"
                user_message = "読み込みタイムアウト"
            else:
                error_message = f"フォルダ '{folder_name}' の画像検出中にエラーが発生しました。\n詳細: {str(error)}"
                user_message = "画像検出エラー"

            # ログにエラー詳細を記録
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "discovery_error_handling",
                f"ファイル検出エラー処理: {folder_path} - {error_type}: {str(error)}",
                level="ERROR",
            )

            # ユーザーにエラーメッセージを表示（アクセシビリティ対応）
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(user_message)
            msg_box.setText(error_message)

            # アクセシビリティ対応
            msg_box.setAccessibleName(f"エラーダイアログ: {user_message}")
            msg_box.setAccessibleDescription(
                f"フォルダアクセスエラーの詳細: {error_message}"
            )

            # 適切なボタンテキスト
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.button(QMessageBox.StandardButton.Ok).setText("了解")

            # 進行状況の表示を停止
            if hasattr(self, "progress_indicator"):
                self.progress_indicator.hide()

            msg_box.exec()

            # エラー発生をシグナルで通知
            self.navigation_error.emit(error_type.lower(), error_message)

            # エラー統計を更新（将来の改善のため）
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "error_statistics",
                f"エラー統計更新: {error_type} - フォルダ: {folder_path}",
                level="DEBUG",
            )

        except Exception as handling_error:
            # エラーハンドリング中のエラー（メタエラー）
            self.error_handler.handle_error(
                handling_error,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "handle_discovery_error",
                    "original_error": str(error),
                    "folder_path": str(folder_path),
                    "user_action": "エラー処理",
                },
                AIComponent.CURSOR,
            )

    def _show_no_images_status(self, folder_path: Path):
        """
        画像ファイルが見つからない場合のステータス表示（ダイアログではなくステータスバー）
        """
        try:
            folder_name = folder_path.name if folder_path else "選択されたフォルダ"

            # ステータスメッセージを作成
            status_message = f"📁 '{folder_name}' - 画像ファイルが見つかりません (対応形式: JPEG, PNG, GIF, BMP, TIFF, WebP)"

            # ログに記録
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "no_images_status",
                f"画像なしステータス表示: {folder_path}",
                level="INFO",
            )

            # ステータス表示シグナルを発行（メインウィンドウのステータスバーに表示）
            self.status_message.emit(status_message, 5000)  # 5秒間表示

            # 統計情報を更新
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "empty_folder_statistics",
                f"空フォルダ統計更新: {folder_path}",
                level="DEBUG",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "show_no_images_status",
                    "current_folder": str(folder_path) if folder_path else "None",
                    "user_action": "画像なしステータス表示",
                },
                AIComponent.CURSOR,
            )

    def _start_folder_monitoring(self, folder_path: Path):
        """
        指定されたフォルダの監視を開始する

        Args:
            folder_path: 監視対象のフォルダパス
        """
        try:
            # ファイルシステム監視を開始
            monitoring_started = self.file_system_watcher.start_watching(folder_path)

            if monitoring_started:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_monitoring_started",
                    f"フォルダ監視開始: {folder_path}",
                    level="INFO",
                )
            else:
                # 監視開始に失敗した場合の処理
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_monitoring_failed",
                    f"フォルダ監視の開始に失敗しました: {folder_path}",
                    level="WARNING",
                )

                # ユーザーに通知（オプション）
                self._show_monitoring_fallback_message()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "start_folder_monitoring",
                    "folder_path": str(folder_path),
                    "user_action": "フォルダ監視開始",
                },
                AIComponent.CURSOR,
            )

    def _on_file_system_change(
        self,
        file_path: Path,
        change_type: FileChangeType,
        old_path: Optional[Path] = None,
    ):
        """
        ファイルシステム変更イベントのハンドラー

        Args:
            file_path: 変更されたファイルのパス
            change_type: 変更タイプ（作成、削除、変更、移動）
            old_path: 移動前のパス（移動の場合のみ）
        """
        try:
            # 現在のフォルダ内の変更のみ処理
            if not self.current_folder or not file_path.parent == self.current_folder:
                return

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "file_system_change_detected",
                f"ファイル変更検出: {file_path.name} ({change_type.value})",
                level="DEBUG",
            )

            # 変更タイプに応じた処理
            if change_type == FileChangeType.CREATED:
                self._handle_file_created(file_path)
            elif change_type == FileChangeType.DELETED:
                self._handle_file_deleted(file_path)
            elif change_type == FileChangeType.MODIFIED:
                self._handle_file_modified(file_path)
            elif change_type == FileChangeType.MOVED:
                self._handle_file_moved(file_path, old_path)

            # フォルダ内容が変更されたことを通知
            self.folder_changed.emit(self.current_folder)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "file_system_change_handler",
                    "file_path": str(file_path),
                    "change_type": change_type.value,
                    "user_action": "ファイル変更処理",
                },
                AIComponent.CURSOR,
            )

    def _handle_file_created(self, file_path: Path):
        """
        ファイル作成イベントの処理

        Args:
            file_path: 作成されたファイルのパス
        """
        try:
            # 画像ファイルかどうかチェック
            if self._is_supported_image_file(file_path):
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "image_file_created",
                    f"新しい画像ファイルが追加されました: {file_path.name}",
                    level="INFO",
                )

                # フォルダの再スキャンをトリガー（効率的な更新のため）
                self._trigger_folder_refresh()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.FILE_ERROR,
                {
                    "operation": "handle_file_created",
                    "file_path": str(file_path),
                    "user_action": "ファイル作成処理",
                },
                AIComponent.CURSOR,
            )

    def _handle_file_deleted(self, file_path: Path):
        """
        ファイル削除イベントの処理

        Args:
            file_path: 削除されたファイルのパス
        """
        try:
            # 画像ファイルかどうかチェック（拡張子ベース）
            if self._is_supported_image_file(file_path):
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "image_file_deleted",
                    f"画像ファイルが削除されました: {file_path.name}",
                    level="INFO",
                )

                # フォルダの再スキャンをトリガー
                self._trigger_folder_refresh()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.FILE_ERROR,
                {
                    "operation": "handle_file_deleted",
                    "file_path": str(file_path),
                    "user_action": "ファイル削除処理",
                },
                AIComponent.CURSOR,
            )

    def _handle_file_modified(self, file_path: Path):
        """
        ファイル変更イベントの処理

        Args:
            file_path: 変更されたファイルのパス
        """
        try:
            # 画像ファイルかどうかチェック
            if self._is_supported_image_file(file_path):
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "image_file_modified",
                    f"画像ファイルが変更されました: {file_path.name}",
                    level="DEBUG",
                )

                # 変更されたファイルのサムネイル更新をトリガー
                # （サムネイルグリッドに直接通知する場合）
                # self.image_file_modified.emit(file_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.FILE_ERROR,
                {
                    "operation": "handle_file_modified",
                    "file_path": str(file_path),
                    "user_action": "ファイル変更処理",
                },
                AIComponent.CURSOR,
            )

    def _handle_file_moved(self, new_path: Path, old_path: Optional[Path]):
        """
        ファイル移動イベントの処理

        Args:
            new_path: 移動後のファイルパス
            old_path: 移動前のファイルパス
        """
        try:
            # 新しいパスまたは古いパスが画像ファイルの場合
            is_new_image = self._is_supported_image_file(new_path)
            is_old_image = old_path and self._is_supported_image_file(old_path)

            if is_new_image or is_old_image:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "image_file_moved",
                    f"画像ファイルが移動されました: {old_path.name if old_path else '不明'} -> {new_path.name}",
                    level="INFO",
                )

                # フォルダの再スキャンをトリガー
                self._trigger_folder_refresh()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.FILE_ERROR,
                {
                    "operation": "handle_file_moved",
                    "new_path": str(new_path),
                    "old_path": str(old_path) if old_path else "None",
                    "user_action": "ファイル移動処理",
                },
                AIComponent.CURSOR,
            )

    def _is_supported_image_file(self, file_path: Path) -> bool:
        """
        ファイルが対応する画像形式かチェックする

        Args:
            file_path: チェック対象のファイルパス

        Returns:
            対応する画像ファイルの場合True
        """
        try:
            # FileDiscoveryServiceの対応拡張子を使用
            supported_extensions = (
                self.file_discovery_service.get_supported_extensions()
            )
            return file_path.suffix.lower() in supported_extensions

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "image_file_check_error",
                f"画像ファイルチェック中にエラー: {file_path} - {str(e)}",
                level="ERROR",
            )
            return False

    def _trigger_folder_refresh(self):
        """
        フォルダの再スキャンをトリガーする（効率的な更新）
        """
        try:
            if not self.current_folder:
                return

            # 短い遅延後にフォルダを再スキャン（連続する変更をまとめて処理）
            if not hasattr(self, "_refresh_timer"):
                self._refresh_timer = QTimer()
                self._refresh_timer.setSingleShot(True)
                self._refresh_timer.timeout.connect(self._perform_folder_refresh)

            # タイマーをリセット（連続する変更を効率的に処理）
            self._refresh_timer.stop()
            self._refresh_timer.start(500)  # 500ms後に実行

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_refresh_scheduled",
                f"フォルダ再スキャンをスケジュール: {self.current_folder}",
                level="DEBUG",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "trigger_folder_refresh",
                    "current_folder": (
                        str(self.current_folder) if self.current_folder else "None"
                    ),
                    "user_action": "フォルダ更新トリガー",
                },
                AIComponent.CURSOR,
            )

    def _perform_folder_refresh(self):
        """
        実際のフォルダ再スキャンを実行する
        """
        try:
            if not self.current_folder:
                return

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_refresh_start",
                f"フォルダ再スキャン開始: {self.current_folder}",
                level="DEBUG",
            )

            # 新しい画像リストを取得
            discovered_images = self._discover_images_in_folder(self.current_folder)

            # フォルダ変更シグナルを発行（サムネイルグリッドが更新される）
            self.folder_changed.emit(self.current_folder)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_refresh_complete",
                f"フォルダ再スキャン完了: {self.current_folder} ({len(discovered_images)}個の画像ファイル)",
                level="INFO",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.FILE_ERROR,
                {
                    "operation": "perform_folder_refresh",
                    "current_folder": (
                        str(self.current_folder) if self.current_folder else "None"
                    ),
                    "user_action": "フォルダ再スキャン実行",
                },
                AIComponent.CURSOR,
            )

    def _show_monitoring_fallback_message(self):
        """
        監視機能が利用できない場合のフォールバックメッセージを表示
        """
        try:
            message = (
                "ファイルシステム監視機能が利用できません。\n\n"
                "フォルダ内のファイルが変更された場合、手動でフォルダを再選択するか、\n"
                "メニューから「更新」を選択してください。\n\n"
                "自動監視機能を有効にするには、watchdogライブラリをインストールしてください。"
            )

            # 情報メッセージとして表示（アクセシビリティ対応）
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("ファイル監視機能について")
            msg_box.setText(message)

            # アクセシビリティ対応
            msg_box.setAccessibleName("情報ダイアログ: ファイル監視機能")
            msg_box.setAccessibleDescription(
                "ファイル監視機能が利用できない場合の説明と対処法"
            )

            # 適切なボタンテキスト
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.button(QMessageBox.StandardButton.Ok).setText("了解")

            # 詳細情報ボタンを追加
            details_button = msg_box.addButton(
                "詳細情報", QMessageBox.ButtonRole.ActionRole
            )
            details_button.setAccessibleDescription("ファイル監視機能の詳細情報を表示")

            result = msg_box.exec()

            # 詳細情報が要求された場合
            if msg_box.clickedButton() == details_button:
                self._show_file_monitoring_details()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "monitoring_fallback_message",
                "ファイル監視フォールバックメッセージを表示",
                level="INFO",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "show_monitoring_fallback_message",
                    "user_action": "監視フォールバックメッセージ表示",
                },
                AIComponent.CURSOR,
            )

    def _show_file_monitoring_details(self):
        """
        ファイル監視機能の詳細情報を表示する
        """
        try:
            details_message = (
                "ファイル監視機能の詳細情報:\n\n"
                "【機能概要】\n"
                "• フォルダ内のファイル変更を自動検出\n"
                "• 画像ファイルの追加・削除・変更を監視\n"
                "• リアルタイムでサムネイル表示を更新\n\n"
                "【必要な環境】\n"
                "• Python watchdogライブラリ\n"
                "• インストール方法: pip install watchdog\n\n"
                "【代替手段】\n"
                "• フォルダを再選択して手動更新\n"
                "• メニューから「更新」を選択\n"
                "• F5キーで画面を更新\n\n"
                "【トラブルシューティング】\n"
                "• ネットワークドライブでは動作しない場合があります\n"
                "• 大量のファイルがある場合は無効化されることがあります"
            )

            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("ファイル監視機能 - 詳細情報")
            msg_box.setText(details_message)

            # アクセシビリティ対応
            msg_box.setAccessibleName("詳細情報ダイアログ: ファイル監視機能")
            msg_box.setAccessibleDescription(
                "ファイル監視機能の詳細な説明とトラブルシューティング情報"
            )

            # ボタンの設定
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.button(QMessageBox.StandardButton.Ok).setText("了解")

            msg_box.exec()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "show_file_monitoring_details",
                    "user_action": "詳細情報表示",
                },
                AIComponent.CURSOR,
            )

    def stop_monitoring(self):
        """
        ファイルシステム監視を停止する（クリーンアップ用）
        """
        try:
            if self.file_system_watcher.is_watching:
                self.file_system_watcher.stop_watching()

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "monitoring_stopped",
                    "ファイルシステム監視を停止しました",
                    level="INFO",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "stop_monitoring", "user_action": "監視停止"},
                AIComponent.CURSOR,
            )

    # Public methods

    def navigate_to_folder(self, folder_path: Path) -> bool:
        """Navigate to the specified folder"""

        try:
            if not folder_path.exists() or not folder_path.is_dir():
                self.navigation_error.emit(
                    "invalid_path", f"Invalid folder: {folder_path}"
                )
                return False

            # Stop watching previous folder
            if self.file_system_watcher.is_watching:
                self.file_system_watcher.stop_watching()

            # Clear previous folder data
            old_folder = self.current_folder
            if old_folder and old_folder != folder_path:
                self._clear_previous_folder_data(old_folder)

            # Update current folder
            self.current_folder = folder_path

            # Add to history
            if old_folder and old_folder != folder_path:
                self._add_to_history(old_folder)

            # Update UI
            self._update_ui_for_folder(folder_path)

            # Update configuration
            self.config_manager.set_setting("ui.current_folder", str(folder_path))

            # Discover images in the new folder
            discovered_images = self._discover_images_in_folder(folder_path)

            # Start watching the new folder for changes
            self._start_folder_monitoring(folder_path)

            # Emit signals with discovered images
            self.folder_selected.emit(folder_path)
            self.folder_changed.emit(folder_path)

            # Log folder change with image count
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_change_complete",
                f"フォルダ変更完了: {folder_path} ({len(discovered_images)}個の画像ファイル)",
            )

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "folder_navigate", f"Navigated to: {folder_path}"
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "navigate_to_folder", "folder": str(folder_path)},
                AIComponent.CURSOR,
            )
            return False

    def open_folder_dialog(self):
        """Open folder selection dialog"""

        try:
            initial_dir = (
                str(self.current_folder) if self.current_folder else str(Path.home())
            )

            folder = QFileDialog.getExistingDirectory(
                self, "Select Folder", initial_dir
            )

            if folder:
                self.navigate_to_folder(Path(folder))

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "folder_dialog"},
                AIComponent.CURSOR,
            )

    def get_current_folder(self) -> Optional[Path]:
        """Get the current folder"""
        return self.current_folder

    def get_folder_history(self) -> List[Path]:
        """Get folder history"""
        return self.folder_history.copy()

    def get_bookmarks(self) -> List[Path]:
        """Get bookmarks"""
        return self.bookmarks.copy()

    # Event handlers

    def _on_tree_item_clicked(self, index: QModelIndex):
        """Handle tree item click"""

        try:
            if index.isValid():
                file_path = Path(self.file_system_model.filePath(index))

                if file_path.is_dir():
                    # Delay navigation to avoid rapid updates
                    self.update_timer.stop()
                    self.update_timer.start(100)  # 100ms delay
                    self._pending_folder = file_path

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "tree_item_click"},
                AIComponent.CURSOR,
            )

    def _on_tree_item_double_clicked(self, index: QModelIndex):
        """Handle tree item double click"""

        try:
            if index.isValid():
                file_path = Path(self.file_system_model.filePath(index))

                if file_path.is_dir():
                    self.navigate_to_folder(file_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "tree_item_double_click"},
                AIComponent.CURSOR,
            )

    def _delayed_folder_update(self):
        """Handle delayed folder update (Kiro optimization)"""

        if hasattr(self, "_pending_folder"):
            folder = self._pending_folder
            delattr(self, "_pending_folder")

            # Only navigate if it's different from current
            if folder != self.current_folder:
                self.navigate_to_folder(folder)

    def _navigate_to_address(self):
        """Navigate to address bar path"""

        try:
            address = self.address_bar.text().strip()
            if address:
                folder_path = Path(address).expanduser().resolve()
                self.navigate_to_folder(folder_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "navigate_to_address", "address": address},
                AIComponent.CURSOR,
            )

    def _navigate_to_history(self, folder_str: str):
        """Navigate to folder from history"""

        try:
            if folder_str and folder_str != "Select folder...":
                folder_path = Path(folder_str)
                if folder_path.exists():
                    self.navigate_to_folder(folder_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "navigate_to_history", "folder": folder_str},
                AIComponent.CURSOR,
            )

    def _go_back(self):
        """Go back in history"""

        if self.folder_history:
            previous_folder = self.folder_history.pop()
            if previous_folder.exists():
                self.navigate_to_folder(previous_folder)

    def _go_forward(self):
        """Go forward in history (placeholder)"""

        # TODO: Implement forward navigation
        pass

    def _go_up(self):
        """Go up one directory level"""

        if self.current_folder and self.current_folder.parent != self.current_folder:
            self.navigate_to_folder(self.current_folder.parent)

    def _go_home(self):
        """Go to home directory"""

        self.navigate_to_folder(Path.home())

    def _bookmark_current_folder(self):
        """Bookmark the current folder"""

        try:
            if self.current_folder and self.current_folder not in self.bookmarks:
                self.bookmarks.append(self.current_folder)

                # Save bookmarks
                bookmarks_data = [str(p) for p in self.bookmarks]
                self.config_manager.set_setting("ui.bookmarks", bookmarks_data)

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_bookmark",
                    f"Bookmarked: {self.current_folder}",
                )

                QMessageBox.information(
                    self,
                    "Bookmark Added",
                    f"Folder bookmarked: {self.current_folder.name}",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "bookmark_folder"},
                AIComponent.CURSOR,
            )

    def _on_current_folder_changed(self, key: str, old_value: Any, new_value: Any):
        """Handle current folder change from state manager"""

        if isinstance(new_value, Path) and new_value != self.current_folder:
            self.navigate_to_folder(new_value)

    # UI update methods

    def _update_ui_for_folder(self, folder_path: Path):
        """Update UI elements for the new folder"""

        try:
            # Update address bar
            self.address_bar.setText(str(folder_path))

            # Update tree view selection
            index = self.file_system_model.index(str(folder_path))
            if index.isValid():
                self.folder_tree.setCurrentIndex(index)
                self.folder_tree.scrollTo(index)

            # Update navigation buttons
            self.back_btn.setEnabled(len(self.folder_history) > 0)
            self.up_btn.setEnabled(folder_path.parent != folder_path)

            # Update history combo
            self._update_history_combo()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "ui_update", "folder": str(folder_path)},
                AIComponent.CURSOR,
            )

    def _add_to_history(self, folder_path: Path):
        """Add folder to history"""

        try:
            # Remove if already in history
            if folder_path in self.folder_history:
                self.folder_history.remove(folder_path)

            # Add to beginning
            self.folder_history.insert(0, folder_path)

            # Limit history size
            if len(self.folder_history) > self.max_history:
                self.folder_history = self.folder_history[: self.max_history]

            # Save to configuration
            history_data = [str(p) for p in self.folder_history]
            self.config_manager.set_setting("ui.folder_history", history_data)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "add_to_history", "folder": str(folder_path)},
                AIComponent.CURSOR,
            )

    def _update_history_combo(self):
        """Update history combo box"""

        try:
            self.history_combo.clear()
            self.history_combo.addItem("Select folder...")

            for folder in self.folder_history:
                if folder.exists():
                    self.history_combo.addItem(str(folder))

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "history_combo_update"},
                AIComponent.CURSOR,
            )

    # Context menu

    def contextMenuEvent(self, event):
        """Show context menu"""

        try:
            menu = QMenu(self)

            # Navigation actions
            if self.current_folder:
                open_action = menu.addAction("Open in File Manager")
                open_action.triggered.connect(self._open_in_file_manager)

                menu.addSeparator()

                bookmark_action = menu.addAction("Bookmark This Folder")
                bookmark_action.triggered.connect(self._bookmark_current_folder)

            # Bookmarks submenu
            if self.bookmarks:
                bookmarks_menu = menu.addMenu("Bookmarks")

                for bookmark in self.bookmarks:
                    if bookmark.exists():
                        action = bookmarks_menu.addAction(bookmark.name)
                        action.triggered.connect(
                            lambda checked, path=bookmark: self.navigate_to_folder(path)
                        )

                bookmarks_menu.addSeparator()
                clear_bookmarks_action = bookmarks_menu.addAction("Clear All Bookmarks")
                clear_bookmarks_action.triggered.connect(self._clear_bookmarks)

            menu.addSeparator()

            # History actions
            clear_history_action = menu.addAction("Clear History")
            clear_history_action.triggered.connect(self._clear_history)

            menu.exec(event.globalPos())

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "context_menu"},
                AIComponent.CURSOR,
            )

    def closeEvent(self, event):
        """Handle widget close event"""
        try:
            # Stop file system monitoring
            self.stop_monitoring()

            # Stop any running timers
            if hasattr(self, "_refresh_timer"):
                self._refresh_timer.stop()

            if self.update_timer:
                self.update_timer.stop()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_navigator_cleanup",
                "フォルダナビゲーターのクリーンアップ完了",
                level="INFO",
            )

            super().closeEvent(event)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "folder_navigator_cleanup"},
                AIComponent.CURSOR,
            )
            super().closeEvent(event)

    def _open_in_file_manager(self):
        """Open current folder in system file manager"""

        try:
            if self.current_folder:
                import platform
                import subprocess

                system = platform.system()
                if system == "Windows":
                    subprocess.run(["explorer", str(self.current_folder)])
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", str(self.current_folder)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(self.current_folder)])

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "open_in_file_manager"},
                AIComponent.CURSOR,
            )

    def _clear_bookmarks(self):
        """Clear all bookmarks"""

        try:
            self.bookmarks.clear()
            self.config_manager.set_setting("ui.bookmarks", [])

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "bookmarks_clear", "All bookmarks cleared"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "clear_bookmarks"},
                AIComponent.CURSOR,
            )

    def _clear_history(self):
        """Clear folder history"""

        try:
            self.folder_history.clear()
            self.config_manager.set_setting("ui.folder_history", [])
            self._update_history_combo()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "history_clear", "Folder history cleared"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "clear_history"},
                AIComponent.CURSOR,
            )

    # Accessibility features (Kiro enhancement)

    def set_accessibility_mode(self, enabled: bool):
        """Enable or disable accessibility features"""

        try:
            if enabled:
                # Increase font size
                font = self.font()
                font.setPointSize(font.pointSize() + 2)
                self.setFont(font)

                # Add keyboard shortcuts
                self.address_bar.setToolTip("Press Enter to navigate to this path")

                # Enable focus indicators
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "accessibility_mode",
                f"Accessibility mode {'enabled' if enabled else 'disabled'}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "accessibility_mode", "enabled": enabled},
                AIComponent.KIRO,
            )

    # Performance optimization (Kiro enhancement)

    def optimize_for_large_directories(self, enabled: bool = True):
        """Optimize for large directories"""
        try:
            if enabled:
                # Reduce update frequency
                self.update_timer.setInterval(200)  # Increase delay

                # Limit visible items in tree
                if hasattr(self.folder_tree, "setUniformRowHeights"):
                    self.folder_tree.setUniformRowHeights(True)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "large_directory_optimization",
                f"Large directory optimization {'enabled' if enabled else 'disabled'}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "large_directory_optimization", "enabled": enabled},
                AIComponent.KIRO,
            )
