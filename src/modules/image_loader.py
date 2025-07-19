"""
画像読み込み機能を提供するモジュール
PhotoGeoView プロジェクト用の画像処理機能
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image, UnidentifiedImageError
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex
from PyQt6.QtGui import QPixmap, QImage

from src.core.logger import get_logger
from src.core.utils import is_image_file, get_supported_image_extensions


class ImageLoader(QObject):
    """画像読み込みクラス"""

    # シグナル定義
    image_loaded = pyqtSignal(str, QPixmap)  # 画像読み込み完了時に発信
    thumbnail_loaded = pyqtSignal(str, QPixmap)  # サムネイル読み込み完了時に発信
    loading_progress = pyqtSignal(int, int)  # 読み込み進捗時に発信
    loading_finished = pyqtSignal()  # 読み込み完了時に発信
    error_occurred = pyqtSignal(str, str)  # エラー発生時に発信

    def __init__(self):
        """ImageLoaderの初期化"""
        super().__init__()
        self.logger = get_logger(__name__)
        self.mutex = QMutex()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._loading_files: List[str] = []
        self._loaded_images: Dict[str, QPixmap] = {}
        self._loaded_thumbnails: Dict[str, QPixmap] = {}

    def load_directory(self, directory_path: str) -> List[str]:
        """
        ディレクトリ内の画像ファイルを読み込み

        Args:
            directory_path: ディレクトリパス

        Returns:
            画像ファイルパスのリスト
        """
        try:
            self.logger.info(f"ディレクトリを読み込み中: {directory_path}")

            if not os.path.exists(directory_path):
                self.logger.error(f"ディレクトリが存在しません: {directory_path}")
                return []

            # 画像ファイルを検索
            image_files = []
            for ext in get_supported_image_extensions():
                image_files.extend(Path(directory_path).glob(f"*{ext}"))
                image_files.extend(Path(directory_path).glob(f"*{ext.upper()}"))

            # パスを文字列に変換
            image_paths = [str(f) for f in image_files if f.is_file()]

            self.logger.info(f"画像ファイルを {len(image_paths)} 個見つけました")
            return image_paths

        except Exception as e:
            self.logger.error(
                f"ディレクトリの読み込みに失敗しました: {directory_path}, エラー: {e}"
            )
            return []

    def load_image(
        self, file_path: str, size: Optional[tuple] = None
    ) -> Optional[QPixmap]:
        """
        画像ファイルを読み込み

        Args:
            file_path: 画像ファイルパス
            size: リサイズサイズ (width, height)

        Returns:
            読み込まれた画像のQPixmap、失敗時はNone
        """
        try:
            if not is_image_file(file_path):
                self.logger.warning(f"画像ファイルではありません: {file_path}")
                return None

            # キャッシュをチェック
            cache_key = f"{file_path}_{size}" if size else file_path
            if cache_key in self._loaded_images:
                self.logger.debug(f"キャッシュから画像を取得: {file_path}")
                return self._loaded_images[cache_key]

            # PILで画像を読み込み
            with Image.open(file_path) as img:
                # 画像をRGBに変換
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # リサイズ
                if size:
                    img.thumbnail(size, Image.Resampling.LANCZOS)

                # QImageに変換
                qimage = QImage(
                    img.tobytes(),
                    img.width,
                    img.height,
                    img.width * 3,
                    QImage.Format.Format_RGB888,
                )

                # QPixmapに変換
                pixmap = QPixmap.fromImage(qimage)

                # キャッシュに保存
                self._loaded_images[cache_key] = pixmap

                self.logger.debug(f"画像を読み込みました: {file_path}")
                return pixmap

        except UnidentifiedImageError:
            self.logger.error(f"画像形式が認識できません: {file_path}")
            self.error_occurred.emit(file_path, "画像形式が認識できません")
        except Exception as e:
            self.logger.error(f"画像の読み込みに失敗しました: {file_path}, エラー: {e}")
            self.error_occurred.emit(file_path, str(e))

        return None

    def load_thumbnail(
        self, file_path: str, size: tuple = (120, 120)
    ) -> Optional[QPixmap]:
        """
        サムネイル画像を読み込み

        Args:
            file_path: 画像ファイルパス
            size: サムネイルサイズ (width, height)

        Returns:
            読み込まれたサムネイルのQPixmap、失敗時はNone
        """
        try:
            if not is_image_file(file_path):
                return None

            # キャッシュをチェック
            cache_key = f"{file_path}_thumb_{size}"
            if cache_key in self._loaded_thumbnails:
                return self._loaded_thumbnails[cache_key]

            # サムネイルを読み込み
            pixmap = self.load_image(file_path, size)
            if pixmap:
                self._loaded_thumbnails[cache_key] = pixmap
                self.thumbnail_loaded.emit(file_path, pixmap)

            return pixmap

        except Exception as e:
            self.logger.error(
                f"サムネイルの読み込みに失敗しました: {file_path}, エラー: {e}"
            )
            return None

    def load_images_async(
        self, file_paths: List[str], size: Optional[tuple] = None
    ) -> None:
        """
        画像ファイルを非同期で読み込み

        Args:
            file_paths: 画像ファイルパスのリスト
            size: リサイズサイズ (width, height)
        """
        try:
            self.logger.info(f"非同期で画像を読み込み開始: {len(file_paths)} ファイル")

            # 読み込み中のファイルリストを更新
            with self.mutex:
                self._loading_files = file_paths.copy()

            total_files = len(file_paths)
            loaded_count = 0

            # 非同期で画像を読み込み
            futures = []
            for file_path in file_paths:
                future = self.executor.submit(self.load_image, file_path, size)
                futures.append((file_path, future))

            # 完了した画像を処理
            for file_path, future in futures:
                try:
                    pixmap = future.result()
                    if pixmap:
                        self.image_loaded.emit(file_path, pixmap)

                    loaded_count += 1
                    self.loading_progress.emit(loaded_count, total_files)

                except Exception as e:
                    self.logger.error(
                        f"非同期読み込みでエラー: {file_path}, エラー: {e}"
                    )
                    self.error_occurred.emit(file_path, str(e))

            # 読み込み完了
            with self.mutex:
                self._loading_files.clear()

            self.loading_finished.emit()
            self.logger.info("非同期画像読み込みが完了しました")

        except Exception as e:
            self.logger.error(f"非同期画像読み込みに失敗しました: {e}")
            self.loading_finished.emit()

    def load_thumbnails_async(
        self, file_paths: List[str], size: tuple = (120, 120)
    ) -> None:
        """
        サムネイル画像を非同期で読み込み

        Args:
            file_paths: 画像ファイルパスのリスト
            size: サムネイルサイズ (width, height)
        """
        try:
            self.logger.info(
                f"非同期でサムネイルを読み込み開始: {len(file_paths)} ファイル"
            )

            total_files = len(file_paths)
            loaded_count = 0

            # 非同期でサムネイルを読み込み
            futures = []
            for file_path in file_paths:
                future = self.executor.submit(self.load_thumbnail, file_path, size)
                futures.append((file_path, future))

            # 完了したサムネイルを処理
            for file_path, future in futures:
                try:
                    pixmap = future.result()
                    if pixmap:
                        self.thumbnail_loaded.emit(file_path, pixmap)

                    loaded_count += 1
                    self.loading_progress.emit(loaded_count, total_files)

                except Exception as e:
                    self.logger.error(
                        f"非同期サムネイル読み込みでエラー: {file_path}, エラー: {e}"
                    )
                    self.error_occurred.emit(file_path, str(e))

            self.loading_finished.emit()
            self.logger.info("非同期サムネイル読み込みが完了しました")

        except Exception as e:
            self.logger.error(f"非同期サムネイル読み込みに失敗しました: {e}")
            self.loading_finished.emit()

    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        画像ファイルの情報を取得

        Args:
            file_path: 画像ファイルパス

        Returns:
            画像情報辞書
        """
        try:
            if not is_image_file(file_path):
                return {}

            with Image.open(file_path) as img:
                info = {
                    "file_path": file_path,
                    "file_name": Path(file_path).name,
                    "file_size": os.path.getsize(file_path),
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "dpi": img.info.get("dpi", (None, None)),
                }

                return info

        except Exception as e:
            self.logger.error(f"画像情報の取得に失敗しました: {file_path}, エラー: {e}")
            return {}

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        with self.mutex:
            self._loaded_images.clear()
            self._loaded_thumbnails.clear()
        self.logger.info("画像キャッシュをクリアしました")

    def get_cache_size(self) -> int:
        """
        キャッシュサイズを取得

        Returns:
            キャッシュされている画像数
        """
        return len(self._loaded_images) + len(self._loaded_thumbnails)

    def is_loading(self) -> bool:
        """
        読み込み中かどうかを確認

        Returns:
            読み込み中の場合はTrue
        """
        with self.mutex:
            return len(self._loading_files) > 0

    def cancel_loading(self) -> None:
        """読み込みをキャンセル"""
        with self.mutex:
            self._loading_files.clear()
        self.logger.info("画像読み込みをキャンセルしました")

    def __del__(self):
        """デストラクタ"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
