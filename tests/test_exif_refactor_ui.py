#!/usr/bin/env python3
"""
EXIF リファクタリングモジュールのテストスクリプト
"""

import sys
import os
sys.path.append('/home/hiro/Projects/PhotoGeoView')

from src.utils.exif_processor import ExifProcessor
from src.utils.gps_utils import GPSUtils
from src.utils.file_utils import FileUtils

def test_file_utils():
    """ファイルユーティリティのテスト"""
    print("=== File Utils Test ===")

    # Test file size formatting
    test_sizes = [0, 500, 1536, 1048576, 1073741824]
    for size in test_sizes:
        formatted = FileUtils.format_file_size(size)
        print(f"Size {size} bytes -> {formatted}")

    # Test image file detection
    test_files = ["test.jpg", "test.png", "test.txt", "test.JPEG", "test.tiff"]
    for file in test_files:
        is_image = FileUtils.is_image_file(file)
        print(f"File {file} is image: {is_image}")

    print()

def test_gps_utils():
    """GPSユーティリティのテスト"""
    print("=== GPS Utils Test ===")

    # Test coordinate validation
    test_coords = [
        (35.6762, 139.6503),  # Tokyo
        (90.0, 180.0),        # Valid extremes
        (-90.0, -180.0),      # Valid extremes
        (91.0, 0.0),          # Invalid latitude
        (0.0, 181.0)          # Invalid longitude
    ]

    for lat, lon in test_coords:
        is_valid = GPSUtils.validate_coordinates(lat, lon)
        formatted = GPSUtils.format_coordinates(lat, lon) if is_valid else "Invalid"
        print(f"Coordinates ({lat}, {lon}) -> Valid: {is_valid}, Formatted: {formatted}")

    # Test rational parsing
    test_rationals = ["123/456", "42", "0/1", "invalid", "1/0"]
    for rational in test_rationals:
        result = GPSUtils._parse_rational(rational)
        print(f"Rational '{rational}' -> {result}")

    print()

def test_exif_processor():
    """EXIFプロセッサのテスト"""
    print("=== EXIF Processor Test ===")

    # Create a test EXIF processor
    processor = ExifProcessor()

    # Test with sample image files (if they exist)
    test_files = [
        "/home/hiro/Projects/PhotoGeoView/sample_image.jpg",  # Hypothetical
        "/tmp/test.jpg",  # Non-existent
        "/usr/share/pixmaps/python3.11.xpm"  # Might exist
    ]

    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\nTesting with file: {file_path}")
            exif_data = processor.extract_exif_data(file_path)
            print(f"EXIF data keys: {list(exif_data.keys())}")

            # Check for GPS data
            if 'gps_coordinates' in exif_data:
                coords = exif_data['gps_coordinates']
                print(f"GPS coordinates found: {coords}")
            else:
                print("No GPS coordinates found")
        else:
            print(f"File not found: {file_path}")

    print()

def test_integration():
    """統合テスト"""
    print("=== Integration Test ===")

    # Test that all imports work
    try:
        from src.modules.exif_info import ExifInfoPanel, ExifLoader
        print("✓ EXIF module imports successfully")

        # Test creating instances
        processor = ExifProcessor()
        print("✓ ExifProcessor created successfully")

        # Test basic functionality without Qt widgets
        test_data = {
            'File Name': 'test.jpg',
            'File Size': '1.5 MB',
            'Camera Make': 'Canon',
            'ISO Speed': '400',
            'GPS Latitude': '35.6762°N',
            'gps_coordinates': (35.6762, 139.6503)
        }

        # Test data categorization logic (without UI)
        panel = ExifInfoPanel()
        categories = panel.categorize_data(test_data)
        print("✓ Data categorization works")
        print(f"Categories: {list(categories.keys())}")

        for cat, items in categories.items():
            if items:
                print(f"  {cat}: {len(items)} items")

        # Test GPS coordinate extraction
        coords = panel.current_data.get('gps_coordinates') if hasattr(panel, 'current_data') else None
        print(f"GPS coordinates: {coords}")

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

    print()

def main():
    """メインテスト関数"""
    print("EXIF Refactoring Module Test Suite")
    print("=" * 50)

    try:
        test_file_utils()
        test_gps_utils()
        test_exif_processor()
        test_integration()

        print("=" * 50)
        print("✓ All tests completed!")

    except Exception as e:
        print(f"✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
