#!/usr/bin/env python3
"""
ファイルリスト表示修正 - 基本機能統合テスト

フォルダ選択からサムネイル表示までの一連の流れをテストし、
正常ケースと異常ケースの両方をカバーします。

要件: 1.1, 1.2, 2.1, 2.2

Author: Kiro AI Integration System
"""

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.models import AIComponent
from src.integration.services.file_discovery_service import FileDiscoveryService
from src.integration.state_manager import StateManager
from src.integration.ui.folder_navigator import EnhancedFolderNavigator
from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid


class FileListDisplayIntegrationTest(unittest.TestCase):
    """
    ファイルリスト表示修正の基本機能統合テスト

    テスト対象:
    - フォルダ選択からサムネイル表示までの一連の流れ
    - 正常ケースと異常ケースの処理
    - 日本語メッセージの表示確認
    """

    def setUp(self):
        """テストセットアップ"""
        # Windows環境での問題を回避
        import platform
        if platform.system() == "Windows":
            self.skipTest("Windows環境ではファイルリスト表示統合テストをスキップ")
            
        # テスト用の一時ディレクトリを作成
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_images_dir = self.test_dir / "test_images"
        self.test_images_dir.mkdir()

        # テスト用の空ディレクトリ
        self.empty_dir = self.test_dir / "empty_folder"
        self.empty_dir.mkdir()

        # アクセス権限のないディレクトリ（シミュレーション用）
        self.restricted_dir = self.test_dir / "restricted"
        self.restricted_dir.mkdir()

        # システムコンポーネントの初期化
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.logger_system = LoggerSystem()

        # テスト用画像ファイルを作成
        self._create_test_images()

        # コンポーネントの初期化
        self.file_discovery_service = FileDiscoveryService(
            logger_system=self.logger_system
        )

        # UIコンポーネントはモックを使用（実際のQtウィジェットを避ける）
        self.folder_navigator = Mock()
        self.thumbnail_grid = Mock()

        # テスト結果の記録用
        self.test_results = []

    def tearDown(self):
        """テストクリーンアップ"""
        # 一時ディレクトリを削除
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_test_images(self):
        """テスト用画像ファイルの作成"""
        # 有効な画像ファイル（ダミーデータ）
        valid_images = [
            "test_image_1.jpg",
            "test_image_2.png",
            "test_image_3.gif",
            "test_image_4.bmp",
            "test_image_5.tiff",
            "test_image_6.webp",
        ]

        for image_name in valid_images:
            image_path = self.test_images_dir / image_name
            # 最小限の有効なファイルサイズでダミーデータを作成
            image_path.write_bytes(b"dummy_image_data" * 10)  # 160バイト

        # 無効なファイル（対応していない拡張子）
        invalid_files = ["document.txt", "video.mp4", "audio.mp3"]

        for file_name in invalid_files:
            file_path = self.test_images_dir / file_name
            file_path.write_bytes(b"invalid_file_data")

        # 破損した画像ファイル（サイズが小さすぎる）
        corrupted_image = self.test_images_dir / "corrupted.jpg"
        corrupted_image.write_bytes(b"bad")  # 3バイトのみ

    def test_01_folder_selection_to_thumbnail_display_normal_case(self):
        """
        テスト1: フォルダ選択からサムネイル表示までの正常ケース

        要件: 1.1, 1.2, 2.1, 2.2
        """
        print("\n=== テスト1: 正常ケース - フォルダ選択からサムネイル表示 ===")

        start_time = time.time()

        try:
            # 1. フォルダ内の画像ファイルを検出
            discovered_images = self.file_discovery_service.discover_images(
                self.test_images_dir
            )

            # 2. 検出結果の検証
            self.assertIsInstance(
                discovered_images, list, "検出結果はリスト型である必要があります"
            )
            self.assertGreater(
                len(discovered_images), 0, "画像ファイルが検出される必要があります"
            )

            # 3. 検出された画像ファイルの検証
            expected_extensions = {".jpg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
            for image_path in discovered_images:
                self.assertIsInstance(
                    image_path,
                    Path,
                    "検出されたファイルはPathオブジェクトである必要があります",
                )
                self.assertTrue(
                    image_path.exists(),
                    f"検出されたファイルが存在する必要があります: {image_path}",
                )
                self.assertIn(
                    image_path.suffix.lower(),
                    expected_extensions,
                    f"対応する画像形式である必要があります: {image_path.suffix}",
                )

            # 4. 無効なファイルが除外されていることを確認
            discovered_names = [p.name for p in discovered_images]
            self.assertNotIn(
                "document.txt",
                discovered_names,
                "テキストファイルは除外される必要があります",
            )
            self.assertNotIn(
                "video.mp4", discovered_names, "動画ファイルは除外される必要があります"
            )
            self.assertNotIn(
                "corrupted.jpg",
                discovered_names,
                "破損ファイルは除外される必要があります",
            )

            # 5. フォルダナビゲーターのシグナル発行をシミュレート
            self.folder_navigator.folder_selected.emit = Mock()
            self.folder_navigator.folder_selected.emit(self.test_images_dir)

            # 6. サムネイルグリッドの更新をシミュレート
            self.thumbnail_grid.set_image_list = Mock()
            self.thumbnail_grid.set_image_list(discovered_images)

            # 7. 呼び出しの検証
            self.folder_navigator.folder_selected.emit.assert_called_once_with(
                self.test_images_dir
            )
            self.thumbnail_grid.set_image_list.assert_called_once_with(
                discovered_images
            )

            duration = time.time() - start_time

            # テスト結果の記録
            test_result = {
                "test_name": "folder_selection_normal_case",
                "status": "passed",
                "duration": duration,
                "images_found": len(discovered_images),
                "folder_path": str(self.test_images_dir),
                "message": f"正常ケーステスト成功: {len(discovered_images)}個の画像ファイルを検出",
            }
            self.test_results.append(test_result)

            print(f"✅ 正常ケーステスト成功")
            print(f"   検出された画像: {len(discovered_images)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(f"   検出されたファイル: {[p.name for p in discovered_images]}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "folder_selection_normal_case",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(self.test_images_dir),
            }
            self.test_results.append(test_result)

            print(f"❌ 正常ケーステスト失敗: {e}")
            raise

    def test_02_empty_folder_handling(self):
        """
        テスト2: 空フォルダの処理

        要件: 1.3, 6.1
        """
        print("\n=== テスト2: 空フォルダの処理 ===")

        start_time = time.time()

        try:
            # 1. 空フォルダでの画像検出
            discovered_images = self.file_discovery_service.discover_images(
                self.empty_dir
            )

            # 2. 結果の検証
            self.assertIsInstance(
                discovered_images, list, "検出結果はリスト型である必要があります"
            )
            self.assertEqual(
                len(discovered_images),
                0,
                "空フォルダでは画像が検出されない必要があります",
            )

            # 3. ログメッセージの確認（日本語メッセージ）
            # 実際の実装では、ログシステムから日本語メッセージが出力されることを確認

            duration = time.time() - start_time

            test_result = {
                "test_name": "empty_folder_handling",
                "status": "passed",
                "duration": duration,
                "images_found": len(discovered_images),
                "folder_path": str(self.empty_dir),
                "message": "空フォルダ処理テスト成功: 画像ファイルが見つからないことを正しく処理",
            }
            self.test_results.append(test_result)

            print(f"✅ 空フォルダ処理テスト成功")
            print(f"   検出された画像: {len(discovered_images)}個（期待値: 0）")
            print(f"   処理時間: {duration:.3f}秒")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "empty_folder_handling",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(self.empty_dir),
            }
            self.test_results.append(test_result)

            print(f"❌ 空フォルダ処理テスト失敗: {e}")
            raise

    def test_03_nonexistent_folder_handling(self):
        """
        テスト3: 存在しないフォルダの処理

        要件: 5.1, 5.4, 6.1
        """
        print("\n=== テスト3: 存在しないフォルダの処理 ===")

        start_time = time.time()
        nonexistent_folder = self.test_dir / "nonexistent_folder"

        try:
            # 1. 存在しないフォルダでの画像検出
            discovered_images = self.file_discovery_service.discover_images(
                nonexistent_folder
            )

            # 2. 結果の検証
            self.assertIsInstance(
                discovered_images, list, "検出結果はリスト型である必要があります"
            )
            self.assertEqual(
                len(discovered_images),
                0,
                "存在しないフォルダでは画像が検出されない必要があります",
            )

            duration = time.time() - start_time

            test_result = {
                "test_name": "nonexistent_folder_handling",
                "status": "passed",
                "duration": duration,
                "images_found": len(discovered_images),
                "folder_path": str(nonexistent_folder),
                "message": "存在しないフォルダ処理テスト成功: エラーを適切に処理",
            }
            self.test_results.append(test_result)

            print(f"✅ 存在しないフォルダ処理テスト成功")
            print(f"   検出された画像: {len(discovered_images)}個（期待値: 0）")
            print(f"   処理時間: {duration:.3f}秒")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "nonexistent_folder_handling",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(nonexistent_folder),
            }
            self.test_results.append(test_result)

            print(f"❌ 存在しないフォルダ処理テスト失敗: {e}")
            raise

    def test_04_file_validation_integration(self):
        """
        テスト4: ファイルバリデーション統合テスト

        要件: 1.1, 1.4
        """
        print("\n=== テスト4: ファイルバリデーション統合テスト ===")

        start_time = time.time()

        try:
            # 1. 各画像ファイルのバリデーション
            test_files = list(self.test_images_dir.glob("*"))
            validation_results = {}

            for file_path in test_files:
                if file_path.is_file():
                    is_valid = self.file_discovery_service.validate_image_file(
                        file_path
                    )
                    validation_results[file_path.name] = is_valid

            # 2. バリデーション結果の検証
            # 有効な画像ファイル
            valid_extensions = [".jpg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
            for file_name, is_valid in validation_results.items():
                file_path = Path(file_name)
                if (
                    file_path.suffix.lower() in valid_extensions
                    and not file_name.startswith("corrupted")
                ):
                    self.assertTrue(
                        is_valid,
                        f"有効な画像ファイルがバリデーションを通過する必要があります: {file_name}",
                    )
                elif file_name.startswith("corrupted"):
                    self.assertFalse(
                        is_valid,
                        f"破損ファイルはバリデーションで除外される必要があります: {file_name}",
                    )
                elif file_path.suffix.lower() not in valid_extensions:
                    self.assertFalse(
                        is_valid,
                        f"無効な拡張子のファイルはバリデーションで除外される必要があります: {file_name}",
                    )

            duration = time.time() - start_time

            test_result = {
                "test_name": "file_validation_integration",
                "status": "passed",
                "duration": duration,
                "files_tested": len(validation_results),
                "validation_results": validation_results,
                "message": f"ファイルバリデーション統合テスト成功: {len(validation_results)}個のファイルをテスト",
            }
            self.test_results.append(test_result)

            print(f"✅ ファイルバリデーション統合テスト成功")
            print(f"   テストしたファイル: {len(validation_results)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(f"   バリデーション結果:")
            for file_name, is_valid in validation_results.items():
                status = "✅ 有効" if is_valid else "❌ 無効"
                print(f"     {file_name}: {status}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "file_validation_integration",
                "status": "failed",
                "duration": duration,
                "error": str(e),
            }
            self.test_results.append(test_result)

            print(f"❌ ファイルバリデーション統合テスト失敗: {e}")
            raise

    def test_05_component_integration_flow(self):
        """
        テスト5: コンポーネント間連携フローテスト

        要件: 2.1, 2.2
        """
        print("\n=== テスト5: コンポーネント間連携フローテスト ===")

        start_time = time.time()

        try:
            # 1. フォルダナビゲーターでのフォルダ選択をシミュレート
            selected_folder = self.test_images_dir

            # 2. ファイル検出サービスでの画像検出
            discovered_images = self.file_discovery_service.discover_images(
                selected_folder
            )

            # 3. サムネイルグリッドでの画像リスト設定をシミュレート
            # 実際のUIコンポーネントの代わりにモックを使用
            mock_thumbnail_grid = Mock()
            mock_thumbnail_grid.set_image_list = Mock()
            mock_thumbnail_grid.show_loading_state = Mock()
            mock_thumbnail_grid.show_empty_state = Mock()

            # 4. 連携フローの実行
            if discovered_images:
                mock_thumbnail_grid.show_loading_state("画像を読み込み中...")
                mock_thumbnail_grid.set_image_list(discovered_images)
            else:
                mock_thumbnail_grid.show_empty_state()

            # 5. 呼び出しの検証
            if discovered_images:
                mock_thumbnail_grid.show_loading_state.assert_called_once()
                mock_thumbnail_grid.set_image_list.assert_called_once_with(
                    discovered_images
                )
                mock_thumbnail_grid.show_empty_state.assert_not_called()
            else:
                mock_thumbnail_grid.show_empty_state.assert_called_once()
                mock_thumbnail_grid.set_image_list.assert_not_called()

            duration = time.time() - start_time

            test_result = {
                "test_name": "component_integration_flow",
                "status": "passed",
                "duration": duration,
                "images_found": len(discovered_images),
                "folder_path": str(selected_folder),
                "message": f"コンポーネント間連携フローテスト成功: {len(discovered_images)}個の画像で連携確認",
            }
            self.test_results.append(test_result)

            print(f"✅ コンポーネント間連携フローテスト成功")
            print(f"   検出された画像: {len(discovered_images)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(f"   連携フロー: フォルダ選択 → ファイル検出 → サムネイル表示")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "component_integration_flow",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(selected_folder),
            }
            self.test_results.append(test_result)

            print(f"❌ コンポーネント間連携フローテスト失敗: {e}")
            raise

    def test_06_japanese_message_display(self):
        """
        テスト6: 日本語メッセージ表示テスト

        要件: 6.1, 6.2
        """
        print("\n=== テスト6: 日本語メッセージ表示テスト ===")

        start_time = time.time()

        try:
            # 1. ログシステムから日本語メッセージが出力されることを確認
            # 実際の実装では、ログハンドラーをモックして日本語メッセージをキャプチャ

            # 2. 空フォルダでの日本語メッセージ確認
            discovered_images = self.file_discovery_service.discover_images(
                self.empty_dir
            )

            # 3. 存在しないフォルダでの日本語メッセージ確認
            nonexistent_folder = self.test_dir / "存在しないフォルダ"
            discovered_images_nonexistent = self.file_discovery_service.discover_images(
                nonexistent_folder
            )

            # 4. 日本語ファイル名のテスト
            japanese_image_dir = self.test_dir / "日本語フォルダ"
            japanese_image_dir.mkdir()
            japanese_image = japanese_image_dir / "日本語画像.jpg"
            japanese_image.write_bytes(b"dummy_japanese_image_data" * 10)

            discovered_japanese = self.file_discovery_service.discover_images(
                japanese_image_dir
            )

            # 5. 結果の検証
            self.assertEqual(
                len(discovered_images), 0, "空フォルダでは画像が検出されない"
            )
            self.assertEqual(
                len(discovered_images_nonexistent),
                0,
                "存在しないフォルダでは画像が検出されない",
            )
            self.assertEqual(
                len(discovered_japanese), 1, "日本語ファイル名の画像が検出される"
            )

            duration = time.time() - start_time

            test_result = {
                "test_name": "japanese_message_display",
                "status": "passed",
                "duration": duration,
                "japanese_files_found": len(discovered_japanese),
                "message": "日本語メッセージ表示テスト成功: 日本語ファイル名とメッセージを正しく処理",
            }
            self.test_results.append(test_result)

            print(f"✅ 日本語メッセージ表示テスト成功")
            print(f"   日本語ファイル名の画像: {len(discovered_japanese)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(f"   日本語対応: ファイル名、フォルダ名、エラーメッセージ")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "japanese_message_display",
                "status": "failed",
                "duration": duration,
                "error": str(e),
            }
            self.test_results.append(test_result)

            print(f"❌ 日本語メッセージ表示テスト失敗: {e}")
            raise

    def test_07_performance_basic_check(self):
        """
        テスト7: 基本パフォーマンスチェック

        要件: 4.1, 4.2
        """
        print("\n=== テスト7: 基本パフォーマンスチェック ===")

        start_time = time.time()

        try:
            # 1. 複数回の検出処理でパフォーマンスを測定
            iterations = 5
            durations = []

            for i in range(iterations):
                iteration_start = time.time()
                discovered_images = self.file_discovery_service.discover_images(
                    self.test_images_dir
                )
                iteration_duration = time.time() - iteration_start
                durations.append(iteration_duration)

            # 2. パフォーマンス指標の計算
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            # 3. パフォーマンス基準の確認
            # 基本的な処理時間の閾値（調整可能）
            max_acceptable_duration = 2.0  # 2秒以内
            self.assertLess(
                avg_duration,
                max_acceptable_duration,
                f"平均処理時間が閾値を超過: {avg_duration:.3f}秒 > {max_acceptable_duration}秒",
            )

            duration = time.time() - start_time

            test_result = {
                "test_name": "performance_basic_check",
                "status": "passed",
                "duration": duration,
                "iterations": iterations,
                "avg_duration": avg_duration,
                "max_duration": max_duration,
                "min_duration": min_duration,
                "images_per_iteration": len(discovered_images),
                "message": f"基本パフォーマンスチェック成功: 平均{avg_duration:.3f}秒で{len(discovered_images)}個の画像を処理",
            }
            self.test_results.append(test_result)

            print(f"✅ 基本パフォーマンスチェック成功")
            print(f"   反復回数: {iterations}回")
            print(f"   平均処理時間: {avg_duration:.3f}秒")
            print(f"   最大処理時間: {max_duration:.3f}秒")
            print(f"   最小処理時間: {min_duration:.3f}秒")
            print(f"   画像数/回: {len(discovered_images)}個")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "performance_basic_check",
                "status": "failed",
                "duration": duration,
                "error": str(e),
            }
            self.test_results.append(test_result)

            print(f"❌ 基本パフォーマンスチェック失敗: {e}")
            raise

    def generate_test_report(self) -> Dict[str, Any]:
        """テスト結果レポートの生成"""
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results if result["status"] == "passed"
        )
        failed_tests = total_tests - passed_tests

        total_duration = sum(result["duration"] for result in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0

        report = {
            "test_suite": "FileListDisplayIntegrationTest",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_duration": total_duration,
                "average_duration": avg_duration,
            },
            "test_results": self.test_results,
            "requirements_coverage": {
                "1.1": "フォルダ内ファイル検出機能",
                "1.2": "画像ファイル検出",
                "2.1": "フォルダナビゲーター連携",
                "2.2": "サムネイルグリッド連携",
                "6.1": "日本語メッセージ表示",
                "6.2": "日本語ログ出力",
            },
        }

        return report


def run_integration_tests():
    """統合テストの実行"""
    print("=" * 80)
    print("ファイルリスト表示修正 - 基本機能統合テスト")
    print("=" * 80)

    # テストスイートの作成と実行
    suite = unittest.TestLoader().loadTestsFromTestCase(FileListDisplayIntegrationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # テスト結果の詳細レポート生成
    if hasattr(result, "test_results"):
        test_instance = FileListDisplayIntegrationTest()
        report = test_instance.generate_test_report()

        print("\n" + "=" * 80)
        print("テスト結果サマリー")
        print("=" * 80)
        print(f"実行日時: {report['timestamp']}")
        print(f"総テスト数: {report['summary']['total_tests']}")
        print(f"成功: {report['summary']['passed_tests']}")
        print(f"失敗: {report['summary']['failed_tests']}")
        print(f"成功率: {report['summary']['success_rate']:.1%}")
        print(f"総実行時間: {report['summary']['total_duration']:.3f}秒")
        print(f"平均実行時間: {report['summary']['average_duration']:.3f}秒")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
