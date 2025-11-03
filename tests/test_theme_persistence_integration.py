"""
Theme Persistence Integration Tests

Tests for theme persistence across application restarts, configuration management,
and state restoration.

Author: Kiro AI Integration System
Requirements: 1.2, 1.3, 4.1
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.theme_integration_controller import ThemeIntegrationController
from src.integration.theme_models import ThemeConfiguration, ThemeType


class TestThemePersistenceIntegration:
    """Test theme persistence across application lifecycle"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create configuration manager with temporary directory"""
        config_manager = ConfigManager()
        config_manager.config_dir = temp_config_dir
        config_manager.config_file = temp_config_dir / "config.json"
        return config_manager

    @pytest.fixture
    def logger_system(self):
        """Create logger system"""
        return LoggerSystem()

    @pytest.fixture
    def theme_controller(self, config_manager, logger_system):
        """Create theme integration controller"""
        return ThemeIntegrationController(
            config_manager=config_manager, logger_system=logger_system
        )

    def test_theme_configuration_save(self, theme_controller, config_manager):
        """Test saving theme configuration to file"""
        # Create test theme configuration
        theme_config = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="Theme for testing persistence",
            author="Test Author",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
        )

        # Set current theme
        theme_controller.current_theme = theme_config

        # Save configuration
        theme_controller._save_theme_to_config()

        # Verify theme was saved
        saved_theme = config_manager.get_setting("ui.theme")
        assert saved_theme == "test_theme"

        # Verify theme details were saved
        theme_details = config_manager.get_setting("ui.theme_details", {})
        assert theme_details.get("name") == "test_theme"
        assert theme_details.get("display_name") == "Test Theme"

    def test_theme_configuration_load(self, theme_controller, config_manager):
        """Test loading theme configuration from file"""
        # Setup saved theme configuration
        config_maer.set_setting("ui.theme", "saved_theme")
        config_manager.set_setting(
            "ui.theme_details",
            {
                "name": "saved_theme",
                "display_name": "Saved Theme",
                "description": "Previously saved theme",
                "author": "Previous User",
                "version": "1.0.0",
                "theme_type": "custom",
            },
        )

        # Load theme configuration
        loaded_theme = theme_controller._load_theme_from_config()

        # Verify theme was loaded correctly
        assert loaded_theme == "saved_theme"

    @pytest.mark.asyncio
    async def test_theme_restoration_on_startup(self, theme_controller, config_manager):
        """Test theme restoration during application startup"""
        # Setup saved theme
        config_manager.set_setting("ui.theme", "startup_theme")
        config_manager.set_setting("ui.theme_persistence", True)

        # Create mock theme manager
        mock_theme_manager = Mock()
        mock_theme_manager.apply_theme = Mock(return_value=True)
        mock_theme_manager.get_current_theme = Mock(
            return_value=ThemeConfiguration(
                name="startup_theme",
                display_name="Startup Theme",
                description="Theme restored on startup",
                author="System",
                version="1.0.0",
            )
        )
        theme_controller.register_theme_manager("startup_manager", mock_theme_manager)

        # Restore theme on startup
        result = await theme_controller.restore_theme_on_startup()

        # Verify restoration
        assert result is True
        mock_theme_manager.apply_theme.assert_called_with("startup_theme")
        assert theme_controller.current_theme.name == "startup_theme"

    def test_theme_persistence_disabled(self, theme_controller, config_manager):
        """Test behavior when theme persistence is disabled"""
        # Disable theme persistence
        config_manager.set_setting("ui.theme_persistence", False)

        # Create test theme
        theme_config = ThemeConfiguration(
            name="temp_theme",
            display_name="Temporary Theme",
            description="Non-persistent theme",
            author="Test",
            version="1.0.0",
        )
        theme_controller.current_theme = theme_config

        # Try to save theme
        theme_controller._save_theme_to_config()

        # Theme should not be saved when persistence is disabled
        saved_theme = config_manager.get_setting("ui.theme")
        assert saved_theme != "temp_theme" or saved_theme is None

    def test_theme_history_tracking(self, theme_controller, config_manager):
        """Test theme change history tracking"""
        # Enable theme history
        config_manager.set_setting("ui.theme_history_enabled", True)
        config_manager.set_setting("ui.theme_history_max_size", 10)

        # Apply multiple themes
        themes = ["theme1", "theme2", "theme3"]
        for theme_name in themes:
            theme_controller._add_to_theme_history(theme_name)

        # Verify history was tracked
        history = theme_controller.get_theme_history()
        assert len(history) == 3
        assert all(entry["theme_name"] in themes for entry in history)

    def test_theme_history_size_limit(self, theme_controller, config_manager):
        """Test theme history size limitation"""
        # Set small history limit
        config_manager.set_setting("ui.theme_history_enabled", True)
        config_manager.set_setting("ui.theme_history_max_size", 2)

        # Add more themes than the limit
        themes = ["theme1", "theme2", "theme3", "theme4"]
        for theme_name in themes:
            theme_controller._add_to_theme_history(theme_name)

        # Verify history respects size limit
        history = theme_controller.get_theme_history()
        assert len(history) <= 2
        # Should keep most recent entries
        assert history[-1]["theme_name"] == "theme4"
        assert history[-2]["theme_name"] == "theme3"

    def test_configuration_file_corruption_handling(
        self, theme_controller, config_manager, temp_config_dir
    ):
        """Test handling of corrupted configuration files"""
        # Create corrupted config file
        config_file = temp_config_dir / "config.json"
        config_file.write_text("invalid json content {")

        # Try to load theme configuration
        with patch.object(config_manager, "handle_config_error") as mock_error_handler:
            loaded_theme = theme_controller._load_theme_from_config()

            # Should handle corruption gracefully
            assert loaded_theme == "default"  # Fallback theme

    def test_theme_backup_and_restore(
        self, theme_controller, config_manager, temp_config_dir
    ):
        """Test theme configuration backup and restore"""
        # Create theme configuration
        theme_config = {
            "ui.theme": "backup_theme",
            "ui.theme_details": {
                "name": "backup_theme",
                "display_name": "Backup Theme",
                "description": "Theme for backup testing",
            },
        }

        # Save configuration
        for key, value in theme_config.items():
            config_manager.set_setting(key, value)

        # Create backup
        backup_file = temp_config_dir / "theme_backup.json"
        theme_controller._create_theme_backup(backup_file)

        # Verify backup was created
        assert backup_file.exists()

        # Clear current configuration
        config_manager.set_setting("ui.theme", "default")

        # Restore from backup
        theme_controller._restore_theme_backup(backup_file)

        # Verify restoration
        restored_theme = config_manager.get_setting("ui.theme")
        assert restored_theme == "backup_theme"

    @pytest.mark.asyncio
    async def test_concurrent_theme_persistence(self, theme_controller, config_manager):
        """Test theme persistence under concurrent access"""
        import asyncio

        # Create multiple theme save operations
        async def save_theme(theme_name):
            theme_config = ThemeConfiguration(
                name=theme_name,
                display_name=f"Theme {theme_name}",
                description=f"Concurrent theme {theme_name}",
                author="Test",
                version="1.0.0",
            )
            theme_controller.current_theme = theme_config
            theme_controller._save_theme_to_config()

        # Run concurrent saves
        tasks = [save_theme(f"theme_{i}") for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify final state is consistent
        final_theme = config_manager.get_setting("ui.theme")
        assert final_theme is not None
        assert final_theme.startswith("theme_")

    def test_theme_migration_between_versions(self, theme_controller, config_manager):
        """Test theme configuration migration between application versions"""
        # Setup old version configuration format
        old_config = {
            "theme_name": "old_theme",
            "theme_style": "dark",
            "custom_colors": {"primary": "#000000"},
        }
        config_manager.set_setting("ui.legacy_theme", old_config)

        # Perform migration
        theme_controller._migrate_theme_configuration()

        # Verify migration to new format
        new_theme = config_manager.get_setting("ui.theme")
        theme_details = config_manager.get_setting("ui.theme_details", {})

        assert new_theme == "old_theme"
        assert theme_details.get("name") == "old_theme"

    def test_theme_export_import(
        self, theme_controller, config_manager, temp_config_dir
    ):
        """Test theme configuration export and import"""
        # Create theme configuration
        theme_config = ThemeConfiguration(
            name="export_theme",
            display_name="Export Theme",
            description="Theme for export testing",
            author="Export User",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
        )
        theme_controller.current_theme = theme_config

        # Export theme
        export_file = temp_config_dir / "exported_theme.json"
        theme_controller._export_theme_configuration(export_file)

        # Verify export file was created
        assert export_file.exists()

        # Clear current theme
        theme_controller.current_theme = None

        # Import theme
        imported_theme = theme_controller._import_theme_configuration(export_file)

        # Verify import
        assert imported_theme is not None
        assert imported_theme.name == "export_theme"
        assert imported_theme.display_name == "Export Theme"

    def test_theme_persistence_with_user_preferences(
        self, theme_controller, config_manager
    ):
        """Test theme persistence with user-specific preferences"""
        # Setup user preferences
        user_prefs = {
            "auto_dark_mode": True,
            "follow_system_theme": False,
            "custom_accent_color": "#3498db",
            "font_scaling": 1.2,
        }

        for key, value in user_prefs.items():
            config_manager.set_setting(f"ui.user_prefs.{key}", value)

        # Apply theme with user preferences
        theme_config = ThemeConfiguration(
            name="user_theme",
            display_name="User Theme",
            description="Theme with user preferences",
            author="User",
            version="1.0.0",
        )
        theme_controller.current_theme = theme_config
        theme_controller._save_theme_with_preferences()

        # Verify preferences were saved with theme
        saved_prefs = config_manager.get_setting("ui.theme_user_prefs", {})
        assert saved_prefs.get("auto_dark_mode") is True
        assert saved_prefs.get("custom_accent_color") == "#3498db"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
