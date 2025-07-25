"""
Core Interfaces for AI Integration

Defines abstract interfaces that unify implementations from different AI agents:
- GitHub Copilot (CS4Coding): Core functionality focus
- Cursor (CursorBLD): UI/UX focus
- Kiro: Integration and quality assurance focus

Author: Kiro AI Integration System
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime


class IImageProcessor(ABC):
    """
    Unified interface for image processing operations
    Combines CS4Coding's robust image handling with Kiro's optimization
    """

    @abstractmethod
    def load_image(self, path: Path) -> Optional[Any]:
        """
        Load an image from the specified path

        Args:
            path: Path to the image file

        Returns:
            Loaded image object or None if failed
        """
        pass

    @abstractmethod
    def generate_thumbnail(self, image: Any, size: Tuple[int, int]) -> Optional[Any]:
        """
        Generate a thumbnail from the given image

        Args:
            image: Source image object
            size: Desired thumbnail size (width, height)

        Returns:
            Thumbnail image object or None if failed
        """
        pass

    @abstractmethod
    def extract_exif(self, path: Path) -> Dict[str, Any]:
        """
        Extract EXIF metadata from image file

        Args:
            path: Path to the image file

        Returns:
            Dictionary containing EXIF data
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported image formats

        Returns:
            List of supported file extensions
        """
        pass

    @abstractmethod
    def validate_image(self, path: Path) -> bool:
        """
        Validate if the file is a supported image

        Args:
            path: Path to validate

        Returns:
            True if valid image, False otherwise
        """
        pass


class IThemeManager(ABC):
    """
    Unified interface for theme management
    Based on CursorBLD's Qt-Theme-Manager integration with Kiro enhancements
    """

    @abstractmethod
    def get_available_themes(self) -> List[str]:
        """
        Get list of available theme names

        Returns:
            List of theme identifiers
        """
        pass

    @abstractmethod
    def apply_theme(self, theme_name: str) -> bool:
        """
        Apply the specified theme to the application

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme applied successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_theme_config(self, theme_name: str) -> Dict[str, Any]:
        """
        Get configuration for the specified theme

        Args:
            theme_name: Name of the theme

        Returns:
            Theme configuration dictionary
        """
        pass

    @abstractmethod
    def get_current_theme(self) -> str:
        """
        Get the currently active theme name

        Returns:
            Current theme identifier
        """
        pass

    @abstractmethod
    def create_custom_theme(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Create a new custom theme

        Args:
            name: Name for the new theme
            config: Theme configuration

        Returns:
            True if theme created successfully, False otherwise
        """
        pass

    @abstractmethod
    def validate_theme_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate theme configuration

        Args:
            config: Theme configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        pass


class IMapProvider(ABC):
    """
    Unified interface for map functionality
    Based on CS4Coding's stable folium integration with Kiro caching
    """

    @abstractmethod
    def create_map(self, center: Tuple[float, float], zoom: int = 10) -> Any:
        """
        Create a new map centered at the specified coordinates

        Args:
            center: (latitude, longitude) tuple for map center
            zoom: Initial zoom level

        Returns:
            Map object
        """
        pass

    @abstractmethod
    def add_marker(self, map_obj: Any, lat: float, lon: float, popup: str = "") -> None:
        """
        Add a marker to the map

        Args:
            map_obj: Map object to add marker to
            lat: Latitude of marker
            lon: Longitude of marker
            popup: Optional popup text for marker
        """
        pass

    @abstractmethod
    def render_html(self, map_obj: Any) -> str:
        """
        Render map as HTML string

        Args:
            map_obj: Map object to render

        Returns:
            HTML representation of the map
        """
        pass

    @abstractmethod
    def set_map_bounds(self, map_obj: Any, bounds: List[Tuple[float, float]]) -> None:
        """
        Set map bounds to fit all specified coordinates

        Args:
            map_obj: Map object to modify
            bounds: List of (latitude, longitude) tuples
        """
        pass

    @abstractmethod
    def add_image_overlay(self, map_obj: Any, image_path: Path, bounds: Tuple[Tuple[float, float], Tuple[float, float]]) -> None:
        """
        Add an image overlay to the map

        Args:
            map_obj: Map object to add overlay to
            image_path: Path to overlay image
            bounds: ((south, west), (north, east)) bounds for overlay
        """
        pass

    @abstractmethod
    def get_map_center(self, map_obj: Any) -> Tuple[float, float]:
        """
        Get current center coordinates of the map

        Args:
            map_obj: Map object to query

        Returns:
            (latitude, longitude) tuple of map center
        """
        pass

    @abstractmethod
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Validate GPS coordinates

        Args:
            lat: Latitude to validate
            lon: Longitude to validate

        Returns:
            True if coordinates are valid, False otherwise
        """
        pass


class IConfigManager(ABC):
    """
    Unified interface for configuration management
    Kiro-designed interface for managing settings across all AI implementations
    """

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration setting value

        Args:
            key: Setting key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a configuration setting value

        Args:
            key: Setting key (supports dot notation for nested keys)
            value: Value to set

        Returns:
            True if setting was saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_ai_config(self, ai_name: str) -> Dict[str, Any]:
        """
        Get configuration section for specific AI implementation

        Args:
            ai_name: Name of AI implementation (copilot, cursor, kiro)

        Returns:
            AI-specific configuration dictionary
        """
        pass

    @abstractmethod
    def save_config(self) -> bool:
        """
        Save current configuration to persistent storage

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def load_config(self) -> bool:
        """
        Load configuration from persistent storage

        Returns:
            True if loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values

        Returns:
            True if reset successfully, False otherwise
        """
        pass


class IPerformanceMonitor(ABC):
    """
    Unified interface for performance monitoring
    Kiro-designed interface for monitoring system performance and AI component health
    """

    @abstractmethod
    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        pass

    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        pass

    @abstractmethod
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage statistics

        Returns:
            Dictionary with memory usage metrics
        """
        pass

    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics

        Returns:
            Dictionary with performance data
        """
        pass

    @abstractmethod
    def log_operation_time(self, operation: str, duration: float) -> None:
        """
        Log the duration of an operation

        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        pass

    @abstractmethod
    def get_ai_component_status(self) -> Dict[str, str]:
        """
        Get status of all AI components

        Returns:
            Dictionary mapping AI component names to status strings
        """
        pass
