"""
FileDiscoveryCache - ファイル検出結果キャッシュシステム

ファイル検出とバリデーション結果の効率的なキャッシュ管理システム。
mtimeベースのキャッシュキー生成により、ファイル変更を自動検出し、
LRUアルゴリズムによる効率的なメモリ使用を実現します。

主な機能:
- ファイル検出結果の高速キャッシュ（mtimeベース）
- バリデーション結果の永続化キャッシュ
- フォルダスキャン結果の一括キャッシュ
- LRUアルゴリズムによる自動メモリ管理
- 詳細なキャッシュヒット率統計

技術仕様:
- スレッドセーフなキャッシュ操作（RLock使用）
- 自動期限切れ検出（ファイルmtime比較）
- 設定可能なキャッシュサイズ制限
- メモリ使用量の継続監視
- 統合ログシステムによる詳細な動作記録

キャッシュ戦略:
- ファイルキャッシュ: ファイルサイズ + mtime
- フォルダキャッシュ: フォルダmtime + ハッシュ
- バリデーションキャッシュ: ファイルサイズ + mtime
- 自動クリーンアップ: 定期的な期限切れエントリ削除

Author: Kiro AI Integration System
"""

import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict
import threading

from ..models import AIComponent
from ..logging_system import LoggerSystem
from ..error_handling import IntegratedErrorHandler, ErrorCategory


@dataclass
class FileDiscoveryResult:
    """ファイル検出結果のデータ構造"""
    file_path: Path
    is_valid: bool
    file_size: int
    modified_time: float
    discovery_time: datetime
    validation_time: Optional[float] = None
    error_message: Optional[str] = None
    cache_key: str = field(init=False)

    def __post_init__(self):
        """キャッシュキーを自動生成"""
        self.cache_key = self._generate_cache_key()

    def _generate_cache_key(self) -> str:
        """mtimeベースのキャッシュキーを生成"""
        return f"file_{self.file_path.stem}_{self.file_size}_{int(self.modified_time)}"

    @property
    def is_expired(self) -> bool:
        """キャッシュエントリが期限切れかチェック"""
        try:
            current_mtime = self.file_path.stat().st_mtime
            return current_mtime != self.modified_time
        except (OSError, FileNotFoundError):
            return True


@dataclass
class FolderScanCache:
    """フォルダスキャン結果のキャッシュ"""
    folder_path: Path
    scan_time: datetime
    file_results: List[FileDiscoveryResult]
    total_files_scanned: int
    scan_duration: float
    cache_key: str = field(init=False)

    def __post_init__(self):
        """キャッシュキーを自動生成"""
        self.cache_key = self._generate_cache_key()

    def _generate_cache_key(self) -> str:
        """フォルダのmtimeベースのキャッシュキーを生成"""
        try:
            folder_stat = self.folder_path.stat()
            return f"folder_{hash(str(self.folder_path))}_{int(folder_stat.st_mtime)}"
        except (OSError, FileNotFoundError):
            return f"folder_{hash(str(self.folder_path))}_{int(time.time())}"

    @property
    def is_expired(self) -> bool:
        """フォルダキャッシュが期限切れかチェック"""
        try:
            current_mtime = self.folder_path.stat().st_mtime
            expected_mtime = int(self.cache_key.split('_')[-1])
            return current_mtime != expected_mtime
        except (OSError, FileNotFoundError, ValueError):
            return True


@dataclass
class CacheMetrics:
    """キャッシュメトリクス"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    entries: int = 0
    memory_usage_bytes: int = 0
    hit_rate: float = 0.0

    def update_hit_rate(self):
        """ヒット率を更新"""
        total = self.hits + self.misses
        self.hit_rate = self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で返す"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "entries": self.entries,
            "memory_usage_mb": self.memory_usage_bytes / 1024 / 1024,
            "hit_rate": self.hit_rate
        }


class FileDiscoveryCache:
    """
    ファイル検出結果のキャッシュシステム

    機能:
    - ファイル検出結果のキャッシュ
    - バリデーション結果のキャッシュ
    - LRUベースの効率的なメモリ管理
    - キャッシュヒット率の監視
    """

    def __init__(self,
                 max_file_entries: int = 2000,
                 max_folder_entries: int = 100,
                 max_memory_mb: float = 50.0,
                 logger_system: Optional[LoggerSystem] = None):
        """
        FileDiscoveryCacheの初期化

        Args:
            max_file_entries: 最大ファイルエントリ数
            max_folder_entries: 最大フォルダエントリ数
            max_memory_mb: 最大メモリ使用量（MB）
            logger_system: ログシステム
        """

        self.max_file_entries = max_file_entries
        self.max_folder_entries = max_folder_entries
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)

        # ログシステムとエラーハンドラー
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # キャッシュストレージ（LRU順序付き辞書）
        self._file_cache: OrderedDict[str, FileDiscoveryResult] = OrderedDict()
        self._folder_cache: OrderedDict[str, FolderScanCache] = OrderedDict()
        self._validation_cache: OrderedDict[str, bool] = OrderedDict()

        # スレッドセーフティ
        self._lock = threading.RLock()

        # メトリクス
        self.file_metrics = CacheMetrics()
        self.folder_metrics = CacheMetrics()
        self.validation_metrics = CacheMetrics()

        # 設定
        self.default_ttl_seconds = 3600  # 1時間
        self.cleanup_interval = timedelta(minutes=10)
        self.last_cleanup = datetime.now()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "file_discovery_cache_init",
            f"FileDiscoveryCache初期化完了 - "
            f"ファイルエントリ上限: {max_file_entries}, "
            f"フォルダエントリ上限: {max_folder_entries}, "
            f"メモリ上限: {max_memory_mb}MB"
        )

    def cache_file_result(self, file_path: Path, is_valid: bool,
                         validation_time: Optional[float] = None,
                         error_message: Optional[str] = None) -> bool:
        """
        ファイル検出結果をキャッシュに保存する

        ファイルの検出・バリデーション結果を効率的にキャッシュし、
        後続の同一ファイルアクセス時の高速化を図ります。

        処理内容:
        1. ファイル情報（サイズ、mtime）の取得
        2. FileDiscoveryResultオブジェクトの生成
        3. 既存エントリの削除（重複防止）
        4. メモリ制限チェックと必要に応じた古いエントリ削除
        5. 新しいエントリの追加とLRU順序の更新
        6. メトリクス情報の更新

        Args:
            file_path (Path): ファイルパス
            is_valid (bool): バリデーション結果
            validation_time (Optional[float]): バリデーション時間（秒）
            error_message (Optional[str]): エラーメッセージ（エラー時のみ）

        Returns:
            bool: キャッシュ成功時True、失敗時False

        Note:
            - mtimeベースのキャッシュキーにより自動的にファイル変更を検出
            - LRU順序により最近使用されたエントリが優先保持される
            - メモリ制限に達した場合は古いエントリが自動削除される
            - スレッドセーフな操作が保証される
        """

        try:
            with self._lock:
                # ファイル情報を取得
                try:
                    file_stat = file_path.stat()
                    file_size = file_stat.st_size
                    modified_time = file_stat.st_mtime
                except (OSError, FileNotFoundError) as e:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "cache_file_stat_error",
                        f"ファイル情報取得エラー: {file_path} - {str(e)}",
                        level="WARNING"
                    )
                    return False

                # FileDiscoveryResultを作成
                result = FileDiscoveryResult(
                    file_path=file_path,
                    is_valid=is_valid,
                    file_size=file_size,
                    modified_time=modified_time,
                    discovery_time=datetime.now(),
                    validation_time=validation_time,
                    error_message=error_message
                )

                # 既存エントリがあれば削除
                if result.cache_key in self._file_cache:
                    del self._file_cache[result.cache_key]

                # メモリ制限チェックと必要に応じて削除
                self._evict_file_entries_if_needed()

                # 新しいエントリを追加
                self._file_cache[result.cache_key] = result
                self._file_cache.move_to_end(result.cache_key)

                # メトリクス更新
                self.file_metrics.entries = len(self._file_cache)
                self._update_memory_usage()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "file_cache_add",
                    f"ファイル結果をキャッシュ: {file_path.name} - 有効: {is_valid}",
                    level="DEBUG"
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "cache_file_result",
                    "file_path": str(file_path),
                    "is_valid": is_valid
                },
                AIComponent.KIRO
            )
            return False

    def get_cached_file_result(self, file_path: Path) -> Optional[FileDiscoveryResult]:
        """
        キャッシュされたファイル結果を取得

        Args:
            file_path: ファイルパス

        Returns:
            キャッシュされた結果、またはNone
        """

        try:
            with self._lock:
                # キャッシュキーを生成
                try:
                    file_stat = file_path.stat()
                    cache_key = f"file_{file_path.stem}_{file_stat.st_size}_{int(file_stat.st_mtime)}"
                except (OSError, FileNotFoundError):
                    self.file_metrics.misses += 1
                    self.file_metrics.update_hit_rate()
                    return None

                # キャッシュから取得
                if cache_key in self._file_cache:
                    result = self._file_cache[cache_key]

                    # 期限切れチェック
                    if result.is_expired:
                        del self._file_cache[cache_key]
                        self.file_metrics.misses += 1
                        self.file_metrics.entries = len(self._file_cache)
                        self.file_metrics.update_hit_rate()

                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "file_cache_expired",
                            f"期限切れキャッシュエントリを削除: {file_path.name}",
                            level="DEBUG"
                        )
                        return None

                    # LRU更新（最近使用したものを末尾に移動）
                    self._file_cache.move_to_end(cache_key)

                    # メトリクス更新
                    self.file_metrics.hits += 1
                    self.file_metrics.update_hit_rate()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "file_cache_hit",
                        f"ファイルキャッシュヒット: {file_path.name} - 有効: {result.is_valid}",
                        level="DEBUG"
                    )

                    return result

                # キャッシュミス
                self.file_metrics.misses += 1
                self.file_metrics.update_hit_rate()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "file_cache_miss",
                    f"ファイルキャッシュミス: {file_path.name}",
                    level="DEBUG"
                )

                return None

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "get_cached_file_result",
                    "file_path": str(file_path)
                },
                AIComponent.KIRO
            )
            return None

    def cache_folder_scan(self, folder_path: Path, file_results: List[FileDiscoveryResult],
                         total_files_scanned: int, scan_duration: float) -> bool:
        """
        フォルダスキャン結果をキャッシュ

        Args:
            folder_path: フォルダパス
            file_results: ファイル結果リスト
            total_files_scanned: スキャンしたファイル総数
            scan_duration: スキャン時間

        Returns:
            キャッシュ成功時True
        """

        try:
            with self._lock:
                # FolderScanCacheを作成
                folder_cache = FolderScanCache(
                    folder_path=folder_path,
                    scan_time=datetime.now(),
                    file_results=file_results,
                    total_files_scanned=total_files_scanned,
                    scan_duration=scan_duration
                )

                # 既存エントリがあれば削除
                if folder_cache.cache_key in self._folder_cache:
                    del self._folder_cache[folder_cache.cache_key]

                # メモリ制限チェックと必要に応じて削除
                self._evict_folder_entries_if_needed()

                # 新しいエントリを追加
                self._folder_cache[folder_cache.cache_key] = folder_cache
                self._folder_cache.move_to_end(folder_cache.cache_key)

                # メトリクス更新
                self.folder_metrics.entries = len(self._folder_cache)
                self._update_memory_usage()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "folder_cache_add",
                    f"フォルダスキャン結果をキャッシュ: {folder_path} - "
                    f"{len(file_results)}個のファイル, {scan_duration:.2f}秒"
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "cache_folder_scan",
                    "folder_path": str(folder_path),
                    "file_count": len(file_results)
                },
                AIComponent.KIRO
            )
            return False

    def get_cached_folder_scan(self, folder_path: Path) -> Optional[FolderScanCache]:
        """
        キャッシュされたフォルダスキャン結果を取得

        Args:
            folder_path: フォルダパス

        Returns:
            キャッシュされた結果、またはNone
        """

        try:
            with self._lock:
                # キャッシュキーを生成
                try:
                    folder_stat = folder_path.stat()
                    cache_key = f"folder_{hash(str(folder_path))}_{int(folder_stat.st_mtime)}"
                except (OSError, FileNotFoundError):
                    self.folder_metrics.misses += 1
                    self.folder_metrics.update_hit_rate()
                    return None

                # キャッシュから取得
                if cache_key in self._folder_cache:
                    folder_cache = self._folder_cache[cache_key]

                    # 期限切れチェック
                    if folder_cache.is_expired:
                        del self._folder_cache[cache_key]
                        self.folder_metrics.misses += 1
                        self.folder_metrics.entries = len(self._folder_cache)
                        self.folder_metrics.update_hit_rate()

                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "folder_cache_expired",
                            f"期限切れフォルダキャッシュエントリを削除: {folder_path}",
                            level="DEBUG"
                        )
                        return None

                    # LRU更新
                    self._folder_cache.move_to_end(cache_key)

                    # メトリクス更新
                    self.folder_metrics.hits += 1
                    self.folder_metrics.update_hit_rate()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "folder_cache_hit",
                        f"フォルダキャッシュヒット: {folder_path} - "
                        f"{len(folder_cache.file_results)}個のファイル"
                    )

                    return folder_cache

                # キャッシュミス
                self.folder_metrics.misses += 1
                self.folder_metrics.update_hit_rate()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "folder_cache_miss",
                    f"フォルダキャッシュミス: {folder_path}",
                    level="DEBUG"
                )

                return None

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "get_cached_folder_scan",
                    "folder_path": str(folder_path)
                },
                AIComponent.KIRO
            )
            return None

    def cache_validation_result(self, file_path: Path, is_valid: bool) -> bool:
        """
        バリデーション結果をキャッシュ

        Args:
            file_path: ファイルパス
            is_valid: バリデーション結果

        Returns:
            キャッシュ成功時True
        """

        try:
            with self._lock:
                # バリデーション用キャッシュキーを生成（ファイルサイズ+mtime基準）
                try:
                    file_stat = file_path.stat()
                    cache_key = f"valid_{file_path.stem}_{file_stat.st_size}_{int(file_stat.st_mtime)}"
                except (OSError, FileNotFoundError):
                    return False

                # 既存エントリがあれば削除
                if cache_key in self._validation_cache:
                    del self._validation_cache[cache_key]

                # メモリ制限チェック
                self._evict_validation_entries_if_needed()

                # 新しいエントリを追加
                self._validation_cache[cache_key] = is_valid
                self._validation_cache.move_to_end(cache_key)

                # メトリクス更新
                self.validation_metrics.entries = len(self._validation_cache)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "validation_cache_add",
                    f"バリデーション結果をキャッシュ: {file_path.name} - 有効: {is_valid}",
                    level="DEBUG"
                )

                return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "cache_validation_result",
                    "file_path": str(file_path),
                    "is_valid": is_valid
                },
                AIComponent.KIRO
            )
            return False

    def get_cached_validation_result(self, file_path: Path) -> Optional[bool]:
        """
        キャッシュされたバリデーション結果を取得

        Args:
            file_path: ファイルパス

        Returns:
            キャッシュされた結果、またはNone
        """

        try:
            with self._lock:
                # バリデーション用キャッシュキーを生成
                try:
                    file_stat = file_path.stat()
                    cache_key = f"valid_{file_path.stem}_{file_stat.st_size}_{int(file_stat.st_mtime)}"
                except (OSError, FileNotFoundError):
                    self.validation_metrics.misses += 1
                    self.validation_metrics.update_hit_rate()
                    return None

                # キャッシュから取得
                if cache_key in self._validation_cache:
                    is_valid = self._validation_cache[cache_key]

                    # LRU更新
                    self._validation_cache.move_to_end(cache_key)

                    # メトリクス更新
                    self.validation_metrics.hits += 1
                    self.validation_metrics.update_hit_rate()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "validation_cache_hit",
                        f"バリデーションキャッシュヒット: {file_path.name} - 有効: {is_valid}",
                        level="DEBUG"
                    )

                    return is_valid

                # キャッシュミス
                self.validation_metrics.misses += 1
                self.validation_metrics.update_hit_rate()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "validation_cache_miss",
                    f"バリデーションキャッシュミス: {file_path.name}",
                    level="DEBUG"
                )

                return None

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "get_cached_validation_result",
                    "file_path": str(file_path)
                },
                AIComponent.KIRO
            )
            return None

    def _evict_file_entries_if_needed(self):
        """必要に応じてファイルエントリを削除"""

        while len(self._file_cache) >= self.max_file_entries:
            if not self._file_cache:
                break

            # 最も古いエントリを削除（FIFO）
            oldest_key, oldest_entry = self._file_cache.popitem(last=False)
            self.file_metrics.evictions += 1

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "file_cache_evict",
                f"ファイルキャッシュエントリを削除: {oldest_entry.file_path.name}",
                level="DEBUG"
            )

    def _evict_folder_entries_if_needed(self):
        """必要に応じてフォルダエントリを削除"""

        while len(self._folder_cache) >= self.max_folder_entries:
            if not self._folder_cache:
                break

            # 最も古いエントリを削除（FIFO）
            oldest_key, oldest_entry = self._folder_cache.popitem(last=False)
            self.folder_metrics.evictions += 1

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "folder_cache_evict",
                f"フォルダキャッシュエントリを削除: {oldest_entry.folder_path}",
                level="DEBUG"
            )

    def _evict_validation_entries_if_needed(self):
        """必要に応じてバリデーションエントリを削除"""

        # バリデーションキャッシュは軽量なので、より多くのエントリを保持
        max_validation_entries = self.max_file_entries * 2

        while len(self._validation_cache) >= max_validation_entries:
            if not self._validation_cache:
                break

            # 最も古いエントリを削除（FIFO）
            oldest_key, oldest_value = self._validation_cache.popitem(last=False)
            self.validation_metrics.evictions += 1

    def _update_memory_usage(self):
        """メモリ使用量を更新"""

        try:
            # 概算メモリ使用量を計算
            file_memory = len(self._file_cache) * 1024  # 1KB per entry estimate
            folder_memory = len(self._folder_cache) * 10240  # 10KB per entry estimate
            validation_memory = len(self._validation_cache) * 100  # 100B per entry estimate

            total_memory = file_memory + folder_memory + validation_memory

            self.file_metrics.memory_usage_bytes = file_memory
            self.folder_metrics.memory_usage_bytes = folder_memory
            self.validation_metrics.memory_usage_bytes = validation_memory

            # メモリ制限チェック
            if total_memory > self.max_memory_bytes:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "cache_memory_warning",
                    f"キャッシュメモリ使用量が制限を超過: {total_memory / 1024 / 1024:.1f}MB / "
                    f"{self.max_memory_bytes / 1024 / 1024:.1f}MB",
                    level="WARNING"
                )

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_memory_update_error",
                f"メモリ使用量更新エラー: {str(e)}",
                level="WARNING"
            )

    def cleanup_expired_entries(self):
        """期限切れエントリのクリーンアップ"""

        try:
            with self._lock:
                current_time = datetime.now()

                # 前回のクリーンアップから十分時間が経過していない場合はスキップ
                if current_time - self.last_cleanup < self.cleanup_interval:
                    return

                expired_files = []
                expired_folders = []

                # ファイルキャッシュの期限切れエントリをチェック
                for key, result in list(self._file_cache.items()):
                    if result.is_expired:
                        expired_files.append(key)

                # フォルダキャッシュの期限切れエントリをチェック
                for key, folder_cache in list(self._folder_cache.items()):
                    if folder_cache.is_expired:
                        expired_folders.append(key)

                # 期限切れエントリを削除
                for key in expired_files:
                    del self._file_cache[key]

                for key in expired_folders:
                    del self._folder_cache[key]

                # メトリクス更新
                self.file_metrics.entries = len(self._file_cache)
                self.folder_metrics.entries = len(self._folder_cache)
                self._update_memory_usage()

                self.last_cleanup = current_time

                if expired_files or expired_folders:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "cache_cleanup",
                        f"期限切れキャッシュエントリを削除: "
                        f"ファイル {len(expired_files)}個, フォルダ {len(expired_folders)}個"
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cleanup_expired_entries"},
                AIComponent.KIRO
            )

    def clear_cache(self, cache_type: Optional[str] = None):
        """
        キャッシュをクリア

        Args:
            cache_type: クリアするキャッシュタイプ（'file', 'folder', 'validation'）
                       Noneの場合は全てクリア
        """

        try:
            with self._lock:
                if cache_type == "file" or cache_type is None:
                    self._file_cache.clear()
                    self.file_metrics = CacheMetrics()

                if cache_type == "folder" or cache_type is None:
                    self._folder_cache.clear()
                    self.folder_metrics = CacheMetrics()

                if cache_type == "validation" or cache_type is None:
                    self._validation_cache.clear()
                    self.validation_metrics = CacheMetrics()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "cache_clear",
                    f"キャッシュをクリア: {cache_type or 'all'}"
                )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "clear_cache", "cache_type": cache_type},
                AIComponent.KIRO
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得

        Returns:
            統計情報の辞書
        """

        try:
            with self._lock:
                # 期限切れエントリのクリーンアップ
                self.cleanup_expired_entries()

                return {
                    "file_cache": self.file_metrics.to_dict(),
                    "folder_cache": self.folder_metrics.to_dict(),
                    "validation_cache": self.validation_metrics.to_dict(),
                    "total_memory_mb": (
                        self.file_metrics.memory_usage_bytes +
                        self.folder_metrics.memory_usage_bytes +
                        self.validation_metrics.memory_usage_bytes
                    ) / 1024 / 1024,
                    "total_entries": (
                        self.file_metrics.entries +
                        self.folder_metrics.entries +
                        self.validation_metrics.entries
                    ),
                    "overall_hit_rate": self._calculate_overall_hit_rate(),
                    "last_cleanup": self.last_cleanup.isoformat(),
                    "cache_config": {
                        "max_file_entries": self.max_file_entries,
                        "max_folder_entries": self.max_folder_entries,
                        "max_memory_mb": self.max_memory_bytes / 1024 / 1024
                    }
                }

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "get_cache_stats"},
                AIComponent.KIRO
            )
            return {"error": str(e)}

    def _calculate_overall_hit_rate(self) -> float:
        """全体のヒット率を計算"""

        total_hits = (self.file_metrics.hits +
                     self.folder_metrics.hits +
                     self.validation_metrics.hits)
        total_requests = (self.file_metrics.hits + self.file_metrics.misses +
                         self.folder_metrics.hits + self.folder_metrics.misses +
                         self.validation_metrics.hits + self.validation_metrics.misses)

        return total_hits / total_requests if total_requests > 0 else 0.0

    def get_cache_summary(self) -> str:
        """
        キャッシュサマリーを文字列で取得

        Returns:
            サマリー文字列
        """

        stats = self.get_cache_stats()

        return (
            f"FileDiscoveryCache Summary:\n"
            f"  File Cache: {stats['file_cache']['entries']} entries, "
            f"{stats['file_cache']['hit_rate']:.1%} hit rate\n"
            f"  Folder Cache: {stats['folder_cache']['entries']} entries, "
            f"{stats['folder_cache']['hit_rate']:.1%} hit rate\n"
            f"  Validation Cache: {stats['validation_cache']['entries']} entries, "
            f"{stats['validation_cache']['hit_rate']:.1%} hit rate\n"
            f"  Total Memory: {stats['total_memory_mb']:.1f}MB\n"
            f"  Overall Hit Rate: {stats['overall_hit_rate']:.1%}"
        )

    def optimize_logging_for_production(self):
        """
        本番環境向けにログ出力を最適化する

        本番環境では以下の最適化を実行:
        - デバッグレベルのキャッシュログを無効化
        - 重要なキャッシュ統計のみログ出力
        - パフォーマンス警告の強化
        """

        self._production_mode = True

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "cache_production_optimized",
            "キャッシュシステムの本番環境最適化が完了しました",
            level="INFO"
        )

    def log_cache_performance_summary(self):
        """
        キャッシュパフォーマンス要約をログに出力する
        """

        stats = self.get_cache_stats()

        # 全体的なパフォーマンス評価
        overall_hit_rate = stats['overall_hit_rate']
        total_memory_mb = stats['total_memory_mb']
        total_entries = stats['total_entries']

        # ログレベルの決定
        log_level = "INFO"
        if overall_hit_rate < 0.5:  # 50%未満
            log_level = "WARNING"
        elif total_memory_mb > self.max_memory_bytes / 1024 / 1024 * 0.9:  # 90%以上
            log_level = "WARNING"

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "cache_performance_summary",
            f"キャッシュパフォーマンス要約 - "
            f"全体ヒット率: {overall_hit_rate:.1%}, "
            f"総エントリ数: {total_entries}, "
            f"メモリ使用量: {total_memory_mb:.1f}MB, "
            f"ファイルキャッシュ: {stats['file_cache']['hit_rate']:.1%}, "
            f"フォルダキャッシュ: {stats['folder_cache']['hit_rate']:.1%}",
            level=log_level
        )

        # 詳細統計をパフォーマンスログに記録
        self.logger_system.log_performance(
            AIComponent.KIRO,
            "cache_detailed_performance",
            stats
        )

    def enable_debug_cache_logging(self):
        """
        キャッシュデバッグログを有効にする（トラブルシューティング用）
        """

        self._debug_cache_logging = True

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "cache_debug_logging_enabled",
            "キャッシュデバッグログが有効になりました",
            level="DEBUG"
        )

    def get_cache_health_status(self) -> Dict[str, Any]:
        """
        キャッシュの健全性状態を取得する

        Returns:
            キャッシュ健全性の評価結果
        """

        stats = self.get_cache_stats()

        # 健全性評価
        health_score = 0
        issues = []
        recommendations = []

        # ヒット率の評価
        overall_hit_rate = stats['overall_hit_rate']
        if overall_hit_rate >= 0.8:
            health_score += 40
        elif overall_hit_rate >= 0.6:
            health_score += 30
            recommendations.append("キャッシュヒット率の改善を検討してください")
        else:
            health_score += 10
            issues.append(f"キャッシュヒット率が低い: {overall_hit_rate:.1%}")
            recommendations.append("キャッシュ戦略の見直しが必要です")

        # メモリ使用量の評価
        memory_usage_ratio = stats['total_memory_mb'] / (self.max_memory_bytes / 1024 / 1024)
        if memory_usage_ratio <= 0.7:
            health_score += 30
        elif memory_usage_ratio <= 0.9:
            health_score += 20
            recommendations.append("メモリ使用量が増加しています")
        else:
            health_score += 5
            issues.append(f"メモリ使用量が制限に近い: {memory_usage_ratio:.1%}")
            recommendations.append("キャッシュサイズの調整が必要です")

        # エントリ数の評価
        total_entries = stats['total_entries']
        max_total_entries = self.max_file_entries + self.max_folder_entries + (self.max_file_entries * 2)
        entry_usage_ratio = total_entries / max_total_entries
        if entry_usage_ratio <= 0.8:
            health_score += 30
        elif entry_usage_ratio <= 0.95:
            health_score += 20
        else:
            health_score += 10
            issues.append("キャッシュエントリ数が上限に近い")

        # 健全性レベルの決定
        if health_score >= 90:
            health_level = "excellent"
            health_message = "キャッシュは最適な状態です"
        elif health_score >= 70:
            health_level = "good"
            health_message = "キャッシュは良好な状態です"
        elif health_score >= 50:
            health_level = "fair"
            health_message = "キャッシュの改善が推奨されます"
        else:
            health_level = "poor"
            health_message = "キャッシュの最適化が必要です"

        return {
            "health_score": health_score,
            "health_level": health_level,
            "health_message": health_message,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": {
                "overall_hit_rate": overall_hit_rate,
                "memory_usage_ratio": memory_usage_ratio,
                "entry_usage_ratio": entry_usage_ratio,
                "total_entries": total_entries,
                "total_memory_mb": stats['total_memory_mb']
            },
            "timestamp": datetime.now().isoformat()
        }
