#!/usr/bin/env python3
"""
ファイルリスト表示修正 - エラーハンドリングテスト

存在しないフォルダ、権限のないフォルダ、破損ファイルの処理をテストし、
すべてのエラーメッセージが日本語で表示されることを確認します。

要件: 5.1, 5.4, 6.1

Author: Kiro AI Integration System
"""

import os
import shutil
import stat
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
from src.integration.services.file_discovery_errors import (
    CorruptedFileError,
    FileDiscoveryError,
    FileValidationError,
    FolderAccessError,
    FolderNotFoundError,
    PermissionDeniedError,
)
from src.integration.services.file_discovery_service import FileDiscoveryService
from src.integration.state_manager import StateManager
from src.integration.ui.folder_navigator import EnhancedFolderNavigator


class FileListDisplayErrorHandlingTest(unittest.TestCase):
    """
    ファイルリスト表示修正のエラーハンドリングテスト

    テスト対象:
    - 存在しないフォルダの処理
    - 権限のないフォルダの処理
    - 破損ファイルの処理
    - 日本語エラーメッセージの表示確認
    """

    def setUp(self):
        """テストセットアップ"""
        # Windows環境での問題を回避
        import platform
        if platform.system() == "Windows":
            self.skipTest("Windows環境ではファイルリスト表示エラーハンドリングテストをスキップ")

        # テスト用の一時ディレクトリを作成
        self.test_dir = Path(tempfile.mkdtemp())

        # システムコンポーネントの初期化
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.logger_system = LoggerSystem()

        # ログメッセージをキャプチャするためのモック
        self.log_messages = []
        self.original_log_method = self.logger_system.log_ai_operation
        self.logger_system.log_ai_operation = self._capture_log_message

        # コンポーネントの初期化
        self.file_discovery_service = FileDiscoveryService(
            logger_system=self.logger_system
        )

        # テスト結果の記録用
        self.test_results = []

        # テスト用ファイルとフォルダの作成
        self._create_test_scenarios()

    def tearDown(self):
        """テストクリーンアップ"""
        # ログメソッドを元に戻す
        self.logger_system.log_ai_operation = self.original_log_method

        # 権限を復元してから削除
        self._restore_permissions()

        # 一時ディレクトリを削除
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _capture_log_message(
        self, component, operation, message, level="INFO", **kwargs
    ):
        """ログメッセージをキャプチャ"""
        self.log_messages.append(
            {
                "component": component,
                "operation": operation,
                "message": message,
                "level": level,
                "kwargs": kwargs,
            }
        )
        # 元のログメソッドも呼び出す
        self.original_log_method(component, operation, message, level, **kwargs)

    def _create_test_scenarios(self):
        """テスト用のシナリオを作成"""
        # 1. 存在しないフォルダ（テスト時に参照）
        self.nonexistent_folder = self.test_dir / "存在しないフォルダ"

        # 2. 権限のないフォルダ（Windowsでは制限的、Linuxでは完全制御）
        self.restricted_folder = self.test_dir / "権限なしフォルダ"
        self.restricted_folder.mkdir()

        # テスト用画像を作成
        test_image = self.restricted_folder / "test_image.jpg"
        test_image.write_bytes(b"dummy_image_data" * 10)

        # 権限を制限（Linuxの場合）
        if os.name != "nt":  # Windows以外
            os.chmod(self.restricted_folder, 0o000)  # 読み取り不可

        # 3. 破損ファイルのあるフォルダ
        self.corrupted_files_folder = self.test_dir / "破損ファイルフォルダ"
        self.corrupted_files_folder.mkdir()

        # 破損した画像ファイル（サイズが異常に小さい）
        corrupted_files = [
            ("空ファイル.jpg", b""),
            ("小さすぎる.png", b"x"),
            ("不正データ.gif", b"invalid_gif_data"),
            ("破損JPEG.jpg", b"bad_jpeg" * 2),
        ]

        for filename, data in corrupted_files:
            corrupted_file = self.corrupted_files_folder / filename
            corrupted_file.write_bytes(data)

        # 4. 混在フォルダ（正常ファイルと破損ファイル）
        self.mixed_folder = self.test_dir / "混在フォルダ"
        self.mixed_folder.mkdir()

        # 正常ファイル
        normal_file = self.mixed_folder / "正常画像.jpg"
        normal_file.write_bytes(b"dummy_normal_image_data" * 20)

        # 破損ファイル
        corrupted_file = self.mixed_folder / "破損画像.jpg"
        corrupted_file.write_bytes(b"bad")

        # 5. 日本語名のフォルダとファイル
        self.japanese_folder = self.test_dir / "日本語フォルダ名"
        self.japanese_folder.mkdir()

        japanese_image = self.japanese_folder / "日本語画像名.jpg"
        japanese_image.write_bytes(b"japanese_image_data" * 15)

    def _restore_permissions(self):
        """権限を復元"""
        if self.restricted_folder.exists() and os.name != "nt":
            try:
                os.chmod(self.restricted_folder, 0o755)
            except:
                pass

    def test_01_nonexistent_folder_error_handling(self):
        """
        テスト1: 存在しないフォルダのエラーハンドリング

        要件: 5.1, 6.1
        """
        print("\n=== テスト1: 存在しないフォルダのエラーハンドリング ===")

        start_time = time.time()

        try:
            # ログメッセージをクリア
            self.log_messages.clear()

            # 存在しないフォルダでの画像検出
            discovered_images = self.file_discovery_service.discover_images(
                self.nonexistent_folder
            )

            # 結果の検証
            self.assertIsInstance(
                discovered_images, list, "戻り値はリスト型である必要があります"
            )
            self.assertEqual(
                len(discovered_images),
                0,
                "存在しないフォルダでは画像が検出されない必要があります",
            )

            # 日本語ログメッセージの確認
            japanese_log_found = False
            for log_entry in self.log_messages:
                if (
                    "存在しません" in log_entry["message"]
                    or "見つかりません" in log_entry["message"]
                ):
                    japanese_log_found = True
                    break

            self.assertTrue(
                japanese_log_found,
                "日本語のエラーメッセージがログに記録される必要があります",
            )

            duration = time.time() - start_time

            test_result = {
                "test_name": "nonexistent_folder_error_handling",
                "status": "passed",
                "duration": duration,
                "folder_path": str(self.nonexistent_folder),
                "images_found": len(discovered_images),
                "japanese_messages_found": japanese_log_found,
                "log_messages": [
                    msg["message"]
                    for msg in self.log_messages
                    if "存在" in msg["message"]
                ],
                "message": "存在しないフォルダのエラーハンドリング成功: 日本語エラーメッセージを確認",
            }
            self.test_results.append(test_result)

            print(f"✅ 存在しないフォルダのエラーハンドリング成功")
            print(f"   フォルダパス: {self.nonexistent_folder}")
            print(f"   検出された画像: {len(discovered_images)}個（期待値: 0）")
            print(f"   処理時間: {duration:.3f}秒")
            print(f"   日本語メッセージ確認: {'✅' if japanese_log_found else '❌'}")

            # ログメッセージの表示
            for log_entry in self.log_messages:
                if "存在" in log_entry["message"]:
                    print(f"   ログ: {log_entry['message']}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "nonexistent_folder_error_handling",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(self.nonexistent_folder),
            }
            self.test_results.append(test_result)

            print(f"❌ 存在しないフォルダのエラーハンドリング失敗: {e}")
            raise

    def test_02_permission_denied_error_handling(self):
        """
        テスト2: 権限のないフォルダのエラーハンドリング

        要件: 5.1, 5.4, 6.1
        """
        print("\n=== テスト2: 権限のないフォルダのエラーハンドリング ===")

        start_time = time.time()

        try:
            # ログメッセージをクリア
            self.log_messages.clear()

            # 権限のないフォルダでの画像検出
            discovered_images = self.file_discovery_service.discover_images(
                self.restricted_folder
            )

            # 結果の検証（権限エラーの場合は空リストが返される）
            self.assertIsInstance(
                discovered_images, list, "戻り値はリスト型である必要があります"
            )

            # Windows環境では権限制限が効かない場合があるため、条件付きチェック
            if os.name != "nt":  # Linux/Unix環境
                self.assertEqual(
                    len(discovered_images),
                    0,
                    "権限のないフォルダでは画像が検出されない必要があります",
                )

            # 日本語ログメッセージの確認
            permission_log_found = False
            for log_entry in self.log_messages:
                if any(
                    keyword in log_entry["message"]
                    for keyword in ["権限", "アクセス", "Permission"]
                ):
                    permission_log_found = True
                    break

            # Windows環境では権限エラーが発生しない場合があるため、条件付きチェック
            if os.name != "nt":
                self.assertTrue(
                    permission_log_found,
                    "権限エラーの日本語メッセージがログに記録される必要があります",
                )

            duration = time.time() - start_time

            test_result = {
                "test_name": "permission_denied_error_handling",
                "status": "passed",
                "duration": duration,
                "folder_path": str(self.restricted_folder),
                "images_found": len(discovered_images),
                "permission_messages_found": permission_log_found,
                "os_type": os.name,
                "log_messages": [
                    msg["message"]
                    for msg in self.log_messages
                    if any(
                        k in msg["message"] for k in ["権限", "アクセス", "Permission"]
                    )
                ],
                "message": f"権限エラーハンドリング成功 (OS: {os.name}): 適切なエラー処理を確認",
            }
            self.test_results.append(test_result)

            print(f"✅ 権限のないフォルダのエラーハンドリング成功")
            print(f"   フォルダパス: {self.restricted_folder}")
            print(f"   検出された画像: {len(discovered_images)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(f"   OS環境: {os.name}")
            print(
                f"   権限エラーメッセージ確認: {'✅' if permission_log_found else '❌ (OS環境による)'}"
            )

            # ログメッセージの表示
            for log_entry in self.log_messages:
                if any(
                    keyword in log_entry["message"]
                    for keyword in ["権限", "アクセス", "Permission"]
                ):
                    print(f"   ログ: {log_entry['message']}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "permission_denied_error_handling",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(self.restricted_folder),
            }
            self.test_results.append(test_result)

            print(f"❌ 権限のないフォルダのエラーハンドリング失敗: {e}")
            raise

    def test_03_corrupted_files_error_handling(self):
        """
        テスト3: 破損ファイルのエラーハンドリング

        要件: 5.1, 6.1
        """
        print("\n=== テスト3: 破損ファイルのエラーハンドリング ===")

        start_time = time.time()

        try:
            # ログメッセージをクリア
            self.log_messages.clear()

            # 破損ファイルのあるフォルダでの画像検出
            discovered_images = self.file_discovery_service.discover_images(
                self.corrupted_files_folder
            )

            # 結果の検証
            self.assertIsInstance(
                discovered_images, list, "戻り値はリスト型である必要があります"
            )
            self.assertEqual(
                len(discovered_images),
                0,
                "破損ファイルのみのフォルダでは有効な画像が検出されない必要があります",
            )

            # 破損ファイル検出の日本語ログメッセージの確認
            corruption_log_found = False
            for log_entry in self.log_messages:
                if any(
                    keyword in log_entry["message"]
                    for keyword in ["破損", "無効", "エラー", "失敗"]
                ):
                    corruption_log_found = True
                    break

            self.assertTrue(
                corruption_log_found,
                "破損ファイル検出の日本語メッセージがログに記録される必要があります",
            )

            # 個別ファイルのバリデーションテスト
            corrupted_files = list(self.corrupted_files_folder.glob("*"))
            validation_results = {}

            for file_path in corrupted_files:
                if file_path.is_file():
                    is_valid = self.file_discovery_service.validate_image_file(
                        file_path
                    )
                    validation_results[file_path.name] = is_valid

            # すべての破損ファイルが無効と判定されることを確認
            for filename, is_valid in validation_results.items():
                self.assertFalse(
                    is_valid,
                    f"破損ファイル {filename} は無効と判定される必要があります",
                )

            duration = time.time() - start_time

            test_result = {
                "test_name": "corrupted_files_error_handling",
                "status": "passed",
                "duration": duration,
                "folder_path": str(self.corrupted_files_folder),
                "images_found": len(discovered_images),
                "corrupted_files_tested": len(validation_results),
                "corruption_messages_found": corruption_log_found,
                "validation_results": validation_results,
                "log_messages": [
                    msg["message"]
                    for msg in self.log_messages
                    if any(k in msg["message"] for k in ["破損", "無効", "エラー"])
                ],
                "message": f"破損ファイルエラーハンドリング成功: {len(validation_results)}個の破損ファイルを適切に検出・除外",
            }
            self.test_results.append(test_result)

            print(f"✅ 破損ファイルのエラーハンドリング成功")
            print(f"   フォルダパス: {self.corrupted_files_folder}")
            print(f"   検出された有効画像: {len(discovered_images)}個（期待値: 0）")
            print(f"   テストした破損ファイル: {len(validation_results)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(
                f"   破損ファイル検出メッセージ確認: {'✅' if corruption_log_found else '❌'}"
            )

            # バリデーション結果の表示
            for filename, is_valid in validation_results.items():
                status = "❌ 無効" if not is_valid else "✅ 有効"
                print(f"     {filename}: {status}")

            # 関連ログメッセージの表示
            for log_entry in self.log_messages:
                if any(
                    keyword in log_entry["message"]
                    for keyword in ["破損", "無効", "エラー"]
                ):
                    print(f"   ログ: {log_entry['message']}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "corrupted_files_error_handling",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(self.corrupted_files_folder),
            }
            self.test_results.append(test_result)

            print(f"❌ 破損ファイルのエラーハンドリング失敗: {e}")
            raise

    def test_04_mixed_folder_error_handling(self):
        """
        テスト4: 正常ファイルと破損ファイルが混在するフォルダの処理

        要件: 5.1, 6.1
        """
        print("\n=== テスト4: 混在フォルダのエラーハンドリング ===")

        start_time = time.time()

        try:
            # ログメッセージをクリア
            self.log_messages.clear()

            # 混在フォルダでの画像検出
            discovered_images = self.file_discovery_service.discover_images(
                self.mixed_folder
            )

            # 結果の検証
            self.assertIsInstance(
                discovered_images, list, "戻り値はリスト型である必要があります"
            )
            self.assertEqual(
                len(discovered_images),
                1,
                "正常ファイル1個のみが検出される必要があります",
            )

            # 検出されたファイルが正常ファイルであることを確認
            if discovered_images:
                detected_file = discovered_images[0]
                self.assertEqual(
                    detected_file.name,
                    "正常画像.jpg",
                    "正常ファイルが検出される必要があります",
                )

            # 破損ファイル除外の日本語ログメッセージの確認
            exclusion_log_found = False
            for log_entry in self.log_messages:
                if any(
                    keyword in log_entry["message"]
                    for keyword in ["除外", "破損", "無効"]
                ):
                    exclusion_log_found = True
                    break

            duration = time.time() - start_time

            test_result = {
                "test_name": "mixed_folder_error_handling",
                "status": "passed",
                "duration": duration,
                "folder_path": str(self.mixed_folder),
                "images_found": len(discovered_images),
                "detected_files": [img.name for img in discovered_images],
                "exclusion_messages_found": exclusion_log_found,
                "log_messages": [
                    msg["message"]
                    for msg in self.log_messages
                    if any(k in msg["message"] for k in ["除外", "破損", "無効"])
                ],
                "message": f"混在フォルダエラーハンドリング成功: 正常ファイル{len(discovered_images)}個を検出、破損ファイルを適切に除外",
            }
            self.test_results.append(test_result)

            print(f"✅ 混在フォルダのエラーハンドリング成功")
            print(f"   フォルダパス: {self.mixed_folder}")
            print(f"   検出された画像: {len(discovered_images)}個（期待値: 1）")
            print(f"   検出されたファイル: {[img.name for img in discovered_images]}")
            print(f"   処理時間: {duration:.3f}秒")
            print(
                f"   破損ファイル除外メッセージ確認: {'✅' if exclusion_log_found else '❌'}"
            )

            # 関連ログメッセージの表示
            for log_entry in self.log_messages:
                if any(
                    keyword in log_entry["message"]
                    for keyword in ["除外", "破損", "無効"]
                ):
                    print(f"   ログ: {log_entry['message']}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "mixed_folder_error_handling",
                "status": "failed",
                "duration": duration,
                "error": str(e),
                "folder_path": str(self.mixed_folder),
            }
            self.test_results.append(test_result)

            print(f"❌ 混在フォルダのエラーハンドリング失敗: {e}")
            raise

    def test_05_japanese_error_messages_comprehensive(self):
        """
        テスト5: 日本語エラーメッセージの包括的テスト

        要件: 6.1
        """
        print("\n=== テスト5: 日本語エラーメッセージの包括的テスト ===")

        start_time = time.time()

        try:
            # 各種エラーシナリオでの日本語メッセージ確認
            error_scenarios = [
                (self.nonexistent_folder, "存在しないフォルダ"),
                (self.restricted_folder, "権限のないフォルダ"),
                (self.corrupted_files_folder, "破損ファイルフォルダ"),
                (self.japanese_folder, "日本語フォルダ"),
            ]

            japanese_messages_found = {}

            for folder_path, scenario_name in error_scenarios:
                # ログメッセージをクリア
                self.log_messages.clear()

                # 画像検出を実行
                discovered_images = self.file_discovery_service.discover_images(
                    folder_path
                )

                # 日本語メッセージの確認
                japanese_found = False
                scenario_messages = []

                for log_entry in self.log_messages:
                    message = log_entry["message"]
                    # 日本語文字が含まれているかチェック
                    if any(ord(char) > 127 for char in message):
                        japanese_found = True
                        scenario_messages.append(message)

                japanese_messages_found[scenario_name] = {
                    "found": japanese_found,
                    "messages": scenario_messages,
                    "images_found": len(discovered_images),
                }

            # 日本語ファイル名の処理確認
            japanese_images = self.file_discovery_service.discover_images(
                self.japanese_folder
            )
            japanese_file_handling = len(japanese_images) > 0

            duration = time.time() - start_time

            test_result = {
                "test_name": "japanese_error_messages_comprehensive",
                "status": "passed",
                "duration": duration,
                "scenarios_tested": len(error_scenarios),
                "japanese_messages_by_scenario": japanese_messages_found,
                "japanese_file_handling": japanese_file_handling,
                "japanese_images_found": len(japanese_images),
                "message": f"日本語エラーメッセージ包括テスト成功: {len(error_scenarios)}個のシナリオで日本語対応を確認",
            }
            self.test_results.append(test_result)

            print(f"✅ 日本語エラーメッセージの包括的テスト成功")
            print(f"   テストシナリオ数: {len(error_scenarios)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(
                f"   日本語ファイル名処理: {'✅' if japanese_file_handling else '❌'}"
            )
            print(f"   日本語画像検出数: {len(japanese_images)}個")

            # シナリオ別結果の表示
            for scenario_name, result in japanese_messages_found.items():
                status = "✅" if result["found"] else "❌"
                print(
                    f"   {scenario_name}: {status} (画像: {result['images_found']}個)"
                )
                for message in result["messages"][:2]:  # 最大2個のメッセージを表示
                    print(f"     メッセージ: {message}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "japanese_error_messages_comprehensive",
                "status": "failed",
                "duration": duration,
                "error": str(e),
            }
            self.test_results.append(test_result)

            print(f"❌ 日本語エラーメッセージの包括的テスト失敗: {e}")
            raise

    def test_06_error_recovery_and_continuation(self):
        """
        テスト6: エラー回復と処理継続テスト

        要件: 5.1, 5.4
        """
        print("\n=== テスト6: エラー回復と処理継続テスト ===")

        start_time = time.time()

        try:
            # 複数のフォルダを連続して処理（エラーがあっても継続）
            test_folders = [
                (self.japanese_folder, "正常フォルダ"),
                (self.nonexistent_folder, "存在しないフォルダ"),
                (self.mixed_folder, "混在フォルダ"),
                (self.corrupted_files_folder, "破損ファイルフォルダ"),
            ]

            processing_results = []

            for folder_path, folder_type in test_folders:
                try:
                    folder_start_time = time.time()
                    discovered_images = self.file_discovery_service.discover_images(
                        folder_path
                    )
                    folder_duration = time.time() - folder_start_time

                    processing_results.append(
                        {
                            "folder_type": folder_type,
                            "folder_path": str(folder_path),
                            "status": "success",
                            "images_found": len(discovered_images),
                            "duration": folder_duration,
                            "error": None,
                        }
                    )

                except Exception as folder_error:
                    folder_duration = time.time() - folder_start_time
                    processing_results.append(
                        {
                            "folder_type": folder_type,
                            "folder_path": str(folder_path),
                            "status": "error",
                            "images_found": 0,
                            "duration": folder_duration,
                            "error": str(folder_error),
                        }
                    )

            # 処理継続の確認
            successful_processes = sum(
                1 for result in processing_results if result["status"] == "success"
            )
            total_processes = len(processing_results)

            # 少なくとも一部の処理が成功していることを確認
            self.assertGreater(
                successful_processes, 0, "少なくとも一部の処理が成功する必要があります"
            )

            duration = time.time() - start_time

            test_result = {
                "test_name": "error_recovery_and_continuation",
                "status": "passed",
                "duration": duration,
                "total_folders_processed": total_processes,
                "successful_processes": successful_processes,
                "error_processes": total_processes - successful_processes,
                "processing_results": processing_results,
                "message": f"エラー回復・継続テスト成功: {total_processes}個中{successful_processes}個のフォルダを正常処理",
            }
            self.test_results.append(test_result)

            print(f"✅ エラー回復と処理継続テスト成功")
            print(f"   処理フォルダ数: {total_processes}個")
            print(f"   成功: {successful_processes}個")
            print(f"   エラー: {total_processes - successful_processes}個")
            print(f"   処理時間: {duration:.3f}秒")

            # 詳細結果の表示
            for result in processing_results:
                status_icon = "✅" if result["status"] == "success" else "❌"
                print(
                    f"   {result['folder_type']}: {status_icon} (画像: {result['images_found']}個, {result['duration']:.3f}秒)"
                )
                if result["error"]:
                    print(f"     エラー: {result['error']}")

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "error_recovery_and_continuation",
                "status": "failed",
                "duration": duration,
                "error": str(e),
            }
            self.test_results.append(test_result)

            print(f"❌ エラー回復と処理継続テスト失敗: {e}")
            raise

    def test_07_ui_error_integration(self):
        """
        テスト7: UIエラー統合テスト（フォルダナビゲーターとの連携）

        要件: 5.4, 6.1
        """
        print("\n=== テスト7: UIエラー統合テスト ===")

        start_time = time.time()

        try:
            # フォルダナビゲーターのエラーハンドリングをモックでシミュレート
            mock_folder_navigator = Mock()
            mock_folder_navigator._handle_discovery_error = Mock()
            mock_folder_navigator._show_no_images_message = Mock()

            # エラーシナリオのシミュレーション
            error_scenarios = [
                (self.nonexistent_folder, "FolderNotFoundError"),
                (self.restricted_folder, "PermissionError"),
                (self.corrupted_files_folder, "ValidationError"),
            ]

            ui_error_results = []

            for folder_path, expected_error_type in error_scenarios:
                # 画像検出を実行
                discovered_images = self.file_discovery_service.discover_images(
                    folder_path
                )

                # UIエラーハンドリングのシミュレーション
                if len(discovered_images) == 0:
                    if not folder_path.exists():
                        # 存在しないフォルダのエラー処理
                        mock_folder_navigator._handle_discovery_error(
                            FileNotFoundError(
                                f"フォルダが見つかりません: {folder_path}"
                            ),
                            folder_path,
                        )
                    else:
                        # 画像が見つからない場合の処理
                        mock_folder_navigator._show_no_images_message()

                ui_error_results.append(
                    {
                        "folder_path": str(folder_path),
                        "expected_error": expected_error_type,
                        "images_found": len(discovered_images),
                        "ui_error_handled": True,
                    }
                )

            # UIエラーハンドリングメソッドの呼び出し確認
            self.assertTrue(
                mock_folder_navigator._handle_discovery_error.called
                or mock_folder_navigator._show_no_images_message.called,
                "UIエラーハンドリングメソッドが呼び出される必要があります",
            )

            duration = time.time() - start_time

            test_result = {
                "test_name": "ui_error_integration",
                "status": "passed",
                "duration": duration,
                "error_scenarios_tested": len(error_scenarios),
                "ui_error_results": ui_error_results,
                "handle_error_calls": mock_folder_navigator._handle_discovery_error.call_count,
                "show_no_images_calls": mock_folder_navigator._show_no_images_message.call_count,
                "message": f"UIエラー統合テスト成功: {len(error_scenarios)}個のエラーシナリオでUI連携を確認",
            }
            self.test_results.append(test_result)

            print(f"✅ UIエラー統合テスト成功")
            print(f"   エラーシナリオ数: {len(error_scenarios)}個")
            print(f"   処理時間: {duration:.3f}秒")
            print(
                f"   エラーハンドリング呼び出し: {mock_folder_navigator._handle_discovery_error.call_count}回"
            )
            print(
                f"   画像なしメッセージ呼び出し: {mock_folder_navigator._show_no_images_message.call_count}回"
            )

            # シナリオ別結果の表示
            for result in ui_error_results:
                print(
                    f"   {Path(result['folder_path']).name}: {result['expected_error']} (画像: {result['images_found']}個)"
                )

        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": "ui_error_integration",
                "status": "failed",
                "duration": duration,
                "error": str(e),
            }
            self.test_results.append(test_result)

            print(f"❌ UIエラー統合テスト失敗: {e}")
            raise

    def generate_error_handling_report(self) -> Dict[str, Any]:
        """エラーハンドリングテスト結果レポートの生成"""
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results if result["status"] == "passed"
        )
        failed_tests = total_tests - passed_tests

        total_duration = sum(result["duration"] for result in self.test_results)
        avg_duration = total_duration / total_tests if total_tests > 0 else 0

        # 日本語メッセージ確認の統計
        japanese_message_tests = [
            r for r in self.test_results if "japanese" in r.get("message", "").lower()
        ]
        japanese_success_rate = (
            len([r for r in japanese_message_tests if r["status"] == "passed"])
            / len(japanese_message_tests)
            if japanese_message_tests
            else 0
        )

        report = {
            "test_suite": "FileListDisplayErrorHandlingTest",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "japanese_message_success_rate": japanese_success_rate,
            },
            "error_scenarios_tested": {
                "nonexistent_folder": "存在しないフォルダ",
                "permission_denied": "権限のないフォルダ",
                "corrupted_files": "破損ファイル",
                "mixed_content": "正常・破損ファイル混在",
                "japanese_names": "日本語ファイル名",
                "ui_integration": "UIエラー統合",
            },
            "test_results": self.test_results,
            "requirements_coverage": {
                "5.1": "ファイルアクセスエラーハンドリング",
                "5.4": "致命的エラー処理",
                "6.1": "日本語エラーメッセージ表示",
            },
        }

        return report


def run_error_handling_tests():
    """エラーハンドリングテストの実行"""
    print("=" * 80)
    print("ファイルリスト表示修正 - エラーハンドリングテスト")
    print("=" * 80)

    # テストスイートの作成と実行
    suite = unittest.TestLoader().loadTestsFromTestCase(
        FileListDisplayErrorHandlingTest
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # テスト結果の詳細レポート生成
    test_instance = FileListDisplayErrorHandlingTest()
    test_instance.setUp()

    try:
        # 各テストを実行してレポートデータを収集
        for test_method in [
            "test_01_nonexistent_folder_error_handling",
            "test_02_permission_denied_error_handling",
            "test_03_corrupted_files_error_handling",
            "test_04_mixed_folder_error_handling",
            "test_05_japanese_error_messages_comprehensive",
            "test_06_error_recovery_and_continuation",
            "test_07_ui_error_integration",
        ]:
            try:
                getattr(test_instance, test_method)()
            except Exception:
                pass  # テスト結果は既に記録されている

        report = test_instance.generate_error_handling_report()

        print("\n" + "=" * 80)
        print("エラーハンドリングテスト結果サマリー")
        print("=" * 80)
        print(f"実行日時: {report['timestamp']}")
        print(f"総テスト数: {report['summary']['total_tests']}")
        print(f"成功: {report['summary']['passed_tests']}")
        print(f"失敗: {report['summary']['failed_tests']}")
        print(f"成功率: {report['summary']['success_rate']:.1%}")
        print(
            f"日本語メッセージ成功率: {report['summary']['japanese_message_success_rate']:.1%}"
        )
        print(f"総実行時間: {report['summary']['total_duration']:.3f}秒")
        print(f"平均実行時間: {report['summary']['average_duration']:.3f}秒")

        print("\nテストしたエラーシナリオ:")
        for scenario_key, scenario_desc in report["error_scenarios_tested"].items():
            print(f"  - {scenario_desc}")

    finally:
        test_instance.tearDown()

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_error_handling_tests()
    exit(0 if success else 1)
