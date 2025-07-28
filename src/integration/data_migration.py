"""
Data Migration Utilities for AI Integration

Provides utilities to migrate existing data from individual AI implementations
to the unified data model system.

Author: Kiro AI Integration System
"""

import json
import pickle
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from .models import (
    ImageMetadata, ThemeConfiguration, ApplicationState,
    ProcessingStatus, AIComponent
)
from .data_validation import DataValidator, ValidationResult
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
    """Result of a data migration operation"""
    source_type: str
    target_model: str
    status: MigrationStatus
    migrated_count: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)


class DataMigrationManager:
    """
    Data migration manager for AI integration

    Handles migration of existing data from individual AI implementations
    to the unified data model system.
    """

    def __init__(self,
                 data_dir: Path = None,
                 backup_dir: Path = None,
                 logger_system: LoggerSystem = None,
                 validator: DataValidator = None):
        """
        Initialize the data migration manager

        Args:
            data_dir: Data directory containing existing data files
            backup_dir: Backup directory for original data
            logger_system: Logging system instance
            validator: Data validator instance
        """
        self.data_dir = data_dir or Path("data")
        self.backup_dir = backup_dir or (self.data_dir / "migration_backups")
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)
        self.validator = validator or DataValidator(self.logger_system, self.error_handler)

        # Migration results
        self.migration_results: List[MigrationResult] = []

        # Create directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Migration mappings for different data sources
        self.migration_mappings = self._setup_migration_mappings()

        self.logger_system.info("Data migration manager initialized")

    def _setup_migration_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Setup migration mappings for different data formats"""
        return {
            # CursorBLD data migration
            "cursor_bld": {
                "image_cache": {
                    "source_files": ["image_cache.json", "thumbnail_cache.json"],
                    "target_model": "ImageMetadata",
                    "field_mappings": {
                        "file_path": "path",
                        "file_size": "size",
                        "thumbnail_path": "thumb_path",
                        "display_name": "name",
                        "created_date": "created",
                        "modified_date": "modified"
                    }
                },
                "theme_data": {
                    "source_files": ["themes.json", "custom_themes.json"],
                    "target_model": "ThemeConfiguration",
                    "field_mappings": {
                        "name": "theme_name",
                        "display_name": "display_name",
                        "color_scheme": "colors",
                        "qt_theme_name": "qt_theme",
                        "style_sheet": "stylesheet"
                    }
                },
                "ui_state": {
                    "source_files": ["ui_state.json", "window_state.json"],
                    "target_model": "ApplicationState",
                    "field_mappings": {
                        "current_theme": "theme",
                        "thumbnail_size": "thumb_size",
                        "window_geometry": "geometry",
                        "splitter_states": "splitters"
                    }
                }
            },

            # CS4Coding data migration
            "cs4_coding": {
                "exif_cache": {
                    "source_files": ["exif_data.json", "image_metadata.json"],
                    "target_model": "ImageMetadata",
                    "field_mappings": {
                        "file_path": "image_path",
                        "camera_make": "make",
                        "camera_model": "model",
                        "lens_model": "lens",
                        "focal_length": "focal_length",
                        "aperture": "f_number",
                        "shutter_speed": "exposure_time",
                        "iso": "iso_speed",
                        "latitude": "gps_lat",
                        "longitude": "gps_lon",
                        "altitude": "gps_alt",
                        "width": "image_width",
                        "height": "image_height"
                    }
                },
                "map_data": {
                    "source_files": ["map_cache.json", "gps_data.json"],
                    "target_model": "ImageMetadata",
                    "field_mappings": {
                        "latitude": "lat",
                        "longitude": "lng",
                        "altitude": "alt",
                        "gps_timestamp": "gps_time"
                    }
                }
            },

            # Legacy PhotoGeoView data
            "legacy": {
                "database": {
                    "source_files": ["photogeoview.db", "images.db"],
                    "target_model": "ImageMetadata",
                    "sql_queries": {
                        "images": """
                            SELECT path, size, created, modified, width, height,
                                   camera_make, camera_model, iso, aperture, shutter_speed,
                                   latitude, longitude, altitude
                            FROM images
                        """,
                        "thumbnails": """
                            SELECT image_path, thumbnail_path, size
                            FROM thumbnails
                        """
                    }
                },
                "settings": {
                    "source_files": ["settings.json", "preferences.json"],
                    "target_model": "ApplicationState",
                    "field_mappings": {
                        "last_folder": "current_folder",
                        "theme_name": "current_theme",
                        "thumb_size": "thumbnail_size",
                        "sort_by": "image_sort_mode",
                        "sort_asc": "image_sort_ascending"
                    }
                }
            }
        }

    def migrate_all_data(self) -> Dict[str, List[MigrationResult]]:
        """
        Migrate all existing data to unified models

        Returns:
            Dictionary of migration results by AI implementation
        """
        self.logger_system.info("Starting data migration process")

        migration_summary = {}

        try:
            # Migrate each AI implementation's data
            for ai_name, data_mappings in self.migration_mappings.items():
                ai_results = self._migrate_ai_data(ai_name, data_mappings)
                migration_summary[ai_name] = ai_results

                self.logger_system.info(
                    f"Completed {ai_name} data migration: {len(ai_results)} operations"
                )

            # Generate migration report
            self._generate_migration_report(migration_summary)

            self.logger_system.info("Data migration process completed")

            return migration_summary

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "migrate_all_data"},
                AIComponent.KIRO
            )
            return {"error": [MigrationResult(
                source_type="unknown",
                target_model="unknown",
                status=MigrationStatus.FAILED,
                migrated_count=0,
                errors=[str(e)]
            )]}

    def _migrate_ai_data(self, ai_name: str, data_mappings: Dict[str, Any]) -> List[MigrationResult]:
        """Migrate data for a specific AI implementation"""
        results = []

        self.logger_system.info(f"Migrating {ai_name} data")

        for data_type, mapping_config in data_mappings.items():
            try:
                if "sql_queries" in mapping_config:
                    # Database migration
                    result = self._migrate_database_data(ai_name, data_type, mapping_config)
                else:
                    # File-based migration
                    result = self._migrate_file_data(ai_name, data_type, mapping_config)

                results.append(result)

            except Exception as e:
                error_result = MigrationResult(
                    source_type=f"{ai_name}_{data_type}",
                    target_model=mapping_config.get("target_model", "unknown"),
                    status=MigrationStatus.FAILED,
                    migrated_count=0,
                    errors=[str(e)]
                )
                results.append(error_result)

                self.logger_system.error(f"Failed to migrate {ai_name} {data_type}: {e}")

        return results

    def _migrate_file_data(self, ai_name: str, data_type: str, mapping_config: Dict[str, Any]) -> MigrationResult:
        """Migrate data from JSON/file sources"""
        source_files = mapping_config["source_files"]
        target_model = mapping_config["target_model"]
        field_mappings = mapping_config["field_mappings"]

        result = MigrationResult(
            source_type=f"{ai_name}_{data_type}",
            target_model=target_model,
            status=MigrationStatus.SUCCESS,
            migrated_count=0
        )

        migrated_objects = []

        for source_file_name in source_files:
            source_file = self.data_dir / source_file_name

            if not source_file.exists():
                result.warnings.append(f"Source file not found: {source_file}")
                continue

            try:
                # Create backup
                self._create_backup(source_file)

                # Load source data
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_data = json.load(f)

                # Convert to list if single object
                if isinstance(source_data, dict):
                    source_data = [source_data]

                # Migrate each object
                for source_obj in source_data:
                    try:
                        migrated_obj = self._convert_object(source_obj, field_mappings, target_model)

                        if migrated_obj:
                            # Validate migrated object
                            validation_result = self._validate_migrated_object(migrated_obj, target_model)
                            result.validation_results.append(validation_result)

                            if validation_result.is_valid or not validation_result.has_errors:
                                migrated_objects.append(migrated_obj)
                                result.migrated_count += 1
                            else:
                                result.errors.extend([error["message"] for error in validation_result.errors])

                    except Exception as e:
                        result.errors.append(f"Failed to migrate object: {str(e)}")

            except Exception as e:
                result.errors.append(f"Failed to process {source_file}: {str(e)}")

        # Save migrated objects
        if migrated_objects:
            self._save_migrated_objects(migrated_objects, target_model, ai_name, data_type)

        # Determine final status
        if result.errors:
            result.status = MigrationStatus.PARTIAL if result.migrated_count > 0 else MigrationStatus.FAILED
        elif result.migrated_count == 0:
            result.status = MigrationStatus.SKIPPED

        return result

    def _migrate_database_data(self, ai_name: str, data_type: str, mapping_config: Dict[str, Any]) -> MigrationResult:
        """Migrate data from SQLite database sources"""
        source_files = mapping_config["source_files"]
        target_model = mapping_config["target_model"]
        sql_queries = mapping_config["sql_queries"]

        result = MigrationResult(
            source_type=f"{ai_name}_{data_type}",
            target_model=target_model,
            status=MigrationStatus.SUCCESS,
            migrated_count=0
        )

        migrated_objects = []

        for source_file_name in source_files:
            source_file = self.data_dir / source_file_name

            if not source_file.exists():
                result.warnings.append(f"Database file not found: {source_file}")
                continue

            try:
                # Create backup
                self._create_backup(source_file)

                # Connect to database
                with sqlite3.connect(source_file) as conn:
                    conn.row_factory = sqlite3.Row  # Enable column access by name

                    # Execute each query
                    for query_name, query_sql in sql_queries.items():
                        try:
                            cursor = conn.execute(query_sql)
                            rows = cursor.fetchall()

                            for row in rows:
                                try:
                                    # Convert row to dictionary
                                    row_dict = dict(row)

                                    # Create object based on target model
                                    migrated_obj = self._create_object_from_db_row(row_dict, target_model)

                                    if migrated_obj:
                                        # Validate migrated object
                                        validation_result = self._validate_migrated_object(migrated_obj, target_model)
                                        result.validation_results.append(validation_result)

                                        if validation_result.is_valid or not validation_result.has_errors:
                                            migrated_objects.append(migrated_obj)
                                            result.migrated_count += 1
                                        else:
                                            result.errors.extend([error["message"] for error in validation_result.errors])

                                except Exception as e:
                                    result.errors.append(f"Failed to migrate row from {query_name}: {str(e)}")

                        except Exception as e:
                            result.errors.append(f"Failed to execute query {query_name}: {str(e)}")

            except Exception as e:
                result.errors.append(f"Failed to process database {source_file}: {str(e)}")

        # Save migrated objects
        if migrated_objects:
            self._save_migrated_objects(migrated_objects, target_model, ai_name, data_type)

        # Determine final status
        if result.errors:
            result.status = MigrationStatus.PARTIAL if result.migrated_count > 0 else MigrationStatus.FAILED
        elif result.migrated_count == 0:
            result.status = MigrationStatus.SKIPPED

        return result

    def _convert_object(self, source_obj: Dict[str, Any], field_mappings: Dict[str, str], target_model: str) -> Optional[Any]:
        """Convert source object to target model using field mappings"""
        try:
            converted_data = {}

            # Apply field mappings
            for target_field, source_field in field_mappings.items():
                if source_field in source_obj:
                    value = source_obj[source_field]

                    # Transform value if needed
                    converted_value = self._transform_field_value(target_field, value, target_model)
                    converted_data[target_field] = converted_value

            # Create target model instance
            if target_model == "ImageMetadata":
                return self._create_image_metadata(converted_data)
            elif target_model == "ThemeConfiguration":
                return self._create_theme_configuration(converted_data)
            elif target_model == "ApplicationState":
                return self._create_application_state(converted_data)

            return None

        except Exception as e:
            self.logger_system.error(f"Failed to convert object to {target_model}: {e}")
            return None

    def _create_object_from_db_row(self, row_dict: Dict[str, Any], target_model: str) -> Optional[Any]:
        """Create target model object from database row"""
        try:
            if target_model == "ImageMetadata":
                return self._create_image_metadata(row_dict)
            elif target_model == "ThemeConfiguration":
                return self._create_theme_configuration(row_dict)
            elif target_model == "ApplicationState":
                return self._create_application_state(row_dict)

            return None

        except Exception as e:
            self.logger_system.error(f"Failed to create {target_model} from database row: {e}")
            return None

    def _create_image_metadata(self, data: Dict[str, Any]) -> Optional[ImageMetadata]:
        """Create ImageMetadata instance from data"""
        try:
            # Required fields with defaults
            file_path = Path(data.get('file_path', data.get('path', data.get('image_path', ''))))
            file_size = data.get('file_size', data.get('size', 0))

            # Handle datetime fields
            created_date = self._parse_datetime(data.get('created_date', data.get('created', datetime.now())))
            modified_date = self._parse_datetime(data.get('modified_date', data.get('modified', datetime.now())))

            return ImageMetadata(
                file_path=file_path,
                file_size=file_size,
                created_date=created_date,
                modified_date=modified_date,
                file_format=data.get('file_format', file_path.suffix if file_path else ''),

                # EXIF data
                camera_make=data.get('camera_make', data.get('make')),
                camera_model=data.get('camera_model', data.get('model')),
                lens_model=data.get('lens_model', data.get('lens')),
                focal_length=data.get('focal_length'),
                aperture=data.get('aperture', data.get('f_number')),
                shutter_speed=data.get('shutter_speed', data.get('exposure_time')),
                iso=data.get('iso', data.get('iso_speed')),

                # GPS data
                latitude=data.get('latitude', data.get('gps_lat', data.get('lat'))),
                longitude=data.get('longitude', data.get('gps_lon', data.get('lng'))),
                altitude=data.get('altitude', data.get('gps_alt', data.get('alt'))),
                gps_timestamp=self._parse_datetime(data.get('gps_timestamp', data.get('gps_time'))),

                # Image dimensions
                width=data.get('width', data.get('image_width')),
                height=data.get('height', data.get('image_height')),

                # UI data
                thumbnail_path=Path(data['thumbnail_path']) if data.get('thumbnail_path') else None,
                display_name=data.get('display_name', data.get('name', file_path.name if file_path else '')),

                # Processing status
                processing_status=ProcessingStatus.COMPLETED,
                ai_processor=AIComponent.KIRO
            )

        except Exception as e:
            self.logger_system.error(f"Failed to create ImageMetadata: {e}")
            return None

    def _create_theme_configuration(self, data: Dict[str, Any]) -> Optional[ThemeConfiguration]:
        """Create ThemeConfiguration instance from data"""
        try:
            return ThemeConfiguration(
                name=data.get('name', data.get('theme_name', 'unknown')),
                display_name=data.get('display_name', data.get('name', 'Unknown Theme')),
                description=data.get('description', ''),
                version=data.get('version', '1.0.0'),
                author=data.get('author', ''),
                qt_theme_name=data.get('qt_theme_name', data.get('qt_theme', '')),
                style_sheet=data.get('style_sheet', data.get('stylesheet', '')),
                color_scheme=data.get('color_scheme', data.get('colors', {})),
                icon_theme=data.get('icon_theme', 'default')
            )

        except Exception as e:
            self.logger_system.error(f"Failed to create ThemeConfiguration: {e}")
            return None

    def _create_application_state(self, data: Dict[str, Any]) -> Optional[ApplicationState]:
        """Create ApplicationState instance from data"""
        try:
            return ApplicationState(
                current_folder=Path(data['current_folder']) if data.get('current_folder') else None,
                selected_image=Path(data['selected_image']) if data.get('selected_image') else None,
                current_theme=data.get('current_theme', data.get('theme', 'default')),
                thumbnail_size=data.get('thumbnail_size', data.get('thumb_size', 150)),
                window_geometry=data.get('window_geometry', data.get('geometry')),
                splitter_states=data.get('splitter_states', data.get('splitters', {})),
                image_sort_mode=data.get('image_sort_mode', data.get('sort_by', 'name')),
                image_sort_ascending=data.get('image_sort_ascending', data.get('sort_asc', True)),
                performance_mode=data.get('performance_mode', 'balanced')
            )

        except Exception as e:
            self.logger_system.error(f"Failed to create ApplicationState: {e}")
            return None

    def _transform_field_value(self, field_name: str, value: Any, target_model: str) -> Any:
        """Transform field value during migration if needed"""
        try:
            # Path transformations
            if field_name in ['file_path', 'thumbnail_path', 'current_folder', 'selected_image']:
                if isinstance(value, str):
                    return Path(value)
                return value

            # DateTime transformations
            if field_name in ['created_date', 'modified_date', 'gps_timestamp']:
                return self._parse_datetime(value)

            # Numeric transformations
            if field_name in ['file_size', 'width', 'height', 'iso', 'thumbnail_size']:
                if isinstance(value, str) and value.isdigit():
                    return int(value)
                return value

            if field_name in ['focal_length', 'aperture', 'latitude', 'longitude', 'altitude', 'current_zoom']:
                if isinstance(value, str):
                    try:
                        return float(value)
                    except ValueError:
                        return value
                return value

            # Boolean transformations
            if field_name in ['image_sort_ascending', 'preview_available', 'validation_status']:
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                return bool(value)

            return value

        except Exception:
            return value

    def _parse_datetime(self, value: Any) -> datetime:
        """Parse datetime from various formats"""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            # Try common datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y'
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

        if isinstance(value, (int, float)):
            # Assume Unix timestamp
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                pass

        # Default to current time
        return datetime.now()

    def _validate_migrated_object(self, obj: Any, target_model: str) -> ValidationResult:
        """Validate migrated object"""
        if target_model == "ImageMetadata":
            return self.validator.validate_image_metadata(obj)
        elif target_model == "ThemeConfiguration":
            return self.validator.validate_theme_configuration(obj)
        elif target_model == "ApplicationState":
            return self.validator.validate_application_state(obj)

        # Default validation result
        from .data_validation import ValidationResult
        return ValidationResult(is_valid=True)

    def _save_migrated_objects(self, objects: List[Any], target_model: str, ai_name: str, data_type: str):
        """Save migrated objects to appropriate storage"""
        try:
            output_file = self.data_dir / f"migrated_{ai_name}_{data_type}_{target_model.lower()}.json"

            # Convert objects to serializable format
            serializable_objects = []
            for obj in objects:
                if hasattr(obj, '__dict__'):
                    obj_dict = {}
                    for key, value in obj.__dict__.items():
                        if isinstance(value, Path):
                            obj_dict[key] = str(value)
                        elif isinstance(value, datetime):
                            obj_dict[key] = value.isoformat()
                        elif isinstance(value, Enum):
                            obj_dict[key] = value.value
                        else:
                            obj_dict[key] = value
                    serializable_objects.append(obj_dict)

            # Save to JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_objects, f, indent=2, default=str)

            self.logger_system.info(f"Saved {len(objects)} migrated {target_model} objects to {output_file}")

        except Exception as e:
            self.logger_system.error(f"Failed to save migrated objects: {e}")

    def _create_backup(self, source_file: Path) -> Path:
        """Create backup of source data file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{source_file.stem}_{timestamp}{source_file.suffix}"

        if source_file.suffix == '.db':
            # For SQLite databases, use proper backup method
            import shutil
            shutil.copy2(source_file, backup_file)
        else:
            # For other files, simple copy
            import shutil
            shutil.copy2(source_file, backup_file)

        return backup_file

    def _generate_migration_report(self, migration_summary: Dict[str, List[MigrationResult]]):
        """Generate detailed migration report"""
        report_file = self.data_dir / "data_migration_report.json"

        report_data = {
            "migration_timestamp": datetime.now().isoformat(),
            "summary": {},
            "detailed_results": {}
        }

        total_migrated = 0
        total_errors = 0

        for ai_name, results in migration_summary.items():
            ai_summary = {
                "total_operations": len(results),
                "successful": sum(1 for r in results if r.status == MigrationStatus.SUCCESS),
                "partial": sum(1 for r in results if r.status == MigrationStatus.PARTIAL),
                "failed": sum(1 for r in results if r.status == MigrationStatus.FAILED),
                "skipped": sum(1 for r in results if r.status == MigrationStatus.SKIPPED),
                "total_migrated": sum(r.migrated_count for r in results),
                "total_errors": sum(len(r.errors) for r in results)
            }

            report_data["summary"][ai_name] = ai_summary
            total_migrated += ai_summary["total_migrated"]
            total_errors += ai_summary["total_errors"]

            # Detailed results
            report_data["detailed_results"][ai_name] = [
                {
                    "source_type": r.source_type,
                    "target_model": r.target_model,
                    "status": r.status.value,
                    "migrated_count": r.migrated_count,
                    "error_count": len(r.errors),
                    "warning_count": len(r.warnings),
                    "validation_issues": sum(len(v.errors) + len(v.warnings) for v in r.validation_results)
                }
                for r in results
            ]

        report_data["overall_summary"] = {
            "total_migrated_objects": total_migrated,
            "total_errors": total_errors,
            "migration_status": "success" if total_errors == 0 else "partial" if total_migrated > 0 else "failed"
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

        self.logger_system.info(f"Migration report saved to {report_file}")

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        return {
            "migration_results_count": len(self.migration_results),
            "backup_directory": str(self.backup_dir),
            "data_directory": str(self.data_dir),
            "available_migrations": list(self.migration_mappings.keys())
        }
