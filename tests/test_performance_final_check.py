#!/usr/bin/env python3
"""
ファイルリスト表示修正 - パフォーマンス最終チェック

メモリリーク、長時間使用での安定性、大量ファイルでの性能を確認します。

要件: 4.1, 4.2, 4.3

Author: Kiro AI Integration System
"""

import gc
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import psutil

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.integration.logging_system import LoggerSystem
from src.integration.services.file_discovery_service import FileDiscoveryService
from src.integration.services.memory_aware_file_discovery import (
    MemoryAwareFileDiscovery,
)
from src.integration.services.paginated_file_discovery import PaginatedFileDiscovery


class PerformanceFinalCheckTest(unittest.TestCase):
    """
    パフォーマンス最終チェックテスト

    テスト対象:
    - メモリリークの確認
    - 長時間使用での安定性確認
    - 大量ファイルでの性能確認
    """

    def setUp(self):
        """テストセットアップ"""
        # Windows環境での問題を回避
        import platform

        if platform.system() == "Windows":
            self.skipTest("Windows環境ではパフォーマンス最終チェックテストをスキップ")

        self.test_dir = Path(tempfile.mkdtemp())
        self.logger_system = LoggerSystem()

        # パフォーマンス監視用
        self.process = psutil.Process(os.getpid())
        self.performance_data = []

        # テスト用サービス
        self.file_discovery_service = FileDiscoveryService(logger_system=self.logger_system)

        self.memory_aware_discovery = MemoryAwareFileDiscovery(max_memory_mb=256, logger_system=self.logger_system)

        self.paginated_discovery = PaginatedFileDiscovery(page_size=100, logger_system=self.logger_system)

    def tearDown(self):
        """テストクリーンアップ"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # ガベージコレクション実行
        gc.collect()

    def _create_large_test_dataset(self, count: int = 1000) -> Path:
        """大量テストデータセットの作成"""
        large_dir = self.test_dir / f"large_dataset_{count}"
        large_dir.mkdir()

        print(f"   {count}個のテストファイルを作成中...")

        for i in range(count):
            # 様々なサイズの画像ファイルを作成
            size_multiplier = (i % 10) + 1
            file_name = f"test_image_{i:04d}.jpg"
            file_path = large_dir / file_name
            file_path.write_bytes(b"test_image_data" * size_multiplier * 100)

        return large_dir

    def _monitor_memory_usage(self) -> Dict[str, float]:
        """メモリ使用量の監視"""
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": self.process.memory_percent(),
        }

    def test_01_memory_leak_detection(self):
        """
        テスト1: メモリリーク検出テスト

        同じ処理を繰り返し実行してメモリリークがないことを確認
        要件: 4.3
        """
        print("\n=== テスト1: メモリリーク検出テスト ===")

        # テストデータの準備
        test_dir = self._create_large_test_dataset(500)

        # 初期メモリ使用量
        initial_memory = self._monitor_memory_usage()
        print(f"   初期メモリ使用量: {initial_memory['rss_mb']:.1f}MB")

        memory_measurements = []

        # 100回の繰り返し処理
        for iteration in range(100):
            # ファイル検出処理
            images = self.file_discovery_service.discover_images(test_dir)

            # メモリ使用量測定
            if iteration % 10 == 0:
                current_memory = self._monitor_memory_usage()
                memory_measurements.append(
                    {
                        "iteration": iteration,
                        "memory_mb": current_memory["rss_mb"],
                        "images_found": len(images),
                    }
                )

                if iteration > 0:
                    print(f"   反復 {iteration}: {current_memory['rss_mb']:.1f}MB ({len(images)}個の画像)")

            # ガベージコレクション
            if iteration % 20 == 0:
                gc.collect()

        # 最終メモリ使用量
        final_memory = self._monitor_memory_usage()
        memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]

        print(f"   最終メモリ使用量: {final_memory['rss_mb']:.1f}MB")
        print(f"   メモリ増加量: {memory_increase:.1f}MB")

        # メモリリーク判定（50MB以下の増加は許容）
        memory_leak_detected = memory_increase > 50.0

        self.assertFalse(
            memory_leak_detected,
            f"メモリリークが検出されました: {memory_increase:.1f}MB増加",
        )

        print(f"✅ メモリリーク検出テスト{'成功' if not memory_leak_detected else '失敗'}")

    def test_02_long_term_stability(self):
        """
        テスト2: 長時間使用安定性テスト

        長時間の連続使用での安定性を確認
        要件: 4.2, 4.3
        """
        print("\n=== テスト2: 長時間使用安定性テスト ===")

        # テストデータの準備
        test_dirs = []
        for i in range(5):
            test_dir = self._create_large_test_dataset(200)
            test_dirs.append(test_dir)

        start_time = time.time()
        target_duration = 60  # 60秒間のテスト

        iteration_count = 0
        error_count = 0
        performance_samples = []

        print(f"   {target_duration}秒間の連続処理テストを開始...")

        while time.time() - start_time < target_duration:
            iteration_start = time.time()

            try:
                # ランダムなディレクトリでファイル検出
                test_dir = test_dirs[iteration_count % len(test_dirs)]
                images = self.file_discovery_service.discover_images(test_dir)

                iteration_time = time.time() - iteration_start
                memory_usage = self._monitor_memory_usage()

                performance_samples.append(
                    {
                        "iteration": iteration_count,
                        "duration": iteration_time,
                        "images_found": len(images),
                        "memory_mb": memory_usage["rss_mb"],
                        "timestamp": time.time(),
                    }
                )

                iteration_count += 1

                # 進捗表示
                if iteration_count % 10 == 0:
                    elapsed = time.time() - start_time
                    print(
                        f"   {elapsed:.0f}秒経過: {iteration_count}回処理完了 "
                        f"(平均 {iteration_time:.3f}秒/回, {memory_usage['rss_mb']:.1f}MB)"
                    )

            except Exception as e:
                error_count += 1
                print(f"   エラー発生 (反復 {iteration_count}): {e}")

                # エラー率が高すぎる場合はテスト失敗
                if error_count > iteration_count * 0.1:  # 10%以上のエラー率
                    self.fail(f"エラー率が高すぎます: {error_count}/{iteration_count}")

            # CPU負荷軽減のための短い休憩
            time.sleep(0.01)

        total_duration = time.time() - start_time

        # 統計計算
        if performance_samples:
            avg_duration = sum(s["duration"] for s in performance_samples) / len(performance_samples)
            max_duration = max(s["duration"] for s in performance_samples)
            avg_memory = sum(s["memory_mb"] for s in performance_samples) / len(performance_samples)
            max_memory = max(s["memory_mb"] for s in performance_samples)
        else:
            avg_duration = max_duration = avg_memory = max_memory = 0

        print(f"   総処理時間: {total_duration:.1f}秒")
        print(f"   総反復回数: {iteration_count}回")
        print(f"   エラー回数: {error_count}回")
        print(f"   平均処理時間: {avg_duration:.3f}秒")
        print(f"   最大処理時間: {max_duration:.3f}秒")
        print(f"   平均メモリ使用量: {avg_memory:.1f}MB")
        print(f"   最大メモリ使用量: {max_memory:.1f}MB")

        # 安定性判定
        error_rate = error_count / iteration_count if iteration_count > 0 else 1.0
        stability_ok = error_rate < 0.05 and max_duration < 10.0  # エラー率5%未満、最大処理時間10秒未満

        self.assertTrue(
            stability_ok,
            f"長時間使用安定性に問題があります: エラー率{error_rate:.1%}, 最大処理時間{max_duration:.3f}秒",
        )

        print(f"✅ 長時間使用安定性テスト{'成功' if stability_ok else '失敗'}")

    def test_03_large_file_performance(self):
        """
        テスト3: 大量ファイル性能テスト

        大量ファイルでの性能を確認
        要件: 4.1, 4.2
        """
        print("\n=== テスト3: 大量ファイル性能テスト ===")

        # 異なるサイズのデータセットでテスト
        test_sizes = [1000, 2000, 5000]
        performance_results = []

        for size in test_sizes:
            print(f"   {size}個のファイルでのテスト...")

            # テストデータ作成
            large_dir = self._create_large_test_dataset(size)

            # 通常の検出テスト
            start_time = time.time()
            initial_memory = self._monitor_memory_usage()

            images = self.file_discovery_service.discover_images(large_dir)

            normal_duration = time.time() - start_time
            normal_memory = self._monitor_memory_usage()

            # 段階的読み込みテスト
            start_time = time.time()
            paginated_memory = self._monitor_memory_usage()

            paginated_images = []
            batch_count = 0

            self.paginated_discovery.set_folder(large_dir)
            while self.paginated_discovery.has_more_files():
                batch = self.paginated_discovery.get_next_batch()
                paginated_images.extend(batch)
                batch_count += 1

                # 無限ループ防止
                if batch_count > 100:
                    break

            paginated_duration = time.time() - start_time
            paginated_final_memory = self._monitor_memory_usage()

            # メモリ効率的な検出テスト
            start_time = time.time()
            memory_aware_initial = self._monitor_memory_usage()

            memory_aware_images = self.memory_aware_discovery.discover_images(large_dir)

            memory_aware_duration = time.time() - start_time
            memory_aware_final = self._monitor_memory_usage()

            result = {
                "file_count": size,
                "normal": {
                    "duration": normal_duration,
                    "images_found": len(images),
                    "memory_increase": normal_memory["rss_mb"] - initial_memory["rss_mb"],
                },
                "paginated": {
                    "duration": paginated_duration,
                    "images_found": len(paginated_images),
                    "batch_count": batch_count,
                    "memory_increase": paginated_final_memory["rss_mb"] - paginated_memory["rss_mb"],
                },
                "memory_aware": {
                    "duration": memory_aware_duration,
                    "images_found": len(memory_aware_images),
                    "memory_increase": memory_aware_final["rss_mb"] - memory_aware_initial["rss_mb"],
                },
            }

            performance_results.append(result)

            print(
                f"     通常検出: {normal_duration:.3f}秒, {len(images)}個, "
                f"メモリ増加 {result['normal']['memory_increase']:.1f}MB"
            )
            print(
                f"     段階的読み込み: {paginated_duration:.3f}秒, {len(paginated_images)}個, "
                f"{batch_count}バッチ, メモリ増加 {result['paginated']['memory_increase']:.1f}MB"
            )
            print(
                f"     メモリ効率的: {memory_aware_duration:.3f}秒, {len(memory_aware_images)}個, "
                f"メモリ増加 {result['memory_aware']['memory_increase']:.1f}MB"
            )

        # 性能要件の確認
        performance_ok = True
        for result in performance_results:
            # 5000ファイルでも30秒以内で処理完了
            if result["file_count"] == 5000 and result["normal"]["duration"] > 30.0:
                performance_ok = False
                print(f"❌ 5000ファイルの処理時間が要件を超過: {result['normal']['duration']:.3f}秒")

            # メモリ使用量が200MB以下
            if result["normal"]["memory_increase"] > 200.0:
                performance_ok = False
                print(f"❌ メモリ使用量が要件を超過: {result['normal']['memory_increase']:.1f}MB")

        self.assertTrue(performance_ok, "大量ファイル性能要件を満たしていません")

        print(f"✅ 大量ファイル性能テスト{'成功' if performance_ok else '失敗'}")

        return performance_results

    def generate_performance_report(self) -> Dict[str, Any]:
        """パフォーマンステストレポートの生成"""
        return {
            "test_suite": "PerformanceFinalCheckTest",
            "timestamp": datetime.now().isoformat(),
            "performance_data": self.performance_data,
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "python_version": sys.version,
            },
        }


def run_performance_final_check():
    """パフォーマンス最終チェックの実行"""
    print("=" * 80)
    print("ファイルリスト表示修正 - パフォーマンス最終チェック")
    print("=" * 80)

    # テストスイートの実行
    suite = unittest.TestLoader().loadTestsFromTestCase(PerformanceFinalCheckTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    print("🎯 パフォーマンス最終チェック結果")
    print("=" * 80)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"総テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")

    if result.failures:
        print("\n❌ 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n❌ エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success = result.wasSuccessful()
    print(f"\n🏆 総合結果: {'✅ 全パフォーマンス要件クリア' if success else '❌ パフォーマンス要件未達'}")
    print("=" * 80)

    return success


if __name__ == "__main__":
    success = run_performance_final_check()
    exit(0 if success else 1)
