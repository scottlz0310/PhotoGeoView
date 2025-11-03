"""
Unit Tests for Navigation Integration Controller

Tests for NavigationIntegrationController functionality including:
- Component registration and management
- Navigation coordination and synchronization
- File system watcher integration
- Error handling for path access and navigation failures
- Performance tracking and optimization

Author: Kiro AI Integration System
Requirements: 2.1, 4.1, 4.2, 4.3, 4.4
"""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.integration.config_manager import ConfigManager
from src.integration.error_handling import IntegratedErrorHandler
from src.integration.logging_system import LoggerSystem
from src.integration.navigation_integration_controller import (
    NavigationIntegrationController,
)
from src.integration.navigation_interfaces import INavigationAware, INavigationManager
from src.integration.navigation_models import NavigationEvent, NavigationState
from src.integration.services.file_system_watcher import (
    FileChangeType,
    FileSystemWatcher,
)


class MockNavigationAware(INavigationAware):
    """Mock navigation-aware component for testing"""

    def __init__(self, component_id: str = "mock_component"):
        self.component_id = component_id
        self.navigation_events = []
        self.supported_events = ["navigate", "refresh", "back", "forward"]

    def on_navigation_changed(self, event: NavigationEvent) -> None:
        """Handle navigation change event"""
        self.navigation_events.append(event)

    def get_supported_navigation_events(self) -> list[str]:
        """Get list of supported navigation event types"""
        return self.supported_events


class MockNavigationManager(INavigationManager):
    """Mock navigation manager for testing"""

    def __init__(self, manager_id: str = "mock_manager"):
        self.manager_id = manager_id
        self.current_state = NavigationState(current_path=Path.home())
        self.navigation_listeners = []

    def get_current_state(self) -> NavigationState:
        """Get current navigation state"""
        return self.current_state

    def navigate_to_path(self, path: Path) -> bool:
        """Navigate to a specific path"""
        try:
            if path.exists() and path.is_dir():
                self.current_state.navigate_to_path(path)
                return True
            return False
        except Exception:
            return False

    def navigate_to_segment(self, segment_index: int) -> bool:
        """Navigate to a specific breadcrumb segment"""
        return True

    def go_back(self) -> bool:
        """Navigate backward in history"""
        return self.current_state.go_back()

    def go_forward(self) -> bool:
        """Navigate forward in history"""
        return self.current_state.go_forward()

    def go_up(self) -> bool:
        """Navigate to parent directory"""
        return self.current_state.go_up()

    def refresh(self) -> bool:
        """Refresh current navigation state"""
        self.current_state.refresh()
        return True

    def add_navigation_listener(self, callback) -> bool:
        """Add navigation event listener"""
        if callback not in self.navigation_listeners:
            self.navigation_listeners.append(callback)
            return True
        return False

    def remove_navigation_listener(self, callback) -> bool:
        """Remove navigation event listener"""
        if callback in self.navigation_listeners:
            self.navigation_listeners.remove(callback)
            return True
        return False

    def get_navigation_history(self) -> list[Path]:
        """Get navigation history"""
        return self.current_state.history.copy()

    def clear_history(self) -> bool:
        """Clear navigation history"""
        self.current_state.history.clear()
        return True


class TestNavigationIntegrationController(unittest.TestCase):
    """Test cases for NavigationIntegrationController"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)

        # Create mock dependencies
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)
        self.mock_file_system_watcher = Mock(spec=FileSystemWatcher)
        self.mock_error_handler = Mock(spec=IntegratedErrorHandler)

        # Configure mock logger
        self.mock_logger = Mock()
        self.mock_logger_system.get_logger.return_value = self.mock_logger

        # Configure mock config manager
        self.mock_config_manager.get_setting.side_effect = self._mock_get_setting
        self.mock_config_manager.set_setting = Mock()
        self.mock_config_manager.save_config = Mock()
        self.mock_config_manager.add_change_listener = Mock()

        # Configure mock file system watcher
        self.mock_file_system_watcher.is_watching = False
        self.mock_file_system_watcher.add_change_listener = Mock()
        self.mock_file_system_watcher.start_watching = Mock(return_value=True)
        self.mock_file_system_watcher.stop_watching = Mock(return_value=True)

        # Default configuration values
        self.config_values = {
            "navigation.sync_enabled": True,
            "navigation.sync_timeout": 5.0,
            "navigation.max_retry_attempts": 3,
            "navigation.max_history_size": 50,
            "navigation.fallback_path": str(Path.home()),
            "navigation.current_path": str(self.test_path),
            "navigation.history": [str(self.test_path)],
        }

        # Create controller instance
        self.controller = NavigationIntegrationController(
            config_manager=self.mock_config_manager,
            logger_system=self.mock_logger_system,
            file_system_watcher=self.mock_file_system_watcher,
            error_handler=self.mock_error_handler,
        )

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _mock_get_setting(self, key: str, default=None):
        """Mock configuration getter"""
        return self.config_values.get(key, default)

    # Test Initialization

    def test_controller_initialization(self):
        """Test controller initialization"""
        self.assertIsNotNone(self.controller)
        self.assertIsNotNone(self.controller.current_navigation_state)
        self.assertEqual(len(self.controller.registered_components), 0)
        self.assertEqual(len(self.controller.navigation_managers), 0)
        self.assertTrue(self.controller.sync_enabled)

    def test_initialization_with_invalid_config(self):
        """Test initialization with invalid configuration"""
        # Set invalid current path
        self.config_values["navigation.current_path"] = "/non/existent/path"

        controller = NavigationIntegrationController(
            config_manager=self.mock_config_manager,
            logger_system=self.mock_logger_system,
            file_system_watcher=self.mock_file_system_watcher,
            error_handler=self.mock_error_handler,
        )

        # Should fallback to home directory
        self.assertIsNotNone(controller.current_navigation_state)

    # Test Component Registration

    def test_register_navigation_component(self):
        """Test registering navigation-aware components"""
        component = MockNavigationAware("test_component")

        # Register component
        result = self.controller.register_navigation_component(
            component, "test_component"
        )

        self.assertTrue(result)
        self.assertIn(component, self.controller.registered_components)
        self.assertIn("test_component", self.controller.component_registry)
        self.assertEqual(
            self.controller.component_registry["test_component"], component
        )

    def test_register_duplicate_component(self):
        """Test registering the same component twice"""
        component = MockNavigationAware("test_component")

        # Register component twice
        result1 = self.controller.register_navigation_component(
            component, "test_component"
        )
        result2 = self.controller.register_navigation_component(
            component, "test_component"
        )

        self.assertTrue(result1)
        self.assertTrue(result2)  # Should still return True
        self.assertEqual(len(self.controller.registered_components), 1)

    def test_unregister_navigation_component(self):
        """Test unregistering navigation-aware components"""
        component = MockNavigationAware("test_component")

        # Register and then unregister component
        self.controller.register_navigation_component(component, "test_component")
        result = self.controller.unregister_navigation_component(
            component, "test_component"
        )

        self.assertTrue(result)
        self.assertNotIn(component, self.controller.registered_components)
        self.assertNotIn("test_component", self.controller.component_registry)

    def test_register_navigation_manager(self):
        """Test registering navigation managers"""
        manager = MockNavigationManager("test_manager")

        # Register manager
        result = self.controller.register_navigation_manager("test_manager", manager)

        self.assertTrue(result)
        self.assertIn("test_manager", self.controller.navigation_managers)
        self.assertEqual(self.controller.navigation_managers["test_manager"], manager)

    def test_unregister_navigation_manager(self):
        """Test unregistering navigation managers"""
        manager = MockNavigationManager("test_manager")

        # Register and then unregister manager
        self.controller.register_navigation_manager("test_manager", manager)
        result = self.controller.unregister_navigation_manager("test_manager")

        self.assertTrue(result)
        self.assertNotIn("test_manager", self.controller.navigation_managers)

    # Test Navigation Coordination

    @pytest.mark.asyncio
    async def test_navigate_to_path_success(self):
        """Test successful navigation to a path"""
        # Create test directory
        test_dir = self.test_path / "test_navigation"
        test_dir.mkdir()

        # Navigate to path
        result = await self.controller.navigate_to_path(test_dir)

        self.assertTrue(result)
        self.assertEqual(
            self.controller.current_navigation_state.current_path, test_dir
        )

    @pytest.mark.asyncio
    async def test_navigate_to_invalid_path(self):
        """Test navigation to invalid path"""
        invalid_path = Path("/non/existent/path")

        # Navigate to invalid path
        result = await self.controller.navigate_to_path(invalid_path)

        # Should fail and fallback
        self.assertFalse(result)

    @pytest.mark.asyncio
    async def test_navigation_synchronization(self):
        """Test navigation synchronization across components"""
        # Register test components
        component1 = MockNavigationAware("component1")
        component2 = MockNavigationAware("component2")

        self.controller.register_navigation_component(component1, "component1")
        self.controller.register_navigation_component(component2, "component2")

        # Create test directory
        test_dir = self.test_path / "sync_test"
        test_dir.mkdir()

        # Navigate to path
        await self.controller.navigate_to_path(test_dir)

        # Check that components received navigation events
        self.assertGreater(len(component1.navigation_events), 0)
        self.assertGreater(len(component2.navigation_events), 0)

        # Check event details
        event1 = component1.navigation_events[-1]
        event2 = component2.navigation_events[-1]

        self.assertEqual(event1.target_path, test_dir)
        self.assertEqual(event2.target_path, test_dir)
        self.assertTrue(event1.success)
        self.assertTrue(event2.success)

    @pytest.mark.asyncio
    async def test_navigation_with_source_component(self):
        """Test navigation initiated by a specific component"""
        # Register test components
        source_component = MockNavigationAware("source")
        target_component = MockNavigationAware("target")

        self.controller.register_navigation_component(source_component, "source")
        self.controller.register_navigation_component(target_component, "target")

        # Create test directory
        test_dir = self.test_path / "source_test"
        test_dir.mkdir()

        # Navigate with source component specified
        await self.controller.navigate_to_path(test_dir, "source")

        # Source component should not receive event (to avoid circular updates)
        # Target component should receive event
        self.assertGreater(len(target_component.navigation_events), 0)

    # Test File System Watcher Integration

    def test_file_system_watcher_setup(self):
        """Test file system watcher integration setup"""
        # Verify watcher listener was added
        self.mock_file_system_watcher.add_change_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_system_change_handling(self):
        """Test handling of file system changes"""
        # Create test directory
        test_dir = self.test_path / "fs_test"
        test_dir.mkdir()

        # Set current navigation state
        await self.controller.navigate_to_path(test_dir)

        # Simulate file system change
        changed_file = test_dir / "test_file.txt"
        self.controller._on_file_system_change(changed_file, FileChangeType.CREATED)

        # Should handle the change without errors
        # (Detailed testing would require more complex setup)

    @pytest.mark.asyncio
    async def test_directory_deletion_handling(self):
        """Test handling of current directory deletion"""
        # Create test directory structure
        parent_dir = self.test_path / "parent"
        child_dir = parent_dir / "child"
        parent_dir.mkdir()
        child_dir.mkdir()

        # Navigate to child directory
        await self.controller.navigate_to_path(child_dir)

        # Simulate directory deletion
        await self.controller._handle_path_change(child_dir, FileChangeType.DELETED)

        # Should navigate to parent or fallback
        current_path = self.controller.current_navigation_state.current_path
        self.assertNotEqual(current_path, child_dir)

    # Test Error Handling

    @pytest.mark.asyncio
    async def test_path_validation_timeout(self):
        """Test path validation with timeout"""
        # Mock path validation to simulate timeout
        with patch.object(self.controller, "_sync_validate_path") as mock_validate:
            mock_validate.side_effect = lambda path: asyncio.sleep(10)  # Long delay

            # Set short timeout
            self.controller.path_access_timeout = 0.1

            result = await self.controller._validate_path_access(Path("/test"))

            self.assertFalse(result)

    @pytest.mark.asyncio
    async def test_navigation_error_handling(self):
        """Test navigation error handling"""
        error_listeners = []

        def error_listener(path: str, message: str):
            error_listeners.append((path, message))

        # Add error listener
        self.controller.add_error_listener(error_listener)

        # Trigger navigation error
        await self.controller._handle_navigation_error(
            Path("/invalid"), "Test error", "test_component"
        )

        # Check that error listener was called
        self.assertEqual(len(error_listeners), 1)
        self.assertEqual(error_listeners[0][0], "/invalid")
        self.assertEqual(error_listeners[0][1], "Test error")

    # Test Event Listener Management

    def test_add_navigation_listener(self):
        """Test adding navigation event listeners"""
        listener = Mock()

        result = self.controller.add_navigation_listener(listener)

        self.assertTrue(result)
        self.assertIn(listener, self.controller.navigation_listeners)

    def test_remove_navigation_listener(self):
        """Test removing navigation event listeners"""
        listener = Mock()

        # Add and then remove listener
        self.controller.add_navigation_listener(listener)
        result = self.controller.remove_navigation_listener(listener)

        self.assertTrue(result)
        self.assertNotIn(listener, self.controller.navigation_listeners)

    def test_add_duplicate_listener(self):
        """Test adding the same listener twice"""
        listener = Mock()

        # Add listener twice
        result1 = self.controller.add_navigation_listener(listener)
        result2 = self.controller.add_navigation_listener(listener)

        self.assertTrue(result1)
        self.assertFalse(result2)  # Should return False for duplicate
        self.assertEqual(len(self.controller.navigation_listeners), 1)

    # Test Performance and Statistics

    def test_performance_stats(self):
        """Test performance statistics collection"""
        stats = self.controller.get_performance_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn("navigation_count", stats)
        self.assertIn("average_navigation_time", stats)
        self.assertIn("registered_components", stats)
        self.assertIn("registered_managers", stats)
        self.assertIn("history_size", stats)
        self.assertIn("sync_enabled", stats)

    def test_clear_performance_stats(self):
        """Test clearing performance statistics"""
        # Add some fake performance data
        self.controller.navigation_times.append(1.0)
        self.controller.sync_operation_times["test"] = [0.5]

        # Clear stats
        self.controller.clear_performance_stats()

        self.assertEqual(len(self.controller.navigation_times), 0)
        self.assertEqual(len(self.controller.sync_operation_times), 0)

    def test_path_validation_cache(self):
        """Test path validation caching"""
        # Add entries to cache
        self.controller.path_validation_cache["/test1"] = True
        self.controller.path_validation_cache["/test2"] = False

        # Clear cache
        self.controller.clear_path_validation_cache()

        self.assertEqual(len(self.controller.path_validation_cache), 0)

    # Test Navigation History

    @pytest.mark.asyncio
    async def test_navigation_history_update(self):
        """Test navigation history updates"""
        # Create test directories
        dir1 = self.test_path / "dir1"
        dir2 = self.test_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Navigate to directories
        await self.controller.navigate_to_path(dir1)
        await self.controller.navigate_to_path(dir2)

        # Check history
        history = self.controller.get_navigation_history()
        self.assertIn(dir1, history)
        self.assertIn(dir2, history)

    @pytest.mark.asyncio
    async def test_navigation_history_limit(self):
        """Test navigation history size limit"""
        # Set small history limit
        self.controller.max_history_size = 2

        # Create and navigate to multiple directories
        for i in range(5):
            test_dir = self.test_path / f"dir{i}"
            test_dir.mkdir()
            await self.controller.navigate_to_path(test_dir)

        # Check history size
        history = self.controller.get_navigation_history()
        self.assertLessEqual(len(history), 2)

    # Test Configuration Integration

    def test_config_change_handling(self):
        """Test handling of configuration changes"""
        # Simulate configuration change
        self.controller._on_config_changed("navigation.sync_enabled", True, False)

        # Should reload preferences
        # (Detailed verification would require more complex setup)

    # Test Shutdown

    @pytest.mark.asyncio
    async def test_controller_shutdown(self):
        """Test controller shutdown"""
        # Register some components
        component = MockNavigationAware("test")
        self.controller.register_navigation_component(component, "test")

        # Add some listeners
        listener = Mock()
        self.controller.add_navigation_listener(listener)

        # Shutdown controller
        await self.controller.shutdown()

        # Check cleanup
        self.assertEqual(len(self.controller.registered_components), 0)
        self.assertEqual(len(self.controller.component_registry), 0)
        self.assertEqual(len(self.controller.navigation_listeners), 0)

    # Test Edge Cases

    @pytest.mark.asyncio
    async def test_navigation_without_components(self):
        """Test navigation when no components are registered"""
        # Create test directory
        test_dir = self.test_path / "no_components"
        test_dir.mkdir()

        # Navigate without registered components
        result = await self.controller.navigate_to_path(test_dir)

        # Should still succeed
        self.assertTrue(result)
        self.assertEqual(
            self.controller.current_navigation_state.current_path, test_dir
        )

    def test_component_registration_with_exception(self):
        """Test component registration when component raises exception"""

        # Create component that raises exception in on_navigation_changed
        class FaultyComponent(INavigationAware):
            def on_navigation_changed(self, event):
                raise Exception("Test exception")

            def get_supported_navigation_events(self):
                return ["navigate"]

        component = FaultyComponent()

        # Register component (should succeed)
        result = self.controller.register_navigation_component(component, "faulty")

        self.assertTrue(result)
        self.assertIn(component, self.controller.registered_components)

    @pytest.mark.asyncio
    async def test_synchronization_timeout(self):
        """Test synchronization timeout handling"""

        # Create component that takes long time to process
        class SlowComponent(INavigationAware):
            def on_navigation_changed(self, event):
                import time

                time.sleep(10)  # Simulate slow processing

            def get_supported_navigation_events(self):
                return ["navigate"]

        component = SlowComponent()
        self.controller.register_navigation_component(component, "slow")

        # Set short timeout
        self.controller.sync_timeout = 0.1

        # Create test directory
        test_dir = self.test_path / "timeout_test"
        test_dir.mkdir()

        # Navigate (should timeout but still succeed)
        result = await self.controller.navigate_to_path(test_dir)

        # Navigation should still succeed despite timeout
        self.assertTrue(result)


class TestNavigationIntegrationControllerIntegration(unittest.TestCase):
    """Integration tests for NavigationIntegrationController"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)

        # Create real dependencies for integration testing
        self.config_manager = Mock(spec=ConfigManager)
        self.logger_system = LoggerSystem()
        self.file_system_watcher = Mock(spec=FileSystemWatcher)

        # Configure mocks
        self.config_manager.get_setting.side_effect = lambda key, default=None: {
            "navigation.sync_enabled": True,
            "navigation.sync_timeout": 5.0,
            "navigation.max_retry_attempts": 3,
            "navigation.max_history_size": 50,
            "navigation.fallback_path": str(Path.home()),
            "navigation.current_path": str(self.test_path),
            "navigation.history": [],
        }.get(key, default)

        self.config_manager.set_setting = Mock()
        self.config_manager.save_config = Mock()
        self.config_manager.add_change_listener = Mock()

        self.file_system_watcher.is_watching = False
        self.file_system_watcher.add_change_listener = Mock()
        self.file_system_watcher.start_watching = Mock(return_value=True)
        self.file_system_watcher.stop_watching = Mock(return_value=True)

        self.controller = NavigationIntegrationController(
            config_manager=self.config_manager,
            logger_system=self.logger_system,
            file_system_watcher=self.file_system_watcher,
        )

    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_full_navigation_workflow(self):
        """Test complete navigation workflow with multiple components"""
        # Create test directory structure
        dir1 = self.test_path / "workflow_dir1"
        dir2 = self.test_path / "workflow_dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Register multiple components
        component1 = MockNavigationAware("breadcrumb")
        component2 = MockNavigationAware("folder_navigator")
        manager = MockNavigationManager("main_manager")

        self.controller.register_navigation_component(component1, "breadcrumb")
        self.controller.register_navigation_component(component2, "folder_navigator")
        self.controller.register_navigation_manager("main_manager", manager)

        # Perform navigation sequence
        result1 = await self.controller.navigate_to_path(dir1)
        result2 = await self.controller.navigate_to_path(dir2)

        # Verify results
        self.assertTrue(result1)
        self.assertTrue(result2)

        # Check final state
        self.assertEqual(self.controller.current_navigation_state.current_path, dir2)

        # Check component synchronization
        self.assertGreater(len(component1.navigation_events), 0)
        self.assertGreater(len(component2.navigation_events), 0)

        # Check history
        history = self.controller.get_navigation_history()
        self.assertIn(dir1, history)
        self.assertIn(dir2, history)

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error recovery and fallback mechanisms"""
        # Create valid directory
        valid_dir = self.test_path / "valid"
        valid_dir.mkdir()

        # Navigate to valid directory first
        await self.controller.navigate_to_path(valid_dir)

        # Try to navigate to invalid directory
        invalid_dir = Path("/completely/invalid/path")
        result = await self.controller.navigate_to_path(invalid_dir)

        # Should fail but controller should remain functional
        self.assertFalse(result)

        # Should still be able to navigate to valid paths
        another_valid_dir = self.test_path / "another_valid"
        another_valid_dir.mkdir()

        result2 = await self.controller.navigate_to_path(another_valid_dir)
        self.assertTrue(result2)


if __name__ == "__main__":
    # Run tests
    unittest.main()
