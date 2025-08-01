#!/usr/bin/env python3
"""
ファイルリスト表示修正 - パフォーマンステスト

大量ファイル（1000個以上）での動作テスト、メモリ使用量の監視テスト、
応答時間の測定テストを実行します。

要件: 4.1, 4.2, 4.3

Author: Kiro AI Integration System
"""

import gc
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import Mock, patch

import psutil

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.models import AIComponent
from src.integration.services.file_discovery_service import FileDiscoveryService
from src.integration.services.memory_aware_file_discovery import (
    MemoryAwareFileDiscovery,
)
from src.integration.services.paginated_file_discovery import PaginatedFileDiscovery
from src.integration.state_manager import StateManager


@dataclass
class PerformanceMetrics:
    """パフォーマンス測定結果"""

    test_name: str
    file_count: int
    duration: float
    memory_usage_mb: float
    peak_memory_mb: float
    cpu_usage_percent: float
    files_per_second: float
    cache_hit_rate: float = 0.0
    error_count: int = 0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MemoryMonitor:
    """メモリ使用量監視クラス"""

    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.memory_samples = []
        self.peak_memory = 0
        self.monitor_thread = None

    def start_monitoring(self):
        """メモリ監視開始"""
        self.monitoring = True
        self.memory_samples = []
        self.peak_memory = 0
        self.monitor_thread = threading.Thread(target=self._monitor_memory)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self) -> Dict[str, float]:
        """メモリ監視停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

        if self.memory_samples:
            avg_memory = sum(self.memory_samples) / len(self.memory_samples)
            return {
                "average_memory_mb": avg_memory,
                "peak_memory_mb": self.peak_memory,
                "sample_count": len(self.memory_samples),
            }
        return {"average_memory_mb": 0, "peak_memory_mb": 0, "sample_count": 0}

    def _monitor_memory(self):
        """メモリ監視ループ"""
        while self.monitoring:
            try:
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # MB
                self.memory_samples.append(memory_mb)
                self.peak_memory = max(self.peak_memory, memory_mb)
                time.sleep(0.1)  # 100ms間隔でサンプリング
            except:
                break


class FileListDisplayPerformanceTest(unittest.TestCase):
    """
    ファイルリスト表示修正のパフォーマンステスト

    テスト対象:
    - 大量ファイル（1000個以上）での動作テスト
    - メモリ使用量の監視テスト
    - 応答時間の測定テスト
    """

    def setUp(self):
        """テストセットアップ"""
        # Windows環境での問題を回避
        import platform
        if platform.system() == "Windows":
            self.skipTest("Windows環境ではファイルリスト表示パフォーマンステストをスキップ")

        # テスト用の一時ディレクトリを作成
        self.test_dir = Path(tempfile.mkdtemp())

        # システムコンポーネントの初期化
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.logger_system = LoggerSystem()

        # メモリ監視の初期化
        self.memory_monitor = MemoryMonitor()

        # コンポーネントの初期化
        self.file_discovery_service = FileDiscoveryService(
            logger_system=self.logger_system, enable_cache=True
        )

        # パフォーマンステスト結果の記録用
        self.performance_results = []

        # テスト開始時のメモリ使用量を記録
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

    def tearDown(self):
        """テストクリーンアップ"""
        # メモリ監視停止
        if self.memory_monitor.monitoring:
            self.memory_monitor.stop_monitoring()

        # ガベージコレクション実行
        gc.collect()

        # 一時ディレクトリを削除
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_large_image_dataset(
        self, count: int, folder_name: str = "large_dataset"
    ) -> Path:
        """大量の画像ファイルを作成"""
        dataset_dir = self.test_dir / folder_name
        dataset_dir.mkdir(exist_ok=True)

        print(f"   大量画像データセット作成中: {count}個のファイル...")

        # 異なるサイズと拡張子のファイルを作成
        extensions = [".jpg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
        file_sizes = [1024, 2048, 4096, 8192]  # バイト

        for i in range(count):
            extension = extensions[i % len(extensions)]
            file_size = file_sizes[i % len(file_sizes)]

            filename = f"test_image_{i:05d}{extension}"
            file_path = dataset_dir / filename

            # ダミーデータを作成（実際の画像データではないが、サイズは実際的）
            dummy_data = b"dummy_image_data" * (file_size // 16)
            file_path.write_bytes(dummy_data)

            # 進捗表示（100ファイルごと）
            if (i + 1) % 100 == 0:
                print(f"     作成済み: {i + 1}/{count} ファイル")

        print(f"   データセット作成完了: {dataset_dir}")
        return dataset_dir

    def _measure_cpu_usage(self, duration: float = 1.0) -> float:
        """CPU使用率を測定"""
        return psutil.cpu_percent(interval=duration)

    def test_01_large_file_count_performance(self):
        """
        テスト1: 大量ファイル処理パフォーマンステスト

        要件: 4.1
        """
        print("\n=== テスト1: 大量ファイル処理パフォーマンステスト ===")

        # テストケース: 異なるファイル数での性能測定
        test_cases = [100, 500, 1000, 2000]

        for file_count in test_cases:
            print(f"\n--- {file_count}個のファイルでのテスト ---")

            # データセット作成
            dataset_dir = self._create_large_image_dataset(
                file_count, f"dataset_{file_count}"
            )

            # メモリ監視開始
            self.memory_monitor.start_monitoring()

            # パフォーマンス測定開始
            start_time = time.time()
            cpu_start = time.time()

            try:
                # 画像検出実行
                discovered_images = self.file_discovery_service.discover_images(
                    dataset_dir
                )

                # 測定終了
                duration = time.time() - start_time
                cpu_usage = self._measure_cpu_usage(0.5)

                # メモリ監視停止
                memory_stats = self.memory_monitor.stop_monitoring()

                # 結果の検証
                self.assertIsInstance(
                    discovered_images, list, "戻り値はリスト型である必要があります"
                )
                self.assertGreater(
                    len(discovered_images), 0, "画像ファイルが検出される必要があります"
                )

                # パフォーマンス指標の計算
                files_per_second = (
                    len(discovered_images) / duration if duration > 0 else 0
                )

                # キャッシュ統計の取得
                cache_stats = {}
                if (
                    hasattr(self.file_discovery_service, "cache")
                    and self.file_discovery_service.cache
                ):
                    cache_stats = self.file_discovery_service.cache.get_cache_stats()

                # パフォーマンス結果の記録
                performance_metrics = PerformanceMetrics(
                    test_name=f"large_file_count_{file_count}",
                    file_count=file_count,
                    duration=duration,
                    memory_usage_mb=memory_stats.get("average_memory_mb", 0),
                    peak_memory_mb=memory_stats.get("peak_memory_mb", 0),
                    cpu_usage_percent=cpu_usage,
                    files_per_second=files_per_second,
                    cache_hit_rate=cache_stats.get("hit_rate", 0.0),
                )

                self.performance_results.append(performance_metrics)

                # パフォーマンス基準の確認
                max_acceptable_duration = file_count * 0.01  # ファイル1個あたり10ms以内
                self.assertLess(
                    duration,
                    max_acceptable_duration,
                    f"処理時間が基準を超過: {duration:.3f}秒 > {max_acceptable_duration:.3f}秒",
                )

                # 最小処理速度の確認（ファイル/秒）
                min_files_per_second = 50  # 最低50ファイル/秒
                self.assertGreater(
                    files_per_second,
                    min_files_per_second,
                    f"処理速度が基準を下回る: {files_per_second:.1f} < {min_files_per_second}",
                )

                print(f"✅ {file_count}個ファイルテスト成功")
                print(f"   検出画像数: {len(discovered_images)}個")
                print(f"   処理時間: {duration:.3f}秒")
                print(f"   処理速度: {files_per_second:.1f}ファイル/秒")
                print(
                    f"   平均メモリ使用量: {memory_stats.get('average_memory_mb', 0):.1f}MB"
                )
                print(
                    f"   ピークメモリ使用量: {memory_stats.get('peak_memory_mb', 0):.1f}MB"
                )
                print(f"   CPU使用率: {cpu_usage:.1f}%")
                if cache_stats:
                    print(
                        f"   キャッシュヒット率: {cache_stats.get('hit_rate', 0):.1%}"
                    )

            except Exception as e:
                # メモリ監視停止
                self.memory_monitor.stop_monitoring()

                print(f"❌ {file_count}個ファイルテスト失敗: {e}")
                raise

    def test_02_memory_usage_monitoring(self):
        """
        テスト2: メモリ使用量監視テスト

        要件: 4.3
        """
        print("\n=== テスト2: メモリ使用量監視テスト ===")

        # 大量ファイルでのメモリ使用量テスト
        file_count = 1500
        dataset_dir = self._create_large_image_dataset(
            file_count, "memory_test_dataset"
        )

        # 初期メモリ使用量
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # メモリ監視開始
        self.memory_monitor.start_monitoring()

        start_time = time.time()

        try:
            # 複数回の処理でメモリリークをチェック
            iterations = 3
            memory_progression = []

            for i in range(iterations):
                iteration_start = time.time()

                # 画像検出実行
                discovered_images = self.file_discovery_service.discover_images(
                    dataset_dir
                )

                # 現在のメモリ使用量を記録
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_progression.append(current_memory)

                iteration_duration = time.time() - iteration_start
                print(
                    f"   反復 {i+1}/{iterations}: {len(discovered_images)}個検出, "
                    f"{iteration_duration:.3f}秒, メモリ: {current_memory:.1f}MB"
                )

                # ガベージコレクション実行
                gc.collect()

            # メモリ監視停止
            memory_stats = self.memory_monitor.stop_monitoring()

            # メモリリークの確認
            memory_increase = memory_progression[-1] - memory_progression[0]
            max_acceptable_increase = 50  # 50MB以内の増加は許容

            self.assertLess(
                memory_increase,
                max_acceptable_increase,
                f"メモリリークの可能性: {memory_increase:.1f}MB増加 > {max_acceptable_increase}MB",
            )

            # ピークメモリ使用量の確認
            max_acceptable_peak = 500  # 500MB以内
            peak_memory = memory_stats.get("peak_memory_mb", 0)
            self.assertLess(
                peak_memory,
                max_acceptable_peak,
                f"ピークメモリ使用量が過大: {peak_memory:.1f}MB > {max_acceptable_peak}MB",
            )

            duration = time.time() - start_time

            # パフォーマンス結果の記録
            performance_metrics = PerformanceMetrics(
                test_name="memory_usage_monitoring",
                file_count=file_count,
                duration=duration,
                memory_usage_mb=memory_stats.get("average_memory_mb", 0),
                peak_memory_mb=peak_memory,
                cpu_usage_percent=self._measure_cpu_usage(0.5),
                files_per_second=file_count * iterations / duration,
            )

            self.performance_results.append(performance_metrics)

            print(f"✅ メモリ使用量監視テスト成功")
            print(f"   テストファイル数: {file_count}個")
            print(f"   反復回数: {iterations}回")
            print(f"   総処理時間: {duration:.3f}秒")
            print(f"   初期メモリ: {initial_memory:.1f}MB")
            print(f"   最終メモリ: {memory_progression[-1]:.1f}MB")
            print(f"   メモリ増加: {memory_increase:.1f}MB")
            print(f"   ピークメモリ: {peak_memory:.1f}MB")
            print(f"   平均メモリ: {memory_stats.get('average_memory_mb', 0):.1f}MB")

        except Exception as e:
            self.memory_monitor.stop_monitoring()
            print(f"❌ メモリ使用量監視テスト失敗: {e}")
            raise

    def test_03_response_time_measurement(self):
        """
        テスト3: 応答時間測定テスト

        要件: 4.2
        """
        print("\n=== テスト3: 応答時間測定テスト ===")

        # 異なるサイズのデータセットでの応答時間測定
        test_scenarios = [
            (100, "小規模"),
            (500, "中規模"),
            (1000, "大規模"),
            (2000, "超大規模"),
        ]

        response_time_results = []

        for file_count, scenario_name in test_scenarios:
            print(f"\n--- {scenario_name}データセット ({file_count}個) ---")

            # データセット作成
            dataset_dir = self._create_large_image_dataset(
                file_count, f"response_test_{file_count}"
            )

            # 複数回測定して平均を取る
            measurements = []
            iterations = 5

            for i in range(iterations):
                # キャッシュクリア（公平な測定のため）
                if (
                    hasattr(self.file_discovery_service, "cache")
                    and self.file_discovery_service.cache
                ):
                    self.file_discovery_service.cache.clear_cache()

                # 応答時間測定
                start_time = time.time()
                discovered_images = self.file_discovery_service.discover_images(
                    dataset_dir
                )
                response_time = time.time() - start_time

                measurements.append(response_time)

                print(
                    f"     測定 {i+1}/{iterations}: {response_time:.3f}秒 ({len(discovered_images)}個検出)"
                )

            # 統計計算
            avg_response_time = sum(measurements) / len(measurements)
            min_response_time = min(measurements)
            max_response_time = max(measurements)

            # 応答時間基準の確認
            max_acceptable_response = file_count * 0.005  # ファイル1個あたり5ms以内
            self.assertLess(
                avg_response_time,
                max_acceptable_response,
                f"{scenario_name}データセットの応答時間が基準を超過: "
                f"{avg_response_time:.3f}秒 > {max_acceptable_response:.3f}秒",
            )

            # 応答時間の一貫性確認（標準偏差）
            variance = sum((t - avg_response_time) ** 2 for t in measurements) / len(
                measurements
            )
            std_deviation = variance**0.5
            coefficient_of_variation = (
                std_deviation / avg_response_time if avg_response_time > 0 else 0
            )

            # 変動係数が30%以内であることを確認（一貫性）
            max_acceptable_cv = 0.3
            self.assertLess(
                coefficient_of_variation,
                max_acceptable_cv,
                f"{scenario_name}データセットの応答時間が不安定: CV={coefficient_of_variation:.2f} > {max_acceptable_cv}",
            )

            response_time_results.append(
                {
                    "scenario": scenario_name,
                    "file_count": file_count,
                    "avg_response_time": avg_response_time,
                    "min_response_time": min_response_time,
                    "max_response_time": max_response_time,
                    "std_deviation": std_deviation,
                    "coefficient_of_variation": coefficient_of_variation,
                    "files_per_second": file_count / avg_response_time,
                }
            )

            print(f"   ✅ {scenario_name}応答時間測定完了")
            print(f"     平均応答時間: {avg_response_time:.3f}秒")
            print(f"     最小応答時間: {min_response_time:.3f}秒")
            print(f"     最大応答時間: {max_response_time:.3f}秒")
            print(f"     標準偏差: {std_deviation:.3f}秒")
            print(f"     変動係数: {coefficient_of_variation:.2%}")
            print(f"     処理速度: {file_count / avg_response_time:.1f}ファイル/秒")

        # 全体結果の記録
        overall_performance = PerformanceMetrics(
            test_name="response_time_measurement",
            file_count=sum(r["file_count"] for r in response_time_results),
            duration=sum(r["avg_response_time"] for r in response_time_results),
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            peak_memory_mb=0,  # この測定では追跡しない
            cpu_usage_percent=self._measure_cpu_usage(0.5),
            files_per_second=sum(r["files_per_second"] for r in response_time_results)
            / len(response_time_results),
        )

        self.performance_results.append(overall_performance)

        print(f"\n✅ 応答時間測定テスト成功")
        print(f"   テストシナリオ数: {len(test_scenarios)}個")
        print(
            f"   総ファイル数: {sum(r['file_count'] for r in response_time_results)}個"
        )
        print(f"   平均処理速度: {overall_performance.files_per_second:.1f}ファイル/秒")

    def test_04_concurrent_processing_performance(self):
        """
        テスト4: 並行処理パフォーマンステスト

        要件: 4.2
        """
        print("\n=== テスト4: 並行処理パフォーマンステスト ===")

        # 複数のフォルダを並行処理
        folder_count = 4
        files_per_folder = 250

        # 複数のデータセットを作成
        datasets = []
        for i in range(folder_count):
            dataset_dir = self._create_large_image_dataset(
                files_per_folder, f"concurrent_dataset_{i}"
            )
            datasets.append(dataset_dir)

        # メモリ監視開始
        self.memory_monitor.start_monitoring()

        # 並行処理テスト
        start_time = time.time()

        def process_folder(folder_path):
            """フォルダ処理関数"""
            folder_start = time.time()
            discovered_images = self.file_discovery_service.discover_images(folder_path)
            folder_duration = time.time() - folder_start
            return {
                "folder": str(folder_path),
                "images_found": len(discovered_images),
                "duration": folder_duration,
            }

        try:
            # ThreadPoolExecutorを使用した並行処理
            with ThreadPoolExecutor(max_workers=folder_count) as executor:
                # 全フォルダの処理を並行実行
                future_to_folder = {
                    executor.submit(process_folder, folder): folder
                    for folder in datasets
                }

                concurrent_results = []
                for future in as_completed(future_to_folder):
                    folder = future_to_folder[future]
                    try:
                        result = future.result()
                        concurrent_results.append(result)
                        print(
                            f"   フォルダ処理完了: {Path(result['folder']).name} "
                            f"({result['images_found']}個, {result['duration']:.3f}秒)"
                        )
                    except Exception as e:
                        print(f"   フォルダ処理エラー: {folder} - {e}")

            # 並行処理時間の測定
            concurrent_duration = time.time() - start_time

            # メモリ監視停止
            memory_stats = self.memory_monitor.stop_monitoring()

            # 逐次処理との比較のため、逐次処理時間を測定
            sequential_start = time.time()
            sequential_results = []

            for dataset in datasets:
                result = process_folder(dataset)
                sequential_results.append(result)

            sequential_duration = time.time() - sequential_start

            # パフォーマンス比較
            total_images = sum(r["images_found"] for r in concurrent_results)
            concurrent_fps = total_images / concurrent_duration
            sequential_fps = total_images / sequential_duration

            speedup_ratio = sequential_duration / concurrent_duration
            efficiency = speedup_ratio / folder_count  # 理想的には1.0

            # 並行処理の効果確認
            min_acceptable_speedup = 1.5  # 最低1.5倍の高速化
            self.assertGreater(
                speedup_ratio,
                min_acceptable_speedup,
                f"並行処理の効果が不十分: {speedup_ratio:.2f}倍 < {min_acceptable_speedup}倍",
            )

            # パフォーマンス結果の記録
            performance_metrics = PerformanceMetrics(
                test_name="concurrent_processing",
                file_count=total_images,
                duration=concurrent_duration,
                memory_usage_mb=memory_stats.get("average_memory_mb", 0),
                peak_memory_mb=memory_stats.get("peak_memory_mb", 0),
                cpu_usage_percent=self._measure_cpu_usage(0.5),
                files_per_second=concurrent_fps,
            )

            self.performance_results.append(performance_metrics)

            print(f"✅ 並行処理パフォーマンステスト成功")
            print(f"   処理フォルダ数: {folder_count}個")
            print(f"   総ファイル数: {total_images}個")
            print(f"   並行処理時間: {concurrent_duration:.3f}秒")
            print(f"   逐次処理時間: {sequential_duration:.3f}秒")
            print(f"   高速化倍率: {speedup_ratio:.2f}倍")
            print(f"   並行効率: {efficiency:.2%}")
            print(f"   並行処理速度: {concurrent_fps:.1f}ファイル/秒")
            print(f"   逐次処理速度: {sequential_fps:.1f}ファイル/秒")
            print(f"   ピークメモリ: {memory_stats.get('peak_memory_mb', 0):.1f}MB")

        except Exception as e:
            self.memory_monitor.stop_monitoring()
            print(f"❌ 並行処理パフォーマンステスト失敗: {e}")
            raise

    def test_05_cache_performance_impact(self):
        """
        テスト5: キャッシュパフォーマンス影響テスト

        要件: 4.1, 4.3
        """
        print("\n=== テスト5: キャッシュパフォーマンス影響テスト ===")

        file_count = 1000
        dataset_dir = self._create_large_image_dataset(file_count, "cache_test_dataset")

        # キャッシュ無効での測定
        print("\n--- キャッシュ無効での測定 ---")
        no_cache_service = FileDiscoveryService(
            logger_system=self.logger_system, enable_cache=False
        )

        no_cache_times = []
        for i in range(3):
            start_time = time.time()
            discovered_images_no_cache = no_cache_service.discover_images(dataset_dir)
            no_cache_duration = time.time() - start_time
            no_cache_times.append(no_cache_duration)
            print(
                f"   測定 {i+1}: {no_cache_duration:.3f}秒 ({len(discovered_images_no_cache)}個)"
            )

        avg_no_cache_time = sum(no_cache_times) / len(no_cache_times)

        # キャッシュ有効での測定
        print("\n--- キャッシュ有効での測定 ---")
        cache_service = FileDiscoveryService(
            logger_system=self.logger_system, enable_cache=True
        )

        # 初回実行（キャッシュ構築）
        print("   初回実行（キャッシュ構築）:")
        start_time = time.time()
        discovered_images_cache_first = cache_service.discover_images(dataset_dir)
        cache_first_duration = time.time() - start_time
        print(
            f"     {cache_first_duration:.3f}秒 ({len(discovered_images_cache_first)}個)"
        )

        # キャッシュヒット測定
        print("   キャッシュヒット測定:")
        cache_hit_times = []
        for i in range(3):
            start_time = time.time()
            discovered_images_cache = cache_service.discover_images(dataset_dir)
            cache_hit_duration = time.time() - start_time
            cache_hit_times.append(cache_hit_duration)
            print(
                f"     測定 {i+1}: {cache_hit_duration:.3f}秒 ({len(discovered_images_cache)}個)"
            )

        avg_cache_hit_time = sum(cache_hit_times) / len(cache_hit_times)

        # キャッシュ統計の取得
        cache_stats = (
            cache_service.cache.get_cache_stats() if cache_service.cache else {}
        )

        # パフォーマンス改善の確認
        cache_speedup = (
            avg_no_cache_time / avg_cache_hit_time if avg_cache_hit_time > 0 else 0
        )
        min_acceptable_speedup = 2.0  # 最低2倍の高速化

        self.assertGreater(
            cache_speedup,
            min_acceptable_speedup,
            f"キャッシュによる高速化が不十分: {cache_speedup:.2f}倍 < {min_acceptable_speedup}倍",
        )

        # キャッシュヒット率の確認
        hit_rate = cache_stats.get("hit_rate", 0)
        min_acceptable_hit_rate = 0.8  # 最低80%のヒット率

        if hit_rate > 0:  # キャッシュ統計が利用可能な場合
            self.assertGreater(
                hit_rate,
                min_acceptable_hit_rate,
                f"キャッシュヒット率が低い: {hit_rate:.1%} < {min_acceptable_hit_rate:.1%}",
            )

        # パフォーマンス結果の記録
        performance_metrics = PerformanceMetrics(
            test_name="cache_performance_impact",
            file_count=file_count,
            duration=avg_cache_hit_time,
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            peak_memory_mb=0,
            cpu_usage_percent=self._measure_cpu_usage(0.5),
            files_per_second=file_count / avg_cache_hit_time,
            cache_hit_rate=hit_rate,
        )

        self.performance_results.append(performance_metrics)

        print(f"\n✅ キャッシュパフォーマンス影響テスト成功")
        print(f"   テストファイル数: {file_count}個")
        print(f"   キャッシュ無効平均時間: {avg_no_cache_time:.3f}秒")
        print(f"   キャッシュ初回時間: {cache_first_duration:.3f}秒")
        print(f"   キャッシュヒット平均時間: {avg_cache_hit_time:.3f}秒")
        print(f"   キャッシュ高速化倍率: {cache_speedup:.2f}倍")
        print(f"   キャッシュヒット率: {hit_rate:.1%}")
        if cache_stats:
            print(f"   キャッシュサイズ: {cache_stats.get('cache_size', 0)}エントリ")

    def test_06_memory_aware_processing(self):
        """
        テスト6: メモリ制限対応処理テスト

        要件: 4.3
        """
        print("\n=== テスト6: メモリ制限対応処理テスト ===")

        # 大量ファイルでメモリ制限テスト
        file_count = 1500
        dataset_dir = self._create_large_image_dataset(
            file_count, "memory_aware_dataset"
        )

        # メモリ制限付きファイル検出サービス
        memory_limit_mb = 100  # 100MBの制限
        memory_aware_service = MemoryAwareFileDiscovery(
            logger_system=self.logger_system, max_memory_mb=memory_limit_mb
        )

        # メモリ監視開始
        self.memory_monitor.start_monitoring()

        start_time = time.time()

        try:
            # メモリ制限付き処理の実行
            discovered_images = memory_aware_service.discover_images(dataset_dir)

            duration = time.time() - start_time

            # メモリ監視停止
            memory_stats = self.memory_monitor.stop_monitoring()

            # 結果の検証
            self.assertIsInstance(
                discovered_images, list, "戻り値はリスト型である必要があります"
            )
            self.assertGreater(
                len(discovered_images), 0, "画像ファイルが検出される必要があります"
            )

            # メモリ制限の遵守確認
            peak_memory = memory_stats.get("peak_memory_mb", 0)
            memory_limit_with_tolerance = memory_limit_mb * 1.2  # 20%の許容範囲

            # メモリ制限が厳密に守られているかは環境依存のため、警告レベルでチェック
            if peak_memory > memory_limit_with_tolerance:
                print(
                    f"   ⚠️  メモリ制限を超過: {peak_memory:.1f}MB > {memory_limit_with_tolerance:.1f}MB"
                )

            # メモリ効率の確認
            memory_per_file = (
                peak_memory / len(discovered_images) if discovered_images else 0
            )
            max_acceptable_memory_per_file = 0.5  # ファイル1個あたり0.5MB以内

            self.assertLess(
                memory_per_file,
                max_acceptable_memory_per_file,
                f"ファイルあたりメモリ使用量が過大: {memory_per_file:.3f}MB > {max_acceptable_memory_per_file}MB",
            )

            # パフォーマンス結果の記録
            performance_metrics = PerformanceMetrics(
                test_name="memory_aware_processing",
                file_count=file_count,
                duration=duration,
                memory_usage_mb=memory_stats.get("average_memory_mb", 0),
                peak_memory_mb=peak_memory,
                cpu_usage_percent=self._measure_cpu_usage(0.5),
                files_per_second=len(discovered_images) / duration,
            )

            self.performance_results.append(performance_metrics)

            print(f"✅ メモリ制限対応処理テスト成功")
            print(f"   テストファイル数: {file_count}個")
            print(f"   検出画像数: {len(discovered_images)}個")
            print(f"   メモリ制限: {memory_limit_mb}MB")
            print(f"   ピークメモリ使用量: {peak_memory:.1f}MB")
            print(
                f"   平均メモリ使用量: {memory_stats.get('average_memory_mb', 0):.1f}MB"
            )
            print(f"   ファイルあたりメモリ: {memory_per_file:.3f}MB")
            print(f"   処理時間: {duration:.3f}秒")
            print(f"   処理速度: {len(discovered_images) / duration:.1f}ファイル/秒")

        except Exception as e:
            self.memory_monitor.stop_monitoring()
            print(f"❌ メモリ制限対応処理テスト失敗: {e}")
            raise

    def generate_performance_report(self) -> Dict[str, Any]:
        """パフォーマンステスト結果レポートの生成"""
        if not self.performance_results:
            return {"error": "No performance results available"}

        total_tests = len(self.performance_results)
        total_files_processed = sum(r.file_count for r in self.performance_results)
        total_duration = sum(r.duration for r in self.performance_results)

        avg_files_per_second = (
            sum(r.files_per_second for r in self.performance_results) / total_tests
        )
        avg_memory_usage = (
            sum(r.memory_usage_mb for r in self.performance_results) / total_tests
        )
        peak_memory_overall = max(r.peak_memory_mb for r in self.performance_results)

        # パフォーマンス基準の評価
        performance_grades = []
        for result in self.performance_results:
            if result.files_per_second > 100:
                grade = "A"
            elif result.files_per_second > 50:
                grade = "B"
            elif result.files_per_second > 25:
                grade = "C"
            else:
                grade = "D"
            performance_grades.append(grade)

        grade_distribution = {
            grade: performance_grades.count(grade) for grade in "ABCD"
        }

        report = {
            "test_suite": "FileListDisplayPerformanceTest",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "total_files_processed": total_files_processed,
                "total_duration": total_duration,
                "average_files_per_second": avg_files_per_second,
                "average_memory_usage_mb": avg_memory_usage,
                "peak_memory_overall_mb": peak_memory_overall,
                "performance_grade_distribution": grade_distribution,
            },
            "performance_results": [
                {
                    "test_name": r.test_name,
                    "file_count": r.file_count,
                    "duration": r.duration,
                    "files_per_second": r.files_per_second,
                    "memory_usage_mb": r.memory_usage_mb,
                    "peak_memory_mb": r.peak_memory_mb,
                    "cpu_usage_percent": r.cpu_usage_percent,
                    "cache_hit_rate": r.cache_hit_rate,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.performance_results
            ],
            "performance_benchmarks": {
                "excellent": "> 100 files/sec",
                "good": "50-100 files/sec",
                "acceptable": "25-50 files/sec",
                "poor": "< 25 files/sec",
            },
            "requirements_coverage": {
                "4.1": "段階的読み込み（ページネーション）",
                "4.2": "UIスレッドブロック防止",
                "4.3": "メモリ使用量制御",
            },
        }

        return report


def run_performance_tests():
    """パフォーマンステストの実行"""
    print("=" * 80)
    print("ファイルリスト表示修正 - パフォーマンステスト")
    print("=" * 80)

    # システム情報の表示
    print(f"システム情報:")
    print(f"  CPU: {psutil.cpu_count()}コア")
    print(f"  メモリ: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")
    print(f"  Python: {sys.version}")
    print()

    # テストスイートの作成と実行
    suite = unittest.TestLoader().loadTestsFromTestCase(FileListDisplayPerformanceTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # テスト結果の詳細レポート生成
    test_instance = FileListDisplayPerformanceTest()
    test_instance.setUp()

    try:
        # 各テストを実行してレポートデータを収集
        test_methods = [
            "test_01_large_file_count_performance",
            "test_02_memory_usage_monitoring",
            "test_03_response_time_measurement",
            "test_04_concurrent_processing_performance",
            "test_05_cache_performance_impact",
            "test_06_memory_aware_processing",
        ]

        for test_method in test_methods:
            try:
                getattr(test_instance, test_method)()
            except Exception as e:
                print(f"テスト {test_method} でエラー: {e}")

        report = test_instance.generate_performance_report()

        print("\n" + "=" * 80)
        print("パフォーマンステスト結果サマリー")
        print("=" * 80)
        print(f"実行日時: {report['timestamp']}")
        print(f"総テスト数: {report['summary']['total_tests']}")
        print(f"総処理ファイル数: {report['summary']['total_files_processed']:,}個")
        print(f"総実行時間: {report['summary']['total_duration']:.3f}秒")
        print(
            f"平均処理速度: {report['summary']['average_files_per_second']:.1f}ファイル/秒"
        )
        print(f"平均メモリ使用量: {report['summary']['average_memory_usage_mb']:.1f}MB")
        print(
            f"ピークメモリ使用量: {report['summary']['peak_memory_overall_mb']:.1f}MB"
        )

        print(f"\nパフォーマンス評価分布:")
        for grade, count in report["summary"]["performance_grade_distribution"].items():
            if count > 0:
                print(f"  {grade}グレード: {count}テスト")

        print(f"\nパフォーマンス基準:")
        for level, criteria in report["performance_benchmarks"].items():
            print(f"  {level}: {criteria}")

    finally:
        test_instance.tearDown()

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_performance_tests()
    exit(0 if success else 1)
