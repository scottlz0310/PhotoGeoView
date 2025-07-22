"""
サムネイルグリッド表示機能を提供するモジュール
PhotoGeoView プロジェクト用のサムネイル表示機能
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QSlider,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont, QPainter, QColor, QContextMenuEvent, QMouseEvent, QAction

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.core.utils import format_file_size


class ThumbnailGrid(QWidget):
    """サムネイルグリッドウィジェット"""

    # シグナル定義
    image_selected = pyqtSignal(str)  # 画像選択時に発信
    image_double_clicked = pyqtSignal(str)  # 画像ダブルクリック時に発信
    thumbnail_clicked = pyqtSignal(str)  # サムネイルクリック時に発信
    thumbnail_double_clicked = pyqtSignal(str)  # サムネイルダブルクリック時に発信

    def __init__(self, parent=None):
        """
        ThumbnailGridの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # サムネイルデータ
        self._image_files: List[str] = []
        self._thumbnails: Dict[str, QPixmap] = {}
        self._selected_image: str = ""

        # 表示設定
        self._thumbnail_size: int = 120
        self._grid_spacing: int = 5
        self._columns: int = 4

        # UI初期化
        self._init_ui()
        self._init_connections()

        self.logger.debug("ThumbnailGridを初期化しました")

    def _init_ui(self) -> None:
        """UIの初期化"""
        # メインレイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ツールバー
        self._init_toolbar()
        layout.addLayout(self.toolbar_layout)

        # スクロールエリア
        self._init_scroll_area()
        layout.addWidget(self.scroll_area, 1)

        # コンテキストメニューを有効化
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def _init_toolbar(self) -> None:
        """ツールバーの初期化"""
        self.toolbar_layout = QHBoxLayout()

        # サムネイルサイズラベル
        self.size_label = QLabel("サイズ:")
        self.size_label.setMinimumWidth(40)

        # サムネイルサイズスライダー
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(60)
        self.size_slider.setMaximum(200)
        self.size_slider.setValue(self._thumbnail_size)
        self.size_slider.setToolTip("サムネイルサイズ")

        # サイズ値表示
        self.size_value_label = QLabel(f"{self._thumbnail_size}px")
        self.size_value_label.setMinimumWidth(50)

        # クリアボタン
        self.clear_button = QPushButton("クリア")
        self.clear_button.setToolTip("選択をクリア")
        self.clear_button.setMaximumWidth(60)

        # ツールバーに追加
        self.toolbar_layout.addWidget(self.size_label)
        self.toolbar_layout.addWidget(self.size_slider)
        self.toolbar_layout.addWidget(self.size_value_label)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.clear_button)

    def _init_scroll_area(self) -> None:
        """スクロールエリアの初期化"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # コンテナウィジェット
        self.container_widget = QWidget()
        self.scroll_area.setWidget(self.container_widget)

        # グリッドレイアウト
        self.grid_layout = QGridLayout(self.container_widget)
        self.grid_layout.setSpacing(self._grid_spacing)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

    def _init_connections(self) -> None:
        """シグナル・スロット接続の初期化"""
        # スライダー接続
        self.size_slider.valueChanged.connect(self._on_size_changed)
        self.logger.info(f"サムネイルスライダーを初期化: 初期値={self.size_slider.value()}")

        # ボタン接続
        self.clear_button.clicked.connect(self.clear_selection)

        # コンテキストメニュー接続
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_image_files(self, image_files: List[str]) -> None:
        """
        画像ファイルリストを設定

        Args:
            image_files: 画像ファイルパスのリスト
        """
        try:
            self.logger.info(f"画像ファイルリストを設定: {len(image_files)} ファイル")

            # 現在のリストをクリア
            self._clear_grid()

            # 新しいリストを設定
            self._image_files = image_files.copy()

            # グリッドを更新
            self._update_grid()

        except Exception as e:
            self.logger.error(f"画像ファイルリストの設定に失敗しました: {e}")

    def load_images(self, image_files: List[str]) -> None:
        """
        画像ファイルリストを読み込み（set_image_filesのエイリアス）

        Args:
            image_files: 画像ファイルパスのリスト
        """
        self.set_image_files(image_files)

    def add_thumbnail(self, file_path: str, pixmap: QPixmap) -> None:
        """
        サムネイルを追加

        Args:
            file_path: 画像ファイルパス
            pixmap: サムネイルのQPixmap
        """
        try:
            if file_path not in self._image_files:
                self.logger.warning(f"画像ファイルがリストにありません: {Path(file_path).name}")
                return

            # サムネイルを保存
            self._thumbnails[file_path] = pixmap
            self.logger.info(f"サムネイルを追加: {Path(file_path).name}, 辞書サイズ: {len(self._thumbnails)}")

            # 対応するサムネイルウィジェットを更新
            self._update_thumbnail_widget(file_path)

        except Exception as e:
            self.logger.error(
                f"サムネイルの追加に失敗しました: {file_path}, エラー: {e}"
            )

    def select_image(self, file_path: str) -> None:
        """
        画像を選択

        Args:
            file_path: 画像ファイルパス
        """
        try:
            if file_path not in self._image_files:
                return

            # 前の選択をクリア
            if self._selected_image:
                self._clear_selection_visual()

            # 新しい選択を設定
            self._selected_image = file_path
            self._set_selection_visual(file_path)

            # シグナルを発信
            self.image_selected.emit(file_path)

        except Exception as e:
            self.logger.error(f"画像の選択に失敗しました: {file_path}, エラー: {e}")

    def clear_selection(self) -> None:
        """選択をクリア"""
        try:
            if self._selected_image:
                self._clear_selection_visual()
                self._selected_image = ""

        except Exception as e:
            self.logger.error(f"選択のクリアに失敗しました: {e}")

    def _clear_grid(self) -> None:
        """グリッドをクリア"""
        try:
            # 既存のウィジェットを削除
            while self.grid_layout.count():
                child = self.grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # 選択状態のみクリア（サムネイルデータは保持）
            self._selected_image = ""
            self.logger.debug(f"グリッドをクリア: サムネイル辞書サイズ={len(self._thumbnails)} を保持")

        except Exception as e:
            self.logger.error(f"グリッドのクリアに失敗しました: {e}")

    def _update_grid(self) -> None:
        """グリッドを更新"""
        try:
            self.logger.info(f"[GRID] _update_grid開始: サムネイル辞書サイズ={len(self._thumbnails)}")

            # グリッドをクリア
            self._clear_grid()

            self.logger.info(f"[GRID] _clear_grid後: サムネイル辞書サイズ={len(self._thumbnails)}")

            if not self._image_files:
                return

            # 列数を計算
            self._calculate_columns()

            # サムネイルウィジェットを作成
            for i, file_path in enumerate(self._image_files):
                row = i // self._columns
                col = i % self._columns

                thumbnail_widget = self._create_thumbnail_widget(file_path)
                self.grid_layout.addWidget(thumbnail_widget, row, col)

            self.logger.debug(
                f"グリッドを更新しました: {len(self._image_files)} ファイル"
            )

        except Exception as e:
            self.logger.error(f"グリッドの更新に失敗しました: {e}")

    def _calculate_columns(self) -> None:
        """列数を計算"""
        try:
            # スクロールエリアの幅を取得
            available_width = self.scroll_area.viewport().width() - 20  # マージンを引く

            if available_width <= 0:
                self._columns = 4  # デフォルト値
                return

            # サムネイルサイズとスペースを考慮して列数を計算
            item_width = self._thumbnail_size + self._grid_spacing
            self._columns = max(1, available_width // item_width)

        except Exception as e:
            self.logger.error(f"列数の計算に失敗しました: {e}")
            self._columns = 4  # デフォルト値

    def _create_thumbnail_widget(self, file_path: str) -> QWidget:
        """
        サムネイルウィジェットを作成

        Args:
            file_path: 画像ファイルパス

        Returns:
            サムネイルウィジェット
        """
        try:
            # メインウィジェット
            widget = QFrame()
            widget.setFrameStyle(QFrame.Shape.StyledPanel)
            widget.setFixedSize(self._thumbnail_size + 10, self._thumbnail_size + 40)
            widget.setStyleSheet(
                """
                QFrame {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    background-color: white;
                }
                QFrame:hover {
                    border: 2px solid #0078d4;
                }
            """
            )

            # レイアウト
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)

            # サムネイルラベル
            thumbnail_label = QLabel()
            thumbnail_label.setFixedSize(self._thumbnail_size, self._thumbnail_size)
            thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumbnail_label.setStyleSheet("border: 1px solid #eee;")

            # サムネイル画像を設定
            if file_path in self._thumbnails:
                self.logger.debug(f"[DEBUG] サムネイル再利用: {Path(file_path).name}, サイズ: {self._thumbnail_size}")
                pixmap = self._thumbnails[file_path]
                # 高品質スケーリングを使用
                scaled_pixmap = self._create_high_quality_thumbnail(
                    pixmap, self._thumbnail_size
                )
                thumbnail_label.setPixmap(scaled_pixmap)
            else:
                self.logger.debug(f"[DEBUG] サムネイル未キャッシュ: {Path(file_path).name}")
                # プレースホルダー
                thumbnail_label.setText("読み込み中...")
                thumbnail_label.setStyleSheet("border: 1px solid #eee; color: #666;")

            # ファイル名ラベル
            file_name = Path(file_path).name
            name_label = QLabel(file_name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setWordWrap(True)
            name_label.setMaximumHeight(30)
            name_label.setStyleSheet("font-size: 10px; color: #333;")

            # レイアウトに追加
            layout.addWidget(thumbnail_label)
            layout.addWidget(name_label)

            # データを設定
            widget.setProperty("file_path", file_path)
            widget.setProperty("thumbnail_label", thumbnail_label)

            # マウスイベントを有効化
            widget.mousePressEvent = (
                lambda event, fp=file_path: self._on_thumbnail_clicked(event, fp)
            )
            widget.mouseDoubleClickEvent = (
                lambda event, fp=file_path: self._on_thumbnail_double_clicked(event, fp)
            )

            return widget

        except Exception as e:
            self.logger.error(
                f"サムネイルウィジェットの作成に失敗しました: {file_path}, エラー: {e}"
            )
            return QLabel("エラー")

    def _update_thumbnail_widget(self, file_path: str) -> None:
        """
        サムネイルウィジェットを更新

        Args:
            file_path: 画像ファイルパス
        """
        try:
            # 対応するウィジェットを探す
            for i in range(self.grid_layout.count()):
                item = self.grid_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if widget.property("file_path") == file_path:
                        # サムネイルラベルを取得
                        thumbnail_label = widget.property("thumbnail_label")
                        if thumbnail_label and file_path in self._thumbnails:
                            pixmap = self._thumbnails[file_path]
                            # 高品質スケーリングを使用
                            scaled_pixmap = self._create_high_quality_thumbnail(
                                pixmap, self._thumbnail_size
                            )
                            thumbnail_label.setPixmap(scaled_pixmap)
                        break

        except Exception as e:
            self.logger.error(
                f"サムネイルウィジェットの更新に失敗しました: {file_path}, エラー: {e}"
            )

    def _set_selection_visual(self, file_path: str) -> None:
        """
        選択の視覚的表示を設定

        Args:
            file_path: 画像ファイルパス
        """
        try:
            # 対応するウィジェットを探す
            for i in range(self.grid_layout.count()):
                item = self.grid_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if widget.property("file_path") == file_path:
                        widget.setStyleSheet(
                            """
                            QFrame {
                                border: 2px solid #0078d4;
                                border-radius: 5px;
                                background-color: #f0f8ff;
                            }
                        """
                        )
                        break

        except Exception as e:
            self.logger.error(
                f"選択の視覚的表示の設定に失敗しました: {file_path}, エラー: {e}"
            )

    def _clear_selection_visual(self) -> None:
        """選択の視覚的表示をクリア"""
        try:
            # 対応するウィジェットを探す
            for i in range(self.grid_layout.count()):
                item = self.grid_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if widget.property("file_path") == self._selected_image:
                        widget.setStyleSheet(
                            """
                            QFrame {
                                border: 1px solid #ccc;
                                border-radius: 5px;
                                background-color: white;
                            }
                            QFrame:hover {
                                border: 2px solid #0078d4;
                            }
                        """
                        )
                        break

        except Exception as e:
            self.logger.error(f"選択の視覚的表示のクリアに失敗しました: {e}")

    def _on_thumbnail_clicked(self, event, file_path: str) -> None:
        """
        サムネイルクリック時の処理

        Args:
            event: マウスイベント
            file_path: 画像ファイルパス
        """
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.select_image(file_path)
                self.thumbnail_clicked.emit(file_path)

        except Exception as e:
            self.logger.error(
                f"サムネイルクリックの処理に失敗しました: {file_path}, エラー: {e}"
            )

    def _on_thumbnail_double_clicked(self, event, file_path: str) -> None:
        """
        サムネイルダブルクリック時の処理

        Args:
            event: マウスイベント
            file_path: 画像ファイルパス
        """
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.image_double_clicked.emit(file_path)
                self.thumbnail_double_clicked.emit(file_path)

        except Exception as e:
            self.logger.error(
                f"サムネイルダブルクリックの処理に失敗しました: {file_path}, エラー: {e}"
            )

    def _on_size_changed(self, value: int) -> None:
        """
        サイズ変更時の処理

        Args:
            value: 新しいサイズ
        """
        self.logger.info(f"[SLIDER] スライダーイベント発生! value={value}")
        try:
            self.logger.info(f"[DEBUG] サイズ変更: {self._thumbnail_size} -> {value}")
            self._thumbnail_size = value
            self.size_value_label.setText(f"{value}px")

            self.logger.info(f"[DEBUG] 既存サムネイル数: {len(self._thumbnails)}")

            # グリッドを再構築
            self._update_grid()

            # 設定を保存
            self.settings.set("ui.panels.thumbnail_size", value)

            self.logger.debug(f"[DEBUG] サイズ変更完了")

        except Exception as e:
            self.logger.error(f"サイズ変更の処理に失敗しました: {e}")

    def _show_context_menu(self, position) -> None:
        """
        コンテキストメニューを表示

        Args:
            position: メニュー表示位置
        """
        try:
            from PyQt6.QtGui import QAction

            menu = QMenu(self)

            # サムネイルサイズ変更サブメニュー
            size_menu = QMenu("サムネイルサイズ", menu)
            menu.addMenu(size_menu)

            # サイズオプション
            size_options = [60, 80, 100, 120, 140, 160, 180, 200]
            for size in size_options:
                action = QAction(f"{size}px", self)
                action.setCheckable(True)
                action.setChecked(size == self._thumbnail_size)
                action.triggered.connect(
                    lambda checked, s=size: self._set_thumbnail_size(s)
                )
                size_menu.addAction(action)

            menu.addSeparator()

            # その他のオプション
            refresh_action = QAction("更新", self)
            refresh_action.triggered.connect(self._update_grid)
            menu.addAction(refresh_action)

            clear_action = QAction("選択をクリア", self)
            clear_action.triggered.connect(self.clear_selection)
            menu.addAction(clear_action)

            # メニューを表示
            menu.exec(self.mapToGlobal(position))

        except Exception as e:
            self.logger.error(f"コンテキストメニューの表示に失敗しました: {e}")

    def _set_thumbnail_size(self, size: int) -> None:
        """
        サムネイルサイズを設定

        Args:
            size: 新しいサイズ
        """
        try:
            self._thumbnail_size = size
            self.size_slider.setValue(size)
            self.size_value_label.setText(f"{size}px")

            # グリッドを再構築
            self._update_grid()

            # 設定を保存
            self.settings.set("ui.panels.thumbnail_size", size)

        except Exception as e:
            self.logger.error(f"サムネイルサイズの設定に失敗しました: {e}")

    def resizeEvent(self, event) -> None:
        """リサイズイベント"""
        super().resizeEvent(event)

        # 列数を再計算してグリッドを更新
        QTimer.singleShot(100, self._update_grid)

    def get_selected_image(self) -> str:
        """
        選択された画像を取得

        Returns:
            選択された画像のファイルパス
        """
        return self._selected_image

    def get_thumbnail_size(self) -> int:
        """
        サムネイルサイズを取得

        Returns:
            サムネイルサイズ
        """
        return self._thumbnail_size

    def get_image_count(self) -> int:
        """
        画像数を取得

        Returns:
            画像数
        """
        return len(self._image_files)

    def _create_high_quality_thumbnail(self, pixmap: QPixmap, size: int) -> QPixmap:
        """
        高品質サムネイル生成（改良版）

        Args:
            pixmap: 元のQPixmap
            size: サムネイルサイズ（正方形）

        Returns:
            高品質にスケーリングされたQPixmap
        """
        if pixmap.isNull():
            return pixmap

        # 元のサイズを取得
        orig_width = pixmap.width()
        orig_height = pixmap.height()

        # すでに適切なサイズの場合は直接返す
        if orig_width <= size and orig_height <= size:
            return pixmap

        # アスペクト比を保持してスケーリング
        scaled_pixmap = pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # 正方形の背景を作成（透明）
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)

        # 中央配置で描画
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # 中央配置の計算
        x = (size - scaled_pixmap.width()) // 2
        y = (size - scaled_pixmap.height()) // 2

        # 高品質描画
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

        return result
