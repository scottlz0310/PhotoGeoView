#!/usr/bin/env python3
"""
詳細EXIF診断テストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path

def test_exif_libraries():
    """EXIF読み取りライブラリの動作確認"""

    # testsディレクトリから見た相対パス
    test_image = Path(__file__).parent.parent / "test_images" / "test_image.jpg"

    if not test_image.exists():
        print(f"Test image not found: {test_image}")
        return

    print(f"Testing EXIF libraries with: {test_image}")
    print("=" * 50)

    # 1. exifreadライブラリテスト
    try:
        import exifread
        print("✓ exifread library is available")

        with open(test_image, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        if tags:
            print(f"✓ exifread found {len(tags)} tags:")
            for tag_key, tag_value in list(tags.items())[:10]:  # 最初の10個のタグを表示
                print(f"  {tag_key}: {tag_value}")
            if len(tags) > 10:
                print(f"  ... and {len(tags) - 10} more tags")
        else:
            print("✗ No EXIF tags found with exifread")

    except ImportError:
        print("✗ exifread library not available")
    except Exception as e:
        print(f"✗ exifread error: {e}")

    print()

    # 2. PILライブラリテスト
    try:
        from PIL import Image
        print("✓ PIL library is available")

        with Image.open(test_image) as img:
            if hasattr(img, '_getexif'):
                exif_dict = img._getexif()
                if exif_dict:
                    print(f"✓ PIL found {len(exif_dict)} EXIF entries:")
                    from PIL.ExifTags import TAGS
                    count = 0
                    for tag_id, value in exif_dict.items():
                        if count >= 10:
                            break
                        tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                        print(f"  {tag_name}: {value}")
                        count += 1
                    if len(exif_dict) > 10:
                        print(f"  ... and {len(exif_dict) - 10} more entries")
                else:
                    print("✗ No EXIF data found with PIL")
            else:
                print("✗ PIL _getexif method not available")

    except ImportError:
        print("✗ PIL library not available")
    except Exception as e:
        print(f"✗ PIL error: {e}")

    print()

    # 3. ファイル情報確認
    try:
        import os
        stat = os.stat(test_image)
        print(f"File info:")
        print(f"  Size: {stat.st_size} bytes")
        print(f"  Modified: {stat.st_mtime}")

        # ファイルヘッダー確認
        with open(test_image, 'rb') as f:
            header = f.read(10)
            print(f"  Header: {header.hex()}")
            if header.startswith(b'\xff\xd8'):
                print("  ✓ Valid JPEG file format")
            else:
                print("  ✗ Not a valid JPEG file")

    except Exception as e:
        print(f"File info error: {e}")

if __name__ == "__main__":
    test_exif_libraries()
