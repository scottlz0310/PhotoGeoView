"""
サムネイル生成機能を提供するモジュール
PhotoGeoView プロジェクト用のサムネイル処理機能
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QObject, pyqtSignal, QMutex, Qt
from PyQt6.QtGui import QPixmap, QImage, QImageReader, QPainter

from src.core.logger import get_logger
from src.core.utils import is_image_file, ensure_directory_exists, get_cache_directory


class ThumbnailGenerator(QObject):
    """サムネイル生成クラス"""

    # シグナル定義
    thumbnail_generated = pyqtSignal(str, QPixmap)  # サムネイル生成完了時に発信
    generation_progress = pyqtSignal(int, int)  # 生成進捗時に発信
    generation_finished = pyqtSignal()  # 生成完了時に発信
    error_occurred = pyqtSignal(str, str)  # エラー発生時に発信

    def __init__(self, cache_dir: Optional[str] = None):
        """
        ThumbnailGeneratorの初期化

        Args:
            cache_dir: キャッシュディレクトリパス
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.mutex = QMutex()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # キャッシュディレクトリの設定
        self.cache_dir = cache_dir or os.path.join(get_cache_directory(), "thumbnails")
        ensure_directory_exists(self.cache_dir)

        # 生成中のファイルリスト
        self._generating_files: List[str] = []

        self.logger.info(f"サムネイルジェネレーターを初期化しました: {self.cache_dir}")

    def generate_thumbnail(
        self, file_path: str, size: tuple[int, int] = (120, 120), quality: int = 95
    ) -> Optional[QPixmap]:
        """
        サムネイルを生成

        Args:
            file_path: 画像ファイルパス
            size: サムネイルサイズ (width, height)
            quality: JPEG品質 (1-100)

        Returns:
            生成されたサムネイルのQPixmap、失敗時はNone
        """
        try:
            if not is_image_file(file_path):
                self.logger.warning(f"画像ファイルではありません: {file_path}")
                return None

            # キャッシュファイルパスを生成
            cache_path = self._get_cache_path(file_path, size)

            # キャッシュが存在する場合は読み込み
            if os.path.exists(cache_path):
                self.logger.debug(f"キャッシュからサムネイルを読み込み: {file_path}")
                cached_thumbnail = self._load_cached_thumbnail(cache_path)
                if cached_thumbnail and not cached_thumbnail.isNull():
                    self.logger.debug(
                        f"[generate_thumbnail] emit cached: file_path={file_path}"
                    )
                    self.thumbnail_generated.emit(file_path, cached_thumbnail)
                    return cached_thumbnail

            # サムネイルを生成
            thumbnail = self._create_thumbnail(file_path, size, quality)
            if thumbnail is not None and not thumbnail.isNull():
                # 【デバッグ用】キャッシュ保存を一時的に無効化
                # キャッシュに保存
                # self._save_thumbnail_cache(thumbnail, cache_path, quality)
                self.logger.debug(
                    f"[generate_thumbnail] emit: file_path={file_path}, isNull={thumbnail.isNull()}"
                )
                self.thumbnail_generated.emit(file_path, thumbnail)
            else:
                self.logger.error(
                    f"[generate_thumbnail] サムネイル生成失敗または不正: file_path={file_path}, thumbnail is None or isNull"
                )
            return thumbnail

        except Exception as e:
            self.logger.error(
                f"サムネイルの生成に失敗しました: {file_path}, エラー: {e}"
            )
            self.error_occurred.emit(file_path, str(e))
            return None

    def _get_cache_path(self, file_path: str, size: tuple[int, int]) -> str:
        """
        キャッシュファイルパスを生成

        Args:
            file_path: 画像ファイルパス
            size: サムネイルサイズ

        Returns:
            キャッシュファイルパス
        """
        # ファイルパスとサイズからハッシュを生成
        cache_key = f"{file_path}_{size[0]}x{size[1]}"
        hash_value = hashlib.md5(cache_key.encode()).hexdigest()

        # ファイル拡張子を取得
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in [
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".gif",
            ".tiff",
            ".tif",
            ".webp",
        ]:
            file_ext = ".jpg"  # デフォルトはJPEG

        return os.path.join(self.cache_dir, f"{hash_value}{file_ext}")

    def _create_thumbnail(
        self, file_path: str, size: tuple[int, int], quality: int
    ) -> Optional[QPixmap]:
        """
        サムネイル画像を作成（高品質サムネイル生成）

        Args:
            file_path: 画像ファイルパス
            size: サムネイルサイズ
            quality: JPEG品質

        Returns:
            生成されたサムネイルのQPixmap
        """
        try:
            # QImageReaderを使用してより詳細なエラー情報を取得
            reader = QImageReader(file_path)

            if not reader.canRead():
                self.logger.error(f"[_create_thumbnail] 読み込み不可: {reader.errorString()}, file_path={file_path}")
                return None

            # 画像を読み込み
            image = reader.read()

            if image.isNull():
                self.logger.error(f"[_create_thumbnail] 読み込み失敗: {reader.errorString()}, file_path={file_path}")
                return None

            # 高品質サムネイル生成方法1: QPainterを使用した方法
            thumbnail_pixmap = self._create_thumbnail_with_painter(image, size[0])

            if thumbnail_pixmap is not None and not thumbnail_pixmap.isNull():
                return thumbnail_pixmap

            # フォールバック: 従来の方法
            pixmap = QPixmap.fromImage(image)
            if pixmap.isNull():
                self.logger.error(f"[_create_thumbnail] QPixmap変換失敗: {file_path}")
                return None

            # アスペクト比を維持してリサイズ（高品質変換）
            scaled = pixmap.scaled(
                size[0],
                size[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            return scaled

        except Exception as e:
            self.logger.error(
                f"サムネイル画像の作成に失敗しました: {file_path}, エラー: {e}"
            )
            return None

    def _create_thumbnail_with_painter(self, image: QImage, size: int) -> Optional[QPixmap]:
        """
        QPainterを使用した高品質サムネイル生成（改良版）

        Args:
            image: 元画像のQImage
            size: サムネイルサイズ（正方形）

        Returns:
            生成されたサムネイルのQPixmap
        """
        try:
            if image.isNull():
                return None

            # 元の画像がすでに小さい場合は直接QPixmapに変換
            orig_width = image.width()
            orig_height = image.height()
            
            if orig_width <= size and orig_height <= size:
                return QPixmap.fromImage(image)

            # 段階的スケーリングでより高品質な結果を得る
            # 最初に大きめのサイズにスケーリング、その後最終サイズに
            intermediate_size = max(size * 2, min(orig_width, orig_height))
            
            if max(orig_width, orig_height) > intermediate_size:
                # 中間サイズにスケール
                intermediate_image = image.scaled(
                    intermediate_size, 
                    intermediate_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                intermediate_image = image

            # 最終サイズにスケール
            final_image = intermediate_image.scaled(
                size, 
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # 正方形の出力用QImageを作成（高品質フォーマット使用）
            output_image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
            output_image.fill(Qt.GlobalColor.white)  # 白背景に変更

            # 中央配置の計算
            x = (size - final_image.width()) // 2
            y = (size - final_image.height()) // 2

            # QPainterで高品質描画
            painter = QPainter(output_image)
            
            # すべての高品質レンダリングヒントを有効化
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
            
            # 高品質な補間モードを設定
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # 最終描画
            painter.drawImage(x, y, final_image)
            painter.end()

            return QPixmap.fromImage(output_image)

        except Exception as e:
            self.logger.error(f"QPainterサムネイル生成エラー: {e}")
            return None

    def _save_thumbnail_cache(
        self, pixmap: QPixmap, cache_path: str, quality: int
    ) -> bool:
        """
        サムネイルをキャッシュに保存

        Args:
            pixmap: サムネイルのQPixmap
            cache_path: キャッシュファイルパス
            quality: JPEG品質

        Returns:
            保存成功の場合True
        """
        try:
            # QPixmapを直接JPEGファイルとして保存
            success = pixmap.save(cache_path, "JPEG", quality)

            if success:
                self.logger.debug(f"サムネイルをキャッシュに保存しました: {cache_path}")
                return True
            else:
                self.logger.error(f"サムネイルの保存に失敗しました: {cache_path}")
                return False

        except Exception as e:
            self.logger.error(
                f"サムネイルのキャッシュ保存に失敗しました: {cache_path}, エラー: {e}"
            )
            return False

    def _load_cached_thumbnail(self, cache_path: str) -> Optional[QPixmap]:
        """
        キャッシュからサムネイルを読み込み

        Args:
            cache_path: キャッシュファイルパス

        Returns:
            読み込まれたサムネイルのQPixmap
        """
        try:
            # QPixmapを直接ファイルから読み込み
            pixmap = QPixmap(cache_path)

            if pixmap.isNull():
                self.logger.error(f"キャッシュファイルの読み込みに失敗しました: {cache_path}")
                return None

            return pixmap

        except Exception as e:
            self.logger.error(
                f"キャッシュからのサムネイル読み込みに失敗しました: {cache_path}, エラー: {e}"
            )
            return None

    def generate_thumbnails_async(
        self, file_paths: List[str], size: tuple[int, int] = (120, 120), quality: int = 85
    ) -> None:
        """
        サムネイルを非同期で生成

        Args:
            file_paths: 画像ファイルパスのリスト
            size: サムネイルサイズ
            quality: JPEG品質
        """
        try:
            self.logger.info(
                f"非同期でサムネイルを生成開始: {len(file_paths)} ファイル"
            )

            # 生成中のファイルリストを更新
            self.mutex.lock()
            try:
                self._generating_files = file_paths.copy()
            finally:
                self.mutex.unlock()

            total_files = len(file_paths)
            generated_count = 0

            # 非同期でサムネイルを生成
            futures = []
            for file_path in file_paths:
                future = self.executor.submit(
                    self.generate_thumbnail, file_path, size, quality
                )
                futures.append((file_path, future))

            # 完了したサムネイルを処理
            for file_path, future in futures:
                try:
                    pixmap = future.result()
                    if pixmap:
                        self.thumbnail_generated.emit(file_path, pixmap)

                    generated_count += 1
                    self.generation_progress.emit(generated_count, total_files)

                except Exception as e:
                    self.logger.error(
                        f"非同期サムネイル生成でエラー: {file_path}, エラー: {e}"
                    )
                    self.error_occurred.emit(file_path, str(e))

            # 生成完了
            self.mutex.lock()
            try:
                self._generating_files.clear()
            finally:
                self.mutex.unlock()

            self.generation_finished.emit()
            self.logger.info("非同期サムネイル生成が完了しました")

        except Exception as e:
            self.logger.error(f"非同期サムネイル生成に失敗しました: {e}")
            self.generation_finished.emit()

    def clear_cache(self) -> bool:
        """
        キャッシュをクリア

        Returns:
            クリア成功の場合True
        """
        try:
            import shutil

            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                ensure_directory_exists(self.cache_dir)
                self.logger.info("サムネイルキャッシュをクリアしました")
                return True
            return False

        except Exception as e:
            self.logger.error(f"サムネイルキャッシュのクリアに失敗しました: {e}")
            return False

    def get_cache_size(self) -> int:
        """
        キャッシュサイズを取得

        Returns:
            キャッシュファイル数
        """
        try:
            if not os.path.exists(self.cache_dir):
                return 0

            count = 0
            for _ in os.listdir(self.cache_dir):
                count += 1
            return count

        except Exception as e:
            self.logger.error(f"キャッシュサイズの取得に失敗しました: {e}")
            return 0

    def get_cache_size_bytes(self) -> int:
        """
        キャッシュサイズをバイト単位で取得

        Returns:
            キャッシュサイズ（バイト）
        """
        try:
            if not os.path.exists(self.cache_dir):
                return 0

            total_size = 0
            for dirpath, _, filenames in os.walk(self.cache_dir):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)

            return total_size

        except Exception as e:
            self.logger.error(f"キャッシュサイズ（バイト）の取得に失敗しました: {e}")
            return 0

    def is_generating(self) -> bool:
        """
        生成中かどうかを確認

        Returns:
            生成中の場合はTrue
        """
        self.mutex.lock()
        try:
            result = len(self._generating_files) > 0
        finally:
            self.mutex.unlock()
        return result

    def cancel_generation(self) -> None:
        """生成をキャンセル"""
        self.mutex.lock()
        try:
            self._generating_files.clear()
        finally:
            self.mutex.unlock()
        self.logger.info("サムネイル生成をキャンセルしました")

    def get_generating_files(self) -> List[str]:
        """
        生成中のファイルリストを取得

        Returns:
            生成中のファイルパスのリスト
        """
        self.mutex.lock()
        try:
            result = self._generating_files.copy()
        finally:
            self.mutex.unlock()
        return result

    def __del__(self):
        """デストラクタ"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
