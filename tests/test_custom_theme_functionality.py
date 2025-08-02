"""
Unit Tests for Custom Theme Functionality

Tests for theme import, export, editor components, and custom theme management.
Implements test coverage for task 6 of the qt-theme-breadcrumb spec.

Author: Kiro AI Integration System
Requirements: 3.1, 3.2, 3.3, 3.4
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.theme_models import ThemeConfiguration, ColorScheme, FontConfig, ThemeType
from src.ui.theme_manager import ThemeManagerWidget
from src.ui.theme_editor import (
    ColorPickerWidget, FontPickerWidget, ThemePreviewWidget,
    ThemeEditorDialog, ThemeImportDialog
)


class TestCustomThemeModels(unittest.TestCase):
    """Test custom theme data models"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create test theme configuration
        self.test_theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="Test themeit tests",
            author="Test Author",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
            is_custom=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_theme_configuration_creation(self):
        """Test theme configuration creation and validation"""
        # Test valid theme creation
        self.assertTrue(self.test_theme.validate())
        self.assertEqual(self.test_theme.name, "test_theme")
        self.assertEqual(self.test_theme.theme_type, ThemeType.CUSTOM)
        self.assertTrue(self.test_theme.is_custom)

    def test_theme_configuration_validation(self):
        """Test theme configuration validation"""
        # Test invalid name
        invalid_theme = ThemeConfiguration(
            name="invalid name with spaces",
            display_name="Invalid Theme",
            description="Test",
            author="Test",
            version="1.0.0"
        )
        self.assertFalse(invalid_theme.validate())
        self.assertIn("Theme name must contain only letters", invalid_theme.validation_errors[0])

        # Test invalid version
        invalid_version_theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="Test",
            author="Test",
            version="invalid_version"
        )
        self.assertFalse(invalid_version_theme.validate())
        self.assertIn("semantic versioning", invalid_version_theme.validation_errors[0])

    def test_theme_serialization(self):
        """Test theme serialization to/from dict and file"""
        # Test to_dict
        theme_dict = self.test_theme.to_dict()
        self.assertEqual(theme_dict["name"], "test_theme")
        self.assertEqual(theme_dict["theme_type"], "custom")
        self.assertTrue(theme_dict["is_custom"])

        # Test from_dict
        restored_theme = ThemeConfiguration.from_dict(theme_dict)
        self.assertEqual(restored_theme.name, self.test_theme.name)
        self.assertEqual(restored_theme.theme_type, self.test_theme.theme_type)

        # Test file save/load
        theme_file = self.temp_dir / "test_theme.json"
        self.assertTrue(self.test_theme.save_to_file(theme_file))
        self.assertTrue(theme_file.exists())

        loaded_theme = ThemeConfiguration.load_from_file(theme_file)
        self.assertIsNotNone(loaded_theme)
        self.assertEqual(loaded_theme.name, self.test_theme.name)

    def test_color_scheme_validation(self):
        """Test color scheme validation"""
        # Test valid colors
        valid_colors = ColorScheme(
            primary="#FF0000",
            secondary="#00FF00",
            background="#FFFFFF",
            surface="#F5F5F5",
            text_primary="#000000",
            text_secondary="#666666",
            accent="#0000FF",
            error="#FF0000",
            warning="#FFA500",
            success="#00FF00"
        )
        # Should not raise exception
        self.assertIsNotNone(valid_colors)

        # Test invalid color format
        with self.assertRaises(Exception):
            ColorScheme(
                primary="invalid_color",
                secondary="#00FF00",
                background="#FFFFFF",
                surface="#F5F5F5",
                text_primary="#000000",
                text_secondary="#666666",
                accent="#0000FF",
                error="#FF0000",
                warning="#FFA500",
                success="#00FF00"
            )

    def test_font_config_validation(self):
        """Test font configuration validation"""
        # Test valid font
        valid_font = FontConfig("Arial", 12, "normal", "normal")
        self.assertEqual(valid_font.family, "Arial")
        self.assertEqual(valid_font.size, 12)

        # Test invalid font size
        with self.assertRaises(Exception):
            FontConfig("Arial", -5, "normal", "normal")

        # Test invalid font weight
        with self.assertRaises(Exception):
            FontConfig("Arial", 12, "invalid_weight", "normal")

        # Test CSS generation
        css = valid_font.to_css()
        self.assertIn("Arial", css)
        self.assertIn("12px", css)


class TestThemeManagerCustomFunctionality(unittest.TestCase):
    """Test theme manager custom theme functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Mock dependencies
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)
        self.mock_logger = Mock()
        self.mock_logger_system.get_logger.return_value = self.mock_logger

        # Create theme manager
        with patch('src.ui.theme_manager.Path') as mock_path:
            mock_path.return_value.mkdir = Mock()
            mock_path.return_value.glob = Mock(return_value=[])

            self.theme_manager = ThemeManagerWidget(
                self.mock_config_manager,
                self.mock_logger_system
            )

            # Set up temp directories
            self.theme_manager.theme_dir = self.temp_dir / "themes"
            self.theme_manager.custom_theme_dir = self.temp_dir / "custom_themes"
            self.theme_manager.theme_dir.mkdir(parents=True, exist_ok=True)
            self.theme_manager.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Create test theme
        self.test_theme = ThemeConfiguration(
            name="test_custom_theme",
            display_name="Test Custom Theme",
            description="Test theme for unit tests",
            author="Test Author",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
            is_custom=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_theme_success(self):
        """Test successful theme import"""
        # Create test theme file
        theme_file = self.temp_dir / "import_test.json"
        self.test_theme.save_to_file(theme_file)

        # Test import
        result = self.theme_manager.import_theme(theme_file)
        self.assertTrue(result)
        self.assertIn("test_custom_theme", self.theme_manager.available_themes)

    def test_import_theme_validation_failure(self):
        """Test theme import with validation failure"""
        # Create invalid theme file
        invalid_theme = ThemeConfiguration(
            name="invalid theme name",  # Invalid name with spaces
            display_name="Invalid Theme",
            description="Test",
            author="Test",
            version="invalid"  # Invalid version
        )

        theme_file = self.temp_dir / "invalid_theme.json"
        invalid_theme.save_to_file(theme_file)

        # Test import with validation
        result = self.theme_manager.import_theme(theme_file, validate=True)
        self.assertFalse(result)

    def test_import_theme_overwrite_protection(self):
        """Test theme import overwrite protection"""
        # Create and import first theme
        theme_file = self.temp_dir / "test_theme.json"
        self.test_theme.save_to_file(theme_file)

        self.assertTrue(self.theme_manager.import_theme(theme_file))

        # Try to import same theme again without overwrite
        result = self.theme_manager.import_theme(theme_file, overwrite=False)
        self.assertFalse(result)

        # Try with overwrite enabled
        result = self.theme_manager.import_theme(theme_file, overwrite=True)
        self.assertTrue(result)

    def test_export_theme_success(self):
        """Test successful theme export"""
        # Add test theme to available themes
        from src.integration.theme_models import ThemeInfo
        theme_info = ThemeInfo.from_theme_config(self.test_theme)
        self.theme_manager.available_themes["test_custom_theme"] = theme_info
        self.theme_manager.current_theme = self.test_theme

        # Test export
        export_file = self.temp_dir / "exported_theme.json"
        result = self.theme_manager.export_theme("test_custom_theme", export_file)
        self.assertTrue(result)
        self.assertTrue(export_file.exists())

        # Verify exported content
        exported_theme = ThemeConfiguration.load_from_file(export_file)
        self.assertIsNotNone(exported_theme)
        self.assertEqual(exported_theme.name, "test_custom_theme")

    def test_export_theme_not_found(self):
        """Test theme export with non-existent theme"""
        export_file = self.temp_dir / "exported_theme.json"
        result = self.theme_manager.export_theme("non_existent_theme", export_file)
        self.assertFalse(result)

    def test_duplicate_theme(self):
        """Test theme duplication"""
        # Add test theme to available themes
        from src.integration.theme_models import ThemeInfo
        theme_info = ThemeInfo.from_theme_config(self.test_theme)
        self.theme_manager.available_themes["test_custom_theme"] = theme_info

        # Mock the _load_theme_configuration method to return True and set current_theme
        def mock_load_theme_config(theme_name):
            if theme_name == "test_custom_theme":
                self.theme_manager.current_theme = self.test_theme
                return True
            return False

        self.theme_manager._load_theme_configuration = mock_load_theme_config

        # Test duplication
        result = self.theme_manager.duplicate_theme(
            "test_custom_theme",
            "duplicated_theme",
            "Duplicated Theme"
        )
        self.assertTrue(result)
        self.assertIn("duplicated_theme", self.theme_manager.available_themes)

        # Verify duplicate theme file exists
        duplicate_file = self.theme_manager.custom_theme_dir / "duplicated_theme.json"
        self.assertTrue(duplicate_file.exists())

    def test_rename_theme(self):
        """Test theme renaming"""
        # Create and save test theme
        theme_file = self.theme_manager.custom_theme_dir / "test_custom_theme.json"
        self.test_theme.save_to_file(theme_file)

        # Add to available themes
        from src.integration.theme_models import ThemeInfo
        theme_info = ThemeInfo.from_theme_config(self.test_theme)
        self.theme_manager.available_themes["test_custom_theme"] = theme_info

        # Test rename
        result = self.theme_manager.rename_theme(
            "test_custom_theme",
            "renamed_theme",
            "Renamed Theme"
        )
        self.assertTrue(result)

        # Verify old theme is removed and new theme exists
        self.assertNotIn("test_custom_theme", self.theme_manager.available_themes)
        self.assertIn("renamed_theme", self.theme_manager.available_themes)

        # Verify file operations
        old_file = self.theme_manager.custom_theme_dir / "test_custom_theme.json"
        new_file = self.theme_manager.custom_theme_dir / "renamed_theme.json"
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.exists())

    def test_search_themes(self):
        """Test theme search functionality"""
        # Add multiple test themes
        themes = [
            ("dark_theme", "Dark Theme", "A dark theme for night use", "Author1"),
            ("light_theme", "Light Theme", "A bright theme for day use", "Author2"),
            ("blue_theme", "Blue Theme", "A blue colored theme", "Author1")
        ]

        for name, display_name, description, author in themes:
            from src.integration.theme_models import ThemeInfo
            theme_info = ThemeInfo(
                name=name,
                display_name=display_name,
                description=description,
                author=author,
                version="1.0.0",
                theme_type=ThemeType.CUSTOM,
                is_dark=False,
                preview_colors={}
            )
            self.theme_manager.available_themes[name] = theme_info

        # Test search by name
        results = self.theme_manager.search_themes("dark")
        self.assertIn("dark_theme", results)
        self.assertEqual(len(results), 1)

        # Test search by author
        results = self.theme_manager.search_themes("Author1")
        self.assertEqual(len(results), 2)
        self.assertIn("dark_theme", results)
        self.assertIn("blue_theme", results)

        # Test search by description
        results = self.theme_manager.search_themes("night")
        self.assertIn("dark_theme", results)

    def test_get_theme_categories(self):
        """Test theme categorization"""
        # Add test themes with different types
        themes = [
            ("builtin_theme", ThemeType.BUILT_IN, False),
            ("custom_theme", ThemeType.CUSTOM, True),
            ("imported_theme", ThemeType.IMPORTED, False),
            ("dark_theme", ThemeType.CUSTOM, True)
        ]

        for name, theme_type, is_dark in themes:
            from src.integration.theme_models import ThemeInfo
            theme_info = ThemeInfo(
                name=name,
                display_name=name.replace('_', ' ').title(),
                description="Test theme",
                author="Test",
                version="1.0.0",
                theme_type=theme_type,
                is_dark=is_dark,
                preview_colors={}
            )
            self.theme_manager.available_themes[name] = theme_info

        # Test categorization
        categories = self.theme_manager.get_theme_categories()

        self.assertIn("builtin_theme", categories["Built-in"])
        self.assertIn("custom_theme", categories["Custom"])
        self.assertIn("imported_theme", categories["Imported"])
        self.assertIn("dark_theme", categories["Dark"])
        self.assertIn("builtin_theme", categories["Light"])

    def test_validate_theme_compatibility(self):
        """Test theme compatibility validation"""
        # Add test theme
        from src.integration.theme_models import ThemeInfo
        theme_info = ThemeInfo.from_theme_config(self.test_theme)
        self.theme_manager.available_themes["test_custom_theme"] = theme_info
        self.theme_manager.current_theme = self.test_theme

        # Test compatibility check
        compatibility = self.theme_manager.validate_theme_compatibility("test_custom_theme")
        self.assertIsInstance(compatibility, dict)
        self.assertIn("compatible", compatibility)
        self.assertIn("errors", compatibility)
        self.assertIn("warnings", compatibility)


class TestThemeEditorComponents(unittest.TestCase):
    """Test theme editor UI components"""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for widget tests"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_color_picker_widget(self):
        """Test color picker widget functionality"""
        color_picker = ColorPickerWidget("primary", "#FF0000")

        # Test initial color
        self.assertEqual(color_picker.get_color(), "#FF0000")

        # Test color change
        color_picker.set_color("#00FF00")
        self.assertEqual(color_picker.get_color(), "#00FF00")

        # Test invalid color
        color_picker.set_color("invalid_color")
        # Should keep previous valid color
        self.assertEqual(color_picker.get_color(), "#00FF00")

    def test_font_picker_widget(self):
        """Test font picker widget functionality"""
        initial_font = FontConfig("Arial", 12, "normal", "normal")
        font_picker = FontPickerWidget("default", initial_font)

        # Test initial font
        current_font = font_picker.get_font()
        self.assertEqual(current_font.family, "Arial")
        self.assertEqual(current_font.size, 12)

        # Test font change
        new_font = FontConfig("Times New Roman", 14, "bold", "italic")
        font_picker.set_font(new_font)

        current_font = font_picker.get_font()
        self.assertEqual(current_font.family, "Times New Roman")
        self.assertEqual(current_font.size, 14)
        self.assertEqual(current_font.weight, "bold")

    def test_theme_preview_widget(self):
        """Test theme preview widget"""
        preview_widget = ThemePreviewWidget()

        # Test initial state
        self.assertIsNone(preview_widget.current_theme)

        # Test theme update
        test_theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="Test",
            author="Test",
            version="1.0.0"
        )

        preview_widget.update_preview(test_theme)
        self.assertEqual(preview_widget.current_theme, test_theme)

    @patch('src.ui.theme_editor.QTimer')
    def test_theme_editor_dialog_creation(self, mock_timer):
        """Test theme editor dialog creation"""
        # Mock dependencies
        mock_theme_manager = Mock(spec=ThemeManagerWidget)
        mock_config_manager = Mock(spec=ConfigManager)
        mock_logger_system = Mock(spec=LoggerSystem)
        mock_logger_system.get_logger.return_value = Mock()

        # Create editor dialog
        editor = ThemeEditorDialog(
            mock_theme_manager,
            mock_config_manager,
            mock_logger_system
        )

        # Test basic properties
        self.assertIsNotNone(editor.current_theme)
        self.assertEqual(editor.current_theme.name, "new_theme")
        self.assertTrue(editor.current_theme.is_custom)

    def test_theme_import_dialog_creation(self):
        """Test theme import dialog creation"""
        # Mock dependencies
        mock_theme_manager = Mock(spec=ThemeManagerWidget)
        mock_logger_system = Mock(spec=LoggerSystem)
        mock_logger_system.get_logger.return_value = Mock()

        # Create import dialog
        import_dialog = ThemeImportDialog(
            mock_theme_manager,
            mock_logger_system
        )

        # Test basic properties
        self.assertEqual(import_dialog.windowTitle(), "Import Theme")
        self.assertFalse(import_dialog.import_button.isEnabled())


class TestThemeEditorIntegration(unittest.TestCase):
    """Test theme editor integration with theme manager"""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for widget tests"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Mock dependencies
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)
        self.mock_logger = Mock()
        self.mock_logger_system.get_logger.return_value = self.mock_logger

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.ui.theme_manager.Path')
    def test_theme_editor_save_integration(self, mock_path):
        """Test theme editor save integration with theme manager"""
        # Setup mocks
        mock_path.return_value.mkdir = Mock()
        mock_path.return_value.glob = Mock(return_value=[])

        # Create theme manager
        theme_manager = ThemeManagerWidget(
            self.mock_config_manager,
            self.mock_logger_system
        )

        # Set up temp directories
        theme_manager.custom_theme_dir = self.temp_dir / "custom_themes"
        theme_manager.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Create theme editor
        editor = ThemeEditorDialog(
            theme_manager,
            self.mock_config_manager,
            self.mock_logger_system
        )

        # Modify theme
        editor.current_theme.name = "integration_test_theme"
        editor.current_theme.display_name = "Integration Test Theme"

        # Mock the reload_themes method
        theme_manager.reload_themes = Mock(return_value=True)

        # Test save
        with patch('src.ui.theme_editor.QMessageBox'):
            editor._save_theme()

        # Verify theme file was created
        theme_file = theme_manager.custom_theme_dir / "integration_test_theme.json"
        self.assertTrue(theme_file.exists())

        # Verify reload was called
        theme_manager.reload_themes.assert_called_once()

    @patch('src.ui.theme_manager.Path')
    def test_theme_import_integration(self, mock_path):
        """Test theme import dialog integration with theme manager"""
        # Setup mocks
        mock_path.return_value.mkdir = Mock()
        mock_path.return_value.glob = Mock(return_value=[])

        # Create theme manager
        theme_manager = ThemeManagerWidget(
            self.mock_config_manager,
            self.mock_logger_system
        )

        # Set up temp directories
        theme_manager.custom_theme_dir = self.temp_dir / "custom_themes"
        theme_manager.custom_theme_dir.mkdir(parents=True, exist_ok=True)

        # Create test theme file
        test_theme = ThemeConfiguration(
            name="import_test_theme",
            display_name="Import Test Theme",
            description="Test theme for import",
            author="Test Author",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
            is_custom=True
        )

        import_file = self.temp_dir / "import_test.json"
        test_theme.save_to_file(import_file)

        # Create import dialog
        import_dialog = ThemeImportDialog(
            theme_manager,
            self.mock_logger_system
        )

        # Set file path
        import_dialog.file_path_input.setText(str(import_file))

        # Trigger validation
        import_dialog._validate_theme_file(import_file)

        # Verify import button is enabled
        self.assertTrue(import_dialog.import_button.isEnabled())

        # Test import
        with patch('src.ui.theme_editor.QMessageBox'):
            import_dialog._import_theme()

        # Verify theme was imported
        imported_file = theme_manager.custom_theme_dir / "import_test_theme.json"
        self.assertTrue(imported_file.exists())


if __name__ == '__main__':
    # Run tests
    unittest.main()
