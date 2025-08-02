"""
Theme and Navigation Integration Interfaces

Integration interfaces that combine theme management and navigation functionality.
Provides unified interfaces for components that need both theme and navigation awareness.

Author: Kiro AI Integration System
Requirements: 5.1, 5.2, 5.3
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

from .navigation_models import NavigationEvent, NavigationState
from .theme_models import ThemeConfiguration
from .navigation_interfaces import INavigationAware
from .theme_interfaces import IThemeAware


class IThemeNavigationIntegration(ABC):
    """
    Abstract interface for integrated theme and navigation management

    This interface provides unified access to both theme and navigation
    functionality for components that need both capabilities.
    """

    @abstractmethod
    def get_current_theme(self) -> Optional[ThemeConfiguration]:
        """
        Get the currently active theme

        Returns:
            Current theme configuration or None if no theme is active
        """
        pass

    @abstractmethod
    def get_navigation_state(self) -> NavigationState:
        """
        Get the current navigation state

        Returns:
            Current navigation state
        """
        pass

    @abstractmethod
    def apply_theme_to_navigation(self, theme: ThemeConfiguration) -> bool:
        """
        Apply theme styling to navigation components

        Args:
            theme: Theme configuration to apply

        Returns:
            True if theme applied successfully, False otherwise
        """
        pass

    @abstractmethod
    def register_integrated_component(self, component: 'IThemeNavigationAware') -> bool:
        """
        Register a component that needs both theme and navigation updates

        Args:
            component: Component to register

        Returns:
            True if registered successfully, False otherwise
        """
        pass

    @abstractmethod
    def unregister_integrated_component(self, component: 'IThemeNavigationAware') -> bool:
        """
        Unregister an integrated component

        Args:
            component: Component to unregister

        Returns:
            True if unregistered successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_themed_navigation_styles(self) -> Dict[str, str]:
        """
        Get navigation-specific styles from current theme

        Returns:
            Dictionary of navigation style properties
        """
        pass

    @abstractmethod
    def update_navigation_theme_properties(self, properties: Dict[str, Any]) -> bool:
        """
        Update theme properties specific to navigation components

        Args:
            properties: Theme properties to update

        Returns:
            True if updated successfully, False otherwise
        """
        pass


class IThemeNavigationAware(IThemeAware, INavigationAware, Protocol):
    """
    Protocol for components that are aware of both theme and navigation changes

    Components implementing this protocol receive notifications for both
    theme changes and navigation events, allowing for coordinated updates.
    """

    def apply_theme(self, theme: ThemeConfiguration) -> None:
        """
        Apply a theme to the component

        Args:
            theme: Theme configuration to apply
        """
        ...

    def on_navigation_changed(self, event: NavigationEvent) -> None:
        """
        Handle navigation change event

        Args:
            event: Navigation event data
        """
        ...

    def update_integrated_state(self, theme: ThemeConfiguration, nav_state: NavigationState) -> None:
        """
        Update component state with both theme and navigation information

        Args:
            theme: Current theme configuration
            nav_state: Current navigation state
        """
        ...

    def get_integration_requirements(self) -> Dict[str, List[str]]:
        """
        Get integration requirements for this component

        Returns:
            Dictionary with 'theme' and 'navigation' keys containing
            lists of required properties/events
        """
        ...


class IBreadcrumbThemeProvider(ABC):
    """
    Abstract interface for breadcrumb-specific theme provision

    Provides theme properties and styling specifically for
    breadcrumb navigation components.
    """

    @abstractmethod
    def get_breadcrumb_colors(self, theme: ThemeConfiguration) -> Dict[str, str]:
        """
        Get breadcrumb-specific colors from theme

        Args:
            theme: Theme configuration

        Returns:
            Dictionary of breadcrumb color properties
        """
        pass

    @abstractmethod
    def get_breadcrumb_fonts(self, theme: ThemeConfiguration) -> Dict[str, str]:
        """
        Get breadcrumb-specific fonts from theme

        Args:
            theme: Theme configuration

        Returns:
            Dictionary of breadcrumb font properties
        """
        pass

    @abstractmethod
    def get_breadcrumb_spacing(self, theme: ThemeConfiguration) -> Dict[str, int]:
        """
        Get breadcrumb-specific spacing from theme

        Args:
            theme: Theme configuration

        Returns:
            Dictionary of breadcrumb spacing properties
        """
        pass

    @abstractmethod
    def get_breadcrumb_icons(self, theme: ThemeConfiguration) -> Dict[str, str]:
        """
        Get breadcrumb-specific icons from theme

        Args:
            theme: Theme configuration

        Returns:
            Dictionary of breadcrumb icon properties
        """
        pass

    @abstractmethod
    def get_segment_styles(self, theme: ThemeConfiguration, segment_state: str) -> Dict[str, str]:
        """
        Get styles for breadcrumb segments based on state

        Args:
            theme: Theme configuration
            segment_state: State of the segment (normal, current, hover, etc.)

        Returns:
            Dictionary of segment style properties
        """
        pass

    @abstractmethod
    def get_separator_styles(self, theme: ThemeConfiguration) -> Dict[str, str]:
        """
        Get styles for breadcrumb separators

        Args:
            theme: Theme configuration

        Returns:
            Dictionary of separator style properties
        """
        pass


class INavigationThemeRenderer(ABC):
    """
    Abstract interface for rendering navigation components with theme support

    Handles the visual rendering of navigation elements with
    proper theme integration and styling.
    """

    @abstractmethod
    def render_themed_breadcrumb(self, nav_state: NavigationState, theme: ThemeConfiguration) -> Any:
        """
        Render breadcrumb navigation with theme styling

        Args:
            nav_state: Navigation state to render
            theme: Theme configuration for styling

        Returns:
            Rendered breadcrumb widget with theme applied
        """
        pass

    @abstractmethod
    def render_themed_segment(self, segment, theme: ThemeConfiguration) -> Any:
        """
        Render a single breadcrumb segment with theme styling

        Args:
            segment: Breadcrumb segment to render
            theme: Theme configuration for styling

        Returns:
            Rendered segment widget with theme applied
        """
        pass

    @abstractmethod
    def update_theme_styling(self, widget: Any, theme: ThemeConfiguration) -> None:
        """
        Update theme styling on an existing widget

        Args:
            widget: Widget to update
            theme: New theme configuration
        """
        pass

    @abstractmethod
    def get_theme_dependent_properties(self) -> List[str]:
        """
        Get list of properties that depend on theme

        Returns:
            List of theme-dependent property names
        """
        pass

    @abstractmethod
    def validate_theme_compatibility(self, theme: ThemeConfiguration) -> List[str]:
        """
        Validate theme compatibility with navigation rendering

        Args:
            theme: Theme configuration to validate

        Returns:
            List of compatibility issues (empty if compatible)
        """
        pass


class IIntegratedEventManager(ABC):
    """
    Abstract interface for managing integrated theme and navigation events

    Coordinates event handling between theme and navigation systems
    to ensure proper synchronization and avoid conflicts.
    """

    @abstractmethod
    def add_integrated_listener(self, callback: 'IntegratedEventCallback') -> bool:
        """
        Add listener for integrated theme/navigation events

        Args:
            callback: Callback function for integrated events

        Returns:
            True if listener added successfully, False otherwise
        """
        pass

    @abstractmethod
    def remove_integrated_listener(self, callback: 'IntegratedEventCallback') -> bool:
        """
        Remove integrated event listener

        Args:
            callback: Callback function to remove

        Returns:
            True if listener removed successfully, False otherwise
        """
        pass

    @abstractmethod
    def emit_theme_navigation_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit an integrated theme/navigation event

        Args:
            event_type: Type of event to emit
            data: Event data dictionary
        """
        pass

    @abstractmethod
    def get_event_history(self) -> List[Dict[str, Any]]:
        """
        Get history of integrated events

        Returns:
            List of event data dictionaries
        """
        pass

    @abstractmethod
    def clear_event_history(self) -> None:
        """Clear integrated event history"""
        pass


class IConfigurationIntegration(ABC):
    """
    Abstract interface for integrated configuration management

    Manages configuration settings that affect both theme
    and navigation functionality.
    """

    @abstractmethod
    def get_integration_config(self) -> Dict[str, Any]:
        """
        Get integrated configuration settings

        Returns:
            Dictionary of integration configuration
        """
        pass

    @abstractmethod
    def set_integration_config(self, config: Dict[str, Any]) -> bool:
        """
        Set integrated configuration settings

        Args:
            config: Configuration dictionary to set

        Returns:
            True if configuration set successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_theme_navigation_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences for theme/navigation integration

        Returns:
            Dictionary of user preferences
        """
        pass

    @abstractmethod
    def set_theme_navigation_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Set user preferences for theme/navigation integration

        Args:
            preferences: Preferences dictionary to set

        Returns:
            True if preferences set successfully, False otherwise
        """
        pass

    @abstractmethod
    def validate_integration_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate integration configuration

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def reset_integration_config(self) -> bool:
        """
        Reset integration configuration to defaults

        Returns:
            True if reset successfully, False otherwise
        """
        pass


class IPerformanceIntegration(ABC):
    """
    Abstract interface for integrated performance monitoring

    Monitors performance of integrated theme and navigation
    operations to identify bottlenecks and optimization opportunities.
    """

    @abstractmethod
    def start_performance_monitoring(self) -> bool:
        """
        Start integrated performance monitoring

        Returns:
            True if monitoring started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop_performance_monitoring(self) -> bool:
        """
        Stop integrated performance monitoring

        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_integration_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for integration operations

        Returns:
            Dictionary of performance metrics
        """
        pass

    @abstractmethod
    def log_integration_operation(self, operation: str, duration: float, details: Dict[str, Any]) -> None:
        """
        Log performance data for an integration operation

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            details: Additional operation details
        """
        pass

    @abstractmethod
    def get_performance_recommendations(self) -> List[str]:
        """
        Get performance optimization recommendations

        Returns:
            List of performance recommendations
        """
        pass

    @abstractmethod
    def clear_performance_data(self) -> bool:
        """
        Clear collected performance data

        Returns:
            True if data cleared successfully, False otherwise
        """
        pass


# Type aliases for convenience
IntegratedEventCallback = Callable[[str, Dict[str, Any]], None]  # (event_type, data) -> None
ThemeNavigationConfig = Dict[str, Any]  # Configuration dictionary
IntegrationMetrics = Dict[str, Any]  # Performance metrics dictionary
StyleProperties = Dict[str, str]  # Style property dictionary
