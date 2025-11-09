"""
Central Application Controller for AI Integration

Coordinates between all AI implementations:
- GitHub Copilot (CS4Coding): Core functionality
- Cursor (CursorBLD): UI/UX components
- Kiro: Integration and quality management

Author: Kiro AI Integration System
"""

import asyncio
import contextlib
import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from .error_handling import ErrorCategory, IntegratedErrorHandler
from .image_processor import CS4CodingImageProcessor
from .interfaces import (
    IConfigManager,
    IImageProcessor,
    IMapProvider,
    IPerformanceMonitor,
    IThemeManager,
)
from .logging_system import LoggerSystem
from .models import (
    AIComponent,
    ApplicationState,
    ImageMetadata,
    PerformanceMetrics,
    ProcessingStatus,
)
from .performance_monitor import KiroPerformanceMonitor
from .state_manager import StateManager
from .unified_cache import UnifiedCacheSystem


class AppController:
    """
    Central application controller that coordinates all AI implementations

    This controller acts as the integration layer between:
    - CursorBLD UI components
    - CS4Coding core functionality
    - Kiro optimization and monitoring
    """

    def __init__(self, config_manager: IConfigManager = None, logger_system: LoggerSystem = None):
        """
        Initialize the application controller

        Args:
            config_manager: Configuration management interface
            logger_system: Logging system instance
        """

        # Core systems
        self.config_manager = config_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Kiro integration components
        self.state_manager: StateManager | None = None
        self.unified_cache: UnifiedCacheSystem | None = None

        # AI component interfaces (to be initialized)
        self.image_processor: IImageProcessor | None = None
        self.theme_manager: IThemeManager | None = None
        self.map_provider: IMapProvider | None = None
        self.performance_monitor: IPerformanceMonitor | None = None

        # Kiro integration components
        self.cache_system: UnifiedCacheSystem | None = None
        self.state_manager: StateManager | None = None

        # Application state
        self.app_state = ApplicationState()
        self.is_initialized = False
        self.is_shutting_down = False

        # Component registry
        self.ai_components: dict[AIComponent, dict[str, Any]] = {
            AIComponent.COPILOT: {"status": "inactive", "last_operation": None},
            AIComponent.CURSOR: {"status": "inactive", "last_operation": None},
            AIComponent.KIRO: {"status": "active", "last_operation": "initialization"},
        }

        # Event system
        self.event_handlers: dict[str, list[Callable]] = {}
        self.event_lock = threading.Lock()

        # Performance tracking
        self.operation_times: dict[str, list[float]] = {}
        self.performance_history: list[PerformanceMetrics] = []

        # Cache system
        self.cache: dict[str, Any] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "size": 0}

        self.logger_system.log_ai_operation(AIComponent.KIRO, "initialization", "AppController initialized")

    async def initialize(self) -> bool:
        """
        Initialize the application controller and all AI components

        Returns:
            True if initialization successful, False otherwise
        """

        try:
            with self.logger_system.operation_context(AIComponent.KIRO, "app_initialization"):
                # Initialize AI components
                await self._initialize_ai_components()

                # Setup event system
                self._setup_event_system()

                # Start performance monitoring
                if self.performance_monitor:
                    self.performance_monitor.start_monitoring()

                # Load application state
                await self._load_application_state()

                self.is_initialized = True

                # Log integration event
                self.logger_system.log_integration_event(
                    "Application initialized",
                    [AIComponent.COPILOT, AIComponent.CURSOR, AIComponent.KIRO],
                    {"initialization_time": datetime.now().isoformat()},
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "app_initialization"},
                AIComponent.KIRO,
            )
            return False

    async def _initialize_ai_components(self):
        """Initialize all AI component interfaces"""

        try:
            # Initialize Kiro integration components first
            self.cache_system = UnifiedCacheSystem(config_manager=self.config_manager, logger_system=self.logger_system)

            self.state_manager = StateManager(config_manager=self.config_manager, logger_system=self.logger_system)

            self.performance_monitor = KiroPerformanceMonitor(
                config_manager=self.config_manager, logger_system=self.logger_system
            )

            # Initialize CS4Coding ImageProcessor
            self.image_processor = CS4CodingImageProcessor(
                config_manager=self.config_manager, logger_system=self.logger_system
            )

            # Start performance monitoring
            self.performance_monitor.start_monitoring()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "component_initialization",
                "All AI component interfaces initialized",
            )

            # Mark components as initialized
            for component in self.ai_components:
                self.ai_components[component]["status"] = "active"
                self.ai_components[component]["last_operation"] = "initialization"

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "ai_component_initialization"},
                AIComponent.KIRO,
            )

    def _setup_event_system(self):
        """Setup the event handling system"""

        # Register core events
        self.register_event_handler("image_selected", self._on_image_selected)
        self.register_event_handler("folder_changed", self._on_folder_changed)
        self.register_event_handler("theme_changed", self._on_theme_changed)
        self.register_event_handler("error_occurred", self._on_error_occurred)

        self.logger_system.log_ai_operation(AIComponent.KIRO, "event_system", "Event system initialized")

    async def _load_application_state(self):
        """Load application state from configuration"""

        if self.config_manager:
            try:
                # Load saved state
                saved_state = self.config_manager.get_setting("app_state", {})

                # Restore relevant state
                if "current_theme" in saved_state:
                    self.app_state.current_theme = saved_state["current_theme"]

                if "thumbnail_size" in saved_state:
                    self.app_state.thumbnail_size = saved_state["thumbnail_size"]

                if "folder_history" in saved_state:
                    self.app_state.folder_history = [Path(p) for p in saved_state["folder_history"]]

                self.lcomer_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_loading",
                    f"Application state loaded: {len(saved_state)} settings",
                )

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "state_loading"},
                    AIComponent.KIRO,
                )

    async def save_application_state(self):
        """Save current application state"""

        if not self.config_manager:
            return

        try:
            state_data = {
                "current_theme": self.app_state.current_theme,
                "thumbnail_size": self.app_state.thumbnail_size,
                "folder_history": [str(p) for p in self.app_state.folder_history],
                "window_geometry": self.app_state.window_geometry,
                "performance_mode": self.app_state.performance_mode,
                "last_saved": datetime.now().isoformat(),
            }

            self.config_manager.set_setting("app_state", state_data)
            await asyncio.to_thread(self.config_manager.save_config)

            self.logger_system.log_ai_operation(AIComponent.KIRO, "state_saving", "Application state saved")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "state_saving"},
                AIComponent.KIRO,
            )

    # Event system methods

    def register_event_handler(self, event_name: str, handler: Callable):
        """Register an event handler"""

        with self.event_lock:
            if event_name not in self.event_handlers:
                self.event_handlers[event_name] = []
            self.event_handlers[event_name].append(handler)

    def unregister_event_handler(self, event_name: str, handler: Callable):
        """Unregister an event handler"""

        with self.event_lock:
            if event_name in self.event_handlers:
                with contextlib.suppress(ValueError):
                    self.event_handlers[event_name].remove(handler)

    async def emit_event(self, event_name: str, data: dict[str, Any] | None = None):
        """Emit an event to all registered handlers"""

        with self.event_lock:
            handlers = self.event_handlers.get(event_name, []).copy()

        if handlers:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "event_emission",
                f"Emitting event: {event_name} to {len(handlers)} handlers",
            )

            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data or {})
                    else:
                        handler(data or {})
                except Exception as e:
                    self.error_handler.handle_error(
                        e,
                        ErrorCategory.INTEGRATION_ERROR,
                        {"operation": "event_handling", "event": event_name},
                        AIComponent.KIRO,
                    )

    # Core event handlers

    async def _on_image_selected(self, data: dict[str, Any]):
        """Handle image selection event"""

        if image_path := data.get("image_path"):
            self.app_state.selected_image = Path(image_path)
            self.app_state.update_activity()

            # Trigger image processing
            await self.process_image(Path(image_path))

    async def _on_folder_changed(self, data: dict[str, Any]):
        """Handle folder change event"""

        if folder_path := data.get("folder_path"):
            folder_path = Path(folder_path)
            self.app_state.current_folder = folder_path
            self.app_state.add_to_history(folder_path)
            self.app_state.update_activity()

            # Load folder contents
            await self.load_folder_contents(folder_path)

    async def _on_theme_changed(self, data: dict[str, Any]):
        """Handle theme change event"""

        theme_name = data.get("theme_name")
        if theme_name and self.theme_manager:
            try:
                success = self.theme_manager.apply_theme(theme_name)
                if success:
                    self.app_state.current_theme = theme_name
                    self.app_state.update_activity()

                    self.logger_system.log_ai_operation(
                        AIComponent.CURSOR,
                        "theme_change",
                        f"Theme changed to: {theme_name}",
                    )

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.UI_ERROR,
                    {"operation": "theme_change", "theme": theme_name},
                    AIComponent.CURSOR,
                )

    async def _on_error_occurred(self, data: dict[str, Any]):
        """Handle error occurrence event"""

        error_context = data.get("error_context")
        if error_context:
            # Update application state with error information
            self.app_state.add_error(
                {
                    "category": error_context.category.value,
                    "severity": error_context.severity.value,
                    "message": error_context.user_message,
                    "ai_component": (error_context.ai_component.value if error_context.ai_component else None),
                }
            )

    # Core operations

    async def process_image(self, image_path: Path) -> ImageMetadata | None:
        """
        Process an image using integrated AI components

        Args:
            image_path: Path to the image file

        Returns:
            ImageMetadata if successful, None otherwise
        """

        if not self.image_processor:
            return None

        start_time = time.time()

        try:
            with self.logger_system.operation_context(AIComponent.COPILOT, "image_processing"):
                # Check cache first
                cache_key = f"image_{image_path.stem}_{image_path.stat().st_mtime}"
                cached_metadata = self.get_from_cache(cache_key)

                if cached_metadata:
                    self.cache_stats["hits"] += 1
                    return cached_metadata

                self.cache_stats["misses"] += 1

                # Load image
                image = self.image_processor.load_image(image_path)
                if not image:
                    return None

                # Extract EXIF data
                exif_data = self.image_processor.extract_exif(image_path)

                # Create metadata
                file_stat = image_path.stat()
                metadata = ImageMetadata(
                    file_path=image_path,
                    file_size=file_stat.st_size,
                    created_date=datetime.fromtimestamp(file_stat.st_ctime),
                    modified_date=datetime.fromtimestamp(file_stat.st_mtime),
                    processing_status=ProcessingStatus.COMPLETED,
                    ai_processor=AIComponent.COPILOT,
                )

                # Populate EXIF data
                self._populate_exif_metadata(metadata, exif_data)

                # Generate thumbnail
                thumbnail = self.image_processor.generate_thumbnail(
                    image,
                    (self.app_state.thumbnail_size, self.app_state.thumbnail_size),
                )

                if thumbnail:
                    # Save thumbnail and update metadata
                    thumbnail_path = self._save_thumbnail(image_path, thumbnail)
                    metadata.thumbnail_path = thumbnail_path
                    metadata.thumbnail_size = (
                        self.app_state.thumbnail_size,
                        self.app_state.thumbnail_size,
                    )

                # Cache the metadata
                self.add_to_cache(cache_key, metadata)

                # Update statistics
                self.app_state.images_processed += 1
                processing_time = time.time() - start_time
                self.app_state.record_operation("image_processing", processing_time)

                # Log performance
                self.logger_system.log_performance(
                    AIComponent.COPILOT,
                    "image_processing",
                    {
                        "duration": processing_time,
                        "file_size": metadata.file_size,
                        "has_exif": bool(exif_data),
                        "has_gps": metadata.has_gps,
                    },
                )

                return metadata

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "image_processing", "file_path": str(image_path)},
                AIComponent.COPILOT,
            )
            return None

    def _populate_exif_metadata(self, metadata: ImageMetadata, exif_data: dict[str, Any]):
        """Populate metadata with EXIF information"""

        # Camera information
        metadata.camera_make = exif_data.get("make")
        metadata.camera_model = exif_data.get("model")
        metadata.lens_model = exif_data.get("lens_model")

        # Technical settings
        metadata.focal_length = exif_data.get("focal_length")
        metadata.aperture = exif_data.get("aperture")
        metadata.shutter_speed = exif_data.get("shutter_speed")
        metadata.iso = exif_data.get("iso")

        # GPS information
        if "gps" in exif_data:
            gps_data = exif_data["gps"]
            metadata.latitude = gps_data.get("latitude")
            metadata.longitude = gps_data.get("longitude")
            metadata.altitude = gps_data.get("altitude")

            if "timestamp" in gps_data:
                metadata.gps_timestamp = gps_data["timestamp"]

        # Image dimensions
        metadata.width = exif_data.get("width")
        metadata.height = exif_data.get("height")

    def _save_thumbnail(self, image_path: Path, thumbnail) -> Path | None:
        """Save thumbnail to cache directory"""

        try:
            cache_dir = Path("cache/thumbnails")
            cache_dir.mkdir(parents=True, exist_ok=True)

            thumbnail_path = cache_dir / f"{image_path.stem}_thumb.jpg"

            # Save thumbnail (implementation depends on image library)
            # This is a placeholder - actual implementation would save the thumbnail

            return thumbnail_path

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "thumbnail_save", "image_path": str(image_path)},
                AIComponent.KIRO,
            )
            return None

    async def load_folder_contents(self, folder_path: Path) -> list[Path]:
        """
        Load and filter folder contents for supported images

        Args:
            folder_path: Path to the folder

        Returns:
            List of supported image file paths
        """

        if not self.image_processor:
            return []

        try:
            with self.logger_system.operation_context(AIComponent.CURSOR, "folder_loading"):
                # Get supported formats
                supported_formats = self.image_processor.get_supported_formats()

                # Find image files
                image_files = []
                for file_path in folder_path.iterdir():
                    if (
                        file_path.is_file() and file_path.suffix.lower() in supported_formats
                    ) and self.image_processor.validate_image(file_path):
                        image_files.append(file_path)

                # Sort files
                if self.app_state.image_sort_mode == "name":
                    image_files.sort(
                        key=lambda p: p.name,
                        reverse=not self.app_state.image_sort_ascending,
                    )
                elif self.app_state.image_sort_mode == "date":
                    image_files.sort(
                        key=lambda p: p.stat().st_mtime,
                        reverse=not self.app_state.image_sort_ascending,
                    )
                elif self.app_state.image_sort_mode == "size":
                    image_files.sort(
                        key=lambda p: p.stat().st_size,
                        reverse=not self.app_state.image_sort_ascending,
                    )

                # Update application state
                self.app_state.loaded_images = image_files

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_loading",
                    f"Loaded {len(image_files)} images from {folder_path}",
                )

                return image_files

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "folder_loading", "folder_path": str(folder_path)},
                AIComponent.CURSOR,
            )
            return []

    # Cache management

    def get_from_cache(self, key: str) -> Any:
        """Get item from cache"""
        return self.cache.get(key)

    def add_to_cache(self, key: str, value: Any, ttl: int | None = None):
        """Add item to cache"""
        self.cache[key] = value
        self.cache_stats["size"] = len(self.cache)

        # Simple cache size management
        if len(self.cache) > 1000:
            # Remove oldest 100 items (simple FIFO)
            keys_to_remove = list(self.cache.keys())[:100]
            for k in keys_to_remove:
                del self.cache[k]
            self.cache_stats["size"] = len(self.cache)

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0, "size": 0}

        self.logger_system.log_ai_operation(AIComponent.KIRO, "cache_management", "Cache cleared")

    # Performance monitoring

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""

        if self.performance_monitor:
            return self.performance_monitor.get_performance_metrics()

        # Fallback basic metrics
        return PerformanceMetrics(
            images_loaded=self.app_state.images_processed,
            cache_hits=self.cache_stats["hits"],
            cache_misses=self.cache_stats["misses"],
        )

    def get_ai_component_status(self) -> dict[str, str]:
        """Get status of all AI components"""

        return {component.value: info["status"] for component, info in self.ai_components.items()}

    # Shutdown

    async def shutdown(self):
        """Shutdown the application controller"""

        if self.is_shutting_down:
            return

        self.is_shutting_down = True

        try:
            with self.logger_system.operation_context(AIComponent.KIRO, "app_shutdown"):
                # Save application state
                await self.save_application_state()

                # Stop performance monitoring
                if self.performance_monitor:
                    self.performance_monitor.stop_monitoring()
                    self.performance_monitor.shutdown()

                # Shutdown cache system
                if self.cache_system:
                    self.cache_system.shutdown()

                # Shutdown state manager
                if self.state_manager:
                    self.state_manager.shutdown()

                # Shutdown image processor
                if self.image_processor and hasattr(self.image_processor, "shutdown"):
                    self.image_processor.shutdown()

                # Clear cache
                self.clear_cache()

                # Shutdown logging
                self.logger_system.shutdown()

                self.logger_system.log_integration_event(
                    "Application shutdown",
                    [AIComponent.COPILOT, AIComponent.CURSOR, AIComponent.KIRO],
                )

        except Exception as e:
            # Log error but continue shutdown
            logger = logging.getLogger(__name__)
            error_msg = f"Error during shutdown: {e}"
            logger.error(error_msg)
            print(error_msg)  # コンソールにも出力(シャットダウン時の重要情報)

        finally:
            self.is_initialized = False
