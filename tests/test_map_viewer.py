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

    def setUp(self):
        """テスト前の準備"""
        self.logger = get_logger(__name__)

        # テスト用の一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()

        # QApplicationとQWebEngineViewをモック
        self.qapp_patcher = patch("PyQt6.QtWidgets.QApplication")
        self.webview_patcher = patch("PyQt6.QtWebEngineWidgets.QWebEngineView")

        self.mock_qapp = self.qapp_patcher.start()
        self.mock_webview = self.webview_patcher.start()

        # QApplicationインスタンスをモック
        self.mock_qapp.instance.return_value = MagicMock()

        # MapViewerの初期化
        self.map_viewer = MapViewer()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # パッチャーを停止
        self.qapp_patcher.stop()
        self.webview_patcher.stop()

        # 一時ディレクトリを削除
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initialization(self):
        """初期化テスト"""
        self.assertIsNotNone(self.map_viewer)
        self.assertIsNotNone(self.map_viewer.logger)

    def test_add_marker_with_valid_data(self):
        """有効なデータでのマーカー追加テスト"""
        # マーカーデータ
        marker_id = "test_marker"
        coordinates = (35.6762, 139.6503)  # 東京の座標
        title = "Test Location"
        description = "Test Description"

        with patch("folium.Marker") as mock_folium_marker:
            mock_marker = MagicMock()
            mock_folium_marker.return_value = mock_marker

            # マーカーを追加
            result = self.map_viewer.add_marker(
                marker_id, coordinates, title, description
            )

            # 結果を検証
            self.assertTrue(result)
            mock_folium_marker.assert_called_once()

    def test_add_marker_with_invalid_coordinates(self):
        """無効な座標でのマーカー追加テスト"""
        # 無効な座標
        marker_id = "invalid_marker"
        coordinates = (200.0, 400.0)  # 無効な座標
        title = "Invalid Location"
        description = "Invalid Description"

        # マーカーを追加
        result = self.map_viewer.add_marker(marker_id, coordinates, title, description)

        # 結果を検証（エラーハンドリングによりFalseが返される可能性）
        self.assertFalse(result)

    def test_remove_marker(self):
        """マーカー削除テスト"""
        # まず有効なマーカーを追加
        marker_id = "test_marker"
        coordinates = (35.6762, 139.6503)
        title = "Test Location"
        description = "Test Description"

        with patch("folium.Marker") as mock_folium_marker:
            mock_marker = MagicMock()
            mock_folium_marker.return_value = mock_marker

            # マーカーを追加
            self.map_viewer.add_marker(marker_id, coordinates, title, description)

            # マーカーを削除
            result = self.map_viewer.remove_marker(marker_id)

            # 結果を検証
            self.assertTrue(result)

    def test_clear_markers(self):
        """マーカークリアテスト"""
        # マーカーをクリア
        self.map_viewer.clear_markers()

        # マーカーが空であることを確認
        markers = self.map_viewer.get_markers()
        self.assertEqual(len(markers), 0)

    def test_set_center(self):
        """地図中心設定テスト"""
        # 新しい中心座標
        new_center = (34.0522, -118.2437)  # ロサンゼルス

        # 中心を設定
        self.map_viewer.set_center(new_center)

        # 中心が設定されたことを確認
        current_center = self.map_viewer.get_center()
        self.assertEqual(current_center, new_center)

    def test_set_zoom(self):
        """ズームレベル設定テスト"""
        # 新しいズームレベル
        new_zoom = 15

        # ズームレベルを設定
        self.map_viewer.set_zoom(new_zoom)

        # ズームレベルが設定されたことを確認
        current_zoom = self.map_viewer.get_zoom()
        self.assertEqual(current_zoom, new_zoom)

    def test_get_markers(self):
        """マーカー取得テスト"""
        # マーカー情報を取得
        markers = self.map_viewer.get_markers()

        # 辞書が返されることを確認
        self.assertIsInstance(markers, dict)


if __name__ == "__main__":
    unittest.main()
