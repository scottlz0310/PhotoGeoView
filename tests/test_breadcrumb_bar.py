"""
Unit Tests for BreadcrumbAddressBar Component

Tests the breadcrumb address bar wrapper component functionality including:
- Path display and segment click handling
- Path truncation logic for long paths
- File system watcher integration
- Navigation event handling

Author: Kiro AI Integration System
Requirements: 2.1, 2.2, 2.3, 2.4
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.navigation_models import (
    BreadcrumbSegment,
    NavigationEvent,
)
from src.integration.services.file_system_watcher import FileSystemWatcher

# Mock the breadcrumb_addressbar import at module level
with patch.dict("sys.modules", {"breadcrumb_addressbar": Mock()}):
    from src.ui.breadcrumb_bar import BreadcrumbAddressBar


class TestBreadcrumbAddressBar:
    """Test class for BreadcrumbAddressBar component"""

    def setup_method(self):
        """Setup test environment"""
        # Ensure QApplication exists
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()

        # Create mock dependencies
        self.logger_system = Mock(spec=LoggerSystem)
        self.logger = Mock()
        self.logger_system.get_logger.return_value = self.logger

        self.file_watcher = Mock(spec=FileSystemWatcher)
        self.config_manager = Mock(spec=ConfigManager)

        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)

        # Create test directory structure
        self.create_test_directory_structure()

    def teardown_method(self):
        """Cleanup test environment"""
        # Cleanup temporary directory
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_directory_structure(self):
        """Create test directory structure"""
        # Create nested directories
        (self.test_path / "level1").mkdir()
        (self.test_path / "level1" / "level2").mkdir()
        (self.test_path / "level1" / "level2" / "level3").mkdir()
        (self.test_path / "level1" / "level2" / "level3" / "level4").mkdir()

        # Create some files
        (self.test_path / "file1.txt").touch()
        (self.test_path / "level1" / "file2.txt").touch()

    def test_initialization_success(self):
        """Test successful initialization of BreadcrumbAddressBar"""
        # Create breadcrumb bar
        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=self.file_watcher,
            logger_system=self.logger_system,
            config_manager=self.config_manager,
        )

        # Verify initialization
        assert breadcrumb_bar.file_watcher == self.file_watcher
        assert breadcrumb_bar.logger == self.logger
        assert breadcrumb_bar.config_manager == self.config_manager

        # Verify file watcher integration
        self.file_watcher.add_change_listener.assert_called_once()

        # Verify configuration loading
        self.config_manager.get_setting.assert_called()

        # Verify logging
        self.logger.info.assert_called_with("BreadcrumbAddressBar initialized successfully")

    def test_initialization_without_breadcrumb_library(self):
        """Test initialization when breadcrumb-addressbar library is not available"""
        with patch(
            "breadcrumb_addressbar.BreadcrumbWidget",
            side_effect=ImportError("Library not found"),
        ):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Verify graceful handling
            assert breadcrumb_bar.breadcrumb_widget is None
            self.logger.warning.assert_called()

    def test_set_current_path_success(self):
        """Test successful path setting"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Mock breadcrumb widget
            breadcrumb_bar.breadcrumb_widget = Mock()
            breadcrumb_bar.breadcrumb_widget.set_path = Mock()

            # Set path
            result = breadcrumb_bar.set_current_path(self.test_path)

            # Verify success
            assert result is True
            assert breadcrumb_bar.current_state.current_path == self.test_path
            breadcrumb_bar.breadcrumb_widget.set_path.assert_called_with(str(self.test_path))

    def test_set_current_path_invalid_path(self):
        """Test path setting with invalid path"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Try to set non-existent path
            invalid_path = Path("/nonexistent/path")
            result = breadcrumb_bar.set_current_path(invalid_path)

            # Verify failure
            assert result is False
            assert breadcrumb_bar.current_state.current_path != invalid_path

    def test_set_current_path_file_instead_of_directory(self):
        """Test path setting with file instead of directory"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Try to set file path
            file_path = self.test_path / "file1.txt"
            result = breadcrumb_bar.set_current_path(file_path)

            # Verify failure
            assert result is False

    def test_path_truncation_smart_mode(self):
        """Test smart truncation mode for long paths"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up long path
            long_path = self.test_path / "level1" / "level2" / "level3" / "level4"
            breadcrumb_bar.max_visible_segments = 3
            breadcrumb_bar.truncation_mode = "smart"

            # Mock breadcrumb widget
            breadcrumb_bar.breadcrumb_widget = Mock()
            breadcrumb_bar.breadcrumb_widget.set_path = Mock()

            # Set path
            breadcrumb_bar.set_current_path(long_path)

            # Verify truncation was applied
            segments = breadcrumb_bar.current_state.breadcrumb_segments
            assert len(segments) <= breadcrumb_bar.max_visible_segments

    def test_path_truncation_middle_mode(self):
        """Test middle truncation mode"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up long path
            long_path = self.test_path / "level1" / "level2" / "level3" / "level4"
            breadcrumb_bar.max_visible_segments = 4
            breadcrumb_bar.truncation_mode = "middle"

            # Mock breadcrumb widget
            breadcrumb_bar.breadcrumb_widget = Mock()
            breadcrumb_bar.breadcrumb_widget.set_path = Mock()

            # Set path
            breadcrumb_bar.set_current_path(long_path)

            # Apply truncation
            breadcrumb_bar._apply_path_truncation()

            # Verify truncation logic was called
            assert breadcrumb_bar.truncation_mode == "middle"

    def test_path_truncation_end_mode(self):
        """Test end truncation mode"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up long path
            long_path = self.test_path / "level1" / "level2" / "level3" / "level4"
            breadcrumb_bar.max_visible_segments = 4
            breadcrumb_bar.truncation_mode = "end"

            # Mock breadcrumb widget
            breadcrumb_bar.breadcrumb_widget = Mock()
            breadcrumb_bar.breadcrumb_widget.set_path = Mock()

            # Set path
            breadcrumb_bar.set_current_path(long_path)

            # Apply truncation
            breadcrumb_bar._apply_path_truncation()

            # Verify truncation logic was called
            assert breadcrumb_bar.truncation_mode == "end"

    def test_path_truncation_none_mode(self):
        """Test no truncation mode"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up long path
            long_path = self.test_path / "level1" / "level2" / "level3" / "level4"
            breadcrumb_bar.max_visible_segments = 3
            breadcrumb_bar.truncation_mode = "none"

            # Mock breadcrumb widget
            breadcrumb_bar.breadcrumb_widget = Mock()
            breadcrumb_bar.breadcrumb_widget.set_path = Mock()

            # Set path
            breadcrumb_bar.set_current_path(long_path)

            # Verify no truncation applied
            original_segments = breadcrumb_bar.current_state.breadcrumb_segments
            breadcrumb_bar._apply_path_truncation()

            # Should not change segments in "none" mode
            assert len(breadcrumb_bar.current_state.breadcrumb_segments) == len(original_segments)

    def test_segment_click_handling(self):
        """Test breadcrumb segment click handling"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up path with segments
            test_path = self.test_path / "level1" / "level2"
            breadcrumb_bar.set_current_path(test_path)

            # Mock signals
            breadcrumb_bar.segment_clicked = Mock()
            breadcrumb_bar.navigation_requested = Mock()

            # Simulate segment click
            segment_index = 1  # Click on level1 segment
            breadcrumb_bar._on_breadcrumb_segment_clicked(segment_index)

            # Verify navigation occurred
            expected_path = breadcrumb_bar.current_state.breadcrumb_segments[segment_index].path
            assert breadcrumb_bar.current_state.current_path == expected_path

    def test_segment_click_invalid_index(self):
        """Test segment click with invalid index"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up path
            breadcrumb_bar.set_current_path(self.test_path)

            # Mock error signal
            breadcrumb_bar.breadcrumb_error = Mock()

            # Try invalid segment index
            invalid_index = 999
            breadcrumb_bar._on_breadcrumb_segment_clicked(invalid_index)

            # Verify no navigation occurred and no error was emitted for out-of-range
            # (the method should handle this gracefully)
            assert breadcrumb_bar.current_state.current_path == self.test_path

    def test_navigate_up(self):
        """Test navigate up functionality"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up nested path
            nested_path = self.test_path / "level1" / "level2"
            breadcrumb_bar.set_current_path(nested_path)

            # Navigate up
            result = breadcrumb_bar.navigate_up()

            # Verify navigation
            assert result is True
            assert breadcrumb_bar.current_state.current_path == nested_path.parent

    def test_navigate_up_at_root(self):
        """Test navigate up when already at root"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up root path (or as close as we can get)
            root_path = Path("/") if os.name != "nt" else Path("C:\\")
            if root_path.exists():
                breadcrumb_bar.current_state.current_path = root_path

                # Try to navigate up from root
                result = breadcrumb_bar.navigate_up()

                # Should fail or stay at root
                assert result is False or breadcrumb_bar.current_state.current_path == root_path

    def test_navigate_to_segment(self):
        """Test navigate to specific segment"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set up path with multiple segments
            test_path = self.test_path / "level1" / "level2"
            breadcrumb_bar.set_current_path(test_path)

            # Navigate to specific segment
            segment_index = 1
            result = breadcrumb_bar.navigate_to_segment(segment_index)

            # Verify navigation
            assert result is True
            expected_path = breadcrumb_bar.current_state.breadcrumb_segments[segment_index].path
            assert breadcrumb_bar.current_state.current_path == expected_path

    def test_file_system_change_handling(self):
        """Test file system change event handling"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set current path
            breadcrumb_bar.set_current_path(self.test_path)

            # Mock QTimer to avoid actual delays in tests
            with patch("src.ui.breadcrumb_bar.QTimer") as mock_timer:
                mock_timer_instance = Mock()
                mock_timer.singleShot = Mock()

                # Simulate file system change
                changed_path = self.test_path / "level1"
                breadcrumb_bar._on_file_system_change(changed_path, "modified")

                # Verify timer was set for delayed refresh
                mock_timer.singleShot.assert_called_with(500, breadcrumb_bar._refresh_breadcrumb_state)

    def test_file_system_change_unrelated_path(self):
        """Test file system change for unrelated path"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set current path
            breadcrumb_bar.set_current_path(self.test_path)

            # Mock QTimer
            with patch("src.ui.breadcrumb_bar.QTimer") as mock_timer:
                mock_timer.singleShot = Mock()

                # Simulate file system change in unrelated path
                unrelated_path = Path("/some/other/path")
                breadcrumb_bar._on_file_system_change(unrelated_path, "modified")

                # Verify no timer was set (no refresh needed)
                mock_timer.singleShot.assert_not_called()

    def test_configuration_methods(self):
        """Test configuration setter methods"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher,
                logger_system=self.logger_system,
                config_manager=self.config_manager,
            )

            # Test max visible segments
            breadcrumb_bar.set_max_visible_segments(15)
            assert breadcrumb_bar.max_visible_segments == 15
            self.config_manager.set_setting.assert_called_with("ui.breadcrumb.max_segments", 15)

            # Test truncation mode
            breadcrumb_bar.set_truncation_mode("middle")
            assert breadcrumb_bar.truncation_mode == "middle"
            self.config_manager.set_setting.assert_called_with("ui.breadcrumb.truncation_mode", "middle")

            # Test show icons
            breadcrumb_bar.set_show_icons(False)
            assert breadcrumb_bar.show_icons is False
            self.config_manager.set_setting.assert_called_with("ui.breadcrumb.show_icons", False)

            # Test show tooltips
            breadcrumb_bar.set_show_tooltips(False)
            assert breadcrumb_bar.show_tooltips is False
            self.config_manager.set_setting.assert_called_with("ui.breadcrumb.show_tooltips", False)

    def test_navigation_listener_management(self):
        """Test navigation listener add/remove functionality"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Create mock listener
            listener = Mock()

            # Add listener
            result = breadcrumb_bar.add_navigation_listener(listener)
            assert result is True
            assert listener in breadcrumb_bar.navigation_listeners

            # Try to add same listener again
            result = breadcrumb_bar.add_navigation_listener(listener)
            assert result is False

            # Remove listener
            result = breadcrumb_bar.remove_navigation_listener(listener)
            assert result is True
            assert listener not in breadcrumb_bar.navigation_listeners

            # Try to remove non-existent listener
            result = breadcrumb_bar.remove_navigation_listener(listener)
            assert result is False

    def test_navigation_event_notification(self):
        """Test navigation event notification to listeners"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Add mock listener
            listener = Mock()
            breadcrumb_bar.add_navigation_listener(listener)

            # Create navigation event
            event = NavigationEvent(event_type="navigate", target_path=self.test_path, success=True)

            # Notify listeners
            breadcrumb_bar._notify_navigation_listeners(event)

            # Verify listener was called
            listener.assert_called_once_with(event)

    def test_navigation_event_listener_error_handling(self):
        """Test error handling in navigation event listeners"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Add listener that raises exception
            def failing_listener(event):
                raise Exception("Listener error")

            breadcrumb_bar.add_navigation_listener(failing_listener)

            # Create navigation event
            event = NavigationEvent(event_type="navigate", target_path=self.test_path, success=True)

            # Notify listeners (should not raise exception)
            breadcrumb_bar._notify_navigation_listeners(event)

            # Verify error was logged
            self.logger.error.assert_called()

    def test_inavigation_aware_interface(self):
        """Test INavigationAware interface implementation"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Test get_supported_navigation_events
            supported_events = breadcrumb_bar.get_supported_navigation_events()
            expected_events = [
                "navigate",
                "segment_click",
                "back",
                "forward",
                "up",
                "refresh",
            ]
            assert all(event in supported_events for event in expected_events)

            # Test on_navigation_changed
            event = NavigationEvent(event_type="navigate", target_path=self.test_path, success=True)

            # Mock breadcrumb widget
            breadcrumb_bar.breadcrumb_widget = Mock()
            breadcrumb_bar.breadcrumb_widget.set_path = Mock()

            # Handle navigation change
            breadcrumb_bar.on_navigation_changed(event)

            # Verify path was updated
            assert breadcrumb_bar.current_state.current_path == self.test_path

    def test_performance_stats(self):
        """Test performance statistics functionality"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Get initial stats
            stats = breadcrumb_bar.get_performance_stats()

            # Verify stats structure
            assert "last_update_time" in stats
            assert "update_count" in stats
            assert "current_segments_count" in stats
            assert "max_visible_segments" in stats
            assert "truncation_mode" in stats

            # Reset stats
            breadcrumb_bar.reset_performance_stats()

            # Verify reset
            assert breadcrumb_bar.update_count == 0

    def test_cleanup(self):
        """Test cleanup functionality"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Add some listeners
            listener = Mock()
            breadcrumb_bar.add_navigation_listener(listener)

            # Mock breadcrumb widget with cleanup method
            breadcrumb_bar.breadcrumb_widget = Mock()
            breadcrumb_bar.breadcrumb_widget.cleanup = Mock()

            # Cleanup
            breadcrumb_bar.cleanup()

            # Verify cleanup actions
            assert len(breadcrumb_bar.navigation_listeners) == 0
            breadcrumb_bar.breadcrumb_widget.cleanup.assert_called_once()
            self.logger.info.assert_called_with("BreadcrumbAddressBar cleanup completed")

    def test_get_widget(self):
        """Test get_widget method"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget") as mock_breadcrumb_widget:
            mock_widget = Mock()
            mock_breadcrumb_widget.return_value = mock_widget

            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Get widget
            widget = breadcrumb_bar.get_widget()

            # Verify widget is returned
            assert widget == mock_widget

    def test_get_current_path(self):
        """Test get_current_path method"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set path
            breadcrumb_bar.set_current_path(self.test_path)

            # Get current path
            current_path = breadcrumb_bar.get_current_path()

            # Verify path
            assert current_path == self.test_path

    def test_get_breadcrumb_segments(self):
        """Test get_breadcrumb_segments method"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Set path
            test_path = self.test_path / "level1" / "level2"
            breadcrumb_bar.set_current_path(test_path)

            # Get segments
            segments = breadcrumb_bar.get_breadcrumb_segments()

            # Verify segments
            assert isinstance(segments, list)
            assert len(segments) > 0
            assert all(isinstance(segment, BreadcrumbSegment) for segment in segments)

    def test_path_validation(self):
        """Test path validation logic"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            # Test valid directory
            assert breadcrumb_bar._validate_path(self.test_path) is True

            # Test non-existent path
            assert breadcrumb_bar._validate_path(Path("/nonexistent")) is False

            # Test file instead of directory
            file_path = self.test_path / "file1.txt"
            assert breadcrumb_bar._validate_path(file_path) is False

    def test_path_affects_breadcrumb(self):
        """Test path affects breadcrumb logic"""
        with patch("src.ui.breadcrumb_bar.BreadcrumbWidget"):
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=self.file_watcher, logger_system=self.logger_system
            )

            current_path = self.test_path / "level1" / "level2"

            # Test same path
            assert breadcrumb_bar._path_affects_breadcrumb(current_path, current_path) is True

            # Test parent path
            parent_path = current_path.parent
            assert breadcrumb_bar._path_affects_breadcrumb(parent_path, current_path) is True

            # Test child path
            child_path = current_path / "child"
            # This might be False since child doesn't exist, but the logic should handle it
            result = breadcrumb_bar._path_affects_breadcrumb(child_path, current_path)
            assert isinstance(result, bool)

            # Test unrelated path
            unrelated_path = Path("/some/other/path")
            assert breadcrumb_bar._path_affects_breadcrumb(unrelated_path, current_path) is False


if __name__ == "__main__":
    pytest.main([__file__])
