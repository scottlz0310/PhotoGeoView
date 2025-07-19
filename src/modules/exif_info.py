"""
EXIF情報表示パネル (リファクタリング版)
画像のEXIF情報を抽出・表示し、GPS座標も含めて整理
重複コードを削除し、ユーティリティモジュールを活用
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QFrame, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from src.core.logger import get_logger
from src.utils.exif_processor import ExifProcessor
from src.utils.file_utils import FileUtils

logger = get_logger(__name__)


class ExifLoader(QThread):
    """Background thread for loading EXIF data - simplified version"""

    exif_loaded = pyqtSignal(str, dict)  # file_path, exif_data

    def __init__(self):
        super().__init__()
        self.file_path: str = ""
        self._stop_requested = False
        self.exif_processor = ExifProcessor()

    def set_file(self, file_path: str) -> None:
        """Set file to process"""
        self.file_path = file_path
        self._stop_requested = False

    def stop(self) -> None:
        """Stop EXIF loading"""
        self._stop_requested = True

    def run(self) -> None:
        """Load EXIF data in background using ExifProcessor"""
        try:
            if self._stop_requested or not self.file_path:
                return

            if not FileUtils.is_image_file(self.file_path) or not Path(self.file_path).exists():
                return

            # Use the centralized EXIF processor
            exif_data = self.exif_processor.extract_exif_data(self.file_path)

            if exif_data and not self._stop_requested:
                self.exif_loaded.emit(self.file_path, exif_data)

        except Exception as e:
            logger.error(f"Error loading EXIF data: {e}")


class ExifInfoPanel(QWidget):
    """
    EXIF information display panel - refactored version
    """

    # シグナル定義
    data_loaded = pyqtSignal(str, dict)  # file_path, exif_data

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logger

        # UI components
        self.content_widget: Optional[QWidget] = None
        self.scroll_area: Optional[QScrollArea] = None
        self.current_file: str = ""
        self.current_data: Dict[str, Any] = {}

        # Background loader
        self.exif_loader = ExifLoader()
        self.exif_loader.exif_loaded.connect(self.on_exif_loaded)

        # Setup UI
        self.setup_ui()

        self.logger.debug("EXIF info panel initialized")

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create content widget
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        layout.addWidget(self.scroll_area)

        # Initialize with empty state
        self.clear_info()

    def load_file_info(self, file_path: str) -> None:
        """Load EXIF information for a file"""
        try:
            if not file_path or not Path(file_path).exists():
                self.clear_info()
                return

            self.current_file = file_path

            # Show loading state
            self._show_loading()

            # Stop any previous loading
            if self.exif_loader.isRunning():
                self.exif_loader.stop()
                self.exif_loader.wait(1000)

            # Start background loading
            self.exif_loader.set_file(file_path)
            self.exif_loader.start()

        except Exception as e:
            self.logger.error(f"Error initiating file load: {e}")
            self.clear_info()

    def on_exif_loaded(self, file_path: str, exif_data: Dict[str, Any]) -> None:
        """Handle EXIF data loaded from background thread"""
        try:
            if file_path != self.current_file:
                return  # Outdated data

            self.current_data = exif_data
            self.display_exif_data(exif_data)

            # Emit signal for other components (like map viewer)
            self.data_loaded.emit(file_path, exif_data)

        except Exception as e:
            self.logger.error(f"Error handling loaded EXIF data: {e}")

    def display_exif_data(self, data: Dict[str, Any]) -> None:
        """Display EXIF data in organized groups"""
        try:
            # Clear previous content safely
            if self.content_widget:
                # Clear existing content without removing layout
                layout = self.content_widget.layout()
                if layout:
                    # Remove all widgets from layout
                    while layout.count():
                        child = layout.takeAt(0)
                        if child and child.widget():
                            child.widget().deleteLater()
                else:
                    # Create new layout if none exists
                    layout = QVBoxLayout(self.content_widget)

                layout.setAlignment(Qt.AlignmentFlag.AlignTop)

                if not data:
                    no_data_label = QLabel("No EXIF data available")
                    no_data_label.setStyleSheet("color: gray; font-style: italic;")
                    layout.addWidget(no_data_label)
                    return

                # Categorize and display data
                categories = self.categorize_data(data)

                for category, items in categories.items():
                    if items:
                        group = self.create_info_group(category, items)
                        layout.addWidget(group)

                layout.addStretch()

        except Exception as e:
            self.logger.error(f"Error displaying EXIF data: {e}")

    def categorize_data(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Categorize EXIF data into logical groups"""
        categories = {
            "File Information": {},
            "Camera Information": {},
            "Exposure Settings": {},
            "GPS Location": {},
            "Other EXIF Data": {}
        }

        # File info keywords
        file_keywords = ['file name', 'file size', 'modified', 'full path', 'extension']

        # Camera info keywords
        camera_keywords = ['camera', 'make', 'model', 'lens', 'orientation']

        # Exposure keywords
        exposure_keywords = ['iso', 'exposure', 'f-number', 'focal length', 'flash', 'white balance', 'date']

        # GPS keywords
        gps_keywords = ['gps', 'latitude', 'longitude', 'coordinates']

        for key, value in data.items():
            if key == 'gps_coordinates':
                continue  # Skip raw coordinates

            key_lower = key.lower()
            categorized = False

            # Check each category
            if any(keyword in key_lower for keyword in file_keywords):
                categories["File Information"][key] = str(value)
                categorized = True
            elif any(keyword in key_lower for keyword in camera_keywords):
                categories["Camera Information"][key] = str(value)
                categorized = True
            elif any(keyword in key_lower for keyword in exposure_keywords):
                categories["Exposure Settings"][key] = str(value)
                categorized = True
            elif any(keyword in key_lower for keyword in gps_keywords):
                categories["GPS Location"][key] = str(value)
                categorized = True

            if not categorized:
                categories["Other EXIF Data"][key] = str(value)

        return categories

    def create_info_group(self, title: str, data: Dict[str, str]) -> QGroupBox:
        """Create a group widget for displaying categorized info"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid gray;
                border-radius: 5px;
                margin-top: 6px;
                padding: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        layout = QGridLayout(group)
        layout.setColumnStretch(1, 1)

        row = 0
        for key, value in data.items():
            # Key label
            key_label = QLabel(f"{key}:")
            key_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            key_label.setStyleSheet("font-weight: normal; color: #666;")

            # Value label
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setStyleSheet("font-weight: normal;")

            layout.addWidget(key_label, row, 0)
            layout.addWidget(value_label, row, 1)
            row += 1

        return group

    def clear_info(self) -> None:
        """Clear all displayed information"""
        try:
            if self.content_widget:
                # Clear existing content without removing layout
                layout = self.content_widget.layout()
                if layout:
                    # Remove all widgets from layout
                    while layout.count():
                        child = layout.takeAt(0)
                        if child and child.widget():
                            child.widget().deleteLater()
                else:
                    # Create new layout if none exists
                    layout = QVBoxLayout(self.content_widget)

                layout.setAlignment(Qt.AlignmentFlag.AlignTop)

                empty_label = QLabel("Select an image to view EXIF information")
                empty_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(empty_label)

            self.current_file = ""
            self.current_data = {}

        except Exception as e:
            self.logger.error(f"Error clearing info: {e}")

    def _show_loading(self) -> None:
        """Show loading state"""
        try:
            if self.content_widget:
                # Clear existing content without removing layout
                layout = self.content_widget.layout()
                if layout:
                    # Remove all widgets from layout
                    while layout.count():
                        child = layout.takeAt(0)
                        if child and child.widget():
                            child.widget().deleteLater()
                else:
                    # Create new layout if none exists
                    layout = QVBoxLayout(self.content_widget)

                layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                loading_label = QLabel("Loading EXIF data...")
                loading_label.setStyleSheet("color: #666; font-style: italic;")
                loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(loading_label)

        except Exception as e:
            self.logger.error(f"Error showing loading state: {e}")

    def get_gps_coordinates(self) -> Optional[Tuple[float, float]]:
        """Get GPS coordinates if available"""
        try:
            return self.current_data.get('gps_coordinates')
        except Exception:
            return None

    def _get_exif_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get EXIF data synchronously (for external use)"""
        try:
            if not FileUtils.is_image_file(file_path):
                return None

            processor = ExifProcessor()
            return processor.extract_exif_data(file_path)

        except Exception as e:
            self.logger.error(f"Error getting EXIF data: {e}")
            return None
