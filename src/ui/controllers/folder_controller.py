"""
Folder Controller for PhotoGeoView
Manages folder selection, navigation, and related operations
"""

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import Optional, List

from src.core.logger import get_logger
from src.core.settings import SettingsManager


class FolderController(QObject):
    """
    Controller for folder management operations
    Handles folder selection, navigation, and path operations
    """

    # Signals
    folder_opened = pyqtSignal(str)  # Emitted when folder is opened
    status_message = pyqtSignal(str)  # For status bar updates
    navigation_state_changed = pyqtSignal(bool, bool, bool)  # back_enabled, forward_enabled, up_enabled

    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize folder controller"""
        super().__init__(parent)

        self.logger = get_logger(__name__)
        self.settings = settings

        # Navigation history
        self.navigation_history: List[str] = []
        self.current_history_index: int = -1

        # Load initial folder if available
        if self.settings.folders.last_opened_folder:
            self.navigation_history.append(self.settings.folders.last_opened_folder)
            self.current_history_index = 0
            # Emit initial navigation state
            self._update_navigation_state()

        self.logger.debug("Folder controller initialized")

    def open_folder_dialog(self, parent_widget: QWidget) -> None:
        """Open folder selection dialog"""
        try:
            folder = QFileDialog.getExistingDirectory(
                parent_widget,
                "Select Image Folder",
                self.settings.folders.last_opened_folder
            )

            if folder:
                self.open_folder(folder, parent_widget)
        except Exception as e:
            self.logger.error(f"Error opening folder dialog: {e}")
            QMessageBox.warning(parent_widget, "Error", f"Failed to open folder dialog: {e}")

    def open_folder(self, folder_path: str, parent_widget: Optional[QWidget] = None, add_to_history: bool = True) -> None:
        """Open a specific folder"""
        try:
            folder_path = Path(folder_path).resolve().as_posix()

            # Add to navigation history if requested
            if add_to_history:
                self._add_to_history(folder_path)

            # Update settings
            self.settings.folders.last_opened_folder = folder_path
            self.settings.add_recent_folder(folder_path)

            # Emit signal for UI updates
            self.folder_opened.emit(folder_path)

            # Update navigation state
            self._update_navigation_state()

            # Update status
            self.status_message.emit(f"Opened folder: {folder_path}")

            self.logger.info(f"Opened folder: {folder_path}")

        except Exception as e:
            self.logger.error(f"Error opening folder {folder_path}: {e}")
            if parent_widget:
                QMessageBox.warning(parent_widget, "Error", f"Failed to open folder: {e}")

    def go_back(self) -> None:
        """Navigate to previous folder in history"""
        if self.can_go_back():
            self.current_history_index -= 1
            folder_path = self.navigation_history[self.current_history_index]
            self.open_folder(folder_path, add_to_history=False)
            self.status_message.emit(f"Navigated back to: {folder_path}")
            self.logger.debug(f"Navigated back to: {folder_path}")

    def go_forward(self) -> None:
        """Navigate to next folder in history"""
        if self.can_go_forward():
            self.current_history_index += 1
            folder_path = self.navigation_history[self.current_history_index]
            self.open_folder(folder_path, add_to_history=False)
            self.status_message.emit(f"Navigated forward to: {folder_path}")
            self.logger.debug(f"Navigated forward to: {folder_path}")

    def go_up(self) -> None:
        """Navigate to parent folder"""
        try:
            current_path = Path(self.get_current_folder())
            parent_path = current_path.parent

            if parent_path != current_path:  # Has parent
                self.open_folder(parent_path.as_posix(), add_to_history=True)
                self.status_message.emit(f"Navigated up to: {parent_path}")
                self.logger.debug(f"Navigated up to parent folder: {parent_path}")
            else:
                self.status_message.emit("Already at root folder")
                self.logger.debug("Cannot navigate up: already at root")
        except Exception as e:
            self.logger.error(f"Error navigating up: {e}")
            self.status_message.emit("Failed to navigate to parent folder")

    def can_go_back(self) -> bool:
        """Check if back navigation is possible"""
        return self.current_history_index > 0

    def can_go_forward(self) -> bool:
        """Check if forward navigation is possible"""
        return self.current_history_index < len(self.navigation_history) - 1

    def can_go_up(self) -> bool:
        """Check if up navigation is possible"""
        try:
            current_path = Path(self.get_current_folder())
            return current_path.parent != current_path
        except Exception:
            return False

    def _add_to_history(self, folder_path: str) -> None:
        """Add folder to navigation history"""
        # Remove any forward history when adding new path
        if self.current_history_index < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[:self.current_history_index + 1]

        # Don't add duplicate consecutive paths
        if not self.navigation_history or self.navigation_history[-1] != folder_path:
            self.navigation_history.append(folder_path)
            self.current_history_index = len(self.navigation_history) - 1

        # Limit history size
        max_history = 50
        if len(self.navigation_history) > max_history:
            self.navigation_history = self.navigation_history[-max_history:]
            self.current_history_index = len(self.navigation_history) - 1

    def _update_navigation_state(self) -> None:
        """Update navigation button states"""
        back_enabled = self.can_go_back()
        forward_enabled = self.can_go_forward()
        up_enabled = self.can_go_up()

        self.navigation_state_changed.emit(back_enabled, forward_enabled, up_enabled)

    def get_current_folder(self) -> str:
        """Get the current folder path"""
        return self.settings.folders.last_opened_folder

    def get_recent_folders(self) -> List[str]:
        """Get list of recent folders"""
        return getattr(self.settings.folders, 'recent_folders', [])
