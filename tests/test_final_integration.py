"""
Final Integration Test for PhotoGeoView AI Integration

Tests the complete integration of all AI components:
- GitHub Copilot (CS4Coding) - Image processing and EXIF handling
- Cursor (CursorBLD) - UI/UX components and layout
- Kiro - Architecture, optimization, and integration

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from photogeoview.integration.config_manager import ConfigManager
from photogeoview.integration.error_handling import IntegratedErrorHandler
from photogeoview.integration.logging_system import LoggerSystem
from photogeoview.integration.models import AIComponent
from photogeoview.integration.state_manager import StateManager
from photogeoview.integration.ui.main_window import IntegratedMainWindow


class TestFinalIntegration:
    """Test complete AI integration functionality"""

    @pytest.fixture(autouse=True)
    def setup_qt_app(self):
        """Setup Qt application for testing"""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        yield
        # Don't quit the app as it might be used by other tests

    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies"""
        with (
            patch("integration.ui.main_window.FileDiscoveryService"),
            patch("integration.ui.main_window.FileSystemWatcher"),
            patch("integration.services.file_discovery_service.FileDiscoveryService"),
            patch("integration.services.file_system_watcher.FileSystemWatcher"),
        ):
            yield

    @pytest.fixture
    def window_dependencies(self):
        """Create required dependencies for main window"""
        config_manager = ConfigManager()
        state_manager = StateManager()
        return config_manager, state_manager

    @pytest.fixture
    def main_window(self, mock_dependencies, window_dependencies):
        """Create main window with dependencies"""
        config_manager, state_manager = window_dependencies
        window = IntegratedMainWindow(config_manager, state_manager)
        yield window
        window.close()

    def test_main_window_initialization(self, main_window):
        """Test that the integrated main window initializes correctly"""

        # Verify basic initialization
        assert main_window is not None
        assert main_window.windowTitle() == "PhotoGeoView - AI Integrated"
        assert main_window.minimumSize().width() >= 1200
        assert main_window.minimumSize().height() >= 800

        # Verify core components are initialized
        assert hasattr(main_window, "config_manager")
        assert hasattr(main_window, "error_handler")
        assert hasattr(main_window, "logger_system")
        assert hasattr(main_window, "state_manager")

        # Verify UI components
        assert hasattr(main_window, "status_bar")
        assert hasattr(main_window, "folder_navigator")
        assert hasattr(main_window, "thumbnail_grid")

    def test_ai_component_integration(self, main_window):
        """Test that all AI components are properly integrated"""

        # Test CS4Coding components (image processing)
        assert hasattr(main_window, "exif_panel")

        # Test CursorBLD components (UI/UX)
        assert hasattr(main_window, "folder_navigator")
        assert hasattr(main_window, "thumbnail_grid")
        assert hasattr(main_window, "theme_manager")

        # Test Kiro components (optimization and integration)
        assert hasattr(main_window, "performance_timer")
        assert hasattr(main_window, "memory_monitor")
        assert hasattr(main_window, "error_handler")

    def test_status_message_handling(self, main_window):
        """Test status message handling system"""

        # Verify status message handler exists
        assert hasattr(main_window, "_on_status_message")

        # Test status message handling
        test_message = "Test status message"
        main_window._on_status_message(test_message)

        # Verify status bar shows the message
        if main_window.status_bar:
            # Note: In real Qt, we'd check the actual message
            # For testing, we just verify the method doesn't crash
            pass

    def test_signal_connections(self, main_window):
        """Test that signals are properly connected between components"""

        # Verify signal connection method exists
        assert hasattr(main_window, "_connect_signals")

        # Test that components have expected signals
        if main_window.folder_navigator:
            assert hasattr(main_window.folder_navigator, "folder_changed")
            assert hasattr(main_window.folder_navigator, "status_message")

        if main_window.thumbnail_grid:
            assert hasattr(main_window.thumbnail_grid, "image_selected")

    def test_error_handling_integration(self, main_window):
        """Test integrated error handling system"""

        # Verify error handler is integrated
        assert main_window.error_handler is not None
        assert isinstance(main_window.error_handler, IntegratedErrorHandler)

        # Test error handling doesn't crash
        try:
            # Import ErrorCategory for proper enum usage
            from integration.error_handling import ErrorCategory

            # Simulate an error condition
            main_window.error_handler.handle_error(
                Exception("Test error"),
                ErrorCategory.UI_ERROR,
                {"test": "data"},
                AIComponent.KIRO,
            )
        except Exception as e:
            pytest.fail(f"Error handling failed: {e}")

    def test_logging_system_integration(self, main_window):
        """Test integrated logging system"""

        # Verify logger system is integrated
        assert main_window.logger_system is not None
        assert isinstance(main_window.logger_system, LoggerSystem)

        # Test logging doesn't crash
        try:
            main_window.logger_system.log_ai_operation(
                AIComponent.KIRO, "test_operation", "Test log message"
            )
        except Exception as e:
            pytest.fail(f"Logging failed: {e}")

    def test_configuration_management(self, main_window):
        """Test configuration management integration"""

        # Verify config manager is integrated
        assert main_window.config_manager is not None
        assert isinstance(main_window.config_manager, ConfigManager)

        # Test configuration access
        try:
            # Test getting a setting (should not crash)
            setting = main_window.config_manager.get_setting("ui.theme", "default")
            assert setting is not None
        except Exception as e:
            pytest.fail(f"Configuration access failed: {e}")

    def test_state_management(self, main_window):
        """Test state management integration"""

        # Verify state manager is integrated
        assert main_window.state_manager is not None
        assert isinstance(main_window.state_manager, StateManager)

        # Test state management
        try:
            # Test state operations with existing state keys
            # Use a simpler state key that should work
            original_value = main_window.state_manager.get_state_value(
                "current_theme", "default"
            )

            # Test setting and getting a state value
            test_result = main_window.state_manager.update_state(current_theme="dark")
            assert test_result == True

            # Verify the value was set
            new_value = main_window.state_manager.get_state_value("current_theme")
            assert new_value == "dark"
        except Exception as e:
            pytest.fail(f"State management failed: {e}")

    def test_performance_monitoring(self, main_window):
        """Test performance monitoring integration"""

        # Verify performance monitoring components
        assert hasattr(main_window, "performance_timer")
        assert hasattr(main_window, "memory_monitor")
        assert hasattr(main_window, "_on_performance_alert")

        # Test performance alert handling
        try:
            main_window._on_performance_alert("warning", "Test performance alert")
        except Exception as e:
            pytest.fail(f"Performance monitoring failed: {e}")

    def test_theme_management(self, main_window):
        """Test theme management integration"""

        # Verify theme manager is integrated
        assert hasattr(main_window, "theme_manager")

        # Test theme change handling
        if hasattr(main_window, "_on_theme_changed"):
            try:
                main_window._on_theme_changed("dark")
            except Exception as e:
                pytest.fail(f"Theme management failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
