"""
Unified Data Models for AI Integration

Defines data models that combine requirements from all AI implementations:
- GitHub Copilot (CS4Coding): Robust data structures
- Cursor (CursorBLD): UI-optimized models
- Kiro: Integration and performance optimization

Author: Kiro AI Integration System
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ProcessingStatus(Enum):
    """Status enumeration for processing operations"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


class AIComponent(Enum):
    """AI component enumeration"""

    COPILOT = "copilot"
    CURSOR = "cursor"
    KIRO = "kiro"


@dataclass
class ImageMetadata:
    """
    Unified image metadata model combining all AI requirements

    Integrates:
    - CS4Coding: High-precision EXIF data
    - CursorBLD: UI-optimized display information
    - Kiro: Performance and caching metadata
    """

    # Basic file information
    file_path: Path
    file_size: int
    created_date: datetime
    modified_date: datetime
    file_format: str = ""

    # EXIF information (CS4Coding precision)
    camera_make: str | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    focal_length: float | None = None
    aperture: float | None = None
    shutter_speed: str | None = None
    iso: int | None = None
    flash: str | None = None
    white_balance: str | None = None
    exposure_mode: str | None = None
    metering_mode: str | None = None

    # GPS information (CS4Coding precision)
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    gps_timestamp: datetime | None = None
    gps_direction: float | None = None
    gps_speed: float | None = None

    # Image technical details
    width: int | None = None
    height: int | None = None
    color_space: str | None = None
    bit_depth: int | None = None
    compression: str | None = None

    # UI information (CursorBLD optimization)
    thumbnail_path: Path | None = None
    thumbnail_size: tuple[int, int] | None = None
    display_name: str = ""
    preview_available: bool = False

    # Kiro integration information
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    cache_key: str | None = None
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    ai_processor: AIComponent | None = None
    last_accessed: datetime | None = None
    access_count: int = 0

    # Error handling
    processing_errors: list[str] = field(default_factory=list)
    validation_status: bool = True

    def __post_init__(self) -> None:
        """Post-initialization processing"""
        if not self.display_name:
            self.display_name = self.file_path.name

        if not self.cache_key:
            timestamp = int(self.modified_date.timestamp())
            self.cache_key = f"{self.file_path.stem}_{self.file_size}_{timestamp}"

    @property
    def has_gps(self) -> bool:
        """Check if image has GPS coordinates"""
        return self.latitude is not None and self.longitude is not None

    @property
    def gps_coordinates(self) -> tuple[float, float] | None:
        """Get GPS coordinates as tuple"""
        if self.has_gps and self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None

    @property
    def aspect_ratio(self) -> float | None:
        """Calculate aspect ratio"""
        if self.width and self.height:
            return self.width / self.height
        return None

    @property
    def megapixels(self) -> float | None:
        """Calculate megapixels"""
        if self.width and self.height:
            return (self.width * self.height) / 1_000_000
        return None


@dataclass
class ThemeConfiguration:
    """
    Unified theme configuration model

    Integrates:
    - CursorBLD: Qt-Theme-Manager system
    - Kiro: Accessibility and performance features
    """

    # Basic theme information
    name: str
    display_name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""

    # CursorBLD theme system integration
    qt_theme_name: str = ""
    style_sheet: str = ""
    color_scheme: dict[str, str] = field(default_factory=dict)
    icon_theme: str = "default"

    # UI component styling
    window_style: dict[str, Any] = field(default_factory=dict)
    button_style: dict[str, Any] = field(default_factory=dict)
    menu_style: dict[str, Any] = field(default_factory=dict)
    toolbar_style: dict[str, Any] = field(default_factory=dict)

    # Kiro accessibility features
    accessibility_features: dict[str, bool] = field(
        default_factory=lambda: {
            "high_contrast": False,
            "large_fonts": False,
            "screen_reader_support": True,
            "keyboard_navigation": True,
            "focus_indicators": True,
        }
    )

    # Kiro performance settings
    performance_settings: dict[str, Any] = field(
        default_factory=lambda: {
            "animation_enabled": True,
            "transparency_enabled": True,
            "shadow_effects": True,
            "gradient_rendering": True,
            "anti_aliasing": True,
        }
    )

    # Custom properties for extensibility
    custom_properties: dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    usage_count: int = 0

    def __post_init__(self):
        """Post-initialization processing"""
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").title()

    @property
    def is_dark_theme(self) -> bool:
        """Check if this is a dark theme"""
        bg_color = self.color_scheme.get("background", "#ffffff")
        # Simple heuristic: if background is dark, it's a dark theme
        if bg_color.startswith("#"):
            rgb_sum = sum(int(bg_color[i : i + 2], 16) for i in (1, 3, 5))
            return rgb_sum < 384  # 128 * 3
        return False

    @property
    def accessibility_score(self) -> float:
        """Calculate accessibility score (0-1)"""
        enabled_features = sum(1 for enabled in self.accessibility_features.values() if enabled)
        total_features = len(self.accessibility_features)
        return enabled_features / total_features if total_features > 0 else 0.0


@dataclass
class ApplicationState:
    """
    Unified application state model

    Integrates:
    - CursorBLD: UI state management
    - CS4Coding: Functional state tracking
    - Kiro: Performance and integration state
    """

    # File system state
    current_folder: Path | None = None
    selected_image: Path | None = None
    loaded_images: list[Path] = field(default_factory=list)

    # CursorBLD UI state
    current_theme: str = "default"
    thumbnail_size: int = 150
    folder_history: list[Path] = field(default_factory=list)
    ui_layout: dict[str, Any] = field(default_factory=dict)
    window_geometry: tuple[int, int, int, int | None] = None  # x, y, width, height
    splitter_states: dict[str, bytes] = field(default_factory=dict)

    # CS4Coding functional state
    map_center: tuple[float, float | None] = None
    map_zoom: int = 10
    exif_display_mode: str = "detailed"  # detailed, compact, minimal
    image_sort_mode: str = "name"  # name, date, size, type
    image_sort_ascending: bool = True

    # Image viewer state
    current_zoom: float = 1.0
    current_pan: tuple[int, int] = (0, 0)
    fit_mode: str = "fit_window"  # fit_window, fit_width, actual_size

    # Kiro integration state
    performance_mode: str = "balanced"  # performance, balanced, quality
    cache_status: dict[str, Any] = field(default_factory=dict)
    ai_component_status: dict[str, str] = field(
        default_factory=lambda: {
            "copilot": "active",
            "cursor": "active",
            "kiro": "active",
        }
    )

    # Session information
    session_start: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    images_processed: int = 0
    operations_performed: list[str] = field(default_factory=list)

    # Error tracking
    recent_errors: list[dict[str, Any]] = field(default_factory=list)
    error_count: int = 0

    # Performance metrics
    memory_usage_history: list[tuple[datetime, float]] = field(default_factory=list)
    operation_times: dict[str, list[float]] = field(default_factory=dict)

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def add_to_history(self, path: Path, max_history: int = 20):
        """Add path to folder history"""
        if path in self.folder_history:
            self.folder_history.remove(path)
        self.folder_history.insert(0, path)
        self.folder_history = self.folder_history[:max_history]

    def record_operation(self, operation: str, duration: float):
        """Record operation performance"""
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(duration)
        # Keep only last 100 measurements
        self.operation_times[operation] = self.operation_times[operation][-100:]

    def add_error(self, error: dict[str, Any], max_errors: int = 50):
        """Add error to recent errors list"""
        error["timestamp"] = datetime.now()
        self.recent_errors.insert(0, error)
        self.recent_errors = self.recent_errors[:max_errors]
        self.error_count += 1

    @property
    def session_duration(self) -> float:
        """Get session duration in seconds"""
        return (datetime.now() - self.session_start).total_seconds()

    @property
    def average_operation_time(self) -> dict[str, float]:
        """Get average operation times"""
        return {operation: sum(times) / len(times) for operation, times in self.operation_times.items() if times}


@dataclass
class CacheEntry:
    """
    Cache entry model for Kiro caching system
    """

    key: str
    data: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: int | None = None  # Time to live

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl_seconds is None:
            return False

        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def access(self):
        """Mark cache entry as accessed"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class PerformanceMetrics:
    """
    Performance metrics model for Kiro monitoring
    """

    timestamp: datetime = field(default_factory=datetime.now)

    # Memory metrics
    memory_usage_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_available_mb: float = 0.0

    # CPU metrics
    cpu_usage_percent: float = 0.0
    cpu_cores: int = 1

    # Application metrics
    images_loaded: int = 0
    thumbnails_generated: int = 0
    maps_rendered: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # AI component metrics
    copilot_operations: int = 0
    cursor_operations: int = 0
    kiro_operations: int = 0

    # Response times (in milliseconds)
    avg_image_load_time: float = 0.0
    avg_thumbnail_time: float = 0.0
    avg_exif_parse_time: float = 0.0
    avg_map_render_time: float = 0.0

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

    @property
    def total_operations(self) -> int:
        """Calculate total AI operations"""
        return self.copilot_operations + self.cursor_operations + self.kiro_operations
