"""
Image Preview Panel - 画像プレビューパネル

選択された画像を表示するプレビューパネル。
基本的なズーム・パン機能を含む。

Author: Kiro AI Integration System
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..state_manager import StateManager


class ImagePreviewPanel(QWidget):
    """
    画像プレビューパネル

    機能:
    - 選択された画像の表示
    - 基本的なズーム機能
    - パン機能（スクロール）
    - 画像情報の表示
    """

    # シグナル
    image_loaded = pyqtSignal(Path)
    zoom_changed = pyqtSignal(float)

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem,
    ):
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system
        self.error_handler = IntegratedErrorHandler(logger_system)

        # 現在の画像パス
        self.current_image_path: Optional[Path] = None

        # ズーム関連
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # UI初期化
        self._setup_ui()

    def _setup_ui(self):
        """UIの初期化"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # タイトル
            title_label = QLabel("画像プレビュー")
            title_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                    color: #2c3e50;
                    padding: 5px;
                    background-color: #ecf0f1;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(title_label)

            # コントロールエリア
            self._create_controls()
            layout.addWidget(self.controls_widget)

            # 画像表示エリア
            self._create_image_display()
            layout.addWidget(self.image_scroll_area)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "image_preview_setup"}, AIComponent.KIRO
            )

    def _create_controls(self):
        """コントロールエリアを作成"""
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 5, 0, 5)

        # ズームアウトボタン
        self.zoom_out_button = QPushButton("−")
        self.zoom_out_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.zoom_out_button.clicked.connect(self._zoom_out)
        controls_layout.addWidget(self.zoom_out_button)

        # ズームスライダー
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(int(self.min_zoom * 100), int(self.max_zoom * 100))
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        controls_layout.addWidget(self.zoom_slider)

        # ズームインボタン
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.zoom_in_button.clicked.connect(self._zoom_in)
        controls_layout.addWidget(self.zoom_in_button)

        # リセットボタン
        self.reset_button = QPushButton("フィット")
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.reset_button.clicked.connect(self._reset_zoom)
        controls_layout.addWidget(self.reset_button)

        controls_layout.addStretch()

        # ズーム率表示
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 5px 10px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        controls_layout.addWidget(self.zoom_label)

    def _create_image_display(self):
        """画像表示エリアを作成"""
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        self.image_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ffffff;
            }
        """)

        # 画像表示ラベル
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: none;
            }
        """)

        # 初期メッセージ
        self._show_placeholder("画像を選択してください")

        self.image_scroll_area.setWidget(self.image_label)

        # 初期化完了後にフィット処理を準備
        self.original_pixmap = None

        # 遅延処理用タイマー
        self.delayed_display_timer = QTimer()
        self.delayed_display_timer.setSingleShot(True)
        self.delayed_display_timer.timeout.connect(self._delayed_display_image)

    def _show_placeholder(self, message: str):
        """プレースホルダーメッセージを表示"""
        try:
            # プレースホルダー画像を作成
            placeholder = QPixmap(400, 300)
            placeholder.fill(QColor("#e9ecef"))

            # メッセージを描画
            painter = QPainter(placeholder)
            painter.setPen(QColor("#6c757d"))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, message)
            painter.end()

            self.image_label.setPixmap(placeholder)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "show_placeholder"}, AIComponent.KIRO
            )

    def set_image(self, image_path: Path):
        """画像を設定して表示"""
        try:
            self.current_image_path = image_path

            if not image_path or not image_path.exists():
                self._show_placeholder("画像が見つかりません")
                return

            # 画像を読み込み
            pixmap = QPixmap(str(image_path))

            if pixmap.isNull():
                self._show_placeholder("画像の読み込みに失敗しました")
                return

            # 元の画像サイズを保存
            self.original_pixmap = pixmap

            # 遅延処理で画像表示（100ms後）
            self.delayed_display_timer.start(100)

            # シグナルを発信
            self.image_loaded.emit(image_path)

            # ログ出力
            self.logger_system.log_info(
                f"画像プレビューに読み込み: {image_path.name}",
                {"image_path": str(image_path), "size": f"{pixmap.width()}x{pixmap.height()}"},
                AIComponent.KIRO,
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_image", "image_path": str(image_path)},
                AIComponent.KIRO
            )
            self._show_placeholder("画像の読み込みに失敗しました")

    def _delayed_display_image(self):
        """遅延処理で画像を表示"""
        try:
            if hasattr(self, 'original_pixmap') and self.original_pixmap:
                # 初期ズーム率を設定（100%で開始）
                self.zoom_factor = 1.0

                # 強制的に表示を更新
                self._update_image_display()

                # ウィンドウフィットに調整（初期表示）
                self._reset_zoom()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "delayed_display_image"}, AIComponent.KIRO
            )

    def _update_image_display(self):
        """画像表示を更新"""
        try:
            if hasattr(self, 'original_pixmap') and self.original_pixmap:
                # ズームを適用
                scaled_pixmap = self.original_pixmap.scaled(
                    int(self.original_pixmap.width() * self.zoom_factor),
                    int(self.original_pixmap.height() * self.zoom_factor),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                self.image_label.setPixmap(scaled_pixmap)

                # ズーム率表示を更新
                zoom_percentage = int(self.zoom_factor * 100)
                self.zoom_label.setText(f"{zoom_percentage}%")

                # スライダーを更新（無限ループを避けるため）
                self.zoom_slider.blockSignals(True)
                self.zoom_slider.setValue(zoom_percentage)
                self.zoom_slider.blockSignals(False)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_image_display"}, AIComponent.KIRO
            )

    def _zoom_in(self):
        """ズームイン"""
        try:
            new_zoom = min(self.zoom_factor * 1.25, self.max_zoom)
            if new_zoom != self.zoom_factor:
                self.zoom_factor = new_zoom
                self._update_image_display()
                self.zoom_changed.emit(self.zoom_factor)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "zoom_in"}, AIComponent.KIRO
            )

    def _zoom_out(self):
        """ズームアウト"""
        try:
            new_zoom = max(self.zoom_factor / 1.25, self.min_zoom)
            if new_zoom != self.zoom_factor:
                self.zoom_factor = new_zoom
                self._update_image_display()
                self.zoom_changed.emit(self.zoom_factor)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "zoom_out"}, AIComponent.KIRO
            )

    def _reset_zoom(self):
        """ズームをウィンドウフィットにリセット"""
        try:
            if hasattr(self, 'original_pixmap') and self.original_pixmap:
                # スクロールエリアのサイズを取得
                scroll_size = self.image_scroll_area.size()
                image_size = self.original_pixmap.size()

                # ウィンドウフィットのズーム率を計算
                width_ratio = scroll_size.width() / image_size.width()
                height_ratio = scroll_size.height() / image_size.height()

                # 小さい方の比率を使用（画像全体が表示されるように）
                self.zoom_factor = min(width_ratio, height_ratio, 1.0)  # 最大100%

                # 最小ズーム率を下回らないように
                self.zoom_factor = max(self.zoom_factor, self.min_zoom)
            else:
                self.zoom_factor = 1.0

            self._update_image_display()
            self.zoom_changed.emit(self.zoom_factor)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "reset_zoom"}, AIComponent.KIRO
            )

    def _on_zoom_slider_changed(self, value: int):
        """ズームスライダーの値変更"""
        try:
            new_zoom = value / 100.0
            if new_zoom != self.zoom_factor:
                self.zoom_factor = new_zoom
                self._update_image_display()
                self.zoom_changed.emit(self.zoom_factor)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "zoom_slider_changed"}, AIComponent.KIRO
            )

    def get_current_image_path(self) -> Optional[Path]:
        """現在の画像パスを取得"""
        return self.current_image_path

    def get_zoom_factor(self) -> float:
        """現在のズーム率を取得"""
        return self.zoom_factor
