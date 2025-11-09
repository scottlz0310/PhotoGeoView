"""
Theme Integration Interfaces

Abstract interfaces for theme management system integration.
Defines contracts for theme managers, theme providers, and theme-aware components.

Author: Kiro AI Integration System
Requirements: 5.1, 5.2, 5.3
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from .theme_models import ThemeConfiguration, ThemeInfo


class IThemeProvider(ABC):
    """
    Abstract interface for theme providers

    Theme providers are responsible for loading, validating,
    and managing theme configurations from various sources.
    """

    @abstractmethod
    def get_available_themes(self) -> list[ThemeInfo]:
        """
        Get list of available themes

        Returns:
            List of theme information objects
        """
        pass

    @abstractmethod
    def load_theme(self, theme_name: str) -> ThemeConfiguration | None:
        """
        Load a specific theme configuration

        Args:
            theme_name: Name of the theme to load

        Returns:
            Theme configuration or None if not found
        """
        pass

    @abstractmethod
    def save_theme(self, theme: ThemeConfiguration) -> bool:
        """
        Save a theme configuration

        Args:
            theme: Theme configuration to save

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def delete_theme(self, theme_name: str) -> bool:
        """
        Delete a theme

        Args:
            theme_name: Name of the theme to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def validate_theme(self, theme: ThemeConfiguration) -> bool:
        """
        Validate a theme configuration

        Args:
            theme: Theme configuration to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def import_theme(self, file_path: Path) -> ThemeConfiguration | None:
        """
        Import a theme from file

        Args:
            file_path: Path to the theme file

        Returns:
            Imported theme configuration or None if failed
        """
        pass

    @abstractmethod
    def export_theme(self, theme_name: str, file_path: Path) -> bool:
        """
        Export a theme to file

        Args:
            theme_name: Name of the theme to export
            file_path: Path to save the theme file

        Returns:
            True if exported successfully, False otherwise
        """
        pass


class IThemeManager(ABC):
    """
    Abstract interface for theme management

    Theme managers coordinate theme application across the application,
    manage theme state, and handle theme change notifications.
    """

    @abstractmethod
    def get_current_theme(self) -> ThemeConfiguration | None:
        """
        Get the currently active theme

        Returns:
            Current theme configuration or None if no theme is active
        """
        pass

    @abstractmethod
    def apply_theme(self, theme_name: str) -> bool:
        """
        Apply a theme to the application

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme applied successfully, False otherwise
        """
        pass

    @abstractmethod
    def register_component(self, component: "IThemeAware") -> bool:
        """
        Register a component for theme updates

        Args:
            component: Theme-aware component to register

        Returns:
            True if registered successfully, False otherwise
        """
        pass

    @abstractmethod
    def unregister_component(self, component: "IThemeAware") -> bool:
        """
        Unregister a component from theme updates

        Args:
            component: Component to unregister

        Returns:
            True if unregistered successfully, False otherwise
        """
        pass

    @abstractmethod
    def add_theme_change_listener(self, callback: Callable[[str, str], None]) -> bool:
        """
        Add a theme change listener

        Args:
            callback: Callback function (old_theme, new_theme) -> None

        Returns:
            True if listener added successfully, False otherwise
        """
        pass

    @abstractmethod
    def remove_theme_change_listener(self, callback: Callable[[str, str], None]) -> bool:
        """
        Remove a theme change listener

        Args:
            callback: Callback function to remove

        Returns:
            True if listener removed successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_theme_property(self, property_path: str, default: Any = None) -> Any:
        """
        Get a theme property value

        Args:
            property_path: Dot-separated path to the property (e.g., "colors.primary")
            default: Default value if property not found

        Returns:
            Property value or default
        """
        pass

    @abstractmethod
    def reload_themes(self) -> bool:
        """
        Reload all available themes

        Returns:
            True if reloaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def reset_to_default(self) -> bool:
        """
        Reset to default theme

        Returns:
            True if reset successfully, False otherwise
        """
        pass


class IThemeAware(Protocol):
    """
    Protocol for theme-aware components

    Components that implement this protocol can receive
    theme change notifications and update their appearance.
    """

    def apply_theme(self, theme: ThemeConfiguration) -> None:
        """
        Apply a theme to the component

        Args:
            theme: Theme configuration to apply
        """
        ...

    def get_theme_properties(self) -> list[str]:
        """
        Get list of theme properties used by this component

        Returns:
            List of property paths used by the component
        """
        ...


class IThemeValidator(ABC):
    """
    Abstract interface for theme validation

    Theme validators ensure theme configurations are valid
    and compatible with the application requirements.
    """

    @abstractmethod
    def validate_theme_structure(self, theme: ThemeConfiguration) -> list[str]:
        """
        Validate theme structure and required fields

        Args:
            theme: Theme configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def validate_color_scheme(self, theme: ThemeConfiguration) -> list[str]:
        """
        Validate theme color scheme

        Args:
            theme: Theme configuration to validate

        Returns:
            List of color validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def validate_fonts(self, theme: ThemeConfiguration) -> list[str]:
        """
        Validate theme font configuration

        Args:
            theme: Theme configuration to validate

        Returns:
            List of font validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def validate_accessibility(self, theme: ThemeConfiguration) -> list[str]:
        """
        Validate theme accessibility compliance

        Args:
            theme: Theme configuration to validate

        Returns:
            List of accessibility issues (empty if compliant)
        """
        pass

    @abstractmethod
    def validate_compatibility(self, theme: ThemeConfiguration) -> list[str]:
        """
        Validate theme compatibility with current system

        Args:
            theme: Theme configuration to validate

        Returns:
            List of compatibility issues (empty if compatible)
        """
        pass


class IThemeStorage(ABC):
    """
    Abstract interface for theme storage

    Theme storage implementations handle persistence
    of theme configurations and user preferences.
    """

    @abstractmethod
    def load_theme_config(self, theme_name: str) -> ThemeConfiguration | None:
        """
        Load theme configuration from storage

        Args:
            theme_name: Name of the theme to load

        Returns:
            Theme configuration or None if not found
        """
        pass

    @abstractmethod
    def save_theme_config(self, theme: ThemeConfiguration) -> bool:
        """
        Save theme configuration to storage

        Args:
            theme: Theme configuration to save

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def delete_theme_config(self, theme_name: str) -> bool:
        """
        Delete theme configuration from storage

        Args:
            theme_name: Name of the theme to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def list_available_themes(self) -> list[str]:
        """
        List all available theme names in storage

        Returns:
            List of theme names
        """
        pass

    @abstractmethod
    def theme_exists(self, theme_name: str) -> bool:
        """
        Check if a theme exists in storage

        Args:
            theme_name: Name of the theme to check

        Returns:
            True if theme exists, False otherwise
        """
        pass

    @abstractmethod
    def get_theme_metadata(self, theme_name: str) -> dict[str, Any] | None:
        """
        Get theme metadata without loading full configuration

        Args:
            theme_name: Name of the theme

        Returns:
            Theme metadata dictionary or None if not found
        """
        pass

    @abstractmethod
    def backup_themes(self, backup_path: Path) -> bool:
        """
        Create backup of all themes

        Args:
            backup_path: Path to save backup

        Returns:
            True if backup created successfully, False otherwise
        """
        pass

    @abstractmethod
    def restore_themes(self, backup_path: Path) -> bool:
        """
        Restore themes from backup

        Args:
            backup_path: Path to backup file

        Returns:
            True if restored successfully, False otherwise
        """
        pass


class IThemeRenderer(ABC):
    """
    Abstract interface for theme rendering

    Theme renderers convert theme configurations into
    platform-specific styling (CSS, Qt stylesheets, etc.).
    """

    @abstractmethod
    def render_stylesheet(self, theme: ThemeConfiguration) -> str:
        """
        Render theme as stylesheet

        Args:
            theme: Theme configuration to render

        Returns:
            Stylesheet string
        """
        pass

    @abstractmethod
    def render_css_variables(self, theme: ThemeConfiguration) -> str:
        """
        Render theme as CSS custom properties

        Args:
            theme: Theme configuration to render

        Returns:
            CSS variables string
        """
        pass

    @abstractmethod
    def render_component_styles(self, theme: ThemeConfiguration, component_type: str) -> dict[str, str]:
        """
        Render styles for a specific component type

        Args:
            theme: Theme configuration to render
            component_type: Type of component to render styles for

        Returns:
            Dictionary of style properties
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported rendering formats

        Returns:
            List of format names (e.g., ["css", "qss", "json"])
        """
        pass

    @abstractmethod
    def validate_rendering(self, theme: ThemeConfiguration, format_type: str) -> list[str]:
        """
        Validate that theme can be rendered in specified format

        Args:
            theme: Theme configuration to validate
            format_type: Target rendering format

        Returns:
            List of rendering issues (empty if valid)
        """
        pass


class IThemeCache(ABC):
    """
    Abstract interface for theme caching

    Theme caches improve performance by storing rendered
    themes and avoiding repeated processing.
    """

    @abstractmethod
    def get_cached_theme(self, theme_name: str, cache_key: str) -> Any | None:
        """
        Get cached theme data

        Args:
            theme_name: Name of the theme
            cache_key: Cache key for specific rendering/format

        Returns:
            Cached data or None if not found
        """
        pass

    @abstractmethod
    def cache_theme(self, theme_name: str, cache_key: str, data: Any, ttl: int | None = None) -> bool:
        """
        Cache theme data

        Args:
            theme_name: Name of the theme
            cache_key: Cache key for specific rendering/format
            data: Data to cache
            ttl: Time to live in seconds (None for no expiration)

        Returns:
            True if cached successfully, False otherwise
        """
        pass

    @abstractmethod
    def invalidate_theme_cache(self, theme_name: str) -> bool:
        """
        Invalidate all cached data for a theme

        Args:
            theme_name: Name of the theme to invalidate

        Returns:
            True if invalidated successfully, False otherwise
        """
        pass

    @abstractmethod
    def clear_cache(self) -> bool:
        """
        Clear all cached theme data

        Returns:
            True if cleared successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        pass


# Type aliases for convenience
ThemeChangeCallback = Callable[[str, str], None]  # (old_theme, new_theme) -> None
ThemePropertyPath = str  # Dot-separated property path like "colors.primary"
ThemeRenderFormat = str  # Rendering format like "css", "qss", "json"
