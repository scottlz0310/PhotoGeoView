"""
PhotoGeoView Main Window Implementation
Main application window with UI layout and theme integration
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QToolBar, QStatusBar, QLabel,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QAction, QCloseEvent
from pathlib import Path
from typing import Dict, Optional, Any, Tuple

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.ui.theme_manager import ThemeManager
from src.ui.controllers.theme_controller import ThemeController
from src.ui.controllers.folder_controller import FolderController
from src.ui.controllers.panel_controller import PanelController
from src.ui.controllers.debug_controller import DebugController
from src.ui.controllers.toolbar_manager import ToolbarManager
from src.modules.file_browser import FileBrowser
from src.modules.thumbnail_view import ThumbnailView
from src.modules.exif_info import ExifInfoPanel
from src.modules.image_viewer import ImageViewer
from src.modules.map_viewer import MapViewer

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for PhotoGeoView
    Provides the primary user interface with theme support
    """

    # Custom signals
    folder_changed = pyqtSignal(str)  # Emitted when folder is changed
    theme_changed = pyqtSignal(str)   # Emitted when theme is changed

    def __init__(self):
        """Initialize the main window"""
        super().__init__()

        self.logger = logger
        self.settings = get_settings()

        # Initialize theme manager first
        self.theme_manager = ThemeManager()

        # Initialize controllers
        self.theme_controller = ThemeController(self.settings, self.theme_manager, self)
        self.folder_controller = FolderController(self.settings, self)
        self.panel_controller = PanelController(self)
        self.debug_controller = DebugController(self.settings, self)
        self.toolbar_manager = ToolbarManager(self)

        # UI components will be created in setup_ui()
        self.central_widget: Optional[QWidget] = None
        self.main_splitter: Optional[QSplitter] = None
        self.left_panel: Optional[QFrame] = None
        self.right_splitter: Optional[QSplitter] = None
        self.image_panel: Optional[QFrame] = None
        self.map_panel: Optional[QFrame] = None

        # Toolbar and status bar
        self.toolbar: Optional[QToolBar] = None
        self.status_bar: Optional[QStatusBar] = None
        self.status_label: Optional[QLabel] = None

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_settings)

        # Theme actions storage for persistent menu
        self.theme_actions: Dict[str, QAction] = {}

        # Initialize UI
        self.setup_ui()
        self.setup_theme()
        self.setup_connections()
        self.restore_window_state()

        # Start auto-save if enabled
        if self.settings.advanced.auto_save_settings:
            interval = self.settings.advanced.save_interval_seconds * 1000
            self.auto_save_timer.start(interval)

        # Setup controller connections
        self.setup_controller_connections()

        # Configure panel controller with widgets
        self.panel_controller.setup_widgets(
            self.file_browser,
            self.thumbnail_view,
            self.exif_panel,
            self.image_viewer,
            self.map_viewer
        )

        self.setup_widget_connections()

        self.logger.info("Main window initialized successfully")

    def setup_ui(self) -> None:
        """Setup the main user interface layout"""
        self.logger.debug("Setting up main UI layout")

        # Set window properties
        self.setWindowTitle("PhotoGeoView")
        self.setMinimumSize(800, 600)

        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)

        # Create toolbar via toolbar manager
        self.toolbar = self.toolbar_manager.setup_toolbar(self)
        self.addToolBar(self.toolbar)

        # Get references from toolbar manager
        self.current_folder_label = self.toolbar_manager.current_folder_label
        self.folder_action = self.toolbar_manager.folder_action
        self.back_action = self.toolbar_manager.back_action
        self.forward_action = self.toolbar_manager.forward_action
        self.up_action = self.toolbar_manager.up_action
        self.theme_action = self.toolbar_manager.theme_action

        # Create main content area with splitters
        self.setup_content_area()

        # Add content area to main layout
        main_layout.addWidget(self.main_splitter)

        # Create status bar
        self.setup_status_bar()

        # Setup debug shortcuts via controller
        self.debug_controller.setup_debug_shortcuts(self)

        self.logger.debug("Main UI layout setup complete")

    def setup_content_area(self) -> None:
        """Setup the main content area with panels"""
        # Create main horizontal splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create left panel (file browser)
        self.left_panel = self.create_left_panel()
        self.main_splitter.addWidget(self.left_panel)

        # Create right splitter (vertical)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Create image panel (top right)
        self.image_panel = self.create_image_panel()
        self.right_splitter.addWidget(self.image_panel)

        # Create map panel (bottom right)
        self.map_panel = self.create_map_panel()
        self.right_splitter.addWidget(self.map_panel)

        # Add right splitter to main splitter
        self.main_splitter.addWidget(self.right_splitter)

        # Set splitter proportions
        self.main_splitter.setSizes([300, 900])  # Left: 25%, Right: 75%
        self.right_splitter.setSizes([450, 450])  # Even split for image/map

    def create_left_panel(self) -> QFrame:
        """Create the left panel for file browsing with resizable sections"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumWidth(250)

        # Create vertical layout for the panel
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)  # No spacing since we use splitters

        # Create vertical splitter for resizable sections
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(left_splitter)

        # File browser section
        browser_widget = QFrame()
        browser_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(4, 4, 4, 4)

        browser_title = QLabel("🗂️ File Browser")
        browser_title.setStyleSheet("font-weight: bold; padding: 2px;")
        browser_title.setFixedHeight(24)  # Fixed height for title
        browser_layout.addWidget(browser_title)

        # Create actual file browser widget
        self.file_browser = FileBrowser()
        self.file_browser.setMinimumHeight(150)
        browser_layout.addWidget(self.file_browser)

        left_splitter.addWidget(browser_widget)

        # Thumbnail section
        thumbnail_widget = QFrame()
        thumbnail_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        thumbnail_layout = QVBoxLayout(thumbnail_widget)
        thumbnail_layout.setContentsMargins(4, 4, 4, 4)

        thumbnail_title = QLabel("🖼️ Thumbnails")
        thumbnail_title.setStyleSheet("font-weight: bold; padding: 2px;")
        thumbnail_title.setFixedHeight(24)  # Fixed height for title
        thumbnail_layout.addWidget(thumbnail_title)

        # Create actual thumbnail view widget
        self.thumbnail_view = ThumbnailView()
        self.thumbnail_view.setMinimumHeight(120)
        thumbnail_layout.addWidget(self.thumbnail_view)

        left_splitter.addWidget(thumbnail_widget)

        # EXIF info section
        exif_widget = QFrame()
        exif_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        exif_layout = QVBoxLayout(exif_widget)
        exif_layout.setContentsMargins(4, 4, 4, 4)

        exif_title = QLabel("ℹ️ EXIF Information")
        exif_title.setStyleSheet("font-weight: bold; padding: 2px;")
        exif_title.setFixedHeight(24)  # Fixed height for title
        exif_layout.addWidget(exif_title)

        # Create actual EXIF info panel widget
        self.exif_panel = ExifInfoPanel()
        self.exif_panel.setMinimumHeight(100)
        # EXIF データ読み込み完了時の地図更新を接続
        self.exif_panel.data_loaded.connect(self.on_exif_data_loaded)
        exif_layout.addWidget(self.exif_panel)

        left_splitter.addWidget(exif_widget)

        # Set initial splitter proportions (Browser: 40%, Thumbnails: 35%, EXIF: 25%)
        left_splitter.setSizes([200, 175, 125])

        # Store references for later access
        self.left_splitter = left_splitter
        self.file_browser = self.file_browser  # Already stored above

        return panel

    def create_image_panel(self) -> QFrame:
        """Create the image display panel with ImageViewer"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(200)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)  # No margins for full widget usage

        # Create the image viewer
        self.image_viewer = ImageViewer()
        layout.addWidget(self.image_viewer)

        # Connect ImageViewer's fullscreen signal to panel maximize
        self.image_viewer.fullscreen_requested.connect(self.on_fullscreen_requested)

        return panel

    def create_map_panel(self) -> QFrame:
        """Create the map display panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(200)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins since MapViewer has its own

        # Map viewer widget (already contains title and controls)
        self.map_viewer = MapViewer()
        self.map_viewer.setMinimumHeight(200)
        layout.addWidget(self.map_viewer)

        # Connect MapViewer's fullscreen signal to panel maximize
        self.map_viewer.fullscreen_requested.connect(self.on_map_fullscreen_requested)

        return panel

    def setup_status_bar(self) -> None:
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Theme indicator
        theme_label = QLabel(f"Theme: {self.settings.ui.current_theme}")
        self.status_bar.addPermanentWidget(theme_label)
        self.theme_status_label = theme_label

    def setup_theme(self) -> None:
        """
        Setup and apply the current theme
        Phase 4: Enhanced theme initialization with validation
        """
        try:
            # Validate theme compatibility on startup
            self.logger.debug("Validating theme system...")
            theme_stats = self.theme_manager.get_theme_statistics()
            self.logger.info(f"Theme system initialized: {theme_stats['total_themes']} themes available")

            # Apply current theme
            current_theme = self.settings.ui.current_theme
            success = self.theme_manager.apply_theme_with_verification(current_theme)

            if success:
                self.logger.info(f"Applied theme: {current_theme}")
                display_name = self.theme_manager.get_theme_display_name(current_theme)
                self.show_status_message(f"Theme: {display_name}", 2000)
            else:
                self.logger.warning(f"Failed to apply preferred theme: {current_theme}")
                # Apply recommended fallback
                recommendations = self.theme_controller.get_theme_recommendations()
                if recommendations:
                    fallback_theme = recommendations[0]
                    self.theme_manager.apply_theme(fallback_theme)
                    self.logger.info(f"Applied fallback theme: {fallback_theme}")

        except Exception as e:
            self.logger.error(f"Failed to setup theme: {e}")
            # Last resort fallback
            self.theme_manager.apply_theme("dark_blue.xml")

    def validate_all_themes(self) -> None:
        """
        Phase 4: Comprehensive theme validation
        Run full theme compatibility test
        """
        try:
            self.logger.info("Starting comprehensive theme validation...")
            self.show_status_message("Validating themes...", 0)  # Persistent message

            # Run validation through theme controller
            validation_results = self.theme_controller.validate_all_themes()

            # Display results
            total = validation_results['total_themes']
            working = len(validation_results['working_themes'])
            failed = len(validation_results['failed_themes'])
            rate = validation_results['compatibility_rate']

            status_msg = f"Theme validation: {working}/{total} working ({rate:.1%})"
            self.show_status_message(status_msg, 5000)

            if failed > 0:
                self.logger.warning(f"Failed themes: {', '.join(validation_results['failed_themes'])}")

            if validation_results['recommendations']:
                for rec in validation_results['recommendations']:
                    self.logger.info(f"Theme recommendation: {rec}")

        except Exception as e:
            self.logger.error(f"Theme validation error: {e}")
            self.show_status_message("Theme validation failed", 3000)

    def run_theme_performance_test(self) -> None:
        """
        Phase 4: Theme performance optimization test
        """
        try:
            self.logger.info("Running theme performance test...")
            self.show_status_message("Testing theme performance...", 0)

            performance_results = self.theme_controller.create_theme_performance_test()

            if performance_results['themes_tested'] > 0:
                avg_time = performance_results['average_switch_time']
                fastest = performance_results['fastest_theme']

                status_msg = f"Theme performance: avg {avg_time:.3f}s (fastest: {fastest})"
                self.show_status_message(status_msg, 5000)

                self.logger.info(f"Theme performance test completed: {status_msg}")
            else:
                self.show_status_message("Performance test failed", 3000)

        except Exception as e:
            self.logger.error(f"Theme performance test error: {e}")
            self.show_status_message("Performance test failed", 3000)

    def setup_connections(self) -> None:
        """Setup signal-slot connections"""
        # Connect theme manager signals
        self.theme_manager.theme_changed.connect(self.on_theme_changed)

        # Connect internal signals
        self.folder_changed.connect(self.on_folder_changed)

    def setup_controller_connections(self) -> None:
        """Setup connections between controllers and main window"""
        # Theme controller connections
        self.theme_controller.theme_applied.connect(self.on_theme_changed)
        self.theme_controller.status_message.connect(self.show_status_message)

        # Toolbar manager theme connections (Phase 4 enhancements)
        self.toolbar_manager.theme_toggle_requested.connect(self.theme_controller.toggle_theme)
        self.toolbar_manager.theme_menu_requested.connect(
            lambda pos: self.theme_controller.show_theme_menu(pos, self)
        )

        # Connect Phase 4 debug features if available
        if hasattr(self.toolbar_manager, 'connect_theme_debug_actions'):
            self.toolbar_manager.connect_theme_debug_actions(
                self.validate_all_themes,
                self.run_theme_performance_test
            )

        # Enable debug mode based on settings (safe access)
        debug_mode = getattr(self.settings, 'debug', None)
        if debug_mode is not None:
            show_theme_debug = getattr(debug_mode, 'show_theme_debug', False)
        else:
            show_theme_debug = False

        if hasattr(self.toolbar_manager, 'set_debug_mode'):
            self.toolbar_manager.set_debug_mode(show_theme_debug)

        # Folder controller connections
        self.folder_controller.folder_opened.connect(self.on_folder_opened)
        self.folder_controller.status_message.connect(self.update_status)

        # Panel controller connections
        self.panel_controller.status_message.connect(self.update_status)

        # Debug controller connections
        self.debug_controller.status_message.connect(self.show_status_message)

        # Toolbar manager connections
        self.toolbar_manager.open_folder_requested.connect(self.open_folder_dialog)
        self.toolbar_manager.theme_toggle_requested.connect(self.theme_controller.toggle_theme)
        self.toolbar_manager.theme_menu_requested.connect(self.on_toolbar_context_menu)

    def on_folder_opened(self, folder_path: str) -> None:
        """Handle folder opened from controller"""
        # Update UI elements with folder info
        if self.current_folder_label:
            self.current_folder_label.setText(f"📁 {folder_path}")
            self.current_folder_label.setToolTip(f"Current folder: {folder_path}")

        # Update file browser to show selected folder
        if hasattr(self, 'file_browser') and self.file_browser:
            self.file_browser.set_root_path(folder_path)

        # Enable navigation buttons
        if self.up_action:
            self.up_action.setEnabled(True)

        # Emit signal
        self.folder_changed.emit(folder_path)

    def restore_window_state(self) -> None:
        """Restore window position and size from settings"""
        window_settings = self.settings.window

        if window_settings.remember_size:
            self.resize(window_settings.width, window_settings.height)

        if window_settings.remember_position:
            self.move(window_settings.x, window_settings.y)

        if window_settings.maximized:
            self.showMaximized()

        self.logger.debug("Window state restored from settings")

    def save_window_state(self) -> None:
        """Save current window position and size to settings"""
        window_settings = self.settings.window

        if not self.isMaximized():
            window_settings.width = self.width()
            window_settings.height = self.height()
            window_settings.x = self.x()
            window_settings.y = self.y()

        window_settings.maximized = self.isMaximized()

        # Save splitter states
        if self.main_splitter:
            splitter_state = self.main_splitter.saveState()
            # Convert QByteArray to bytes for JSON serialization
            self.settings.ui.panel_splitter_state = splitter_state.data()

        self.settings.save()
        self.logger.debug("Window state saved to settings")

    # Folder operations delegated to folder_controller
    def open_folder_dialog(self) -> None:
        """Open folder selection dialog"""
        self.folder_controller.open_folder_dialog(self)

    def open_folder(self, folder_path: str) -> None:
        """Open a specific folder"""
        self.folder_controller.open_folder(folder_path, self)

    # Theme operations delegated to theme_controller
    def toggle_theme(self) -> None:
        """Toggle between selected themes in order"""
        self.theme_controller.toggle_theme()

    def on_toolbar_context_menu(self, position: QPoint) -> None:
        """Handle toolbar context menu request"""
        self.theme_controller.show_theme_menu(position, self)

    def toggle_panel_maximize(self, panel_type: str) -> None:
        """Toggle panel maximization"""
        try:
            if panel_type == 'image':
                is_maximized = self.settings.ui.image_panel_maximized
                self.settings.ui.image_panel_maximized = not is_maximized

                if not is_maximized:
                    # Maximize image panel
                    if self.left_panel:
                        self.left_panel.hide()
                    if self.map_panel:
                        self.map_panel.hide()
                else:
                    # Restore normal view
                    if self.left_panel:
                        self.left_panel.show()
                    if self.map_panel:
                        self.map_panel.show()

            elif panel_type == 'map':
                is_maximized = self.settings.ui.map_panel_maximized
                self.settings.ui.map_panel_maximized = not is_maximized

                if not is_maximized:
                    # Maximize map panel
                    if self.left_panel:
                        self.left_panel.hide()
                    if self.image_panel:
                        self.image_panel.hide()
                else:
                    # Restore normal view
                    if self.left_panel:
                        self.left_panel.show()
                    if self.image_panel:
                        self.image_panel.show()

            self.logger.debug(f"Toggled {panel_type} panel maximization")

        except Exception as e:
            self.logger.error(f"Error toggling panel maximization: {e}")

    def update_status(self, message: str) -> None:
        """Update status bar message"""
        if self.status_label:
            self.status_label.setText(message)
            self.logger.debug(f"Status updated: {message}")

    def show_status_message(self, message: str, timeout: int = 2000) -> None:
        """Show a temporary message in the status bar"""
        if self.status_bar:
            self.status_bar.showMessage(message, timeout)
            self.logger.debug(f"Temporary status message: {message}")

    def on_theme_changed(self, theme_name: str) -> None:
        """
        Handle theme change event
        Phase 4: Enhanced theme change handling with UI feedback
        """
        try:
            # Update settings
            self.settings.ui.current_theme = theme_name

            # Update status bar display
            if self.theme_status_label:
                display_name = self.theme_manager.get_theme_display_name(theme_name)
                category = self.theme_manager.get_theme_category(theme_name)
                icon = "🌙" if category == 'dark' else "☀️"
                self.theme_status_label.setText(f"{icon} {display_name}")

            # Update toolbar button display
            if hasattr(self.toolbar_manager, 'update_theme_display'):
                display_name = self.theme_manager.get_theme_display_name(theme_name)
                self.toolbar_manager.update_theme_display(theme_name, display_name)

            # Apply theme-specific optimizations
            self._apply_theme_specific_optimizations(theme_name)

            # Save settings
            self.settings.save()

            # Emit theme change signal for other components
            self.theme_changed.emit(theme_name)

            # Log with category information
            category = self.theme_manager.get_theme_category(theme_name)
            self.logger.info(f"Theme changed to: {theme_name} ({category} theme)")

        except Exception as e:
            self.logger.error(f"Error handling theme change: {e}")

    def _apply_theme_specific_optimizations(self, theme_name: str) -> None:
        """
        Apply theme-specific UI optimizations
        Phase 4: Theme-specific styling adjustments

        Args:
            theme_name: Current theme name
        """
        try:
            category = self.theme_manager.get_theme_category(theme_name)

            # Apply category-specific optimizations
            if category == 'dark':
                # Dark theme optimizations
                self._apply_dark_theme_optimizations()
            else:
                # Light theme optimizations
                self._apply_light_theme_optimizations()

            # Apply color-specific optimizations
            color = self._extract_theme_color(theme_name)
            self._apply_color_optimizations(color)

            self.logger.debug(f"Applied theme-specific optimizations for {theme_name}")

        except Exception as e:
            self.logger.error(f"Error applying theme optimizations: {e}")

    def _apply_dark_theme_optimizations(self) -> None:
        """Apply optimizations specific to dark themes"""
        # Dark theme specific adjustments could go here
        # For example: adjust icon brightness, modify text contrast, etc.
        pass

    def _apply_light_theme_optimizations(self) -> None:
        """Apply optimizations specific to light themes"""
        # Light theme specific adjustments could go here
        # For example: adjust icon contrast, modify text colors, etc.
        pass

    def _extract_theme_color(self, theme_name: str) -> str:
        """Extract color name from theme name"""
        # Remove 'dark_' or 'light_' prefix and '.xml' suffix
        color = theme_name.replace('dark_', '').replace('light_', '').replace('.xml', '')
        return color.replace('_500', '')  # Remove variant suffixes

    def _apply_color_optimizations(self, color: str) -> None:
        """Apply color-specific optimizations"""
        # Color-specific optimizations could go here
        # For example: adjust accent colors, modify highlighting, etc.
        self.logger.debug(f"Applied color optimizations for: {color}")

    def on_folder_changed(self, folder_path: str) -> None:
        """Handle folder change event"""
        # This can be connected to other components that need to respond to folder changes
        self.logger.debug(f"Folder changed signal received: {folder_path}")

    def _auto_save_settings(self) -> None:
        """Auto-save settings periodically"""
        try:
            self.save_window_state()
            self.logger.debug("Settings auto-saved")
        except Exception as e:
            self.logger.error(f"Failed to auto-save settings: {e}")

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        """Handle window close event"""
        try:
            # Save window state before closing
            self.save_window_state()

            # Stop auto-save timer
            if self.auto_save_timer.isActive():
                self.auto_save_timer.stop()

            self.logger.info("Main window closing")
            if a0:
                a0.accept()

        except Exception as e:
            self.logger.error(f"Error during window close: {e}")
            if a0:
                a0.accept()  # Close anyway

    def setup_widget_connections(self) -> None:
        """Setup signal connections between widgets - delegated to panel controller"""
        try:
            # Panel controller handles all widget connections
            # This avoids duplication and ensures proper coordination
            self.logger.debug("Widget connections delegated to panel controller")

        except Exception as e:
            self.logger.error(f"Error setting up widget connections: {e}")

    # Panel coordination methods delegated to panel_controller
    # Individual handler methods removed to avoid duplication

    def on_fullscreen_requested(self) -> None:
        """Handle fullscreen request from image viewer"""
        try:
            self.toggle_panel_maximize('image')
            self.logger.debug("Fullscreen requested")
        except Exception as e:
            self.logger.error(f"Error handling fullscreen request: {e}")

    def on_map_fullscreen_requested(self) -> None:
        """Handle fullscreen request from map viewer"""
        try:
            self.toggle_panel_maximize('map')
            self.logger.debug("Map fullscreen requested")
        except Exception as e:
            self.logger.error(f"Error handling map fullscreen request: {e}")

    def on_exif_data_loaded(self, file_path: str, exif_data: Dict[str, Any]) -> None:
        """Handle EXIF data loaded signal and update map if GPS coordinates are available"""
        try:
            # GPS座標が含まれている場合のみ地図を更新
            if 'gps_coordinates' in exif_data:
                coordinates = exif_data['gps_coordinates']
                if coordinates and isinstance(coordinates, tuple) and len(coordinates) >= 2:
                    lat: float = float(coordinates[0])
                    lon: float = float(coordinates[1])
                    self.map_viewer.set_current_photo(file_path, lat, lon)
                    self.logger.debug(f"Map updated via EXIF signal for {file_path} at ({lat}, {lon})")

        except Exception as e:
            self.logger.error(f"Error handling EXIF data loaded signal: {e}")

    def update_map_with_folder_images(self) -> None:
        """Update map with all images in current folder that have GPS data"""
        try:
            image_files = self.file_browser.get_image_files_in_current_path()
            photo_locations: Dict[str, Tuple[float, float]] = {}

            for image_file in image_files:
                try:
                    # Temporarily load EXIF to check for GPS
                    from src.modules.exif_info import ExifInfoPanel
                    temp_exif = ExifInfoPanel()
                    temp_exif.load_file_info(image_file)

                    if hasattr(temp_exif, 'get_gps_coordinates'):
                        coordinates = temp_exif.get_gps_coordinates()
                        if coordinates:
                            photo_locations[image_file] = coordinates

                except Exception as e:
                    self.logger.debug(f"No GPS data for {image_file}: {e}")
                    continue

            # Update map with all photo locations
            if photo_locations:
                self.map_viewer.set_photo_locations(photo_locations)
                self.logger.info(f"Updated map with {len(photo_locations)} photo locations")
            else:
                self.map_viewer.clear_map()
                self.logger.debug("No photos with GPS data found")

        except Exception as e:
            self.logger.error(f"Error updating map with folder images: {e}")

    def is_image_file(self, file_path: str) -> bool:
        """Check if the file is a supported image file"""
        try:
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
            return Path(file_path).suffix.lower() in image_extensions
        except Exception:
            return False

    # Debug operations delegated to debug_controller
    # (No methods needed here - controller handles shortcuts directly)
