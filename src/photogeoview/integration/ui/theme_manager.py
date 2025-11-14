"""
Integrated Theme Manager for AI Integration

Combines CursorBLD's Qt-Theme-Manager integration with Kiro enhancements:
- CursorBLD: 16 theme variations, Qt-Theme-Manager integration
- Kiro: Accessibility features, performance optimization, validation

Author: Kiro AI Integration System
"""

import json
import platform
from pathlib import Path
from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent, ThemeConfiguration
from ..state_manager import StateManager


class QtThemeManagerProtocol(Protocol):
    """Protocol for Qt theme manager"""

    def get_available_themes(self) -> dict[str, Any]: ...
    def set_theme(self, theme_name: str) -> bool: ...


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
    theme_changed = Signal(str)
    theme_change_requested = Signal(str, str)  # old_theme, new_theme
    theme_applied = Signal(str)  # theme_name
    theme_error = Signal(str, str)  # theme_name, error_message
    theme_transition_progress = Signal(int)  # progress percentage

    # Compatibility signals for SimpleThemeManager
    theme_changed_compat = Signal(str, str)  # old_theme, new_theme

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
        main_window: QWidget | None = None,
    ):
        """
        Initialize the integrated theme manager

        Args:
            config_manager: Configuration manager instance
            state_manager: State manager instance
            logger_system: Logging system instance
            main_window: Reference to main window for style application
        """
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)
        self.main_window = main_window
        self.theme_dir = Path("config/themes")
        self.custom_theme_dir = Path("config/custom_themes")
        self.themes: dict[str, ThemeConfiguration] = {}
        self.current_theme = "default"
        self.is_windows = platform.system().lower().startswith("windows")
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
            current_theme = self.state_manager.get_state().current_theme or self.current_theme
            self.current_theme = current_theme
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

                self.qt_theme_manager = qt_theme_manager.ThemeController()
                if hasattr(self.qt_theme_manager, "get_available_themes"):
                    themes = self.qt_theme_manager.get_available_themes()
                    self.qt_themes_available = list(themes.keys())
                else:
                    self.qt_themes_available = ["default", "dark", "light"]
                    self.logger_system.warning(
                        "Qt-Theme-Manager initialized but " "get_available_themes method not found"
                    )

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "qt_theme_manager_init",
                    f"Qt-Theme-Manager initialized with " f"{len(self.qt_themes_available)} themes",
                )
            except ImportError:
                self.logger_system.warning("Qt-Theme-Manager not available, using fallback themes")
                self.qt_theme_manager = None
                self.qt_themes_available = ["default", "dark", "light"]

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "initialize_qt_theme_manager"},
                AIComponent.CURSOR,
            )

    def _load_builtin_themes(self):
        """Load built-in themes (CursorBLD 16 theme variations)"""
        try:
            self.logger_system.info("Loading built-in themes...")

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
                },
                {
                    "name": "performance",
                    "display_name": "Performance",
                    "base": "light",
                    "performance": True,
                },
            ]

            self.logger_system.info(f"Processing {len(builtin_themes)} built-in themes...")

            for theme_info in builtin_themes:
                try:
                    theme_config = self._create_builtin_theme_config(theme_info)
                    self.themes[theme_config.name] = theme_config
                    self.logger_system.info(f"Created theme: {theme_config.name} ({theme_config.display_name})")
                except Exception as e:
                    self.logger_system.error(f"Failed to create theme {theme_info['name']}: {e}")

            self.logger_system.info(f"Successfully loaded {len(self.themes)} built-in themes")
            self.logger_system.info(f"Available theme names: {list(self.themes.keys())}")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "builtin_themes_loaded",
                f"Loaded {len(self.themes)} built-in themes",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_builtin_themes"},
                AIComponent.CURSOR,
            )

    def _create_builtin_theme_config(self, theme_info: dict[str, Any]) -> ThemeConfiguration:
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

    def _get_base_colors(self, base: str) -> dict[str, str]:
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

    def _apply_high_contrast(self, colors: dict[str, str]) -> dict[str, str]:
        """Apply high contrast modifications"""
        if colors["background"] == "#ffffff":  # Light theme
            colors.update(
                {
                    "background": "#ffffff",
                    "foreground": "#000000",
                    "primary": "#0000ff",
                    "secondary": "#000000",
                    "accent": "#ff0000",
                    "border": "#000000",
                    "hover": "#ffff00",
                    "selected": "#00ff00",
                }
            )
        else:  # Dark theme
            colors.update(
                {
                    "background": "#000000",
                    "foreground": "#ffffff",
                    "primary": "#ffff00",
                    "secondary": "#ffffff",
                    "accent": "#00ff00",
                    "border": "#ffffff",
                    "hover": "#333333",
                    "selected": "#0000ff",
                }
            )
        return colors

    def _load_custom_themes(self):
        """Load custom theme configurations"""

        try:
            self.logger_system.info(f"Loading custom themes from: {self.custom_theme_dir}")

            for theme_file in self.custom_theme_dir.glob("*.json"):
                try:
                    self.logger_system.info(f"Processing theme file: {theme_file}")

                    with open(theme_file, encoding="utf-8") as f:
                        theme_data = json.load(f)

                    self.logger_system.info(f"Theme data type: {type(theme_data)}")

                    # テーマファイルが配列形式の場合の処理
                    if isinstance(theme_data, list):
                        self.logger_system.info(f"Processing {len(theme_data)} themes from array")
                        for theme_item in theme_data:
                            if isinstance(theme_item, dict) and self._validate_theme_config(theme_item):
                                theme_config = ThemeConfiguration(**theme_item)
                                self.themes[theme_config.name] = theme_config

                                self.logger_system.log_ai_operation(
                                    AIComponent.CURSOR,
                                    "custom_theme_loaded",
                                    f"Custom theme loaded: {theme_config.name}",
                                )
                    # 単一テーマの場合の処理
                    elif isinstance(theme_data, dict):
                        self.logger_system.info("Processing single theme")
                        if self._validate_theme_config(theme_data):
                            theme_config = ThemeConfiguration(**theme_data)
                            self.themes[theme_config.name] = theme_config

                            self.logger_system.log_ai_operation(
                                AIComponent.CURSOR,
                                "custom_theme_loaded",
                                f"Custom theme loaded: {theme_config.name}",
                            )

                except Exception as e:
                    self.logger_system.warning(f"Failed to load custom theme {theme_file}: {e}")

            self.logger_system.info(f"Total themes loaded: {len(self.themes)}")
            self.logger_system.info(f"Available themes: {list(self.themes.keys())}")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_custom_themes"},
                AIComponent.CURSOR,
            )

    def _validate_theme_config(self, config: dict[str, Any]) -> bool:
        """Validate theme configuration"""
        required_fields = ["name", "display_name"]
        return all(field in config for field in required_fields)

    def _load_accessibility_settings(self):
        """Load accessibility settings"""
        try:
            self.accessibility_enabled = self.config_manager.get_setting("ui.accessibility_enabled", True)
            self.high_contrast_mode = self.config_manager.get_setting("ui.high_contrast_mode", False)
            self.large_fonts_mode = self.config_manager.get_setting("ui.large_fonts_mode", False)

            # Performance settings
            self.animation_enabled = self.config_manager.get_setting("ui.animation_enabled", True)
            self.transparency_enabled = self.config_manager.get_setting("ui.transparency_enabled", True)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_accessibility_settings"},
                AIComponent.CURSOR,
            )

    # IThemeManager implementation

    def get_available_themes(self) -> list[str]:
        """Get list of available theme names"""
        themes_list = list(self.themes.keys())
        self.logger_system.info(f"get_available_themes called, returning {len(themes_list)} themes: {themes_list}")
        return themes_list

    def debug_theme_status(self):
        """デバッグ用:テーマの状況を詳細にログ出力"""
        try:
            self.logger_system.info("=== Theme Manager Debug Status ===")
            self.logger_system.info(f"Total themes loaded: {len(self.themes)}")
            self.logger_system.info(f"Current theme: {self.current_theme}")
            self.logger_system.info(f"Available themes: {list(self.themes.keys())}")

            for theme_name, theme_config in self.themes.items():
                self.logger_system.info(f"  - {theme_name}: {theme_config.display_name}")
                if hasattr(theme_config, "color_scheme"):
                    self.logger_system.info(f"    Colors: {theme_config.color_scheme}")
                if hasattr(theme_config, "style_sheet"):
                    self.logger_system.info(f"    Style sheet length: {len(theme_config.style_sheet)}")

            self.logger_system.info("=== End Theme Manager Debug Status ===")

        except Exception as e:
            self.logger_system.error(f"Error in debug_theme_status: {e}")

    def apply_theme(self, theme_name: str) -> bool:
        """Apply the specified theme to the application - 改善版"""

        try:
            self.logger_system.info(f"Starting theme application: {theme_name}")

            if theme_name not in self.themes:
                self.logger_system.error(
                    f"Theme '{theme_name}' not found in available themes: {list(self.themes.keys())}"
                )
                self.theme_error.emit(theme_name, f"Theme '{theme_name}' not found")
                return False

            theme = self.themes[theme_name]
            self.logger_system.info(f"Found theme configuration: {theme.name} - {theme.display_name}")

            # Apply Qt theme (CursorBLD integration)
            success = self._apply_qt_theme(theme)

            if success:
                self.logger_system.info("Qt theme applied successfully, applying additional features...")

                # Apply accessibility features (Kiro enhancement)
                try:
                    self._apply_accessibility_features(theme)
                    self.logger_system.info("Accessibility features applied")
                except Exception as e:
                    self.logger_system.warning(f"Failed to apply accessibility features: {e}")

                # Apply performance settings (Kiro enhancement)
                try:
                    self._apply_performance_settings(theme)
                    self.logger_system.info("Performance settings applied")
                except Exception as e:
                    self.logger_system.warning(f"Failed to apply performance settings: {e}")

                # Update current theme
                old_theme = self.current_theme
                self.current_theme = theme_name

                # Update configuration
                try:
                    self.config_manager.set_setting("ui.theme", theme_name)
                    self.logger_system.info("Theme configuration saved")
                except Exception as e:
                    self.logger_system.warning(f"Failed to save theme configuration: {e}")

                # Update state
                try:
                    self.state_manager.update_state(current_theme=theme_name)
                    self.logger_system.info("Theme state updated")
                except Exception as e:
                    self.logger_system.warning(f"Failed to update theme state: {e}")

                # Emit signals
                try:
                    self.theme_changed.emit(theme_name)
                    # Emit compatibility signal for SimpleThemeManager
                    self.theme_changed_compat.emit(old_theme, theme_name)
                    self.theme_applied.emit(theme_name)
                    self.logger_system.info("Theme change signals emitted")
                except Exception as e:
                    self.logger_system.warning(f"Failed to emit theme signals: {e}")

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "theme_apply",
                    f"Theme applied successfully: {theme_name}",
                )

                self.logger_system.info(f"Theme application completed successfully: {theme_name}")
                return True
            else:
                self.logger_system.error(f"Failed to apply Qt theme: {theme_name}")
                self.theme_error.emit(theme_name, "Failed to apply Qt theme")
                return False

        except Exception as e:
            self.logger_system.error(f"Exception during theme application: {e}")
            import traceback

            self.logger_system.error(f"Traceback: {traceback.format_exc()}")

            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_apply", "theme": theme_name},
                AIComponent.CURSOR,
            )
            return False

    def get_theme_config(self, theme_name: str) -> dict[str, Any]:
        """Get configuration for the specified theme"""

        # Return basic theme info based on theme name
        is_dark = "dark" in theme_name.lower()

        # Define color schemes for different theme types
        if is_dark:
            color_scheme = {
                "border": "#2c3e50",
                "primary": "#3498db",
                "accent": "#2980b9",
                "background": "#2c3e50",
                "text": "#ecf0f1",
            }
        else:
            color_scheme = {
                "border": "#bdc3c7",
                "primary": "#3498db",
                "accent": "#2980b9",
                "background": "#ffffff",
                "text": "#2c3e50",
            }

        return {
            "name": theme_name,
            "display_name": theme_name.replace("_", " ").title(),
            "description": f"{theme_name} theme",
            "color_scheme": color_scheme,
            "accessibility_features": {},
            "performance_settings": {},
            "is_dark_theme": is_dark,
            "accessibility_score": 0.8,
        }

    def get_theme_info(self, theme_name: str) -> dict[str, Any] | None:
        """Get theme info (compatibility method for ThemeToggleButton)"""
        theme_config = self.get_theme_config(theme_name)
        if theme_config:
            return {
                "display_name": theme_config.get("display_name", theme_name),
                "description": theme_config.get("description", f"{theme_name} theme"),
                "name": theme_name,
            }
        return None

    def get_color(self, color_type: str, default_color: str = "#000000") -> str:
        """Get color for the specified type (compatibility method)"""
        try:
            current_theme = self.get_current_theme()
            theme_config = self.get_theme_config(current_theme)

            if theme_config and "color_scheme" in theme_config:
                color_scheme = theme_config["color_scheme"]
                if color_type in color_scheme:
                    return color_scheme[color_type]

            # Fallback colors based on theme type
            if current_theme in ["dark", "dark_blue", "dark_green", "dark_purple"]:
                if color_type == "border":
                    return "#2c3e50"
                elif color_type == "primary":
                    return "#3498db"
                elif color_type == "accent":
                    return "#2980b9"
            else:  # Light themes
                if color_type == "border":
                    return "#bdc3c7"
                elif color_type == "primary":
                    return "#3498db"
                elif color_type == "accent":
                    return "#2980b9"

            return default_color
        except Exception:
            return default_color

    def get_current_theme(self) -> str:
        """Get the currently active theme name"""
        return self.current_theme

    def create_custom_theme(self, name: str, config: dict[str, Any]) -> bool:
        """Create a new custom theme"""

        try:
            if name in self.themes:
                self.logger_system.warning(f"Theme '{name}' already exists")
                return False

            if not self._validate_theme_config(config):
                self.logger_system.warning(f"Invalid theme configuration for '{name}'")
                return False

            # Create theme file
            theme_file = self.custom_theme_dir / f"{name}.json"
            with open(theme_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # Load the new theme
            theme_config = ThemeConfiguration(**config)
            self.themes[name] = theme_config

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "custom_theme_created",
                f"Custom theme created: {name}",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_custom_theme", "theme": name},
                AIComponent.CURSOR,
            )
            return False

    def validate_theme_config(self, config: dict[str, Any]) -> bool:
        """Validate theme configuration"""
        return self._validate_theme_config(config)

    # Private helper methods

    def _apply_qt_theme(self, theme: ThemeConfiguration) -> bool:
        """Apply Qt theme (CursorBLD integration) - 改善版"""
        try:
            self.logger_system.info(f"Applying Qt theme: {theme.name}")
            success = True

            # 1. Qt-Theme-Managerのテーマを適用
            if self.qt_theme_manager and hasattr(theme, "qt_theme_name") and theme.qt_theme_name:
                if hasattr(self.qt_theme_manager, "set_theme"):
                    qt_success = self.qt_theme_manager.set_theme(theme.qt_theme_name)
                    if qt_success:
                        self.logger_system.info(f"Qt-Theme-Manager theme applied: {theme.qt_theme_name}")
                    else:
                        self.logger_system.warning(f"Failed to apply Qt theme: {theme.qt_theme_name}")
                    success = qt_success and success
                else:
                    self.logger_system.warning("Qt-Theme-Manager set_theme method not found")
            else:
                self.logger_system.info("Qt-Theme-Manager not available or no qt_theme_name specified")

            # 2. カスタムスタイルシートを適用
            if hasattr(theme, "style_sheet") and theme.style_sheet:
                self.logger_system.info(f"Applying custom stylesheet: {len(theme.style_sheet)} characters")
                style_success = self._apply_style_sheet(theme.style_sheet)
                success = style_success and success
            else:
                self.logger_system.info("No custom stylesheet provided")

            # 3. カラースキームを適用(最も重要)
            if hasattr(theme, "color_scheme") and theme.color_scheme:
                self.logger_system.info(f"Applying color scheme: {list(theme.color_scheme.keys())}")
                color_success = self._apply_color_scheme(theme.color_scheme)
                success = color_success and success
            else:
                self.logger_system.warning("No color scheme provided, generating from theme name")
                # テーマ名からカラースキームを生成
                generated_scheme = self._generate_color_scheme_from_theme_name(theme.name)
                color_success = self._apply_color_scheme(generated_scheme)
                success = color_success and success

            if success:
                self.logger_system.info(f"Qt theme applied successfully: {theme.name}")
            else:
                self.logger_system.error(f"Failed to apply Qt theme: {theme.name}")

            return success

        except Exception as e:
            self.logger_system.error(f"Failed to apply Qt theme: {e}")
            import traceback

            self.logger_system.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _generate_color_scheme_from_theme_name(self, theme_name: str) -> dict[str, str]:
        """テーマ名からカラースキームを生成"""
        try:
            # ダークテーマの判定
            is_dark = any(keyword in theme_name.lower() for keyword in ["dark", "night", "black"])

            if is_dark:
                return {
                    "background": "#2b2b2b",
                    "foreground": "#ffffff",
                    "primary": "#007acc",
                    "secondary": "#6c757d",
                    "accent": "#17a2b8",
                    "success": "#28a745",
                    "warning": "#ffc107",
                    "error": "#dc3545",
                    "border": "#495057",
                    "hover": "#3a3a3a",
                    "selected": "#0d7377",
                    "disabled": "#6c757d",
                    "input_background": "#3a3a3a",
                    "button_text": "#ffffff",
                }
            else:
                return {
                    "background": "#ffffff",
                    "foreground": "#000000",
                    "primary": "#007acc",
                    "secondary": "#6c757d",
                    "accent": "#17a2b8",
                    "success": "#28a745",
                    "warning": "#ffc107",
                    "error": "#dc3545",
                    "border": "#dee2e6",
                    "hover": "#f8f9fa",
                    "selected": "#e3f2fd",
                    "disabled": "#6c757d",
                    "input_background": "#ffffff",
                    "button_text": "#ffffff",
                }
        except Exception as e:
            self.logger_system.error(f"Failed to generate color scheme: {e}")
            return self._get_default_color_scheme()

    def _apply_style_sheet(self, style_sheet: str) -> bool:
        """スタイルシートをアプリケーション全体に適用"""
        try:
            if not style_sheet:
                return True

            if self.is_windows:
                self.logger_system.warning(
                    "Windows safety mode: skipping stylesheet application to avoid Qt crash"
                )
                return True

            app = QApplication.instance()

            if app and hasattr(app, "setStyleSheet"):
                style_length = len(style_sheet)
                self.logger_system.info(
                    f"Applying stylesheet to QApplication (length={style_length} characters)"
                )
                app.setStyleSheet(style_sheet)
                self.logger_system.info(
                    f"Style sheet applied to QApplication: {style_length} characters"
                )
                return True

            # QApplicationが利用できない場合はメインウィンドウへの遅延適用を試みる
            if self.main_window:
                style_length = len(style_sheet)

                def _apply_to_main_window():
                    try:
                        self.logger_system.info(
                            f"Applying stylesheet to main window as fallback (length={style_length} characters)"
                        )
                        self.main_window.setStyleSheet(style_sheet)
                        self.logger_system.info(
                            f"Style sheet applied to main window: {style_length} characters"
                        )
                    except Exception as e:
                        self.logger_system.error(f"Failed to apply style sheet to main window: {e}")

                QTimer.singleShot(0, _apply_to_main_window)
                return True

            self.logger_system.warning("No QApplication or main window available for style sheet application")
            return False

        except Exception as e:
            self.logger_system.error(f"Failed to apply style sheet: {e}")
            return False

    def _apply_color_scheme(self, color_scheme: dict[str, str]) -> bool:
        """カラースキームをUIコンポーネントに適用(改善版)"""
        try:
            if not color_scheme:
                self.logger_system.warning("Color scheme is empty, generating default styles")
                # デフォルトのカラースキームを使用
                color_scheme = self._get_default_color_scheme()

            self.logger_system.info(f"Applying color scheme: {color_scheme}")

            # カラースキームに基づいてスタイルシートを生成
            stylesheet_parts: list[str] = []

            # 1. メインウィンドウとQWidgetの基本スタイル
            if "background" in color_scheme and "foreground" in color_scheme:
                bg_color = color_scheme["background"]
                fg_color = color_scheme["foreground"]

                main_style = f"""
                QMainWindow {{
                    background-color: {bg_color};
                    color: {fg_color};
                }}

                QWidget {{
                    background-color: {bg_color};
                    color: {fg_color};
                }}

                QFrame {{
                    background-color: {bg_color};
                    color: {fg_color};
                }}
                """
                stylesheet_parts.append(main_style)

            # 2. ボタンスタイル
            if "primary" in color_scheme:
                primary_color = color_scheme["primary"]
                hover_color = color_scheme.get("hover", self._darken_color(primary_color))
                button_text_color = color_scheme.get("button_text", "#ffffff")

                button_style = f"""
                QPushButton {{
                    background-color: {primary_color};
                    color: {button_text_color};
                    border: 1px solid {primary_color};
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }}

                QPushButton:hover {{
                    background-color: {hover_color};
                    border-color: {hover_color};
                }}

                QPushButton:pressed {{
                    background-color: {self._darken_color(primary_color, 0.2)};
                }}

                QPushButton:disabled {{
                    background-color: {color_scheme.get("disabled", "#cccccc")};
                    color: #666666;
                }}
                """
                stylesheet_parts.append(button_style)

            # 3. ラベルとテキストスタイル
            if "foreground" in color_scheme:
                fg_color = color_scheme["foreground"]
                color_scheme.get("secondary", fg_color)

                text_style = f"""
                QLabel {{
                    color: {fg_color};
                    background-color: transparent;
                }}

                QTextEdit {{
                    background-color: {color_scheme.get("input_background", color_scheme.get("background", "#ffffff"))};
                    color: {fg_color};
                    border: 1px solid {color_scheme.get("border", "#cccccc")};
                    border-radius: 3px;
                    padding: 4px;
                }}

                QLineEdit {{
                    background-color: {color_scheme.get("input_background", color_scheme.get("background", "#ffffff"))};
                    color: {fg_color};
                    border: 1px solid {color_scheme.get("border", "#cccccc")};
                    border-radius: 3px;
                    padding: 4px;
                }}
                """
                stylesheet_parts.append(text_style)

            # 4. メニューとツールバースタイル
            if "background" in color_scheme and "foreground" in color_scheme:
                bg_color = color_scheme["background"]
                fg_color = color_scheme["foreground"]
                selected_color = color_scheme.get("selected", color_scheme.get("primary", "#0078d4"))

                menu_style = f"""
                QMenuBar {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border-bottom: 1px solid {color_scheme.get("border", "#cccccc")};
                }}

                QMenuBar::item {{
                    background-color: transparent;
                    padding: 4px 8px;
                }}

                QMenuBar::item:selected {{
                    background-color: {selected_color};
                    color: white;
                }}

                QMenu {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border: 1px solid {color_scheme.get("border", "#cccccc")};
                }}

                QMenu::item:selected {{
                    background-color: {selected_color};
                    color: white;
                }}

                QToolBar {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border: none;
                    spacing: 2px;
                }}
                """
                stylesheet_parts.append(menu_style)

            # 5. スクロールバーとその他のコントロール
            if "background" in color_scheme:
                bg_color = color_scheme["background"]
                border_color = color_scheme.get("border", "#cccccc")

                control_style = f"""
                QScrollBar:vertical {{
                    background-color: {bg_color};
                    width: 12px;
                    border: none;
                }}

                QScrollBar::handle:vertical {{
                    background-color: {border_color};
                    border-radius: 6px;
                    min-height: 20px;
                }}

                QScrollBar::handle:vertical:hover {{
                    background-color: {color_scheme.get("hover", border_color)};
                }}

                QComboBox {{
                    background-color: {color_scheme.get("input_background", bg_color)};
                    color: {color_scheme.get("foreground", "#000000")};
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    padding: 4px;
                }}
                """
                stylesheet_parts.append(control_style)

            # 生成されたスタイルシートを結合して適用
            if stylesheet_parts:
                combined_stylesheet = "\n".join(stylesheet_parts)
                self.logger_system.info(f"Generated stylesheet length: {len(combined_stylesheet)} characters")

                # デバッグ用:生成されたスタイルシートをログに出力
                self.logger_system.debug(f"Generated stylesheet:\n{combined_stylesheet[:500]}...")

                success = self._apply_style_sheet(combined_stylesheet)
                if success:
                    self.logger_system.info("Color scheme applied successfully")
                else:
                    self.logger_system.error("Failed to apply generated stylesheet")
                return success
            else:
                self.logger_system.warning("No stylesheet parts generated from color scheme")
                return False

        except Exception as e:
            self.logger_system.error(f"Failed to apply color scheme: {e}")
            import traceback

            self.logger_system.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _get_default_color_scheme(self) -> dict[str, str]:
        """デフォルトのカラースキームを取得"""
        return {
            "background": "#ffffff",
            "foreground": "#000000",
            "primary": "#0078d4",
            "secondary": "#6c757d",
            "accent": "#17a2b8",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "border": "#dee2e6",
            "hover": "#e3f2fd",
            "selected": "#0d7377",
            "disabled": "#6c757d",
            "input_background": "#ffffff",
            "button_text": "#ffffff",
        }

    def _darken_color(self, color: str, factor: float = 0.1) -> str:
        """色を暗くする"""
        try:
            # 簡単な色の暗化処理
            if color.startswith("#") and len(color) == 7:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)

                r = max(0, int(r * (1 - factor)))
                g = max(0, int(g * (1 - factor)))
                b = max(0, int(b * (1 - factor)))

                return f"#{r:02x}{g:02x}{b:02x}"
            else:
                return color
        except Exception:
            return color

    def _apply_accessibility_features(self, theme: ThemeConfiguration):
        """Apply accessibility features (Kiro enhancement)"""
        try:
            features = theme.accessibility_features

            if features.get("high_contrast"):
                self.high_contrast_mode = True
                self.config_manager.set_setting("ui.high_contrast_mode", True)

            if features.get("large_fonts"):
                self.large_fonts_mode = True
                self.config_manager.set_setting("ui.large_fonts_mode", True)

        except Exception as e:
            self.logger_system.warning(f"Failed to apply accessibility features: {e}")

    def _apply_performance_settings(self, theme: ThemeConfiguration):
        """Apply performance settings (Kiro enhancement)"""
        try:
            settings = theme.performance_settings

            self.animation_enabled = settings.get("animation_enabled", True)
            self.transparency_enabled = settings.get("transparency_enabled", True)

            self.config_manager.set_setting("ui.animation_enabled", self.animation_enabled)
            self.config_manager.set_setting("ui.transparency_enabled", self.transparency_enabled)

        except Exception as e:
            self.logger_system.warning(f"Failed to apply performance settings: {e}")

    def get_theme_accessibility_score(self, theme_name: str) -> float:
        """Get accessibility score for the specified theme"""
        if theme_name in self.themes:
            return self.themes[theme_name].accessibility_score
        return 0.0
