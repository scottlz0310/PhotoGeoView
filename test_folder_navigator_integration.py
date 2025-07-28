#!/usr/bin/env python3
"""
Test script for FolderNavigator integration with FileDiscoveryService

This script tests the newly implemented integration functionality in task 3.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integration.services.file_discovery_service import FileDiscoveryService
from integration.logging_system import LoggerSystem
from integration.models import AIComponent

def test_file_discovery_integration():
    """Test the file discovery service integration functionality"""

    print("=== FileDiscoveryService 連携機能テスト ===\n")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create some test image files
        test_images = [
            temp_path / "test1.jpg",
            temp_path / "test2.png",
            temp_path / "test3.gif",
            temp_path / "invalid.txt"  # Non-image file
        ]

        for img_path in test_images:
            img_path.write_text("test content")

        print(f"テスト用フォルダ作成: {temp_path}")
        print(f"テスト用ファイル: {[f.name for f in test_images]}\n")

        # Initialize components
        logger_system = LoggerSystem(
            log_dir=Path("logs"),
            log_level="DEBUG",
            enable_performance_logging=True,
            enable_ai_operation_logging=True
        )

        # Initialize FileDiscoveryService
        print("1. FileDiscoveryService を初期化中...")
        service = FileDiscoveryService(logger_system=logger_system)

        print("✓ FileDiscoveryService 初期化完了\n")

        # Test file discovery functionality
        print("2. ファイル検出機能をテスト中...")
        discovered_images = service.discover_images(temp_path)

        print(f"✓ 検出された画像ファイル数: {len(discovered_images)}")
        for img in discovered_images:
            print(f"  - {img.name}")
        print()

        # Test error handling with non-existent folder
        print("3. エラーハンドリング機能をテスト中...")
        non_existent_folder = temp_path / "non_existent"
        error_images = service.discover_images(non_existent_folder)

        print(f"✓ 存在しないフォルダでのエラーハンドリング完了")
        print(f"  検出されたファイル数: {len(error_images)} (期待値: 0)")
        print()

        # Test empty folder handling
        print("4. 空フォルダ処理をテスト中...")
        empty_folder = temp_path / "empty"
        empty_folder.mkdir()

        empty_images = service.discover_images(empty_folder)
        print(f"✓ 空フォルダ処理完了")
        print(f"  検出されたファイル数: {len(empty_images)} (期待値: 0)")
        print()

        # Test file validation
        print("5. ファイル検証機能をテスト中...")
        for test_file in test_images:
            if test_file.suffix.lower() in service.get_supported_extensions():
                is_valid = service.validate_image_file(test_file)
                print(f"  {test_file.name}: {'有効' if is_valid else '無効'}")
        print()

        # Test statistics
        print("6. 統計情報をテスト中...")
        stats = service.get_discovery_stats()

        print("✓ 統計情報取得完了:")
        print(f"  総スキャン数: {stats['total_scans']}")
        print(f"  発見ファイル数: {stats['total_files_found']}")
        print(f"  有効ファイル数: {stats['total_valid_files']}")
        print(f"  平均スキャン時間: {stats['avg_scan_time']:.3f}秒")
        print()

        print("=== テスト完了 ===")
        print("FileDiscoveryService の連携機能が正常に動作しています。")
        print(f"詳細なログは logs/ フォルダを確認してください。")

if __name__ == "__main__":
    test_file_discovery_integration()
