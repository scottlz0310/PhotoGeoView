"""
Toolbar Manager for PhotoGeoView
Manages toolbar creation, actions, and updates
"""

from PyQt6.QtWidgets import QToolBar, QLabel, QSizePolicy
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QAction

from src.core.logger import get_logger


class ToolbarManager(QObject):
    """
    Manager for toolbar operations
    Handles toolbar setup, action management, and state updates
    """

    # Signals
    open_folder_requested = pyqtSignal()
    back_requested = pyqtSignal()
    forward_requested = pyqtSignal()
    up_requested = pyqtSignal()
    theme_toggle_requested = pyqtSignal()
    theme_menu_requested = pyqtSignal(object)  # QPoint

    def __init__(self, parent=None):
        """Initialize toolbar manager"""
        super().__init__(parent)

        self.logger = get_logger(__name__)

        # Toolbar components
        self.toolbar = None
        self.current_folder_label = None
        self.folder_action = None
        self.back_action = None
        self.forward_action = None
        self.up_action = None
        self.theme_action = None

        self.logger.debug("Toolbar manager initialized")

    def setup_toolbar(self, main_window) -> QToolBar:
        """Setup the main toolbar"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # Folder selection button
        self.folder_action = QAction("📁 Open Folder", main_window)
        self.folder_action.setToolTip("Select folder to browse images")
        self.folder_action.triggered.connect(self.open_folder_requested.emit)
        self.toolbar.addAction(self.folder_action)

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
        self.back_action = QAction("← Back", main_window)
        self.back_action.setToolTip("Go back to previous folder")
        self.back_action.setEnabled(False)  # Initially disabled
        self.back_action.triggered.connect(self.back_requested.emit)
        self.toolbar.addAction(self.back_action)

        self.forward_action = QAction("→ Forward", main_window)
        self.forward_action.setToolTip("Go forward to next folder")
        self.forward_action.setEnabled(False)  # Initially disabled
        self.forward_action.triggered.connect(self.forward_requested.emit)
        self.toolbar.addAction(self.forward_action)

        self.up_action = QAction("↑ Up", main_window)
        self.up_action.setToolTip("Go to parent folder")
        self.up_action.setEnabled(False)  # Initially disabled
        self.up_action.triggered.connect(self.up_requested.emit)
        self.toolbar.addAction(self.up_action)

        self.toolbar.addSeparator()

        # Theme toggle button with enhanced functionality
        self.theme_action = QAction("🎨 Theme", main_window)
        self.theme_action.setToolTip(
            "Left-click: Toggle between selected themes\n"
            "Right-click: Advanced theme options\n"
            "Ctrl+Click: Quick light/dark toggle"
        )
        self.theme_action.triggered.connect(self.theme_toggle_requested.emit)
        self.toolbar.addAction(self.theme_action)

        self.toolbar.addSeparator()

        # Advanced theme actions (Phase 4)
        self.validate_themes_action = QAction("🔍 Validate Themes", main_window)
        self.validate_themes_action.setToolTip("Validate all themes for compatibility")
        self.validate_themes_action.setVisible(False)  # Hidden by default
        self.toolbar.addAction(self.validate_themes_action)

        self.performance_test_action = QAction("⚡ Performance Test", main_window)
        self.performance_test_action.setToolTip("Test theme switching performance")
        self.performance_test_action.setVisible(False)  # Hidden by default
        self.toolbar.addAction(self.performance_test_action)

        # Set up context menu policy for the toolbar itself
        self.toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.toolbar.customContextMenuRequested.connect(self.theme_menu_requested.emit)

        self.logger.debug("Toolbar setup complete with Phase 4 theme enhancements")
        return self.toolbar

    def update_theme_display(self, theme_name: str, theme_display_name: str = None) -> None:
        """
        Update theme button display
        Phase 4: Enhanced theme feedback

        Args:
            theme_name: Current theme name
            theme_display_name: User-friendly display name
        """
        if self.theme_action:
            # Determine theme category and icon
            if 'dark' in theme_name.lower():
                icon = "🌙"
                category = "Dark"
            else:
                icon = "☀️"
                category = "Light"

            # Update button text and tooltip
            display_name = theme_display_name or theme_name.replace('.xml', '').replace('_', ' ').title()
            self.theme_action.setText(f"{icon} {display_name}")

            tooltip = (
                f"Current Theme: {display_name} ({category})\n"
                "Left-click: Toggle between selected themes\n"
                "Right-click: Advanced theme options\n"
                "Ctrl+Click: Quick light/dark toggle"
            )
            self.theme_action.setToolTip(tooltip)

    def set_debug_mode(self, enabled: bool) -> None:
        """
        Show/hide debug theme actions
        Phase 4: Development and testing features

        Args:
            enabled: Whether to show debug actions
        """
        if self.validate_themes_action:
            self.validate_themes_action.setVisible(enabled)
        if self.performance_test_action:
            self.performance_test_action.setVisible(enabled)

        self.logger.debug(f"Debug mode {'enabled' if enabled else 'disabled'} for theme actions")

    def connect_theme_debug_actions(self, validate_callback, performance_callback) -> None:
        """
        Connect debug theme actions to callbacks
        Phase 4: Testing functionality

        Args:
            validate_callback: Function to call for theme validation
            performance_callback: Function to call for performance testing
        """
        if self.validate_themes_action:
            self.validate_themes_action.triggered.connect(validate_callback)
        if self.performance_test_action:
            self.performance_test_action.triggered.connect(performance_callback)

        self.logger.debug("Theme debug actions connected")

    def update_folder_display(self, folder_path: str) -> None:
        """Update the current folder display in toolbar"""
        if self.current_folder_label:
            self.current_folder_label.setText(f"📁 {folder_path}")
            self.current_folder_label.setToolTip(f"Current folder: {folder_path}")

    def set_navigation_enabled(self, back: bool = False, forward: bool = False, up: bool = False) -> None:
        """Enable/disable navigation buttons"""
        if self.back_action:
            self.back_action.setEnabled(back)
        if self.forward_action:
            self.forward_action.setEnabled(forward)
        if self.up_action:
            self.up_action.setEnabled(up)
