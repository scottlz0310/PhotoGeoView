"""
UI Integration Controller for AI Integration

Coordinates seamless integration between CursorBLD UI components and CS4Coding functionality.

Author: Kiro AI Integration System
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QMutex, QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from .config_manager import ConfigManager
from .error_handling import ErrorCategory, IntegratedErrorHandler
from .image_processor import CS4CodingImageProcessor
from .logging_system import LoggerSystem
from .models import AIComponent, ApplicationState, ImageMetadata, ProcessingStatus
from .performance_monitor import KiroPerformanceMonitor
from .state_manager import StateManager
from .ui.folder_navigator import EnhancedFolderNavigator
from .ui.theme_manager import IntegratedThemeManager
from .ui.thumbnail_grid import OptimizedThumbnailGrid
from .unified_cache import UnifiedCacheSystem


@dataclass
class UIIntegrationState:
    """State tracking for UI integration"""

    current_folder: Optional[Path] = None
    selected_image: Optional[Path] = None
    loaded_images: List[Path] = field(default_factory=list)
    thumbnail_cache_status: Dict[str, Any] = field(default_factory=dict)
    theme_transition_active: bool = False
    exif_loading_active: bool = False
    map_rendering_active: bool = False
    ui_responsive: bool = True
    last_inteOptional[datetime] = None


class UIIntegrationController(QObject):
    """
    Controller for seamless UI integration between AI components

    Responsibilities:
    - Connect CursorBLD UI components with CS4Coding functionality
    - Manage smooth theme transitions without functionality disruption
    - Coordinate fast thumbnail loading with accurate EXIF display
    - Integrate zoom/pan operations with precise GPS mapping
    """

    # Signals for UI coordination
    folder_loaded = pyqtSignal(Path, list)  # folder, image_list
    image_selected = pyqtSignal(Path, ImageMetadata)  # image_path, metadata
    thumbnail_ready = pyqtSignal(Path, QPixmap)  # image_path, thumbnail
    exif_data_ready = pyqtSignal(Path, dict)  # image_path, exif_data
    map_location_ready = pyqtSignal(float, float, dict)  # lat, lon, map_data
    theme_transition_started = pyqtSignal(str, str)  # old_theme, new_theme
    theme_transition_completed = pyqtSignal(str)  # new_theme
    ui_performance_alert = pyqtSignal(str, str)  # level, message

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        image_processor: CS4CodingImageProcessor,
        theme_manager: IntegratedThemeManager,
        thumbnail_grid: OptimizedThumbnailGrid,
        folder_navigator: EnhancedFolderNavigator,
        cache_system: UnifiedCacheSystem,
        performance_monitor: KiroPerformanceMonitor,
        logger_system: LoggerSystem = None,
    ):
        """
        Initialize UI integration controller

        Args:
            config_manager: Configuration manager
            state_manager: State manager
            image_processor: CS4Coding image processor
            theme_manager: Integrated theme manager
            thumbnail_grid: Optimized thumbnail grid
            folder_navigator: Enhanced folder navigator
            cache_system: Unified cache system
            performance_monitor: Performance monitor
            logger_system: Logging system
        """
        super().__init__()

        # Core systems
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.image_processor = image_processor
        self.cache_system = cache_system
        self.performance_monitor = performance_monitor
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # UI components
        self.theme_manager = theme_manager
        self.thumbnail_grid = thumbnail_grid
        self.folder_navigator = folder_navigator

        # Integration state
        self.integration_state = UIIntegrationState()
        self.ui_mutex = QMutex()

        # Background processing
        self.thumbnail_thread_pool = []
        self.exif_thread_pool = []
        self.map_thread_pool = []

        # Performance monitoring
        self.ui_performance_timer = QTimer()
        self.ui_performance_timer.timeout.connect(self._monitor_ui_performance)
        self.ui_performance_timer.start(1000)  # Check every second

        # Theme transition management
        self.theme_transition_timer = QTimer()
        self.theme_transition_timer.setSingleShot(True)
        self.theme_transition_timer.timeout.connect(self._complete_theme_transition)

        # Setup connections
        self._setup_ui_connections()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "ui_integration_init",
            "UI Integration Controller initialized",
        )

    def _setup_ui_connections(self):
        """Setup connections between UI components"""
        try:
            # Folder navigator connections
            self.folder_navigator.folder_selected.connect(self._handle_folder_selection)
            self.folder_navigator.folder_changed.connect(self._handle_folder_change)

            # Thumbnail grid connections
            self.thumbnail_grid.image_selected.connect(self._handle_image_selection)
            self.thumbnail_grid.thumbnail_requested.connect(
                self._handle_thumbnail_request
            )

            # Theme manager connections
            self.theme_manager.theme_change_requested.connect(
                self._handle_theme_change_request
            )
            self.theme_manager.theme_applied.connect(self._handle_theme_applied)

            # Image processor connections
            self.image_processor.image_processed.connect(self._handle_image_processed)
            self.image_processor.exif_extracted.connect(self._handle_exif_extracted)
            self.image_processor.thumbnail_generated.connect(
                self._handle_thumbnail_generated
            )

            # Performance monitor connections
            self.performance_monitor.performance_alert.connect(
                self._handle_performance_alert
            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "ui_connections_setup",
                "UI component connections established",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "setup_ui_connections"},
                AIComponent.KIRO,
            )

    def _handle_folder_selection(self, folder_path: Path):
        """Handle folder selection from navigator"""
        try:
            with self.ui_mutex:
                self.integration_state.current_folder = folder_path
                self.integration_state.last_interaction = datetime.now()

            # Update application state
            self.state_manager.update_state(current_folder=folder_path)

            # Load folder contents asynchronously
            self._load_folder_async(folder_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_selection",
                f"Folder selected: {folder_path}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "handle_folder_selection", "folder": str(folder_path)},
                AIComponent.CURSOR,
            )

    def _handle_folder_change(self, folder_path: Path):
        """Handle folder change event"""
        try:
            # Clear current selections
            with self.ui_mutex:
                self.integration_state.selected_image = None
                self.integration_state.loaded_images.clear()

            # Update thumbnail grid
            self.thumbnail_grid.clear_thumbnails()

            # Load new folder
            self._handle_folder_selection(folder_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "handle_folder_change", "folder": str(folder_path)},
                AIComponent.CURSOR,
            )

    def _load_folder_async(self, folder_path: Path):
        """Load folder contents asynchronously"""
        try:
            # Check cache first
            cache_key = f"folder_contents_{folder_path}"
            cached_contents = self.cache_system.get(cache_key)

            if cached_contents:
                self._process_folder_contents(folder_path, cached_contents)
                return

            # Load from filesystem
            image_extensions = self.config_manager.get_setting(
                "core.image_formats", [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
            )
            image_files = []

            if folder_path.exists() and folder_path.is_dir():
                for file_path in folder_path.iterdir():
                    if (
                        file_path.is_file()
                        and file_path.suffix.lower() in image_extensions
                    ):
                        image_files.append(file_path)

            # Sort images
            sort_mode = self.state_manager.get_state().image_sort_mode
            ascending = self.state_manager.get_state().image_sort_ascending

            if sort_mode == "name":
                image_files.sort(key=lambda x: x.name, reverse=not ascending)
            elif sort_mode == "date":
                image_files.sort(key=lambda x: x.stat().st_mtime, reverse=not ascending)
            elif sort_mode == "size":
                image_files.sort(key=lambda x: x.stat().st_size, reverse=not ascending)

            # Cache results
            self.cache_system.set(cache_key, image_files, ttl=300)  # 5 minutes

            # Process contents
            self._process_folder_contents(folder_path, image_files)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "load_folder_async", "folder": str(folder_path)},
                AIComponent.KIRO,
            )

    def _process_folder_contents(self, folder_path: Path, image_files: List[Path]):
        """Process loaded folder contents"""
        try:
            with self.ui_mutex:
                self.integration_state.loaded_images = image_files

            # Update thumbnail grid
            self.thumbnail_grid.set_image_list(image_files)

            # Start thumbnail generation
            self._generate_thumbnails_async(image_files)

            # Emit signal
            self.folder_loaded.emit(folder_path, image_files)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "folder_processed",
                f"Processed folder with {len(image_files)} images: {folder_path}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "process_folder_contents", "folder": str(folder_path)},
                AIComponent.KIRO,
            )

    def _generate_thumbnails_async(self, image_files: List[Path]):
        """Generate thumbnails asynchronously"""
        try:
            thumbnail_size = self.state_manager.get_state().thumbnail_size

            for image_path in image_files:
                # Check cache first
                cache_key = f"thumbnail_{image_path}_{thumbnail_size}"
                cached_thumbnail = self.cache_system.get(cache_key)

                if cached_thumbnail:
                    self.thumbnail_ready.emit(image_path, cached_thumbnail)
                    continue

                # Generate thumbnail asynchronously
                self.image_processor.generate_thumbnail_async(
                    image_path,
                    (thumbnail_size, thumbnail_size),
                    callback=lambda path, thumb: self._handle_thumbnail_generated(
                        path, thumb
                    ),
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "generate_thumbnails_async"},
                AIComponent.KIRO,
            )

    def _handle_image_selection(self, image_path: Path):
        """Handle image selection from thumbnail grid"""
        try:
            with self.ui_mutex:
                self.integration_state.selected_image = image_path
                self.integration_state.last_interaction = datetime.now()

            # Update application state
            self.state_manager.update_state(selected_image=image_path)

            # Load image metadata asynchronously
            self._load_image_metadata_async(image_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "image_selection", f"Image selected: {image_path}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "handle_image_selection", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _load_image_metadata_async(self, image_path: Path):
        """Load image metadata asynchronously"""
        try:
            # Check cache first
            cache_key = f"metadata_{image_path}"
            cached_metadata = self.cache_system.get(cache_key)

            if cached_metadata:
                self.image_selected.emit(image_path, cached_metadata)
                return

            # Extract metadata using CS4Coding processor
            with self.ui_mutex:
                self.integration_state.exif_loading_active = True

            self.image_processor.extract_metadata_async(
                image_path,
                callback=lambda path, metadata: self._handle_metadata_extracted(
                    path, metadata
                ),
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "load_image_metadata_async", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _handle_metadata_extracted(self, image_path: Path, metadata: ImageMetadata):
        """Handle extracted image metadata"""
        try:
            with self.ui_mutex:
                self.integration_state.exif_loading_active = False

            # Cache metadata
            cache_key = f"metadata_{image_path}"
            self.cache_system.set(cache_key, metadata, ttl=3600)  # 1 hour

            # Emit signal
            self.image_selected.emit(image_path, metadata)

            # If GPS data is available, prepare map
            if metadata.has_gps:
                self._prepare_map_async(metadata.latitude, metadata.longitude, metadata)

            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "metadata_extracted",
                f"Metadata extracted for: {image_path}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "handle_metadata_extracted", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _prepare_map_async(
        self, latitude: float, longitude: float, metadata: ImageMetadata
    ):
        """Prepare map data asynchronously"""
        try:
            with self.ui_mutex:
                self.integration_state.map_rendering_active = True

            # Check cache first
            cache_key = f"map_{latitude}_{longitude}"
            cached_map_data = self.cache_system.get(cache_key)

            if cached_map_data:
                self.map_location_ready.emit(latitude, longitude, cached_map_data)
                with self.ui_mutex:
                    self.integration_state.map_rendering_active = False
                return

            # Generate map data using CS4Coding functionality
            map_data = {
                "center": (latitude, longitude),
                "zoom": self.state_manager.get_state().map_zoom,
                "markers": [
                    {
                        "lat": latitude,
                        "lon": longitude,
                        "popup": f"{metadata.display_name}<br/>Taken: {metadata.created_date}",
                        "icon": "camera",
                    }
                ],
                "metadata": metadata,
            }

            # Cache map data
            self.cache_system.set(cache_key, map_data, ttl=1800)  # 30 minutes

            # Emit signal
            self.map_location_ready.emit(latitude, longitude, map_data)

            with self.ui_mutex:
                self.integration_state.map_rendering_active = False

            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "map_prepared",
                f"Map prepared for location: {latitude}, {longitude}",
            )

        except Exception as e:
            with self.ui_mutex:
                self.integration_state.map_rendering_active = False

            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "prepare_map_async", "lat": latitude, "lon": longitude},
                AIComponent.COPILOT,
            )

    def _handle_thumbnail_request(self, image_path: Path):
        """Handle thumbnail request from grid"""
        try:
            thumbnail_size = self.state_manager.get_state().thumbnail_size

            # Check cache first
            cache_key = f"thumbnail_{image_path}_{thumbnail_size}"
            cached_thumbnail = self.cache_system.get(cache_key)

            if cached_thumbnail:
                self.thumbnail_ready.emit(image_path, cached_thumbnail)
                return

            # Generate thumbnail
            self.image_processor.generate_thumbnail_async(
                image_path,
                (thumbnail_size, thumbnail_size),
                callback=lambda path, thumb: self._handle_thumbnail_generated(
                    path, thumb
                ),
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "handle_thumbnail_request", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _handle_thumbnail_generated(self, image_path: Path, thumbnail: QPixmap):
        """Handle generated thumbnail"""
        try:
            thumbnail_size = self.state_manager.get_state().thumbnail_size

            # Cache thumbnail
            cache_key = f"thumbnail_{image_path}_{thumbnail_size}"
            self.cache_system.set(cache_key, thumbnail, ttl=1800)  # 30 minutes

            # Emit signal
            self.thumbnail_ready.emit(image_path, thumbnail)

            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "thumbnail_generated",
                f"Thumbnail generated for: {image_path}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "handle_thumbnail_generated", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _handle_theme_change_request(self, old_theme: str, new_theme: str):
        """Handle theme change request"""
        try:
            with self.ui_mutex:
                self.integration_state.theme_transition_active = True

            # Emit transition started signal
            self.theme_transition_started.emit(old_theme, new_theme)

            # Start transition timer
            self.theme_transition_timer.start(500)  # 500ms transition

            # Update application state
            self.state_manager.update_state(current_theme=new_theme)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "theme_change_started",
                f"Theme change: {old_theme} -> {new_theme}",
            )

        except Exception as e:
            with self.ui_mutex:
                self.integration_state.theme_transition_active = False

            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "handle_theme_change_request",
                    "old_theme": old_theme,
                    "new_theme": new_theme,
                },
                AIComponent.CURSOR,
            )

    def _complete_theme_transition(self):
        """Complete theme transition"""
        try:
            with self.ui_mutex:
                self.integration_state.theme_transition_active = False

            current_theme = self.state_manager.get_state().current_theme

            # Emit transition completed signal
            self.theme_transition_completed.emit(current_theme)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "theme_change_completed",
                f"Theme transition completed: {current_theme}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "complete_theme_transition"},
                AIComponent.CURSOR,
            )

    def _handle_theme_applied(self, theme_name: str):
        """Handle theme applied event"""
        try:
            # Refresh UI components with new theme
            self.thumbnail_grid.refresh_theme()
            self.folder_navigator.refresh_theme()

            # Update cache status
            with self.ui_mutex:
                self.integration_state.thumbnail_cache_status["theme_applied"] = (
                    datetime.now()
                )

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "theme_applied",
                f"Theme applied and UI refreshed: {theme_name}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "handle_theme_applied", "theme": theme_name},
                AIComponent.CURSOR,
            )

    def _handle_image_processed(self, image_path: Path, result: Dict[str, Any]):
        """Handle image processing completion"""
        try:
            # Update processing status
            if "metadata" in result:
                metadata = result["metadata"]
                self.exif_data_ready.emit(image_path, metadata)

            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "image_processed",
                f"Image processing completed: {image_path}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "handle_image_processed", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _handle_exif_extracted(self, image_path: Path, exif_data: Dict[str, Any]):
        """Handle EXIF data extraction"""
        try:
            # Emit EXIF data ready signal
            self.exif_data_ready.emit(image_path, exif_data)

            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "exif_extracted",
                f"EXIF data extracted: {image_path}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "handle_exif_extracted", "image": str(image_path)},
                AIComponent.COPILOT,
            )

    def _handle_performance_alert(self, level: str, message: str):
        """Handle performance alert"""
        try:
            # Check if UI is responsive
            with self.ui_mutex:
                if not self.integration_state.ui_responsive:
                    return  # Don't emit alerts if UI is already unresponsive

            # Emit UI performance alert
            self.ui_performance_alert.emit(level, message)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_alert",
                f"UI Performance alert [{level}]: {message}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "handle_performance_alert",
                    "level": level,
                    "message": message,
                },
                AIComponent.KIRO,
            )

    def _monitor_ui_performance(self):
        """Monitor UI performance"""
        try:
            # Check UI responsiveness
            app = QApplication.instance()
            if app:
                events_processed = app.processEvents()

                with self.ui_mutex:
                    self.integration_state.ui_responsive = events_processed >= 0

                # Check for performance issues
                if (
                    self.integration_state.theme_transition_active
                    and self.integration_state.exif_loading_active
                    and self.integration_state.map_rendering_active
                ):

                    self.ui_performance_alert.emit(
                        "warning", "Multiple heavy operations running simultaneously"
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "monitor_ui_performance"},
                AIComponent.KIRO,
            )

    def get_integration_state(self) -> UIIntegrationState:
        """Get current integration state"""
        with self.ui_mutex:
            return self.integration_state

    def set_thumbnail_size(self, size: int):
        """Set thumbnail size and refresh grid"""
        try:
            # Update state
            self.state_manager.update_state(thumbnail_size=size)

            # Clear thumbnail cache
            self.cache_system.clear_pattern("thumbnail_*")

            # Refresh thumbnail grid
            self.thumbnail_grid.set_thumbnail_size(size)

            # Regenerate thumbnails for current folder
            if self.integration_state.loaded_images:
                self._generate_thumbnails_async(self.integration_state.loaded_images)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "thumbnail_size_changed",
                f"Thumbnail size changed to: {size}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_thumbnail_size", "size": size},
                AIComponent.KIRO,
            )

    def refresh_current_folder(self):
        """Refresh current folder contents"""
        try:
            if self.integration_state.current_folder:
                # Clear cache for current folder
                cache_key = f"folder_contents_{self.integration_state.current_folder}"
                self.cache_system.delete(cache_key)

                # Reload folder
                self._load_folder_async(self.integration_state.current_folder)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "refresh_current_folder"},
                AIComponent.KIRO,
            )

    def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop timers
            if self.ui_performance_timer:
                self.ui_performance_timer.stop()

            if self.theme_transition_timer:
                self.theme_transition_timer.stop()

            # Clear thread pools
            self.thumbnail_thread_pool.clear()
            self.exif_thread_pool.clear()
            self.map_thread_pool.clear()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "ui_integration_cleanup",
                "UI Integration Controller cleaned up",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cleanup"},
                AIComponent.KIRO,
            )
