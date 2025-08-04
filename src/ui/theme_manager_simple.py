"""
Simple Theme Manager using theme_manager library

Direct integration with theme_manager library without complex fallback logic.
Enhanced with JSON-based theme configuration support.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from ..integration.config_manager import ConfigManager
from ..integration.logging_system import LoggerSystem


class SimpleThemeManager(QObject):
    """Simple theme manager using theme_manager library directly"""

    # Signals
    theme_changed = Signal(str, str)  # old_theme, new_theme
    theme_applied = Signal(str)  # theme_name
    theme_error = Signal(str, str)  # theme_name, error_message

    def __init__(self, config_manager: ConfigManager, logger_system: LoggerSystem):
        super().__init__()

        self.config_manager = config_manager
        self.logger_system = logger_system
        self.logger = logger_system.get_logger(__name__)

        # Initialize theme controller
        self.theme_controller = None
        self.current_theme = "light"  # Default theme
        self.available_themes = {}

        # JSON theme configuration paths
        self.theme_settings_path = Path("config/qt_theme_settings.json")
        self.user_settings_path = Path("config/qt_theme_user_settings.json")

        self._initialize_theme_controller()
        self._load_available_themes()
        self._load_json_themes()

        # Apply initial theme
        initial_theme = self.config_manager.get_setting("ui.theme", "light")

        # Map 'default' to 'light' if default is not available
        if initial_theme == "default" and "default" not in self.available_themes:
            if "light" in self.available_themes:
                initial_theme = "light"
                self.logger.info("Mapped 'default' theme to 'light'")
            else:
                # Use first available theme as fallback
                available_themes = list(self.available_themes.keys())
                if available_themes:
                    initial_theme = available_themes[0]
                    self.logger.info(f"Using fallback theme: {initial_theme}")

        self.apply_theme(initial_theme)

    def _load_json_themes(self):
        """Load themes from JSON configuration files"""
        try:
            if self.theme_settings_path.exists():
                with open(self.theme_settings_path, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)

                json_themes = theme_data.get('available_themes', {})

                # Merge JSON themes with theme_manager themes
                for theme_name, theme_config in json_themes.items():
                    if theme_name not in self.available_themes:
                        # Add JSON theme to available themes
                        self.available_themes[theme_name] = theme_config

                        # Register with theme_controller if available
                        if self.theme_controller and hasattr(self.theme_controller, 'register_theme'):
                            try:
                                self.theme_controller.register_theme(theme_name, theme_config)
                            except Exception as e:
                                self.logger.warning(f"Failed to register JSON theme '{theme_name}' with theme controller: {e}")

                self.logger.info(f"Loaded {len(json_themes)} themes from JSON configuration")

        except Exception as e:
            self.logger.error(f"Failed to load JSON themes: {e}")

    def _save_json_themes(self):
        """Save current themes to JSON configuration"""
        try:
            # Load existing configuration
            theme_data = {}
            if self.theme_settings_path.exists():
                with open(self.theme_settings_path, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)

            # Update available themes
            theme_data['available_themes'] = self.available_themes
            theme_data['version'] = theme_data.get('version', '0.0.1')

            # Save to file
            self.theme_settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.theme_settings_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=4, ensure_ascii=False)

            self.logger.info("Themes saved to JSON configuration")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save JSON themes: {e}")
            return False

    def add_custom_theme(self, theme_name: str, theme_config: Dict) -> bool:
        """
        Add a custom theme to the configuration

        Args:
            theme_name: Name of the theme
            theme_config: Theme configuration dictionary

        Returns:
            True if theme was added successfully
        """
        try:
            if theme_name in self.available_themes:
                self.logger.warning(f"Theme '{theme_name}' already exists")
                return False

            # Validate theme configuration
            required_fields = ['name', 'display_name', 'description', 'primaryColor', 'backgroundColor', 'textColor']
            for field in required_fields:
                if field not in theme_config:
                    self.logger.error(f"Theme configuration missing required field: {field}")
                    return False

            # Add theme to available themes
            self.available_themes[theme_name] = theme_config

            # Register with theme controller if available
            if self.theme_controller and hasattr(self.theme_controller, 'register_theme'):
                try:
                    self.theme_controller.register_theme(theme_name, theme_config)
                except Exception as e:
                    self.logger.warning(f"Failed to register custom theme with theme controller: {e}")

            # Save to JSON configuration
            if self._save_json_themes():
                self.logger.info(f"Custom theme '{theme_name}' added successfully")
                return True
            else:
                # Rollback if save failed
                del self.available_themes[theme_name]
                return False

        except Exception as e:
            self.logger.error(f"Failed to add custom theme '{theme_name}': {e}")
            return False

    def remove_custom_theme(self, theme_name: str) -> bool:
        """
        Remove a custom theme from the configuration

        Args:
            theme_name: Name of the theme to remove

        Returns:
            True if theme was removed successfully
        """
        try:
            if theme_name not in self.available_themes:
                self.logger.warning(f"Theme '{theme_name}' not found")
                return False

            # Don't allow removal of built-in themes from theme_manager
            # Check if theme exists in original theme_manager themes (not JSON themes)
            if self.theme_controller:
                try:
                    builtin_themes = self.theme_controller.get_available_themes()
                    # Only prevent removal if it's a true built-in theme (not added via JSON)
                    if theme_name in builtin_themes:
                        # Check if this theme was loaded from JSON
                        if self.theme_settings_path.exists():
                            with open(self.theme_settings_path, 'r', encoding='utf-8') as f:
                                theme_data = json.load(f)
                                json_themes = theme_data.get('available_themes', {})
                                # If theme is in JSON config, it's removable
                                if theme_name not in json_themes:
                                    self.logger.warning(f"Cannot remove built-in theme '{theme_name}'")
                                    return False
                except:
                    pass

            # Remove theme
            del self.available_themes[theme_name]

            # Unregister from theme controller if available
            if self.theme_controller and hasattr(self.theme_controller, 'unregister_theme'):
                try:
                    self.theme_controller.unregister_theme(theme_name)
                except Exception as e:
                    self.logger.warning(f"Failed to unregister theme from theme controller: {e}")

            # Save to JSON configuration
            if self._save_json_themes():
                self.logger.info(f"Custom theme '{theme_name}' removed successfully")

                # Switch to default theme if current theme was removed
                if self.current_theme == theme_name:
                    fallback_theme = "light" if "light" in self.available_themes else list(self.available_themes.keys())[0]
                    self.apply_theme(fallback_theme)

                return True
            else:
                # Rollback if save failed
                self.available_themes[theme_name] = theme_config
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove custom theme '{theme_name}': {e}")
            return False

    def update_theme(self, theme_name: str, theme_config: Dict) -> bool:
        """
        Update an existing theme configuration

        Args:
            theme_name: Name of the theme to update
            theme_config: Updated theme configuration

        Returns:
            True if theme was updated successfully
        """
        try:
            if theme_name not in self.available_themes:
                self.logger.warning(f"Theme '{theme_name}' not found")
                return False

            # Backup original configuration
            original_config = self.available_themes[theme_name].copy()

            # Update theme configuration
            self.available_themes[theme_name].update(theme_config)

            # Update theme controller if available
            if self.theme_controller and hasattr(self.theme_controller, 'update_theme'):
                try:
                    self.theme_controller.update_theme(theme_name, self.available_themes[theme_name])
                except Exception as e:
                    self.logger.warning(f"Failed to update theme in theme controller: {e}")

            # Save to JSON configuration
            if self._save_json_themes():
                self.logger.info(f"Theme '{theme_name}' updated successfully")

                # Reapply theme if it's currently active
                if self.current_theme == theme_name:
                    self.apply_theme(theme_name)

                return True
            else:
                # Rollback if save failed
                self.available_themes[theme_name] = original_config
                return False

        except Exception as e:
            self.logger.error(f"Failed to update theme '{theme_name}': {e}")
            return False

    def get_theme_config(self, theme_name: str) -> Optional[Dict]:
        """
        Get the full configuration for a specific theme

        Args:
            theme_name: Name of the theme

        Returns:
            Theme configuration dictionary or None if not found
        """
        return self.available_themes.get(theme_name)

    def export_theme(self, theme_name: str, export_path: str) -> bool:
        """
        Export a theme configuration to a file

        Args:
            theme_name: Name of the theme to export
            export_path: Path to save the exported theme

        Returns:
            True if export was successful
        """
        try:
            if theme_name not in self.available_themes:
                self.logger.error(f"Theme '{theme_name}' not found")
                return False

            theme_config = self.available_themes[theme_name]
            export_data = {
                'theme_name': theme_name,
                'theme_config': theme_config,
                'exported_at': str(Path().cwd()),
                'version': '1.0.0'
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)

            self.logger.info(f"Theme '{theme_name}' exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export theme '{theme_name}': {e}")
            return False

    def import_theme(self, import_path: str) -> bool:
        """
        Import a theme configuration from a file

        Args:
            import_path: Path to the theme file to import

        Returns:
            True if import was successful
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            theme_name = import_data.get('theme_name')
            theme_config = import_data.get('theme_config')

            if not theme_name or not theme_config:
                self.logger.error("Invalid theme file format")
                return False

            return self.add_custom_theme(theme_name, theme_config)

        except Exception as e:
            self.logger.error(f"Failed to import theme from {import_path}: {e}")
            return False

    def reload_themes(self):
        """Reload themes from all sources"""
        try:
            # Clear current themes
            self.available_themes.clear()

            # Reload from theme_manager
            self._load_available_themes()

            # Reload from JSON
            self._load_json_themes()

            self.logger.info("Themes reloaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to reload themes: {e}")

    def _initialize_theme_controller(self):
        """Initialize theme controller from theme_manager library"""
        try:
            from theme_manager import ThemeController
            self.theme_controller = ThemeController()
            self.logger.info("Theme controller initialized successfully")
        except ImportError as e:
            self.logger.error(f"Failed to import theme_manager: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize theme controller: {e}")
            raise

    def _load_available_themes(self):
        """Load available themes from theme controller"""
        try:
            if self.theme_controller:
                self.available_themes = self.theme_controller.get_available_themes()
                self.logger.info(f"Loaded {len(self.available_themes)} themes: {list(self.available_themes.keys())}")
            else:
                self.logger.warning("Theme controller not available")
        except Exception as e:
            self.logger.error(f"Failed to load available themes: {e}")

    def get_available_themes(self) -> List[str]:
        """Get list of available theme names"""
        return list(self.available_themes.keys())

    def get_current_theme(self) -> str:
        """Get current theme name"""
        if self.theme_controller:
            try:
                return self.theme_controller.get_current_theme_name()
            except:
                pass
        return self.current_theme

    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme"""
        try:
            if not self.theme_controller:
                self.logger.error("Theme controller not available")
                return False

            if theme_name not in self.available_themes:
                self.logger.error(f"Theme '{theme_name}' not available")
                self.theme_error.emit(theme_name, f"Theme '{theme_name}' not found")
                return False

            old_theme = self.current_theme

            # Set theme using theme controller
            self.theme_controller.set_theme(theme_name)

            # Apply to application
            app = QApplication.instance()
            if app:
                self.theme_controller.apply_theme_to_application(app)

            # Update current theme
            self.current_theme = theme_name

            # Save to config
            self.config_manager.set_setting("ui.theme", theme_name)

            # Emit signals
            if old_theme != theme_name:
                self.theme_changed.emit(old_theme, theme_name)
            self.theme_applied.emit(theme_name)

            self.logger.info(f"Theme applied successfully: {theme_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply theme '{theme_name}': {e}")
            self.theme_error.emit(theme_name, str(e))
            return False

    def apply_theme_to_widget(self, widget):
        """Apply current theme to a specific widget"""
        try:
            if self.theme_controller:
                self.theme_controller.apply_theme_to_widget(widget)
                return True
        except Exception as e:
            self.logger.error(f"Failed to apply theme to widget: {e}")
        return False

    def get_theme_info(self, theme_name: str) -> Optional[Dict]:
        """Get theme information"""
        return self.available_themes.get(theme_name)

    def cycle_theme(self):
        """Cycle to next available theme"""
        themes = self.get_available_themes()
        if len(themes) <= 1:
            return

        current_index = 0
        try:
            current_index = themes.index(self.current_theme)
        except ValueError:
            pass

        next_index = (current_index + 1) % len(themes)
        next_theme = themes[next_index]

        self.apply_theme(next_theme)
