"""
Unified Configuration Management System for AI Integration

Manages configuration across all AI implementations:
- GitHub Copilot (CS4Coding): Core functionality settings
- Cursor (CursorBLD): UI/UX preferences and theme settings
- Kiro: Integration settings and performance tuning

Author: Kiro AI Integration System
"""

import json
import threading
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .config_migration import ConfigMigrationManager
from .error_handling import ErrorCategory, IntegratedErrorHandler
from .interfaces import IConfigManager
from .logging_system import LoggerSystem
from .models import AIComponent, ApplicationState


class ConfigManager(IConfigManager):
    """
    Unified configuration manager that merges settings from all AI implementations

    Features:
    - Hierarchical configuration (default -> AI-specific -> user overrides)
    - Hot reloading and change notifications
    - Backup and migration support
    - Validation and schema enforcement
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        logger_system: LoggerSystem = None,
        error_handler: IntegratedErrorHandler = None,
    ):
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
        self.config_data: dict[str, Any] = {}
        self.default_config: dict[str, Any] = {}
        self.ai_configs: dict[AIComponent, dict[str, Any]] = {}

        # Application state management
        self.application_state: ApplicationState = ApplicationState()
        self.state_file = self.config_dir / "application_state.json"

        # File paths
        self.main_config_file = self.config_dir / "app_config.json"
        self.user_config_file = self.config_dir / "user_config.json"
        self.ai_config_files = {
            AIComponent.COPILOT: self.config_dir / "copilot_config.json",
            AIComponent.CURSOR: self.config_dir / "cursor_config.json",
            AIComponent.KIRO: self.config_dir / "kiro_config.json",
        }

        # Thread safety
        self._lock = threading.RLock()

        # Change tracking
        self.change_listeners: list[callable] = []
        self.last_modified: dict[str, datetime] = {}

        # Validation schemas
        self.validation_schemas: dict[str, dict[str, Any]] = {}

        # Migration manager
        self.migration_manager = ConfigMigrationManager(config_dir=self.config_dir, logger_system=self.logger_system)

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

            # Load application state
            self._load_application_state()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "config_initialization",
                f"Configuration system initialized with {len(self.config_data)} settings",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "config_initialization"},
                AIComponent.KIRO,
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
                "telemetry_enabled": False,
            },
            # UI settings (CursorBLD defaults)
            "ui": {
                "theme": "default",
                "thumbnail_size": 150,
                "window_geometry": None,
                "splitter_states": {},
                "show_toolbar": True,
                "show_statusbar": True,
                "animation_enabled": True,
            },
            # Core functionality settings (CS4Coding defaults)
            "core": {
                "image_formats": [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"],
                "exif_parsing_enabled": True,
                "map_provider": "folium",
                "map_zoom_default": 10,
                "thumbnail_quality": 85,
                "cache_enabled": True,
                "cache_size_mb": 100,
            },
            # Performance settings (Kiro defaults)
            "performance": {
                "mode": "balanced",  # performance, balanced, quality
                "max_memory_mb": 512,
                "thread_pool_size": 4,
                "async_loading": True,
                "preload_thumbnails": True,
                "performance_monitoring": True,
            },
            # AI integration settings
            "ai_integration": {
                "copilot_enabled": True,
                "cursor_enabled": True,
                "kiro_enabled": True,
                "error_recovery": True,
                "cross_component_caching": True,
                "performance_sharing": True,
            },
            # Logging settings
            "logging": {
                "level": "INFO",
                "file_logging": True,
                "console_logging": True,
                "performance_logging": True,
                "ai_operation_logging": True,
                "max_log_size_mb": 10,
                "log_retention_days": 30,
            },
        }

    def _load_ai_configs(self):
        """Load AI-specific configuration files"""

        for ai_component, config_file in self.ai_config_files.items():
            try:
                if config_file.exists():
                    with open(config_file, encoding="utf-8") as f:
                        ai_config = json.load(f)
                        self.ai_configs[ai_component] = ai_config

                        self.logger_system.log_ai_operation(
                            ai_component,
                            "config_loading",
                            f"Loaded {len(ai_config)} AI-specific settings",
                        )
                else:
                    # Create default AI config
                    self.ai_configs[ai_component] = self._get_default_ai_config(ai_component)
                    self._save_ai_config(ai_component)

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.CONFIGURATION_ERROR,
                    {
                        "operation": "ai_config_loading",
                        "ai_component": ai_component.value,
                    },
                    ai_component,
                )
                # Use default config on error
                self.ai_configs[ai_component] = self._get_default_ai_config(ai_component)

    def _get_default_ai_config(self, ai_component: AIComponent) -> dict[str, Any]:
        """Get default configuration for specific AI component"""

        if ai_component == AIComponent.COPILOT:
            return {
                "image_processing": {
                    "high_quality_exif": True,
                    "detailed_metadata": True,
                    "gps_precision": "high",
                    "error_recovery": "robust",
                },
                "map_integration": {
                    "folium_version": "latest",
                    "marker_clustering": True,
                    "offline_tiles": False,
                    "custom_markers": True,
                },
            }

        elif ai_component == AIComponent.CURSOR:
            return {
                "theme_system": {
                    "qt_theme_manager": True,
                    "theme_count": 16,
                    "custom_themes": True,
                    "theme_validation": True,
                },
                "ui_optimization": {
                    "fast_thumbnails": True,
                    "smooth_scrolling": True,
                    "responsive_layout": True,
                    "accessibility_features": True,
                },
            }

        elif ai_component == AIComponent.KIRO:
            return {
                "integration": {
                    "error_correlation": True,
                    "performance_monitoring": True,
                    "ai_coordination": True,
                    "quality_assurance": True,
                },
                "optimization": {
                    "memory_management": True,
                    "cache_optimization": True,
                    "async_processing": True,
                    "resource_pooling": True,
                },
            }

        return {}

    def _load_main_config(self):
        """Load main application configuration"""

        try:
            if self.main_config_file.exists():
                with open(self.main_config_file, encoding="utf-8") as f:
                    main_config = json.load(f)

                    # Update last modified time
                    self.last_modified["main"] = datetime.fromtimestamp(self.main_config_file.stat().st_mtime)

                    # Merge with defaults
                    self._deep_merge(self.config_data, main_config)

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "config_loading",
                        f"Loaded main configuration with {len(main_config)} sections",
                    )
            else:
                # Create default main config
                self._save_main_config()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "main_config_loading"},
                AIComponent.KIRO,
            )

    def _load_user_config(self):
        """Load user-specific configuration overrides"""

        try:
            if self.user_config_file.exists():
                with open(self.user_config_file, encoding="utf-8") as f:
                    user_config = json.load(f)

                    # Update last modified time
                    self.last_modified["user"] = datetime.fromtimestamp(self.user_config_file.stat().st_mtime)

                    # Apply user overrides
                    self._deep_merge(self.config_data, user_config)

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "config_loading",
                        f"Applied {len(user_config)} user configuration overrides",
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "user_config_loading"},
                AIComponent.KIRO,
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

    def _deep_merge(self, target: dict[str, Any], source: dict[str, Any]):
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
                "telemetry_enabled": bool,
            },
            "ui": {
                "theme": str,
                "thumbnail_size": int,
                "show_toolbar": bool,
                "show_statusbar": bool,
                "animation_enabled": bool,
            },
            "core": {
                "image_formats": list,
                "exif_parsing_enabled": bool,
                "map_provider": str,
                "map_zoom_default": int,
                "thumbnail_quality": int,
                "cache_enabled": bool,
                "cache_size_mb": int,
            },
            "performance": {
                "mode": str,
                "max_memory_mb": int,
                "thread_pool_size": int,
                "async_loading": bool,
                "preload_thumbnails": bool,
                "performance_monitoring": bool,
            },
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
                keys = key.split(".")
                value = self.config_data

                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default

                return value

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "get_setting", "key": key},
                    AIComponent.KIRO,
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
                keys = key.split(".")
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
                    f"Setting changed: {key} = {value}",
                )

                return True

            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "set_setting", "key": key, "value": str(value)},
                    AIComponent.KIRO,
                )
                return False

    def get_ai_config(self, ai_name: str) -> dict[str, Any]:
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

    def set_ai_config(self, ai_name: str, config: dict[str, Any]) -> bool:
        """
        Set configuration for specific AI implementation

        Args:
            ai_name: Name of AI implementation (copilot, cursor, kiro)
            config: Configuration dictionary to set

        Returns:
            True if configuration was set successfully
        """
        try:
            ai_component = AIComponent(ai_name.lower())

            with self._lock:
                old_config = self.ai_configs.get(ai_component, {})
                self.ai_configs[ai_component] = config

                # Update merged configuration
                self._merge_configurations()

                # Save AI-specific configuration
                self._save_ai_config(ai_component)

                # Notify change listeners
                self._notify_change_listeners(f"ai_{ai_name}", old_config, config)

                self.logger_system.log_ai_operation(
                    ai_component,
                    "config_update",
                    f"AI configuration updated with {len(config)} settings",
                )

                return True

        except ValueError:
            self.logger_system.error(f"Invalid AI component name: {ai_name}")
            return False
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "set_ai_config", "ai_name": ai_name},
                AIComponent.KIRO,
            )
            return False

    def update_ai_config(self, ai_name: str, updates: dict[str, Any]) -> bool:
        """
        Update specific settings in AI configuration

        Args:
            ai_name: Name of AI implementation (copilot, cursor, kiro)
            updates: Dictionary of settings to update

        Returns:
            True if configuration was updated successfully
        """
        try:
            ai_component = AIComponent(ai_name.lower())

            with self._lock:
                if ai_component not in self.ai_configs:
                    self.ai_configs[ai_component] = self._get_default_ai_config(ai_component)

                # Deep merge updates into existing config
                self._deep_merge(self.ai_configs[ai_component], updates)

                # Update merged configuration
                self._merge_configurations()

                # Save AI-specific configuration
                self._save_ai_config(ai_component)

                # Notify change listeners
                for key, value in updates.items():
                    self._notify_change_listeners(f"ai_{ai_name}.{key}", None, value)

                self.logger_system.log_ai_operation(
                    ai_component,
                    "config_update",
                    f"AI configuration updated: {list(updates.keys())}",
                )

                return True

        except ValueError:
            self.logger_system.error(f"Invalid AI component name: {ai_name}")
            return False
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {
                    "operation": "update_ai_config",
                    "ai_name": ai_name,
                    "updates": str(updates),
                },
                AIComponent.KIRO,
            )
            return False

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
                    "All configuration files saved successfully",
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "save_config"},
                AIComponent.KIRO,
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
                    "Configuration reloaded from storage",
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "load_config"},
                AIComponent.KIRO,
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
                with open(backup_file, "w", encoding="utf-8") as f:
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
                    f"Configuration reset to defaults (backup saved: {backup_file})",
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "reset_to_defaults"},
                AIComponent.KIRO,
            )
            return False

    # Helper methods

    def _save_main_config(self):
        """Save main configuration file"""

        # Extract main config (exclude AI-specific sections)
        main_config = {key: value for key, value in self.config_data.items() if not key.startswith("ai_")}

        with open(self.main_config_file, "w", encoding="utf-8") as f:
            json.dump(main_config, f, indent=2, default=str)

        self.last_modified["main"] = datetime.now()

    def _save_ai_config(self, ai_component: AIComponent):
        """Save AI-specific configuration file"""

        config_file = self.ai_config_files[ai_component]
        ai_config = self.ai_configs[ai_component]

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(ai_config, f, indent=2, default=str)

        self.last_modified[f"ai_{ai_component.value}"] = datetime.now()

    def _validate_setting(self, key: str, value: Any) -> bool:
        """Validate a setting value against its schema"""

        try:
            # Get the section from the key
            section = key.split(".")[0]

            if section in self.validation_schemas:
                schema = self.validation_schemas[section]
                setting_name = key.split(".")[-1]

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
                    e,
                    ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "change_notification", "key": key},
                    AIComponent.KIRO,
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
                "main_config": self.config_data,
            }

            if include_ai_configs:
                export_data["ai_configs"] = {ai.value: config for ai, config in self.ai_configs.items()}

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "config_export",
                f"Configuration exported to {file_path}",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "export_config", "file_path": str(file_path)},
                AIComponent.KIRO,
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
            with open(file_path, encoding="utf-8") as f:
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
                f"Configuration imported from {file_path} (merge: {merge})",
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "import_config", "file_path": str(file_path)},
                AIComponent.KIRO,
            )
            return False

    def get_config_summary(self) -> dict[str, Any]:
        """Get a summary of the current configuration"""

        return {
            "total_settings": self._count_settings(self.config_data),
            "ai_configs": {ai.value: self._count_settings(config) for ai, config in self.ai_configs.items()},
            "last_modified": dict(self.last_modified),
            "config_files": {
                "main": self.main_config_file.exists(),
                "user": self.user_config_file.exists(),
                "ai_configs": {ai.value: file.exists() for ai, file in self.ai_config_files.items()},
            },
        }

    def _count_settings(self, config: dict[str, Any]) -> int:
        """Recursively count settings in a configuration dictionary"""

        count = 0
        for value in config.values():
            if isinstance(value, dict):
                count += self._count_settings(value)
            else:
                count += 1
        return count

    # Configuration migration methods

    def migrate_existing_configurations(self) -> dict[str, Any]:
        """
        Migrate existing configuration files to unified system

        Returns:
            Migration summary dictionary
        """

        try:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO, "config_migration", "Starting configuration migration"
            )

            # Run migration
            migration_result = self.migration_manager.migrate_all_configurations()

            # Reload configuration after migration
            if migration_result["status"] in ["success", "partial"]:
                self.load_config()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "config_migration",
                f"Configuration migration completed: {migration_result['status']}",
            )

            return migration_result

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "migrate_existing_configurations"},
                AIComponent.KIRO,
            )
            return {"status": "failed", "error": str(e)}

    def rollback_migration(self, migration_timestamp: str | None = None) -> bool:
        """
        Rollback configuration migration

        Args:
            migration_timestamp: Specific migration timestamp to rollback

        Returns:
            True if rollback was successful
        """

        try:
            success = self.migration_manager.rollback_migration(migration_timestamp)

            if success:
                # Reload configuration after rollback
                self.load_config()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "config_rollback",
                    "Configuration migration rollback completed",
                )

            return success

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "rollback_migration"},
                AIComponent.KIRO,
            )
            return False

    def validate_configuration(self) -> dict[str, Any]:
        """
        Validate current configuration

        Returns:
            Validation results dictionary
        """

        try:
            return self.migration_manager.validate_migrated_configuration()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "validate_configuration"},
                AIComponent.KIRO,
            )
            return {"status": "error", "error": str(e)}

    def get_migration_status(self) -> dict[str, Any]:
        """Get current migration status"""

        try:
            return self.migration_manager.get_migration_status()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "get_migration_status"},
                AIComponent.KIRO,
            )
            return {"status": "error", "error": str(e)}

    def has_legacy_configurations(self) -> bool:
        """
        Check if legacy configuration files exist that need migration

        Returns:
            True if legacy configurations are found
        """

        try:
            legacy_files = [
                "qt_theme_settings.json",
                "qt_theme_user_settings.json",
                "cursor_ui_config.json",
                "copilot_config.json",
                "image_processing_config.json",
                "map_config.json",
                "kiro_config.json",
                "integration_config.json",
                "performance_config.json",
                "photogeoview_config.json",
                "app_settings.json",
                "user_preferences.json",
            ]

            return any((self.config_dir / filename).exists() for filename in legacy_files)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "has_legacy_configurations"},
                AIComponent.KIRO,
            )
            return False

    # ApplicationState management methods

    def get_application_state(self) -> ApplicationState:
        """
        Get current application state

        Returns:
            Current ApplicationState instance
        """
        return self.application_state

    def update_application_state(self, **kwargs) -> bool:
        """
        Update application state with provided values

        Args:
            **kwargs: State values to update

        Returns:
            True if state was updated successfully
        """
        try:
            with self._lock:
                for key, value in kwargs.items():
                    if hasattr(self.application_state, key):
                        setattr(self.application_state, key, value)
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "state_update",
                            f"Application state updated: {key} = {value}",
                        )

                # Update activity timestamp
                self.application_state.update_activity()

                # Save state to file
                self._save_application_state()

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "update_application_state", "kwargs": str(kwargs)},
                AIComponent.KIRO,
            )
            return False

    def save_application_state(self) -> bool:
        """
        Save current application state to persistent storage

        Returns:
            True if saved successfully
        """
        try:
            return self._save_application_state()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "save_application_state"},
                AIComponent.KIRO,
            )
            return False

    def load_application_state(self) -> bool:
        """
        Load application state from persistent storage

        Returns:
            True if loaded successfully
        """
        try:
            return self._load_application_state()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "load_application_state"},
                AIComponent.KIRO,
            )
            return False

    def reset_application_state(self) -> bool:
        """
        Reset application state to defaults

        Returns:
            True if reset successfully
        """
        try:
            with self._lock:
                # Backup current state
                backup_file = self.config_dir / f"state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self._save_application_state_to_file(backup_file)

                # Reset to default state
                self.application_state = ApplicationState()

                # Save reset state
                self._save_application_state()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "state_reset",
                    f"Application state reset to defaults (backup saved: {backup_file})",
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "reset_application_state"},
                AIComponent.KIRO,
            )
            return False

    def _save_application_state(self) -> bool:
        """Save application state to default file"""
        return self._save_application_state_to_file(self.state_file)

    def _save_application_state_to_file(self, file_path: Path) -> bool:
        """Save application state to specified file"""
        try:
            # Convert ApplicationState to dictionary
            state_dict = {
                "current_folder": (
                    str(self.application_state.current_folder) if self.application_state.current_folder else None
                ),
                "selected_image": (
                    str(self.application_state.selected_image) if self.application_state.selected_image else None
                ),
                "loaded_images": [str(path) for path in self.application_state.loaded_images],
                "current_theme": self.application_state.current_theme,
                "thumbnail_size": self.application_state.thumbnail_size,
                "folder_history": [str(path) for path in self.application_state.folder_history],
                "ui_layout": self.application_state.ui_layout,
                "window_geometry": self.application_state.window_geometry,
                "splitter_states": {
                    k: v.hex() if isinstance(v, bytes) else v for k, v in self.application_state.splitter_states.items()
                },
                "map_center": self.application_state.map_center,
                "map_zoom": self.application_state.map_zoom,
                "exif_display_mode": self.application_state.exif_display_mode,
                "image_sort_mode": self.application_state.image_sort_mode,
                "image_sort_ascending": self.application_state.image_sort_ascending,
                "current_zoom": self.application_state.current_zoom,
                "current_pan": self.application_state.current_pan,
                "fit_mode": self.application_state.fit_mode,
                "performance_mode": self.application_state.performance_mode,
                "cache_status": self.application_state.cache_status,
                "ai_component_status": self.application_state.ai_component_status,
                "session_start": self.application_state.session_start.isoformat(),
                "last_activity": self.application_state.last_activity.isoformat(),
                "images_processed": self.application_state.images_processed,
                "operations_performed": self.application_state.operations_performed,
                "recent_errors": self.application_state.recent_errors,
                "error_count": self.application_state.error_count,
                "memory_usage_history": [
                    (dt.isoformat(), usage) for dt, usage in self.application_state.memory_usage_history
                ],
                "operation_times": self.application_state.operation_times,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=2, default=str)

            return True

        except Exception as e:
            self.logger_system.error(f"Failed to save application state: {e}")
            return False

    def _load_application_state(self) -> bool:
        """Load application state from file"""
        try:
            if not self.state_file.exists():
                # No state file exists, use default state
                self.application_state = ApplicationState()
                return True

            with open(self.state_file, encoding="utf-8") as f:
                state_dict = json.load(f)

            # Convert dictionary back to ApplicationState
            self.application_state = ApplicationState(
                current_folder=(Path(state_dict["current_folder"]) if state_dict.get("current_folder") else None),
                selected_image=(Path(state_dict["selected_image"]) if state_dict.get("selected_image") else None),
                loaded_images=[Path(path) for path in state_dict.get("loaded_images", [])],
                current_theme=state_dict.get("current_theme", "default"),
                thumbnail_size=state_dict.get("thumbnail_size", 150),
                folder_history=[Path(path) for path in state_dict.get("folder_history", [])],
                ui_layout=state_dict.get("ui_layout", {}),
                window_geometry=(tuple(state_dict["window_geometry"]) if state_dict.get("window_geometry") else None),
                splitter_states={
                    k: bytes.fromhex(v) if isinstance(v, str) else v
                    for k, v in state_dict.get("splitter_states", {}).items()
                },
                map_center=(tuple(state_dict["map_center"]) if state_dict.get("map_center") else None),
                map_zoom=state_dict.get("map_zoom", 10),
                exif_display_mode=state_dict.get("exif_display_mode", "detailed"),
                image_sort_mode=state_dict.get("image_sort_mode", "name"),
                image_sort_ascending=state_dict.get("image_sort_ascending", True),
                current_zoom=state_dict.get("current_zoom", 1.0),
                current_pan=tuple(state_dict.get("current_pan", (0, 0))),
                fit_mode=state_dict.get("fit_mode", "fit_window"),
                performance_mode=state_dict.get("performance_mode", "balanced"),
                cache_status=state_dict.get("cache_status", {}),
                ai_component_status=state_dict.get(
                    "ai_component_status",
                    {"copilot": "active", "cursor": "active", "kiro": "active"},
                ),
                session_start=datetime.fromisoformat(state_dict.get("session_start", datetime.now().isoformat())),
                last_activity=datetime.fromisoformat(state_dict.get("last_activity", datetime.now().isoformat())),
                images_processed=state_dict.get("images_processed", 0),
                operations_performed=state_dict.get("operations_performed", []),
                recent_errors=state_dict.get("recent_errors", []),
                error_count=state_dict.get("error_count", 0),
                memory_usage_history=[
                    (datetime.fromisoformat(dt), usage) for dt, usage in state_dict.get("memory_usage_history", [])
                ],
                operation_times=state_dict.get("operation_times", {}),
            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "state_loading",
                "Application state loaded from storage",
            )

            return True

        except Exception as e:
            self.logger_system.error(f"Failed to load application state: {e}")
            # Use default state on error
            self.application_state = ApplicationState()
            return False

    def get_state_summary(self) -> dict[str, Any]:
        """Get summary of current application state"""
        return {
            "current_folder": (
                str(self.application_state.current_folder) if self.application_state.current_folder else None
            ),
            "selected_image": (
                str(self.application_state.selected_image) if self.application_state.selected_image else None
            ),
            "loaded_images_count": len(self.application_state.loaded_images),
            "current_theme": self.application_state.current_theme,
            "session_duration": self.application_state.session_duration,
            "images_processed": self.application_state.images_processed,
            "error_count": self.application_state.error_count,
            "ai_component_status": self.application_state.ai_component_status,
            "performance_mode": self.application_state.performance_mode,
        }
