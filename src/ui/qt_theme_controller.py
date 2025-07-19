"""
Enhanced Theme Manager with Qt-Theme-Manager Integration
Supports configuration file based theme management
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

try:
    from qt_theme_manager import QtThemeManager
    QT_THEME_MANAGER_AVAILABLE = True
except ImportError:
    QT_THEME_MANAGER_AVAILABLE = False

from src.core.logger import get_logger

logger = get_logger(__name__)


class QtThemeController:
    """
    Qt Theme Manager controller with configuration file support
    Based on Copilot's recommendations for Qt-Theme-Manager usage
    """

    def __init__(self, config_file: str = "config/qt_themes.json"):
        """
        Initialize theme controller with configuration file

        Args:
            config_file: Path to theme configuration JSON file
        """
        self.logger = logger
        self.config_file = config_file
        self.config_path = Path(config_file)
        self.theme_config: Dict[str, Any] = {}
        self.qt_theme_manager: Optional[QtThemeManager] = None

        # Load theme configuration
        self.load_config()

        # Initialize Qt Theme Manager
        self._initialize_qt_theme_manager()

        self.logger.info(f"Qt Theme Controller initialized with config: {config_file}")

    def load_config(self) -> bool:
        """
        Load theme configuration from JSON file

        Returns:
            True if config loaded successfully
        """
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Theme config file not found: {self.config_file}")
                self.create_default_config()
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.theme_config = json.load(f)

            self.logger.info(f"Loaded theme config with {len(self.theme_config.get('available_themes', {}))} themes")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load theme config: {e}")
            self.create_default_config()
            return False

    def save_config(self) -> bool:
        """
        Save current theme configuration to JSON file

        Returns:
            True if config saved successfully
        """
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.theme_config, f, indent=2, ensure_ascii=False)

            self.logger.debug("Theme config saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save theme config: {e}")
            return False

    def create_default_config(self) -> None:
        """Create default theme configuration"""
        self.theme_config = {
            "current_theme": "dark_blue",
            "last_selected_theme": "dark_blue",
            "theme_switching_enabled": True,
            "remember_theme_choice": True,
            "version": "0.1.0",
            "available_themes": {
                "dark_blue": {
                    "name": "dark_blue",
                    "display_name": "Dark Blue",
                    "description": "Default dark blue theme",
                    "primaryColor": "#3f7cac",
                    "backgroundColor": "#2b2b2b",
                    "textColor": "#ffffff"
                },
                "light_blue": {
                    "name": "light_blue",
                    "display_name": "Light Blue",
                    "description": "Default light blue theme",
                    "primaryColor": "#3f7cac",
                    "backgroundColor": "#f0f0f0",
                    "textColor": "#000000"
                }
            }
        }
        self.save_config()
        self.logger.info("Created default theme configuration")

    def _initialize_qt_theme_manager(self) -> None:
        """Initialize Qt Theme Manager with custom configuration"""
        try:
            if not QT_THEME_MANAGER_AVAILABLE:
                self.logger.warning("Qt-Theme-Manager package not available")
                return

            app = QApplication.instance()
            if app is None:
                self.logger.warning("No Qt application instance found")
                return

            # Initialize Qt Theme Manager with custom config
            self.qt_theme_manager = QtThemeManager(app)

            # Register custom themes from config file
            self._register_custom_themes()

            self.logger.info("Qt Theme Manager initialized with custom themes")

        except Exception as e:
            self.logger.error(f"Failed to initialize Qt Theme Manager: {e}")
            self.qt_theme_manager = None

    def _register_custom_themes(self) -> None:
        """Register custom themes from configuration file"""
        if not self.qt_theme_manager or not self.theme_config:
            return

        try:
            available_themes = self.theme_config.get('available_themes', {})

            for theme_name, theme_data in available_themes.items():
                # Create theme stylesheet from config data
                stylesheet = self._create_stylesheet_from_config(theme_data)

                # Register theme with Qt Theme Manager
                # Note: Actual API may vary - this is based on typical usage patterns
                if hasattr(self.qt_theme_manager, 'register_custom_theme'):
                    self.qt_theme_manager.register_custom_theme(theme_name, stylesheet)

                self.logger.debug(f"Registered custom theme: {theme_name}")

        except Exception as e:
            self.logger.error(f"Failed to register custom themes: {e}")

    def _create_stylesheet_from_config(self, theme_data: Dict[str, Any]) -> str:
        """
        Create Qt stylesheet from theme configuration data

        Args:
            theme_data: Theme configuration dictionary

        Returns:
            Generated CSS stylesheet string
        """
        # Extract colors from theme config
        bg_color = theme_data.get('backgroundColor', '#2b2b2b')
        text_color = theme_data.get('textColor', '#ffffff')
        primary_color = theme_data.get('primaryColor', '#3f7cac')
        accent_color = theme_data.get('accentColor', primary_color)
        secondary_color = theme_data.get('secondaryColor', '#404040')
        border_color = theme_data.get('borderColor', '#555555')

        # Generate comprehensive stylesheet
        stylesheet = f"""
        QMainWindow {{
            background-color: {bg_color};
            color: {text_color};
        }}

        QWidget {{
            background-color: {bg_color};
            color: {text_color};
        }}

        QFrame {{
            background-color: {secondary_color};
            border: 1px solid {border_color};
            border-radius: 4px;
        }}

        QToolBar {{
            background-color: {secondary_color};
            border: none;
            spacing: 3px;
            padding: 2px;
        }}

        QToolBar QToolButton {{
            background-color: {secondary_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 5px;
            margin: 2px;
            color: {text_color};
        }}

        QToolBar QToolButton:hover {{
            background-color: {primary_color};
            border-color: {accent_color};
        }}

        QToolBar QToolButton:checked {{
            background-color: {primary_color};
            color: white;
            border-color: {accent_color};
        }}

        QStatusBar {{
            background-color: {secondary_color};
            border-top: 1px solid {border_color};
            color: {text_color};
        }}

        QPushButton {{
            background-color: {secondary_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 5px;
            color: {text_color};
            min-width: 80px;
        }}

        QPushButton:hover {{
            background-color: {primary_color};
            border-color: {accent_color};
        }}

        QPushButton:pressed {{
            background-color: {accent_color};
            color: white;
        }}

        QLabel {{
            color: {text_color};
        }}

        QSplitter::handle {{
            background-color: {border_color};
        }}

        QSplitter::handle:hover {{
            background-color: {primary_color};
        }}

        QMenuBar {{
            background-color: {secondary_color};
            color: {text_color};
            border-bottom: 1px solid {border_color};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
        }}

        QMenuBar::item:selected {{
            background-color: {primary_color};
        }}

        QMenu {{
            background-color: {secondary_color};
            color: {text_color};
            border: 1px solid {border_color};
        }}

        QMenu::item {{
            padding: 4px 20px;
        }}

        QMenu::item:selected {{
            background-color: {primary_color};
        }}
        """

        return stylesheet

    def apply_theme(self, theme_name: str) -> bool:
        """
        Apply theme by name using Qt Theme Manager

        Args:
            theme_name: Name of theme to apply

        Returns:
            True if theme applied successfully
        """
        try:
            if not self.theme_config:
                self.logger.error("No theme configuration loaded")
                return False

            available_themes = self.theme_config.get('available_themes', {})
            if theme_name not in available_themes:
                self.logger.error(f"Theme '{theme_name}' not found in configuration")
                return False

            if self.qt_theme_manager:
                # Use Qt Theme Manager to apply theme
                if hasattr(self.qt_theme_manager, 'apply_theme'):
                    self.qt_theme_manager.apply_theme(theme_name)
                else:
                    # Fallback: apply stylesheet directly
                    theme_data = available_themes[theme_name]
                    stylesheet = self._create_stylesheet_from_config(theme_data)
                    app = QApplication.instance()
                    if app:
                        app.setStyleSheet(stylesheet)
            else:
                # Fallback: apply stylesheet directly
                theme_data = available_themes[theme_name]
                stylesheet = self._create_stylesheet_from_config(theme_data)
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(stylesheet)

            # Update current theme in config
            self.theme_config['current_theme'] = theme_name
            self.theme_config['last_selected_theme'] = theme_name

            # Save config if remember_theme_choice is enabled
            if self.theme_config.get('remember_theme_choice', True):
                self.save_config()

            self.logger.info(f"Applied theme: {theme_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply theme '{theme_name}': {e}")
            return False

    def get_available_themes(self) -> List[str]:
        """
        Get list of available theme names

        Returns:
            List of available theme names
        """
        return list(self.theme_config.get('available_themes', {}).keys())

    def get_current_theme(self) -> str:
        """
        Get current theme name

        Returns:
            Current theme name
        """
        return self.theme_config.get('current_theme', 'dark_blue')

    def get_theme_display_name(self, theme_name: str) -> str:
        """
        Get user-friendly display name for theme

        Args:
            theme_name: Internal theme name

        Returns:
            Display name for UI
        """
        available_themes = self.theme_config.get('available_themes', {})
        if theme_name in available_themes:
            return available_themes[theme_name].get('display_name', theme_name)
        return theme_name

    def add_custom_theme(self, theme_name: str, theme_config: Dict[str, Any]) -> bool:
        """
        Add a new custom theme to configuration

        Args:
            theme_name: Name of the new theme
            theme_config: Theme configuration dictionary

        Returns:
            True if theme added successfully
        """
        try:
            if 'available_themes' not in self.theme_config:
                self.theme_config['available_themes'] = {}

            self.theme_config['available_themes'][theme_name] = theme_config

            # Re-register themes if Qt Theme Manager is available
            if self.qt_theme_manager:
                stylesheet = self._create_stylesheet_from_config(theme_config)
                if hasattr(self.qt_theme_manager, 'register_custom_theme'):
                    self.qt_theme_manager.register_custom_theme(theme_name, stylesheet)

            # Save updated configuration
            self.save_config()

            self.logger.info(f"Added custom theme: {theme_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add custom theme '{theme_name}': {e}")
            return False

    def is_theme_switching_enabled(self) -> bool:
        """Check if theme switching is enabled"""
        return self.theme_config.get('theme_switching_enabled', True)

    def set_theme_switching_enabled(self, enabled: bool) -> None:
        """Enable or disable theme switching"""
        self.theme_config['theme_switching_enabled'] = enabled
        self.save_config()
        self.logger.info(f"Theme switching {'enabled' if enabled else 'disabled'}")
