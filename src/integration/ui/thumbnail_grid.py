"""
Optimized Thumbnail Grid for AI Integration

Combines CursorBLD's fast thumbnail display with Kiro optimization:
- CursorBLD: Qt native high-speed thumbnail generation and display
- Kiro: Memory management, caching, performance monitoring

Author: Kiro AI Integration System
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QGridLayout, QPushButton, QSlider, QSpinBox, QFrame,
    QMenu, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QTimer, QThread, QObject,
    QMutex, QMutexLocker
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

    def __init__(self, image_path: Path, thumbnail_size: int = 150):
        super().__init__()

        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.is_loaded = False
        self.is_loading = False

        # Setup UI
        self.setFixedSize(thumbnail_size + 20, thumbnail_size + 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
                self.thumbnail_size, self.thumbnail_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.setPixmap(scaled_pixmap)
            self.is_loaded = True
        else:
            self._show_error()

    def _show_error(self):
        """Show error placeholder"""

        error_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        error_pixmap.fill(QColor("#f8d7da"))

        painter = QPainterpixmap)
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
                len(image_paths)
            )

    def _load_single_thumbnail(self, image_path: Path, size: int, index: int, total: int):
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
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
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
                {"image_path": str(image_path), "size": size}
            )

            # Emit error
            self.thumbnail_loaded.emit(image_path, QPixmap())
            self.loading_progress.emit(index + 1, total)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""

        with QMutexLocker(self.cache_mutex):
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

            avg_load_time = sum(self.load_times) / len(self.load_times) if self.load_times else 0

            return {
                "cache_size": len(self.cache),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": hit_rate,
                "average_load_time": avg_load_time,
                "recent_load_times": self.load_times[-10:]
            }

    def clear_cache(self):
        """Clear thumbnail cache"""

        with QMutexLocker(self.cache_mutex):
            self.cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0


class OptimizedThumbnailGrid(QWidget):
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

    def __init__(self,
                 config_manager: ConfigManager,
                 state_manager: StateManager,
                 logger_system: LoggerSystem = None):
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
            "Optimized thumbnail grid initialized"
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
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # Create grid widget
            self.grid_widget = QWidget()
            self.grid_layout = QGridLayout(self.grid_widget)
            self.grid_layout.setSpacing(self.spacing)
            self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            self.scroll_area.setWidget(self.grid_widget)
            main_layout.addWidget(self.scroll_area, 1)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_grid_ui_init"},
                AIComponent.CURSOR
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
        self.state_manager.add_change_listener("thumbnail_size", self._on_thumbnail_size_changed)

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
                f"Loading {len(image_paths)} thumbnails"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "load_images", "count": len(image_paths)},
                AIComponent.CURSOR
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
                e, ErrorCategory.UI_ERROR,
                {"operation": "create_thumbnail_items"},
                AIComponent.CURSOR
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
                e, ErrorCategory.UI_ERROR,
                {"operation": "clear_thumbnails"},
                AIComponent.CURSOR
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
                f"Thumbnail clicked: {image_path.name}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_click", "image": str(image_path)},
                AIComponent.CURSOR
            )

    def _on_thumbnail_loaded(self, image_path: Path, pixmap: QPixmap):
        """Handle thumbnail loaded"""

        try:
            if image_path in self.thumbnail_items:
                thumbnail_item = self.thumbnail_items[image_path]
                thumbnail_item.set_thumbnail(pixmap)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_loaded", "image": str(image_path)},
                AIComponent.CURSOR
            )

    def _on_loading_progress(self, current: int, total: int):
        """Handle loading progress"""

        self.loading_progress.emit(current, total)

        if current >= total:
            self.loading_finished.emit()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_load_complete",
                f"Loaded {total} thumbnails"
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
                e, ErrorCategory.UI_ERROR,
                {"operation": "size_change", "size": size},
                AIComponent.CURSOR
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
                AIComponent.KIRO,
                "cache_clear",
                "Thumbnail cache cleared"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_clear"},
                AIComponent.KIRO
            )

    def _update_cache_info(self):
        """Update cache information display (Kiro enhancement)"""

        try:
            cache_stats = self.thumbnail_loader.get_cache_stats()

            cache_size = cache_stats.get("cache_size", 0)
            hit_rate = cache_stats.get("hit_rate", 0)

            self.cache_label.setText(f"Cache: {cache_size} items ({hit_rate:.1%} hit rate)")

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_info_update"},
                AIComponent.KIRO
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
                    "average_load_time": cache_stats.get("average_load_time", 0)
                }
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "performance_metrics_update"},
                AIComponent.KIRO
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
                action.triggered.connect(lambda checked, s=size: self._on_size_changed(s))
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
                e, ErrorCategory.UI_ERROR,
                {"operation": "context_menu"},
                AIComponent.CURSOR
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
                e, ErrorCategory.UI_ERROR,
                {"operation": "cache_info_dialog"},
                AIComponent.CURSOR
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
