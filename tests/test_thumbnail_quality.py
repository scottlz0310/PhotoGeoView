#!/usr/bin/env python3
"""
サムネイル品質テストスクリプト
改良されたサムネイル生成機能をテストします
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from src.modules.thumbnail_generator import ThumbnailGenerator
from src.core.logger import setup_logging, get_logger


def test_thumbnail_quality():
    """サムネイル品質テスト"""
    # ログ設定
    setup_logging()
    logger = get_logger(__name__)

    app = QApplication(sys.argv)

    # テスト用画像パス
    test_image_dir = Path(__file__).parent / "test_data" / "images" / "with_gps"
    test_images = [
        test_image_dir / "england-london-bridge.jpg",
        test_image_dir / "irland-dingle.jpg",
        test_image_dir / "taiwan-jiufen.jpg",
        test_image_dir / "PIC001.jpg"
    ]

    # サムネイル生成器を初期化
    thumbnail_gen = ThumbnailGenerator()

    print("=== サムネイル品質テスト開始 ===")
    print(f"テストサイズ: 128x128, 256x256")

    for image_path in test_images:
        if not image_path.exists():
            print(f"⚠️ テスト画像が見つかりません: {image_path}")
            continue

        print(f"\n📁 テスト中: {image_path.name}")

        # オリジナル画像のサイズ確認
        original_pixmap = QPixmap(str(image_path))
        if original_pixmap.isNull():
            print(f"❌ 画像読み込み失敗: {image_path.name}")
            continue

        print(f"   オリジナルサイズ: {original_pixmap.width()}x{original_pixmap.height()}")

        # 複数のサイズでサムネイル生成テスト
        for size in [(128, 128), (256, 256)]:
            thumbnail = thumbnail_gen.generate_thumbnail(str(image_path), size)

            if thumbnail and not thumbnail.isNull():
                print(f"   ✅ サムネイル生成成功 ({size[0]}x{size[1]}): {thumbnail.width()}x{thumbnail.height()}")
            else:
                print(f"   ❌ サムネイル生成失敗 ({size[0]}x{size[1]})")

    print("\n=== サムネイル品質テスト完了 ===")
    print("💡 アプリケーションでは高品質QPainter方式のサムネイル生成が使用されます")
    print("💡 キャッシュ保存はデバッグ中は無効化されています（読み込みは有効）")


if __name__ == '__main__':
    test_thumbnail_quality()
