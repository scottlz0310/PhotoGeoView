"""
Debug Controller for PhotoGeoView
Manages debug shortcuts, logging level control, and debug features
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence

from src.core.logger import get_logger
from src.core.settings import SettingsManager


class DebugController(QObject):
    """
    Controller for debug functionality
    Handles keyboard shortcuts and logging level management
    """

    # Signals
    status_message = pyqtSignal(str, int)  # For status bar updates (message, timeout)

    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize debug controller"""
        super().__init__(parent)

        self.logger = get_logger(__name__)
        self.settings = settings

        self.logger.debug("Debug controller initialized")

    def setup_debug_shortcuts(self, parent_widget) -> None:
        """Setup debug keyboard shortcuts"""
        # Ctrl+Shift+D: Toggle DEBUG/INFO logging
        debug_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), parent_widget)
        debug_shortcut.activated.connect(self.toggle_debug_mode)

        # Ctrl+Shift+L: Show current log level in status bar
        log_info_shortcut = QShortcut(QKeySequence("Ctrl+Shift+L"), parent_widget)
        log_info_shortcut.activated.connect(self.show_log_level_info)

        self.logger.debug("Debug shortcuts initialized")

    def toggle_debug_mode(self) -> None:
        """Cycle through all log levels: DEBUG → INFO → WARNING → ERROR → CRITICAL → DEBUG..."""
        current_level = self.settings.logging.level

        # Define log levels in order
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        try:
            current_index = log_levels.index(current_level)
            # Move to next level (cycle back to DEBUG after CRITICAL)
            next_index = (current_index + 1) % len(log_levels)
            new_level = log_levels[next_index]
        except ValueError:
            # If current level is not in our list, default to DEBUG
            new_level = "DEBUG"

        success = self.settings.set_log_level(new_level)

        if success:
            # Show level with description
            level_descriptions = {
                "DEBUG": "DEBUG (All messages)",
                "INFO": "INFO (General information)",
                "WARNING": "WARNING (Warnings and above)",
                "ERROR": "ERROR (Errors and critical)",
                "CRITICAL": "CRITICAL (Critical errors only)"
            }

            message = f"Log level: {level_descriptions.get(new_level, new_level)}"
            self.logger.info(f"Log level changed to {new_level}")
            self.status_message.emit(message, 4000)  # Show for 4 seconds
        else:
            message = "Failed to change log level"
            self.logger.error(message)
            self.status_message.emit(message, 3000)

    def show_log_level_info(self) -> None:
        """Show current log level and available levels in status bar"""
        current_level = self.settings.logging.level

        level_info = {
            "DEBUG": "Shows all messages (most verbose)",
            "INFO": "Shows general information and above",
            "WARNING": "Shows warnings, errors and critical",
            "ERROR": "Shows errors and critical only",
            "CRITICAL": "Shows only critical errors (least verbose)"
        }

        current_description = level_info.get(current_level, "Unknown level")
        message = f"Log Level: {current_level} - {current_description} | Press Ctrl+Shift+D to cycle"

        self.status_message.emit(message, 7000)  # Show for 7 seconds
        self.logger.info(f"Log level info displayed: {current_level} - {current_description}")
