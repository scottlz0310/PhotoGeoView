#!/usr/bin/env python3
"""
PhotoGeoView システムテスト
エンドツーエンドのシステムテストを実行する
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.core.logger import setup_logging, get_logger
from src.core.settings import get_settings
from src.ui.main_window import MainWindow
from src.modules.exif_parser import ExifParser
from src.modules.map_viewer import MapViewer
from src.modules.image_loader import ImageLoader
from src.ui.theme_manager import ThemeManager


class SystemTest(unittest.TestCase):
    """PhotoGeoView システムテストクラス"""

    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        # ログ設定
        setup_logging()
        cls.logger = get_logger(__name__)

        # QApplicationの初期化
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

        # テスト用の一時ディレクトリを作成
        cls.test_dir = tempfile.mkdtemp(prefix="photogeoview_test_")
        cls.logger.info(f"テスト用ディレクトリを作成: {cls.test_dir}")

        # テスト用の画像ファイルを作成
        cls._create_test_images()

        # テスト用の設定を初期化
        cls._setup_test_config()

    @classmethod
    def tearDownClass(cls):
        """テストクラスのクリーンアップ"""
        # テスト用ディレクトリを削除
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
            cls.logger.info(f"テスト用ディレクトリを削除: {cls.test_dir}")

    @classmethod
    def _create_test_images(cls):
        """テスト用の画像ファイルを作成"""
        # テスト用の画像ディレクトリを作成
        test_images_dir = Path(cls.test_dir) / "test_images"
        test_images_dir.mkdir(exist_ok=True)

        # サンプル画像ファイルを作成（実際の画像ファイルをコピー）
        sample_images = [
            "tests/test_data/images/sample1.jpg",
            "tests/test_data/images/sample2.jpg",
            "tests/test_data/images/sample3.jpg",
        ]

        for i, sample_path in enumerate(sample_images):
            if os.path.exists(sample_path):
                dest_path = test_images_dir / f"test_image_{i+1}.jpg"
                shutil.copy2(sample_path, dest_path)
                cls.logger.info(f"テスト画像を作成: {dest_path}")
            else:
                # PyQt6を使用してテスト画像を作成
                try:
                    from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor
                    from PyQt6.QtCore import QSize

                    # 100x100のテスト画像を作成
                    image = QImage(QSize(100, 100), QImage.Format.Format_RGB888)
                    image.fill(QColor(128, 128, 128))  # グレーで塗りつぶし
                    
                    dest_path = test_images_dir / f"test_image_{i+1}.jpg"
                    success = image.save(str(dest_path), "JPEG", 90)
                    
                    if success:
                        cls.logger.info(f"テスト画像を作成: {dest_path}")
                    else:
                        cls.logger.warning(f"テスト画像の作成に失敗: {dest_path}")
                        # フォールバック: ダミーファイルを作成
                        dest_path = test_images_dir / f"test_image_{i+1}.jpg"
                        with open(dest_path, "wb") as f:
                            # 最小限のJPEGヘッダーを作成
                            f.write(b'\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00')
                            f.write(b'\x00' * 1000)  # パディング
                        cls.logger.info(f"ダミーテスト画像を作成: {dest_path}")
                        
                except ImportError:
                    # PyQt6が利用できない場合はダミーファイルを作成
                    dest_path = test_images_dir / f"test_image_{i+1}.jpg"
                    with open(dest_path, "wb") as f:
                        f.write(b"\xff\xd8\xff\xe0")  # JPEGヘッダー
                    cls.logger.info(f"ダミー画像を作成: {dest_path}")

    @classmethod
    def _setup_test_config(cls):
        """テスト用の設定を初期化"""
        # テスト用の設定ファイルを作成
        test_config = {
            "theme": "dark",
            "window_size": [1200, 800],
            "splitter_sizes": [400, 800],
            "thumbnail_size": 100,
            "auto_load_images": True,
            "show_exif_info": True,
            "map_zoom_level": 13,
        }

        config_path = Path(cls.test_dir) / "test_config.json"
        import json

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)

    def setUp(self):
        """各テストケースの初期化"""
        self.logger.info(f"テストケース開始: {self._testMethodName}")

        # メインウィンドウを作成
        self.main_window = MainWindow()
        self.main_window.show()

        # イベントループを処理
        QTest.qWait(100)

    def tearDown(self):
        """各テストケースのクリーンアップ"""
        if hasattr(self, "main_window"):
            self.main_window.close()
            self.main_window.deleteLater()

        # イベントループを処理
        QTest.qWait(100)

        self.logger.info(f"テストケース終了: {self._testMethodName}")

    def test_01_application_startup(self):
        """アプリケーション起動テスト"""
        self.logger.info("アプリケーション起動テストを開始")

        # メインウィンドウが正常に表示されているか確認
        self.assertTrue(self.main_window.isVisible())
        self.assertEqual(self.main_window.windowTitle(), "PhotoGeoView")

        # 基本的なウィジェットが存在するか確認
        self.assertIsNotNone(self.main_window.central_widget)
        self.assertIsNotNone(self.main_window.main_splitter)
        self.assertIsNotNone(self.main_window.status_bar)

        self.logger.info("アプリケーション起動テスト完了")

    def test_02_theme_system(self):
        """テーマシステムテスト"""
        self.logger.info("テーマシステムテストを開始")

        # テーママネージャーが正常に動作するか確認
        theme_manager = self.main_window.theme_manager
        self.assertIsNotNone(theme_manager)

        # 利用可能なテーマを取得
        available_themes = theme_manager.get_available_themes()
        self.assertIsInstance(available_themes, list)
        self.assertGreater(len(available_themes), 0)

        # テーマ切り替えをテスト
        if len(available_themes) > 1:
            new_theme = (
                available_themes[1]
                if available_themes[0] == theme_manager.get_current_theme()
                else available_themes[0]
            )
            theme_manager.apply_theme(new_theme)

            # テーマが変更されたか確認
            QTest.qWait(100)
            self.assertEqual(theme_manager.get_current_theme(), new_theme)

        self.logger.info("テーマシステムテスト完了")

    def test_03_folder_navigation(self):
        """フォルダナビゲーションテスト"""
        self.logger.info("フォルダナビゲーションテストを開始")

        # フォルダ選択ボタンが存在するか確認（ヘッダーエリアが初期化されている場合）
        if hasattr(self.main_window, "folder_button"):
            self.assertIsNotNone(self.main_window.folder_button)

            # フォルダ選択ダイアログをモック
            with patch(
                "PyQt6.QtWidgets.QFileDialog.getExistingDirectory"
            ) as mock_dialog:
                mock_dialog.return_value = self.test_dir

                # フォルダ選択ボタンをクリック
                QTest.mouseClick(
                    self.main_window.folder_button, Qt.MouseButton.LeftButton
                )
                QTest.qWait(100)

                # アドレスバーが更新されたか確認
                if hasattr(self.main_window, "address_edit"):
                    self.assertIn(self.test_dir, self.main_window.address_edit.text())
        else:
            # ヘッダーエリアが初期化されていない場合はスキップ
            self.logger.info(
                "ヘッダーエリアが初期化されていないため、フォルダナビゲーションテストをスキップ"
            )

        self.logger.info("フォルダナビゲーションテスト完了")

    def test_04_image_loading(self):
        """画像読み込みテスト"""
        self.logger.info("画像読み込みテストを開始")

        # テスト用の画像ディレクトリを設定
        test_images_dir = Path(self.test_dir) / "test_images"

        # フォルダナビゲーターにディレクトリを設定
        if hasattr(self.main_window, "folder_navigator"):
            self.main_window.folder_navigator.set_directory(str(test_images_dir))
            QTest.qWait(200)

            # サムネイルグリッドに画像が表示されているか確認
            if hasattr(self.main_window, "thumbnail_grid"):
                # サムネイルグリッドの状態を確認
                self.assertIsNotNone(self.main_window.thumbnail_grid)

        self.logger.info("画像読み込みテスト完了")

    def test_05_exif_parsing(self):
        """EXIF解析テスト"""
        self.logger.info("EXIF解析テストを開始")

        # EXIFパーサーをテスト
        exif_parser = ExifParser()

        # テスト用の画像ファイルを解析
        test_images_dir = Path(self.test_dir) / "test_images"
        image_files = list(test_images_dir.glob("*.jpg"))

        if image_files:
            test_image = str(image_files[0])

            # EXIF情報を解析
            exif_data = exif_parser.parse_exif(test_image)
            self.assertIsInstance(exif_data, dict)

            # GPS情報を抽出
            gps_data = exif_parser.get_gps_coordinates(test_image)
            # GPS情報がない場合もあるので、Noneまたは辞書であることを確認
            self.assertTrue(gps_data is None or isinstance(gps_data, tuple))

        self.logger.info("EXIF解析テスト完了")

    def test_06_map_display(self):
        """地図表示テスト"""
        self.logger.info("地図表示テストを開始")

        # 地図ビューアーが存在するか確認
        if hasattr(self.main_window, "map_viewer"):
            map_viewer = self.main_window.map_viewer
            self.assertIsNotNone(map_viewer)

            # 地図の初期化を確認
            self.assertTrue(hasattr(map_viewer, "web_view"))

        self.logger.info("地図表示テスト完了")

    def test_07_ui_interactions(self):
        """UI操作テスト"""
        self.logger.info("UI操作テストを開始")

        # ナビゲーションボタンのテスト
        if hasattr(self.main_window, "back_button"):
            QTest.mouseClick(self.main_window.back_button, Qt.MouseButton.LeftButton)
            QTest.qWait(100)

        if hasattr(self.main_window, "forward_button"):
            QTest.mouseClick(self.main_window.forward_button, Qt.MouseButton.LeftButton)
            QTest.qWait(100)

        if hasattr(self.main_window, "up_button"):
            QTest.mouseClick(self.main_window.up_button, Qt.MouseButton.LeftButton)
            QTest.qWait(100)

        # テーマボタンのテスト
        if hasattr(self.main_window, "theme_button"):
            QTest.mouseClick(self.main_window.theme_button, Qt.MouseButton.LeftButton)
            QTest.qWait(100)

        self.logger.info("UI操作テスト完了")

    def test_08_performance_test(self):
        """パフォーマンステスト"""
        self.logger.info("パフォーマンステストを開始")

        # 大量の画像ファイルを処理するテスト
        test_images_dir = Path(self.test_dir) / "test_images"

        # 画像ローダーをテスト
        image_loader = ImageLoader()

        # 複数の画像を同時に読み込むテスト
        image_files = list(test_images_dir.glob("*.jpg"))

        if image_files:
            start_time = time.time()

            for image_file in image_files[:5]:  # 最大5個の画像をテスト
                try:
                    # 画像読み込み
                    image_loader.load_image(str(image_file))
                    QTest.qWait(50)  # 短い待機時間
                except Exception as e:
                    self.logger.warning(f"画像読み込みエラー: {e}")

            end_time = time.time()
            processing_time = end_time - start_time

            # 処理時間が妥当な範囲内か確認（5秒以内）
            self.assertLess(processing_time, 5.0)
            self.logger.info(f"画像処理時間: {processing_time:.2f}秒")

        self.logger.info("パフォーマンステスト完了")

    def test_09_error_handling(self):
        """エラーハンドリングテスト"""
        self.logger.info("エラーハンドリングテストを開始")

        # 存在しないファイルへのアクセス
        non_existent_file = "/path/to/non/existent/file.jpg"

        # EXIFパーサーでエラーハンドリングをテスト
        exif_parser = ExifParser()
        try:
            exif_data = exif_parser.parse_exif(non_existent_file)
            # エラーが適切に処理されることを確認
            self.assertIsInstance(exif_data, dict)
        except Exception as e:
            # 例外が発生した場合も正常
            self.logger.info(f"期待されるエラー: {e}")

        # 画像ローダーでエラーハンドリングをテスト
        image_loader = ImageLoader()
        try:
            result = image_loader.load_image(non_existent_file)
            # エラーが適切に処理されることを確認
            self.assertIsInstance(result, (dict, type(None)))
        except Exception as e:
            # 例外が発生した場合も正常
            self.logger.info(f"期待されるエラー: {e}")

        self.logger.info("エラーハンドリングテスト完了")

    def test_10_integration_workflow(self):
        """統合ワークフローテスト"""
        self.logger.info("統合ワークフローテストを開始")

        # 完全なワークフローをテスト
        test_images_dir = Path(self.test_dir) / "test_images"
        image_files = list(test_images_dir.glob("*.jpg"))

        if image_files:
            test_image = str(image_files[0])

            # 1. EXIF解析
            exif_parser = ExifParser()
            exif_data = exif_parser.parse_exif(test_image)
            self.assertIsInstance(exif_data, dict)

            # 2. GPS座標抽出
            gps_data = exif_parser.get_gps_coordinates(test_image)

            # 3. 地図表示（GPSデータがある場合）
            if gps_data and hasattr(self.main_window, "map_viewer"):
                map_viewer = self.main_window.map_viewer
                # 地図にマーカーを追加
                if hasattr(map_viewer, "add_marker"):
                    latitude, longitude = gps_data
                    map_viewer.add_marker(latitude, longitude, "テスト画像")

            # 4. 画像表示
            image_loader = ImageLoader()
            image_data = image_loader.load_image(test_image)
            # ImageLoaderはQPixmapを返す（Noneの場合は読み込み失敗）
            if image_data is not None:
                from PyQt6.QtGui import QPixmap
                self.assertIsInstance(image_data, QPixmap)
            else:
                # 画像読み込みに失敗した場合でもテストは続行
                self.logger.warning(f"画像読み込みに失敗: {test_image}")

            # 4.5. 画像情報取得
            image_info = image_loader.get_image_info(test_image)
            self.assertIsInstance(image_info, dict)

            # 5. UI更新
            QTest.qWait(200)

            # ステータスバーにメッセージが表示されているか確認
            if hasattr(self.main_window, "status_bar"):
                self.assertIsNotNone(self.main_window.status_bar.currentMessage())

        self.logger.info("統合ワークフローテスト完了")

    def test_11_memory_management(self):
        """メモリ管理テスト"""
        self.logger.info("メモリ管理テストを開始")

        # 大量の画像を読み込んでメモリ使用量をテスト
        test_images_dir = Path(self.test_dir) / "test_images"
        image_files = list(test_images_dir.glob("*.jpg"))

        if image_files:
            image_loader = ImageLoader()

            # 複数の画像を読み込む
            loaded_images = []
            for image_file in image_files[:3]:
                try:
                    image_data = image_loader.load_image(str(image_file))
                    loaded_images.append(image_data)
                    QTest.qWait(50)
                except Exception as e:
                    self.logger.warning(f"画像読み込みエラー: {e}")

            # 画像データが正常に読み込まれているか確認
            self.assertGreater(len(loaded_images), 0)

            # メモリクリーンアップをテスト
            loaded_images.clear()
            QTest.qWait(100)

        self.logger.info("メモリ管理テスト完了")

    def test_12_configuration_persistence(self):
        """設定永続化テスト"""
        self.logger.info("設定永続化テストを開始")

        # 設定の読み込み
        settings = get_settings()
        self.assertIsNotNone(settings)

        # 設定の変更と保存をテスト
        original_theme = settings.get("ui.theme_manager.current_theme", "dark")
        new_theme = "light" if original_theme == "dark" else "dark"

        # 設定を変更
        settings.set("ui.theme_manager.current_theme", new_theme)

        # 設定が変更されたか確認
        self.assertEqual(settings.get("ui.theme_manager.current_theme"), new_theme)

        # 設定を元に戻す
        settings.set("ui.theme_manager.current_theme", original_theme)

        self.logger.info("設定永続化テスト完了")


def run_system_tests():
    """システムテストを実行"""
    # テストスイートを作成
    test_suite = unittest.TestLoader().loadTestsFromTestCase(SystemTest)

    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 結果をログに出力
    logger = get_logger(__name__)
    logger.info(
        f"システムテスト結果: {result.testsRun}個実行, {len(result.failures)}個失敗, {len(result.errors)}個エラー"
    )

    return result.wasSuccessful()


if __name__ == "__main__":
    # システムテストを実行
    success = run_system_tests()
    sys.exit(0 if success else 1)
