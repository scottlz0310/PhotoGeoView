#!/usr/bin/env python3
"""
EXIF読み取りテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.utils.exif_processor import ExifProcessor
from pathlib import Path

def test_exif_reading():
    """EXIF読み取りのテスト"""

    test_image = "test_images/test_image.jpg"

    if not Path(test_image).exists():
        print(f"Test image not found: {test_image}")
        return

    print(f"Testing EXIF reading for: {test_image}")

    processor = ExifProcessor()
    exif_data = processor.extract_exif_data(test_image)

    if exif_data:
        print(f"Successfully extracted {len(exif_data)} EXIF fields:")
        for key, value in exif_data.items():
            print(f"  {key}: {value}")
    else:
        print("No EXIF data found")

if __name__ == "__main__":
    test_exif_reading()
