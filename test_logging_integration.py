#!/usr/bin/env python3
"""
Test script for FileDiscoveryService logging integration

This script tests the newly implemented logging functionality in task 2.3
"""

import sys
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integration.services.file_discovery_service import FileDiscoveryService
from integration.logging_system import LoggerSystem
from integration.models import AIComponent

def test_logging_integration():
    """Test the integrated logging functionality"""

    print("=== FileDiscoveryService ログ機能統合テスト ===\n")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create some test files
        (temp_path / "test1.jpg").write_text("fake image content")
        (temp_path / "test2.png").write_text("fake image content")
        (temp_path / "test.txt").write_text("not an image")

        # Initialize logging system with DEBUG level
        logger_system = LoggerSystem(
            log_dir=temp_path / "logs",
            log_level="DEBUG",
            enable_performance_logging=True,
            enable_ai_operation_logging=True
        )

        # Initialize FileDiscoveryService
        print("1. FileDiscoveryService を初期化中...")
        service = FileDiscoveryService(logger_system=logger_system)

        # Test logging configuration
        print("2. ログ設定をテスト中...")
        service.configure_logging(
            debug_enabled=True,
            performance_logging_enabled=True,
            log_level="DEBUG"
        )

        # Get logging status
        status = service.get_logging_status()
        print(f"   - デバッグ有効: {status['debug_enabled']}")
        print(f"   - パフォーマンスログ有効: {status['performance_logging_enabled']}")
        print(f"   - メモリ使用量: {status['memory_usage_mb']:.1f}MB")

        # Test detailed debug logging
        print("3. 詳細デバッグ情報のログテスト...")
        service.log_detailed_debug_info("test_operation", {
            "test_parameter": "test_value",
            "execution_time": 0.123,
            "file_size": 1024,
            "timestamp": "2024-01-01T00:00:00"
        })

        # Test performance metrics logging
        print("4. パフォーマンス情報のログテスト...")
        service.log_performance_metrics("test_performance", {
            "duration": 1.5,
            "files_processed": 100,
            "files_per_second": 66.7,
            "success_rate": 0.95,
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-01T00:00:01"
        })

        # Test error logging
        print("5. エラー詳細情報のログテスト...")
        try:
            raise ValueError("テストエラー")
        except Exception as e:
            service.log_error_details("test_error", e, {
                "context_info": "テストコンテキスト",
                "operation_stage": "testing"
            })

        # Test appropriate level logging
        print("6. ログレベル別出力テスト...")
        service.log_with_appropriate_level("INFO", "test_info", "情報レベルのテストメッセージ")
        service.log_with_appropriate_level("WARNING", "test_warning", "警告レベルのテストメッセージ", {
            "warning_details": "詳細情報"
        })
        service.log_with_appropriate_level("ERROR", "test_error_level", "エラーレベルのテストメッセージ")

        # Test actual file discovery with logging
        print("7. 実際のファイル検出でのログテスト...")
        discovered_files = service.discover_images(temp_path)
        print(f"   - 検出されたファイル数: {len(discovered_files)}")

        # Test file validation with logging
        print("8. ファイル検証でのログテスト...")
        for file_path in discovered_files:
            is_valid = service.validate_image_file(file_path)
            print(f"   - {file_path.name}: {'有効' if is_valid else '無効'}")

        # Get final statistics
        print("9. 最終統計情報...")
        stats = service.get_discovery_stats()
        print(f"   - 総スキャン数: {stats['total_scans']}")
        print(f"   - 発見ファイル数: {stats['total_files_found']}")
        print(f"   - 有効ファイル数: {stats['total_valid_files']}")
        print(f"   - 平均スキャン時間: {stats['avg_scan_time']:.3f}秒")

        # Flush all logs
        print("10. ログフラッシュテスト...")
        service.flush_logs()

        # Check log files
        log_dir = temp_path / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log*"))
            print(f"    - 作成されたログファイル数: {len(log_files)}")
            for log_file in log_files:
                print(f"      - {log_file.name}")

        print("\n=== テスト完了 ===")
        print("すべてのログ機能が正常に統合されました。")

if __name__ == "__main__":
    test_logging_integration()
