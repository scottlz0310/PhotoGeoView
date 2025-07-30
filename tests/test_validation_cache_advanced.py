"""
バリデーション結果キャッシュの高度なテスト

無効ファイルのキャッシュと重複チェック回避のテスト

Author: Kiro AI Integration System
"""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from integration.logging_system import LoggerSystem
from integration.services.file_discovery_cache import FileDiscoveryCache


class TestValidationCacheAdvanced(unittest.TestCase):
    """バリデーション結果キャッシュの高度なテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.logger_system = LoggerSystem()
        self.cache = FileDiscoveryCache(
            max_file_entries=50,
            max_folder_entries=10,
            max_memory_mb=5.0,
            logger_system=self.logger_system,
        )

        # テスト用の一時ディレクトリとファイルを作成
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # 有効なファイル（大きなサイズ）
        self.valid_file = self.temp_path / "valid_image.jpg"
        self.valid_file.write_bytes(b"valid_image_data" * 100)  # 1600バイト

        # 無効なファイル（小さなサイズ）
        self.invalid_file = self.temp_path / "invalid_image.jpg"
        self.invalid_file.write_bytes(b"bad")  # 3バイト

        # 破損ファイル（空）
        self.corrupted_file = self.temp_path / "corrupted_image.jpg"
        self.corrupted_file.write_bytes(b"")  # 0バイト

    def tearDown(self):
        """テストクリーンアップ"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_invalid_file_caching(self):
        """無効ファイルのキャッシュテスト"""
        # 無効ファイルの結果をキャッシュ
        success = self.cache.cache_validation_result(self.invalid_file, False)
        self.assertTrue(success)

        # キャッシュから取得
        cached_result = self.cache.get_cached_validation_result(self.invalid_file)
        self.assertIsNotNone(cached_result)
        self.assertFalse(cached_result)  # 無効であることを確認

    def test_mixed_validation_results_caching(self):
        """有効・無効混在のバリデーション結果キャッシュテスト"""
        # 有効ファイルをキャッシュ
        self.cache.cache_validation_result(self.valid_file, True)

        # 無効ファイルをキャッシュ
        self.cache.cache_validation_result(self.invalid_file, False)

        # 破損ファイルをキャッシュ
        self.cache.cache_validation_result(self.corrupted_file, False)

        # 全ての結果を確認
        valid_result = self.cache.get_cached_validation_result(self.valid_file)
        invalid_result = self.cache.get_cached_validation_result(self.invalid_file)
        corrupted_result = self.cache.get_cached_validation_result(self.corrupted_file)

        self.assertTrue(valid_result)
        self.assertFalse(invalid_result)
        self.assertFalse(corrupted_result)

    def test_duplicate_check_avoidance(self):
        """重複チェック回避のテスト"""
        # 初期状態の統計を取得
        initial_stats = self.cache.get_cache_stats()
        initial_misses = initial_stats["validation_cache"]["misses"]

        # 最初のアクセス（キャッシュミス）
        result1 = self.cache.get_cached_validation_result(self.invalid_file)
        self.assertIsNone(result1)

        # ミス数が増加していることを確認
        stats_after_miss = self.cache.get_cache_stats()
        self.assertEqual(
            stats_after_miss["validation_cache"]["misses"], initial_misses + 1
        )

        # 結果をキャッシュ
        self.cache.cache_validation_result(self.invalid_file, False)

        # 2回目のアクセス（キャッシュヒット）
        result2 = self.cache.get_cached_validation_result(self.invalid_file)
        self.assertFalse(result2)

        # 3回目のアクセス（キャッシュヒット）
        result3 = self.cache.get_cached_validation_result(self.invalid_file)
        self.assertFalse(result3)

        # ヒット数が増加していることを確認
        final_stats = self.cache.get_cache_stats()
        self.assertGreaterEqual(final_stats["validation_cache"]["hits"], 2)

        # ミス数は変わらないことを確認（重複チェック回避）
        self.assertEqual(final_stats["validation_cache"]["misses"], initial_misses + 1)

    def test_file_size_mtime_cache_key(self):
        """ファイルサイズ+mtime基準のキャッシュキーテスト"""
        # ファイルの初期状態をキャッシュ
        self.cache.cache_validation_result(self.valid_file, True)

        # キャッシュヒットを確認
        result1 = self.cache.get_cached_validation_result(self.valid_file)
        self.assertTrue(result1)

        # ファイルを変更（サイズとmtimeが変わる）
        time.sleep(0.1)  # mtimeが確実に変わるように待機
        self.valid_file.write_bytes(b"modified_valid_image_data" * 200)  # サイズ変更

        # キャッシュミスになることを確認（新しいキー）
        result2 = self.cache.get_cached_validation_result(self.valid_file)
        self.assertIsNone(result2)

        # 新しい状態をキャッシュ
        self.cache.cache_validation_result(self.valid_file, False)  # 今度は無効として

        # 新しい結果を確認
        result3 = self.cache.get_cached_validation_result(self.valid_file)
        self.assertFalse(result3)

    def test_cache_size_limit_and_eviction(self):
        """キャッシュサイズ制限と自動削除のテスト"""
        # 大量のファイルを作成してキャッシュ
        test_files = []
        for i in range(100):  # キャッシュ制限を超える数
            test_file = self.temp_path / f"test_file_{i}.jpg"
            test_file.write_bytes(f"test_data_{i}".encode() * 10)
            test_files.append(test_file)

            # バリデーション結果をキャッシュ
            self.cache.cache_validation_result(
                test_file, i % 2 == 0
            )  # 偶数は有効、奇数は無効

        # 統計を確認
        stats = self.cache.get_cache_stats()

        # エントリ数がmax_file_entries * 2（バリデーションキャッシュの制限）を超えていないことを確認
        max_validation_entries = self.cache.max_file_entries * 2
        self.assertLessEqual(
            stats["validation_cache"]["entries"], max_validation_entries
        )

        # 削除が発生していることを確認
        self.assertGreater(stats["validation_cache"]["evictions"], 0)

    def test_cache_performance_with_invalid_files(self):
        """無効ファイルでのキャッシュパフォーマンステスト"""
        # 多数の無効ファイルを作成
        invalid_files = []
        for i in range(20):
            invalid_file = self.temp_path / f"invalid_{i}.jpg"
            invalid_file.write_bytes(b"x")  # 1バイトの無効ファイル
            invalid_files.append(invalid_file)

        # 最初のラウンド：全てキャッシュミス
        start_time = time.time()
        for invalid_file in invalid_files:
            result = self.cache.get_cached_validation_result(invalid_file)
            self.assertIsNone(result)  # キャッシュミス
            # 無効として結果をキャッシュ
            self.cache.cache_validation_result(invalid_file, False)
        first_round_time = time.time() - start_time

        # 2回目のラウンド：全てキャッシュヒット
        start_time = time.time()
        for invalid_file in invalid_files:
            result = self.cache.get_cached_validation_result(invalid_file)
            self.assertFalse(result)  # キャッシュヒット、無効ファイル
        second_round_time = time.time() - start_time

        # 2回目の方が高速であることを確認（キャッシュ効果）
        # 注意: 実際の環境では必ずしも成立しないため、統計での確認に変更
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats["validation_cache"]["hits"], 20)  # 20回のヒット
        self.assertEqual(stats["validation_cache"]["misses"], 20)  # 20回のミス

    def test_cache_memory_usage_tracking(self):
        """キャッシュメモリ使用量追跡のテスト"""
        # 初期メモリ使用量
        initial_stats = self.cache.get_cache_stats()
        initial_memory = initial_stats["total_memory_mb"]

        # 多数のバリデーション結果をキャッシュ
        for i in range(50):
            test_file = self.temp_path / f"memory_test_{i}.jpg"
            test_file.write_bytes(f"memory_test_data_{i}".encode() * 20)
            self.cache.cache_validation_result(test_file, i % 3 == 0)

        # メモリ使用量が増加していることを確認
        final_stats = self.cache.get_cache_stats()
        final_memory = final_stats["total_memory_mb"]

        self.assertGreater(final_memory, initial_memory)
        self.assertGreater(final_stats["validation_cache"]["memory_usage_mb"], 0)


if __name__ == "__main__":
    unittest.main()
