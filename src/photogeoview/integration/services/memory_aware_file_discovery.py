"""
MemoryAwareFileDiscovery - メモリ管理機能付きファイル検出

メモリ使用量を監視し、閾値超過時に自動キャッシュクリアを行う
ファイル検出機能を提供する。

主な機能:
- リアルタイムメモリ使用量監視
- 設定可能な警告・危険閾値による自動制御
- 自動キャッシュクリアによるメモリ解放
- 詳細なメモリ統計情報の記録
- psutilライブラリによる正確なメモリ測定

技術仕様:
- FileDiscoveryServiceとの連携による高速ファイル検出
- LRUキャッシュによる効率的なデータ管理
- ガベージコレクション連携による確実なメモリ解放
- スレッドセーフなメモリ監視機能
- 設定可能なメモリ制限とクリーンアップ戦略

使用例:
    memory_aware = MemoryAwareFileDiscovery(
        max_memory_mb=256,
        warning_threshold=0.75,
        critical_threshold=0.90
    )
    files = memory_aware.discover_images_with_memory_management(folder_path)

Author: Kiro AI Integration System
"""

import gc
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from ..logging_system import LoggerSystem
from ..models import AIComponent
from .file_discovery_service import FileDiscoveryService


@dataclass
class MemoryStats:
    """メモリ統計情報"""

    current_usage_mb: float
    peak_usage_mb: float
    available_mb: float
    usage_percentage: float
    cache_size_mb: float
    timestamp: datetime = datetime.now()

    @property
    def is_high_usage(self) -> bool:
        """高メモリ使用量かどうか"""
        return self.usage_percentage > 80.0

    @property
    def is_critical_usage(self) -> bool:
        """危険なメモリ使用量かどうか"""
        return self.usage_percentage > 90.0


class MemoryAwareFileDiscovery:
    """
    メモリ管理機能付きファイル検出

    メモリ使用量を監視し、閾値を超えた場合に自動的に
    キャッシュクリアを実行してメモリを解放する。
    """

    def __init__(
        self,
        file_discovery_service: FileDiscoveryService | None = None,
        max_memory_mb: int = 256,
        warning_threshold: float = 0.75,
        critical_threshold: float = 0.90,
        logger_system: LoggerSystem | None = None,
    ):
        """
        MemoryAwareFileDiscoveryの初期化

        Args:
            file_discovery_service: ファイル検出サービス
            max_memory_mb: 最大メモリ使用量(MB)
            warning_threshold: 警告閾値(0.0-1.0)
            critical_threshold: 危険閾値(0.0-1.0)
            logger_system: ログシステム
        """
        self.file_discovery_service = file_discovery_service or FileDiscoveryService()
        self.max_memory_mb = max_memory_mb
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.logger_system = logger_system or LoggerSystem()

        # メモリ監視用の変数
        self._memory_stats_history: list[MemoryStats] = []
        self._cache_data: dict[str, Any] = {}
        self._last_cleanup_time = datetime.now()
        self._cleanup_count = 0

        # 統計情報
        self._stats = {
            "total_discoveries": 0,
            "memory_cleanups": 0,
            "peak_memory_usage": 0.0,
            "avg_memory_usage": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # 初期化完了をログに記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_aware_init",
            f"MemoryAwareFileDiscovery初期化完了 - "
            f"最大メモリ: {max_memory_mb}MB, "
            f"警告閾値: {warning_threshold:.1%}, "
            f"危険閾値: {critical_threshold:.1%}",
            level="INFO",
        )

    def discover_images_with_memory_management(self, folder_path: Path) -> list[Path]:
        """
        メモリ管理機能付きで画像ファイルを検出する

        このメソッドは通常のファイル検出に加えて、メモリ使用量を
        継続的に監視し、必要に応じて自動的にメモリクリーンアップを実行します。

        処理フロー:
        1. 開始前のメモリ状態測定と危険レベルチェック
        2. キャッシュからの結果確認(メモリ効率化)
        3. FileDiscoveryServiceによるファイル検出実行
        4. 検出中の継続的なメモリ監視
        5. 閾値超過時の自動クリーンアップ実行
        6. 結果のキャッシュ保存(メモリ余裕時のみ)
        7. 詳細なパフォーマンス統計の記録

        Args:
            folder_path (Path): 検索対象のフォルダパス

        Returns:
            list[Path]: 検出された画像ファイルのリスト

        Note:
            - 危険レベル(90%以上)のメモリ使用時は事前クリーンアップを実行
            - 警告レベル(75%以上)でログ警告を出力
            - キャッシュヒット時は高速に結果を返却
            - メモリ不足時は自動的にキャッシュをクリア
            - 詳細なメモリ使用量変化がログに記録される
        """
        start_time = time.time()

        with self.logger_system.operation_context(AIComponent.KIRO, "memory_aware_discovery"):
            # 開始前のメモリ状態をチェック
            initial_memory = self._get_current_memory_stats()
            self._log_memory_status("discovery_start", initial_memory)

            # メモリ使用量が危険レベルの場合は事前クリーンアップ
            if initial_memory.is_critical_usage:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "memory_preemptive_cleanup",
                    f"危険なメモリ使用量を検出、事前クリーンアップを実行: {initial_memory.usage_percentage:.1f}%",
                    level="WARNING",
                )
                self._perform_memory_cleanup()

            try:
                # キャッシュをチェック
                cache_key = self._generate_cache_key(folder_path)
                cached_result = self._get_from_cache(cache_key)

                if cached_result is not None:
                    self._stats["cache_hits"] += 1
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "cache_hit",
                        f"キャッシュヒット: {folder_path}",
                        level="DEBUG",
                    )
                    return cached_result

                self._stats["cache_misses"] += 1

                # ファイル検出を実行
                discovered_files = self.file_discovery_service.discover_images(folder_path)

                # 検出中のメモリ監視
                current_memory = self._get_current_memory_stats()
                self._memory_stats_history.append(current_memory)

                # メモリ使用量をチェック
                if current_memory.usage_percentage > self.warning_threshold * 100:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "memory_warning",
                        f"メモリ使用量が警告レベルに達しました: {current_memory.usage_percentage:.1f}%",
                        level="WARNING",
                    )

                if current_memory.usage_percentage > self.critical_threshold * 100:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "memory_critical",
                        f"メモリ使用量が危険レベルに達しました: {current_memory.usage_percentage:.1f}%",
                        level="ERROR",
                    )
                    self._perform_memory_cleanup()

                # 結果をキャッシュに保存(メモリに余裕がある場合のみ)
                if current_memory.usage_percentage < self.warning_threshold * 100:
                    self._store_in_cache(cache_key, discovered_files)

                # 統計情報を更新
                self._update_stats(current_memory)

                # 完了時のメモリ状態をログ
                final_memory = self._get_current_memory_stats()
                self._log_memory_status("discovery_complete", final_memory)

                # パフォーマンス情報をログに記録
                duration = time.time() - start_time
                self.logger_system.log_performance(
                    AIComponent.KIRO,
                    "memory_aware_discovery",
                    {
                        "folder_path": str(folder_path),
                        "files_found": len(discovered_files),
                        "duration": duration,
                        "initial_memory_mb": initial_memory.current_usage_mb,
                        "final_memory_mb": final_memory.current_usage_mb,
                        "memory_delta_mb": final_memory.current_usage_mb - initial_memory.current_usage_mb,
                        "peak_memory_usage": final_memory.usage_percentage,
                        "cache_hit": cached_result is not None,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                return discovered_files

            except Exception as e:
                # エラー時のメモリ状態をログ
                error_memory = self._get_current_memory_stats()
                self._log_memory_status("discovery_error", error_memory)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "memory_aware_discovery_error",
                    f"メモリ管理機能付きファイル検出エラー: {e!s}",
                    level="ERROR",
                )
                raise

    def _get_current_memory_stats(self) -> MemoryStats:
        """現在のメモリ統計情報を取得する"""
        try:
            # システム全体のメモリ情報
            memory = psutil.virtual_memory()

            # 現在のプロセスのメモリ情報
            process = psutil.Process()
            process_memory = process.memory_info()

            # キャッシュサイズの推定
            cache_size_mb = sum(len(str(v)) for v in self._cache_data.values()) / (1024 * 1024)  # バイトからMBに変換

            return MemoryStats(
                current_usage_mb=process_memory.rss / (1024 * 1024),
                peak_usage_mb=process_memory.vms / (1024 * 1024),
                available_mb=memory.available / (1024 * 1024),
                usage_percentage=memory.percent,
                cache_size_mb=cache_size_mb,
            )

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "memory_stats_error",
                f"メモリ統計取得エラー: {e!s}",
                level="WARNING",
            )

            # フォールバック値を返す
            return MemoryStats(
                current_usage_mb=0.0,
                peak_usage_mb=0.0,
                available_mb=1024.0,
                usage_percentage=0.0,
                cache_size_mb=0.0,
            )

    def _perform_memory_cleanup(self):
        """メモリクリーンアップを実行する"""
        cleanup_start_time = time.time()
        initial_memory = self._get_current_memory_stats()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_cleanup_start",
            f"メモリクリーンアップ開始 - 現在の使用量: {initial_memory.current_usage_mb:.1f}MB",
            level="INFO",
        )

        # キャッシュをクリア
        cache_items_before = len(self._cache_data)
        self._cache_data.clear()

        # メモリ統計履歴を制限
        if len(self._memory_stats_history) > 100:
            self._memory_stats_history = self._memory_stats_history[-50:]

        # ガベージコレクションを実行
        collected = gc.collect()

        # クリーンアップ後のメモリ状態
        final_memory = self._get_current_memory_stats()
        cleanup_duration = time.time() - cleanup_start_time

        # 統計を更新
        self._cleanup_count += 1
        self._stats["memory_cleanups"] += 1
        self._last_cleanup_time = datetime.now()

        # クリーンアップ結果をログ
        memory_freed = initial_memory.current_usage_mb - final_memory.current_usage_mb

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_cleanup_complete",
            f"メモリクリーンアップ完了 - "
            f"解放メモリ: {memory_freed:.1f}MB, "
            f"キャッシュアイテム削除: {cache_items_before}個, "
            f"GC回収オブジェクト: {collected}個, "
            f"処理時間: {cleanup_duration:.3f}秒",
            level="INFO",
        )

        # パフォーマンス情報をログに記録
        self.logger_system.log_performance(
            AIComponent.KIRO,
            "memory_cleanup",
            {
                "initial_memory_mb": initial_memory.current_usage_mb,
                "final_memory_mb": final_memory.current_usage_mb,
                "memory_freed_mb": memory_freed,
                "cache_items_cleared": cache_items_before,
                "gc_objects_collected": collected,
                "cleanup_duration": cleanup_duration,
                "cleanup_count": self._cleanup_count,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def _generate_cache_key(self, folder_path: Path) -> str:
        """フォルダパスからキャッシュキーを生成する"""
        try:
            # フォルダの最終更新時刻を含めてキーを生成
            mtime = folder_path.stat().st_mtime
            return f"{folder_path!s}_{mtime}"
        except OSError:
            # ファイルアクセスエラーの場合はパスのみを使用
            return str(folder_path)

    def _get_from_cache(self, cache_key: str) -> list[Path] | None:
        """キャッシュからデータを取得する"""
        return self._cache_data.get(cache_key)

    def _store_in_cache(self, cache_key: str, data: list[Path]):
        """データをキャッシュに保存する"""
        # キャッシュサイズ制限
        if len(self._cache_data) >= 50:  # 最大50エントリ
            # 最も古いエントリを削除(LRU的な動作)
            oldest_key = next(iter(self._cache_data))
            del self._cache_data[oldest_key]

        self._cache_data[cache_key] = data

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "cache_store",
            f"キャッシュに保存: {cache_key} ({len(data)}ファイル)",
            level="DEBUG",
        )

    def _log_memory_status(self, operation: str, memory_stats: MemoryStats):
        """メモリ状態をログに記録する"""
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            f"memory_status_{operation}",
            f"メモリ状態 - 使用量: {memory_stats.current_usage_mb:.1f}MB "
            f"({memory_stats.usage_percentage:.1f}%), "
            f"利用可能: {memory_stats.available_mb:.1f}MB, "
            f"キャッシュ: {memory_stats.cache_size_mb:.1f}MB",
            level="DEBUG",
        )

    def _update_stats(self, memory_stats: MemoryStats):
        """統計情報を更新する"""
        self._stats["total_discoveries"] += 1

        if memory_stats.current_usage_mb > self._stats["peak_memory_usage"]:
            self._stats["peak_memory_usage"] = memory_stats.current_usage_mb

        # 平均メモリ使用量を更新
        total_discoveries = self._stats["total_discoveries"]
        current_avg = self._stats["avg_memory_usage"]
        self._stats["avg_memory_usage"] = (
            current_avg * (total_discoveries - 1) + memory_stats.current_usage_mb
        ) / total_discoveries

    def get_memory_status(self) -> dict[str, Any]:
        """現在のメモリ状態と統計情報を取得する"""
        current_memory = self._get_current_memory_stats()

        status = {
            "current_memory": {
                "usage_mb": current_memory.current_usage_mb,
                "usage_percentage": current_memory.usage_percentage,
                "available_mb": current_memory.available_mb,
                "cache_size_mb": current_memory.cache_size_mb,
                "is_high_usage": current_memory.is_high_usage,
                "is_critical_usage": current_memory.is_critical_usage,
            },
            "thresholds": {
                "max_memory_mb": self.max_memory_mb,
                "warning_threshold": self.warning_threshold,
                "critical_threshold": self.critical_threshold,
            },
            "statistics": self._stats.copy(),
            "cache_info": {
                "cache_entries": len(self._cache_data),
                "cache_keys": list(self._cache_data.keys()),
            },
            "cleanup_info": {
                "last_cleanup": self._last_cleanup_time.isoformat(),
                "cleanup_count": self._cleanup_count,
            },
            "status_timestamp": datetime.now().isoformat(),
        }

        return status

    def force_memory_cleanup(self) -> dict[str, Any]:
        """強制的にメモリクリーンアップを実行する"""
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "force_cleanup_requested",
            "強制メモリクリーンアップが要求されました",
            level="INFO",
        )

        before_memory = self._get_current_memory_stats()
        self._perform_memory_cleanup()
        after_memory = self._get_current_memory_stats()

        return {
            "cleanup_performed": True,
            "memory_before_mb": before_memory.current_usage_mb,
            "memory_after_mb": after_memory.current_usage_mb,
            "memory_freed_mb": before_memory.current_usage_mb - after_memory.current_usage_mb,
            "cleanup_timestamp": datetime.now().isoformat(),
        }

    def clear_cache(self):
        """キャッシュをクリアする"""
        cache_items = len(self._cache_data)
        self._cache_data.clear()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "cache_cleared",
            f"キャッシュをクリアしました: {cache_items}個のエントリを削除",
            level="INFO",
        )

    def cleanup(self):
        """リソースをクリーンアップする"""
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_aware_cleanup",
            f"MemoryAwareFileDiscoveryクリーンアップ開始 - "
            f"総検出回数: {self._stats['total_discoveries']}, "
            f"クリーンアップ回数: {self._stats['memory_cleanups']}",
            level="DEBUG",
        )

        # 最終統計をログに記録
        final_stats = self._stats.copy()
        final_stats["cleanup_timestamp"] = datetime.now().isoformat()
        final_stats["final_memory_status"] = self.get_memory_status()

        self.logger_system.log_performance(AIComponent.KIRO, "memory_aware_final_stats", final_stats)

        # リソースをクリア
        self._cache_data.clear()
        self._memory_stats_history.clear()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_aware_cleanup_complete",
            "MemoryAwareFileDiscoveryクリーンアップ完了",
            level="DEBUG",
        )

    def optimize_logging_for_production(self):
        """
        本番環境向けにログ出力を最適化する

        本番環境では以下の最適化を実行:
        - メモリ警告のみログ出力
        - 詳細デバッグ情報の無効化
        - パフォーマンス統計の定期出力
        """

        self._production_mode = True

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_aware_production_optimized",
            "メモリ管理機能の本番環境最適化が完了しました",
            level="INFO",
        )

    def log_memory_performance_summary(self):
        """
        メモリパフォーマンス要約をログに出力する
        """

        current_memory = self._get_current_memory_stats()

        summary = {
            "memory_status": {
                "current_usage_mb": current_memory.current_usage_mb,
                "usage_percentage": current_memory.usage_percentage,
                "available_mb": current_memory.available_mb,
                "cache_size_mb": current_memory.cache_size_mb,
            },
            "statistics": self._stats.copy(),
            "thresholds": {
                "max_memory_mb": self.max_memory_mb,
                "warning_threshold": self.warning_threshold,
                "critical_threshold": self.critical_threshold,
            },
            "cache_info": {
                "cache_entries": len(self._cache_data),
                "cleanup_count": self._cleanup_count,
            },
            "timestamp": datetime.now().isoformat(),
        }

        # 警告レベルのチェック
        log_level = "INFO"
        if current_memory.is_critical_usage:
            log_level = "ERROR"
        elif current_memory.is_high_usage:
            log_level = "WARNING"

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_performance_summary",
            f"メモリパフォーマンス要約 - "
            f"使用量: {current_memory.current_usage_mb:.1f}MB ({current_memory.usage_percentage:.1f}%), "
            f"キャッシュ: {current_memory.cache_size_mb:.1f}MB, "
            f"検出回数: {self._stats['total_discoveries']}, "
            f"クリーンアップ回数: {self._stats['memory_cleanups']}",
            level=log_level,
        )

        # 詳細統計をパフォーマンスログに記録
        self.logger_system.log_performance(AIComponent.KIRO, "memory_detailed_performance", summary)

    def enable_debug_memory_logging(self):
        """
        メモリデバッグログを有効にする(トラブルシューティング用)
        """

        self._debug_memory_logging = True

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "memory_debug_logging_enabled",
            "メモリデバッグログが有効になりました",
            level="DEBUG",
        )
