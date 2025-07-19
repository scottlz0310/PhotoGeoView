"""
Thumbnail View Module for PhotoGeoView
Provides thumbnail grid display for image files
"""

from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QPen
from pathlib import Path
from typing import Optional, List
import time

from src.core.logger import get_logger

logger = get_logger(__name__)


class ThumbnailLoader(QThread):
    """Background thread for loading thumbnails"""

    thumbnail_loaded = pyqtSignal(str, QPixmap)  # file_path, thumbnail

    def __init__(self):
        super().__init__()
        self.file_paths: List[str] = []
        self.thumbnail_size = QSize(128, 128)
        self._stop_requested = False

    def set_files(self, file_paths: List[str]) -> None:
        """Set list of files to process"""
        self.file_paths = file_paths.copy()
        self._stop_requested = False

    def set_thumbnail_size(self, size: QSize) -> None:
        """Set thumbnail size"""
        self.thumbnail_size = size

    def stop(self) -> None:
        """Stop thumbnail loading"""
        self._stop_requested = True

    def run(self) -> None:
        """Load thumbnails in background"""
        try:
            for file_path in self.file_paths:
                if self._stop_requested:
                    break

                try:
                    # Load and resize image
                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        # Scale to thumbnail size maintaining aspect ratio
                        thumbnail = pixmap.scaled(
                            self.thumbnail_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )

                        # Emit loaded thumbnail
                        self.thumbnail_loaded.emit(file_path, thumbnail)

                    # Small delay to prevent UI freezing
                    time.sleep(0.01)

                except Exception as e:
                    logger.warning(f"Failed to load thumbnail for {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error in thumbnail loader thread: {e}")


class ThumbnailView(QWidget):
    """
    Thumbnail grid view widget for images
    """

    # Signals
    image_selected = pyqtSignal(str)  # Emitted when image is selected
    image_double_clicked = pyqtSignal(str)  # Emitted when image is double-clicked

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logger

        # UI components
        self.list_widget: Optional[QListWidget] = None
        self.info_label: Optional[QLabel] = None

        # Thumbnail settings
        self.thumbnail_size = QSize(128, 128)
        self.current_files: List[str] = []

        # Background loader
        self.thumbnail_loader = ThumbnailLoader()
        self.thumbnail_loader.thumbnail_loaded.connect(self.on_thumbnail_loaded)

        self.setup_ui()

        self.logger.debug("ThumbnailView initialized")

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Info label
        self.info_label = QLabel("No images to display")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-style: italic;
                padding: 10px;
            }
        """)
        layout.addWidget(self.info_label)

        # List widget for thumbnails
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setSpacing(10)

        # Set item size
        item_size = self.thumbnail_size + QSize(20, 40)  # Extra space for filename
        self.list_widget.setIconSize(self.thumbnail_size)
        self.list_widget.setGridSize(item_size)

        # Selection behavior
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.list_widget)

        # Connect signals
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.logger.debug("ThumbnailView UI setup complete")

    def set_thumbnail_size(self, size: QSize) -> None:
        """Set thumbnail size"""
        self.thumbnail_size = size
        self.thumbnail_loader.set_thumbnail_size(size)

        if self.list_widget:
            item_size = size + QSize(20, 40)
            self.list_widget.setIconSize(size)
            self.list_widget.setGridSize(item_size)

        # Reload thumbnails with new size
        if self.current_files:
            self.load_images(self.current_files)

    def load_images(self, file_paths: List[str]) -> None:
        """Load images and display thumbnails"""
        try:
            # Stop any existing loading
            self.thumbnail_loader.stop()
            self.thumbnail_loader.wait(1000)  # Wait up to 1 second

            # Clear existing items
            self.list_widget.clear()
            self.current_files = file_paths.copy()

            if not file_paths:
                self.info_label.setText("No images to display")
                self.info_label.show()
                return

            self.info_label.hide()

            # Create placeholder items first
            for file_path in file_paths:
                self.add_placeholder_item(file_path)

            # Update info
            self.info_label.setText(f"Loading {len(file_paths)} images...")
            self.info_label.show()

            # Start background loading
            self.thumbnail_loader.set_files(file_paths)
            self.thumbnail_loader.start()

            self.logger.info(f"Started loading {len(file_paths)} thumbnails")

        except Exception as e:
            self.logger.error(f"Error loading images: {e}")

    def add_placeholder_item(self, file_path: str) -> None:
        """Add a placeholder item while thumbnail loads"""
        try:
            # Create placeholder pixmap
            placeholder = QPixmap(self.thumbnail_size)
            placeholder.fill(Qt.GlobalColor.lightGray)

            # Draw loading indicator
            painter = QPainter(placeholder)
            painter.setPen(QPen(Qt.GlobalColor.darkGray, 2))
            painter.drawRect(placeholder.rect())
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "Loading...")
            painter.end()

            # Create list item
            item = QListWidgetItem()
            item.setIcon(QIcon(placeholder))
            item.setText(Path(file_path).name)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setToolTip(file_path)

            self.list_widget.addItem(item)

        except Exception as e:
            self.logger.error(f"Error creating placeholder item: {e}")

    def on_thumbnail_loaded(self, file_path: str, thumbnail: QPixmap) -> None:
        """Handle loaded thumbnail"""
        try:
            # Find the corresponding item
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == file_path:
                    # Update item with actual thumbnail
                    item.setIcon(QIcon(thumbnail))
                    break

            # Update info label
            loaded_count = sum(1 for i in range(self.list_widget.count())
                             if self.list_widget.item(i).icon().pixmap(self.thumbnail_size).isNull() == False)

            if loaded_count == len(self.current_files):
                self.info_label.hide()
            else:
                self.info_label.setText(f"Loading {len(self.current_files) - loaded_count} images...")

        except Exception as e:
            self.logger.error(f"Error handling loaded thumbnail: {e}")

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click"""
        try:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.image_selected.emit(file_path)
                self.logger.debug(f"Image selected: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling item click: {e}")

    def on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double click"""
        try:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.image_double_clicked.emit(file_path)
                self.logger.debug(f"Image double-clicked: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling item double click: {e}")

    def clear(self) -> None:
        """Clear all thumbnails"""
        try:
            # Stop loading
            self.thumbnail_loader.stop()

            # Clear UI
            if self.list_widget:
                self.list_widget.clear()

            self.current_files.clear()

            if self.info_label:
                self.info_label.setText("No images to display")
                self.info_label.show()

            self.logger.debug("ThumbnailView cleared")

        except Exception as e:
            self.logger.error(f"Error clearing thumbnails: {e}")

    def get_selected_file(self) -> Optional[str]:
        """Get currently selected file path"""
        try:
            current_item = self.list_widget.currentItem()
            if current_item:
                return current_item.data(Qt.ItemDataRole.UserRole)
            return None

        except Exception as e:
            self.logger.error(f"Error getting selected file: {e}")
            return None

    def __del__(self) -> None:
        """Handle widget destruction"""
        try:
            # Stop thumbnail loading thread
            if hasattr(self, 'thumbnail_loader'):
                self.thumbnail_loader.stop()
                self.thumbnail_loader.wait(1000)

        except Exception as e:
            self.logger.error(f"Error in destructor: {e}")
