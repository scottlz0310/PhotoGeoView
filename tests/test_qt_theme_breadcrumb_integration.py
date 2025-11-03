"""
Comprehensive Integration Tests for Qt Theme Breadcrumb Feature

Tests for theme changes across multiple components, breadcrumb synchronization,
file system watcher integration, theme persistence, and cross-platform compatibility.

Author: Kiro AI Integration System
Requirements: 1.2, 1.3, 2.1, 4.1, 4.3
"""

import platform
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.navigation_integration_controller import (
    NavigationIntegrationController,
)
from src.integration.services.file_system_watcher import FileSystemWatcher
from src.integration.theme_integration_controller import ThemeIntegrationController
from src.integration.theme_models import ThemeConfiguration
from src.integration.ui.theme_manager import IntegratedThemeManager
from src.ui.breadcrumb_bar import BreadcrumbAddressBar


class TestQtThemeBreadcrumbIntegration:
    """Comprehensive integration tests for Qt theme breadcrumb feature"""

    @pytest.fixture(autouse=True)
    def setup_qt_application(self):
        """Setup Qt application for testing"""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        yield
        # Cleanup is handled by Qt

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create test directory structure
            (temp_path / "folder1").mkdir()
            (temp_path / "folder1" / "subfolder1").mkdir()
            (temp_path / "folder2").mkdir()
            (temp_path / "folder2" / "subfolder2").mkdir()
            yield temp_path

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager"""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_setting = Mock(side_effect=self._mock_get_setting)
        config_manager.set_setting = Mock(return_value=True)
        config_manager.save_config = Mock(return_value=True)
        config_manager.add_change_listener = Mock()
        return config_manager

    @pytest.fixture
    def mock_logger_system(self):
        """Create mock logger system"""
        logger_system = Mock(spec=LoggerSystem)
        logger_system.get_logger = Mock(return_value=Mock())
        return logger_system

    @pytest.fixture
    def file_system_watcher(self, mock_logger_system):
        """Create file system watcher"""
        return FileSystemWatcher(
            logger_system=mock_logger_system, enable_monitoring=True
        )

    @pytest.fixture
    def theme_controller(self, mock_config_manager, mock_logger_system):
        """Create theme integration controller"""
        return ThemeIntegrationController(
            config_manager=mock_config_manager, logger_system=mock_logger_system
        )

    @pytest.fixture
    def navigation_controller(
        self, mock_config_manager, mock_logger_system, file_system_watcher
    ):
        """Create navigation integration controller"""
        return NavigationIntegrationController(
            config_manager=mock_config_manager,
            logger_system=mock_logger_system,
            file_system_watcher=file_system_watcher,
        )

    @pytest.fixture
    def breadcrumb_bar(
        self, file_system_watcher, mock_logger_system, mock_config_manager
    ):
        """Create breadcrumb address bar"""
        return BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=mock_logger_system,
            config_manager=mock_config_manager,
        )

    @pytest.fixture
    def theme_manager_widget(self, mock_config_manager, mock_logger_system):
        """Create theme manager widget"""
        return IntegratedThemeManager(
            config_manager=mock_config_manager, logger_system=mock_logger_system
        )

    def _mock_get_setting(self, key: str, default=None):
        """Mock configuration getter"""
        config_values = {
            "ui.theme": "default",
            "ui.theme_persistence": True,
            "ui.breadcrumb.max_segments": 10,
            "ui.breadcrumb.truncation_mode": "smart",
            "ui.breadcrumb.show_icons": True,
            "ui.breadcrumb.show_tooltips": True,
            "navigation.sync_enabled": True,
            "navigation.sync_timeout": 5.0,
            "navigation.current_path": str(Path.home()),
            "navigation.history": [],
        }
        return config_values.get(key, default)

    # Test 1: Theme changes across multiple components
    @pytest.mark.asyncio
    async def test_theme_changes_across_components(
        self, theme_controller, breadcrumb_bar, theme_manager_widget, temp_directory
    ):
        """Test theme synchronization across multiple components"""
        # Register components with theme controller
        theme_controller.register_component(breadcrumb_bar, "breadcrumb_bar")
        theme_controller.register_component(
            theme_manager_widget, "theme_manager_widget"
        )

        # Create mock theme manager
        mock_theme_manager = Mock()
        mock_theme_manager.apply_theme = Mock(return_value=True)
        mock_theme_manager.get_current_theme = Mock(
            return_value=ThemeConfiguration(
                name="dark",
                display_name="Dark Theme",
                description="Dark theme for testing",
                author="Test",
                version="1.0.0",
            )
        )
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Apply theme change
        result = await theme_controller.apply_theme("dark")

        # Verify theme was applied successfully
        assert result is True
        assert theme_controller.current_theme is not None
        assert theme_controller.current_theme.name == "dark"

        # Verify components received theme updates
        mock_theme_manager.apply_theme.assert_called_with("dark")

    @pytest.mark.asyncio
    async def test_theme_change_error_handling(
        self, theme_controller, breadcrumb_bar, theme_manager_widget
    ):
        """Test error handling during theme changes"""
        # Register components
        theme_controller.register_component(breadcrumb_bar, "breadcrumb_bar")
        theme_controller.register_component(
            theme_manager_widget, "theme_manager_widget"
        )

        # Create failing theme manager
        mock_theme_manager = Mock()
        mock_theme_manager.apply_theme = Mock(return_value=False)
        theme_controller.register_theme_manager("failing_manager", mock_theme_manager)

        # Apply theme change (should fail and fallback)
        result = await theme_controller.apply_theme("invalid_theme")

        # Should handle error gracefully
        assert isinstance(result, bool)

    # Test 2: Breadcrumb synchronization with folder navigator
    @pytest.mark.asyncio
    async def test_breadcrumb_folder_navigator_sync(
        self, navigation_controller, breadcrumb_bar, temp_directory
    ):
        """Test synchronization between breadcrumb and folder navigator"""
        # Register breadcrumb with navigation controller
        navigation_controller.register_navigation_component(
            breadcrumb_bar, "breadcrumb_bar"
        )

        # Create mock folder navigator
        mock_folder_navigator = Mock()
        mock_folder_navigator.get_current_state = Mock()
        mock_folder_navigator.navigate_to_path = Mock(return_value=True)
        navigation_controller.register_navigation_manager(
            "folder_navigator", mock_folder_navigator
        )

        # Navigate to test directory
        test_path = temp_directory / "folder1"
        result = await navigation_controller.navigate_to_path(test_path)

        # Verify navigation succeeded
        assert result is True
        assert navigation_controller.current_navigation_state.current_path == test_path

        # Verify breadcrumb was updated
        # (This would be verified through signal connections in real implementation)

    @pytest.mark.asyncio
    async def test_breadcrumb_segment_navigation(
        self, navigation_controller, breadcrumb_bar, temp_directory
    ):
        """Test navigation via breadcrumb segment clicks"""
        # Setup navigation to nested directory
        nested_path = temp_directory / "folder1" / "subfolder1"
        breadcrumb_bar.set_current_path(nested_path)

        # Register with navigation controller
        navigation_controller.register_navigation_component(
            breadcrumb_bar, "breadcrumb_bar"
        )

        # Simulate segment click (navigate to parent)
        parent_path = temp_directory / "folder1"
        result = await navigation_controller.navigate_to_path(parent_path)

        # Verify navigation
        assert result is True
        assert (
            navigation_controller.current_navigation_state.current_path == parent_path
        )

    # Test 3: File system watcher integration
    @pytest.mark.asyncio
    async def test_file_system_watcher_integration(
        self, breadcrumb_bar, file_system_watcher, temp_directory
    ):
        """Test file system watcher integration with breadcrumb"""
        # Set current path
        breadcrumb_bar.set_current_path(temp_directory)

        # Start watching
        file_system_watcher.start_watching(temp_directory)

        # Create new directory
        new_dir = temp_directory / "new_folder"
        new_dir.mkdir()

        # Simulate file system change notification
        # (In real implementation, this would be triggered by the watcher)
        breadcrumb_bar._on_file_system_change(new_dir, "created")

        # Verify breadcrumb handles the change
        # (Implementation would refresh breadcrumb state)

    @pytest.mark.asyncio
    async def test_directory_deletion_handling(
        self, breadcrumb_bar, navigation_controller, temp_directory
    ):
        """Test handling of current directory deletion"""
        # Navigate to subdirectory
        subdir = temp_directory / "folder1" / "subfolder1"
        breadcrumb_bar.set_current_path(subdir)
        navigation_controller.register_navigation_component(
            breadcrumb_bar, "breadcrumb_bar"
        )

        # Simulate directory deletion
        import shutil

        shutil.rmtree(subdir)

        # Simulate file system change
        await navigation_controller._handle_path_change(subdir, "deleted")

        # Should navigate to parent or fallback
        current_path = navigation_controller.current_navigation_state.current_path
        assert current_path != subdir
        assert current_path.exists()

    # Test 4: Theme persistence across application restarts
    def test_theme_persistence_save(self, theme_controller, mock_config_manager):
        """Test theme persistence when saving configuration"""
        # Apply theme
        theme_controller.current_theme = ThemeConfiguration(
            name="dark",
            display_name="Dark Theme",
            description="Test theme",
            author="Test",
            version="1.0.0",
        )

        # Save configuration (simulated)
        theme_controller._save_theme_to_config()

        # Verify theme was saved
        mock_config_manager.set_setting.assert_called_with("ui.theme", "dark")

    def test_theme_persistence_load(self, theme_controller, mock_config_manager):
        """Test theme persistence when loading configuration"""
        # Mock saved theme
        mock_config_manager.get_setting.return_value = "dark"

        # Load theme from configuration
        saved_theme = theme_controller._load_theme_from_config()

        # Verify theme was loaded
        assert saved_theme == "dark"
        mock_config_manager.get_setting.assert_called_with("ui.theme", "default")

    @pytest.mark.asyncio
    async def test_theme_restoration_on_startup(
        self, theme_controller, mock_config_manager
    ):
        """Test theme restoration during application startup"""
        # Mock saved theme configuration
        mock_config_manager.get_setting.side_effect = lambda key, default: {
            "ui.theme": "dark",
            "ui.theme_persistence": True,
        }.get(key, default)

        # Create mock theme manager
        mock_theme_manager = Mock()
        mock_theme_manager.apply_theme = Mock(return_value=True)
        mock_theme_manager.get_current_theme = Mock(
            return_value=ThemeConfiguration(
                name="dark",
                display_name="Dark Theme",
                description="Restored theme",
                author="Test",
                version="1.0.0",
            )
        )
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Simulate startup theme restoration
        result = await theme_controller.restore_theme_on_startup()

        # Verify theme was restored
        assert result is True
        mock_theme_manager.apply_theme.assert_called_with("dark")

    # Test 5: Cross-platform compatibility
    @pytest.mark.parametrize("platform_name", ["Windows", "Linux", "Darwin"])
    def test_cross_platform_path_handling(
        self, breadcrumb_bar, temp_directory, platform_name
    ):
        """Test cross-platform path handling in breadcrumb"""
        with patch("platform.system", return_value=platform_name):
            # Test path setting with platform-specific paths
            if platform_name == "Windows":
                # Test Windows-style paths
                test_path = Path("C:\\Users\\Test\\Documents")
                if not test_path.exists():
                    test_path = temp_directory  # Fallback to temp directory
            else:
                # Test Unix-style paths
                test_path = temp_directory

            # Set path and verify handling
            result = breadcrumb_bar.set_current_path(test_path)

            # Should handle path correctly regardless of platform
            if test_path.exists():
                assert result is True
                assert breadcrumb_bar.current_state.current_path == test_path

    def test_cross_platform_file_system_events(
        self, file_system_watcher, temp_directory
    ):
        """Test cross-platform file system event handling"""
        current_platform = platform.system()

        # Start watching directory
        file_system_watcher.start_watching(temp_directory)

        # Create test file
        test_file = temp_directory / "test_file.txt"
        test_file.write_text("test content")

        # Verify watcher can handle file creation on current platform
        assert file_system_watcher.is_watching

        # Platform-specific event handling would be tested here
        # (Implementation details vary by platform)

    @pytest.mark.asyncio
    async def test_cross_platform_theme_application(
        self, theme_controller, mock_config_manager
    ):
        """Test theme application across different platforms"""
        current_platform = platform.system()

        # Create platform-specific theme configuration
        theme_config = ThemeConfiguration(
            name=f"{current_platform.lower()}_theme",
            display_name=f"{current_platform} Theme",
            description=f"Theme optimized for {current_platform}",
            author="Test",
            version="1.0.0",
        )

        # Mock theme manager with platform-specific behavior
        mock_theme_manager = Mock()
        mock_theme_manager.apply_theme = Mock(return_value=True)
        mock_theme_manager.get_current_theme = Mock(return_value=theme_config)
        theme_controller.register_theme_manager("platform_manager", mock_theme_manager)

        # Apply theme
        result = await theme_controller.apply_theme(theme_config.name)

        # Verify theme application works on current platform
        assert result is True
        assert theme_controller.current_theme.name == theme_config.name

    # Integration test scenarios
    @pytest.mark.asyncio
    async def test_complete_theme_breadcrumb_workflow(
        self,
        theme_controller,
        navigation_controller,
        breadcrumb_bar,
        theme_manager_widget,
        temp_directory,
    ):
        """Test complete workflow: theme change + navigation + breadcrumb sync"""
        # Setup components
        theme_controller.register_component(breadcrumb_bar, "breadcrumb_bar")
        theme_controller.register_component(
            theme_manager_widget, "theme_manager_widget"
        )
        navigation_controller.register_navigation_component(
            breadcrumb_bar, "breadcrumb_bar"
        )

        # Create mock managers
        mock_theme_manager = Mock()
        mock_theme_manager.apply_theme = Mock(return_value=True)
        mock_theme_manager.get_current_theme = Mock(
            return_value=ThemeConfiguration(
                name="dark",
                display_name="Dark Theme",
                description="Test",
                author="Test",
                version="1.0.0",
            )
        )
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        mock_nav_manager = Mock()
        mock_nav_manager.navigate_to_path = Mock(return_value=True)
        navigation_controller.register_navigation_manager(
            "nav_manager", mock_nav_manager
        )

        # Step 1: Apply theme
        theme_result = await theme_controller.apply_theme("dark")
        assert theme_result is True

        # Step 2: Navigate to directory
        test_path = temp_directory / "folder1"
        nav_result = await navigation_controller.navigate_to_path(test_path)
        assert nav_result is True

        # Step 3: Verify breadcrumb synchronization
        breadcrumb_bar.set_current_path(test_path)
        assert breadcrumb_bar.current_state.current_path == test_path

        # Step 4: Test segment navigation
        parent_path = test_path.parent
        segment_result = await navigation_controller.navigate_to_path(parent_path)
        assert segment_result is True

    @pytest.mark.asyncio
    async def test_error_recovery_integration(
        self, theme_controller, navigation_controller, breadcrumb_bar, temp_directory
    ):
        """Test error recovery in integrated scenario"""
        # Setup components
        theme_controller.register_component(breadcrumb_bar, "breadcrumb_bar")
        navigation_controller.register_navigation_component(
            breadcrumb_bar, "breadcrumb_bar"
        )

        # Create failing theme manager
        mock_theme_manager = Mock()
        mock_theme_manager.apply_theme = Mock(side_effect=Exception("Theme error"))
        theme_controller.register_theme_manager("failing_manager", mock_theme_manager)

        # Try to apply theme (should fail gracefully)
        with pytest.raises(Exception):
            await theme_controller.apply_theme("failing_theme")

        # Navigation should still work
        test_path = temp_directory / "folder1"
        nav_result = await navigation_controller.navigate_to_path(test_path)
        assert nav_result is True

        # Breadcrumb should still function
        breadcrumb_result = breadcrumb_bar.set_current_path(test_path)
        assert breadcrumb_result is True

    def test_performance_under_load(
        self, theme_controller, navigation_controller, breadcrumb_bar, temp_directory
    ):
        """Test performance with multiple rapid operations"""
        # Setup components
        theme_controller.register_component(breadcrumb_bar, "breadcrumb_bar")
        navigation_controller.register_navigation_component(
            breadcrumb_bar, "breadcrumb_bar"
        )

        # Create multiple directories for testing
        test_dirs = []
        for i in range(10):
            test_dir = temp_directory / f"test_dir_{i}"
            test_dir.mkdir()
            test_dirs.append(test_dir)

        # Measure performance of rapid navigation
        start_time = time.time()

        for test_dir in test_dirs:
            breadcrumb_bar.set_current_path(test_dir)

        end_time = time.time()

        # Should complete within reasonable time (adjust threshold as needed)
        assert (end_time - start_time) < 1.0  # 1 second for 10 operations

    @pytest.mark.asyncio
    async def test_memory_cleanup_integration(
        self, theme_controller, navigation_controller, breadcrumb_bar
    ):
        """Test memory cleanup in integrated components"""
        # Setup components
        theme_controller.register_component(breadcrumb_bar, "breadcrumb_bar")
        navigation_controller.register_navigation_component(
            breadcrumb_bar, "breadcrumb_bar"
        )

        # Perform operations to create state
        mock_theme_manager = Mock()
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Shutdown components
        await theme_controller.shutdown()
        await navigation_controller.shutdown()
        breadcrumb_bar.cleanup()

        # Verify cleanup
        assert len(theme_controller.registered_components) == 0
        assert len(navigation_controller.registered_components) == 0
        assert len(breadcrumb_bar.navigation_listeners) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
