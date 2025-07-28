"""
Optimized Thumbnail Grid for AI Integration - 最適化サムネイルグリッド

CursorBLDの高速サムネイル表示とKiroの最適化を組み合わせた
高性能サムネイルグリッドコンポーネント。

主な機能:
- CursorBLD: Qt native高速サムネイル生成と表示
- Kiro: メモリ管理、キャッシュ機能、パフォーマンス監視
- CS4Coding: 正確なEXIFデータ統合と表示
- 非同期サムネイル読み込みによる応答性向上
- 動的ファイルリスト更新対応

技術仕様:
- ThreadPoolExecutorによる並列サムネイル生成
- LRUキャッシュによる効率的なメモリ使用
- QMutexによるスレッドセーフな操作
- 設定可能なサムネイルサイズとグリッド列数
- リアルタイムパフォーマンス監視

UI機能:
- マウスクリック・ダブルクリック・右クリックメニュー対応
- EXIFデータのツールチップ表示
- ローディング・エラー・空状態の適切な表示
- サムネイルサイズのリアルタイム調整

Author: Kiro AI Integration System
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QGridLayout,
    QPushButton,
    QSlider,
    QSpinBox,
    QFrame,
    QMenu,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QSize,
    pyqtSignal,
    QTimer,
    QThread,
    QObject,
    QMutex,
    QMutexLocker,
)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont

from ..models import ImageMetadata, AIComponent, ProcessingStatus
from ..config_manager import ConfigManager
from ..state_manager import StateManager
from ..error_handling import IntegratedErrorHandler, ErrorCategory
from ..logging_system import LoggerSystem


class ThumbnailItem(QLabel):
    """
    Individual thumbnail item with Kiro optimization
    """

    clicked = pyqtSignal(Path)
    context_menu_requested = pyqtSignal(Path, object)  # image_path, position
    exif_info_requested = pyqtSignal(Path)

    def __init__(self, image_path: Path, thumbnail_size: int = 150):
        super().__init__()

        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.is_loaded = False
        self.is_loading = False

        # Setup UI
        self.setFixedSize(thumbnail_size + 20, thumbnail_size + 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            """
            QLabel {
                border: 2px solid transparent;
                border-radius: 4px;
                background-color: #f8f9fa;
                padding: 4px;
            }
            QLabel:hover {
                border-color: #007acc;
                background-color: #e3f2fd;
            }
        """
        )

        # Show placeholder
        self._show_placeholder()

    def _show_placeholder(self):
        """Show placeholder while loading"""

        placeholder = QPixmap(self.thumbnail_size, self.thumbnail_size)
        placeholder.fill(QColor("#e9ecef"))

        # Draw placeholder text
        painter = QPainter(placeholder)
        painter.setPen(QColor("#6c757d"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "Loading...")
        painter.end()

        self.setPixmap(placeholder)
        self.setText(self.image_path.name)

    def set_thumbnail(self, pixmap: QPixmap):
        """Set the thumbnail pixmap"""

        if pixmap and not pixmap.isNull():
            # Scale pixmap to fit
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_size,
                self.thumbnail_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            self.setPixmap(scaled_pixmap)
            self.is_loaded = True
        else:
            self._show_error()

    def _show_error(self):
        """Show error placeholder"""
        error_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        error_pixmap.fill(QColor("#f8d7da"))

        painter = QPainter(error_pixmap)
        painter.setPen(QColor("#721c24"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(error_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Error")
        painter.end()

        self.setPixmap(error_pixmap)

    def set_exif_info(self, exif_data: Dict[str, Any]):
        """Set EXIF information for display"""
        if not exif_data:
            return

        # Create tooltip with EXIF information
        tooltip_lines = []

        # Camera information
        if exif_data.get("camera_make") and exif_data.get("camera_model"):
            tooltip_lines.append(
                f"Camera: {exif_data['camera_make']} {exif_data['camera_model']}"
            )

        # Lens information
        if exif_data.get("lens_model"):
            tooltip_lines.append(f"Lens: {exif_data['lens_model']}")

        # Shooting settings
        settings = []
        if exif_data.get("focal_length"):
            settings.append(f"{exif_data['focal_length']}mm")
        if exif_data.get("aperture"):
            settings.append(f"f/{exif_data['aperture']}")
        if exif_data.get("shutter_speed"):
            settings.append(f"{exif_data['shutter_speed']}")
        if exif_data.get("iso"):
            settings.append(f"ISO {exif_data['iso']}")

        if settings:
            tooltip_lines.append(" | ".join(settings))

        # GPS information
        if exif_data.get("latitude") and exif_data.get("longitude"):
            tooltip_lines.append(
                f"GPS: {exif_data['latitude']:.6f}, {exif_data['longitude']:.6f}"
            )

        # Image dimensions
        if exif_data.get("width") and exif_data.get("height"):
            tooltip_lines.append(f"Size: {exif_data['width']} × {exif_data['height']}")

        if tooltip_lines:
            self.setToolTip("\n".join(tooltip_lines))

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self.image_path, event.globalPosition())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.exif_info_requested.emit(self.image_path)
        super().mouseDoubleClickEvent(event)

    def _show_error(self):
        """Show error placeholder"""

        error_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        error_pixmap.fill(QColor("#f8d7da"))

        painter = QPainter(error_pixmap)
        painter.setPen(QColor("#721c24"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(error_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Error")
        painter.end()

        self.setPixmap(error_pixmap)

    def mousePressEvent(self, event):
        """Handle mouse click"""

        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)


class ThumbnailLoader(QObject):
    """
    Asynchronous thumbnail loader with Kiro optimization
    """

    thumbnail_loaded = pyqtSignal(Path, QPixmap)
    loading_progress = pyqtSignal(int, int)  # current, total

    def __init__(self, logger_system: LoggerSystem):
        super().__init__()

        self.logger_system = logger_system
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.loading_queue: List[Path] = []
        self.cache: Dict[str, QPixmap] = {}
        self.cache_mutex = QMutex()
        self.is_loading = False

        # Performance tracking
        self.load_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0

    def load_thumbnails(self, image_paths: List[Path], thumbnail_size: int):
        """Load thumbnails for multiple images"""

        if self.is_loading:
            return

        self.is_loading = True
        self.loading_queue = image_paths.copy()

        # Submit loading tasks
        for i, image_path in enumerate(image_paths):
            future = self.executor.submit(
                self._load_single_thumbnail,
                image_path,
                thumbnail_size,
                i,
                len(image_paths),
            )

    def _load_single_thumbnail(
        self, image_path: Path, size: int, index: int, total: int
    ):
        """Load a single thumbnail"""

        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"{image_path}_{size}"

            with QMutexLocker(self.cache_mutex):
                if cache_key in self.cache:
                    self.cache_hits += 1
                    self.thumbnail_loaded.emit(image_path, self.cache[cache_key])
                    self.loading_progress.emit(index + 1, total)
                    return

            self.cache_misses += 1

            # Load image and create thumbnail
            pixmap = QPixmap(str(image_path))

            if not pixmap.isNull():
                # Scale to thumbnail size
                thumbnail = pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                # Cache the thumbnail
                with QMutexLocker(self.cache_mutex):
                    self.cache[cache_key] = thumbnail

                    # Limit cache size (Kiro optimization)
                    if len(self.cache) > 1000:
                        # Remove oldest 100 items
                        keys_to_remove = list(self.cache.keys())[:100]
                        for key in keys_to_remove:
                            del self.cache[key]

                # Emit loaded signal
                self.thumbnail_loaded.emit(image_path, thumbnail)
            else:
                # Emit with null pixmap for error handling
                self.thumbnail_loaded.emit(image_path, QPixmap())

            # Update progress
            self.loading_progress.emit(index + 1, total)

            # Track performance
            load_time = time.time() - start_time
            self.load_times.append(load_time)

            # Keep only recent load times
            if len(self.load_times) > 100:
                self.load_times = self.load_times[-100:]

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.CURSOR,
                e,
                "thumbnail_load",
                {"image_path": str(image_path), "size": size},
            )

            # Emit error
            self.thumbnail_loaded.emit(image_path, QPixmap())
            self.loading_progress.emit(index + 1, total)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""

        with QMutexLocker(self.cache_mutex):
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

            avg_load_time = (
                sum(self.load_times) / len(self.load_times) if self.load_times else 0
            )

            return {
                "cache_size": len(self.cache),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": hit_rate,
                "average_load_time": avg_load_time,
                "recent_load_times": self.load_times[-10:],
            }

    def clear_cache(self):
        """Clear thumbnail cache"""

        with QMutexLocker(self.cache_mutex):
            self.cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0


class OptimizedThumbnailGrid(QWidget):
    """
    Optimized thumbnail grid with fast loading and EXIF display

    Features:
    - CursorBLD: High-speed thumbnail generation and display
    - Kiro: Memory management, intelligent caching, performance monitoring
    - CS4Coding: Accurate EXIF data integration
    """

    # Signals
    image_selected = pyqtSignal(Path)
    thumbnail_requested = pyqtSignal(Path)
    exif_display_requested = pyqtSignal(Path)
    performance_warning = pyqtSignal(str)

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
    ):
        """
        Initialize optimized thumbnail grid

        Args:
            config_manager: Configuration manager
            state_manager: State manager
            logger_system: Logging system
        """
        super().__init__()

        # Core systems
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Grid settings
        self.thumbnail_size = self.state_manager.get_state().thumbnail_size
        self.columns = 4
        self.spacing = 10

        # Data storage
        self.image_list: List[Path] = []
        self.thumbnail_items: Dict[Path, ThumbnailItem] = {}
        self.exif_cache: Dict[Path, Dict[str, Any]] = {}

        # Performance tracking
        self.load_start_time = None
        self.loaded_count = 0
        self.total_count = 0
        self.performance_metrics = {
            "avg_load_time": 0.0,
            "cache_hit_rate": 0.0,
            "memory_usage": 0,
        }

        # Threading
        self.thumbnail_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="thumbnail"
        )
        self.exif_executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="exif"
        )
        self.load_mutex = QMutex()

        # UI components
        self.scroll_area: Optional[QScrollArea] = None
        self.grid_widget: Optional[QWidget] = None
        self.grid_layout: Optional[QGridLayout] = None
        self.controls_widget: Optional[QWidget] = None

        # Performance monitoring
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._monitor_performance)
        self.performance_timer.start(2000)  # Check every 2 seconds

        # Progress indicator for accessibility
        self.progress_indicator = None

        # Initialize UI
        self._setup_ui()

        self.logger_system.log_ai_operation(
            AIComponent.CURSOR,
            "thumbnail_grid_init",
            "Optimized thumbnail grid initialized",
        )

    def show_progress_indicator(self, message: str, maximum: int = 0):
        """
        進行状況インジケーターを表示する（アクセシビリティ対応）

        Args:
            message: 進行状況メッセージ
            maximum: 最大値（0の場合は不定進行状況）
        """
        try:
            from PyQt6.QtWidgets import QProgressBar, QVBoxLayout, QLabel

            # 既存のインジケーターを削除
            if self.progress_indicator:
                self.progress_indicator.deleteLater()

            # 進行状況ウィジェットを作成
            self.progress_indicator = QWidget(self)
            progress_layout = QVBoxLayout(self.progress_indicator)

            # メッセージラベル
            message_label = QLabel(message)
            message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_label.setAccessibleName("進行状況メッセージ")
            message_label.setAccessibleDescription(f"現在の処理状況: {message}")
            progress_layout.addWidget(message_label)

            # プログレスバー
            progress_bar = QProgressBar()
            if maximum > 0:
                progress_bar.setMaximum(maximum)
                progress_bar.setValue(0)
            else:
                progress_bar.setRange(0, 0)  # 不定進行状況

            progress_bar.setAccessibleName("進行状況バー")
            progress_bar.setAccessibleDescription("処理の進行状況を示すプログレスバー")
            progress_layout.addWidget(progress_bar)

            # スタイル設定
            self.progress_indicator.setStyleSheet(
                """
                QWidget {
                    background-color: rgba(255, 255, 255, 240);
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 20px;
                }
                QProgressBar {
                    border: 2px solid #e0e0e0;
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #2196f3;
                    border-radius: 3px;
                }
            """
            )

            # 位置とサイズの設定
            self.progress_indicator.resize(300, 100)
            self.progress_indicator.move(
                (self.width() - 300) // 2, (self.height() - 100) // 2
            )

            self.progress_indicator.show()
            self.progress_indicator.raise_()

            # 参照を保存
            self._progress_bar = progress_bar
            self._progress_message = message_label

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "show_progress_indicator",
                    "message": message,
                    "user_action": "進行状況表示",
                },
                AIComponent.CURSOR,
            )

    def update_progress(self, value: int, message: str = None):
        """
        進行状況を更新する

        Args:
            value: 現在の値
            message: 更新するメッセージ（オプション）
        """
        try:
            if hasattr(self, "_progress_bar") and self._progress_bar:
                self._progress_bar.setValue(value)

                # アクセシビリティ用の説明更新
                total = self._progress_bar.maximum()
                if total > 0:
                    percentage = (value / total) * 100
                    self._progress_bar.setAccessibleDescription(
                        f"進行状況: {value}/{total} ({percentage:.0f}%)"
                    )

            if (
                message
                and hasattr(self, "_progress_message")
                and self._progress_message
            ):
                self._progress_message.setText(message)
                self._progress_message.setAccessibleDescription(
                    f"現在の処理状況: {message}"
                )

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "progress_update_error",
                f"進行状況更新エラー: {str(e)}",
                level="WARNING",
            )

    def hide_progress_indicator(self):
        """
        進行状況インジケーターを非表示にする
        """
        try:
            if self.progress_indicator:
                self.progress_indicator.hide()
                self.progress_indicator.deleteLater()
                self.progress_indicator = None
                self._progress_bar = None
                self._progress_message = None

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "progress_hide_error",
                f"進行状況非表示エラー: {str(e)}",
                level="WARNING",
            )

    def _setup_ui(self):
        """Setup the user interface"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Controls
            self.controls_widget = self._create_controls()
            layout.addWidget(self.controls_widget)

            # Scroll area for thumbnails
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )

            # Grid widget
            self.grid_widget = QWidget()
            self.grid_layout = QGridLayout(self.grid_widget)
            self.grid_layout.setSpacing(self.spacing)
            self.grid_layout.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )

            self.scroll_area.setWidget(self.grid_widget)
            layout.addWidget(self.scroll_area)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "setup_ui"}, AIComponent.CURSOR
            )

    def _create_controls(self) -> QWidget:
        """Create control widgets"""
        controls = QWidget()
        layout = QHBoxLayout(controls)

        # Thumbnail size control
        size_label = QLabel("Size:")
        layout.addWidget(size_label)

        size_slider = QSlider(Qt.Orientation.Horizontal)
        size_slider.setRange(50, 300)
        size_slider.setValue(self.thumbnail_size)
        size_slider.valueChanged.connect(self._on_size_changed)
        layout.addWidget(size_slider)

        size_spinbox = QSpinBox()
        size_spinbox.setRange(50, 300)
        size_spinbox.setValue(self.thumbnail_size)
        size_spinbox.valueChanged.connect(self._on_size_changed)
        layout.addWidget(size_spinbox)

        # Connect slider and spinbox
        size_slider.valueChanged.connect(size_spinbox.setValue)
        size_spinbox.valueChanged.connect(size_slider.setValue)

        layout.addStretch()

        # Performance info
        self.performance_label = QLabel("Ready")
        layout.addWidget(self.performance_label)

        return controls

    def set_image_list(self, image_list: List[Path]):
        """Set the list of images to display"""
        try:
            with QMutexLocker(self.load_mutex):
                self.image_list = image_list
                self.total_count = len(image_list)
                self.loaded_count = 0
                self.load_start_time = time.time()

            # Clear existing thumbnails
            self.clear_thumbnails_safely()

            # Create thumbnail items
            self._create_thumbnail_items()

            # Start loading thumbnails
            self._load_thumbnails_async()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "image_list_set",
                f"Image list set with {len(image_list)} images",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_image_list", "count": len(image_list)},
                AIComponent.CURSOR,
            )

    def update_image_list(self, image_list: List[Path]):
        """
        動的にファイルリストを更新する（ファイルシステム監視用）

        ファイルシステム監視からの通知に基づいて、サムネイルグリッドを
        効率的に更新します。差分検出により必要最小限の更新を実行します。

        処理フロー:
        1. 現在のリストと新しいリストの差分を計算
        2. 削除されたファイルのサムネイルを除去
        3. 追加されたファイルの新しいサムネイルを生成
        4. グリッドレイアウトの再構成
        5. 統計情報とパフォーマンス指標の更新

        Args:
            image_list (List[Path]): 新しい画像ファイルのリスト

        Note:
            - 差分検出により効率的な更新を実現
            - 既存のサムネイルキャッシュは保持される
            - スレッドセーフな操作が保証される
            - 更新中もUI応答性を維持
            - 詳細な更新ログが記録される
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "image_list_update_start",
                f"画像リスト更新開始: {len(image_list)}個のファイル",
                level="DEBUG",
            )

            # 現在のリストと比較して変更を検出
            old_set = set(self.image_list)
            new_set = set(image_list)

            # 追加されたファイル
            added_files = new_set - old_set
            # 削除されたファイル
            removed_files = old_set - new_set

            if added_files or removed_files:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "image_list_changes_detected",
                    f"変更検出 - 追加: {len(added_files)}, 削除: {len(removed_files)}",
                    level="INFO",
                )

                # 削除されたファイルのサムネイルを削除
                for removed_file in removed_files:
                    self._remove_thumbnail_item(removed_file)

                # 新しいファイルのサムネイルを追加
                for added_file in added_files:
                    self._add_thumbnail_item(added_file)

                # リストを更新
                with QMutexLocker(self.load_mutex):
                    self.image_list = image_list
                    self.total_count = len(image_list)

                # レイアウトを再構成
                self._reorganize_grid()

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "image_list_update_complete",
                    f"画像リスト更新完了: {len(image_list)}個のファイル",
                    level="INFO",
                )
            else:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "image_list_no_changes",
                    "画像リストに変更はありませんでした",
                    level="DEBUG",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "update_image_list",
                    "new_count": len(image_list),
                    "old_count": len(self.image_list),
                    "user_action": "画像リスト動的更新",
                },
                AIComponent.CURSOR,
            )

    def clear_thumbnails_safely(self):
        """
        既存のサムネイルを安全にクリアする

        メモリリークを防ぐため、全てのサムネイルアイテムを適切に
        削除し、関連するリソースを解放します。

        処理内容:
        1. 各サムネイルアイテムのレイアウトからの除去
        2. Qtウィジェットの適切な削除（deleteLater）
        3. 内部辞書とキャッシュのクリア
        4. EXIFデータキャッシュのクリア
        5. メモリ使用量の最適化

        Note:
            - Qt のメモリ管理に従った安全な削除
            - 削除中のエラーは個別にハンドリング
            - 全ての操作がログに記録される
            - メモリリークの防止を最優先
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnails_clear_start",
                f"サムネイルクリア開始: {len(self.thumbnail_items)}個のアイテム",
                level="DEBUG",
            )

            # 既存のサムネイルアイテムを削除
            for image_path, thumbnail_item in self.thumbnail_items.items():
                try:
                    # レイアウトから削除
                    self.grid_layout.removeWidget(thumbnail_item)
                    # ウィジェットを削除
                    thumbnail_item.deleteLater()
                except Exception as item_error:
                    self.logger_system.log_ai_operation(
                        AIComponent.CURSOR,
                        "thumbnail_item_clear_error",
                        f"サムネイルアイテム削除エラー: {image_path} - {str(item_error)}",
                        level="WARNING",
                    )

            # 辞書をクリア
            self.thumbnail_items.clear()

            # EXIFキャッシュもクリア
            self.exif_cache.clear()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnails_clear_complete",
                "サムネイルクリア完了",
                level="DEBUG",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "clear_thumbnails_safely",
                    "user_action": "サムネイル安全クリア",
                },
                AIComponent.CURSOR,
            )

    def show_loading_state(self, message: str):
        """
        ローディング状態を表示する（アクセシビリティ対応）

        Args:
            message: 表示するメッセージ
        """
        try:
            # パフォーマンスラベルにローディングメッセージを表示
            if hasattr(self, "performance_label"):
                loading_text = f"🔄 {message}"
                self.performance_label.setText(loading_text)

                # アクセシビリティ対応
                self.performance_label.setAccessibleName("読み込み状態")
                self.performance_label.setAccessibleDescription(
                    f"現在の状態: {message}"
                )

                # スクリーンリーダー用の追加情報
                self.setAccessibleDescription(f"サムネイルグリッド: {message}")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "loading_state_shown",
                f"ローディング状態表示: {message}",
                level="DEBUG",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "show_loading_state",
                    "message": message,
                    "user_action": "ローディング状態表示",
                },
                AIComponent.CURSOR,
            )

    def show_error_state(self, error_message: str):
        """
        エラー状態を表示する（アクセシビリティ対応）

        Args:
            error_message: エラーメッセージ
        """
        try:
            # パフォーマンスラベルにエラーメッセージを表示
            if hasattr(self, "performance_label"):
                error_text = f"❌ エラー: {error_message}"
                self.performance_label.setText(error_text)

                # アクセシビリティ対応
                self.performance_label.setAccessibleName("エラー状態")
                self.performance_label.setAccessibleDescription(
                    f"エラーが発生しました: {error_message}"
                )

                # 高コントラストモード対応
                self.performance_label.setStyleSheet(
                    """
                    QLabel {
                        color: #d32f2f;
                        background-color: #ffebee;
                        border: 1px solid #d32f2f;
                        border-radius: 4px;
                        padding: 4px;
                    }
                """
                )

                # スクリーンリーダー用の追加情報
                self.setAccessibleDescription(
                    f"サムネイルグリッド: エラー - {error_message}"
                )

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "error_state_shown",
                f"エラー状態表示: {error_message}",
                level="INFO",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "show_error_state",
                    "error_message": error_message,
                    "user_action": "エラー状態表示",
                },
                AIComponent.CURSOR,
            )

    def show_empty_state(self):
        """
        空の状態（画像なし）を表示する（アクセシビリティ対応）
        """
        try:
            # パフォーマンスラベルに空状態メッセージを表示
            if hasattr(self, "performance_label"):
                empty_text = "📁 画像ファイルがありません"
                self.performance_label.setText(empty_text)

                # アクセシビリティ対応
                self.performance_label.setAccessibleName("空の状態")
                self.performance_label.setAccessibleDescription(
                    "選択されたフォルダに画像ファイルがありません"
                )

                # スタイル調整（視認性向上）
                self.performance_label.setStyleSheet(
                    """
                    QLabel {
                        color: #757575;
                        font-style: italic;
                        padding: 8px;
                    }
                """
                )

                # スクリーンリーダー用の追加情報
                self.setAccessibleDescription("サムネイルグリッド: 画像ファイルなし")

            # 空状態用のプレースホルダーを表示
            self._show_empty_placeholder()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "empty_state_shown", "空状態表示", level="DEBUG"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_empty_state", "user_action": "空状態表示"},
                AIComponent.CURSOR,
            )

    def _show_empty_placeholder(self):
        """
        空状態用のプレースホルダーを表示する
        """
        try:
            # 既存のプレースホルダーを削除
            if hasattr(self, "_empty_placeholder"):
                self._empty_placeholder.deleteLater()

            # 新しいプレースホルダーを作成
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont

            self._empty_placeholder = QLabel(self.grid_widget)
            self._empty_placeholder.setText(
                "📁\n\n"
                "画像ファイルがありません\n\n"
                "対応形式: JPG, PNG, GIF, BMP, TIFF, WebP\n"
                "別のフォルダを選択してください"
            )

            # スタイル設定
            font = QFont()
            font.setPointSize(14)
            self._empty_placeholder.setFont(font)
            self._empty_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_placeholder.setStyleSheet(
                """
                QLabel {
                    color: #9e9e9e;
                    background-color: #fafafa;
                    border: 2px dashed #e0e0e0;
                    border-radius: 8px;
                    padding: 40px;
                    margin: 20px;
                }
            """
            )

            # アクセシビリティ対応
            self._empty_placeholder.setAccessibleName("空状態プレースホルダー")
            self._empty_placeholder.setAccessibleDescription(
                "画像ファイルがない状態を示すプレースホルダー。"
                "対応形式の説明と別のフォルダ選択の案内を含む"
            )

            # レイアウトに追加
            self.grid_layout.addWidget(self._empty_placeholder, 0, 0, 1, self.columns)

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "empty_placeholder_error",
                f"空状態プレースホルダー表示エラー: {str(e)}",
                level="WARNING",
            )

    def _add_thumbnail_item(self, image_path: Path):
        """
        新しいサムネイルアイテムを追加する

        Args:
            image_path: 追加する画像ファイルのパス
        """
        try:
            if image_path in self.thumbnail_items:
                # 既に存在する場合はスキップ
                return

            # サムネイルアイテムを作成
            thumbnail_item = ThumbnailItem(image_path, self.thumbnail_size)

            # シグナルを接続
            thumbnail_item.clicked.connect(self._on_thumbnail_clicked)
            thumbnail_item.context_menu_requested.connect(
                self._on_context_menu_requested
            )
            thumbnail_item.exif_info_requested.connect(self._on_exif_info_requested)

            # 辞書に追加
            self.thumbnail_items[image_path] = thumbnail_item

            # サムネイル読み込みを開始
            self._load_single_thumbnail(image_path)

            # EXIFデータ読み込みを開始
            self._load_single_exif(image_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_item_added",
                f"サムネイルアイテム追加: {image_path.name}",
                level="DEBUG",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "add_thumbnail_item",
                    "image_path": str(image_path),
                    "user_action": "サムネイルアイテム追加",
                },
                AIComponent.CURSOR,
            )

    def _remove_thumbnail_item(self, image_path: Path):
        """
        サムネイルアイテムを削除する

        Args:
            image_path: 削除する画像ファイルのパス
        """
        try:
            if image_path not in self.thumbnail_items:
                # 存在しない場合はスキップ
                return

            thumbnail_item = self.thumbnail_items[image_path]

            # レイアウトから削除
            self.grid_layout.removeWidget(thumbnail_item)

            # ウィジェットを削除
            thumbnail_item.deleteLater()

            # 辞書から削除
            del self.thumbnail_items[image_path]

            # EXIFキャッシュからも削除
            if image_path in self.exif_cache:
                del self.exif_cache[image_path]

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_item_removed",
                f"サムネイルアイテム削除: {image_path.name}",
                level="DEBUG",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "remove_thumbnail_item",
                    "image_path": str(image_path),
                    "user_action": "サムネイルアイテム削除",
                },
                AIComponent.CURSOR,
            )

    def _create_thumbnail_items(self):
        """Create thumbnail items for all images"""
        try:
            row = 0
            col = 0

            for image_path in self.image_list:
                # Create thumbnail item
                thumbnail_item = ThumbnailItem(image_path, self.thumbnail_size)

                # Connect signals
                thumbnail_item.clicked.connect(self._on_thumbnail_clicked)
                thumbnail_item.context_menu_requested.connect(
                    self._on_context_menu_requested
                )
                thumbnail_item.exif_info_requested.connect(self._on_exif_info_requested)

                # Add to layout
                self.grid_layout.addWidget(thumbnail_item, row, col)

                # Store reference
                self.thumbnail_items[image_path] = thumbnail_item

                # Update grid position
                col += 1
                if col >= self.columns:
                    col = 0
                    row += 1

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_thumbnail_items"},
                AIComponent.CURSOR,
            )

    def _load_thumbnails_async(self):
        """Load thumbnails asynchronously"""
        try:
            for image_path in self.image_list:
                # Submit thumbnail loading task
                future = self.thumbnail_executor.submit(
                    self._load_single_thumbnail, image_path
                )

                # Submit EXIF loading task
                exif_future = self.exif_executor.submit(
                    self._load_single_exif, image_path
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "load_thumbnails_async"},
                AIComponent.KIRO,
            )

    def _load_single_thumbnail(self, image_path: Path):
        """Load a single thumbnail"""
        try:
            # Emit request signal for caching system
            self.thumbnail_requested.emit(image_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "load_single_thumbnail", "image": str(image_path)},
                AIComponent.KIRO,
            )

    def _load_single_exif(self, image_path: Path):
        """Load EXIF data for a single image"""
        try:
            # Check cache first
            if image_path in self.exif_cache:
                exif_data = self.exif_cache[image_path]
                self._update_thumbnail_exif(image_path, exif_data)
                return

            # Request EXIF data
            self.exif_display_requested.emit(image_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "load_single_exif", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def set_thumbnail(self, image_path: Path, pixmap: QPixmap):
        """Set thumbnail for specific image"""
        try:
            if image_path in self.thumbnail_items:
                thumbnail_item = self.thumbnail_items[image_path]
                thumbnail_item.set_thumbnail(pixmap)

                with QMutexLocker(self.load_mutex):
                    self.loaded_count += 1

                self._update_performance_metrics()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_thumbnail", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def set_exif_data(self, image_path: Path, exif_data: Dict[str, Any]):
        """Set EXIF data for specific image"""
        try:
            # Cache EXIF data
            self.exif_cache[image_path] = exif_data

            # Update thumbnail item
            self._update_thumbnail_exif(image_path, exif_data)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_exif_data", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _update_thumbnail_exif(self, image_path: Path, exif_data: Dict[str, Any]):
        """Update thumbnail with EXIF information"""
        try:
            if image_path in self.thumbnail_items:
                thumbnail_item = self.thumbnail_items[image_path]
                thumbnail_item.set_exif_info(exif_data)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_thumbnail_exif", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _on_thumbnail_clicked(self, image_path: Path):
        """Handle thumbnail click"""
        try:
            self.image_selected.emit(image_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_clicked",
                f"Thumbnail clicked: {image_path}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_clicked", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_context_menu_requested(self, image_path: Path, position):
        """Handle context menu request"""
        try:
            menu = QMenu(self)

            # Add menu actions
            view_action = menu.addAction("View Image")
            view_action.triggered.connect(lambda: self.image_selected.emit(image_path))

            exif_action = menu.addAction("Show EXIF Data")
            exif_action.triggered.connect(
                lambda: self._on_exif_info_requested(image_path)
            )

            menu.addSeparator()

            refresh_action = menu.addAction("Refresh Thumbnail")
            refresh_action.triggered.connect(
                lambda: self._refresh_thumbnail(image_path)
            )

            # Show menu
            menu.exec(position.toPoint())

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "context_menu_requested", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_exif_info_requested(self, image_path: Path):
        """Handle EXIF info request"""
        try:
            self.exif_display_requested.emit(image_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "exif_info_requested", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _refresh_thumbnail(self, image_path: Path):
        """Refresh specific thumbnail"""
        try:
            if image_path in self.thumbnail_items:
                thumbnail_item = self.thumbnail_items[image_path]
                thumbnail_item._show_placeholder()

                # Request new thumbnail
                self.thumbnail_requested.emit(image_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "refresh_thumbnail", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_size_changed(self, size: int):
        """Handle thumbnail size change"""
        try:
            self.thumbnail_size = size

            # Update all thumbnail items
            for thumbnail_item in self.thumbnail_items.values():
                thumbnail_item.thumbnail_size = size
                thumbnail_item.setFixedSize(size + 20, size + 40)
                thumbnail_item._show_placeholder()

            # Update grid layout
            self._update_grid_layout()

            # Request new thumbnails
            for image_path in self.image_list:
                self.thumbnail_requested.emit(image_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_size_changed",
                f"Thumbnail size changed to: {size}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "size_changed", "size": size},
                AIComponent.CURSOR,
            )

    def _update_grid_layout(self):
        """Update grid layout based on current size"""
        try:
            # Calculate optimal columns based on widget width and thumbnail size
            widget_width = self.width()
            if widget_width > 0:
                item_width = self.thumbnail_size + 20 + self.spacing
                new_columns = max(1, widget_width // item_width)

                if new_columns != self.columns:
                    self.columns = new_columns
                    self._reorganize_grid()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_grid_layout"},
                AIComponent.CURSOR,
            )

    def _reorganize_grid(self):
        """Reorganize grid with new column count"""
        try:
            # Remove all items from layout
            for i in reversed(range(self.grid_layout.count())):
                item = self.grid_layout.itemAt(i)
                if item:
                    self.grid_layout.removeItem(item)

            # Re-add items with new layout
            row = 0
            col = 0

            for image_path in self.image_list:
                if image_path in self.thumbnail_items:
                    thumbnail_item = self.thumbnail_items[image_path]
                    self.grid_layout.addWidget(thumbnail_item, row, col)

                    col += 1
                    if col >= self.columns:
                        col = 0
                        row += 1

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "reorganize_grid"},
                AIComponent.CURSOR,
            )

    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            with QMutexLocker(self.load_mutex):
                if self.total_count > 0 and self.load_start_time:
                    elapsed_time = time.time() - self.load_start_time
                    progress = self.loaded_count / self.total_count

                    if progress > 0:
                        estimated_total_time = elapsed_time / progress
                        self.performance_metrics["avg_load_time"] = estimated_total_time

                    # Update performance label
                    self.performance_label.setText(
                        f"Loaded: {self.loaded_count}/{self.total_count} "
                        f"({progress*100:.1f}%)"
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "update_performance_metrics"},
                AIComponent.KIRO,
            )

    def _monitor_performance(self):
        """Monitor performance and emit warnings if needed"""
        try:
            # Check memory usage
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            self.performance_metrics["memory_usage"] = memory_mb

            # Check for performance issues
            if memory_mb > 500:  # 500MB threshold
                self.performance_warning.emit(f"High memory usage: {memory_mb:.1f}MB")

            # Check loading performance
            if (
                self.total_count > 0
                and self.loaded_count < self.total_count
                and self.performance_metrics["avg_load_time"] > 30
            ):  # 30 seconds threshold

                self.performance_warning.emit("Slow thumbnail loading detected")

        except Exception as e:
            # Don't log performance monitoring errors to avoid spam
            pass

    def clear_thumbnails(self):
        """Clear all thumbnails"""
        try:
            # Clear layout
            for i in reversed(range(self.grid_layout.count())):
                item = self.grid_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

            # Clear data
            self.thumbnail_items.clear()
            self.exif_cache.clear()

            with QMutexLocker(self.load_mutex):
                self.loaded_count = 0
                self.total_count = 0

            self.performance_label.setText("Ready")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "clear_thumbnails"},
                AIComponent.CURSOR,
            )

    def refresh_theme(self):
        """Refresh theme for all thumbnails"""
        try:
            # Update thumbnail item styles based on current theme
            current_theme = self.state_manager.get_state().current_theme

            for thumbnail_item in self.thumbnail_items.values():
                # Apply theme-specific styling
                if "dark" in current_theme:
                    thumbnail_item.setStyleSheet(
                        """
                        QLabel {
                            border: 2px solid transparent;
                            border-radius: 4px;
                            background-color: #3a3a3a;
                            color: #ffffff;
                            padding: 4px;
                        }
                        QLabel:hover {
                            border-color: #007acc;
                            background-color: #4a4a4a;
                        }
                    """
                    )
                else:
                    thumbnail_item.setStyleSheet(
                        """
                        QLabel {
                            border: 2px solid transparent;
                            border-radius: 4px;
                            background-color: #f8f9fa;
                            color: #000000;
                            padding: 4px;
                        }
                        QLabel:hover {
                            border-color: #007acc;
                            background-color: #e3f2fd;
                        }
                    """
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "refresh_theme"},
                AIComponent.CURSOR,
            )

    def set_thumbnail_size(self, size: int):
        """Set thumbnail size programmatically"""
        self._on_size_changed(size)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()

    def update_image_list(self, image_list: List[Path]):
        """
        Update the image list with new images

        Args:
            image_list: List of image paths to display
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "update_image_list",
                f"Updating image list with {len(image_list)} images",
            )

            # Clear existing thumbnails safely
            self.clear_thumbnails_safely()

            # Update image list
            self.image_list = image_list
            self.total_count = len(image_list)
            self.loaded_count = 0
            self.load_start_time = time.time()

            if not image_list:
                # Show empty state if no images
                self.performance_label.setText("画像ファイルがありません")
                return

            # Create new thumbnail items
            self._create_thumbnail_items()

            # Start loading thumbnails asynchronously
            self._load_thumbnails_async()

            # Update performance label
            self.performance_label.setText(f"読み込み中... 0/{len(image_list)}")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "update_image_list_complete",
                f"Image list updated successfully with {len(image_list)} images",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_image_list", "count": len(image_list)},
                AIComponent.CURSOR,
            )

    def clear_thumbnails_safely(self):
        """
        Safely clear all thumbnails with proper cleanup
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "clear_thumbnails_safely",
                "Safely clearing thumbnails",
            )

            # Stop any ongoing loading operations
            with QMutexLocker(self.load_mutex):
                self.loaded_count = 0
                self.total_count = 0
                self.load_start_time = None

            # Clear thumbnail items from layout
            if self.grid_layout:
                for i in reversed(range(self.grid_layout.count())):
                    item = self.grid_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        self.grid_layout.removeWidget(widget)
                        widget.setParent(None)
                        widget.deleteLater()

            # Clear data structures
            self.thumbnail_items.clear()
            self.exif_cache.clear()

            # Reset performance label
            if hasattr(self, "performance_label"):
                self.performance_label.setText("準備完了")

            # Force garbage collection to free memory
            import gc

            gc.collect()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "clear_thumbnails_safely_complete",
                "Thumbnails cleared safely",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "clear_thumbnails_safely"},
                AIComponent.CURSOR,
            )

    def show_loading_state(self, message: str):
        """
        Show loading state with Japanese message

        Args:
            message: Loading message to display
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "show_loading_state",
                f"Showing loading state: {message}",
            )

            # Clear existing thumbnails
            self.clear_thumbnails_safely()

            # Create loading indicator widget
            loading_widget = QWidget()
            loading_layout = QVBoxLayout(loading_widget)
            loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Loading icon/animation placeholder
            loading_icon = QLabel("🔄")
            loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 48px;
                    color: #007acc;
                    margin: 20px;
                }
            """
            )
            loading_layout.addWidget(loading_icon)

            # Loading message
            loading_label = QLabel(message)
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet(
                """
                QLabel {
                    font-size: 16px;
                    color: #333333;
                    margin: 10px;
                    padding: 10px;
                }
            """
            )
            loading_layout.addWidget(loading_label)

            # Add to grid layout
            self.grid_layout.addWidget(loading_widget, 0, 0, 1, self.columns)

            # Update performance label
            if hasattr(self, "performance_label"):
                self.performance_label.setText(message)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "show_loading_state_complete",
                f"Loading state displayed: {message}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_loading_state", "message": message},
                AIComponent.CURSOR,
            )

    def show_error_state(self, error_message: str):
        """
        Show error state with Japanese error message

        Args:
            error_message: Error message to display
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "show_error_state",
                f"Showing error state: {error_message}",
            )

            # Clear existing thumbnails
            self.clear_thumbnails_safely()

            # Create error indicator widget
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Error icon
            error_icon = QLabel("⚠️")
            error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 48px;
                    color: #dc3545;
                    margin: 20px;
                }
            """
            )
            error_layout.addWidget(error_icon)

            # Error message
            error_label = QLabel(error_message)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setWordWrap(True)
            error_label.setStyleSheet(
                """
                QLabel {
                    font-size: 14px;
                    color: #dc3545;
                    margin: 10px;
                    padding: 15px;
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 4px;
                    max-width: 400px;
                }
            """
            )
            error_layout.addWidget(error_label)

            # Retry suggestion
            retry_label = QLabel(
                "フォルダを再選択するか、アプリケーションを再起動してください。"
            )
            retry_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            retry_label.setWordWrap(True)
            retry_label.setStyleSheet(
                """
                QLabel {
                    font-size: 12px;
                    color: #6c757d;
                    margin: 5px;
                    padding: 10px;
                }
            """
            )
            error_layout.addWidget(retry_label)

            # Add to grid layout
            self.grid_layout.addWidget(error_widget, 0, 0, 1, self.columns)

            # Update performance label
            if hasattr(self, "performance_label"):
                self.performance_label.setText(f"エラー: {error_message}")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "show_error_state_complete",
                f"Error state displayed: {error_message}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_error_state", "error_message": error_message},
                AIComponent.CURSOR,
            )

    def show_empty_state(self):
        """
        Show empty state when no images are found
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "show_empty_state", "Showing empty state"
            )

            # Clear existing thumbnails
            self.clear_thumbnails_safely()

            # Create empty state widget
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Empty state icon
            empty_icon = QLabel("📁")
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 64px;
                    color: #6c757d;
                    margin: 30px;
                }
            """
            )
            empty_layout.addWidget(empty_icon)

            # Empty state message
            empty_title = QLabel("画像ファイルが見つかりません")
            empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_title.setStyleSheet(
                """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #495057;
                    margin: 10px;
                }
            """
            )
            empty_layout.addWidget(empty_title)

            # Helpful message
            empty_message = QLabel(
                "このフォルダには対応する画像ファイル（JPG、PNG、GIF、BMP、TIFF、WEBP）がありません。\n別のフォルダを選択してください。"
            )
            empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_message.setWordWrap(True)
            empty_message.setStyleSheet(
                """
                QLabel {
                    font-size: 14px;
                    color: #6c757d;
                    margin: 10px;
                    padding: 15px;
                    max-width: 500px;
                    line-height: 1.4;
                }
            """
            )
            empty_layout.addWidget(empty_message)

            # Supported formats info
            formats_label = QLabel(
                "対応形式: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp"
            )
            formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            formats_label.setStyleSheet(
                """
                QLabel {
                    font-size: 12px;
                    color: #868e96;
                    margin: 5px;
                    padding: 5px;
                    font-style: italic;
                }
            """
            )
            empty_layout.addWidget(formats_label)

            # Add to grid layout
            self.grid_layout.addWidget(empty_widget, 0, 0, 1, self.columns)

            # Update performance label
            if hasattr(self, "performance_label"):
                self.performance_label.setText("画像ファイルがありません")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "show_empty_state_complete", "Empty state displayed"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_empty_state"},
                AIComponent.CURSOR,
            )

    def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop performance monitoring
            if self.performance_timer:
                self.performance_timer.stop()

            # Shutdown thread pools
            self.thumbnail_executor.shutdown(wait=False)
            self.exif_executor.shutdown(wait=False)

            # Clear data safely
            self.clear_thumbnails_safely()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_grid_cleanup",
                "Thumbnail grid cleaned up",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "cleanup"}, AIComponent.CURSOR
            )

    """
    Optimized thumbnail grid combining CursorBLD speed with Kiro optimization

    Features:
    - CursorBLD's Qt native high-speed thumbnail display
    - Kiro's memory management and caching
    - Asynchronous loading with progress indication
    - Dynamic sizing and responsive layout
    """

    image_selected = pyqtSignal(Path)
    loading_started = pyqtSignal(int)  # total count
    loading_progress = pyqtSignal(int, int)  # current, total
    loading_finished = pyqtSignal()

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
    ):
        """
        Initialize the optimized thumbnail grid

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

        # Thumbnail settings
        self.thumbnail_size = self.config_manager.get_setting("ui.thumbnail_size", 150)
        self.columns = 4
        self.spacing = 10

        # Data
        self.image_paths: List[Path] = []
        self.thumbnail_items: Dict[Path, ThumbnailItem] = {}

        # UI components
        self.scroll_area: Optional[QScrollArea] = None
        self.grid_widget: Optional[QWidget] = None
        self.grid_layout: Optional[QGridLayout] = None
        self.controls_widget: Optional[QWidget] = None

        # Thumbnail loader
        self.thumbnail_loader = ThumbnailLoader(self.logger_system)

        # Performance monitoring
        self.performance_timer = QTimer()
        self.last_performance_check = time.time()

        # Initialize UI
        self._initialize_ui()
        self._connect_signals()
        self._setup_monitoring()

        self.logger_system.log_ai_operation(
            AIComponent.CURSOR,
            "thumbnail_grid_init",
            "Optimized thumbnail grid initialized",
        )

    def _initialize_ui(self):
        """Initialize the user interface"""

        try:
            # Main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(5)

            # Create controls
            self._create_controls()
            main_layout.addWidget(self.controls_widget)

            # Create scroll area
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )

            # Create grid widget
            self.grid_widget = QWidget()
            self.grid_layout = QGridLayout(self.grid_widget)
            self.grid_layout.setSpacing(self.spacing)
            self.grid_layout.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )

            self.scroll_area.setWidget(self.grid_widget)
            main_layout.addWidget(self.scroll_area, 1)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_grid_ui_init"},
                AIComponent.CURSOR,
            )

    def _create_controls(self):
        """Create thumbnail controls (CursorBLD style with Kiro enhancements)"""

        self.controls_widget = QFrame()
        self.controls_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        self.controls_widget.setMaximumHeight(60)

        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(10, 5, 10, 5)

        # Size label
        size_label = QLabel("Thumbnail Size:")
        controls_layout.addWidget(size_label)

        # Size slider (CursorBLD feature)
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(50)
        self.size_slider.setMaximum(300)
        self.size_slider.setValue(self.thumbnail_size)
        self.size_slider.setMaximumWidth(150)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        controls_layout.addWidget(self.size_slider)

        # Size spinbox
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setMinimum(50)
        self.size_spinbox.setMaximum(300)
        self.size_spinbox.setValue(self.thumbnail_size)
        self.size_spinbox.setSuffix(" px")
        self.size_spinbox.valueChanged.connect(self._on_size_changed)
        controls_layout.addWidget(self.size_spinbox)

        controls_layout.addStretch()

        # Cache info (Kiro enhancement)
        self.cache_label = QLabel("Cache: 0 items")
        self.cache_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        controls_layout.addWidget(self.cache_label)

        # Clear cache button (Kiro enhancement)
        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.setMaximumWidth(100)
        clear_cache_btn.clicked.connect(self._clear_cache)
        controls_layout.addWidget(clear_cache_btn)

    def _connect_signals(self):
        """Connect internal signals"""

        # Connect thumbnail loader signals
        self.thumbnail_loader.thumbnail_loaded.connect(self._on_thumbnail_loaded)
        self.thumbnail_loader.loading_progress.connect(self._on_loading_progress)

        # Connect state manager changes
        self.state_manager.add_change_listener(
            "thumbnail_size", self._on_thumbnail_size_changed
        )

    def _setup_monitoring(self):
        """Setup performance monitoring (Kiro enhancement)"""

        self.performance_timer.timeout.connect(self._update_performance_metrics)
        self.performance_timer.start(10000)  # Update every 10 seconds

    # Public methods

    def load_images(self, image_paths: List[Path]):
        """Load images and display thumbnails"""

        try:
            self.image_paths = image_paths

            # Clear existing thumbnails
            self._clear_thumbnails()

            if not image_paths:
                return

            # Emit loading started
            self.loading_started.emit(len(image_paths))

            # Create thumbnail items
            self._create_thumbnail_items()

            # Start loading thumbnails
            self.thumbnail_loader.load_thumbnails(image_paths, self.thumbnail_size)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_load_start",
                f"Loading {len(image_paths)} thumbnails",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_images", "count": len(image_paths)},
                AIComponent.CURSOR,
            )

    def _create_thumbnail_items(self):
        """Create thumbnail items in grid layout"""

        try:
            # Calculate columns based on widget width
            widget_width = self.scroll_area.viewport().width()
            item_width = self.thumbnail_size + 20 + self.spacing
            self.columns = max(1, widget_width // item_width)

            # Create thumbnail items
            for i, image_path in enumerate(self.image_paths):
                row = i // self.columns
                col = i % self.columns

                # Create thumbnail item
                thumbnail_item = ThumbnailItem(image_path, self.thumbnail_size)
                thumbnail_item.clicked.connect(self._on_thumbnail_clicked)

                # Add to layout
                self.grid_layout.addWidget(thumbnail_item, row, col)

                # Store reference
                self.thumbnail_items[image_path] = thumbnail_item

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_thumbnail_items"},
                AIComponent.CURSOR,
            )

    def _clear_thumbnails(self):
        """Clear all thumbnail items"""

        try:
            # Remove all items from layout
            while self.grid_layout.count():
                child = self.grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Clear references
            self.thumbnail_items.clear()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "clear_thumbnails"},
                AIComponent.CURSOR,
            )

    # Event handlers

    def _on_thumbnail_clicked(self, image_path: Path):
        """Handle thumbnail click"""

        try:
            # Update state
            self.state_manager.update_state(selected_image=image_path)

            # Emit signal
            self.image_selected.emit(image_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_click",
                f"Thumbnail clicked: {image_path.name}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_click", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_thumbnail_loaded(self, image_path: Path, pixmap: QPixmap):
        """Handle thumbnail loaded"""

        try:
            if image_path in self.thumbnail_items:
                thumbnail_item = self.thumbnail_items[image_path]
                thumbnail_item.set_thumbnail(pixmap)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_loaded", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_loading_progress(self, current: int, total: int):
        """Handle loading progress"""

        self.loading_progress.emit(current, total)

        if current >= total:
            self.loading_finished.emit()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_load_complete",
                f"Loaded {total} thumbnails",
            )

    def _on_size_changed(self, size: int):
        """Handle thumbnail size change"""

        try:
            # Update size from either slider or spinbox
            if self.sender() == self.size_slider:
                self.size_spinbox.setValue(size)
            elif self.sender() == self.size_spinbox:
                self.size_slider.setValue(size)

            self.thumbnail_size = size

            # Update configuration
            self.config_manager.set_setting("ui.thumbnail_size", size)

            # Update state
            self.state_manager.update_state(thumbnail_size=size)

            # Reload thumbnails with new size
            if self.image_paths:
                self.load_images(self.image_paths)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "size_change", "size": size},
                AIComponent.CURSOR,
            )

    def _on_thumbnail_size_changed(self, key: str, old_value: Any, new_value: Any):
        """Handle thumbnail size change from state manager"""

        if new_value != self.thumbnail_size:
            self.thumbnail_size = new_value
            self.size_slider.setValue(new_value)
            self.size_spinbox.setValue(new_value)

    def _clear_cache(self):
        """Clear thumbnail cache (Kiro enhancement)"""

        try:
            self.thumbnail_loader.clear_cache()
            self._update_cache_info()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO, "cache_clear", "Thumbnail cache cleared"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_clear"},
                AIComponent.KIRO,
            )

    def _update_cache_info(self):
        """Update cache information display (Kiro enhancement)"""

        try:
            cache_stats = self.thumbnail_loader.get_cache_stats()

            cache_size = cache_stats.get("cache_size", 0)
            hit_rate = cache_stats.get("hit_rate", 0)

            self.cache_label.setText(
                f"Cache: {cache_size} items ({hit_rate:.1%} hit rate)"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_info_update"},
                AIComponent.KIRO,
            )

    def _update_performance_metrics(self):
        """Update performance metrics (Kiro enhancement)"""

        try:
            # Update cache info
            self._update_cache_info()

            # Log performance metrics
            cache_stats = self.thumbnail_loader.get_cache_stats()

            self.logger_system.log_performance(
                AIComponent.CURSOR,
                "thumbnail_grid_performance",
                {
                    "thumbnail_count": len(self.thumbnail_items),
                    "cache_size": cache_stats.get("cache_size", 0),
                    "cache_hit_rate": cache_stats.get("hit_rate", 0),
                    "average_load_time": cache_stats.get("average_load_time", 0),
                },
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "performance_metrics_update"},
                AIComponent.KIRO,
            )

    # Context menu (CursorBLD feature)

    def contextMenuEvent(self, event):
        """Show context menu"""

        try:
            menu = QMenu(self)

            # Size options
            size_menu = menu.addMenu("Thumbnail Size")

            sizes = [75, 100, 150, 200, 250, 300]
            for size in sizes:
                action = size_menu.addAction(f"{size}px")
                action.triggered.connect(
                    lambda checked, s=size: self._on_size_changed(s)
                )
                action.setCheckable(True)
                action.setChecked(size == self.thumbnail_size)

            menu.addSeparator()

            # Cache options (Kiro enhancement)
            cache_menu = menu.addMenu("Cache")

            cache_info_action = cache_menu.addAction("Cache Info")
            cache_info_action.triggered.connect(self._show_cache_info)

            clear_cache_action = cache_menu.addAction("Clear Cache")
            clear_cache_action.triggered.connect(self._clear_cache)

            menu.exec(event.globalPos())

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "context_menu"},
                AIComponent.CURSOR,
            )

    def _show_cache_info(self):
        """Show cache information dialog"""

        try:
            from PyQt6.QtWidgets import QMessageBox

            cache_stats = self.thumbnail_loader.get_cache_stats()

            info_text = f"""
            Cache Statistics:

            Cache Size: {cache_stats.get('cache_size', 0)} items
            Cache Hits: {cache_stats.get('cache_hits', 0)}
            Cache Misses: {cache_stats.get('cache_misses', 0)}
            Hit Rate: {cache_stats.get('hit_rate', 0):.1%}
            Average Load Time: {cache_stats.get('average_load_time', 0):.3f}s

            Recent Load Times: {cache_stats.get('recent_load_times', [])}
            """

            QMessageBox.information(self, "Cache Information", info_text)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "cache_info_dialog"},
                AIComponent.CURSOR,
            )

    # Resize handling

    def resizeEvent(self, event):
        """Handle widget resize"""

        super().resizeEvent(event)

        # Recalculate columns and reload if needed
        if self.image_paths:
            widget_width = self.scroll_area.viewport().width()
            item_width = self.thumbnail_size + 20 + self.spacing
            new_columns = max(1, widget_width // item_width)

            if new_columns != self.columns:
                self.columns = new_columns
                # Recreate layout with new column count
                self._create_thumbnail_items()
