#!/usr/bin/env python3
"""
GPS座標抽出のテストスクリプト
ExifReadライブラリを使用してGPS座標を正常に抽出できるかテスト
仕様に準拠してtests/ディレクトリに配置、Logger使用
"""

import sys
import os
import logging
from pathlib import Path
import exifread
from typing import Optional, Any

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Logger設定（仕様準拠）
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# コンソールハンドラー設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def convert_gps_to_decimal(gps_coord: Any, gps_ref: Any) -> Optional[float]:
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
                degrees = parse_rational(coord_parts[0])
                minutes = parse_rational(coord_parts[1])
                seconds = parse_rational(coord_parts[2])

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

def parse_rational(rational_str: str) -> Optional[float]:
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

def extract_gps_from_file(file_path: str) -> Optional[tuple[float, float]]:
    """Extract GPS coordinates from image file using ExifRead"""
    try:
        logger.info(f"Processing: {file_path}")

        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        logger.info(f"Found {len(tags)} EXIF tags")

        # Show GPS related tags
        gps_tags = {k: v for k, v in tags.items() if k.startswith('GPS')}
        logger.info(f"GPS tags found: {len(gps_tags)}")

        for tag_name, tag_value in gps_tags.items():
            logger.debug(f"  {tag_name}: {tag_value}")

        # Check if GPS data exists
        gps_latitude = tags.get('GPS GPSLatitude')
        gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
        gps_longitude = tags.get('GPS GPSLongitude')
        gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            logger.info("GPS data found! Converting to decimal...")

            # Convert GPS coordinates to decimal format
            lat_decimal = convert_gps_to_decimal(gps_latitude, gps_latitude_ref)
            lon_decimal = convert_gps_to_decimal(gps_longitude, gps_longitude_ref)

            if lat_decimal is not None and lon_decimal is not None:
                logger.info(f"✓ GPS Coordinates: {lat_decimal:.8f}, {lon_decimal:.8f}")
                return (lat_decimal, lon_decimal)
            else:
                logger.warning("Failed to convert GPS coordinates to decimal")
        else:
            logger.info("No GPS coordinates found in this image")

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return None

    return None

def main():
    """テストメイン関数"""
    logger.info("GPS座標抽出テスト開始")

    # テスト用の画像ファイルパスを指定
    pictures_dir = os.path.expanduser("~/Pictures")

    if not os.path.exists(pictures_dir):
        logger.error(f"Pictures directory not found: {pictures_dir}")
        return

    logger.info(f"Searching for images in: {pictures_dir}")

    found_images = []

    # GPS付き画像を探す
    for root, _, files in os.walk(pictures_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.tiff', '.tif')):
                full_path = os.path.join(root, file)
                found_images.append(full_path)
                if len(found_images) >= 10:  # 最大10個までテスト
                    break
        if len(found_images) >= 10:
            break

    if found_images:
        logger.info(f"Found {len(found_images)} image files to test")

        gps_found_count = 0
        for image_path in found_images:
            logger.info("="*50)
            result = extract_gps_from_file(image_path)
            if result:
                gps_found_count += 1
                logger.info("✓ GPS座標が正常に抽出されました！")
            else:
                logger.info("- GPS座標なし")

        logger.info("="*50)
        logger.info(f"テスト完了: {gps_found_count}/{len(found_images)} 個の画像からGPS座標を抽出")

        if gps_found_count > 0:
            logger.info("✅ ExifReadによるGPS座標抽出が正常に動作しています")
        else:
            logger.warning("⚠️  GPS付き画像が見つかりませんでした")
    else:
        logger.error("テスト用の画像ファイルが見つかりませんでした")

if __name__ == "__main__":
    main()
