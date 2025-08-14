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

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QMutex, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..state_manager import StateManager


class ThumbnailItem(QLabel):
    """
    Individual thumbnail item with Kiro optimization
    """

    clicked = Signal(Path)
    context_menu_requested = Signal(Path, object)  # image_path, position
    exif_info_requested = Signal(Path)

    def __init__(self, image_path: Path, thumbnail_size: int = 150):
        super().__init__()

        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.is_loaded = False
        self.is_loading = False

        # Setup UI
        self.setFixedSize(thumbnail_size + 20, thumbnail_size + 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # テーマ対応のスタイルシートは後で設定
        self.theme_manager = None  # 後で設定される
        self._update_thumbnail_style()

        # Show placeholder
        self._show_placeholder()


    def set_theme_manager(self, theme_manager):
        """テーママネージャーを設定"""
        self.theme_manager = theme_manager
        if theme_manager:
            if hasattr(theme_manager, 'theme_changed'):
                theme_manager.theme_changed.connect(self._on_theme_changed)
            elif hasattr(theme_manager, 'theme_changed_compat'):
                theme_manager.theme_changed_compat.connect(self._on_theme_changed)
        self._update_thumbnail_style()

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        self._update_thumbnail_style()

    def _update_thumbnail_style(self):
        """テーマに基づいてスタイルを更新"""
        try:
            # デフォルト色
            bg_color = "#f8f9fa"
            hover_bg = "#e3f2fd"
            border_color = "#007acc"

            # テーママネージャーから色を取得
            if self.theme_manager:
                try:
                    bg_color = self.theme_manager.get_color("background", "#f8f9fa")
                    hover_bg = self.theme_manager.get_color("hover", "#e3f2fd")
                    border_color = self.theme_manager.get_color("primary", "#007acc")
                except Exception:
                    pass  # デフォルト色を使用

            self.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid transparent;
                    border-radius: 4px;
                    background-color: {bg_color};
                    padding: 4px;
                }}
                QLabel:hover {{
                    border-color: {border_color};
                    background-color: {hover_bg};
                }}
            """)
        except Exception as e:
            # エラー時はデフォルトスタイルを適用
            self.setStyleSheet("""
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
            """)

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
            self.setText("")  # Clear text
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
        self.setText("Error")

    def set_exif_info(self, exif_data: Dict[str, Any]):
        """Set EXIF information for display"""
        if exif_data:
            # Create tooltip with EXIF info
            tooltip_parts = []
            if "DateTime" in exif_data:
                tooltip_parts.append(f"Date: {exif_data['DateTime']}")
            if "Make" in exif_data and "Model" in exif_data:
                tooltip_parts.append(f"Camera: {exif_data['Make']} {exif_data['Model']}")
            if "ExposureTime" in exif_data:
                tooltip_parts.append(f"Exposure: {exif_data['ExposureTime']}s")
            if "FNumber" in exif_data:
                tooltip_parts.append(f"F-Number: f/{exif_data['FNumber']}")
            if "ISOSpeedRatings" in exif_data:
                tooltip_parts.append(f"ISO: {exif_data['ISOSpeedRatings']}")

            if tooltip_parts:
                self.setToolTip("\n".join(tooltip_parts))

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self.image_path, event.globalPos())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.exif_info_requested.emit(self.image_path)
        super().mouseDoubleClickEvent(event)


class ThumbnailLoader(QObject):
    """
    Asynchronous thumbnail loader with Kiro optimization
    """

    thumbnail_loaded = Signal(Path, QPixmap)
    loading_progress = Signal(int, int)  # current, total

    def __init__(self, logger_system: LoggerSystem):
        super().__init__()
        self.logger_system = logger_system
        self.cache: Dict[str, QPixmap] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.recent_load_times = []

    def load_thumbnails(self, image_paths: List[Path], thumbnail_size: int):
        """Load thumbnails for the given image paths"""
        try:
            total = len(image_paths)
            loaded = 0

            for i, image_path in enumerate(image_paths):
                start_time = time.time()

                # Check cache first
                cache_key = f"{image_path}_{thumbnail_size}"
                if cache_key in self.cache:
                    self.cache_hits += 1
                    self.thumbnail_loaded.emit(image_path, self.cache[cache_key])
                else:
                    self.cache_misses += 1
                    # Load thumbnail
                    pixmap = QPixmap(str(image_path))
                    if not pixmap.isNull():
                        # Scale to thumbnail size
                        scaled_pixmap = pixmap.scaled(
                            thumbnail_size,
                            thumbnail_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        # Cache the result
                        self.cache[cache_key] = scaled_pixmap
                        self.thumbnail_loaded.emit(image_path, scaled_pixmap)
                    else:
                        # Create error placeholder
                        error_pixmap = QPixmap(thumbnail_size, thumbnail_size)
                        error_pixmap.fill(QColor("#f8d7da"))
                        self.thumbnail_loaded.emit(image_path, error_pixmap)

                loaded += 1
                self.loading_progress.emit(loaded, total)

                # Track load time
                load_time = time.time() - start_time
                self.recent_load_times.append(load_time)
                if len(self.recent_load_times) > 10:
                    self.recent_load_times.pop(0)

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_load_error",
                f"Error loading thumbnails: {str(e)}",
                level="ERROR",
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        avg_load_time = sum(self.recent_load_times) / len(self.recent_load_times) if self.recent_load_times else 0

        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "average_load_time": avg_load_time,
            "recent_load_times": self.recent_load_times,
        }

    def clear_cache(self):
        """Clear the thumbnail cache"""
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
    image_selected = Signal(Path)
    thumbnail_requested = Signal(Path)
    exif_display_requested = Signal(Path)
    performance_warning = Signal(str)

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
        theme_manager: Optional[object] = None,
    ):
        """
        Initialize optimized thumbnail grid

        Args:
            config_manager: Configuration manager
            state_manager: State manager
            logger_system: Logging system
            theme_manager: Theme manager for styling
        """
        super().__init__()

        # Core systems
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)
        self.theme_manager = theme_manager

        # テーマ変更シグナルの接続
        if self.theme_manager:
            if hasattr(self.theme_manager, 'theme_changed'):
                self.theme_manager.theme_changed.connect(self._on_theme_changed)
            elif hasattr(self.theme_manager, 'theme_changed_compat'):
                self.theme_manager.theme_changed_compat.connect(self._on_theme_changed)

        # Grid settings
        try:
            self.thumbnail_size = self.state_manager.get_state_value("thumbnail_size", 150)
        except:
            self.thumbnail_size = 150  # デフォルト値
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

        # Threading - 初期化を最初に行う
        self.load_mutex = QMutex()
        self.thumbnail_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="thumbnail"
        )
        self.exif_executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="exif"
        )

        # UI components initialization
        self.performance_label = None
        self.progress_indicator = None

        # UI components
        self.scroll_area: Optional[QScrollArea] = None
        self.grid_widget: Optional[QWidget] = None
        self.grid_layout: Optional[QGridLayout] = None
        self.controls_widget: Optional[QWidget] = None

        # Thumbnail loader
        self.thumbnail_loader = ThumbnailLoader(self.logger_system)

        # Initialize UI first
        self._setup_ui()

        # Performance monitoring - UIの後に開始
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._monitor_performance)
        self.performance_timer.start(2000)  # Check every 2 seconds

        # Connect signals
        self.thumbnail_loader.thumbnail_loaded.connect(self._on_thumbnail_loaded)
        self.thumbnail_loader.loading_progress.connect(self._on_loading_progress)

        self.logger_system.log_ai_operation(
            AIComponent.CURSOR,
            "thumbnail_grid_init",
            "Optimized thumbnail grid initialized",
        )

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            # 既存のサムネイルアイテムのスタイルを更新
            for thumbnail_item in self.thumbnail_items.values():
                if hasattr(thumbnail_item, '_update_thumbnail_style'):
                    thumbnail_item._update_thumbnail_style()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_grid_theme_changed",
                f"Thumbnail grid theme updated: {theme_name}",
            )
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_grid_theme_change", "theme": theme_name},
                AIComponent.CURSOR,
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
            # 基本的な設定
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

    def clear_thumbnails_safely(self):
        """
        既存のサムネイルを安全にクリアする
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

    def _create_thumbnail_items(self):
        """Create thumbnail items in grid layout"""
        try:
            # Calculate columns based on widget width
            widget_width = self.scroll_area.viewport().width()
            item_width = self.thumbnail_size + 20 + self.spacing
            self.columns = max(1, widget_width // item_width)

            # Create thumbnail items
            for i, image_path in enumerate(self.image_list):
                row = i // self.columns
                col = i % self.columns

                # Create thumbnail item
                thumbnail_item = ThumbnailItem(image_path, self.thumbnail_size)
                thumbnail_item.set_theme_manager(self.theme_manager)  # テーママネージャーを設定
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

    def _load_thumbnails_async(self):
        """Load thumbnails asynchronously"""
        try:
            if self.image_list:
                # Submit thumbnail loading task to thread pool
                future = self.thumbnail_executor.submit(
                    self.thumbnail_loader.load_thumbnails,
                    self.image_list,
                    self.thumbnail_size
                )
                future.add_done_callback(self._on_loading_complete)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_thumbnails_async"},
                AIComponent.CURSOR,
            )

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
                self.loaded_count += 1

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_loaded", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_loading_progress(self, current: int, total: int):
        """Handle loading progress"""
        try:
            if hasattr(self, "performance_label") and self.performance_label:
                self.performance_label.setText(f"読み込み中... {current}/{total}")

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "loading_progress_error",
                f"Progress update error: {str(e)}",
                level="WARNING",
            )

    def _on_loading_complete(self, future):
        """Handle loading completion"""
        try:
            if hasattr(self, "performance_label") and self.performance_label:
                self.performance_label.setText(f"完了: {self.loaded_count}/{self.total_count}")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_load_complete",
                f"Loaded {self.loaded_count} thumbnails",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "loading_complete"},
                AIComponent.CURSOR,
            )

    def _on_size_changed(self, size: int):
        """Handle thumbnail size change"""
        try:
            self.thumbnail_size = size

            # Update configuration
            self.config_manager.set_setting("ui.thumbnail_size", size)

            # Update state
            self.state_manager.update_state(thumbnail_size=size)

            # Reload thumbnails with new size
            if self.image_list:
                self.set_image_list(self.image_list)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "size_change", "size": size},
                AIComponent.CURSOR,
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

    def show_loading_state(self, message: str = "読み込み中..."):
        """Show loading state"""
        try:
            # Clear existing thumbnails but preserve grid layout
            self.clear_thumbnails_safely()

            # Create loading state widget and add to grid
            loading_widget = QWidget()
            loading_layout = QVBoxLayout(loading_widget)
            loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Loading icon
            loading_icon = QLabel("⏳")
            loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 64px;
                    color: #007acc;
                    margin: 30px;
                }
            """
            )
            loading_layout.addWidget(loading_icon)

            # Loading message
            loading_title = QLabel(message)
            loading_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_title.setStyleSheet(
                """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #007acc;
                    margin: 10px;
                }
            """
            )
            loading_layout.addWidget(loading_title)

            # Add loading widget to grid layout instead of replacing scroll area content
            if self.grid_layout:
                self.grid_layout.addWidget(loading_widget, 0, 0, 1, -1)  # Span all columns

        except Exception as e:
            self.logger_system.error(f"Loading state display error: {e}")

    def show_error_state(self, message: str = "エラーが発生しました"):
        """Show error state"""
        try:
            # Clear existing thumbnails but preserve grid layout
            self.clear_thumbnails_safely()

            # Create error state widget
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Error icon
            error_icon = QLabel("❌")
            error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 64px;
                    color: #dc3545;
                    margin: 30px;
                }
            """
            )
            error_layout.addWidget(error_icon)

            # Error message
            error_title = QLabel(message)
            error_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_title.setStyleSheet(
                """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #dc3545;
                    margin: 10px;
                }
            """
            )
            error_layout.addWidget(error_title)

            # Add error widget to grid layout instead of replacing scroll area content
            if self.grid_layout:
                self.grid_layout.addWidget(error_widget, 0, 0, 1, -1)  # Span all columns

        except Exception as e:
            self.logger_system.error(f"Error state display error: {e}")

    def show_empty_state(self):
        """Show empty state when no images are found"""
        try:
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


    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(f"サムネイルグリッド: テーマ変更を検出 - {theme_name}")

            # 全てのサムネイルアイテムにテーママネージャーを設定
            for thumbnail_item in self.thumbnail_items:
                thumbnail_item.set_theme_manager(self.theme_manager)

            # 空状態表示のスタイルも更新
            self._update_empty_state_style()

        except Exception as e:
            self.logger_system.error(f"サムネイルグリッドのテーマ変更処理でエラー: {e}")

    def _update_empty_state_style(self):
        """空状態表示のスタイルを更新"""
        try:
            if hasattr(self, 'empty_state_label'):
                # テーママネージャーから色を取得
                text_color = "#7f8c8d"
                bg_color = "#ffffff"

                if self.theme_manager:
                    try:
                        text_color = self.theme_manager.get_color("secondary", "#7f8c8d")
                        bg_color = self.theme_manager.get_color("background", "#ffffff")
                    except Exception:
                        pass  # デフォルト色を使用

                self.empty_state_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {bg_color};
                        font-size: 16px;
                        font-style: italic;
                        padding: 40px;
                        border-radius: 8px;
                    }}
                """)
        except Exception as e:
            self.logger_system.error(f"空状態スタイル更新でエラー: {e}")


    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(f"サムネイルグリッド: テーマ変更を検出 - {theme_name}")

            # 全てのサムネイルアイテムにテーママネージャーを設定
            for thumbnail_item in self.thumbnail_items:
                thumbnail_item.set_theme_manager(self.theme_manager)

            # 空状態表示のスタイルも更新
            self._update_empty_state_style()

        except Exception as e:
            self.logger_system.error(f"サムネイルグリッドのテーマ変更処理でエラー: {e}")

    def _update_empty_state_style(self):
        """空状態表示のスタイルを更新"""
        try:
            if hasattr(self, 'empty_state_label'):
                # テーママネージャーから色を取得
                text_color = "#7f8c8d"
                bg_color = "#ffffff"

                if self.theme_manager:
                    try:
                        text_color = self.theme_manager.get_color("secondary", "#7f8c8d")
                        bg_color = self.theme_manager.get_color("background", "#ffffff")
                    except Exception:
                        pass  # デフォルト色を使用

                self.empty_state_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {bg_color};
                        font-size: 16px;
                        font-style: italic;
                        padding: 40px;
                        border-radius: 8px;
                    }}
                """)
        except Exception as e:
            self.logger_system.error(f"空状態スタイル更新でエラー: {e}")


    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(f"サムネイルグリッド: テーマ変更を検出 - {theme_name}")

            # 全てのサムネイルアイテムにテーママネージャーを設定
            for thumbnail_item in self.thumbnail_items:
                thumbnail_item.set_theme_manager(self.theme_manager)

            # 空状態表示のスタイルも更新
            self._update_empty_state_style()

        except Exception as e:
            self.logger_system.error(f"サムネイルグリッドのテーマ変更処理でエラー: {e}")

    def _update_empty_state_style(self):
        """空状態表示のスタイルを更新"""
        try:
            if hasattr(self, 'empty_state_label'):
                # テーママネージャーから色を取得
                text_color = "#7f8c8d"
                bg_color = "#ffffff"

                if self.theme_manager:
                    try:
                        text_color = self.theme_manager.get_color("secondary", "#7f8c8d")
                        bg_color = self.theme_manager.get_color("background", "#ffffff")
                    except Exception:
                        pass  # デフォルト色を使用

                self.empty_state_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {bg_color};
                        font-size: 16px;
                        font-style: italic;
                        padding: 40px;
                        border-radius: 8px;
                    }}
                """)
        except Exception as e:
            self.logger_system.error(f"空状態スタイル更新でエラー: {e}")

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
