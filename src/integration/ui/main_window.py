"""
Integrated Main Window for AI Integration

Combines CursorBLD's main window layout with Kiro optimization:
- CursorBLD: UI layout, toolbar, theme integration
- Kiro: Performance monitoring, memory management, error handling

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent, ApplicationState, PerformanceMetrics
from ..services.file_discovery_service import FileDiscoveryService
from ..services.file_system_watcher import FileSystemWatcher
from ..state_manager import StateManager

# from .folder_navigator import EnhancedFolderNavigator  # Removed: Using breadcrumb navigation instead
from .simple_thumbnail_grid import SimpleThumbnailGrid

# Import theme manager and breadcrumb components
try:
    from ...ui.breadcrumb_bar import BreadcrumbAddressBar
    from ...ui.theme_manager_simple import SimpleThemeManager
except ImportError:
    # Fallback import paths
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from ui.breadcrumb_bar import BreadcrumbAddressBar
        from ui.theme_manager_simple import SimpleThemeManager
    except ImportError:
        # Create mock classes if imports fail
        from PySide6.QtCore import QObject, Signal

        class SimpleThemeManager(QObject):
            theme_changed = Signal(str, str)
            theme_applied = Signal(str)
            theme_error = Signal(str, str)

            def __init__(self, *args, **kwargs):
                super().__init__()

            def apply_theme(self, theme_name):
                return False

            def get_available_themes(self):
                return ["light", "dark"]

            def get_current_theme(self):
                return "light"

        class BreadcrumbAddressBar(QObject):
            path_changed = Signal(object)
            segment_clicked = Signal(int, object)
            navigation_requested = Signal(object)
            breadcrumb_error = Signal(str, str)

            def __init__(self, *args, **kwargs):
                super().__init__()

            def get_widget(self):
                return None

            def set_current_path(self, path):
                return False


class IntegratedMainWindow(QMainWindow):
    """
    Integrated main window combining CursorBLD UI excellence with Kiro optimization

    Features:
    - CursorBLD's intuitive layout and theme system
    - Kiro's performance monitoring and memory optimization
    - Unified error handling and logging
    - Responsive design with accessibility features
    """

    # Signals
    folder_changed = Signal(Path)
    image_selected = Signal(Path)
    theme_changed = Signal(str)
    performance_alert = Signal(str, str)  # level, message

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem = None,
    ):
        """
        Initialize the integrated main window

        Args:
            config_manager: Configuration manager instance
            state_manager: State manager instance
            logger_system: Logging system instance
        """
        super().__init__()

        # Core systems
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # UI components
        self.theme_manager: Optional[IntegratedThemeManager] = None
        self.theme_manager_widget: Optional[SimpleThemeManager] = None
        self.breadcrumb_bar: Optional[BreadcrumbAddressBar] = None
        self.thumbnail_grid: Optional[SimpleThumbnailGrid] = None
        # self.folder_navigator: Optional[EnhancedFolderNavigator] = None  # Removed: Using breadcrumb navigation instead

        # Services
        self.file_discovery_service = FileDiscoveryService(
            logger_system=self.logger_system
        )

        # Layout components
        self.central_widget: Optional[QWidget] = None
        self.main_splitter: Optional[QSplitter] = None
        self.left_panel: Optional[QWidget] = None
        self.right_panel: Optional[QWidget] = None

        # Status and monitoring
        self.status_bar: Optional[QStatusBar] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.performance_timer: Optional[QTimer] = None
        self.memory_monitor: Optional[QTimer] = None

        # Performance tracking
        self.last_performance_check = None
        self.performance_history = []

        # Theme management
        self.selected_themes = []
        self.current_theme_index = 0

        # Initialize UI
        self._initialize_ui()
        self._setup_monitoring()
        self._restore_state()

        self.logger_system.log_ai_operation(
            AIComponent.KIRO, "main_window_init", "Integrated main window initialized"
        )

    def _initialize_ui(self):
        """Initialize the user interface"""

        try:
            # Set window properties
            self.setWindowTitle("PhotoGeoView - AI Integrated")
            self.setMinimumSize(1200, 800)

            # Create menu bar
            self._create_menu_bar()

            # Initialize breadcrumb bar first (needed for left panel creation)
            self._initialize_breadcrumb_bar()

            # Create central widget and layout
            self._create_central_widget()

            # Create status bar
            self._create_status_bar()

            # Initialize theme manager
            self._initialize_theme_manager()

            # Create toolbar (after theme manager is initialized)
            self._create_toolbar()

            # Apply initial theme
            self._apply_initial_theme()

            # Connect signals after all UI components are created
            self._connect_signals()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "ui_initialization"},
                AIComponent.CURSOR,
            )

    def _create_menu_bar(self):
        """Create the menu bar (CursorBLD style)"""

        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_folder_action = QAction("📁 &Open Folder...", self)
        open_folder_action.setShortcut(QKeySequence.StandardKey.Open)
        open_folder_action.setStatusTip("Open a folder containing images")
        open_folder_action.triggered.connect(self._open_folder)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        performance_action = QAction("&Performance Monitor", self)
        performance_action.setCheckable(True)
        performance_action.setChecked(True)
        performance_action.triggered.connect(self._toggle_performance_monitor)
        view_menu.addAction(performance_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Create the toolbar (CursorBLD style with Kiro enhancements)"""

        toolbar = self.addToolBar("Main")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # Open folder action
        open_action = QAction("📁 Open Folder", self)
        open_action.setStatusTip("Open a folder containing images")
        open_action.triggered.connect(self._open_folder)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        # Advanced theme selector
        self.advanced_theme_action = QAction("🎨 テーマ設定", self)
        self.advanced_theme_action.setStatusTip("Open advanced theme selector with preview")
        self.advanced_theme_action.triggered.connect(self._show_advanced_theme_selector)
        toolbar.addAction(self.advanced_theme_action)

        # Theme toggle button for selected themes
        from ...ui.theme_selector import ThemeToggleButton
        self.theme_toggle_button = ThemeToggleButton(self.theme_manager_widget, self)
        self.theme_toggle_button.theme_changed.connect(self._on_toggle_theme_changed)
        toolbar.addWidget(self.theme_toggle_button)

        toolbar.addSeparator()

        # Performance indicator (Kiro enhancement)
        self.performance_label = QLabel("Performance: Good")
        self.performance_label.setStyleSheet("color: green; font-weight: bold;")
        toolbar.addWidget(self.performance_label)

        # Memory usage indicator (Kiro enhancement)
        self.memory_label = QLabel("Memory: 0 MB")
        toolbar.addWidget(self.memory_label)

    def _create_central_widget(self):
        """Create the central widget layout (CursorBLD design)"""

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # Create left panel (folder navigation and thumbnails)
        self._create_left_panel()

        # Create right panel (image preview and map)
        self._create_right_panel()

        # Set splitter proportions (CursorBLD style)
        self.main_splitter.setSizes([400, 800])
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

    def _create_left_panel(self):
        """Create the left panel with splitters (4-area adjustable design with breadcrumb)"""

        # 左パネル用の垂直スプリッターを作成
        self.left_panel_splitter = QSplitter(Qt.Orientation.Vertical)
        self.left_panel_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bdc3c7;
                height: 4px;
                border-radius: 2px;
                margin: 1px 0px;
            }
            QSplitter::handle:hover {
                background-color: #3498db;
            }
            QSplitter::handle:pressed {
                background-color: #2980b9;
            }
        """)

        # 1. Breadcrumb address bar (最上段)
        breadcrumb_added = False
        if self.breadcrumb_bar:
            breadcrumb_widget = self.breadcrumb_bar.get_widget()
            if breadcrumb_widget:
                breadcrumb_widget.setMinimumHeight(40)  # 最小高さ設定
                breadcrumb_widget.setMaximumHeight(60)  # 最大高さ設定
                self.left_panel_splitter.addWidget(breadcrumb_widget)
                breadcrumb_added = True

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "breadcrumb_widget_added",
                    "Breadcrumb widget added to left panel"
                )
            else:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "breadcrumb_widget_missing",
                    "Breadcrumb widget not available for left panel",
                    level="WARNING"
                )

        if not breadcrumb_added:
            # ブレッドクラムが利用できない場合は、プレースホルダーを追加
            from PySide6.QtWidgets import QLabel
            placeholder = QLabel("ブレッドクラムナビゲーション利用不可")
            placeholder.setMinimumHeight(40)
            placeholder.setMaximumHeight(60)
            placeholder.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 10px;
                    color: #6c757d;
                    font-style: italic;
                    text-align: center;
                }
            """)
            self.left_panel_splitter.addWidget(placeholder)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_placeholder_added",
                "Breadcrumb placeholder added to left panel"
            )

        # 2. Thumbnail grid (上段)
        self.thumbnail_grid = SimpleThumbnailGrid(
            self.config_manager, self.state_manager, self.logger_system
        )
        self.thumbnail_grid.setMinimumHeight(200)  # 最小高さ設定
        self.left_panel_splitter.addWidget(self.thumbnail_grid)

        # 3. EXIF information panel (下段)
        from .exif_panel import EXIFPanel
        self.exif_panel = EXIFPanel(
            self.config_manager, self.state_manager, self.logger_system
        )
        self.exif_panel.setMinimumHeight(300)  # 最小高さ設定
        self.left_panel_splitter.addWidget(self.exif_panel)

        # スプリッターの初期サイズ設定 (ブレッドクラム:サムネイル:EXIF = 1:5:4)
        self.left_panel_splitter.setSizes([50, 500, 400])

        # 各エリアの伸縮設定（3つのウィジェット）
        self.left_panel_splitter.setStretchFactor(0, 0)  # ブレッドクラム: 固定
        self.left_panel_splitter.setStretchFactor(1, 1)  # サムネイルグリッド: 伸縮可能（メイン）
        self.left_panel_splitter.setStretchFactor(2, 1)  # EXIFパネル: 伸縮可能

        # 左パネルスプリッターをメインスプリッターに追加
        self.main_splitter.addWidget(self.left_panel_splitter)

        # 左パネルスプリッターの設定を復元
        self._restore_left_panel_splitter_state()

    def _restore_left_panel_splitter_state(self):
        """左パネルスプリッターの状態を復元"""
        try:
            # 保存されたスプリッター状態を取得
            splitter_states = self.config_manager.get_setting("ui.splitter_states", {})

            if "left_panel_splitter" in splitter_states:
                self.left_panel_splitter.restoreState(splitter_states["left_panel_splitter"])

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "left_panel_splitter_restored",
                    "Left panel splitter state restored",
                )
            else:
                # デフォルト設定を適用 (ブレッドクラム:サムネイル:EXIF の3エリア構成)
                self.left_panel_splitter.setSizes([50, 500, 400])

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "left_panel_splitter_default",
                    "Left panel splitter set to default sizes (3-panel layout)",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "restore_left_panel_splitter_state"},
                AIComponent.KIRO,
            )

    def _create_right_panel(self):
        """Create the right panel (image preview and map)"""

        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Vertical splitter for image and map
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_layout.addWidget(right_splitter)

        # Image preview panel (Kiro component)
        from .image_preview_panel import ImagePreviewPanel
        self.image_preview_panel = ImagePreviewPanel(
            self.config_manager, self.state_manager, self.logger_system
        )
        right_splitter.addWidget(self.image_preview_panel)

        # Map panel (Kiro component)
        from .map_panel import MapPanel
        self.map_panel = MapPanel(
            self.config_manager, self.state_manager, self.logger_system
        )
        right_splitter.addWidget(self.map_panel)

        # Set splitter proportions
        right_splitter.setSizes([400, 200])

        self.main_splitter.addWidget(self.right_panel)

    def _create_status_bar(self):
        """Create the status bar with Kiro enhancements"""

        self.status_bar = self.statusBar()

        # Main status message
        self.status_bar.showMessage("Ready")

        # Progress bar (Kiro enhancement)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Performance indicator
        self.status_performance = QLabel("Performance: Good")
        self.status_performance.setStyleSheet("color: green;")
        self.status_bar.addPermanentWidget(self.status_performance)

        # Memory usage
        self.status_memory = QLabel("Memory: 0 MB")
        self.status_bar.addPermanentWidget(self.status_memory)

    def _initialize_theme_manager(self):
        """Initialize the simple theme manager"""

        try:
            # Initialize the simple theme manager
            self.theme_manager_widget = SimpleThemeManager(
                self.config_manager, self.logger_system
            )

            # Connect theme change signals
            self.theme_manager_widget.theme_changed.connect(self._on_simple_theme_changed)
            self.theme_manager_widget.theme_applied.connect(self._on_theme_applied)
            self.theme_manager_widget.theme_error.connect(self._on_theme_error)

            # Populate theme menu after theme manager is initialized
            if hasattr(self, 'theme_menu'):
                self._populate_theme_menu()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_manager_init"},
                AIComponent.CURSOR,
            )

    def _initialize_breadcrumb_bar(self):
        """Initialize the breadcrumb address bar"""

        try:
            # Initialize file system watcher if not already available
            if not hasattr(self, 'file_system_watcher'):
                from ..services.file_system_watcher import FileSystemWatcher
                self.file_system_watcher = FileSystemWatcher(
                    logger_system=self.logger_system, enable_monitoring=True
                )

            # Initialize breadcrumb bar
            self.breadcrumb_bar = BreadcrumbAddressBar(
                self.file_system_watcher, self.logger_system, self.config_manager, self
            )

            # Verify breadcrumb widget is available
            breadcrumb_widget = self.breadcrumb_bar.get_widget()
            if breadcrumb_widget is None:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "breadcrumb_widget_unavailable",
                    "Breadcrumb widget not available, creating fallback",
                    level="WARNING"
                )
                # Set breadcrumb_bar to None instead of creating fallback
                self.breadcrumb_bar = None
            else:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "breadcrumb_widget_available",
                    "Breadcrumb widget successfully initialized"
                )

            # Connect breadcrumb signals
            if self.breadcrumb_bar:
                self.breadcrumb_bar.path_changed.connect(self._on_breadcrumb_path_changed)
                self.breadcrumb_bar.segment_clicked.connect(self._on_breadcrumb_segment_clicked)
                self.breadcrumb_bar.navigation_requested.connect(self._on_breadcrumb_navigation_requested)
                self.breadcrumb_bar.breadcrumb_error.connect(self._on_breadcrumb_error)
                # Breadcrumb path changes are handled by _on_breadcrumb_path_changed

                # Set initial path from state
                current_folder = self.state_manager.get_state_value("current_folder", Path.home())
                self.breadcrumb_bar.set_current_path(current_folder)

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_init_error",
                f"Failed to initialize breadcrumb bar: {e}",
                level="ERROR"
            )
            # Set breadcrumb_bar to None instead of creating fallback
            self.breadcrumb_bar = None

            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_bar_init"},
                AIComponent.KIRO,
            )



    def _apply_initial_theme(self):
        """Apply the initial theme from configuration"""

        try:
            current_theme = self.config_manager.get_setting("ui.theme", "default")
            if self.theme_manager:
                self.theme_manager.apply_theme(current_theme)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "initial_theme_apply"},
                AIComponent.CURSOR,
            )

    def _setup_monitoring(self):
        """Setup performance and memory monitoring (Kiro enhancement)"""

        # Performance monitoring timer
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._update_performance_metrics)
        self.performance_timer.start(5000)  # Update every 5 seconds

        # Memory monitoring timer
        self.memory_monitor = QTimer()
        self.memory_monitor.timeout.connect(self._update_memory_usage)
        self.memory_monitor.start(2000)  # Update every 2 seconds

    def _connect_signals(self):
        """Connect internal signals"""

        # Folder navigator removed - using breadcrumb navigation instead

        # Connect thumbnail grid signals
        if self.thumbnail_grid:
            self.thumbnail_grid.image_selected.connect(self._on_image_selected)
            # Connect folder changes to thumbnail grid
            self.folder_changed.connect(self._update_thumbnail_grid)
            # Connect status messages if available
            if hasattr(self.thumbnail_grid, 'status_message'):
                self.thumbnail_grid.status_message.connect(self._on_status_message)

        # Connect EXIF panel signals
        if self.exif_panel:
            self.exif_panel.gps_coordinates_updated.connect(self._on_gps_coordinates_updated)
            # 画像選択時にEXIFパネルに画像を設定
            self.thumbnail_grid.image_selected.connect(self.exif_panel.set_image)
            # Connect status messages if available
            if hasattr(self.exif_panel, 'status_message'):
                self.exif_panel.status_message.connect(self._on_status_message)

        # Connect image preview panel signals
        if self.image_preview_panel:
            self.image_preview_panel.image_loaded.connect(self._on_image_preview_loaded)
            # Connect status messages if available
            if hasattr(self.image_preview_panel, 'status_message'):
                self.image_preview_panel.status_message.connect(self._on_status_message)

        # Connect map panel signals
        if self.map_panel:
            self.map_panel.map_loaded.connect(self._on_map_loaded)
            self.map_panel.map_error.connect(self._on_map_error)
            # Connect status messages if available
            if hasattr(self.map_panel, 'status_message'):
                self.map_panel.status_message.connect(self._on_status_message)

        # Connect performance alerts
        self.performance_alert.connect(self._on_performance_alert)

        # Register UI components with theme manager
        if self.theme_manager_widget:
            self._register_theme_aware_components()

    def _restore_state(self):
        """Restore window state from configuration"""

        try:
            # Restore window geometry
            geometry = self.config_manager.get_setting("ui.window_geometry")
            if geometry:
                self.restoreGeometry(geometry)

            # Restore splitter states
            splitter_states = self.config_manager.get_setting("ui.splitter_states", {})

            if "main_splitter" in splitter_states:
                self.main_splitter.restoreState(splitter_states["main_splitter"])

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "state_restore"},
                AIComponent.KIRO,
            )

    # Event handlers

    def _open_folder(self):
        """Open folder dialog and load images"""

        try:
            from PySide6.QtWidgets import QFileDialog

            folder = QFileDialog.getExistingDirectory(
                self,
                "Select Image Folder",
                str(self.state_manager.get_state_value("current_folder", Path.home())),
            )

            if folder:
                folder_path = Path(folder)
                self.folder_changed.emit(folder_path)

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR, "folder_open", f"Folder opened: {folder_path}"
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "open_folder"},
                AIComponent.CURSOR,
            )



    def _populate_theme_menu(self):
        """Populate theme menu with available themes"""
        try:
            if not hasattr(self, 'theme_menu') or not self.theme_manager_widget:
                return

            # Clear existing actions
            self.theme_menu.clear()

            # Get available themes
            available_themes = self.theme_manager_widget.get_available_themes()
            current_theme = self.theme_manager_widget.get_current_theme()

            # Create action group for exclusive selection
            from PySide6.QtGui import QActionGroup
            self.theme_action_group = QActionGroup(self)

            # Add theme actions
            for theme_name in sorted(available_themes):
                # Get theme display name
                theme_info = self.theme_manager_widget.get_theme_info(theme_name)
                display_name = theme_info.get('display_name', theme_name.replace('_', ' ').title()) if theme_info else theme_name.replace('_', ' ').title()

                # Create action
                action = QAction(display_name, self)
                action.setCheckable(True)
                action.setChecked(theme_name == current_theme)
                action.setData(theme_name)  # Store theme name in action data

                # Connect to theme change handler
                action.triggered.connect(lambda checked, name=theme_name: self._apply_theme(name))

                # Add to action group and menu
                self.theme_action_group.addAction(action)
                self.theme_menu.addAction(action)

            # Add separator and refresh action
            self.theme_menu.addSeparator()
            refresh_action = QAction("🔄 Refresh Themes", self)
            refresh_action.triggered.connect(self._refresh_themes)
            self.theme_menu.addAction(refresh_action)

            # Add advanced theme selector
            self.theme_menu.addSeparator()
            advanced_theme_action = QAction("テーマ設定", self)
            advanced_theme_action.triggered.connect(self._show_advanced_theme_selector)
            self.theme_menu.addAction(advanced_theme_action)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO, "theme_menu_populated", f"Added {len(available_themes)} themes to menu"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "populate_theme_menu"},
                AIComponent.KIRO,
            )

    def _apply_theme(self, theme_name: str):
        """Apply selected theme"""
        try:
            if self.theme_manager_widget:
                success = self.theme_manager_widget.apply_theme(theme_name)
                if success:
                    self.logger_system.log_ai_operation(
                        AIComponent.CURSOR, "theme_applied", f"Theme applied: {theme_name}"
                    )
                else:
                    self.logger_system.log_ai_operation(
                        AIComponent.CURSOR, "theme_apply_failed", f"Failed to apply theme: {theme_name}"
                    )
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "apply_theme", "theme": theme_name},
                AIComponent.CURSOR,
            )

    def _refresh_themes(self):
        """Refresh theme list"""
        try:
            if self.theme_manager_widget:
                self.theme_manager_widget.reload_themes()
                self._populate_theme_menu()
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO, "themes_refreshed", "Theme list refreshed"
                )
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "refresh_themes"},
                AIComponent.KIRO,
            )

    def _show_advanced_theme_selector(self):
        """Show advanced theme selector dialog"""
        try:
            from ...ui.theme_selector import ThemeSelectionDialog

            dialog = ThemeSelectionDialog(self.theme_manager_widget, self)
            dialog.theme_applied.connect(self._on_advanced_theme_applied)
            dialog.exec()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "advanced_theme_selector_opened", "Advanced theme selector opened"
            )
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_advanced_theme_selector"},
                AIComponent.CURSOR,
            )

    def _on_advanced_theme_applied(self, theme_list: list):
        """Handle themes applied from advanced selector"""
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "advanced_theme_applied", f"Themes applied from advanced selector: {theme_list}"
            )

            # 選択されたテーマを管理
            self.selected_themes = theme_list
            self.current_theme_index = 0

            # 最初のテーマを適用
            if self.selected_themes:
                first_theme = self.selected_themes[0]
                self.theme_manager_widget.apply_theme(first_theme)
                self._update_toggle_button_text()

            # 選択されたテーマリストをトグルボタンに設定
            if hasattr(self, 'theme_toggle_button'):
                self.theme_toggle_button.set_selected_themes(theme_list)

            # Update menu selection
            self._populate_theme_menu()
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "on_advanced_theme_applied", "themes": theme_list},
                AIComponent.CURSOR,
            )

    def _on_toggle_theme_changed(self, theme_name: str):
        """Handle theme change from toggle button"""
        try:
            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "toggle_theme_changed", f"Theme toggled: {theme_name}"
            )

            # 選択されたテーマを循環切り替え
            if self.selected_themes and len(self.selected_themes) > 1:
                self.current_theme_index = (self.current_theme_index + 1) % len(self.selected_themes)
                next_theme = self.selected_themes[self.current_theme_index]

                # テーママネージャーに直接適用
                if self.theme_manager_widget:
                    self.theme_manager_widget.apply_theme(next_theme)

                self._update_toggle_button_text()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "on_toggle_theme_changed", "theme": theme_name},
                AIComponent.CURSOR,
            )

    def _update_toggle_button_text(self):
        """Update toggle button text to show current theme"""
        try:
            if hasattr(self, 'theme_toggle_button'):
                if self.selected_themes:
                    current_theme = self.selected_themes[self.current_theme_index]
                    self.theme_toggle_button.setText(f"テーマ切替: {current_theme}")
                else:
                    self.theme_toggle_button.setText("テーマ切替")
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_toggle_button_text"},
                AIComponent.CURSOR,
            )

    def _on_simple_theme_changed(self, old_theme: str, new_theme: str):
        """Handle theme change from SimpleThemeManager"""
        try:
            # Update menu selection
            if hasattr(self, 'theme_action_group'):
                for action in self.theme_action_group.actions():
                    theme_name = action.data()
                    action.setChecked(theme_name == new_theme)

            # Update toolbar theme button text
            if hasattr(self, 'theme_action'):
                theme_config = self.theme_manager_widget.get_theme_config(new_theme)
                display_name = theme_config.get('display_name', new_theme.replace('_', ' ').title()) if theme_config else new_theme.replace('_', ' ').title()
                self.theme_action.setText(f"🎨 {display_name}")
                self.theme_action.setStatusTip(f"Current theme: {display_name}. Click to toggle between light and dark.")

            # Emit theme changed signal
            self.theme_changed.emit(new_theme)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR, "theme_changed", f"Theme changed: {old_theme} -> {new_theme}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_change_handler"},
                AIComponent.CURSOR,
            )

    def _toggle_performance_monitor(self, enabled: bool):
        """Toggle performance monitoring display"""

        if enabled:
            self.performance_timer.start()
            self.memory_monitor.start()
        else:
            self.performance_timer.stop()
            self.memory_monitor.stop()

        self.performance_label.setVisible(enabled)
        self.memory_label.setVisible(enabled)
        self.status_performance.setVisible(enabled)
        self.status_memory.setVisible(enabled)

    def _show_about(self):
        """Show about dialog"""

        QMessageBox.about(
            self,
            "About PhotoGeoView",
            "PhotoGeoView - AI Integrated\n\n"
            "A photo management application with geographic information display.\n\n"
            "Powered by:\n"
            "• GitHub Copilot (CS4Coding): Core functionality\n"
            "• Cursor (CursorBLD): UI/UX excellence\n"
            "• Kiro: Integration and optimization\n\n"
            "Version: 1.0.0",
        )

    def _on_folder_changed(self, folder_path: Path):
        """Handle folder change event"""

        try:
            # Update state
            self.state_manager.update_state(current_folder=folder_path)

            # Breadcrumb bar updates are handled by breadcrumb itself

            # Update status
            if hasattr(self, "status_bar") and self.status_bar:
                self.status_bar.showMessage(f"Navigated to: {folder_path}")

            # Emit signal for other components
            self.folder_changed.emit(folder_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "folder_change_handling", "folder": str(folder_path)},
                AIComponent.CURSOR,
            )

    def _on_status_message(self, message: str, timeout_ms: int = 3000):
        """Handle status message from components"""

        try:
            if hasattr(self, "status_bar") and self.status_bar:
                self.status_bar.showMessage(message, timeout_ms)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "status_message_displayed",
                    f"ステータスメッセージ表示: {message}",
                    level="DEBUG",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "status_message", "message": message},
                AIComponent.KIRO,
            )

    def _on_image_selected(self, image_path: Path):
        """Handle image selection event"""

        try:
            # Update state
            self.state_manager.update_state(selected_image=image_path)

            # Update status
            self.status_bar.showMessage(f"Selected: {image_path.name}")

            # Update EXIF panel
            if self.exif_panel:
                self.exif_panel.set_image(image_path)

            # Update image preview panel
            if self.image_preview_panel:
                self.image_preview_panel.set_image(image_path)

            # Extract GPS coordinates and add to map
            self._extract_and_add_to_map(image_path)

            # Emit signal for other components
            self.image_selected.emit(image_path)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "image_selection_handling", "image": str(image_path)},
                AIComponent.CURSOR,
            )

    def _extract_and_add_to_map(self, image_path: Path):
        """画像からGPS座標を抽出して地図に追加"""
        try:
            from ..image_processor import CS4CodingImageProcessor

            # 画像プロセッサーでEXIF情報を抽出
            image_processor = CS4CodingImageProcessor(
                self.config_manager, self.logger_system
            )

            exif_data = image_processor.extract_exif(image_path)

            # GPS座標を取得
            latitude = exif_data.get("GPS Latitude")
            longitude = exif_data.get("GPS Longitude")

            if latitude is not None and longitude is not None:
                # 地図パネルに位置情報を追加
                if self.map_panel:
                    self.map_panel.add_image_location(
                        image_path, latitude, longitude, image_path.name
                    )

                    # 個別の画像の位置にフォーカス
                    self.map_panel.set_coordinates(latitude, longitude, focus_on_location=True, image_path=str(image_path))

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "add_gps_to_map",
                    f"GPS座標を地図に追加: {image_path.name} ({latitude:.6f}, {longitude:.6f})",
                    context={"image_path": str(image_path), "latitude": latitude, "longitude": longitude},
                )
            else:
                # GPS座標がない場合の処理
                if self.map_panel:
                    self.map_panel.show_no_gps_message(image_path.name)

                # GPS座標がない場合のログ
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "no_gps_coordinates",
                    f"GPS座標なし: {image_path.name}",
                    context={"image_path": str(image_path)},
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "extract_and_add_to_map", "image_path": str(image_path)},
                AIComponent.KIRO,
            )

    def _on_gps_coordinates_updated(self, latitude: float, longitude: float):
        """Handle GPS coordinates update from EXIF panel"""

        try:
            # Update state with GPS coordinates
            self.state_manager.update_state(
                current_latitude=latitude,
                current_longitude=longitude
            )

            # Log GPS coordinates update
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "gps_coordinates_updated",
                f"GPS coordinates updated: {latitude:.6f}, {longitude:.6f}",
                context={"latitude": latitude, "longitude": longitude},
            )

                        # Update map panel
            if self.map_panel:
                self.map_panel.set_coordinates(latitude, longitude)

            # Update status bar
            self.status_bar.showMessage(
                f"GPS: {latitude:.6f}°, {longitude:.6f}°",
                3000
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "gps_coordinates_update", "lat": latitude, "lon": longitude},
                AIComponent.KIRO,
            )

    # Breadcrumb event handlers

    def _on_breadcrumb_path_changed(self, path: Path):
        """Handle breadcrumb path change event"""
        try:
            # Folder navigator removed - breadcrumb handles navigation

            # Call the main folder change handler to avoid duplication
            self._on_folder_changed(path)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_path_changed",
                f"Path changed via breadcrumb: {path}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_path_changed", "path": str(path)},
                AIComponent.KIRO,
            )

    def _on_breadcrumb_segment_clicked(self, segment_index: int, path: Path):
        """Handle breadcrumb segment click event"""
        try:
            # Folder navigator removed - breadcrumb handles navigation

            # Update state
            self.state_manager.update_state(current_folder=path)

            # Update status
            self.status_bar.showMessage(f"Navigated to segment: {path}")

            # Emit folder changed signal
            self.folder_changed.emit(path)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_segment_clicked",
                f"Segment {segment_index} clicked: {path}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_segment_clicked", "segment": segment_index, "path": str(path)},
                AIComponent.KIRO,
            )

    def _on_breadcrumb_navigation_requested(self, path: Path):
        """Handle breadcrumb navigation request"""
        try:
            # Validate path before navigation
            if not path.exists() or not path.is_dir():
                self.status_bar.showMessage(f"Invalid path: {path}", 5000)
                return

            # Folder navigator removed - breadcrumb handles navigation

            # Update state
            self.state_manager.update_state(current_folder=path)

            # Update status
            self.status_bar.showMessage(f"Navigation requested: {path}")

            # Emit folder changed signal
            self.folder_changed.emit(path)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_navigation_requested",
                f"Navigation requested: {path}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_navigation_requested", "path": str(path)},
                AIComponent.KIRO,
            )

    def _on_breadcrumb_error(self, error_type: str, error_message: str):
        """Handle breadcrumb error event"""
        try:
            # Show error in status bar
            self.status_bar.showMessage(f"Breadcrumb error: {error_message}", 5000)

            # Log error
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_error",
                f"Breadcrumb error ({error_type}): {error_message}",
                level="ERROR"
            )

            # Show user notification if available
            if hasattr(self, 'notification_system') and self.notification_system:
                self.notification_system.show_error(
                    "Breadcrumb Navigation Error",
                    error_message
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_error_handling", "error_type": error_type, "error_message": error_message},
                AIComponent.KIRO,
            )

    def _on_image_preview_loaded(self, image_path: Path):
        """Handle image preview loaded event"""

        try:
            # Update status bar
            self.status_bar.showMessage(f"画像プレビュー読み込み完了: {image_path.name}", 2000)

            # Log the event
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "image_preview_loaded",
                f"画像プレビュー読み込み完了: {image_path.name}",
                context={"image_path": str(image_path)},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "image_preview_loaded", "image_path": str(image_path)},
                AIComponent.KIRO,
            )

    def _on_map_loaded(self, latitude: float, longitude: float):
        """Handle map loaded event"""

        try:
            # Update status bar
            self.status_bar.showMessage(f"地図読み込み完了: {latitude:.6f}, {longitude:.6f}", 2000)

            # Log the event
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "map_loaded",
                f"地図読み込み完了: {latitude:.6f}, {longitude:.6f}",
                context={"latitude": latitude, "longitude": longitude},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "map_loaded", "latitude": latitude, "longitude": longitude},
                AIComponent.KIRO,
            )

    def _on_map_error(self, error_message: str):
        """Handle map error event"""

        try:
            # Update status bar
            self.status_bar.showMessage(f"地図エラー: {error_message}", 3000)

            # Log the error
            self.logger_system.log_error(
                Exception(error_message),
                "map_error",
                {"error_message": error_message},
                AIComponent.KIRO,
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "map_error", "error_message": error_message},
                AIComponent.KIRO,
            )

    def _on_theme_changed(self, theme_name: str):
        """Handle theme change event"""

        try:
            # Update state
            self.state_manager.update_state(current_theme=theme_name)

            # Update status
            self.status_bar.showMessage(f"Theme changed to: {theme_name}", 2000)

            # Emit signal
            self.theme_changed.emit(theme_name)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_change_handling", "theme": theme_name},
                AIComponent.CURSOR,
            )

    def _on_theme_manager_widget_changed(self, old_theme: str, new_theme: str):
        """Handle theme change from theme manager widget"""

        try:
            # Update integrated theme manager to stay in sync
            if self.theme_manager and hasattr(self.theme_manager, 'apply_theme'):
                self.theme_manager.apply_theme(new_theme)

            # Update status
            self.status_bar.showMessage(f"Theme changed from {old_theme} to {new_theme}", 2000)

            # Log the change
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "theme_changed_via_widget",
                f"Theme changed from {old_theme} to {new_theme}",
                context={"old_theme": old_theme, "new_theme": new_theme}
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_manager_widget_change", "old_theme": old_theme, "new_theme": new_theme},
                AIComponent.KIRO,
            )

    def _on_theme_applied(self, theme_name: str):
        """Handle theme applied event"""

        try:
            # Update status
            self.status_bar.showMessage(f"Theme applied: {theme_name}", 1500)

            # Log the application
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "theme_applied",
                f"Theme applied successfully: {theme_name}",
                context={"theme_name": theme_name}
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_applied", "theme": theme_name},
                AIComponent.KIRO,
            )

    def _on_theme_error(self, theme_name: str, error_message: str):
        """Handle theme error event"""

        try:
            # Update status with error
            self.status_bar.showMessage(f"Theme error: {error_message}", 5000)

            # Log the error
            self.logger_system.log_error(
                Exception(error_message),
                "theme_error",
                {"theme_name": theme_name, "error_message": error_message},
                AIComponent.KIRO,
            )

            # Show user notification for critical errors
            if "not found" in error_message.lower() or "failed to load" in error_message.lower():
                QMessageBox.warning(
                    self,
                    "Theme Error",
                    f"Failed to apply theme '{theme_name}':\n{error_message}\n\nReverting to default theme."
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_error_handling", "theme": theme_name, "error": error_message},
                AIComponent.KIRO,
            )

    def _on_breadcrumb_path_changed(self, new_path: Path):
        """Handle breadcrumb path change event"""

        try:
            # Folder navigator removed - breadcrumb handles navigation

            # Update state
            self.state_manager.update_state(current_folder=new_path)

            # Update status
            self.status_bar.showMessage(f"Navigated to: {new_path}", 2000)

            # Emit folder changed signal
            self.folder_changed.emit(new_path)

            # Log the navigation
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_navigation",
                f"Navigated via breadcrumb to: {new_path}",
                context={"path": str(new_path)}
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_path_change", "path": str(new_path)},
                AIComponent.KIRO,
            )

    def _on_breadcrumb_segment_clicked(self, segment_index: int, path: Path):
        """Handle breadcrumb segment click event"""

        try:
            # Update status
            self.status_bar.showMessage(f"Navigated to segment {segment_index}: {path.name}", 2000)

            # Log the segment click
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_segment_click",
                f"Clicked breadcrumb segment {segment_index}: {path}",
                context={"segment_index": segment_index, "path": str(path)}
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_segment_click", "segment": segment_index, "path": str(path)},
                AIComponent.KIRO,
            )

    def _on_breadcrumb_navigation_requested(self, target_path: Path):
        """Handle breadcrumb navigation request"""

        try:
            # Validate path before navigation
            if not target_path.exists() or not target_path.is_dir():
                self.status_bar.showMessage(f"Cannot navigate to: {target_path} (path not accessible)", 3000)
                return

            # Perform navigation
            self._on_folder_changed(target_path)

            # Log the navigation request
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "breadcrumb_navigation_request",
                f"Navigation requested to: {target_path}",
                context={"target_path": str(target_path)}
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_navigation_request", "path": str(target_path)},
                AIComponent.KIRO,
            )

    def _on_breadcrumb_error(self, error_type: str, error_message: str):
        """Handle breadcrumb error event"""

        try:
            # Update status with error
            self.status_bar.showMessage(f"Breadcrumb error: {error_message}", 4000)

            # Log the error
            self.logger_system.log_error(
                Exception(error_message),
                "breadcrumb_error",
                {"error_type": error_type, "error_message": error_message},
                AIComponent.KIRO,
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "breadcrumb_error_handling", "error_type": error_type, "error": error_message},
                AIComponent.KIRO,
            )

    def _register_theme_aware_components(self):
        """Register UI components with theme manager for theme updates"""

        try:
            if not self.theme_manager_widget:
                return

            # Register main UI components that support theming
            components_to_register = []

            # Folder navigator removed - no theming needed

            # Add thumbnail grid if it supports theming
            if self.thumbnail_grid and hasattr(self.thumbnail_grid, 'apply_theme'):
                components_to_register.append(self.thumbnail_grid)

            # Add EXIF panel if it supports theming
            if hasattr(self, 'exif_panel') and hasattr(self.exif_panel, 'apply_theme'):
                components_to_register.append(self.exif_panel)

            # Add image preview panel if it supports theming
            if hasattr(self, 'image_preview_panel') and hasattr(self.image_preview_panel, 'apply_theme'):
                components_to_register.append(self.image_preview_panel)

            # Add map panel if it supports theming
            if hasattr(self, 'map_panel') and hasattr(self.map_panel, 'apply_theme'):
                components_to_register.append(self.map_panel)

            # Add breadcrumb bar widget if it supports theming
            if self.breadcrumb_bar and self.breadcrumb_bar.get_widget():
                breadcrumb_widget = self.breadcrumb_bar.get_widget()
                if hasattr(breadcrumb_widget, 'apply_theme'):
                    components_to_register.append(breadcrumb_widget)

            # Register all theme-aware components
            for component in components_to_register:
                if hasattr(self.theme_manager_widget, 'register_component'):
                    success = self.theme_manager_widget.register_component(component)
                    if success:
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "component_registered_for_theming",
                            f"Component registered for theme updates: {type(component).__name__}",
                            context={"component_type": type(component).__name__}
                        )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "theme_aware_components_registered",
                f"Registered {len(components_to_register)} components for theme updates",
                context={"component_count": len(components_to_register)}
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "register_theme_aware_components"},
                AIComponent.KIRO,
            )

    def _update_thumbnail_grid(self, folder_path: Path):
        """
        Update thumbnail grid with images from the selected folder using FileDiscoveryService

        Args:
            folder_path: Path to the folder to scan for images
        """
        try:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "thumbnail_update_start",
                f"Starting thumbnail update for folder: {folder_path}",
            )

            # Validate folder path
            if not folder_path.exists() or not folder_path.is_dir():
                error_msg = f"フォルダが存在しないか、アクセスできません: {folder_path}"
                self.logger_system.log_error(
                    AIComponent.KIRO,
                    Exception(error_msg),
                    "folder_validation",
                    {"folder_path": str(folder_path)},
                )

                if self.thumbnail_grid:
                    self.thumbnail_grid.show_error_state(error_msg)
                return

            # Show loading state
            if self.thumbnail_grid:
                self.thumbnail_grid.show_loading_state("フォルダをスキャン中...")

            # Use FileDiscoveryService to discover images
            try:
                image_files = self.file_discovery_service.discover_images(folder_path)

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "file_discovery_complete",
                    f"Discovered {len(image_files)} images in {folder_path}",
                )

                # Update thumbnail grid based on results
                if self.thumbnail_grid:
                    if image_files:
                        # Update with discovered images
                        self.thumbnail_grid.update_image_list(image_files)

                        # Update status bar
                        if hasattr(self, "status_bar") and self.status_bar:
                            self.status_bar.showMessage(
                                f"{len(image_files)}個の画像ファイルが見つかりました - {folder_path.name}",
                                3000,
                            )
                    else:
                        # Show empty state
                        self.thumbnail_grid.show_empty_state()

                        # Update status bar
                        if hasattr(self, "status_bar") and self.status_bar:
                            self.status_bar.showMessage(
                                f"画像ファイルが見つかりませんでした - {folder_path.name}",
                                3000,
                            )

                # Update state manager
                self.state_manager.update_state(
                    current_folder=folder_path, image_count=len(image_files)
                )

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "thumbnail_update_complete",
                    f"Successfully updated thumbnails for {len(image_files)} images",
                )

            except Exception as discovery_error:
                # Handle FileDiscoveryService errors
                error_msg = (
                    f"ファイル検出中にエラーが発生しました: {str(discovery_error)}"
                )

                self.logger_system.log_error(
                    AIComponent.KIRO,
                    discovery_error,
                    "file_discovery_error",
                    {"folder_path": str(folder_path)},
                )

                if self.thumbnail_grid:
                    self.thumbnail_grid.show_error_state(error_msg)

                # Update status bar with error
                if hasattr(self, "status_bar") and self.status_bar:
                    self.status_bar.showMessage(f"エラー: {error_msg}", 5000)

                # Show user-friendly error dialog
                self._show_error_dialog(
                    "ファイル検出エラー",
                    f"フォルダ '{folder_path.name}' の画像ファイル検出中にエラーが発生しました。\n\n"
                    f"詳細: {str(discovery_error)}\n\n"
                    "フォルダの権限を確認するか、別のフォルダを選択してください。",
                )

        except Exception as e:
            # Handle unexpected errors
            error_msg = f"サムネイル更新中に予期しないエラーが発生しました: {str(e)}"

            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "thumbnail_grid_update", "folder": str(folder_path)},
                AIComponent.KIRO,
            )

            if self.thumbnail_grid:
                self.thumbnail_grid.show_error_state("予期しないエラーが発生しました")

            # Update status bar with error
            if hasattr(self, "status_bar") and self.status_bar:
                self.status_bar.showMessage(f"エラー: {error_msg}", 5000)

    def _show_error_dialog(self, title: str, message: str):
        """
        Show error dialog to user

        Args:
            title: Dialog title
            message: Error message
        """
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

        except Exception as e:
            # Fallback if dialog fails
            self.logger_system.log_error(
                AIComponent.KIRO,
                e,
                "error_dialog_failure",
                {"title": title, "message": message},
            )

    def _on_performance_alert(self, level: str, message: str):
        """Handle performance alerts (Kiro enhancement)"""

        # UI要素の存在確認
        if not hasattr(self, "performance_label") or self.performance_label is None:
            return

        if level == "warning":
            self.performance_label.setStyleSheet("color: orange; font-weight: bold;")
            if (
                hasattr(self, "status_performance")
                and self.status_performance is not None
            ):
                self.status_performance.setStyleSheet("color: orange;")
                self.status_performance.setText(f"Performance: {message}")
        elif level == "critical":
            self.performance_label.setStyleSheet("color: red; font-weight: bold;")
            if (
                hasattr(self, "status_performance")
                and self.status_performance is not None
            ):
                self.status_performance.setStyleSheet("color: red;")
                self.status_performance.setText(f"Performance: {message}")
        else:
            self.performance_label.setStyleSheet("color: green; font-weight: bold;")
            if (
                hasattr(self, "status_performance")
                and self.status_performance is not None
            ):
                self.status_performance.setStyleSheet("color: green;")
                self.status_performance.setText("Performance: Good")

    # Monitoring methods (Kiro enhancements)

    def _update_performance_metrics(self):
        """Update performance metrics display"""

        try:
            # UI要素が初期化されているかチェック
            if not hasattr(self, "performance_label") or self.performance_label is None:
                return

            # Get performance summary from state manager
            perf_summary = self.state_manager.get_performance_summary()

            if perf_summary.get("status") != "no_data":
                avg_memory = perf_summary.get("average_memory_mb", 0)
                avg_cpu = perf_summary.get("average_cpu_percent", 0)

                # Update performance label
                if avg_cpu > 80:
                    self.performance_alert.emit("critical", "High CPU")
                elif avg_cpu > 60:
                    self.performance_alert.emit("warning", "Moderate CPU")
                else:
                    self.performance_alert.emit("good", "Good")

                # Update performance display
                self.performance_label.setText(f"CPU: {avg_cpu:.1f}%")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "performance_update"},
                AIComponent.KIRO,
            )

    def _update_memory_usage(self):
        """Update memory usage display"""

        try:
            # UI要素が初期化されているかチェック
            if not hasattr(self, "memory_label") or self.memory_label is None:
                return

            import os

            import psutil

            # Get current process memory usage
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024

            # Update memory labels
            self.memory_label.setText(f"Memory: {memory_mb:.1f} MB")
            if hasattr(self, "status_memory") and self.status_memory is not None:
                self.status_memory.setText(f"Memory: {memory_mb:.1f} MB")

            # Check for memory alerts
            max_memory = self.config_manager.get_setting(
                "performance.max_memory_mb", 512
            )

            if memory_mb > max_memory * 0.9:
                self.performance_alert.emit("critical", "High Memory")
            elif memory_mb > max_memory * 0.7:
                self.performance_alert.emit("warning", "Moderate Memory")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.INTEGRATION_ERROR,
                {"operation": "memory_update"},
                AIComponent.KIRO,
            )

    # Window events

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""

        try:
            # Save window state
            self.config_manager.set_setting("ui.window_geometry", self.saveGeometry())

            # Save splitter states
            splitter_states = {
                "main_splitter": self.main_splitter.saveState()
            }

            # 左パネルスプリッターの状態も保存
            if hasattr(self, "left_panel_splitter"):
                splitter_states["left_panel_splitter"] = self.left_panel_splitter.saveState()

            self.config_manager.set_setting("ui.splitter_states", splitter_states)

            # Save configuration
            self.config_manager.save_config()

            # Folder navigator removed - no monitoring to stop

            # Stop performance monitoring
            if hasattr(self, "performance_timer") and self.performance_timer:
                self.performance_timer.stop()

            if hasattr(self, "memory_monitor") and self.memory_monitor:
                self.memory_monitor.stop()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO, "main_window_cleanup", "Main window cleanup completed"
            )

            # Stop timers
            if self.performance_timer:
                self.performance_timer.stop()
            if self.memory_monitor:
                self.memory_monitor.stop()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO, "main_window_close", "Main window closed, state saved"
            )

            event.accept()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "window_close"},
                AIComponent.KIRO,
            )
            event.accept()  # Accept anyway to prevent hanging

    # Public methods

    def show_progress(self, message: str, maximum: int = 0):
        """Show progress bar with message"""

        self.status_bar.showMessage(message)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def update_progress(self, value: int, message: str = None):
        """Update progress bar value"""

        self.progress_bar.setValue(value)
        if message:
            self.status_bar.showMessage(message)

    def hide_progress(self):
        """Hide progress bar"""

        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Ready")

    def get_current_folder(self) -> Optional[Path]:
        """Get currently selected folder"""

        return self.state_manager.get_state_value("current_folder")

    def get_selected_image(self) -> Optional[Path]:
        """Get currently selected image"""

        return self.state_manager.get_state_value("selected_image")
