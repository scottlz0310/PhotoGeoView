"""
画像読み込み機能を提供するモジュール（セグフォルト対策版）
PhotoGeoView プロジェクト用の画像処理機能
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QImageReader

from src.core.logger import get_logger
from src.core.utils import is_image_file, get_supported_image_extensions


class ImageLoader(QObject):
    """画像読み込みクラス（スレッドセーフ対応）"""

    # シグナル定義
    image_loaded = pyqtSignal(str, QPixmap)
    thumbnail_loaded = pyqtSignal(str, QPixmap)
    loading_progress = pyqtSignal(int, int)
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str, str)

    def __init__(self):
        """ImageLoaderの初期化"""
        super().__init__()
        self.logger = get_logger(__name__)
        self.mutex = QMutex()
        self.executor = ThreadPoolExecutor(max_workers=2)  # ワーカー数を減らす
        self._loading_files: List[str] = []
        self._loaded_images: Dict[str, QPixmap] = {}
        self._loaded_thumbnails: Dict[str, QPixmap] = {}

        # バッチ処理用タイマー
        self._batch_timer = QTimer()
        self._batch_timer.timeout.connect(self._process_batch_results)
        self._batch_results = []

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

    def _load_image_data(self, file_path: str, size: Optional[Tuple[int, int]] = None) -> Optional[bytes]:
        """
        画像データをワーカースレッドで読み込み（スレッドセーフ）

        Args:
            file_path: 画像ファイルパス
            size: リサイズサイズ

        Returns:
            画像のバイナリデータまたはNone
        """
        try:
            if not is_image_file(file_path) or not os.path.exists(file_path):
                return None

            # QImageを使用してスレッドセーフに読み込み
            image = QImage(file_path)
            if image.isNull():
                self.logger.error(f"画像の読み込みに失敗: {file_path}")
                return None

            # リサイズ処理
            if size and (image.width() > size[0] or image.height() > size[1]):
                image = image.scaled(
                    size[0], size[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            # バイト配列に変換
            from PyQt6.QtCore import QByteArray, QBuffer
            from PyQt6.QtCore import QIODevice

            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            return buffer.data().data()

        except Exception as e:
            self.logger.error(f"画像データ読み込みエラー: {file_path}, {e}")
            return None

    def load_image(
        self, file_path: str, size: Optional[Tuple[int, int]] = None
    ) -> Optional[QPixmap]:
        """
        画像ファイルを読み込み（メインスレッド用）

        Args:
            file_path: 画像ファイルパス
            size: リサイズサイズ (width, height)

        Returns:
            読み込まれた画像のQPixmap、失敗時はNone
        """
        try:
            self.logger.debug(f"[DEBUG] load_image開始: {file_path}")

            if not is_image_file(file_path):
                self.logger.warning(f"画像ファイルではありません: {file_path}")
                return None

            if not os.path.exists(file_path):
                self.logger.error(f"ファイルが存在しません: {file_path}")
                self.error_occurred.emit(file_path, "ファイルが存在しません")
                return None

            # キャッシュをチェック
            cache_key = f"{file_path}_{size}" if size else file_path
            if cache_key in self._loaded_images:
                cached_pixmap = self._loaded_images[cache_key]
                if not cached_pixmap.isNull():
                    self.logger.debug(f"キャッシュから画像を取得: {file_path}")
                    return cached_pixmap

            # メインスレッドでQImageを使用して安全に読み込み
            image = QImage(file_path)
            if image.isNull():
                self.logger.error(f"画像の読み込みに失敗しました: {file_path}")
                self.error_occurred.emit(file_path, "画像の読み込みに失敗しました")
                return None

            # リサイズ（必要な場合）
            if size and (image.width() > size[0] or image.height() > size[1]):
                image = image.scaled(
                    size[0], size[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            # QPixmapに変換（メインスレッドでのみ実行）
            pixmap = QPixmap.fromImage(image)
            if pixmap.isNull():
                self.logger.error(f"QPixmap変換に失敗: {file_path}")
                return None

            # キャッシュに保存
            self._loaded_images[cache_key] = pixmap
            self.logger.debug(f"画像を読み込みました: {file_path}")
            return pixmap

        except Exception as e:
            self.logger.error(f"画像の読み込みに失敗しました: {file_path}, エラー: {e}")
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")
            self.error_occurred.emit(file_path, str(e))

        return None

    def load_thumbnail(
        self, file_path: str, size: Tuple[int, int] = (120, 120)
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

    def _process_batch_results(self):
        """バッチ処理結果をメインスレッドで処理"""
        self._batch_timer.stop()

        results_to_process = self._batch_results.copy()
        self._batch_results.clear()

        for file_path, image_data, size, is_thumbnail in results_to_process:
            try:
                if image_data is None:
                    self.error_occurred.emit(file_path, "画像データの読み込みに失敗")
                    continue

                # メインスレッドでQPixmapを作成
                from PyQt6.QtCore import QByteArray
                qbyte_array = QByteArray(image_data)
                image = QImage.fromData(qbyte_array)

                if image.isNull():
                    self.error_occurred.emit(file_path, "画像データの変換に失敗")
                    continue

                pixmap = QPixmap.fromImage(image)
                if pixmap.isNull():
                    continue

                # キャッシュに保存
                cache_key = f"{file_path}_{size}" if size else file_path
                if is_thumbnail:
                    cache_key = f"{file_path}_thumb_{size}"
                    self._loaded_thumbnails[cache_key] = pixmap
                    self.thumbnail_loaded.emit(file_path, pixmap)
                else:
                    self._loaded_images[cache_key] = pixmap
                    self.image_loaded.emit(file_path, pixmap)

            except Exception as e:
                self.logger.error(f"バッチ処理エラー: {file_path}, {e}")
                self.error_occurred.emit(file_path, str(e))

    def load_images_async(
        self, file_paths: List[str], size: Optional[Tuple[int, int]] = None
    ) -> None:
        """
        画像ファイルを非同期で読み込み（改良版）

        Args:
            file_paths: 画像ファイルパスのリスト
            size: リサイズサイズ (width, height)
        """
        try:
            self.logger.info(f"非同期で画像を読み込み開始: {len(file_paths)} ファイル")

            # 読み込み中のファイルリストを更新
            self.mutex.lock()
            try:
                self._loading_files = file_paths.copy()
            finally:
                self.mutex.unlock()

            total_files = len(file_paths)
            loaded_count = 0

            # バッチサイズを制限
            batch_size = 10
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i + batch_size]

                # 非同期でバッチを処理
                futures = []
                for file_path in batch:
                    future = self.executor.submit(self._load_image_data, file_path, size)
                    futures.append((file_path, future))

                # バッチの完了を待機
                for file_path, future in futures:
                    try:
                        image_data = future.result(timeout=10)  # タイムアウト設定
                        self._batch_results.append((file_path, image_data, size, False))

                        loaded_count += 1
                        self.loading_progress.emit(loaded_count, total_files)

                    except Exception as e:
                        self.logger.error(f"非同期読み込みでエラー: {file_path}, エラー: {e}")
                        self.error_occurred.emit(file_path, str(e))
                        loaded_count += 1
                        self.loading_progress.emit(loaded_count, total_files)

                # バッチ結果を処理
                if self._batch_results:
                    self._batch_timer.start(10)  # 10ms後に処理

            # 読み込み完了
            self.mutex.lock()
            try:
                self._loading_files.clear()
            finally:
                self.mutex.unlock()

            # 最終的な完了処理を遅延実行
            QTimer.singleShot(100, self.loading_finished.emit)
            self.logger.info("非同期画像読み込みが完了しました")

        except Exception as e:
            self.logger.error(f"非同期画像読み込みに失敗しました: {e}")
            self.loading_finished.emit()

    def load_thumbnails_async(
        self, file_paths: List[str], size: Tuple[int, int] = (120, 120)
    ) -> None:
        """
        サムネイル画像を非同期で読み込み（改良版）

        Args:
            file_paths: 画像ファイルパスのリスト
            size: サムネイルサイズ (width, height)
        """
        try:
            self.logger.info(f"非同期でサムネイルを読み込み開始: {len(file_paths)} ファイル")

            total_files = len(file_paths)
            loaded_count = 0

            # バッチ処理でサムネイルを読み込み
            batch_size = 5  # サムネイルはより小さいバッチサイズ
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i + batch_size]

                futures = []
                for file_path in batch:
                    future = self.executor.submit(self._load_image_data, file_path, size)
                    futures.append((file_path, future))

                for file_path, future in futures:
                    try:
                        image_data = future.result(timeout=10)
                        self._batch_results.append((file_path, image_data, size, True))

                        loaded_count += 1
                        self.loading_progress.emit(loaded_count, total_files)

                    except Exception as e:
                        self.logger.error(f"非同期サムネイル読み込みでエラー: {file_path}, エラー: {e}")
                        self.error_occurred.emit(file_path, str(e))
                        loaded_count += 1
                        self.loading_progress.emit(loaded_count, total_files)

                # バッチ結果を処理
                if self._batch_results:
                    self._batch_timer.start(10)

            QTimer.singleShot(100, self.loading_finished.emit)
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

            # QImageReaderを使用して画像情報を取得
            reader = QImageReader(file_path)
            if not reader.canRead():
                self.logger.error(f"画像ファイルを読み込めません: {file_path}")
                return {}

            size = reader.size()
            format_name = reader.format().data().decode('utf-8')

            info = {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "file_size": os.path.getsize(file_path),
                "width": size.width(),
                "height": size.height(),
                "format": format_name.upper(),
                "mode": "RGB",
                "dpi": (None, None),
            }

            return info

        except Exception as e:
            self.logger.error(f"画像情報の取得に失敗しました: {file_path}, エラー: {e}")
            return {}

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self.mutex.lock()
        try:
            self._loaded_images.clear()
            self._loaded_thumbnails.clear()
        finally:
            self.mutex.unlock()
        self.logger.info("画像キャッシュをクリアしました")

    def get_cache_size(self) -> int:
        """キャッシュサイズを取得"""
        return len(self._loaded_images) + len(self._loaded_thumbnails)

    def is_loading(self) -> bool:
        """読み込み中かどうかを確認"""
        self.mutex.lock()
        try:
            return len(self._loading_files) > 0
        finally:
            self.mutex.unlock()

    def cancel_loading(self) -> None:
        """読み込みをキャンセル"""
        self.mutex.lock()
        try:
            self._loading_files.clear()
            self._batch_results.clear()
        finally:
            self.mutex.unlock()
        self.logger.info("画像読み込みをキャンセルしました")

    def __del__(self):
        """デストラクタ"""
        if hasattr(self, "_batch_timer"):
            self._batch_timer.stop()
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)  # 適切にシャットダウン
