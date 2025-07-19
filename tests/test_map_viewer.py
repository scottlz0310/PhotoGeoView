#!/usr/bin/env python3
"""
Map Viewer Test Suite
地図表示機能のテスト (仕様書準拠)

Tests the map viewer functionality as specified in the project documentation.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.logger import get_logger
from src.utils.gps_utils import GPSUtils

logger = get_logger(__name__)


class TestMapViewerIntegration(unittest.TestCase):
    """Test cases for map viewer integration"""

    def setUp(self):
        """Set up test fixtures"""
        logger.info("Setting up map viewer test")

    def test_gps_coordinates_processing(self):
        """Test GPS coordinate processing for map display"""
        logger.debug("Testing GPS coordinate processing for map display")

        # Test coordinates from famous locations
        test_locations = [
            {
                'name': 'Tokyo Tower',
                'lat': 35.6586,
                'lon': 139.7454,
                'expected_valid': True
            },
            {
                'name': 'Statue of Liberty',
                'lat': 40.6892,
                'lon': -74.0445,
                'expected_valid': True
            },
            {
                'name': 'Eiffel Tower',
                'lat': 48.8584,
                'lon': 2.2945,
                'expected_valid': True
            },
            {
                'name': 'Invalid Location',
                'lat': 91.0,
                'lon': 181.0,
                'expected_valid': False
            }
        ]

        for location in test_locations:
            with self.subTest(location=location['name']):
                is_valid = GPSUtils.validate_coordinates(
                    location['lat'],
                    location['lon']
                )
                self.assertEqual(
                    is_valid,
                    location['expected_valid'],
                    f"Validation for {location['name']} should be {location['expected_valid']}"
                )

                if is_valid:
                    formatted = GPSUtils.format_coordinates(
                        location['lat'],
                        location['lon']
                    )
                    self.assertIsInstance(formatted, str)
                    self.assertTrue(len(formatted) > 0)

        logger.info("✓ GPS coordinate processing test passed")

    def test_coordinate_formatting_for_map_display(self):
        """Test coordinate formatting suitable for map markers"""
        logger.debug("Testing coordinate formatting for map markers")

        # Test various coordinate formats
        test_cases = [
            {
                'lat': 35.6762,
                'lon': 139.6503,
                'name': 'Tokyo',
                'expected_contains': ['35.676200', '139.650300', '°N', '°E']
            },
            {
                'lat': -33.8688,
                'lon': 151.2093,
                'name': 'Sydney',
                'expected_contains': ['33.868800', '151.209300', '°S', '°E']
            },
            {
                'lat': 51.5074,
                'lon': -0.1278,
                'name': 'London',
                'expected_contains': ['51.507400', '0.127800', '°N', '°W']
            }
        ]

        for case in test_cases:
            with self.subTest(location=case['name']):
                formatted = GPSUtils.format_coordinates(case['lat'], case['lon'])

                for expected_part in case['expected_contains']:
                    self.assertIn(
                        expected_part,
                        formatted,
                        f"Formatted coordinate should contain '{expected_part}'"
                    )

        logger.info("✓ Coordinate formatting for map display test passed")

    def test_map_marker_data_preparation(self):
        """Test data preparation for map markers"""
        logger.debug("Testing map marker data preparation")

        # Simulate EXIF data with GPS coordinates
        sample_photos = [
            {
                'file_path': '/path/to/photo1.jpg',
                'gps_coordinates': (35.6762, 139.6503),
                'camera': 'Canon EOS R5'
            },
            {
                'file_path': '/path/to/photo2.jpg',
                'gps_coordinates': (40.7128, -74.0060),
                'camera': 'Nikon D850'
            },
            {
                'file_path': '/path/to/photo3.jpg',
                'gps_coordinates': None,  # No GPS data
                'camera': 'Sony A7R IV'
            }
        ]

        # Process photos for map display
        map_markers = []

        for photo in sample_photos:
            if photo['gps_coordinates']:
                lat, lon = photo['gps_coordinates']

                if GPSUtils.validate_coordinates(lat, lon):
                    marker_data = {
                        'file_path': photo['file_path'],
                        'lat': lat,
                        'lon': lon,
                        'formatted_coords': GPSUtils.format_coordinates(lat, lon),
                        'camera': photo['camera']
                    }
                    map_markers.append(marker_data)

        # Verify results
        self.assertEqual(len(map_markers), 2, "Should have 2 valid markers")

        for marker in map_markers:
            self.assertIn('lat', marker)
            self.assertIn('lon', marker)
            self.assertIn('formatted_coords', marker)
            self.assertTrue(
                GPSUtils.validate_coordinates(marker['lat'], marker['lon'])
            )

        logger.info("✓ Map marker data preparation test passed")


def run_map_test_suite():
    """Run the complete map viewer test suite"""
    logger.info("Starting Map Viewer Test Suite")

    # Create and run test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapViewerIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Log results
    if result.wasSuccessful():
        logger.info("✓ All map viewer tests passed")
        return True
    else:
        logger.error(f"✗ Map tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return False


if __name__ == "__main__":
    success = run_map_test_suite()
    sys.exit(0 if success else 1)
