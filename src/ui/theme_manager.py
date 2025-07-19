"""
PhotoGeoView Theme Manager
Qt-Theme-Manager integration for 16 theme support
"""

import os
from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

try:
    from qt_theme_manager import QtThemeManager
    QT_THEME_MANAGER_AVAILABLE = True
except ImportError:
    QT_THEME_MANAGER_AVAILABLE = False

from src.core.logger import get_logger

logger = get_logger(__name__)


class ThemeManager(QObject):
    """
    Theme management class for PhotoGeoView
    Integrates with Qt-Theme-Manager for 16 theme support
    """

    # Signals
    theme_changed = pyqtSignal(str)  # Emitted when theme changes

    def __init__(self):
        """Initialize theme manager"""
        super().__init__()

        self.logger = logger
        self.qt_theme_manager: Optional[QtThemeManager] = None
        self.current_theme = "dark_blue.xml"

        # Available themes (16 themes from qt-theme-manager)
        self.available_themes = [
            "dark_blue.xml",
            "dark_cyan.xml",
            "dark_lightgreen.xml",
            "dark_orange.xml",
            "dark_pink.xml",
            "dark_purple.xml",
            "dark_red.xml",
            "dark_teal.xml",
            "light_blue.xml",
            "light_cyan.xml",
            "light_cyan_500.xml",
            "light_lightgreen.xml",
            "light_orange.xml",
            "light_pink.xml",
            "light_purple.xml",
            "light_red.xml"
        ]

        # Initialize theme manager
        self._initialize_theme_manager()

        self.logger.info(f"Theme manager initialized with {len(self.available_themes)} themes")

    def _initialize_theme_manager(self) -> None:
        """Initialize Qt Theme Manager"""
        try:
            if not QT_THEME_MANAGER_AVAILABLE:
                self.logger.warning("Qt-Theme-Manager not available, using fallback themes")
                return

            # Get Qt application instance
            app = QApplication.instance()
            if app is None:
                self.logger.error("No Qt application instance found")
                return

            # Initialize Qt Theme Manager
            self.qt_theme_manager = QtThemeManager(app)
            self.logger.info("Qt Theme Manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Qt Theme Manager: {e}")
            self.qt_theme_manager = None

    def apply_theme(self, theme_name: str) -> bool:
        """
        Apply a theme to the application

        Args:
            theme_name: Name of the theme to apply

        Returns:
            True if theme applied successfully, False otherwise
        """
        try:
            if theme_name not in self.available_themes:
                self.logger.warning(f"Unknown theme: {theme_name}, using fallback")
                theme_name = "dark_blue.xml"

            if self.qt_theme_manager:
                # Use Qt Theme Manager
                success = self._apply_qt_theme(theme_name)
            else:
                # Use fallback theme system
                success = self._apply_fallback_theme(theme_name)

            if success:
                self.current_theme = theme_name
                self.theme_changed.emit(theme_name)
                self.logger.info(f"Applied theme: {theme_name}")
                return True
            else:
                self.logger.error(f"Failed to apply theme: {theme_name}")
                return False

        except Exception as e:
            self.logger.error(f"Error applying theme {theme_name}: {e}")
            return False

    def _apply_qt_theme(self, theme_name: str) -> bool:
        """Apply theme using Qt Theme Manager"""
        try:
            if not self.qt_theme_manager:
                return False

            # Remove .xml extension for theme manager
            theme_base_name = theme_name.replace('.xml', '')

            # Apply the theme
            self.qt_theme_manager.apply_theme(theme_base_name)
            return True

        except Exception as e:
            self.logger.error(f"Qt Theme Manager error: {e}")
            return False

    def _apply_fallback_theme(self, theme_name: str) -> bool:
        """Apply fallback theme when Qt Theme Manager is not available"""
        try:
            app = QApplication.instance()
            if not app:
                return False

            # Create basic theme stylesheets
            if 'dark' in theme_name.lower():
                stylesheet = self._get_dark_stylesheet()
            else:
                stylesheet = self._get_light_stylesheet()

            # Apply theme color variants
            color_variant = self._extract_color_from_theme_name(theme_name)
            stylesheet = self._apply_color_variant(stylesheet, color_variant)

            app.setStyleSheet(stylesheet)
            return True

        except Exception as e:
            self.logger.error(f"Fallback theme error: {e}")
            return False

    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet"""
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QFrame {
            background-color: #3c3c3c;
            border: 1px solid #555555;
        }
        QToolBar {
            background-color: #404040;
            border: none;
            spacing: 3px;
        }
        QToolBar QToolButton {
            background-color: #505050;
            border: 1px solid #666666;
            border-radius: 3px;
            padding: 5px;
            margin: 2px;
        }
        QToolBar QToolButton:hover {
            background-color: #606060;
        }
        QStatusBar {
            background-color: #404040;
            border-top: 1px solid #555555;
        }
        QPushButton {
            background-color: #505050;
            border: 1px solid #666666;
            border-radius: 3px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #606060;
        }
        QLabel {
            color: #ffffff;
        }
        QSplitter::handle {
            background-color: #555555;
        }
        QSplitter::handle:hover {
            background-color: #777777;
        }
        """

    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet"""
        return """
        QMainWindow {
            background-color: #f0f0f0;
            color: #000000;
        }
        QWidget {
            background-color: #f0f0f0;
            color: #000000;
        }
        QFrame {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        QToolBar {
            background-color: #e6e6e6;
            border: none;
            spacing: 3px;
        }
        QToolBar QToolButton {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
            margin: 2px;
        }
        QToolBar QToolButton:hover {
            background-color: #f0f0f0;
        }
        QStatusBar {
            background-color: #e6e6e6;
            border-top: 1px solid #cccccc;
        }
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 3px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #f0f0f0;
        }
        QLabel {
            color: #000000;
        }
        QSplitter::handle {
            background-color: #cccccc;
        }
        QSplitter::handle:hover {
            background-color: #aaaaaa;
        }
        """

    def _extract_color_from_theme_name(self, theme_name: str) -> str:
        """Extract color variant from theme name"""
        colors = ['blue', 'cyan', 'lightgreen', 'orange', 'pink', 'purple', 'red', 'teal']

        for color in colors:
            if color in theme_name.lower():
                return color

        return 'blue'  # default

    def _apply_color_variant(self, stylesheet: str, color: str) -> str:
        """Apply color variant to stylesheet"""
        # Color mappings for different variants
        color_map = {
            'blue': '#3f7cac',
            'cyan': '#17a2b8',
            'lightgreen': '#28a745',
            'orange': '#fd7e14',
            'pink': '#e83e8c',
            'purple': '#6f42c1',
            'red': '#dc3545',
            'teal': '#20c997'
        }

        accent_color = color_map.get(color, '#3f7cac')

        # Add color-specific styles
        color_styles = f"""
        QToolBar QToolButton:checked {{
            background-color: {accent_color};
            color: white;
        }}
        QPushButton:pressed {{
            background-color: {accent_color};
            color: white;
        }}
        """

        return stylesheet + color_styles

    def get_available_themes(self) -> List[str]:
        """
        Get list of available themes

        Returns:
            List of theme names
        """
        return self.available_themes.copy()

    def get_current_theme(self) -> str:
        """
        Get current theme name

        Returns:
            Current theme name
        """
        return self.current_theme

    def cycle_theme(self) -> str:
        """
        Cycle to next theme

        Returns:
            New theme name
        """
        try:
            current_index = self.available_themes.index(self.current_theme)
            next_index = (current_index + 1) % len(self.available_themes)
            next_theme = self.available_themes[next_index]

            if self.apply_theme(next_theme):
                return next_theme
            else:
                return self.current_theme

        except Exception as e:
            self.logger.error(f"Error cycling theme: {e}")
            return self.current_theme

    def toggle_theme_type(self) -> str:
        """
        Toggle between dark and light theme of the same color

        Returns:
            New theme name
        """
        try:
            if 'dark' in self.current_theme:
                # Switch to light version
                new_theme = self.current_theme.replace('dark_', 'light_')
            elif 'light' in self.current_theme:
                # Switch to dark version
                new_theme = self.current_theme.replace('light_', 'dark_')
            else:
                # Default toggle
                new_theme = "light_blue.xml" if 'dark' in self.current_theme else "dark_blue.xml"

            # Validate theme exists
            if new_theme not in self.available_themes:
                new_theme = "dark_blue.xml"

            if self.apply_theme(new_theme):
                return new_theme
            else:
                return self.current_theme

        except Exception as e:
            self.logger.error(f"Error toggling theme type: {e}")
            return self.current_theme

    def is_dark_theme(self) -> bool:
        """
        Check if current theme is dark

        Returns:
            True if current theme is dark, False otherwise
        """
        return 'dark' in self.current_theme.lower()

    def is_qt_theme_manager_available(self) -> bool:
        """
        Check if Qt Theme Manager is available

        Returns:
            True if Qt Theme Manager is available, False otherwise
        """
        return QT_THEME_MANAGER_AVAILABLE and self.qt_theme_manager is not None
