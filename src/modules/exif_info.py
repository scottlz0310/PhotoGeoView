"""
EXIF情報表示パネル
画像のEXIF情報を抽出・表示し、GPS座標も含めて整理
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, QThread, QTimer, Qt
from PyQt6.QtGui import QFont

import logging
import exifread
from PIL import Image
from typing import Optional, Dict, Any, List

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
    import exifread
    exifread_available = True
except ImportError:
    exifread_available = False

try:
    from PIL import Image
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
        """Load EXIF data in background using ExifRead"""
        try:
            if self._stop_requested:
                return

            if not self.file_path or not Path(self.file_path).exists():
                return

            path_obj = Path(self.file_path)
            exif_data = {}

            # Basic file information
            try:
                stat_info = path_obj.stat()
                exif_data.update({
                    'File Name': path_obj.name,
                    'File Size': self.format_file_size(stat_info.st_size),
                    'Modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'Full Path': str(path_obj.absolute())
                })
            except Exception as e:
                logger.warning(f"Error getting file stats: {e}")

            # Use ExifRead for EXIF data
            if exifread_available:
                try:
                    with open(self.file_path, 'rb') as f:
                        tags = exifread.process_file(f, details=False)

                        if tags:
                            # Parse basic EXIF data
                            exif_data.update(self.parse_exifread_tags(tags))

                            # Extract GPS data
                            gps_data = self.extract_gps_from_exifread(tags)
                            if gps_data:
                                logger.debug(f"ExifRead GPS data extracted: {gps_data}")
                                exif_data.update(gps_data)
                            else:
                                logger.debug(f"No GPS data found in ExifRead tags for {self.file_path}")

                except Exception as e:
                    logger.warning(f"Error reading EXIF with ExifRead: {e}")

            # Use PIL only for image dimensions and format (not EXIF)
            if pil_available:
                try:
                    with Image.open(self.file_path) as img:
                        exif_data.update({
                            'Dimensions': f"{img.width} × {img.height}",
                            'Format': img.format or 'Unknown',
                            'Mode': img.mode
                        })
                except Exception as e:
                    logger.warning(f"Error getting image info with PIL: {e}")
                    # Fallback using QPixmap for dimensions
                    try:
                        pixmap = QPixmap(self.file_path)
                        if not pixmap.isNull():
                            exif_data.update({
                                'Dimensions': f"{pixmap.width()} × {pixmap.height()}",
                                'Format': path_obj.suffix.upper().lstrip('.') if path_obj.suffix else 'Unknown'
                            })
                    except Exception as e2:
                        logger.warning(f"Error getting image info with QPixmap: {e2}")

            if not self._stop_requested:
                # Debug GPS coordinates
                if 'gps_coordinates' in exif_data:
                    logger.info(f"GPS coordinates found: {exif_data['gps_coordinates']}")
                else:
                    logger.warning(f"No GPS coordinates in EXIF data for {self.file_path}")
                    # Log available GPS-related keys
                    gps_keys = [key for key in exif_data.keys() if 'GPS' in key.upper()]
                    if gps_keys:
                        logger.debug(f"Available GPS keys: {gps_keys}")

                self.exif_loaded.emit(self.file_path, exif_data)

        except Exception as e:
            logger.error(f"Error in ExifLoader.run(): {e}")
            if not self._stop_requested:
                self.exif_loaded.emit(self.file_path, {'Error': str(e)})

    def parse_exifread_tags(self, tags: Dict[str, Any]) -> Dict[str, str]:
        """Parse ExifRead tags into readable format"""
        parsed_data = {}

        try:
            # Common EXIF tags mapping
            tag_mapping = {
                'Image Make': 'Camera Make',
                'Image Model': 'Camera Model',
                'Image DateTime': 'Date Taken',
                'EXIF DateTimeOriginal': 'Date Original',
                'EXIF ExposureTime': 'Exposure Time',
                'EXIF FNumber': 'F-Number',
                'EXIF ISOSpeedRatings': 'ISO Speed',
                'EXIF FocalLength': 'Focal Length',
                'EXIF Flash': 'Flash',
                'EXIF WhiteBalance': 'White Balance',
                'Image Orientation': 'Orientation',
                'Image XResolution': 'X Resolution',
                'Image YResolution': 'Y Resolution',
                'EXIF ColorSpace': 'Color Space',
                'EXIF ExifImageWidth': 'EXIF Width',
                'EXIF ExifImageLength': 'EXIF Height'
            }

            for tag_key, tag_value in tags.items():
                if tag_key in tag_mapping:
                    display_name = tag_mapping[tag_key]
                    parsed_data[display_name] = str(tag_value)
                elif tag_key.startswith('EXIF') or tag_key.startswith('Image'):
                    # Include other important EXIF tags
                    if len(str(tag_value)) < 100:  # Skip very long values
                        parsed_data[tag_key.replace('EXIF ', '').replace('Image ', '')] = str(tag_value)

        except Exception as e:
            logger.error(f"Error parsing ExifRead tags: {e}")

        return parsed_data

    def extract_gps_from_exifread(self, tags: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract GPS data from ExifRead tags"""
        try:
            gps_data = {}

            # GPS coordinates
            lat_tag = tags.get('GPS GPSLatitude')
            lat_ref_tag = tags.get('GPS GPSLatitudeRef')
            lon_tag = tags.get('GPS GPSLongitude')
            lon_ref_tag = tags.get('GPS GPSLongitudeRef')

            logger.debug(f"GPS tags found - Lat: {lat_tag}, LatRef: {lat_ref_tag}, Lon: {lon_tag}, LonRef: {lon_ref_tag}")

            if lat_tag and lat_ref_tag and lon_tag and lon_ref_tag:
                # Convert GPS coordinates
                try:
                    lat_decimal = self.convert_gps_to_decimal(lat_tag, lat_ref_tag)
                    lon_decimal = self.convert_gps_to_decimal(lon_tag, lon_ref_tag)

                    if lat_decimal is not None and lon_decimal is not None:
                        gps_data.update({
                            'GPS Latitude': f"{lat_decimal:.8f}°",
                            'GPS Longitude': f"{lon_decimal:.8f}°",
                            'GPS Coordinates': f"{lat_decimal:.8f}, {lon_decimal:.8f}",
                            'gps_coordinates': (lat_decimal, lon_decimal)  # For map use
                        })
                        logger.debug(f"GPS coordinates extracted: ({lat_decimal}, {lon_decimal})")
                    else:
                        logger.debug("Failed to convert GPS coordinates to decimal")
                except Exception as e:
                    logger.error(f"Error converting GPS coordinates: {e}")
            else:
                logger.debug("GPS coordinate tags not found or incomplete")

            # Other GPS info
            altitude_tag = tags.get('GPS GPSAltitude')
            if altitude_tag:
                gps_data['GPS Altitude'] = str(altitude_tag)

            timestamp_tag = tags.get('GPS GPSTimeStamp')
            datestamp_tag = tags.get('GPS GPSDateStamp')
            if timestamp_tag:
                gps_data['GPS Time'] = str(timestamp_tag)
            if datestamp_tag:
                gps_data['GPS Date'] = str(datestamp_tag)

            # Add all other GPS tags
            for tag_key, tag_value in tags.items():
                if tag_key.startswith('GPS ') and tag_key not in ['GPS GPSLatitude', 'GPS GPSLongitude']:
                    if len(str(tag_value)) < 100:
                        gps_data[tag_key] = str(tag_value)

            return gps_data if gps_data else None

        except Exception as e:
            logger.error(f"Error extracting GPS data: {e}")
            return None

    def convert_gps_to_decimal(self, gps_coord: Any, gps_ref: Any) -> Optional[float]:
        """Convert GPS coordinates from DMS to decimal degrees"""
        try:
            # Convert GPS coordinate to decimal
            coord_str = str(gps_coord)
            ref_str = str(gps_ref).upper()

            logger.debug(f"Converting GPS coordinate: {coord_str}, ref: {ref_str}")

            # Parse the coordinate string [DD, MM, SS]
            if '[' in coord_str and ']' in coord_str:
                coord_parts = coord_str.strip('[]').split(', ')
                if len(coord_parts) >= 3:
                    # Parse degrees, minutes, seconds
                    degrees = self._parse_rational(coord_parts[0])
                    minutes = self._parse_rational(coord_parts[1])
                    seconds = self._parse_rational(coord_parts[2])

                    if degrees is not None and minutes is not None and seconds is not None:
                        decimal = degrees + minutes / 60 + seconds / 3600

                        # Apply hemisphere correction
                        if ref_str in ['S', 'W']:
                            decimal = -decimal

                        logger.debug(f"Converted to decimal: {decimal}")
                        return decimal

        except Exception as e:
            logger.error(f"Error converting GPS coordinate to decimal: {e}")

        return None
        """Convert GPS coordinate string to decimal degrees"""
        try:
            # Parse coordinate string like "[45, 26, 123/10]"
            coord_str = gps_coord.strip('[]').replace(' ', '')
            parts = coord_str.split(',')

            if len(parts) >= 3:
                # Parse degrees
                degrees = float(parts[0])

                # Parse minutes
                minutes = float(parts[1])

                # Parse seconds (might be a fraction)
                seconds_str = parts[2]
                if '/' in seconds_str:
                    num, den = seconds_str.split('/')
                    seconds = float(num) / float(den)
                else:
                    seconds = float(seconds_str)

                # Convert to decimal
                decimal = degrees + minutes / 60 + seconds / 3600

                # Apply hemisphere
                if gps_ref.upper() in ['S', 'W']:
                    decimal = -decimal

                return decimal

        except Exception as e:
            logger.debug(f"Error parsing GPS coordinate '{gps_coord}': {e}")

        return None

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

    def _parse_rational(self, rational_str: str) -> Optional[float]:
        """Parse a rational number string (e.g., '123/456' or '123')"""
        try:
            rational_str = rational_str.strip()
            if '/' in rational_str:
                numerator, denominator = rational_str.split('/')
                return float(numerator) / float(denominator)
            else:
                return float(rational_str)
        except Exception:
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

    def convert_gps_to_decimal(self, gps_coord: Any, gps_ref: Any) -> Optional[float]:
        """Convert GPS coordinates from DMS to decimal degrees"""
        try:
            # Convert GPS coordinate to decimal
            coord_str = str(gps_coord)
            ref_str = str(gps_ref).upper()

            # Parse the coordinate string [DD, MM, SS]
            if '[' in coord_str and ']' in coord_str:
                coord_parts = coord_str.strip('[]').split(', ')
                if len(coord_parts) >= 3:
                    # Parse degrees, minutes, seconds
                    degrees = self._parse_rational(coord_parts[0])
                    minutes = self._parse_rational(coord_parts[1])
                    seconds = self._parse_rational(coord_parts[2])

                    if degrees is not None and minutes is not None and seconds is not None:
                        decimal = degrees + minutes / 60 + seconds / 3600

                        # Apply hemisphere correction
                        if ref_str in ['S', 'W']:
                            decimal = -decimal

                        return decimal

        except Exception as e:
            self.logger.debug(f"Error converting GPS coordinate to decimal: {e}")

        return None

    def _parse_rational(self, rational_str: str) -> Optional[float]:
        """Parse a rational number string (e.g., '123/456' or '123')"""
        try:
            rational_str = rational_str.strip()
            if '/' in rational_str:
                numerator, denominator = rational_str.split('/')
                return float(numerator) / float(denominator)
            else:
                return float(rational_str)
        except Exception:
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

    # シグナル定義
    data_loaded = pyqtSignal(str, dict)  # file_path, exif_data

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

            # GPS座標データが読み込まれたことを通知
            self.data_loaded.emit(file_path, exif_data)

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

    def get_gps_coordinates(self) -> Optional[tuple[float, float]]:
        """Extract GPS coordinates from current EXIF data"""
        try:
            if not self.current_data:
                return None

            # First try to get directly stored coordinates from ExifRead processing
            if 'gps_coordinates' in self.current_data:
                coords = self.current_data['gps_coordinates']
                if isinstance(coords, tuple) and len(coords) == 2:
                    return coords

            # Fallback: Look for GPS data in EXIF format
            gps_data = self.current_data.get('gps', {})
            if not gps_data:
                return None

            # Extract latitude
            lat_data = gps_data.get('GPS GPSLatitude')
            lat_ref = gps_data.get('GPS GPSLatitudeRef')

            # Extract longitude
            lon_data = gps_data.get('GPS GPSLongitude')
            lon_ref = gps_data.get('GPS GPSLongitudeRef')

            if not all([lat_data, lat_ref, lon_data, lon_ref]):
                return None

            # Convert DMS to decimal degrees
            lat_decimal = self._dms_to_decimal(lat_data, lat_ref)
            lon_decimal = self._dms_to_decimal(lon_data, lon_ref)

            if lat_decimal is None or lon_decimal is None:
                return None

            return (lat_decimal, lon_decimal)

        except Exception as e:
            self.logger.error(f"Error extracting GPS coordinates: {e}")
            return None

    def _dms_to_decimal(self, dms_data: Any, ref: str) -> Optional[float]:
        """Convert DMS (Degrees, Minutes, Seconds) to decimal degrees"""
        try:
            if isinstance(dms_data, (list, tuple)) and len(dms_data) >= 3:
                # Handle rational numbers or floats
                degrees = float(dms_data[0]) if hasattr(dms_data[0], 'real') else float(dms_data[0])
                minutes = float(dms_data[1]) if hasattr(dms_data[1], 'real') else float(dms_data[1])
                seconds = float(dms_data[2]) if hasattr(dms_data[2], 'real') else float(dms_data[2])

                decimal = degrees + minutes / 60 + seconds / 3600

                # Apply hemisphere correction
                if ref.upper() in ['S', 'W']:
                    decimal = -decimal

                return decimal

            elif isinstance(dms_data, (int, float)):
                # Already in decimal format
                decimal = float(dms_data)
                if ref.upper() in ['S', 'W']:
                    decimal = -decimal
                return decimal

        except Exception as e:
            self.logger.debug(f"Error converting DMS to decimal: {e}")

        return None

    def has_gps_data(self) -> bool:
        """Check if current image has GPS data"""
        return self.get_gps_coordinates() is not None

    def __del__(self) -> None:
        """Handle widget destruction"""
        try:
            if hasattr(self, 'exif_loader'):
                self.exif_loader.stop()
                self.exif_loader.wait(1000)

        except Exception as e:
            self.logger.error(f"Error in EXIF panel destructor: {e}")
