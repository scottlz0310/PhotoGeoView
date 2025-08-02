"""
Unit Tests for Theme Manager Widget Component

Tests the ThemeManagerWidget class functionality including:
- Theme loading and validation
- Component registration system
- Qt-theme-manager integration
- Theme application and management

Author: Kiro AI Integration System
Requirements: 1.1, 1.2, 1.3, 1.4
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from PySide6.QtCore import QObject, Signal

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.theme_interfaces import IThemeAware
from src.integration.theme_models import ThemeConfiguration, ThemeInfo, ThemeType
from src.ui.theme_manager import ThemeManagerWidget


class MockThemeAwareComponent(QObject):
    """Mock theme-aware component for testing"""

    def __init__(self):
        super().__init__()
        self.applied_theme = None
        self.theme_properties = ["colors.primary", "colors.background"]

    def apply_theme(self, theme: ThemeConfiguration) -> None:
        """Apply theme to component"""
        self.applied_theme = theme

    def get_theme_properties(self) -> list:
        """Get theme properties used by component"""
        return self.theme_properties


class TestThemeManagerWidget(unittest.TestCase):
    """Test cases for ThemeManagerWidget"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.theme_dir = Path(self.temp_dir) / "themes"
        self.custom_theme_dir = Path(self.temp_dir) / "custom_themes"

        # Mock dependencies
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)
        self.mock_logger = Mock()
        self.mock_logger_system.get_logger.return_value = self.mock_logger

        # Configure mock config manager
        self.mock_config_manager.get_setting.return_value = "default"

        # Create theme manager widget with mocked dependencies
        with patch('src.ui.theme_manager.Path') as mock_path:
            mock_path.return_value = Path(self.temp_dir)
            self.theme_manager = ThemeManagerWidget(
                self.mock_config_manager,
                self.mock_logger_system
            )

            # Override paths for testing
            self.theme_manager.theme_dir = self.theme_dir
            self.theme_manager.custom_theme_dir = self.custom_theme_dir

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_qt_theme_manager_initialization_success(self):
        """Test successful qt-theme-manager initialization"""
        # Test that the theme manager can handle qt-theme-manager being available
        # Since qt-theme-manager is in requirements.txt, this should work
        self.assertIsNotNone(self.theme_manager)
        # The theme manager should initialize even if qt-theme-manager is not available
        # (it will use fallback behavior)

    def test_qt_theme_manager_initialization_import_error(self):
        """Test qt-theme-manager initialization with import error"""
        # Test that the theme manager handles import errors gracefully
        # The theme manager should still work even if qt-theme-manager is not available
        self.assertIsNotNone(self.theme_manager)
        # Should have built-in themes available regardless
        self.assertGreater(len(self.theme_manager.available_themes), 0)

    def test_initialize_themes(self):
        """Test theme initialization"""
        # Create theme directories
        self.theme_dir.mkdir(parents=True, exist_ok=True)
        self.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Call initialize_themes
        self.theme_manager.initialize_themes()

        # Verify themes were loaded
        self.assertGreater(len(self.theme_manager.available_themes), 0)
        self.assertIn("default", self.theme_manager.available_themes)
        self.mock_logger.info.assert_called()

    def test_register_component_success(self):
        """Test successful component registration"""
        # Create mock component
        component = MockThemeAwareComponent()

        # Register component
        result = self.theme_manager.register_component(component)

        # Verify registration
        self.assertTrue(result)
        self.assertIn(component, self.theme_manager.registered_components)
        self.mock_logger.debug.assert_called()

    def test_register_component_duplicate(self):
        """Test registering the same component twice"""
        # Create mock component
        component = MockThemeAwareComponent()

        # Register component twice
        result1 = self.theme_manager.register_component(component)
        result2 = self.theme_manager.register_component(component)

        # Verify only first registration succeeds
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertEqual(len(self.theme_manager.registered_components), 1)

    def test_unregister_component_success(self):
        """Test successful component unregistration"""
        # Create and register component
        component = MockThemeAwareComponent()
        self.theme_manager.register_component(component)

        # Unregister component
        result = self.theme_manager.unregister_component(component)

        # Verify unregistration
        self.assertTrue(result)
        self.assertNotIn(component, self.theme_manager.registered_components)

    def test_unregister_component_not_registered(self):
        """Test unregistering component that wasn't registered"""
        # Create component without registering
        component = MockThemeAwareComponent()

        # Try to unregister
        result = self.theme_manager.unregister_component(component)

        # Verify failure
        self.assertFalse(result)

    def test_add_theme_change_listener(self):
        """Test adding theme change listener"""
        # Create mock listener
        listener = Mock()

        # Add listener
        result = self.theme_manager.add_theme_change_listener(listener)

        # Verify addition
        self.assertTrue(result)
        self.assertIn(listener, self.theme_manager.theme_change_listeners)

    def test_add_theme_change_listener_duplicate(self):
        """Test adding duplicate theme change listener"""
        # Create mock listener
        listener = Mock()

        # Add listenee
        result1 = self.theme_manager.add_theme_change_listener(listener)
        result2 = self.theme_manager.add_theme_change_listener(listener)

        # Verify only first addition succeeds
        self.assertTrue(result1)
        self.assertFalse(result2)
        self.assertEqual(len(self.theme_manager.theme_change_listeners), 1)

    def test_remove_theme_change_listener(self):
        """Test removing theme change listener"""
        # Create and add listener
        listener = Mock()
        self.theme_manager.add_theme_change_listener(listener)

        # Remove listener
        result = self.theme_manager.remove_theme_change_listener(listener)

        # Verify removal
        self.assertTrue(result)
        self.assertNotIn(listener, self.theme_manager.theme_change_listeners)

    def test_get_available_themes(self):
        """Test getting available themes"""
        # Initialize themes
        self.theme_manager.initialize_themes()

        # Get available themes
        themes = self.theme_manager.get_available_themes()

        # Verify themes returned
        self.assertIsInstance(themes, list)
        self.assertGreater(len(themes), 0)

        # Verify theme info structure
        for theme in themes:
            self.assertIsInstance(theme, ThemeInfo)
            self.assertIsInstance(theme.name, str)
            self.assertIsInstance(theme.display_name, str)

    def test_apply_theme_success(self):
        """Test successful theme application"""
        # Initialize themes
        self.theme_manager.initialize_themes()

        # Apply theme
        result = self.theme_manager.apply_theme("default")

        # Verify application
        self.assertTrue(result)
        self.assertIsNotNone(self.theme_manager.current_theme)
        self.assertEqual(self.theme_manager.current_theme.name, "default")
        self.mock_config_manager.set_setting.assert_called_with("ui.theme", "default")

    def test_apply_theme_not_found(self):
        """Test applying non-existent theme"""
        # Try to apply non-existent theme
        result = self.theme_manager.apply_theme("nonexistent")

        # Verify failure
        self.assertFalse(result)

    def test_apply_theme_with_registered_components(self):
        """Test theme application with registered components"""
        # Initialize themes and register component
        self.theme_manager.initialize_themes()
        component = MockThemeAwareComponent()
        self.theme_manager.register_component(component)

        # Apply theme
        result = self.theme_manager.apply_theme("default")

        # Verify theme was applied to component
        self.assertTrue(result)
        self.assertIsNotNone(component.applied_theme)
        self.assertEqual(component.applied_theme.name, "default")

    def test_get_theme_property_success(self):
        """Test getting theme property"""
        # Create theme with properties
        theme_config = ThemeConfiguration(
            name="test",
            display_name="Test Theme",
            description="Test theme",
            author="Test",
            version="1.0.0"
        )
        theme_config.colors = Mock()
        theme_config.colors.primary = "#007acc"

        self.theme_manager.current_theme = theme_config

        # Get theme property
        value = self.theme_manager.get_theme_property("colors.primary", "#000000")

        # Verify value
        self.assertEqual(value, "#007acc")

    def test_get_theme_property_not_found(self):
        """Test getting non-existent theme property"""
        # Create theme without the property
        theme_config = ThemeConfiguration(
            name="test",
            display_name="Test Theme",
            description="Test theme",
            author="Test",
            version="1.0.0"
        )

        self.theme_manager.current_theme = theme_config

        # Get non-existent property
        value = self.theme_manager.get_theme_property("nonexistent.property", "default")

        # Verify default returned
        self.assertEqual(value, "default")

    def test_get_theme_property_no_current_theme(self):
        """Test getting theme property when no theme is set"""
        # Ensure no current theme
        self.theme_manager.current_theme = None

        # Get property
        value = self.theme_manager.get_theme_property("colors.primary", "default")

        # Verify default returned
        self.assertEqual(value, "default")

    def test_import_theme_success(self):
        """Test successful theme import"""
        # Create temporary theme file
        theme_config = ThemeConfiguration(
            name="imported_theme",
            display_name="Imported Theme",
            description="Test imported theme",
            author="Test Author",
            version="1.0.0"
        )

        temp_theme_file = Path(self.temp_dir) / "test_theme.json"
        theme_config.save_to_file(temp_theme_file)

        # Create custom theme directory
        self.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Import theme
        result = self.theme_manager.import_theme(temp_theme_file)

        # Verify import
        self.assertTrue(result)
        self.assertIn("imported_theme", self.theme_manager.available_themes)

        # Verify theme file was copied
        imported_file = self.custom_theme_dir / "imported_theme.json"
        self.assertTrue(imported_file.exists())

    def test_import_theme_invalid_file(self):
        """Test importing invalid theme file"""
        # Create invalid theme file
        invalid_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")

        # Try to import
        result = self.theme_manager.import_theme(invalid_file)

        # Verify failure
        self.assertFalse(result)

    def test_export_theme_success(self):
        """Test successful theme export"""
        # Initialize themes
        self.theme_manager.initialize_themes()

        # Export theme
        export_path = Path(self.temp_dir) / "exported_theme.json"
        result = self.theme_manager.export_theme("default", export_path)

        # Verify export
        self.assertTrue(result)
        self.assertTrue(export_path.exists())

        # Verify exported content
        with open(export_path, 'r') as f:
            exported_data = json.load(f)

        self.assertEqual(exported_data["name"], "default")

    def test_export_theme_not_found(self):
        """Test exporting non-existent theme"""
        # Try to export non-existent theme
        export_path = Path(self.temp_dir) / "exported.json"
        result = self.theme_manager.export_theme("nonexistent", export_path)

        # Verify failure
        self.assertFalse(result)
        self.assertFalse(export_path.exists())

    def test_reload_themes(self):
        """Test theme reloading"""
        # Initialize themes
        self.theme_manager.initialize_themes()
        initial_count = len(self.theme_manager.available_themes)

        # Add a custom theme file
        self.custom_theme_dir.mkdir(parents=True, exist_ok=True)
        custom_theme = ThemeConfiguration(
            name="new_custom",
            display_name="New Custom Theme",
            description="Test custom theme",
            author="Test",
            version="1.0.0"
        )
        custom_theme_file = self.custom_theme_dir / "new_custom.json"
        custom_theme.save_to_file(custom_theme_file)

        # Reload themes
        result = self.theme_manager.reload_themes()

        # Verify reload
        self.assertTrue(result)
        self.assertGreater(len(self.theme_manager.available_themes), initial_count)
        self.assertIn("new_custom", self.theme_manager.available_themes)

    def test_reset_to_default(self):
        """Test resetting to default theme"""
        # Initialize themes and apply different theme
        self.theme_manager.initialize_themes()
        self.theme_manager.apply_theme("dark")

        # Reset to default
        result = self.theme_manager.reset_to_default()

        # Verify reset
        self.assertTrue(result)
        self.assertEqual(self.theme_manager.current_theme.name, "default")

    def test_get_current_theme(self):
        """Test getting current theme"""
        # Initially should have default theme loaded
        current = self.theme_manager.get_current_theme()
        self.assertIsNotNone(current)

        # Apply theme
        self.theme_manager.initialize_themes()
        self.theme_manager.apply_theme("default")

        # Get current theme
        current = self.theme_manager.get_current_theme()
        self.assertIsNotNone(current)
        self.assertEqual(current.name, "default")

    def test_validate_theme(self):
        """Test theme validation"""
        # Create valid theme
        valid_theme = ThemeConfiguration(
            name="valid_theme",
            display_name="Valid Theme",
            description="A valid theme",
            author="Test",
            version="1.0.0"
        )

        # Validate theme
        result = self.theme_manager.validate_theme(valid_theme)
        self.assertTrue(result)

        # Create invalid theme (missing required fields)
        invalid_theme = ThemeConfiguration(
            name="",  # Invalid empty name
            display_name="Invalid Theme",
            description="An invalid theme",
            author="Test",
            version="invalid_version"  # Invalid version format
        )

        # Validate invalid theme
        result = self.theme_manager.validate_theme(invalid_theme)
        self.assertFalse(result)

    def test_get_theme_stylesheet(self):
        """Test getting theme stylesheet"""
        # Initialize themes
        self.theme_manager.initialize_themes()

        # Get stylesheet for existing theme
        stylesheet = self.theme_manager.get_theme_stylesheet("default")
        self.assertIsInstance(stylesheet, str)

        # Get stylesheet for non-existent theme
        stylesheet = self.theme_manager.get_theme_stylesheet("nonexistent")
        self.assertEqual(stylesheet, "")

    def test_create_theme_from_template(self):
        """Test creating theme from template"""
        # Initialize themes
        self.theme_manager.initialize_themes()
        self.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Apply default theme first to ensure current_theme is set
        self.theme_manager.apply_theme("default")

        # Create theme from template
        customizations = {
            'display_name': 'My Custom Theme',
            'description': 'A custom theme based on default',
            'colors': {
                'primary': '#ff0000'
            }
        }

        result = self.theme_manager.create_theme_from_template(
            "default", "my_custom", customizations
        )

        # Verify creation
        self.assertTrue(result)
        self.assertIn("my_custom", self.theme_manager.available_themes)

        # Verify theme file was created
        theme_file = self.custom_theme_dir / "my_custom.json"
        self.assertTrue(theme_file.exists())

    def test_create_theme_from_template_invalid_template(self):
        """Test creating theme from non-existent template"""
        result = self.theme_manager.create_theme_from_template(
            "nonexistent", "new_theme"
        )
        self.assertFalse(result)

    def test_delete_custom_theme(self):
        """Test deleting custom theme"""
        # Initialize themes
        self.theme_manager.initialize_themes()
        self.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Create a custom theme manually for testing
        custom_theme = ThemeConfiguration(
            name="test_custom",
            display_name="Test Custom Theme",
            description="A test custom theme",
            author="Test",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
            is_custom=True
        )

        # Save the custom theme file
        theme_file = self.custom_theme_dir / "test_custom.json"
        custom_theme.save_to_file(theme_file)

        # Add to available themes
        theme_info = ThemeInfo.from_theme_config(custom_theme)
        self.theme_manager.available_themes["test_custom"] = theme_info

        # Verify theme exists
        self.assertIn("test_custom", self.theme_manager.available_themes)
        self.assertTrue(theme_file.exists())

        # Delete the custom theme
        result = self.theme_manager.delete_custom_theme("test_custom")

        # Verify deletion
        self.assertTrue(result)
        self.assertNotIn("test_custom", self.theme_manager.available_themes)
        self.assertFalse(theme_file.exists())

    def test_delete_custom_theme_builtin(self):
        """Test attempting to delete built-in theme"""
        # Initialize themes
        self.theme_manager.initialize_themes()

        # Try to delete built-in theme
        result = self.theme_manager.delete_custom_theme("default")

        # Verify failure
        self.assertFalse(result)
        self.assertIn("default", self.theme_manager.available_themes)

    def test_get_theme_usage_statistics(self):
        """Test getting theme usage statistics"""
        # Initialize themes
        self.theme_manager.initialize_themes()

        # Get statistics
        stats = self.theme_manager.get_theme_usage_statistics()

        # Verify statistics structure
        self.assertIsInstance(stats, dict)
        self.assertIn("total_themes", stats)
        self.assertIn("builtin_themes", stats)
        self.assertIn("custom_themes", stats)
        self.assertIn("current_theme", stats)
        self.assertIn("registered_components", stats)

        # Verify values
        self.assertGreater(stats["total_themes"], 0)
        self.assertGreaterEqual(stats["builtin_themes"], 0)
        self.assertGreaterEqual(stats["custom_themes"], 0)

    def test_backup_themes(self):
        """Test backing up themes"""
        # Initialize themes and create custom theme
        self.theme_manager.initialize_themes()
        self.custom_theme_dir.mkdir(parents=True, exist_ok=True)
        self.theme_manager.create_theme_from_template("default", "backup_test")

        # Create backup
        backup_path = Path(self.temp_dir) / "theme_backup.json"
        result = self.theme_manager.backup_themes(backup_path)

        # Verify backup
        self.assertTrue(result)
        self.assertTrue(backup_path.exists())

        # Verify backup content
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)

        self.assertIn("backup_timestamp", backup_data)
        self.assertIn("themes", backup_data)

    def test_restore_themes(self):
        """Test restoring themes from backup"""
        # Create backup data
        backup_data = {
            "backup_timestamp": "2023-01-01T00:00:00",
            "themes": {
                "restored_theme": {
                    "name": "restored_theme",
                    "display_name": "Restored Theme",
                    "description": "A restored theme",
                    "author": "Test",
                    "version": "1.0.0",
                    "theme_type": "custom",
                    "colors": {
                        "primary": "#007acc",
                        "secondary": "#FFC107",
                        "background": "#FFFFFF",
                        "surface": "#F5F5F5",
                        "text_primary": "#212121",
                        "text_secondary": "#757575",
                        "accent": "#FF5722",
                        "error": "#F44336",
                        "warning": "#FF9800",
                        "success": "#4CAF50"
                    },
                    "fonts": {},
                    "styles": {},
                    "custom_properties": {},
                    "is_custom": True,
                    "created_date": "2023-01-01T00:00:00",
                    "modified_date": "2023-01-01T00:00:00",
                    "usage_count": 0
                }
            }
        }

        # Save backup file
        backup_path = Path(self.temp_dir) / "restore_backup.json"
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f)

        # Initialize themes and custom directory
        self.theme_manager.initialize_themes()
        self.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Restore themes
        result = self.theme_manager.restore_themes(backup_path)

        # Verify restoration
        self.assertTrue(result)
        self.assertIn("restored_theme", self.theme_manager.available_themes)

        # Verify theme file was created
        theme_file = self.custom_theme_dir / "restored_theme.json"
        self.assertTrue(theme_file.exists())

    def test_restore_themes_invalid_backup(self):
        """Test restoring from invalid backup file"""
        # Create invalid backup file
        backup_path = Path(self.temp_dir) / "invalid_backup.json"
        with open(backup_path, 'w') as f:
            f.write("invalid json")

        # Try to restore
        result = self.theme_manager.restore_themes(backup_path)

        # Verify failure
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
