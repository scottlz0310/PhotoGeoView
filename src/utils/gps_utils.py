"""
GPS coordinate processing utilities
Shared functions for GPS coordinate conversion and validation
"""

from typing import Any, Optional, Tuple, Union
from src.core.logger import get_logger

logger = get_logger(__name__)


class GPSUtils:
    """Utility class for GPS coordinate processing"""

    @staticmethod
    def convert_gps_to_decimal(gps_coord: Any, gps_ref: Any) -> Optional[float]:
        """
        Convert GPS coordinates from degrees/minutes/seconds format to decimal

        Args:
            gps_coord: GPS coordinate in DMS format
            gps_ref: GPS reference (N/S for latitude, E/W for longitude)

        Returns:
            Decimal coordinate or None if conversion fails
        """
        try:
            if not gps_coord or not gps_ref:
                return None

            # Handle string representation
            coord_str = str(gps_coord)

            # Parse coordinate parts
            if '[' in coord_str and ']' in coord_str:
                # Format: [degrees, minutes, seconds]
                coord_parts = coord_str.strip('[]').split(', ')
                if len(coord_parts) >= 3:
                    degrees = GPSUtils._parse_rational(coord_parts[0])
                    minutes = GPSUtils._parse_rational(coord_parts[1])
                    seconds = GPSUtils._parse_rational(coord_parts[2])

                    if degrees is not None and minutes is not None and seconds is not None:
                        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

                        # Apply reference direction
                        ref_str = str(gps_ref).upper().strip()
                        if ref_str in ['S', 'W']:
                            decimal = -decimal

                        return decimal

            # Try direct float conversion
            try:
                decimal = float(coord_str)
                ref_str = str(gps_ref).upper().strip()
                if ref_str in ['S', 'W']:
                    decimal = -decimal
                return decimal
            except ValueError:
                pass

            return None

        except Exception as e:
            logger.debug(f"GPS coordinate conversion error: {e}")
            return None

    @staticmethod
    def _parse_rational(rational_str: str) -> Optional[float]:
        """
        Parse a rational number string (e.g., "123/456" or "123")

        Args:
            rational_str: String representation of rational number

        Returns:
            Float value or None if parsing fails
        """
        try:
            rational_str = rational_str.strip()

            if '/' in rational_str:
                numerator, denominator = rational_str.split('/')
                if float(denominator) != 0:
                    return float(numerator) / float(denominator)
            else:
                return float(rational_str)

        except (ValueError, ZeroDivisionError):
            pass

        return None

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """
        Validate GPS coordinates

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)

        Returns:
            True if coordinates are valid
        """
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)

    @staticmethod
    def format_coordinates(lat: float, lon: float, precision: int = 6) -> str:
        """
        Format coordinates for display

        Args:
            lat: Latitude
            lon: Longitude
            precision: Decimal places

        Returns:
            Formatted coordinate string
        """
        lat_dir = 'N' if lat >= 0 else 'S'
        lon_dir = 'E' if lon >= 0 else 'W'

        return f"{abs(lat):.{precision}f}°{lat_dir}, {abs(lon):.{precision}f}°{lon_dir}"
