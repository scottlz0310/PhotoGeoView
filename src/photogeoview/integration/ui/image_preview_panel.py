"""
Image Preview Panel - 画像プレビューパネル

選択された画像を表示するプレビューパネル。
全画面表示機能とマウス操作(ズーム・パン)機能を含む。

Author: Kiro AI Integration System
"""

from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..state_manager import StateManager


class ImageViewerWidget(QWidget):
    """
    カスタム画像ビューアーウィジェット

    機能:
    - マウスホイールでのズーム
    - マウスドラッグでのパン
    - 全画面表示対応
    """

    zoom_changed = Signal(float)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # 画像関連
        self.original_pixmap: QPixmap | None = None
        self.display_pixmap: QPixmap | None = None

        # ズーム・パン関連
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.pan_offset = QPoint(0, 0)
        self.last_mouse_pos = QPoint(0, 0)
        self.is_panning = False

        # UI設定
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 背景色
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2c3e50;
            }
        """
        )

    def set_image(self, pixmap: QPixmap):
        """画像を設定"""
        self.original_pixmap = pixmap
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self._update_display()

    def set_zoom(self, zoom_factor: float):
        """ズームを設定"""
        self.zoom_factor = max(self.min_zoom, min(self.max_zoom, zoom_factor))
        self._update_display()
        self.zoom_changed.emit(self.zoom_factor)

    def _update_display(self):
        """表示を更新"""
        if self.original_pixmap is None:
            return

        # ズーム適用
        scaled_size = self.original_pixmap.size() * self.zoom_factor
        self.display_pixmap = self.original_pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.update()

    def paintEvent(self, event):
        """描画イベント"""
        if self.display_pixmap is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 背景を描画
        painter.fillRect(self.rect(), QColor("#2c3e50"))

        # 画像を中央に配置
        image_rect = self.display_pixmap.rect()
        image_rect.moveCenter(self.rect().center() + self.pan_offset)

        painter.drawPixmap(image_rect, self.display_pixmap)

    def wheelEvent(self, event: QWheelEvent):
        """マウスホイールイベント(ズーム)"""
        delta = event.angleDelta().y()
        zoom_delta = 0.1 if delta > 0 else -0.1

        # マウス位置を基準にズーム
        mouse_pos = event.position()
        old_zoom = self.zoom_factor
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom_factor + zoom_delta))

        if new_zoom != old_zoom:
            # マウス位置を基準にパンオフセットを調整
            zoom_ratio = new_zoom / old_zoom
            self.pan_offset = QPoint(
                int(mouse_pos.x() - (mouse_pos.x() - self.pan_offset.x()) * zoom_ratio),
                int(mouse_pos.y() - (mouse_pos.y() - self.pan_offset.y()) * zoom_ratio),
            )

            self.set_zoom(new_zoom)

            # 全画面表示中の場合、親のImagePreviewPanelにフォーカスを戻す
            parent_panel = self.parent()
            while parent_panel:
                if hasattr(parent_panel, "is_fullscreen_mode") and hasattr(parent_panel, "setFocus"):
                    if parent_panel.is_fullscreen_mode:
                        parent_panel.setFocus(Qt.FocusReason.MouseFocusReason)
                    break
                parent_panel = parent_panel.parent()

    def mousePressEvent(self, event: QMouseEvent):
        """マウスプレスイベント(パン開始)"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

            # 全画面表示中の場合、フォーカスを親に確実に設定
            parent_panel = self.parent()
            while parent_panel:
                if hasattr(parent_panel, "is_fullscreen_mode") and hasattr(parent_panel, "setFocus"):
                    if parent_panel.is_fullscreen_mode:
                        parent_panel.setFocus(Qt.FocusReason.MouseFocusReason)
                        # 自分自身はフォーカスを放棄
                        self.clearFocus()
                    break
                parent_panel = parent_panel.parent()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """マウスリリースイベント(パン終了)"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

            # 全画面表示中の場合、親のImagePreviewPanelにフォーカスを戻す
            parent_panel = self.parent()
            while parent_panel:
                if hasattr(parent_panel, "is_fullscreen_mode") and hasattr(parent_panel, "setFocus"):
                    if parent_panel.is_fullscreen_mode:
                        parent_panel.setFocus(Qt.FocusReason.MouseFocusReason)
                    break
                parent_panel = parent_panel.parent()

    def mouseMoveEvent(self, event: QMouseEvent):
        """マウスムーブイベント(パン)"""
        if self.is_panning:
            delta = event.pos() - self.last_mouse_pos
            self.pan_offset += delta
            self.last_mouse_pos = event.pos()
            self.update()

            # パン操作中でも親にフォーカスを維持(重要！)
            parent_panel = self.parent()
            while parent_panel:
                if hasattr(parent_panel, "is_fullscreen_mode") and hasattr(parent_panel, "setFocus"):
                    if parent_panel.is_fullscreen_mode:
                        # フォーカスを親に強制的に設定
                        parent_panel.setFocus(Qt.FocusReason.MouseFocusReason)
                    break
                parent_panel = parent_panel.parent()

    def keyPressEvent(self, event):
        """キーイベント"""
        if event.key() == Qt.Key.Key_Escape:
            # ESCキーは親のImagePreviewPanelで処理
            parent_panel = self.parent()
            # ImagePreviewPanelを探して上へ遡る(_exit_fullscreenメソッドを持つ親を探す)
            while parent_panel:
                if hasattr(parent_panel, "_exit_fullscreen") and hasattr(parent_panel, "is_fullscreen_mode"):
                    # 全画面モードの場合のみ処理
                    if parent_panel.is_fullscreen_mode:
                        parent_panel._exit_fullscreen()
                        return  # イベントを消費
                    break
                parent_panel = parent_panel.parent()

        # その他のキーイベントは親クラスに委譲
        super().keyPressEvent(event)


class ImagePreviewPanel(QWidget):
    """
    画像プレビューパネル

    機能:
    - 選択された画像の表示
    - 全画面表示機能
    - マウス操作(ズーム・パン)
    - 画像情報の表示
    """

    # シグナル
    image_loaded = Signal(Path)
    zoom_changed = Signal(float)
    status_message = Signal(str)

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
        self.current_image_path: Path | None = None

        # ズーム関連
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0

        # 全画面表示関連
        self.is_fullscreen_mode = False
        self._hidden_widgets = []
        self._original_parent = None

        # UI初期化
        self._setup_ui()

    def _setup_ui(self):
        """UIの初期化"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # タイトルバー(全画面ボタン付き)
            title_layout = QHBoxLayout()

            title_label = QLabel("🖼️ 画像プレビュー")
            title_label.setStyleSheet(
                """
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                    color: #2c3e50;
                    padding: 5px;
                }
            """
            )
            title_layout.addWidget(title_label)

            title_layout.addStretch()

            # 全画面ボタン
            self.fullscreen_button = QPushButton("⛶ 全画面表示")
            self.fullscreen_button.setToolTip("画像をウィンドウいっぱいに表示 / 通常表示に戻る (F11)")
            self.fullscreen_button.setFixedSize(100, 24)
            self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
            title_layout.addWidget(self.fullscreen_button)

            layout.addLayout(title_layout)

            # 画像表示エリア
            self._create_image_display()
            layout.addWidget(self.image_viewer)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "image_preview_setup"},
                AIComponent.KIRO,
            )

    def _create_controls(self):
        """コントロールエリアを作成"""
        self.controls_widget = QWidget()
        self.controls_widget.setFixedHeight(35)  # 高さを固定
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 2, 0, 2)  # 上下マージンを縮小

        # ズームアウトボタン
        self.zoom_out_button = QPushButton("−")
        self.zoom_out_button.setFixedSize(30, 25)  # サイズを固定
        self.zoom_out_button.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """
        )
        self.zoom_out_button.clicked.connect(self._zoom_out)
        controls_layout.addWidget(self.zoom_out_button)

        # ズームスライダー
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setFixedHeight(20)  # 高さを固定
        self.zoom_slider.setRange(int(self.min_zoom * 100), int(self.max_zoom * 100))
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        controls_layout.addWidget(self.zoom_slider)

        # ズームインボタン
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setFixedSize(30, 25)  # サイズを固定
        self.zoom_in_button.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """
        )
        self.zoom_in_button.clicked.connect(self._zoom_in)
        controls_layout.addWidget(self.zoom_in_button)

        # ウィンドウフィットボタン
        self.fit_button = QPushButton("フィット")
        self.fit_button.setToolTip("画面にフィット")
        self.fit_button.setFixedSize(50, 25)  # 幅を50pxに拡大
        self.fit_button.setStyleSheet(
            """
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """
        )
        self.fit_button.clicked.connect(self._fit_to_screen)
        controls_layout.addWidget(self.fit_button)

        controls_layout.addStretch()

        # ズーム表示ラベル
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedSize(50, 25)  # サイズを固定
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
                border-radius: 3px;
                font-size: 12px;
            }
        """
        )
        controls_layout.addWidget(self.zoom_label)

    def _create_image_display(self):
        """画像表示エリアを作成"""
        # カスタム画像ビューアーを使用
        self.image_viewer = ImageViewerWidget()
        self.image_viewer.zoom_changed.connect(self._on_zoom_changed)

        # プレースホルダーを表示
        self._show_placeholder("画像を選択してください")

    def _show_placeholder(self, message: str):
        """プレースホルダーを表示"""
        try:
            # プレースホルダー画像を作成
            placeholder = QPixmap(400, 300)
            placeholder.fill(QColor("#ecf0f1"))

            painter = QPainter(placeholder)
            painter.setPen(QColor("#7f8c8d"))
            painter.setFont(QFont("Arial", 14))

            # メッセージを中央に描画
            text_rect = placeholder.rect()
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, message)
            painter.end()

            self.image_viewer.set_image(placeholder)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_placeholder"},
                AIComponent.KIRO,
            )

    def set_image(self, image_path: Path):
        """画像を設定"""
        try:
            self.current_image_path = image_path

            # ローディング状態を表示
            self._show_placeholder("画像を読み込み中...")

            # 遅延読み込み(UI応答性向上のため)
            QTimer.singleShot(100, self._delayed_display_image)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_image"},
                AIComponent.KIRO,
            )

    def _delayed_display_image(self):
        """遅延画像表示"""
        try:
            if self.current_image_path and self.current_image_path.exists():
                # 画像を読み込み
                pixmap = QPixmap(str(self.current_image_path))

                if not pixmap.isNull():
                    self.image_viewer.set_image(pixmap)
                    self.zoom_factor = 1.0
                    self._update_controls()

                    # シグナルを発信
                    self.image_loaded.emit(self.current_image_path)

                    # ステータスメッセージ
                    self.status_message.emit(f"画像を読み込みました: {self.current_image_path.name}")

                    # 遅延処理でフィット処理を実行
                    QTimer.singleShot(200, self._fit_to_screen)
                else:
                    self._show_placeholder("画像の読み込みに失敗しました")
            else:
                self._show_placeholder("画像ファイルが見つかりません")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "delayed_display_image"},
                AIComponent.KIRO,
            )

    def _update_controls(self):
        """コントロールを更新"""
        try:
            # ズームスライダーを更新
            self.zoom_slider.setValue(int(self.zoom_factor * 100))

            # ズームラベルを更新
            self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_controls"},
                AIComponent.KIRO,
            )

    def _zoom_in(self):
        """ズームイン"""
        try:
            new_zoom = min(self.max_zoom, self.zoom_factor + 0.25)
            self.image_viewer.set_zoom(new_zoom)
            self.zoom_factor = new_zoom
            self._update_controls()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "zoom_in"},
                AIComponent.KIRO,
            )

    def _zoom_out(self):
        """ズームアウト"""
        try:
            new_zoom = max(self.min_zoom, self.zoom_factor - 0.25)
            self.image_viewer.set_zoom(new_zoom)
            self.zoom_factor = new_zoom
            self._update_controls()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "zoom_out"},
                AIComponent.KIRO,
            )

    def _reset_zoom(self):
        """ズームをリセット"""
        try:
            self.image_viewer.set_zoom(1.0)
            self.zoom_factor = 1.0
            self._update_controls()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "reset_zoom"},
                AIComponent.KIRO,
            )

    def _on_zoom_slider_changed(self, value: int):
        """ズームスライダー変更時の処理"""
        try:
            zoom_factor = value / 100.0
            self.image_viewer.set_zoom(zoom_factor)
            self.zoom_factor = zoom_factor
            self._update_controls()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "zoom_slider_changed"},
                AIComponent.KIRO,
            )

    def _on_zoom_changed(self, zoom_factor: float):
        """ズーム変更時の処理"""
        try:
            self.zoom_factor = zoom_factor
            self._update_controls()
            self.zoom_changed.emit(zoom_factor)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "zoom_changed"},
                AIComponent.KIRO,
            )

    def _toggle_fullscreen(self):
        """画像プレビューパネルを全画面表示"""
        try:
            # 親ウィンドウを取得
            parent_window = self.window()

            if self.is_fullscreen_mode:
                # 通常表示に戻る
                self._exit_fullscreen()

            else:
                # 画像ビューアーを全画面表示
                self._enter_fullscreen(parent_window)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "toggle_fullscreen"},
                AIComponent.KIRO,
            )

    def _enter_fullscreen(self, parent_window):
        """全画面表示を開始"""
        try:
            self.is_fullscreen_mode = True

            # 他のUI要素を非表示(全画面ボタンは残す)
            self._hide_other_ui_elements()

            # 画像ビューアーの元の親とレイアウト情報を保存
            self._original_parent = self.image_viewer.parent()

            # レイアウトから画像ビューアーの位置を取得して保存
            main_layout = self.layout()
            if main_layout:
                self._original_layout_index = main_layout.indexOf(self.image_viewer)
                # レイアウトから一時的に削除(親を変更する前に)
                main_layout.removeWidget(self.image_viewer)

            # 全画面ボタンの元のレイアウト情報も保存
            if hasattr(self, "fullscreen_button"):
                # 元のスタイルとウィンドウフラグを保存
                self._original_button_style = self.fullscreen_button.styleSheet()
                self._original_button_flags = self.fullscreen_button.windowFlags()

                # title_layoutを探す(メインレイアウトの最初のアイテム)
                if main_layout and main_layout.count() > 0:
                    title_layout_item = main_layout.itemAt(0)
                    if title_layout_item and hasattr(title_layout_item, "layout"):
                        title_layout = title_layout_item.layout()
                        if title_layout:
                            self._original_button_layout = title_layout
                            self._original_button_index = title_layout.indexOf(self.fullscreen_button)
                            # ボタンをレイアウトから一時的に削除
                            title_layout.removeWidget(self.fullscreen_button)

            # 画像ビューアーのみを親ウィンドウに配置
            self.image_viewer.setParent(parent_window)

            # 全画面表示中はImageViewerWidgetがフォーカスを受け取らないように設定
            self._original_focus_policy = self.image_viewer.focusPolicy()
            self.image_viewer.setFocusPolicy(Qt.FocusPolicy.NoFocus)

            # 全画面ボタンも親ウィンドウに配置(画像の上に表示)
            if hasattr(self, "fullscreen_button"):
                self.fullscreen_button.setParent(parent_window)
                self.fullscreen_button.setText("⛶ 戻る")

                # 全画面時のボタンスタイルを強化(必ず見えるように)
                self.fullscreen_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(52, 73, 94, 0.8);
                        color: white;
                        border: 2px solid #2c3e50;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 12px;
                        padding: 3px 6px;
                    }
                    QPushButton:hover {
                        background-color: rgba(44, 62, 80, 0.9);
                        border-color: #34495e;
                    }
                    QPushButton:pressed {
                        background-color: rgba(44, 62, 80, 1.0);
                    }
                """)

                self.fullscreen_button.setVisible(True)
                self.fullscreen_button.show()
                self.fullscreen_button.raise_()  # 最前面に表示

                # 確実に最前面に表示
                self.fullscreen_button.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "debug_reparent_image_to_window",
                f"画像ビューアーを親ウィンドウに配置しました: {type(parent_window).__name__}",
                level="INFO",
            )

            # 画像ビューアーを確実に表示
            self.image_viewer.setVisible(True)
            self.image_viewer.raise_()

            # 画像ビューアーをウィンドウいっぱいに表示
            self.image_viewer.setMaximumSize(16777215, 16777215)
            self.image_viewer.resize(parent_window.size())

            # 画像ビューアーを親ウィンドウの中央に配置
            self.image_viewer.move(0, 0)

            # 全画面ボタンを右上角に配置(遅延処理で確実に配置)
            if hasattr(self, "fullscreen_button"):
                # 即座に基本位置を設定
                self.fullscreen_button.move(parent_window.width() - 110, 10)

                # 遅延処理でより正確な位置を計算・配置
                QTimer.singleShot(50, lambda: self._position_fullscreen_button(parent_window))

            # 全画面表示後に画面フィットを実行
            QTimer.singleShot(100, self._fit_to_screen)

            # 複数回のタイミングでボタンの表示を確認
            QTimer.singleShot(150, lambda: self._position_fullscreen_button(parent_window))
            QTimer.singleShot(300, lambda: self._position_fullscreen_button(parent_window))

            # フォーカスを確実に設定(キーイベントを受信するため)
            self.setFocus(Qt.FocusReason.OtherFocusReason)

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "enter_image_fullscreen",
                "画像全画面表示を開始",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "enter_fullscreen"},
                AIComponent.KIRO,
            )

    def _exit_fullscreen(self):
        """全画面表示を終了"""
        try:
            self.is_fullscreen_mode = False

            # 画像ビューアーを元の親とレイアウトに戻す
            if hasattr(self, "_original_parent"):
                # 親を戻す
                self.image_viewer.setParent(self._original_parent)

                # レイアウトに再追加
                main_layout = self.layout()
                if main_layout and hasattr(self, "_original_layout_index"):
                    # 元の位置に再挿入
                    main_layout.insertWidget(self._original_layout_index, self.image_viewer)
                    delattr(self, "_original_layout_index")
                else:
                    # フォールバック:レイアウトの最後に追加
                    if main_layout:
                        main_layout.addWidget(self.image_viewer)

                # 元のフォーカスポリシーを復元
                if hasattr(self, "_original_focus_policy"):
                    self.image_viewer.setFocusPolicy(self._original_focus_policy)
                    delattr(self, "_original_focus_policy")

                # 全画面ボタンも元の親とレイアウトに戻す
                if hasattr(self, "fullscreen_button"):
                    # 元の親に戻す
                    self.fullscreen_button.setParent(self._original_parent)

                    # 元のスタイルとウィンドウフラグを復元
                    if hasattr(self, "_original_button_style"):
                        self.fullscreen_button.setStyleSheet(self._original_button_style)
                        delattr(self, "_original_button_style")

                    if hasattr(self, "_original_button_flags"):
                        self.fullscreen_button.setWindowFlags(self._original_button_flags)
                        delattr(self, "_original_button_flags")

                    # ボタンテキストを元に戻す
                    self.fullscreen_button.setText("⛶ 全画面表示")

                    # 元のレイアウトに再追加
                    if hasattr(self, "_original_button_layout") and hasattr(self, "_original_button_index"):
                        self._original_button_layout.insertWidget(self._original_button_index, self.fullscreen_button)
                        delattr(self, "_original_button_layout")
                        delattr(self, "_original_button_index")

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_restore_image_parent",
                    f"画像ビューアーを元の親とレイアウトに戻しました: {type(self._original_parent).__name__}",
                    level="INFO",
                )
                delattr(self, "_original_parent")

            # 他のUI要素を再表示
            self._show_other_ui_elements()

            # ImagePreviewPanelのレイアウトを強制的に更新
            self.adjustSize()
            self.update()
            self.repaint()

            # 全画面ボタンを確実に表示
            if hasattr(self, "fullscreen_button"):
                self.fullscreen_button.setVisible(True)
                self.fullscreen_button.show()
                self.fullscreen_button.update()

            # 遅延処理でフィット処理を実行
            QTimer.singleShot(200, self._fit_to_screen)

            # 遅延処理でレイアウト更新も実行(確実に全画面ボタンを表示)
            QTimer.singleShot(300, self._ensure_ui_visibility)

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "exit_image_fullscreen",
                "画像全画面表示を終了",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "exit_fullscreen"},
                AIComponent.KIRO,
            )

    def _fit_to_screen(self):
        """画面にフィットするようにズームを調整"""
        try:
            if not self.image_viewer.original_pixmap:
                return

            # ウィンドウサイズを取得
            window_size = self.image_viewer.size()
            image_size = self.image_viewer.original_pixmap.size()

            # 画面フィットのズーム率を計算
            width_ratio = window_size.width() / image_size.width()
            height_ratio = window_size.height() / image_size.height()

            # 小さい方の比率を使用(画像全体が表示されるように)
            fit_zoom = min(width_ratio, height_ratio)

            # 最小ズーム率を下回らないように
            fit_zoom = max(fit_zoom, self.min_zoom)

            # ズームを適用
            self.image_viewer.set_zoom(fit_zoom)
            self.zoom_factor = fit_zoom
            self._update_controls()

            # パンオフセットをリセット
            self.image_viewer.pan_offset = QPoint(0, 0)
            self.image_viewer.update()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "fit_to_screen",
                f"画面フィット完了: ズーム率={fit_zoom:.2f}",
                level="INFO",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "fit_to_screen"},
                AIComponent.KIRO,
            )

    def _hide_other_ui_elements(self):
        """他のUI要素を非表示にする(安全な方法)"""
        try:
            # 親ウィンドウを取得
            parent_window = self.window()

            # 非表示にするウィジェットのリストを初期化
            if not hasattr(self, "_hidden_widgets"):
                self._hidden_widgets = []

            # メインスプリッターを探す
            from PySide6.QtWidgets import QSplitter

            main_splitter = None
            for child in parent_window.findChildren(QSplitter):
                # 最初に見つかったQSplitterをメインスプリッターとする
                main_splitter = child
                break

            if main_splitter:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_splitter_found",
                    f"メインスプリッター発見: {type(main_splitter).__name__}, 子要素数: {main_splitter.count()}",
                    level="INFO",
                )

                # メインスプリッターの子要素を非表示にする
                for i in range(main_splitter.count()):
                    widget = main_splitter.widget(i)
                    if widget and widget != self and widget.isVisible():
                        widget.setVisible(False)
                        self._hidden_widgets.append(widget)
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "debug_hide_widget",
                            f"ウィジェットを非表示: {type(widget).__name__}",
                            level="INFO",
                        )

                        # 左パネルスプリッター内の要素も非表示
                        if hasattr(widget, "count"):  # スプリッターの場合
                            for j in range(widget.count()):
                                sub_widget = widget.widget(j)
                                if sub_widget and sub_widget.isVisible():
                                    sub_widget.setVisible(False)
                                    self._hidden_widgets.append(sub_widget)
                                    self.logger_system.log_ai_operation(
                                        AIComponent.KIRO,
                                        "debug_hide_sub_widget",
                                        f"サブウィジェットを非表示: {type(sub_widget).__name__}",
                                        level="INFO",
                                    )
            else:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_splitter_not_found",
                    "メインスプリッターが見つかりませんでした",
                    level="WARNING",
                )

            # デバッグ用ログ
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "hide_ui_elements",
                f"非表示にしたウィジェット数: {len(self._hidden_widgets)}",
                level="INFO",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "hide_other_ui_elements"},
                AIComponent.KIRO,
            )

    def _show_other_ui_elements(self):
        """他のUI要素を再表示する(安全な方法)"""
        try:
            # 非表示にしたウィジェットを再表示
            if hasattr(self, "_hidden_widgets"):
                for widget in self._hidden_widgets:
                    if widget and hasattr(widget, "setVisible"):
                        widget.setVisible(True)
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "debug_show_widget",
                            f"ウィジェットを再表示: {type(widget).__name__}",
                            level="INFO",
                        )

                self._hidden_widgets.clear()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "show_ui_elements",
                    "全てのウィジェットを再表示しました",
                    level="INFO",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_other_ui_elements"},
                AIComponent.KIRO,
            )

    def _position_fullscreen_button(self, parent_window):
        """全画面ボタンの位置を確実に設定する"""
        try:
            if hasattr(self, "fullscreen_button") and self.is_fullscreen_mode:
                # ボタンのサイズを正確に取得
                self.fullscreen_button.adjustSize()
                button_size = self.fullscreen_button.size()

                # 親ウィンドウのサイズを取得
                parent_size = parent_window.size()

                # 右上角に配置(マージン10px)
                x = parent_size.width() - button_size.width() - 10
                y = 10

                # 位置を設定
                self.fullscreen_button.move(x, y)

                # 確実に表示
                self.fullscreen_button.setVisible(True)
                self.fullscreen_button.show()
                self.fullscreen_button.raise_()
                self.fullscreen_button.repaint()

                # デバッグログ
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "position_fullscreen_button",
                    f"全画面ボタン配置: 位置=({x}, {y}), サイズ={button_size}, 親サイズ={parent_size}, 表示状態={self.fullscreen_button.isVisible()}",
                    level="INFO",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "position_fullscreen_button"},
                AIComponent.KIRO,
            )

    def _ensure_ui_visibility(self):
        """UI要素の表示を確実にする(遅延処理用)"""
        try:
            # レイアウトの強制更新
            main_layout = self.layout()
            if main_layout:
                main_layout.activate()
                main_layout.update()

            # ImagePreviewPanel全体のレイアウトを更新
            self.adjustSize()
            self.updateGeometry()
            self.update()
            self.repaint()

            # 全画面ボタンを確実に表示
            if hasattr(self, "fullscreen_button") and self.is_fullscreen_mode:
                # 全画面時のボタン位置を再確認
                parent_window = self.window()
                if parent_window:
                    self._position_fullscreen_button(parent_window)

            # 画像ビューアーも確実に表示
            if hasattr(self, "image_viewer"):
                self.image_viewer.setVisible(True)
                self.image_viewer.show()
                self.image_viewer.update()
                # 画像ビューアーのサイズを親に合わせて調整
                self.image_viewer.adjustSize()
                self.image_viewer.updateGeometry()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "ensure_ui_visibility",
                "UI要素の表示を確実にしました",
                level="INFO",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "ensure_ui_visibility"},
                AIComponent.KIRO,
            )

    def keyPressEvent(self, event):
        """キーイベント"""
        if event.key() == Qt.Key.Key_Escape:
            if self.is_fullscreen_mode:
                # 全画面表示中の場合は通常表示に戻る
                self._exit_fullscreen()
            # 通常表示中のESCキーは何もしない(適切なUI慣例に従う)
        elif event.key() == Qt.Key.Key_F:
            # Fキーで画面フィット
            self._fit_to_screen()
        elif event.key() == Qt.Key.Key_F11:
            # F11キーで全画面表示切り替え
            self._toggle_fullscreen()
        else:
            # その他のキーイベントは親クラスに委譲
            super().keyPressEvent(event)

    def get_current_image_path(self) -> Path | None:
        """現在の画像パスを取得"""
        return self.current_image_path

    def get_zoom_factor(self) -> float:
        """現在のズーム係数を取得"""
        return self.zoom_factor
