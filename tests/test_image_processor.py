"""
Tests for CS4Coding ImageProcessor with Kiro Integration

Tests the integrated ImageProcessor functionality including:
- Image loading and validation
- EXIF data extraction
- GPS coordinate processing
- Performance monitoring
- Caching system

Author: Kiro AI Integration System
"""

import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

sys.path.append(str(Path(__file__).parent.parent / "src"))

from photogeoview.integration.config_manager import ConfigManager
from photogeoview.integration.image_processor import CS4CodingImageProcessor
from photogeoview.integration.logging_system import LoggerSystem
from photogeoview.integration.models import AIComponent, ImageMetadata, ProcessingStatus


class TestCS4CodingImageProcessor(unittest.TestCase):
    """Test cases for CS4Coding ImageProcessor"""

    def setUp(self):
        """Set up test environment"""

        # Create temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp())

        # Mock dependencies
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)

        # Create ImageProcessor instance
        self.processor = CS4CodingImageProcessor(
            config_manager=self.mock_config_manager,
            logger_system=self.mock_logger_system,
        )

    def tearDown(self):
        """Clean up test environment"""

        # Clean up temporary directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Shutdown processor
        self.processor.shutdown()

    def test_initialization(self):
        """Test ImageProcessor initialization"""

        # Check that processor is properly initialized
        self.assertIsNotNone(self.processor)
        self.assertIsInstance(self.processor.supported_formats, list)
        self.assertGreater(len(self.processor.supported_formats), 0)

        # Check that common image formats are supported
        self.assertIn(".jpg", self.processor.supported_formats)
        self.assertIn(".png", self.processor.supported_formats)
        self.assertIn(".tiff", self.processor.supported_formats)

    def test_get_supported_formats(self):
        """Test getting supported image formats"""

        formats = self.processor.get_supported_formats()

        self.assertIsInstance(formats, list)
        self.assertGreater(len(formats), 0)

        # Check that formats start with dot
        for fmt in formats:
            self.assertTrue(fmt.startswith("."))
            self.assertEqual(fmt, fmt.lower())

    def test_validate_image_nonexistent_file(self):
        """Test image validation with non-existent file"""

        non_existent_path = self.test_dir / "nonexistent.jpg"

        result = self.processor.validate_image(non_existent_path)

        self.assertFalse(result)

    def test_validate_image_unsupported_format(self):
        """Test image validation with unsupported format"""

        # Create a text file with unsupported extension
        text_file = self.test_dir / "test.txt"
        text_file.write_text("This is not an image")

        result = self.processor.validate_image(text_file)

        self.assertFalse(result)

    def test_validate_coordinates(self):
        """Test GPS coordinate validation"""

        # Valid coordinates
        self.assertTrue(self.processor.validate_coordinates(40.7128, -74.0060))  # New York
        self.assertTrue(self.processor.validate_coordinates(0, 0))  # Equator/Prime Meridian
        self.assertTrue(self.processor.validate_coordinates(90, 180))  # Extremes
        self.assertTrue(self.processor.validate_coordinates(-90, -180))  # Extremes

        # Invalid coordinates
        self.assertFalse(self.processor.validate_coordinates(91, 0))  # Latitude too high
        self.assertFalse(self.processor.validate_coordinates(-91, 0))  # Latitude too low
        self.assertFalse(self.processor.validate_coordinates(0, 181))  # Longitude too high
        self.assertFalse(self.processor.validate_coordinates(0, -181))  # Longitude too low

    def test_format_coordinates(self):
        """Test GPS coordinate formatting"""

        # Test positive coordinates
        result = self.processor._format_coordinates(40.7128, -74.0060)
        self.assertIn("N", result)
        self.assertIn("W", result)
        self.assertIn("40.712800", result)
        self.assertIn("74.006000", result)

        # Test negative coordinates
        result = self.processor._format_coordinates(-33.8688, 151.2093)
        self.assertIn("S", result)
        self.assertIn("E", result)

    def test_format_file_size(self):
        """Test file size formatting"""

        # Test various file sizes
        self.assertEqual(self.processor._format_file_size(0), "0 B")
        self.assertEqual(self.processor._format_file_size(512), "512.0 B")
        self.assertEqual(self.processor._format_file_size(1024), "1.0 KB")
        self.assertEqual(self.processor._format_file_size(1048576), "1.0 MB")
        self.assertEqual(self.processor._format_file_size(1073741824), "1.0 GB")

    def test_parse_rational(self):
        """Test rational number parsing"""

        # Test fraction parsing
        self.assertEqual(self.processor._parse_rational("1/2"), 0.5)
        self.assertEqual(self.processor._parse_rational("3/4"), 0.75)
        self.assertEqual(self.processor._parse_rational("10/5"), 2.0)

        # Test whole number parsing
        self.assertEqual(self.processor._parse_rational("42"), 42.0)
        self.assertEqual(self.processor._parse_rational("0"), 0.0)

        # Test invalid input
        self.assertIsNone(self.processor._parse_rational("invalid"))
        self.assertIsNone(self.processor._parse_rational("1/0"))  # Division by zero

    def test_convert_gps_to_decimal(self):
        """Test GPS coordinate conversion"""

        # Test DMS format conversion
        # Mock GPS coordinate in DMS format: [40, 42, 46.08]
        gps_coord = "[40, 42, 46.08]"
        gps_ref = "N"

        result = self.processor._convert_gps_to_decimal(gps_coord, gps_ref)

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 40.7128, places=4)

        # Test with South reference (should be negative)
        result_south = self.processor._convert_gps_to_decimal(gps_coord, "S")
        self.assertAlmostEqual(result_south, -40.7128, places=4)

        # Test with West reference (should be negative)
        result_west = self.processor._convert_gps_to_decimal(gps_coord, "W")
        self.assertAlmostEqual(result_west, -40.7128, places=4)

    @patch("integration.image_processor.PIL_AVAILABLE", True)
    @patch("integration.image_processor.Image")
    def test_load_with_pil(self, mock_image):
        """Test image loading with PIL"""

        # Create a test image file
        test_image_path = self.test_dir / "test.jpg"
        test_image_path.write_bytes(b"fake image data")

        # Mock PIL Image
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img

        # Mock ImageOps.exif_transpose
        with patch("integration.image_processor.ImageOps") as mock_imageops:
            mock_imageops.exif_transpose.return_value = mock_img

            result = self.processor._load_with_pil(test_image_path)

            self.assertEqual(result, mock_img)
            mock_image.open.assert_called_once_with(test_image_path)
            mock_imageops.exif_transpose.assert_called_once_with(mock_img)

    def test_get_file_info(self):
        """Test getting basic file information"""

        # Create a test file
        test_file = self.test_dir / "test.jpg"
        test_content = b"fake image data"
        test_file.write_bytes(test_content)

        result = self.processor._get_file_info(test_file)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["File Name"], "test.jpg")
        self.assertEqual(result["Extension"], ".jpg")
        self.assertEqual(result["Size Bytes"], len(test_content))
        self.assertIn("Modified", result)
        self.assertIn("Full Path", result)

    def test_cache_functionality(self):
        """Test caching system"""

        # Check initial cache state
        stats = self.processor.get_performance_stats()
        self.assertEqual(stats["image_cache_size"], 0)
        self.assertEqual(stats["metadata_cache_size"], 0)
        self.assertEqual(stats["cache_hits"], 0)
        self.assertEqual(stats["cache_misses"], 0)

        # Test cache clearing
        self.processor.clear_cache()

        stats_after_clear = self.processor.get_performance_stats()
        self.assertEqual(stats_after_clear["cache_hits"], 0)
        self.assertEqual(stats_after_clear["cache_misses"], 0)

    def test_performance_stats(self):
        """Test performance statistics"""

        stats = self.processor.get_performance_stats()

        # Check that all expected keys are present
        expected_keys = [
            "image_cache_size",
            "metadata_cache_size",
            "cache_hits",
            "cache_misses",
            "cache_hit_rate",
            "average_processing_time",
            "recent_processing_times",
            "supported_formats_count",
            "libraries_available",
        ]

        for key in expected_keys:
            self.assertIn(key, stats)

        # Check library availability info
        self.assertIsInstance(stats["libraries_available"], dict)
        self.assertIn("exifread", stats["libraries_available"])
        self.assertIn("pil", stats["libraries_available"])
        self.assertIn("cv2", stats["libraries_available"])

    def test_create_image_metadata(self):
        """Test ImageMetadata creation"""

        # Create a test file
        test_file = self.test_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")

        # Mock EXIF data
        exif_data = {
            "Camera Make": "Canon",
            "Camera Model": "EOS 5D Mark IV",
            "F-Number": "f/2.8",
            "ISO Speed": "400",
            "Focal Length": "85mm",
            "Image Width": "6720",
            "Image Height": "4480",
            "gps_coordinates": (40.7128, -74.0060),
        }

        metadata = self.processor._create_image_metadata(test_file, exif_data)

        self.assertIsInstance(metadata, ImageMetadata)
        self.assertEqual(metadata.file_path, test_file)
        self.assertEqual(metadata.camera_make, "Canon")
        self.assertEqual(metadata.camera_model, "EOS 5D Mark IV")
        self.assertEqual(metadata.aperture, 2.8)
        self.assertEqual(metadata.iso, 400)
        self.assertEqual(metadata.focal_length, 85.0)
        self.assertEqual(metadata.width, 6720)
        self.assertEqual(metadata.height, 4480)
        self.assertEqual(metadata.latitude, 40.7128)
        self.assertEqual(metadata.longitude, -74.0060)
        self.assertTrue(metadata.has_gps)
        self.assertEqual(metadata.ai_processor, AIComponent.COPILOT)
        self.assertEqual(metadata.processing_status, ProcessingStatus.COMPLETED)

    def test_metadata_to_dict(self):
        """Test converting ImageMetadata to dictionary"""

        # Create test metadata
        test_file = self.test_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")

        metadata = ImageMetadata(
            file_path=test_file,
            file_size=1024,
            created_date=datetime.now(),
            modified_date=datetime.now(),
            file_format=".jpg",
            camera_make="Canon",
            camera_model="EOS 5D",
            aperture=2.8,
            iso=400,
            latitude=40.7128,
            longitude=-74.0060,
            processing_status=ProcessingStatus.COMPLETED,
            ai_processor=AIComponent.COPILOT,
        )

        result = self.processor._metadata_to_dict(metadata)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["File Name"], "test.jpg")
        self.assertEqual(result["Camera Make"], "Canon")
        self.assertEqual(result["Camera Model"], "EOS 5D")
        self.assertEqual(result["F-Number"], "f/2.8")
        self.assertEqual(result["ISO Speed"], "400")
        self.assertIn("GPS Latitude", result)
        self.assertIn("GPS Longitude", result)
        self.assertIn("GPS Coordinates", result)
        self.assertIn("gps_coordinates", result)

    @patch("integration.image_processor.EXIFREAD_AVAILABLE", False)
    @patch("integration.image_processor.PIL_AVAILABLE", False)
    def test_extract_exif_no_libraries(self):
        """Test EXIF extraction when no libraries are available"""

        # Create a test file
        test_file = self.test_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")

        result = self.processor.extract_exif(test_file)

        # Should still return basic file info
        self.assertIsInstance(result, dict)
        self.assertIn("File Name", result)
        self.assertIn("File Size", result)

    def test_shutdown(self):
        """Test processor shutdown"""

        # Add some data to caches
        self.processor.image_cache["test"] = "data"
        self.processor.metadata_cache["test"] = "metadata"

        # Shutdown processor
        self.processor.shutdown()

        # Check that caches are cleared
        self.assertEqual(len(self.processor.image_cache), 0)
        self.assertEqual(len(self.processor.metadata_cache), 0)


class TestImageProcessorIntegration(unittest.TestCase):
    """Integration tests for ImageProcessor with other components"""

    def setUp(self):
        """Set up integration test environment"""

        self.test_dir = Path(tempfile.mkdtemp())

        # Create real instances for integration testing
        self.config_manager = Mock(spec=ConfigManager)
        self.logger_system = LoggerSystem()

        self.processor = CS4CodingImageProcessor(config_manager=self.config_manager, logger_system=self.logger_system)

    def tearDown(self):
        """Clean up integration test environment"""

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.processor.shutdown()
        self.logger_system.shutdown()

    def test_logging_integration(self):
        """Test integration with logging system"""

        # Create a test file
        test_file = self.test_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")

        # Perform operations that should generate logs
        self.processor.validate_image(test_file)
        self.processor.extract_exif(test_file)

        # Check that logging system was called
        # (In a real test, you might check log files or mock the logger)
        self.assertTrue(True)  # Placeholder assertion

    def test_error_handling_integration(self):
        """Test integration with error handling system"""

        # Try to process a non-existent file
        non_existent = self.test_dir / "nonexistent.jpg"

        result = self.processor.load_image(non_existent)

        # Should handle error gracefully
        self.assertIsNone(result)

    def test_performance_monitoring(self):
        """Test performance monitoring integration"""

        # Create a test file
        test_file = self.test_dir / "test.jpg"
        test_file.write_bytes(b"fake image data")

        # Perform operations
        self.processor.extract_exif(test_file)

        # Check performance stats
        stats = self.processor.get_performance_stats()

        self.assertIsInstance(stats, dict)
        self.assertIn("average_processing_time", stats)


if __name__ == "__main__":
    # Create test directory if it doesn't exist
    test_dir = Path(__file__).parent
    test_dir.mkdir(exist_ok=True)

    # Run tests
    unittest.main(verbosity=2)
