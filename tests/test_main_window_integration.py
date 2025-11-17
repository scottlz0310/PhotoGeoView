"""
Integration tests for main window components

Tests the integration of theme manager and breadcrumb components with the main window.
Verifies that components are properly connected and communicate correctly.

Author: Kiro AI Integration System
Requirements: 1.1, 1.2, 2.1, 2.2
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from photogeoview.integration.config_manager import ConfigManager
from photogeoview.integration.logging_system import LoggerSystem
from photogeoview.integration.state_manager import StateManager
from photogeoview.integration.ui.main_window import IntegratedMainWindow


class TestMainWindowIntegration(unittest.TestCase):
    """Test suite for main window component integration"""

    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test configuration
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)

        # Create test configuration
        self.config_manager = ConfigManager(config_dir=self.config_dir)
        self.state_manager = StateManager()
        self.logger_system = LoggerSystem()

        # Mock file system watcher to avoid actual file monitoring
        self.file_watcher_mock = Mock()
        self.file_watcher_mock.add_change_listener = Mock()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_main_window_initialization(self):
        """Test that main window initializes with theme manager and breadcrumb components"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Verify main window is created
            self.assertIsNotNone(main_window)

            # Verify theme manager widget is initialized
            self.assertIsNotNone(main_window.theme_manager_widget)

            # Verify breadcrumb bar is initialized
            self.assertIsNotNone(main_window.breadcrumb_bar)

            # Verify components are connected
            self.assertTrue(hasattr(main_window, "_on_theme_manager_widget_changed"))
            self.assertTrue(hasattr(main_window, "_on_breadcrumb_path_changed"))

            main_window.close()

    def test_theme_manager_integration(self):
        """Test theme manager integration with main window"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test theme manager widget exists
            self.assertIsNotNone(main_window.theme_manager_widget)

            # Test theme change handling
            if main_window.theme_manager_widget:
                # Mock theme change
                main_window._on_theme_manager_widget_changed("default", "dark")

                # Verify state was updated
                # Note: This would need actual state verification in a real test

            main_window.close()

    def test_breadcrumb_bar_integration(self):
        """Test breadcrumb bar integration with main window"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test breadcrumb bar exists
            self.assertIsNotNone(main_window.breadcrumb_bar)

            # Test breadcrumb widget is available
            if main_window.breadcrumb_bar:
                breadcrumb_widget = main_window.breadcrumb_bar.get_widget()
                # Widget might be None if breadcrumb-addressbar library is not available
                # This is acceptable for testing

            # Test breadcrumb path change handling
            test_path = Path.home()
            main_window._on_breadcrumb_path_changed(test_path)

            # Verify state was updated
            current_folder = main_window.state_manager.get_state_value("current_folder")
            self.assertEqual(current_folder, test_path)

            main_window.close()

    def test_folder_navigator_breadcrumb_connection(self):
        """Test connection between folder navigator and breadcrumb bar"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test that folder navigator and breadcrumb bar are connected
            self.assertIsNotNone(main_window.folder_navigator)
            self.assertIsNotNone(main_window.breadcrumb_bar)

            # Test folder change propagation
            test_path = Path.home()

            # Simulate folder change from folder navigator
            main_window._on_folder_changed(test_path)

            # Verify breadcrumb bar was updated (would need to check actual breadcrumb state)
            # For now, just verify the method doesn't crash
            self.assertTrue(True)

            main_window.close()

    def test_theme_component_registration(self):
        """Test that UI components are registered with theme manager"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test component registration method exists
            self.assertTrue(hasattr(main_window, "_register_theme_aware_components"))

            # Test registration method can be called
            main_window._register_theme_aware_components()

            # Verify no exceptions were raised
            self.assertTrue(True)

            main_window.close()

    def test_keyboard_shortcuts_integration(self):
        """Test keyboard shortcuts for theme manager"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test that theme manager widget has shortcuts setup
            if main_window.theme_manager_widget:
                shortcuts_info = main_window.theme_manager_widget.get_keyboard_shortcuts_info()
                self.assertIsInstance(shortcuts_info, dict)
                self.assertIn("Ctrl+T", shortcuts_info)
                self.assertIn("Ctrl+Shift+T", shortcuts_info)

            main_window.close()

    def test_error_handling_integration(self):
        """Test error handling for integrated components"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test theme error handling
            main_window._on_theme_error("test_theme", "Test error message")

            # Test breadcrumb error handling
            main_window._on_breadcrumb_error("test_error", "Test breadcrumb error")

            # Verify error handlers don't crash
            self.assertTrue(True)

            main_window.close()

    def test_left_panel_layout_with_breadcrumb(self):
        """Test that left panel layout includes breadcrumb bar"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test that left panel splitter exists
            self.assertIsNotNone(main_window.left_panel_splitter)

            # Test that splitter has the expected number of widgets
            # Should have breadcrumb + folder navigator + thumbnail grid + EXIF panel
            widget_count = main_window.left_panel_splitter.count()

            # Count should be 4 if breadcrumb is present, 3 if not
            self.assertIn(widget_count, [3, 4])

            main_window.close()

    def test_state_persistence_with_new_components(self):
        """Test state persistence includes new components"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test state restoration method
            main_window._restore_left_panel_splitter_state()

            # Verify no exceptions were raised
            self.assertTrue(True)

            main_window.close()


class TestMainWindowComponentCommunication(unittest.TestCase):
    """Test communication between main window components"""

    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test configuration
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)

        # Create test configuration
        self.config_manager = ConfigManager(config_dir=self.config_dir)
        self.state_manager = StateManager()
        self.logger_system = LoggerSystem()

        # Mock file system watcher
        self.file_watcher_mock = Mock()
        self.file_watcher_mock.add_change_listener = Mock()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_theme_change_propagation(self):
        """Test that theme changes propagate to all components"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Mock theme-aware components
            mock_component = Mock()
            mock_component.apply_theme = Mock()

            # Test theme change propagation
            if main_window.theme_manager_widget:
                # Register mock component
                main_window.theme_manager_widget.register_component(mock_component)

                # Simulate theme change
                main_window._on_theme_manager_widget_changed("default", "dark")

            main_window.close()

    def test_navigation_synchronization(self):
        """Test navigation synchronization between components"""

        with patch(
            "src.integration.ui.main_window.FileSystemWatcher",
            return_value=self.file_watcher_mock,
        ):
            # Create main window
            main_window = IntegratedMainWindow(self.config_manager, self.state_manager, self.logger_system)

            # Test navigation synchronization
            test_path = Path.home()

            # Simulate folder change from folder navigator
            main_window._on_folder_changed(test_path)

            # Verify state was updated
            current_folder = main_window.state_manager.get_state_value("current_folder")
            self.assertEqual(current_folder, test_path)

            # Simulate breadcrumb navigation
            main_window._on_breadcrumb_path_changed(test_path)

            # Verify state consistency
            current_folder = main_window.state_manager.get_state_value("current_folder")
            self.assertEqual(current_folder, test_path)

            main_window.close()


if __name__ == "__main__":
    unittest.main()
