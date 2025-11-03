"""
Navigation Integration Interfaces

Abstract interfaces for breadcrumb navigation system integration.
Defines contracts for navigation managers, path providers, and navigation-aware components.

Author: Kiro AI Integration System
Requirements: 5.1, 5.2, 5.3
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

from .navigation_models import (
    BreadcrumbSegment,
    NavigationEvent,
    NavigationState,
    PathInfo,
)


class INavigationProvider(ABC):
    """
    Abstract interface for navigation providers

    Navigation providers handle path resolution, validation,
    and file system interaction for navigation operations.
    """

    @abstractmethod
    def resolve_path(self, path: Union[str, Path]) -> Optional[Path]:
        """
        Resolve a path to its canonical form

        Args:
            path: Path to resolve

        Returns:
            Resolved path or None if invalid
        """
        pass

    @abstractmethod
    def validate_path(self, path: Path) -> bool:
        """
        Validate if a path is accessible for navigation

        Args:
            path: Path to validate

        Returns:
            True if path is valid and accessible, False otherwise
        """
        pass

    @abstractmethod
    def get_path_info(self, path: Path) -> Optional[PathInfo]:
        """
        Get detailed information about a path

        Args:
            path: Path to analyze

        Returns:
            Path information or None if path is invalid
        """
        pass

    @abstractmethod
    def get_parent_path(self, path: Path) -> Optional[Path]:
        """
        Get the parent path of the given path

        Args:
            path: Path to get parent for

        Returns:
            Parent path or None if no parent exists
        """
        pass

    @abstractmethod
    def list_child_paths(self, path: Path) -> List[Path]:
        """
        List child paths (directories) under the given path

        Args:
            path: Parent path to list children for

        Returns:
            List of child directory paths
        """
        pass

    @abstractmethod
    def watch_path(self, path: Path, callback: Callable[[Path, str], None]) -> bool:
        """
        Start watching a path for changes

        Args:
            path: Path to watch
            callback: Callback function (path, event_type) -> None

        Returns:
            True if watching started successfully, False otherwise
        """
        pass

    @abstractmethod
    def unwatch_path(self, path: Path) -> bool:
        """
        Stop watching a path for changes

        Args:
            path: Path to stop watching

        Returns:
            True if watching stopped successfully, False otherwise
        """
        pass


class INavigationManager(ABC):
    """
    Abstract interface for navigation management

    Navigation managers coordinate navigation state, handle
    navigation events, and manage breadcrumb display.
    """

    @abstractmethod
    def get_current_state(self) -> NavigationState:
        """
        Get the current navigation state

        Returns:
            Current navigation state
        """
        pass

    @abstractmethod
    def navigate_to_path(self, path: Path) -> bool:
        """
        Navigate to a specific path

        Args:
            path: Target path to navigate to

        Returns:
            True if navigation successful, False otherwise
        """
        pass

    @abstractmethod
    def navigate_to_segment(self, segment_index: int) -> bool:
        """
        Navigate to a specific breadcrumb segment

        Args:
            segment_index: Index of the segment to navigate to

        Returns:
            True if navigation successful, False otherwise
        """
        pass

    @abstractmethod
    def go_back(self) -> bool:
        """
        Navigate backward in history

        Returns:
            True if navigation successful, False otherwise
        """
        pass

    @abstractmethod
    def go_forward(self) -> bool:
        """
        Navigate forward in history

        Returns:
            True if navigation successful, False otherwise
        """
        pass

    @abstractmethod
    def go_up(self) -> bool:
        """
        Navigate to parent directory

        Returns:
            True if navigation successful, False otherwise
        """
        pass

    @abstractmethod
    def refresh(self) -> bool:
        """
        Refresh current navigation state

        Returns:
            True if refresh successful, False otherwise
        """
        pass

    @abstractmethod
    def add_navigation_listener(
        self, callback: Callable[[NavigationEvent], None]
    ) -> bool:
        """
        Add a navigation event listener

        Args:
            callback: Callback function for navigation events

        Returns:
            True if listener added successfully, False otherwise
        """
        pass

    @abstractmethod
    def remove_navigation_listener(
        self, callback: Callable[[NavigationEvent], None]
    ) -> bool:
        """
        Remove a navigation event listener

        Args:
            callback: Callback function to remove

        Returns:
            True if listener removed successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_navigation_history(self) -> List[Path]:
        """
        Get navigation history

        Returns:
            List of paths in navigation history
        """
        pass

    @abstractmethod
    def clear_history(self) -> bool:
        """
        Clear navigation history

        Returns:
            True if history cleared successfully, False otherwise
        """
        pass


class IBreadcrumbRenderer(ABC):
    """
    Abstract interface for breadcrumb rendering

    Breadcrumb renderers handle the visual representation
    of breadcrumb segments and navigation state.
    """

    @abstractmethod
    def render_breadcrumb(self, state: NavigationState) -> Any:
        """
        Render breadcrumb navigation from state

        Args:
            state: Navigation state to render

        Returns:
            Rendered breadcrumb widget/component
        """
        pass

    @abstractmethod
    def render_segment(self, segment: BreadcrumbSegment) -> Any:
        """
        Render a single breadcrumb segment

        Args:
            segment: Segment to render

        Returns:
            Rendered segment widget/component
        """
        pass

    @abstractmethod
    def update_segment_state(self, segment: BreadcrumbSegment, widget: Any) -> None:
        """
        Update the visual state of a rendered segment

        Args:
            segment: Segment with updated state
            widget: Rendered segment widget to update
        """
        pass

    @abstractmethod
    def set_truncation_mode(self, mode: str) -> None:
        """
        Set the truncation mode for long paths

        Args:
            mode: Truncation mode ("smart", "middle", "end", "none")
        """
        pass

    @abstractmethod
    def set_max_segments(self, max_segments: int) -> None:
        """
        Set maximum number of visible segments

        Args:
            max_segments: Maximum number of segments to display
        """
        pass

    @abstractmethod
    def get_segment_at_position(
        self, position: Tuple[int, int]
    ) -> Optional[BreadcrumbSegment]:
        """
        Get the segment at a specific screen position

        Args:
            position: Screen position (x, y)

        Returns:
            Segment at position or None if no segment found
        """
        pass


class INavigationAware(Protocol):
    """
    Protocol for navigation-aware components

    Components that implement this protocol can receive
    navigation change notifications and update accordingly.
    """

    def on_navigation_changed(self, event: NavigationEvent) -> None:
        """
        Handle navigation change event

        Args:
            event: Navigation event data
        """
        ...

    def get_supported_navigation_events(self) -> List[str]:
        """
        Get list of navigation event types supported by this component

        Returns:
            List of event type names
        """
        ...


class IPathValidator(ABC):
    """
    Abstract interface for path validation

    Path validators ensure paths are valid, accessible,
    and safe for navigation operations.
    """

    @abstractmethod
    def validate_path_format(self, path: Union[str, Path]) -> bool:
        """
        Validate path format and syntax

        Args:
            path: Path to validate

        Returns:
            True if format is valid, False otherwise
        """
        pass

    @abstractmethod
    def validate_path_access(self, path: Path) -> bool:
        """
        Validate path accessibility

        Args:
            path: Path to validate

        Returns:
            True if path is accessible, False otherwise
        """
        pass

    @abstractmethod
    def validate_path_security(self, path: Path) -> bool:
        """
        Validate path security (no traversal attacks, etc.)

        Args:
            path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        pass

    @abstractmethod
    def get_validation_errors(self, path: Path) -> List[str]:
        """
        Get detailed validation errors for a path

        Args:
            path: Path to validate

        Returns:
            List of validation error messages
        """
        pass

    @abstractmethod
    def sanitize_path(self, path: Union[str, Path]) -> Optional[Path]:
        """
        Sanitize and normalize a path

        Args:
            path: Path to sanitize

        Returns:
            Sanitized path or None if path cannot be sanitized
        """
        pass


class IFileSystemWatcher(ABC):
    """
    Abstract interface for file system watching

    File system watchers monitor path changes and notify
    navigation components of relevant file system events.
    """

    @abstractmethod
    def start_watching(self) -> bool:
        """
        Start file system watching

        Returns:
            True if watching started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop_watching(self) -> bool:
        """
        Stop file system watching

        Returns:
            True if watching stopped successfully, False otherwise
        """
        pass

    @abstractmethod
    def add_watch_path(self, path: Path, recursive: bool = False) -> bool:
        """
        Add a path to watch for changes

        Args:
            path: Path to watch
            recursive: Whether to watch subdirectories recursively

        Returns:
            True if path added successfully, False otherwise
        """
        pass

    @abstractmethod
    def remove_watch_path(self, path: Path) -> bool:
        """
        Remove a path from watching

        Args:
            path: Path to stop watching

        Returns:
            True if path removed successfully, False otherwise
        """
        pass

    @abstractmethod
    def add_event_handler(self, callback: Callable[[Path, str, str], None]) -> bool:
        """
        Add file system event handler

        Args:
            callback: Callback function (path, event_type, details) -> None

        Returns:
            True if handler added successfully, False otherwise
        """
        pass

    @abstractmethod
    def remove_event_handler(self, callback: Callable[[Path, str, str], None]) -> bool:
        """
        Remove file system event handler

        Args:
            callback: Callback function to remove

        Returns:
            True if handler removed successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_watched_paths(self) -> List[Path]:
        """
        Get list of currently watched paths

        Returns:
            List of watched paths
        """
        pass

    @abstractmethod
    def is_watching(self, path: Path) -> bool:
        """
        Check if a path is being watched

        Args:
            path: Path to check

        Returns:
            True if path is being watched, False otherwise
        """
        pass


class INavigationHistory(ABC):
    """
    Abstract interface for navigation history management

    Navigation history managers handle storage and retrieval
    of navigation history for back/forward functionality.
    """

    @abstractmethod
    def add_to_history(self, path: Path) -> None:
        """
        Add a path to navigation history

        Args:
            path: Path to add to history
        """
        pass

    @abstractmethod
    def get_history(self) -> List[Path]:
        """
        Get complete navigation history

        Returns:
            List of paths in history order (most recent first)
        """
        pass

    @abstractmethod
    def get_back_history(self) -> List[Path]:
        """
        Get backward navigation history

        Returns:
            List of paths available for backward navigation
        """
        pass

    @abstractmethod
    def get_forward_history(self) -> List[Path]:
        """
        Get forward navigation history

        Returns:
            List of paths available for forward navigation
        """
        pass

    @abstractmethod
    def can_go_back(self) -> bool:
        """
        Check if backward navigation is possible

        Returns:
            True if can go back, False otherwise
        """
        pass

    @abstractmethod
    def can_go_forward(self) -> bool:
        """
        Check if forward navigation is possible

        Returns:
            True if can go forward, False otherwise
        """
        pass

    @abstractmethod
    def go_back(self) -> Optional[Path]:
        """
        Get the previous path in history

        Returns:
            Previous path or None if no previous path
        """
        pass

    @abstractmethod
    def go_forward(self) -> Optional[Path]:
        """
        Get the next path in history

        Returns:
            Next path or None if no next path
        """
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """Clear all navigation history"""
        pass

    @abstractmethod
    def set_max_history_size(self, size: int) -> None:
        """
        Set maximum history size

        Args:
            size: Maximum number of paths to keep in history
        """
        pass

    @abstractmethod
    def save_history(self, file_path: Path) -> bool:
        """
        Save history to file

        Args:
            file_path: Path to save history file

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def load_history(self, file_path: Path) -> bool:
        """
        Load history from file

        Args:
            file_path: Path to history file

        Returns:
            True if loaded successfully, False otherwise
        """
        pass


class INavigationCache(ABC):
    """
    Abstract interface for navigation caching

    Navigation caches improve performance by storing
    path information and reducing file system queries.
    """

    @abstractmethod
    def get_cached_path_info(self, path: Path) -> Optional[PathInfo]:
        """
        Get cached path information

        Args:
            path: Path to get cached info for

        Returns:
            Cached path info or None if not cached
        """
        pass

    @abstractmethod
    def cache_path_info(
        self, path: Path, info: PathInfo, ttl: Optional[int] = None
    ) -> bool:
        """
        Cache path information

        Args:
            path: Path to cache info for
            info: Path information to cache
            ttl: Time to live in seconds (None for no expiration)

        Returns:
            True if cached successfully, False otherwise
        """
        pass

    @abstractmethod
    def invalidate_path_cache(self, path: Path) -> bool:
        """
        Invalidate cached information for a path

        Args:
            path: Path to invalidate cache for

        Returns:
            True if invalidated successfully, False otherwise
        """
        pass

    @abstractmethod
    def clear_cache(self) -> bool:
        """
        Clear all cached path information

        Returns:
            True if cleared successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        pass

    @abstractmethod
    def preload_path_info(self, paths: List[Path]) -> int:
        """
        Preload path information for multiple paths

        Args:
            paths: List of paths to preload

        Returns:
            Number of paths successfully preloaded
        """
        pass


# Type aliases for convenience
NavigationCallback = Callable[[NavigationEvent], None]  # Navigation event callback
PathChangeCallback = Callable[
    [Path, str], None
]  # Path change callback (path, event_type)
FileSystemEventCallback = Callable[
    [Path, str, str], None
]  # FS event callback (path, event_type, details)
PositionTuple = Tuple[int, int]  # Screen position (x, y)
TruncationMode = str  # Truncation mode ("smart", "middle", "end", "none")
