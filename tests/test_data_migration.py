"""
Test suite for Data Migration System - Task 7 Implementation

Tests the data migration functionality for AI integration.

Author: Kiro AI Integration System
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.integration.data_migration import (
    DataMigrationManager,
    MigrationResult,
    MigrationStatus,
)
from src.integration.data_validation import DataValidator
from src.integration.error_handling import IntegratedErrorHandler
from src.integration.logging_system import LoggerSystem
from src.integration.models import ApplicationState, ImageMetadata, ThemeConfiguration


class TestDataMigrationManager:
    """Test suite for DataMigrationManager"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def migration_manager(self, temp_dir):
        """Create DataMigrationManager instance for testing"""
        logger_system = LoggerSystem()
        error_handler = IntegratedErrorHandler(logger_system)
        validator = DataValidator(logger_system, error_handler)

        return DataMigrationManager(
            data_dir=temp_dir,
            backup_dir=temp_dir / "backups",
            logger_system=logger_system,
            validator=validator,
        )

    @pytest.fixture
    def sample_cursor_image_cache(self, temp_dir):
        """Create sample CursorBLD image cache data"""
        cache_data = [
            {
                "path": str(temp_dir / "image1.jpg"),
                "size": 1024000,
                "thumb_path": str(temp_dir / "thumb1.jpg"),
                "name": "Image 1",
                "created": "2024-01-01 10:00:00",
                "modified": "2024-01-01 10:00:00",
            },
            {
                "path": str(temp_dir / "image2.jpg"),
                "size": 2048000,
                "thumb_path": str(temp_dir / "thumb2.jpg"),
                "name": "Image 2",
                "created": "2024-01-02 11:00:00",
                "modified": "2024-01-02 11:00:00",
            },
        ]

        cache_file = temp_dir / "image_cache.json"
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        return cache_file, cache_data

    @pytest.fixture
    def sample_cursor_theme_data(self, temp_dir):
        """Create sample CursorBLD theme data"""
        theme_data = [
            {
                "theme_name": "dark_theme",
                "display_name": "Dark Theme",
                "colors": {
                    "background": "#2b2b2b",
                    "foreground": "#ffffff",
                    "primary": "#007acc",
                    "secondary": "#6c757d",
                },
                "qt_theme": "dark",
                "stylesheet": "QWidget { background-color: #2b2b2b; }",
            },
            {
                "theme_name": "light_theme",
                "display_name": "Light Theme",
                "colors": {
                    "background": "#ffffff",
                    "foreground": "#000000",
                    "primary": "#007acc",
                    "secondary": "#6c757d",
                },
                "qt_theme": "light",
                "stylesheet": "QWidget { background-color: #ffffff; }",
            },
        ]

        theme_file = temp_dir / "themes.json"
        with open(theme_file, "w") as f:
            json.dump(theme_data, f)

        return theme_file, theme_data

    @pytest.fixture
    def sample_cs4_exif_data(self, temp_dir):
        """Create sample CS4Coding EXIF data"""
        exif_data = [
            {
                "image_path": str(temp_dir / "photo1.jpg"),
                "make": "Canon",
                "model": "EOS R5",
                "lens": "RF 24-70mm F2.8 L IS USM",
                "focal_length": 50.0,
                "f_number": 2.8,
                "exposure_time": "1/125",
                "iso_speed": 400,
                "gps_lat": 35.6762,
                "gps_lon": 139.6503,
                "gps_alt": 10.5,
                "image_width": 8192,
                "image_height": 5464,
            },
            {
                "image_path": str(temp_dir / "photo2.jpg"),
                "make": "Nikon",
                "model": "D850",
                "lens": "NIKKOR 85mm f/1.4G",
                "focal_length": 85.0,
                "f_number": 1.4,
                "exposure_time": "1/200",
                "iso_speed": 800,
                "gps_lat": 40.7128,
                "gps_lon": -74.0060,
                "image_width": 8256,
                "image_height": 5504,
            },
        ]

        exif_file = temp_dir / "exif_data.json"
        with open(exif_file, "w") as f:
            json.dump(exif_data, f)

        return exif_file, exif_data

    @pytest.fixture
    def sample_legacy_database(self, temp_dir):
        """Create sample legacy SQLite database"""
        db_file = temp_dir / "photogeoview.db"

        with sqlite3.connect(db_file) as conn:
            # Create images table
            conn.execute(
                """
                CREATE TABLE images (
                    id INTEGER PRIMARY KEY,
                    path TEXT NOT NULL,
                    size INTEGER,
                    created TEXT,
                    modified TEXT,
                    width INTEGER,
                    height INTEGER,
                    camera_make TEXT,
                    camera_model TEXT,
                    iso INTEGER,
                    aperture REAL,
                    shutter_speed TEXT,
                    latitude REAL,
                    longitude REAL,
                    altitude REAL
                )
            """
            )

            # Insert sample data
            sample_images = [
                (
                    str(temp_dir / "legacy1.jpg"),
                    1500000,
                    "2024-01-01 12:00:00",
                    "2024-01-01 12:00:00",
                    4000,
                    3000,
                    "Sony",
                    "A7R IV",
                    200,
                    4.0,
                    "1/60",
                    51.5074,
                    -0.1278,
                    50.0,
                ),
                (
                    str(temp_dir / "legacy2.jpg"),
                    1800000,
                    "2024-01-02 13:00:00",
                    "2024-01-02 13:00:00",
                    6000,
                    4000,
                    "Fujifilm",
                    "X-T4",
                    400,
                    2.8,
                    "1/125",
                    48.8566,
                    2.3522,
                    35.0,
                ),
            ]

            conn.executemany(
                """
                INSERT INTO images (path, size, created, modified, width, height, camera_make,
                                  camera_model, iso, aperture, shutter_speed, latitude, longitude, altitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                sample_images,
            )

            # Create thumbnails table
            conn.execute(
                """
                CREATE TABLE thumbnails (
                    id INTEGER PRIMARY KEY,
                    image_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    size INTEGER
                )
            """
            )

            # Insert thumbnail data
            thumbnail_data = [
                (
                    str(temp_dir / "legacy1.jpg"),
                    str(temp_dir / "thumb_legacy1.jpg"),
                    150,
                ),
                (
                    str(temp_dir / "legacy2.jpg"),
                    str(temp_dir / "thumb_legacy2.jpg"),
                    150,
                ),
            ]

            conn.executemany(
                """
                INSERT INTO thumbnails (image_path, thumbnail_path, size)
                VALUES (?, ?, ?)
            """,
                thumbnail_data,
            )

        return db_file

    def test_migration_manager_initialization(self, migration_manager):
        """Test DataMigrationManager initialization"""
        assert migration_manager is not None
        assert migration_manager.data_dir.exists()
        assert migration_manager.backup_dir.exists()
        assert migration_manager.migration_mappings is not None
        assert len(migration_manager.migration_mappings) > 0

    def test_migration_mappings_setup(self, migration_manager):
        """Test migration mappings setup"""
        mappings = migration_manager.migration_mappings

        # Check that all expected AI implementations are present
        assert "cursor_bld" in mappings
        assert "cs4_coding" in mappings
        assert "legacy" in mappings

        # Check CursorBLD mappings
        cursor_mappings = mappings["cursor_bld"]
        assert "image_cache" in cursor_mappings
        assert "theme_data" in cursor_mappings
        assert "ui_state" in cursor_mappings

        # Check CS4Coding mappings
        cs4_mappings = mappings["cs4_coding"]
        assert "exif_cache" in cs4_mappings
        assert "map_data" in cs4_mappings

        # Check legacy mappings
        legacy_mappings = mappings["legacy"]
        assert "database" in legacy_mappings
        assert "settings" in legacy_mappings

    def test_migrate_cursor_image_cache(
        self, migration_manager, sample_cursor_image_cache
    ):
        """Test migration of CursorBLD image cache data"""
        cache_file, cache_data = sample_cursor_image_cache

        # Run migration for cursor_bld image_cache
        mapping_config = migration_manager.migration_mappings["cursor_bld"][
            "image_cache"
        ]
        result = migration_manager._migrate_file_data(
            "cursor_bld", "image_cache", mapping_config
        )

        assert isinstance(result, MigrationResult)
        assert result.source_type == "cursor_bld_image_cache"
        assert result.target_model == "ImageMetadata"
        assert result.migrated_count == len(cache_data)

        # Check that backup was created
        backup_files = list(migration_manager.backup_dir.glob("image_cache_*"))
        assert len(backup_files) > 0

    def test_migrate_cursor_theme_data(
        self, migration_manager, sample_cursor_theme_data
    ):
        """Test migration of CursorBLD theme data"""
        theme_file, theme_data = sample_cursor_theme_data

        # Run migration for cursor_bld theme_data
        mapping_config = migration_manager.migration_mappings["cursor_bld"][
            "theme_data"
        ]
        result = migration_manager._migrate_file_data(
            "cursor_bld", "theme_data", mapping_config
        )

        assert isinstance(result, MigrationResult)
        assert result.source_type == "cursor_bld_theme_data"
        assert result.target_model == "ThemeConfiguration"
        assert result.migrated_count == len(theme_data)

    def test_migrate_cs4_exif_data(self, migration_manager, sample_cs4_exif_data):
        """Test migration of CS4Coding EXIF data"""
        exif_file, exif_data = sample_cs4_exif_data

        # Run migration for cs4_coding exif_cache
        mapping_config = migration_manager.migration_mappings["cs4_coding"][
            "exif_cache"
        ]
        result = migration_manager._migrate_file_data(
            "cs4_coding", "exif_cache", mapping_config
        )

        assert isinstance(result, MigrationResult)
        assert result.source_type == "cs4_coding_exif_cache"
        assert result.target_model == "ImageMetadata"
        assert result.migrated_count == len(exif_data)

    def test_migrate_legacy_database(self, migration_manager, sample_legacy_database):
        """Test migration of legacy SQLite database"""
        db_file = sample_legacy_database

        # Run migration for legacy database
        mapping_config = migration_manager.migration_mappings["legacy"]["database"]
        result = migration_manager._migrate_database_data(
            "legacy", "database", mapping_config
        )

        assert isinstance(result, MigrationResult)
        assert result.source_type == "legacy_database"
        assert result.target_model == "ImageMetadata"
        assert result.migrated_count > 0  # Should have migrated some records

    def test_migrate_all_data(
        self, migration_manager, sample_cursor_image_cache, sample_cursor_theme_data
    ):
        """Test migration of all data"""
        cache_file, cache_data = sample_cursor_image_cache
        theme_file, theme_data = sample_cursor_theme_data

        # Run full migration
        migration_summary = migration_manager.migrate_all_data()

        assert isinstance(migration_summary, dict)
        assert "cursor_bld" in migration_summary
        assert "cs4_coding" in migration_summary
        assert "legacy" in migration_summary

        # Check cursor_bld results
        cursor_results = migration_summary["cursor_bld"]
        assert isinstance(cursor_results, list)
        assert len(cursor_results) > 0

        # Check that some migrations were successful
        successful_migrations = [
            r for r in cursor_results if r.status == MigrationStatus.SUCCESS
        ]
        assert len(successful_migrations) > 0

    def test_create_image_metadata(self, migration_manager, temp_dir):
        """Test creation of ImageMetadata from data"""
        test_data = {
            "file_path": str(temp_dir / "test.jpg"),
            "file_size": 1024000,
            "created_date": "2024-01-01 10:00:00",
            "modified_date": "2024-01-01 10:00:00",
            "camera_make": "Canon",
            "camera_model": "EOS R5",
            "latitude": 35.6762,
            "longitude": 139.6503,
            "width": 1920,
            "height": 1080,
        }

        metadata = migration_manager._create_image_metadata(test_data)

        assert isinstance(metadata, ImageMetadata)
        assert metadata.file_path == Path(test_data["file_path"])
        assert metadata.file_size == test_data["file_size"]
        assert metadata.camera_make == test_data["camera_make"]
        assert metadata.camera_model == test_data["camera_model"]
        assert metadata.latitude == test_data["latitude"]
        assert metadata.longitude == test_data["longitude"]
        assert metadata.width == test_data["width"]
        assert metadata.height == test_data["height"]

    def test_create_theme_configuration(self, migration_manager):
        """Test creation of ThemeConfiguration from data"""
        test_data = {
            "name": "test_theme",
            "display_name": "Test Theme",
            "description": "A test theme",
            "version": "1.0.0",
            "color_scheme": {"background": "#ffffff", "foreground": "#000000"},
        }

        theme = migration_manager._create_theme_configuration(test_data)

        assert isinstance(theme, ThemeConfiguration)
        assert theme.name == test_data["name"]
        assert theme.display_name == test_data["display_name"]
        assert theme.description == test_data["description"]
        assert theme.version == test_data["version"]
        assert theme.color_scheme == test_data["color_scheme"]

    def test_create_application_state(self, migration_manager, temp_dir):
        """Test creation of ApplicationState from data"""
        test_folder = temp_dir / "test_folder"
        test_folder.mkdir()

        test_data = {
            "current_folder": str(test_folder),
            "current_theme": "dark",
            "thumbnail_size": 200,
            "performance_mode": "performance",
            "image_sort_mode": "date",
            "image_sort_ascending": False,
        }

        state = migration_manager._create_application_state(test_data)

        assert isinstance(state, ApplicationState)
        assert state.current_folder == test_folder
        assert state.current_theme == test_data["current_theme"]
        assert state.thumbnail_size == test_data["thumbnail_size"]
        assert state.performance_mode == test_data["performance_mode"]
        assert state.image_sort_mode == test_data["image_sort_mode"]
        assert state.image_sort_ascending == test_data["image_sort_ascending"]

    def test_transform_field_value(self, migration_manager):
        """Test field value transformation during migration"""
        # Test path transformation
        path_value = migration_manager._transform_field_value(
            "file_path", "/test/path", "ImageMetadata"
        )
        assert isinstance(path_value, Path)
        assert str(path_value) == "/test/path"

        # Test datetime transformation
        datetime_value = migration_manager._transform_field_value(
            "created_date", "2024-01-01 10:00:00", "ImageMetadata"
        )
        assert isinstance(datetime_value, datetime)

        # Test numeric transformation
        int_value = migration_manager._transform_field_value(
            "file_size", "1024", "ImageMetadata"
        )
        assert isinstance(int_value, int)
        assert int_value == 1024

        float_value = migration_manager._transform_field_value(
            "latitude", "35.6762", "ImageMetadata"
        )
        assert isinstance(float_value, float)
        assert float_value == 35.6762

        # Test boolean transformation
        bool_value = migration_manager._transform_field_value(
            "image_sort_ascending", "true", "ApplicationState"
        )
        assert isinstance(bool_value, bool)
        assert bool_value is True

    def test_parse_datetime(self, migration_manager):
        """Test datetime parsing from various formats"""
        # Test string formats
        dt1 = migration_manager._parse_datetime("2024-01-01 10:00:00")
        assert isinstance(dt1, datetime)
        assert dt1.year == 2024
        assert dt1.month == 1
        assert dt1.day == 1

        dt2 = migration_manager._parse_datetime("2024-01-01T10:00:00")
        assert isinstance(dt2, datetime)

        dt3 = migration_manager._parse_datetime("2024-01-01")
        assert isinstance(dt3, datetime)

        # Test datetime object (should return as-is)
        original_dt = datetime.now()
        dt4 = migration_manager._parse_datetime(original_dt)
        assert dt4 is original_dt

        # Test timestamp
        timestamp = 1704110400  # 2024-01-01 10:00:00 UTC
        dt5 = migration_manager._parse_datetime(timestamp)
        assert isinstance(dt5, datetime)

        # Test invalid format (should return current time)
        dt6 = migration_manager._parse_datetime("invalid_format")
        assert isinstance(dt6, datetime)

    def test_backup_creation(self, migration_manager, temp_dir):
        """Test backup file creation"""
        # Create test file
        test_file = temp_dir / "test_data.json"
        test_data = {"test": "data"}
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        # Create backup
        backup_file = migration_manager._create_backup(test_file)

        assert backup_file.exists()
        assert backup_file.parent == migration_manager.backup_dir
        assert "test_data" in backup_file.name

        # Verify backup content
        with open(backup_file, "r") as f:
            backup_data = json.load(f)
        assert backup_data == test_data

    def test_migration_with_validation_errors(self, migration_manager, temp_dir):
        """Test migration with validation errors"""
        # Create data with validation issues
        invalid_data = [
            {
                "path": "invalid_path",  # Will cause validation issues
                "size": -1,  # Invalid size
                "created": "invalid_date",
                "modified": "invalid_date",
            }
        ]

        cache_file = temp_dir / "invalid_cache.json"
        with open(cache_file, "w") as f:
            json.dump(invalid_data, f)

        # Run migration
        mapping_config = migration_manager.migration_mappings["cursor_bld"][
            "image_cache"
        ]
        result = migration_manager._migrate_file_data(
            "cursor_bld", "image_cache", mapping_config
        )

        # Should have validation results with issues
        assert len(result.validation_results) > 0
        validation_result = result.validation_results[0]
        assert not validation_result.is_valid or len(validation_result.warnings) > 0

    def test_migration_status_tracking(self, migration_manager):
        """Test migration status tracking"""
        status = migration_manager.get_migration_status()

        assert isinstance(status, dict)
        assert "migration_results_count" in status
        assert "backup_directory" in status
        assert "data_directory" in status
        assert "available_migrations" in status

        assert status["backup_directory"] == str(migration_manager.backup_dir)
        assert status["data_directory"] == str(migration_manager.data_dir)
        assert isinstance(status["available_migrations"], list)
        assert len(status["available_migrations"]) > 0

    def test_error_handling_during_migration(self, migration_manager, temp_dir):
        """Test error handling during migration"""
        # Create invalid JSON file
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("invalid json content")

        # Try to migrate invalid file
        mapping_config = {
            "source_files": ["invalid.json"],
            "target_model": "ImageMetadata",
            "field_mappings": {"file_path": "path"},
        }

        result = migration_manager._migrate_file_data("test", "invalid", mapping_config)

        assert isinstance(result, MigrationResult)
        assert result.status == MigrationStatus.FAILED
        assert len(result.errors) > 0
        assert result.migrated_count == 0


class TestMigrationResult:
    """Test suite for MigrationResult"""

    def test_migration_result_creation(self):
        """Test MigrationResult creation"""
        result = MigrationResult(
            source_type="test_source",
            target_model="TestModel",
            status=MigrationStatus.SUCCESS,
            migrated_count=5,
        )

        assert result.source_type == "test_source"
        assert result.target_model == "TestModel"
        assert result.status == MigrationStatus.SUCCESS
        assert result.migrated_count == 5
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.validation_results, list)
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.validation_results) == 0

    def test_migration_result_with_errors(self):
        """Test MigrationResult with errors and warnings"""
        result = MigrationResult(
            source_type="test_source",
            target_model="TestModel",
            status=MigrationStatus.PARTIAL,
            migrated_count=3,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )

        assert result.status == MigrationStatus.PARTIAL
        assert result.migrated_count == 3
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert "Error 1" in result.errors
        assert "Warning 1" in result.warnings


if __name__ == "__main__":
    pytest.main([__file__])
