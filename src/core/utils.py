"""
共通ユーティリティ関数を提供するモジュール
PhotoGeoView プロジェクト用のユーティリティ機能を提供
"""

import os
import platform
from pathlib import Path
from typing import List, Optional, Tuple

from .logger import get_logger


logger = get_logger(__name__)


def get_supported_image_extensions() -> List[str]:
    """
    サポートされている画像ファイル拡張子の取得

    Returns:
        サポートされている画像ファイル拡張子のリスト
    """
    return [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"]


def is_image_file(file_path: str) -> bool:
    """
    ファイルが画像ファイルかどうかを判定

    Args:
        file_path: ファイルパス

    Returns:
        画像ファイルの場合True
    """
    if not file_path:
        return False

    file_ext = Path(file_path).suffix.lower()
    return file_ext in get_supported_image_extensions()


def get_file_size_mb(file_path: str) -> float:
    """
    ファイルサイズをMB単位で取得

    Args:
        file_path: ファイルパス

    Returns:
        ファイルサイズ（MB）
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError as e:
        logger.error(f"ファイルサイズの取得に失敗しました: {file_path}, エラー: {e}")
        return 0.0


def format_file_size(size_bytes: int) -> str:
    """
    ファイルサイズを人間が読みやすい形式にフォーマット

    Args:
        size_bytes: ファイルサイズ（バイト）

    Returns:
        フォーマットされたファイルサイズ文字列
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_system_info() -> dict:
    """
    システム情報の取得

    Returns:
        システム情報辞書
    """
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture()[0],
        "python_version": platform.python_version(),
        "processor": platform.processor(),
    }


def ensure_directory_exists(directory_path: str) -> bool:
    """
    ディレクトリが存在することを保証

    Args:
        directory_path: ディレクトリパス

    Returns:
        作成成功の場合True
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"ディレクトリの作成に失敗しました: {directory_path}, エラー: {e}")
        return False


def get_relative_path(base_path: str, target_path: str) -> str:
    """
    相対パスの取得

    Args:
        base_path: 基準パス
        target_path: 対象パス

    Returns:
        相対パス
    """
    try:
        base = Path(base_path).resolve()
        target = Path(target_path).resolve()
        return str(target.relative_to(base))
    except ValueError:
        # 相対パスが取得できない場合は絶対パスを返す
        return target_path


def normalize_path(path: str) -> str:
    """
    パスの正規化

    Args:
        path: パス文字列

    Returns:
        正規化されたパス
    """
    return str(Path(path).resolve())


def split_path(path: str) -> Tuple[str, str]:
    """
    パスをディレクトリとファイル名に分割

    Args:
        path: パス文字列

    Returns:
        (ディレクトリパス, ファイル名)のタプル
    """
    path_obj = Path(path)
    return str(path_obj.parent), path_obj.name


def get_file_info(file_path: str) -> dict:
    """
    ファイル情報の取得

    Args:
        file_path: ファイルパス

    Returns:
        ファイル情報辞書
    """
    try:
        path_obj = Path(file_path)
        stat = path_obj.stat()

        return {
            "name": path_obj.name,
            "stem": path_obj.stem,
            "suffix": path_obj.suffix,
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "is_file": path_obj.is_file(),
            "is_dir": path_obj.is_dir(),
            "exists": path_obj.exists(),
        }
    except Exception as e:
        logger.error(f"ファイル情報の取得に失敗しました: {file_path}, エラー: {e}")
        return {}


def safe_filename(filename: str) -> str:
    """
    安全なファイル名に変換

    Args:
        filename: 元のファイル名

    Returns:
        安全なファイル名
    """
    # 危険な文字を置換
    dangerous_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, "_")

    # 先頭と末尾の空白・ドットを削除
    safe_name = safe_name.strip(" .")

    # 空文字列の場合はデフォルト名を返す
    if not safe_name:
        safe_name = "unnamed"

    return safe_name


def get_cache_directory() -> str:
    """
    キャッシュディレクトリのパスを取得

    Returns:
        キャッシュディレクトリのパス
    """
    cache_dir = Path("cache")
    ensure_directory_exists(str(cache_dir))
    return str(cache_dir)


def clear_cache() -> bool:
    """
    キャッシュディレクトリのクリア

    Returns:
        クリア成功の場合True
    """
    try:
        cache_dir = Path("cache")
        if cache_dir.exists():
            import shutil

            shutil.rmtree(cache_dir)
            cache_dir.mkdir()
            logger.info("キャッシュディレクトリをクリアしました")
        return True
    except Exception as e:
        logger.error(f"キャッシュのクリアに失敗しました: {e}")
        return False
