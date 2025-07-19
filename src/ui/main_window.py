"""
PhotoGeoView Main Window Implementation
Main application window with UI layout and theme integration
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QToolBar, QStatusBar, QLabel,
    QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QCloseEvent
from pathlib import Path
from typing import Optional

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.ui.theme_manager import ThemeManager

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

        # Initialize UI
        self.setup_ui()
        self.setup_theme()
        self.setup_connections()
        self.restore_window_state()

        # Start auto-save if enabled
        if self.settings.advanced.auto_save_settings:
            interval = self.settings.advanced.save_interval_seconds * 1000
            self.auto_save_timer.start(interval)

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

        # Create toolbar
        self.setup_toolbar()

        # Create main content area with splitters
        self.setup_content_area()

        # Add content area to main layout
        main_layout.addWidget(self.main_splitter)

        # Create status bar
        self.setup_status_bar()

        self.logger.debug("Main UI layout setup complete")

    def setup_toolbar(self) -> None:
        """Setup the main toolbar"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(self.toolbar)

        # Folder selection button
        folder_action = QAction("📁 Open Folder", self)
        folder_action.setToolTip("Select folder to browse images")
        folder_action.triggered.connect(self.open_folder_dialog)
        self.toolbar.addAction(folder_action)

        self.toolbar.addSeparator()

        # Navigation buttons
        back_action = QAction("← Back", self)
        back_action.setToolTip("Go back to previous folder")
        back_action.setEnabled(False)  # Initially disabled
        self.toolbar.addAction(back_action)

        forward_action = QAction("→ Forward", self)
        forward_action.setToolTip("Go forward to next folder")
        forward_action.setEnabled(False)  # Initially disabled
        self.toolbar.addAction(forward_action)

        up_action = QAction("↑ Up", self)
        up_action.setToolTip("Go to parent folder")
        up_action.setEnabled(False)  # Initially disabled
        self.toolbar.addAction(up_action)

        self.toolbar.addSeparator()

        # Theme toggle button
        theme_action = QAction("🎨 Theme", self)
        theme_action.setToolTip("Toggle theme (right-click for more options)")
        theme_action.triggered.connect(self.toggle_theme)
        self.toolbar.addAction(theme_action)

        # Store actions for later reference
        self.folder_action = folder_action
        self.back_action = back_action
        self.forward_action = forward_action
        self.up_action = up_action
        self.theme_action = theme_action

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
        """Create the left panel for file browsing"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumWidth(250)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)

        # Address bar placeholder
        address_label = QLabel("📁 Current Folder: (No folder selected)")
        address_label.setStyleSheet("padding: 4px; border: 1px solid gray; background-color: #f0f0f0;")
        layout.addWidget(address_label)

        # File browser placeholder
        browser_label = QLabel("🗂️ File Browser\n\n(Select a folder to browse images)")
        browser_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browser_label.setMinimumHeight(200)
        browser_label.setStyleSheet("border: 1px dashed gray; color: gray;")
        layout.addWidget(browser_label)

        # Thumbnail area placeholder
        thumbnail_label = QLabel("🖼️ Thumbnails\n\n(Images will appear here)")
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setMinimumHeight(150)
        thumbnail_label.setStyleSheet("border: 1px dashed gray; color: gray;")
        layout.addWidget(thumbnail_label)

        # EXIF info placeholder
        exif_label = QLabel("ℹ️ EXIF Information\n\n(Select an image to view details)")
        exif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        exif_label.setMinimumHeight(100)
        exif_label.setStyleSheet("border: 1px dashed gray; color: gray;")
        layout.addWidget(exif_label)

        # Store references for later access
        self.address_label = address_label
        self.browser_label = browser_label
        self.thumbnail_label = thumbnail_label
        self.exif_label = exif_label

        return panel

    def create_image_panel(self) -> QFrame:
        """Create the image display panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(200)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)

        # Panel header with maximize button
        header = QHBoxLayout()
        title_label = QLabel("🖼️ Image Viewer")
        title_label.setStyleSheet("font-weight: bold;")

        maximize_btn = QPushButton("⛶")
        maximize_btn.setMaximumSize(30, 30)
        maximize_btn.setToolTip("Maximize image panel")
        maximize_btn.clicked.connect(lambda: self.toggle_panel_maximize('image'))

        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(maximize_btn)
        layout.addLayout(header)

        # Image display area placeholder
        image_area = QLabel("🖼️ Image Preview\n\n(Select an image to display)")
        image_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_area.setMinimumHeight(200)
        image_area.setStyleSheet("border: 2px dashed gray; color: gray; background-color: #fafafa;")
        layout.addWidget(image_area)

        # Store references
        self.image_maximize_btn = maximize_btn
        self.image_area = image_area

        return panel

    def create_map_panel(self) -> QFrame:
        """Create the map display panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(200)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)

        # Panel header with maximize button
        header = QHBoxLayout()
        title_label = QLabel("🗺️ Map Viewer")
        title_label.setStyleSheet("font-weight: bold;")

        maximize_btn = QPushButton("⛶")
        maximize_btn.setMaximumSize(30, 30)
        maximize_btn.setToolTip("Maximize map panel")
        maximize_btn.clicked.connect(lambda: self.toggle_panel_maximize('map'))

        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(maximize_btn)
        layout.addLayout(header)

        # Map display area placeholder
        map_area = QLabel("🗺️ Map Display\n\n(GPS location will appear here)")
        map_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        map_area.setMinimumHeight(200)
        map_area.setStyleSheet("border: 2px dashed gray; color: gray; background-color: #fafafa;")
        layout.addWidget(map_area)

        # Store references
        self.map_maximize_btn = maximize_btn
        self.map_area = map_area

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
        """Setup and apply the current theme"""
        try:
            current_theme = self.settings.ui.current_theme
            self.theme_manager.apply_theme(current_theme)
            self.logger.info(f"Applied theme: {current_theme}")
        except Exception as e:
            self.logger.error(f"Failed to apply theme: {e}")
            # Fallback to default theme
            self.theme_manager.apply_theme("dark_blue.xml")

    def setup_connections(self) -> None:
        """Setup signal-slot connections"""
        # Connect theme manager signals
        self.theme_manager.theme_changed.connect(self.on_theme_changed)

        # Connect internal signals
        self.folder_changed.connect(self.on_folder_changed)

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

    def open_folder_dialog(self) -> None:
        """Open folder selection dialog"""
        try:
            folder = QFileDialog.getExistingDirectory(
                self,
                "Select Image Folder",
                self.settings.folders.last_opened_folder
            )

            if folder:
                self.open_folder(folder)
        except Exception as e:
            self.logger.error(f"Error opening folder dialog: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open folder dialog: {e}")

    def open_folder(self, folder_path: str) -> None:
        """Open a specific folder"""
        try:
            folder_path = Path(folder_path).resolve().as_posix()

            # Update settings
            self.settings.folders.last_opened_folder = folder_path
            self.settings.add_recent_folder(folder_path)

            # Update UI
            self.address_label.setText(f"📁 Current Folder: {folder_path}")
            self.browser_label.setText(f"🗂️ File Browser\n\nLoading files from:\n{folder_path}")

            # Enable navigation buttons
            self.up_action.setEnabled(True)

            # Emit signal
            self.folder_changed.emit(folder_path)

            # Update status
            self.update_status(f"Opened folder: {folder_path}")

            self.logger.info(f"Opened folder: {folder_path}")

        except Exception as e:
            self.logger.error(f"Error opening folder {folder_path}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open folder: {e}")

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes"""
        try:
            current_theme = self.settings.ui.current_theme

            # Simple toggle between dark and light
            if 'dark' in current_theme.lower():
                new_theme = "light_blue.xml"
            else:
                new_theme = "dark_blue.xml"

            self.theme_manager.apply_theme(new_theme)
            self.settings.ui.current_theme = new_theme
            self.settings.save()

            self.logger.info(f"Theme toggled to: {new_theme}")

        except Exception as e:
            self.logger.error(f"Error toggling theme: {e}")

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
                    self.image_maximize_btn.setText("⛷")
                    self.image_maximize_btn.setToolTip("Restore image panel")
                else:
                    # Restore normal view
                    if self.left_panel:
                        self.left_panel.show()
                    if self.map_panel:
                        self.map_panel.show()
                    self.image_maximize_btn.setText("⛶")
                    self.image_maximize_btn.setToolTip("Maximize image panel")

            elif panel_type == 'map':
                is_maximized = self.settings.ui.map_panel_maximized
                self.settings.ui.map_panel_maximized = not is_maximized

                if not is_maximized:
                    # Maximize map panel
                    if self.left_panel:
                        self.left_panel.hide()
                    if self.image_panel:
                        self.image_panel.hide()
                    self.map_maximize_btn.setText("⛷")
                    self.map_maximize_btn.setToolTip("Restore map panel")
                else:
                    # Restore normal view
                    if self.left_panel:
                        self.left_panel.show()
                    if self.image_panel:
                        self.image_panel.show()
                    self.map_maximize_btn.setText("⛶")
                    self.map_maximize_btn.setToolTip("Maximize map panel")

            self.logger.debug(f"Toggled {panel_type} panel maximization")

        except Exception as e:
            self.logger.error(f"Error toggling panel maximization: {e}")

    def update_status(self, message: str) -> None:
        """Update status bar message"""
        if self.status_label:
            self.status_label.setText(message)
            self.logger.debug(f"Status updated: {message}")

    def on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change event"""
        self.settings.ui.current_theme = theme_name
        if self.theme_status_label:
            self.theme_status_label.setText(f"Theme: {theme_name}")

        self.theme_changed.emit(theme_name)
        self.logger.info(f"Theme changed to: {theme_name}")

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
