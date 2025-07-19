"""
EXIF data processing core
Handles EXIF data extraction and parsing from images
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from src.core.logger import get_logger
from src.utils.gps_utils import GPSUtils
from src.utils.file_utils import FileUtils

logger = get_logger(__name__)

# Check library availability
try:
    import exifread
    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False
    logger.warning("exifread library not available")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL library not available")


class ExifProcessor:
    """Core EXIF processing functionality"""

    def __init__(self):
        self.logger = logger

    def extract_exif_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract EXIF data from image file

        Args:
            file_path: Path to image file

        Returns:
            Dictionary containing EXIF data
        """
        if not Path(file_path).exists():
            return {}

        exif_data = {}

        # Get basic file information
        file_info = FileUtils.get_file_info(file_path)
        if file_info:
            exif_data.update(file_info)

        # Try ExifRead first (more reliable)
        if EXIFREAD_AVAILABLE:
            exif_data.update(self._extract_with_exifread(file_path))

        # Fallback to PIL if ExifRead fails
        elif PIL_AVAILABLE:
            exif_data.update(self._extract_with_pil(file_path))

        return exif_data

    def _extract_with_exifread(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF using exifread library"""
        exif_data = {}

        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)

                if tags:
                    # Parse basic EXIF data
                    exif_data.update(self._parse_exifread_tags(tags))

                    # Extract GPS data
                    gps_data = self._extract_gps_from_exifread(tags)
                    if gps_data:
                        exif_data.update(gps_data)

        except Exception as e:
            self.logger.debug(f"ExifRead extraction failed for {file_path}: {e}")

        return exif_data

    def _extract_with_pil(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF using PIL library"""
        exif_data = {}

        try:
            with Image.open(file_path) as img:
                if hasattr(img, '_getexif'):
                    exif_dict = img._getexif()
                    if exif_dict:
                        exif_data.update(self._parse_pil_exif(exif_dict))

        except Exception as e:
            self.logger.debug(f"PIL extraction failed for {file_path}: {e}")

        return exif_data

    def _parse_exifread_tags(self, tags: Dict[str, Any]) -> Dict[str, str]:
        """Parse ExifRead tags into readable format"""
        parsed = {}

        # Mapping of important EXIF tags
        tag_mapping = {
            'Image Make': 'Camera Make',
            'Image Model': 'Camera Model',
            'Image DateTime': 'Date Taken',
            'Image Orientation': 'Orientation',
            'EXIF DateTimeOriginal': 'Date Original',
            'EXIF ExifImageWidth': 'Image Width',
            'EXIF ExifImageLength': 'Image Height',
            'EXIF ISO': 'ISO Speed',
            'EXIF FNumber': 'F-Number',
            'EXIF ExposureTime': 'Exposure Time',
            'EXIF FocalLength': 'Focal Length',
            'EXIF Flash': 'Flash',
            'EXIF WhiteBalance': 'White Balance',
            'EXIF LensModel': 'Lens Model'
        }

        for tag_key, tag_value in tags.items():
            try:
                if tag_key in tag_mapping:
                    readable_key = tag_mapping[tag_key]
                    parsed[readable_key] = str(tag_value)
                else:
                    # Include other important tags
                    tag_str = str(tag_key)
                    if any(keyword in tag_str.lower() for keyword in
                           ['camera', 'lens', 'exposure', 'iso', 'flash', 'focus']):
                        parsed[tag_str] = str(tag_value)

            except Exception as e:
                self.logger.debug(f"Error parsing tag {tag_key}: {e}")

        return parsed

    def _extract_gps_from_exifread(self, tags: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract GPS data from ExifRead tags"""
        try:
            gps_tags = ['GPS GPSLatitude', 'GPS GPSLatitudeRef',
                       'GPS GPSLongitude', 'GPS GPSLongitudeRef']

            # Check if all required GPS tags are present
            if not all(tag in tags for tag in gps_tags):
                return None

            lat_tag = tags['GPS GPSLatitude']
            lat_ref_tag = tags['GPS GPSLatitudeRef']
            lon_tag = tags['GPS GPSLongitude']
            lon_ref_tag = tags['GPS GPSLongitudeRef']

            # Convert to decimal degrees
            lat_decimal = GPSUtils.convert_gps_to_decimal(lat_tag, lat_ref_tag)
            lon_decimal = GPSUtils.convert_gps_to_decimal(lon_tag, lon_ref_tag)

            if lat_decimal is not None and lon_decimal is not None:
                if GPSUtils.validate_coordinates(lat_decimal, lon_decimal):
                    return {
                        'GPS Latitude': f"{lat_decimal:.6f}°",
                        'GPS Longitude': f"{lon_decimal:.6f}°",
                        'GPS Coordinates': GPSUtils.format_coordinates(lat_decimal, lon_decimal),
                        'gps_coordinates': (lat_decimal, lon_decimal)  # For programmatic use
                    }

        except Exception as e:
            self.logger.debug(f"GPS extraction error: {e}")

        return None

    def _parse_pil_exif(self, exif_dict: Dict[int, Any]) -> Dict[str, str]:
        """Parse PIL EXIF dictionary"""
        from PIL.ExifTags import TAGS
        parsed = {}

        try:
            for tag_id, value in exif_dict.items():
                tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                parsed[tag_name] = str(value)

        except Exception as e:
            self.logger.debug(f"PIL EXIF parsing error: {e}")

        return parsed
