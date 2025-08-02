"""
Navigation Integration Controller

Implements NavigationIntegrationController for breadcrumb-folder navigator coordination.
Provides file system watcher integration for automatic path updates, path synchronization
between components, and error handling for path access and navigation failures.

Author: Kiro AI Integration System
Requirements: 2.1, 4.1, 4.2, 4.3, 4.4
"""

import asyncio
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .config_manager import ConfigManager
from .error_handling import ErrorCategory, IntegratedErrorHandler
from .logging_system import LoggerSystem
from .models import AIComponent
from .navigation_interfaces import (
    IFileSystemWatcher,
    INavigationAware,
    INavigationManager,
    NavigationCallback,
    PathChangeCallback,
)
from .navigation_models import NavigationEvent, NavigationState, PathInfo
from .services.file_system_watcher import FileChangeType, FileSystemWatcher


class NavigationIntegrationController:
    """
    Navigation Integration Controller for breadcrumb-folder navigator coordination

    This controller coordinates navigation between breadcrumb address bar and folder navigator,
    manages file system watcher integration for automatic path updates, implements path
    synchronization between components, and provides comprehensive error handling for
    path access and navigation failures.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        logger_system: LoggerSystem,
        file_system_watcher: Optional[FileSystemWatcher] = None,
        error_handler: Optional[IntegratedErrorHandler] = None
    ):
        """
        Initialize the navigation integration controller

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
            file_system_watcher: File system watcher instance (optional)
            error_handler: Error handler instance (optional)
        """
        self.config_manager = config_manager
        self.logger_system = logger_system
        self.logger = logger_system.get_logger(__name__)
        self.error_handler = error_handler or IntegratedErrorHandler(logger_system)

        # File system watcher integration
        self.file_system_watcher = file_system_watcher or FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        # Navigation state management
        self.current_navigation_state: Optional[NavigationState] = None
        self.navigation_history: List[Path] = []
        self.max_history_size = 50

        # Component registration system
        self.registered_components: Set[INavigationAware] = set()
        self.component_registry: Dict[str, INavigationAware] = {}
        self.navigation_managers: Dict[str, INavigationManager] = {}

        # Navigation event listeners
        self.navigation_listeners: List[NavigationCallback] = []
        self.path_change_listeners: List[PathChangeCallback] = []
        self.error_listeners: List[Callable[[str, str], None]] = []

        # Thread safety
        self._lock = threading.RLock()
        self._notification_lock = threading.Lock()

        # Path synchronization settings
        self.sync_enabled = True
        self.sync_timeout = 5.0  # seconds
        self.max_retry_attempts = 3

        # Performance tracking
        self.navigation_times: List[float] = []
        self.sync_operation_times: Dict[str, List[float]] = {}
        self.path_validation_cache: Dict[str, bool] = {}

        # Error handling and fallback
        self.fallback_path = Path.home()
        self.path_access_timeout = 3.0  # seconds

        # Initialize controller
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the navigation integration controller"""
        try:
            # Load navigation preferences from configuration
            self._load_navigation_preferences()

            # Initialize navigation history
            self._initialize_navigation_history()

            # Set up file system watcher integration
            self._setup_file_system_watcher()

            # Set up configuration change listeners
            self._setup_config_listeners()

            # Initialize with home directory
            self._initialize_default_navigation_state()

            self.logger.info("Navigation integration controller initialized successfully")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "navigation_controller_initialization"},
                AIComponent.KIRO
            )

    def _load_navigation_preferences(self) -> None:
        """Load navigation preferences from configuration"""
        try:
            # Load synchronization settings
            self.sync_enabled = self.config_manager.get_setting(
                "navigation.sync_enabled", True
            )
            self.sync_timeout = self.config_manager.get_setting(
                "navigation.sync_timeout", 5.0
            )
            self.max_retry_attempts = self.config_manager.get_setting(
                "navigation.max_retry_attempts", 3
            )

            # Load history settings
            self.max_history_size = self.config_manager.get_setting(
                "navigation.max_history_size", 50
            )

            # Load fallback path
            fallback_path_str = self.config_manager.get_setting(
                "navigation.fallback_path", str(Path.home())
            )
            self.fallback_path = Path(fallback_path_str)

            self.logger.debug(f"Loaded navigation preferences: sync_enabled={self.sync_enabled}")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "load_navigation_preferences"},
                AIComponent.KIRO
            )

    def _initialize_navigation_history(self) -> None:
        """Initialize navigation history from configuration"""
        try:
            history_data = self.config_manager.get_setting("navigation.history", [])

            # Validate and load history paths
            self.navigation_history = []
            for path_str in history_data:
                try:
                    path = Path(path_str)
                    if path.exists() and path.is_dir():
                        self.navigation_history.append(path)
                except (ValueError, OSError):
                    continue

            # Limit history size
            if len(self.navigation_history) > self.max_history_size:
                self.navigation_history = self.navigation_history[-self.max_history_size:]

            self.logger.debug(f"Initialized navigation history with {len(self.navigation_history)} entries")

        except Exception as e:
            self.logger.warning(f"Failed to initialize navigation history: {e}")

    def _setup_file_system_watcher(self) -> None:
        """Set up file system watcher integration"""
        try:
            # Add file system change listener
            self.file_system_watcher.add_change_listener(self._on_file_system_change)

            self.logger.debug("File system watcher integration setup complete")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "setup_file_system_watcher"},
                AIComponent.KIRO
            )

    def _setup_config_listeners(self) -> None:
        """Set up configuration change listeners"""
        try:
            # Add listener for navigation configuration changes
            self.config_manager.add_change_listener(self._on_config_changed)

        except Exception as e:
            self.logger.warning(f"Failed to setup config listeners: {e}")

    def _initialize_default_navigation_state(self) -> None:
        """Initialize default navigation state"""
        try:
            # Get current path from configuration or use home directory
            current_path_str = self.config_manager.get_setting(
                "navigation.current_path", str(Path.home())
            )
            current_path = Path(current_path_str)

            # Validate current path
            if not current_path.exists() or not current_path.is_dir():
                current_path = self.fallback_path

            # Create initial navigation state
            self.current_navigation_state = NavigationState(current_path=current_path)

            self.logger.debug(f"Initialized default navigation state: {current_path}")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "initialize_default_navigation_state"},
                AIComponent.KIRO
            )

    def _on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle configuration changes"""
        if key.startswith("navigation."):
            # Reload navigation preferences
            self._load_navigation_preferences()

    # Component Registration

    def register_navigation_component(
        self,
        component: INavigationAware,
        component_id: Optional[str] = None
    ) -> bool:
        """
        Register a navigation-aware component

        Args:
            component: Navigation-aware component to register
            component_id: Optional identifier for the component

        Returns:
            True if registered successfully, False otherwise
        """
        try:
            with self._lock:
                if component in self.registered_components:
                    self.logger.debug(f"Component already registered: {type(component).__name__}")
                    return True

                self.registered_components.add(component)

                # Store in registry with ID if provided
                if component_id:
                    self.component_registry[component_id] = component

                # Send current navigation state to newly registered component
                if self.current_navigation_state:
                    try:
                        event = NavigationEvent(
                            event_type="navigate",
                            target_path=self.current_navigation_state.current_path,
                            timestamp=datetime.now(),
                            success=True
                        )
                        component.on_navigation_changed(event)
                    except Exception as e:
                        self.logger.error(f"Failed to send current state to new component: {e}")

                self.logger.debug(f"Navigation component registered: {type(component).__name__}")
                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "register_navigation_component", "component_type": type(component).__name__},
                AIComponent.KIRO
            )
            return False

    def unregister_navigation_component(
        self,
        component: INavigationAware,
        component_id: Optional[str] = None
    ) -> bool:
        """
        Unregister a navigation-aware component

        Args:
            component: Component to unregister
            component_id: Optional identifier for the component

        Returns:
            True if unregistered successfully, False otherwise
        """
        try:
            with self._lock:
                success = False

                if component in self.registered_components:
                    self.registered_components.remove(component)
                    success = True

                # Remove from registry if ID provided
                if component_id and component_id in self.component_registry:
                    del self.component_registry[component_id]
                    success = True

                if success:
                    self.logger.debug(f"Navigation component unregistered: {type(component).__name__}")

                return success

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "unregister_navigation_component", "component_type": type(component).__name__},
                AIComponent.KIRO
            )
            return False

    def register_navigation_manager(self, name: str, manager: INavigationManager) -> bool:
        """
        Register a navigation manager

        Args:
            name: Name identifier for the navigation manager
            manager: Navigation manager instance

        Returns:
            True if registered successfully, False otherwise
        """
        try:
            with self._lock:
                if name in self.navigation_managers:
                    self.logger.warning(f"Navigation manager '{name}' already registered, replacing")

                self.navigation_managers[name] = manager

                # Add navigation listener to manager
                manager.add_navigation_listener(self._on_manager_navigation_event)

                self.logger.info(f"Navigation manager registered: {name}")
                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "register_navigation_manager", "manager_name": name},
                AIComponent.KIRO
            )
            return False

    def unregister_navigation_manager(self, name: str) -> bool:
        """
        Unregister a navigation manager

        Args:
            name: Name identifier for the navigation manager

        Returns:
            True if unregistered successfully, False otherwise
        """
        try:
            with self._lock:
                if name in self.navigation_managers:
                    manager = self.navigation_managers[name]

                    # Remove navigation listener
                    try:
                        manager.remove_navigation_listener(self._on_manager_navigation_event)
                    except Exception as e:
                        self.logger.warning(f"Failed to remove listener from manager '{name}': {e}")

                    del self.navigation_managers[name]
                    self.logger.info(f"Navigation manager unregistered: {name}")
                    return True

                return False

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "unregister_navigation_manager", "manager_name": name},
                AIComponent.KIRO
            )
            return False

    # Navigation Coordination

    async def navigate_to_path(self, path: Path, source_component: Optional[str] = None) -> bool:
        """
        Navigate to a specific path and synchronize across all components

        Args:
            path: Target path to navigate to
            source_component: Optional identifier of the component initiating navigation

        Returns:
            True if navigation successful, False otherwise
        """
        start_time = datetime.now()

        try:
            with self._lock:
                # Validate path
                if not await self._validate_path_access(path):
                    await self._handle_navigation_error(
                        path,
                        f"Path is not accessible: {path}",
                        source_component
                    )
                    return await self._navigate_to_fallback_path()

                old_path = self.current_navigation_state.current_path if self.current_navigation_state else None

                # Update navigation state
                if not self.current_navigation_state:
                    self.current_navigation_state = NavigationState(current_path=path)
                else:
                    success = self.current_navigation_state.navigate_to_path(path)
                    if not success:
                        await self._handle_navigation_error(
                            path,
                            "Failed to update navigation state",
                            source_component
                        )
                        return await self._navigate_to_fallback_path()

                # Update file system watcher
                await self._update_file_system_watcher(path)

                # Synchronize with all registered components
                if self.sync_enabled:
                    success = await self._synchronize_navigation_state(source_component)
                    if not success:
                        self.logger.warning("Some components failed to synchronize navigation state")

                # Update navigation history
                await self._update_navigation_history(path)

                # Persist current path
                await self._persist_current_path(path)

                # Create and broadcast navigation event
                event = NavigationEvent(
                    event_type="navigate",
                    source_path=old_path,
                    target_path=path,
                    timestamp=datetime.now(),
                    success=True,
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
                await self._notify_navigation_listeners(event)

                # Record performance metrics
                navigation_time = (datetime.now() - start_time).total_seconds()
                self.navigation_times.append(navigation_time)

                self.logger.info(f"Navigation successful: {path} (took {navigation_time:.3f}s)")
                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "navigate_to_path", "path": str(path), "source": source_component},
                AIComponent.KIRO
            )
            return await self._navigate_to_fallback_path()

    async def _validate_path_access(self, path: Path) -> bool:
        """
        Validate if a path is accessible for navigation

        Args:
            path: Path to validate

        Returns:
            True if path is accessible, False otherwise
        """
        try:
            # Check cache first
            path_str = str(path)
            if path_str in self.path_validation_cache:
                return self.path_validation_cache[path_str]

            # Validate path with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self._sync_validate_path, path),
                    timeout=self.path_access_timeout
                )

                # Cache result
                self.path_validation_cache[path_str] = result

                # Limit cache size
                if len(self.path_validation_cache) > 1000:
                    # Remove oldest entries
                    keys_to_remove = list(self.path_validation_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self.path_validation_cache[key]

                return result

            except asyncio.TimeoutError:
                self.logger.warning(f"Path validation timed out: {path}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to validate path access: {path} - {e}")
            return False

    def _sync_validate_path(self, path: Path) -> bool:
        """Synchronous path validation"""
        try:
            return (
                path.exists() and
                path.is_dir() and
                os.access(path, os.R_OK)
            )
        except (OSError, PermissionError):
            return False

    async def _update_file_system_watcher(self, path: Path) -> None:
        """Update file system watcher to monitor new path"""
        try:
            # Stop current watching
            if self.file_system_watcher.is_watching:
                self.file_system_watcher.stop_watching()

            # Start watching new path
            success = self.file_system_watcher.start_watching(path)
            if success:
                self.logger.debug(f"File system watcher updated for path: {path}")
            else:
                self.logger.warning(f"Failed to start file system watcher for path: {path}")

        except Exception as e:
            self.logger.error(f"Failed to update file system watcher: {e}")

    async def _synchronize_navigation_state(self, source_component: Optional[str] = None) -> bool:
        """
        Synchronize navigation state across all registered components

        Args:
            source_component: Optional identifier of the component that initiated the change

        Returns:
            True if synchronization successful for all components, False otherwise
        """
        try:
            if not self.current_navigation_state:
                return False

            success_count = 0
            total_components = len(self.registered_components)

            if total_components == 0:
                return True  # No components to synchronize

            # Create navigation event
            event = NavigationEvent(
                event_type="navigate",
                target_path=self.current_navigation_state.current_path,
                timestamp=datetime.now(),
                success=True
            )

            # Synchronize with components (excluding source component)
            tasks = []
            for component in self.registered_components.copy():
                # Skip source component to avoid circular updates
                component_id = self._get_component_id(component)
                if component_id == source_component:
                    continue

                task = asyncio.create_task(
                    self._synchronize_component(component, event)
                )
                tasks.append(task)

            # Wait for all components with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.sync_timeout
                )

                for result in results:
                    if result is True:
                        success_count += 1
                    elif isinstance(result, Exception):
                        self.logger.error(f"Component synchronization failed: {result}")

            except asyncio.TimeoutError:
                self.logger.warning(f"Navigation synchronization timed out after {self.sync_timeout}s")

            # Consider successful if at least 50% of components succeeded
            success_rate = success_count / max(len(tasks), 1) if tasks else 1.0
            return success_rate >= 0.5

        except Exception as e:
            self.logger.error(f"Failed to synchronize navigation state: {e}")
            return False

    async def _synchronize_component(self, component: INavigationAware, event: NavigationEvent) -> bool:
        """Synchronize a single component with navigation state"""
        try:
            component_name = type(component).__name__
            start_time = datetime.now()

            # Check if component supports the event type
            supported_events = component.get_supported_navigation_events()
            if event.event_type not in supported_events:
                return True  # Skip unsupported events

            component.on_navigation_changed(event)

            # Record performance
            sync_time = (datetime.now() - start_time).total_seconds()
            if component_name not in self.sync_operation_times:
                self.sync_operation_times[component_name] = []
            self.sync_operation_times[component_name].append(sync_time)

            return True

        except Exception as e:
            self.logger.error(f"Failed to synchronize component {type(component).__name__}: {e}")
            return False

    def _get_component_id(self, component: INavigationAware) -> Optional[str]:
        """Get component ID from registry"""
        for component_id, registered_component in self.component_registry.items():
            if registered_component is component:
                return component_id
        return None

    async def _update_navigation_history(self, path: Path) -> None:
        """Update navigation history"""
        try:
            # Remove path if it already exists
            if path in self.navigation_history:
                self.navigation_history.remove(path)

            # Add to beginning of history
            self.navigation_history.insert(0, path)

            # Limit history size
            if len(self.navigation_history) > self.max_history_size:
                self.navigation_history = self.navigation_history[:self.max_history_size]

            # Persist history
            await self._persist_navigation_history()

        except Exception as e:
            self.logger.error(f"Failed to update navigation history: {e}")

    async def _persist_current_path(self, path: Path) -> None:
        """Persist current path to configuration"""
        try:
            self.config_manager.set_setting("navigation.current_path", str(path))
            await asyncio.to_thread(self.config_manager.save_config)

        except Exception as e:
            self.logger.error(f"Failed to persist current path: {e}")

    async def _persist_navigation_history(self) -> None:
        """Persist navigation history to configuration"""
        try:
            history_data = [str(path) for path in self.navigation_history]
            self.config_manager.set_setting("navigation.history", history_data)
            await asyncio.to_thread(self.config_manager.save_config)

        except Exception as e:
            self.logger.error(f"Failed to persist navigation history: {e}")

    async def _navigate_to_fallback_path(self) -> bool:
        """Navigate to fallback path in case of errors"""
        try:
            if self.fallback_path.exists() and self.fallback_path.is_dir():
                self.logger.info(f"Navigating to fallback path: {self.fallback_path}")
                return await self.navigate_to_path(self.fallback_path, "fallback")
            else:
                self.logger.error("Fallback path is not accessible")
                return False

        except Exception as e:
            self.logger.error(f"Failed to navigate to fallback path: {e}")
            return False

    # File System Event Handling

    def _on_file_system_change(
        self,
        file_path: Path,
        change_type: FileChangeType,
        old_path: Optional[Path] = None
    ) -> None:
        """Handle file system change events"""
        try:
            if not self.current_navigation_state:
                return

            current_path = self.current_navigation_state.current_path

            # Check if the change affects current navigation path
            if self._path_affects_navigation(file_path, current_path):
                asyncio.create_task(self._handle_path_change(file_path, change_type, old_path))

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "file_system_change_handler", "file_path": str(file_path)},
                AIComponent.KIRO
            )

    def _path_affects_navigation(self, changed_path: Path, current_path: Path) -> bool:
        """Check if a path change affects current navigation"""
        try:
            # Check if changed path is current path or affects it
            return (
                changed_path == current_path or
                current_path.is_relative_to(changed_path) or
                changed_path.parent == current_path
            )

        except (ValueError, OSError):
            return False

    async def _handle_path_change(
        self,
        file_path: Path,
        change_type: FileChangeType,
        old_path: Optional[Path] = None
    ) -> None:
        """Handle path changes that affect navigation"""
        try:
            current_path = self.current_navigation_state.current_path

            if change_type == FileChangeType.DELETED and file_path == current_path:
                # Current directory was deleted, navigate to parent
                parent_path = current_path.parent
                if parent_path.exists() and parent_path.is_dir():
                    await self.navigate_to_path(parent_path, "file_system_watcher")
                else:
                    await self._navigate_to_fallback_path()

            elif change_type == FileChangeType.MOVED and old_path == current_path:
                # Current directory was moved, follow the move
                if file_path.exists() and file_path.is_dir():
                    await self.navigate_to_path(file_path, "file_system_watcher")
                else:
                    await self._navigate_to_fallback_path()

            else:
                # Other changes in current directory, refresh navigation state
                if self.current_navigation_state:
                    self.current_navigation_state.refresh()

                    # Notify components of path refresh
                    event = NavigationEvent(
                        event_type="refresh",
                        target_path=current_path,
                        timestamp=datetime.now(),
                        success=True
                    )
                    await self._notify_navigation_listeners(event)

        except Exception as e:
            self.logger.error(f"Failed to handle path change: {e}")

    # Navigation Manager Event Handling

    def _on_manager_navigation_event(self, event: NavigationEvent) -> None:
        """Handle navigation events from registered managers"""
        try:
            if event.success and event.target_path:
                # Propagate navigation to other components
                asyncio.create_task(
                    self.navigate_to_path(event.target_path, "navigation_manager")
                )

        except Exception as e:
            self.logger.error(f"Failed to handle manager navigation event: {e}")

    # Error Handling

    async def _handle_navigation_error(
        self,
        path: Path,
        error_message: str,
        source_component: Optional[str] = None
    ) -> None:
        """Handle navigation errors and notify listeners"""
        try:
            self.logger.error(f"Navigation error for '{path}': {error_message}")

            # Create error event
            event = NavigationEvent(
                event_type="navigate",
                target_path=path,
                timestamp=datetime.now(),
                success=False,
                error_message=error_message
            )

            # Notify error listeners
            await self._notify_error_listeners(str(path), error_message)

            # Notify navigation listeners of failed event
            await self._notify_navigation_listeners(event)

        except Exception as e:
            self.logger.error(f"Failed to handle navigation error: {e}")

    # Event Listener Management

    def add_navigation_listener(self, callback: NavigationCallback) -> bool:
        """
        Add a navigation event listener

        Args:
            callback: Callback function for navigation events

        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback not in self.navigation_listeners:
                    self.navigation_listeners.append(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to add navigation listener: {e}")
            return False

    def remove_navigation_listener(self, callback: NavigationCallback) -> bool:
        """
        Remove a navigation event listener

        Args:
            callback: Callback function to remove

        Returns:
            True if listener removed successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback in self.navigation_listeners:
                    self.navigation_listeners.remove(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove navigation listener: {e}")
            return False

    def add_path_change_listener(self, callback: PathChangeCallback) -> bool:
        """
        Add a path change listener

        Args:
            callback: Callback function for path changes

        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback not in self.path_change_listeners:
                    self.path_change_listeners.append(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to add path change listener: {e}")
            return False

    def add_error_listener(self, callback: Callable[[str, str], None]) -> bool:
        """
        Add an error listener

        Args:
            callback: Callback function for errors (path, error_message) -> None

        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback not in self.error_listeners:
                    self.error_listeners.append(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to add error listener: {e}")
            return False

    async def _notify_navigation_listeners(self, event: NavigationEvent) -> None:
        """Notify navigation event listeners"""
        try:
            with self._notification_lock:
                listeners = self.navigation_listeners.copy()

            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(event)
                    else:
                        listener(event)
                except Exception as e:
                    self.logger.error(f"Navigation listener failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to notify navigation listeners: {e}")

    async def _notify_path_change_listeners(self, path: Path, event_type: str) -> None:
        """Notify path change listeners"""
        try:
            with self._notification_lock:
                listeners = self.path_change_listeners.copy()

            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(path, event_type)
                    else:
                        listener(path, event_type)
                except Exception as e:
                    self.logger.error(f"Path change listener failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to notify path change listeners: {e}")

    async def _notify_error_listeners(self, path: str, error_message: str) -> None:
        """Notify error listeners"""
        try:
            with self._notification_lock:
                listeners = self.error_listeners.copy()

            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(path, error_message)
                    else:
                        listener(path, error_message)
                except Exception as e:
                    self.logger.error(f"Error listener failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to notify error listeners: {e}")

    # Public API

    def get_current_navigation_state(self) -> Optional[NavigationState]:
        """
        Get the current navigation state

        Returns:
            Current navigation state or None if not initialized
        """
        return self.current_navigation_state

    def get_navigation_history(self) -> List[Path]:
        """
        Get navigation history

        Returns:
            List of paths in navigation history
        """
        return self.navigation_history.copy()

    def get_registered_components(self) -> List[str]:
        """
        Get list of registered component IDs

        Returns:
            List of registered component identifiers
        """
        return list(self.component_registry.keys())

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics

        Returns:
            Dictionary with performance statistics
        """
        avg_navigation_time = (
            sum(self.navigation_times) / len(self.navigation_times)
            if self.navigation_times else 0.0
        )

        return {
            "navigation_count": len(self.navigation_times),
            "average_navigation_time": avg_navigation_time,
            "registered_components": len(self.registered_components),
            "registered_managers": len(self.navigation_managers),
            "history_size": len(self.navigation_history),
            "sync_enabled": self.sync_enabled,
            "cache_size": len(self.path_validation_cache),
            "sync_operation_times": dict(self.sync_operation_times)
        }

    def clear_performance_stats(self) -> None:
        """Clear performance statistics"""
        self.navigation_times.clear()
        self.sync_operation_times.clear()

    def clear_path_validation_cache(self) -> None:
        """Clear path validation cache"""
        self.path_validation_cache.clear()

    async def shutdown(self) -> None:
        """Shutdown the navigation integration controller"""
        try:
            # Stop file system watcher
            if self.file_system_watcher.is_watching:
                self.file_system_watcher.stop_watching()

            # Persist current state
            if self.current_navigation_state:
                await self._persist_current_path(self.current_navigation_state.current_path)

            await self._persist_navigation_history()

            # Clear listeners
            with self._notification_lock:
                self.navigation_listeners.clear()
                self.path_change_listeners.clear()
                self.error_listeners.clear()

            # Clear registrations
            with self._lock:
                self.registered_components.clear()
                self.component_registry.clear()
                self.navigation_managers.clear()

            self.logger.info("Navigation integration controller shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during navigation controller shutdown: {e}")
