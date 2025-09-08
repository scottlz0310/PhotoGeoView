"""
Unified State Manager for AI Integration

Provides centralized state coordination across AI components:
- Application state persistence and restoration
- State change notifications and event handling
- Cross-component state synchronization
- State validation and migration

Author: Kiro AI Integration System
"""

import asyncio
import copy
import json
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .config_manager import ConfigManager
from .error_handling import ErrorCategory, IntegratedErrorHandler
from .logging_system import LoggerSystem
from .models import AIComponent, ApplicationState, ImageMetadata, ThemeConfiguration


@dataclass
class StateChangeEvent:
    """State change event data structure"""

    key: str
    old_value: Any
    new_value: Any
    component: AIComponent
    timestamp: datetime = field(default_factory=datetime.now)


class StateManager:
    """
    Unified state manager for AI integration

    Features:
    - Centralized state storage and management
    - State change notifications
    - Persistence and restoration
    - Cross-component synchronization
    - State validation and migration
    """

    def __init__(
        self, config_manager: ConfigManager = None, logger_system: LoggerSystem = None
    ):
        """
        Initialize the state manager

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
        """

        self.config_manager = config_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # State storage
        self.app_state = ApplicationState()
        self.state_lock = threading.RLock()

        # Change listeners
        self.change_listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.global_listeners: List[Callable] = []

        # State history for undo/redo functionality
        self.state_history: List[Dict[str, Any]] = []
        self.max_history_size = 50
        self.current_history_index = -1

        # State persistence
        self.state_file = Path("state/app_state.json")
        self.backup_file = Path("state/app_state_backup.json")
        self.auto_save_enabled = True
        self.auto_save_interval = 30.0  # seconds
        self.last_save_time = datetime.now()

        # State validation
        self.validators: Dict[str, Callable[[Any], bool]] = {}
        self.migrations: Dict[str, Callable[[Any], Any]] = {}

        # Performance tracking
        self.state_access_count = 0
        self.state_change_count = 0
        self.last_performance_check = datetime.now()

        # Initialize state directories
        self._initialize_directories()

        # Load initial state
        self._load_state()

        # Setup default validators
        self._setup_default_validators()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO, "state_manager_init", "State manager initialized"
        )

    def _initialize_directories(self):
        """Initialize state storage directories"""

        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.backup_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "directory_initialization"},
                AIComponent.KIRO,
            )

    def _setup_default_validators(self):
        """Setup default state validators"""

        # Path validators
        self.validators["current_folder"] = lambda x: x is None or isinstance(x, Path)
        self.validators["selected_image"] = lambda x: x is None or isinstance(x, Path)

        # Numeric validators
        self.validators["thumbnail_size"] = (
            lambda x: isinstance(x, int) and 50 <= x <= 500
        )
        self.validators["map_zoom"] = lambda x: isinstance(x, int) and 1 <= x <= 20
        self.validators["current_zoom"] = (
            lambda x: isinstance(x, (int, float)) and 0.1 <= x <= 10.0
        )

        # String validators
        self.validators["current_theme"] = lambda x: isinstance(x, str) and len(x) > 0
        self.validators["performance_mode"] = lambda x: x in [
            "performance",
            "balanced",
            "quality",
        ]
        self.validators["image_sort_mode"] = lambda x: x in [
            "name",
            "date",
            "size",
            "type",
        ]

    # Core state management

    def get_state(self) -> ApplicationState:
        """
        Get the current application state

        Returns:
            ApplicationState: Current application state
        """
        try:
            return self.app_state
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.STATE_ERROR,
                {"operation": "get_state"},
                AIComponent.KIRO,
            )
            # Return default state on error
            return ApplicationState()

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """
        Get a state value

        Args:
            key: State key (supports dot notation)
            default: Default value if key not found

        Returns:
            State value or default
        """

        with self.state_lock:
            try:
                self.state_access_count += 1

                # Handle dot notation
                keys = key.split(".")
                value = self.app_state

                for k in keys:
                    if hasattr(value, k):
                        value = getattr(value, k)
                    else:
                        return default

                return value

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "get_state_value", "key": key},
                    AIComponent.KIRO,
                )
                return default

    def set_state_value(
        self, key: str, value: Any, component: AIComponent = AIComponent.KIRO
    ) -> bool:
        """
        Set a state value

        Args:
            key: State key (supports dot notation)
            value: Value to set
            component: AI component making the change

        Returns:
            True if value was set successfully
        """

        with self.state_lock:
            try:
                # Validate the value
                if not self._validate_state_value(key, value):
                    return False

                # Get old value for change notification
                old_value = self.get_state_value(key)

                # Handle dot notation
                keys = key.split(".")
                target = self.app_state

                # Navigate to parent of target key
                for k in keys[:-1]:
                    if not hasattr(target, k):
                        return False
                    target = getattr(target, k)

                # Set the value
                final_key = keys[-1]
                if hasattr(target, final_key):
                    setattr(target, final_key, value)

                    # Update activity timestamp
                    self.app_state.update_activity()
                    self.state_change_count += 1

                    # Add to history
                    self._add_to_history()

                    # Notify listeners
                    self._notify_change_listeners(key, old_value, value, component)

                    # Auto-save if enabled
                    if self.auto_save_enabled:
                        self._auto_save_if_needed()

                    self.logger_system.log_ai_operation(
                        component, "state_change", f"State changed: {key} = {value}"
                    )

                    return True

                return False

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "set_state_value", "key": key},
                    component,
                )
                return False

    def update_state(self, component: AIComponent = AIComponent.KIRO, **kwargs) -> bool:
        """
        Update multiple state values at once

        Args:
            component: AI component making the changes
            **kwargs: Key-value pairs to update

        Returns:
            True if all updates were successful
        """

        success = True

        for key, value in kwargs.items():
            if not self.set_state_value(key, value, component):
                success = False

        return success

    def _validate_state_value(self, key: str, value: Any) -> bool:
        """Validate a state value"""

        try:
            # Check if we have a validator for this key
            if key in self.validators:
                return self.validators[key](value)

            # Default validation (allow anything)
            return True

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO,
                e,
                "state_validation",
                {"key": key, "value": str(value)},
            )
            return False

    # Change notification system

    def add_change_listener(self, key: str, listener: Callable[[str, Any, Any], None]):
        """
        Add a change listener for a specific key

        Args:
            key: State key to listen for changes
            listener: Callback function (key, old_value, new_value)
        """

        with self.state_lock:
            if listener not in self.change_listeners[key]:
                self.change_listeners[key].append(listener)

    def remove_change_listener(
        self, key: str, listener: Callable[[str, Any, Any], None]
    ):
        """
        Remove a change listener

        Args:
            key: State key
            listener: Callback function to remove
        """

        with self.state_lock:
            if listener in self.change_listeners[key]:
                self.change_listeners[key].remove(listener)

    def add_global_listener(self, listener: Callable[[StateChangeEvent], None]):
        """
        Add a global change listener

        Args:
            listener: Callback function that receives StateChangeEvent
        """

        with self.state_lock:
            if listener not in self.global_listeners:
                self.global_listeners.append(listener)

    def remove_global_listener(self, listener: Callable[[StateChangeEvent], None]):
        """
        Remove a global change listener

        Args:
            listener: Callback function to remove
        """

        with self.state_lock:
            if listener in self.global_listeners:
                self.global_listeners.remove(listener)

    def _notify_change_listeners(
        self, key: str, old_value: Any, new_value: Any, component: AIComponent
    ):
        """Notify all relevant change listeners"""

        try:
            # Create change event
            event = StateChangeEvent(
                key=key, old_value=old_value, new_value=new_value, component=component
            )

            # Notify key-specific listeners
            for listener in self.change_listeners.get(key, []):
                try:
                    listener(key, old_value, new_value)
                except Exception as e:
                    self.logger_system.log_error(
                        AIComponent.KIRO,
                        e,
                        "change_listener_error",
                        {"key": key, "listener": str(listener)},
                    )

            # Notify global listeners
            for listener in self.global_listeners:
                try:
                    listener(event)
                except Exception as e:
                    self.logger_system.log_error(
                        AIComponent.KIRO,
                        e,
                        "global_listener_error",
                        {"key": key, "listener": str(listener)},
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "change_notification", "key": key},
                AIComponent.KIRO,
            )

    # State history and undo/redo

    def _add_to_history(self):
        """Add current state to history"""

        try:
            # Convert state to dictionary
            state_dict = self._state_to_dict()

            # Remove future history if we're not at the end
            if self.current_history_index < len(self.state_history) - 1:
                self.state_history = self.state_history[
                    : self.current_history_index + 1
                ]

            # Add new state
            self.state_history.append(copy.deepcopy(state_dict))
            self.current_history_index = len(self.state_history) - 1

            # Limit history size
            if len(self.state_history) > self.max_history_size:
                self.state_history.pop(0)
                self.current_history_index -= 1

        except Exception as e:
            self.logger_system.log_error(AIComponent.KIRO, e, "history_management", {})

    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return self.current_history_index > 0

    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return self.current_history_index < len(self.state_history) - 1

    def undo(self) -> bool:
        """Undo last state change"""

        with self.state_lock:
            if not self.can_undo():
                return False

            try:
                self.current_history_index -= 1
                previous_state = self.state_history[self.current_history_index]

                # Restore state without adding to history
                self._restore_state_from_dict(previous_state, add_to_history=False)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_undo",
                    f"State undone to index {self.current_history_index}",
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "state_undo"},
                    AIComponent.KIRO,
                )
                return False

    def redo(self) -> bool:
        """Redo next state change"""

        with self.state_lock:
            if not self.can_redo():
                return False

            try:
                self.current_history_index += 1
                next_state = self.state_history[self.current_history_index]

                # Restore state without adding to history
                self._restore_state_from_dict(next_state, add_to_history=False)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_redo",
                    f"State redone to index {self.current_history_index}",
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "state_redo"},
                    AIComponent.KIRO,
                )
                return False

    # State persistence

    def save_state(self, file_path: Optional[Path] = None) -> bool:
        """
        Save current state to file

        Args:
            file_path: Optional custom file path

        Returns:
            True if saved successfully
        """

        with self.state_lock:
            try:
                target_file = file_path or self.state_file

                # Create backup of existing file
                if target_file.exists():
                    backup_path = target_file.with_suffix(".backup")
                    target_file.rename(backup_path)

                # Convert state to dictionary
                state_dict = self._state_to_dict()

                # Add metadata
                state_dict["_metadata"] = {
                    "version": "1.0",
                    "saved_at": datetime.now().isoformat(),
                    "state_changes": self.state_change_count,
                    "state_accesses": self.state_access_count,
                }

                # Save to file
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(state_dict, f, indent=2, default=str)

                self.last_save_time = datetime.now()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO, "state_save", f"State saved to {target_file}"
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {
                        "operation": "state_save",
                        "file_path": str(file_path or self.state_file),
                    },
                    AIComponent.KIRO,
                )
                return False

    def _load_state(self, file_path: Optional[Path] = None) -> bool:
        """Load state from file"""

        with self.state_lock:
            try:
                source_file = file_path or self.state_file

                if not source_file.exists():
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "state_load",
                        "No existing state file found, using defaults",
                    )
                    return True

                with open(source_file, "r", encoding="utf-8") as f:
                    state_dict = json.load(f)

                # Check for metadata and version
                metadata = state_dict.pop("_metadata", {})
                version = metadata.get("version", "1.0")

                # Apply migrations if needed
                state_dict = self._migrate_state(state_dict, version)

                # Restore state
                self._restore_state_from_dict(state_dict)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_load",
                    f"State loaded from {source_file} (version: {version})",
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.INTEGRATION_ERROR,
                    {
                        "operation": "state_load",
                        "file_path": str(file_path or self.state_file),
                    },
                    AIComponent.KIRO,
                )
                return False

    def _auto_save_if_needed(self):
        """Auto-save state if interval has passed"""

        if not self.auto_save_enabled:
            return

        now = datetime.now()
        if (now - self.last_save_time).total_seconds() >= self.auto_save_interval:
            self.save_state()

    def _state_to_dict(self) -> Dict[str, Any]:
        """Convert application state to dictionary"""

        try:
            # Convert dataclass to dict
            state_dict = asdict(self.app_state)

            # Handle Path objects
            for key, value in state_dict.items():
                if isinstance(value, Path):
                    state_dict[key] = str(value)
                elif isinstance(value, list) and value and isinstance(value[0], Path):
                    state_dict[key] = [str(p) for p in value]

            return state_dict

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO, e, "state_to_dict_conversion", {}
            )
            return {}

    def _restore_state_from_dict(
        self, state_dict: Dict[str, Any], add_to_history: bool = True
    ):
        """Restore state from dictionary"""

        try:
            # Convert string paths back to Path objects
            if "current_folder" in state_dict and state_dict["current_folder"]:
                state_dict["current_folder"] = Path(state_dict["current_folder"])

            if "selected_image" in state_dict and state_dict["selected_image"]:
                state_dict["selected_image"] = Path(state_dict["selected_image"])

            if "folder_history" in state_dict:
                state_dict["folder_history"] = [
                    Path(p) for p in state_dict["folder_history"]
                ]

            if "loaded_images" in state_dict:
                state_dict["loaded_images"] = [
                    Path(p) for p in state_dict["loaded_images"]
                ]

            # Convert datetime strings back to datetime objects
            for key in ["session_start", "last_activity"]:
                if key in state_dict and isinstance(state_dict[key], str):
                    try:
                        state_dict[key] = datetime.fromisoformat(state_dict[key])
                    except ValueError:
                        state_dict[key] = datetime.now()

            # Update application state
            for key, value in state_dict.items():
                if hasattr(self.app_state, key):
                    setattr(self.app_state, key, value)

            # Add to history if requested
            if add_to_history:
                self._add_to_history()

        except Exception as e:
            self.logger_system.log_error(AIComponent.KIRO, e, "state_restoration", {})

    def _migrate_state(
        self, state_dict: Dict[str, Any], version: str
    ) -> Dict[str, Any]:
        """Migrate state from older versions"""

        try:
            # Apply migrations based on version
            for migration_version, migration_func in self.migrations.items():
                if version < migration_version:
                    state_dict = migration_func(state_dict)
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "state_migration",
                        f"Applied migration for version {migration_version}",
                    )

            return state_dict

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO, e, "state_migration", {"version": version}
            )
            return state_dict

    # Performance and monitoring

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of state management"""

        try:
            return {
                "state_accesses": self.state_access_count,
                "state_changes": self.state_change_count,
                "history_size": len(self.state_history),
                "current_history_index": self.current_history_index,
                "can_undo": self.can_undo(),
                "can_redo": self.can_redo(),
                "change_listeners": sum(
                    len(listeners) for listeners in self.change_listeners.values()
                ),
                "global_listeners": len(self.global_listeners),
                "auto_save_enabled": self.auto_save_enabled,
                "last_save_time": self.last_save_time.isoformat(),
                "session_duration": (
                    datetime.now() - self.app_state.session_start
                ).total_seconds(),
            }

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "performance_summary"},
                AIComponent.KIRO,
            )
            return {"status": "error"}

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current application state"""

        try:
            return {
                "current_folder": (
                    str(self.app_state.current_folder)
                    if self.app_state.current_folder
                    else None
                ),
                "selected_image": (
                    str(self.app_state.selected_image)
                    if self.app_state.selected_image
                    else None
                ),
                "loaded_images_count": len(self.app_state.loaded_images),
                "current_theme": self.app_state.current_theme,
                "thumbnail_size": self.app_state.thumbnail_size,
                "folder_history_count": len(self.app_state.folder_history),
                "performance_mode": self.app_state.performance_mode,
                "session_start": self.app_state.session_start.isoformat(),
                "last_activity": self.app_state.last_activity.isoformat(),
                "images_processed": self.app_state.images_processed,
                "error_count": self.app_state.error_count,
                "session_duration": self.app_state.session_duration,
            }

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "state_summary"},
                AIComponent.KIRO,
            )
            return {"status": "error"}

    # Cleanup and shutdown

    def clear_history(self):
        """Clear state history"""

        with self.state_lock:
            self.state_history.clear()
            self.current_history_index = -1

    def reset_state(self):
        """Reset to default state"""

        with self.state_lock:
            self.app_state = ApplicationState()
            self.clear_history()
            self._add_to_history()

    def shutdown(self):
        """Shutdown the state manager"""

        try:
            # Save current state
            self.save_state()

            # Clear listeners
            self.change_listeners.clear()
            self.global_listeners.clear()

            # Clear history
            self.clear_history()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "state_manager_shutdown",
                "State manager shutdown complete",
            )

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO, e, "state_manager_shutdown", {}
            )
