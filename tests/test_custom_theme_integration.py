"""
Integration Test for Custom Theme Functionality

Simple integration test to verify the custom theme functionality works end-to-end.
Tests the main requirements for task 6 of the qt-theme-breadcrumb spec.

Author: Kiro AI Integration System
Requirements: 3.1, 3.2, 3.3, 3.4
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.theme_models import ThemeConfiguration, ColorScheme, FontConfig, ThemeType
from src.ui.theme_manager import ThemeManagerWidget


class TestCustomThemeIntegration(unittest.TestCase):
    """Integration test for custom theme functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Mock dependencies
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)
        self.mock_logger = Mock()
        self.mock_logger_system.get_logger.return_value = self.mock_logger

        # Create theme manager with mocked paths
        with patch('src.ui.theme_manager.Path') as mock_path:
            mock_path.return_value.mkdir = Mock()
            mock_path.return_value.glob = Mock(return_value=[])

            self.theme_manager = ThemeManagerWidget(
                self.mock_config_manager,
                self.mock_logger_system
            )

            # Set up real temp directories for testing
            self.theme_manager.theme_dir = self.temp_dir / "themes"
            self.theme_manager.custom_theme_dir = self.temp_dir / "custom_themes"
            self.theme_manager.theme_dir.mkdir(parents=True, exist_ok=True)
            self.theme_manager.custom_theme_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_custom_theme_workflow(self):
        """Test complete custom theme workflow: create, save, import, export"""

        # Step 1: Create a custom theme
        custom_theme = ThemeConfiguration(
            name="integration_test_theme",
            display_name="Integration Test Theme",
            description="A theme created for integration testing",
            author="Test Suite",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
            colors=ColorScheme(
                primary="#007ACC",
                secondary="#FFA500",
                background="#FFFFFF",
                surface="#F5F5F5",
                text_primary="#000000",
                text_secondary="#666666",
                accent="#FF5722",
                error="#F44336",
                warning="#FF9800",
                success="#4CAF50"
            ),
            fonts={
                "default": FontConfig("Arial", 12),
                "heading": FontConfig("Arial", 16, "bold"),
                "small": FontConfig("Arial", 10),
                "monospace": FontConfig("Courier New", 12)
            },
            is_custom=True
        )

        # Step 2: Validate the theme
        self.assertTrue(custom_theme.validate(),
                       f"Theme validation failed: {custom_theme.validation_errors}")

        # Step 3: Save theme to file
        theme_file = self.theme_manager.custom_theme_dir / "integration_test_theme.json"
        self.assertTrue(custom_theme.save_to_file(theme_file))
        self.assertTrue(theme_file.exists())

        # Step 4: Import the theme using theme manager
        result = self.theme_manager.import_theme(theme_file)
        self.assertTrue(result)
        self.assertIn("integration_test_theme", self.theme_manager.available_themes)

        # Step 5: Export the theme
        export_file = self.temp_dir / "exported_theme.json"

        # Mock the _load_theme_configuration method
        def mock_load_theme_config(theme_name):
            if theme_name == "integration_test_theme":
                self.theme_manager.current_theme = custom_theme
                return True
            return False

        self.theme_manager._load_theme_configuration = mock_load_theme_config

        result = self.theme_manager.export_theme("integration_test_theme", export_file)
        self.assertTrue(result)
        self.assertTrue(export_file.exists())

        # Step 6: Verify exported theme can be loaded
        exported_theme = ThemeConfiguration.load_from_file(export_file)
        self.assertIsNotNone(exported_theme)
        self.assertEqual(exported_theme.name, "integration_test_theme")
        self.assertEqual(exported_theme.display_name, "Integration Test Theme")

        # Step 7: Test theme duplication
        result = self.theme_manager.duplicate_theme(
            "integration_test_theme",
            "duplicated_integration_theme",
            "Duplicated Integration Theme"
        )
        self.assertTrue(result)
        self.assertIn("duplicated_integration_theme", self.theme_manager.available_themes)

        # Step 8: Verify duplicate theme file exists
        duplicate_file = self.theme_manager.custom_theme_dir / "duplicated_integration_theme.json"
        self.assertTrue(duplicate_file.exists())

        # Step 9: Test theme search
        search_results = self.theme_manager.search_themes("integration")
        self.assertGreaterEqual(len(search_results), 2)  # Original and duplicate
        self.assertIn("integration_test_theme", search_results)
        self.assertIn("duplicated_integration_theme", search_results)

        # Step 10: Test theme categories
        categories = self.theme_manager.get_theme_categories()
        self.assertIn("integration_test_theme", categories["Custom"])
        self.assertIn("duplicated_integration_theme", categories["Custom"])

    def test_theme_validation_and_error_handling(self):
        """Test theme validation and error handling"""

        # Test invalid theme import
        invalid_theme = ThemeConfiguration(
            name="invalid theme name",  # Invalid name with spaces
            display_name="Invalid Theme",
            description="Test",
            author="Test",
            version="invalid_version"  # Invalid version format
        )

        invalid_theme_file = self.temp_dir / "invalid_theme.json"
        invalid_theme.save_to_file(invalid_theme_file)

        # Import should fail with validation
        result = self.theme_manager.import_theme(invalid_theme_file, validate=True)
        self.assertFalse(result)

        # Import should succeed without validation
        result = self.theme_manager.import_theme(invalid_theme_file, validate=False)
        self.assertTrue(result)

    def test_theme_file_operations(self):
        """Test theme file operations and persistence"""

        # Create test theme
        test_theme = ThemeConfiguration(
            name="file_ops_test",
            display_name="File Operations Test",
            description="Testing file operations",
            author="Test",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
            is_custom=True
        )

        # Test save and load
        theme_file = self.temp_dir / "file_ops_test.json"
        self.assertTrue(test_theme.save_to_file(theme_file))

        loaded_theme = ThemeConfiguration.load_from_file(theme_file)
        self.assertIsNotNone(loaded_theme)
        self.assertEqual(loaded_theme.name, test_theme.name)
        self.assertEqual(loaded_theme.display_name, test_theme.display_name)

        # Test JSON structure
        with open(theme_file, 'r') as f:
            theme_data = json.load(f)

        self.assertEqual(theme_data["name"], "file_ops_test")
        self.assertEqual(theme_data["theme_type"], "custom")
        self.assertTrue(theme_data["is_custom"])

    def test_theme_manager_statistics(self):
        """Test theme manager statistics and information"""

        # Add some test themes
        themes = [
            ("custom1", ThemeType.CUSTOM),
            ("custom2", ThemeType.CUSTOM),
            ("imported1", ThemeType.IMPORTED)
        ]

        for name, theme_type in themes:
            from src.integration.theme_models import ThemeInfo
            theme_info = ThemeInfo(
                name=name,
                display_name=name.title(),
                description="Test theme",
                author="Test",
                version="1.0.0",
                theme_type=theme_type,
                is_dark=False,
                preview_colors={}
            )
            self.theme_manager.available_themes[name] = theme_info

        # Test statistics
        stats = self.theme_manager.get_theme_usage_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_themes", stats)
        self.assertIn("custom_themes", stats)
        self.assertIn("imported_themes", stats)

        # Verify counts
        self.assertEqual(stats["custom_themes"], 2)
        self.assertEqual(stats["imported_themes"], 1)


if __name__ == '__main__':
    unittest.main()
