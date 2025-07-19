#!/usr/bin/env python3
"""
地図ビューアーモジュールの単体テスト
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# プロジェクトルートをPythonパスに追加
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.map_viewer import MapViewer
from src.core.logger import get_logger


class TestMapViewer(unittest.TestCase):
    """MapViewerのテストクラス"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        # QApplicationを初期化
        from PyQt6.QtWidgets import QApplication
        import sys
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    @classmethod
    def tearDownClass(cls):
        """テストクラス全体のクリーンアップ"""
        if cls.app:
            cls.app.quit()

    def setUp(self):
        """テスト前の準備"""
        self.logger = get_logger(__name__)

        # テスト用の一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()

        # QApplicationとQWebEngineViewをモック
        self.qapp_patcher = patch("PyQt6.QtWidgets.QApplication")
        self.webview_patcher = patch("PyQt6.QtWebEngineWidgets.QWebEngineView")
        self.webpage_patcher = patch("PyQt6.QtWebEngineCore.QWebEnginePage")

        self.mock_qapp = self.qapp_patcher.start()
        self.mock_webview = self.webview_patcher.start()
        self.mock_webpage = self.webpage_patcher.start()

        # QApplicationインスタンスをモック
        self.mock_qapp.instance.return_value = self.app

        # MapViewerの初期化は各テストで行う
        self.map_viewer = None

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # パッチャーを停止
        self.qapp_patcher.stop()
        self.webview_patcher.stop()
        self.webpage_patcher.stop()

        # 一時ディレクトリを削除
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        """初期化テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # 基本的な機能をテスト
        self.assertIsNotNone(map_viewer)
        self.assertIsNotNone(map_viewer.logger)

    def test_add_marker_with_valid_data(self):
        """有効なデータでのマーカー追加テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # マーカーデータ
        marker_id = "test_marker"
        coordinates = (35.6762, 139.6503)  # 東京の座標
        title = "Test Location"
        description = "Test Description"

        with patch("folium.Marker") as mock_folium_marker:
            mock_marker = MagicMock()
            mock_folium_marker.return_value = mock_marker

            # マーカーを追加
            result = map_viewer.add_marker(marker_id, coordinates, title, description)

            # 結果を検証
            self.assertTrue(result)
            mock_folium_marker.assert_called_once()

    def test_add_marker_with_invalid_coordinates(self):
        """無効な座標でのマーカー追加テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # 無効な座標
        marker_id = "invalid_marker"
        coordinates = (200.0, 400.0)  # 無効な座標
        title = "Invalid Location"
        description = "Invalid Description"

        # マーカーを追加
        result = map_viewer.add_marker(marker_id, coordinates, title, description)

        # 結果を検証（エラーハンドリングによりFalseが返される可能性）
        self.assertFalse(result)

    def test_remove_marker(self):
        """マーカー削除テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # まず有効なマーカーを追加
        marker_id = "test_marker"
        coordinates = (35.6762, 139.6503)
        title = "Test Location"
        description = "Test Description"

        with patch("folium.Marker") as mock_folium_marker:
            mock_marker = MagicMock()
            mock_folium_marker.return_value = mock_marker

            # マーカーを追加
            map_viewer.add_marker(marker_id, coordinates, title, description)

            # マーカーを削除
            result = map_viewer.remove_marker(marker_id)

            # 結果を検証
            self.assertTrue(result)

    def test_clear_markers(self):
        """マーカークリアテスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # マーカーをクリア
        map_viewer.clear_markers()

        # マーカーが空であることを確認
        markers = map_viewer.get_markers()
        self.assertEqual(len(markers), 0)

    def test_set_center(self):
        """地図中心設定テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # 新しい中心座標
        new_center = (34.0522, -118.2437)  # ロサンゼルス

        # 中心を設定
        map_viewer.set_center(new_center)

        # 中心が設定されたことを確認
        current_center = map_viewer.get_center()
        self.assertEqual(current_center, new_center)

    def test_set_zoom(self):
        """ズームレベル設定テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # 新しいズームレベル
        new_zoom = 15

        # ズームレベルを設定
        map_viewer.set_zoom(new_zoom)

        # ズームレベルが設定されたことを確認
        current_zoom = map_viewer.get_zoom()
        self.assertEqual(current_zoom, new_zoom)

    def test_get_markers(self):
        """マーカー取得テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # マーカー情報を取得
        markers = map_viewer.get_markers()

        # 辞書が返されることを確認
        self.assertIsInstance(markers, dict)

    def test_map_viewer_with_qapplication(self):
        """QApplication初期化後のMapViewerテスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # 基本的な機能をテスト
        self.assertIsNotNone(map_viewer)
        self.assertIsNotNone(map_viewer.logger)

        # マーカー追加テスト
        marker_id = "test_marker"
        coordinates = (35.6762, 139.6503)  # 東京の座標
        title = "Test Location"
        description = "Test Description"

        result = map_viewer.add_marker(marker_id, coordinates, title, description)
        self.assertTrue(result)

        # マーカー情報を取得
        markers = map_viewer.get_markers()
        self.assertIn(marker_id, markers)

    def test_map_viewer_center_and_zoom(self):
        """地図の中心とズーム設定テスト"""
        # MapViewerを初期化
        map_viewer = MapViewer()

        # 中心座標を設定
        new_center = (34.0522, -118.2437)  # ロサンゼルス
        map_viewer.set_center(new_center)

        # 中心が設定されたことを確認
        current_center = map_viewer.get_center()
        self.assertEqual(current_center, new_center)

        # ズームレベルを設定
        new_zoom = 15
        map_viewer.set_zoom(new_zoom)

        # ズームレベルが設定されたことを確認
        current_zoom = map_viewer.get_zoom()
        self.assertEqual(current_zoom, new_zoom)


if __name__ == "__main__":
    unittest.main()
