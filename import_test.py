#!/usr/bin/env python3
"""
モジュールインポートテスト
"""

import sys
sys.path.append('/home/hiro/Projects/PhotoGeoView')

try:
    from src.modules.image_loader import ImageLoader
    print('ImageLoader正常にインポートできました')
except Exception as e:
    print(f'ImageLoaderのインポートエラー: {e}')
    import traceback
    traceback.print_exc()

try:
    from src.modules.thumbnail_generator import ThumbnailGenerator
    print('ThumbnailGenerator正常にインポートできました')
except Exception as e:
    print(f'ThumbnailGeneratorのインポートエラー: {e}')
    import traceback
    traceback.print_exc()

print('テスト完了')
