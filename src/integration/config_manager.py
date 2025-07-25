"""
Unified Configuration Management System for AI Integration

Manages configuration across all AI implementations:
- GitHub Copilot (CS4Coding): Core functionality settings
- Cursor (CursorBLD): UI/UX preferences and theme settings
- Kiro: Integration settings and performance tuning

Author: Kiro AI Integration System
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import threading
from copy import deepcopy

from .interfaces import IConfigManager
from .models import AIComponent, ThemeConfiguration
from .error_handling import IntegratedErrorHandler, ErrorCategory
from .logging_system import LoggerSystem


class ConfigManager(IConfigManager):
    """
    Unified configuration manager that merges settings from all AI implementations

    Features:
    - Hierarchical configuration (default -> AI-specific -> user overrides)
    - Hot reloading and change notifications
    - Backup and migration support
    - Validation and schema enforcement
    """

    def __init__(self,
                 config_dir: Path = None,
                 logger_system: LoggerSystem = None,
                 error_handler: IntegratedErrorHandler = None):
        """
        Initialize the configuration manager

        Args:
            config_dir: Directory for configuration files
            logger_system: Logging system instance
   error_handler: Error handler instance
        """

        self.config_dir = config_dir or Path("config")
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = error_handler or IntegratedErrorHandler(self.logger_system)

        # Configuration storage
        self.config_data: Dict[str, Any] = {}
        self.default_config: Dict[str, Any] = {}
        self.ai_configs: Dict[AIComponent, Dict[str, Any]] = {}

        # File paths
        self.main_config_file = self.config_dir / "app_config.json"
        self.user_config_file = self.config_dir / "user_config.json"
        self.ai_config_files = {
            AIComponent.COPILOT: self.config_dir / "copilot_config.json",
            AIComponent.CURSOR: self.config_dir / "cursor_config.json",
            AIComponent.KIRO: self.config_dir / "kiro_config.json"
        }

        # Thread safety
        self._lock = threading.RLock()

        # Change tracking
        self.change_listeners: List[callable] = []
        self.last_modified: Dict[str, datetime] = {}

        # Validation schemas
        self.validation_schemas: Dict[str, Dict[str, Any]] = {}

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize the configuration system"""

        try:
            # Create config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Load default configuration
            self._load_default_config()

            # Load AI-specific configurations
            self._load_ai_configs()

            # Load main configuration
            self._load_main_config()

            # Load user overrides
            self._load_user_config()

            # Merge all configurations
            self._merge_configurations()

            # Setup validation schemas
            self._setup_validation_schemas()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "config_initialization",
                f"Configuration system initialized with {len(self.config_data)} settings"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "config_initialization"},
                AIComponent.KIRO
            )

    def _load_default_config(self):
        """Load default configuration values"""

        self.default_config = {
            # Application settings
            "app": {
                "name": "PhotoGeoView",
                "version": "1.0.0",
                "debug_mode": False,
                "auto_save": True,
                "backup_enabled": True,
                "telemetry_enabled": False
            },

            # UI settings (CursorBLD defaults)
            "ui": {
                "theme": "default",
                "thumbnail_size": 150,
                "window_geometry": None,
                "splitter_states": {},
                "show_toolbar": True,
                "show_statusbar": True,
                "animation_enabled": True
            },

            # Core functionality settings (CS4Coding defaults)
            "core": {
                "image_formats": [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"],
                "exif_parsing_enabled": True,
                "map_provider": "folium",
                "map_zoom_default": 10,
                "thumbnail_quality": 85,
                "cache_enabled": True,
                "cache_size_mb": 100
            },

            # Performance settings (Kiro defaults)
            "performance": {
                "mode": "balanced",  # performance, balanced, quality
                "max_memory_mb": 512,
                "thread_pool_size": 4,
                "async_loading": True,
                "preload_thumbnails": True,
                "performance_monitoring": True
            },

            # AI integration settings
            "ai_integration": {
                "copilot_enabled": True,
                "cursor_enabled": True,
                "kiro_enabled": True,
                "error_recovery": True,
                "cross_component_caching": True,
                "performance_sharing": True
            },

            # Logging settings
            "logging": {
                "level": "INFO",
                "file_logging": True,
                "console_logging": True,
                "performance_logging": True,
                "ai_operation_logging": True,
                "max_log_size_mb": 10,
                "log_retention_days": 30
            }
        }

    def _load_ai_configs(self):
        """Load AI-specific configuration files"""

        for ai_component, config_file in self.ai_config_files.items():
            try:
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        ai_config = json.load(f)
                        self.ai_configs[ai_component] = ai_config

                        self.logger_system.log_ai_operation(
                            ai_component,
                            "config_loading",
                            f"Loaded {len(ai_config)} AI-specific settings"
                        )
                else:
                    # Create default AI config
                    self.ai_configs[ai_component] = self._get_default_ai_config(ai_component)
                    self._save_ai_config(ai_component)

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "ai_config_loading", "ai_component": ai_component.value},
                    ai_component
                )
                # Use default config on error
                self.ai_configs[ai_component] = self._get_default_ai_config(ai_component)

    def _get_default_ai_config(self, ai_component: AIComponent) -> Dict[str, Any]:
        """Get default configuration for specific AI component"""

        if ai_component == AIComponent.COPILOT:
            return {
                "image_processing": {
                    "high_quality_exif": True,
                    "detailed_metadata": True,
                    "gps_precision": "high",
                    "error_recovery": "robust"
                },
                "map_integration": {
                    "folium_version": "latest",
                    "marker_clustering": True,
                    "offline_tiles": False,
                    "custom_markers": True
                }
            }

        elif ai_component == AIComponent.CURSOR:
            return {
                "theme_system": {
                    "qt_theme_manager": True,
                    "theme_count": 16,
                    "custom_themes": True,
                    "theme_validation": True
                },
                "ui_optimization": {
                    "fast_thumbnails": True,
                    "smooth_scrolling": True,
                    "responsive_layout": True,
                    "accessibility_features": True
                }
            }

        elif ai_component == AIComponent.KIRO:
            return {
                "integration": {
                    "error_correlation": True,
                    "performance_monitoring": True,
                    "ai_coordination": True,
                    "quality_assurance": True
                },
                "optimization": {
                    "memory_management": True,
                    "cache_optimization": True,
                    "async_processing": True,
                    "resource_pooling": True
                }
            }

        return {}

    def _load_main_config(self):
        """Load main application configuration"""

        try:
            if self.main_config_file.exists():
                with open(self.main_config_file, 'r', encoding='utf-8') as f:
                    main_config = json.load(f)

                    # Update last modified time
                    self.last_modified["main"] = datetime.fromtimestamp(
                        self.main_config_file.stat().st_mtime
                    )

                    # Merge with defaults
                    self._deep_merge(self.config_data, main_config)

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "config_loading",
                        f"Loaded main configuration with {len(main_config)} sections"
                    )
            else:
                # Create default main config
                self._save_main_config()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "main_config_loading"},
                AIComponent.KIRO
            )

    def _load_user_config(self):
        """Load user-specific configuration overrides"""

        try:
            if self.user_config_file.exists():
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)

                    # Update last modified time
                    self.last_modified["user"] = datetime.fromtimestamp(
                        self.user_config_file.stat().st_mtime
                    )

                    # Apply user overrides
                    self._deep_merge(self.config_data, user_config)

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "config_loading",
                        f"Applied {len(user_config)} user configuration overrides"
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "user_config_loading"},
                AIComponent.KIRO
            )

    def _merge_configurations(self):
        """Merge all configuration sources in priority order"""

        with self._lock:
            # Start with defaults
            self.config_data = deepcopy(self.default_config)

            # Apply AI-specific configurations
            for ai_component, ai_config in self.ai_configs.items():
                ai_section = f"ai_{ai_component.value}"
                self.config_data[ai_section] = ai_config

            # Main config and user config are already merged in their load methods

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source dictionary into target dictionary"""

        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _setup_validation_schemas(self):
        """Setup validation schemas for configuration sections"""

        self.validation_schemas = {
            "app": {
                "name": str,
                "version": str,
                "debug_mode": bool,
                "auto_save": bool,
                "backup_enabled": bool,
                "telemetry_enabled": bool
            },
            "ui": {
                "theme": str,
                "thumbnail_size": int,
                "show_toolbar": bool,
                "show_statusbar": bool,
                "animation_enabled": bool
            },
            "core": {
                "image_formats": list,
                "exif_parsing_enabled": bool,
                "map_provider": str,
                "map_zoom_default": int,
                "thumbnail_quality": int,
                "cache_enabled": bool,
                "cache_size_mb": int
            },
            "performance": {
                "mode": str,
                "max_memory_mb": int,
                "thread_pool_size": int,
                "async_loading": bool,
                "preload_thumbnails": bool,
                "performance_monitoring": bool
            }
        }

    # IConfigManager implementation

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration setting value

        Args:
            key: Setting key (supports dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Setting value or default
        """

        with self._lock:
            try:
                # Split key by dots for nested access
                keys = key.split('.')
                value = self.config_data

                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default

                return value

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "get_setting", "key": key},
                    AIComponent.KIRO
                )
                return default

    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a configuration setting value

        Args:
            key: Setting key (supports dot notation for nested keys)
            value: Value to set

        Returns:
            True if setting was saved successfully, False otherwise
        """

        with self._lock:
            try:
                # Validate the setting
                if not self._validate_setting(key, value):
                    return False

                # Split key by dots for nested access
                keys = key.split('.')
                target = self.config_data

                # Navigate to the parent of the target key
                for k in keys[:-1]:
                    if k not in target:
                        target[k] = {}
                    target = target[k]

                # Set the value
                old_value = target.get(keys[-1])
                target[keys[-1]] = value

                # Notify change listeners
                self._notify_change_listeners(key, old_value, value)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "config_change",
                    f"Setting changed: {key} = {value}"
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "set_setting", "key": key, "value": str(value)},
                    AIComponent.KIRO
                )
                return False

    def get_ai_config(self, ai_name: str) -> Dict[str, Any]:
        """
        Get configuration section for specific AI implementation

        Args:
            ai_name: Name of AI implementation (copilot, cursor, kiro)

        Returns:
            AI-specific configuration dictionary
        """

        try:
            ai_component = AIComponent(ai_name.lower())
            return self.ai_configs.get(ai_component, {})
        except ValueError:
            return {}

    def save_config(self) -> bool:
        """
        Save current configuration to persistent storage

        Returns:
            True if saved successfully, False otherwise
        """

        try:
            with self._lock:
                # Save main configuration
                self._save_main_config()

                # Save AI-specific configurations
                for ai_component in self.ai_configs:
                    self._save_ai_config(ai_component)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "config_save",
                    "All configuration files saved successfully"
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "save_config"},
                AIComponent.KIRO
            )
            return False

    def load_config(self) -> bool:
        """
        Load configuration from persistent storage

        Returns:
            True if loaded successfully, False otherwise
        """

        try:
            with self._lock:
                # Reload all configurations
                self._load_ai_configs()
                self._load_main_config()
                self._load_user_config()
                self._merge_configurations()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "config_reload",
                    "Configuration reloaded from storage"
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "load_config"},
                AIComponent.KIRO
            )
            return False

    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values

        Returns:
            True if reset successfully, False otherwise
        """

        try:
            with self._lock:
                # Backup current config
                backup_file = self.config_dir / f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, indent=2, default=str)

                # Reset to defaults
                self.config_data = deepcopy(self.default_config)

                # Reset AI configs
                for ai_component in self.ai_configs:
                    self.ai_configs[ai_component] = self._get_default_ai_config(ai_component)

                # Save the reset configuration
                self.save_config()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "config_reset",
                    f"Configuration reset to defaults (backup saved: {backup_file})"
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "reset_to_defaults"},
                AIComponent.KIRO
            )
            return False

    # Helper methods

    def _save_main_config(self):
        """Save main configuration file"""

        # Extract main config (exclude AI-specific sections)
        main_config = {
            key: value for key, value in self.config_data.items()
            if not key.startswith('ai_')
        }

        with open(self.main_config_file, 'w', encoding='utf-8') as f:
            json.dump(main_config, f, indent=2, default=str)

        self.last_modified["main"] = datetime.now()

    def _save_ai_config(self, ai_component: AIComponent):
        """Save AI-specific configuration file"""

        config_file = self.ai_config_files[ai_component]
        ai_config = self.ai_configs[ai_component]

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(ai_config, f, indent=2, default=str)

        self.last_modified[f"ai_{ai_component.value}"] = datetime.now()

    def _validate_setting(self, key: str, value: Any) -> bool:
        """Validate a setting value against its schema"""

        try:
            # Get the section from the key
            section = key.split('.')[0]

            if section in self.validation_schemas:
                schema = self.validation_schemas[section]
                setting_name = key.split('.')[-1]

                if setting_name in schema:
                    expected_type = schema[setting_name]

                    if expected_type == list:
                        return isinstance(value, list)
                    elif expected_type == dict:
                        return isinstance(value, dict)
                    else:
                        return isinstance(value, expected_type)

            # If no schema defined, allow the setting
            return True

        except Exception:
            return False

    def _notify_change_listeners(self, key: str, old_value: Any, new_value: Any):
        """Notify registered change listeners"""

        for listener in self.change_listeners:
            try:
                listener(key, old_value, new_value)
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "change_notification", "key": key},
                    AIComponent.KIRO
                )

    # Advanced features

    def add_change_listener(self, listener: callable):
        """Add a configuration change listener"""

        if listener not in self.change_listeners:
            self.change_listeners.append(listener)

    def remove_change_listener(self, listener: callable):
        """Remove a configuration change listener"""

        if listener in self.change_listeners:
            self.change_listeners.remove(listener)

    def export_config(self, file_path: Path, include_ai_configs: bool = True) -> bool:
        """
        Export configuration to a file

        Args:
            file_path: Path to export file
            include_ai_configs: Whether to include AI-specific configurations

        Returns:
            True if exported successfully, False otherwise
        """

        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "app_version": self.get_setting("app.version", "unknown"),
                "main_config": self.config_data
            }

            if include_ai_configs:
                export_data["ai_configs"] = {
                    ai.value: config for ai, config in self.ai_configs.items()
                }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "config_export",
                f"Configuration exported to {file_path}"
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "export_config", "file_path": str(file_path)},
                AIComponent.KIRO
            )
            return False

    def import_config(self, file_path: Path, merge: bool = True) -> bool:
        """
        Import configuration from a file

        Args:
            file_path: Path to import file
            merge: Whether to merge with existing config or replace

        Returns:
            True if imported successfully, False otherwise
        """

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if "main_config" in import_data:
                if merge:
                    self._deep_merge(self.config_data, import_data["main_config"])
                else:
                    self.config_data = import_data["main_config"]

            if "ai_configs" in import_data:
                for ai_name, ai_config in import_data["ai_configs"].items():
                    try:
                        ai_component = AIComponent(ai_name)
                        if merge:
                            self._deep_merge(self.ai_configs[ai_component], ai_config)
                        else:
                            self.ai_configs[ai_component] = ai_config
                    except ValueError:
                        continue

            # Save the imported configuration
            self.save_config()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "config_import",
                f"Configuration imported from {file_path} (merge: {merge})"
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "import_config", "file_path": str(file_path)},
                AIComponent.KIRO
            )
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration"""

        return {
            "total_settings": self._count_settings(self.config_data),
            "ai_configs": {
                ai.value: self._count_settings(config)
                for ai, config in self.ai_configs.items()
            },
            "last_modified": dict(self.last_modified),
            "config_files": {
                "main": self.main_config_file.exists(),
                "user": self.user_config_file.exists(),
                "ai_configs": {
                    ai.value: file.exists()
                    for ai, file in self.ai_config_files.items()
                }
            }
        }

    def _count_settings(self, config: Dict[str, Any]) -> int:
        """Recursively count settings in a configuration dictionary"""

        count = 0
        for value in config.values():
            if isinstance(value, dict):
                count += self._count_settings(value)
            else:
                count += 1
        return count
