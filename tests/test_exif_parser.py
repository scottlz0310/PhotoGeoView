#!/usr/bin/env python3
"""
EXIF Parser Test Suite
仕様書に従ったEXIF解析機能のテスト

This test file follows the project specification:
- Located in tests/ directory (not root)
- Uses logging instead of print statements
- Follows project structure guidelines
"""

import sys
import os
import unittest
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.exif_processor import ExifProcessor
from src.utils.gps_utils import GPSUtils
from src.utils.file_utils import FileUtils
from src.core.logger import get_logger

logger = get_logger(__name__)


class TestExifProcessor(unittest.TestCase):
    """Test cases for EXIF processing functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = ExifProcessor()
        logger.info("Setting up EXIF processor test")

    def test_extract_exif_data_nonexistent_file(self):
        """Test EXIF extraction with non-existent file"""
        logger.debug("Testing EXIF extraction with non-existent file")

        result = self.processor.extract_exif_data("nonexistent.jpg")

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)
        logger.info("✓ Non-existent file handling test passed")

    def test_extract_exif_data_empty_file(self):
        """Test EXIF extraction with empty file"""
        logger.debug("Testing EXIF extraction with empty file")

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            try:
                result = self.processor.extract_exif_data(temp_file.name)
                self.assertIsInstance(result, dict)
                logger.info("✓ Empty file handling test passed")
            finally:
                os.unlink(temp_file.name)

    def test_extract_exif_data_sample_image(self):
        """Test EXIF extraction with sample image"""
        logger.debug("Testing EXIF extraction with sample image")

        try:
            from PIL import Image

            # Create a simple test image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                try:
                    # Create a 100x100 test image
                    img = Image.new('RGB', (100, 100), color='blue')
                    img.save(temp_file.name, "JPEG")

                    # Test EXIF extraction
                    result = self.processor.extract_exif_data(temp_file.name)

                    self.assertIsInstance(result, dict)
                    self.assertGreater(len(result), 0)

                    # Should contain basic file information
                    self.assertIn('File Name', result)
                    self.assertIn('File Size', result)
                    self.assertIn('Modified', result)

                    logger.info("✓ Sample image EXIF extraction test passed")

                except ImportError:
                    logger.warning("PIL not available, skipping image creation test")
                    self.skipTest("PIL not available")
                finally:
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)

        except Exception as e:
            logger.error(f"Sample image test failed: {e}")
            self.fail(f"Sample image test failed: {e}")


class TestGPSUtils(unittest.TestCase):
    """Test cases for GPS utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        logger.info("Setting up GPS utils test")

    def test_validate_coordinates_valid(self):
        """Test GPS coordinate validation with valid coordinates"""
        logger.debug("Testing GPS coordinate validation with valid coordinates")

        test_cases = [
            (0, 0),           # Equator, Prime Meridian
            (35.6762, 139.6503),  # Tokyo
            (40.7128, -74.0060),  # New York
            (51.5074, -0.1278),   # London
            (90, 180),        # Valid extremes
            (-90, -180),      # Valid extremes
        ]

        for lat, lon in test_cases:
            with self.subTest(lat=lat, lon=lon):
                result = GPSUtils.validate_coordinates(lat, lon)
                self.assertTrue(result, f"Coordinates ({lat}, {lon}) should be valid")

        logger.info("✓ Valid coordinates test passed")

    def test_validate_coordinates_invalid(self):
        """Test GPS coordinate validation with invalid coordinates"""
        logger.debug("Testing GPS coordinate validation with invalid coordinates")

        test_cases = [
            (91, 0),      # Invalid latitude (too high)
            (-91, 0),     # Invalid latitude (too low)
            (0, 181),     # Invalid longitude (too high)
            (0, -181),    # Invalid longitude (too low)
            (100, 200),   # Both invalid
        ]

        for lat, lon in test_cases:
            with self.subTest(lat=lat, lon=lon):
                result = GPSUtils.validate_coordinates(lat, lon)
                self.assertFalse(result, f"Coordinates ({lat}, {lon}) should be invalid")

        logger.info("✓ Invalid coordinates test passed")

    def test_format_coordinates(self):
        """Test GPS coordinate formatting"""
        logger.debug("Testing GPS coordinate formatting")

        test_cases = [
            ((35.6762, 139.6503), "35.676200°N, 139.650300°E"),
            ((40.7128, -74.0060), "40.712800°N, 74.006000°W"),
            ((-33.8688, 151.2093), "33.868800°S, 151.209300°E"),
            ((0, 0), "0.000000°N, 0.000000°E"),
        ]

        for (lat, lon), expected in test_cases:
            with self.subTest(lat=lat, lon=lon):
                result = GPSUtils.format_coordinates(lat, lon)
                self.assertEqual(result, expected)

        logger.info("✓ Coordinate formatting test passed")

    def test_parse_rational(self):
        """Test rational number parsing"""
        logger.debug("Testing rational number parsing")

        test_cases = [
            ("123/456", 0.26973684210526316),
            ("42", 42.0),
            ("0/1", 0.0),
            ("100/1", 100.0),
            ("1/3", 0.3333333333333333),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = GPSUtils._parse_rational(input_str)
                self.assertIsNotNone(result)
                self.assertAlmostEqual(result, expected, places=10)

        # Test invalid cases
        invalid_cases = ["invalid", "1/0", "", "abc/def"]
        for input_str in invalid_cases:
            with self.subTest(input=input_str):
                result = GPSUtils._parse_rational(input_str)
                self.assertIsNone(result)

        logger.info("✓ Rational parsing test passed")


class TestFileUtils(unittest.TestCase):
    """Test cases for file utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        logger.info("Setting up file utils test")

    def test_format_file_size(self):
        """Test file size formatting"""
        logger.debug("Testing file size formatting")

        test_cases = [
            (0, "0 B"),
            (500, "500.0 B"),
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (1048576, "1.0 MB"),
            (1073741824, "1.0 GB"),
            (1099511627776, "1.0 TB"),
        ]

        for size_bytes, expected in test_cases:
            with self.subTest(size=size_bytes):
                result = FileUtils.format_file_size(size_bytes)
                self.assertEqual(result, expected)

        logger.info("✓ File size formatting test passed")

    def test_is_image_file(self):
        """Test image file detection"""
        logger.debug("Testing image file detection")

        image_files = [
            "test.jpg", "test.jpeg", "test.JPEG", "test.JPG",
            "test.png", "test.PNG", "test.bmp", "test.tiff",
            "test.tif", "test.gif", "test.webp"
        ]

        non_image_files = [
            "test.txt", "test.doc", "test.pdf", "test.mp4",
            "test.mp3", "test.zip", "test", "test.xyz"
        ]

        for file_path in image_files:
            with self.subTest(file=file_path):
                result = FileUtils.is_image_file(file_path)
                self.assertTrue(result, f"{file_path} should be detected as image")

        for file_path in non_image_files:
            with self.subTest(file=file_path):
                result = FileUtils.is_image_file(file_path)
                self.assertFalse(result, f"{file_path} should not be detected as image")

        logger.info("✓ Image file detection test passed")

    def test_get_file_info_nonexistent(self):
        """Test file info extraction with non-existent file"""
        logger.debug("Testing file info extraction with non-existent file")

        result = FileUtils.get_file_info("nonexistent_file.txt")
        self.assertIsNone(result)

        logger.info("✓ Non-existent file info test passed")


def run_test_suite():
    """Run the complete EXIF test suite"""
    logger.info("Starting EXIF Parser Test Suite")

    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTest(unittest.makeSuite(TestExifProcessor))
    suite.addTest(unittest.makeSuite(TestGPSUtils))
    suite.addTest(unittest.makeSuite(TestFileUtils))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Log results
    if result.wasSuccessful():
        logger.info("✓ All EXIF parser tests passed")
        return 0
    else:
        logger.error(f"✗ Tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = run_test_suite()
    sys.exit(exit_code)
