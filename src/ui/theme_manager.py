"""
Theme Manager Widget Component

Wrapper around qt-theme-manager library providing PhotoGeoView-specific functionality.
Implements the theme manager component as specified in the qt-theme-breadcrumb spec.

Author: Kiro AI Integration System
Requirements: 1.1, 1.2, 1.3, 1.4
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget

from ..integration.config_manager import ConfigManager
from ..integration.logging_system import LoggerSystem
from ..integration.performance_optimizer import PerformanceOptimizer
from ..integration.theme_interfaces import IThemeAware, IThemeManager
from ..integration.theme_models import ThemeConfiguration, ThemeInfo, ThemeType, FontConfig, ColorScheme
from ..integration.user_notification_system import UserNotificationSystem, NotificationAction


class ThemeManagerWidget(QObject):
    """
    Wrapper around qt-theme-manager library providing PhotoGeoView-specific functionality

    This component implements the theme manager wrapper as specified in task 2 of the
    qt-theme-breadcrumb specification, providing:
    - Theme loading and validation functionality
    - Component registration system for theme updates
    - Integration with qt-theme-manager library
    """

    # Signals for theme management
    theme_changed = Signal(str, str)  # old_theme, new_theme
    theme_applied = Signal(str)  # theme_name
    theme_error = Signal(str, str)  # theme_name, error_message
    theme_loading_progress = Signal(int)  # progress percentage

    def __init__(self, config_manager: ConfigManager, logger_system: LoggerSystem, notification_system: Optional[UserNotificationSystem] = None):
        """
        Initialize the theme manager widget

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
            notification_system: User notification system instance (optional)
        """
        super().__init__()

        self.config_manager = config_manager
        self.logger = logger_system.get_logger(__name__)
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
                self.logger.debug("No event loop running, skipping performance optimization")
        except Exception as e:
            self.logger.warning(f"Failed to initialize performance optimizer: {e}")
            self.performance_optimizer = None

        # Qt-theme-manager integration
        self.qt_theme_manager = None
        self.theme_controller = None
        self.theme_loader = None
        self.stylesheet_generator = None
        self._initialize_qt_theme_manager()

        # Theme storage and management
        self.available_themes: Dict[str, ThemeInfo] = {}
        self.current_theme: Optional[ThemeConfiguration] = None

        # Component registration system
        self.registered_components: Set[IThemeAware] = set()
        self.theme_change_listeners: List[callable] = []

        # Theme directories
        self.theme_dir = Path("config/themes")
        self.custom_theme_dir = Path("config/custom_themes")

        # Initialize theme system
        self._initialize_themes()

        # Keyboard shortcuts and accessibility
        self.keyboard_shortcuts = {}
        self.accessibility_enabled = True
        self.theme_selection_dialog = None
        self._setup_keyboard_shortcuts()

    def _initialize_qt_theme_manager(self) -> None:
        """Initialize qt-theme-manager library integration"""
        try:
            # Try to import qt_theme_manager library
            import qt_theme_manager as theme_manager

            # Initialize the theme manager from qt-theme-manager library
            if hasattr(theme_manager, 'ThemeManager'):
                self.qt_theme_manager = theme_manager.ThemeManager()
            else:
                raise AttributeError("ThemeManager not found in qt_theme_manager")

            # Initialize additional components if available
            if hasattr(theme_manager, 'ThemeController'):
                self.theme_controller = theme_manager.ThemeController()
            else:
                self.theme_controller = None

            if hasattr(theme_manager, 'ThemeLoader'):
                self.theme_loader = theme_manager.ThemeLoader()
            else:
                self.theme_loader = None

            if hasattr(theme_manager, 'StylesheetGenerator'):
                self.stylesheet_generator = theme_manager.StylesheetGenerator()
            else:
                self.stylesheet_generator = None

            self.logger.info("Qt-theme-manager library initialized successfully")

        except (ImportError, AttributeError) as e:
            self.logger.warning(f"Qt-theme-manager library not available: {e}")

            # Try to use fallback implementation
            try:
                from .theme_manager_fallback import ThemeManagerFallback
                self.qt_theme_manager = ThemeManagerFallback()
                self.theme_controller = None
                self.theme_loader = None
                self.stylesheet_generator = None
                self.logger.info("Using ThemeManager fallback implementation")
            except ImportError:
                self.logger.error("ThemeManager fallback implementation not found")
                self.qt_theme_manager = None
                self.theme_controller = None
                self.theme_loader = None
                self.stylesheet_generator = None

        except Exception as e:
            self.logger.error(f"Failed to initialize qt-theme-manager: {e}")
            self.qt_theme_manager = None
            self.theme_controller = None
            self.theme_loader = None
            self.stylesheet_generator = None

    def initialize_themes(self) -> None:
        """Load available themes and set current theme"""
        self._initialize_themes()

    def _initialize_themes(self) -> None:
        """Internal theme initialization"""
        try:
            # Create theme directories
            self.theme_dir.mkdir(parents=True, exist_ok=True)
            self.custom_theme_dir.mkdir(parents=True, exist_ok=True)

            # Load themes from qt-theme-manager if available
            if self.qt_theme_manager:
                self._load_qt_themes()

            # Load built-in themes
            self._load_builtin_themes()

            # Load custom themes
            self._load_custom_themes()

            # Set current theme from configuration
            current_theme_name = self.config_manager.get_setting("ui.theme", "default")
            if current_theme_name in self.available_themes:
                self._load_theme_configuration(current_theme_name)

            self.logger.info(f"Theme system initialized with {len(self.available_themes)} themes")

        except Exception as e:
            self.logger.error(f"Failed to initialize themes: {e}")

    def _setup_keyboard_shortcuts(self, parent_widget: Optional[QWidget] = None) -> None:
        """
        Setup keyboard shortcuts for theme management

        Args:
            parent_widget: Parent widget for shortcuts (optional)
        """
        try:
            if not parent_widget:
                # If no parent widget provided, shortcuts will be global when parent is set later
                self.logger.debug("No parent widget provided for shortcuts, will setup when parent is available")
                return

            # Ctrl+T: Open theme selection dialog
            self.keyboard_shortcuts['theme_dialog'] = QShortcut(
                QKeySequence("Ctrl+T"), parent_widget
            )
            self.keyboard_shortcuts['theme_dialog'].activated.connect(self._open_theme_selection_dialog)
            # Use proper shortcut context instead of window flags
            from PySide6.QtCore import Qt
            self.keyboard_shortcuts['theme_dialog'].setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

            # Ctrl+Shift+T: Cycle through available themes
            self.keyboard_shortcuts['cycle_theme'] = QShortcut(
                QKeySequence("Ctrl+Shift+T"), parent_widget
            )
            self.keyboard_shortcuts['cycle_theme'].activated.connect(self._cycle_to_next_theme)
            self.keyboard_shortcuts['cycle_theme'].setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)

            # Set accessibility properties for shortcuts
            if self.accessibility_enabled:
                self.keyboard_shortcuts['theme_dialog'].setWhatsThis(
                    "Open theme selection dialog to choose from available themes"
                )
                self.keyboard_shortcuts['cycle_theme'].setWhatsThis(
                    "Cycle through available themes in sequence"
                )

            self.logger.debug("Theme manager keyboard shortcuts configured")

        except Exception as e:
            self.logger.error(f"Failed to setup keyboard shortcuts: {e}")

    def setup_shortcuts_with_parent(self, parent_widget: QWidget) -> None:
        """
        Setup keyboard shortcuts with a specific parent widget

        Args:
            parent_widget: Parent widget for shortcuts
        """
        self._setup_keyboard_shortcuts(parent_widget)

    def _open_theme_selection_dialog(self) -> None:
        """Open theme selection dialog"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel

            if self.theme_selection_dialog and self.theme_selection_dialog.isVisible():
                self.theme_selection_dialog.raise_()
                self.theme_selection_dialog.activateWindow()
                return

            # Create theme selection dialog
            dialog = QDialog()
            dialog.setWindowTitle("Select Theme")
            dialog.setModal(True)
            dialog.resize(400, 300)

            # Set accessibility properties
            if self.accessibility_enabled:
                dialog.setAccessibleName("Theme Selection Dialog")
                dialog.setAccessibleDescription("Dialog for selecting application theme")

            layout = QVBoxLayout(dialog)

            # Add description label
            description_label = QLabel("Choose a theme for the application:")
            if self.accessibility_enabled:
                description_label.setAccessibleName("Theme selection instructions")
            layout.addWidget(description_label)

            # Create theme list
            theme_list = QListWidget()
            if self.accessibility_enabled:
                theme_list.setAccessibleName("Available themes list")
                theme_list.setAccessibleDescription("List of available themes to choose from")

            # Populate theme list
            current_theme_name = self.current_theme.name if self.current_theme else None
            for theme_info in self.get_available_themes():
                item = QListWidgetItem(f"{theme_info.display_name}")
                item.setData(256, theme_info.name)  # Store theme name in user data

                # Set accessibility properties
                if self.accessibility_enabled:
                    item.setToolTip(f"{theme_info.description} by {theme_info.author}")
                    if theme_info.name == current_theme_name:
                        item.setText(f"{theme_info.display_name} (Current)")

                theme_list.addItem(item)

                # Select current theme
                if theme_info.name == current_theme_name:
                    theme_list.setCurrentItem(item)

            layout.addWidget(theme_list)

            # Create button layout
            button_layout = QHBoxLayout()

            # Apply button
            apply_button = QPushButton("Apply")
            if self.accessibility_enabled:
                apply_button.setAccessibleName("Apply selected theme")
                apply_button.setAccessibleDescription("Apply the selected theme to the application")
            apply_button.clicked.connect(lambda: self._apply_selected_theme(theme_list, dialog))
            button_layout.addWidget(apply_button)

            # Cancel button
            cancel_button = QPushButton("Cancel")
            if self.accessibility_enabled:
                cancel_button.setAccessibleName("Cancel theme selection")
                cancel_button.setAccessibleDescription("Close dialog without changing theme")
            cancel_button.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_button)

            layout.addLayout(button_layout)

            # Set default button
            apply_button.setDefault(True)

            # Handle double-click to apply
            theme_list.itemDoubleClicked.connect(lambda: self._apply_selected_theme(theme_list, dialog))

            # Store dialog reference
            self.theme_selection_dialog = dialog

            # Show dialog
            dialog.exec()

        except Exception as e:
            self.logger.error(f"Failed to open theme selection dialog: {e}")

    def _apply_selected_theme(self, theme_list, dialog) -> None:
        """Apply the selected theme from the dialog"""
        try:
            current_item = theme_list.currentItem()
            if current_item:
                theme_name = current_item.data(256)
                if self.apply_theme(theme_name):
                    dialog.accept()
                else:
                    self.logger.error(f"Failed to apply selected theme: {theme_name}")
            else:
                self.logger.warning("No theme selected")

        except Exception as e:
            self.logger.error(f"Failed to apply selected theme: {e}")

    def _cycle_to_next_theme(self) -> None:
        """Cycle to the next available theme"""
        try:
            available_themes = self.get_available_themes()
            if len(available_themes) <= 1:
                self.logger.info("Only one theme available, cannot cycle")
                return

            current_theme_name = self.current_theme.name if self.current_theme else None
            current_index = -1

            # Find current theme index
            for i, theme_info in enumerate(available_themes):
                if theme_info.name == current_theme_name:
                    current_index = i
                    break

            # Calculate next theme index
            next_index = (current_index + 1) % len(available_themes)
            next_theme = available_themes[next_index]

            # Apply next theme
            if self.apply_theme(next_theme.name):
                self.logger.info(f"Cycled to theme: {next_theme.display_name}")
            else:
                self.logger.error(f"Failed to cycle to theme: {next_theme.name}")

        except Exception as e:
            self.logger.error(f"Failed to cycle to next theme: {e}")

    def set_accessibility_enabled(self, enabled: bool) -> None:
        """
        Enable or disable accessibility features

        Args:
            enabled: Whether to enable accessibility features
        """
        try:
            self.accessibility_enabled = enabled

            # Update existing shortcuts with accessibility properties
            if enabled and self.keyboard_shortcuts:
                if 'theme_dialog' in self.keyboard_shortcuts:
                    self.keyboard_shortcuts['theme_dialog'].setWhatsThis(
                        "Open theme selection dialog to choose from available themes"
                    )
                if 'cycle_theme' in self.keyboard_shortcuts:
                    self.keyboard_shortcuts['cycle_theme'].setWhatsThis(
                        "Cycle through available themes in sequence"
                    )

            self.logger.debug(f"Accessibility features {'enabled' if enabled else 'disabled'}")

        except Exception as e:
            self.logger.error(f"Failed to set accessibility enabled: {e}")

    def get_keyboard_shortcuts_info(self) -> Dict[str, str]:
        """
        Get information about available keyboard shortcuts

        Returns:
            Dictionary mapping shortcut names to descriptions
        """
        return {
            "Ctrl+T": "Open theme selection dialog",
            "Ctrl+Shift+T": "Cycle through available themes"
        }

    def _load_qt_themes(self) -> None:
        """Load themes from qt-theme-manager library"""
        if not self.qt_theme_manager:
            return

        try:
            # Try to get available themes from qt-theme-manager
            if hasattr(self.qt_theme_manager, 'get_available_themes'):
                qt_themes = self.qt_theme_manager.get_available_themes()
            elif hasattr(self.qt_theme_manager, 'list_themes'):
                qt_themes = self.qt_theme_manager.list_themes()
            else:
                # Fallback to common theme names if no method available
                qt_themes = ['dark', 'light', 'blue', 'green']
                self.logger.warning("Qt-theme-manager API not fully compatible, using fallback themes")

            for theme_name in qt_themes:
                theme_info = ThemeInfo(
                    name=theme_name,
                    display_name=theme_name.replace('_', ' ').title(),
                    description=f"Qt theme: {theme_name}",
                    author="qt-theme-manager",
                    version="1.0.0",
                    theme_type=ThemeType.BUILT_IN,
                    is_dark=self._is_dark_theme_name(theme_name),
                    preview_colors=self._get_preview_colors(theme_name),
                    is_available=True
                )

                self.available_themes[theme_name] = theme_info

            self.logger.info(f"Loaded {len(qt_themes)} themes from qt-theme-manager")

        except Exception as e:
            self.logger.error(f"Failed to load qt-theme-manager themes: {e}")

    def _load_builtin_themes(self) -> None:
        """Load built-in PhotoGeoView themes"""
        builtin_themes = [
            {
                "name": "default",
                "display_name": "Default Light",
                "description": "Default light theme for PhotoGeoView",
                "is_dark": False
            },
            {
                "name": "dark",
                "display_name": "Dark",
                "description": "Dark theme for PhotoGeoView",
                "is_dark": True
            },
            {
                "name": "photography",
                "display_name": "Photography",
                "description": "Optimized theme for photo viewing",
                "is_dark": True
            }
        ]

        for theme_data in builtin_themes:
            if theme_data["name"] not in self.available_themes:
                theme_info = ThemeInfo(
                    name=theme_data["name"],
                    display_name=theme_data["display_name"],
                    description=theme_data["description"],
                    author="PhotoGeoView",
                    version="1.0.0",
                    theme_type=ThemeType.BUILT_IN,
                    is_dark=theme_data["is_dark"],
                    preview_colors=self._get_preview_colors(theme_data["name"]),
                    is_available=True
                )

                self.available_themes[theme_data["name"]] = theme_info

    def _load_custom_themes(self) -> None:
        """Load custom themes from directory"""
        try:
            for theme_file in self.custom_theme_dir.glob("*.json"):
                theme_config = ThemeConfiguration.load_from_file(theme_file)
                if theme_config and theme_config.is_valid:
                    theme_info = ThemeInfo.from_theme_config(theme_config)
                    self.available_themes[theme_config.name] = theme_info

            custom_count = sum(1 for t in self.available_themes.values()
                             if t.theme_type == ThemeType.CUSTOM)
            self.logger.info(f"Loaded {custom_count} custom themes")

        except Exception as e:
            self.logger.error(f"Failed to load custom themes: {e}")

    def _is_dark_theme_name(self, theme_name: str) -> bool:
        """Determine if theme is dark based on name"""
        dark_keywords = ['dark', 'black', 'night', 'midnight', 'shadow']
        return any(keyword in theme_name.lower() for keyword in dark_keywords)

    def _get_preview_colors(self, theme_name: str) -> Dict[str, str]:
        """Get preview colors for theme"""
        if self._is_dark_theme_name(theme_name):
            return {
                "primary": "#007acc",
                "background": "#2b2b2b",
                "text": "#ffffff"
            }
        else:
            return {
                "primary": "#007acc",
                "background": "#ffffff",
                "text": "#000000"
            }

    def _load_theme_configuration(self, theme_name: str) -> bool:
        """Load full theme configuration with lazy loading optimization"""
        try:
            # Check if theme is already cached
            cached_theme = self.performance_optimizer.theme_cache.get(f"config_{theme_name}")
            if cached_theme:
                self.current_theme = cached_theme
                return True

            # Try to load from custom themes first
            theme_file = self.custom_theme_dir / f"{theme_name}.json"
            if theme_file.exists():
                self.current_theme = ThemeConfiguration.load_from_file(theme_file)
                if self.current_theme:
                    # Cache the loaded theme
                    self.performance_optimizer.theme_cache.set(f"config_{theme_name}", self.current_theme)
                    return True

            # Try to load from built-in themes
            theme_file = self.theme_dir / f"{theme_name}.json"
            if theme_file.exists():
                self.current_theme = ThemeConfiguration.load_from_file(theme_file)
                if self.current_theme:
                    # Cache the loaded theme
                    self.performance_optimizer.theme_cache.set(f"config_{theme_name}", self.current_theme)
                    return True

            # Create default configuration for qt-theme-manager themes
            if theme_name in self.available_themes:
                self.current_theme = self._create_default_theme_config(theme_name)
                # Cache the created theme
                self.performance_optimizer.theme_cache.set(f"config_{theme_name}", self.current_theme)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to load theme configuration for {theme_name}: {e}")
            return False

    def _create_default_theme_config(self, theme_name: str) -> ThemeConfiguration:
        """Create default theme configuration"""
        theme_info = self.available_themes[theme_name]

        return ThemeConfiguration(
            name=theme_name,
            display_name=theme_info.display_name,
            description=theme_info.description,
            author=theme_info.author,
            version=theme_info.version,
            theme_type=theme_info.theme_type
        )

    # IThemeManager implementation

    def get_current_theme(self) -> Optional[ThemeConfiguration]:
        """Get the currently active theme"""
        return self.current_theme

    def apply_theme(self, theme_name: str) -> bool:
        """
        Apply a theme to the application with comprehensive error handling and fallback

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme applied successfully, False otherwise
        """
        # Start performance monitoring
        operation_id = self.performance_optimizer.start_theme_operation(f"apply_{theme_name}")

        try:
            # Validate theme exists
            if theme_name not in self.available_themes:
                error_msg = f"Theme '{theme_name}' not found"
                self.logger.error(error_msg)
                self.theme_error.emit(theme_name, error_msg)

                # Try fallback to default theme if not already trying default
                if theme_name != "default":
                    self.logger.info("Attempting fallback to default theme")
                    return self._apply_fallback_theme()
                return False

            old_theme_name = self.current_theme.name if self.current_theme else None

            # Load theme configuration with retry mechanism
            theme_config_loaded = False
            for attempt in range(3):  # Try up to 3 times
                try:
                    if self._load_theme_configuration(theme_name):
                        theme_config_loaded = True
                        break
                    else:
                        self.logger.warning(f"Theme configuration load attempt {attempt + 1} failed")
                        if attempt < 2:  # Don't sleep on last attempt
                            import time
                            time.sleep(0.1)  # Brief before retry
                except Exception as e:
                    self.logger.warning(f"Theme configuration load attempt {attempt + 1} error: {e}")
                    if attempt < 2:
                        import time
                        time.sleep(0.1)

            if not theme_config_loaded:
                error_msg = f"Failed to load theme configuration after 3 attempts"
                self.logger.error(error_msg)
                self.theme_error.emit(theme_name, error_msg)

                # Show user notification
                if self.notification_system:
                    self.notification_system.show_theme_error(
                        theme_name,
                        "Could not load theme configuration",
                        fallback_applied=False
                    )

                # Try fallback to default theme if not already trying default
                if theme_name != "default":
                    return self._apply_fallback_theme()
                return False

            # Apply theme using qt-theme-manager with error handling
            qt_manager_success = False
            if self.qt_theme_manager:
                try:
                    if hasattr(self.qt_theme_manager, 'apply_theme'):
                        self.qt_theme_manager.apply_theme(theme_name)
                        qt_manager_success = True
                    elif hasattr(self.qt_theme_manager, 'set_theme'):
                        self.qt_theme_manager.set_theme(theme_name)
                        qt_manager_success = True
                    else:
                        self.logger.warning("Qt-theme-manager has no apply_theme or set_theme method")
                except Exception as e:
                    self.logger.error(f"Qt-theme-manager failed to apply theme: {e}")
                    # Continue without qt-theme-manager support

            # Notify registered components with error handling
            component_failures = []
            for component in self.registered_components.copy():  # Copy to avoid modification during iteration
                try:
                    component.apply_theme(self.current_theme)
                except Exception as e:
                    component_name = type(component).__name__
                    self.logger.error(f"Failed to apply theme to component {component_name}: {e}")
                    component_failures.append(component_name)

            # Check if too many components failed
            if len(component_failures) > len(self.registered_components) * 0.5:  # More than 50% failed
                error_msg = f"Theme application failed for {len(component_failures)} components"
                self.logger.error(error_msg)
                self.theme_error.emit(theme_name, error_msg)

                # Try fallback if not already trying default
                if theme_name != "default":
                    return self._apply_fallback_theme()
                return False

            # Update configuration with error handling
            try:
                self.config_manager.set_setting("ui.theme", theme_name)
            except Exception as e:
                self.logger.error(f"Failed to persist theme setting: {e}")
                # Continue anyway - theme is applied even if not persisted

            # Emit signals with error handling
            try:
                if old_theme_name:
                    self.theme_changed.emit(old_theme_name, theme_name)
                self.theme_applied.emit(theme_name)
            except Exception as e:
                self.logger.error(f"Failed to emit theme signals: {e}")
                # Continue anyway - theme is applied

            # Log success with warnings if applicable
            if component_failures:
                self.logger.warning(f"Theme applied with {len(component_failures)} component failures: {theme_name}")
            else:
                self.logger.info(f"Theme applied successfully: {theme_name}")

            # End performance monitoring
            duration = self.performance_optimizer.end_theme_operation(operation_id)
            self.logger.debug(f"Theme application took {duration:.3f}s")

            return True

        except Exception as e:
            error_msg = f"Critical error applying theme {theme_name}: {e}"
            self.logger.error(error_msg)
            self.theme_error.emit(theme_name, error_msg)

            # End performance monitoring on error
            self.performance_optimizer.end_theme_operation(operation_id)

            # Try fallback to default theme if not already trying default
            if theme_name != "default":
                return self._apply_fallback_theme()
            return False

    def _apply_fallback_theme(self) -> bool:
        """
        Apply fallback theme with error handling

        Returns:
            True if fallback applied successfully, False otherwise
        """
        try:
            # Prevent infinite recursion
            if hasattr(self, '_applying_fallback') and self._applying_fallback:
                self.logger.error("Already applying fallback theme, preventing recursion")
                return False

            self._applying_fallback = True

            try:
                fallback_theme = "default"

                # Check if default theme exists
                if fallback_theme not in self.available_themes:
                    # Try to create a minimal default theme
                    self._create_emergency_default_theme()

                if fallback_theme in self.available_themes:
                    self.logger.info(f"Applying fallback theme: {fallback_theme}")

                    # Load fallback theme configuration
                    if self._load_theme_configuration(fallback_theme):
                        # Apply to components with minimal error handling
                        for component in self.registered_components.copy():
                            try:
                                component.apply_theme(self.current_theme)
                            except Exception as e:
                                self.logger.warning(f"Fallback theme failed for component {type(component).__name__}: {e}")

                        # Update configuration
                        try:
                            self.config_manager.set_setting("ui.theme", fallback_theme)
                        except Exception as e:
                            self.logger.warning(f"Failed to persist fallback theme: {e}")

                        # Emit signals
                        try:
                            self.theme_applied.emit(fallback_theme)
                        except Exception as e:
                            self.logger.warning(f"Failed to emit fallback theme signals: {e}")

                        self.logger.info("Fallback theme applied successfully")
                        return True
                    else:
                        self.logger.error("Failed to load fallback theme configuration")
                        return False
                else:
                    self.logger.error("Fallback theme not available")
                    return False

            finally:
                self._applying_fallback = False

        except Exception as e:
            self.logger.error(f"Critical error in fallback theme application: {e}")
            if hasattr(self, '_applying_fallback'):
                self._applying_fallback = False
            return False

    def _create_emergency_default_theme(self) -> None:
        """Create an emergency default theme when none exists"""
        try:
            from ..integration.theme_models import ThemeConfiguration, ThemeInfo, ThemeType

            # Create minimal default theme info
            default_theme_info = ThemeInfo(
                name="default",
                display_name="Default Light",
                description="Emergency default theme",
                author="PhotoGeoView",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN,
                is_dark=False,
                preview_colors={
                    "primary": "#007acc",
                    "background": "#ffffff",
                    "text": "#000000"
                },
                is_available=True
            )

            # Add to available themes
            self.available_themes["default"] = default_theme_info

            self.logger.info("Emergency default theme created")

        except Exception as e:
            self.logger.error(f"Failed to create emergency default theme: {e}")

    def register_component(self, component: IThemeAware) -> bool:
        """
        Register a component for theme updates

        Args:
            component: Theme-aware component to register

        Returns:
            True if registered successfully, False otherwise
        """
        try:
            if component not in self.registered_components:
                self.registered_components.add(component)

                # Apply current theme to newly registered component
                if self.current_theme:
                    component.apply_theme(self.current_theme)

                self.logger.debug(f"Component registered for theme updates: {type(component).__name__}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to register component: {e}")
            return False

    def unregister_component(self, component: IThemeAware) -> bool:
        """
        Unregister a component from theme updates

        Args:
            component: Component to unregister

        Returns:
            True if unregistered successfully, False otherwise
        """
        try:
            if component in self.registered_components:
                self.registered_components.remove(component)
                self.logger.debug(f"Component unregistered from theme updates: {type(component).__name__}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to unregister component: {e}")
            return False

    def add_theme_change_listener(self, callback: callable) -> bool:
        """
        Add a theme change listener

        Args:
            callback: Callback function (old_theme, new_theme) -> None

        Returns:
            True if listener added successfully, False otherwise
        """
        try:
            if callback not in self.theme_change_listeners:
                self.theme_change_listeners.append(callback)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to add theme change listener: {e}")
            return False

    def remove_theme_change_listener(self, callback: callable) -> bool:
        """
        Remove a theme change listener

        Args:
            callback: Callback function to remove

        Returns:
            True if listener removed successfully, False otherwise
        """
        try:
            if callback in self.theme_change_listeners:
                self.theme_change_listeners.remove(callback)
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to remove theme change listener: {e}")
            return False

    def get_theme_property(self, property_path: str, default: Any = None) -> Any:
        """
        Get a theme property value

        Args:
            property_path: Dot-separated path to the property (e.g., "colors.primary")
            default: Default value if property not found

        Returns:
            Property value or default
        """
        if not self.current_theme:
            return default

        try:
            # Split property path and navigate through theme configuration
            parts = property_path.split('.')
            value = self.current_theme

            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default

            return value

        except Exception as e:
            self.logger.error(f"Failed to get theme property {property_path}: {e}")
            return default

    def reload_themes(self) -> bool:
        """
        Reload all available themes

        Returns:
            True if reloaded successfully, False otherwise
        """
        try:
            self.available_themes.clear()
            self._initialize_themes()

            self.logger.info("Themes reloaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reload themes: {e}")
            return False

    def reset_to_default(self) -> bool:
        """
        Reset to default theme

        Returns:
            True if reset successfully, False otherwise
        """
        return self.apply_theme("default")

    # Additional methods for theme management

    def get_available_themes(self) -> List[ThemeInfo]:
        """Get list of available themes with metadata"""
        return list(self.available_themes.values())

    def import_theme(self, theme_path: Path, validate: bool = True, overwrite: bool = False) -> bool:
        """
        Import custom theme file with enhanced validation and options

        Args:
            theme_path: Path to the theme file
            validate: Whether to validate theme before importing
            overwrite: Whether to overwrite existing theme with same name

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            # Load theme configuration from file
            theme_config = ThemeConfiguration.load_from_file(theme_path)
            if not theme_config:
                self.logger.error(f"Failed to load theme file: {theme_path}")
                return False

            # Validate theme if requested
            if validate and not theme_config.validate():
                self.logger.error(f"Theme validation failed: {theme_config.validation_errors}")
                return False

            # Check if theme already exists
            if theme_config.name in self.available_themes and not overwrite:
                self.logger.error(f"Theme already exists: {theme_config.name}")
                return False

            # Ensure theme is marked as imported
            theme_config.theme_type = ThemeType.IMPORTED
            theme_config.is_custom = True

            # Save to custom themes directory
            custom_theme_path = self.custom_theme_dir / f"{theme_config.name}.json"
            if theme_config.save_to_file(custom_theme_path):
                # Add to available themes
                theme_info = ThemeInfo.from_theme_config(theme_config)
                self.available_themes[theme_config.name] = theme_info

                self.logger.info(f"Theme imported successfully: {theme_config.name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to import theme from {theme_path}: {e}")
            return False

    def export_theme(self, theme_name: str, export_path: Path, include_metadata: bool = True) -> bool:
        """
        Export theme to file with enhanced options

        Args:
            theme_name: Name of the theme to export
            export_path: Path to save the theme file
            include_metadata: Whether to include usage metadata in export

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            if theme_name not in self.available_themes:
                self.logger.error(f"Theme not found: {theme_name}")
                return False

            # Load full theme configuration
            if not self._load_theme_configuration(theme_name):
                self.logger.error(f"Failed to load theme configuration: {theme_name}")
                return False

            # Create export copy
            export_theme = self.current_theme

            # Remove metadata if requested
            if not include_metadata:
                export_theme.usage_count = 0
                export_theme.last_used = None

            # Ensure export directory exists
            export_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to export path
            if export_theme.save_to_file(export_path):
                self.logger.info(f"Theme exported successfully: {theme_name} -> {export_path}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to export theme {theme_name}: {e}")
            return False

    def _notify_components(self, theme: ThemeConfiguration) -> None:
        """Notify all registered components of theme change"""
        for component in self.registered_components.copy():  # Copy to avoid modification during iteration
            try:
                component.apply_theme(theme)
            except Exception as e:
                self.logger.error(f"Failed to apply theme to component {type(component).__name__}: {e}")

        # Notify theme change listeners
        for listener in self.theme_change_listeners.copy():
            try:
                old_theme = getattr(self, '_previous_theme_name', None)
                listener(old_theme, theme.name)
            except Exception as e:
                self.logger.error(f"Theme change listener failed: {e}")

        # Store current theme name for next change
        self._previous_theme_name = theme.name

    def validate_theme(self, theme: ThemeConfiguration) -> bool:
        """
        Validate theme configuration

        Args:
            theme: Theme configuration to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            return theme.validate()
        except Exception as e:
            self.logger.error(f"Theme validation failed: {e}")
            return False

    def get_theme_stylesheet(self, theme_name: str) -> str:
        """
        Get stylesheet for a specific theme

        Args:
            theme_name: Name of the theme

        Returns:
            CSS stylesheet string or empty string if not found
        """
        try:
            if theme_name not in self.available_themes:
                return ""

            # Load theme configuration if not current
            if not self.current_theme or self.current_theme.name != theme_name:
                if not self._load_theme_configuration(theme_name):
                    return ""

            # Generate CSS variables from theme
            if self.current_theme:
                return self.current_theme.get_css_variables()

            return ""

        except Exception as e:
            self.logger.error(f"Failed to get stylesheet for theme {theme_name}: {e}")
            return ""

    def create_theme_from_template(self, template_name: str, new_theme_name: str,
                                 customizations: Dict[str, Any] = None) -> bool:
        """
        Create a new theme based on an existing template

        Args:
            template_name: Name of the template theme
            new_theme_name: Name for the new theme
            customizations: Dictionary of customizations to apply

        Returns:
            True if theme created successfully, False otherwise
        """
        try:
            if template_name not in self.available_themes:
                self.logger.error(f"Template theme not found: {template_name}")
                return False

            if new_theme_name in self.available_themes:
                self.logger.error(f"Theme already exists: {new_theme_name}")
                return False

            # Load template theme configuration
            if not self._load_theme_configuration(template_name):
                self.logger.error(f"Failed to load template theme: {template_name}")
                return False

            # Create new theme based on template
            template_colors = self.current_theme.colors if self.current_theme.colors else self._get_default_colors()
            template_fonts = self.current_theme.fonts.copy() if self.current_theme.fonts else self._get_default_fonts()
            template_styles = self.current_theme.styles.copy() if self.current_theme.styles else {}

            new_theme = ThemeConfiguration(
                name=new_theme_name,
                display_name=customizations.get('display_name', new_theme_name.replace('_', ' ').title()),
                description=customizations.get('description', f"Custom theme based on {template_name}"),
                author=customizations.get('author', "User"),
                version="1.0.0",
                theme_type=ThemeType.CUSTOM,
                colors=template_colors,
                fonts=template_fonts,
                styles=template_styles,
                custom_properties=customizations.get('custom_properties', {}),
                is_custom=True
            )

            # Apply customizations
            if customizations:
                if 'colors' in customizations:
                    for color_key, color_value in customizations['colors'].items():
                        if hasattr(new_theme.colors, color_key):
                            setattr(new_theme.colors, color_key, color_value)

                if 'fonts' in customizations:
                    for font_key, font_config in customizations['fonts'].items():
                        if isinstance(font_config, dict):
                            new_theme.fonts[font_key] = FontConfig(**font_config)

                if 'styles' in customizations:
                    new_theme.styles.update(customizations['styles'])

            # Validate new theme
            if not new_theme.validate():
                self.logger.error(f"New theme validation failed: {new_theme.validation_errors}")
                return False

            # Save new theme
            custom_theme_path = self.custom_theme_dir / f"{new_theme_name}.json"
            if new_theme.save_to_file(custom_theme_path):
                # Add to available themes
                theme_info = ThemeInfo.from_theme_config(new_theme)
                self.available_themes[new_theme_name] = theme_info

                self.logger.info(f"Created new theme: {new_theme_name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to create theme from template: {e}")
            return False

    def delete_custom_theme(self, theme_name: str) -> bool:
        """
        Delete a custom theme

        Args:
            theme_name: Name of the theme to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if theme_name not in self.available_themes:
                self.logger.error(f"Theme not found: {theme_name}")
                return False

            theme_info = self.available_themes[theme_name]
            if theme_info.theme_type != ThemeType.CUSTOM:
                self.logger.error(f"Cannot delete non-custom theme: {theme_name}")
                return False

            # Delete theme file
            theme_file = self.custom_theme_dir / f"{theme_name}.json"
            if theme_file.exists():
                theme_file.unlink()

            # Remove from available themes
            del self.available_themes[theme_name]

            # If this was the current theme, reset to default
            if self.current_theme and self.current_theme.name == theme_name:
                self.apply_theme("default")

            self.logger.info(f"Deleted custom theme: {theme_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete custom theme {theme_name}: {e}")
            return False

    def get_theme_usage_statistics(self) -> Dict[str, Any]:
        """
        Get theme usage statistics

        Returns:
            Dictionary with usage statistics
        """
        try:
            stats = {
                "total_themes": len(self.available_themes),
                "builtin_themes": sum(1 for t in self.available_themes.values()
                                    if t.theme_type == ThemeType.BUILT_IN),
                "custom_themes": sum(1 for t in self.available_themes.values()
                                   if t.theme_type == ThemeType.CUSTOM),
                "imported_themes": sum(1 for t in self.available_themes.values()
                                     if t.theme_type == ThemeType.IMPORTED),
                "current_theme": self.current_theme.name if self.current_theme else None,
                "registered_components": len(self.registered_components),
                "theme_change_listeners": len(self.theme_change_listeners)
            }

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get theme usage statistics: {e}")
            return {}

    def duplicate_theme(self, source_theme_name: str, new_theme_name: str,
                       new_display_name: str = None) -> bool:
        """
        Duplicate an existing theme with a new name

        Args:
            source_theme_name: Name of the theme to duplicate
            new_theme_name: Name for the new theme
            new_display_name: Display name for the new theme

        Returns:
            True if duplicated successfully, False otherwise
        """
        try:
            if source_theme_name not in self.available_themes:
                self.logger.error(f"Source theme not found: {source_theme_name}")
                return False

            if new_theme_name in self.available_themes:
                self.logger.error(f"Theme already exists: {new_theme_name}")
                return False

            # Load source theme configuration
            if not self._load_theme_configuration(source_theme_name):
                self.logger.error(f"Failed to load source theme: {source_theme_name}")
                return False

            # Create duplicate theme
            duplicate_theme = ThemeConfiguration(
                name=new_theme_name,
                display_name=new_display_name or new_theme_name.replace('_', ' ').title(),
                description=f"Copy of {self.current_theme.display_name}",
                author=self.current_theme.author,
                version="1.0.0",
                theme_type=ThemeType.CUSTOM,
                colors=self.current_theme.colors,
                fonts=self.current_theme.fonts.copy(),
                styles=self.current_theme.styles.copy(),
                custom_properties=self.current_theme.custom_es.copy(),
                is_custom=True
            )

            # Validate duplicate theme
            if not duplicate_theme.validate():
                self.logger.error(f"Duplicate theme validation failed: {duplicate_theme.validation_errors}")
                return False

            # Save duplicate theme
            custom_theme_path = self.custom_theme_dir / f"{new_theme_name}.json"
            if duplicate_theme.save_to_file(custom_theme_path):
                # Add to available themes
                theme_info = ThemeInfo.from_theme_config(duplicate_theme)
                self.available_themes[new_theme_name] = theme_info

                self.logger.info(f"Theme duplicated successfully: {source_theme_name} -> {new_theme_name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to duplicate theme: {e}")
            return False

    def rename_theme(self, old_name: str, new_name: str, new_display_name: str = None) -> bool:
        """
        Rename an existing custom theme

        Args:
            old_name: Current theme name
            new_name: New theme name
            new_display_name: New display name (optional)

        Returns:
            True if renamed successfully, False otherwise
        """
        try:
            if old_name not in self.available_themes:
                self.logger.error(f"Theme not found: {old_name}")
                return False

            theme_info = self.available_themes[old_name]
            if theme_info.theme_type != ThemeType.CUSTOM:
                self.logger.error(f"Cannot rename non-custom theme: {old_name}")
                return False

            if new_name in self.available_themes:
                self.logger.error(f"Theme already exists: {new_name}")
                return False

            # Load theme configuration
            if not self._load_theme_configuration(old_name):
                self.logger.error(f"Failed to load theme configuration: {old_name}")
                return False

            # Update theme configuration
            self.current_theme.name = new_name
            if new_display_name:
                self.current_theme.display_name = new_display_name

            # Save with new name
            new_theme_path = self.custom_theme_dir / f"{new_name}.json"
            if self.current_theme.save_to_file(new_theme_path):
                # Remove old theme file
                old_theme_path = self.custom_theme_dir / f"{old_name}.json"
                if old_theme_path.exists():
                    old_theme_path.unlink()

                # Update available themes
                del self.available_themes[old_name]
                theme_info = ThemeInfo.from_theme_config(self.current_theme)
                self.available_themes[new_name] = theme_info

                # Update current theme if it was the renamed one
                if hasattr(self, '_previous_theme_name') and self._previous_theme_name == old_name:
                    self._previous_theme_name = new_name

                self.logger.info(f"Theme renamed successfully: {old_name} -> {new_name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to rename theme: {e}")
            return False

    def get_theme_categories(self) -> Dict[str, List[str]]:
        """
        Get themes organized by categories

        Returns:
            Dictionary with category names as keys and theme lists as values
        """
        try:
            categories = {
                "Built-in": [],
                "Custom": [],
                "Imported": [],
                "Dark": [],
                "Light": []
            }

            for theme_name, theme_info in self.available_themes.items():
                # By type
                if theme_info.theme_type == ThemeType.BUILT_IN:
                    categories["Built-in"].append(theme_name)
                elif theme_info.theme_type == ThemeType.CUSTOM:
                    categories["Custom"].append(theme_name)
                elif theme_info.theme_type == ThemeType.IMPORTED:
                    categories["Imported"].append(theme_name)

                # By appearance
                if theme_info.is_dark:
                    categories["Dark"].append(theme_name)
                else:
                    categories["Light"].append(theme_name)

            return categories

        except Exception as e:
            self.logger.error(f"Failed to get theme categories: {e}")
            return {}

    def search_themes(self, query: str, search_fields: List[str] = None) -> List[str]:
        """
        Search themes by name, description, or author

        Args:
            query: Search query
            search_fields: Fields to search in (name, display_name, description, author)

        Returns:
            List of matching theme names
        """
        try:
            if not query:
                return list(self.available_themes.keys())

            if search_fields is None:
                search_fields = ["name", "display_name", "description", "author"]

            query_lower = query.lower()
            matching_themes = []

            for theme_name, theme_info in self.available_themes.items():
                # Search in specified fields
                for field in search_fields:
                    if hasattr(theme_info, field):
                        field_value = getattr(theme_info, field)
                        if field_value and query_lower in field_value.lower():
                            matching_themes.append(theme_name)
                            break

            return matching_themes

        except Exception as e:
            self.logger.error(f"Failed to search themes: {e}")
            return []

    def get_theme_dependencies(self, theme_name: str) -> Dict[str, Any]:
        """
        Get theme dependencies and requirements

        Args:
            theme_name: Name of the theme

        Returns:
            Dictionary with dependency information
        """
        try:
            if theme_name not in self.available_themes:
                return {}

            # Load theme configuration
            if not self._load_theme_configuration(theme_name):
                return {}

            dependencies = {
                "qt_version": "6.0+",
                "required_fonts": [],
                "optional_fonts": [],
                "color_depth": "24-bit",
                "custom_properties": list(self.current_theme.custom_properties.keys()) if self.current_theme.custom_properties else []
            }

            # Check font dependencies
            for font_name, font_config in self.current_theme.fonts.items():
                if font_config.family not in ["Arial", "Helvetica", "Times New Roman", "Courier New"]:
                    dependencies["optional_fonts"].append(font_config.family)

            return dependencies

        except Exception as e:
            self.logger.error(f"Failed to get theme dependencies: {e}")
            return {}

    def validate_theme_compatibility(self, theme_name: str) -> Dict[str, Any]:
        """
        Validate theme compatibility with current system

        Args:
            theme_name: Name of the theme to validate

        Returns:
            Dictionary with compatibility information
        """
        try:
            if theme_name not in self.available_themes:
                return {"compatible": False, "errors": ["Theme not found"]}

            # Load theme configuration
            if not self._load_theme_configuration(theme_name):
                return {"compatible": False, "errors": ["Failed to load theme"]}

            compatibility = {
                "compatible": True,
                "errors": [],
                "warnings": [],
                "missing_fonts": [],
                "unsupported_features": []
            }

            # Validate theme configuration
            if not self.current_theme.validate():
                compatibility["compatible"] = False
                compatibility["errors"].extend(self.current_theme.validation_errors)

            # Check font availability (skip in test environment)
            try:
                from PySide6.QtGui import QFontDatabase
                font_db = QFontDatabase()
                available_fonts = font_db.families()
            except Exception:
                # Fallback for test environment
                available_fonts = ["Arial", "Helvetica", "Times New Roman", "Courier New"]

            for font_name, font_config in self.current_theme.fonts.items():
                if font_config.family not in available_fonts:
                    compatibility["missing_fonts"].append(font_config.family)
                    compatibility["warnings"].append(f"Font not available: {font_config.family}")

            # Check for unsupported custom properties
            if self.current_theme.custom_properties:
                for prop_name in self.current_theme.custom_properties.keys():
                    if prop_name.startswith("experimental_"):
                        compatibility["unsupported_features"].append(prop_name)
                        compatibility["warnings"].append(f"Experimental feature: {prop_name}")

            return compatibility

        except Exception as e:
            self.logger.error(f"Failed to validate theme compatibility: {e}")
            return {"compatible": False, "errors": [str(e)]}

    def backup_themes(self, backup_path: Path) -> bool:
        """
        Create backup of all custom themes

        Args:
            backup_path: Path to save backup file

        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "app_version": "1.0.0",
                "themes": {}
            }

            # Backup custom themes
            for theme_name, theme_info in self.available_themes.items():
                if theme_info.theme_type in [ThemeType.CUSTOM, ThemeType.IMPORTED]:
                    theme_file = self.custom_theme_dir / f"{theme_name}.json"
                    if theme_file.exists():
                        theme_config = ThemeConfiguration.load_from_file(theme_file)
                        if theme_config:
                            backup_data["themes"][theme_name] = theme_config.to_dict()

            # Save backup
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Theme backup created: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create theme backup: {e}")
            return False

    def restore_themes(self, backup_path: Path) -> bool:
        """
        Restore themes from backup

        Args:
            backup_path: Path to backup file

        Returns:
            True if restored successfully, False otherwise
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            if "themes" not in backup_data:
                self.logger.error("Invalid backup file format")
                return False

            restored_count = 0
            for theme_name, theme_data in backup_data["themes"].items():
                try:
                    theme_config = ThemeConfiguration.from_dict(theme_data)
                    theme_config.theme_type = ThemeType.CUSTOM
                    theme_config.is_custom = True

                    # Save restored theme
                    theme_file = self.custom_theme_dir / f"{theme_name}.json"
                    if theme_config.save_to_file(theme_file):
                        # Add to available themes
                        theme_info = ThemeInfo.from_theme_config(theme_config)
                        self.available_themes[theme_name] = theme_info
                        restored_count += 1

                except Exception as e:
                    self.logger.warning(f"Failed to restore theme {theme_name}: {e}")

            self.logger.info(f"Restored {restored_count} themes from backup")
            return restored_count > 0

        except Exception as e:
            self.logger.error(f"Failed to restore themes from backup: {e}")
            return False

    def _create_emergency_default_theme(self) -> None:
        """Create an emergency default theme when no themes are available"""
        try:
            # Create minimal default theme configuration
            default_theme = ThemeConfiguration(
                name="default",
                display_name="Emergency Default",
                description="Emergency fallback theme",
                author="PhotoGeoView",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN
            )

            # Add to available themes
            theme_info = ThemeInfo(
                name="default",
                display_name="Emergency Default",
                description="Emergency fallback theme",
                author="PhotoGeoView",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN,
                is_dark=False,
                preview_colors={
                    "primary": "#007acc",
                    "background": "#ffffff",
                    "text": "#000000"
                },
                is_available=True
            )

            self.available_themes["default"] = theme_info
            self.logger.info("Created emergency default theme")

        except Exception as e:
            self.logger.error(f"Failed to create emergency default theme: {e}")

    def handle_theme_loading_error(self, theme_name: str, error: Exception) -> bool:
        """
        Handle theme loading errors with comprehensive fallback strategy

        Args:
            theme_name: Name of the theme that failed to load
            error: The error that occurred

        Returns:
            True if error was handled successfully, False otherwise
        """
        try:
            error_msg = f"Theme loading error for '{theme_name}': {str(error)}"
            self.logger.error(error_msg)
            self.theme_error.emit(theme_name, error_msg)

            # Show user notification
            if self.notification_system:
                self.notification_system.show_theme_error(
                    theme_name,
                    str(error),
                    fallback_applied=False
                )

            # Try fallback strategies in order
            fallback_strategies = [
                ("default", "Applying default theme"),
                ("light", "Applying light theme"),
                ("dark", "Applying dark theme")
            ]

            for fallback_theme, strategy_msg in fallback_strategies:
                if fallback_theme != theme_name and fallback_theme in self.available_themes:
                    self.logger.info(f"{strategy_msg} as fallback for '{theme_name}'")
                    if self.apply_theme(fallback_theme):
                        # Update notification to show fallback was applied
                        if self.notification_system:
                            self.notification_system.show_info(
                                "Theme Fallback Applied",
                                f"Applied '{fallback_theme}' theme due to error with '{theme_name}'"
                            )
                        return True

            # If no fallback themes work, create emergency theme
            self._create_emergency_default_theme()
            if "default" in self.available_themes:
                return self.apply_theme("default")

            return False

        except Exception as e:
            self.logger.error(f"Failed to handle theme loading error: {e}")
            return False

    def validate_theme_integrity(self, theme_name: str) -> bool:
        """
        Validate theme integrity before application

        Args:
            theme_name: Name of theme to validate

        Returns:
            True if theme is valid, False otherwise
        """
        try:
            if theme_name not in self.available_themes:
                return False

            theme_info = self.available_themes[theme_name]

            # Check if theme file exists for custom themes
            if theme_info.theme_type == ThemeType.CUSTOM:
                theme_file = self.custom_theme_dir / f"{theme_name}.json"
                if not theme_file.exists():
                    self.logger.warning(f"Custom theme file missing: {theme_file}")
                    return False

                # Try to load and validate theme configuration
                try:
                    theme_config = ThemeConfiguration.load_from_file(theme_file)
                    if not theme_config or not theme_config.is_valid:
                        self.logger.warning(f"Invalid theme configuration: {theme_name}")
                        return False
                except Exception as e:
                    self.logger.warning(f"Failed to load theme configuration for validation: {e}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate theme integrity: {e}")
            return False
