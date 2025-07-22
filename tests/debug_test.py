#!/usr/bin/env python3
"""
デバッグ用テストスクリプト
"""

import sys
import os
sys.path.append('/home/hiro/Projects/PhotoGeoView')

from src.modules.image_loader import ImageLoader
from src.core.utils import is_image_file

def main():
    # テスト用ファイルを作成
    test_file = "/tmp/test_image.jpg"
    with open(test_file, "w") as f:
        f.write("test content")

    print(f"テストファイル: {test_file}")
    print(f"is_image_file結果: {is_image_file(test_file)}")

    # ImageLoaderでテスト
    loader = ImageLoader()
    try:
        result = loader.get_image_info(test_file)
        print(f"get_image_info結果: {result}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
