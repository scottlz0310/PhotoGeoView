"""
メモリ管理機能付きファイル検出のテスト

MemoryAwareFileDiscoveryのテストケース
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.integration.services.memory_aware_file_discovery import MemoryAwareFileDiscovery, MemoryStats
from src.integration.services.file_discovery_service import FileDiscoveryService
from src.integration.logging_system import LoggerSystem


class TestMemoryAwareFileDiscovery(unittest.TestCase):
    """MemoryAwareFileDiscoveryのテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger_system = LoggerSystem()
        self.mock_file_discovery = Mock(spec=FileDiscoveryService)

        # テスト用の画像ファイルを作成
        self.test_files = []
        for i in range(5):
            file_path = self.temp_dir / f"test_image_{i:03d}.jpg"
            file_path.touch()
            self.test_files.append(file_path)

        # MemoryAwareFileDiscoveryのインスタンス作成
        self.memory_aware_discovery = MemoryAwareFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            max_memory_mb=128,
            warning_threshold=0.75,
            critical_threshold=0.90,
            logger_system=self.logger_system
        )

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """初期化のテスト"""
        self.assertEqual(self.memory_aware_discovery.max_memory_mb, 128)
        self.assertEqual(self.memory_aware_discovery.warning_threshold, 0.75)
        self.assertEqual(self.memory_aware_discovery.critical_threshold, 0.90)
        self.assertEqual(len(self.memory_aware_discovery._cache_data), 0)

    def test_discover_images_with_memory_management(self):
        """メモリ管理機能付きファイル検出のテスト"""
        # モックの設定
        self.mock_file_discovery.discover_images.return_value = self.test_files

        # ファイル検出を実行
        discovered_files = self.memory_aware_discovery.discover_images_with_memory_management(self.temp_dir)

        # 結果の検証
        self.assertEqual(len(discovered_files), 5)
        self.mock_file_discovery.discover_images.assert_called_once_with(self.temp_dir)

        # 統計情報の確認
        stats = self.memory_aware_discovery._stats
        self.assertEqual(stats['total_discoveries'], 1)
        self.assertEqual(stats['cache_misses'], 1)

    def test_cache_functionality(self):
        """キャッシュ機能のテスト"""
        # モックの設定
        self.mock_file_discovery.discover_images.return_value = self.test_files

        # 最初の検出（キャッシュミス）
        discovered_files1 = self.memory_aware_discovery.discover_images_with_memory_management(self.temp_dir)
        self.assertEqual(len(discovered_files1), 5)
        self.assertEqual(self.memory_aware_discovery._stats['cache_misses'], 1)
        self.assertEqual(self.memory_aware_discovery._stats['cache_hits'], 0)

        # 2回目の検出（キャッシュヒット）
        discovered_files2 = self.memory_aware_discovery.discover_images_with_memory_management(self.temp_dir)
        self.assertEqual(len(discovered_files2), 5)
        self.assertEqual(self.memory_aware_discovery._stats['cache_misses'], 1)
        self.assertEqual(self.memory_aware_discovery._stats['cache_hits'], 1)

        # ファイル検出サービスは1回だけ呼ばれる
        self.mock_file_discovery.discover_images.assert_called_once()

    @patch('src.integration.services.memory_aware_file_discovery.psutil.virtual_memory')
    @patch('src.integration.services.memory_aware_file_discovery.psutil.Process')
    def test_memory_stats_collection(self, mock_process, mock_virtual_memory):
        """メモリ統計収集のテスト"""
        # モックの設定
        mock_virtual_memory.return_value.percent = 75.0
        mock_virtual_memory.return_value.available = 1024 * 1024 * 1024  # 1GB

        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 128 * 1024 * 1024  # 128MB
        mock_process_instance.memory_info.return_value.vms = 256 * 1024 * 1024  # 256MB
        mock_process.return_value = mock_process_instance

        # メモリ統計を取得
        memory_stats = self.memory_aware_discovery._get_current_memory_stats()

        # 結果の検証
        self.assertEqual(memory_stats.current_usage_mb, 128.0)
        self.assertEqual(memory_stats.peak_usage_mb, 256.0)
        self.assertEqual(memory_stats.available_mb, 1024.0)
        self.assertEqual(memory_stats.usage_percentage, 75.0)
        self.assertFalse(memory_stats.is_critical_usage)
        self.assertFalse(memory_stats.is_high_usage)

    @patch('src.integration.services.memory_aware_file_discovery.psutil.virtual_memory')
    @patch('src.integration.services.memory_aware_file_discovery.psutil.Process')
    def test_high_memory_usage_detection(self, mock_process, mock_virtual_memory):
        """高メモリ使用量検出のテスト"""
        # 高メモリ使用量をシミュレート
        mock_virtual_memory.return_value.percent = 85.0
        mock_virtual_memory.return_value.available = 512 * 1024 * 1024  # 512MB

        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 200 * 1024 * 1024  # 200MB
        mock_process_instance.memory_info.return_value.vms = 400 * 1024 * 1024  # 400MB
        mock_process.return_value = mock_process_instance

        memory_stats = self.memory_aware_discovery._get_current_memory_stats()

        # 高メモリ使用量として検出される
        self.assertTrue(memory_stats.is_high_usage)
        self.assertFalse(memory_stats.is_critical_usage)

    @patch('src.integration.services.memory_aware_file_discovery.psutil.virtual_memory')
    @patch('src.integration.services.memory_aware_file_discovery.psutil.Process')
    def test_critical_memory_usage_detection(self, mock_process, mock_virtual_memory):
        """危険メモリ使用量検出のテスト"""
        # 危険メモリ使用量をシミュレート
        mock_virtual_memory.return_value.percent = 95.0
        mock_virtual_memory.return_value.available = 256 * 1024 * 1024  # 256MB

        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 300 * 1024 * 1024  # 300MB
        mock_process_instance.memory_info.return_value.vms = 600 * 1024 * 1024  # 600MB
        mock_process.return_value = mock_process_instance

        memory_stats = self.memory_aware_discovery._get_current_memory_stats()

        # 危険メモリ使用量として検出される
        self.assertTrue(memory_stats.is_high_usage)
        self.assertTrue(memory_stats.is_critical_usage)

    def test_memory_cleanup(self):
        """メモリクリーンアップのテスト"""
        # キャッシュにデータを追加
        self.memory_aware_discovery._cache_data = {
            'test1': [Path('file1.jpg')],
            'test2': [Path('file2.jpg')],
            'test3': [Path('file3.jpg')]
        }

        # メモリ統計履歴を追加
        for i in range(150):  # 制限を超える数
            self.memory_aware_discovery._memory_stats_history.append(
                MemoryStats(100.0, 200.0, 500.0, 50.0, 10.0)
            )

        initial_cache_size = len(self.memory_aware_discovery._cache_data)
        initial_history_size = len(self.memory_aware_discovery._memory_stats_history)

        # クリーンアップを実行
        self.memory_aware_discovery._perform_memory_cleanup()

        # 結果の検証
        self.assertEqual(len(self.memory_aware_discovery._cache_data), 0)
        self.assertLess(len(self.memory_aware_discovery._memory_stats_history), initial_history_size)
        self.assertEqual(self.memory_aware_discovery._stats['memory_cleanups'], 1)

    def test_cache_key_generation(self):
        """キャッシュキー生成のテスト"""
        # 正常なフォルダパス
        cache_key = self.memory_aware_discovery._generate_cache_key(self.temp_dir)
        self.assertIn(str(self.temp_dir), cache_key)

        # 存在しないフォルダパス
        nonexistent_path = Path("/nonexistent/folder")
        cache_key = self.memory_aware_discovery._generate_cache_key(nonexistent_path)
        self.assertEqual(cache_key, str(nonexistent_path))

    def test_cache_size_limit(self):
        """キャッシュサイズ制限のテスト"""
        # キャッシュ制限を超えるデータを追加
        for i in range(55):  # 制限(50)を超える数
            cache_key = f"test_key_{i}"
            self.memory_aware_discovery._store_in_cache(cache_key, [Path(f"file_{i}.jpg")])

        # キャッシュサイズが制限内に収まっている
        self.assertLessEqual(len(self.memory_aware_discovery._cache_data), 50)

    def test_get_memory_status(self):
        """メモリ状態取得のテスト"""
        status = self.memory_aware_discovery.get_memory_status()

        # 必要なキーが含まれている
        self.assertIn('current_memory', status)
        self.assertIn('thresholds', status)
        self.assertIn('statistics', status)
        self.assertIn('cache_info', status)
        self.assertIn('cleanup_info', status)

        # 閾値情報の確認
        self.assertEqual(status['thresholds']['max_memory_mb'], 128)
        self.assertEqual(status['thresholds']['warning_threshold'], 0.75)
        self.assertEqual(status['thresholds']['critical_threshold'], 0.90)

    def test_force_memory_cleanup(self):
        """強制メモリクリーンアップのテスト"""
        # キャッシュにデータを追加
        self.memory_aware_discovery._cache_data = {'test': [Path('file.jpg')]}

        # 強制クリーンアップを実行
        result = self.memory_aware_discovery.force_memory_cleanup()

        # 結果の検証
        self.assertTrue(result['cleanup_performed'])
        self.assertIn('memory_before_mb', result)
        self.assertIn('memory_after_mb', result)
        self.assertIn('memory_freed_mb', result)
        self.assertEqual(len(self.memory_aware_discovery._cache_data), 0)

    def test_clear_cache(self):
        """キャッシュクリアのテスト"""
        # キャッシュにデータを追加
        self.memory_aware_discovery._cache_data = {
            'test1': [Path('file1.jpg')],
            'test2': [Path('file2.jpg')]
        }

        # キャッシュをクリア
        self.memory_aware_discovery.clear_cache()

        # キャッシュが空になっている
        self.assertEqual(len(self.memory_aware_discovery._cache_data), 0)

    def test_cleanup(self):
        """クリーンアップのテスト"""
        # データを追加
        self.memory_aware_discovery._cache_data = {'test': [Path('file.jpg')]}
        self.memory_aware_discovery._memory_stats_history = [
            MemoryStats(100.0, 200.0, 500.0, 50.0, 10.0)
        ]

        # クリーンアップを実行
        self.memory_aware_discovery.cleanup()

        # すべてのデータがクリアされている
        self.assertEqual(len(self.memory_aware_discovery._cache_data), 0)
        self.assertEqual(len(self.memory_aware_discovery._memory_stats_history), 0)

    @patch('src.integration.services.memory_aware_file_discovery.psutil.virtual_memory')
    @patch('src.integration.services.memory_aware_file_discovery.psutil.Process')
    def test_memory_stats_error_handling(self, mock_process, mock_virtual_memory):
        """メモリ統計エラーハンドリングのテスト"""
        # psutilでエラーが発生する場合をシミュレート
        mock_virtual_memory.side_effect = Exception("psutil error")
        mock_process.side_effect = Exception("process error")

        # エラーが発生してもフォールバック値が返される
        memory_stats = self.memory_aware_discovery._get_current_memory_stats()

        self.assertEqual(memory_stats.current_usage_mb, 0.0)
        self.assertEqual(memory_stats.usage_percentage, 0.0)
        self.assertEqual(memory_stats.available_mb, 1024.0)


if __name__ == '__main__':
    unittest.main()
