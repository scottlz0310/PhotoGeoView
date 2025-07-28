"""
FileDiscoveryCache テストスイート

ファイル検出キャッシュ機能のテスト:
- ファイル情報キャッシュ
- バリデーション結果キャッシュ
- フォルダスキャンキャッシュ
- LRU機能
- キャッシュヒット率監視

Author: Kiro AI Integration System
"""

import unittest
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

# テスト用のモックファイルを作成
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from integration.services.file_discovery_cache import (
    FileDiscoveryCache, FileDiscoveryResult, FolderScanCache, CacheMetrics
)
from integration.logging_system import LoggerSystem


class TestFileDiscoveryCache(unittest.TestCase):
    """FileDiscoveryCacheのテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.logger_system = LoggerSystem()
        self.cache = FileDiscoveryCache(
            max_file_entries=10,
            max_folder_entries=5,
            max_memory_mb=1.0,
            logger_system=self.logger_system
        )

        # テスト用の一時ディレクトリとファイルを作成
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # テスト用画像ファイルを作成
        self.test_files = []
        for i in range(5):
            test_file = self.temp_path / f"test_image_{i}.jpg"
            test_file.write_bytes(b"fake_image_data_" + str(i).encode() * 100)
            self.test_files.append(test_file)

    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_result_caching(self):
        """ファイル結果キャッシュのテスト"""
        test_file = self.test_files[0]

        # ファイル結果をキャッシュ
        success = self.cache.cache_file_result(test_file, True, 0.1)
        self.assertTrue(success)

        # キャッシュから取得
        cached_result = self.cache.get_cached_file_result(test_file)
        self.assertIsNotNone(cached_result)
        self.assertTrue(cached_result.is_valid)
        self.assertEqual(cached_result.file_path, test_file)
        self.assertAlmostEqual(cached_result.validation_time, 0.1, places=2)

    def test_validation_result_caching(self):
        """バリデーション結果キャッシュのテスト"""
        test_file = self.test_files[1]

        # バリデーション結果をキャッシュ
        success = self.cache.cache_validation_result(test_file, True)
        self.assertTrue(success)

        # キャッシュから取得
        cached_result = self.cache.get_cached_validation_result(test_file)
        self.assertIsNotNone(cached_result)
        self.assertTrue(cached_result)

        # 無効な結果もテスト
        success = self.cache.cache_validation_result(test_file, False)
        self.assertTrue(success)

        cached_result = self.cache.get_cached_validation_result(test_file)
        self.assertIsNotNone(cached_result)
        self.assertFalse(cached_result)

    def test_folder_scan_caching(self):
        """フォルダスキャンキャッシュのテスト"""
        # ファイル結果リストを作成
        file_results = []
        for test_file in self.test_files[:3]:
            file_stat = test_file.stat()
            result = FileDiscoveryResult(
                file_path=test_file,
                is_valid=True,
                file_size=file_stat.st_size,
                modified_time=file_stat.st_mtime,
                discovery_time=datetime.now(),
                validation_time=0.1
            )
            file_results.append(result)

        # フォルダスキャン結果をキャッシュ
        success = self.cache.cache_folder_scan(
            self.temp_path, file_results, 5, 1.5
        )
        self.assertTrue(success)

        # キャッシュから取得
        cached_scan = self.cache.get_cached_folder_scan(self.temp_path)
        self.assertIsNotNone(cached_scan)
        self.assertEqual(cached_scan.folder_path, self.temp_path)
        self.assertEqual(len(cached_scan.file_results), 3)
        self.assertEqual(cached_scan.total_files_scanned, 5)
        self.assertAlmostEqual(cached_scan.scan_duration, 1.5, places=1)

    def test_cache_hit_miss_metrics(self):
        """キャッシュヒット/ミスメトリクスのテスト"""
        test_file = self.test_files[0]

        # 初期状態の確認
        stats = self.cache.get_cache_stats()
        initial_hits = stats['validation_cache']['hits']
        initial_misses = stats['validation_cache']['misses']

        # キャッシュミス
        result = self.cache.get_cached_validation_result(test_file)
        self.assertIsNone(result)

        # ミス数が増加していることを確認
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['validation_cache']['misses'], initial_misses + 1)

        # キャッシュに保存
        self.cache.cache_validation_result(test_file, True)

        # キャッシュヒット
        result = self.cache.get_cached_validation_result(test_file)
        self.assertTrue(result)

        # ヒット数が増加していることを確認
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['validation_cache']['hits'], initial_hits + 1)

    def test_lru_eviction(self):
        """LRU削除機能のテスト"""
        # キャッシュサイズを超えるファイルを追加
        for i, test_file in enumerate(self.test_files):
            self.cache.cache_validation_result(test_file, i % 2 == 0)

        # さらに多くのファイルを追加してLRU削除をトリガー
        for i in range(20):
            fake_file = self.temp_path / f"fake_{i}.jpg"
            fake_file.write_bytes(b"fake_data")
            self.cache.cache_validation_result(fake_file, True)

        # 統計を確認
        stats = self.cache.get_cache_stats()
        self.assertGreater(stats['validation_cache']['evictions'], 0)

    def test_cache_expiration(self):
        """キャッシュ期限切れのテスト"""
        test_file = self.test_files[0]

        # ファイル結果をキャッシュ
        self.cache.cache_file_result(test_file, True, 0.1)

        # キャッシュから取得できることを確認
        cached_result = self.cache.get_cached_file_result(test_file)
        self.assertIsNotNone(cached_result)

        # ファイルを変更（mtime更新）
        time.sleep(0.1)  # 確実にmtimeが変わるように待機
        test_file.write_bytes(b"modified_fake_image_data")

        # 期限切れによりキャッシュミスになることを確認
        cached_result = self.cache.get_cached_file_result(test_file)
        self.assertIsNone(cached_result)

    def test_cache_cleanup(self):
        """キャッシュクリーンアップのテスト"""
        # いくつかのエントリをキャッシュ
        for test_file in self.test_files:
            self.cache.cache_validation_result(test_file, True)

        # クリーンアップ前の統計
        stats_before = self.cache.get_cache_stats()
        entries_before = stats_before['validation_cache']['entries']

        # クリーンアップ実行
        self.cache.cleanup_expired_entries()

        # クリーンアップ後の統計（期限切れがない場合は変化なし）
        stats_after = self.cache.get_cache_stats()
        entries_after = stats_after['validation_cache']['entries']

        # 期限切れエントリがない場合はエントリ数は変わらない
        self.assertEqual(entries_before, entries_after)

    def test_cache_clear(self):
        """キャッシュクリア機能のテスト"""
        # 各種キャッシュにデータを追加
        test_file = self.test_files[0]
        self.cache.cache_validation_result(test_file, True)
        self.cache.cache_file_result(test_file, True, 0.1)

        file_results = [FileDiscoveryResult(
            file_path=test_file,
            is_valid=True,
            file_size=test_file.stat().st_size,
            modified_time=test_file.stat().st_mtime,
            discovery_time=datetime.now()
        )]
        self.cache.cache_folder_scan(self.temp_path, file_results, 1, 0.5)

        # 全キャッシュクリア
        self.cache.clear_cache()

        # 全てのキャッシュが空になっていることを確認
        stats = self.cache.get_cache_stats()
        self.assertEqual(stats['file_cache']['entries'], 0)
        self.assertEqual(stats['folder_cache']['entries'], 0)
        self.assertEqual(stats['validation_cache']['entries'], 0)

    def test_cache_stats(self):
        """キャッシュ統計情報のテスト"""
        # 初期統計
        stats = self.cache.get_cache_stats()
        self.assertIn('file_cache', stats)
        self.assertIn('folder_cache', stats)
        self.assertIn('validation_cache', stats)
        self.assertIn('total_memory_mb', stats)
        self.assertIn('total_entries', stats)
        self.assertIn('overall_hit_rate', stats)

        # データを追加
        test_file = self.test_files[0]
        self.cache.cache_validation_result(test_file, True)

        # 統計が更新されていることを確認
        stats = self.cache.get_cache_stats()
        self.assertGreater(stats['validation_cache']['entries'], 0)

    def test_cache_summary(self):
        """キャッシュサマリーのテスト"""
        # データを追加
        for test_file in self.test_files[:3]:
            self.cache.cache_validation_result(test_file, True)

        # サマリーを取得
        summary = self.cache.get_cache_summary()
        self.assertIsInstance(summary, str)
        self.assertIn("FileDiscoveryCache Summary", summary)
        self.assertIn("Validation Cache", summary)

    def test_memory_usage_tracking(self):
        """メモリ使用量追跡のテスト"""
        # 大量のデータを追加
        for i, test_file in enumerate(self.test_files):
            self.cache.cache_file_result(test_file, True, 0.1)
            self.cache.cache_validation_result(test_file, True)

        # メモリ使用量が記録されていることを確認
        stats = self.cache.get_cache_stats()
        self.assertGreater(stats['total_memory_mb'], 0)
        self.assertGreater(stats['file_cache']['memory_usage_mb'], 0)


class TestFileDiscoveryResult(unittest.TestCase):
    """FileDiscoveryResultのテストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.test_file = self.temp_path / "test.jpg"
        self.test_file.write_bytes(b"test_image_data")

    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_key_generation(self):
        """キャッシュキー生成のテスト"""
        file_stat = self.test_file.stat()
        result = FileDiscoveryResult(
            file_path=self.test_file,
            is_valid=True,
            file_size=file_stat.st_size,
            modified_time=file_stat.st_mtime,
            discovery_time=datetime.now()
        )

        # キャッシュキーが正しく生成されることを確認
        expected_key = f"file_{self.test_file.stem}_{file_stat.st_size}_{int(file_stat.st_mtime)}"
        self.assertEqual(result.cache_key, expected_key)

    def test_expiration_check(self):
        """期限切れチェックのテスト"""
        file_stat = self.test_file.stat()
        result = FileDiscoveryResult(
            file_path=self.test_file,
            is_valid=True,
            file_size=file_stat.st_size,
            modified_time=file_stat.st_mtime,
            discovery_time=datetime.now()
        )

        # 初期状態では期限切れではない
        self.assertFalse(result.is_expired)

        # ファイルを変更
        time.sleep(0.1)
        self.test_file.write_bytes(b"modified_test_image_data")

        # 期限切れになることを確認
        self.assertTrue(result.is_expired)


if __name__ == '__main__':
    unittest.main()
