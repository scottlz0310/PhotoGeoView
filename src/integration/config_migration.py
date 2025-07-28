"""
Configuration Migration Utilities for AI Integration

Provides utilities to migrate existing configuration files from individual AI implementations
to the unified configuration system.

Author: Kiro AI Integration System
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .models import AIComponent
from .logging_system import LoggerSystem
from .error_handling import IntegratedErrorHandler, ErrorCategory


class MigrationStatus(Enum):
    """Migration status enumeration"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class MigrationResult:
    """Migration result data structure"""
    source_file: Path
    target_section: str
    status: MigrationStatus
    migrated_settings: int
    errors: List[str]
    warnings: List[str]
    backup_file: Optional[Path] = None


class ConfigMigrationManager:
    """
    Configuration migration manager for AI integration

    Handles migration of existing configuration files from individual AI implementations
    to the unified configuration system.
    """

    def __init__(self,
                 config_dir: Path = None,
                 backup_dir: Path = None,
                 logger_system: LoggerSystem = None):
        """
        Initialize the migration manager

        Args:
            config_dir: Configuration directory
            backup_dir: Backup directory for original files
            logger_system: Logging system instance
        """

        self.config_dir = config_dir or Path("config")
        self.backup_dir = backup_dir or (self.config_dir / "migration_backups")
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Migration results
        self.migration_results: List[MigrationResult] = []

        # Create directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Migration mappings for different AI implementations
        self.migration_mappings = self._setup_migration_mappings()

        self.logger_system.info("Configuration migration manager initialized")

    def _setup_migration_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Setup migration mappings for different configuration formats"""

        return {
            # CursorBLD configuration migration
            "cursor_bld": {
                "source_files": [
                    "qt_theme_settings.json",
                    "qt_theme_user_settings.json",
                    "cursor_ui_config.json"
                ],
                "target_section": "ai_cursor",
                "mappings": {
                    # Qt theme settings
                    "current_theme": "theme_system.current_theme",
                    "theme_list": "theme_system.available_themes",
                    "custom_themes": "theme_system.custom_themes",
                    "theme_validation": "theme_system.theme_validation",

                    # UI optimization settings
                    "thumbnail_size": "ui_optimization.thumbnail_size",
                    "fast_thumbnails": "ui_optimization.fast_thumbnails",
                    "smooth_scrolling": "ui_optimization.smooth_scrolling",
                    "responsive_layout": "ui_optimization.responsive_layout",
                    "accessibility_features": "ui_optimization.accessibility_features",

                    # Window settings
                    "window_geometry": "ui.window_geometry",
                    "splitter_states": "ui.splitter_states",
                    "show_toolbar": "ui.show_toolbar",
                    "show_statusbar": "ui.show_statusbar"
                }
            },

            # CS4Coding configuration migration
            "cs4_coding": {
                "source_files": [
                    "copilot_config.json",
                    "image_processing_config.json",
                    "map_config.json"
                ],
                "target_section": "ai_copilot",
                "mappings": {
                    # Image processing settings
                    "high_quality_exif": "image_processing.high_quality_exif",
                    "detailed_metadata": "image_processing.detailed_metadata",
                    "gps_precision": "image_processing.gps_precision",
                    "error_recovery": "image_processing.error_recovery",

                    # Map integration settings
                    "folium_version": "map_integration.folium_version",
                    "marker_clustering": "map_integration.marker_clustering",
                    "offline_tiles": "map_integration.offline_tiles",
                    "custom_markers": "map_integration.custom_markers",

                    # Core functionality
                    "image_formats": "core.image_formats",
                    "exif_parsing_enabled": "core.exif_parsing_enabled",
                    "map_provider": "core.map_provider",
                    "map_zoom_default": "core.map_zoom_default",
                    "thumbnail_quality": "core.thumbna",
                    "cache_enabled": "core.cache_enabled",
                    "cache_size_mb": "core.cache_size_mb"
                }
            },

            # Kiro configuration migration
            "kiro": {
                "source_files": [
                    "kiro_config.json",
                    "integration_config.json",
                    "performance_config.json"
                ],
                "target_section": "ai_kiro",
                "mappings": {
                    # Integration settings
                    "error_correlation": "integration.error_correlation",
                    "performance_monitoring": "integration.performance_monitoring",
                    "ai_coordination": "integration.ai_coordination",
                    "quality_assurance": "integration.quality_assurance",

                    # Optimization settings
                    "memory_management": "optimization.memory_management",
                    "cache_optimization": "optimization.cache_optimization",
                    "async_processing": "optimization.async_processing",
                    "resource_pooling": "optimization.resource_pooling",

                    # Performance settings
                    "mode": "performance.mode",
                    "max_memory_mb": "performance.max_memory_mb",
                    "thread_pool_size": "performance.thread_pool_size",
                    "async_loading": "performance.async_loading",
                    "preload_thumbnails": "performance.preload_thumbnails",
                    "performance_monitoring": "performance.performance_monitoring"
                }
            },

            # Legacy PhotoGeoView configuration
            "legacy": {
                "source_files": [
                    "photogeoview_config.json",
                    "app_settings.json",
                    "user_preferences.json"
                ],
                "target_section": "app",
                "mappings": {
                    # Application settings
                    "app_name": "app.name",
                    "app_version": "app.version",
                    "debug_mode": "app.debug_mode",
                    "auto_save": "app.auto_save",
                    "backup_enabled": "app.backup_enabled",
                    "telemetry_enabled": "app.telemetry_enabled",

                    # Logging settings
                    "log_level": "logging.level",
                    "file_logging": "logging.file_logging",
                    "console_logging": "logging.console_logging",
                    "performance_logging": "logging.performance_logging",
                    "ai_operation_logging": "logging.ai_operation_logging",
                    "max_log_size_mb": "logging.max_log_size_mb",
                    "log_retention_days": "logging.log_retention_days"
                }
            }
        }

    def migrate_all_configurations(self) -> Dict[str, Any]:
        """
        Migrate all existing configuration files to unified system

        Returns:
            Migration summary dictionary
        """

        self.logger_system.info("Starting configuration migration process")

        migration_summary = {
            "start_time": datetime.now().isoformat(),
            "migrations": {},
            "total_files_processed": 0,
            "total_settings_migrated": 0,
            "errors": [],
            "warnings": []
        }

        try:
            # Migrate each AI implementation's configuration
            for ai_name, mapping_config in self.migration_mappings.items():
                ai_results = self._migrate_ai_configuration(ai_name, mapping_config)
                migration_summary["migrations"][ai_name] = ai_results

                # Update totals
                migration_summary["total_files_processed"] += len(ai_results)
                for result in ai_results:
                    migration_summary["total_settings_migrated"] += result.migrated_settings
                    migration_summary["errors"].extend(result.errors)
                    migration_summary["warnings"].extend(result.warnings)

            migration_summary["end_time"] = datetime.now().isoformat()
            migration_summary["status"] = self._determine_overall_status(migration_summary)

            # Generate migration report
            self._generate_migration_report(migration_summary)

            self.logger_system.info(
                f"Configuration migration completed: {migration_summary['status']}"
            )

            return migration_summary

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "migrate_all_configurations"},
                AIComponent.KIRO
            )
            migration_summary["status"] = "failed"
            migration_summary["errors"].append(str(e))
            return migration_summary

    def _migrate_ai_configuration(self, ai_name: str, mapping_config: Dict[str, Any]) -> List[MigrationResult]:
        """Migrate configuration for a specific AI implementation"""

        results = []
        source_files = mapping_config["source_files"]
        target_section = mapping_config["target_section"]
        mappings = mapping_config["mappings"]

        self.logger_system.info(f"Migrating {ai_name} configuration")

        for source_file_name in source_files:
            source_file = self.config_dir / source_file_name

            if not source_file.exists():
                result = MigrationResult(
                    source_file=source_file,
                    target_section=target_section,
                    status=MigrationStatus.SKIPPED,
                    migrated_settings=0,
                    errors=[],
                    warnings=[f"Source file not found: {source_file}"]
                )
                results.append(result)
                continue

            try:
                # Load source configuration
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_config = json.load(f)

                # Create backup
                backup_file = self._create_backup(source_file)

                # Migrate settings
                migrated_config, migration_errors, migration_warnings = self._migrate_settings(
                    source_config, mappings
                )

                # Determine migration status
                if migration_errors:
                    status = MigrationStatus.FAILED if not migrated_config else MigrationStatus.PARTIAL
                else:
                    status = MigrationStatus.SUCCESS

                result = MigrationResult(
                    source_file=source_file,
                    target_section=target_section,
                    status=status,
                    migrated_settings=len(migrated_config),
                    errors=migration_errors,
                    warnings=migration_warnings,
                    backup_file=backup_file
                )

                results.append(result)

                # Save migrated configuration
                if migrated_config:
                    self._save_migrated_config(target_section, migrated_config)

                self.logger_system.info(
                    f"Migrated {len(migrated_config)} settings from {source_file}"
                )

            except Exception as e:
                result = MigrationResult(
                    source_file=source_file,
                    target_section=target_section,
                    status=MigrationStatus.FAILED,
                    migrated_settings=0,
                    errors=[str(e)],
                    warnings=[]
                )
                results.append(result)

                self.logger_system.error(f"Failed to migrate {source_file}: {e}")

        return results

    def _migrate_settings(self, source_config: Dict[str, Any], mappings: Dict[str, str]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Migrate individual settings using mapping configuration"""

        migrated_config = {}
        errors = []
        warnings = []

        for source_key, target_path in mappings.items():
            try:
                if source_key in source_config:
                    value = source_config[source_key]

                    # Validate and transform value if needed
                    transformed_value = self._transform_setting_value(source_key, value)

                    # Set nested value using dot notation
                    self._set_nested_value(migrated_config, target_path, transformed_value)

                else:
                    warnings.append(f"Source setting not found: {source_key}")

            except Exception as e:
                errors.append(f"Failed to migrate {source_key}: {str(e)}")

        return migrated_config, errors, warnings

    def _transform_setting_value(self, key: str, value: Any) -> Any:
        """Transform setting value during migration if needed"""

        # Handle specific transformations
        transformations = {
            # Convert string paths to Path objects
            "current_folder": lambda x: str(Path(x)) if x else None,
            "selected_image": lambda x: str(Path(x)) if x else None,

            # Convert theme names
            "current_theme": lambda x: x.lower() if isinstance(x, str) else x,

            # Ensure numeric ranges
            "thumbnail_size": lambda x: max(50, min(500, int(x))) if isinstance(x, (int, float)) else x,
            "map_zoom_default": lambda x: max(1, min(20, int(x))) if isinstance(x, (int, float)) else x,

            # Convert boolean strings
            "debug_mode": lambda x: str(x).lower() in ['true', '1', 'yes', 'on'] if isinstance(x, str) else bool(x),
            "auto_save": lambda x: str(x).lower() in ['true', '1', 'yes', 'on'] if isinstance(x, str) else bool(x),
        }

        if key in transformations:
            try:
                return transformations[key](value)
            except Exception:
                # Return original value if transformation fails
                return value

        return value

    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set nested configuration value using dot notation"""

        keys = path.split('.')
        current = config

        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

    def _create_backup(self, source_file: Path) -> Path:
        """Create backup of source configuration file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{source_file.stem}_{timestamp}{source_file.suffix}"

        shutil.copy2(source_file, backup_file)

        return backup_file

    def _save_migrated_config(self, target_section: str, migrated_config: Dict[str, Any]):
        """Save migrated configuration to appropriate file"""

        # Determine target file based on section
        if target_section.startswith("ai_"):
            ai_name = target_section[3:]  # Remove "ai_" prefix
            target_file = self.config_dir / f"{ai_name}_config.json"
        else:
            target_file = self.config_dir / "app_config.json"

        # Load existing configuration if it exists
        existing_config = {}
        if target_file.exists():
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except Exception:
                pass

        # Merge migrated configuration
        self._deep_merge(existing_config, migrated_config)

        # Save merged configuration
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, indent=2, default=str)

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source dictionary into target dictionary"""

        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _determine_overall_status(self, migration_summary: Dict[str, Any]) -> str:
        """Determine overall migration status"""

        total_errors = len(migration_summary["errors"])
        total_settings = migration_summary["total_settings_migrated"]

        if total_errors == 0 and total_settings > 0:
            return "success"
        elif total_errors > 0 and total_settings > 0:
            return "partial"
        elif total_errors > 0:
            return "failed"
        else:
            return "no_migration_needed"

    def _generate_migration_report(self, migration_summary: Dict[str, Any]):
        """Generate detailed migration report"""

        report_file = self.config_dir / "migration_report.json"

        # Add detailed results
        detailed_summary = migration_summary.copy()
        detailed_summary["migration_results"] = [
            {
                "source_file": str(result.source_file),
                "target_section": result.target_section,
                "status": result.status.value,
                "migrated_settings": result.migrated_settings,
                "errors": result.errors,
                "warnings": result.warnings,
                "backup_file": str(result.backup_file) if result.backup_file else None
            }
            for result in self.migration_results
        ]

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_summary, f, indent=2, default=str)

        self.logger_system.info(f"Migration report saved to {report_file}")

    def rollback_migration(self, migration_timestamp: str = None) -> bool:
        """
        Rollback migration by restoring backup files

        Args:
            migration_timestamp: Specific migration timestamp to rollback

        Returns:
            True if rollback was successful
        """

        try:
            self.logger_system.info("Starting migration rollback")

            # Find backup files
            if migration_timestamp:
                backup_pattern = f"*_{migration_timestamp}.*"
            else:
                backup_pattern = "*"

            backup_files = list(self.backup_dir.glob(backup_pattern))

            if not backup_files:
                self.logger_system.warning("No backup files found for rollback")
                return False

            # Restore backup files
            restored_count = 0
            for backup_file in backup_files:
                try:
                    # Extract original filename
                    parts = backup_file.stem.split('_')
                    if len(parts) >= 3:  # name_timestamp format
                        original_name = '_'.join(parts[:-2])  # Remove timestamp parts
                        original_file = self.config_dir / f"{original_name}{backup_file.suffix}"

                        # Restore backup
                        shutil.copy2(backup_file, original_file)
                        restored_count += 1

                        self.logger_system.info(f"Restored {original_file} from backup")

                except Exception as e:
                    self.logger_system.error(f"Failed to restore {backup_file}: {e}")

            self.logger_system.info(f"Migration rollback completed: {restored_count} files restored")
            return restored_count > 0

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "rollback_migration"},
                AIComponent.KIRO
            )
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""

        return {
            "migration_results_count": len(self.migration_results),
            "backup_directory": str(self.backup_dir),
            "backup_files_count": len(list(self.backup_dir.glob("*"))),
            "config_directory": str(self.config_dir),
            "available_migrations": list(self.migration_mappings.keys())
        }

    def migrate_all_configurations(self) -> Dict[str, Any]:
        """
        Migrate all existing configuration files to unified system

        Returns:
            Migration summary dictionary
        """

        self.logger_system.info("Starting configuration migration process")

        migration_summary = {
            "start_time": datetime.now().isoformat(),
            "migrations": {},
            "total_files_processed": 0,
            "total_settings_migrated": 0,
            "errors": [],
            "warnings": []
        }

        try:
            # Migrate each AI implementation's configuration
            for ai_name, mapping_config in self.migration_mappings.items():
                ai_results = self._migrate_ai_configuration(ai_name, mapping_config)
                migration_summary["migrations"][ai_name] = ai_results

                # Update totals
                migration_summary["total_files_processed"] += len(ai_results)
                for result in ai_results:
                    migration_summary["total_settings_migrated"] += result.migrated_settings
                    migration_summary["errors"].extend(result.errors)
                    migration_summary["warnings"].extend(result.warnings)

            migration_summary["end_time"] = datetime.now().isoformat()
            migration_summary["status"] = self._determine_overall_status(migration_summary)

            # Generate migration report
            self._generate_migration_report(migration_summary)

            self.logger_system.info(
                f"Configuration migration completed: {migration_summary['status']}"
            )

            return migration_summary

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "migrate_all_configurations"},
                AIComponent.KIRO
            )
            migration_summary["status"] = "failed"
            migration_summary["errors"].append(str(e))
            return migration_summary

    def _migrate_ai_configuration(self, ai_name: str, mapping_config: Dict[str, Any]) -> List[MigrationResult]:
        """Migrate configuration for a specific AI implementation"""

        results = []
        source_files = mapping_config["source_files"]
        target_section = mapping_config["target_section"]
        mappings = mapping_config["mappings"]

        self.logger_system.info(f"Migrating {ai_name} configuration")

        for source_file_name in source_files:
            source_file = self.config_dir / source_file_name

            if not source_file.exists():
                result = MigrationResult(
                    source_file=source_file,
                    target_section=target_section,
                    status=MigrationStatus.SKIPPED,
                    migrated_settings=0,
                    errors=[],
                    warnings=[f"Source file not found: {source_file}"]
                )
                results.append(result)
                continue

            try:
                # Load source configuration
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_config = json.load(f)

                # Create backup
                backup_file = self._create_backup(source_file)

                # Migrate settings
                migrated_config, migration_errors, migration_warnings = self._migrate_settings(
                    source_config, mappings
                )

                # Determine migration status
                if migration_errors:
                    status = MigrationStatus.FAILED if not migrated_config else MigrationStatus.PARTIAL
                else:
                    status = MigrationStatus.SUCCESS

                result = MigrationResult(
                    source_file=source_file,
                    target_section=target_section,
                    status=status,
                    migrated_settings=len(migrated_config),
                    errors=migration_errors,
                    warnings=migration_warnings,
                    backup_file=backup_file
                )

                results.append(result)

                # Save migrated configuration
                if migrated_config:
                    self._save_migrated_config(target_section, migrated_config)

                self.logger_system.info(
                    f"Migrated {len(migrated_config)} settings from {source_file}"
                )

            except Exception as e:
                result = MigrationResult(
                    source_file=source_file,
                    target_section=target_section,
                    status=MigrationStatus.FAILED,
                    migrated_settings=0,
                    errors=[str(e)],
                    warnings=[]
                )
                results.append(result)

                self.logger_system.error(f"Failed to migrate {source_file}: {e}")

        return results

    def _migrate_settings(self, source_config: Dict[str, Any], mappings: Dict[str, str]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """Migrate individual settings using mapping configuration"""

        migrated_config = {}
        errors = []
        warnings = []

        for source_key, target_path in mappings.items():
            try:
                if source_key in source_config:
                    value = source_config[source_key]

                    # Validate and transform value if needed
                    transformed_value = self._transform_setting_value(source_key, value)

                    # Set nested value using dot notation
                    self._set_nested_value(migrated_config, target_path, transformed_value)

                else:
                    warnings.append(f"Source setting not found: {source_key}")

            except Exception as e:
                errors.append(f"Failed to migrate {source_key}: {str(e)}")

        return migrated_config, errors, warnings

    def _transform_setting_value(self, key: str, value: Any) -> Any:
        """Transform setting value during migration if needed"""

        # Handle specific transformations
        transformations = {
            # Convert string paths to Path objects
            "current_folder": lambda x: str(Path(x)) if x else None,
            "selected_image": lambda x: str(Path(x)) if x else None,

            # Convert theme names
            "current_theme": lambda x: x.lower() if isinstance(x, str) else x,

            # Ensure numeric ranges
            "thumbnail_size": lambda x: max(50, min(500, int(x))) if isinstance(x, (int, float)) else x,
            "map_zoom_default": lambda x: max(1, min(20, int(x))) if isinstance(x, (int, float)) else x,

            # Convert boolean strings
            "debug_mode": lambda x: str(x).lower() in ['true', '1', 'yes', 'on'] if isinstance(x, str) else bool(x),
            "auto_save": lambda x: str(x).lower() in ['true', '1', 'yes', 'on'] if isinstance(x, str) else bool(x),
        }

        if key in transformations:
            try:
                return transformations[key](value)
            except Exception:
                # Return original value if transformation fails
                return value

        return value

    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set nested configuration value using dot notation"""

        keys = path.split('.')
        current = config

        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

    def _create_backup(self, source_file: Path) -> Path:
        """Create backup of source configuration file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{source_file.stem}_{timestamp}{source_file.suffix}"

        shutil.copy2(source_file, backup_file)

        return backup_file

    def _save_migrated_config(self, target_section: str, migrated_config: Dict[str, Any]):
        """Save migrated configuration to appropriate file"""

        # Determine target file based on section
        if target_section.startswith("ai_"):
            ai_name = target_section[3:]  # Remove "ai_" prefix
            target_file = self.config_dir / f"{ai_name}_config.json"
        else:
            target_file = self.config_dir / "app_config.json"

        # Load existing configuration if it exists
        existing_config = {}
        if target_file.exists():
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except Exception:
                pass

        # Merge migrated configuration
        self._deep_merge(existing_config, migrated_config)

        # Save merged configuration
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, indent=2, default=str)

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source dictionary into target dictionary"""

        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _determine_overall_status(self, migration_summary: Dict[str, Any]) -> str:
        """Determine overall migration status"""

        total_errors = len(migration_summary["errors"])
        total_settings = migration_summary["total_settings_migrated"]

        if total_errors == 0 and total_settings > 0:
            return "success"
        elif total_errors > 0 and total_settings > 0:
            return "partial"
        elif total_errors > 0:
            return "failed"
        else:
            return "no_migration_needed"

    def _generate_migration_report(self, migration_summary: Dict[str, Any]):
        """Generate detailed migration report"""

        report_file = self.config_dir / "migration_report.json"

        # Add detailed results
        detailed_summary = migration_summary.copy()
        detailed_summary["migration_results"] = [
            {
                "source_file": str(result.source_file),
                "target_section": result.target_section,
                "status": result.status.value,
                "migrated_settings": result.migrated_settings,
                "errors": result.errors,
                "warnings": result.warnings,
                "backup_file": str(result.backup_file) if result.backup_file else None
            }
            for result in self.migration_results
        ]

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_summary, f, indent=2, default=str)

        self.logger_system.info(f"Migration report saved to {report_file}")

    def rollback_migration(self, migration_timestamp: str = None) -> bool:
        """
        Rollback migration by restoring backup files

        Args:
            migration_timestamp: Specific migration timestamp to rollback

        Returns:
            True if rollback was successful
        """

        try:
            self.logger_system.info("Starting migration rollback")

            # Find backup files
            if migration_timestamp:
                backup_pattern = f"*_{migration_timestamp}.*"
            else:
                backup_pattern = "*"

            backup_files = list(self.backup_dir.glob(backup_pattern))

            if not backup_files:
                self.logger_system.warning("No backup files found for rollback")
                return False

            # Restore backup files
            restored_count = 0
            for backup_file in backup_files:
                try:
                    # Extract original filename
                    parts = backup_file.stem.split('_')
                    if len(parts) >= 3:  # name_timestamp format
                        original_name = '_'.join(parts[:-2])  # Remove timestamp parts
                        original_file = self.config_dir / f"{original_name}{backup_file.suffix}"

                        # Restore backup
                        shutil.copy2(backup_file, original_file)
                        restored_count += 1

                        self.logger_system.info(f"Restored {original_file} from backup")

                except Exception as e:
                    self.logger_system.error(f"Failed to restore {backup_file}: {e}")

            self.logger_system.info(f"Migration rollback completed: {restored_count} files restored")
            return restored_count > 0

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "rollback_migration"},
                AIComponent.KIRO
            )
            return False

    def validate_migrated_configuration(self) -> Dict[str, Any]:
        """Validate migrated configuration files"""

        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "files_validated": 0,
            "validation_errors": [],
            "validation_warnings": [],
            "status": "success"
        }

        try:
            # Validate each configuration file
            config_files = [
                self.config_dir / "app_config.json",
                self.config_dir / "copilot_config.json",
                self.config_dir / "cursor_config.json",
                self.config_dir / "kiro_config.json"
            ]

            for config_file in config_files:
                if config_file.exists():
                    file_validation = self._validate_config_file(config_file)
                    validation_results["files_validated"] += 1
                    validation_results["validation_errors"].extend(file_validation["errors"])
                    validation_results["validation_warnings"].extend(file_validation["warnings"])

            # Determine overall status
            if validation_results["validation_errors"]:
                validation_results["status"] = "failed"
            elif validation_results["validation_warnings"]:
                validation_results["status"] = "warnings"

            return validation_results

        except Exception as e:
            validation_results["status"] = "error"
            validation_results["validation_errors"].append(str(e))
            return validation_results

    def _validate_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Validate individual configuration file"""

        validation_result = {
            "file": str(config_file),
            "errors": [],
            "warnings": []
        }

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Basic JSON structure validation
            if not isinstance(config_data, dict):
                validation_result["errors"].append("Configuration must be a JSON object")
                return validation_result

            # Check for required sections based on file type
            if "app_config" in config_file.name:
                required_sections = ["app", "ui", "core", "performance", "logging"]
            elif "copilot_config" in config_file.name:
                required_sections = ["image_processing", "map_integration"]
            elif "cursor_config" in config_file.name:
                required_sections = ["theme_system", "ui_optimization"]
            elif "kiro_config" in config_file.name:
                required_sections = ["integration", "optimization"]
            else:
                required_sections = []

            for section in required_sections:
                if section not in config_data:
                    validation_result["warnings"].append(f"Missing recommended section: {section}")

            return validation_result

        except json.JSONDecodeError as e:
            validation_result["errors"].append(f"Invalid JSON format: {str(e)}")
            return validation_result
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            return validation_result

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""

        return {
            "migration_results_count": len(self.migration_results),
            "backup_directory": str(self.backup_dir),
            "backup_files_count": len(list(self.backup_dir.glob("*"))),
            "config_directory": str(self.config_dir),
            "available_migrations": list(self.migration_mappings.keys())
        }
