"""
User Notification System for Error Handling and Warnings

Provides a centralized system for displaying user-friendly notifications
for errors, warnings, and informational messages across the application.

Author: Kiro AI Integration System
Requirements: 1.4, 3.4, 4.2, 4.4
"""

from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .config_manager import ConfigManager
from .logging_system import LoggerSystem


class NotificationType(Enum):
    """Types of notifications"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"


class NotificationPriority(Enum):
    """Priority levels for notifications"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationAction:
    """Represents an action that can be taken from a notification"""

    def __init__(
        self, text: str, callback: Callable[[], None], is_primary: bool = False
    ):
        self.text = text
        self.callback = callback
        self.is_primary = is_primary


class UserNotification:
    """Represents a user notification"""

    def __init__(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        duration: Optional[int] = None,  # Duration in seconds, None for persistent
        actions: Optional[List[NotificationAction]] = None,
        details: Optional[str] = None,
        source_component: Optional[str] = None,
    ):
        self.id = f"notification_{int(datetime.now().timestamp())}_{id(self)}"
        self.title = title
        self.message = message
        self.notification_type = notification_type
        self.priority = priority
        self.duration = duration
        self.actions = actions or []
        self.details = details
        self.source_component = source_component
        self.created_at = datetime.now()
        self.shown_at: Optional[datetime] = None
        self.dismissed_at: Optional[datetime] = None
        self.is_dismissed = False


class UserNotificationSystem(QObject):
    """
    Centralized user notification system for errors, warnings, and information
    """

    # Signals
    notification_shown = Signal(str)  # notification_id
    notification_dismissed = Signal(str)  # notification_id
    notification_action_triggered = Signal(str, str)  # notification_id, action_text

    def __init__(
        self,
        config_manager: ConfigManager,
        logger_system: LoggerSystem,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the user notification system

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        self.config_manager = config_manager
        self.logger = logger_system.get_logger(__name__)

        # Notification storage
        self.active_notifications: Dict[str, UserNotification] = {}
        self.notification_history: List[UserNotification] = []
        self.max_history_size = 100

        # UI components
        self.system_tray_icon: Optional[QSystemTrayIcon] = None
        self.notification_dialogs: Dict[str, QDialog] = {}

        # Configuration
        self.notifications_enabled = True
        self.show_system_tray = True
        self.auto_dismiss_duration = 5  # seconds
        self.max_concurrent_notifications = 3

        # Cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_expired_notifications)
        self.cleanup_timer.start(30000)  # Clean up every 30 seconds

        # Initialize system
        self._load_configuration()
        self._setup_system_tray()

        self.logger.info("User notification system initialized")

    def _load_configuration(self) -> None:
        """Load notification system configuration"""
        try:
            self.notifications_enabled = self.config_manager.get_setting(
                "notifications.enabled", True
            )
            self.show_system_tray = self.config_manager.get_setting(
                "notifications.system_tray", True
            )
            self.auto_dismiss_duration = self.config_manager.get_setting(
                "notifications.auto_dismiss_duration", 5
            )
            self.max_concurrent_notifications = self.config_manager.get_setting(
                "notifications.max_concurrent", 3
            )

            self.logger.debug("Notification configuration loaded")

        except Exception as e:
            self.logger.error(f"Failed to load notification configuration: {e}")

    def _setup_system_tray(self) -> None:
        """Setup system tray icon for notifications"""
        try:
            if not self.show_system_tray or not QSystemTrayIcon.isSystemTrayAvailable():
                return

            self.system_tray_icon = QSystemTrayIcon(self)

            # Set default icon
            app = QApplication.instance()
            if app and app.windowIcon():
                self.system_tray_icon.setIcon(app.windowIcon())
            else:
                # Create a simple default icon
                pixmap = QPixmap(16, 16)
                pixmap.fill()
                self.system_tray_icon.setIcon(QIcon(pixmap))

            self.system_tray_icon.setToolTip("PhotoGeoView")
            self.system_tray_icon.show()

            self.logger.debug("System tray icon setup complete")

        except Exception as e:
            self.logger.error(f"Failed to setup system tray: {e}")

    def show_notification(self, notification: UserNotification) -> bool:
        """
        Show a notification to the user

        Args:
            notification: Notification to show

        Returns:
            True if notification was shown, False otherwise
        """
        try:
            if not self.notifications_enabled:
                return False

            # Check if we have too many concurrent notifications
            if len(self.active_notifications) >= self.max_concurrent_notifications:
                # Dismiss oldest notification
                oldest_id = min(
                    self.active_notifications.keys(),
                    key=lambda x: self.active_notifications[x].created_at,
                )
                self.dismiss_notification(oldest_id)

            # Add to active notifications
            self.active_notifications[notification.id] = notification
            notification.shown_at = datetime.now()

            # Show notification based on type and priority
            if (
                notification.priority == NotificationPriority.URGENT
                or notification.notification_type == NotificationType.CRITICAL
            ):
                self._show_modal_dialog(notification)
            elif (
                notification.priority == NotificationPriority.HIGH
                or notification.notification_type == NotificationType.ERROR
            ):
                self._show_message_box(notification)
            else:
                self._show_system_tray_notification(notification)

            # Set auto-dismiss timer if duration is specified
            if notification.duration:
                QTimer.singleShot(
                    notification.duration * 1000,
                    lambda: self.dismiss_notification(notification.id),
                )
            elif notification.notification_type in [
                NotificationType.INFO,
                NotificationType.SUCCESS,
            ]:
                # Auto-dismiss info and success notifications
                QTimer.singleShot(
                    self.auto_dismiss_duration * 1000,
                    lambda: self.dismiss_notification(notification.id),
                )

            # Emit signal
            self.notification_shown.emit(notification.id)

            self.logger.debug(f"Notification shown: {notification.title}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
            return False

    def _show_modal_dialog(self, notification: UserNotification) -> None:
        """Show notification as modal dialog for urgent/critical notifications"""
        try:
            dialog = QDialog()
            dialog.setWindowTitle(notification.title)
            dialog.setModal(True)
            dialog.resize(400, 200)

            layout = QVBoxLayout(dialog)

            # Message
            message_label = QLabel(notification.message)
            message_label.setWordWrap(True)
            layout.addWidget(message_label)

            # Details if available
            if notification.details:
                details_label = QLabel(f"Details: {notification.details}")
                details_label.setWordWrap(True)
                details_label.setStyleSheet("color: gray; font-size: 10px;")
                layout.addWidget(details_label)

            # Actions
            button_layout = QHBoxLayout()

            if notification.actions:
                for action in notification.actions:
                    button = QPushButton(action.text)
                    if action.is_primary:
                        button.setDefault(True)
                    button.clicked.connect(
                        lambda checked, a=action: self._handle_notification_action(
                            notification.id, a
                        )
                    )
                    button_layout.addWidget(button)
            else:
                # Default OK button
                ok_button = QPushButton("OK")
                ok_button.setDefault(True)
                ok_button.clicked.connect(dialog.accept)
                button_layout.addWidget(ok_button)

            layout.addLayout(button_layout)

            # Store dialog reference
            self.notification_dialogs[notification.id] = dialog

            # Show dialog
            dialog.exec()

            # Clean up
            if notification.id in self.notification_dialogs:
                del self.notification_dialogs[notification.id]

        except Exception as e:
            self.logger.error(f"Failed to show modal dialog: {e}")

    def _show_message_box(self, notification: UserNotification) -> None:
        """Show notification as message box for high priority notifications"""
        try:
            # Determine message box type
            if notification.notification_type == NotificationType.ERROR:
                icon = QMessageBox.Icon.Critical
            elif notification.notification_type == NotificationType.WARNING:
                icon = QMessageBox.Icon.Warning
            elif notification.notification_type == NotificationType.SUCCESS:
                icon = QMessageBox.Icon.Information
            else:
                icon = QMessageBox.Icon.Information

            msg_box = QMessageBox()
            msg_box.setIcon(icon)
            msg_box.setWindowTitle(notification.title)
            msg_box.setText(notification.message)

            if notification.details:
                msg_box.setDetailedText(notification.details)

            # Add custom actions or default OK
            if notification.actions:
                for action in notification.actions:
                    button = msg_box.addButton(
                        action.text, QMessageBox.ButtonRole.ActionRole
                    )
                    if action.is_primary:
                        msg_box.setDefaultButton(button)
            else:
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

            # Show message box
            result = msg_box.exec()

            # Handle action if custom actions were provided
            if notification.actions and result < len(notification.actions):
                action = notification.actions[result]
                self._handle_notification_action(notification.id, action)

        except Exception as e:
            self.logger.error(f"Failed to show message box: {e}")

    def _show_system_tray_notification(self, notification: UserNotification) -> None:
        """Show notification in system tray for normal priority notifications"""
        try:
            if not self.system_tray_icon:
                return

            # Determine system tray icon
            if notification.notification_type == NotificationType.ERROR:
                icon = QSystemTrayIcon.MessageIcon.Critical
            elif notification.notification_type == NotificationType.WARNING:
                icon = QSystemTrayIcon.MessageIcon.Warning
            else:
                icon = QSystemTrayIcon.MessageIcon.Information

            # Show system tray message
            self.system_tray_icon.showMessage(
                notification.title,
                notification.message,
                icon,
                (notification.duration or self.auto_dismiss_duration) * 1000,
            )

        except Exception as e:
            self.logger.error(f"Failed to show system tray notification: {e}")

    def _handle_notification_action(
        self, notification_id: str, action: NotificationAction
    ) -> None:
        """Handle notification action"""
        try:
            # Execute action callback
            if action.callback:
                action.callback()

            # Emit signal
            self.notification_action_triggered.emit(notification_id, action.text)

            # Dismiss notification
            self.dismiss_notification(notification_id)

        except Exception as e:
            self.logger.error(f"Failed to handle notification action: {e}")

    def dismiss_notification(self, notification_id: str) -> bool:
        """
        Dismiss a notification

        Args:
            notification_id: ID of notification to dismiss

        Returns:
            True if notification was dismissed, False otherwise
        """
        try:
            if notification_id not in self.active_notifications:
                return False

            notification = self.active_notifications[notification_id]
            notification.dismissed_at = datetime.now()
            notification.is_dismissed = True

            # Remove from active notifications
            del self.active_notifications[notification_id]

            # Add to history
            self.notification_history.append(notification)

            # Limit history size
            if len(self.notification_history) > self.max_history_size:
                self.notification_history = self.notification_history[
                    -self.max_history_size :
                ]

            # Close dialog if exists
            if notification_id in self.notification_dialogs:
                dialog = self.notification_dialogs[notification_id]
                dialog.close()
                del self.notification_dialogs[notification_id]

            # Emit signal
            self.notification_dismissed.emit(notification_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to dismiss notification: {e}")
            return False

    def dismiss_all_notifications(self) -> None:
        """Dismiss all active notifications"""
        try:
            notification_ids = list(self.active_notifications.keys())
            for notification_id in notification_ids:
                self.dismiss_notification(notification_id)

        except Exception as e:
            self.logger.error(f"Failed to dismiss all notifications: {e}")

    def _cleanup_expired_notifications(self) -> None:
        """Clean up expired notifications"""
        try:
            current_time = datetime.now()
            expired_ids = []

            for notification_id, notification in self.active_notifications.items():
                if notification.duration:
                    if (
                        notification.shown_at
                        and (current_time - notification.shown_at).total_seconds()
                        > notification.duration
                    ):
                        expired_ids.append(notification_id)

            for notification_id in expired_ids:
                self.dismiss_notification(notification_id)

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired notifications: {e}")

    # Convenience methods for common notification types

    def show_error(
        self,
        title: str,
        message: str,
        details: Optional[str] = None,
        actions: Optional[List[NotificationAction]] = None,
        source_component: Optional[str] = None,
    ) -> str:
        """Show error notification"""
        notification = UserNotification(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH,
            details=details,
            actions=actions,
            source_component=source_component,
        )
        self.show_notification(notification)
        return notification.id

    def show_warning(
        self,
        title: str,
        message: str,
        details: Optional[str] = None,
        actions: Optional[List[NotificationAction]] = None,
        source_component: Optional[str] = None,
    ) -> str:
        """Show warning notification"""
        notification = UserNotification(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.NORMAL,
            details=details,
            actions=actions,
            source_component=source_component,
        )
        self.show_notification(notification)
        return notification.id

    def show_info(
        self,
        title: str,
        message: str,
        duration: Optional[int] = None,
        source_component: Optional[str] = None,
    ) -> str:
        """Show info notification"""
        notification = UserNotification(
            title=title,
            message=message,
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.LOW,
            duration=duration,
            source_component=source_component,
        )
        self.show_notification(notification)
        return notification.id

    def show_success(
        self,
        title: str,
        message: str,
        duration: Optional[int] = None,
        source_component: Optional[str] = None,
    ) -> str:
        """Show success notification"""
        notification = UserNotification(
            title=title,
            message=message,
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.LOW,
            duration=duration,
            source_component=source_component,
        )
        self.show_notification(notification)
        return notification.id

    def show_critical(
        self,
        title: str,
        message: str,
        details: Optional[str] = None,
        actions: Optional[List[NotificationAction]] = None,
        source_component: Optional[str] = None,
    ) -> str:
        """Show critical notification"""
        notification = UserNotification(
            title=title,
            message=message,
            notification_type=NotificationType.CRITICAL,
            priority=NotificationPriority.URGENT,
            details=details,
            actions=actions,
            source_component=source_component,
        )
        self.show_notification(notification)
        return notification.id

    # Theme-specific error notifications

    def show_theme_error(
        self, theme_name: str, error_message: str, fallback_applied: bool = False
    ) -> str:
        """Show theme-related error notification"""
        title = "Theme Error"
        message = f"Failed to apply theme '{theme_name}': {error_message}"

        if fallback_applied:
            message += "\nDefault theme has been applied."

        actions = []
        if not fallback_applied:
            actions.append(
                NotificationAction(
                    "Use Default Theme",
                    lambda: self._apply_default_theme(),
                    is_primary=True,
                )
            )

        return self.show_error(
            title=title,
            message=message,
            actions=actions,
            source_component="theme_manager",
        )

    def show_breadcrumb_error(
        self,
        path: str,
        error_type: str,
        error_message: str,
        fallback_path: Optional[str] = None,
    ) -> str:
        """Show breadcrumb navigation error notification"""
        title = "Navigation Error"

        if error_type == "network_disconnected":
            message = f"Network drive disconnected: {path}"
            if fallback_path:
                message += f"\nNavigated to: {fallback_path}"
        elif error_type == "permission_denied":
            message = f"Access denied to: {path}"
        elif error_type == "path_not_found":
            message = f"Path not found: {path}"
        else:
            message = f"Navigation failed: {error_message}"

        actions = []
        if not fallback_path:
            actions.append(
                NotificationAction(
                    "Go to Home", lambda: self._navigate_to_home(), is_primary=True
                )
            )

        return self.show_error(
            title=title,
            message=message,
            actions=actions,
            source_component="breadcrumb_bar",
        )

    def _apply_default_theme(self) -> None:
        """Apply default theme (callback for theme error action)"""
        try:
            # This would be connected to the theme manager
            self.logger.info("Applying default theme from notification action")
        except Exception as e:
            self.logger.error(f"Failed to apply default theme: {e}")

    def _navigate_to_home(self) -> None:
        """Navigate to home directory (callback for breadcrumb error action)"""
        try:
            # This would be connected to the navigation controller
            self.logger.info("Navigating to home directory from notification action")
        except Exception as e:
            self.logger.error(f"Failed to navigate to home: {e}")

    def get_notification_history(self) -> List[UserNotification]:
        """Get notification history"""
        return self.notification_history.copy()

    def get_active_notifications(self) -> List[UserNotification]:
        """Get active notifications"""
        return list(self.active_notifications.values())

    def set_notifications_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications"""
        self.notifications_enabled = enabled
        self.config_manager.set_setting("notifications.enabled", enabled)

        if not enabled:
            self.dismiss_all_notifications()

    def cleanup(self) -> None:
        """Cleanup notification system resources"""
        try:
            # Stop cleanup timer
            if self.cleanup_timer:
                self.cleanup_timer.stop()

            # Dismiss all notifications
            self.dismiss_all_notifications()

            # Hide system tray icon
            if self.system_tray_icon:
                self.system_tray_icon.hide()

            self.logger.info("User notification system cleaned up")

        except Exception as e:
            self.logger.error(f"Failed to cleanup notification system: {e}")
