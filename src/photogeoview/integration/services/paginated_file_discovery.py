"""
PaginatedFileDiscovery - 段階的ファイル読み込み機能

大量ファイル対応のための段階的読み込み(ページネーション)機能を提供する。
バッチサイズを設定して、メモリ効率的にファイルを処理する。

主な機能:
- 大量ファイル(1000個以上)の効率的な処理
- 設定可能なバッチサイズ(デフォルト100ファイル)
- イテレータパターンによる順次処理
- 詳細な進行状況追跡とパフォーマンス監視
- メモリ使用量の推定と最適化

技術仕様:
- FileDiscoveryServiceとの連携による高速ファイル検出
- バッチ単位での処理により一定のメモリ使用量を維持
- 統計情報の自動収集とパフォーマンス分析
- エラー耐性のある安全な処理フロー

使用例:
    paginated = PaginatedFileDiscovery(page_size=50)
    paginated.initialize_folder(Path("/large/folder"))

    while paginated.has_more_files():
        batch = paginated.get_next_batch()
        process_batch(batch.files)

Author: Kiro AI Integration System
"""

import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..logging_system import LoggerSystem
from ..models import AIComponent
from .file_discovery_service import FileDiscoveryService


@dataclass
class FileBatch:
    """ファイルバッチ情報"""

    files: list[Path]
    batch_number: int
    total_batches: int
    start_index: int
    end_index: int
    batch_size: int
    processing_time: float = 0.0

    @property
    def is_last_batch(self) -> bool:
        """最後のバッチかどうか"""
        return self.batch_number >= self.total_batches - 1

class PaginatedFileDiscovery:
    """
    段階的ファイル読み込み機能

    大量のファイルがあるフォルダに対しモリ効率的な
    段階的読み込み(ページネーション)を提供する。
    """

    def __init__(
        self,
        file_discovery_service: FileDiscoveryService | None = None,
        page_size: int = 100,
        logger_system: LoggerSystem | None = None,
    ):
        """
        PaginatedFileDiscoveryの初期化

        Args:
            file_discovery_service: ファイル検出サービス
            page_size: バッチサイズ(デフォルト100ファイル)
            logger_system: ログシステム
        """
        self.file_discovery_service = file_discovery_service or FileDiscoveryService()
        self.page_size = page_size
        self.logger_system = logger_system or LoggerSystem()

        # 現在の状態
        self._current_folder: Path | None = None
        self._all_files: list[Path] = []
        self._current_batch_index = 0
        self._total_batches = 0
        self._is_initialized = False

        # 統計情報
        self._stats = {
            "total_files_discovered": 0,
            "total_batches_processed": 0,
            "total_processing_time": 0.0,
            "avg_batch_processing_time": 0.0,
            "last_folder_scan_time": None,
        }

        # 初期化完了をログに記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "paginated_discovery_init",
            f"PaginatedFileDiscovery初期化完了 - バッチサイズ: {self.page_size}",
            level="INFO",
        )

    def initialize_folder(self, folder_path: Path) -> dict[str, Any]:
        """
        フォルダを初期化し、全ファイルを検出する

        このメソッドは指定されたフォルダ内の全画像ファイルを検出し、
        段階的読み込み用の内部状態を初期化します。

        処理内容:
        1. FileDiscoveryServiceによる全ファイル検出
        2. バッチ数の計算と内部状態の初期化
        3. メモリ使用量の推定
        4. 初期化統計情報の記録

        Args:
            folder_path (Path): 対象フォルダパス

        Returns:
            dict[str, Any]: 初期化結果の詳細情報
                - total_files: 検出されたファイル総数
                - total_batches: 計算されたバッチ総数
                - batch_size: 設定されたバッチサイズ
                - initialization_time: 初期化にかかった時間
                - estimated_memory_per_batch: バッチあたりの推定メモリ使用量

        Raises:
            Exception: フォルダアクセスエラーまたはファイル検出エラー

        Note:
            - 初期化後はhas_more_files()とget_next_batch()が使用可能
            - 大量ファイルの場合、初期化に時間がかかる場合があります
        """
        start_time = time.time()

        with self.logger_system.operation_context(
            AIComponent.KIRO, "paginated_folder_init"
        ):
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "folder_init_start",
                f"段階的読み込み用フォルダ初期化開始: {folder_path}",
            )

            try:
                # 全ファイルを検出
                self._all_files = self.file_discovery_service.discover_images(
                    folder_path
                )
                self._current_folder = folder_path
                self._current_batch_index = 0

                # バッチ数を計算
                if self._all_files:
                    self._total_batches = (
                        len(self._all_files) + self.page_size - 1
                    ) // self.page_size
                else:
                    self._total_batches = 0

                self._is_initialized = True

                # 初期化時間を記録
                init_duration = time.time() - start_time
                self._stats["last_folder_scan_time"] = datetime.now()
                self._stats["total_files_discovered"] = len(self._all_files)

                # 初期化結果
                init_result = {
                    "folder_path": str(folder_path),
                    "total_files": len(self._all_files),
                    "total_batches": self._total_batches,
                    "batch_size": self.page_size,
                    "initialization_time": init_duration,
                    "files_per_batch": self.page_size,
                    "last_batch_size": (
                        len(self._all_files) % self.page_size if self._all_files else 0
                    ),
                    "estimated_memory_per_batch": self._estimate_memory_per_batch(),
                    "initialization_timestamp": datetime.now().isoformat(),
                }

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "folder_init_complete",
                    f"フォルダ初期化完了: {len(self._all_files)}ファイル, "
                    f"{self._total_batches}バッチ, {init_duration:.2f}秒",
                )

                # パフォーマンス情報をログに記録
                self.logger_system.log_performance(
                    AIComponent.KIRO, "paginated_folder_initialization", init_result
                )

                return init_result

            except Exception as e:
                init_duration = time.time() - start_time
                {
                    "folder_path": str(folder_path),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "initialization_time": init_duration,
                }

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "folder_init_error",
                    f"フォルダ初期化エラー: {folder_path} - {e!s}",
                    level="ERROR",
                )

                self._is_initialized = False
                raise

    def get_next_batch(self) -> FileBatch | None:
        """
        次のバッチを取得する

        現在のバッチインデックスに基づいて次のファイルバッチを生成し、
        内部状態を更新します。

        処理内容:
        1. 初期化状態とバッチ可用性の確認
        2. バッチ範囲の計算(start_index, end_index)
        3. FileBatchオブジェクトの生成
        4. 統計情報の更新とパフォーマンス記録
        5. 次のバッチインデックスへの更新

        Returns:
            Optional[FileBatch]: 次のファイルバッチ、または利用可能なバッチがない場合はNone
                FileBatch属性:
                - files: バッチ内のファイルパスリスト
                - batch_number: 現在のバッチ番号(0から開始)
                - total_batches: 総バッチ数
                - start_index, end_index: ファイルリスト内の範囲
                - processing_time: バッチ生成にかかった時間

        Note:
            - フォルダが初期化されていない場合はNoneを返却
            - 最後のバッチの場合、is_last_batchプロパティがTrueになる
            - バッチ取得後は自動的に次のバッチインデックスに進む
        """
        if not self._is_initialized:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "batch_request_error",
                "フォルダが初期化されていません",
                level="WARNING",
            )
            return None

        if not self.has_more_files():
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "batch_request_complete",
                "すべてのバッチが処理済みです",
                level="DEBUG",
            )
            return None

        batch_start_time = time.time()

        # バッチの範囲を計算
        start_index = self._current_batch_index * self.page_size
        end_index = min(start_index + self.page_size, len(self._all_files))

        # バッチファイルを取得
        batch_files = self._all_files[start_index:end_index]

        # バッチ処理時間を記録
        batch_processing_time = time.time() - batch_start_time

        # FileBatchオブジェクトを作成
        file_batch = FileBatch(
            files=batch_files,
            batch_number=self._current_batch_index,
            total_batches=self._total_batches,
            start_index=start_index,
            end_index=end_index,
            batch_size=len(batch_files),
            processing_time=batch_processing_time,
        )

        # 統計情報を更新
        self._stats["total_batches_processed"] += 1
        self._stats["total_processing_time"] += batch_processing_time
        self._stats["avg_batch_processing_time"] = (
            self._stats["total_processing_time"]
            / self._stats["total_batches_processed"]
        )

        # バッチ情報をログに記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "batch_retrieved",
            f"バッチ {self._current_batch_index + 1}/{self._total_batches} 取得完了: "
            f"{len(batch_files)}ファイル ({start_index}-{end_index - 1})",
            level="DEBUG",
        )

        # 詳細なバッチ情報をログに記録
        batch_details = {
            "batch_number": file_batch.batch_number,
            "total_batches": file_batch.total_batches,
            "batch_size": file_batch.batch_size,
            "start_index": file_batch.start_index,
            "end_index": file_batch.end_index,
            "processing_time": file_batch.processing_time,
            "is_last_batch": file_batch.is_last_batch,
            "folder_path": str(self._current_folder),
            "timestamp": datetime.now().isoformat(),
        }

        self.logger_system.log_performance(
            AIComponent.KIRO, "batch_processing", batch_details
        )

        # 次のバッチインデックスに進む
        self._current_batch_index += 1

        return file_batch

    def has_more_files(self) -> bool:
        """
        さらにファイルがあるかチェックする

        Returns:
            まだ処理されていないファイルがある場合True
        """
        if not self._is_initialized:
            return False

        has_more = self._current_batch_index < self._total_batches

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "has_more_check",
            f"残りバッチ確認: {has_more} "
            f"(現在: {self._current_batch_index}/{self._total_batches})",
            level="DEBUG",
        )

        return has_more

    def reset_pagination(self):
        """ページネーションをリセットして最初から開始する"""
        self._current_batch_index = 0

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "pagination_reset",
            f"ページネーションリセット - 総バッチ数: {self._total_batches}",
            level="DEBUG",
        )

    def get_pagination_status(self) -> dict[str, Any]:
        """
        現在のページネーション状態を取得する

        Returns:
            ページネーション状態の詳細情報
        """
        if not self._is_initialized:
            return {"initialized": False, "error": "フォルダが初期化されていません"}

        progress_percentage = (
            (self._current_batch_index / self._total_batches * 100)
            if self._total_batches > 0
            else 0
        )

        status = {
            "initialized": self._is_initialized,
            "folder_path": str(self._current_folder) if self._current_folder else None,
            "total_files": len(self._all_files),
            "total_batches": self._total_batches,
            "current_batch_index": self._current_batch_index,
            "processed_batches": self._current_batch_index,
            "remaining_batches": max(
                0, self._total_batches - self._current_batch_index
            ),
            "progress_percentage": progress_percentage,
            "batch_size": self.page_size,
            "has_more_files": self.has_more_files(),
            "stats": self._stats.copy(),
            "status_timestamp": datetime.now().isoformat(),
        }

        return status

    def get_batch_iterator(self) -> Iterator[FileBatch]:
        """
        すべてのバッチを順次処理するイテレータを取得する

        Returns:
            FileBatchのイテレータ
        """
        if not self._is_initialized:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "iterator_error",
                "フォルダが初期化されていないためイテレータを作成できません",
                level="WARNING",
            )
            return

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "iterator_start",
            f"バッチイテレータ開始 - 総バッチ数: {self._total_batches}",
            level="DEBUG",
        )

        # ページネーションをリセット
        self.reset_pagination()

        while self.has_more_files():
            batch = self.get_next_batch()
            if batch:
                yield batch

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "iterator_complete",
            f"バッチイテレータ完了 - 処理済みバッチ数: {self._stats['total_batches_processed']}",
            level="DEBUG",
        )

    def _estimate_memory_per_batch(self) -> float:
        """
        バッチあたりの推定メモリ使用量を計算する(MB単位)

        Returns:
            推定メモリ使用量(MB)
        """
        # 基本的な推定: ファイルパス情報 + オーバーヘッド
        # 1ファイルあたり約1KB(パス情報、メタデータ等)と仮定
        estimated_mb = (self.page_size * 1024) / (1024 * 1024)  # KB to MB

        return round(estimated_mb, 2)

    def cleanup(self):
        """リソースをクリーンアップする"""
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "paginated_cleanup",
            f"PaginatedFileDiscoveryクリーンアップ開始 - "
            f"処理済みバッチ数: {self._stats['total_batches_processed']}",
            level="DEBUG",
        )

        # 状態をリセット
        self._current_folder = None
        self._all_files.clear()
        self._current_batch_index = 0
        self._total_batches = 0
        self._is_initialized = False

        # 最終統計をログに記録
        final_stats = self._stats.copy()
        final_stats["cleanup_timestamp"] = datetime.now().isoformat()

        self.logger_system.log_performance(
            AIComponent.KIRO, "paginated_discovery_final_stats", final_stats
        )

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "paginated_cleanup_complete",
            "PaginatedFileDiscoveryクリーンアップ完了",
            level="DEBUG",
        )
