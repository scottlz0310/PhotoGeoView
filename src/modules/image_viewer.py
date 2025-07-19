"""
画像表示機能を提供するモジュール
PhotoGeoView プロジェクト用の画像表示機能
"""

from typing import Optional, Tuple
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QPixmap,
    QPainter,
    QPen,
    QColor,
    QMouseEvent,
    QWheelEvent,
    QKeyEvent,
)

from src.core.logger import get_logger


class ImageViewer(QWidget):
    """画像表示ウィジェット"""

    # シグナル定義
    image_changed = pyqtSignal(str)  # 画像変更時に発信
    zoom_changed = pyqtSignal(float)  # ズーム変更時に発信

    def __init__(self, parent=None):
        """
        ImageViewerの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)

        # 画像データ
        self._original_pixmap: Optional[QPixmap] = None
        self._current_pixmap: Optional[QPixmap] = None
        self._current_file_path: str = ""

        # 表示設定
        self._zoom_factor: float = 1.0
        self._min_zoom: float = 0.1
        self._max_zoom: float = 5.0
        self._zoom_step: float = 0.1

        # パン設定
        self._pan_start: Optional[Tuple[int, int]] = None
        self._pan_offset: Tuple[int, int] = (0, 0)
        self._is_panning: bool = False

        # 表示モード
        self._fit_to_window: bool = True
        self._show_grid: bool = False

        # UI初期化
        self._init_ui()
        self._init_connections()

        self.logger.debug("ImageViewerを初期化しました")

    def _init_ui(self) -> None:
        """UIの初期化"""
        # メインレイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ツールバー
        self._init_toolbar()
        layout.addLayout(self.toolbar_layout)

        # 画像表示エリア
        self._init_image_area()
        layout.addWidget(self.image_frame, 1)

    def _init_toolbar(self) -> None:
        """ツールバーの初期化"""
        self.toolbar_layout = QHBoxLayout()

        # ズームアウトボタン
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setToolTip("ズームアウト")
        self.zoom_out_button.setMaximumWidth(30)

        # ズームスライダー
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(int(self._min_zoom * 100))
        self.zoom_slider.setMaximum(int(self._max_zoom * 100))
        self.zoom_slider.setValue(int(self._zoom_factor * 100))
        self.zoom_slider.setToolTip("ズーム")

        # ズームインボタン
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setToolTip("ズームイン")
        self.zoom_in_button.setMaximumWidth(30)

        # フィットボタン
        self.fit_button = QPushButton("フィット")
        self.fit_button.setToolTip("ウィンドウにフィット")
        self.fit_button.setCheckable(True)
        self.fit_button.setChecked(self._fit_to_window)

        # グリッドボタン
        self.grid_button = QPushButton("グリッド")
        self.grid_button.setToolTip("グリッド表示")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(self._show_grid)

        # リセットボタン
        self.reset_button = QPushButton("リセット")
        self.reset_button.setToolTip("表示をリセット")

        # ツールバーに追加
        self.toolbar_layout.addWidget(self.zoom_out_button)
        self.toolbar_layout.addWidget(self.zoom_slider)
        self.toolbar_layout.addWidget(self.zoom_in_button)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.fit_button)
        self.toolbar_layout.addWidget(self.grid_button)
        self.toolbar_layout.addWidget(self.reset_button)

    def _init_image_area(self) -> None:
        """画像表示エリアの初期化"""
        self.image_frame = QFrame()
        self.image_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.image_frame.setStyleSheet("background-color: #f0f0f0;")

        # 画像ラベル
        self.image_label = QLabel("画像を選択してください")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")

        # マウスイベントを有効化
        self.image_label.setMouseTracking(True)
        self.image_label.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # レイアウト
        image_layout = QVBoxLayout(self.image_frame)
        image_layout.addWidget(self.image_label)

    def _init_connections(self) -> None:
        """シグナル・スロット接続の初期化"""
        # ボタン接続
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.fit_button.toggled.connect(self.set_fit_to_window)
        self.grid_button.toggled.connect(self.set_show_grid)
        self.reset_button.clicked.connect(self.reset_view)

        # スライダー接続
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)

    def load_image(self, file_path: str, pixmap: Optional[QPixmap] = None) -> bool:
        """
        画像を読み込み

        Args:
            file_path: 画像ファイルパス
            pixmap: 画像のQPixmap

        Returns:
            読み込み成功の場合True
        """
        try:
            if pixmap is None:
                self.logger.warning("画像データが提供されていません")
                return False

            self._original_pixmap = pixmap
            self._current_file_path = file_path

            # 表示をリセット
            self.reset_view()

            self.logger.debug(f"画像を読み込みました: {file_path}")
            self.image_changed.emit(file_path)
            return True

        except Exception as e:
            self.logger.error(f"画像の読み込みに失敗しました: {file_path}, エラー: {e}")
            return False

    def set_zoom(self, factor: float) -> None:
        """
        ズーム率を設定

        Args:
            factor: ズーム率
        """
        factor = max(self._min_zoom, min(self._max_zoom, factor))

        if abs(self._zoom_factor - factor) > 0.01:
            self._zoom_factor = factor
            self._update_display()
            self.zoom_changed.emit(factor)

            # スライダーを更新
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(int(factor * 100))
            self.zoom_slider.blockSignals(False)

    def zoom_in(self) -> None:
        """ズームイン"""
        self.set_zoom(self._zoom_factor + self._zoom_step)

    def zoom_out(self) -> None:
        """ズームアウト"""
        self.set_zoom(self._zoom_factor - self._zoom_step)

    def set_fit_to_window(self, enabled: bool) -> None:
        """
        ウィンドウフィットモードを設定

        Args:
            enabled: 有効にする場合True
        """
        self._fit_to_window = enabled
        if enabled:
            self._fit_image_to_window()
        else:
            self._update_display()

    def set_show_grid(self, enabled: bool) -> None:
        """
        グリッド表示を設定

        Args:
            enabled: 有効にする場合True
        """
        self._show_grid = enabled
        self._update_display()

    def reset_view(self) -> None:
        """表示をリセット"""
        self._zoom_factor = 1.0
        self._pan_offset = (0, 0)
        self._fit_to_window = True
        self.fit_button.setChecked(True)
        self._update_display()

    def _on_zoom_slider_changed(self, value: int) -> None:
        """
        ズームスライダー変更時の処理

        Args:
            value: スライダー値
        """
        factor = value / 100.0
        self.set_zoom(factor)

    def _fit_image_to_window(self) -> None:
        """画像をウィンドウにフィット"""
        if not self._original_pixmap:
            return

        # ウィンドウサイズを取得
        window_size = self.image_label.size()

        # 画像サイズを取得
        image_size = self._original_pixmap.size()

        # アスペクト比を保持してフィット
        scale_x = window_size.width() / image_size.width()
        scale_y = window_size.height() / image_size.height()
        scale = min(scale_x, scale_y)

        self.set_zoom(scale)

    def _update_display(self) -> None:
        """表示を更新"""
        if not self._original_pixmap:
            return

        try:
            # ズーム適用
            if self._fit_to_window:
                self._fit_image_to_window()
            else:
                # ズームを適用
                scaled_size = self._original_pixmap.size() * self._zoom_factor
                self._current_pixmap = self._original_pixmap.scaled(
                    scaled_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            # パンオフセットを適用
            if self._current_pixmap:
                # パンオフセットを計算
                label_size = self.image_label.size()
                image_size = self._current_pixmap.size()

                # 画像がラベルより小さい場合は中央に配置
                if (
                    image_size.width() <= label_size.width()
                    and image_size.height() <= label_size.height()
                ):
                    self._pan_offset = (0, 0)

                # パンオフセットを制限
                max_offset_x = max(0, image_size.width() - label_size.width()) // 2
                max_offset_y = max(0, image_size.height() - label_size.height()) // 2

                self._pan_offset = (
                    max(-max_offset_x, min(max_offset_x, self._pan_offset[0])),
                    max(-max_offset_y, min(max_offset_y, self._pan_offset[1])),
                )

            # 表示を更新
            self.image_label.update()

        except Exception as e:
            self.logger.error(f"表示の更新に失敗しました: {e}")

    def paintEvent(self, event) -> None:
        """描画イベント"""
        super().paintEvent(event)

        if not self._current_pixmap:
            return

        # ペインターを作成
        painter = QPainter(self.image_label)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 画像を描画
        label_rect = self.image_label.rect()
        image_rect = self._current_pixmap.rect()

        # パンオフセットを適用
        draw_x = (label_rect.width() - image_rect.width()) // 2 + self._pan_offset[0]
        draw_y = (label_rect.height() - image_rect.height()) // 2 + self._pan_offset[1]

        painter.drawPixmap(draw_x, draw_y, self._current_pixmap)

        # グリッドを描画
        if self._show_grid:
            self._draw_grid(painter, label_rect)

        painter.end()

    def _draw_grid(self, painter: QPainter, rect) -> None:
        """
        グリッドを描画

        Args:
            painter: ペインター
            rect: 描画領域
        """
        painter.setPen(QPen(QColor(128, 128, 128, 64), 1, Qt.PenStyle.SolidLine))

        # 縦線
        for x in range(0, rect.width(), 50):
            painter.drawLine(x, 0, x, rect.height())

        # 横線
        for y in range(0, rect.height(), 50):
            painter.drawLine(0, y, rect.width(), y)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウスプレスイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pan_start = (int(event.position().x()), int(event.position().y()))
            self._is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウスリリースイベント"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pan_start = None
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウス移動イベント"""
        if self._is_panning and self._pan_start:
            dx = int(event.position().x()) - self._pan_start[0]
            dy = int(event.position().y()) - self._pan_start[1]

            self._pan_offset = (self._pan_offset[0] + dx, self._pan_offset[1] + dy)

            self._pan_start = (int(event.position().x()), int(event.position().y()))
            self._update_display()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """ホイールイベント"""
        # Ctrlキーを押しながらホイールでズーム
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # 通常のホイールでパン
            delta = event.angleDelta().y()
            self._pan_offset = (self._pan_offset[0], self._pan_offset[1] - delta // 8)
            self._update_display()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """キープレスイベント"""
        if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key.Key_0:
            self.reset_view()
        elif event.key() == Qt.Key.Key_F:
            self.fit_button.toggle()
        elif event.key() == Qt.Key.Key_G:
            self.grid_button.toggle()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:
        """リサイズイベント"""
        super().resizeEvent(event)
        if self._fit_to_window:
            self._fit_image_to_window()

    def get_current_file_path(self) -> str:
        """
        現在のファイルパスを取得

        Returns:
            現在のファイルパス
        """
        return self._current_file_path

    def get_zoom_factor(self) -> float:
        """
        現在のズーム率を取得

        Returns:
            ズーム率
        """
        return self._zoom_factor

    def has_image(self) -> bool:
        """
        画像が読み込まれているかどうかを確認

        Returns:
            画像が読み込まれている場合True
        """
        return self._original_pixmap is not None
