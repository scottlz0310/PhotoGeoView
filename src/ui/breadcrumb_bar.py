"""
Breadcrumb Address Bar Wrapper Component

Wrapper around breadcrumb-addressbar library providing PhotoGeoView-specific functionality.
Implements the breadcrumb address bar component as specified in the qt-theme-breadcrumb spec.

Author: Kiro AI Integration System
Requirements: 2.1, 2.2, 2.3, 2.4
"""

import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget

from ..integration.config_manager import ConfigManager
from ..integration.logging_system import LoggerSystem
from ..integration.models import AIComponent
from ..integration.navigation_models import (
    BreadcrumbSegment,
    NavigationEvent,
    NavigationState,
    SegmentState,
)
from ..integration.performance_optimizer import PerformanceOptimizer
from ..integration.services.file_system_watcher import FileChangeType, FileSystemWatcher
from ..integration.user_notification_system import UserNotificationSystem


class BreadcrumbAddressBar(QObject):
    """
    Wrapper around breadcrumb-addressbar library with PhotoGeoView integration

    This component implements the breadcrumb address bar wrapper as specified in task 3 of the
    qt-theme-breadcrumb specification, providing:
    - Path display and segment click handling
    - Path truncation logic for long paths
    - Integration with breadcrumb-addressbar library
    - File system watcher integration for automatic updates
    """

    # Signals for breadcrumb navigation
    path_changed = Signal(Path)  # new_path
    segment_clicked = Signal(int, Path)  # segment_index, path
    navigation_requested = Signal(Path)  # target_path
    breadcrumb_error = Signal(str, str)  # error_type, error_message

    def __init__(
        self,
        file_system_watcher: FileSystemWatcher,
        logger_system: LoggerSystem,
        config_manager: Optional[ConfigManager] = None,
        notification_system: Optional[UserNotificationSystem] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the breadcrumb address bar

        Args:
            file_system_watcher: File system watcher instance
            logger_system: Logging system instance
            config_manager: Configuration manager instance (optional)
            notification_system: User notification system instance (optional)
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        self.file_watcher = file_system_watcher
        self.logger_system = logger_system  # Add this line
        self.logger = logger_system.get_logger(__name__)
        self.config_manager = config_manager
        self.notification_system = notification_system

        # Performance optimization (optional)
        try:
            self.performance_optimizer = PerformanceOptimizer(logger_system)
            # Only start optimization if we have an event loop
            try:
                import asyncio

                asyncio.get_running_loop()
                self.performance_optimizer.start_optimization()
            except RuntimeError:
                # No event loop running, skip optimization
                self.logger.debug(
                    "No event loop running, skipping performance optimization"
                )
        except Exception as e:
            self.logger.warning(f"Failed to initialize performance optimizer: {e}")
            self.performance_optimizer = None

        # Breadcrumb-addressbar integration
        self.breadcrumb_widget = None
        self._initialize_breadcrumb_widget()

        # Navigation state management
        self.current_state = NavigationState(current_path=Path.home())
        self.navigation_listeners: List[Callable[[NavigationEvent], None]] = []

        # Configuration settings
        self.max_visible_segments = 10
        self.truncation_mode = "smart"  # smart, middle, end, none
        self.show_icons = True
        self.show_tooltips = True

        # Performance tracking
        self.last_update_time = datetime.now()
        self.update_count = 0

        # File system watcher integration
        self._setup_file_watcher()

        # Keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Load configuration
        self._load_configuration()

        self.logger.info("BreadcrumbAddressBar initialized successfully")

    def _initialize_breadcrumb_widget(self) -> None:
        """Initialize breadcrumb-addressbar library integration"""
        try:
            # Import and initialize breadcrumb_addressbar library
            from breadcrumb_addressbar import BreadcrumbAddressBar

            self.breadcrumb_widget = BreadcrumbAddressBar()

            # 新しい設定オプションを適用
            self.breadcrumb_widget.setShowPopupForAllButtons(
                True
            )  # どのボタンでもポップアップを表示
            self.breadcrumb_widget.setPopupPositionOffset(
                (0, 2)
            )  # ポップアップの位置オフセット

            # Connect breadcrumb widget signals
            if hasattr(self.breadcrumb_widget, "pathChanged"):
                self.breadcrumb_widget.pathChanged.connect(
                    self._on_breadcrumb_path_changed
                )

            if hasattr(self.breadcrumb_widget, "folderSelected"):
                self.breadcrumb_widget.folderSelected.connect(
                    self._on_breadcrumb_segment_clicked
                )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_init",
                "Using breadcrumb_addressbar library with enhanced popup support",
            )
            self.logger.info(
                "Breadcrumb-addressbar library initialized successfully with enhanced popup support"
            )

        except ImportError as e:
            self.logger.error(f"Breadcrumb-addressbar library not available: {e}")
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_error",
                f"Failed to import breadcrumb_addressbar: {e}",
            )
            self.breadcrumb_widget = None
            raise  # Re-raise to let caller handle the error
        except Exception as e:
            self.logger.error(f"Failed to initialize breadcrumb-addressbar: {e}")
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_error",
                f"Failed to initialize breadcrumb_addressbar: {e}",
            )
            self.breadcrumb_widget = None
            raise  # Re-raise to let caller handle the error

    def _setup_file_watcher(self) -> None:
        """Setup file system watcher integration"""
        try:
            # Add change listener for path updates
            self.file_watcher.add_change_listener(self._on_file_system_change)
            self.logger.debug("File system watcher integration setup complete")

        except Exception as e:
            self.logger.error(f"Failed to setup file system watcher integration: {e}")

    def _setup_keyboard_shortcuts(self) -> None:
        """Configure keyboard navigation shortcuts"""
        try:
            if self.breadcrumb_widget:
                # Alt+Up: Navigate to parent directory
                self.up_shortcut = QShortcut(
                    QKeySequence("Alt+Up"), self.breadcrumb_widget
                )
                self.up_shortcut.activated.connect(self.navigate_up)

                # Tab: Navigate between breadcrumb segments (handled by widget focus)
                self.breadcrumb_widget.setFocusPolicy(
                    self.breadcrumb_widget.focusPolicy()
                )

                # Set up accessibility features
                self._setup_accessibility_features()

            self.logger.debug("Keyboard shortcuts configured")

        except Exception as e:
            self.logger.error(f"Failed to setup keyboard shortcuts: {e}")

    def _setup_accessibility_features(self) -> None:
        """Setup accessibility features for screen readers and keyboard navigation"""
        try:
            if not self.breadcrumb_widget:
                return

            # Set accessibility properties for the breadcrumb widget
            self.breadcrumb_widget.setAccessibleName("Breadcrumb Navigation")
            self.breadcrumb_widget.setAccessibleDescription(
                "Navigation breadcrumb showing current folder path. Use Tab to navigate between segments, "
                "Enter to navigate to a segment, Alt+Up to go to parent directory."
            )

            # Set up focus management
            self._setup_focus_management()

            # Set up screen reader support
            self._setup_screen_reader_support()

            self.logger.debug("Accessibility features configured")

        except Exception as e:
            self.logger.error(f"Failed to setup accessibility features: {e}")

    def _setup_focus_management(self) -> None:
        """Setup focus management for breadcrumb segments"""
        try:
            if not self.breadcrumb_widget:
                return

            from PySide6.QtCore import Qt

            # Enable keyboard focus
            self.breadcrumb_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            # Set tab order for segments if supported by the widget
            if hasattr(self.breadcrumb_widget, "setTabOrder"):
                # This would be implemented by the breadcrumb-addressbar library
                pass

            # Install event filter for custom keyboard handling
            self.breadcrumb_widget.installEventFilter(self)

            self.logger.debug("Focus management configured")

        except Exception as e:
            self.logger.error(f"Failed to setup focus management: {e}")

    def _setup_screen_reader_support(self) -> None:
        """Setup screen reader support"""
        try:
            if not self.breadcrumb_widget:
                return

            # Set ARIA-like properties using Qt accessibility
            self.breadcrumb_widget.setAccessibleRole(0x27)  # Navigation role

            # Update accessibility info when path changes
            self._update_accessibility_info()

            self.logger.debug("Screen reader support configured")

        except Exception as e:
            self.logger.error(f"Failed to setup screen reader support: {e}")

    def _update_accessibility_info(self) -> None:
        """Update accessibility information for current path"""
        try:
            if not self.breadcrumb_widget:
                return

            current_path = self.current_state.current_path
            segments = self.current_state.breadcrumb_segments

            # Update accessible description with current path info
            path_description = f"Current location: {current_path}. "
            if len(segments) > 1:
                path_description += f"Path has {len(segments)} segments. "
                path_description += (
                    "Use Tab to navigate between segments, Enter to select a segment."
                )
            else:
                path_description += "At root level."

            self.breadcrumb_widget.setAccessibleDescription(path_description)

            # Announce path change to screen readers
            if hasattr(self.breadcrumb_widget, "accessibilityUpdateRequested"):
                self.breadcrumb_widget.accessibilityUpdateRequested.emit()

        except Exception as e:
            self.logger.error(f"Failed to update accessibility info: {e}")

    def eventFilter(self, obj: Any, event: Any) -> bool:
        """Event filter for custom keyboard handling"""
        try:
            from PySide6.QtCore import QEvent, Qt
            from PySide6.QtGui import QKeyEvent

            if obj == self.breadcrumb_widget and event.type() == QEvent.Type.KeyPress:
                key_event: QKeyEvent = event
                key = key_event.key()
                modifiers = key_event.modifiers()

                # Handle custom keyboard shortcuts
                if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                    # Enter: Navigate to currently focused segment
                    return self._handle_enter_key()
                elif key == Qt.Key.Key_Home:
                    # Home: Navigate to root segment
                    return self._handle_home_key()
                elif key == Qt.Key.Key_End:
                    # End: Focus on last segment
                    return self._handle_end_key()
                elif key == Qt.Key.Key_Left:
                    # Left arrow: Move to previous segment
                    return self._handle_left_arrow()
                elif key == Qt.Key.Key_Right:
                    # Right arrow: Move to next segment
                    return self._handle_right_arrow()

            return super().eventFilter(obj, event)

        except Exception as e:
            self.logger.error(f"Error in event filter: {e}")
            return False

    def _handle_enter_key(self) -> bool:
        """Handle Enter key press on breadcrumb"""
        try:
            # Get currently focused segment and navigate to it
            focused_segment_index = self._get_focused_segment_index()
            if focused_segment_index >= 0:
                return self.navigate_to_segment(focused_segment_index)
            return False

        except Exception as e:
            self.logger.error(f"Failed to handle Enter key: {e}")
            return False

    def _handle_home_key(self) -> bool:
        """Handle Home key press - navigate to root"""
        try:
            segments = self.current_state.breadcrumb_segments
            if segments:
                root_segment = segments[0]
                return self.set_current_path(root_segment.path)
            return False

        except Exception as e:
            self.logger.error(f"Failed to handle Home key: {e}")
            return False

    def _handle_end_key(self) -> bool:
        """Handle End key press - focus on last segment"""
        try:
            segments = self.current_state.breadcrumb_segments
            if segments:
                # Focus on the last segment
                self._set_focused_segment_index(len(segments) - 1)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to handle End key: {e}")
            return False

    def _handle_left_arrow(self) -> bool:
        """Handle Left arrow key - move to previous segment"""
        try:
            current_index = self._get_focused_segment_index()
            if current_index > 0:
                self._set_focused_segment_index(current_index - 1)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to handle Left arrow: {e}")
            return False

    def _handle_right_arrow(self) -> bool:
        """Handle Right arrow key - move to next segment"""
        try:
            current_index = self._get_focused_segment_index()
            segments = self.current_state.breadcrumb_segments
            if current_index < len(segments) - 1:
                self._set_focused_segment_index(current_index + 1)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to handle Right arrow: {e}")
            return False

    def _get_focused_segment_index(self) -> int:
        """Get the index of the currently focused segment"""
        try:
            # This would depend on the breadcrumb-addressbar library implementation
            # For now, return 0 as a fallback
            if hasattr(self.breadcrumb_widget, "getFocusedSegmentIndex"):
                return self.breadcrumb_widget.getFocusedSegmentIndex()
            return 0

        except Exception as e:
            self.logger.error(f"Failed to get focused segment index: {e}")
            return -1

    def _set_focused_segment_index(self, index: int) -> None:
        """Set the focused segment index"""
        try:
            segments = self.current_state.breadcrumb_segments
            if 0 <= index < len(segments):
                # This would depend on the breadcrumb-addressbar library implementation
                if hasattr(self.breadcrumb_widget, "setFocusedSegmentIndex"):
                    self.breadcrumb_widget.setFocusedSegmentIndex(index)

                # Update accessibility info for the focused segment
                segment = segments[index]
                self.breadcrumb_widget.setAccessibleDescription(
                    f"Focused on segment: {segment.display_name} at {segment.path}"
                )

        except Exception as e:
            self.logger.error(f"Failed to set focused segment index: {e}")

    def get_keyboard_shortcuts_info(self) -> Dict[str, str]:
        """
        Get information about available keyboard shortcuts

        Returns:
            Dictionary mapping shortcut keys to descriptions
        """
        return {
            "Alt+Up": "Navigate to parent directory",
            "Tab": "Navigate between breadcrumb segments",
            "Enter": "Navigate to focused segment",
            "Home": "Navigate to root directory",
            "End": "Focus on last segment",
            "Left Arrow": "Move focus to previous segment",
            "Right Arrow": "Move focus to next segment",
        }

    def set_accessibility_enabled(self, enabled: bool) -> None:
        """
        Enable or disable accessibility features

        Args:
            enabled: Whether to enable accessibility features
        """
        try:
            if enabled:
                self._setup_accessibility_features()
            else:
                # Remove accessibility features
                if self.breadcrumb_widget:
                    self.breadcrumb_widget.setAccessibleName("")
                    self.breadcrumb_widget.setAccessibleDescription("")

            self.logger.debug(
                f"Accessibility features {'enabled' if enabled else 'disabled'}"
            )

        except Exception as e:
            self.logger.error(f"Failed to set accessibility enabled: {e}")

    def _load_configuration(self) -> None:
        """Load configuration settings"""
        if not self.config_manager:
            return

        try:
            # Load breadcrumb settings
            self.max_visible_segments = self.config_manager.get_setting(
                "ui.breadcrumb.max_segments", 10
            )
            self.truncation_mode = self.config_manager.get_setting(
                "ui.breadcrumb.truncation_mode", "smart"
            )
            self.show_icons = self.config_manager.get_setting(
                "ui.breadcrumb.show_icons", True
            )
            self.show_tooltips = self.config_manager.get_setting(
                "ui.breadcrumb.show_tooltips", True
            )

            self.logger.debug("Configuration loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")

    def _apply_optimized_path_truncation(self) -> None:
        """Apply optimized path truncation for long paths"""
        try:
            if not self.current_state or not self.current_state.breadcrumb_segments:
                return

            segments = self.current_state.breadcrumb_segments

            # Use performance optimizer for breadcrumb rendering
            if hasattr(self, "performance_optimizer") and self.performance_optimizer:
                try:
                    # Check if optimize_breadcrumb_rendering is async
                    if hasattr(
                        self.performance_optimizer, "optimize_breadcrumb_rendering"
                    ):
                        import inspect

                        if inspect.iscoroutinefunction(
                            self.performance_optimizer.optimize_breadcrumb_rendering
                        ):
                            # Skip async optimization in sync context, use fallback
                            self.logger.debug(
                                "Skipping async breadcrumb optimization in sync context"
                            )
                            optimized_segments = segments
                        else:
                            optimized_segments = self.performance_optimizer.optimize_breadcrumb_rendering(
                                self.current_state.current_path, segments
                            )
                    else:
                        optimized_segments = segments
                except Exception as e:
                    self.logger.warning(f"Performance optimizer failed: {e}")
                    optimized_segments = segments
            else:
                optimized_segments = segments

            # Update segments if optimization was applied
            if optimized_segments != segments:
                self.current_state.breadcrumb_segments = optimized_segments
                self.logger.debug(
                    f"Applied breadcrumb optimization: {len(segments)} -> {len(optimized_segments)} segments"
                )

        except Exception as e:
            self.logger.error(f"Failed to apply optimized path truncation: {e}")

    def _apply_path_truncation(self) -> None:
        """Legacy path truncation method (fallback)"""
        try:
            if not self.current_state or not self.current_state.breadcrumb_segments:
                return

            segments = self.current_state.breadcrumb_segments

            # Apply simple truncation if too many segments
            if len(segments) > self.max_visible_segments:
                # Keep first 2, last 3, and add ellipsis
                truncated = segments[:2] + ["..."] + segments[-3:]
                self.current_state.breadcrumb_segments = truncated
                self.logger.debug(
                    f"Applied simple truncation: {len(segments)} -> {len(truncated)} segments"
                )

        except Exception as e:
            self.logger.error(f"Failed to apply path truncation: {e}")

    # Core breadcrumb functionality

    def get_widget(self) -> Optional[QWidget]:
        """
        Get the breadcrumb widget for UI integration

        Returns:
            Breadcrumb widget or None if not available
        """
        return self.breadcrumb_widget

    def set_current_path(self, path: Path) -> bool:
        """
        Update breadcrumb display with new path with comprehensive error handling

        Args:
            path: New path to display

        Returns:
            True if path set successfully, False otherwise
        """
        # Start performance monitoring
        operation_id = self.performance_optimizer.start_navigation_operation(
            f"set_path_{path.name}"
        )

        try:
            # Validate path with comprehensive checks
            path_validation_result = self._validate_path_comprehensive(path)
            if not path_validation_result["valid"]:
                error_type = path_validation_result["error_type"]
                error_msg = path_validation_result["error_message"]

                self.logger.error(f"Path validation failed: {error_msg}")
                self.breadcrumb_error.emit(error_type, error_msg)

                # Show user notification
                if self.notification_system:
                    self.notification_system.show_breadcrumb_error(
                        str(path), error_type, error_msg
                    )

                # Try to navigate to fallback path
                return self._navigate_to_fallback_path(path, error_type)

            # Check for network drive disconnection
            if self._is_network_path(path) and not self._is_network_accessible(path):
                error_msg = f"Network drive disconnected or inaccessible: {path}"
                self.logger.warning(error_msg)
                self.breadcrumb_error.emit("network_disconnected", error_msg)

                # Show user notification
                if self.notification_system:
                    self.notification_system.show_breadcrumb_error(
                        str(path), "network_disconnected", error_msg
                    )

                # Try to navigate to local fallback
                return self._handle_network_disconnection(path)

            old_path = self.current_state.current_path

            # Update navigation state with retry mechanism
            navigation_success = False
            for attempt in range(3):  # Try up to 3 times
                try:
                    if self.current_state.navigate_to_path(path):
                        navigation_success = True
                        break
                    else:
                        self.logger.warning(
                            f"Navigation state update attempt {attempt + 1} failed"
                        )
                        if attempt < 2:  # Don't sleep on last attempt
                            import time

                            time.sleep(0.05)  # Brief delay before retry
                except Exception as e:
                    self.logger.warning(
                        f"Navigation state update attempt {attempt + 1} error: {e}"
                    )
                    if attempt < 2:
                        import time

                        time.sleep(0.05)

            if not navigation_success:
                error_msg = "Failed to update navigation state after 3 attempts"
                self.logger.error(error_msg)
                self.breadcrumb_error.emit("navigation_state_error", error_msg)
                return self._navigate_to_fallback_path(path, "navigation_state_error")

            # Update breadcrumb widget with error handling
            widget_update_success = False
            if self.breadcrumb_widget:
                try:
                    if hasattr(self.breadcrumb_widget, "setPath"):
                        self.breadcrumb_widget.setPath(str(path))
                        widget_update_success = True
                    else:
                        self.logger.warning("Breadcrumb widget has no setPath method")
                        widget_update_success = True  # Continue without widget update
                except Exception as e:
                    self.logger.error(f"Failed to update breadcrumb widget: {e}")
                    # Continue anyway - navigation state is updated
                    widget_update_success = True

            # Apply truncation with error handling and optimization
            try:
                self._apply_optimized_path_truncation()
            except Exception as e:
                self.logger.warning(f"Failed to apply path truncation: {e}")
                # Continue anyway

            # Update accessibility info with error handling
            try:
                self._update_accessibility_info()
            except Exception as e:
                self.logger.warning(f"Failed to update accessibility info: {e}")
                # Continue anyway

            # Emit signals with error handling
            try:
                self.path_changed.emit(path)
            except Exception as e:
                self.logger.error(f"Failed to emit path_changed signal: {e}")

            # Create and notify navigation event
            try:
                event = NavigationEvent(
                    event_type="navigate",
                    source_path=old_path,
                    target_path=path,
                    timestamp=datetime.now(),
                    success=True,
                )
                self._notify_navigation_listeners(event)
            except Exception as e:
                self.logger.error(f"Failed to notify navigation listeners: {e}")

            # Update performance tracking
            try:
                self.last_update_time = datetime.now()
                self.update_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to update performance tracking: {e}")

            # End performance monitoring
            duration = self.performance_optimizer.end_navigation_operation(operation_id)
            self.logger.debug(
                f"Path updated successfully: {path} (took {duration:.3f}s)"
            )
            return True

        except Exception as e:
            error_msg = f"Critical error setting current path {path}: {e}"
            self.logger.error(error_msg)
            self.breadcrumb_error.emit("critical_path_error", error_msg)

            # End performance monitoring on error
            self.performance_optimizer.end_navigation_operation(operation_id)

            return self._navigate_to_fallback_path(path, "critical_path_error")

    def _validate_path_comprehensive(self, path: Path) -> Dict[str, Any]:
        """
        Comprehensive path validation with detailed error information and caching

        Args:
            path: Path to validate

        Returns:
            Dictionary with validation result and error details
        """
        try:
            # Check cache first
            cached_result = self.performance_optimizer.get_cached_path_info(path)
            if cached_result and "validation_result" in cached_result:
                return cached_result["validation_result"]
            # Check if path is None or empty
            if not path:
                return {
                    "valid": False,
                    "error_type": "invalid_path",
                    "error_message": "Path is None or empty",
                }

            # Check if path exists
            if not path.exists():
                return {
                    "valid": False,
                    "error_type": "path_not_found",
                    "error_message": f"Path does not exist: {path}",
                }

            # Check if path is a directory
            if not path.is_dir():
                return {
                    "valid": False,
                    "error_type": "not_directory",
                    "error_message": f"Path is not a directory: {path}",
                }

            # Check read permissions
            if not os.access(path, os.R_OK):
                return {
                    "valid": False,
                    "error_type": "permission_denied",
                    "error_message": f"No read permission for path: {path}",
                }

            # Check if it's a network path and if accessible
            if self._is_network_path(path):
                if not self._is_network_accessible(path):
                    return {
                        "valid": False,
                        "error_type": "network_inaccessible",
                        "error_message": f"Network path is not accessible: {path}",
                    }

            result = {"valid": True, "error_type": None, "error_message": None}

            # Cache the validation result
            path_info = {
                "validation_result": result,
                "timestamp": datetime.now().isoformat(),
            }
            self.performance_optimizer.cache_path_info(path, path_info)

            return result

        except (OSError, PermissionError) as e:
            result = {
                "valid": False,
                "error_type": "system_error",
                "error_message": f"System error validating path: {e}",
            }
            # Cache error result with shorter TTL
            path_info = {
                "validation_result": result,
                "timestamp": datetime.now().isoformat(),
            }
            self.performance_optimizer.cache_path_info(path, path_info)
            return result
        except Exception as e:
            result = {
                "valid": False,
                "error_type": "validation_error",
                "error_message": f"Unexpected error validating path: {e}",
            }
            # Cache error result with shorter TTL
            path_info = {
                "validation_result": result,
                "timestamp": datetime.now().isoformat(),
            }
            self.performance_optimizer.cache_path_info(path, path_info)
            return result

    def _is_network_path(self, path: Path) -> bool:
        """
        Check if path is on a network drive

        Args:
            path: Path to check

        Returns:
            True if path is on network drive, False otherwise
        """
        try:
            path_str = str(path)

            # Windows UNC paths
            if path_str.startswith("\\\\"):
                return True

            # Windows mapped network drives (check if drive is network)
            if (
                platform.system() == "Windows"
                and len(path_str) >= 2
                and path_str[1] == ":"
            ):
                try:
                    import win32file

                    drive_letter = path_str[0] + ":"
                    drive_type = win32file.GetDriveType(drive_letter + "\\")
                    # DRIVE_REMOTE = 4
                    return drive_type == 4
                except ImportError:
                    # Fallback without win32file
                    pass

            # Unix/Linux network mounts (common patterns)
            if path_str.startswith("/mnt/") or path_str.startswith("/media/"):
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Failed to determine if path is network: {e}")
            return False

    def _is_network_accessible(self, path: Path) -> bool:
        """
        Check if network path is accessible

        Args:
            path: Network path to check

        Returns:
            True if accessible, False otherwise
        """
        try:
            # Try to list directory contents with timeout
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Network access timeout")

            # Set timeout for network access check
            if platform.system() != "Windows":  # signal.alarm not available on Windows
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)  # 3 second timeout

            try:
                # Try to access the path
                list(path.iterdir())
                return True
            except (OSError, PermissionError, TimeoutError):
                return False
            finally:
                if platform.system() != "Windows":
                    signal.alarm(0)  # Cancel timeout

        except Exception as e:
            self.logger.warning(f"Error checking network accessibility: {e}")
            return False

    def _navigate_to_fallback_path(self, failed_path: Path, error_type: str) -> bool:
        """
        Navigate to fallback path when primary path fails

        Args:
            failed_path: The path that failed
            error_type: Type of error that occurred

        Returns:
            True if fallback navigation successful, False otherwise
        """
        try:
            # Prevent infinite recursion
            if (
                hasattr(self, "_navigating_to_fallback")
                and self._navigating_to_fallback
            ):
                self.logger.error(
                    "Already navigating to fallback, preventing recursion"
                )
                return False

            self._navigating_to_fallback = True

            try:
                fallback_candidates = []

                # Try parent directory first
                if failed_path.parent != failed_path:  # Not root
                    fallback_candidates.append(failed_path.parent)

                # Try home directory
                fallback_candidates.append(Path.home())

                # Try current working directory
                try:
                    fallback_candidates.append(Path.cwd())
                except OSError:
                    pass

                # Try root directory as last resort
                if platform.system() == "Windows":
                    fallback_candidates.append(Path("C:\\"))
                else:
                    fallback_candidates.append(Path("/"))

                # Try each fallback candidate
                for fallback_path in fallback_candidates:
                    try:
                        validation_result = self._validate_path_comprehensive(
                            fallback_path
                        )
                        if validation_result["valid"]:
                            self.logger.info(
                                f"Navigating to fallback path: {fallback_path}"
                            )

                            # Update navigation state directly (avoid recursion)
                            if self.current_state.navigate_to_path(fallback_path):
                                # Update widget
                                if self.breadcrumb_widget and hasattr(
                                    self.breadcrumb_widget, "setPath"
                                ):
                                    try:
                                        self.breadcrumb_widget.setPath(
                                            str(fallback_path)
                                        )
                                    except Exception as e:
                                        self.logger.warning(
                                            f"Failed to update widget with fallback path: {e}"
                                        )

                                # Emit signals
                                try:
                                    self.path_changed.emit(fallback_path)
                                except Exception as e:
                                    self.logger.warning(
                                        f"Failed to emit path_changed for fallback: {e}"
                                    )

                                self.logger.info(
                                    f"Successfully navigated to fallback path: {fallback_path}"
                                )
                                return True
                    except Exception as e:
                        self.logger.warning(
                            f"Fallback path {fallback_path} failed: {e}"
                        )
                        continue

                # If all fallbacks failed
                self.logger.error("All fallback paths failed")
                return False

            finally:
                self._navigating_to_fallback = False

        except Exception as e:
            self.logger.error(f"Critical error in fallback navigation: {e}")
            if hasattr(self, "_navigating_to_fallback"):
                self._navigating_to_fallback = False
            return False

    def _handle_network_disconnection(self, network_path: Path) -> bool:
        """
        Handle network drive disconnection

        Args:
            network_path: The disconnected network path

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            self.logger.warning(f"Handling network disconnection for: {network_path}")

            # Emit specific network disconnection error
            self.breadcrumb_error.emit(
                "network_disconnected",
                f"Network drive disconnected: {network_path}. Navigating to local directory.",
            )

            # Try to navigate to a local directory
            local_fallbacks = [
                Path.home(),
                Path.home() / "Documents",
                Path.home() / "Desktop",
            ]

            for fallback in local_fallbacks:
                try:
                    validation_result = self._validate_path_comprehensive(fallback)
                    if validation_result["valid"]:
                        self.logger.info(
                            f"Navigating to local fallback after network disconnection: {fallback}"
                        )
                        return self._navigate_to_fallback_path(
                            network_path, "network_disconnected"
                        )
                except Exception as e:
                    self.logger.warning(f"Local fallback {fallback} failed: {e}")
                    continue

            # If no local fallback worked, use general fallback
            return self._navigate_to_fallback_path(network_path, "network_disconnected")

        except Exception as e:
            self.logger.error(f"Error handling network disconnection: {e}")
            return False

    def _validate_path(self, path: Path) -> bool:
        """
        Validate if a path is suitable for breadcrumb display

        Args:
            path: Path to validate

        Returns:
            True if path is valid, False otherwise
        """
        try:
            # Check if path exists
            if not path.exists():
                return False

            # Check if path is accessible
            if not os.access(path, os.R_OK):
                return False

            # Check if path is a directory
            if not path.is_dir():
                return False

            return True

        except (OSError, PermissionError):
            return False

    def _apply_path_truncation(self) -> None:
        """Apply intelligent truncation to long paths"""
        try:
            segments = self.current_state.breadcrumb_segments

            if len(segments) <= self.max_visible_segments:
                return

            if self.truncation_mode == "smart":
                self._apply_smart_truncation()
            elif self.truncation_mode == "middle":
                self._apply_middle_truncation()
            elif self.truncation_mode == "end":
                self._apply_end_truncation()
            # "none" mode - no truncation

        except Exception as e:
            self.logger.error(f"Failed to apply path truncation: {e}")

    def _apply_smart_truncation(self) -> None:
        """Apply smart truncation keeping important segments"""
        segments = self.current_state.breadcrumb_segments

        if len(segments) <= self.max_visible_segments:
            return

        # Always keep root and current segments
        root_segments = [s for s in segments if s.is_root]
        current_segments = [s for s in segments if s.state == SegmentState.CURRENT]

        # Calculate available space for middle segments
        reserved_count = (
            len(root_segments) + len(current_segments) + 1
        )  # +1 for ellipsis
        available_count = max(0, self.max_visible_segments - reserved_count)

        if available_count > 0:
            # Keep segments closest to current
            middle_segments = [
                s for s in segments if not s.is_root and s.state != SegmentState.CURRENT
            ]

            if len(middle_segments) > available_count:
                # Keep the last N segments before current
                keep_segments = middle_segments[-available_count:]

                # Update breadcrumb widget with truncated path
                self._update_widget_with_truncation(
                    root_segments, keep_segments, current_segments
                )

    def _apply_middle_truncation(self) -> None:
        """Apply middle truncation keeping start and end segments"""
        segments = self.current_state.breadcrumb_segments

        if len(segments) <= self.max_visible_segments:
            return

        # Keep first and last segments, truncate middle
        keep_start = self.max_visible_segments // 2
        keep_end = self.max_visible_segments - keep_start - 1  # -1 for ellipsis

        start_segments = segments[:keep_start]
        end_segments = segments[-keep_end:] if keep_end > 0 else []

        self._update_widget_with_truncation(start_segments, [], end_segments)

    def _apply_end_truncation(self) -> None:
        """Apply end truncation keeping start segments"""
        segments = self.current_state.breadcrumb_segments

        if len(segments) <= self.max_visible_segments:
            return

        # Keep first N-1 segments, add ellipsis
        keep_segments = segments[: self.max_visible_segments - 1]
        self._update_widget_with_truncation(keep_segments, [], [])

    def _update_widget_with_truncation(
        self,
        start_segments: List[BreadcrumbSegment],
        middle_segments: List[BreadcrumbSegment],
        end_segments: List[BreadcrumbSegment],
    ) -> None:
        """Update breadcrumb widget with truncated segments"""
        if not self.breadcrumb_widget:
            return

        try:
            # Build truncated path representation
            truncated_segments = []
            truncated_segments.extend(start_segments)

            # Add ellipsis if we have middle segments or truncation
            if middle_segments or (not middle_segments and end_segments):
                ellipsis_segment = BreadcrumbSegment(
                    name="...",
                    path=Path("..."),
                    display_name="...",
                    is_clickable=False,
                    icon="ellipsis",
                )
                truncated_segments.append(ellipsis_segment)

            truncated_segments.extend(middle_segments)
            truncated_segments.extend(end_segments)

            # Update widget if it supports segment-based updates
            if hasattr(self.breadcrumb_widget, "set_segments"):
                self.breadcrumb_widget.set_segments(
                    [s.to_dict() for s in truncated_segments]
                )
            elif hasattr(self.breadcrumb_widget, "setPath"):
                # Fallback to path-based update
                display_path = " > ".join([s.display_name for s in truncated_segments])
                self.breadcrumb_widget.setPath(display_path)

        except Exception as e:
            self.logger.error(f"Failed to update widget with truncation: {e}")

    # Event handlers

    def _on_breadcrumb_segment_clicked(self, path_str: str) -> None:
        """Handle breadcrumb segment click"""
        try:
            target_path = Path(path_str)

            # Navigate to the clicked segment
            if self.set_current_path(target_path):
                # Emit signals
                self.segment_clicked.emit(0, target_path)  # Use 0 as placeholder index
                self.navigation_requested.emit(target_path)

                # Create navigation event
                event = NavigationEvent(
                    event_type="segment_click",
                    source_path=self.current_state.current_path,
                    target_path=target_path,
                    timestamp=datetime.now(),
                    success=True,
                )
                self._notify_navigation_listeners(event)

                self.logger.debug(f"Navigated to path: {path_str}")
            else:
                self.breadcrumb_error.emit(
                    "navigation_failed", f"Failed to navigate to {path_str}"
                )

        except Exception as e:
            self.logger.error(f"Failed to handle segment click {path_str}: {e}")
            self.breadcrumb_error.emit("segment_click_error", str(e))

    def _on_breadcrumb_path_changed(self, new_path: str) -> None:
        """Handle breadcrumb path change from widget"""
        try:
            path = Path(new_path)
            self.set_current_path(path)

        except Exception as e:
            self.logger.error(f"Failed to handle path change {new_path}: {e}")

    def _on_file_system_change(
        self,
        file_path: Path,
        change_type: FileChangeType,
        old_path: Optional[Path] = None,
    ) -> None:
        """Handle file system change events"""
        try:
            current_path = self.current_state.current_path

            # Check if the change affects current path or its parents
            if self._path_affects_breadcrumb(file_path, current_path):
                # Delay update to avoid rapid successive updates
                QTimer.singleShot(500, self._refresh_breadcrumb_state)

        except Exception as e:
            self.logger.error(f"Failed to handle file system change: {e}")

    def _path_affects_breadcrumb(self, changed_path: Path, current_path: Path) -> bool:
        """Check if a path change affects the current breadcrumb"""
        try:
            # Check if changed path is current path or a parent
            return (
                changed_path == current_path
                or current_path.is_relative_to(changed_path)
                or changed_path.is_relative_to(current_path)
            )

        except (ValueError, OSError):
            return False

    def _refresh_breadcrumb_state(self) -> None:
        """Refresh breadcrumb state after file system changes"""
        try:
            # Refresh navigation state
            self.current_state.refresh()

            # Update breadcrumb display
            if self.breadcrumb_widget and hasattr(self.breadcrumb_widget, "refresh"):
                self.breadcrumb_widget.refresh()

            # Check if current path still exists
            if not self.current_state.current_path.exists():
                # Navigate to nearest existing parent
                parent = self.current_state.current_path.parent
                while parent != parent.parent and not parent.exists():
                    parent = parent.parent

                if parent.exists():
                    self.set_current_path(parent)

            self.logger.debug("Breadcrumb state refreshed")

        except Exception as e:
            self.logger.error(f"Failed to refresh breadcrumb state: {e}")

    # Navigation methods

    def navigate_up(self) -> bool:
        """
        Navigate to parent directory

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            parent_path = self.current_state.current_path.parent

            if parent_path != self.current_state.current_path:
                return self.set_current_path(parent_path)

            return False

        except Exception as e:
            self.logger.error(f"Failed to navigate up: {e}")
            return False

    def navigate_to_segment(self, segment_index: int) -> bool:
        """
        Navigate to a specific breadcrumb segment

        Args:
            segment_index: Index of the segment to navigate to

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            if 0 <= segment_index < len(self.current_state.breadcrumb_segments):
                segment = self.current_state.breadcrumb_segments[segment_index]
                return self.set_current_path(segment.path)

            return False

        except Exception as e:
            self.logger.error(f"Failed to navigate to segment {segment_index}: {e}")
            return False

    def get_current_path(self) -> Path:
        """
        Get the current path

        Returns:
            Current path
        """
        return self.current_state.current_path

    def get_breadcrumb_segments(self) -> List[BreadcrumbSegment]:
        """
        Get current breadcrumb segments

        Returns:
            List of breadcrumb segments
        """
        return self.current_state.breadcrumb_segments.copy()

    # Configuration methods

    def set_max_visible_segments(self, max_segments: int) -> None:
        """
        Set maximum number of visible segments

        Args:
            max_segments: Maximum number of segments to display
        """
        if max_segments > 0:
            self.max_visible_segments = max_segments
            self._apply_path_truncation()

            if self.config_manager:
                self.config_manager.set_setting(
                    "ui.breadcrumb.max_segments", max_segments
                )

    def set_truncation_mode(self, mode: str) -> None:
        """
        Set the truncation mode for long paths

        Args:
            mode: Truncation mode ("smart", "middle", "end", "none")
        """
        if mode in ["smart", "middle", "end", "none"]:
            self.truncation_mode = mode
            self._apply_path_truncation()

            if self.config_manager:
                self.config_manager.set_setting("ui.breadcrumb.truncation_mode", mode)

    def set_show_icons(self, show_icons: bool) -> None:
        """
        Set whether to show icons in breadcrumb segments

        Args:
            show_icons: Whether to show icons
        """
        self.show_icons = show_icons

        if self.breadcrumb_widget and hasattr(self.breadcrumb_widget, "set_show_icons"):
            self.breadcrumb_widget.set_show_icons(show_icons)

        if self.config_manager:
            self.config_manager.set_setting("ui.breadcrumb.show_icons", show_icons)

    def set_show_tooltips(self, show_tooltips: bool) -> None:
        """
        Set whether to show tooltips for breadcrumb segments

        Args:
            show_tooltips: Whether to show tooltips
        """
        self.show_tooltips = show_tooltips

        if self.breadcrumb_widget and hasattr(
            self.breadcrumb_widget, "set_show_tooltips"
        ):
            self.breadcrumb_widget.set_show_tooltips(show_tooltips)

        if self.config_manager:
            self.config_manager.set_setting(
                "ui.breadcrumb.show_tooltips", show_tooltips
            )

    # INavigationAware implementation

    def on_navigation_changed(self, event: NavigationEvent) -> None:
        """
        Handle navigation change event

        Args:
            event: Navigation event data
        """
        try:
            if event.target_path and event.success:
                # Update breadcrumb if navigation came from external source
                if event.target_path != self.current_state.current_path:
                    self.set_current_path(event.target_path)

        except Exception as e:
            self.logger.error(f"Failed to handle navigation change event: {e}")

    def get_supported_navigation_events(self) -> List[str]:
        """
        Get list of navigation event types supported by this component

        Returns:
            List of event type names
        """
        return ["navigate", "segment_click", "back", "forward", "up", "refresh"]

    # Navigation listener management

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
        try:
            if callback not in self.navigation_listeners:
                self.navigation_listeners.append(callback)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to add navigation listener: {e}")
            return False

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
        try:
            if callback in self.navigation_listeners:
                self.navigation_listeners.remove(callback)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to remove navigation listener: {e}")
            return False

    def _notify_navigation_listeners(self, event: NavigationEvent) -> None:
        """Notify all navigation listeners of an event"""
        for listener in self.navigation_listeners.copy():
            try:
                listener(event)
            except Exception as e:
                self.logger.error(f"Navigation listener failed: {e}")

    # Utility methods

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics

        Returns:
            Dictionary with performance statistics
        """
        return {
            "last_update_time": self.last_update_time.isoformat()
            if self.last_update_time
            else None,
            "update_count": self.update_count,
            "current_segments_count": len(self.current_state.breadcrumb_segments),
            "max_visible_segments": self.max_visible_segments,
            "truncation_mode": self.truncation_mode,
            "segment_generation_time": self.current_state.segment_generation_time,
            "navigation_state_update_count": self.current_state.update_count,
        }

    def reset_performance_stats(self) -> None:
        """Reset performance statistics"""
        self.last_update_time = datetime.now()
        self.update_count = 0
        self.current_state.update_count = 0
        self.current_state.segment_generation_time = 0.0

    def cleanup(self) -> None:
        """Cleanup resources and connections"""
        try:
            # Remove file system watcher listener
            if hasattr(self.file_watcher, "remove_change_listener"):
                self.file_watcher.remove_change_listener(self._on_file_system_change)

            # Clear navigation listeners
            self.navigation_listeners.clear()

            # Cleanup breadcrumb widget
            if self.breadcrumb_widget:
                if hasattr(self.breadcrumb_widget, "cleanup"):
                    self.breadcrumb_widget.cleanup()

            self.logger.info("BreadcrumbAddressBar cleanup completed")

        except Exception as e:
            self.logger.error(f"Failed to cleanup BreadcrumbAddressBar: {e}")

    def _handle_network_disconnection(self, path: Path) -> bool:
        """
        Handle network drive disconnection with fallback navigation

        Args:
            path: The network path that became inaccessible

        Returns:
            True if fallback navigation successful, False otherwise
        """
        try:
            self.logger.warning(f"Handling network disconnection for path: {path}")

            # Show user notification about network disconnection
            if self.notification_system:
                self.notification_system.show_warning(
                    "Network Drive Disconnected",
                    f"Theve at '{path}' is no longer accessible.",
                    details="Attempting to navigate to a local directory.",
                )

            # Try fallback paths in order of preference
            fallback_candidates = [
                Path.home(),  # User home directory
                Path.home() / "Documents",  # Documents folder
                Path("/"),  # Root directory (Unix/Linux)
                Path("C:\\") if os.name == "nt" else Path("/"),  # System root
            ]

            for fallback_path in fallback_candidates:
                try:
                    if (
                        fallback_path.exists()
                        and fallback_path.is_dir()
                        and os.access(fallback_path, os.R_OK)
                    ):
                        self.logger.info(
                            f"Navigating to fallback path: {fallback_path}"
                        )

                        # Update current path
                        if self.set_current_path(fallback_path):
                            # Show success notification
                            if self.notification_system:
                                self.notification_system.show_info(
                                    "Navigation Recovered",
                                    f"Navigated to '{fallback_path}' after network disconnection.",
                                )
                            return True

                except (OSError, PermissionError) as e:
                    self.logger.debug(
                        f"Fallback path {fallback_path} not accessible: {e}"
                    )
                    continue

            # If all fallbacks fail, show error
            error_msg = "Unable to find accessible fallback directory after network disconnection"
            self.logger.error(error_msg)
            self.breadcrumb_error.emit("fallback_failed", error_msg)

            if self.notification_system:
                self.notification_system.show_error(
                    "Navigation Failed",
                    "Unable to navigate to any accessible directory after network disconnection.",
                )

            return False

        except Exception as e:
            self.logger.error(f"Failed to handle network disconnection: {e}")
            return False

    def handle_path_access_error(
        self, path: Path, error_type: str, error_message: str
    ) -> bool:
        """
        Handle path access errors with appropriate fallback strategies

        Args:
            path: The path that caused the error
            error_type: Type of error (permission_denied, path_not_found, etc.)
            error_message: Detailed error message

        Returns:
            True if error was handled successfully, False otherwise
        """
        try:
            self.logger.error(
                f"Path access error for '{path}': {error_type} - {error_message}"
            )
            self.breadcrumb_error.emit(error_type, error_message)

            # Show appropriate user notification based on error type
            if self.notification_system:
                if error_type == "permission_denied":
                    self.notification_system.show_breadcrumb_error(
                        str(path),
                        error_type,
                        "You don't have permission to access this directory.",
                    )
                elif error_type == "path_not_found":
                    self.notification_system.show_breadcrumb_error(
                        str(path),
                        error_type,
                        "The specified directory could not be found.",
                    )
                elif error_type == "network_inaccessible":
                    return self._handle_network_disconnection(path)
                else:
                    self.notification_system.show_breadcrumb_error(
                        str(path), error_type, error_message
                    )

            # Try to navigate to parent directory first
            if path.parent != path and path.parent.exists():
                try:
                    if self.set_current_path(path.parent):
                        self.logger.info(
                            f"Navigated to parent directory: {path.parent}"
                        )
                        if self.notification_system:
                            self.notification_system.show_info(
                                "Navigation Recovered",
                                f"Navigated to parent directory: {path.parent}",
                            )
                        return True
                except Exception as e:
                    self.logger.debug(f"Failed to navigate to parent directory: {e}")

            # If parent navigation fails, try standard fallback paths
            return self._navigate_to_fallback_path(path, error_type)

        except Exception as e:
            self.logger.error(f"Failed to handle path access error: {e}")
            return False

    def validate_path_accessibility(self, path: Path) -> Dict[str, Any]:
        """
        Validate path accessibility with detailed error information

        Args:
            path: Path to validate

        Returns:
            Dictionary with validation result and error details
        """
        try:
            # Use the existing comprehensive validation method
            return self._validate_path_comprehensive(path)

        except Exception as e:
            return {
                "valid": False,
                "error_type": "validation_error",
                "error_message": f"Failed to validate path: {e}",
            }

    def get_error_recovery_options(self, error_type: str) -> List[Dict[str, Any]]:
        """
        Get available error recovery options based on error type

        Args:
            error_type: Type of error that occurred

        Returns:
            List of recovery options with descriptions and actions
        """
        try:
            recovery_options = []

            if error_type == "permission_denied":
                recovery_options.extend(
                    [
                        {
                            "name": "Navigate to Parent",
                            "description": "Navigate to the parent directory",
                            "action": "navigate_parent",
                        },
                        {
                            "name": "Go to Home",
                            "description": "Navigate to your home directory",
                            "action": "navigate_home",
                        },
                    ]
                )

            elif error_type == "path_not_found":
                recovery_options.extend(
                    [
                        {
                            "name": "Navigate to Parent",
                            "description": "Navigate to the parent directory if it exists",
                            "action": "navigate_parent",
                        },
                        {
                            "name": "Go to Home",
                            "description": "Navigate to your home directory",
                            "action": "navigate_home",
                        },
                        {
                            "name": "Browse Recent",
                            "description": "Choose from recently visited directories",
                            "action": "show_recent",
                        },
                    ]
                )

            elif error_type == "network_disconnected":
                recovery_options.extend(
                    [
                        {
                            "name": "Retry Connection",
                            "description": "Attempt to reconnect to the network drive",
                            "action": "retry_network",
                        },
                        {
                            "name": "Go to Local Drive",
                            "description": "Navigate to a local directory",
                            "action": "navigate_local",
                        },
                        {
                            "name": "Go to Home",
                            "description": "Navigate to your home directory",
                            "action": "navigate_home",
                        },
                    ]
                )

            else:
                # Generic recovery options
                recovery_options.extend(
                    [
                        {
                            "name": "Go to Home",
                            "description": "Navigate to your home directory",
                            "action": "navigate_home",
                        },
                        {
                            "name": "Refresh",
                            "description": "Refresh the current directory",
                            "action": "refresh",
                        },
                    ]
                )

            return recovery_options

        except Exception as e:
            self.logger.error(f"Failed to get error recovery options: {e}")
            return []

    def execute_recovery_action(
        self, action: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Execute a recovery action

        Args:
            action: Recovery action to execute
            context: Optional context information

        Returns:
            True if action executed successfully, False otherwise
        """
        try:
            if action == "navigate_parent":
                current_path = self.current_state.current_path
                if current_path.parent != current_path:
                    return self.set_current_path(current_path.parent)

            elif action == "navigate_home":
                return self.set_current_path(Path.home())

            elif action == "navigate_local":
                # Navigate to a local directory (Documents, Desktop, etc.)
                local_paths = [
                    Path.home() / "Documents",
                    Path.home() / "Desktop",
                    Path.home(),
                ]
                for local_path in local_paths:
                    if local_path.exists() and local_path.is_dir():
                        return self.set_current_path(local_path)

            elif action == "retry_network":
                # Retry accessing the current path if it's a network path
                current_path = self.current_state.current_path
                if self._is_network_path(current_path):
                    return self.set_current_path(current_path)

            elif action == "refresh":
                # Refresh current directory
                current_path = self.current_state.current_path
                return self.set_current_path(current_path)

            elif action == "show_recent":
                # This would typically show a dialog with recent paths
                # For now, just log the action
                self.logger.info("Show recent directories action requested")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to execute recovery action '{action}': {e}")
            return False
