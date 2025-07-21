#!/usr/bin/env python3
"""
画像ローダーモジュールの単体テスト
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをPythonパスに追加
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.image_loader import ImageLoader
from src.core.logger import get_logger


class TestImageLoader(unittest.TestCase):
    """ImageLoaderのテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        self.logger = get_logger(__name__)

        # QApplicationのモック
        with patch("PyQt6.QtWidgets.QApplication") as mock_qapp:
            mock_qapp.instance.return_value = MagicMock()
            self.image_loader = ImageLoader()

        # テスト用の一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        """初期化テスト"""
        self.assertIsNotNone(self.image_loader)
        self.assertIsNotNone(self.image_loader.logger)
        self.assertIsNotNone(self.image_loader.mutex)
        self.assertIsNotNone(self.image_loader.executor)

    def test_load_directory(self):
        """ディレクトリ読み込みテスト"""
        # テスト用の画像ファイルを作成
        test_files = [
            "image1.jpg",
            "image2.png",
            "image3.bmp",
            "document.txt",  # 画像以外のファイル
            "image4.gif",
        ]

        for filename in test_files:
            file_path = os.path.join(self.test_dir, filename)
            with open(file_path, "w") as f:
                f.write("test content")

        # ディレクトリから画像を読み込み
        result = self.image_loader.load_directory(self.test_dir)

        # 結果を検証（画像ファイルのみが読み込まれる）
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)  # 画像ファイル4つ

        # 画像ファイル名を確認
        image_names = [os.path.basename(path) for path in result]
        self.assertIn("image1.jpg", image_names)
        self.assertIn("image2.png", image_names)
        self.assertIn("image3.bmp", image_names)
        self.assertIn("image4.gif", image_names)
        self.assertNotIn("document.txt", image_names)

    def test_load_directory_empty(self):
        """空のディレクトリ読み込みテスト"""
        # 空のディレクトリ
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)

        # ディレクトリから画像を読み込み
        result = self.image_loader.load_directory(empty_dir)

        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_load_directory_nonexistent(self):
        """存在しないディレクトリ読み込みテスト"""
        # 存在しないディレクトリ
        nonexistent_dir = os.path.join(self.test_dir, "nonexistent")

        # ディレクトリから画像を読み込み
        result = self.image_loader.load_directory(nonexistent_dir)

        # 結果を検証
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    def test_load_image_with_valid_file(self):
        """有効な画像ファイルの読み込みテスト"""
        # テスト用の画像ファイルパス
        test_image_path = os.path.join(self.test_dir, "test_image.jpg")

        # モックのPIL Image
        mock_image = MagicMock()
        mock_image.size = (800, 600)
        mock_image.mode = "RGB"
        mock_image.width = 800
        mock_image.height = 600
        mock_image.tobytes.return_value = b"mock_image_data"

        with patch("PIL.Image.open") as mock_pil_open:
            mock_pil_open.return_value.__enter__.return_value = mock_image

            # 画像を読み込み
            result = self.image_loader.load_image(test_image_path)

            # 結果を検証
            self.assertIsNotNone(result)
            mock_pil_open.assert_called_once_with(test_image_path)

    def test_load_image_with_invalid_file(self):
        """無効な画像ファイルの読み込みテスト"""
        # 存在しないファイルパス
        invalid_path = os.path.join(self.test_dir, "nonexistent.jpg")

        # 画像を読み込み
        result = self.image_loader.load_image(invalid_path)

        # 結果を検証（ファイルが存在しないのでNone）
        self.assertIsNone(result)

    def test_load_image_with_corrupted_file(self):
        """破損した画像ファイルの読み込みテスト"""
        # テスト用の画像ファイルパス
        test_image_path = os.path.join(self.test_dir, "corrupted_image.jpg")

        # 破損したファイル（実際にはテキスト）を作成
        with open(test_image_path, "w") as f:
            f.write("これは画像ファイルではありません")

        # 画像を読み込み
        result = self.image_loader.load_image(test_image_path)

        # 結果を検証（破損ファイルなのでNone）
        self.assertIsNone(result)

    def test_load_image_with_size(self):
        """サイズ指定での画像読み込みテスト"""
        # テスト用の画像ファイルパス
        test_image_path = os.path.join(self.test_dir, "test_image.jpg")

        # モックのPIL Image
        mock_image = MagicMock()
        mock_image.size = (800, 600)
        mock_image.mode = "RGB"
        mock_image.width = 800
        mock_image.height = 600
        mock_image.tobytes.return_value = b"mock_image_data"

        with patch("PIL.Image.open") as mock_pil_open:
            mock_pil_open.return_value.__enter__.return_value = mock_image

            # サイズを指定して画像を読み込み
            result = self.image_loader.load_image(test_image_path, size=(400, 300))

            # 結果を検証
            self.assertIsNotNone(result)
            mock_pil_open.assert_called_once_with(test_image_path)

    def test_load_thumbnail(self):
        """サムネイル読み込みテスト"""
        # テスト用の画像ファイルパス
        test_image_path = os.path.join(self.test_dir, "test_image.jpg")

        # モックのPIL Image
        mock_image = MagicMock()
        mock_image.size = (800, 600)
        mock_image.mode = "RGB"
        mock_image.width = 800
        mock_image.height = 600
        mock_image.tobytes.return_value = b"mock_image_data"

        with patch("PIL.Image.open") as mock_pil_open:
            mock_pil_open.return_value.__enter__.return_value = mock_image

            # サムネイルを読み込み
            result = self.image_loader.load_thumbnail(test_image_path)

            # 結果を検証
            self.assertIsNotNone(result)
            mock_pil_open.assert_called_once_with(test_image_path)

    def test_get_image_info(self):
        """画像情報取得テスト"""
        # テスト用の画像ファイルパス
        test_image_path = os.path.join(self.test_dir, "test_image.jpg")

        # テストファイルを作成
        with open(test_image_path, "w") as f:
            f.write("test content")

        # モックのQImageReaderとQSize
        from PyQt6.QtCore import QSize

        mock_reader = MagicMock()
        mock_reader.canRead.return_value = True
        mock_reader.size.return_value = QSize(800, 600)
        mock_reader.format.return_value.data.return_value.decode.return_value = "jpeg"

        with patch("src.modules.image_loader.QImageReader") as mock_reader_class:
            mock_reader_class.return_value = mock_reader

            # 画像情報を取得
            result = self.image_loader.get_image_info(test_image_path)

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertEqual(result["width"], 800)
            self.assertEqual(result["height"], 600)
            self.assertEqual(result["mode"], "RGB")
            self.assertEqual(result["format"], "JPEG")
            self.assertEqual(result["file_path"], test_image_path)

    def test_clear_cache(self):
        """キャッシュクリアテスト"""
        # キャッシュをクリア
        self.image_loader.clear_cache()

        # キャッシュサイズを確認
        cache_size = self.image_loader.get_cache_size()
        self.assertEqual(cache_size, 0)

    def test_get_cache_size(self):
        """キャッシュサイズ取得テスト"""
        # 初期キャッシュサイズ
        initial_size = self.image_loader.get_cache_size()
        self.assertEqual(initial_size, 0)

    def test_is_loading(self):
        """読み込み状態確認テスト"""
        # 初期状態
        is_loading = self.image_loader.is_loading()
        self.assertFalse(is_loading)

    def test_cancel_loading(self):
        """読み込みキャンセルテスト"""
        # 読み込みをキャンセル
        self.image_loader.cancel_loading()

        # 読み込み状態を確認
        is_loading = self.image_loader.is_loading()
        self.assertFalse(is_loading)

    def test_load_image_with_real_file(self):
        """実際の画像ファイルでの読み込みテスト"""
        # 実際の画像ファイルパス
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        test_image_path = test_data_dir / "with_exif" / "SUGA2491.JPG"

        if test_image_path.exists():
            # 画像を読み込み
            result = self.image_loader.load_image(str(test_image_path))

            # 結果を検証
            self.assertIsNotNone(result)

    def test_get_image_info_with_real_file(self):
        """実際の画像ファイルでの情報取得テスト"""
        # 実際の画像ファイルパス
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        test_image_path = test_data_dir / "with_exif" / "SUGA2491.JPG"

        if test_image_path.exists():
            # 画像情報を取得
            result = self.image_loader.get_image_info(str(test_image_path))

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertIn("width", result)
            self.assertIn("height", result)
            self.assertIn("format", result)


if __name__ == "__main__":
    unittest.main()
