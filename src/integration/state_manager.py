"""
Application State Manager for AI Integration

Manages centralized application state across all AI implementations:
- GitHub Copilot (CS4Coding): Core functionality state
- Cursor (CursorBLD): UI state and user preferences
- Kiro: Integration state and performance metrics

Author: Kiro AI Integration System
"""

import asyncio
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import asdict
import json

from .models import ApplicationState, ImageMetadata, AIComponent, PerformanceMetrics
from .config_manager import ConfigManager
from .error_handling import IntegratedErrorHandler, ErrorCategory
from .logging_system import LoggerSystem


class StateManager:
    """
    Centralized application state manager that coordinates state across AI implementations

    Features:
    - Thread-safe state management
    - State persistence and recovery
    - Change notifications and event handling
    - State validation and rollback
    - Performance state tracking
    """

    def __init__(self,
                 config_manager: ConfigManager,
                 logger_system: LoggerSystem = None,
                 error_handler: IntegratedErrorHandler = None):
        """
        Initialize the state manager

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
            error_handler: Error handler instance
        """

        self.config_manager = config_manager
        self.logger_system = log or LoggerSystem()
        self.error_handler = error_handler or IntegratedErrorHandler(self.logger_system)

        # Application state
        self.app_state = ApplicationState()
        self.state_history: List[ApplicationState] = []
        self.max_history_size = 100

        # State persistence
        self.state_file = Path("config/app_state.json")
        self.auto_save_enabled = True
        self.auto_save_interval = 30  # seconds
        self.last_save_time = datetime.now()

        # Thread safety
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()

        # Change tracking
        self.change_listeners: Dict[str, List[Callable]] = {}
        self.state_validators: Dict[str, Callable] = {}

        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.performance_window = timedelta(hours=1)  # Keep 1 hour of metrics

        # AI component states
        self.ai_states: Dict[AIComponent, Dict[str, Any]] = {
            AIComponent.COPILOT: {"active": True, "last_operation": None, "error_count": 0},
            AIComponent.CURSOR: {"active": True, "last_operation": None, "error_count": 0},
            AIComponent.KIRO: {"active": True, "last_operation": None, "error_count": 0}
        }

        # Initialize
        self._initialize()

        # Start background tasks
        self._start_background_tasks()

    def _initialize(self):
        """Initialize the state manager"""

        try:
            # Load persisted state
            self._load_state()

            # Setup state validators
            self._setup_validators()

            # Register configuration change listener
            self.config_manager.add_change_listener(self._on_config_change)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "state_initialization",
                "State manager initialized successfully"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "state_initialization"},
                AIComponent.KIRO
            )

    def _setup_validators(self):
        """Setup state validation functions"""

        self.state_validators = {
            "current_folder": self._validate_folder_path,
            "selected_image": self._validate_image_path,
            "thumbnail_size": self._validate_thumbnail_size,
            "current_theme": self._validate_theme_name,
            "performance_mode": self._validate_performance_mode
        }

    def _start_background_tasks(self):
        """Start background tasks for state management"""

        # Auto-save task
        if self.auto_save_enabled:
            threading.Thread(
                target=self._auto_save_worker,
                daemon=True,
                name="StateManager-AutoSave"
            ).start()

        # Performance cleanup task
        threading.Thread(
            target=self._performance_cleanup_worker,
            daemon=True,
            name="StateManager-PerformanceCleanup"
        ).start()

    def _auto_save_worker(self):
        """Background worker for automatic state saving"""

        while not self._shutdown_event.is_set():
            try:
                # Wait for the save interval
                if self._shutdown_event.wait(self.auto_save_interval):
                    break

                # Check if state has changed since last save
                if datetime.now() - self.last_save_time > timedelta(seconds=self.auto_save_interval):
                    self._save_state()

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "auto_save"},
                    AIComponent.KIRO
                )

    def _performance_cleanup_worker(self):
        """Background worker for performance metrics cleanup"""

        while not self._shutdown_event.is_set():
            try:
                # Wait for cleanup interval (every 10 minutes)
                if self._shutdown_event.wait(600):
                    break

                # Clean old performance metrics
                cutoff_time = datetime.now() - self.performance_window
                self.performance_history = [
                    metric for metric in self.performance_history
                    if metric.timestamp > cutoff_time
                ]

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "performance_cleanup"},
                    AIComponent.KIRO
                )

    # State access methods

    def get_state(self) -> ApplicationState:
        """
        Get the current application state

        Returns:
            Current ApplicationState instance
        """

        with self._lock:
            return self.app_state

    def update_state(self, **kwargs) -> bool:
        """
        Update application state with new values

        Args:
            **kwargs: State attributes to update

        Returns:
            True if update successful, False otherwise
        """

        with self._lock:
            try:
                # Validate changes
                for key, value in kwargs.items():
                    if not self._validate_state_change(key, value):
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "state_validation",
                            f"State validation failed for {key} = {value}",
                            level="WARNING"
                        )
                        return False

                # Save current state to history
                self._save_to_history()

                # Apply changes
                old_values = {}
                for key, value in kwargs.items():
                    if hasattr(self.app_state, key):
                        old_values[key] = getattr(self.app_state, key)
                        setattr(self.app_state, key, value)

                # Update activity timestamp
                self.app_state.update_activity()

                # Notify change listeners
                for key, value in kwargs.items():
                    self._notify_change_listeners(key, old_values.get(key), value)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_update",
                    f"State updated: {list(kwargs.keys())}"
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "state_update", "changes": str(kwargs)},
                    AIComponent.KIRO
                )
                return False

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific state value

        Args:
            key: State attribute name
            default: Default value if attribute not found

        Returns:
            State value or default
        """

        with self._lock:
            return getattr(self.app_state, key, default)

    def set_state_value(self, key: str, value: Any) -> bool:
        """
        Set a specific state value

        Args:
            key: State attribute name
            value: Value to set

        Returns:
            True if set successfully, False otherwise
        """

        return self.update_state(**{key: value})

    # AI component state management

    def update_ai_state(self, ai_component: AIComponent, **kwargs) -> bool:
        """
        Update AI component-specific state

        Args:
            ai_component: AI component to update
            **kwargs: State values to update

        Returns:
            True if updated successfully, False otherwise
        """

        with self._lock:
            try:
                if ai_component not in self.ai_states:
                    self.ai_states[ai_component] = {}

                # Update AI state
                old_values = {}
                for key, value in kwargs.items():
                    old_values[key] = self.ai_states[ai_component].get(key)
                    self.ai_states[ai_component][key] = value

                # Update main application state
                self.app_state.ai_component_status[ai_component.value] = kwargs.get("status", "active")

                self.logger_system.log_ai_operation(
                    ai_component,
                    "ai_state_update",
                    f"AI state updated: {list(kwargs.keys())}"
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "ai_state_update", "ai_component": ai_component.value},
                    ai_component
                )
                return False

    def get_ai_state(self, ai_component: AIComponent) -> Dict[str, Any]:
        """
        Get AI component-specific state

        Args:
            ai_component: AI component

        Returns:
            AI component state dictionary
        """

        with self._lock:
            return self.ai_states.get(ai_component, {}).copy()

    # Performance metrics management

    def add_performance_metrics(self, metrics: PerformanceMetrics):
        """
        Add performance metrics to history

        Args:
            metrics: Performance metrics to add
        """

        with self._lock:
            self.performance_history.append(metrics)

            # Update application state with latest metrics
            self.app_state.memory_usage_history.append(
                (metrics.timestamp, metrics.memory_usage_mb)
            )

            # Keep only recent memory usage history
            cutoff_time = datetime.now() - timedelta(hours=1)
            self.app_state.memory_usage_history = [
                (timestamp, usage) for timestamp, usage in self.app_state.memory_usage_history
                if timestamp > cutoff_time
            ]

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance metrics summary

        Returns:
            Performance summary dictionary
        """

        with self._lock:
            if not self.performance_history:
                return {"status": "no_data"}

            recent_metrics = self.performance_history[-10:]  # Last 10 metrics

            avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
            avg_cpu = sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics)

            total_operations = sum(m.total_operations for m in recent_metrics)

            return {
                "average_memory_mb": avg_memory,
                "average_cpu_percent": avg_cpu,
                "total_operations": total_operations,
                "metrics_count": len(self.performance_history),
                "latest_timestamp": recent_metrics[-1].timestamp.isoformat(),
                "ai_operations": {
                    "copilot": sum(m.copilot_operations for m in recent_metrics),
                    "cursor": sum(m.cursor_operations for m in recent_metrics),
                    "kiro": sum(m.kiro_operations for m in recent_metrics)
                }
            }

    # State persistence

    def _save_state(self):
        """Save current state to persistent storage"""

        try:
            with self._lock:
                # Prepare state data for serialization
                state_data = {
                    "app_state": self._serialize_app_state(),
                    "ai_states": {
                        ai.value: state for ai, state in self.ai_states.items()
                    },
                    "performance_summary": self.get_performance_summary(),
                    "save_timestamp": datetime.now().isoformat(),
                    "session_duration": self.app_state.session_duration
                }

                # Ensure config directory exists
                self.state_file.parent.mkdir(parents=True, exist_ok=True)

                # Save to file
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2, default=str)

                self.last_save_time = datetime.now()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_save",
                    f"Application state saved to {self.state_file}"
                )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "state_save"},
                AIComponent.KIRO
            )

    def _load_state(self):
        """Load state from persistent storage"""

        try:
            if not self.state_file.exists():
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_load",
                    "No saved state file found, using defaults"
                )
                return

            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # Restore application state
            if "app_state" in state_data:
                self._deserialize_app_state(state_data["app_state"])

            # Restore AI states
            if "ai_states" in state_data:
                for ai_name, ai_state in state_data["ai_states"].items():
                    try:
                        ai_component = AIComponent(ai_name)
                        self.ai_states[ai_component] = ai_state
                    except ValueError:
                        continue

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "state_load",
                f"Application state loaded from {self.state_file}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "state_load"},
                AIComponent.KIRO
            )

    def _serialize_app_state(self) -> Dict[str, Any]:
        """Serialize application state for storage"""

        # Convert ApplicationState to dictionary
        state_dict = asdict(self.app_state)

        # Convert Path objects to strings
        if state_dict.get("current_folder"):
            state_dict["current_folder"] = str(state_dict["current_folder"])

        if state_dict.get("selected_image"):
            state_dict["selected_image"] = str(state_dict["selected_image"])

        if state_dict.get("loaded_images"):
            state_dict["loaded_images"] = [str(p) for p in state_dict["loaded_images"]]

        if state_dict.get("folder_history"):
            state_dict["folder_history"] = [str(p) for p in state_dict["folder_history"]]

        # Convert datetime objects to ISO strings
        if state_dict.get("session_start"):
            state_dict["session_start"] = state_dict["session_start"].isoformat()

        if state_dict.get("last_activity"):
            state_dict["last_activity"] = state_dict["last_activity"].isoformat()

        # Convert memory usage history
        if state_dict.get("memory_usage_history"):
            state_dict["memory_usage_history"] = [
                (timestamp.isoformat(), usage)
                for timestamp, usage in state_dict["memory_usage_history"]
            ]

        return state_dict

    def _deserialize_app_state(self, state_dict: Dict[str, Any]):
        """Deserialize application state from storage"""

        # Convert string paths back to Path objects
        if state_dict.get("current_folder"):
            self.app_state.current_folder = Path(state_dict["current_folder"])

        if state_dict.get("selected_image"):
            self.app_state.selected_image = Path(state_dict["selected_image"])

        if state_dict.get("loaded_images"):
            self.app_state.loaded_images = [Path(p) for p in state_dict["loaded_images"]]

        if state_dict.get("folder_history"):
            self.app_state.folder_history = [Path(p) for p in state_dict["folder_history"]]

        # Convert ISO strings back to datetime objects
        if state_dict.get("session_start"):
            self.app_state.session_start = datetime.fromisoformat(state_dict["session_start"])

        if state_dict.get("last_activity"):
            self.app_state.last_activity = datetime.fromisoformat(state_dict["last_activity"])

        # Convert memory usage history
        if state_dict.get("memory_usage_history"):
            self.app_state.memory_usage_history = [
                (datetime.fromisoformat(timestamp), usage)
                for timestamp, usage in state_dict["memory_usage_history"]
            ]

        # Restore other simple attributes
        simple_attrs = [
            "current_theme", "thumbnail_size", "map_center", "map_zoom",
            "exif_display_mode", "image_sort_mode", "image_sort_ascending",
            "current_zoom", "current_pan", "fit_mode", "performance_mode",
            "images_processed", "error_count"
        ]

        for attr in simple_attrs:
            if attr in state_dict:
                setattr(self.app_state, attr, state_dict[attr])

    # State validation

    def _validate_state_change(self, key: str, value: Any) -> bool:
        """Validate a state change"""

        validator = self.state_validators.get(key)
        if validator:
            return validator(value)

        # If no specific validator, allow the change
        return True

    def _validate_folder_path(self, path: Any) -> bool:
        """Validate folder path"""

        if path is None:
            return True

        if isinstance(path, (str, Path)):
            path_obj = Path(path)
            return path_obj.exists() and path_obj.is_dir()

        return False

    def _validate_image_path(self, path: Any) -> bool:
        """Validate image path"""

        if path is None:
            return True

        if isinstance(path, (str, Path)):
            path_obj = Path(path)
            return path_obj.exists() and path_obj.is_file()

        return False

    def _validate_thumbnail_size(self, size: Any) -> bool:
        """Validate thumbnail size"""

        if isinstance(size, int):
            return 50 <= size <= 500

        return False

    def _validate_theme_name(self, theme: Any) -> bool:
        """Validate theme name"""

        if isinstance(theme, str):
            # Get available themes from config
            available_themes = self.config_manager.get_setting("ui.available_themes", [])
            return theme in available_themes or theme == "default"

        return False

    def _validate_performance_mode(self, mode: Any) -> bool:
        """Validate performance mode"""

        valid_modes = ["performance", "balanced", "quality"]
        return mode in valid_modes

    # Event handling

    def add_change_listener(self, key: str, listener: Callable):
        """Add a state change listener for specific key"""

        if key not in self.change_listeners:
            self.change_listeners[key] = []

        if listener not in self.change_listeners[key]:
            self.change_listeners[key].append(listener)

    def remove_change_listener(self, key: str, listener: Callable):
        """Remove a state change listener"""

        if key in self.change_listeners:
            try:
                self.change_listeners[key].remove(listener)
            except ValueError:
                pass

    def _notify_change_listeners(self, key: str, old_value: Any, new_value: Any):
        """Notify change listeners for a specific key"""

        listeners = self.change_listeners.get(key, [])
        for listener in listeners:
            try:
                listener(key, old_value, new_value)
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "change_notification", "key": key},
                    AIComponent.KIRO
                )

    def _on_config_change(self, key: str, old_value: Any, new_value: Any):
        """Handle configuration changes"""

        # Update application state based on configuration changes
        if key == "ui.theme":
            self.update_state(current_theme=new_value)
        elif key == "ui.thumbnail_size":
            self.update_state(thumbnail_size=new_value)
        elif key == "performance.mode":
            self.update_state(performance_mode=new_value)

    # History management

    def _save_to_history(self):
        """Save current state to history"""

        # Create a copy of current state
        state_copy = ApplicationState(
            current_folder=self.app_state.current_folder,
            selected_image=self.app_state.selected_image,
            current_theme=self.app_state.current_theme,
            thumbnail_size=self.app_state.thumbnail_size,
            performance_mode=self.app_state.performance_mode
        )

        self.state_history.append(state_copy)

        # Limit history size
        if len(self.state_history) > self.max_history_size:
            self.state_history = self.state_history[-self.max_history_size:]

    def get_state_history(self, count: int = 10) -> List[ApplicationState]:
        """Get recent state history"""

        with self._lock:
            return self.state_history[-count:]

    def rollback_state(self, steps: int = 1) -> bool:
        """Rollback state to previous version"""

        with self._lock:
            if len(self.state_history) < steps:
                return False

            try:
                # Get previous state
                previous_state = self.state_history[-(steps + 1)]

                # Restore key attributes
                self.app_state.current_folder = previous_state.current_folder
                self.app_state.selected_image = previous_state.selected_image
                self.app_state.current_theme = previous_state.current_theme
                self.app_state.thumbnail_size = previous_state.thumbnail_size
                self.app_state.performance_mode = previous_state.performance_mode

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_rollback",
                    f"State rolled back {steps} steps"
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.INTEGRATION_ERROR,
                    {"operation": "state_rollback", "steps": steps},
                    AIComponent.KIRO
                )
                return False

    # Shutdown

    def shutdown(self):
        """Shutdown the state manager"""

        try:
            # Signal shutdown to background workers
            self._shutdown_event.set()

            # Save final state
            self._save_state()

            # Remove configuration change listener
            self.config_manager.remove_change_listener(self._on_config_change)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "state_shutdown",
                "State manager shutdown completed"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "state_shutdown"},
                AIComponent.KIRO
            )
