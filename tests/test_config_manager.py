"""
Test suite for ConfigManager - Task 2 Implementation

Tests the unified configuration management system for AI integration.

Author: Kiro AI Integration System
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.integration.config_manager import ConfigManager
from src.integration.models import AIComponent, ApplicationState
from src.integration.logging_system import LoggerSystem
from src.integration.error_handling import IntegratedErrorHandler


class TestConfigManager:
    """Test suite for ConfigManager"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create ConfigManager insttesting"""
        logger_system = LoggerSystem()
        error_handler = IntegratedErrorHandler(logger_system)

        return ConfigManager(
            config_dir=temp_config_dir,
            logger_system=logger_system,
            error_handler=error_handler,
        )

    def test_config_manager_initialization(self, config_manager):
        """Test ConfigManager initialization"""
        assert config_manager is not None
        assert config_manager.config_data is not None
        assert config_manager.application_state is not None
        assert isinstance(config_manager.application_state, ApplicationState)

    def test_default_configuration_loading(self, config_manager):
        """Test loading of default configuration"""
        # Check that default configuration is loaded
        assert config_manager.get_setting("app.name") == "PhotoGeoView"
        assert config_manager.get_setting("app.version") == "1.0.0"
        assert config_manager.get_setting("ui.theme") == "default"
        assert config_manager.get_setting("ui.thumbnail_size") == 150
        assert config_manager.get_setting("performance.mode") == "balanced"

    def test_ai_specific_configuration(self, config_manager):
        """Test AI-specific configuration management"""
        # Test getting AI configuration
        copilot_config = config_manager.get_ai_config("copilot")
        assert isinstance(copilot_config, dict)

        cursor_config = config_manager.get_ai_config("cursor")
        assert isinstance(cursor_config, dict)

        kiro_config = config_manager.get_ai_config("kiro")
        assert isinstance(kiro_config, dict)

    def test_setting_get_and_set(self, config_manager):
        """Test getting and setting configuration values"""
        # Test setting a value
        assert config_manager.set_setting("ui.thumbnail_size", 200)
        assert config_manager.get_setting("ui.thumbnail_size") == 200

        # Test nested setting
        assert config_manager.set_setting("test.nested.value", "test_value")
        assert config_manager.get_setting("test.nested.value") == "test_value"

        # Test default value
        assert config_manager.get_setting("nonexistent.key", "default") == "default"

    def test_ai_config_update(self, config_manager):
        """Test updating AI-specific configuration"""
        # Update Copilot configuration
        updates = {
            "image_processing": {"high_quality_exif": False, "detailed_metadata": False}
        }

        assert config_manager.update_ai_config("copilot", updates)

        # Verify the update
        copilot_config = config_manager.get_ai_config("copilot")
        assert copilot_config["image_processing"]["high_quality_exif"] is False
        assert copilot_config["image_processing"]["detailed_metadata"] is False

    def test_application_state_management(self, config_manager):
        """Test application state management"""
        # Get initial state
        state = config_manager.get_application_state()
        assert isinstance(state, ApplicationState)
        assert state.current_theme == "default"
        assert state.thumbnail_size == 150

        # Update state
        assert config_manager.update_application_state(
            current_theme="dark", thumbnail_size=200, images_processed=5
        )

        # Verify update
        updated_state = config_manager.get_application_state()
        assert updated_state.current_theme == "dark"
        assert updated_state.thumbnail_size == 200
        assert updated_state.images_processed == 5

    def test_configuration_persistence(self, config_manager, temp_config_dir):
        """Test configuration saving and loading"""
        # Set some configuration values
        config_manager.set_setting("ui.theme", "dark")
        config_manager.set_setting("performance.mode", "performance")

        # Save configuration
        assert config_manager.save_config()

        # Verify files were created
        assert (temp_config_dir / "app_config.json").exists()
        assert (temp_config_dir / "copilot_config.json").exists()
        assert (temp_config_dir / "cursor_config.json").exists()
        assert (temp_config_dir / "kiro_config.json").exists()

        # Create new ConfigManager instance and verify settings persist
        new_config_manager = ConfigManager(config_dir=temp_config_dir)
        assert new_config_manager.get_setting("ui.theme") == "dark"
        assert new_config_manager.get_setting("performance.mode") == "performance"

    def test_application_state_persistence(self, config_manager, temp_config_dir):
        """Test application state saving and loading"""
        # Update application state
        config_manager.update_application_state(
            current_theme="dark", thumbnail_size=200, images_processed=10
        )

        # Save state
        assert config_manager.save_application_state()

        # Verify state file was created
        assert (temp_config_dir / "application_state.json").exists()

        # Create new ConfigManager instance and verify state persists
        new_config_manager = ConfigManager(config_dir=temp_config_dir)
        state = new_config_manager.get_application_state()
        assert state.current_theme == "dark"
        assert state.thumbnail_size == 200
        assert state.images_processed == 10

    def test_configuration_reset(self, config_manager):
        """Test configuration reset to defaults"""
        # Modify configuration
        config_manager.set_setting("ui.theme", "dark")
        config_manager.set_setting("performance.mode", "performance")

        # Reset to defaults
        assert config_manager.reset_to_defaults()

        # Verify reset
        assert config_manager.get_setting("ui.theme") == "default"
        assert config_manager.get_setting("performance.mode") == "balanced"

    def test_application_state_reset(self, config_manager):
        """Test application state reset"""
        # Modify state
        config_manager.update_application_state(
            current_theme="dark", thumbnail_size=200, images_processed=10
        )

        # Reset state
        assert config_manager.reset_application_state()

        # Verify reset
        state = config_manager.get_application_state()
        assert state.current_theme == "default"
        assert state.thumbnail_size == 150
        assert state.images_processed == 0

    def test_configuration_export_import(self, config_manager, temp_config_dir):
        """Test configuration export and import"""
        # Set some configuration values
        config_manager.set_setting("ui.theme", "dark")
        config_manager.update_ai_config("copilot", {"test_setting": "test_value"})

        # Export configuration
        export_file = temp_config_dir / "config_export.json"
        assert config_manager.export_config(export_file)
        assert export_file.exists()

        # Reset configuration
        config_manager.reset_to_defaults()

        # Import configuration
        assert config_manager.import_config(export_file)

        # Verify import
        assert config_manager.get_setting("ui.theme") == "dark"
        copilot_config = config_manager.get_ai_config("copilot")
        assert copilot_config.get("test_setting") == "test_value"

    def test_configuration_validation(self, config_manager):
        """Test configuration validation"""
        # Test valid settings
        assert config_manager.set_setting("ui.thumbnail_size", 200)
        assert config_manager.set_setting("ui.show_toolbar", True)

        # Test invalid type (should be handled gracefully)
        # The validation should prevent invalid types but not crash
        result = config_manager.set_setting("ui.thumbnail_size", "invalid")
        # The result depends on validation implementation

    def test_change_listeners(self, config_manager):
        """Test configuration change listeners"""
        change_events = []

        def change_listener(key, old_value, new_value):
            change_events.append((key, old_value, new_value))

        # Add change listener
        config_manager.add_change_listener(change_listener)

        # Make changes
        config_manager.set_setting("ui.theme", "dark")

        # Verify listener was called
        assert len(change_events) > 0
        assert change_events[-1][0] == "ui.theme"
        assert change_events[-1][2] == "dark"

        # Remove listener
        config_manager.remove_change_listener(change_listener)

    def test_config_summary(self, config_manager):
        """Test configuration summary"""
        summary = config_manager.get_config_summary()

        assert "total_settings" in summary
        assert "ai_configs" in summary
        assert "last_modified" in summary
        assert "config_files" in summary

        assert isinstance(summary["total_settings"], int)
        assert isinstance(summary["ai_configs"], dict)

    def test_state_summary(self, config_manager):
        """Test application state summary"""
        # Update some state
        config_manager.update_application_state(
            current_theme="dark", images_processed=5
        )

        summary = config_manager.get_state_summary()

        assert "current_theme" in summary
        assert "images_processed" in summary
        assert "session_duration" in summary
        assert "ai_component_status" in summary

        assert summary["current_theme"] == "dark"
        assert summary["images_processed"] == 5

    def test_error_handling(self, config_manager, temp_config_dir):
        """Test error handling in configuration operations"""
        # Test with invalid AI component name
        result = config_manager.get_ai_config("invalid_ai")
        assert result == {}

        # Test setting with invalid key format
        # Should handle gracefully without crashing
        config_manager.set_setting("", "value")

        # Test loading from non-existent file
        # Should handle gracefully
        config_manager.load_config()

    def test_migration_integration(self, config_manager, temp_config_dir):
        """Test configuration migration integration"""
        # Create some legacy configuration files
        legacy_config = {
            "app_name": "PhotoGeoView",
            "debug_mode": True,
            "current_theme": "dark",
        }

        legacy_file = temp_config_dir / "photogeoview_config.json"
        with open(legacy_file, "w") as f:
            json.dump(legacy_config, f)

        # Test migration detection
        assert config_manager.has_legacy_configurations()

        # Test migration execution
        migration_result = config_manager.migrate_existing_configurations()
        assert isinstance(migration_result, dict)
        assert "status" in migration_result


class TestConfigMigrationManager:
    """Test suite for ConfigMigrationManager"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_migration_mappings_setup(self, temp_config_dir):
        """Test migration mappings setup"""
        from src.integration.config_migration import ConfigMigrationManager

        migration_manager = ConfigMigrationManager(config_dir=temp_config_dir)

        assert "cursor_bld" in migration_manager.migration_mappings
        assert "cs4_coding" in migration_manager.migration_mappings
        assert "kiro" in migration_manager.migration_mappings
        assert "legacy" in migration_manager.migration_mappings

    def test_setting_transformation(self, temp_config_dir):
        """Test setting value transformation during migration"""
        from src.integration.config_migration import ConfigMigrationManager

        migration_manager = ConfigMigrationManager(config_dir=temp_config_dir)

        # Test path transformation
        result = migration_manager._transform_setting_value(
            "current_folder", "/test/path"
        )
        assert isinstance(result, str)

        # Test boolean transformation
        result = migration_manager._transform_setting_value("debug_mode", "true")
        assert result is True

        result = migration_manager._transform_setting_value("debug_mode", "false")
        assert result is False

        # Test numeric range validation
        result = migration_manager._transform_setting_value("thumbnail_size", 1000)
        assert result == 500  # Should be clamped to max

        result = migration_manager._transform_setting_value("thumbnail_size", 10)
        assert result == 50  # Should be clamped to min

    def test_nested_value_setting(self, temp_config_dir):
        """Test nested configuration value setting"""
        from src.integration.config_migration import ConfigMigrationManager

        migration_manager = ConfigMigrationManager(config_dir=temp_config_dir)

        config = {}
        migration_manager._set_nested_value(config, "ui.theme.name", "dark")

        assert config["ui"]["theme"]["name"] == "dark"

    def test_backup_creation(self, temp_config_dir):
        """Test backup file creation during migration"""
        from src.integration.config_migration import ConfigMigrationManager

        migration_manager = ConfigMigrationManager(config_dir=temp_config_dir)

        # Create a test file
        test_file = temp_config_dir / "test_config.json"
        test_file.write_text('{"test": "value"}')

        # Create backup
        backup_file = migration_manager._create_backup(test_file)

        assert backup_file.exists()
        assert backup_file.parent == migration_manager.backup_dir
        assert "test_config" in backup_file.name


if __name__ == "__main__":
    pytest.main([__file__])
