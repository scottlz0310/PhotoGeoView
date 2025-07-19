#!/usr/bin/env python3
"""
GPS座標抽出のテストスクリプト
ExifReadライブラリを使用してGPS座標を正常に抽出できるかテスト
"""

import exifread
import os
from typing import Optional, Dict, Any

def convert_gps_to_decimal(gps_coord: Any, gps_ref: Any) -> Optional[float]:
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
                degrees = parse_rational(coord_parts[0])
                minutes = parse_rational(coord_parts[1])
                seconds = parse_rational(coord_parts[2])

                if degrees is not None and minutes is not None and seconds is not None:
                    decimal = degrees + minutes / 60 + seconds / 3600

                    # Apply hemisphere correction
                    if ref_str in ['S', 'W']:
                        decimal = -decimal

                    return decimal

    except Exception as e:
        print(f"Error converting GPS coordinate to decimal: {e}")

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
        print(f"Processing: {file_path}")

        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        print(f"Found {len(tags)} EXIF tags")

        # Show GPS related tags
        gps_tags = {k: v for k, v in tags.items() if k.startswith('GPS')}
        print(f"GPS tags found: {len(gps_tags)}")

        for tag_name, tag_value in gps_tags.items():
            print(f"  {tag_name}: {tag_value}")

        # Check if GPS data exists
        gps_latitude = tags.get('GPS GPSLatitude')
        gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
        gps_longitude = tags.get('GPS GPSLongitude')
        gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            print("GPS data found! Converting to decimal...")

            # Convert GPS coordinates to decimal format
            lat_decimal = convert_gps_to_decimal(gps_latitude, gps_latitude_ref)
            lon_decimal = convert_gps_to_decimal(gps_longitude, gps_longitude_ref)

            if lat_decimal is not None and lon_decimal is not None:
                print(f"GPS Coordinates: {lat_decimal:.8f}, {lon_decimal:.8f}")
                return (lat_decimal, lon_decimal)
            else:
                print("Failed to convert GPS coordinates to decimal")
        else:
            print("No GPS coordinates found in this image")

    except Exception as e:
        print(f"Error processing file: {e}")
        return None

    return None

def main():
    """テストメイン関数"""
    print("GPS座標抽出テスト開始\n")

    # テスト用の画像ファイルパスを指定
    # ユーザーがGPS付き画像を持っている場合のテスト
    test_image_paths = [
        # 一般的なGPS付き画像の場所
        "/home/hiro/Pictures",
        "/home/hiro/Downloads",
        "/home/hiro/Desktop"
    ]

    found_images = []

    # GPS付き画像を探す
    for search_dir in test_image_paths:
        if os.path.exists(search_dir):
            print(f"Searching in: {search_dir}")
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.tiff', '.tif')):
                        full_path = os.path.join(root, file)
                        found_images.append(full_path)
                        if len(found_images) >= 5:  # 最大5つまでテスト
                            break
                if len(found_images) >= 5:
                    break
        if len(found_images) >= 5:
            break

    if found_images:
        print(f"Found {len(found_images)} image files to test\n")

        gps_found_count = 0
        for image_path in found_images:
            print(f"\n{'='*50}")
            result = extract_gps_from_file(image_path)
            if result:
                gps_found_count += 1
                print("✓ GPS座標が正常に抽出されました！")
            else:
                print("- GPS座標なし")

        print(f"\n{'='*50}")
        print(f"テスト完了: {gps_found_count}/{len(found_images)} 個の画像からGPS座標を抽出")
    else:
        print("テスト用の画像ファイルが見つかりませんでした")
        print("GPS付きの.jpg/.jpeg画像を以下のディレクトリに置いてください:")
        for path in test_image_paths:
            print(f"  - {path}")

if __name__ == "__main__":
    main()
