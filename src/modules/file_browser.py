"""
File Browser Module for PhotoGeoView
Provides file system navigation and image file filtering
"""

from PyQt6.QtWidgets import (
    QTreeView, QVBoxLayout, QWidget, QHeaderView
)
from PyQt6.QtCore import QDir, Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QFileSystemModel
from pathlib import Path
from typing import Optional, Any

from src.core.logger import get_logger
from src.core.settings import SettingsManager

logger = get_logger(__name__)


class FileBrowser(QWidget):
    """
    File browser widget with image file filtering
    """

    # Signals
    folder_changed = pyqtSignal(str)  # Emitted when folder selection changes
    file_selected = pyqtSignal(str)   # Emitted when file is selected

    # Image file extensions
    IMAGE_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
        '.gif', '.webp', '.ico', '.svg'
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logger

        # Settings manager
        self.settings_manager = SettingsManager()

        # File system model
        self.model: Optional[QFileSystemModel] = None
        self.tree_view: Optional[QTreeView] = None
        self.current_path: str = ""

        self.setup_ui()
        self.setup_model()
        self.setup_connections()

        self.logger.debug("FileBrowser initialized")

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tree view
        self.tree_view = QTreeView()

        # Get alternating row colors setting - for now, disable it
        alternating_colors = False  # Disable alternating row colors
        self.tree_view.setAlternatingRowColors(alternating_colors)

        self.tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree_view.setSortingEnabled(True)

        # Hide unnecessary columns (show only Name)
        self.tree_view.setRootIsDecorated(True)

        layout.addWidget(self.tree_view)

        self.logger.debug(f"FileBrowser UI setup complete (alternating colors: {alternating_colors})")

    def setup_model(self) -> None:
        """Setup the file system model"""
        self.model = QFileSystemModel()

        # Set name filters for images only
        name_filters = [f"*{ext}" for ext in self.IMAGE_EXTENSIONS]
        name_filters.extend([f"*{ext.upper()}" for ext in self.IMAGE_EXTENSIONS])

        # Also show directories
        self.model.setNameFilterDisables(False)
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)

        # Set root path to user's home directory
        root_path = str(Path.home())
        self.model.setRootPath(root_path)

        # Apply model to tree view
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(root_path))

        # Configure columns
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name column
        header.hideSection(1)  # Hide Size
        header.hideSection(2)  # Hide Type
        header.hideSection(3)  # Hide Date Modified

        self.current_path = root_path
        self.logger.info(f"File browser root set to: {root_path}")

    def setup_connections(self) -> None:
        """Setup signal connections"""
        if self.tree_view and self.model:
            self.tree_view.clicked.connect(self.on_item_clicked)
            self.tree_view.doubleClicked.connect(self.on_item_double_clicked)

    def on_item_clicked(self, index: QModelIndex) -> None:
        """Handle item click"""
        try:
            if not self.model:
                return

            file_path = self.model.filePath(index)
            file_info = self.model.fileInfo(index)

            if file_info.isDir():
                # Directory selected
                self.current_path = file_path
                self.folder_changed.emit(file_path)
                self.logger.debug(f"Folder selected: {file_path}")
            else:
                # File selected - check if it's an image
                path_obj = Path(file_path)
                if path_obj.suffix.lower() in self.IMAGE_EXTENSIONS:
                    self.file_selected.emit(file_path)
                    self.logger.debug(f"Image file selected: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling item click: {e}")

    def on_item_double_clicked(self, index: QModelIndex) -> None:
        """Handle item double click - navigate to directory"""
        try:
            if not self.model:
                return

            file_path = self.model.filePath(index)
            file_info = self.model.fileInfo(index)

            if file_info.isDir():
                # Navigate to directory
                self.set_root_path(file_path)
                self.logger.info(f"Navigated to: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling double click: {e}")

    def set_root_path(self, path: str) -> None:
        """Set the root path for browsing"""
        try:
            if not self.model or not self.tree_view:
                return

            path_obj = Path(path)
            if not path_obj.exists():
                self.logger.warning(f"Path does not exist: {path}")
                return

            if not path_obj.is_dir():
                # If it's a file, use its parent directory
                path = str(path_obj.parent)

            self.model.setRootPath(path)
            self.tree_view.setRootIndex(self.model.index(path))
            self.current_path = path

            # Emit signal
            self.folder_changed.emit(path)

            self.logger.info(f"Root path changed to: {path}")

        except Exception as e:
            self.logger.error(f"Error setting root path {path}: {e}")

    def get_current_path(self) -> str:
        """Get the current browsing path"""
        return self.current_path

    def get_image_files_in_current_path(self) -> list[str]:
        """Get list of image files in current path"""
        try:
            path_obj = Path(self.current_path)
            if not path_obj.exists() or not path_obj.is_dir():
                return []

            image_files = []
            for file_path in path_obj.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    image_files.append(str(file_path))

            # Sort files by name
            image_files.sort()

            self.logger.debug(f"Found {len(image_files)} image files in {self.current_path}")
            return image_files

        except Exception as e:
            self.logger.error(f"Error getting image files: {e}")
            return []

    def refresh(self) -> None:
        """Refresh the file browser"""
        try:
            if self.model:
                current_path = self.current_path
                self.model.setRootPath("")
                self.model.setRootPath(current_path)
                self.logger.debug("File browser refreshed")

        except Exception as e:
            self.logger.error(f"Error refreshing file browser: {e}")
