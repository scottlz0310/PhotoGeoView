"""
アプリケーション制御ロジックを提供するモジュール
PhotoGeoView プロジェクト用のメインコントローラー
"""

import os
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.core.utils import is_image_file, get_supported_image_extensions
from src.modules.image_loader import ImageLoader
from src.modules.exif_parser import ExifParser
from src.modules.thumbnail_generator import ThumbnailGenerator
from src.modules.image_viewer import ImageViewer
from src.modules.map_viewer import MapViewer


class PhotoGeoViewController(QObject):
    """PhotoGeoViewアプリケーションのメインコントローラー"""

    # シグナル定義
    current_directory_changed = pyqtSignal(str)  # 現在のディレクトリ変更時に発信
    images_loaded = pyqtSignal(list)  # 画像リスト読み込み完了時に発信
    image_list_updated = pyqtSignal(list)  # 画像リスト更新時に発信
    image_selected = pyqtSignal(dict)  # 画像選択時に発信（画像情報辞書）
    selected_image_changed = pyqtSignal(str)  # 選択画像変更時に発信
    thumbnail_loaded = pyqtSignal(str, object)  # サムネイル読み込み完了時に発信
    image_loaded = pyqtSignal(str, object)  # 画像読み込み完了時に発信
    exif_parsed = pyqtSignal(str, dict)  # EXIFデータ解析完了時に発信
    exif_data_loaded = pyqtSignal(str, dict)  # EXIFデータ読み込み完了時に発信
    gps_coordinates_found = pyqtSignal(str, tuple)  # GPS座標発見時に発信
    map_marker_added = pyqtSignal(str, tuple)  # 地図マーカー追加時に発信
    error_occurred = pyqtSignal(str)  # エラー発生時に発信
    loading_progress = pyqtSignal(int)  # 読み込み進捗時に発信
    loading_finished = pyqtSignal()  # 読み込み完了時に発信

    def __init__(self):
        """PhotoGeoViewControllerの初期化"""
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.info("controller.py 実行確認")
        self.settings = get_settings()
        self.mutex = QMutex()

        # 現在の状態
        self._current_directory: str = ""
        self._image_files: List[str] = []
        self._selected_image: str = ""
        self._image_data: Dict[str, Any] = {}
        self._exif_data: Dict[str, Dict[str, Any]] = {}
        self._gps_coordinates: Dict[str, Tuple[float, float]] = {}

        # モジュールの初期化
        self._init_modules()
        self._init_connections()

        self.logger.info("PhotoGeoViewControllerを初期化しました")

    def _init_modules(self) -> None:
        """モジュールの初期化"""
        try:
            # 画像読み込みモジュール
            self.image_loader = ImageLoader()

            # EXIF解析モジュール
            self.exif_parser = ExifParser()

            # サムネイル生成モジュール
            self.thumbnail_generator = ThumbnailGenerator()

            # 画像表示モジュール
            self.image_viewer = ImageViewer()

            # 地図表示モジュール
            self.map_viewer = MapViewer()

            self.logger.debug("すべてのモジュールを初期化しました")

        except Exception as e:
            self.logger.error(f"モジュールの初期化に失敗しました: {e}")
            raise

    def _init_connections(self) -> None:
        """シグナル・スロット接続の初期化"""
        try:
            # 画像読み込みモジュールの接続
            self.image_loader.image_loaded.connect(self._on_image_loaded)
            self.image_loader.thumbnail_loaded.connect(self._on_thumbnail_loaded)
            self.image_loader.loading_progress.connect(self.loading_progress)
            self.image_loader.loading_finished.connect(self.loading_finished)
            self.image_loader.error_occurred.connect(self.error_occurred)

            # サムネイル生成モジュールの接続
            self.thumbnail_generator.thumbnail_generated.connect(
                self._on_thumbnail_generated
            )
            self.thumbnail_generator.generation_progress.connect(self.loading_progress)
            self.thumbnail_generator.generation_finished.connect(self.loading_finished)
            self.thumbnail_generator.error_occurred.connect(self.error_occurred)

            # 地図表示モジュールの接続
            self.map_viewer.marker_clicked.connect(self._on_marker_clicked)

            self.logger.debug("シグナル・スロット接続を初期化しました")

        except Exception as e:
            self.logger.error(f"シグナル・スロット接続の初期化に失敗しました: {e}")

    def load_directory(self, directory_path: str) -> bool:
        self.logger.info(f"load_directory呼び出し: {directory_path}")
        """
        ディレクトリを読み込み

        Args:
            directory_path: ディレクトリパス

        Returns:
            読み込み成功の場合True
        """
        try:
            if not os.path.exists(directory_path):
                self.logger.error(f"ディレクトリが存在しません: {directory_path}")
                return False

            if not os.path.isdir(directory_path):
                self.logger.error(f"パスがディレクトリではありません: {directory_path}")
                return False

            self.logger.info(f"ディレクトリを読み込み開始: {directory_path}")

            # 現在のディレクトリを更新
            self._current_directory = directory_path

            # 画像ファイルを検索
            image_files = self._find_image_files(directory_path)
            self._image_files = image_files

            # 状態をリセット
            self._selected_image = ""
            self._image_data.clear()
            self._exif_data.clear()
            self._gps_coordinates.clear()

            # 地図のマーカーをクリア
            self.map_viewer.clear_markers()

            # シグナルを発信
            self.current_directory_changed.emit(directory_path)
            self.images_loaded.emit(image_files)
            self.image_list_updated.emit(image_files)

            # サムネイルを生成
            if image_files:
                self._generate_thumbnails(image_files)

            self.logger.info(
                f"ディレクトリの読み込みが完了しました: {len(image_files)} ファイル"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"ディレクトリの読み込みに失敗しました: {directory_path}, エラー: {e}"
            )
            self.error_occurred.emit("ディレクトリ読み込みエラー", str(e))
            return False

    def _find_image_files(self, directory_path: str) -> List[str]:
        self.logger.info(f"_find_image_files呼び出し: {directory_path}")
        """
        ディレクトリ内の画像ファイルを検索

        Args:
            directory_path: ディレクトリパス

        Returns:
            画像ファイルパスのリスト
        """
        try:
            image_files = []

            for ext in get_supported_image_extensions():
                # 大文字小文字両方で検索
                pattern_lower = f"*{ext}"
                pattern_upper = f"*{ext.upper()}"

                for pattern in [pattern_lower, pattern_upper]:
                    for file_path in Path(directory_path).glob(pattern):
                        if file_path.is_file() and is_image_file(str(file_path)):
                            image_files.append(str(file_path))

            # 重複を除去してソート
            image_files = sorted(list(set(image_files)))

            self.logger.info(
                f"画像ファイルを {len(image_files)} 個見つけました: {image_files}"
            )
            return image_files

        except Exception as e:
            self.logger.error(f"画像ファイルの検索に失敗しました: {e}")
            return []

    def _generate_thumbnails(self, image_files: List[str]) -> None:
        self.logger.info(f"_generate_thumbnails呼び出し: {len(image_files)}ファイル")
        """
        サムネイルを生成

        Args:
            image_files: 画像ファイルパスのリスト
        """
        try:
            # 設定からサムネイルサイズを取得
            thumbnail_size = self.settings.get("ui.panels.thumbnail_size", 120)
            size = (thumbnail_size, thumbnail_size)

            self.logger.info(f"サムネイル生成を開始: {len(image_files)} ファイル")
            self.thumbnail_generator.generate_thumbnails_async(image_files, size)

        except Exception as e:
            self.logger.error(f"サムネイル生成の開始に失敗しました: {e}")

    def select_image(self, file_path: str) -> bool:
        """
        画像を選択

        Args:
            file_path: 画像ファイルパス

        Returns:
            選択成功の場合True
        """
        try:
            if file_path not in self._image_files:
                self.logger.warning(f"画像ファイルがリストにありません: {file_path}")
                return False

            self.logger.info(f"画像を選択: {file_path}")

            # 選択画像を更新
            self._selected_image = file_path
            self.selected_image_changed.emit(file_path)

            # 画像を読み込み
            self._load_selected_image(file_path)

            # EXIF情報を解析
            self._parse_exif_data(file_path)

            # 画像情報を取得して送信
            image_info = self.get_image_info(file_path)
            self.image_selected.emit(image_info)

            return True

        except Exception as e:
            self.logger.error(f"画像の選択に失敗しました: {file_path}, エラー: {e}")
            return False

    def _load_selected_image(self, file_path: str) -> None:
        """
        選択された画像を読み込み

        Args:
            file_path: 画像ファイルパス
        """
        try:
            # デバッグ用に画像読み込みの詳細ログを追加
            self.logger.info(f"[DEBUG] 画像読み込み開始: {file_path}")

            # 現在の画像のインデックスを取得
            try:
                current_index = self._image_files.index(file_path)
            except ValueError:
                self.logger.warning(f"画像ファイルがリストにありません: {file_path}")
                current_index = 0

            # 画像リストを設定してナビゲーションを有効にする
            self.logger.info(f"[DEBUG] 画像リスト設定: {len(self._image_files)}枚, index={current_index}")
            self.image_viewer.set_image_list(self._image_files, current_index)

            self.logger.info(f"[DEBUG] image_viewer読み込み完了: {file_path}")

            # 互換性のため、image_loaderでも読み込む
            pixmap = self.image_loader.load_image(file_path)
            if pixmap:
                self.logger.info(f"[DEBUG] QPixmap読み込み完了: {file_path}")
                self._image_data[file_path] = pixmap
                self.image_loaded.emit(file_path, pixmap)
                self.logger.info(f"[DEBUG] 画像読み込み処理完了: {file_path}")
            else:
                self.logger.error(f"[DEBUG] QPixmap読み込み失敗: {file_path}")

        except Exception as e:
            self.logger.error(
                f"選択画像の読み込みに失敗しました: {file_path}, エラー: {e}"
            )
            import traceback
            self.logger.error(f"スタックトレース: {traceback.format_exc()}")

    def _parse_exif_data(self, file_path: str) -> None:
        """
        EXIF情報を解析

        Args:
            file_path: 画像ファイルパス
        """
        try:
            # EXIF情報を解析
            exif_data = self.exif_parser.parse_exif(file_path)
            self._exif_data[file_path] = exif_data

            # EXIFデータ読み込み完了を通知
            self.exif_parsed.emit(file_path, exif_data)
            self.exif_data_loaded.emit(file_path, exif_data)

            # GPS座標をチェック
            if "gps" in exif_data:
                gps = exif_data["gps"]
                if "latitude" in gps and "longitude" in gps:
                    lat, lon = gps["latitude"], gps["longitude"]

                    # NullIsland (0.0, 0.0) をGPS情報なしとして扱う
                    if lat == 0.0 and lon == 0.0:
                        self.logger.info(f"GPS座標がNullIsland (0.0, 0.0) です: {file_path}")
                        self._notify_map_no_gps(file_path)
                    else:
                        coordinates = (lat, lon)
                        self._gps_coordinates[file_path] = coordinates

                        # 地図にマーカーを追加
                        self._add_map_marker(file_path, coordinates, exif_data)

                        # GPS座標発見を通知
                        self.gps_coordinates_found.emit(file_path, coordinates)
                else:
                    # GPS情報はあるが座標が不完全な場合
                    self.logger.info(f"GPS情報が不完全です: {file_path}")
                    self._notify_map_no_gps(file_path)
            else:
                # GPS情報がない場合
                self.logger.info(f"GPS情報がありません: {file_path}")
                self._notify_map_no_gps(file_path)

        except Exception as e:
            self.logger.error(f"EXIF情報の解析に失敗しました: {file_path}, エラー: {e}")
            # EXIF解析エラーの場合も GPS情報なし として処理
            self._notify_map_no_gps(file_path)

    def _add_map_marker(
        self,
        file_path: str,
        coordinates: Tuple[float, float],
        exif_data: Dict[str, Any],
    ) -> None:
        """
        地図にマーカーを追加

        Args:
            file_path: 画像ファイルパス
            coordinates: GPS座標
            exif_data: EXIF情報
        """
        try:
            # ファイル名を取得
            file_name = Path(file_path).name

            # タイトルと説明を作成
            title = file_name

            description_parts = []
            if "datetime_original" in exif_data:
                description_parts.append(f"撮影日時: {exif_data['datetime_original']}")
            if "make" in exif_data and "model" in exif_data:
                description_parts.append(
                    f"カメラ: {exif_data['make']} {exif_data['model']}"
                )

            description = (
                "<br>".join(description_parts) if description_parts else "GPS情報あり"
            )

            # マーカーを追加
            self.map_viewer.add_marker(file_path, coordinates, title, description)
            self.map_marker_added.emit(file_path, coordinates)

        except Exception as e:
            self.logger.error(
                f"地図マーカーの追加に失敗しました: {file_path}, エラー: {e}"
            )

    def _notify_map_no_gps(self, file_path: str) -> None:
        """
        GPS情報がない画像を地図ビューアーに通知

        Args:
            file_path: 画像ファイルパス
        """
        try:
            # MapViewer の set_current_photo をGPS座標なしで呼び出し
            self.map_viewer.set_current_photo(file_path)
            self.logger.debug(f"GPS情報なし画像を地図に通知: {file_path}")
        except Exception as e:
            self.logger.error(f"GPS情報なし画像の地図通知に失敗: {file_path}, エラー: {e}")

    def _on_image_loaded(self, file_path: str, pixmap) -> None:
        """
        画像読み込み完了時の処理

        Args:
            file_path: 画像ファイルパス
            pixmap: 画像のQPixmap
        """
        self.logger.debug(f"画像読み込み完了: {file_path}")

    def _on_thumbnail_loaded(self, file_path: str, pixmap) -> None:
        """
        サムネイル読み込み完了時の処理

        Args:
            file_path: 画像ファイルパス
            pixmap: サムネイルのQPixmap
        """
        self.logger.debug(f"サムネイル読み込み完了: {file_path}")

    def _on_thumbnail_generated(self, file_path: str, pixmap) -> None:
        """
        サムネイル生成完了時の処理

        Args:
            file_path: 画像ファイルパス
            pixmap: サムネイルのQPixmap
        """
        self.logger.debug(f"サムネイル生成完了: {file_path}")
        self.thumbnail_loaded.emit(file_path, pixmap)

    def _on_marker_clicked(self, marker_id: str) -> None:
        """
        マーカークリック時の処理

        Args:
            marker_id: マーカーID（ファイルパス）
        """
        self.logger.debug(f"マーカーがクリックされました: {marker_id}")

        # 対応する画像を選択
        if marker_id in self._image_files:
            self.select_image(marker_id)

    def get_current_directory(self) -> str:
        """
        現在のディレクトリを取得

        Returns:
            現在のディレクトリパス
        """
        return self._current_directory

    def get_image_files(self) -> List[str]:
        """
        画像ファイルリストを取得

        Returns:
            画像ファイルパスのリスト
        """
        return self._image_files.copy()

    def get_selected_image(self) -> str:
        """
        選択された画像を取得

        Returns:
            選択された画像のファイルパス
        """
        return self._selected_image

    def get_exif_data(self, file_path: str) -> Dict[str, Any]:
        """
        EXIF情報を取得

        Args:
            file_path: 画像ファイルパス

        Returns:
            EXIF情報辞書
        """
        return self._exif_data.get(file_path, {})

    def get_gps_coordinates(self, file_path: str) -> Optional[Tuple[float, float]]:
        """
        GPS座標を取得

        Args:
            file_path: 画像ファイルパス

        Returns:
            GPS座標 (緯度, 経度)、GPS情報がない場合はNone
        """
        return self._gps_coordinates.get(file_path)

    def get_all_gps_coordinates(self) -> Dict[str, Tuple[float, float]]:
        """
        すべてのGPS座標を取得

        Returns:
            GPS座標辞書 {ファイルパス: (緯度, 経度)}
        """
        return self._gps_coordinates.copy()

    def navigate_to_parent_directory(self) -> bool:
        """
        親ディレクトリに移動

        Returns:
            移動成功の場合True
        """
        try:
            if not self._current_directory:
                return False

            parent_dir = str(Path(self._current_directory).parent)

            # ルートディレクトリでない場合のみ移動
            if parent_dir != self._current_directory:
                return self.load_directory(parent_dir)

            return False

        except Exception as e:
            self.logger.error(f"親ディレクトリへの移動に失敗しました: {e}")
            return False

    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        画像情報を取得

        Args:
            file_path: 画像ファイルパス

        Returns:
            画像情報辞書
        """
        try:
            # 基本情報
            info = {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "file_size": (
                    os.path.getsize(file_path) if os.path.exists(file_path) else 0
                ),
            }

            # EXIF情報を追加
            exif_data = self.get_exif_data(file_path)
            if exif_data:
                info["exif"] = exif_data

            # GPS座標を追加
            gps_coords = self.get_gps_coordinates(file_path)
            if gps_coords:
                info["gps_coordinates"] = gps_coords

            return info

        except Exception as e:
            self.logger.error(f"画像情報の取得に失敗しました: {file_path}, エラー: {e}")
            return {}

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        try:
            self.image_loader.clear_cache()
            self.thumbnail_generator.clear_cache()
            self.logger.info("キャッシュをクリアしました")

        except Exception as e:
            self.logger.error(f"キャッシュのクリアに失敗しました: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        キャッシュ情報を取得

        Returns:
            キャッシュ情報辞書
        """
        try:
            return {
                "image_cache_size": self.image_loader.get_cache_size(),
                "thumbnail_cache_size": self.thumbnail_generator.get_cache_size(),
                "thumbnail_cache_bytes": self.thumbnail_generator.get_cache_size_bytes(),
            }

        except Exception as e:
            self.logger.error(f"キャッシュ情報の取得に失敗しました: {e}")
            return {}
