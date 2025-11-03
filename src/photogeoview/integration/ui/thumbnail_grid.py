"""
Optimized Thumbnail Grid for AI Integration - 最適化サムネイルグリッド

CursorBLDの高速サムネイル表示とKiroの最適化を組み合わせた
高性能サムネイルグリッドコンポーネント。

主な機能:
- CursorBLD: Qt native高速サムネイル生成と表示
- Kiro: メモリ管理、キャッシュ機能、パフォーマンス監視
- CS4Coding: 正確なEXIFデータ統合と表示
- 非同期サムネイル読み込みによる応答性向上
- 動的ファイルリスト更新対応

技術仕様:
- ThreadPoolExecutorによる並列サムネイル生成
- LRUキャッシュによる効率的なメモリ使用
- QMutexによるスレッドセーフな操作
- 設定可能なサムネイルサイズとグリッド列数
- リアルタイムパフォーマンス監視

UI機能:
- マウスクリック・ダブルクリック・右クリックメニュー対応
- EXIFデータのツールチップ表示
- ローディング・エラー・空状態の適切な表示
- サムネイルサイズのリアルタイム調整

Author: Kiro AI Integration System
"""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QEvent, QMutex, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImage, QImageReader, QPainter, QPixmap
from PySide6.QtWidgets import (
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


class ThumbnailItem(QLabel):
    """
    Individual thumbnail item with Kiro optimization
    """

    clicked = Signal(Path)
    context_menu_requested = Signal(Path, object)  # image_path, position
    exif_info_requested = Signal(Path)

    def __init__(self, image_path: Path, thumbnail_size: int = 150):
        super().__init__()

        self.image_path = image_path
        self.thumbnail_size = thumbnail_size
        self.is_loaded = False
        self.is_loading = False

        # Setup UI
        self.setFixedSize(thumbnail_size + 20, thumbnail_size + 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # テーマ対応のスタイルシートは後で設定
        self.theme_manager = None  # 後で設定される
        self._update_thumbnail_style()

        # Show placeholder
        self._show_placeholder()

    def set_theme_manager(self, theme_manager):
        """テーママネージャーを設定"""
        self.theme_manager = theme_manager
        if theme_manager:
            if hasattr(theme_manager, "theme_changed"):
                theme_manager.theme_changed.connect(self._on_theme_changed)
            elif hasattr(theme_manager, "theme_changed_compat"):
                theme_manager.theme_changed_compat.connect(self._on_theme_changed)
        self._update_thumbnail_style()

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        self._update_thumbnail_style()

    def changeEvent(self, event):  # type: ignore[override]
        """スタイル/パレット変更で再適用（無限ループ防止）"""
        try:
            if event and event.type() in (
                QEvent.Type.PaletteChange,
                QEvent.Type.StyleChange,
                QEvent.Type.ThemeChange,
            ):
                # 無限ループ防止: 現在のスタイルと異なる場合のみ更新
                self._update_thumbnail_style()
        except Exception:
            pass
        finally:
            super().changeEvent(event)

    def _update_thumbnail_style(self):
        """テーマに基づいてスタイルを更新（無限ループ防止版）"""
        try:
            # 現在のスタイルシートを取得
            current_style = self.styleSheet()

            # デフォルト色
            bg_color = "#f8f9fa"
            hover_bg = "#e3f2fd"
            border_color = "#007acc"
            fg_color = "#2c3e50"

            # テーママネージャーから色を取得（利用可能な色キーのみ）
            if self.theme_manager:
                try:
                    # 利用可能な色キーのみを使用
                    bg_color = self.theme_manager.get_color("background", "#f8f9fa")
                    border_color = self.theme_manager.get_color("primary", "#007acc")

                    # ダークテーマかどうかを判定
                    current_theme = self.theme_manager.get_current_theme()
                    if (
                        isinstance(current_theme, str)
                        and "dark" in current_theme.lower()
                    ):
                        # ダークテーマ用の色調整
                        if bg_color.startswith("#") and len(bg_color) == 7:
                            try:
                                r = int(bg_color[1:3], 16)
                                g = int(bg_color[3:5], 16)
                                b = int(bg_color[5:7], 16)
                                # ホバー色を背景より少し明るく
                                hover_r = min(255, int(r * 1.15))
                                hover_g = min(255, int(g * 1.15))
                                hover_b = min(255, int(b * 1.15))
                                hover_bg = f"#{hover_r:02x}{hover_g:02x}{hover_b:02x}"
                                # 前景色を明るく
                                fg_color = "#ecf0f1"
                            except ValueError:
                                pass
                        else:
                            hover_bg = "#4a5568"
                            fg_color = "#ecf0f1"
                    else:
                        # ライトテーマ用の色調整
                        hover_bg = "#e3f2fd"
                        fg_color = "#2c3e50"

                except Exception:
                    # エラー時はデフォルト色を使用（ログ出力は最小限）
                    pass

            new_style = f"""
                QLabel {{
                    border: 2px solid transparent;
                    border-radius: 4px;
                    background-color: {bg_color};
                    color: {fg_color};
                    padding: 4px;
                }}
                QLabel:hover {{
                    border-color: {border_color};
                    background-color: {hover_bg};
                }}
            """

            # 無限ループ防止: 現在のスタイルと異なる場合のみ更新
            if new_style.strip() != current_style.strip():
                self.setStyleSheet(new_style)
        except Exception:
            # エラー時はデフォルトスタイルを適用
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid transparent;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                    padding: 4px;
                }
                QLabel:hover {
                    border-color: #007acc;
                    background-color: #e3f2fd;
                }
            """)

    def _show_placeholder(self):
        """Show placeholder while loading（最適化版）"""

        # テーマに追随したプレースホルダー（シンプル化）
        bg = "#e9ecef"
        text_col = "#6c757d"

        try:
            if self.theme_manager:
                # 利用可能な色キーのみを使用
                bg = self.theme_manager.get_color("background", "#e9ecef")

                # ダークテーマかどうかを判定
                current_theme = self.theme_manager.get_current_theme()
                if isinstance(current_theme, str) and "dark" in current_theme.lower():
                    text_col = "#ecf0f1"  # ダークテーマ用の明るい文字色
                else:
                    text_col = "#6c757d"  # ライトテーマ用の暗い文字色

        except Exception:
            # エラー時はデフォルト色を使用
            pass

        placeholder = QPixmap(self.thumbnail_size, self.thumbnail_size)
        placeholder.fill(QColor(bg))

        # Draw placeholder text
        painter = QPainter(placeholder)
        painter.setPen(QColor(text_col))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "Loading...")
        painter.end()

        self.setPixmap(placeholder)
        self.setText(self.image_path.name)

    def set_thumbnail(self, pixmap: QPixmap):
        """Set the thumbnail pixmap"""

        if pixmap and not pixmap.isNull():
            # Scale pixmap to fit
            scaled_pixmap = pixmap.scaled(
                self.thumbnail_size,
                self.thumbnail_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # デバッグ情報をログ出力
            if hasattr(self, "logger_system") and self.logger_system:
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "thumbnail_set_debug",
                    f"Setting thumbnail: {self.image_path.name}, Original: {pixmap.width()}x{pixmap.height()}, Scaled: {scaled_pixmap.width()}x{scaled_pixmap.height()}",
                    level="DEBUG",
                )

            self.setPixmap(scaled_pixmap)
            self.setText("")  # Clear text
            self.is_loaded = True
        else:
            self._show_error()

    def _show_error(self):
        """Show error placeholder"""
        # テーマに追随したエラープレースホルダー
        err_bg = "#f8d7da"
        err_fg = "#721c24"
        try:
            if self.theme_manager:
                primary_err = self.theme_manager.get_color("error", err_fg)
                err_fg = primary_err
                # 背景はエラー色をやや薄く
                if primary_err.startswith("#") and len(primary_err) == 7:
                    r = int(primary_err[1:3], 16)
                    g = int(primary_err[3:5], 16)
                    b = int(primary_err[5:7], 16)
                    r = min(255, int(r + (255 - r) * 0.8))
                    g = min(255, int(g + (255 - g) * 0.8))
                    b = min(255, int(b + (255 - b) * 0.8))
                    err_bg = f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            pass

        error_pixmap = QPixmap(self.thumbnail_size, self.thumbnail_size)
        error_pixmap.fill(QColor(err_bg))

        painter = QPainter(error_pixmap)
        painter.setPen(QColor(err_fg))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(error_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Error")
        painter.end()

        self.setPixmap(error_pixmap)
        self.setText("Error")

    def set_exif_info(self, exif_data: Dict[str, Any]):
        """Set EXIF information for display"""
        if exif_data:
            # Create tooltip with EXIF info
            tooltip_parts = []
            if "DateTime" in exif_data:
                tooltip_parts.append(f"Date: {exif_data['DateTime']}")
            if "Make" in exif_data and "Model" in exif_data:
                tooltip_parts.append(
                    f"Camera: {exif_data['Make']} {exif_data['Model']}"
                )
            if "ExposureTime" in exif_data:
                tooltip_parts.append(f"Exposure: {exif_data['ExposureTime']}s")
            if "FNumber" in exif_data:
                tooltip_parts.append(f"F-Number: f/{exif_data['FNumber']}")
            if "ISOSpeedRatings" in exif_data:
                tooltip_parts.append(f"ISO: {exif_data['ISOSpeedRatings']}")

            if tooltip_parts:
                self.setToolTip("\n".join(tooltip_parts))

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self.image_path, event.globalPos())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.exif_info_requested.emit(self.image_path)
        super().mouseDoubleClickEvent(event)


class ThumbnailLoader(QObject):
    """
    Asynchronous thumbnail loader with Kiro optimization
    """

    thumbnail_loaded = Signal(Path, QImage)
    loading_progress = Signal(int, int)  # current, total

    def __init__(self, logger_system: LoggerSystem):
        super().__init__()
        self.logger_system = logger_system
        self.cache: Dict[str, QPixmap] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.recent_load_times = []

    def load_thumbnails(self, image_paths: List[Path], thumbnail_size: int):
        """Load thumbnails for the given image paths (I/O thread) - デバッグ版

        - Uses QImageReader with setAutoTransform(True)
        - Reads scaled images directly to avoid loading full-size bitmaps
        - Emits QImage (thread-safe) instead of QPixmap
        - Enhanced debugging for performance analysis
        """
        try:
            total = len(image_paths)
            loaded = 0
            batch_start_time = time.time()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_batch_start",
                f"バッチ処理開始: {total}枚の画像",
                level="DEBUG",
            )

            for i, image_path in enumerate(image_paths):
                item_start_time = time.time()

                # Check cache first
                cache_key = f"{image_path}_{thumbnail_size}"
                if cache_key in self.cache:
                    self.cache_hits += 1
                    self.thumbnail_loaded.emit(image_path, self.cache[cache_key])
                else:
                    self.cache_misses += 1
                    # Load thumbnail as QImage (thread-safe)
                    reader = QImageReader(str(image_path))
                    reader.setAutoTransform(True)

                    # 直接サムネイルサイズで読み込み
                    reader.setScaledSize(QSize(thumbnail_size, thumbnail_size))

                    image = reader.read()
                    if not image.isNull():
                        # デバッグ情報をログ出力
                        if loaded % 5 == 0:  # 5枚ごとにログ出力
                            self.logger_system.log_ai_operation(
                                AIComponent.CURSOR,
                                "thumbnail_generated_debug",
                                f"Thumbnail generated: {image_path.name}, Size: {image.width()}x{image.height()}",
                                level="DEBUG",
                            )

                        # キャッシュに保存してから送信
                        self.cache[cache_key] = image
                        self.thumbnail_loaded.emit(image_path, image)
                    else:
                        # Create error placeholder image
                        err = QImage(
                            thumbnail_size, thumbnail_size, QImage.Format.Format_RGB32
                        )
                        err.fill(QColor("#f8d7da"))
                        self.thumbnail_loaded.emit(image_path, err)

                loaded += 1

                # 進捗イベントの頻度を調整
                if loaded == total or (loaded % 8 == 0):
                    self.loading_progress.emit(loaded, total)

                # 詳細なタイミング情報を記録
                item_load_time = time.time() - item_start_time
                if item_load_time > 1.0:  # 1秒以上かかった場合は警告
                    self.logger_system.log_ai_operation(
                        AIComponent.CURSOR,
                        "thumbnail_slow_load",
                        f"遅いサムネイル読み込み: {image_path.name}, 時間: {item_load_time:.2f}秒",
                        level="WARNING",
                    )

                # Track load time
                if len(self.recent_load_times) < 10:
                    self.recent_load_times.append(item_load_time)
                else:
                    self.recent_load_times[loaded % 10] = item_load_time

            # バッチ処理完了のログ
            batch_total_time = time.time() - batch_start_time
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_batch_complete",
                f"バッチ処理完了: {total}枚, 総時間: {batch_total_time:.2f}秒, 平均: {batch_total_time / total:.3f}秒/枚",
                level="DEBUG",
            )

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_load_error",
                f"Error loading thumbnails: {e!s}",
                level="ERROR",
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        avg_load_time = (
            sum(self.recent_load_times) / len(self.recent_load_times)
            if self.recent_load_times
            else 0
        )

        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "average_load_time": avg_load_time,
            "recent_load_times": self.recent_load_times,
        }

    def clear_cache(self):
        """Clear the thumbnail cache"""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0


class OptimizedThumbnailGrid(QWidget):
    """
    Optimized thumbnail grid with fast loading and EXIF display

    Features:
    - CursorBLD: High-speed thumbnail generation and display
    - Kiro: Memory management, intelligent caching, performance monitoring
    - CS4Coding: Accurate EXIF data integration
    """

    # Signals
    image_selected = Signal(Path)
    thumbnail_requested = Signal(Path)
    exif_display_requested = Signal(Path)
    performance_warning = Signal(str)

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
        theme_manager: Optional[object] = None,
    ):
        """
        Initialize optimized thumbnail grid

        Args:
            config_manager: Configuration manager
            state_manager: State manager
            logger_system: Logging system
            theme_manager: Theme manager for styling
        """
        super().__init__()

        # Core systems
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)
        self.theme_manager = theme_manager

        # テーマ変更シグナルの接続
        if self.theme_manager:
            if hasattr(self.theme_manager, "theme_changed"):
                self.theme_manager.theme_changed.connect(self._on_theme_changed)
            elif hasattr(self.theme_manager, "theme_changed_compat"):
                self.theme_manager.theme_changed_compat.connect(self._on_theme_changed)

        # Grid settings
        try:
            self.thumbnail_size = self.state_manager.get_state_value(
                "thumbnail_size", 150
            )
        except:
            self.thumbnail_size = 150  # デフォルト値
        self.columns = 4
        self.spacing = 10

        # Data storage
        self.image_list: List[Path] = []
        self.thumbnail_items: Dict[Path, ThumbnailItem] = {}
        self.exif_cache: Dict[Path, Dict[str, Any]] = {}

        # Performance tracking
        self.load_start_time = None
        self.loaded_count = 0
        self.total_count = 0
        self.performance_metrics = {
            "avg_load_time": 0.0,
            "cache_hit_rate": 0.0,
            "memory_usage": 0,
        }

        # Threading - 初期化を最初に行う
        self.load_mutex = QMutex()
        # サムネイル読み込み用のワーカー数を大幅に増加（I/O処理の並列化）
        self.thumbnail_executor = ThreadPoolExecutor(
            max_workers=8, thread_name_prefix="thumbnail"
        )
        self.exif_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="exif"
        )

        # UI components initialization
        self.performance_label = None
        self.progress_indicator = None
        # Theme reapply guard
        self._theme_updating = False

        # UI components
        self.scroll_area: Optional[QScrollArea] = None
        self.grid_widget: Optional[QWidget] = None
        self.grid_layout: Optional[QGridLayout] = None
        self.controls_widget: Optional[QWidget] = None

        # Thumbnail loader
        self.thumbnail_loader = ThumbnailLoader(self.logger_system)

        # Initialize UI first
        self._setup_ui()

        # Performance monitoring - UIの後に開始
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._monitor_performance)
        self.performance_timer.start(5000)  # Check every 5 seconds to reduce overhead

        # Connect signals
        self.thumbnail_loader.thumbnail_loaded.connect(self._on_thumbnail_loaded)
        self.thumbnail_loader.loading_progress.connect(self._on_loading_progress)

        self.logger_system.log_ai_operation(
            AIComponent.CURSOR,
            "thumbnail_grid_init",
            "Optimized thumbnail grid initialized",
        )

    def changeEvent(self, event):  # type: ignore[override]
        """Qtの各種変更イベントでテーマを再適用"""
        try:
            if (
                not getattr(self, "_theme_updating", False)
                and event
                and event.type()
                in (
                    QEvent.Type.PaletteChange,
                    QEvent.Type.ApplicationPaletteChange,
                    QEvent.Type.ThemeChange,
                )
            ):
                self._theme_updating = True
                try:
                    self._apply_container_theme()
                    for item in self.thumbnail_items.values():
                        if hasattr(item, "_update_thumbnail_style"):
                            item._update_thumbnail_style()
                finally:
                    self._theme_updating = False
        except Exception:
            pass
        finally:
            super().changeEvent(event)

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            # 既存のサムネイルアイテムのスタイルを更新
            for thumbnail_item in self.thumbnail_items.values():
                if hasattr(thumbnail_item, "_update_thumbnail_style"):
                    thumbnail_item._update_thumbnail_style()

            # コンテナのスタイルを更新
            if hasattr(self, "_apply_container_theme"):
                self._apply_container_theme()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_grid_theme_changed",
                f"Thumbnail grid theme updated: {theme_name}",
            )
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_grid_theme_change", "theme": theme_name},
                AIComponent.CURSOR,
            )

    def _setup_ui(self):
        """Setup the user interface"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            # Controls
            self.controls_widget = self._create_controls()
            try:
                self.controls_widget.setObjectName("thumbnailControls")
            except Exception:
                pass
            layout.addWidget(self.controls_widget)

            # Scroll area for thumbnails
            self.scroll_area = QScrollArea()
            try:
                self.scroll_area.setObjectName("thumbnailScrollArea")
            except Exception:
                pass
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )

            # Grid widget
            self.grid_widget = QWidget()
            try:
                self.grid_widget.setObjectName("thumbnailGridContainer")
            except Exception:
                pass
            self.grid_layout = QGridLayout(self.grid_widget)
            self.grid_layout.setSpacing(self.spacing)
            self.grid_layout.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )

            self.scroll_area.setWidget(self.grid_widget)
            layout.addWidget(self.scroll_area)

            # 初期テーマ適用
            self._apply_container_theme()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "setup_ui"}, AIComponent.CURSOR
            )

    def _apply_container_theme(self):
        """テーマに応じてスクロールエリアやコントロールの背景/色を調整"""
        try:
            bg = "#ffffff"
            fg = "#000000"
            border = "#dee2e6"
            if self.theme_manager:
                bg = self.theme_manager.get_color("background", bg)
                fg = self.theme_manager.get_color("foreground", fg)
                border = self.theme_manager.get_color("border", border)

            if self.controls_widget:
                self.controls_widget.setStyleSheet(
                    f"QWidget#thumbnailControls {{ background-color: {bg}; color: {fg}; }}"
                )

            if self.scroll_area:
                self.scroll_area.setStyleSheet(
                    f"QScrollArea#thumbnailScrollArea {{ background-color: {bg}; border: 1px solid {border}; }}"
                )

            if self.grid_widget:
                self.grid_widget.setStyleSheet(
                    f"QWidget#thumbnailGridContainer {{ background-color: {bg}; color: {fg}; }}"
                )
        except Exception:
            pass

    def _create_controls(self) -> QWidget:
        """Create control widgets"""
        controls = QWidget()
        layout = QHBoxLayout(controls)

        # Thumbnail size control
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

        # Connect slider and spinbox
        size_slider.valueChanged.connect(size_spinbox.setValue)
        size_spinbox.valueChanged.connect(size_slider.setValue)

        layout.addStretch()

        # Performance info
        self.performance_label = QLabel("Ready")
        layout.addWidget(self.performance_label)

        return controls

    def set_image_list(self, image_list: List[Path]):
        """Set the list of images to display"""
        try:
            # 基本的な設定
            self.image_list = image_list
            self.total_count = len(image_list)
            self.loaded_count = 0
            self.load_start_time = time.time()

            # Clear existing thumbnails
            self.clear_thumbnails_safely()

            # Create thumbnail items
            self._create_thumbnail_items()

            # Start loading thumbnails
            self._load_thumbnails_async()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "image_list_set",
                f"Image list set with {len(image_list)} images",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_image_list", "count": len(image_list)},
                AIComponent.CURSOR,
            )

    def clear_thumbnails_safely(self):
        """
        既存のサムネイルを安全にクリアする
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnails_clear_start",
                f"サムネイルクリア開始: {len(self.thumbnail_items)}個のアイテム",
                level="DEBUG",
            )

            # 既存のサムネイルアイテムを削除
            for image_path, thumbnail_item in self.thumbnail_items.items():
                try:
                    # レイアウトから削除
                    self.grid_layout.removeWidget(thumbnail_item)
                    # ウィジェットを削除
                    thumbnail_item.deleteLater()
                except Exception as item_error:
                    self.logger_system.log_ai_operation(
                        AIComponent.CURSOR,
                        "thumbnail_item_clear_error",
                        f"サムネイルアイテム削除エラー: {image_path} - {item_error!s}",
                        level="WARNING",
                    )

            # 辞書をクリア
            self.thumbnail_items.clear()

            # EXIFキャッシュもクリア
            self.exif_cache.clear()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnails_clear_complete",
                "サムネイルクリア完了",
                level="DEBUG",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {
                    "operation": "clear_thumbnails_safely",
                    "user_action": "サムネイル安全クリア",
                },
                AIComponent.CURSOR,
            )

    def _create_thumbnail_items(self):
        """Create thumbnail items in grid layout"""
        try:
            # Calculate columns based on widget width
            widget_width = self.scroll_area.viewport().width()
            item_width = self.thumbnail_size + 20 + self.spacing
            self.columns = max(1, widget_width // item_width)

            # Create thumbnail items
            for i, image_path in enumerate(self.image_list):
                row = i // self.columns
                col = i % self.columns

                # Create thumbnail item
                thumbnail_item = ThumbnailItem(image_path, self.thumbnail_size)
                thumbnail_item.set_theme_manager(
                    self.theme_manager
                )  # テーママネージャーを設定
                thumbnail_item.clicked.connect(self._on_thumbnail_clicked)

                # Add to layout
                self.grid_layout.addWidget(thumbnail_item, row, col)

                # Store reference
                self.thumbnail_items[image_path] = thumbnail_item

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_thumbnail_items"},
                AIComponent.CURSOR,
            )

    def _load_thumbnails_async(self):
        """Load thumbnails asynchronously with progressive loading"""
        try:
            if self.image_list:
                # 段階的な読み込みでUI応答性を向上
                # 最初に表示可能な範囲（画面に表示される分）を優先読み込み
                visible_count = min(32, len(self.image_list))
                preload = self.image_list[:visible_count]

                # デバッグ情報をログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "thumbnail_loading_start",
                    f"サムネイル読み込み開始: {len(self.image_list)}枚, 最初のバッチ: {len(preload)}枚",
                    level="DEBUG",
                )

                # 最初のバッチを読み込み
                future = self.thumbnail_executor.submit(
                    self.thumbnail_loader.load_thumbnails, preload, self.thumbnail_size
                )
                future.add_done_callback(self._on_loading_complete)

                # 残りの画像をバックグラウンドで段階的に読み込み
                if len(self.image_list) > visible_count:
                    self._schedule_background_loading(visible_count)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_thumbnails_async"},
                AIComponent.CURSOR,
            )

    def _on_thumbnail_clicked(self, image_path: Path):
        """Handle thumbnail click"""
        try:
            # Update state
            self.state_manager.update_state(selected_image=image_path)

            # Emit signal
            self.image_selected.emit(image_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_click",
                f"Thumbnail clicked: {image_path.name}",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_click", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_thumbnail_loaded(self, image_path: Path, image: QImage):
        """Handle thumbnail loaded"""
        try:
            if image_path in self.thumbnail_items:
                thumbnail_item = self.thumbnail_items[image_path]
                # QPixmapはGUIスレッドで生成
                pixmap = QPixmap.fromImage(image)

                # デバッグ情報をログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "thumbnail_loaded_debug",
                    f"Thumbnail loaded: {image_path.name}, Image size: {image.width()}x{image.height()}, Pixmap valid: {not pixmap.isNull()}",
                    level="DEBUG",
                )

                thumbnail_item.set_thumbnail(pixmap)
                self.loaded_count += 1

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_loaded", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _on_loading_progress(self, current: int, total: int):
        """Handle loading progress"""
        try:
            if hasattr(self, "performance_label") and self.performance_label:
                self.performance_label.setText(f"読み込み中... {current}/{total}")

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "loading_progress_error",
                f"Progress update error: {e!s}",
                level="WARNING",
            )

    def _on_loading_complete(self, future):
        """Handle loading completion"""
        try:
            if hasattr(self, "performance_label") and self.performance_label:
                self.performance_label.setText(
                    f"読み込み中: {self.loaded_count}/{self.total_count}"
                )

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_load_complete",
                f"Loaded {self.loaded_count} thumbnails",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "loading_complete"},
                AIComponent.CURSOR,
            )

    def _schedule_background_loading(self, start_index: int):
        """Schedule background loading of remaining thumbnails"""
        try:
            remaining_images = self.image_list[start_index:]
            if not remaining_images:
                return

            # 残りの画像を小さなバッチに分けて読み込み
            batch_size = 16
            for i in range(0, len(remaining_images), batch_size):
                batch = remaining_images[i : i + batch_size]

                # 少し遅延を入れて読み込み（UI応答性を保つため）
                QTimer.singleShot(i * 100, lambda b=batch: self._load_batch_async(b))

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "schedule_background_loading"},
                AIComponent.CURSOR,
            )

    def _load_batch_async(self, image_batch: List[Path]):
        """Load a batch of thumbnails asynchronously"""
        try:
            if image_batch:
                future = self.thumbnail_executor.submit(
                    self.thumbnail_loader.load_thumbnails,
                    image_batch,
                    self.thumbnail_size,
                )
                future.add_done_callback(self._on_batch_complete)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "load_batch_async"},
                AIComponent.CURSOR,
            )

    def _on_batch_complete(self, future):
        """Handle batch loading completion"""
        try:
            if hasattr(self, "performance_label") and self.performance_label:
                self.performance_label.setText(
                    f"読み込み中: {self.loaded_count}/{self.total_count}"
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "batch_complete"},
                AIComponent.CURSOR,
            )

    def _on_size_changed(self, size: int):
        """Handle thumbnail size change"""
        try:
            self.thumbnail_size = size

            # Update configuration
            self.config_manager.set_setting("ui.thumbnail_size", size)

            # Update state
            self.state_manager.update_state(thumbnail_size=size)

            # Reload thumbnails with new size (無限ループ防止)
            if self.image_list:
                # 既存のサムネイルをクリアして再作成
                self.clear_thumbnails_safely()
                self._create_thumbnail_items()
                self._load_thumbnails_async()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "size_change", "size": size},
                AIComponent.CURSOR,
            )

    def _monitor_performance(self):
        """Monitor performance and emit warnings if needed"""
        try:
            # Check memory usage
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            self.performance_metrics["memory_usage"] = memory_mb

            # Check for performance issues
            if memory_mb > 500:  # 500MB threshold
                self.performance_warning.emit(f"High memory usage: {memory_mb:.1f}MB")

            # Check loading performance
            if (
                self.total_count > 0
                and self.loaded_count < self.total_count
                and self.performance_metrics["avg_load_time"] > 30
            ):  # 30 seconds threshold
                self.performance_warning.emit("Slow thumbnail loading detected")

        except Exception:
            # Don't log performance monitoring errors to avoid spam
            pass

    def show_loading_state(self, message: str = "読み込み中..."):
        """Show loading state"""
        try:
            # Clear existing thumbnails but preserve grid layout
            self.clear_thumbnails_safely()

            # Create loading state widget and add to grid
            loading_widget = QWidget()
            loading_layout = QVBoxLayout(loading_widget)
            loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Loading icon
            loading_icon = QLabel("⏳")
            loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 64px;
                    color: #007acc;
                    margin: 30px;
                }
            """
            )
            loading_layout.addWidget(loading_icon)

            # Loading message
            loading_title = QLabel(message)
            loading_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_title.setStyleSheet(
                """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #007acc;
                    margin: 10px;
                }
            """
            )
            loading_layout.addWidget(loading_title)

            # Add loading widget to grid layout instead of replacing scroll area content
            if self.grid_layout:
                self.grid_layout.addWidget(
                    loading_widget, 0, 0, 1, -1
                )  # Span all columns

        except Exception as e:
            self.logger_system.error(f"Loading state display error: {e}")

    def show_error_state(self, message: str = "エラーが発生しました"):
        """Show error state"""
        try:
            # Clear existing thumbnails but preserve grid layout
            self.clear_thumbnails_safely()

            # Create error state widget
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Error icon
            error_icon = QLabel("❌")
            error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 64px;
                    color: #dc3545;
                    margin: 30px;
                }
            """
            )
            error_layout.addWidget(error_icon)

            # Error message
            error_title = QLabel(message)
            error_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_title.setStyleSheet(
                """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #dc3545;
                    margin: 10px;
                }
            """
            )
            error_layout.addWidget(error_title)

            # Add error widget to grid layout instead of replacing scroll area content
            if self.grid_layout:
                self.grid_layout.addWidget(
                    error_widget, 0, 0, 1, -1
                )  # Span all columns

        except Exception as e:
            self.logger_system.error(f"Error state display error: {e}")

    def show_empty_state(self):
        """Show empty state when no images are found"""
        try:
            # Clear existing thumbnails
            self.clear_thumbnails_safely()

            # Create empty state widget
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Empty state icon
            empty_icon = QLabel("📁")
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 64px;
                    color: #6c757d;
                    margin: 30px;
                }
            """
            )
            empty_layout.addWidget(empty_icon)

            # Empty state message
            empty_title = QLabel("画像ファイルが見つかりません")
            empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_title.setStyleSheet(
                """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #495057;
                    margin: 10px;
                }
            """
            )
            empty_layout.addWidget(empty_title)

            # Helpful message
            empty_message = QLabel(
                "このフォルダには対応する画像ファイル（JPG、PNG、GIF、BMP、TIFF、WEBP）がありません。\n別のフォルダを選択してください。"
            )
            empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_message.setWordWrap(True)
            empty_message.setStyleSheet(
                """
                QLabel {
                    font-size: 14px;
                    color: #6c757d;
                    margin: 10px;
                    padding: 15px;
                    max-width: 500px;
                    line-height: 1.4;
                }
            """
            )
            empty_layout.addWidget(empty_message)

            # Add to grid layout
            self.grid_layout.addWidget(empty_widget, 0, 0, 1, self.columns)

            # Update performance label
            if hasattr(self, "performance_label"):
                self.performance_label.setText("画像ファイルがありません")

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "show_empty_state_complete", "Empty state displayed"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_empty_state"},
                AIComponent.CURSOR,
            )

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(
                f"サムネイルグリッド: テーマ変更を検出 - {theme_name}"
            )

            # 全てのサムネイルアイテムにテーママネージャーを設定
            for thumbnail_item in self.thumbnail_items:
                thumbnail_item.set_theme_manager(self.theme_manager)

            # 空状態表示のスタイルも更新
            self._update_empty_state_style()

        except Exception as e:
            self.logger_system.error(f"サムネイルグリッドのテーマ変更処理でエラー: {e}")

    def _update_empty_state_style(self):
        """空状態表示のスタイルを更新"""
        try:
            if hasattr(self, "empty_state_label"):
                # テーママネージャーから色を取得
                text_color = "#7f8c8d"
                bg_color = "#ffffff"

                if self.theme_manager:
                    try:
                        text_color = self.theme_manager.get_color(
                            "secondary", "#7f8c8d"
                        )
                        bg_color = self.theme_manager.get_color("background", "#ffffff")
                    except Exception:
                        pass  # デフォルト色を使用

                self.empty_state_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {bg_color};
                        font-size: 16px;
                        font-style: italic;
                        padding: 40px;
                        border-radius: 8px;
                    }}
                """)
        except Exception as e:
            self.logger_system.error(f"空状態スタイル更新でエラー: {e}")

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(
                f"サムネイルグリッド: テーマ変更を検出 - {theme_name}"
            )

            # 全てのサムネイルアイテムにテーママネージャーを設定
            for thumbnail_item in self.thumbnail_items:
                thumbnail_item.set_theme_manager(self.theme_manager)

            # 空状態表示のスタイルも更新
            self._update_empty_state_style()

        except Exception as e:
            self.logger_system.error(f"サムネイルグリッドのテーマ変更処理でエラー: {e}")

    def _update_empty_state_style(self):
        """空状態表示のスタイルを更新"""
        try:
            if hasattr(self, "empty_state_label"):
                # テーママネージャーから色を取得
                text_color = "#7f8c8d"
                bg_color = "#ffffff"

                if self.theme_manager:
                    try:
                        text_color = self.theme_manager.get_color(
                            "secondary", "#7f8c8d"
                        )
                        bg_color = self.theme_manager.get_color("background", "#ffffff")
                    except Exception:
                        pass  # デフォルト色を使用

                self.empty_state_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {bg_color};
                        font-size: 16px;
                        font-style: italic;
                        padding: 40px;
                        border-radius: 8px;
                    }}
                """)
        except Exception as e:
            self.logger_system.error(f"空状態スタイル更新でエラー: {e}")

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(
                f"サムネイルグリッド: テーマ変更を検出 - {theme_name}"
            )

            # 全てのサムネイルアイテムにテーママネージャーを設定
            for thumbnail_item in self.thumbnail_items:
                thumbnail_item.set_theme_manager(self.theme_manager)

            # 空状態表示のスタイルも更新
            self._update_empty_state_style()

        except Exception as e:
            self.logger_system.error(f"サムネイルグリッドのテーマ変更処理でエラー: {e}")

    def _update_empty_state_style(self):
        """空状態表示のスタイルを更新"""
        try:
            if hasattr(self, "empty_state_label"):
                # テーママネージャーから色を取得
                text_color = "#7f8c8d"
                bg_color = "#ffffff"

                if self.theme_manager:
                    try:
                        text_color = self.theme_manager.get_color(
                            "secondary", "#7f8c8d"
                        )
                        bg_color = self.theme_manager.get_color("background", "#ffffff")
                    except Exception:
                        pass  # デフォルト色を使用

                self.empty_state_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {bg_color};
                        font-size: 16px;
                        font-style: italic;
                        padding: 40px;
                        border-radius: 8px;
                    }}
                """)
        except Exception as e:
            self.logger_system.error(f"空状態スタイル更新でエラー: {e}")

    def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop performance monitoring
            if self.performance_timer:
                self.performance_timer.stop()

            # Shutdown thread pools
            self.thumbnail_executor.shutdown(wait=False)
            self.exif_executor.shutdown(wait=False)

            # Clear data safely
            self.clear_thumbnails_safely()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "thumbnail_grid_cleanup",
                "Thumbnail grid cleaned up",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "cleanup"}, AIComponent.CURSOR
            )
