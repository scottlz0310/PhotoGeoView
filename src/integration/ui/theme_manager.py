"""
Integrated Theme Manager for AI Integration

Combines CursorBLD's Qt-Theme-Manager integration with Kiro enhancements:
- CursorBLD: 16 theme variations, Qt-Theme-Manager integration
- Kiro: Accessibility features, performance optimization, validation

Author: Kiro AI Integration System
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent, ThemeConfiguration
from ..state_manager import StateManager


class IntegratedThemeManager(QObject):
    """
    Integrated theme manager combining CursorBLD's theme system with Kiro enhancements

    Features:
    - CursorBLD's Qt-Theme-Manager integration with 16 themes
    - Kiro's accessibility features and performance optimization
    - Theme validation and error recovery
    - Custom theme creation and management
    """

    # Signals
    theme_changed = pyqtSignal(str)
    theme_change_requested = pyqtSignal(str, str)  # old_theme, new_theme
    theme_applied = pyqtSignal(str)  # theme_name
    theme_error = pyqtSignal(str, str)  # theme_name, error_message
    theme_transition_progress = pyqtSignal(int)  # progress percentage

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
    ):
        """
        Initialize the integrated theme manager

        Args:
            config_manager: Configuration manager instance
            state_manager: State manager instance
            logger_system: Logging system instance
        """
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Theme storage
        self.themes: Dict[str, ThemeConfiguration] = {}
        self.current_theme = "default"

        # Theme directories
        self.theme_dir = Path("config/themes")
        self.custom_theme_dir = Path("config/custom_themes")

        # CursorBLD Qt-Theme-Manager integration
        self.qt_theme_manager = None
        self.qt_themes_available = []

        # Kiro accessibility features
        self.accessibility_enabled = True
        self.high_contrast_mode = False
        self.large_fonts_mode = False

        # Performance settings
        self.animation_enabled = True
        self.transparency_enabled = True

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize the theme manager"""

        try:
            # Create theme directories
            self.theme_dir.mkdir(parents=True, exist_ok=True)
            self.custom_theme_dir.mkdir(parents=True, exist_ok=True)

            # Initialize Qt-Theme-Manager (CursorBLD integration)
            self._initialize_qt_theme_manager()

            # Load built-in themes
            self._load_builtin_themes()

            # Load custom themes
            self._load_custom_themes()

            # Load accessibility settings
            self._load_accessibility_settings()

            # Apply current theme
            current_theme = self.state_manager.get_state().current_theme
            self.apply_theme(current_theme)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "theme_manager_init",
                f"Theme manager initialized with {len(self.themes)} themes",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_manager_init"},
                AIComponent.CURSOR,
            )

    def _initialize_qt_theme_manager(self):
        """Initialize Qt-Theme-Manager integration (CursorBLD)"""
        try:
            # Import Qt-Theme-Manager if available
            try:
                import qt_theme_manager

                self.qt_theme_manager = qt_theme_manager.ThemeManager()
                self.qt_themes_available = self.qt_theme_manager.get_available_themes()

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "qt_theme_manager_init",
                    f"Qt-Theme-Manager initialized with {len(self.qt_themes_available)} themes",
                )
            except ImportError:
                self.logger_system.warning(
                    "Qt-Theme-Manager not available, using fallback themes"
                )
                self.qt_themes_available = ["default", "dark", "light"]

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "initialize_qt_theme_manager"},
                AIComponent.CURSOR,
            )

    def _load_buil(self):
        """Load built-in themes (CursorBLD 16 theme variations)"""
        try:
            builtin_themes = [
                # Light themes
                {"name": "default", "display_name": "Default Light", "base": "light"},
                {"name": "light_blue", "display_name": "Light Blue", "base": "light"},
                {"name": "light_green", "display_name": "Light Green", "base": "light"},
                {
                    "name": "light_purple",
                    "display_name": "Light Purple",
                    "base": "light",
                },
                # Dark themes
                {"name": "dark", "display_name": "Default Dark", "base": "dark"},
                {"name": "dark_blue", "display_name": "Dark Blue", "base": "dark"},
                {"name": "dark_green", "display_name": "Dark Green", "base": "dark"},
                {"name": "dark_purple", "display_name": "Dark Purple", "base": "dark"},
                # High contrast themes (Kiro accessibility)
                {
                    "name": "high_contrast_light",
                    "display_name": "High Contrast Light",
                    "base": "light",
                    "high_contrast": True,
                },
                {
                    "name": "high_contrast_dark",
                    "display_name": "High Contrast Dark",
                    "base": "dark",
                    "high_contrast": True,
                },
                # Specialized themes
                {"name": "photography", "display_name": "Photography", "base": "dark"},
                {"name": "minimal", "display_name": "Minimal", "base": "light"},
                {"name": "vibrant", "display_name": "Vibrant", "base": "light"},
                {
                    "name": "professional",
                    "display_name": "Professional",
                    "base": "dark",
                },
                {
                    "name": "accessibility",
                    "display_name": "Accessibility",
                    "base": "light",
                    "accessibility": True,
                },
                {
                    "name": "performance",
                    "display_name": "Performance",
                    "base": "light",
                    "performance": True,
                },
            ]

            for theme_info in builtin_themes:
                theme_config = self._create_builtin_theme_config(theme_info)
                self.themes[theme_config.name] = theme_config

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "builtin_themes_loaded",
                f"Loaded {len(builtin_themes)} built-in themes",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_builtin_themes"},
                AIComponent.CURSOR,
            )

    def _create_builtin_theme_config(
        self, theme_info: Dict[str, Any]
    ) -> ThemeConfiguration:
        """Create theme configuration from theme info"""
        base_colors = self._get_base_colors(theme_info["base"])

        # Apply theme-specific modifications
        if theme_info.get("high_contrast"):
            base_colors = self._apply_high_contrast(base_colors)

        # Create theme configuration
        return ThemeConfiguration(
            name=theme_info["name"],
            display_name=theme_info["display_name"],
            description=f"Built-in {theme_info['display_name']} theme",
            version="1.0.0",
            author="CursorBLD + Kiro Integration",
            qt_theme_name=theme_info.get("qt_theme", theme_info["base"]),
            color_scheme=base_colors,
            accessibility_features={
                "high_contrast": theme_info.get("high_contrast", False),
                "large_fonts": theme_info.get("accessibility", False),
                "screen_reader_support": True,
                "keyboard_navigation": True,
                "focus_indicators": True,
            },
            performance_settings={
                "animation_enabled": not theme_info.get("performance", False),
                "transparency_enabled": not theme_info.get("performance", False),
                "shadow_effects": not theme_info.get("performance", False),
                "gradient_rendering": True,
                "anti_aliasing": True,
            },
        )

    def _get_base_colors(self, base: str) -> Dict[str, str]:
        """Get base color scheme"""
        if base == "dark":
            return {
                "background": "#2b2b2b",
                "foreground": "#ffffff",
                "primary": "#007acc",
                "secondary": "#6c757d",
                "accent": "#17a2b8",
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "info": "#17a2b8",
                "border": "#495057",
                "hover": "#3a3a3a",
                "selected": "#0d7377",
                "disabled": "#6c757d",
            }
        else:  # light
            return {
                "background": "#ffffff",
                "foreground": "#000000",
                "primary": "#007acc",
                "secondary": "#6c757d",
                "accent": "#17a2b8",
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "info": "#17a2b8",
                "border": "#dee2e6",
                "hover": "#f8f9fa",
                "selected": "#e3f2fd",
                "disabled": "#6c757d",
            }

    def _apply_high_contrast(self, colors: Dict[str, str]) -> Dict[str, str]:
        """Apply high contrast modifications"""
        if colors["background"] == "#ffffff":  # Light theme
            colors.update(
                {
                    "background": "#ffffff",
                    "foreground": "#000000",
                    "border": "#000000",
                    "hover": "#e0e0e0",
                    "selected": "#0000ff",
                }
            )
        else:  # Dark theme
            colors.update(
                {
                    "background": "#000000",
                    "foreground": "#ffffff",
                    "border": "#ffffff",
                    "hover": "#333333",
                    "selected": "#ffff00",
                }
            )
        return colors

    def _load_custom_themes(self):
        """Load custom themes from directory"""
        try:
            if not self.custom_theme_dir.exists():
                return

            for theme_file in self.custom_theme_dir.glob("*.json"):
                try:
                    with open(theme_file, "r", encoding="utf-8") as f:
                        theme_data = json.load(f)

                    theme_config = ThemeConfiguration(**theme_data)
                    self.themes[theme_config.name] = theme_config

                except Exception as e:
                    self.logger_system.error(
                        f"Failed to load custom theme {theme_file}: {e}"
                    )

            custom_count = len(
                [
                    t
                    for t in self.themes.values()
                    if t.author != "CursorBLD + Kiro Integration"
                ]
            )
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "custom_themes_loaded",
                f"Loaded {custom_count} custom themes",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_custom_themes"},
                AIComponent.CURSOR,
            )

    def _load_accessibility_settings(self):
        """Load accessibility settings"""
        try:
            self.accessibility_enabled = self.config_manager.get_setting(
                "ui.accessibility_enabled", True
            )
            self.high_contrast_mode = self.config_manager.get_setting(
                "ui.high_contrast_mode", False
            )
            self.large_fonts_mode = self.config_manager.get_setting(
                "ui.large_fonts_mode", False
            )

            # Performance settings
            self.animation_enabled = self.config_manager.get_setting(
                "ui.animation_enabled", True
            )
            self.transparency_enabled = self.config_manager.get_setting(
                "ui.transparency_enabled", True
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_accessibility_settings"},
                AIComponent.CURSOR,
            )

    # IThemeManager implementation

    def get_available_themes(self) -> List[str]:
        """Get list of available theme names"""
        return list(self.themes.keys())

    def apply_theme(self, theme_name: str) -> bool:
        """Apply theme with seamless transition"""
        try:
            if theme_name not in self.themes:
                self.theme_error.emit(theme_name, f"Theme '{theme_name}' not found")
                return False

            old_theme = self.current_theme
            theme_config = self.themes[theme_name]

            # Emit transition request signal
            self.theme_change_requested.emit(old_theme, theme_name)

            # Start transition process
            self._apply_theme_transition(theme_config)

            # Update current theme
            self.current_theme = theme_name

            # Update application state
            self.state_manager.update_state(current_theme=theme_name)

            # Save to configuration
            self.config_manager.set_setting("ui.theme", theme_name)

            # Emit signals
            self.theme_applied.emit(theme_name)
            self.theme_changed.emit(theme_name)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "theme_applied",
                f"Theme applied: {old_theme} -> {theme_name}",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "apply_theme", "theme": theme_name},
                AIComponent.CURSOR,
            )
            self.theme_error.emit(theme_name, str(e))
            return False

    def _apply_theme_transition(self, theme_config: ThemeConfiguration):
        """Apply theme with smooth transition"""
        try:
            app = QApplication.instance()
            if not app:
                return

            # Progress tracking
            progress = 0
            self.theme_transition_progress.emit(progress)

            # Step 1: Apply Qt theme (if available)
            if (
                self.qt_theme_manager
                and theme_config.qt_theme_name in self.qt_themes_available
            ):
                self.qt_theme_manager.apply_theme(theme_config.qt_theme_name)
                progress = 25
                self.theme_transition_progress.emit(progress)

            # Step 2: Apply color scheme
            if theme_config.color_scheme:
                self._apply_color_scheme(theme_config.color_scheme)
                progress = 50
                self.theme_transition_progress.emit(progress)

            # Step 3: Apply accessibility features
            if self.accessibility_enabled:
                self._apply_accessibility_features(theme_config.accessibility_features)
                progress = 75
                self.theme_transition_progress.emit(progress)

            # Step 4: Apply performance settings
            self._apply_performance_settings(theme_config.performance_settings)
            progress = 100
            self.theme_transition_progress.emit(progress)

            # Apply custom stylesheet if available
            if theme_config.style_sheet:
                app.setStyleSheet(theme_config.style_sheet)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "apply_theme_transition", "theme": theme_config.name},
                AIComponent.CURSOR,
            )

    def _apply_color_scheme(self, color_scheme: Dict[str, str]):
        """Apply color scheme to application"""
        try:
            app = QApplication.instance()
            if not app:
                return

            # Generate stylesheet from color scheme
            stylesheet = self._generate_stylesheet(color_scheme)

            # Apply with smooth transition
            current_stylesheet = app.styleSheet()

            # Merge stylesheets for smooth transition
            if current_stylesheet:
                # Gradually transition colors (simplified approach)
                app.setStyleSheet(stylesheet)
            else:
                app.setStyleSheet(stylesheet)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "apply_color_scheme"},
                AIComponent.CURSOR,
            )

    def _generate_stylesheet(self, color_scheme: Dict[str, str]) -> str:
        """Generate Qt stylesheet from color scheme"""
        return f"""
        QMainWindow {{
            background-color: {color_scheme.get('background', '#ffffff')};
            color: {color_scheme.get('foreground', '#000000')};
        }}

        QWidget {{
            background-color: {color_scheme.get('background', '#ffffff')};
            color: {color_scheme.get('foreground', '#000000')};
            border: 1px solid {color_scheme.get('border', '#dee2e6')};
        }}

        QPushButton {{
            background-color: {color_scheme.get('primary', '#007acc')};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}

        QPushButton:hover {{
            background-color: {color_scheme.get('hover', '#0056b3')};
        }}

        QPushButton:pressed {{
            background-color: {color_scheme.get('selected', '#004085')};
        }}

        QListWidget {{
            background-color: {color_scheme.get('background', '#ffffff')};
            color: {color_scheme.get('foreground', '#000000')};
            border: 1px solid {color_scheme.get('border', '#dee2e6')};
        }}

        QListWidget::item:selected {{
            background-color: {color_scheme.get('selected', '#e3f2fd')};
        }}

        QListWidget::item:hover {{
            background-color: {color_scheme.get('hover', '#f8f9fa')};
        }}

        QScrollBar:vertical {{
            background-color: {color_scheme.get('background', '#ffffff')};
            border: 1px solid {color_scheme.get('border', '#dee2e6')};
            width: 12px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {color_scheme.get('secondary', '#6c757d')};
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {color_scheme.get('primary', '#007acc')};
        }}

        QStatusBar {{
            background-color: {color_scheme.get('background', '#ffffff')};
            color: {color_scheme.get('foreground', '#000000')};
            border-top: 1px solid {color_scheme.get('border', '#dee2e6')};
        }}

        QToolBar {{
            background-color: {color_scheme.get('background', '#ffffff')};
            border-bottom: 1px solid {color_scheme.get('border', '#dee2e6')};
        }}

        QMenuBar {{
            background-color: {color_scheme.get('background', '#ffffff')};
            color: {color_scheme.get('foreground', '#000000')};
        }}

        QMenuBar::item:selected {{
            background-color: {color_scheme.get('hover', '#f8f9fa')};
        }}

        QMenu {{
            background-color: {color_scheme.get('background', '#ffffff')};
            color: {color_scheme.get('foreground', '#000000')};
            border: 1px solid {color_scheme.get('border', '#dee2e6')};
        }}

        QMenu::item:selected {{
            background-color: {color_scheme.get('selected', '#e3f2fd')};
        }}
        """

    def _apply_accessibility_features(self, accessibility_features: Dict[str, bool]):
        """Apply accessibility features"""
        try:
            app = QApplication.instance()
            if not app:
                return

            # High contrast mode
            if accessibility_features.get("high_contrast", False):
                self.high_contrast_mode = True
                # Apply high contrast styles

            # Large fonts mode
            if accessibility_features.get("large_fonts", False):
                self.large_fonts_mode = True
                font = app.font()
                font.setPointSize(font.pointSize() + 2)
                app.setFont(font)

            # Focus indicators
            if accessibility_features.get("focus_indicators", True):
                # Ensure focus indicators are visible
                pass

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "apply_accessibility_features"},
                AIComponent.CURSOR,
            )

    def _apply_performance_settings(self, performance_settings: Dict[str, Any]):
        """Apply performance settings"""
        try:
            # Animation settings
            self.animation_enabled = performance_settings.get("animation_enabled", True)

            # Transparency settings
            self.transparency_enabled = performance_settings.get(
                "transparency_enabled", True
            )

            # Update configuration
            self.config_manager.set_setting(
                "ui.animation_enabled", self.animation_enabled
            )
            self.config_manager.set_setting(
                "ui.transparency_enabled", self.transparency_enabled
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "apply_performance_settings"},
                AIComponent.CURSOR,
            )

    def get_theme_config(self, theme_name: str) -> Optional[ThemeConfiguration]:
        """Get theme configuration"""
        return self.themes.get(theme_name)

    def create_custom_theme(self, theme_config: ThemeConfiguration) -> bool:
        """Create custom theme"""
        try:
            # Validate theme configuration
            if not theme_config.name or not theme_config.display_name:
                return False

            # Save theme configuration
            theme_file = self.custom_theme_dir / f"{theme_config.name}.json"

            theme_data = {
                "name": theme_config.name,
                "display_name": theme_config.display_name,
                "description": theme_config.description,
                "version": theme_config.version,
                "author": theme_config.author,
                "qt_theme_name": theme_config.qt_theme_name,
                "style_sheet": theme_config.style_sheet,
                "color_scheme": theme_config.color_scheme,
                "accessibility_features": theme_config.accessibility_features,
                "performance_settings": theme_config.performance_settings,
                "custom_properties": theme_config.custom_properties,
            }

            with open(theme_file, "w", encoding="utf-8") as f:
                json.dump(theme_data, f, indent=2)

            # Add to themes
            self.themes[theme_config.name] = theme_config

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "custom_theme_created",
                f"Custom theme created: {theme_config.name}",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_custom_theme", "theme": theme_config.name},
                AIComponent.CURSOR,
            )
            return False

    def delete_custom_theme(self, theme_name: str) -> bool:
        """Delete custom theme"""
        try:
            if theme_name not in self.themes:
                return False

            theme_config = self.themes[theme_name]

            # Don't delete built-in themes
            if theme_config.author == "CursorBLD + Kiro Integration":
                return False

            # Delete theme file
            theme_file = self.custom_theme_dir / f"{theme_name}.json"
            if theme_file.exists():
                theme_file.unlink()

            # Remove from themes
            del self.themes[theme_name]

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "custom_theme_deleted",
                f"Custom theme deleted: {theme_name}",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "delete_custom_theme", "theme": theme_name},
                AIComponent.CURSOR,
            )
            return False

    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.current_theme

    def is_dark_theme(self, theme_name: str = None) -> bool:
        """Check if theme is dark"""
        if theme_name is None:
            theme_name = self.current_theme

        if theme_name in self.themes:
            return self.themes[theme_name].is_dark_theme

        return False

    def get_accessibility_score(self, theme_name: str = None) -> float:
        """Get accessibility score for theme"""
        if theme_name is None:
            theme_name = self.current_theme

        if theme_name in self.themes:
            return self.themes[theme_name].accessibility_score

        return 0.0

    def _initialize_qt_theme_manager(self):
        """Initialize Qt-Theme-Manager integration (CursorBLD feature)"""

        try:
            # Try to import and initialize qt-theme-manager
            # This is a placeholder - actual implementation would depend on the library

            # Simulate CursorBLD's 16 available themes
            self.qt_themes_available = [
                "default",
                "dark",
                "blue",
                "green",
                "purple",
                "orange",
                "red",
                "pink",
                "cyan",
                "yellow",
                "brown",
                "gray",
                "light_blue",
                "light_green",
                "light_purple",
                "high_contrast",
            ]

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "qt_theme_init",
                f"Qt-Theme-Manager initialized with {len(self.qt_themes_available)} themes",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "qt_theme_init"},
                AIComponent.CURSOR,
            )
            # Fallback to basic themes
            self.qt_themes_available = ["default", "dark"]

    def _load_builtin_themes(self):
        """Load built-in theme configurations"""

        # Default theme (CursorBLD style)
        default_theme = ThemeConfiguration(
            name="default",
            display_name="Default Light",
            description="Default light theme with clean design",
            qt_theme_name="default",
            color_scheme={
                "background": "#ffffff",
                "foreground": "#000000",
                "primary": "#0078d4",
                "secondary": "#6c757d",
                "accent": "#007acc",
                "border": "#dee2e6",
                "hover": "#f8f9fa",
                "selected": "#e3f2fd",
            },
            accessibility_features={
                "high_contrast": False,
                "large_fonts": False,
                "screen_reader_support": True,
                "keyboard_navigation": True,
                "focus_indicators": True,
            },
            performance_settings={
                "animation_enabled": True,
                "transparency_enabled": True,
                "shadow_effects": True,
                "gradient_rendering": True,
                "anti_aliasing": True,
            },
        )
        self.themes["default"] = default_theme

        # Dark theme (CursorBLD style)
        dark_theme = ThemeConfiguration(
            name="dark",
            display_name="Dark",
            description="Dark theme for reduced eye strain",
            qt_theme_name="dark",
            color_scheme={
                "background": "#2b2b2b",
                "foreground": "#ffffff",
                "primary": "#0078d4",
                "secondary": "#6c757d",
                "accent": "#007acc",
                "border": "#404040",
                "hover": "#3c3c3c",
                "selected": "#0d47a1",
            },
            accessibility_features={
                "high_contrast": False,
                "large_fonts": False,
                "screen_reader_support": True,
                "keyboard_navigation": True,
                "focus_indicators": True,
            },
            performance_settings={
                "animation_enabled": True,
                "transparency_enabled": True,
                "shadow_effects": True,
                "gradient_rendering": True,
                "anti_aliasing": True,
            },
        )
        self.themes["dark"] = dark_theme

        # High contrast theme (Kiro accessibility enhancement)
        high_contrast_theme = ThemeConfiguration(
            name="high_contrast",
            display_name="High Contrast",
            description="High contrast theme for accessibility",
            qt_theme_name="high_contrast",
            color_scheme={
                "background": "#000000",
                "foreground": "#ffffff",
                "primary": "#ffff00",
                "secondary": "#ffffff",
                "accent": "#00ff00",
                "border": "#ffffff",
                "hover": "#333333",
                "selected": "#0000ff",
            },
            accessibility_features={
                "high_contrast": True,
                "large_fonts": True,
                "screen_reader_support": True,
                "keyboard_navigation": True,
                "focus_indicators": True,
            },
            performance_settings={
                "animation_enabled": False,
                "transparency_enabled": False,
                "shadow_effects": False,
                "gradient_rendering": False,
                "anti_aliasing": True,
            },
        )
        self.themes["high_contrast"] = high_contrast_theme

        # Create additional CursorBLD-style themes
        color_variants = [
            ("blue", "Blue", "#1976d2", "#bbdefb"),
            ("green", "Green", "#388e3c", "#c8e6c9"),
            ("purple", "Purple", "#7b1fa2", "#e1bee7"),
            ("orange", "Orange", "#f57c00", "#ffe0b2"),
            ("red", "Red", "#d32f2f", "#ffcdd2"),
        ]

        for name, display, primary, accent in color_variants:
            theme = ThemeConfiguration(
                name=name,
                display_name=display,
                description=f"{display} themed interface",
                qt_theme_name=name,
                color_scheme={
                    "background": "#ffffff",
                    "foreground": "#000000",
                    "primary": primary,
                    "secondary": "#6c757d",
                    "accent": accent,
                    "border": "#dee2e6",
                    "hover": "#f8f9fa",
                    "selected": accent,
                },
            )
            self.themes[name] = theme

    def _load_custom_themes(self):
        """Load custom theme configurations"""

        try:
            for theme_file in self.custom_theme_dir.glob("*.json"):
                try:
                    with open(theme_file, "r", encoding="utf-8") as f:
                        theme_data = json.load(f)

                    # Create theme configuration
                    theme = ThemeConfiguration(
                        name=theme_data.get("name", theme_file.stem),
                        display_name=theme_data.get("display_name", theme_file.stem),
                        description=theme_data.get("description", ""),
                        qt_theme_name=theme_data.get("qt_theme_name", "default"),
                        color_scheme=theme_data.get("color_scheme", {}),
                        accessibility_features=theme_data.get(
                            "accessibility_features", {}
                        ),
                        performance_settings=theme_data.get("performance_settings", {}),
                    )

                    # Validate theme
                    if self.validate_theme_config(theme_data):
                        self.themes[theme.name] = theme

                        self.logger_system.log_ai_operation(
                            AIComponent.CURSOR,
                            "custom_theme_load",
                            f"Loaded custom theme: {theme.name}",
                        )

                except Exception as e:
                    self.error_handler.handle_error(
                        e,
                        ErrorCategory.UI_ERROR,
                        {"operation": "custom_theme_load", "file": str(theme_file)},
                        AIComponent.CURSOR,
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "custom_themes_load"},
                AIComponent.CURSOR,
            )

    def _load_accessibility_settings(self):
        """Load accessibility settings (Kiro enhancement)"""

        self.accessibility_enabled = self.config_manager.get_setting(
            "ui.accessibility_enabled", True
        )
        self.high_contrast_mode = self.config_manager.get_setting(
            "ui.high_contrast_mode", False
        )
        self.large_fonts_mode = self.config_manager.get_setting(
            "ui.large_fonts_mode", False
        )

    def _load_performance_settings(self):
        """Load performance settings (Kiro enhancement)"""

        self.animation_enabled = self.config_manager.get_setting(
            "ui.animation_enabled", True
        )
        self.transparency_enabled = self.config_manager.get_setting(
            "ui.transparency_enabled", True
        )

    # IThemeManager implementation

    def get_available_themes(self) -> List[str]:
        """Get list of available theme names"""

        return list(self.themes.keys())

    def apply_theme(self, theme_name: str) -> bool:
        """Apply the specified theme to the application"""

        try:
            if theme_name not in self.themes:
                self.theme_error.emit(theme_name, f"Theme '{theme_name}' not found")
                return False

            theme = self.themes[theme_name]

            # Apply Qt theme (CursorBLD integration)
            success = self._apply_qt_theme(theme)

            if success:
                # Apply accessibility features (Kiro enhancement)
                self._apply_accessibility_features(theme)

                # Apply performance settings (Kiro enhancement)
                self._apply_performance_settings(theme)

                # Update current theme
                self.current_theme = theme_name

                # Update configuration
                self.config_manager.set_setting("ui.theme", theme_name)

                # Update state
                self.state_manager.update_state(current_theme=theme_name)

                # Emit signal
                self.theme_changed.emit(theme_name)

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR, "theme_apply", f"Theme applied: {theme_name}"
                )

                return True
            else:
                self.theme_error.emit(theme_name, "Failed to apply Qt theme")
                return False

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_apply", "theme": theme_name},
                AIComponent.CURSOR,
            )
            return False

    def get_theme_config(self, theme_name: str) -> Dict[str, Any]:
        """Get configuration for the specified theme"""

        if theme_name in self.themes:
            theme = self.themes[theme_name]
            return {
                "name": theme.name,
                "display_name": theme.display_name,
                "description": theme.description,
                "color_scheme": theme.color_scheme,
                "accessibility_features": theme.accessibility_features,
                "performance_settings": theme.performance_settings,
                "is_dark_theme": theme.is_dark_theme,
                "accessibility_score": theme.accessibility_score,
            }

        return {}

    def get_current_theme(self) -> str:
        """Get the currently active theme name"""

        return self.current_theme

    def create_custom_theme(self, name: str, config: Dict[str, Any]) -> bool:
        """Create a new custom theme"""

        try:
            # Validate configuration
            if not self.validate_theme_config(config):
                return False

            # Create theme configuration
            theme = ThemeConfiguration(
                name=name,
                display_name=config.get("display_name", name),
                description=config.get("description", ""),
                qt_theme_name=config.get("qt_theme_name", "default"),
                color_scheme=config.get("color_scheme", {}),
                accessibility_features=config.get("accessibility_features", {}),
                performance_settings=config.get("performance_settings", {}),
            )

            # Add to themes
            self.themes[name] = theme

            # Save to file
            theme_file = self.custom_theme_dir / f"{name}.json"
            with open(theme_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "custom_theme_create",
                f"Custom theme created: {name}",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "custom_theme_create", "theme": name},
                AIComponent.CURSOR,
            )
            return False

    def validate_theme_config(self, config: Dict[str, Any]) -> bool:
        """Validate theme configuration"""

        try:
            # Required fields
            required_fields = ["name"]
            for field in required_fields:
                if field not in config:
                    return False

            # Validate color scheme
            if "color_scheme" in config:
                color_scheme = config["color_scheme"]
                if not isinstance(color_scheme, dict):
                    return False

                # Check for valid color values
                for color_name, color_value in color_scheme.items():
                    if not isinstance(color_value, str):
                        return False

                    # Basic hex color validation
                    if color_value.startswith("#") and len(color_value) not in [4, 7]:
                        return False

            # Validate accessibility features
            if "accessibility_features" in config:
                accessibility = config["accessibility_features"]
                if not isinstance(accessibility, dict):
                    return False

                # Check boolean values
                for feature, enabled in accessibility.items():
                    if not isinstance(enabled, bool):
                        return False

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_validation"},
                AIComponent.CURSOR,
            )
            return False

    # Theme application methods

    def _apply_qt_theme(self, theme: ThemeConfiguration) -> bool:
        """Apply Qt theme (CursorBLD integration)"""

        try:
            app = QApplication.instance()
            if not app:
                return False

            # Generate stylesheet from theme configuration
            stylesheet = self._generate_stylesheet(theme)

            # Apply stylesheet
            app.setStyleSheet(stylesheet)

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "qt_theme_apply", "theme": theme.name},
                AIComponent.CURSOR,
            )
            return False

    def _generate_stylesheet(self, theme: ThemeConfiguration) -> str:
        """Generate Qt stylesheet from theme configuration"""

        colors = theme.color_scheme

        # Basic stylesheet template
        stylesheet = f"""
        QMainWindow {{
            background-color: {colors.get('background', '#ffffff')};
            color: {colors.get('foreground', '#000000')};
        }}

        QMenuBar {{
            background-color: {colors.get('background', '#ffffff')};
            color: {colors.get('foreground', '#000000')};
            border-bottom: 1px solid {colors.get('border', '#dee2e6')};
        }}

        QMenuBar::item {{
            padding: 4px 8px;
            background-color: transparent;
        }}

        QMenuBar::item:selected {{
            background-color: {colors.get('hover', '#f8f9fa')};
        }}

        QToolBar {{
            background-color: {colors.get('background', '#ffffff')};
            border: 1px solid {colors.get('border', '#dee2e6')};
            spacing: 2px;
        }}

        QPushButton {{
            background-color: {colors.get('primary', '#0078d4')};
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }}

        QPushButton:hover {{
            background-color: {colors.get('accent', '#007acc')};
        }}

        QPushButton:pressed {{
            background-color: {colors.get('secondary', '#6c757d')};
        }}

        QLabel {{
            color: {colors.get('foreground', '#000000')};
        }}

        QStatusBar {{
            background-color: {colors.get('background', '#ffffff')};
            color: {colors.get('foreground', '#000000')};
            border-top: 1px solid {colors.get('border', '#dee2e6')};
        }}

        QSplitter::handle {{
            background-color: {colors.get('border', '#dee2e6')};
        }}

        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        QSplitter::handle:vertical {{
            height: 2px;
        }}
        """

        # Add accessibility enhancements if enabled
        if theme.accessibility_features.get("high_contrast", False):
            stylesheet += f"""
            * {{
                outline: 2px solid {colors.get('accent', '#007acc')} !important;
            }}
            """

        if theme.accessibility_features.get("large_fonts", False):
            stylesheet += """
            * {
                font-size: 14px;
            }
            """

        return stylesheet

    def _apply_accessibility_features(self, theme: ThemeConfiguration):
        """Apply accessibility features (Kiro enhancement)"""

        try:
            accessibility = theme.accessibility_features

            # Update accessibility state
            self.high_contrast_mode = accessibility.get("high_contrast", False)
            self.large_fonts_mode = accessibility.get("large_fonts", False)

            # Save accessibility settings
            self.config_manager.set_setting(
                "ui.high_contrast_mode", self.high_contrast_mode
            )
            self.config_manager.set_setting(
                "ui.large_fonts_mode", self.large_fonts_mode
            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "accessibility_apply",
                f"Accessibility features applied: {accessibility}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "accessibility_apply"},
                AIComponent.KIRO,
            )

    def _apply_performance_settings(self, theme: ThemeConfiguration):
        """Apply performance settings (Kiro enhancement)"""

        try:
            performance = theme.performance_settings

            # Update performance state
            self.animation_enabled = performance.get("animation_enabled", True)
            self.transparency_enabled = performance.get("transparency_enabled", True)

            # Save performance settings
            self.config_manager.set_setting(
                "ui.animation_enabled", self.animation_enabled
            )
            self.config_manager.set_setting(
                "ui.transparency_enabled", self.transparency_enabled
            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_apply",
                f"Performance settings applied: {performance}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "performance_apply"},
                AIComponent.KIRO,
            )

    # Utility methods

    def get_theme_preview(self, theme_name: str) -> Dict[str, Any]:
        """Get theme preview information"""

        if theme_name not in self.themes:
            return {}

        theme = self.themes[theme_name]

        return {
            "name": theme.name,
            "display_name": theme.display_name,
            "description": theme.description,
            "primary_color": theme.color_scheme.get("primary", "#0078d4"),
            "background_color": theme.color_scheme.get("background", "#ffffff"),
            "is_dark": theme.is_dark_theme,
            "accessibility_score": theme.accessibility_score,
        }

    def export_theme(self, theme_name: str, file_path: Path) -> bool:
        """Export theme configuration to file"""

        try:
            if theme_name not in self.themes:
                return False

            theme = self.themes[theme_name]
            theme_data = {
                "name": theme.name,
                "display_name": theme.display_name,
                "description": theme.description,
                "qt_theme_name": theme.qt_theme_name,
                "color_scheme": theme.color_scheme,
                "accessibility_features": theme.accessibility_features,
                "performance_settings": theme.performance_settings,
                "export_timestamp": theme.created_date.isoformat(),
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(theme_data, f, indent=2)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "theme_export",
                f"Theme exported: {theme_name} to {file_path}",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_export", "theme": theme_name},
                AIComponent.CURSOR,
            )
            return False

    def import_theme(self, file_path: Path) -> bool:
        """Import theme configuration from file"""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                theme_data = json.load(f)

            theme_name = theme_data.get("name", file_path.stem)

            return self.create_custom_theme(theme_name, theme_data)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_import", "file": str(file_path)},
                AIComponent.CURSOR,
            )
            return False
