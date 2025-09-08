"""
Theme Integration Controller

Implements ThemeIntegrationController for cross-component theme management.
Provides theme persistence, change notification system, and error handling
for theme loading and application failures.

Author: Kiro AI Integration System
Requirements: 1.2, 1.3, 1.4, 5.1, 5.2
"""

import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .config_manager import ConfigManager
from .error_handling import ErrorCategory, IntegratedErrorHandler
from .logging_system import LoggerSystem
from .models import AIComponent
from .theme_interfaces import IThemeAware, IThemeManager
from .theme_models import ThemeConfiguration, ThemeInfo, ThemeType


class ThemeIntegrationController:
    """
    Theme Integration Controller for cross-component theme management

    This controller coordinates theme management across all UI components,
    handles theme persistence using ConfigManager, and provides a robust
    theme change notification system with error handling.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        logger_system: LoggerSystem,
        error_handler: Optional[IntegratedErrorHandler] = None
    ):
        """
        Initialize the theme integration controller

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
            error_handler: Error handler instance (opt
     """
        self.config_manager = config_manager
        self.logger_system = logger_system
        self.logger = logger_system.get_logger(__name__)
        self.error_handler = error_handler or IntegratedErrorHandler(logger_system)

        # Theme management state
        self.current_theme: Optional[ThemeConfiguration] = None
        self.available_themes: Dict[str, ThemeInfo] = {}
        self.theme_managers: Dict[str, IThemeManager] = {}

        # Component registration system
        self.registered_components: Set[IThemeAware] = set()
        self.component_registry: Dict[str, IThemeAware] = {}

        # Theme change notification system
        self.theme_change_listeners: List[Callable[[str, str], None]] = []
        self.theme_applied_listeners: List[Callable[[ThemeConfiguration], None]] = []
        self.theme_error_listeners: List[Callable[[str, str], None]] = []

        # Thread safety
        self._lock = threading.RLock()
        self._notification_lock = threading.Lock()

        # Theme persistence settings
        self.theme_config_key = "ui.theme"
        self.theme_history_key = "ui.theme_history"
        self.theme_preferences_key = "ui.theme_preferences"

        # Error handling and fallback
        self.fallback_theme = "default"
        self.theme_application_timeout = 5.0  # seconds
        self.max_retry_attempts = 3

        # Performance tracking
        self.theme_switch_times: List[float] = []
        self.component_application_times: Dict[str, List[float]] = {}

        # Initialize controller
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the theme integration controller"""
        try:
            # Load theme preferences from configuration
            self._load_theme_preferences()

            # Initialize theme history tracking
            self._initialize_theme_history()

            # Set up configuration change listeners
            self._setup_config_listeners()

            self.logger.info("Theme integration controller initialized successfully")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "theme_controller_initialization"},
                AIComponent.KIRO
            )

    def _load_theme_preferences(self) -> None:
        """Load theme preferences from configuration"""
        try:
            preferences = self.config_manager.get_setting(self.theme_preferences_key, {})

            # Load current theme
            current_theme_name = self.config_manager.get_setting(self.theme_config_key, self.fallback_theme)

            # Load theme history
            theme_history = self.config_manager.get_setting(self.theme_history_key, [])

            self.logger.debug(f"Loaded theme preferences: current={current_theme_name}, history={len(theme_history)} entries")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "load_theme_preferences"},
                AIComponent.KIRO
            )

    def _initialize_theme_history(self) -> None:
        """Initialize theme history tracking"""
        try:
            history = self.config_manager.get_setting(self.theme_history_key, [])

            # Ensure history doesn't exceed reasonable size
            max_history_size = 50
            if len(history) > max_history_size:
                history = history[-max_history_size:]
                self.config_manager.set_setting(self.theme_history_key, history)

        except Exception as e:
            self.logger.warning(f"Failed to initialize theme history: {e}")

    def _setup_config_listeners(self) -> None:
        """Set up configuration change listeners"""
        try:
            # Add listener for theme configuration changes
            self.config_manager.add_change_listener(self._on_config_changed)

        except Exception as e:
            self.logger.warning(f"Failed to setup config listeners: {e}")

    def _on_config_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Handle configuration changes"""
        if key == self.theme_config_key and old_value != new_value:
            # Theme changed externally, apply the new theme
            asyncio.create_task(self._apply_theme_from_config(new_value))

    async def _apply_theme_from_config(self, theme_name: str) -> None:
        """Apply theme from configuration change"""
        try:
            await self.apply_theme(theme_name)
        except Exception as e:
            self.logger.error(f"Failed to apply theme from config change: {e}")

    # Theme Manager Registration

    def register_theme_manager(self, name: str, theme_manager: IThemeManager) -> bool:
        """
        Register a theme manager

        Args:
            name: Name identifier for the theme manager
            theme_manager: Theme manager instance

        Returns:
            True if registered successfully, False otherwise
        """
        try:
            with self._lock:
                if name in self.theme_managers:
                    self.logger.warning(f"Theme manager '{name}' already registered, replacing")

                self.theme_managers[name] = theme_manager

                # If this is the first theme manager, load available themes
                if len(self.theme_managers) == 1:
                    self._load_available_themes()

                self.logger.info(f"Theme manager registered: {name}")
                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "register_theme_manager", "manager_name": name},
                AIComponent.KIRO
            )
            return False

    def unregister_theme_manager(self, name: str) -> bool:
        """
        Unregister a theme manager

        Args:
            name: Name identifier for the theme manager

        Returns:
            True if unregistered successfully, False otherwise
        """
        try:
            with self._lock:
                if name in self.theme_managers:
                    del self.theme_managers[name]
                    self.logger.info(f"Theme manager unregistered: {name}")
                    return True

                return False

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "unregister_theme_manager", "manager_name": name},
                AIComponent.KIRO
            )
            return False

    def _load_available_themes(self) -> None:
        """Load available themes from registered theme managers"""
        try:
            self.available_themes.clear()

            for manager_name, theme_manager in self.theme_managers.items():
                try:
                    if hasattr(theme_manager, 'get_available_themes'):
                        themes = theme_manager.get_available_themes()
                        for theme_info in themes:
                            self.available_themes[theme_info.name] = theme_info

                        self.logger.debug(f"Loaded {len(themes)} themes from manager '{manager_name}'")

                except Exception as e:
                    self.logger.error(f"Failed to load themes from manager '{manager_name}': {e}")

            self.logger.info(f"Total available themes: {len(self.available_themes)}")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "load_available_themes"},
                AIComponent.KIRO
            )

    # Component Registration

    def register_component(self, component: IThemeAware, component_id: Optional[str] = None) -> bool:
        """
        Register a theme-aware component

        Args:
            component: Theme-aware component to register
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

                # Apply current theme to newly registered component
                if self.current_theme:
                    try:
                        component.apply_theme(self.current_theme)
                    except Exception as e:
                        self.logger.error(f"Failed to apply current theme to new component: {e}")

                self.logger.debug(f"Component registered: {type(component).__name__}")
                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "register_component", "component_type": type(component).__name__},
                AIComponent.KIRO
            )
            return False

    def unregister_component(self, component: IThemeAware, component_id: Optional[str] = None) -> bool:
        """
        Unregister a theme-aware component

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
                    self.logger.debug(f"Component unregistered: {type(component).__name__}")

                return success

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "unregister_component", "component_type": type(component).__name__},
                AIComponent.KIRO
            )
            return False

    def get_registered_component(self, component_id: str) -> Optional[IThemeAware]:
        """
        Get a registered component by ID

        Args:
            component_id: Component identifier

        Returns:
            Component instance or None if not found
        """
        return self.component_registry.get(component_id)

    # Theme Application

    async def apply_theme(self, theme_name: str) -> bool:
        """
        Apply a theme across all registered components

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme applied successfully, False otherwise
        """
        start_time = datetime.now()

        try:
            with self._lock:
                # Validate theme exists
                if theme_name not in self.available_themes:
                    await self._handle_theme_error(theme_name, f"Theme '{theme_name}' not found")
                    if theme_name != self.fallback_theme:
                        return await self._apply_fallback_theme()
                    else:
                        return False

                old_theme_name = self.current_theme.name if self.current_theme else None

                # Load theme configuration
                theme_config = await self._load_theme_configuration(theme_name)
                if not theme_config:
                    await self._handle_theme_error(theme_name, f"Failed to load theme configuration")
                    if theme_name != self.fallback_theme:
                        return await self._apply_fallback_theme()
                    else:
                        return False

                # Apply theme to all registered theme managers
                success = await self._apply_theme_to_managers(theme_name)
                if not success:
                    await self._handle_theme_error(theme_name, f"Failed to apply theme to managers")
                    if theme_name != self.fallback_theme:
                        return await self._apply_fallback_theme()
                    else:
                        return False

                # Apply theme to all registered components
                success = await self._apply_theme_to_components(theme_config)
                if not success:
                    await self._handle_theme_error(theme_name, f"Failed to apply theme to components")
                    if theme_name != self.fallback_theme:
                        return await self._apply_fallback_theme()
                    else:
                        return False

                # Update current theme
                self.current_theme = theme_config

                # Persist theme selection
                await self._persist_theme_selection(theme_name)

                # Update theme history
                await self._update_theme_history(theme_name)

                # Notify listeners
                await self._notify_theme_change(old_theme_name, theme_name)
                await self._notify_theme_applied(theme_config)

                # Record performance metrics
                application_time = (datetime.now() - start_time).total_seconds()
                self.theme_switch_times.append(application_time)

                self.logger.info(f"Theme applied successfully: {theme_name} (took {application_time:.3f}s)")
                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "apply_theme", "theme_name": theme_name},
                AIComponent.KIRO
            )
            fallback_result = await self._apply_fallback_theme()
            return fallback_result if fallback_result is not None else False

    async def _load_theme_configuration(self, theme_name: str) -> Optional[ThemeConfiguration]:
        """Load theme configuration from theme managers"""
        try:
            for manager_name, theme_manager in self.theme_managers.items():
                try:
                    if hasattr(theme_manager, 'get_current_theme') and hasattr(theme_manager, 'apply_theme'):
                        # Try to get theme from this manager
                        if theme_manager.apply_theme(theme_name):
                            theme_config = theme_manager.get_current_theme()
                            if theme_config:
                                return theme_config

                except Exception as e:
                    self.logger.warning(f"Failed to load theme from manager '{manager_name}': {e}")

            return None

        except Exception as e:
            self.logger.error(f"Failed to load theme configuration for '{theme_name}': {e}")
            return None

    async def _apply_theme_to_managers(self, theme_name: str) -> bool:
        """Apply theme to all registered theme managers"""
        try:
            success_count = 0
            total_managers = len(self.theme_managers)

            for manager_name, theme_manager in self.theme_managers.items():
                try:
                    if hasattr(theme_manager, 'apply_theme'):
                        if theme_manager.apply_theme(theme_name):
                            success_count += 1
                        else:
                            self.logger.warning(f"Theme manager '{manager_name}' failed to apply theme")
                    else:
                        self.logger.warning(f"Theme manager '{manager_name}' does not support apply_theme")

                except Exception as e:
                    self.logger.error(f"Error applying theme to manager '{manager_name}': {e}")

            # Consider successful if at least one manager succeeded
            return success_count > 0

        except Exception as e:
            self.logger.error(f"Failed to apply theme to managers: {e}")
            return False

    async def _apply_theme_to_components(self, theme_config: ThemeConfiguration) -> bool:
        """Apply theme to all registered components"""
        try:
            success_count = 0
            total_components = len(self.registered_components)

            if total_components == 0:
                return True  # No components to apply theme to

            # Apply theme to components with timeout
            tasks = []
            for component in self.registered_components.copy():  # Copy to avoid modification during iteration
                task = asyncio.create_task(self._apply_theme_to_component(component, theme_config))
                tasks.append(task)

            # Wait for all components with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.theme_application_timeout
                )

                for result in results:
                    if result is True:
                        success_count += 1
                    elif isinstance(result, Exception):
                        self.logger.error(f"Component theme application failed: {result}")

            except asyncio.TimeoutError:
                self.logger.warning(f"Theme application timed out after {self.theme_application_timeout}s")
                # Still count partial successes
                pass

            # Consider successful if at least 50% of components succeeded (more lenient)
            success_rate = success_count / max(total_components, 1)
            return success_rate >= 0.5

        except Exception as e:
            self.logger.error(f"Failed to apply theme to components: {e}")
            return False

    async def _apply_theme_to_component(self, component: IThemeAware, theme_config: ThemeConfiguration) -> bool:
        """Apply theme to a single component"""
        try:
            component_name = type(component).__name__
            start_time = datetime.now()

            component.apply_theme(theme_config)

            # Record performance
            application_time = (datetime.now() - start_time).total_seconds()
            if component_name not in self.component_application_times:
                self.component_application_times[component_name] = []
            self.component_application_times[component_name].append(application_time)

            return True

        except Exception as e:
            self.logger.error(f"Failed to apply theme to component {type(component).__name__}: {e}")
            return False

    async def _apply_fallback_theme(self) -> bool:
        """Apply fallback theme in case of errors"""
        try:
            # Prevent infinite recursion by checking if we're already applying fallback
            if hasattr(self, '_applying_fallback') and self._applying_fallback:
                self.logger.error("Already applying fallback theme, preventing recursion")
                return False

            if self.fallback_theme in self.available_themes:
                self.logger.info(f"Applying fallback theme: {self.fallback_theme}")
                self._applying_fallback = True
                try:
                    # Directly apply fallback without going through full apply_theme to avoid recursion
                    theme_config = await self._load_theme_configuration(self.fallback_theme)
                    if theme_config:
                        manager_success = await self._apply_theme_to_managers(self.fallback_theme)
                        component_success = await self._apply_theme_to_components(theme_config)

                        # Consider successful if at least one succeeded
                        if manager_success or component_success:
                            self.current_theme = theme_config
                            await self._persist_theme_selection(self.fallback_theme)
                            return True
                        else:
                            self.logger.error("Failed to apply fallback theme to any managers or components")
                            return False
                    else:
                        self.logger.error("Failed to load fallback theme configuration")
                        return False
                finally:
                    self._applying_fallback = False
            else:
                self.logger.error("Fallback theme not available")
                return False

        except Exception as e:
            self.logger.error(f"Failed to apply fallback theme: {e}")
            return False

    # Theme Persistence

    async def _persist_theme_selection(self, theme_name: str) -> None:
        """Persist theme selection to configuration"""
        try:
            self.config_manager.set_setting(self.theme_config_key, theme_name)
            await asyncio.to_thread(self.config_manager.save_config)

        except Exception as e:
            self.logger.error(f"Failed to persist theme selection: {e}")

    async def _update_theme_history(self, theme_name: str) -> None:
        """Update theme history"""
        try:
            history = self.config_manager.get_setting(self.theme_history_key, [])

            # Add new entry
            history_entry = {
                "theme_name": theme_name,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }

            # Remove duplicate entries for the same theme
            history = [entry for entry in history if entry.get("theme_name") != theme_name]

            # Add new entry at the beginning
            history.insert(0, history_entry)

            # Limit history size
            max_history_size = 50
            if len(history) > max_history_size:
                history = history[:max_history_size]

            self.config_manager.set_setting(self.theme_history_key, history)

        except Exception as e:
            self.logger.error(f"Failed to update theme history: {e}")

    # Notification System

    def add_theme_change_listener(self, callback: Callable[[str, str], None]) -> bool:
        """
        Add a theme change listener

        Args:
            callback: Callback function (old_theme, new_theme) -> None

        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback not in self.theme_change_listeners:
                    self.theme_change_listeners.append(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to add theme change listener: {e}")
            return False

    def remove_theme_change_listener(self, callback: Callable[[str, str], None]) -> bool:
        """
        Remove a theme change listener

        Args:
            callback: Callback function to remove

        Returns:
            True if listener removed successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback in self.theme_change_listeners:
                    self.theme_change_listeners.remove(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove theme change listener: {e}")
            return False

    def add_theme_applied_listener(self, callback: Callable[[ThemeConfiguration], None]) -> bool:
        """
        Add a theme applied listener

        Args:
            callback: Callback function (theme_config) -> None

        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback not in self.theme_applied_listeners:
                    self.theme_applied_listeners.append(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to add theme applied listener: {e}")
            return False

    def add_theme_error_listener(self, callback: Callable[[str, str], None]) -> bool:
        """
        Add a theme error listener

        Args:
            callback: Callback function (theme_name, error_message) -> None

        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            with self._notification_lock:
                if callback not in self.theme_error_listeners:
                    self.theme_error_listeners.append(callback)
                    return True
                return False

        except Exception as e:
            self.logger.error(f"Failed to add theme error listener: {e}")
            return False

    async def _notify_theme_change(self, old_theme: Optional[str], new_theme: str) -> None:
        """Notify theme change listeners"""
        try:
            with self._notification_lock:
                listeners = self.theme_change_listeners.copy()

            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(old_theme, new_theme)
                    else:
                        listener(old_theme, new_theme)
                except Exception as e:
                    self.logger.error(f"Theme change listener failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to notify theme change listeners: {e}")

    async def _notify_theme_applied(self, theme_config: ThemeConfiguration) -> None:
        """Notify theme applied listeners"""
        try:
            with self._notification_lock:
                listeners = self.theme_applied_listeners.copy()

            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(theme_config)
                    else:
                        listener(theme_config)
                except Exception as e:
                    self.logger.error(f"Theme applied listener failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to notify theme applied listeners: {e}")

    async def _handle_theme_error(self, theme_name: str, error_message: str) -> None:
        """Handle theme errors and notify listeners"""
        try:
            self.logger.error(f"Theme error for '{theme_name}': {error_message}")

            with self._notification_lock:
                listeners = self.theme_error_listeners.copy()

            for listener in listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(theme_name, error_message)
                    else:
                        listener(theme_name, error_message)
                except Exception as e:
                    self.logger.error(f"Theme error listener failed: {e}")

        except Exception as e:
            self.logger.error(f"Failed to handle theme error: {e}")

    # Public API

    def get_current_theme(self) -> Optional[ThemeConfiguration]:
        """Get the currently active theme"""
        return self.current_theme

    def get_available_themes(self) -> List[ThemeInfo]:
        """Get list of available themes"""
        return list(self.available_themes.values())

    def get_theme_history(self) -> List[Dict[str, Any]]:
        """Get theme application history"""
        return self.config_manager.get_setting(self.theme_history_key, [])

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get theme performance metrics"""
        try:
            return {
                "total_theme_switches": len(self.theme_switch_times),
                "average_switch_time": sum(self.theme_switch_times) / max(len(self.theme_switch_times), 1),
                "registered_components": len(self.registered_components),
                "registered_managers": len(self.theme_managers),
                "component_application_times": {
                    component: sum(times) / len(times)
                    for component, times in self.component_application_times.items()
                    if times
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {}

    async def reload_themes(self) -> bool:
        """Reload available themes from all managers"""
        try:
            self._load_available_themes()
            self.logger.info("Themes reloaded successfully")
            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "reload_themes"},
                AIComponent.KIRO
            )
            return False

    async def reset_to_default(self) -> bool:
        """Reset to default theme"""
        return await self.apply_theme(self.fallback_theme)

    def shutdown(self) -> None:
        """Shutdown the theme integration controller"""
        try:
            # Clear all listeners
            with self._notification_lock:
                self.theme_change_listeners.clear()
                self.theme_applied_listeners.clear()
                self.theme_error_listeners.clear()

            # Clear registrations
            with self._lock:
                self.registered_components.clear()
                self.component_registry.clear()
                self.theme_managers.clear()

            self.logger.info("Theme integration controller shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during theme controller shutdown: {e}")
