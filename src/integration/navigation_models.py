"""
Navigation State Models for Breadcrumb Functionality

Data models for breadcrumb address bar navigation state management.
Supports path tracking, segment management, and file system integration.

Author: Kiro AI Integration System
Requirements: 5.1, 5.2, 5.3
"""

import os
import platform
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PathType(Enum):
    """Path type enumeration"""

    LOCAL = "local"
    NETWORK = "network"
    REMOVABLE = "removable"
    VIRTUAL = "virtual"


class SegmentState(Enum):
    """Breadcrumb segment state enumeration"""

    NORMAL = "normal"
    CURRENT = "current"
    INACCESSIBLE = "inaccessible"
    LOADING = "loading"
    ERROR = "error"


class NavigationError(Exception):
    """Navigation-related error"""

    pass


@dataclass
class BreadcrumbSegment:
    """
    Individual breadcrumb segment data model

    Represents a single segment in the breadcrumb path with
    display information, navigation state, and accessibility data.
    """

    # Core segment data
    name: str
    path: Path
    display_name: str = ""

    # State information
    state: SegmentState = SegmentState.NORMAL
    is_clickable: bool = True
    is_accessible: bool = True

    # Visual information
    icon: Optional[str] = None
    tooltip: str = ""

    # Metadata
    segment_index: int = 0
    is_root: bool = False
    is_drive: bool = False

    # Performance data
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    def __post_init__(self):
        """Post-initialization setup"""
        # Set default display name
        if not self.display_name:
            if self.is_root:
                self.display_name = "Root"
            elif self.is_drive:
                self.display_name = str(self.path)
            else:
                self.display_name = self.name or self.path.name

        # Set default tooltip
        if not self.tooltip:
            self.tooltip = str(self.path)

        # Determine if this is a drive segment
        if platform.system() == "Windows":
            self.is_drive = len(str(self.path)) <= 3 and str(self.path).endswith(":\\")
        else:
            self.is_drive = str(self.path) == "/"

        # Set root flag
        self.is_root = self.is_drive

        # Set default icon based on segment type
        if not self.icon:
            self.icon = self._get_default_icon()

        # Validate accessibility
        self._validate_accessibility()

    def _get_default_icon(self) -> str:
        """Get default icon for the segment"""
        if self.is_drive:
            if platform.system() == "Windows":
                return "drive"
            else:
                return "root"
        elif not self.is_accessible:
            return "error"
        elif self.state == SegmentState.LOADING:
            return "loading"
        else:
            return "folder"

    def _validate_accessibility(self):
        """Validate if the path is accessible"""
        try:
            self.is_accessible = self.path.exists() and os.access(self.path, os.R_OK)
            if not self.is_accessible:
                self.state = SegmentState.INACCESSIBLE
                self.is_clickable = False
        except (OSError, PermissionError):
            self.is_accessible = False
            self.state = SegmentState.INACCESSIBLE
            self.is_clickable = False

    def update_access_info(self):
        """Update access information"""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def refresh_state(self):
        """Refresh the segment state"""
        self._validate_accessibility()
        self.icon = self._get_default_icon()

    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary"""
        return {
            "name": self.name,
            "path": str(self.path),
            "display_name": self.display_name,
            "state": self.state.value,
            "is_clickable": self.is_clickable,
            "is_accessible": self.is_accessible,
            "icon": self.icon,
            "tooltip": self.tooltip,
            "segment_index": self.segment_index,
            "is_root": self.is_root,
            "is_drive": self.is_drive,
            "access_count": self.access_count,
        }


@dataclass
class PathInfo:
    """
    Path information and metadata

    Contains detailed information about a path including
    type, accessibility, and system-specific properties.
    """

    path: Path
    path_type: PathType = PathType.LOCAL
    is_accessible: bool = True
    is_network_path: bool = False
    is_removable: bool = False

    # System information
    drive_letter: Optional[str] = None
    mount_point: Optional[str] = None
    file_system: Optional[str] = None

    # Capacity information
    total_space: Optional[int] = None
    free_space: Optional[int] = None
    used_space: Optional[int] = None

    # Metadata
    last_checked: Optional[datetime] = None
    check_count: int = 0

    def __post_init__(self):
        """Post-initialization analysis"""
        self._analyze_path()

    def _analyze_path(self):
        """Analyze path properties"""
        try:
            path_str = str(self.path)

            # Determine path type
            if platform.system() == "Windows":
                if path_str.startswith("\\\\"):
                    self.path_type = PathType.NETWORK
                    self.is_network_path = True
                elif len(path_str) >= 2 and path_str[1] == ":":
                    self.drive_letter = path_str[0].upper()
                    self.path_type = PathType.LOCAL

                    # Check if removable drive
                    try:
                        import win32file

                        drive_type = win32file.GetDriveType(f"{self.drive_letter}:\\")
                        self.is_removable = drive_type in [
                            win32file.DRIVE_REMOVABLE,
                            win32file.DRIVE_CDROM,
                        ]
                        if self.is_removable:
                            self.path_type = PathType.REMOVABLE
                    except ImportError:
                        # Fallback without win32file
                        pass
            else:
                # Unix-like systems
                if path_str.startswith("/mnt/") or path_str.startswith("/media/"):
                    self.path_type = PathType.REMOVABLE
                    self.is_removable = True
                elif path_str.startswith("/proc/") or path_str.startswith("/sys/"):
                    self.path_type = PathType.VIRTUAL
                else:
                    self.path_type = PathType.LOCAL

            # Check accessibility
            self.is_accessible = self.path.exists() and os.access(self.path, os.R_OK)

            # Get disk usage information
            if self.is_accessible and self.path.exists():
                try:
                    stat = os.statvfs(self.path) if hasattr(os, "statvfs") else None
                    if stat:
                        self.total_space = stat.f_blocks * stat.f_frsize
                        self.free_space = stat.f_bavail * stat.f_frsize
                        self.used_space = self.total_space - self.free_space
                except (OSError, AttributeError):
                    pass

            self.last_checked = datetime.now()
            self.check_count += 1

        except Exception:
            self.is_accessible = False

    def refresh(self):
        """Refresh path information"""
        self._analyze_path()

    @property
    def usage_percentage(self) -> Optional[float]:
        """Get disk usage percentage"""
        if self.total_space and self.used_space:
            return (self.used_space / self.total_space) * 100
        return None


@dataclass
class NavigationState:
    """
    Current navigation state for breadcrumb bar

    Manages the complete navigation state including current path,
    breadcrumb segments, history, and file system integration.
    """

    # Current navigation state
    current_path: Path
    breadcrumb_segments: List[BreadcrumbSegment] = field(default_factory=list)

    # Path information
    path_info: Optional[PathInfo] = None

    # Navigation history
    history: List[Path] = field(default_factory=list)
    history_index: int = -1
    max_history_size: int = 50

    # State flags
    is_loading: bool = False
    has_error: bool = False
    error_message: str = ""

    # Performance tracking
    last_update: Optional[datetime] = None
    update_count: int = 0
    segment_generation_time: float = 0.0

    # Configuration
    max_visible_segments: int = 10
    truncation_enabled: bool = True
    show_root_segment: bool = True

    def __post_init__(self):
        """Post-initialization setup"""
        if not self.breadcrumb_segments:
            self.generate_segments()

        if not self.path_info:
            self.path_info = PathInfo(self.current_path)

        self.last_update = datetime.now()

    def generate_segments(self) -> List[BreadcrumbSegment]:
        """
        Generate breadcrumb segments from current path

        Returns:
            List of breadcrumb segments
        """
        start_time = datetime.now()
        segments = []

        try:
            # Get all path parts
            path_parts = []
            current = self.current_path.resolve()

            # Build path parts list
            while current.parent != current:
                path_parts.append(current)
                current = current.parent

            # Add root/drive
            path_parts.append(current)
            path_parts.reverse()

            # Create segments
            for i, path_part in enumerate(path_parts):
                segment = BreadcrumbSegment(
                    name=path_part.name,
                    path=path_part,
                    segment_index=i,
                    is_root=(i == 0),
                )

                # Mark current segment
                if path_part == self.current_path:
                    segment.state = SegmentState.CURRENT

                segments.append(segment)

            self.breadcrumb_segments = segments

            # Apply truncation if needed
            if self.truncation_enabled and len(segments) > self.max_visible_segments:
                self._apply_truncation()

        except Exception as e:
            self.has_error = True
            self.error_message = f"Failed to generate segments: {e!s}"
            segments = []

        finally:
            end_time = datetime.now()
            self.segment_generation_time = (end_time - start_time).total_seconds()
            self.update_count += 1
            self.last_update = end_time

        return segments

    def _apply_truncation(self):
        """Apply intelligent truncation to segments"""
        if len(self.breadcrumb_segments) <= self.max_visible_segments:
            return

        # Always keep root and current segments
        root_segments = [s for s in self.breadcrumb_segments if s.is_root]
        current_segments = [
            s for s in self.breadcrumb_segments if s.state == SegmentState.CURRENT
        ]

        # Calculate how many middle segments we can keep
        reserved_count = (
            len(root_segments) + len(current_segments) + 1
        )  # +1 for ellipsis
        available_count = self.max_visible_segments - reserved_count

        if available_count > 0:
            # Keep some segments before the current one
            middle_segments = [
                s
                for s in self.breadcrumb_segments
                if not s.is_root and s.state != SegmentState.CURRENT
            ]

            if len(middle_segments) > available_count:
                # Keep the last N segments before current
                keep_segments = middle_segments[-available_count:]

                # Create truncated list
                truncated = []
                truncated.extend(root_segments)

                # Add ellipsis segment if we truncated
                if len(middle_segments) > available_count:
                    ellipsis_segment = BreadcrumbSegment(
                        name="...",
                        path=Path("..."),
                        display_name="...",
                        is_clickable=False,
                        icon="ellipsis",
                    )
                    truncated.append(ellipsis_segment)

                truncated.extend(keep_segments)
                truncated.extend(current_segments)

                self.breadcrumb_segments = truncated

    def navigate_to_path(self, path: Path) -> bool:
        """
        Navigate to a new path

        Args:
            path: Target path to navigate to

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # Validate path
            if not path.exists():
                self.has_error = True
                self.error_message = f"Path does not exist: {path}"
                return False

            if not os.access(path, os.R_OK):
                self.has_error = True
                self.error_message = f"Access denied: {path}"
                return False

            # Add current path to history
            if self.current_path != path:
                self.add_to_history(self.current_path)

            # Update current path
            self.current_path = path
            self.path_info = PathInfo(path)

            # Regenerate segments
            self.generate_segments()

            # Clear error state
            self.has_error = False
            self.error_message = ""

            return True

        except Exception as e:
            self.has_error = True
            self.error_message = f"Navigation failed: {e!s}"
            return False

    def navigate_to_segment(self, segment_index: int) -> bool:
        """
        Navigate to a specific breadcrumb segment

        Args:
            segment_index: Index of the segment to navigate to

        Returns:
            True if navigation successful, False otherwise
        """
        if 0 <= segment_index < len(self.breadcrumb_segments):
            segment = self.breadcrumb_segments[segment_index]
            if segment.is_clickable and segment.is_accessible:
                segment.update_access_info()
                return self.navigate_to_path(segment.path)

        return False

    def add_to_history(self, path: Path):
        """Add path to navigation history"""
        # Remove path if it already exists
        if path in self.history:
            self.history.remove(path)

        # Add to beginning of history
        self.history.insert(0, path)

        # Trim history to max size
        if len(self.history) > self.max_history_size:
            self.history = self.history[: self.max_history_size]

        # Reset history index
        self.history_index = -1

    def can_go_back(self) -> bool:
        """Check if backward navigation is possible"""
        return len(self.history) > 0 and self.history_index < len(self.history) - 1

    def can_go_forward(self) -> bool:
        """Check if forward navigation is possible"""
        return self.history_index > 0

    def go_back(self) -> bool:
        """Navigate backward in history"""
        if self.can_go_back():
            self.history_index += 1
            target_path = self.history[self.history_index]
            return self.navigate_to_path(target_path)
        return False

    def go_forward(self) -> bool:
        """Navigate forward in history"""
        if self.can_go_forward():
            self.history_index -= 1
            target_path = self.history[self.history_index]
            return self.navigate_to_path(target_path)
        return False

    def go_up(self) -> bool:
        """Navigate to parent directory"""
        parent_path = self.current_path.parent
        if parent_path != self.current_path:
            return self.navigate_to_path(parent_path)
        return False

    def refresh(self):
        """Refresh navigation state"""
        if self.path_info:
            self.path_info.refresh()

        # Refresh all segments
        for segment in self.breadcrumb_segments:
            segment.refresh_state()

        # Regenerate segments if path changed
        if not self.current_path.exists():
            # Try to navigate to nearest existing parent
            parent = self.current_path.parent
            while parent != parent.parent and not parent.exists():
                parent = parent.parent

            if parent.exists():
                self.navigate_to_path(parent)

    def get_segment_by_path(self, path: Path) -> Optional[BreadcrumbSegment]:
        """Get segment by path"""
        for segment in self.breadcrumb_segments:
            if segment.path == path:
                return segment
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert navigation state to dictionary"""
        return {
            "current_path": str(self.current_path),
            "segments": [segment.to_dict() for segment in self.breadcrumb_segments],
            "history": [str(p) for p in self.history],
            "history_index": self.history_index,
            "is_loading": self.is_loading,
            "has_error": self.has_error,
            "error_message": self.error_message,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "update_count": self.update_count,
            "segment_generation_time": self.segment_generation_time,
        }


@dataclass
class NavigationEvent:
    """
    Navigation event data model

    Represents navigation events for event handling and logging.
    """

    event_type: str  # navigate, segment_click, back, forward, up, refresh
    source_path: Optional[Path] = None
    target_path: Optional[Path] = None
    segment_index: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_type": self.event_type,
            "source_path": str(self.source_path) if self.source_path else None,
            "target_path": str(self.target_path) if self.target_path else None,
            "segment_index": self.segment_index,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }
