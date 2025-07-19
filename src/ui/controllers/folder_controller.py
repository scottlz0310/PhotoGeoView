"""
Folder Controller for PhotoGeoView
Manages folder selection, navigation, and related operations
"""

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import Optional

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

    def __init__(self, settings: SettingsManager, parent=None):
        """Initialize folder controller"""
        super().__init__(parent)

        self.logger = get_logger(__name__)
        self.settings = settings

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

    def open_folder(self, folder_path: str, parent_widget: Optional[QWidget] = None) -> None:
        """Open a specific folder"""
        try:
            folder_path = Path(folder_path).resolve().as_posix()

            # Update settings
            self.settings.folders.last_opened_folder = folder_path
            self.settings.add_recent_folder(folder_path)

            # Emit signal for UI updates
            self.folder_opened.emit(folder_path)

            # Update status
            self.status_message.emit(f"Opened folder: {folder_path}")

            self.logger.info(f"Opened folder: {folder_path}")

        except Exception as e:
            self.logger.error(f"Error opening folder {folder_path}: {e}")
            if parent_widget:
                QMessageBox.warning(parent_widget, "Error", f"Failed to open folder: {e}")

    def get_current_folder(self) -> str:
        """Get the current folder path"""
        return self.settings.folders.last_opened_folder

    def get_recent_folders(self) -> list:
        """Get list of recent folders"""
        return getattr(self.settings.folders, 'recent_folders', [])
