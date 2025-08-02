"""
Unit Tests for Error Handling and Fallback Mechanisms

Tests the error handling and fallback mechanisms implemented for task 9
of the qt-theme-breadcrumb specification.

Author: Kiro AI Integration System
Requirements: 1.4, 3.4, 4.2, 4.4
"""

import os
import platform
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.services.file_system_watcher import FileSystemWatcher
from src.integration.theme_models import ThemeConfiguration, ThemeInfo, ThemeType
from src.integration.user_notification_system import (
    NotificationAction,
    NotificationType,
    UserNotification,
    UserNotificationSystem,
)
from src.ui.breadcrumb_bar import BreadcrumbAddressBar
from src.ui.theme_manager import ThemeManagerWidget


class TestThemeErrorHandling(unittest.TestCase):
    """Test theme loading error handling and fallback mechanisms"""

    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=ConfigManager)
        self.logger_system = Mock(spec=LoggerSystem)
        self.logger = Mock()
        self.logger_system.get_logger.return_value = self.logger
        self.notification_system = Mock(spec=UserNotificationSystem)

        self.theme_manager = ThemeManagerWidget(
            config_manager=self.config_manager,
            logger_system=self.logger_system,
            notification_system=self.notification_system
        )

    def test_theme_not_found_fallback(self):
        """Test fallback to default theme when requested theme not found"""
        # Setup
        self.theme_manager.available_themes = {
            "default": ThemeInfo(
                name="default",
                display_name="Default",
                description="Default theme",
                author="PhotoGeoView",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN,
                is_dark=False,
                preview_colors={},
                is_available=True
            )
        }

        # Mock theme configuration loading
        with patch.object(self.theme_manager, '_load_theme_configuration') as mock_load:
            mock_load.return_value = True
            self.theme_manager.current_theme = ThemeConfiguration(
                name="default",
                display_name="Default",
                description="Default theme",
                author="PhotoGeoView",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN
            )

            # Test applying non-existent theme
            result = self.theme_manager.apply_theme("non_existent_theme")

            # Verify fallback was attempted
            self.assertTrue(result)
            self.notification_system.show_theme_error.assert_called_once()

    def test_theme_configuration_load_failure(self):
        """Test handling of theme configuration load failures"""
        # Setup
        self.theme_manager.available_themes = {
            "test_theme": ThemeInfo(
                name="test_theme",
                display_name="Test Theme",
                description="Test theme",
                author="Test",
                version="1.0.0",
                theme_type=ThemeType.CUSTOM,
                is_dark=False,
                preview_colors={},
                is_available=True
            )
        }

        # Mock configuration loading to fail
        with patch.object(self.theme_manager, '_load_theme_configuration') as mock_load:
            mock_load.return_value = False

            # Test applying theme with configuration failure
            result = self.theme_manager.apply_theme("test_theme")

            # Verify error handling
            self.assertFalse(result)
            self.logger.error.assert_called()
            self.notification_system.show_theme_error.assert_called()

    def test_component_application_failure_handling(self):
        """Test handling of component theme application failures"""
        # Setup
        self.theme_manager.available_themes = {
            "test_theme": ThemeInfo(
                name="test_theme",
                display_name="Test Theme",
                description="Test theme",
                author="Test",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN,
                is_dark=False,
                preview_colors={},
                is_available=True
            )
        }

        # Mock theme configuration
        test_theme_config = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="Test theme",
            author="Test",
            version="1.0.0",
            theme_type=ThemeType.BUILT_IN
        )

        # Create mock components - some will fail
        failing_component = Mock()
        failing_component.apply_theme.side_effect = Exception("Component failure")
        working_component = Mock()

        self.theme_manager.registered_components = {failing_component, working_component}

        with patch.object(self.theme_manager, '_load_theme_configuration') as mock_load:
            mock_load.return_value = True
            self.theme_manager.current_theme = test_theme_config

            # Test applying theme with component failures
            result = self.theme_manager.apply_theme("test_theme")

            # Verify partial success handling
            self.assertTrue(result)  # Should succeed if less than 50% fail
            working_component.apply_theme.assert_called_once()

    def test_emergency_default_theme_creation(self):
        """Test creation of emergency default theme when none exists"""
        # Setup - no themes available
        self.theme_manager.available_themes = {}

        # Test emergency theme creation
        self.theme_manager._create_emergency_default_theme()

        # Verify default theme was created
        self.assertIn("default", self.theme_manager.available_themes)
        default_theme = self.theme_manager.available_themes["default"]
        self.assertEqual(default_theme.name, "default")
        self.assertEqual(default_theme.display_name, "Default Light")

    def test_fallback_recursion_prevention(self):
        """Test prevention of infinite recursion in fallback theme application"""
        # Setup
        self.theme_manager.available_themes = {}

        # Set recursion flag
        self.theme_manager._applying_fallback = True

        # Test fallback application
        result = self.theme_manager._apply_fallback_theme()

        # Verify recursion was prevented
        self.assertFalse(result)
        self.logger.error.assert_called_with("Already applying fallback theme, preventing recursion")

    def test_qt_theme_manager_failure_handling(self):
        """Test handling of qt-theme-manager library failures"""
        # Setup
        self.theme_manager.available_themes = {
            "test_theme": ThemeInfo(
                name="test_theme",
                display_name="Test Theme",
                description="Test theme",
                author="Test",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN,
                is_dark=False,
                preview_colors={},
                is_available=True
            )
        }

        # Mock qt-theme-manager to fail
        mock_qt_manager = Mock()
        mock_qt_manager.apply_theme.side_effect = Exception("Qt manager failure")
        self.theme_manager.qt_theme_manager = mock_qt_manager

        test_theme_config = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="Test theme",
            author="Test",
            version="1.0.0",
            theme_type=ThemeType.BUILT_IN
        )

        with patch.object(self.theme_manager, '_load_theme_configuration') as mock_load:
            mock_load.return_value = True
            self.theme_manager.current_theme = test_theme_config

            # Test applying theme with qt-manager failure
            result = self.theme_manager.apply_theme("test_theme")

            # Verify theme still applies despite qt-manager failure
            self.assertTrue(result)
            self.logger.error.assert_called()


class TestBreadcrumbErrorHandling(unittest.TestCase):
    """Test breadcrumb navigation error handling and fallback mechanisms"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_system_watcher = Mock(spec=FileSystemWatcher)
        self.logger_system = Mock(spec=LoggerSystem)
        self.logger = Mock()
        self.logger_system.get_logger.return_value = self.logger
        self.config_manager = Mock(spec=ConfigManager)
        self.notification_system = Mock(spec=UserNotificationSystem)

        self.breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=self.file_system_watcher,
            logger_system=self.logger_system,
            config_manager=self.config_manager,
            notification_system=self.notification_system
        )

    def test_invalid_path_handling(self):
        """Test handling of invalid paths"""
        # Test with non-existent path
        invalid_path = Path("/non/existent/path")

        with patch.object(self.breadcrumb_bar, '_navigate_to_fallback_path') as mock_fallback:
            mock_fallback.return_value = True

            result = self.breadcrumb_bar.set_current_path(invalid_path)

            # Verify error handling
            self.assertTrue(result)  # Should succeed via fallback
            self.notification_system.show_breadcrumb_error.assert_called()
            mock_fallback.assert_called_once()

    def test_permission_denied_handling(self):
        """Test handling of permission denied errors"""
        # Create a temporary directory and remove read permissions
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "restricted"
            test_path.mkdir()

            # Remove read permissions (Unix-like systems)
            if platform.system() != "Windows":
                os.chmod(test_path, 0o000)

                try:
                    with patch.object(self.breadcrumb_bar, '_navigate_to_fallback_path') as mock_fallback:
                        mock_fallback.return_value = True

                        result = self.breadcrumb_bar.set_current_path(test_path)

                        # Verify permission error handling
                        self.assertTrue(result)  # Should succeed via fallback
                        self.notification_system.show_breadcrumb_error.assert_called()

                finally:
                    # Restore permissions for cleanup
                    os.chmod(test_path, 0o755)

    @patch('platform.system')
    def test_network_path_detection_windows(self, mock_platform):
        """Test network path detection on Windows"""
        mock_platform.return_value = "Windows"

        # Test UNC path
        unc_path = Path("\\\\server\\share\\folder")
        self.assertTrue(self.breadcrumb_bar._is_network_path(unc_path))

        # Test local path
        local_path = Path("C:\\local\\folder")
        self.assertFalse(self.breadcrumb_bar._is_network_path(local_path))

    @patch('platform.system')
    def test_network_path_detection_unix(self, mock_platform):
        """Test network path detection on Unix-like systems"""
        mock_platform.return_value = "Linux"

        # Test network mount paths
        mount_path = Path("/mnt/network/folder")
        self.assertTrue(self.breadcrumb_bar._is_network_path(mount_path))

        media_path = Path("/media/network/folder")
        self.assertTrue(self.breadcrumb_bar._is_network_path(media_path))

        # Test local path
        local_path = Path("/home/user/folder")
        self.assertFalse(self.breadcrumb_bar._is_network_path(local_path))

    def test_network_disconnection_handling(self):
        """Test handling of network drive disconnection"""
        network_path = Path("\\\\server\\share\\folder")

        with patch.object(self.breadcrumb_bar, '_is_network_path') as mock_is_network:
            with patch.object(self.breadcrumb_bar, '_is_network_accessible') as mock_accessible:
                with patch.object(self.breadcrumb_bar, '_handle_network_disconnection') as mock_handle:
                    mock_is_network.return_value = True
                    mock_accessible.return_value = False
                    mock_handle.return_value = True

                    result = self.breadcrumb_bar.set_current_path(network_path)

                    # Verify network disconnection handling
                    self.assertTrue(result)
                    self.notification_system.show_breadcrumb_error.assert_called()
                    mock_handle.assert_called_once()

    def test_fallback_path_navigation(self):
        """Test fallback path navigation logic"""
        failed_path = Path("/failed/path")

        with patch.object(self.breadcrumb_bar, '_validate_path_comprehensive') as mock_validate:
            # Mock home directory as valid fallback
            mock_validate.side_effect = lambda p: {
                "valid": p == Path.home(),
                "error_type": None if p == Path.home() else "path_not_found",
                "error_message": None if p == Path.home() else "Path not found"
            }

            with patch.object(self.breadcrumb_bar.current_state, 'navigate_to_path') as mock_navigate:
                mock_navigate.return_value = True

                result = self.breadcrumb_bar._navigate_to_fallback_path(failed_path, "path_not_found")

                # Verify fallback navigation
                self.assertTrue(result)
                mock_navigate.assert_called_with(Path.home())

    def test_fallback_recursion_prevention(self):
        """Test prevention of infinite recursion in fallback navigation"""
        failed_path = Path("/failed/path")

        # Set recursion flag
        self.breadcrumb_bar._navigating_to_fallback = True

        result = self.breadcrumb_bar._navigate_to_fallback_path(failed_path, "test_error")

        # Verify recursion was prevented
        self.assertFalse(result)
        self.logger.error.assert_called_with("Already navigating to fallback, preventing recursion")

    def test_comprehensive_path_validation(self):
        """Test comprehensive path validation"""
        # Test valid path
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_path = Path(temp_dir)
            result = self.breadcrumb_bar._validate_path_comprehensive(valid_path)

            self.assertTrue(result["valid"])
            self.assertIsNone(result["error_type"])

        # Test non-existent path
        invalid_path = Path("/non/existent/path")
        result = self.breadcrumb_bar._validate_path_comprehensive(invalid_path)

        self.assertFalse(result["valid"])
        self.assertEqual(result["error_type"], "path_not_found")

        # Test None path
        result = self.breadcrumb_bar._validate_path_comprehensive(None)

        self.assertFalse(result["valid"])
        self.assertEqual(result["error_type"], "invalid_path")

    def test_navigation_state_update_retry(self):
        """Test retry mechanism for navigation state updates"""
        test_path = Path.home()

        with patch.object(self.breadcrumb_bar.current_state, 'navigate_to_path') as mock_navigate:
            # Fail first two attempts, succeed on third
            mock_navigate.side_effect = [False, False, True]

            result = self.breadcrumb_bar.set_current_path(test_path)

            # Verify retry mechanism worked
            self.assertTrue(result)
            self.assertEqual(mock_navigate.call_count, 3)


class TestUserNotificationSystem(unittest.TestCase):
    """Test user notification system functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=ConfigManager)
        self.logger_system = Mock(spec=LoggerSystem)
        self.logger = Mock()
        self.logger_system.get_logger.return_value = self.logger

        # Mock QApplication for testing
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()

        self.notification_system = UserNotificationSystem(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )

    def test_notification_creation(self):
        """Test creation of user notifications"""
        notification = UserNotification(
            title="Test Title",
            message="Test message",
            notification_type=NotificationType.ERROR,
            details="Test details"
        )

        self.assertEqual(notification.title, "Test Title")
        self.assertEqual(notification.message, "Test message")
        self.assertEqual(notification.notification_type, NotificationType.ERROR)
        self.assertEqual(notification.details, "Test details")
        self.assertIsNotNone(notification.id)
        self.assertIsNotNone(notification.created_at)

    def test_show_error_notification(self):
        """Test showing error notifications"""
        with patch.object(self.notification_system, '_show_message_box') as mock_show:
            notification_id = self.notification_system.show_error(
                "Error Title",
                "Error message",
                details="Error details"
            )

            self.assertIsNotNone(notification_id)
            self.assertIn(notification_id, self.notification_system.active_notifications)
            mock_show.assert_called_once()

    def test_show_theme_error_notification(self):
        """Test showing theme-specific error notifications"""
        with patch.object(self.notification_system, 'show_error') as mock_show_error:
            self.notification_system.show_theme_error(
                "dark_theme",
                "Theme file corrupted",
                fallback_applied=True
            )

            mock_show_error.assert_called_once()
            args, kwargs = mock_show_error.call_args
            self.assertEqual(args[0], "Theme Error")
            self.assertIn("dark_theme", args[1])
            self.assertIn("Default theme has been applied", args[1])

    def test_show_breadcrumb_error_notification(self):
        """Test showing breadcrumb-specific error notifications"""
        with patch.object(self.notification_system, 'show_error') as mock_show_error:
            self.notification_system.show_breadcrumb_error(
                "/network/path",
                "network_disconnected",
                "Network drive disconnected"
            )

            mock_show_error.assert_called_once()
            args, kwargs = mock_show_error.call_args
            self.assertEqual(args[0], "Navigation Error")
            self.assertIn("Network drive disconnected", args[1])

    def test_notification_dismissal(self):
        """Test notification dismissal"""
        notification_id = self.notification_system.show_info("Test", "Test message")

        # Dismiss notification
        result = self.notification_system.dismiss_notification(notification_id)

        self.assertTrue(result)
        self.assertNotIn(notification_id, self.notification_system.active_notifications)
        self.assertEqual(len(self.notification_system.notification_history), 1)

    def test_max_concurrent_notifications(self):
        """Test maximum concurrent notifications limit"""
        self.notification_system.max_concurrent_notifications = 2

        # Show more notifications than the limit
        id1 = self.notification_system.show_info("Test 1", "Message 1")
        id2 = self.notification_system.show_info("Test 2", "Message 2")
        id3 = self.notification_system.show_info("Test 3", "Message 3")

        # Verify oldest notification was dismissed
        self.assertEqual(len(self.notification_system.active_notifications), 2)
        self.assertNotIn(id1, self.notification_system.active_notifications)
        self.assertIn(id2, self.notification_system.active_notifications)
        self.assertIn(id3, self.notification_system.active_notifications)

    def test_notification_actions(self):
        """Test notification actions"""
        action_called = False

        def test_action():
            nonlocal action_called
            action_called = True

        action = NotificationAction("Test Action", test_action, is_primary=True)
        notification = UserNotification(
            title="Test",
            message="Test message",
            actions=[action]
        )

        # Simulate action trigger
        self.notification_system._handle_notification_action(notification.id, action)

        self.assertTrue(action_called)

    def test_configuration_loading(self):
        """Test loading of notification system configuration"""
        self.config_manager.get_setting.side_effect = lambda key, default: {
            "notifications.enabled": True,
            "notifications.system_tray": False,
            "notifications.auto_dismiss_duration": 10,
            "notifications.max_concurrent": 5
        }.get(key, default)

        # Reload configuration
        self.notification_system._load_configuration()

        self.assertTrue(self.notification_system.notifications_enabled)
        self.assertFalse(self.notification_system.show_system_tray)
        self.assertEqual(self.notification_system.auto_dismiss_duration, 10)
        self.assertEqual(self.notification_system.max_concurrent_notifications, 5)

    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'notification_system'):
            self.notification_system.cleanup()


class TestIntegratedErrorHandling(unittest.TestCase):
    """Test integrated error handling across components"""

    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=ConfigManager)
        self.logger_system = Mock(spec=LoggerSystem)
        self.logger = Mock()
        self.logger_system.get_logger.return_value = self.logger

        if not QApplication.instance():
            self.app = QApplication([])

        self.notification_system = UserNotificationSystem(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )

        self.theme_manager = ThemeManagerWidget(
            config_manager=self.config_manager,
            logger_system=self.logger_system,
            notification_system=self.notification_system
        )

        self.file_system_watcher = Mock(spec=FileSystemWatcher)
        self.breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=self.file_system_watcher,
            logger_system=self.logger_system,
            config_manager=self.config_manager,
            notification_system=self.notification_system
        )

    def test_theme_error_notification_integration(self):
        """Test integration between theme manager and notification system"""
        # Setup theme manager with no themes
        self.theme_manager.available_themes = {}

        with patch.object(self.notification_system, 'show_theme_error') as mock_notify:
            result = self.theme_manager.apply_theme("non_existent")

            # Verify notification was shown
            mock_notify.assert_called_once()
            args = mock_notify.call_args[0]
            self.assertEqual(args[0], "non_existent")

    def test_breadcrumb_error_notification_integration(self):
        """Test integration between breadcrumb bar and notification system"""
        invalid_path = Path("/invalid/path")

        with patch.object(self.notification_system, 'show_breadcrumb_error') as mock_notify:
            with patch.object(self.breadcrumb_bar, '_navigate_to_fallback_path') as mock_fallback:
                mock_fallback.return_value = True

                result = self.breadcrumb_bar.set_current_path(invalid_path)

                # Verify notification was shown
                mock_notify.assert_called_once()
                args = mock_notify.call_args[0]
                self.assertEqual(args[0], str(invalid_path))

    def test_error_recovery_workflow(self):
        """Test complete error recovery workflow"""
        # Test theme error recovery
        self.theme_manager.available_themes = {
            "default": ThemeInfo(
                name="default",
                display_name="Default",
                description="Default theme",
                author="PhotoGeoView",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN,
                is_dark=False,
                preview_colors={},
                is_available=True
            )
        }

        with patch.object(self.theme_manager, '_load_theme_configuration') as mock_load:
            mock_load.return_value = True
            self.theme_manager.current_theme = ThemeConfiguration(
                name="default",
                display_name="Default",
                description="Default theme",
                author="PhotoGeoView",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN
            )

            # Apply non-existent theme - should fallback to default
            result = self.theme_manager.apply_theme("non_existent")

            # Verify recovery was successful
            self.assertTrue(result)
            self.assertEqual(self.theme_manager.current_theme.name, "default")

    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'notification_system'):
            self.notification_system.cleanup()


if __name__ == '__main__':
    # Run tests
    unittest.main()
