"""
Simple Thumbnail Grid - シンプルサムネイルグリッド

複雑な機能を排除し、基本的なサムネイル表示に特化したコンポーネント。
テストで動作確認済みの機能のみを実装。

Author: Kiro AI Integration System
"""

from pathlib import Path
from typing import Dict, List

from PyQt6.QtCore import Qt, pyqtSignal
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

        # 実際の画像を読み込み（初期読み込みは即座に実行）
        self._load_image_immediate()

    def _show_placeholder(self):
        """プレースホルダーを表示"""
        placeholder = QPixmap(self.thumbnail_size, self.thumbnail_size)
        placeholder.fill(Qt.GlobalColor.lightGray)
        self.setPixmap(placeholder)
        self.setText("Loading...")

    def _load_image(self):
        """画像を読み込み（最適化版）"""
        try:
            # 既存の読み込みタイマーをキャンセル
            if hasattr(self, '_load_timer'):
                self._load_timer.stop()

            # 遅延読み込みタイマーを設定（UI応答性向上のため）
            from PyQt6.QtCore import QTimer
            self._load_timer = QTimer()
            self._load_timer.setSingleShot(True)
            self._load_timer.timeout.connect(self._do_load_image)
            self._load_timer.start(50)  # 50ms遅延

        except Exception:
            self._show_error()

    def _do_load_image(self):
        """実際の画像読み込み処理"""
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

        except Exception:
            self._show_error()

    def _load_image_immediate(self):
        """即座に画像を読み込み（初期読み込み用）"""
        self._do_load_image()

    def _show_error(self):
        """エラー表示"""
        error_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        error_pixmap.fill(Qt.GlobalColor.red)
        self.setPixmap(error_pixmap)
        self.setText("Error")

    def mousePressEvent(self, ev):
        """マウスクリック処理"""
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(ev)


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
        self.spacing = 10
        self.min_columns = 2  # 最小列数
        self.max_columns = 8  # 最大列数

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
            layout.addWidget(self.controls_widget)

            # スクロールエリア（上下スクロールのみ）
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 左右スクロール無効
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)     # 上下スクロールのみ
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #f9f9f9;
                }
                QScrollBar:vertical {
                    background-color: #f0f0f0;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #c0c0c0;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #a0a0a0;
                }
            """)

            # グリッドウィジェット
            self.grid_widget = QWidget()
            self.grid_layout = QGridLayout(self.grid_widget)
            self.grid_layout.setSpacing(self.spacing)
            self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

            # グリッドウィジェットの幅を親に合わせる
            self.grid_widget.setMinimumWidth(0)  # 最小幅を0に設定

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
        """サムネイルサイズ変更（遅延処理版）"""
        try:
            # サイズを即座に更新（UI反応性のため）
            self.thumbnail_size = size

            # 既存の遅延タイマーをキャンセル
            if hasattr(self, '_size_change_timer'):
                self._size_change_timer.stop()

            # 新しい遅延タイマーを開始（500ms後に実行）
            from PyQt6.QtCore import QTimer
            self._size_change_timer = QTimer()
            self._size_change_timer.setSingleShot(True)
            self._size_change_timer.timeout.connect(lambda: self._apply_size_change(size))
            self._size_change_timer.start(500)  # 500ms遅延

            # ステータス表示を即座に更新
            self.status_label.setText(f"Size: {size}px (updating...)")

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "size_change", "size": size}, AIComponent.CURSOR
            )

    def _apply_size_change(self, size: int):
        """サイズ変更を実際に適用"""
        try:
            # 状態を保存
            self.state_manager.update_state(thumbnail_size=size)

            # 効率的なサムネイル更新
            self._update_thumbnail_sizes_optimized()

            # ステータス更新
            self.status_label.setText(f"{len(self.image_list)} images (Size: {size}px)")

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_size_applied",
                f"Thumbnail size applied: {size}px",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "apply_size_change", "size": size}, AIComponent.CURSOR
            )

    def _update_thumbnail_sizes_optimized(self):
        """最適化されたサムネイルサイズ更新"""
        try:
            if not self.image_list:
                return

            # 新しい列数を計算
            new_columns = self._calculate_columns()

            # 既存のサムネイルアイテムのサイズを更新
            for thumbnail_item in self.thumbnail_items.values():
                # サイズを更新
                thumbnail_item.thumbnail_size = self.thumbnail_size
                thumbnail_item.setFixedSize(self.thumbnail_size + 20, self.thumbnail_size + 40)

                # 画像を非同期で再読み込み（重い処理を避ける）
                thumbnail_item._load_image()

            # 列数が変わった場合のみグリッドを再構築
            current_columns = self._get_current_columns()
            if new_columns != current_columns:
                self._rebuild_grid_layout(new_columns)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_thumbnail_sizes_optimized"}, AIComponent.CURSOR
            )

    def _get_current_columns(self) -> int:
        """現在のグリッドの列数を取得"""
        try:
            if not self.thumbnail_items:
                return 0

            # グリッドレイアウトから列数を推定
            max_col = 0
            for row in range(self.grid_layout.rowCount()):
                for col in range(self.grid_layout.columnCount()):
                    item = self.grid_layout.itemAtPosition(row, col)
                    if item:
                        max_col = max(max_col, col)

            return max_col + 1

        except Exception:
            return 0

    def _rebuild_grid_layout(self, new_columns: int):
        """グリッドレイアウトのみを再構築（アイテムは再利用）"""
        try:
            # 既存のアイテムをグリッドから削除（削除はしない）
            existing_items = []
            for thumbnail_item in self.thumbnail_items.values():
                self.grid_layout.removeWidget(thumbnail_item)
                existing_items.append(thumbnail_item)

            # 新しいレイアウトで再配置
            for i, thumbnail_item in enumerate(existing_items):
                row = i // new_columns
                col = i % new_columns
                self.grid_layout.addWidget(thumbnail_item, row, col)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "grid_layout_rebuilt",
                f"Grid layout rebuilt with {new_columns} columns",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "rebuild_grid_layout", "columns": new_columns}, AIComponent.CURSOR
            )

    def _update_thumbnail_sizes(self):
        """既存のサムネイルサイズを更新（後方互換性のため）"""
        # 最適化版を呼び出し
        self._update_thumbnail_sizes_optimized()

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

    def _calculate_columns(self) -> int:
        """利用可能な幅に基づいて列数を計算"""
        try:
            # スクロールエリアの利用可能な幅を取得
            available_width = self.scroll_area.viewport().width()

            # スクロールバーの幅を考慮（垂直スクロールバーのみ）
            scrollbar_width = 15  # 垂直スクロールバーの幅
            usable_width = available_width - scrollbar_width - (self.spacing * 2)

            # サムネイルアイテムの実際の幅（サムネイル + パディング）
            item_width = self.thumbnail_size + 20 + self.spacing

            # 計算可能な列数
            calculated_columns = max(1, usable_width // item_width)

            # 最小・最大列数の制限を適用
            columns = max(self.min_columns, min(self.max_columns, calculated_columns))

            return columns

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "calculate_columns"}, AIComponent.CURSOR
            )
            return 3  # デフォルト値

    def _create_thumbnails(self):
        """サムネイルを作成"""
        try:
            # 動的に列数を計算
            columns = self._calculate_columns()

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
                if col >= columns:
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
        except Exception:
            pass

    def resizeEvent(self, event):
        """ウィンドウリサイズ時の処理"""
        super().resizeEvent(event)

        # リサイズ後に少し遅延してグリッドを再構築
        # （リサイズイベントが連続して発生するのを避けるため）
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()

        from PyQt6.QtCore import QTimer
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._on_resize_finished)
        self._resize_timer.start(300)  # 300ms後に実行（最適化）

    def _on_resize_finished(self):
        """リサイズ完了時の処理（最適化版）"""
        try:
            if self.image_list:
                # 新しい列数を計算
                new_columns = self._calculate_columns()
                current_columns = self._get_current_columns()

                # 列数が変わった場合のみ再構築
                if new_columns != current_columns:
                    self._rebuild_grid_layout(new_columns)
                else:
                    # 列数が同じ場合は何もしない（パフォーマンス向上）
                    return

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "grid_resized",
                    f"Grid resized, new columns: {new_columns}",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "resize_finished"}, AIComponent.CURSOR
            )

    def show_error_state(self, error_message: str):
        """エラー状態を表示"""
        try:
            self.status_label.setText(f"❌ {error_message}")
        except Exception:
            pass

    def show_empty_state(self):
        """空状態を表示"""
        try:
            self.status_label.setText("No images found")
            self._clear_thumbnails()
        except Exception:
            pass

    def clear_thumbnails_safely(self):
        """安全にサムネイルをクリア（互換性のため）"""
        self._clear_thumbnails()
