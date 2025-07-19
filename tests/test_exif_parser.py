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
        # テスト用の画像ファイルパス（実際のファイルは存在しないが、モックでテスト）
        test_image_path = os.path.join(self.test_dir, "test_image.jpg")

        # モックのEXIFデータ
        mock_exif_data = {
            "EXIF": {
                "DateTimeOriginal": "2023:01:01 12:00:00",
                "Make": "Test Camera",
                "Model": "Test Model",
                "FNumber": (5, 1),
                "ISOSpeedRatings": 100,
                "FocalLength": (50, 1),
            },
            "GPS": {
                "GPSLatitude": [(35, 1), (40, 1), (0, 1)],
                "GPSLongitude": [(139, 1), (45, 1), (0, 1)],
                "GPSLatitudeRef": "N",
                "GPSLongitudeRef": "E",
            },
        }

        with patch("exifread.process_file") as mock_process_file:
            mock_process_file.return_value = mock_exif_data

            # EXIFデータを解析
            result = self.exif_parser.parse_exif(test_image_path)

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertIn("make", result)
            self.assertIn("model", result)
            self.assertIn("gps", result)

            # カメラ情報の検証
            self.assertEqual(result["make"], "Test Camera")
            self.assertEqual(result["model"], "Test Model")
            self.assertEqual(result["f_number"], "5/1")
            self.assertEqual(result["iso"], 100)
            self.assertEqual(result["focal_length"], "50/1")

            # GPS座標の検証
            gps_data = result["gps"]
            self.assertIsNotNone(gps_data)
            self.assertIn("latitude", gps_data)
            self.assertIn("longitude", gps_data)

    def test_parse_exif_data_with_no_exif(self):
        """EXIFデータがない画像ファイルのテスト"""
        test_image_path = os.path.join(self.test_dir, "no_exif_image.jpg")

        with patch("exifread.process_file") as mock_process_file:
            mock_process_file.return_value = {}

            # EXIFデータを解析
            result = self.exif_parser.parse_exif(test_image_path)

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertEqual(result, {})

    def test_parse_exif_data_with_gps_only(self):
        """GPS座標のみの画像ファイルのテスト"""
        test_image_path = os.path.join(self.test_dir, "gps_only_image.jpg")

        mock_exif_data = {
            "GPS": {
                "GPSLatitude": [(35, 1), (40, 1), (0, 1)],
                "GPSLongitude": [(139, 1), (45, 1), (0, 1)],
                "GPSLatitudeRef": "N",
                "GPSLongitudeRef": "E",
            }
        }

        with patch("exifread.process_file") as mock_process_file:
            mock_process_file.return_value = mock_exif_data

            # EXIFデータを解析
            result = self.exif_parser.parse_exif(test_image_path)

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertIn("gps", result)
            self.assertNotIn("make", result)
            self.assertNotIn("model", result)

    def test_parse_exif_data_with_invalid_file(self):
        """無効なファイルパスのテスト"""
        invalid_path = os.path.join(self.test_dir, "nonexistent.jpg")

        with patch("exifread.process_file") as mock_process_file:
            mock_process_file.side_effect = FileNotFoundError("File not found")

            # EXIFデータを解析
            result = self.exif_parser.parse_exif(invalid_path)

            # 結果を検証
            self.assertIsNotNone(result)
            self.assertEqual(result, {})

    def test_get_gps_coordinates(self):
        """GPS座標取得のテスト"""
        # テスト用の画像ファイルパス
        test_image_path = os.path.join(self.test_dir, "test_image.jpg")

        # モックのEXIFデータ
        mock_exif_data = {
            "EXIF": {
                "DateTimeOriginal": "2023:01:01 12:00:00",
            },
            "GPS": {
                "GPSLatitude": [(35, 1), (40, 1), (0, 1)],
                "GPSLongitude": [(139, 1), (45, 1), (0, 1)],
                "GPSLatitudeRef": "N",
                "GPSLongitudeRef": "E",
            },
        }

        with patch("exifread.process_file") as mock_process_file:
            mock_process_file.return_value = mock_exif_data

            # GPS座標を取得
            coords = self.exif_parser.get_gps_coordinates(test_image_path)
            self.assertIsNotNone(coords)
            if coords is not None:  # 型チェック
                self.assertEqual(len(coords), 2)
                self.assertAlmostEqual(coords[0], 35.666667, places=5)
                self.assertAlmostEqual(coords[1], 139.75, places=5)

    def test_get_camera_info(self):
        """カメラ情報取得のテスト"""
        # テスト用の画像ファイルパス
        test_image_path = os.path.join(self.test_dir, "test_image.jpg")

        # モックのEXIFデータ
        mock_exif_data = {
            "EXIF": {
                "DateTimeOriginal": "2023:01:01 12:00:00",
            },
            "Image": {
                "Make": "Test Camera",
                "Model": "Test Model",
            },
        }

        with patch("exifread.process_file") as mock_process_file:
            mock_process_file.return_value = mock_exif_data

            # カメラ情報を取得
            camera_info = self.exif_parser.get_camera_info(test_image_path)
            self.assertIsNotNone(camera_info)
            self.assertEqual(camera_info["make"], "Test Camera")
            self.assertEqual(camera_info["model"], "Test Model")


if __name__ == "__main__":
    unittest.main()
