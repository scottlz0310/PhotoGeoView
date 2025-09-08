"""
Unit tests for theme and navigation data models

Tests the core data models and interfaces for the qt-theme-breadcrumb feature.
Validates model creation, validation, and interface compliance.

Author: Kiro AI Integration System
"""

import unittest
from datetime import datetime
from pathlib import Path
import tempfile
import json

# Import the models and interfaces we created
from src.integration.theme_models import (
    ThemeConfiguration, ThemeInfo, ThemeType, ColorScheme, FontConfig, ValidationError
)
from src.integration.navigation_models import (
    BreadcrumbSegment, NavigationState, PathInfo, PathType, SegmentState, NavigationEvent
)


class TestThemeModels(unittest.TestCase):
    """Test theme-related data models"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_color_scheme_creation(self):
        """Test ColorScheme creation and validation"""
        # Valid color scheme
        colors = ColorScheme(
            primary="#2196F3",
            secondary="#FFC107",
            background="#FFFFFF",
            surface="#F5F5F5",
            text_primary="#212121",
            text_secondary="#757575",
            accent="#FF5722",
            error="#F44336",
            warning="#FF9800",
            success="#4CAF50"
        )

        self.assertEqual(colors.primary, "#2196F3")
        self.assertFalse(colors.is_dark_theme)

        # Dark theme
        dark_colors = ColorScheme(
            primary="#2196F3",
            secondary="#FFC107",
            background="#121212",
            surface="#1E1E1E",
            text_primary="#FFFFFF",
            text_secondary="#CCCCCC",
            accent="#FF5722",
            error="#F44336",
            warning="#FF9800",
            success="#4CAF50"
        )

        self.assertTrue(dark_colors.is_dark_theme)

    def test_color_scheme_validation(self):
        """Test ColorScheme validation"""
        # Invalid color should raise ValidationError
        with self.assertRaises(ValidationError):
            ColorScheme(
                primary="invalid_color",
                secondary="#FFC107",
                background="#FFFFFF",
                surface="#F5F5F5",
                text_primary="#212121",
                text_secondary="#757575",
                accent="#FF5722",
                error="#F44336",
                warning="#FF9800",
                success="#4CAF50"
            )

    def test_font_config_creation(self):
        """Test FontConfig creation and validation"""
        font = FontConfig("Arial", 12, "bold", "italic")

        self.assertEqual(font.family, "Arial")
        self.assertEqual(font.size, 12)
        self.assertEqual(font.weight, "bold")
        self.assertEqual(font.style, "italic")

        css = font.to_css()
        self.assertIn("Arial", css)
        self.assertIn("12px", css)
        self.assertIn("bold", css)
        self.assertIn("italic", css)

    def test_font_config_validation(self):
        """Test FontConfig validation"""
        # Invalid font size
        with self.assertRaises(ValidationError):
            FontConfig("Arial", -1)

        # Invalid font weight
        with self.assertRaises(ValidationError):
            FontConfig("Arial", 12, "invalid_weight")

    def test_theme_configuration_creation(self):
        """Test ThemeConfiguration creation"""
        theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="A test theme",
            author="Test Author",
            version="1.0.0"
        )

        self.assertEqual(theme.name, "test_theme")
        self.assertEqual(theme.display_name, "Test Theme")
        self.assertTrue(theme.is_valid)
        self.assertIsNotNone(theme.colors)
        self.assertIsNotNone(theme.fonts)

    def test_theme_configuration_validation(self):
        """Test ThemeConfiguration validation"""
        # Valid theme
        theme = ThemeConfiguration(
            name="valid_theme",
            display_name="Valid Theme",
            description="A valid theme",
            author="Test Author",
            version="1.0.0"
        )

        self.assertTrue(theme.validate())
        self.assertTrue(theme.is_valid)
        self.assertEqual(len(theme.validation_errors), 0)

        # Invalid theme name
        invalid_theme = ThemeConfiguration(
            name="invalid theme name!",
            display_name="Invalid Theme",
            description="An invalid theme",
            author="Test Author",
            version="1.0.0"
        )

        self.assertFalse(invalid_theme.validate())
        self.assertFalse(invalid_theme.is_valid)
        self.assertGreater(len(invalid_theme.validation_errors), 0)

    def test_theme_configuration_serialization(self):
        """Test ThemeConfiguration serialization"""
        theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="A test theme",
            author="Test Author",
            version="1.0.0"
        )

        # Test to_dict
        theme_dict = theme.to_dict()
        self.assertIsInstance(theme_dict, dict)
        self.assertEqual(theme_dict["name"], "test_theme")
        self.assertIn("colors", theme_dict)
        self.assertIn("fonts", theme_dict)

        # Test from_dict
        restored_theme = ThemeConfiguration.from_dict(theme_dict)
        self.assertEqual(restored_theme.name, theme.name)
        self.assertEqual(restored_theme.display_name, theme.display_name)

    def test_theme_info_creation(self):
        """Test ThemeInfo creation"""
        theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="A test theme",
            author="Test Author",
            version="1.0.0"
        )

        theme_info = ThemeInfo.from_theme_config(theme)

        self.assertEqual(theme_info.name, "test_theme")
        self.assertEqual(theme_info.display_name, "Test Theme")
        self.assertEqual(theme_info.theme_type, ThemeType.BUILT_IN)
        self.assertIsInstance(theme_info.preview_colors, dict)


class TestNavigationModels(unittest.TestCase):
    """Test navigation-related data models"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_path = self.temp_dir / "test_folder"
        self.test_path.mkdir(exist_ok=True)

    def test_breadcrumb_segment_creation(self):
        """Test BreadcrumbSegment creation"""
        segment = BreadcrumbSegment(
            name="test_folder",
            path=self.test_path
        )

        self.assertEqual(segment.name, "test_folder")
        self.assertEqual(segment.path, self.test_path)
        self.assertEqual(segment.state, SegmentState.NORMAL)
        self.assertTrue(segment.is_clickable)
        self.assertIsNotNone(segment.icon)

    def test_path_info_creation(self):
        """Test PathInfo creation"""
        path_info = PathInfo(self.test_path)

        self.assertEqual(path_info.path, self.test_path)
        self.assertEqual(path_info.path_type, PathType.LOCAL)
        self.assertTrue(path_info.is_accessible)
        self.assertIsNotNone(path_info.last_checked)

    def test_navigation_state_creation(self):
        """Test NavigationState creation"""
        nav_state = NavigationState(current_path=self.test_path)

        self.assertEqual(nav_state.current_path, self.test_path)
        self.assertIsInstance(nav_state.breadcrumb_segments, list)
        self.assertGreater(len(nav_state.breadcrumb_segments), 0)
        self.assertIsNotNone(nav_state.path_info)

    def test_navigation_state_segment_generation(self):
        """Test NavigationState segment generation"""
        nav_state = NavigationState(current_path=self.test_path)
        segments = nav_state.generate_segments()

        self.assertIsInstance(segments, list)
        self.assertGreater(len(segments), 0)

        # Check that current path is marked as current
        current_segments = [s for s in segments if s.state == SegmentState.CURRENT]
        self.assertEqual(len(current_segments), 1)
        self.assertEqual(current_segments[0].path, self.test_path)

    def test_navigation_state_navigation(self):
        """Test NavigationState navigation methods"""
        nav_state = NavigationState(current_path=self.test_path)

        # Test navigation to parent
        parent_path = self.test_path.parent
        success = nav_state.navigate_to_path(parent_path)

        self.assertTrue(success)
        self.assertEqual(nav_state.current_path, parent_path)
        self.assertIn(self.test_path, nav_state.history)

    def test_navigation_event_creation(self):
        """Test NavigationEvent creation"""
        event = NavigationEvent(
            event_type="navigate",
            source_path=self.test_path,
            target_path=self.test_path.parent,
            success=True
        )

        self.assertEqual(event.event_type, "navigate")
        self.assertEqual(event.source_path, self.test_path)
        self.assertEqual(event.target_path, self.test_path.parent)
        self.assertTrue(event.success)
        self.assertIsInstance(event.timestamp, datetime)

    def test_navigation_state_serialization(self):
        """Test NavigationState serialization"""
        nav_state = NavigationState(current_path=self.test_path)

        # Test to_dict
        state_dict = nav_state.to_dict()
        self.assertIsInstance(state_dict, dict)
        self.assertEqual(state_dict["current_path"], str(self.test_path))
        self.assertIn("segments", state_dict)
        self.assertIn("history", state_dict)


class TestModelIntegration(unittest.TestCase):
    """Test integration between theme and navigation models"""

    def test_models_import_correctly(self):
        """Test that all models can be imported without errors"""
        # This test ensures all imports work correctly
        from src.integration.theme_models import ThemeConfiguration, ThemeInfo
        from src.integration.navigation_models import NavigationState, BreadcrumbSegment
        from src.integration.theme_interfaces import IThemeManager, IThemeProvider
        from src.integration.navigation_interfaces import INavigationManager, IBreadcrumbRenderer
        from src.integration.theme_navigation_integration import IThemeNavigationIntegration

        # If we get here, all imports succeeded
        self.assertTrue(True)

    def test_interface_compatibility(self):
        """Test that interfaces are properly defined"""
        from src.integration.theme_interfaces import IThemeManager
        from src.integration.navigation_interfaces import INavigationManager

        # Check that interfaces have required methods
        self.assertTrue(hasattr(IThemeManager, 'get_current_theme'))
        self.assertTrue(hasattr(IThemeManager, 'apply_theme'))
        self.assertTrue(hasattr(INavigationManager, 'get_current_state'))
        self.assertTrue(hasattr(INavigationManager, 'navigate_to_path'))


if __name__ == '__main__':
    unittest.main()
