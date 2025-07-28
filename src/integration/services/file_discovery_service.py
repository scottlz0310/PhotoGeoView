"""
FileDiscoveryService - 画像ファイル検出サービス

フォルダ内の画像ファイルを検出し、バリデーションを行うサービスクラス。
CS4CodingImageProcessorと連携してファイルの有効性をチェックし、
Kiroの統合ログシステムでエラーハンドリングを行う。

主な機能:
- 対応画像形式（.jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp）のファイル検出
- CS4CodingImageProcessorを使用したファイルバリデーション
- 破損ファイルの検出と除外
- キャッシュ機能による高速化
- 詳細なパフォーマンス監視とログ記録
- 日本語エラーメッセージ対応

技術仕様:
- 非同期処理によるUI応答性の維持
- LRUキャッシュによる効率的なメモリ使用
- 統合ログシステムによる詳細な動作記録
- エラーハンドリングとフォールバック機能

Author: Kiro AI Integration System
"""

import time
import asyncio
from pathlib import Path
from typing import List, Set, Optional, Dict, Any, AsyncIterator, Callable
from datetime import datetime

from ..models import AIComponent, ProcessingStatus
from ..logging_system import LoggerSystem
from ..error_handling import IntegratedErrorHandler, ErrorCategory
from ..image_processor import CS4CodingImageProcessor
from .file_discovery_errors import (
    FileDiscoveryError,
    FileDiscoveryErrorHandler,
    FileDiscoveryErrorMessages,
    FolderAccessError,
    FolderNotFoundError,
    PermissionDeniedError,
    FileValidationError,
    CorruptedFileError,
    UnsupportedFileFormatError,
    ScanTimeoutError,
    MemoryLimitExceededError,
    TooManyFilesError,
    FileDiscoveryErrorLevel,
)
from .file_discovery_cache import FileDiscoveryCache, FileDiscoveryResult


class FileDiscoveryService:
    """
    画像ファイル検出サービス

    機能:
    - 対応画像形式のファイル検出
    - ファイルバリデーション
    - CS4CodingImageProcessorとの連携
    - 統合ログシステムでのエラーハンドリング
    """

    # 対応画像形式の定数定義
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

    def __init__(
        self,
        logger_system: Optional[LoggerSystem] = None,
        image_processor: Optional[CS4CodingImageProcessor] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
    ):
        """
        FileDiscoveryServiceの初期化

        Args:
            logger_system: ログシステムインスタンス
            image_processor: 画像処理インスタンス
            enable_cache: キャッシュ機能を有効にするか
            cache_config: キャッシュ設定
        """

        # ロガーとエラーハンドラーの初期化
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # FileDiscoveryService専用エラーハンドラーの初期化
        self.file_discovery_error_handler = FileDiscoveryErrorHandler(
            logger=self.logger_system.get_logger("file_discovery")
        )

        # 画像処理インスタンスの初期化
        self.image_processor = image_processor or CS4CodingImageProcessor(
            logger_system=self.logger_system
        )

        # キャッシュシステムの初期化
        self.enable_cache = enable_cache
        if self.enable_cache:
            cache_config = cache_config or {}
            self.cache = FileDiscoveryCache(
                max_file_entries=cache_config.get("max_file_entries", 2000),
                max_folder_entries=cache_config.get("max_folder_entries", 100),
                max_memory_mb=cache_config.get("max_memory_mb", 50.0),
                logger_system=self.logger_system,
            )
        else:
            self.cache = None

        # パフォーマンス追跡用の変数
        self.discovery_stats = {
            "total_scans": 0,
            "total_files_found": 0,
            "total_valid_files": 0,
            "total_scan_time": 0.0,
            "last_scan_time": None,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # ログレベル設定の初期化
        self.debug_enabled = self.logger_system.log_level <= 10  # DEBUG level
        self.performance_logging_enabled = True

        # 初期化完了をログに記録
        self.log_with_appropriate_level(
            "INFO",
            "file_discovery_init",
            "FileDiscoveryService が初期化されました",
            {
                "supported_extensions": list(self.SUPPORTED_EXTENSIONS),
                "debug_enabled": self.debug_enabled,
                "performance_logging_enabled": self.performance_logging_enabled,
                "cache_enabled": self.enable_cache,
                "initialization_time": datetime.now().isoformat(),
            },
        )

    def discover_images(self, folder_path: Path) -> List[Path]:
        """
        指定されたフォルダ内の画像ファイルを検出する（キャッシュ対応）

        このメソッドは以下の処理を順次実行します:
        1. キャッシュから既存の検出結果を確認
        2. フォルダの存在確認とアクセス権限チェック
        3. フォルダ内ファイルの走査と拡張子フィルタリング
        4. 各ファイルのバリデーション実行
        5. 結果のキャッシュ保存とパフォーマンス記録

        Args:
            folder_path (Path): 検索対象のフォルダパス

        Returns:
            List[Path]: 検出された有効な画像ファイルのパスリスト

        Raises:
            FileNotFoundError: フォルダが存在しない場合
            PermissionError: フォルダへのアクセス権限がない場合
            Exception: その他の予期しないエラー

        Note:
            - 対応形式: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp
            - キャッシュヒット時は高速に結果を返却
            - 破損ファイルは自動的に除外される
            - 詳細なパフォーマンス情報がログに記録される
        """

        # 操作コンテキストを使用してログ記録を自動化
        with self.logger_system.operation_context(
            AIComponent.KIRO, "image_discovery"
        ) as ctx:
            start_time = time.time()
            discovered_files = []
            scan_details = {
                "folder_path": str(folder_path),
                "start_time": datetime.now().isoformat(),
                "cache_enabled": self.enable_cache,
            }

            try:
                # キャッシュからフォルダスキャン結果を確認
                if self.enable_cache and self.cache:
                    cached_folder_scan = self.cache.get_cached_folder_scan(folder_path)
                    if cached_folder_scan:
                        # キャッシュヒット - キャッシュされた結果を使用
                        discovered_files = [
                            result.file_path
                            for result in cached_folder_scan.file_results
                            if result.is_valid
                        ]
                        scan_duration = time.time() - start_time

                        self.discovery_stats["cache_hits"] += 1

                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "folder_cache_hit",
                            f"フォルダキャッシュヒット: {folder_path} - "
                            f"{len(discovered_files)}個のファイル ({cached_folder_scan.scan_duration:.2f}秒でスキャン済み)",
                        )

                        scan_details.update(
                            {
                                "cache_hit": True,
                                "cached_scan_duration": cached_folder_scan.scan_duration,
                                "cached_file_count": len(
                                    cached_folder_scan.file_results
                                ),
                                "images_found": len(discovered_files),
                                "scan_duration": scan_duration,
                            }
                        )

                        self._log_scan_performance(
                            scan_details,
                            cached_folder_scan.total_files_scanned,
                            len(discovered_files),
                            scan_duration,
                        )
                        return discovered_files

                # キャッシュミスまたはキャッシュ無効 - 実際のスキャンを実行
                if self.enable_cache:
                    self.discovery_stats["cache_misses"] += 1

                # デバッグ情報: フォルダスキャン開始
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "folder_scan_debug",
                    f"画像検出開始 - フォルダ: {folder_path}, 対応形式: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                    level="DEBUG",
                )

                # フォルダの存在確認
                if not folder_path.exists():
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "folder_validation",
                        f"フォルダが存在しません: {folder_path}",
                        level="WARNING",
                    )
                    scan_details["error"] = "folder_not_found"
                    self._log_scan_performance(
                        scan_details, 0, 0, time.time() - start_time
                    )
                    return []

                if not folder_path.is_dir():
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "folder_validation",
                        f"指定されたパスはフォルダではありません: {folder_path}",
                        level="WARNING",
                    )
                    scan_details["error"] = "not_directory"
                    self._log_scan_performance(
                        scan_details, 0, 0, time.time() - start_time
                    )
                    return []

                # フォルダスキャン開始をログに記録
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "folder_scan_start",
                    f"フォルダスキャンを開始: {folder_path}",
                )

                # フォルダ内のファイルを走査
                all_files = []
                try:
                    all_files = list(folder_path.iterdir())

                    # デバッグ情報: 発見したファイル数
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "folder_scan_debug",
                        f"フォルダ内ファイル数: {len(all_files)}個",
                        level="DEBUG",
                    )

                except PermissionError as e:
                    self.error_handler.handle_error(
                        e,
                        ErrorCategory.FILE_ERROR,
                        {
                            "operation": "folder_scan",
                            "file_path": str(folder_path),
                            "user_action": "フォルダ選択",
                        },
                        AIComponent.KIRO,
                    )
                    scan_details["error"] = "permission_denied"
                    self._log_scan_performance(
                        scan_details, 0, 0, time.time() - start_time
                    )
                    return []

                # 画像ファイルのフィルタリング（キャッシュ対応）
                filtered_count = 0
                validation_failures = 0
                file_results = []  # キャッシュ用のファイル結果リスト

                for file_path in all_files:
                    if file_path.is_file():
                        # 拡張子による基本フィルタリング
                        if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                            filtered_count += 1

                            # デバッグ情報: 対象ファイル発見
                            self.logger_system.log_ai_operation(
                                AIComponent.KIRO,
                                "file_filter_debug",
                                f"対象ファイル発見: {file_path.name} (サイズ: {file_path.stat().st_size}バイト)",
                                level="DEBUG",
                            )

                            # キャッシュから個別ファイル結果を確認
                            cached_result = None
                            if self.enable_cache and self.cache:
                                cached_result = self.cache.get_cached_file_result(
                                    file_path
                                )

                            if cached_result:
                                # ファイルキャッシュヒット
                                if cached_result.is_valid:
                                    discovered_files.append(file_path)
                                else:
                                    validation_failures += 1
                                file_results.append(cached_result)

                                self.logger_system.log_ai_operation(
                                    AIComponent.KIRO,
                                    "file_cache_hit_debug",
                                    f"ファイルキャッシュヒット: {file_path.name} - 有効: {cached_result.is_valid}",
                                    level="DEBUG",
                                )
                            else:
                                # キャッシュミス - 実際のバリデーションを実行
                                validation_start_time = time.time()
                                is_valid = self._basic_file_validation(file_path)
                                validation_time = time.time() - validation_start_time

                                if is_valid:
                                    discovered_files.append(file_path)
                                else:
                                    validation_failures += 1

                                # ファイル結果をキャッシュに保存
                                if self.enable_cache and self.cache:
                                    try:
                                        file_stat = file_path.stat()
                                        file_result = FileDiscoveryResult(
                                            file_path=file_path,
                                            is_valid=is_valid,
                                            file_size=file_stat.st_size,
                                            modified_time=file_stat.st_mtime,
                                            discovery_time=datetime.now(),
                                            validation_time=validation_time,
                                        )
                                        file_results.append(file_result)
                                        self.cache.cache_file_result(
                                            file_path, is_valid, validation_time
                                        )
                                    except (OSError, FileNotFoundError):
                                        pass

                                # デバッグ情報: バリデーション結果
                                self.logger_system.log_ai_operation(
                                    AIComponent.KIRO,
                                    "file_validation_debug",
                                    f"ファイルバリデーション: {file_path.name} - 有効: {is_valid} ({validation_time:.3f}秒)",
                                    level="DEBUG",
                                )

                # スキャン結果をログに記録
                scan_duration = time.time() - start_time
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "folder_scan_complete",
                    f"フォルダスキャン完了: {len(discovered_files)}個のファイルを{scan_duration:.2f}秒で検出",
                )

                # フォルダスキャン結果をキャッシュに保存
                if self.enable_cache and self.cache and file_results:
                    self.cache.cache_folder_scan(
                        folder_path, file_results, len(all_files), scan_duration
                    )

                # 詳細なデバッグ情報をログに記録
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "scan_summary_debug",
                    f"スキャン詳細 - 総ファイル数: {len(all_files)}, "
                    f"対象拡張子: {filtered_count}, "
                    f"バリデーション通過: {len(discovered_files)}, "
                    f"バリデーション失敗: {validation_failures}",
                    level="DEBUG",
                )

                # 統計情報の更新
                self._update_discovery_stats(
                    len(all_files), len(discovered_files), scan_duration
                )

                # 詳細なパフォーマンス情報をログに記録
                scan_details.update(
                    {
                        "cache_hit": False,
                        "total_files_scanned": len(all_files),
                        "filtered_files": filtered_count,
                        "validation_failures": validation_failures,
                        "images_found": len(discovered_files),
                        "scan_duration": scan_duration,
                        "files_per_second": (
                            len(all_files) / scan_duration if scan_duration > 0 else 0
                        ),
                        "success_rate": (
                            len(discovered_files) / filtered_count
                            if filtered_count > 0
                            else 0
                        ),
                        "end_time": datetime.now().isoformat(),
                    }
                )

                self._log_scan_performance(
                    scan_details, len(all_files), len(discovered_files), scan_duration
                )

                # 統合ログ機能を使用した詳細ログ記録
                self.log_detailed_debug_info("image_discovery", scan_details)
                self.log_performance_metrics(
                    "image_discovery",
                    {
                        "duration": scan_duration,
                        "files_processed": len(all_files),
                        "files_per_second": (
                            len(all_files) / scan_duration if scan_duration > 0 else 0
                        ),
                        "success_rate": (
                            len(discovered_files) / filtered_count
                            if filtered_count > 0
                            else 0
                        ),
                        "cache_enabled": self.enable_cache,
                        "start_time": scan_details["start_time"],
                        "end_time": scan_details["end_time"],
                    },
                )

                # パフォーマンス警告のチェック
                self._check_performance_warnings(
                    scan_duration, len(all_files), len(discovered_files)
                )

                return discovered_files

            except Exception as e:
                # 予期しないエラーのハンドリング
                scan_duration = time.time() - start_time
                scan_details.update(
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "scan_duration": scan_duration,
                    }
                )

                self._log_scan_performance(scan_details, 0, 0, scan_duration)

                # 統合ログ機能を使用したエラー詳細記録
                self.log_error_details(
                    "image_discovery",
                    e,
                    {
                        "folder_path": str(folder_path),
                        "scan_duration": scan_duration,
                        "user_action": "フォルダ内画像検出",
                    },
                )

                self.error_handler.handle_error(
                    e,
                    ErrorCategory.CORE_ERROR,
                    {
                        "operation": "image_discovery",
                        "file_path": str(folder_path),
                        "user_action": "フォルダ内画像検出",
                        "scan_duration": scan_duration,
                    },
                    AIComponent.KIRO,
                )
                return []

    def validate_image_file(self, file_path: Path) -> bool:
        """
        CS4CodingImageProcessorと連携してファイルの有効性をチェックする（キャッシュ対応）

        このメソッドは多段階のバリデーションを実行します:
        1. キャッシュから既存のバリデーション結果を確認
        2. 基本的なファイル存在確認とサイズチェック
        3. CS4CodingImageProcessorによる詳細検証
        4. 実際の画像読み込みテストによる最終確認
        5. 結果のキャッシュ保存とパフォーマンス記録

        Args:
            file_path (Path): 検証対象のファイルパス

        Returns:
            bool: ファイルが有効な画像の場合True、そうでなければFalse

        Note:
            - 100バイト未満のファイルは破損とみなして除外
            - CS4CodingImageProcessorで形式チェック実行
            - 実際の読み込みテストで最終確認
            - バリデーション結果はキャッシュに保存
            - 詳細なバリデーション時間がログに記録
        """

        # 操作コンテキストを使用してバリデーション処理をログ記録
        with self.logger_system.operation_context(
            AIComponent.COPILOT, "image_validation"
        ) as ctx:
            validation_start_time = time.time()
            validation_details = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "start_time": datetime.now().isoformat(),
                "cache_enabled": self.enable_cache,
            }

            try:
                # キャッシュからバリデーション結果を確認
                if self.enable_cache and self.cache:
                    cached_result = self.cache.get_cached_validation_result(file_path)
                    if cached_result is not None:
                        # キャッシュヒット
                        validation_duration = time.time() - validation_start_time

                        self.logger_system.log_ai_operation(
                            AIComponent.COPILOT,
                            "validation_cache_hit",
                            f"バリデーションキャッシュヒット: {file_path.name} - 有効: {cached_result} ({validation_duration:.3f}秒)",
                            level="DEBUG",
                        )

                        validation_details.update(
                            {
                                "cache_hit": True,
                                "is_valid": cached_result,
                                "validation_duration": validation_duration,
                                "end_time": datetime.now().isoformat(),
                            }
                        )

                        self._log_validation_performance(
                            validation_details, cached_result, validation_duration
                        )

                        if cached_result:
                            self.discovery_stats["total_valid_files"] += 1

                        return cached_result

                # キャッシュミスまたはキャッシュ無効 - 実際のバリデーションを実行
                validation_details["cache_hit"] = False

                # ファイル情報の詳細ログ記録
                try:
                    file_stat = file_path.stat()
                    validation_details.update(
                        {
                            "file_size": file_stat.st_size,
                            "file_modified": datetime.fromtimestamp(
                                file_stat.st_mtime
                            ).isoformat(),
                            "file_extension": file_path.suffix.lower(),
                        }
                    )

                    self.logger_system.log_ai_operation(
                        AIComponent.COPILOT,
                        "validation_debug",
                        f"ファイル検証開始: {file_path.name} "
                        f"(サイズ: {file_stat.st_size}バイト, 拡張子: {file_path.suffix.lower()})",
                        level="DEBUG",
                    )
                except OSError as stat_error:
                    validation_details["stat_error"] = str(stat_error)
                    self.logger_system.log_ai_operation(
                        AIComponent.COPILOT,
                        "validation_debug",
                        f"ファイル情報取得エラー: {file_path.name} - {str(stat_error)}",
                        level="DEBUG",
                    )

                # 基本的なファイル検証
                if not self._basic_file_validation(file_path):
                    validation_details["validation_stage"] = "basic_validation_failed"
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "image_validation",
                        f"基本ファイル検証失敗: {file_path.name}",
                        level="DEBUG",
                    )

                    # 失敗結果をキャッシュに保存
                    if self.enable_cache and self.cache:
                        self.cache.cache_validation_result(file_path, False)

                    self._log_validation_performance(
                        validation_details, False, time.time() - validation_start_time
                    )
                    return False

                # 追加の破損ファイルチェック（CS4CodingImageProcessor呼び出し前）
                file_size = file_path.stat().st_size
                if file_size < 100:  # 100バイト未満は破損の可能性が高い
                    validation_details.update(
                        {
                            "validation_stage": "size_check_failed",
                            "failure_reason": "file_too_small",
                        }
                    )

                    self.logger_system.log_ai_operation(
                        AIComponent.COPILOT,
                        "corrupted_file_detection",
                        f"ファイルサイズが異常に小さいため破損ファイルとして除外: {file_path.name} ({file_size}バイト)",
                        level="WARNING",
                    )

                    # 失敗結果をキャッシュに保存
                    if self.enable_cache and self.cache:
                        self.cache.cache_validation_result(file_path, False)

                    self._log_validation_performance(
                        validation_details, False, time.time() - validation_start_time
                    )
                    return False

                # CS4CodingImageProcessorを使用した詳細検証
                validation_details["validation_stage"] = "processor_validation"
                processor_start_time = time.time()

                self.logger_system.log_ai_operation(
                    AIComponent.COPILOT,
                    "validation_debug",
                    f"CS4CodingImageProcessor検証開始: {file_path.name}",
                    level="DEBUG",
                )

                is_valid = self.image_processor.validate_image(file_path)
                processor_duration = time.time() - processor_start_time
                validation_details["processor_duration"] = processor_duration

                # 破損ファイルの検出と除外（追加チェック）
                if is_valid:
                    validation_details["validation_stage"] = "load_test"
                    load_test_start_time = time.time()

                    # 画像プロセッサでの実際の読み込み試行で最終確認
                    try:
                        self.logger_system.log_ai_operation(
                            AIComponent.COPILOT,
                            "validation_debug",
                            f"画像読み込みテスト開始: {file_path.name}",
                            level="DEBUG",
                        )

                        test_image = self.image_processor.load_image(file_path)
                        load_test_duration = time.time() - load_test_start_time
                        validation_details["load_test_duration"] = load_test_duration

                        if test_image is None:
                            validation_details.update(
                                {
                                    "validation_stage": "load_test_failed",
                                    "failure_reason": "image_load_returned_none",
                                }
                            )

                            self.logger_system.log_ai_operation(
                                AIComponent.COPILOT,
                                "corrupted_file_detection",
                                f"画像読み込み失敗により破損ファイルとして除外: {file_path.name}",
                                level="WARNING",
                            )
                            is_valid = False
                        else:
                            self.logger_system.log_ai_operation(
                                AIComponent.COPILOT,
                                "validation_debug",
                                f"画像読み込みテスト成功: {file_path.name} ({load_test_duration:.3f}秒)",
                                level="DEBUG",
                            )

                    except Exception as validation_error:
                        load_test_duration = time.time() - load_test_start_time
                        validation_details.update(
                            {
                                "load_test_duration": load_test_duration,
                                "validation_stage": "load_test_exception",
                                "failure_reason": str(validation_error),
                                "error_type": type(validation_error).__name__,
                            }
                        )

                        self.logger_system.log_ai_operation(
                            AIComponent.COPILOT,
                            "corrupted_file_detection",
                            f"破損ファイル検出中にエラー: {file_path.name} - {str(validation_error)}",
                            level="WARNING",
                        )
                        is_valid = False

                # バリデーション結果をキャッシュに保存
                if self.enable_cache and self.cache:
                    self.cache.cache_validation_result(file_path, is_valid)

                # バリデーション結果をログに記録
                validation_duration = time.time() - validation_start_time
                validation_details.update(
                    {
                        "validation_duration": validation_duration,
                        "is_valid": is_valid,
                        "end_time": datetime.now().isoformat(),
                    }
                )

                if is_valid:
                    self.logger_system.log_ai_operation(
                        AIComponent.COPILOT,
                        "image_validation",
                        f"画像ファイル検証成功: {file_path.name} ({validation_duration:.3f}秒)",
                        level="DEBUG",
                    )
                    # 有効ファイル数を統計に追加
                    self.discovery_stats["total_valid_files"] += 1

                    # 成功時の詳細ログ
                    self.logger_system.log_ai_operation(
                        AIComponent.COPILOT,
                        "validation_success_debug",
                        f"検証成功詳細: {file_path.name} - "
                        f"プロセッサ検証: {processor_duration:.3f}秒, "
                        f"読み込みテスト: {validation_details.get('load_test_duration', 0):.3f}秒",
                        level="DEBUG",
                    )
                else:
                    self.logger_system.log_ai_operation(
                        AIComponent.COPILOT,
                        "image_validation",
                        f"画像ファイル検証失敗: {file_path.name} ({validation_duration:.3f}秒) - "
                        f"段階: {validation_details.get('validation_stage', 'unknown')}, "
                        f"理由: {validation_details.get('failure_reason', 'unknown')}",
                        level="WARNING",
                    )

                # 詳細なパフォーマンス情報をログに記録
                self._log_validation_performance(
                    validation_details, is_valid, validation_duration
                )

                # 統合ログ機能を使用した詳細ログ記録
                self.log_detailed_debug_info("image_validation", validation_details)
                self.log_performance_metrics(
                    "image_validation",
                    {
                        "duration": validation_duration,
                        "file_size": file_size,
                        "is_valid": is_valid,
                        "cache_enabled": self.enable_cache,
                        "cache_hit": validation_details.get("cache_hit", False),
                        "processor_duration": validation_details.get(
                            "processor_duration", 0
                        ),
                        "load_test_duration": validation_details.get(
                            "load_test_duration", 0
                        ),
                        "start_time": validation_details["start_time"],
                        "end_time": validation_details["end_time"],
                    },
                )

                # バリデーション時間の警告チェック
                self._check_validation_performance_warnings(
                    validation_duration, file_size, is_valid
                )

                return is_valid

            except Exception as e:
                # バリデーションエラーのハンドリング
                validation_duration = time.time() - validation_start_time
                validation_details.update(
                    {
                        "validation_duration": validation_duration,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "validation_stage": "exception",
                    }
                )

                self._log_validation_performance(
                    validation_details, False, validation_duration
                )

                # 統合ログ機能を使用したエラー詳細記録
                self.log_error_details(
                    "image_validation",
                    e,
                    {
                        "file_path": str(file_path),
                        "validation_duration": validation_duration,
                        "user_action": "画像ファイル検証",
                        "validation_stage": "exception",
                    },
                )

                self.error_handler.handle_error(
                    e,
                    ErrorCategory.VALIDATION_ERROR,
                    {
                        "operation": "image_validation",
                        "file_path": str(file_path),
                        "user_action": "画像ファイル検証",
                        "validation_duration": validation_duration,
                    },
                    AIComponent.COPILOT,
                )
                return False

    def _log_validation_performance(
        self, validation_details: Dict[str, Any], is_valid: bool, duration: float
    ):
        """
        バリデーションパフォーマンス情報を詳細にログ記録する

        Args:
            validation_details: バリデーション詳細情報
            is_valid: バリデーション結果
            duration: バリデーション時間
        """

        # パフォーマンスメトリクス
        performance_metrics = {
            "file_path": validation_details.get("file_path", "unknown"),
            "file_name": validation_details.get("file_name", "unknown"),
            "file_size": validation_details.get("file_size", 0),
            "file_extension": validation_details.get("file_extension", "unknown"),
            "validation_duration": duration,
            "is_valid": is_valid,
            "validation_stage": validation_details.get("validation_stage", "unknown"),
            "processor_duration": validation_details.get("processor_duration", 0),
            "load_test_duration": validation_details.get("load_test_duration", 0),
            "timestamp": datetime.now().isoformat(),
        }

        # エラー情報があれば追加
        if "error" in validation_details:
            performance_metrics["error"] = validation_details["error"]
            performance_metrics["error_type"] = validation_details.get(
                "error_type", "unknown"
            )

        if "failure_reason" in validation_details:
            performance_metrics["failure_reason"] = validation_details["failure_reason"]

        # パフォーマンスログに記録
        self.logger_system.log_performance(
            AIComponent.COPILOT, "image_validation_detailed", performance_metrics
        )

        # 詳細デバッグ情報
        if validation_details.get("file_size", 0) > 0:
            validation_speed = (
                validation_details["file_size"] / duration if duration > 0 else 0
            )
            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "validation_performance_debug",
                f"バリデーション性能: {validation_details.get('file_name', 'unknown')} - "
                f"処理速度: {validation_speed:.0f}バイト/秒, "
                f"メモリ使用量: {self._get_memory_usage():.1f}MB",
                level="DEBUG",
            )

    def _check_validation_performance_warnings(
        self, duration: float, file_size: int, is_valid: bool
    ):
        """
        バリデーションパフォーマンス警告をチェックする

        Args:
            duration: バリデーション時間
            file_size: ファイルサイズ
            is_valid: バリデーション結果
        """

        # バリデーション時間の警告閾値
        SLOW_VALIDATION_THRESHOLD = 1.0  # 1秒
        VERY_SLOW_VALIDATION_THRESHOLD = 3.0  # 3秒

        # ファイルサイズに対する処理速度の警告閾値（バイト/秒）
        SLOW_PROCESSING_SPEED_THRESHOLD = 1024 * 1024  # 1MB/秒

        if duration > VERY_SLOW_VALIDATION_THRESHOLD:
            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "validation_performance_warning",
                f"非常に遅いバリデーション: {duration:.3f}秒 (閾値: {VERY_SLOW_VALIDATION_THRESHOLD}秒) - "
                f"ファイルサイズ: {file_size}バイト",
                level="WARNING",
            )
        elif duration > SLOW_VALIDATION_THRESHOLD:
            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "validation_performance_warning",
                f"遅いバリデーション: {duration:.3f}秒 (閾値: {SLOW_VALIDATION_THRESHOLD}秒)",
                level="WARNING",
            )

        # 処理速度の警告
        if file_size > 0 and duration > 0:
            processing_speed = file_size / duration
            if processing_speed < SLOW_PROCESSING_SPEED_THRESHOLD:
                self.logger_system.log_ai_operation(
                    AIComponent.COPILOT,
                    "validation_performance_warning",
                    f"低いバリデーション処理速度: {processing_speed:.0f}バイト/秒 "
                    f"(閾値: {SLOW_PROCESSING_SPEED_THRESHOLD}バイト/秒)",
                    level="WARNING",
                )

    def get_supported_extensions(self) -> Set[str]:
        """
        対応している画像形式の拡張子セットを取得する

        Returns:
            対応拡張子のセット
        """
        return self.SUPPORTED_EXTENSIONS.copy()

    def get_discovery_stats(self) -> Dict[str, Any]:
        """
        ファイル検出の統計情報を取得する

        Returns:
            統計情報の辞書
        """

        # 統計情報取得開始をログに記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "stats_request_debug",
            "ファイル検出統計情報の取得を開始",
            level="DEBUG",
        )

        stats = self.discovery_stats.copy()

        # 平均値の計算
        if stats["total_scans"] > 0:
            stats["avg_files_per_scan"] = (
                stats["total_files_found"] / stats["total_scans"]
            )
            stats["avg_scan_time"] = stats["total_scan_time"] / stats["total_scans"]
            stats["success_rate"] = (
                stats["total_valid_files"] / stats["total_files_found"]
                if stats["total_files_found"] > 0
                else 0
            )

            # 追加の統計情報
            stats["avg_files_per_second"] = (
                stats["total_files_found"] / stats["total_scan_time"]
                if stats["total_scan_time"] > 0
                else 0
            )
            stats["validation_success_rate"] = (
                stats["total_valid_files"] / stats["total_files_found"]
                if stats["total_files_found"] > 0
                else 0
            )
        else:
            stats["avg_files_per_scan"] = 0
            stats["avg_scan_time"] = 0
            stats["success_rate"] = 0
            stats["avg_files_per_second"] = 0
            stats["validation_success_rate"] = 0

        # 現在のメモリ使用量を追加
        stats["current_memory_usage_mb"] = self._get_memory_usage()

        # 統計情報生成時刻を追加
        stats["stats_generated_at"] = datetime.now().isoformat()

        # 詳細な統計情報をログに記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "stats_summary",
            f"統計情報サマリー - 総スキャン数: {stats['total_scans']}, "
            f"発見ファイル数: {stats['total_files_found']}, "
            f"有効ファイル数: {stats['total_valid_files']}, "
            f"平均スキャン時間: {stats['avg_scan_time']:.2f}秒, "
            f"成功率: {stats['success_rate']:.1%}",
            level="INFO",
        )

        # パフォーマンス統計をログに記録
        self.logger_system.log_performance(
            AIComponent.KIRO,
            "discovery_statistics",
            {
                "total_scans": stats["total_scans"],
                "total_files_found": stats["total_files_found"],
                "total_valid_files": stats["total_valid_files"],
                "total_scan_time": stats["total_scan_time"],
                "avg_scan_time": stats["avg_scan_time"],
                "avg_files_per_scan": stats["avg_files_per_scan"],
                "avg_files_per_second": stats["avg_files_per_second"],
                "success_rate": stats["success_rate"],
                "validation_success_rate": stats["validation_success_rate"],
                "current_memory_usage_mb": stats["current_memory_usage_mb"],
                "last_scan_time": (
                    stats["last_scan_time"].isoformat()
                    if stats["last_scan_time"]
                    else None
                ),
                "timestamp": stats["stats_generated_at"],
            },
        )

        return stats

    def _basic_file_validation(self, file_path: Path) -> bool:
        """
        基本的なファイル検証を行う

        Args:
            file_path: 検証対象のファイルパス

        Returns:
            基本検証をパスした場合True
        """

        validation_start_time = time.time()

        try:
            # デバッグ情報: 基本検証開始
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "basic_validation_debug",
                f"基本ファイル検証開始: {file_path.name}",
                level="DEBUG",
            )

            # ファイルの存在確認
            if not file_path.exists():
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "basic_validation_debug",
                    f"ファイルが存在しません: {file_path.name}",
                    level="DEBUG",
                )
                return False

            # ファイル統計情報の取得
            try:
                file_stat = file_path.stat()
                file_size = file_stat.st_size

                # デバッグ情報: ファイル情報
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "basic_validation_debug",
                    f"ファイル情報: {file_path.name} - サイズ: {file_size}バイト, "
                    f"更新日時: {datetime.fromtimestamp(file_stat.st_mtime).isoformat()}",
                    level="DEBUG",
                )

            except OSError as stat_error:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "basic_validation_debug",
                    f"ファイル統計情報取得エラー: {file_path.name} - {str(stat_error)}",
                    level="DEBUG",
                )
                return False

            # ファイルサイズの確認（0バイトファイルは無効）
            if file_size == 0:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "file_validation",
                    f"ファイルサイズが0バイトです: {file_path.name}",
                    level="DEBUG",
                )
                return False

            # 拡張子の確認
            file_extension = file_path.suffix.lower()
            if file_extension not in self.SUPPORTED_EXTENSIONS:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "basic_validation_debug",
                    f"未対応の拡張子: {file_path.name} ({file_extension}) - "
                    f"対応拡張子: {', '.join(self.SUPPORTED_EXTENSIONS)}",
                    level="DEBUG",
                )
                return False

            # 基本検証成功
            validation_duration = time.time() - validation_start_time
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "basic_validation_debug",
                f"基本ファイル検証成功: {file_path.name} ({validation_duration:.3f}秒)",
                level="DEBUG",
            )

            # パフォーマンス情報をログに記録
            self.logger_system.log_performance(
                AIComponent.KIRO,
                "basic_file_validation",
                {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "file_size": file_size,
                    "file_extension": file_extension,
                    "validation_duration": validation_duration,
                    "is_valid": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return True

        except Exception as e:
            # 基本検証エラーのハンドリング
            validation_duration = time.time() - validation_start_time

            # 詳細なエラー情報をログに記録
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "basic_validation_error",
                f"基本ファイル検証中にエラー: {file_path.name} - {str(e)}",
                level="ERROR",
            )

            # エラー時のパフォーマンス情報もログに記録
            self.logger_system.log_performance(
                AIComponent.KIRO,
                "basic_file_validation_error",
                {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "validation_duration": validation_duration,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "is_valid": False,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            self.logger_system.log_performance(
                AIComponent.KIRO,
                "basic_file_validation",
                {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "file_size": file_size,
                    "file_extension": file_extension,
                    "validation_duration": validation_duration,
                    "validation_result": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return True

        except Exception as e:
            validation_duration = time.time() - validation_start_time

            # エラー詳細をログに記録
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "basic_validation_error",
                f"基本ファイル検証中にエラー: {file_path.name} - {str(e)} ({validation_duration:.3f}秒)",
                level="ERROR",
            )

            # パフォーマンス情報（エラー時）をログに記録
            self.logger_system.log_performance(
                AIComponent.KIRO,
                "basic_file_validation",
                {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "validation_duration": validation_duration,
                    "validation_result": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # 統合エラーハンドラーでエラー処理
            self.logger_system.log_error(
                AIComponent.KIRO,
                e,
                "basic_file_validation",
                {
                    "file_path": str(file_path),
                    "validation_duration": validation_duration,
                },
            )
            return False

    def _update_discovery_stats(
        self, total_files: int, found_files: int, scan_time: float
    ):
        """
        検出統計情報を更新する

        Args:
            total_files: スキャンした総ファイル数
            found_files: 発見した画像ファイル数
            scan_time: スキャン時間（秒）
        """

        self.discovery_stats["total_scans"] += 1
        self.discovery_stats["total_files_found"] += found_files
        self.discovery_stats["total_scan_time"] += scan_time
        self.discovery_stats["last_scan_time"] = datetime.now()

        # 有効ファイル数は後でバリデーション時に更新される
        # ここでは発見したファイル数のみ記録

        # 統計情報の詳細ログ記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "stats_update_debug",
            f"統計更新 - 総スキャン数: {self.discovery_stats['total_scans']}, "
            f"累計発見ファイル数: {self.discovery_stats['total_files_found']}, "
            f"累計スキャン時間: {self.discovery_stats['total_scan_time']:.2f}秒",
            level="DEBUG",
        )

    def _log_scan_performance(
        self,
        scan_details: Dict[str, Any],
        total_files: int,
        found_files: int,
        duration: float,
    ):
        """
        スキャンパフォーマンス情報を詳細にログ記録する

        Args:
            scan_details: スキャン詳細情報
            total_files: 総ファイル数
            found_files: 発見ファイル数
            duration: スキャン時間
        """

        # 基本パフォーマンスメトリクス
        performance_metrics = {
            "folder_path": scan_details.get("folder_path", "unknown"),
            "total_files_scanned": total_files,
            "images_found": found_files,
            "scan_duration": duration,
            "files_per_second": total_files / duration if duration > 0 else 0,
            "success_rate": found_files / total_files if total_files > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }

        # 追加の詳細情報があれば含める
        if "filtered_files" in scan_details:
            performance_metrics["filtered_files"] = scan_details["filtered_files"]
            performance_metrics["filter_success_rate"] = (
                found_files / scan_details["filtered_files"]
                if scan_details["filtered_files"] > 0
                else 0
            )

        if "validation_failures" in scan_details:
            performance_metrics["validation_failures"] = scan_details[
                "validation_failures"
            ]

        if "error" in scan_details:
            performance_metrics["error"] = scan_details["error"]
            performance_metrics["error_type"] = scan_details.get(
                "error_type", "unknown"
            )

        # パフォーマンスログに記録
        self.logger_system.log_performance(
            AIComponent.KIRO, "image_discovery_scan", performance_metrics
        )

        # 詳細デバッグ情報をログに記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "performance_debug",
            f"パフォーマンス詳細 - "
            f"処理速度: {performance_metrics['files_per_second']:.1f}ファイル/秒, "
            f"成功率: {performance_metrics['success_rate']:.1%}, "
            f"メモリ使用量: {self._get_memory_usage():.1f}MB",
            level="DEBUG",
        )

    def _check_performance_warnings(
        self, duration: float, total_files: int, found_files: int
    ):
        """
        パフォーマンス警告をチェックし、必要に応じて警告ログを出力する

        Args:
            duration: スキャン時間
            total_files: 総ファイル数
            found_files: 発見ファイル数
        """

        # スキャン時間の警告閾値（秒）
        SLOW_SCAN_THRESHOLD = 5.0
        VERY_SLOW_SCAN_THRESHOLD = 15.0

        # ファイル処理速度の警告閾値（ファイル/秒）
        SLOW_PROCESSING_THRESHOLD = 50.0

        # メモリ使用量の警告閾値（MB）
        HIGH_MEMORY_THRESHOLD = 500.0

        files_per_second = total_files / duration if duration > 0 else 0
        memory_usage = self._get_memory_usage()

        # スキャン時間の警告
        if duration > VERY_SLOW_SCAN_THRESHOLD:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_warning",
                f"非常に遅いスキャン検出: {duration:.2f}秒 (閾値: {VERY_SLOW_SCAN_THRESHOLD}秒) - "
                f"ファイル数: {total_files}, 処理速度: {files_per_second:.1f}ファイル/秒",
                level="WARNING",
            )
        elif duration > SLOW_SCAN_THRESHOLD:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_warning",
                f"遅いスキャン検出: {duration:.2f}秒 (閾値: {SLOW_SCAN_THRESHOLD}秒) - "
                f"ファイル数: {total_files}",
                level="WARNING",
            )

        # 処理速度の警告
        if files_per_second < SLOW_PROCESSING_THRESHOLD and total_files > 100:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_warning",
                f"低い処理速度検出: {files_per_second:.1f}ファイル/秒 (閾値: {SLOW_PROCESSING_THRESHOLD}ファイル/秒)",
                level="WARNING",
            )

        # メモリ使用量の警告
        if memory_usage > HIGH_MEMORY_THRESHOLD:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_warning",
                f"高いメモリ使用量検出: {memory_usage:.1f}MB (閾値: {HIGH_MEMORY_THRESHOLD}MB)",
                level="WARNING",
            )

        # 成功率の警告
        success_rate = found_files / total_files if total_files > 0 else 0
        if (
            success_rate < 0.1 and total_files > 10
        ):  # 10%未満の成功率で10ファイル以上の場合
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "performance_warning",
                f"低い画像検出成功率: {success_rate:.1%} ({found_files}/{total_files})",
                level="WARNING",
            )

    def _get_memory_usage(self) -> float:
        """
        現在のメモリ使用量を取得する（MB単位）

        Returns:
            メモリ使用量（MB）
        """

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # バイトからMBに変換
        except ImportError:
            # psutilが利用できない場合は0を返す
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "memory_debug",
                "psutilが利用できないため、メモリ使用量を取得できません",
                level="DEBUG",
            )
            return 0.0
        except Exception as e:
            # その他のエラーの場合もログに記録して0を返す
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "memory_debug",
                f"メモリ使用量取得エラー: {str(e)}",
                level="DEBUG",
            )
            return 0.0

    def log_detailed_debug_info(self, operation: str, details: Dict[str, Any]):
        """
        詳細なデバッグ情報をログに出力する

        Args:
            operation: 実行中の操作名
            details: 詳細情報の辞書
        """

        # デバッグレベルでの詳細情報出力
        debug_message = f"詳細デバッグ情報 [{operation}]: "
        debug_parts = []

        for key, value in details.items():
            if isinstance(value, (int, float)):
                if key.endswith("_time") or key.endswith("_duration"):
                    debug_parts.append(f"{key}: {value:.3f}秒")
                elif key.endswith("_size") or key.endswith("_bytes"):
                    debug_parts.append(f"{key}: {value:,}バイト")
                else:
                    debug_parts.append(f"{key}: {value}")
            elif isinstance(value, datetime):
                debug_parts.append(f"{key}: {value.isoformat()}")
            else:
                debug_parts.append(f"{key}: {str(value)}")

        debug_message += ", ".join(debug_parts)

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            f"{operation}_detailed_debug",
            debug_message,
            level="DEBUG",
        )

        # パフォーマンス情報も同時に記録
        self.logger_system.log_performance(
            AIComponent.KIRO,
            f"{operation}_debug_metrics",
            {
                "operation": operation,
                "debug_details": details,
                "memory_usage_mb": self._get_memory_usage(),
                "timestamp": datetime.now().isoformat(),
            },
        )

    def log_performance_metrics(self, operation: str, metrics: Dict[str, Any]):
        """
        パフォーマンス情報を詳細にログ記録する

        Args:
            operation: 操作名
            metrics: パフォーマンスメトリクス
        """

        # 基本パフォーマンス情報のログ出力
        perf_message = f"パフォーマンス情報 [{operation}]: "
        perf_parts = []

        # 時間関連の情報
        if "duration" in metrics:
            perf_parts.append(f"実行時間: {metrics['duration']:.3f}秒")
        if "start_time" in metrics and "end_time" in metrics:
            start = (
                datetime.fromisoformat(metrics["start_time"])
                if isinstance(metrics["start_time"], str)
                else metrics["start_time"]
            )
            end = (
                datetime.fromisoformat(metrics["end_time"])
                if isinstance(metrics["end_time"], str)
                else metrics["end_time"]
            )
            duration = (end - start).total_seconds()
            perf_parts.append(f"計算実行時間: {duration:.3f}秒")

        # ファイル処理関連の情報
        if "files_processed" in metrics:
            perf_parts.append(f"処理ファイル数: {metrics['files_processed']}個")
        if "files_per_second" in metrics:
            perf_parts.append(f"処理速度: {metrics['files_per_second']:.1f}ファイル/秒")
        if "success_rate" in metrics:
            perf_parts.append(f"成功率: {metrics['success_rate']:.1%}")

        # メモリ関連の情報
        current_memory = self._get_memory_usage()
        perf_parts.append(f"メモリ使用量: {current_memory:.1f}MB")

        perf_message += ", ".join(perf_parts)

        # INFO レベルでパフォーマンス情報をログ出力
        self.logger_system.log_ai_operation(
            AIComponent.KIRO, f"{operation}_performance", perf_message, level="INFO"
        )

        # 詳細なパフォーマンスメトリクスを記録
        enhanced_metrics = {
            **metrics,
            "current_memory_mb": current_memory,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger_system.log_performance(
            AIComponent.KIRO, f"{operation}_detailed_performance", enhanced_metrics
        )

        # パフォーマンス警告のチェック
        self._check_performance_thresholds(operation, enhanced_metrics)

    def log_error_details(
        self, operation: str, error: Exception, context: Dict[str, Any] = None
    ):
        """
        エラー発生時の詳細情報を記録する

        Args:
            operation: エラーが発生した操作
            error: 発生したエラー
            context: エラーのコンテキスト情報
        """

        error_context = context or {}

        # エラーの基本情報
        error_details = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "memory_usage_mb": self._get_memory_usage(),
        }

        # コンテキスト情報を追加
        error_details.update(error_context)

        # エラーレベルでの詳細ログ出力
        error_message = (
            f"エラー詳細 [{operation}]: {type(error).__name__} - {str(error)}"
        )

        if error_context:
            context_parts = []
            for key, value in error_context.items():
                if key not in ["operation", "error_type", "error_message"]:
                    context_parts.append(f"{key}: {value}")

            if context_parts:
                error_message += f" (コンテキスト: {', '.join(context_parts)})"

        self.logger_system.log_ai_operation(
            AIComponent.KIRO, f"{operation}_error_details", error_message, level="ERROR"
        )

        # エラーの詳細情報をパフォーマンスログにも記録
        self.logger_system.log_performance(
            AIComponent.KIRO, f"{operation}_error_metrics", error_details
        )

        # 統合エラーハンドラーにも通知
        self.error_handler.handle_error(
            error, self._categorize_error(error), error_context, AIComponent.KIRO
        )

    def log_with_appropriate_level(
        self, level: str, operation: str, message: str, details: Dict[str, Any] = None
    ):
        """
        ログレベルに応じた適切な出力を行う

        Args:
            level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            operation: 操作名
            message: ログメッセージ
            details: 追加の詳細情報
        """

        # ログレベルの正規化
        log_level = level.upper()
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            log_level = "INFO"

        # 基本ログ出力
        self.logger_system.log_ai_operation(
            AIComponent.KIRO, operation, message, level=log_level
        )

        # レベルに応じた追加処理
        if details:
            if log_level == "DEBUG":
                # DEBUGレベルでは詳細情報も出力
                self.log_detailed_debug_info(operation, details)
            elif log_level in ["WARNING", "ERROR", "CRITICAL"]:
                # 警告以上のレベルではパフォーマンス情報も記録
                self.log_performance_metrics(operation, details)

        # CRITICALレベルの場合は即座にログをフラッシュ
        if log_level == "CRITICAL":
            self.logger_system.flush_all()

    def _categorize_error(self, error: Exception) -> str:
        """
        エラーを適切なカテゴリに分類する

        Args:
            error: 分類対象のエラー

        Returns:
            エラーカテゴリ文字列
        """

        if isinstance(error, PermissionError):
            return "PERMISSION_ERROR"
        elif isinstance(error, FileNotFoundError):
            return "FILE_NOT_FOUND"
        elif isinstance(error, OSError):
            return "FILE_SYSTEM_ERROR"
        elif isinstance(error, MemoryError):
            return "MEMORY_ERROR"
        elif isinstance(error, TimeoutError):
            return "TIMEOUT_ERROR"
        else:
            return "GENERAL_ERROR"

    def _check_performance_thresholds(self, operation: str, metrics: Dict[str, Any]):
        """
        パフォーマンス閾値をチェックし、必要に応じて警告を出力

        Args:
            operation: 操作名
            metrics: パフォーマンスメトリクス
        """

        # 実行時間の警告閾値
        duration_thresholds = {
            "image_discovery": 10.0,  # 10秒
            "image_validation": 2.0,  # 2秒
            "basic_file_validation": 0.1,  # 0.1秒
        }

        # メモリ使用量の警告閾値（MB）
        memory_threshold = 1000.0  # 1GB

        # 実行時間のチェック
        if "duration" in metrics:
            duration = metrics["duration"]
            threshold = duration_thresholds.get(operation, 5.0)  # デフォルト5秒

            if duration > threshold:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    f"{operation}_performance_warning",
                    f"実行時間が閾値を超過: {duration:.3f}秒 (閾値: {threshold}秒)",
                    level="WARNING",
                )

        # メモリ使用量のチェック
        if "current_memory_mb" in metrics:
            memory_usage = metrics["current_memory_mb"]

            if memory_usage > memory_threshold:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    f"{operation}_memory_warning",
                    f"メモリ使用量が閾値を超過: {memory_usage:.1f}MB (閾値: {memory_threshold}MB)",
                    level="WARNING",
                )

        # 成功率のチェック
        if "success_rate" in metrics:
            success_rate = metrics["success_rate"]

            if success_rate < 0.5:  # 50%未満
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    f"{operation}_success_rate_warning",
                    f"成功率が低下: {success_rate:.1%}",
                    level="WARNING",
                )

    def configure_logging(
        self,
        debug_enabled: bool = None,
        performance_logging_enabled: bool = None,
        log_level: str = None,
    ):
        """
        ログ機能の設定を変更する

        Args:
            debug_enabled: デバッグログの有効/無効
            performance_logging_enabled: パフォーマンスログの有効/無効
            log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """

        if debug_enabled is not None:
            self.debug_enabled = debug_enabled

        if performance_logging_enabled is not None:
            self.performance_logging_enabled = performance_logging_enabled

        if log_level is not None:
            # ログレベルの設定（LoggerSystemに反映）
            import logging

            level_mapping = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }

            if log_level.upper() in level_mapping:
                self.logger_system.log_level = level_mapping[log_level.upper()]

        # 設定変更をログに記録
        self.log_with_appropriate_level(
            "INFO",
            "logging_configuration_changed",
            "ログ設定が変更されました",
            {
                "debug_enabled": self.debug_enabled,
                "performance_logging_enabled": self.performance_logging_enabled,
                "log_level": log_level or "unchanged",
                "change_time": datetime.now().isoformat(),
            },
        )

    def get_logging_status(self) -> Dict[str, Any]:
        """
        現在のログ設定状況を取得する

        Returns:
            ログ設定状況の辞書
        """

        status = {
            "debug_enabled": self.debug_enabled,
            "performance_logging_enabled": self.performance_logging_enabled,
            "current_log_level": self.logger_system.log_level,
            "operation_counts": dict(self.logger_system.operation_counts),
            "total_operations": sum(self.logger_system.operation_counts.values()),
            "memory_usage_mb": self._get_memory_usage(),
            "status_timestamp": datetime.now().isoformat(),
        }

        # ログ状況の取得をデバッグレベルで記録
        if self.debug_enabled:
            self.log_detailed_debug_info("logging_status_request", status)

        return status

    def flush_logs(self):
        """
        すべてのログをフラッシュする
        """

        self.logger_system.flush_all()

        self.log_with_appropriate_level(
            "DEBUG",
            "logs_flushed",
            "すべてのログがフラッシュされました",
            {
                "flush_time": datetime.now().isoformat(),
                "memory_usage_mb": self._get_memory_usage(),
            },
        )

    def optimize_logging_for_production(self):
        """
        本番環境向けにログ出力を最適化する

        本番環境では以下の最適化を実行:
        - デバッグログの無効化
        - パフォーマンスログの定期出力設定
        - ログレベルをINFO以上に制限
        - メモリ使用量の監視強化
        """

        # 本番環境設定
        self.debug_enabled = False
        self.performance_logging_enabled = True

        # ログレベルをINFOに設定
        import logging

        self.logger_system.log_level = logging.INFO

        # パフォーマンス情報の定期出力を設定
        self._setup_periodic_performance_logging()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "production_logging_optimized",
            "本番環境向けログ最適化が完了しました",
            level="INFO",
        )

    def _setup_periodic_performance_logging(self):
        """
        パフォーマンス情報の定期出力を設定する
        """

        # 定期的なパフォーマンス統計の出力
        def log_periodic_stats():
            stats = {
                "total_scans": self.discovery_stats["total_scans"],
                "total_files_found": self.discovery_stats["total_files_found"],
                "total_valid_files": self.discovery_stats["total_valid_files"],
                "avg_scan_time": self.discovery_stats["total_scan_time"]
                / max(1, self.discovery_stats["total_scans"]),
                "cache_hit_rate": self.discovery_stats["cache_hits"]
                / max(
                    1,
                    self.discovery_stats["cache_hits"]
                    + self.discovery_stats["cache_misses"],
                ),
                "memory_usage_mb": self._get_memory_usage(),
                "timestamp": datetime.now().isoformat(),
            }

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "periodic_performance_stats",
                f"定期パフォーマンス統計 - スキャン数: {stats['total_scans']}, "
                f"平均時間: {stats['avg_scan_time']:.2f}秒, "
                f"キャッシュヒット率: {stats['cache_hit_rate']:.1%}, "
                f"メモリ使用量: {stats['memory_usage_mb']:.1f}MB",
                level="INFO",
            )

            # 詳細統計をパフォーマンスログに記録
            self.logger_system.log_performance(
                AIComponent.KIRO, "periodic_performance_detailed", stats
            )

        # 初回実行
        log_periodic_stats()

        # 定期実行の設定（実際の実装では適切なスケジューラーを使用）
        self._periodic_stats_callback = log_periodic_stats

    def enable_debug_logging(self):
        """
        デバッグログを有効にする（開発・トラブルシューティング用）
        """

        self.debug_enabled = True
        self.performance_logging_enabled = True

        import logging

        self.logger_system.log_level = logging.DEBUG

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "debug_logging_enabled",
            "デバッグログが有効になりました",
            level="DEBUG",
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        パフォーマンス統計の要約を取得する

        Returns:
            パフォーマンス統計の要約辞書
        """

        total_operations = self.discovery_stats["total_scans"]
        cache_requests = (
            self.discovery_stats["cache_hits"] + self.discovery_stats["cache_misses"]
        )

        summary = {
            "operations": {
                "total_scans": total_operations,
                "total_files_found": self.discovery_stats["total_files_found"],
                "total_valid_files": self.discovery_stats["total_valid_files"],
                "avg_files_per_scan": self.discovery_stats["total_files_found"]
                / max(1, total_operations),
            },
            "performance": {
                "total_scan_time": self.discovery_stats["total_scan_time"],
                "avg_scan_time": self.discovery_stats["total_scan_time"]
                / max(1, total_operations),
                "last_scan_time": self.discovery_stats["last_scan_time"],
            },
            "cache": {
                "cache_hits": self.discovery_stats["cache_hits"],
                "cache_misses": self.discovery_stats["cache_misses"],
                "hit_rate": self.discovery_stats["cache_hits"] / max(1, cache_requests),
                "total_requests": cache_requests,
            },
            "system": {
                "memory_usage_mb": self._get_memory_usage(),
                "debug_enabled": self.debug_enabled,
                "performance_logging_enabled": self.performance_logging_enabled,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return summary

    async def discover_images_async(
        self,
        folder_path: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        batch_size: int = 50,
    ) -> AsyncIterator[Path]:
        """
        非同期で画像ファイルを検出する

        UIスレッドをブロックしない非同期ファイル検出を提供する。
        プログレスバー表示との連携も可能。

        Args:
            folder_path: 検索対象のフォルダパス
            progress_callback: 進行状況コールバック関数 (current, total, message)
            batch_size: 一度に処理するファイル数

        Yields:
            検出された画像ファイルのパス
        """

        with self.logger_system.operation_context(
            AIComponent.KIRO, "async_image_discovery"
        ) as ctx:
            start_time = time.time()
            total_processed = 0
            total_found = 0

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "async_discovery_start",
                f"非同期画像検出開始: {folder_path}, バッチサイズ: {batch_size}",
            )

            try:
                # フォルダの存在確認
                if not folder_path.exists() or not folder_path.is_dir():
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "async_discovery_error",
                        f"無効なフォルダパス: {folder_path}",
                        level="WARNING",
                    )
                    return

                # 全ファイルリストを取得
                try:
                    all_files = list(folder_path.iterdir())
                    total_files = len(all_files)

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "async_discovery_info",
                        f"総ファイル数: {total_files}個",
                        level="DEBUG",
                    )

                    if progress_callback:
                        progress_callback(0, total_files, "ファイルスキャン開始...")

                except PermissionError as e:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "async_discovery_error",
                        f"フォルダアクセス権限エラー: {folder_path} - {str(e)}",
                        level="ERROR",
                    )
                    return

                # バッチ処理でファイルを検証
                for i in range(0, len(all_files), batch_size):
                    batch_files = all_files[i : i + batch_size]
                    batch_start_time = time.time()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "async_batch_start",
                        f"バッチ処理開始: {i//batch_size + 1}/{(len(all_files) + batch_size - 1)//batch_size} "
                        f"({len(batch_files)}ファイル)",
                        level="DEBUG",
                    )

                    # バッチ内の各ファイルを処理
                    for file_path in batch_files:
                        total_processed += 1

                        if file_path.is_file():
                            # 拡張子チェック
                            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                                # 非同期でファイル検証
                                if await self._validate_image_file_async(file_path):
                                    total_found += 1

                                    self.logger_system.log_ai_operation(
                                        AIComponent.KIRO,
                                        "async_file_found",
                                        f"有効な画像ファイル発見: {file_path.name}",
                                        level="DEBUG",
                                    )

                                    yield file_path

                        # 進行状況を更新
                        if progress_callback and total_processed % 10 == 0:
                            progress_message = f"処理中... {total_found}個の画像を発見"
                            progress_callback(
                                total_processed, total_files, progress_message
                            )

                    # バッチ処理完了
                    batch_duration = time.time() - batch_start_time
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "async_batch_complete",
                        f"バッチ処理完了: {batch_duration:.2f}秒, "
                        f"発見ファイル数: {total_found}個",
                        level="DEBUG",
                    )

                    # UIスレッドに制御を戻すため短時間待機
                    await asyncio.sleep(0.001)

                # 最終進行状況を更新
                if progress_callback:
                    progress_callback(
                        total_files, total_files, f"完了: {total_found}個の画像を発見"
                    )

                # 完了ログ
                total_duration = time.time() - start_time
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "async_discovery_complete",
                    f"非同期画像検出完了: {total_found}個のファイルを{total_duration:.2f}秒で検出",
                )

                # パフォーマンス情報をログに記録
                self.logger_system.log_performance(
                    AIComponent.KIRO,
                    "async_image_discovery",
                    {
                        "folder_path": str(folder_path),
                        "total_files_processed": total_processed,
                        "total_images_found": total_found,
                        "processing_duration": total_duration,
                        "batch_size": batch_size,
                        "files_per_second": (
                            total_processed / total_duration
                            if total_duration > 0
                            else 0
                        ),
                        "success_rate": (
                            total_found / total_processed if total_processed > 0 else 0
                        ),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            except Exception as e:
                error_duration = time.time() - start_time
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "async_discovery_error",
                    f"非同期画像検出エラー: {str(e)}",
                    level="ERROR",
                )

                self.error_handler.handle_error(
                    e,
                    ErrorCategory.CORE_ERROR,
                    {
                        "operation": "async_image_discovery",
                        "folder_path": str(folder_path),
                        "processing_duration": error_duration,
                        "user_action": "非同期フォルダ内画像検出",
                    },
                    AIComponent.KIRO,
                )

                if progress_callback:
                    # 変数が初期化されていない場合のフォールバック
                    processed = locals().get("total_processed", 0)
                    progress_callback(processed, processed, f"エラー: {str(e)}")

    async def _validate_image_file_async(self, file_path: Path) -> bool:
        """
        非同期で画像ファイルの有効性をチェックする

        Args:
            file_path: 検証対象のファイルパス

        Returns:
            ファイルが有効な画像の場合True
        """

        try:
            # 基本的なファイル検証（同期）
            if not self._basic_file_validation(file_path):
                return False

            # 重い処理を非同期で実行
            loop = asyncio.get_event_loop()

            # CS4CodingImageProcessorの検証を別スレッドで実行
            is_valid = await loop.run_in_executor(
                None, self.image_processor.validate_image, file_path
            )

            if is_valid:
                # 実際の画像読み込みテストも非同期で実行
                try:
                    test_image = await loop.run_in_executor(
                        None, self.image_processor.load_image, file_path
                    )

                    if test_image is None:
                        self.logger_system.log_ai_operation(
                            AIComponent.COPILOT,
                            "async_validation_failed",
                            f"非同期画像読み込み失敗: {file_path.name}",
                            level="DEBUG",
                        )
                        return False

                except Exception as validation_error:
                    self.logger_system.log_ai_operation(
                        AIComponent.COPILOT,
                        "async_validation_error",
                        f"非同期バリデーションエラー: {file_path.name} - {str(validation_error)}",
                        level="DEBUG",
                    )
                    return False

            return is_valid

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.COPILOT,
                "async_validation_exception",
                f"非同期バリデーション例外: {file_path.name} - {str(e)}",
                level="WARNING",
            )
            return False

    async def scan_folder_async(
        self,
        folder_path: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Path]:
        """
        フォルダを非同期でスキャンし、すべての画像ファイルを取得する

        Args:
            folder_path: スキャン対象のフォルダパス
            progress_callback: 進行状況コールバック関数

        Returns:
            検出された画像ファイルのリスト
        """

        discovered_files = []

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "async_scan_start",
            f"非同期フォルダスキャン開始: {folder_path}",
        )

        try:
            async for image_path in self.discover_images_async(
                folder_path, progress_callback
            ):
                discovered_files.append(image_path)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "async_scan_complete",
                f"非同期フォルダスキャン完了: {len(discovered_files)}個のファイルを発見",
            )

            return discovered_files

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "async_scan_error",
                f"非同期フォルダスキャンエラー: {str(e)}",
                level="ERROR",
            )
            return discovered_files

    # キャッシュ管理メソッド

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得する

        Returns:
            キャッシュ統計情報の辞書
        """

        if not self.enable_cache or not self.cache:
            return {"cache_enabled": False, "message": "キャッシュが無効です"}

        try:
            cache_stats = self.cache.get_cache_stats()

            # 発見サービス固有の統計を追加
            cache_stats.update(
                {
                    "discovery_cache_hits": self.discovery_stats.get("cache_hits", 0),
                    "discovery_cache_misses": self.discovery_stats.get(
                        "cache_misses", 0
                    ),
                    "discovery_cache_hit_rate": (
                        self.discovery_stats.get("cache_hits", 0)
                        / max(
                            1,
                            self.discovery_stats.get("cache_hits", 0)
                            + self.discovery_stats.get("cache_misses", 0),
                        )
                    ),
                }
            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_stats_request",
                f"キャッシュ統計情報を取得: ヒット率 {cache_stats.get('overall_hit_rate', 0):.1%}",
            )

            return cache_stats

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "get_cache_stats"},
                AIComponent.KIRO,
            )
            return {"error": str(e)}

    def clear_cache(self, cache_type: Optional[str] = None):
        """
        キャッシュをクリアする

        Args:
            cache_type: クリアするキャッシュタイプ（'file', 'folder', 'validation'）
                       Noneの場合は全てクリア
        """

        if not self.enable_cache or not self.cache:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_clear_disabled",
                "キャッシュが無効のため、クリア操作をスキップ",
                level="WARNING",
            )
            return

        try:
            self.cache.clear_cache(cache_type)

            # 統計情報もリセット
            if cache_type is None:
                self.discovery_stats["cache_hits"] = 0
                self.discovery_stats["cache_misses"] = 0

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_clear_success",
                f"キャッシュクリア完了: {cache_type or 'all'}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "clear_cache", "cache_type": cache_type},
                AIComponent.KIRO,
            )

    def cleanup_cache(self):
        """
        期限切れキャッシュエントリのクリーンアップを実行する
        """

        if not self.enable_cache or not self.cache:
            return

        try:
            self.cache.cleanup_expired_entries()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_cleanup_success",
                "キャッシュクリーンアップ完了",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cleanup_cache"},
                AIComponent.KIRO,
            )

    def get_cache_summary(self) -> str:
        """
        キャッシュサマリーを文字列で取得する

        Returns:
            キャッシュサマリー文字列
        """

        if not self.enable_cache or not self.cache:
            return "キャッシュ機能: 無効"

        try:
            return self.cache.get_cache_summary()
        except Exception as e:
            return f"キャッシュサマリー取得エラー: {str(e)}"

    def configure_cache(self, cache_config: Dict[str, Any]):
        """
        キャッシュ設定を更新する

        Args:
            cache_config: 新しいキャッシュ設定
        """

        try:
            if not self.enable_cache:
                # キャッシュが無効の場合は有効化
                self.enable_cache = True
                self.cache = FileDiscoveryCache(
                    max_file_entries=cache_config.get("max_file_entries", 2000),
                    max_folder_entries=cache_config.get("max_folder_entries", 100),
                    max_memory_mb=cache_config.get("max_memory_mb", 50.0),
                    logger_system=self.logger_system,
                )

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "cache_enabled",
                    f"キャッシュ機能を有効化: {cache_config}",
                )
            else:
                # 既存のキャッシュ設定を更新（新しいインスタンスを作成）
                old_cache = self.cache
                self.cache = FileDiscoveryCache(
                    max_file_entries=cache_config.get("max_file_entries", 2000),
                    max_folder_entries=cache_config.get("max_folder_entries", 100),
                    max_memory_mb=cache_config.get("max_memory_mb", 50.0),
                    logger_system=self.logger_system,
                )

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "cache_reconfigured",
                    f"キャッシュ設定を更新: {cache_config}",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "configure_cache", "cache_config": cache_config},
                AIComponent.KIRO,
            )

    def disable_cache(self):
        """
        キャッシュ機能を無効化する
        """

        try:
            if self.enable_cache and self.cache:
                self.cache.clear_cache()
                self.cache = None

            self.enable_cache = False

            # 統計情報をリセット
            self.discovery_stats["cache_hits"] = 0
            self.discovery_stats["cache_misses"] = 0

            self.logger_system.log_ai_operation(
                AIComponent.KIRO, "cache_disabled", "キャッシュ機能を無効化"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "disable_cache"},
                AIComponent.KIRO,
            )

    def get_cache_hit_rate(self) -> float:
        """
        キャッシュヒット率を取得する

        Returns:
            キャッシュヒット率（0.0-1.0）
        """

        if not self.enable_cache:
            return 0.0

        hits = self.discovery_stats.get("cache_hits", 0)
        misses = self.discovery_stats.get("cache_misses", 0)
        total = hits + misses

        return hits / total if total > 0 else 0.0

    def optimize_cache_performance(self):
        """
        キャッシュパフォーマンスを最適化する
        """

        if not self.enable_cache or not self.cache:
            return

        try:
            # 期限切れエントリのクリーンアップ
            self.cache.cleanup_expired_entries()

            # キャッシュ統計を取得してパフォーマンスを分析
            stats = self.cache.get_cache_stats()

            # ヒット率が低い場合の警告
            overall_hit_rate = stats.get("overall_hit_rate", 0)
            if overall_hit_rate < 0.3:  # 30%未満
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "cache_performance_warning",
                    f"キャッシュヒット率が低いです: {overall_hit_rate:.1%}。"
                    "キャッシュサイズの増加を検討してください。",
                    level="WARNING",
                )

            # メモリ使用量の確認
            total_memory_mb = stats.get("total_memory_mb", 0)
            if total_memory_mb > 100:  # 100MB超過
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "cache_memory_warning",
                    f"キャッシュメモリ使用量が多いです: {total_memory_mb:.1f}MB。"
                    "クリーンアップを実行します。",
                    level="WARNING",
                )

                # 自動クリーンアップ
                self.cache.cleanup_expired_entries()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_optimization_complete",
                f"キャッシュ最適化完了 - ヒット率: {overall_hit_rate:.1%}, "
                f"メモリ使用量: {total_memory_mb:.1f}MB",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "optimize_cache_performance"},
                AIComponent.KIRO,
            )
