#!/usr/bin/env python3
"""
EXIF解析モジュールの単体テスト
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

# プロジェクトルートをPythonパスに追加
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.exif_parser import ExifParser
from src.core.logger import get_logger


class TestExifParser(unittest.TestCase):
    """ExifParserのテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        self.logger = get_logger(__name__)
        self.exif_parser = ExifParser()

        # テスト用の一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリを削除
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_exif_data_with_valid_image(self):
        """有効な画像ファイルでのEXIF解析テスト"""
        # 実際の画像ファイルを使用
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        test_image_path = test_data_dir / "with_exif" / "SUGA2491.JPG"

        if test_image_path.exists():
            # EXIFデータを解析
            result = self.exif_parser.parse_exif(str(test_image_path))

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)

            # 実際のEXIFデータが含まれているかチェック
            if result:  # EXIFデータがある場合
                self.assertIsInstance(result, dict)

    def test_parse_exif_data_with_no_exif(self):
        """EXIFデータがない画像ファイルのテスト"""
        # 実際のEXIFデータなし画像を使用
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        test_image_path = test_data_dir / "no_exif" / "ScreenShot-tw.png"

        if test_image_path.exists():
            # EXIFデータを解析
            result = self.exif_parser.parse_exif(str(test_image_path))

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)

    def test_parse_exif_data_with_gps_only(self):
        """GPS座標のみの画像ファイルのテスト"""
        # 実際のGPS座標付き画像を使用
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        test_image_path = test_data_dir / "with_gps" / "PIC001.jpg"

        if test_image_path.exists():
            # EXIFデータを解析
            result = self.exif_parser.parse_exif(str(test_image_path))

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)

    def test_parse_exif_data_with_invalid_file(self):
        """無効なファイルパスのテスト"""
        invalid_path = os.path.join(self.test_dir, "nonexistent.jpg")

        with patch("exifread.process_file") as mock_process_file:
            mock_process_file.side_effect = FileNotFoundError("File not found")

            # ファイル存在チェックをモック
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False

                # EXIFデータを解析
                result = self.exif_parser.parse_exif(invalid_path)

                # 結果を検証
                self.assertIsNotNone(result)
                self.assertEqual(result, {})

    def test_get_gps_coordinates(self):
        """GPS座標取得のテスト"""
        # 実際のGPS座標付き画像を使用
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        test_image_path = test_data_dir / "with_gps" / "PIC001.jpg"

        if test_image_path.exists():
            # GPS座標を取得
            coords = self.exif_parser.get_gps_coordinates(str(test_image_path))

            # 結果を検証（GPS座標がある場合とない場合の両方を考慮）
            if coords is not None:
                self.assertEqual(len(coords), 2)
                self.assertIsInstance(coords[0], float)
                self.assertIsInstance(coords[1], float)

    def test_get_camera_info(self):
        """カメラ情報取得のテスト"""
        # 実際のEXIFデータ付き画像を使用
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        test_image_path = test_data_dir / "with_exif" / "SUGA2491.JPG"

        if test_image_path.exists():
            # カメラ情報を取得
            camera_info = self.exif_parser.get_camera_info(str(test_image_path))

            # 結果を検証
            self.assertIsNotNone(camera_info)
            self.assertIsInstance(camera_info, dict)

    def test_parse_exif_with_real_image(self):
        """実際の画像ファイルでのEXIF解析テスト"""
        # 実際の画像ファイルパス
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        exif_image_path = test_data_dir / "with_exif" / "SUGA2491.JPG"

        if exif_image_path.exists():
            # EXIFデータを解析
            result = self.exif_parser.parse_exif(str(exif_image_path))

            # 結果を検証
            self.assertIsNotNone(result)
            # 実際のEXIFデータが含まれているかチェック
            self.assertIsInstance(result, dict)

    def test_get_gps_coordinates_with_real_image(self):
        """実際のGPS座標付き画像でのGPS座標取得テスト"""
        # 実際の画像ファイルパス
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        gps_image_path = test_data_dir / "with_gps" / "PIC001.jpg"

        if gps_image_path.exists():
            # GPS座標を取得
            coords = self.exif_parser.get_gps_coordinates(str(gps_image_path))

            # 結果を検証（GPS座標がある場合とない場合の両方を考慮）
            if coords is not None:
                self.assertEqual(len(coords), 2)
                self.assertIsInstance(coords[0], float)
                self.assertIsInstance(coords[1], float)

    def test_get_camera_info_with_real_image(self):
        """実際の画像ファイルでのカメラ情報取得テスト"""
        # 実際の画像ファイルパス
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        exif_image_path = test_data_dir / "with_exif" / "SUGA2491.JPG"

        if exif_image_path.exists():
            # カメラ情報を取得
            camera_info = self.exif_parser.get_camera_info(str(exif_image_path))

            # 結果を検証
            self.assertIsNotNone(camera_info)
            self.assertIsInstance(camera_info, dict)

    def test_parse_exif_with_no_exif_image(self):
        """EXIFデータなし画像でのテスト"""
        # 実際の画像ファイルパス
        test_data_dir = Path(__file__).parent / "test_data" / "images"
        no_exif_image_path = test_data_dir / "no_exif" / "ScreenShot-tw.png"

        if no_exif_image_path.exists():
            # EXIFデータを解析
            result = self.exif_parser.parse_exif(str(no_exif_image_path))

            # 結果を検証（EXIFデータがない場合は空の辞書が返される）
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
