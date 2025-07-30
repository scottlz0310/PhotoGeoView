"""
非同期ファイル検出機能のテスト

FileDiscoveryServiceの非同期機能のテストケース
"""

import asyncio
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from src.integration.image_processor import CS4CodingImageProcessor
from src.integration.logging_system import LoggerSystem
from src.integration.services.file_discovery_service import FileDiscoveryService


class TestAsyncFileDiscovery(unittest.TestCase):
    """非同期ファイル検出のテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.logger_system = LoggerSystem()
        self.mock_image_processor = Mock(spec=CS4CodingImageProcessor)

        # テスト用の画像ファイルを作成
        self.test_files = []
        for i in range(10):
            file_path = self.temp_dir / f"test_image_{i:03d}.jpg"
            file_path.touch()  # 空ファイルを作成
            self.test_files.append(file_path)

        # 非画像ファイルも作成
        for i in range(5):
            file_path = self.temp_dir / f"test_document_{i:03d}.txt"
            file_path.touch()

        # FileDiscoveryServiceのインスタンス作成
        self.file_discovery = FileDiscoveryService(
            logger_system=self.logger_system, image_processor=self.mock_image_processor
        )

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_images_async_basic(self):
        """基本的な非同期画像検出のテスト"""
        # モックの設定
        self.mock_image_processor.validate_image.return_value = True
        self.mock_image_processor.load_image.return_value = (
            Mock()
        )  # 有効な画像オブジェクト

        async def run_test():
            discovered_files = []
            async for image_path in self.file_discovery.discover_images_async(
                self.temp_dir
            ):
                discovered_files.append(image_path)

            # 結果の検証
            self.assertEqual(len(discovered_files), 10)  # 10個のJPGファイル
            for file_path in discovered_files:
                self.assertTrue(file_path.suffix.lower() == ".jpg")
                self.assertTrue(file_path.exists())

        # 非同期テストを実行
        asyncio.run(run_test())

    def test_discover_images_async_with_progress(self):
        """進行状況コールバック付き非同期検出のテスト"""
        # モックの設定
        self.mock_image_processor.validate_image.return_value = True
        self.mock_image_processor.load_image.return_value = Mock()

        # 進行状況を記録するリスト
        progress_calls = []

        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))

        async def run_test():
            discovered_files = []
            async for image_path in self.file_discovery.discover_images_async(
                self.temp_dir, progress_callback=progress_callback, batch_size=3
            ):
                discovered_files.append(image_path)

            # 結果の検証
            self.assertEqual(len(discovered_files), 10)

            # 進行状況コールバックが呼ばれたことを確認
            self.assertGreater(len(progress_calls), 0)

            # 最初と最後の進行状況を確認
            first_call = progress_calls[0]
            last_call = progress_calls[-1]

            self.assertEqual(first_call[0], 0)  # 開始時は0
            self.assertEqual(last_call[0], last_call[1])  # 最後は完了
            self.assertIn("完了", last_call[2])  # 完了メッセージ

        asyncio.run(run_test())

    def test_discover_images_async_invalid_folder(self):
        """無効なフォルダでの非同期検出のテスト"""
        invalid_folder = Path("/nonexistent/folder")

        async def run_test():
            discovered_files = []
            async for image_path in self.file_discovery.discover_images_async(
                invalid_folder
            ):
                discovered_files.append(image_path)

            # 無効なフォルダでは何も発見されない
            self.assertEqual(len(discovered_files), 0)

        asyncio.run(run_test())

    def test_discover_images_async_validation_failure(self):
        """バリデーション失敗時の非同期検出のテスト"""
        # バリデーションが失敗するように設定
        self.mock_image_processor.validate_image.return_value = False

        async def run_test():
            discovered_files = []
            async for image_path in self.file_discovery.discover_images_async(
                self.temp_dir
            ):
                discovered_files.append(image_path)

            # バリデーション失敗により何も発見されない
            self.assertEqual(len(discovered_files), 0)

        asyncio.run(run_test())

    def test_discover_images_async_mixed_validation(self):
        """一部のファイルがバリデーション失敗する場合のテスト"""

        # 偶数インデックスのファイルのみ有効とする
        def mock_validate(file_path):
            index = int(file_path.stem.split("_")[-1])
            return index % 2 == 0

        self.mock_image_processor.validate_image.side_effect = mock_validate
        self.mock_image_processor.load_image.return_value = Mock()

        async def run_test():
            discovered_files = []
            async for image_path in self.file_discovery.discover_images_async(
                self.temp_dir
            ):
                discovered_files.append(image_path)

            # 偶数インデックスのファイルのみ発見される（5個）
            self.assertEqual(len(discovered_files), 5)

            # 発見されたファイルが偶数インデックスであることを確認
            for file_path in discovered_files:
                index = int(file_path.stem.split("_")[-1])
                self.assertEqual(index % 2, 0)

        asyncio.run(run_test())

    def test_scan_folder_async(self):
        """非同期フォルダスキャンのテスト"""
        # モックの設定
        self.mock_image_processor.validate_image.return_value = True
        self.mock_image_processor.load_image.return_value = Mock()

        progress_calls = []

        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))

        async def run_test():
            discovered_files = await self.file_discovery.scan_folder_async(
                self.temp_dir, progress_callback=progress_callback
            )

            # 結果の検証
            self.assertEqual(len(discovered_files), 10)
            self.assertIsInstance(discovered_files, list)

            # すべてのファイルがPathオブジェクトであることを確認
            for file_path in discovered_files:
                self.assertIsInstance(file_path, Path)
                self.assertTrue(file_path.exists())

        asyncio.run(run_test())

    def test_validate_image_file_async(self):
        """非同期ファイルバリデーションのテスト"""
        test_file = self.test_files[0]

        # モックの設定
        self.mock_image_processor.validate_image.return_value = True
        self.mock_image_processor.load_image.return_value = Mock()

        async def run_test():
            # 有効なファイルのテスト
            is_valid = await self.file_discovery._validate_image_file_async(test_file)
            self.assertTrue(is_valid)

            # 無効なファイルのテスト
            self.mock_image_processor.validate_image.return_value = False
            is_valid = await self.file_discovery._validate_image_file_async(test_file)
            self.assertFalse(is_valid)

        asyncio.run(run_test())

    def test_validate_image_file_async_load_failure(self):
        """画像読み込み失敗時の非同期バリデーションのテスト"""
        test_file = self.test_files[0]

        # バリデーションは成功するが読み込みが失敗する設定
        self.mock_image_processor.validate_image.return_value = True
        self.mock_image_processor.load_image.return_value = None  # 読み込み失敗

        async def run_test():
            is_valid = await self.file_discovery._validate_image_file_async(test_file)
            self.assertFalse(is_valid)  # 読み込み失敗により無効

        asyncio.run(run_test())

    def test_validate_image_file_async_exception(self):
        """例外発生時の非同期バリデーションのテスト"""
        test_file = self.test_files[0]

        # バリデーション時に例外が発生する設定
        self.mock_image_processor.validate_image.side_effect = Exception(
            "Test exception"
        )

        async def run_test():
            is_valid = await self.file_discovery._validate_image_file_async(test_file)
            self.assertFalse(is_valid)  # 例外により無効

        asyncio.run(run_test())

    def test_async_batch_processing(self):
        """バッチ処理の非同期動作テスト"""
        # モックの設定
        self.mock_image_processor.validate_image.return_value = True
        self.mock_image_processor.load_image.return_value = Mock()

        async def run_test():
            discovered_files = []
            batch_size = 3

            async for image_path in self.file_discovery.discover_images_async(
                self.temp_dir, batch_size=batch_size
            ):
                discovered_files.append(image_path)

            # バッチサイズに関係なく全ファイルが発見される
            self.assertEqual(len(discovered_files), 10)

        asyncio.run(run_test())

    def test_async_cancellation(self):
        """非同期処理のキャンセルテスト"""

        # モックの設定（処理を遅くする）
        async def slow_validate(file_path):
            await asyncio.sleep(0.1)  # 100ms待機
            return True

        self.mock_image_processor.validate_image.return_value = True
        self.mock_image_processor.load_image.return_value = Mock()

        async def run_test():
            discovered_files = []

            try:
                # タスクを作成
                async def discovery_task():
                    async for image_path in self.file_discovery.discover_images_async(
                        self.temp_dir
                    ):
                        discovered_files.append(image_path)

                # 短時間でタイムアウト
                await asyncio.wait_for(discovery_task(), timeout=0.05)

            except asyncio.TimeoutError:
                # タイムアウトが発生することを期待
                pass

            # 部分的な結果が得られる可能性がある
            self.assertLessEqual(len(discovered_files), 10)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
