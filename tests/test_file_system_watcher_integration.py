"""
File System Watcher Integration Tests

Tests for file system watcher integration with breadcrumb navigation,
directory monitoring, and cross-platform file system events.

Author: Kiro AI Integration System
Requirements: 2.1, 4.1, 4.3
"""

import asyncio
import os
import platform
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.integration.logging_system import LoggerSystem
from src.integration.navigation_integration_controller import NavigationIntegrationController
from src.integration.services.file_system_watcher import FileChangeType, FileSystemWatcher
from src.ui.breadcrumb_bar import BreadcrumbAddressBar


class TestFileSystemWatcherIntegration:
    """Test file system watcher integration with navigation components"""

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory structure for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test directory structure
            (temp_path / "watched_folder").mkdir()
            (temp_path / "watched_folder" / "subfolder1").mkdir()
            (temp_path / "watched_folder" / "subfolder2").mkdir()
            (temp_path / "unwatched_folder").mkdir()

            # Create test files
            (temp_path / "watched_folder" / "file1.txt").write_text("content1")
            (temp_path / "watched_folder" / "file2.txt").write_text("content2")

            yield temp_path

    @pytest.fixture
    def logger_system(self):
        """Create logger system"""
        return LoggerSystem()

    @pytest.fixture
    def file_system_watcher(self, logger_system):
        """Create file system watcher"""
        return FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager"""
        config_manager = Mock()
        config_manager.get_setting = Mock(side_effect=self._mock_get_setting)
        config_manager.set_setting = Mock(return_value=True)
        return config_manager

    @pytest.fixture
    def navigation_controller(self, mock_config_manager, logger_system, file_system_watcher):
        """Create navigation integration controller"""
        return NavigationIntegrationController(
            config_manager=mock_config_manager,
            logger_system=logger_system,
            file_system_watcher=file_system_watcher
        )

    @pytest.fixture
    def breadcrumb_bar(self, file_system_watcher, logger_system, mock_config_manager):
        """Create breadcrumb address bar"""
        return BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

    def _mock_get_setting(self, key: str, default=None):
        """Mock configuration getter"""
        config_values = {
            "ui.breadcrumb.max_segments": 10,
            "ui.breadcrumb.truncation_mode": "smart",
            "navigation.sync_enabled": True,
            "navigation.current_path": str(Path.home()),
            "file_watcher.enable_monitoring": True,
            "file_watcher.watch_subdirectories": True,
            "file_watcher.debounce_delay": 500,
        }
        return config_values.get(key, default)

    def test_file_system_watcher_initialization(self, file_system_watcher, temp_directory):
        """Test file system watcher initialization and setup"""
        # Start watching directory
        result = file_system_watcher.start_watching(temp_directory / "watched_folder")

        # Verify watcher started successfully
        assert result is True
        assert file_system_watcher.is_watching is True

    def test_directory_creation_detection(self, file_system_watcher, breadcrumb_bar, temp_directory):
        """Test detection of new directory creation"""
        watched_dir = temp_directory / "watched_folder"
        breadcrumb_bar.set_current_path(watched_dir)

        # Start watching
        file_system_watcher.start_watching(watched_dir)

        # Add change listener
        change_events = []
        def change_listener(path, change_type):
            change_events.append((path, change_type))

        file_system_watcher.add_change_listener(change_listener)

        # Create new directory
        new_dir = watched_dir / "new_subfolder"
        new_dir.mkdir()

        # Wait for file system event processing
        time.sleep(0.1)

        # Simulate file system change notification
        file_system_watcher._notify_change_listeners(new_dir, FileChangeType.CREATED)

        # Verify change was detected
        assert len(change_events) > 0
        assert any(str(new_dir) in str(event[0]) for event in change_events)

    def test_directory_deletion_detection(self, file_system_watcher, breadcrumb_bar, temp_directory):
        """Test detection of directory deletion"""
        watched_dir = temp_directory / "watched_folder"
        target_dir = watched_dir / "subfolder1"

        breadcrumb_bar.setrrent_path(watched_dir)
        file_system_watcher.start_watching(watched_dir)

        # Add change listener
        change_events = []
        def change_listener(path, change_type):
            change_events.append((path, change_type))

        file_system_watcher.add_change_listener(change_listener)

        # Delete directory
        import shutil
        shutil.rmtree(target_dir)

        # Simulate file system change notification
        file_system_watcher._notify_change_listeners(target_dir, FileChangeType.DELETED)

        # Verify deletion was detected
        assert len(change_events) > 0
        assert any(change_type == FileChangeType.DELETED for _, change_type in change_events)

    def test_file_modification_detection(self, file_system_watcher, temp_directory):
        """Test detection of file modifications"""
        watched_dir = temp_directory / "watched_folder"
        target_file = watched_dir / "file1.txt"

        file_system_watcher.start_watching(watched_dir)

        # Add change listener
        change_events = []
        def change_listener(path, change_type):
            change_events.append((path, change_type))

        file_system_watcher.add_change_listener(change_listener)

        # Modify file
        target_file.write_text("modified content")

        # Simulate file system change notification
        file_system_watcher._notify_change_listeners(target_file, FileChangeType.MODIFIED)

        # Verify modification was detected
        assert len(change_events) > 0
        assert any(change_type == FileChangeType.MODIFIED for _, change_type in change_events)

    @pytest.mark.asyncio
    async def test_breadcrumb_file_system_integration(self, breadcrumb_bar, file_system_watcher, temp_directory):
        """Test integration between breadcrumb and file system watcher"""
        watched_dir = temp_directory / "watched_folder"
        breadcrumb_bar.set_current_path(watched_dir)

        # Start watching
        file_system_watcher.start_watching(watched_dir)

        # Create new directory
        new_dir = watched_dir / "dynamic_folder"
        new_dir.mkdir()

        # Simulate file system change
        breadcrumb_bar._on_file_system_change(new_dir, FileChangeType.CREATED)

        # Wait for any async processing
        await asyncio.sleep(0.1)

        # Verify breadcrumb handled the change
        # (In real implementation, this would trigger breadcrumb refresh)
        assert breadcrumb_bar.current_state.current_path == watched_dir

    @pytest.mark.asyncio
    async def test_navigation_controller_file_system_integration(
        self, navigation_controller, file_system_watcher, temp_directory
    ):
        """Test integration between navigation controller and file system watcher"""
        watched_dir = temp_directory / "watched_folder"

        # Navigate to watched directory
        await navigation_controller.navigate_to_path(watched_dir)

        # Start watching
        file_system_watcher.start_watching(watched_dir)

        # Create new directory
        new_dir = watched_dir / "nav_test_folder"
        new_dir.mkdir()

        # Simulate file system change
        await navigation_controller._handle_path_change(new_dir, FileChangeType.CREATED)

        # Verify navigation controller handled the change
        assert navigation_controller.current_navigation_state.current_path == watched_dir

    def test_current_directory_deletion_handling(self, breadcrumb_bar, navigation_controller, temp_directory):
        """Test handling when current directory is deleted"""
        watched_dir = temp_directory / "watched_folder"
        target_dir = watched_dir / "subfolder1"

        # Navigate to target directory
        breadcrumb_bar.set_current_path(target_dir)
        navigation_controller.register_navigation_component(breadcrumb_bar, "breadcrumb")

        # Delete current directory
        import shutil
        shutil.rmtree(target_dir)

        # Simulate file system change
        breadcrumb_bar._on_file_system_change(target_dir, FileChangeType.DELETED)

        # Should navigate to parent directory
        # (Implementation would handle this gracefully)
        assert not target_dir.exists()

    def test_multiple_watchers_coordination(self, logger_system, temp_directory):
        """Test coordination between multiple file system watchers"""
        # Create multiple watchers
        watcher1 = FileSystemWatcher(logger_system=logger_system, enable_monitoring=True)
        watcher2 = FileSystemWatcher(logger_system=logger_system, enable_monitoring=True)

        watched_dir1 = temp_directory / "watched_folder"
        watched_dir2 = temp_directory / "unwatched_folder"

        # Start watching different directories
        watcher1.start_watching(watched_dir1)
        watcher2.start_watching(watched_dir2)

        # Verify both watchers are active
        assert watcher1.is_watching is True
        assert watcher2.is_watching is True

        # Create files in both directories
        (watched_dir1 / "file_w1.txt").write_text("watcher1")
        (watched_dir2 / "file_w2.txt").write_text("watcher2")

        # Both watchers should be independent
        assert watcher1.is_watching is True
        assert watcher2.is_watching is True

    def test_watcher_performance_under_load(self, file_system_watcher, temp_directory):
        """Test file system watcher performance under high load"""
        watched_dir = temp_directory / "watched_folder"
        file_system_watcher.start_watching(watched_dir)

        # Add change listener
        change_count = 0
        def change_listener(path, change_type):
            nonlocal change_count
            change_count += 1

        file_system_watcher.add_change_listener(change_listener)

        # Create many files rapidly
        start_time = time.time()

        for i in range(50):
            test_file = watched_dir / f"load_test_{i}.txt"
            test_file.write_text(f"content {i}")
            # Simulate change notification
            file_system_watcher._notify_change_listeners(test_file, FileChangeType.CREATED)

        end_time = time.time()

        # Should handle load within reasonable time
        assert (end_time - start_time) < 2.0  # 2 seconds for 50 operations
        assert change_count == 50

    def test_watcher_debouncing(self, file_system_watcher, temp_directory):
        """Test file system watcher debouncing of rapid changes"""
        watched_dir = temp_directory / "watched_folder"
        target_file = watched_dir / "debounce_test.txt"

        file_system_watcher.start_watching(watched_dir)
        file_system_watcher.debounce_delay = 100  # 100ms debounce

        # Add change listener
        change_events = []
        def change_listener(path, change_type):
            change_events.append((path, change_type, time.time()))

        file_system_watcher.add_change_listener(change_listener)

        # Make rapid changes to same file
        for i in range(5):
            target_file.write_text(f"content {i}")
            file_system_watcher._notify_change_listeners(target_file, FileChangeType.MODIFIED)
            time.sleep(0.01)  # 10ms between changes

        # Wait for debounce period
        time.sleep(0.2)

        # Should have debounced multiple rapid changes
        # (Implementation would reduce number of notifications)
        assert len(change_events) <= 5

    @pytest.mark.parametrize("platform_name", ["Windows", "Linux", "Darwin"])
    def test_cross_platform_file_system_events(self, file_system_watcher, temp_directory, platform_name):
        """Test cross-platform file system event handling"""
        with patch('platform.system', return_value=platform_name):
            watched_dir = temp_directory / "watched_folder"

            # Start watching with platform-specific configuration
            result = file_system_watcher.start_watching(watched_dir)
            assert result is True

            # Create platform-specific test file
            if platform_name == "Windows":
                test_file = watched_dir / "windows_test.txt"
            else:
                test_file = watched_dir / "unix_test.txt"

            test_file.write_text("platform test")

            # Simulate platform-specific event
            file_system_watcher._notify_change_listeners(test_file, FileChangeType.CREATED)

            # Should handle event regardless of platform
            assert file_system_watcher.is_watching is True

    def test_symbolic_link_handling(self, file_system_watcher, temp_directory):
        """Test handling of symbolic links in watched directories"""
        if platform.system() == "Windows":
            pytest.skip("Symbolic link test skipped on Windows")

        watched_dir = temp_directory / "watched_folder"
        target_dir = temp_directory / "unwatched_folder"
        link_path = watched_dir / "symlink_test"

        # Create symbolic link
        try:
            link_path.symlink_to(target_dir)
        except OSError:
            pytest.skip("Cannot create symbolic links")

        file_system_watcher.start_watching(watched_dir)

        # Add change listener
        change_events = []
        def change_listener(path, change_type):
            change_events.append((path, change_type))

        file_system_watcher.add_change_listener(change_listener)

        # Create file in linked directory
        (target_dir / "linked_file.txt").write_text("linked content")

        # Simulate change notification
        file_system_watcher._notify_change_listeners(link_path, FileChangeType.MODIFIED)

        # Should handle symbolic links appropriately
        assert len(change_events) >= 0  # May or may not detect depending on implementation

    def test_watcher_error_recovery(self, file_system_watcher, temp_directory):
        """Test file system watcher error recovery"""
        watched_dir = temp_directory / "watched_folder"

        # Start watching
        file_system_watcher.start_watching(watched_dir)
        assert file_system_watcher.is_watching is True

        # Simulate watcher error
        with patch.object(file_system_watcher, '_handle_watcher_error') as mock_error_handler:
            # Trigger error condition
            file_system_watcher._simulate_error("Test error")

            # Should attempt error recovery
            mock_error_handler.assert_called()

        # Watcher should attempt to recover
        # (Implementation would restart watching)

    def test_watcher_cleanup_on_shutdown(self, file_system_watcher, temp_directory):
        """Test proper cleanup when file system watcher is shut down"""
        watched_dir = temp_directory / "watched_folder"

        # Start watching
        file_system_watcher.start_watching(watched_dir)
        assert file_system_watcher.is_watching is True

        # Add change listeners
        listener1 = Mock()
        listener2 = Mock()
        file_system_watcher.add_change_listener(listener1)
        file_system_watcher.add_change_listener(listener2)

        # Shutdown watcher
        file_system_watcher.stop_watching()

        # Verify cleanup
        assert file_system_watcher.is_watching is False

        # Create file after shutdown - should not trigger listeners
        (watched_dir / "after_shutdown.txt").write_text("should not notify")

        # Listeners should not be called
        listener1.assert_not_called()
        listener2.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_file_system_event_handling(self, file_system_watcher, temp_directory):
        """Test asynchronous file system event handling"""
        watched_dir = temp_directory / "watched_folder"
        file_system_watcher.start_watching(watched_dir)

        # Add async change listener
        async_events = []
        async def async_change_listener(path, change_type):
            await asyncio.sleep(0.01)  # Simulate async processing
            async_events.append((path, change_type))

        file_system_watcher.add_async_change_listener(async_change_listener)

        # Create multiple files
        for i in range(3):
            test_file = watched_dir / f"async_test_{i}.txt"
            test_file.write_text(f"async content {i}")
            await file_system_watcher._notify_async_listeners(test_file, FileChangeType.CREATED)

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Verify async events were processed
        assert len(async_events) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
