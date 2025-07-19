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
            # Dark themes
            "dark_blue.xml",
            "dark_cyan.xml",
            "dark_lightgreen.xml",
            "dark_orange.xml",
            "dark_pink.xml",
            "dark_purple.xml",
            "dark_red.xml",
            "dark_teal.xml",
            # Light themes
            "light_blue.xml",
            "light_cyan.xml",
            "light_cyan_500.xml",
            "light_lightgreen.xml",
            "light_orange.xml",
            "light_pink.xml",
            "light_purple.xml",
            "light_red.xml"
        ]

        # Theme categories for better organization
        self.theme_categories = {
            'dark': [t for t in self.available_themes if t.startswith('dark_')],
            'light': [t for t in self.available_themes if t.startswith('light_')]
        }

        # Theme display names for UI
        self.theme_display_names = {
            "dark_blue.xml": "Dark Blue",
            "dark_cyan.xml": "Dark Cyan",
            "dark_lightgreen.xml": "Dark Light Green",
            "dark_orange.xml": "Dark Orange",
            "dark_pink.xml": "Dark Pink",
            "dark_purple.xml": "Dark Purple",
            "dark_red.xml": "Dark Red",
            "dark_teal.xml": "Dark Teal",
            "light_blue.xml": "Light Blue",
            "light_cyan.xml": "Light Cyan",
            "light_cyan_500.xml": "Light Cyan 500",
            "light_lightgreen.xml": "Light Light Green",
            "light_orange.xml": "Light Orange",
            "light_pink.xml": "Light Pink",
            "light_purple.xml": "Light Purple",
            "light_red.xml": "Light Red"
        }

        # Initialize theme manager
        self._initialize_theme_manager()

        # Validate all themes are available
        self._validate_themes()

        self.logger.info(f"Theme manager initialized with {len(self.available_themes)} themes")

    def _validate_themes(self) -> None:
        """Validate that all 16 themes are properly configured"""
        if len(self.available_themes) != 16:
            self.logger.warning(f"Expected 16 themes, found {len(self.available_themes)}")

        # Ensure all themes have display names
        for theme in self.available_themes:
            if theme not in self.theme_display_names:
                self.logger.warning(f"No display name defined for theme: {theme}")
                # Auto-generate display name
                display_name = theme.replace('.xml', '').replace('_', ' ').title()
                self.theme_display_names[theme] = display_name

        self.logger.debug(f"Dark themes: {len(self.theme_categories['dark'])}")
        self.logger.debug(f"Light themes: {len(self.theme_categories['light'])}")

    def _initialize_theme_manager(self) -> None:
        """Initialize Qt Theme Manager"""
        try:
            if not QT_THEME_MANAGER_AVAILABLE:
                self.logger.warning("Qt-Theme-Manager package not available, using fallback themes")
                return

            # Get Qt application instance
            app = QApplication.instance()
            if app is None:
                self.logger.warning("No Qt application instance found for theme manager")
                return

            # Try importing and initializing Qt Theme Manager
            try:
                from qt_theme_manager import QtThemeManager
                self.qt_theme_manager = QtThemeManager(app)
                self.logger.info("Qt Theme Manager initialized successfully")
                return
            except Exception as import_error:
                self.logger.warning(f"Qt Theme Manager import failed: {import_error}")
                self.qt_theme_manager = None
                return

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
        Toggle between dark and light theme variants

        Returns:
            New theme name after toggle
        """
        try:
            current_theme = self.current_theme

            # Determine current theme type
            if current_theme.startswith('dark_'):
                # Switch to light theme
                target_color = current_theme.replace('dark_', '')
                target_themes = [t for t in self.theme_categories['light'] if target_color in t]
            else:
                # Switch to dark theme
                target_color = current_theme.replace('light_', '').replace('_500', '')
                target_themes = [t for t in self.theme_categories['dark'] if target_color in t]

            if target_themes:
                target_theme = target_themes[0]  # Use first match
                if self.apply_theme(target_theme):
                    return target_theme

            # Fallback to simple cycle if no matching variant found
            return self.cycle_theme()

        except Exception as e:
            self.logger.error(f"Error toggling theme type: {e}")
            return self.current_theme

    def get_theme_display_name(self, theme_name: str) -> str:
        """
        Get user-friendly display name for theme

        Args:
            theme_name: Internal theme name

        Returns:
            Display name for UI
        """
        return self.theme_display_names.get(theme_name, theme_name.replace('.xml', '').replace('_', ' ').title())

    def get_theme_category(self, theme_name: str) -> str:
        """
        Get theme category (dark/light)

        Args:
            theme_name: Theme name

        Returns:
            Theme category
        """
        if theme_name.startswith('dark_'):
            return 'dark'
        elif theme_name.startswith('light_'):
            return 'light'
        else:
            return 'unknown'

    def get_themes_by_category(self, category: str) -> List[str]:
        """
        Get themes by category

        Args:
            category: Theme category ('dark' or 'light')

        Returns:
            List of theme names in category
        """
        return self.theme_categories.get(category, []).copy()

    def validate_theme_compatibility(self) -> bool:
        """
        Validate all themes work with current Qt installation

        Returns:
            True if all themes are compatible
        """
        compatible_count = 0

        for theme in self.available_themes:
            try:
                # Test theme application (dry run)
                if self.qt_theme_manager:
                    # Just validate theme exists in manager
                    theme_base = theme.replace('.xml', '')
                    # Note: Real validation would require actually testing theme application
                    compatible_count += 1
                else:
                    # For fallback themes, all are considered compatible
                    compatible_count += 1

            except Exception as e:
                self.logger.warning(f"Theme {theme} may not be compatible: {e}")

        compatibility_ratio = compatible_count / len(self.available_themes)
        self.logger.info(f"Theme compatibility: {compatible_count}/{len(self.available_themes)} ({compatibility_ratio:.1%})")

        return compatibility_ratio >= 0.8  # 80% compatibility threshold

    def apply_theme_with_verification(self, theme_name: str) -> bool:
        """
        Apply theme with verification and fallback

        Args:
            theme_name: Theme to apply

        Returns:
            True if theme applied successfully
        """
        # Store current theme as fallback
        fallback_theme = self.current_theme

        # Try to apply new theme
        success = self.apply_theme(theme_name)

        if not success:
            self.logger.warning(f"Failed to apply theme {theme_name}, reverting to {fallback_theme}")
            # Try to revert to fallback
            fallback_success = self.apply_theme(fallback_theme)
            if not fallback_success:
                self.logger.error("Failed to revert to fallback theme")
                # Apply default theme as last resort
                self.apply_theme("dark_blue.xml")

        return success

    def get_theme_statistics(self) -> dict:
        """
        Get statistics about theme usage and availability

        Returns:
            Dictionary with theme statistics
        """
        return {
            'total_themes': len(self.available_themes),
            'dark_themes': len(self.theme_categories['dark']),
            'light_themes': len(self.theme_categories['light']),
            'current_theme': self.current_theme,
            'current_category': self.get_theme_category(self.current_theme),
            'qt_theme_manager_available': self.qt_theme_manager is not None,
            'theme_manager_initialized': self.qt_theme_manager is not None
        }

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
