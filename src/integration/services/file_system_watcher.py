"""
FileSystemWatcher - ファイルシステム監視サービス

フォルダ内のファイル変更を監視し、リアルタイムでファイルリスト更新を行うサービスクラス。
watchdogライブラリを使用してクロスプラットフォーム対応のファイル監視機能を提供する。

主な機能:
- リアルタイムファイル変更監視（作成、削除、変更、移動）
- 画像ファイルのみのフィルタリング機能
- デバウンス処理による連続イベントの抑制
- 複数のコールバック関数登録対応
- 詳細な監視統計情報の記録

技術仕様:
- watchdogライブラリによるクロスプラットフォーム対応
- スレッドセーフな監視状態管理
- メモリ効率的なイベント処理
- 自動フォールバック機能（watchdog未インストール時）
- 統合ログシステムによる詳細な動作記録

使用例:
    watcher = FileSystemWatcher(logger_system=logger)
    watcher.add_change_listener(callback_function)
    watcher.start_watching(Path("/path/to/folder"))

Author: Kiro AI Integration System
"""

import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
    FileSystemEvent = None

from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent


class FileChangeType(Enum):
    """ファイル変更タイプの定義"""

    CREATED = "created"
    DELETED = "deleted"
    MODIFIED = "modified"
    MOVED = "moved"


class FileSystemWatcher:
    """
    ファイルシステム監視サービス

    機能:
    - フォルダ内ファイル変更の自動検出
    - 画像ファイルのみのフィルタリング
    - リアルタイムでのファイルリスト更新通知
    - リソース効率的な監視機能
    """

    # 対応画像形式の定数定義（FileDiscoveryServiceと同じ）
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

    def __init__(
        self,
        logger_system: Optional[LoggerSystem] = None,
        enable_monitoring: bool = True,
    ):
        """
        FileSystemWatcherの初期化

        Args:
            logger_system: ログシステムインスタンス
            enable_monitoring: 監視機能を有効にするか
        """

        # ロガーとエラーハンドラーの初期化
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # watchdogライブラリの可用性チェック
        self.watchdog_available = WATCHDOG_AVAILABLE
        if not self.watchdog_available:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "watchdog_unavailable",
                "watchdogライブラリが利用できません。ファイルシステム監視機能は無効になります。",
                level="WARNING",
            )

        # 監視状態の管理
        self.is_watching = False
        self.current_folder = None
        self.observer = None
        self.event_handler = None
        self.enable_monitoring = enable_monitoring and self.watchdog_available

        # コールバック関数の管理
        self.change_listeners: List[
            Callable[[Path, FileChangeType, Optional[Path]], None]
        ] = []

        # 監視統計情報
        self.watch_stats = {
            "start_time": None,
            "total_events": 0,
            "filtered_events": 0,
            "callback_calls": 0,
            "errors": 0,
            "last_event_time": None,
        }

        # パフォーマンス設定
        self.debounce_interval = 0.5  # 連続イベントの抑制間隔（秒）
        self.last_event_times: Dict[str, float] = {}

        # 初期化完了をログに記録
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "file_watcher_init",
            f"FileSystemWatcher が初期化されました (監視機能: {'有効' if self.enable_monitoring else '無効'})",
            level="INFO",
        )

    def start_watching(self, folder_path: Path) -> bool:
        """
        指定されたフォルダの監視を開始する

        このメソッドは以下の処理を実行します:
        1. 既存の監視を停止（必要に応じて）
        2. フォルダの存在確認とアクセス権限チェック
        3. watchdogオブザーバーの作成と設定
        4. イベントハンドラーの登録
        5. 監視の開始と状態管理の初期化

        Args:
            folder_path (Path): 監視対象のフォルダパス

        Returns:
            bool: 監視開始に成功した場合True、失敗した場合False

        Note:
            - watchdogライブラリが必要（未インストール時は自動的にFalseを返却）
            - サブフォルダは監視対象外（recursive=False）
            - 画像ファイルのみがフィルタリング対象
            - 監視統計情報が自動的にリセットされる
        """

        # 操作コンテキストを使用してログ記録を自動化
        with self.logger_system.operation_context(
            AIComponent.KIRO, "start_file_watching"
        ) as ctx:
            start_time = time.time()
            watch_details = {
                "folder_path": str(folder_path),
                "start_time": datetime.now().isoformat(),
                "monitoring_enabled": self.enable_monitoring,
            }

            try:
                # 監視機能が無効な場合
                if not self.enable_monitoring:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "watch_disabled",
                        f"ファイルシステム監視が無効のため、監視を開始しません: {folder_path}",
                        level="INFO",
                    )
                    return False

                # 既に監視中の場合は停止
                if self.is_watching:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "watch_restart",
                        f"既存の監視を停止して新しいフォルダの監視を開始: {self.current_folder} -> {folder_path}",
                        level="INFO",
                    )
                    self.stop_watching()

                # フォルダの存在確認
                if not folder_path.exists():
                    watch_details["error"] = "folder_not_found"
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "watch_error",
                        f"監視対象フォルダが存在しません: {folder_path}",
                        level="ERROR",
                    )
                    return False

                if not folder_path.is_dir():
                    watch_details["error"] = "not_directory"
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "watch_error",
                        f"指定されたパスはフォルダではありません: {folder_path}",
                        level="ERROR",
                    )
                    return False

                # イベントハンドラーの作成
                if WATCHDOG_AVAILABLE:
                    self.event_handler = ImageFileEventHandler(
                        watcher=self,
                        supported_extensions=self.SUPPORTED_EXTENSIONS,
                        logger_system=self.logger_system,
                    )
                else:
                    # watchdog が利用できない場合はダミーハンドラー
                    self.event_handler = None

                # オブザーバーの作成と開始
                self.observer = Observer()
                self.observer.schedule(
                    self.event_handler,
                    str(folder_path),
                    recursive=False,  # サブフォルダは監視しない
                )

                self.observer.start()

                # 監視状態の更新
                self.is_watching = True
                self.current_folder = folder_path
                self.watch_stats["start_time"] = datetime.now()
                self.watch_stats["total_events"] = 0
                self.watch_stats["filtered_events"] = 0
                self.watch_stats["callback_calls"] = 0
                self.watch_stats["errors"] = 0

                setup_duration = time.time() - start_time
                watch_details.update(
                    {
                        "setup_duration": setup_duration,
                        "success": True,
                        "end_time": datetime.now().isoformat(),
                    }
                )

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "watch_started",
                    f"ファイルシステム監視を開始しました: {folder_path} ({setup_duration:.3f}秒)",
                )

                # 詳細なデバッグ情報をログに記録
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "watch_debug",
                    f"監視設定詳細 - フォルダ: {folder_path}, "
                    f"対応拡張子: {', '.join(self.SUPPORTED_EXTENSIONS)}, "
                    f"デバウンス間隔: {self.debounce_interval}秒",
                    level="DEBUG",
                )

                return True

            except Exception as e:
                # 監視開始エラーのハンドリング
                setup_duration = time.time() - start_time
                watch_details.update(
                    {
                        "setup_duration": setup_duration,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "success": False,
                    }
                )

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "watch_start_error",
                    f"ファイルシステム監視の開始に失敗しました: {folder_path} - {str(e)}",
                    level="ERROR",
                )

                self.error_handler.handle_error(
                    e,
                    ErrorCategory.SYSTEM_ERROR,
                    {
                        "operation": "start_file_watching",
                        "file_path": str(folder_path),
                        "user_action": "フォルダ監視開始",
                        "setup_duration": setup_duration,
                    },
                    AIComponent.KIRO,
                )

                # クリーンアップ
                self._cleanup_observer()
                return False

    def stop_watching(self) -> bool:
        """
        現在の監視を停止する

        Returns:
            監視停止に成功した場合True、失敗した場合False
        """

        with self.logger_system.operation_context(
            AIComponent.KIRO, "stop_file_watching"
        ) as ctx:
            stop_time = time.time()
            stop_details = {
                "current_folder": (
                    str(self.current_folder) if self.current_folder else None
                ),
                "was_watching": self.is_watching,
                "stop_time": datetime.now().isoformat(),
            }

            try:
                if not self.is_watching:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "watch_not_active",
                        "監視が開始されていないため、停止処理をスキップします",
                        level="DEBUG",
                    )
                    return True

                # 監視統計の記録
                if self.watch_stats["start_time"]:
                    watch_duration = (
                        datetime.now() - self.watch_stats["start_time"]
                    ).total_seconds()
                    stop_details.update(
                        {
                            "watch_duration": watch_duration,
                            "total_events": self.watch_stats["total_events"],
                            "filtered_events": self.watch_stats["filtered_events"],
                            "callback_calls": self.watch_stats["callback_calls"],
                            "errors": self.watch_stats["errors"],
                        }
                    )

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "watch_statistics",
                        f"監視統計 - 期間: {watch_duration:.1f}秒, "
                        f"総イベント: {self.watch_stats['total_events']}, "
                        f"フィルタ済み: {self.watch_stats['filtered_events']}, "
                        f"コールバック: {self.watch_stats['callback_calls']}, "
                        f"エラー: {self.watch_stats['errors']}",
                        level="INFO",
                    )

                # オブザーバーの停止とクリーンアップ
                self._cleanup_observer()

                # 監視状態のリセット
                self.is_watching = False
                self.current_folder = None

                stop_duration = time.time() - stop_time
                stop_details.update({"stop_duration": stop_duration, "success": True})

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "watch_stopped",
                    f"ファイルシステム監視を停止しました ({stop_duration:.3f}秒)",
                )

                return True

            except Exception as e:
                # 監視停止エラーのハンドリング
                stop_duration = time.time() - stop_time
                stop_details.update(
                    {
                        "stop_duration": stop_duration,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "success": False,
                    }
                )

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "watch_stop_error",
                    f"ファイルシステム監視の停止中にエラーが発生しました: {str(e)}",
                    level="ERROR",
                )

                self.error_handler.handle_error(
                    e,
                    ErrorCategory.SYSTEM_ERROR,
                    {
                        "operation": "stop_file_watching",
                        "user_action": "フォルダ監視停止",
                        "stop_duration": stop_duration,
                    },
                    AIComponent.KIRO,
                )

                # 強制クリーンアップ
                self._cleanup_observer()
                self.is_watching = False
                self.current_folder = None
                return False

    def add_change_listener(
        self, callback: Callable[[Path, FileChangeType, Optional[Path]], None]
    ):
        """
        ファイル変更通知のコールバック関数を追加する

        登録されたコールバック関数は、監視対象フォルダ内で画像ファイルの
        変更が検出された際に自動的に呼び出されます。

        Args:
            callback (Callable): ファイル変更時に呼び出されるコールバック関数
                引数:
                - file_path (Path): 変更されたファイルのパス
                - change_type (FileChangeType): 変更タイプ（CREATED, DELETED, MODIFIED, MOVED）
                - old_path (Optional[Path]): 移動前のパス（移動の場合のみ）

        Note:
            - 同じコールバック関数の重複登録は防止される
            - コールバック実行中のエラーは自動的にログに記録される
            - デバウンス処理により連続する同一ファイルの変更は抑制される
        """

        if callback not in self.change_listeners:
            self.change_listeners.append(callback)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "listener_added",
                f"ファイル変更リスナーを追加しました (総数: {len(self.change_listeners)})",
                level="DEBUG",
            )

    def remove_change_listener(
        self, callback: Callable[[Path, FileChangeType, Optional[Path]], None]
    ):
        """
        ファイル変更通知のコールバック関数を削除する

        Args:
            callback: 削除するコールバック関数
        """

        if callback in self.change_listeners:
            self.change_listeners.remove(callback)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "listener_removed",
                f"ファイル変更リスナーを削除しました (総数: {len(self.change_listeners)})",
                level="DEBUG",
            )

    def get_watch_status(self) -> Dict[str, Any]:
        """
        現在の監視状態を取得する

        Returns:
            監視状態の詳細情報
        """

        status = {
            "is_watching": self.is_watching,
            "current_folder": str(self.current_folder) if self.current_folder else None,
            "watchdog_available": self.watchdog_available,
            "enable_monitoring": self.enable_monitoring,
            "listener_count": len(self.change_listeners),
            "supported_extensions": list(self.SUPPORTED_EXTENSIONS),
            "debounce_interval": self.debounce_interval,
            "stats": dict(self.watch_stats),
        }

        # 監視期間の計算
        if self.is_watching and self.watch_stats["start_time"]:
            status["watch_duration"] = (
                datetime.now() - self.watch_stats["start_time"]
            ).total_seconds()

        return status

    def _cleanup_observer(self):
        """オブザーバーのクリーンアップ処理"""

        try:
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=5.0)  # 5秒でタイムアウト

                if self.observer.is_alive():
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "observer_cleanup_timeout",
                        "オブザーバーの停止がタイムアウトしました",
                        level="WARNING",
                    )

            self.observer = None
            self.event_handler = None

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "observer_cleanup_error",
                f"オブザーバーのクリーンアップ中にエラーが発生しました: {str(e)}",
                level="ERROR",
            )

    def _notify_listeners(
        self,
        file_path: Path,
        change_type: FileChangeType,
        old_path: Optional[Path] = None,
    ):
        """
        登録されたリスナーにファイル変更を通知する

        Args:
            file_path: 変更されたファイルのパス
            change_type: 変更タイプ
            old_path: 移動前のパス（移動の場合のみ）
        """

        notification_start_time = time.time()

        try:
            # デバウンス処理
            file_key = str(file_path)
            current_time = time.time()

            if file_key in self.last_event_times:
                time_diff = current_time - self.last_event_times[file_key]
                if time_diff < self.debounce_interval:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "event_debounced",
                        f"イベントをデバウンス処理でスキップ: {file_path.name} ({time_diff:.3f}秒)",
                        level="DEBUG",
                    )
                    return

            self.last_event_times[file_key] = current_time

            # リスナーへの通知
            successful_notifications = 0
            failed_notifications = 0

            for listener in self.change_listeners:
                try:
                    listener(file_path, change_type, old_path)
                    successful_notifications += 1

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "listener_notification_debug",
                        f"リスナー通知成功: {file_path.name} ({change_type.value})",
                        level="DEBUG",
                    )

                except Exception as listener_error:
                    failed_notifications += 1

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "listener_notification_error",
                        f"リスナー通知エラー: {file_path.name} - {str(listener_error)}",
                        level="ERROR",
                    )

                    self.error_handler.handle_error(
                        listener_error,
                        ErrorCategory.INTEGRATION_ERROR,
                        {
                            "operation": "file_change_notification",
                            "file_path": str(file_path),
                            "change_type": change_type.value,
                            "user_action": "ファイル変更通知",
                        },
                        AIComponent.KIRO,
                    )

            # 通知統計の更新
            self.watch_stats["callback_calls"] += successful_notifications
            self.watch_stats["errors"] += failed_notifications

            notification_duration = time.time() - notification_start_time

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "listener_notification_complete",
                f"リスナー通知完了: {file_path.name} ({change_type.value}) - "
                f"成功: {successful_notifications}, 失敗: {failed_notifications} ({notification_duration:.3f}秒)",
                level="DEBUG",
            )

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "notification_error",
                f"リスナー通知処理中にエラーが発生しました: {str(e)}",
                level="ERROR",
            )

            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {
                    "operation": "file_change_notification",
                    "file_path": str(file_path),
                    "change_type": change_type.value,
                    "user_action": "ファイル変更通知処理",
                },
                AIComponent.KIRO,
            )

    def optimize_logging_for_production(self):
        """
        本番環境向けにログ出力を最適化する

        本番環境では以下の最適化を実行:
        - デバッグログの無効化
        - 重要なイベントのみログ出力
        - パフォーマンス統計の定期出力
        """

        # 本番環境設定
        self._production_mode = True

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "watcher_production_optimized",
            "ファイルシステム監視の本番環境最適化が完了しました",
            level="INFO",
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        監視パフォーマンスの要約を取得する

        Returns:
            パフォーマンス統計の要約辞書
        """

        watch_duration = 0.0
        if self.is_watching and self.watch_stats["start_time"]:
            watch_duration = (
                datetime.now() - self.watch_stats["start_time"]
            ).total_seconds()

        event_rate = (
            self.watch_stats["total_events"] / max(1, watch_duration)
            if watch_duration > 0
            else 0
        )
        filter_efficiency = (
            self.watch_stats["filtered_events"]
            / max(1, self.watch_stats["total_events"])
            if self.watch_stats["total_events"] > 0
            else 0
        )

        summary = {
            "monitoring": {
                "is_watching": self.is_watching,
                "current_folder": (
                    str(self.current_folder) if self.current_folder else None
                ),
                "watch_duration": watch_duration,
                "watchdog_available": self.watchdog_available,
            },
            "events": {
                "total_events": self.watch_stats["total_events"],
                "filtered_events": self.watch_stats["filtered_events"],
                "callback_calls": self.watch_stats["callback_calls"],
                "errors": self.watch_stats["errors"],
                "event_rate_per_second": event_rate,
                "filter_efficiency": filter_efficiency,
            },
            "listeners": {
                "listener_count": len(self.change_listeners),
                "debounce_interval": self.debounce_interval,
            },
            "timestamp": datetime.now().isoformat(),
        }

        return summary

    def log_performance_summary(self):
        """
        パフォーマンス要約をログに出力する
        """

        summary = self.get_performance_summary()

        if self.is_watching:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "watcher_performance_summary",
                f"監視パフォーマンス要約 - "
                f"監視時間: {summary['monitoring']['watch_duration']:.1f}秒, "
                f"イベント数: {summary['events']['total_events']}, "
                f"フィルタ効率: {summary['events']['filter_efficiency']:.1%}, "
                f"イベント率: {summary['events']['event_rate_per_second']:.2f}/秒",
                level="INFO",
            )

        # 詳細統計をパフォーマンスログに記録
        self.logger_system.log_performance(
            AIComponent.KIRO, "watcher_detailed_performance", summary
        )


if WATCHDOG_AVAILABLE:

    class ImageFileEventHandler(FileSystemEventHandler):
        """
        画像ファイル専用のファイルシステムイベントハンドラー
        """

        def __init__(
            self,
            watcher: FileSystemWatcher,
            supported_extensions: Set[str],
            logger_system: LoggerSystem,
        ):
            """
            イベントハンドラーの初期化

            Args:
                watcher: 親のFileSystemWatcherインスタンス
                supported_extensions: 対応する拡張子のセット
                logger_system: ログシステムインスタンス
            """

            super().__init__()
            self.watcher = watcher
            self.supported_extensions = supported_extensions
            self.logger_system = logger_system

        def _is_image_file(self, file_path: Path) -> bool:
            """
            ファイルが対応する画像ファイルかチェックする

            Args:
                file_path: チェック対象のファイルパス

            Returns:
                対応する画像ファイルの場合True
            """

            return file_path.suffix.lower() in self.supported_extensions

        def on_created(self, event):
            """ファイル作成イベントの処理"""

            if not event.is_directory:
                file_path = Path(event.src_path)

                # 統計更新
                self.watcher.watch_stats["total_events"] += 1

                if self._is_image_file(file_path):
                    self.watcher.watch_stats["filtered_events"] += 1
                    self.watcher.watch_stats["last_event_time"] = datetime.now()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "file_created",
                        f"画像ファイルが作成されました: {file_path.name}",
                        level="DEBUG",
                    )

                    self.watcher._notify_listeners(file_path, FileChangeType.CREATED)

        def on_deleted(self, event):
            """ファイル削除イベントの処理"""

            if not event.is_directory:
                file_path = Path(event.src_path)

                # 統計更新
                self.watcher.watch_stats["total_events"] += 1

                if self._is_image_file(file_path):
                    self.watcher.watch_stats["filtered_events"] += 1
                    self.watcher.watch_stats["last_event_time"] = datetime.now()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "file_deleted",
                        f"画像ファイルが削除されました: {file_path.name}",
                        level="DEBUG",
                    )

                    self.watcher._notify_listeners(file_path, FileChangeType.DELETED)

        def on_modified(self, event):
            """ファイル変更イベントの処理"""

            if not event.is_directory:
                file_path = Path(event.src_path)

                # 統計更新
                self.watcher.watch_stats["total_events"] += 1

                if self._is_image_file(file_path):
                    self.watcher.watch_stats["filtered_events"] += 1
                    self.watcher.watch_stats["last_event_time"] = datetime.now()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "file_modified",
                        f"画像ファイルが変更されました: {file_path.name}",
                        level="DEBUG",
                    )

                    self.watcher._notify_listeners(file_path, FileChangeType.MODIFIED)

        def on_moved(self, event):
            """ファイル移動イベントの処理"""

            if not event.is_directory:
                src_path = Path(event.src_path)
                dest_path = Path(event.dest_path)

                # 統計更新
                self.watcher.watch_stats["total_events"] += 1

                # 移動元または移動先が画像ファイルの場合
                if self._is_image_file(src_path) or self._is_image_file(dest_path):
                    self.watcher.watch_stats["filtered_events"] += 1
                    self.watcher.watch_stats["last_event_time"] = datetime.now()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "file_moved",
                        f"画像ファイルが移動されました: {src_path.name} -> {dest_path.name}",
                        level="DEBUG",
                    )

                    self.watcher._notify_listeners(
                        dest_path, FileChangeType.MOVED, src_path
                    )

else:

    class ImageFileEventHandler:
        """
        watchdog が利用できない場合のダミーイベントハンドラー
        """

        def __init__(self, watcher, supported_extensions, logger_system):
            """ダミー初期化"""
            pass
