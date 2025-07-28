"""
FileDiscoveryService専用エラーハンドリングシステム

ファイル検出サービスに特化したエラークラスと日本語メッセージを提供。
要件5.1, 6.1, 6.2に対応。

Author: Kiro AI Integration System
"""

from enum import Enum
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


class FileDiscoveryErrorLevel(Enum):
    """ファイル検出エラーのレベル分類"""
    WARNING = "warning"      # 警告 - 処理は継続可能
    ERROR = "error"          # エラー - 機能が利用不可
    CRITICAL = "critical"    # 致命的 - アプリケーション停止が必要


class FileDiscoveryError(Exception):
    """ファイル検出エラーの基底クラス"""

    def __init__(self,
                 message: str,
                 error_code: str = None,
                 level: FileDiscoveryErrorLevel = FileDiscoveryErrorLevel.ERROR,
                 file_path: Optional[Path] = None,
              details: Optional[Dict] = None):
        """
        FileDiscoveryErrorの初期化

        Args:
            message: エラーメッセージ（日本語）
            error_code: エラーコード
            level: エラーレベル
            file_path: 関連するファイルパス
            details: 追加の詳細情報
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.level = level
        self.file_path = file_path
        self.details = details or {}
        self.timestamp = datetime.now()


class FolderAccessError(FileDiscoveryError):
    """フォルダアクセスエラー"""

    def __init__(self, folder_path: Path, reason: str = None):
        error_code = "FOLDER_ACCESS_ERROR"
        message = f"フォルダにアクセスできません: {folder_path}"
        if reason:
            message += f" ({reason})"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.ERROR,
            file_path=folder_path,
            details={"reason": reason}
        )


class FolderNotFoundError(FileDiscoveryError):
    """フォルダ不存在エラー"""

    def __init__(self, folder_path: Path):
        error_code = "FOLDER_NOT_FOUND"
        message = f"指定されたフォルダが見つかりません: {folder_path}"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.ERROR,
            file_path=folder_path
        )


class PermissionDeniedError(FileDiscoveryError):
    """権限不足エラー"""

    def __init__(self, path: Path, operation: str = "アクセス"):
        error_code = "PERMISSION_DENIED"
        message = f"権限が不足しています: {path} への{operation}が拒否されました"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.ERROR,
            file_path=path,
            details={"operation": operation}
        )


class FileValidationError(FileDiscoveryError):
    """ファイルバリデーションエラー"""

    def __init__(self, file_path: Path, reason: str):
        error_code = "FILE_VALIDATION_ERROR"
        message = f"ファイルの検証に失敗しました: {file_path.name} - {reason}"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.WARNING,
            file_path=file_path,
            details={"validation_reason": reason}
        )


class CorruptedFileError(FileDiscoveryError):
    """破損ファイルエラー"""

    def __init__(self, file_path: Path, details: str = None):
        error_code = "CORRUPTED_FILE"
        message = f"破損したファイルが検出されました: {file_path.name}"
        if details:
            message += f" - {details}"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.WARNING,
            file_path=file_path,
            details={"corruption_details": details}
        )


class UnsupportedFileFormatError(FileDiscoveryError):
    """未対応ファイル形式エラー"""

    def __init__(self, file_path: Path, supported_formats: List[str]):
        error_code = "UNSUPPORTED_FORMAT"
        message = f"未対応のファイル形式です: {file_path.name} (拡張子: {file_path.suffix})"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.WARNING,
            file_path=file_path,
            details={"supported_formats": supported_formats}
        )


class ScanTimeoutError(FileDiscoveryError):
    """スキャンタイムアウトエラー"""

    def __init__(self, folder_path: Path, timeout_seconds: int):
        error_code = "SCAN_TIMEOUT"
        message = f"フォルダスキャンがタイムアウトしました: {folder_path} ({timeout_seconds}秒)"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.ERROR,
            file_path=folder_path,
            details={"timeout_seconds": timeout_seconds}
        )


class MemoryLimitExceededError(FileDiscoveryError):
    """メモリ制限超過エラー"""

    def __init__(self, current_usage_mb: float, limit_mb: float):
        error_code = "MEMORY_LIMIT_EXCEEDED"
        message = f"メモリ使用量が制限を超過しました: {current_usage_mb:.1f}MB / {limit_mb:.1f}MB"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.CRITICAL,
            details={
                "current_usage_mb": current_usage_mb,
                "limit_mb": limit_mb
            }
        )


class TooManyFilesError(FileDiscoveryError):
    """ファイル数過多エラー"""

    def __init__(self, folder_path: Path, file_count: int, limit: int):
        error_code = "TOO_MANY_FILES"
        message = f"フォルダ内のファイル数が制限を超過しています: {folder_path} ({file_count}個 / 制限: {limit}個)"

        super().__init__(
            message=message,
            error_code=error_code,
            level=FileDiscoveryErrorLevel.WARNING,
            file_path=folder_path,
            details={
                "file_count": file_count,
                "limit": limit
            }
        )


@dataclass
class FileDiscoveryErrorMessages:
    """日本語エラーメッセージの定義"""

    # フォルダ関連メッセージ
    FOLDER_SCANNING = "フォルダをスキャン中..."
    FOLDER_SCAN_COMPLETE = "フォルダスキャンが完了しました"
    FOLDER_NOT_ACCESSIBLE = "フォルダにアクセスできません"
    FOLDER_EMPTY = "このフォルダには画像ファイルがありません"
    FOLDER_PERMISSION_DENIED = "フォルダへのアクセス権限がありません"

    # ファイル関連メッセージ
    FILE_VALIDATION_START = "ファイルの検証を開始しています"
    FILE_VALIDATION_COMPLETE = "ファイルの検証が完了しました"
    FILE_CORRUPTED = "破損したファイルが検出されました"
    FILE_TOO_SMALL = "ファイルサイズが異常に小さいです"
    FILE_UNSUPPORTED_FORMAT = "未対応のファイル形式です"

    # 処理状況メッセージ
    PROCESSING_FILES = "ファイルを処理中... ({current}/{total})"
    LOADING_THUMBNAILS = "サムネイルを読み込み中..."
    SCAN_PROGRESS = "スキャン進行状況: {progress}%"

    # エラー状況メッセージ
    SCAN_ERROR_OCCURRED = "スキャン中にエラーが発生しました"
    VALIDATION_ERROR_OCCURRED = "ファイル検証中にエラーが発生しました"
    PERMISSION_ERROR_OCCURRED = "権限エラーが発生しました"
    TIMEOUT_ERROR_OCCURRED = "処理がタイムアウトしました"
    MEMORY_ERROR_OCCURRED = "メモリ不足エラーが発生しました"

    # 成功メッセージ
    IMAGES_FOUND = "{count}個の画像ファイルが見つかりました"
    VALIDATION_SUCCESS = "すべてのファイルの検証が完了しました"
    SCAN_SUCCESS = "スキャンが正常に完了しました ({duration:.1f}秒)"

    # 警告メッセージ
    SOME_FILES_SKIPPED = "一部のファイルがスキップされました"
    PERFORMANCE_WARNING = "処理に時間がかかっています"
    MEMORY_WARNING = "メモリ使用量が多くなっています"

    # 情報メッセージ
    NO_IMAGES_FOUND = "画像ファイルが見つかりませんでした"
    SUPPORTED_FORMATS = "対応形式: {formats}"
    CACHE_CLEARED = "キャッシュがクリアされました"

    @classmethod
    def get_error_message(cls, error_code: str, **kwargs) -> str:
        """
        エラーコードに基づいて適切な日本語メッセージを取得

        Args:
            error_code: エラーコード
            **kwargs: メッセージのフォーマット用パラメータ

        Returns:
            フォーマットされた日本語エラーメッセージ
        """

        message_map = {
            "FOLDER_ACCESS_ERROR": "フォルダにアクセスできません: {path}",
            "FOLDER_NOT_FOUND": "指定されたフォルダが見つかりません: {path}",
            "PERMISSION_DENIED": "権限が不足しています: {path}",
            "FILE_VALIDATION_ERROR": "ファイルの検証に失敗しました: {filename}",
            "CORRUPTED_FILE": "破損したファイルが検出されました: {filename}",
            "UNSUPPORTED_FORMAT": "未対応のファイル形式です: {filename}",
            "SCAN_TIMEOUT": "フォルダスキャンがタイムアウトしました: {path}",
            "MEMORY_LIMIT_EXCEEDED": "メモリ使用量が制限を超過しました",
            "TOO_MANY_FILES": "フォルダ内のファイル数が制限を超過しています: {path}"
        }

        template = message_map.get(error_code, "不明なエラーが発生しました")

        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @classmethod
    def get_recovery_suggestions(cls, error_code: str) -> List[str]:
        """
        エラーコードに基づいて回復提案を取得

        Args:
            error_code: エラーコード

        Returns:
            回復提案のリスト（日本語）
        """

        suggestions_map = {
            "FOLDER_ACCESS_ERROR": [
                "フォルダが存在することを確認してください",
                "フォルダのアクセス権限を確認してください",
                "別のフォルダを選択してみてください",
                "アプリケーションを管理者権限で実行してみてください"
            ],
            "FOLDER_NOT_FOUND": [
                "フォルダパスが正しいことを確認してください",
                "フォルダが移動または削除されていないか確認してください",
                "別のフォルダを選択してください"
            ],
            "PERMISSION_DENIED": [
                "ファイルまたはフォルダのアクセス権限を確認してください",
                "アプリケーションを管理者権限で実行してみてください",
                "ファイルが他のアプリケーションで使用されていないか確認してください"
            ],
            "FILE_VALIDATION_ERROR": [
                "ファイルが破損していないか確認してください",
                "ファイル形式が対応しているか確認してください",
                "別のファイルで試してみてください"
            ],
            "CORRUPTED_FILE": [
                "元のファイルをバックアップから復元してください",
                "ファイルを別の場所からコピーし直してください",
                "画像編集ソフトでファイルを修復してみてください"
            ],
            "UNSUPPORTED_FORMAT": [
                "対応している形式に変換してください",
                "対応形式の一覧を確認してください",
                "別のファイルを選択してください"
            ],
            "SCAN_TIMEOUT": [
                "フォルダ内のファイル数を減らしてください",
                "サブフォルダに分けて処理してください",
                "アプリケーションを再起動してください"
            ],
            "MEMORY_LIMIT_EXCEEDED": [
                "他のアプリケーションを終了してメモリを解放してください",
                "キャッシュをクリアしてください",
                "アプリケーションを再起動してください",
                "処理するファイル数を減らしてください"
            ],
            "TOO_MANY_FILES": [
                "フォルダ内のファイル数を減らしてください",
                "サブフォルダに分けて処理してください",
                "段階的読み込み機能を有効にしてください"
            ]
        }

        return suggestions_map.get(error_code, [
            "操作を再試行してください",
            "アプリケーションを再起動してください",
            "問題が続く場合はサポートにお問い合わせください"
        ])


class FileDiscoveryErrorHandler:
    """FileDiscoveryService専用エラーハンドラー"""

    def __init__(self, logger=None):
        """
        エラーハンドラーの初期化

        Args:
            logger: ログシステムインスタンス
        """
        self.logger = logger
        self.error_counts: Dict[str, int] = {}
        self.recent_errors: List[FileDiscoveryError] = []
        self.max_recent_errors = 50

    def handle_error(self, error: FileDiscoveryError) -> Dict[str, any]:
        """
        FileDiscoveryErrorを処理する

        Args:
            error: 処理するエラー

        Returns:
            エラー処理結果の辞書
        """

        # エラー統計を更新
        self.error_counts[error.error_code] = self.error_counts.get(error.error_code, 0) + 1

        # 最近のエラーリストに追加
        self.recent_errors.insert(0, error)
        self.recent_errors = self.recent_errors[:self.max_recent_errors]

        # ログに記録
        self._log_error(error)

        # 回復提案を取得
        recovery_suggestions = FileDiscoveryErrorMessages.get_recovery_suggestions(error.error_code)

        # エラー処理結果を返す
        return {
            "error_code": error.error_code,
            "message": error.message,
            "level": error.level.value,
            "file_path": str(error.file_path) if error.file_path else None,
            "timestamp": error.timestamp.isoformat(),
            "recovery_suggestions": recovery_suggestions,
            "details": error.details
        }

    def _log_error(self, error: FileDiscoveryError):
        """エラーをログに記録"""

        if not self.logger:
            return

        log_message = f"[FileDiscovery] {error.message}"
        log_extra = {
            "error_code": error.error_code,
            "file_path": str(error.file_path) if error.file_path else None,
            "details": error.details
        }

        if error.level == FileDiscoveryErrorLevel.CRITICAL:
            self.logger.critical(log_message, extra=log_extra)
        elif error.level == FileDiscoveryErrorLevel.ERROR:
            self.logger.error(log_message, extra=log_extra)
        elif error.level == FileDiscoveryErrorLevel.WARNING:
            self.logger.warning(log_message, extra=log_extra)

    def get_error_statistics(self) -> Dict[str, any]:
        """エラー統計情報を取得"""

        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts.copy(),
            "recent_error_count": len(self.recent_errors),
            "most_common_error": max(self.error_counts, key=self.error_counts.get) if self.error_counts else None
        }

    def clear_error_history(self):
        """エラー履歴をクリア"""

        self.error_counts.clear()
        self.recent_errors.clear()

        if self.logger:
            self.logger.info("[FileDiscovery] エラー履歴がクリアされました")
