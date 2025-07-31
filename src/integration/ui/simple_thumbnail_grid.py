"""
Simple Thumbnail Grid - シンプルサムネイルグリッド

複雑な機能を排除し、基本的なサムネイル表示に特化したコンポーネント。
テストで動作確認済みの機能のみを実装。

Author: Kiro AI Integration System
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..state_manager import StateManager


class SimpleThumbnailItem(QLabel):
    """シンプルなサムネイルアイテム"""

    clicked = pyqtSignal(Path)

    def __init__(self, image_path: Path, thumbnail_size: int = 150):
        super().__init__()

        self.image_path = image_path
        self.thumbnail_size = thumbnail_size

        # UI設定
        self.setFixedSize(thumbnail_size + 20, thumbnail_size + 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 4px;
                background-color: white;
            }
            QLabel:hover {
                border-color: #007acc;
            }
        """)

        # ツールチップにファイル名を設定
        self.setToolTip(image_path.name)

        # プレースホルダーを表示
        self._show_placeholder()

        # 実際の画像を読み込み
        self._load_image()

    def _show_placeholder(self):
        """プレースホルダーを表示"""
        placeholder = QPixmap(self.thumbnail_size, self.thumbnail_size)
        placeholder.fill(Qt.GlobalColor.lightGray)
        self.setPixmap(placeholder)
        self.setText("Loading...")

    def _load_image(self):
        """画像を読み込み"""
        try:
            pixmap = QPixmap(str(self.image_path))

            if not pixmap.isNull():
                # サムネイルサイズにスケール
                scaled_pixmap = pixmap.scaled(
                    self.thumbnail_size, self.thumbnail_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
                self.setText("")  # テキストをクリア
            else:
                self._show_error()

        except Exception as e:
            self._show_error()

    def _show_error(self):
        """エラー表示"""
        error_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        error_pixmap.fill(Qt.GlobalColor.red)
        self.setPixmap(error_pixmap)
        self.setText("Error")

    def mousePressEvent(self, event):
        """マウスクリック処理"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)


class SimpleThumbnailGrid(QWidget):
    """
    シンプルなサムネイルグリッド

    複雑な機能を排除し、基本的なサムネイル表示のみを実装。
    テストで動作確認済みの機能のみを使用。
    """

    # シグナル
    image_selected = pyqtSignal(Path)

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
    ):
        super().__init__()

        # コアシステム
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # グリッド設定
        try:
            self.thumbnail_size = self.state_manager.get_state_value("thumbnail_size", 150)
        except:
            self.thumbnail_size = 150
        self.columns = 4
        self.spacing = 10

        # データ保存
        self.image_list: List[Path] = []
        self.thumbnail_items: Dict[Path, SimpleThumbnailItem] = {}

        # UI初期化
        self._setup_ui()

        self.logger_system.log_ai_operation(
            AIComponent.CURSOR,
            "simple_thumbnail_grid_init",
            "Simple thumbnail grid initialized",
        )

    def _setup_ui(self):
        """UI設定"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # コントロール
            self.controls_widget = self._create_controls()
            lout.addWidget(self.controls_widget)

            # スクロールエリア
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # グリッドウィジェット
            self.grid_widget = QWidget()
            self.grid_layout = QGridLayout(self.grid_widget)
            self.grid_layout.setSpacing(self.spacing)
            self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            self.scroll_area.setWidget(self.grid_widget)
            layout.addWidget(self.scroll_area)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "setup_ui"}, AIComponent.CURSOR
            )

    def _create_controls(self) -> QWidget:
        """コントロールウィジェット作成"""
        controls = QWidget()
        layout = QHBoxLayout(controls)

        # サムネイルサイズ制御
        size_label = QLabel("Size:")
        layout.addWidget(size_label)

        size_slider = QSlider(Qt.Orientation.Horizontal)
        size_slider.setRange(50, 300)
        size_slider.setValue(self.thumbnail_size)
        size_slider.valueChanged.connect(self._on_size_changed)
        layout.addWidget(size_slider)

        size_spinbox = QSpinBox()
        size_spinbox.setRange(50, 300)
        size_spinbox.setValue(self.thumbnail_size)
        size_spinbox.valueChanged.connect(self._on_size_changed)
        layout.addWidget(size_spinbox)

        # スライダーとスピンボックスを連携
        size_slider.valueChanged.connect(size_spinbox.setValue)
        size_spinbox.valueChanged.connect(size_slider.setValue)

        layout.addStretch()

        # ステータス表示
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        return controls

    def _on_size_changed(self, size: int):
        """サムネイルサイズ変更"""
        try:
            self.thumbnail_size = size
            self.state_manager.update_state(thumbnail_size=size)

            # 既存のサムネイルを更新
            self._update_thumbnail_sizes()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_size_changed",
                f"Thumbnail size changed to {size}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "size_change", "size": size}, AIComponent.CURSOR
            )

    def _update_thumbnail_sizes(self):
        """既存のサムネイルサイズを更新"""
        try:
            for thumbnail_item in self.thumbnail_items.values():
                thumbnail_item.thumbnail_size = self.thumbnail_size
                thumbnail_item.setFixedSize(self.thumbnail_size + 20, self.thumbnail_size + 40)
                thumbnail_item._load_image()  # 画像を再読み込み

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_thumbnail_sizes"}, AIComponent.CURSOR
            )

    def set_image_list(self, image_list: List[Path]):
        """画像リストを設定"""
        try:
            self.image_list = image_list

            # 既存のサムネイルをクリア
            self._clear_thumbnails()

            # 新しいサムネイルを作成
            self._create_thumbnails()

            self.status_label.setText(f"{len(image_list)} images")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "image_list_set",
                f"Image list set with {len(image_list)} images",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "set_image_list", "count": len(image_list)}, AIComponent.CURSOR
            )

    def update_image_list(self, image_list: List[Path]):
        """画像リストを更新（動的更新用）"""
        self.set_image_list(image_list)

    def _clear_thumbnails(self):
        """既存のサムネイルをクリア"""
        try:
            for thumbnail_item in self.thumbnail_items.values():
                self.grid_layout.removeWidget(thumbnail_item)
                thumbnail_item.deleteLater()

            self.thumbnail_items.clear()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "clear_thumbnails"}, AIComponent.CURSOR
            )

    def _create_thumbnails(self):
        """サムネイルを作成"""
        try:
            row = 0
            col = 0

            for image_path in self.image_list:
                # サムネイルアイテムを作成
                thumbnail_item = SimpleThumbnailItem(image_path, self.thumbnail_size)

                # シグナル接続
                thumbnail_item.clicked.connect(self._on_thumbnail_clicked)

                # レイアウトに追加
                self.grid_layout.addWidget(thumbnail_item, row, col)

                # 参照を保存
                self.thumbnail_items[image_path] = thumbnail_item

                # グリッド位置を更新
                col += 1
                if col >= self.columns:
                    col = 0
                    row += 1

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "create_thumbnails", "count": len(self.image_list)}, AIComponent.CURSOR
            )

    def _on_thumbnail_clicked(self, image_path: Path):
        """サムネイルクリック処理"""
        try:
            self.image_selected.emit(image_path)
            self.status_label.setText(f"Selected: {image_path.name}")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_clicked",
                f"Thumbnail clicked: {image_path.name}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "thumbnail_click", "image": str(image_path)}, AIComponent.CURSOR
            )

    def show_loading_state(self, message: str):
        """ローディング状態を表示"""
        try:
            self.status_label.setText(f"🔄 {message}")
        except Exception as e:
            pass

    def show_error_state(self, error_message: str):
        """エラー状態を表示"""
        try:
            self.status_label.setText(f"❌ {error_message}")
        except Exception as e:
            pass

    def show_empty_state(self):
        """空状態を表示"""
        try:
            self.status_label.setText("No images found")
            self._clear_thumbnails()
        except Exception as e:
            pass

    def clear_thumbnails_safely(self):
        """安全にサムネイルをクリア（互換性のため）"""
        self._clear_thumbnails()
