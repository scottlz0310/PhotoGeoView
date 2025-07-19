"""
PhotoGeoView Main Window Implementation
Main application window with UI layout and theme integration
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QToolBar, QStatusBar, QLabel,
    QFileDialog, QMessageBox, QFrame, QSizePolicy, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QAction, QCloseEvent
from pathlib import Path
from typing import Dict, Optional

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.ui.theme_manager import ThemeManager
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

        self.setup_connections()
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

        # Current folder display (between Open Folder and Back)
        self.current_folder_label = QLabel("No folder selected")
        self.current_folder_label.setStyleSheet("""
            QLabel {
                padding: 4px 8px;
                margin: 2px;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                color: white;
                font-size: 11px;
                min-width: 150px;
            }
        """)
        self.current_folder_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.toolbar.addWidget(self.current_folder_label)

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
        self.theme_action = QAction("🎨 Theme", self)
        self.theme_action.setToolTip("Toggle between selected themes (right-click to select multiple themes)")
        self.theme_action.triggered.connect(self.toggle_theme)
        self.toolbar.addAction(self.theme_action)

        # Set up context menu policy for the toolbar itself
        self.toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.toolbar.customContextMenuRequested.connect(self.on_toolbar_context_menu)

        # Store actions for later reference
        self.folder_action = folder_action
        self.back_action = back_action
        self.forward_action = forward_action
        self.up_action = up_action

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

        # Map viewer widget
        self.map_viewer = MapViewer()
        self.map_viewer.setMinimumHeight(200)
        layout.addWidget(self.map_viewer)

        # Store references
        self.map_maximize_btn = maximize_btn

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

            # Update toolbar current folder display (show full path)
            self.current_folder_label.setText(f"📁 {folder_path}")
            self.current_folder_label.setToolTip(f"Current folder: {folder_path}")

            # Update file browser to show selected folder
            if hasattr(self, 'file_browser') and self.file_browser:
                self.file_browser.set_root_path(folder_path)

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
        """Toggle between selected themes in order"""
        try:
            selected_themes = self.settings.ui.selected_themes

            # If no themes selected or only one theme, fall back to simple dark/light toggle
            if len(selected_themes) <= 1:
                current_theme = self.settings.ui.current_theme
                if 'dark' in current_theme.lower():
                    new_theme = "light_blue.xml"
                else:
                    new_theme = "dark_blue.xml"

                # Update selection to include both themes for future toggling
                self.settings.ui.selected_themes = [current_theme, new_theme]
                self.settings.ui.theme_toggle_index = 1
            else:
                # Cycle through selected themes
                current_index = self.settings.ui.theme_toggle_index
                next_index = (current_index + 1) % len(selected_themes)
                new_theme = selected_themes[next_index]
                self.settings.ui.theme_toggle_index = next_index

            # Apply the theme
            if self.theme_manager.apply_theme(new_theme):
                self.settings.ui.current_theme = new_theme
                self.settings.save()

                # Show which theme we're on in multi-theme mode
                if len(selected_themes) > 1:
                    theme_position = f" ({self.settings.ui.theme_toggle_index + 1}/{len(selected_themes)})"
                    display_name = new_theme.replace('.xml', '').replace('_', ' ').title()
                    self.update_status(f"Theme: {display_name}{theme_position}")

                self.logger.info(f"Theme toggled to: {new_theme} (index {self.settings.ui.theme_toggle_index})")
            else:
                self.logger.error(f"Failed to apply theme: {new_theme}")

        except Exception as e:
            self.logger.error(f"Error toggling theme: {e}")

    def on_toolbar_context_menu(self, position: QPoint) -> None:
        """Handle toolbar context menu request"""
        # Check if the click was near the theme action
        self.show_theme_menu(position)

    def show_theme_menu(self, position: QPoint) -> None:
        """Show theme selection context menu with multiple selection support"""
        try:
            # Create persistent context menu that doesn't auto-close
            menu = QMenu(self)
            menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
            current_theme = self.settings.ui.current_theme
            selected_themes = self.settings.ui.selected_themes

            # Add header with instructions
            info_action = QAction("🎨 Multi-Theme Selector", self)
            info_action.setEnabled(False)
            font = info_action.font()
            font.setBold(True)
            info_action.setFont(font)
            menu.addAction(info_action)

            instruction_action = QAction("   → Click themes to add/remove from selection", self)
            instruction_action.setEnabled(False)
            menu.addAction(instruction_action)
            menu.addSeparator()

            # Store theme actions for updating display
            self.theme_actions = {}

            # Add available themes to menu with visual indicators
            for theme in self.theme_manager.available_themes:
                display_name = theme.replace('.xml', '').replace('_', ' ').title()

                # Add status indicators
                if theme == current_theme:
                    display_name = f"● {display_name} (Active)"
                elif theme in selected_themes:
                    display_name = f"✓ {display_name}"
                else:
                    display_name = f"   {display_name}"

                action = QAction(display_name, self)
                action.setCheckable(False)

                # Connect with a closure to avoid lambda issues
                def make_toggle_handler(theme_name: str, menu_ref: QMenu):
                    return lambda: self.toggle_theme_in_persistent_menu(theme_name, menu_ref)

                action.triggered.connect(make_toggle_handler(theme, menu))
                menu.addAction(action)
                self.theme_actions[theme] = action

            menu.addSeparator()

            # Add status and control buttons
            selection_count = len(selected_themes)
            status_text = f"📊 Selected: {selection_count} theme{'s' if selection_count != 1 else ''}"

            status_action = QAction(status_text, self)
            status_action.setEnabled(False)
            menu.addAction(status_action)
            self.status_action = status_action  # Store reference for updates

            menu.addSeparator()

            # Utility buttons
            clear_action = QAction("🗑️ Clear All", self)
            clear_action.triggered.connect(lambda: self.clear_and_update_menu(menu))
            menu.addAction(clear_action)

            select_all_action = QAction("✓ Select All", self)
            select_all_action.triggered.connect(lambda: self.select_all_and_update_menu(menu))
            menu.addAction(select_all_action)

            menu.addSeparator()

            # Close button
            close_action = QAction("✅ Done", self)
            close_action.triggered.connect(menu.close)
            font.setBold(True)
            close_action.setFont(font)
            menu.addAction(close_action)

            # Show menu at cursor position (better UX than toolbar position)
            global_pos = self.mapToGlobal(position)
            menu.popup(global_pos)

        except Exception as e:
            self.logger.error(f"Error showing theme menu: {e}")

    def toggle_theme_selection(self, theme_name: str) -> None:
        """Toggle theme selection for multi-theme cycling"""
        try:
            selected_themes = self.settings.ui.selected_themes.copy()

            if theme_name in selected_themes:
                # Remove from selection
                selected_themes.remove(theme_name)
                self.logger.info(f"Removed theme from selection: {theme_name}")
            else:
                # Add to selection
                selected_themes.append(theme_name)
                self.logger.info(f"Added theme to selection: {theme_name}")

            # Update settings
            self.settings.ui.selected_themes = selected_themes

            # Reset toggle index if selection changed
            if len(selected_themes) > 0:
                # Find current theme index in new selection, or reset to 0
                try:
                    current_index = selected_themes.index(self.settings.ui.current_theme)
                    self.settings.ui.theme_toggle_index = current_index
                except ValueError:
                    self.settings.ui.theme_toggle_index = 0

            self.settings.save()

        except Exception as e:
            self.logger.error(f"Error toggling theme selection {theme_name}: {e}")

    def toggle_theme_in_persistent_menu(self, theme_name: str, menu: QMenu) -> None:
        """Toggle theme selection and update the menu without closing it"""
        try:
            selected_themes = self.settings.ui.selected_themes.copy()
            current_theme = self.settings.ui.current_theme

            if theme_name in selected_themes:
                # Remove from selection (but don't allow removing the current theme if it's the only one)
                if len(selected_themes) > 1 or theme_name != current_theme:
                    selected_themes.remove(theme_name)
                    self.logger.info(f"Removed theme from selection: {theme_name}")
            else:
                # Add to selection
                selected_themes.append(theme_name)
                self.logger.info(f"Added theme to selection: {theme_name}")

            # Update settings
            self.settings.ui.selected_themes = selected_themes

            # Update toggle index if current theme is still in selection
            if current_theme in selected_themes:
                self.settings.ui.theme_toggle_index = selected_themes.index(current_theme)
            else:
                self.settings.ui.theme_toggle_index = 0

            self.settings.save()

            # Update menu display immediately
            self.refresh_menu_display(menu)

        except Exception as e:
            self.logger.error(f"Error toggling theme selection {theme_name}: {e}")

    def refresh_menu_display(self, menu: QMenu) -> None:
        """Refresh the menu display to show current selection state"""
        try:
            current_theme = self.settings.ui.current_theme
            selected_themes = self.settings.ui.selected_themes

            # Update theme action texts
            if hasattr(self, 'theme_actions'):
                for theme, action in self.theme_actions.items():
                    display_name = theme.replace('.xml', '').replace('_', ' ').title()

                    if theme == current_theme:
                        display_name = f"● {display_name} (Active)"
                    elif theme in selected_themes:
                        display_name = f"✓ {display_name}"
                    else:
                        display_name = f"   {display_name}"

                    action.setText(display_name)

            # Update status text
            if hasattr(self, 'status_action'):
                selection_count = len(selected_themes)
                status_text = f"📊 Selected: {selection_count} theme{'s' if selection_count != 1 else ''}"
                self.status_action.setText(status_text)

        except Exception as e:
            self.logger.error(f"Error refreshing menu display: {e}")

    def clear_and_update_menu(self, menu: QMenu) -> None:
        """Clear all selections except current theme and update menu"""
        try:
            current_theme = self.settings.ui.current_theme
            self.settings.ui.selected_themes = [current_theme]
            self.settings.ui.theme_toggle_index = 0
            self.settings.save()
            self.logger.info("Cleared all theme selections")

            # Refresh menu
            self.refresh_menu_display(menu)

        except Exception as e:
            self.logger.error(f"Error clearing selections: {e}")

    def select_all_and_update_menu(self, menu: QMenu) -> None:
        """Select all themes and update menu"""
        try:
            # Select all available themes
            self.settings.ui.selected_themes = self.theme_manager.available_themes.copy()

            # Set current theme index
            current_theme = self.settings.ui.current_theme
            if current_theme in self.settings.ui.selected_themes:
                self.settings.ui.theme_toggle_index = self.settings.ui.selected_themes.index(current_theme)

            self.settings.save()
            self.logger.info("Selected all themes")

            # Refresh menu
            self.refresh_menu_display(menu)

        except Exception as e:
            self.logger.error(f"Error selecting all themes: {e}")

    def clear_theme_selection(self) -> None:
        """Clear all theme selections"""
        try:
            self.settings.ui.selected_themes = [self.settings.ui.current_theme]
            self.settings.ui.theme_toggle_index = 0
            self.settings.save()
            self.logger.info("Cleared all theme selections")

        except Exception as e:
            self.logger.error(f"Error clearing theme selection: {e}")

    def apply_selected_themes(self) -> None:
        """Apply the currently selected themes for cycling"""
        try:
            selected_themes = self.settings.ui.selected_themes
            if not selected_themes:
                return

            # Ensure current theme is in the selection
            if self.settings.ui.current_theme not in selected_themes:
                selected_themes.insert(0, self.settings.ui.current_theme)
                self.settings.ui.selected_themes = selected_themes

            self.settings.save()
            self.logger.info(f"Applied theme selection: {selected_themes}")

        except Exception as e:
            self.logger.error(f"Error applying selected themes: {e}")

    def select_theme(self, theme_name: str) -> None:
        """Select and apply a specific theme directly"""
        try:
            if self.theme_manager.apply_theme(theme_name):
                self.settings.ui.current_theme = theme_name

                # Update toggle index to match current theme if it's in selection
                selected_themes = self.settings.ui.selected_themes
                if theme_name in selected_themes:
                    self.settings.ui.theme_toggle_index = selected_themes.index(theme_name)

                self.settings.save()
                self.logger.info(f"Theme selected: {theme_name}")
            else:
                self.logger.error(f"Failed to apply theme: {theme_name}")

        except Exception as e:
            self.logger.error(f"Error selecting theme {theme_name}: {e}")

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

    def setup_widget_connections(self) -> None:
        """Setup signal connections between widgets"""
        try:
            # File browser connections
            self.file_browser.folder_changed.connect(self.on_folder_changed_handler)
            self.file_browser.file_selected.connect(self.on_file_selected_handler)

            # Thumbnail view connections
            self.thumbnail_view.image_selected.connect(self.on_image_selected_handler)
            self.thumbnail_view.image_double_clicked.connect(self.on_image_double_clicked_handler)

            # Image viewer connections
            self.image_viewer.fullscreen_requested.connect(self.on_fullscreen_requested)
            self.image_viewer.image_changed.connect(self.on_image_viewer_changed)

            # Map viewer connections
            self.map_viewer.fullscreen_requested.connect(self.on_map_fullscreen_requested)
            self.map_viewer.marker_clicked.connect(self.on_map_marker_clicked)

            self.logger.debug("Widget connections established")

        except Exception as e:
            self.logger.error(f"Error setting up widget connections: {e}")

    def on_folder_changed_handler(self, folder_path: str) -> None:
        """Handle folder change from file browser"""
        try:
            # Get image files in the folder
            image_files = self.file_browser.get_image_files_in_current_path()

            # Update thumbnail view
            self.thumbnail_view.load_images(image_files)

            # Clear EXIF panel
            self.exif_panel.clear_info()

            self.logger.info(f"Folder changed to: {folder_path}, found {len(image_files)} images")

        except Exception as e:
            self.logger.error(f"Error handling folder change: {e}")

    def on_file_selected_handler(self, file_path: str) -> None:
        """Handle file selection from file browser"""
        try:
            # Update EXIF panel
            self.exif_panel.load_file_info(file_path)

            # If it's an image file, load it in the image viewer
            if self.is_image_file(file_path):
                # Get all images in current folder for navigation
                image_files = self.file_browser.get_image_files_in_current_path()

                # Find the index of the selected file
                try:
                    current_index = image_files.index(file_path)
                except ValueError:
                    current_index = 0

                # Set the image list with correct index
                self.image_viewer.set_image_list(image_files, current_index)

                # Update map with GPS location if available
                self.update_map_for_image(file_path)

            # Update status
            self.update_status(f"Selected: {Path(file_path).name}")

            self.logger.debug(f"File selected: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling file selection: {e}")

    def on_image_selected_handler(self, file_path: str) -> None:
        """Handle image selection from thumbnail view"""
        try:
            # Update EXIF panel
            self.exif_panel.load_file_info(file_path)

            # Load image in viewer
            image_files = self.file_browser.get_image_files_in_current_path()

            # Find the index of the selected file
            try:
                current_index = image_files.index(file_path)
            except ValueError:
                current_index = 0

            # Set the image list with correct index
            self.image_viewer.set_image_list(image_files, current_index)

            # Update map with GPS location if available
            self.update_map_for_image(file_path)

            # Update status
            self.update_status(f"Selected: {Path(file_path).name}")

            self.logger.debug(f"Image selected from thumbnails: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling image selection: {e}")

    def on_image_double_clicked_handler(self, file_path: str) -> None:
        """Handle image double-click from thumbnail view"""
        try:
            # Open image in viewer with fullscreen
            image_files = self.file_browser.get_image_files_in_current_path()

            # Find the index of the selected file
            try:
                current_index = image_files.index(file_path)
            except ValueError:
                current_index = 0

            # Set the image list with correct index
            self.image_viewer.set_image_list(image_files, current_index)

            # Trigger fullscreen mode
            self.on_fullscreen_requested()

            self.update_status(f"Opening: {Path(file_path).name}")
            self.logger.info(f"Image double-clicked: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling image double-click: {e}")

    def on_fullscreen_requested(self) -> None:
        """Handle fullscreen request from image viewer"""
        try:
            self.toggle_panel_maximize('image')
            self.logger.debug("Fullscreen requested")
        except Exception as e:
            self.logger.error(f"Error handling fullscreen request: {e}")

    def on_image_viewer_changed(self, image_path: str) -> None:
        """Handle image change in viewer (from navigation)"""
        try:
            # Update EXIF panel
            self.exif_panel.load_file_info(image_path)

            # Update status
            self.update_status(f"Viewing: {Path(image_path).name}")

            self.logger.debug(f"Image viewer changed to: {image_path}")
        except Exception as e:
            self.logger.error(f"Error handling image viewer change: {e}")

    def on_map_fullscreen_requested(self) -> None:
        """Handle fullscreen request from map viewer"""
        try:
            self.toggle_panel_maximize('map')
            self.logger.debug("Map fullscreen requested")
        except Exception as e:
            self.logger.error(f"Error handling map fullscreen request: {e}")

    def on_map_marker_clicked(self, photo_path: str) -> None:
        """Handle marker click from map viewer"""
        try:
            # Load the clicked photo in image viewer
            image_files = self.file_browser.get_image_files_in_current_path()

            if photo_path in image_files:
                try:
                    current_index = image_files.index(photo_path)
                    self.image_viewer.set_image_list(image_files, current_index)

                    # Update EXIF panel
                    self.exif_panel.load_file_info(photo_path)

                    # Update thumbnail selection (if method exists)
                    # self.thumbnail_view.select_image(photo_path)

                    self.update_status(f"Viewing: {Path(photo_path).name}")
                    self.logger.info(f"Map marker clicked for: {photo_path}")
                except ValueError:
                    self.logger.warning(f"Photo not found in current folder: {photo_path}")

        except Exception as e:
            self.logger.error(f"Error handling map marker click: {e}")

    def update_map_for_image(self, image_path: str) -> None:
        """Update map display for the selected image"""
        try:
            # Get GPS coordinates from EXIF panel
            if hasattr(self.exif_panel, 'get_gps_coordinates'):
                coordinates = self.exif_panel.get_gps_coordinates()
                if coordinates:
                    lat, lon = coordinates
                    self.map_viewer.set_current_photo(image_path, lat, lon)
                    self.logger.debug(f"Updated map for {image_path} at ({lat}, {lon})")
                else:
                    # No GPS data available
                    self.map_viewer.set_current_photo(image_path)
                    self.logger.debug(f"No GPS data for {image_path}")
            else:
                self.logger.warning("EXIF panel doesn't support GPS coordinate extraction")

        except Exception as e:
            self.logger.error(f"Error updating map for image: {e}")

    def on_exif_data_loaded(self, file_path: str, exif_data: dict) -> None:
        """Handle EXIF data loaded signal and update map if GPS coordinates are available"""
        try:
            # GPS座標が含まれている場合のみ地図を更新
            if 'gps_coordinates' in exif_data:
                coordinates = exif_data['gps_coordinates']
                if coordinates and isinstance(coordinates, tuple) and len(coordinates) == 2:
                    lat, lon = coordinates
                    self.map_viewer.set_current_photo(file_path, lat, lon)
                    self.logger.debug(f"Map updated via EXIF signal for {file_path} at ({lat}, {lon})")

        except Exception as e:
            self.logger.error(f"Error handling EXIF data loaded signal: {e}")

    def update_map_with_folder_images(self) -> None:
        """Update map with all images in current folder that have GPS data"""
        try:
            image_files = self.file_browser.get_image_files_in_current_path()
            photo_locations = {}

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
