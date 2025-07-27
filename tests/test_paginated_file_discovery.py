"""
PaginatedFileDiscovery のテスト

段階的ファイル読み込み機能のテストケース
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.integration.services.paginated_file_discovery import PaginatedFileDiscovery, FileBatch
from src.integration.services.file_discovery_service import FileDiscoveryService
from src.integration.logging_system import LoggerSystem


class TestPaginatedFileDiscovery(unittest.TestCase):
    """PaginatedFileDiscoveryのテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger_system = LoggerSystem()
        self.mock_file_discovery = Mock(spec=FileDiscoveryService)

        # テスト用の画像ファイルパスを作成
        self.test_files = []
        for i in range(25):  # 25個のテストファイル
            file_path = self.temp_dir / f"test_image_{i:03d}.jpg"
            file_path.touch()  # 空ファイルを作成
            self.test_files.append(file_path)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """初期化のテスト"""
        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        self.assertEqual(paginated_discovery.page_size, 10)
        self.assertFalse(paginated_discovery._is_initialized)
        self.assertEqual(paginated_discovery._current_batch_index, 0)

    def test_folder_initialization(self):
        """フォルダ初期化のテスト"""
        # モックの設定
        self.mock_file_discovery.discover_images.return_value = self.test_files

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # フォルダを初期化
        result = paginated_discovery.initialize_folder(self.temp_dir)

        # 結果の検証
        self.assertTrue(paginated_discovery._is_initialized)
        self.assertEqual(result['total_files'], 25)
        self.assertEqual(result['total_batches'], 3)  # 25ファイル ÷ 10 = 3バッチ
        self.assertEqual(result['batch_size'], 10)
        self.mock_file_discovery.discover_images.assert_called_once_with(self.temp_dir)

    def test_get_next_batch(self):
        """次のバッチ取得のテスト"""
        self.mock_file_discovery.discover_images.return_value = self.test_files

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # フォルダを初期化
        paginated_discovery.initialize_folder(self.temp_dir)

        # 最初のバッチを取得
        batch1 = paginated_discovery.get_next_batch()
        self.assertIsInstance(batch1, FileBatch)
        self.assertEqual(batch1.batch_number, 0)
        self.assertEqual(batch1.batch_size, 10)
        self.assertEqual(batch1.total_batches, 3)
        self.assertFalse(batch1.is_last_batch)

        # 2番目のバッチを取得
        batch2 = paginated_discovery.get_next_batch()
        self.assertEqual(batch2.batch_number, 1)
        self.assertEqual(batch2.batch_size, 10)

        # 最後のバッチを取得
        batch3 = paginated_discovery.get_next_batch()
        self.assertEqual(batch3.batch_number, 2)
        self.assertEqual(batch3.batch_size, 5)  # 残り5ファイル
        self.assertTrue(batch3.is_last_batch)

        # もうバッチがないことを確認
        batch4 = paginated_discovery.get_next_batch()
        self.assertIsNone(batch4)

    def test_has_more_files(self):
        """残りファイル確認のテスト"""
        self.mock_file_discovery.discover_images.return_value = self.test_files

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # 初期化前はFalse
        self.assertFalse(paginated_discovery.has_more_files())

        # フォルダを初期化
        paginated_discovery.initialize_folder(self.temp_dir)

        # 初期化後はTrue
        self.assertTrue(paginated_discovery.has_more_files())

        # バッチを取得していく
        paginated_discovery.get_next_batch()  # バッチ1
        self.assertTrue(paginated_discovery.has_more_files())

        paginated_discovery.get_next_batch()  # バッチ2
        self.assertTrue(paginated_discovery.has_more_files())

        paginated_discovery.get_next_batch()  # バッチ3（最後）
        self.assertFalse(paginated_discovery.has_more_files())

    def test_reset_pagination(self):
        """ページネーションリセットのテスト"""
        self.mock_file_discovery.discover_images.return_value = self.test_files

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # フォルダを初期化してバッチを取得
        paginated_discovery.initialize_folder(self.temp_dir)
        paginated_discovery.get_next_batch()
        paginated_discovery.get_next_batch()

        # 現在のインデックスが2であることを確認
        self.assertEqual(paginated_discovery._current_batch_index, 2)

        # リセット
        paginated_discovery.reset_pagination()

        # インデックスが0に戻ることを確認
        self.assertEqual(paginated_discovery._current_batch_index, 0)
        self.assertTrue(paginated_discovery.has_more_files())

    def test_get_pagination_status(self):
        """ページネーション状態取得のテスト"""
        self.mock_file_discovery.discover_images.return_value = self.test_files

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # 初期化前の状態
        status = paginated_discovery.get_pagination_status()
        self.assertFalse(status['initialized'])

        # フォルダを初期化
        paginated_discovery.initialize_folder(self.temp_dir)

        # 初期化後の状態
        status = paginated_discovery.get_pagination_status()
        self.assertTrue(status['initialized'])
        self.assertEqual(status['total_files'], 25)
        self.assertEqual(status['total_batches'], 3)
        self.assertEqual(status['current_batch_index'], 0)
        self.assertEqual(status['progress_percentage'], 0.0)

        # バッチを1つ取得後の状態
        paginated_discovery.get_next_batch()
        status = paginated_discovery.get_pagination_status()
        self.assertEqual(status['current_batch_index'], 1)
        self.assertAlmostEqual(status['progress_percentage'], 33.33, places=1)

    def test_batch_iterator(self):
        """バッチイテレータのテスト"""
        self.mock_file_discovery.discover_images.return_value = self.test_files

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # フォルダを初期化
        paginated_discovery.initialize_folder(self.temp_dir)

        # イテレータを使用してすべてのバッチを取得
        batches = list(paginated_discovery.get_batch_iterator())

        # バッチ数の確認
        self.assertEqual(len(batches), 3)

        # 各バッチの確認
        self.assertEqual(batches[0].batch_number, 0)
        self.assertEqual(batches[0].batch_size, 10)

        self.assertEqual(batches[1].batch_number, 1)
        self.assertEqual(batches[1].batch_size, 10)

        self.assertEqual(batches[2].batch_number, 2)
        self.assertEqual(batches[2].batch_size, 5)
        self.assertTrue(batches[2].is_last_batch)

    def test_empty_folder(self):
        """空フォルダのテスト"""
        self.mock_file_discovery.discover_images.return_value = []

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # 空フォルダを初期化
        result = paginated_discovery.initialize_folder(self.temp_dir)

        # 結果の確認
        self.assertEqual(result['total_files'], 0)
        self.assertEqual(result['total_batches'], 0)
        self.assertFalse(paginated_discovery.has_more_files())
        self.assertIsNone(paginated_discovery.get_next_batch())

    def test_single_batch(self):
        """単一バッチのテスト"""
        # 5ファイルのみ（バッチサイズ10より少ない）
        small_file_list = self.test_files[:5]
        self.mock_file_discovery.discover_images.return_value = small_file_list

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # フォルダを初期化
        result = paginated_discovery.initialize_folder(self.temp_dir)

        # 結果の確認
        self.assertEqual(result['total_files'], 5)
        self.assertEqual(result['total_batches'], 1)

        # バッチを取得
        batch = paginated_discovery.get_next_batch()
        self.assertEqual(batch.batch_size, 5)
        self.assertTrue(batch.is_last_batch)

        # 次のバッチはない
        self.assertIsNone(paginated_discovery.get_next_batch())

    def test_cleanup(self):
        """クリーンアップのテスト"""
        self.mock_file_discovery.discover_images.return_value = self.test_files

        paginated_discovery = PaginatedFileDiscovery(
            file_discovery_service=self.mock_file_discovery,
            page_size=10,
            logger_system=self.logger_system
        )

        # フォルダを初期化してバッチを取得
        paginated_discovery.initialize_folder(self.temp_dir)
        paginated_discovery.get_next_batch()

        # クリーンアップ前の状態確認
        self.assertTrue(paginated_discovery._is_initialized)
        self.assertIsNotNone(paginated_discovery._current_folder)

        # クリーンアップ実行
        paginated_discovery.cleanup()

        # クリーンアップ後の状態確認
        self.assertFalse(paginated_discovery._is_initialized)
        self.assertIsNone(paginated_discovery._current_folder)
        self.assertEqual(len(paginated_discovery._all_files), 0)
        self.assertEqual(paginated_discovery._current_batch_index, 0)


if __name__ == '__main__':
    unittest.main()
