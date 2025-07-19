"""
EXIF Info Module for PhotoGeoView
Displays image metadata and EXIF information
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QGroupBox, QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from pathlib import Path
from typing import Optional, Dict, Any
import os
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    pil_available = True
except ImportError:
    pil_available = False

from src.core.logger import get_logger

logger = get_logger(__name__)


class ExifLoader(QThread):
    """Background thread for loading EXIF data"""

    exif_loaded = pyqtSignal(str, dict)  # file_path, exif_data

    def __init__(self):
        super().__init__()
        self.file_path: str = ""
        self._stop_requested = False

    def set_file(self, file_path: str) -> None:
        """Set file to process"""
        self.file_path = file_path
        self._stop_requested = False

    def stop(self) -> None:
        """Stop EXIF loading"""
        self._stop_requested = True

    def run(self) -> None:
        """Load EXIF data in background"""
        try:
            if self._stop_requested:
                return

            exif_data = self.extract_exif_data(self.file_path)

            if not self._stop_requested:
                self.exif_loaded.emit(self.file_path, exif_data)

        except Exception as e:
            logger.error(f"Error in EXIF loader thread: {e}")

    def extract_exif_data(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF data from image file"""
        exif_data = {}

        try:
            # Basic file info
            path_obj = Path(file_path)
            stat_info = path_obj.stat()

            exif_data.update({
                'File Name': path_obj.name,
                'File Size': self.format_file_size(stat_info.st_size),
                'Modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'Full Path': str(path_obj.absolute())
            })

            if pil_available:
                # Load image with PIL
                with Image.open(file_path) as img:
                    # Image dimensions
                    exif_data.update({
                        'Dimensions': f"{img.width} × {img.height}",
                        'Format': img.format or 'Unknown',
                        'Mode': img.mode
                    })

                    # Extract EXIF data
                    exif_dict = img.getexif()
                    if exif_dict:
                        exif_data.update(self.parse_exif_dict(exif_dict))

                        # GPS data
                        gps_data = self.extract_gps_data(exif_dict)
                        if gps_data:
                            exif_data.update(gps_data)
            else:
                # Fallback using QPixmap
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    exif_data.update({
                        'Dimensions': f"{pixmap.width()} × {pixmap.height()}",
                        'Format': path_obj.suffix.upper().lstrip('.') if path_obj.suffix else 'Unknown'
                    })

        except Exception as e:
            logger.error(f"Error extracting EXIF data from {file_path}: {e}")
            exif_data['Error'] = str(e)

        return exif_data

    def parse_exif_dict(self, exif_dict: Any) -> Dict[str, str]:
        """Parse EXIF dictionary into readable format"""
        parsed_data = {}

        try:
            for tag_id, value in exif_dict.items():
                tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")

                # Skip large binary data
                if isinstance(value, bytes) and len(value) > 100:
                    continue

                # Format specific tags
                if tag_name == 'DateTime':
                    try:
                        parsed_data['Date Taken'] = str(value)
                    except:
                        parsed_data[tag_name] = str(value)
                elif tag_name == 'ExposureTime':
                    if isinstance(value, tuple) and len(value) == 2:
                        parsed_data['Exposure Time'] = f"{value[0]}/{value[1]} sec"
                    else:
                        parsed_data['Exposure Time'] = str(value)
                elif tag_name == 'FNumber':
                    if isinstance(value, tuple) and len(value) == 2:
                        f_number = value[0] / value[1] if value[1] != 0 else value[0]
                        parsed_data['F-Number'] = f"f/{f_number:.1f}"
                    else:
                        parsed_data['F-Number'] = str(value)
                elif tag_name == 'ISOSpeedRatings':
                    parsed_data['ISO Speed'] = str(value)
                elif tag_name == 'FocalLength':
                    if isinstance(value, tuple) and len(value) == 2:
                        focal_length = value[0] / value[1] if value[1] != 0 else value[0]
                        parsed_data['Focal Length'] = f"{focal_length:.1f}mm"
                    else:
                        parsed_data['Focal Length'] = str(value)
                elif tag_name in ['Make', 'Model', 'Software']:
                    parsed_data[tag_name] = str(value)
                elif len(str(value)) < 100:  # Only include short values
                    parsed_data[tag_name] = str(value)

        except Exception as e:
            logger.error(f"Error parsing EXIF dictionary: {e}")

        return parsed_data

    def extract_gps_data(self, exif_dict: Any) -> Dict[str, str]:
        """Extract GPS data from EXIF"""
        gps_data = {}

        try:
            if pil_available and 34853 in exif_dict:  # GPS IFD
                gps_info = exif_dict[34853]

                if isinstance(gps_info, dict):
                    # Parse GPS coordinates
                    lat = self.get_gps_coordinates(gps_info, 'Latitude')
                    lon = self.get_gps_coordinates(gps_info, 'Longitude')

                    if lat and lon:
                        gps_data['GPS Latitude'] = lat
                        gps_data['GPS Longitude'] = lon
                        gps_data['GPS Coordinates'] = f"{lat}, {lon}"

                    # Other GPS data
                    for key, value in gps_info.items():
                        gps_tag = GPSTAGS.get(key, f"GPS_{key}")
                        if gps_tag not in ['GPSLatitude', 'GPSLongitude'] and len(str(value)) < 100:
                            gps_data[f"GPS {gps_tag}"] = str(value)

        except Exception as e:
            logger.error(f"Error extracting GPS data: {e}")

        return gps_data

    def get_gps_coordinates(self, gps_info: Dict[Any, Any], coord_type: str) -> Optional[str]:
        """Extract GPS coordinates in decimal degrees"""
        try:
            if coord_type == 'Latitude':
                coord_key = 2  # GPSLatitude
                ref_key = 1    # GPSLatitudeRef
            else:  # Longitude
                coord_key = 4  # GPSLongitude
                ref_key = 3    # GPSLongitudeRef

            if coord_key in gps_info and ref_key in gps_info:
                coords = gps_info[coord_key]
                ref = gps_info[ref_key]

                if len(coords) == 3:
                    degrees = float(coords[0])
                    minutes = float(coords[1])
                    seconds = float(coords[2])

                    decimal_degrees = degrees + minutes/60.0 + seconds/3600.0

                    if ref in ['S', 'W']:
                        decimal_degrees = -decimal_degrees

                    return f"{decimal_degrees:.6f}°{ref}"

        except Exception as e:
            logger.error(f"Error getting GPS coordinates: {e}")

        return None

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class ExifInfoPanel(QWidget):
    """
    EXIF information display panel
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logger

        # UI components
        self.scroll_area: Optional[QScrollArea] = None
        self.content_widget: Optional[QWidget] = None
        self.no_data_label: Optional[QLabel] = None

        # Current file
        self.current_file: str = ""
        self.current_data: Dict[str, Any] = {}

        # Background loader
        self.exif_loader = ExifLoader()
        self.exif_loader.exif_loaded.connect(self.on_exif_loaded)

        self.setup_ui()

        self.logger.debug("ExifInfoPanel initialized")

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_label = QLabel("Image Information")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # No data label
        self.no_data_label = QLabel("No image selected")
        self.no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_data_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-style: italic;
                padding: 20px;
            }
        """)

        self.scroll_area.setWidget(self.no_data_label)
        layout.addWidget(self.scroll_area)

        self.logger.debug("ExifInfoPanel UI setup complete")

    def load_file_info(self, file_path: str) -> None:
        """Load and display file information"""
        try:
            if not file_path or not Path(file_path).exists():
                self.clear_info()
                return

            self.current_file = file_path

            # Show loading message
            loading_label = QLabel("Loading image information...")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet("color: #666666; padding: 20px;")
            self.scroll_area.setWidget(loading_label)

            # Stop any existing loading
            self.exif_loader.stop()
            self.exif_loader.wait(1000)

            # Start background loading
            self.exif_loader.set_file(file_path)
            self.exif_loader.start()

            self.logger.info(f"Started loading EXIF data for: {file_path}")

        except Exception as e:
            self.logger.error(f"Error loading file info: {e}")
            self.clear_info()

    def on_exif_loaded(self, file_path: str, exif_data: Dict[str, Any]) -> None:
        """Handle loaded EXIF data"""
        try:
            if file_path != self.current_file:
                return  # Ignore outdated data

            self.current_data = exif_data
            self.display_exif_data(exif_data)

        except Exception as e:
            self.logger.error(f"Error handling loaded EXIF data: {e}")

    def display_exif_data(self, data: Dict[str, Any]) -> None:
        """Display EXIF data in the panel"""
        try:
            # Create content widget
            self.content_widget = QWidget()
            layout = QVBoxLayout(self.content_widget)
            layout.setSpacing(10)

            if not data:
                no_data = QLabel("No EXIF data available")
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data.setStyleSheet("color: #666666; padding: 20px;")
                layout.addWidget(no_data)
            else:
                # Group data by category
                categories = self.categorize_data(data)

                for category, items in categories.items():
                    if items:
                        group_box = self.create_group_box(category, items)
                        layout.addWidget(group_box)

            # Add stretch to push content to top
            layout.addStretch()

            # Set the widget in scroll area
            self.scroll_area.setWidget(self.content_widget)

        except Exception as e:
            self.logger.error(f"Error displaying EXIF data: {e}")

    def categorize_data(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Categorize EXIF data for better display"""
        categories = {
            'File Information': {},
            'Camera Settings': {},
            'Image Details': {},
            'GPS Information': {},
            'Other': {}
        }

        try:
            for key, value in data.items():
                key_lower = key.lower()

                if any(x in key_lower for x in ['file', 'path', 'size', 'modified']):
                    categories['File Information'][key] = str(value)
                elif any(x in key_lower for x in ['exposure', 'iso', 'focal', 'f-number', 'flash']):
                    categories['Camera Settings'][key] = str(value)
                elif any(x in key_lower for x in ['dimensions', 'format', 'mode', 'date', 'make', 'model']):
                    categories['Image Details'][key] = str(value)
                elif 'gps' in key_lower:
                    categories['GPS Information'][key] = str(value)
                else:
                    categories['Other'][key] = str(value)

        except Exception as e:
            self.logger.error(f"Error categorizing data: {e}")

        return categories

    def create_group_box(self, title: str, items: Dict[str, str]) -> QGroupBox:
        """Create a group box for a category of information"""
        group_box = QGroupBox(title)
        layout = QGridLayout(group_box)
        layout.setSpacing(5)

        row = 0
        for key, value in items.items():
            # Key label
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet("font-weight: bold; color: #333333;")
            key_label.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Value label
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setStyleSheet("color: #555555;")

            layout.addWidget(key_label, row, 0)
            layout.addWidget(value_label, row, 1)
            row += 1

        # Set column stretch
        layout.setColumnStretch(1, 1)

        return group_box

    def clear_info(self) -> None:
        """Clear the information panel"""
        try:
            # Stop any loading
            self.exif_loader.stop()

            # Reset data
            self.current_file = ""
            self.current_data.clear()

            # Show no data message
            self.scroll_area.setWidget(self.no_data_label)

            self.logger.debug("EXIF info panel cleared")

        except Exception as e:
            self.logger.error(f"Error clearing info panel: {e}")

    def get_current_data(self) -> Dict[str, Any]:
        """Get current EXIF data"""
        return self.current_data.copy()

    def __del__(self) -> None:
        """Handle widget destruction"""
        try:
            if hasattr(self, 'exif_loader'):
                self.exif_loader.stop()
                self.exif_loader.wait(1000)

        except Exception as e:
            self.logger.error(f"Error in EXIF panel destructor: {e}")
