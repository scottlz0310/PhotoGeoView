"""
Image Viewer Module for PhotoGeoView
Provides image display with zoom, pan, and navigation capabilities
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QPixmap, QWheelEvent, QMouseEvent, QPainter, QColor,
    QPaintEvent, QCursor, QFont, QKeyEvent
)
from pathlib import Path
from typing import Optional

from src.core.logger import get_logger

logger = get_logger(__name__)


class ImageDisplayWidget(QLabel):
    """
    Custom image display widget with zoom and pan capabilities
    """

    # Signals
    image_clicked = pyqtSignal(QPoint)  # Mouse click position
    zoom_changed = pyqtSignal(float)    # Current zoom level

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Image properties
        self.original_pixmap: Optional[QPixmap] = None
        self.scaled_pixmap: Optional[QPixmap] = None
        self.zoom_factor: float = 1.0
        self.min_zoom: float = 0.1
        self.max_zoom: float = 10.0

        # Pan properties
        self.pan_start: Optional[QPoint] = None
        self.image_offset: QPoint = QPoint(0, 0)
        self.is_panning: bool = False

        # Widget setup
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 1px solid #555555;
            }
        """)

        # Enable mouse tracking for pan operations
        self.setMouseTracking(True)

        # Default image
        self.set_placeholder()

        logger.debug("ImageDisplayWidget initialized")

    def set_placeholder(self) -> None:
        """Set placeholder when no image is loaded"""
        placeholder = QPixmap(400, 300)
        placeholder.fill(QColor("#3a3a3a"))

        painter = QPainter(placeholder)
        painter.setPen(QColor("#888888"))

        font = QFont()
        font.setPointSize(16)
        painter.setFont(font)

        painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter,
                        "No image selected\nSelect an image to view")
        painter.end()

        self.setPixmap(placeholder)
        self.original_pixmap = None
        self.scaled_pixmap = None

    def load_image(self, image_path: str) -> bool:
        """Load and display an image"""
        try:
            path_obj = Path(image_path)
            if not path_obj.exists():
                logger.error(f"Image file not found: {image_path}")
                return False

            # Load pixmap
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                logger.error(f"Failed to load image: {image_path}")
                return False

            self.original_pixmap = pixmap
            self.zoom_factor = 1.0
            self.image_offset = QPoint(0, 0)

            # Fit to widget size initially
            self.fit_to_window()

            logger.info(f"Loaded image: {path_obj.name} ({pixmap.width()}x{pixmap.height()})")
            return True

        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            self.set_placeholder()
            return False

    def fit_to_window(self) -> None:
        """Fit image to current widget size"""
        if not self.original_pixmap:
            return

        widget_size = self.size()
        image_size = self.original_pixmap.size()

        # サイズが0の場合は処理しない（レイアウト未完了の可能性）
        if widget_size.width() <= 0 or widget_size.height() <= 0:
            return
        if image_size.width() <= 0 or image_size.height() <= 0:
            return

        # Calculate zoom factor to fit image in widget
        scale_x = widget_size.width() / image_size.width()
        scale_y = widget_size.height() / image_size.height()

        # Use smaller scale to fit entirely
        self.zoom_factor = min(scale_x, scale_y, 1.0)  # Don't zoom in by default
        self.image_offset = QPoint(0, 0)

        self.update_display()
        self.zoom_changed.emit(self.zoom_factor)

    def zoom_to(self, zoom_factor: float) -> None:
        """Set specific zoom level"""
        if not self.original_pixmap:
            return

        # Clamp zoom factor to valid range
        zoom_factor = max(self.min_zoom, min(self.max_zoom, zoom_factor))

        if zoom_factor != self.zoom_factor:
            self.zoom_factor = zoom_factor
            self.update_display()
            self.zoom_changed.emit(self.zoom_factor)

    def zoom_in(self) -> None:
        """Zoom in by 25%"""
        self.zoom_to(self.zoom_factor * 1.25)

    def zoom_out(self) -> None:
        """Zoom out by 20%"""
        self.zoom_to(self.zoom_factor * 0.8)

    def reset_zoom(self) -> None:
        """Reset zoom to 100%"""
        self.zoom_to(1.0)

    def update_display(self) -> None:
        """Update the displayed image with current zoom and pan"""
        if not self.original_pixmap:
            return

        # Calculate scaled size
        original_size = self.original_pixmap.size()
        scaled_width = int(original_size.width() * self.zoom_factor)
        scaled_height = int(original_size.height() * self.zoom_factor)

        # Scale the pixmap
        self.scaled_pixmap = self.original_pixmap.scaled(
            QSize(scaled_width, scaled_height),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Update display
        self.setPixmap(self.scaled_pixmap)
        self.update()

    def wheelEvent(self, a0: Optional[QWheelEvent]) -> None:
        """Handle mouse wheel for zooming"""
        if not a0:
            return

        if not self.original_pixmap:
            super().wheelEvent(a0)
            return

        # Get wheel delta
        delta = a0.angleDelta().y()
        zoom_in = delta > 0

        # Calculate new zoom factor
        zoom_multiplier = 1.1 if zoom_in else 0.9
        new_zoom = self.zoom_factor * zoom_multiplier

        # Apply zoom
        self.zoom_to(new_zoom)

        a0.accept()

    def mousePressEvent(self, ev: Optional[QMouseEvent]) -> None:
        """Handle mouse press for panning"""
        if not ev:
            return

        if ev.button() == Qt.MouseButton.LeftButton:
            if self.original_pixmap and self.zoom_factor > 1.0:
                # Start panning
                self.pan_start = ev.position().toPoint()
                self.is_panning = True
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

            # Emit click signal
            self.image_clicked.emit(ev.position().toPoint())

        ev.accept()

    def mouseMoveEvent(self, ev: Optional[QMouseEvent]) -> None:
        """Handle mouse move for panning"""
        if not ev:
            return

        if self.is_panning and self.pan_start is not None:
            # Calculate pan offset
            current_pos = ev.position().toPoint()
            delta = current_pos - self.pan_start

            # Update image offset
            self.image_offset += delta
            self.pan_start = current_pos

            # Update display
            self.update()

        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: Optional[QMouseEvent]) -> None:
        """Handle mouse release to stop panning"""
        if not ev:
            return

        if self.is_panning:
            self.is_panning = False
            self.pan_start = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseReleaseEvent(ev)

    def keyPressEvent(self, ev: Optional[QKeyEvent]) -> None:
        """Handle keyboard events - delegate navigation to parent"""
        if not ev:
            return

        # Delegate navigation keys to parent ImageViewer
        key = ev.key()
        if key in [Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
                   Qt.Key.Key_Space, Qt.Key.Key_Backspace, Qt.Key.Key_Home, Qt.Key.Key_End,
                   Qt.Key.Key_Escape]:  # ESCキーも親に委譲
            # Ignore navigation keys - let the parent ImageViewer handle them
            ev.ignore()
            return

        # Handle zoom keys directly
        if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            self.zoom_in()
            ev.accept()
        elif key == Qt.Key.Key_Minus:
            self.zoom_out()
            ev.accept()
        elif key == Qt.Key.Key_0:
            self.reset_zoom()
            ev.accept()
        else:
            super().keyPressEvent(ev)

    def paintEvent(self, a0: Optional[QPaintEvent]) -> None:
        """Custom paint event for panning support"""
        if not a0:
            return

        super().paintEvent(a0)

        if self.scaled_pixmap and not self.image_offset.isNull():
            painter = QPainter(self)

            # Calculate image position with offset
            widget_rect = self.rect()
            pixmap_rect = self.scaled_pixmap.rect()

            # Center the image by default
            x = (widget_rect.width() - pixmap_rect.width()) // 2 + self.image_offset.x()
            y = (widget_rect.height() - pixmap_rect.height()) // 2 + self.image_offset.y()

            # Draw the image with offset
            painter.drawPixmap(x, y, self.scaled_pixmap)

    def get_zoom_factor(self) -> float:
        """Get current zoom factor"""
        return self.zoom_factor

    def has_image(self) -> bool:
        """Check if an image is currently loaded"""
        return self.original_pixmap is not None


class ImageViewer(QWidget):
    """
    Complete image viewer widget with controls
    """

    # Signals
    image_changed = pyqtSignal(str)     # Current image path
    fullscreen_requested = pyqtSignal()  # Request fullscreen mode
    escape_pressed = pyqtSignal()        # Escape key pressed

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logger

        # Current image info
        self.current_image: str = ""
        self.image_list: list[str] = []
        self.current_index: int = -1

        # UI components
        self.image_display: ImageDisplayWidget
        self.zoom_slider: QSlider
        self.zoom_label: QLabel
        self.nav_buttons: dict[str, QPushButton] = {}

        # フォーカス設定
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setup_ui()
        self.setup_connections()

        self.logger.debug("ImageViewer initialized")

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title bar with fullscreen button
        title_layout = QHBoxLayout()

        title_label = QLabel("🖼️ Image Viewer")
        title_label.setStyleSheet("font-weight: bold; padding: 2px;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Fullscreen button
        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setToolTip("Fullscreen view")
        fullscreen_btn.setFixedSize(24, 24)
        fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)
        title_layout.addWidget(fullscreen_btn)

        layout.addLayout(title_layout)

        # Main image display
        self.image_display = ImageDisplayWidget()
        self.image_display.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.image_display, 1)

        # Control panel
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        controls_frame.setMaximumHeight(60)

        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        # Navigation buttons
        self.nav_buttons['prev'] = QPushButton("⮜")
        self.nav_buttons['prev'].setToolTip("Previous image")
        self.nav_buttons['prev'].clicked.connect(self.previous_image)
        controls_layout.addWidget(self.nav_buttons['prev'])

        self.nav_buttons['next'] = QPushButton("⮞")
        self.nav_buttons['next'].setToolTip("Next image")
        self.nav_buttons['next'].clicked.connect(self.next_image)
        controls_layout.addWidget(self.nav_buttons['next'])

        controls_layout.addWidget(QFrame())  # Separator

        # Zoom controls
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setToolTip("Zoom out")
        zoom_out_btn.clicked.connect(self.image_display.zoom_out)
        controls_layout.addWidget(zoom_out_btn)

        # Zoom slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)   # 10% min zoom
        self.zoom_slider.setMaximum(1000) # 1000% max zoom
        self.zoom_slider.setValue(100)    # 100% default
        self.zoom_slider.setToolTip("Zoom level")
        controls_layout.addWidget(self.zoom_slider)

        zoom_in_btn = QPushButton("＋")
        zoom_in_btn.setToolTip("Zoom in")
        zoom_in_btn.clicked.connect(self.image_display.zoom_in)
        controls_layout.addWidget(zoom_in_btn)

        # Zoom label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.zoom_label)

        controls_layout.addWidget(QFrame())  # Separator

        # Fit controls
        fit_btn = QPushButton("🔲")
        fit_btn.setToolTip("Fit to window")
        fit_btn.clicked.connect(self.image_display.fit_to_window)
        controls_layout.addWidget(fit_btn)

        reset_btn = QPushButton("1:1")
        reset_btn.setToolTip("Actual size (100%)")
        reset_btn.clicked.connect(self.image_display.reset_zoom)
        controls_layout.addWidget(reset_btn)

        layout.addWidget(controls_frame)

        # Initial state
        self.update_navigation_buttons()

        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.logger.debug("ImageViewer UI setup complete")

    def setup_connections(self) -> None:
        """Setup signal connections"""
        try:
            # Image display connections
            self.image_display.zoom_changed.connect(self.on_zoom_changed)

            # Zoom slider connection
            self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)

            self.logger.debug("ImageViewer connections established")

        except Exception as e:
            self.logger.error(f"Error setting up ImageViewer connections: {e}")

    def load_image(self, image_path: str) -> None:
        """Load a single image"""
        try:
            if self.image_display.load_image(image_path):
                self.current_image = image_path
                self.current_index = -1
                self.image_list = [image_path]

                self.update_navigation_buttons()
                self.image_changed.emit(image_path)

                # フォーカスを設定してキー入力を受け取れるようにする
                self.setFocus()

                self.logger.info(f"Loaded single image: {Path(image_path).name}")

        except Exception as e:
            self.logger.error(f"Error loading image: {e}")

    def set_image_list(self, image_list: list[str], current_index: int = 0) -> None:
        """Set list of images for navigation"""
        try:
            self.image_list = image_list.copy()

            if 0 <= current_index < len(self.image_list):
                self.current_index = current_index
                self.load_current_image()
            else:
                self.current_index = -1
                self.current_image = ""
                self.image_display.set_placeholder()

            self.update_navigation_buttons()

            self.logger.info(f"Set image list with {len(image_list)} images")

        except Exception as e:
            self.logger.error(f"Error setting image list: {e}")

    def load_current_image(self) -> None:
        """Load the currently selected image from the list"""
        try:
            if 0 <= self.current_index < len(self.image_list):
                image_path = self.image_list[self.current_index]
                if self.image_display.load_image(image_path):
                    self.current_image = image_path
                    self.image_changed.emit(image_path)

                    # フォーカスを設定してキー入力を受け取れるようにする
                    self.setFocus()

        except Exception as e:
            self.logger.error(f"Error loading current image: {e}")

    def previous_image(self) -> None:
        """Navigate to previous image"""
        self.logger.debug(f"previous_image called: list_len={len(self.image_list)}, current_index={self.current_index}")
        if len(self.image_list) > 1 and self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
            self.update_navigation_buttons()
            self.logger.debug(f"Moved to previous image: index={self.current_index}")
        else:
            self.logger.debug("Cannot go to previous image")

    def next_image(self) -> None:
        """Navigate to next image"""
        self.logger.debug(f"next_image called: list_len={len(self.image_list)}, current_index={self.current_index}")
        if len(self.image_list) > 1 and self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_current_image()
            self.update_navigation_buttons()
            self.logger.debug(f"Moved to next image: index={self.current_index}")
        else:
            self.logger.debug("Cannot go to next image")

    def update_navigation_buttons(self) -> None:
        """Update navigation button states"""
        has_prev = len(self.image_list) > 1 and self.current_index > 0
        has_next = len(self.image_list) > 1 and self.current_index < len(self.image_list) - 1

        self.nav_buttons['prev'].setEnabled(has_prev)
        self.nav_buttons['next'].setEnabled(has_next)

        self.logger.debug(f"Navigation buttons updated: prev={has_prev}, next={has_next} (list_len={len(self.image_list)}, index={self.current_index})")

    def on_zoom_changed(self, zoom_factor: float) -> None:
        """Handle zoom factor changes"""
        try:
            # Update zoom label
            zoom_percent = int(zoom_factor * 100)
            self.zoom_label.setText(f"{zoom_percent}%")

            # Update zoom slider (avoid recursive signals)
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(zoom_percent)
            self.zoom_slider.blockSignals(False)

        except Exception as e:
            self.logger.error(f"Error handling zoom change: {e}")

    def on_zoom_slider_changed(self, value: int) -> None:
        """Handle zoom slider changes"""
        try:
            zoom_factor = value / 100.0
            self.image_display.zoom_to(zoom_factor)

        except Exception as e:
            self.logger.error(f"Error handling zoom slider change: {e}")

    def clear_image(self) -> None:
        """Clear the current image"""
        self.current_image = ""
        self.image_list.clear()
        self.current_index = -1

        self.image_display.set_placeholder()
        self.update_navigation_buttons()

        self.logger.debug("Image viewer cleared")

    def get_current_image(self) -> str:
        """Get the current image path"""
        return self.current_image

    def has_image(self) -> bool:
        """Check if an image is currently loaded"""
        return self.image_display.has_image()

    def keyPressEvent(self, a0: Optional[QKeyEvent]) -> None:
        """Handle keyboard navigation"""
        if not a0:
            return

        key = a0.key()
        self.logger.debug(f"ImageViewer received key: {key}")

        if key == Qt.Key.Key_Left or key == Qt.Key.Key_Up:
            # Previous image
            if self.nav_buttons['prev'].isEnabled():
                self.previous_image()
            a0.accept()

        elif key == Qt.Key.Key_Right or key == Qt.Key.Key_Down:
            # Next image
            if self.nav_buttons['next'].isEnabled():
                self.next_image()
            a0.accept()

        elif key == Qt.Key.Key_Space:
            # Next image with space
            if self.nav_buttons['next'].isEnabled():
                self.next_image()
            a0.accept()

        elif key == Qt.Key.Key_Backspace:
            # Previous image with backspace
            if self.nav_buttons['prev'].isEnabled():
                self.previous_image()
            a0.accept()

        elif key == Qt.Key.Key_Home:
            # First image
            if len(self.image_list) > 1:
                self.current_index = 0
                self.load_current_image()
                self.update_navigation_buttons()
            a0.accept()

        elif key == Qt.Key.Key_End:
            # Last image
            if len(self.image_list) > 1:
                self.current_index = len(self.image_list) - 1
                self.load_current_image()
                self.update_navigation_buttons()
            a0.accept()

        elif key == Qt.Key.Key_Escape:
            # Escape key - emit signal for parent to handle
            self.logger.info("ImageViewer: ESCキーが押されました - シグナル発行")
            self.escape_pressed.emit()
            self.logger.info("ImageViewer: escape_pressed シグナルを発行しました")
            a0.accept()

        else:
            super().keyPressEvent(a0)
