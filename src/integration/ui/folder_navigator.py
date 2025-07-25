"""
Enhanced Folder Navigator for AI Integration

Combines CursorBLD's folder navigation with Kiro optimization:
- CursorBLD: Intuitive folder browsing and history management
- Kiro: Performancetion, error handling, accessibility

Author: Kiro AI Integration System
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTreeView, QFileSystemModel, QLabel, QComboBox, QFrame,
    QFileDialog, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex, QTimer
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem

from ..models import AIComponent
from ..config_manager import ConfigManager
from ..state_manager import StateManager
from ..error_handling import IntegratedErrorHandler, ErrorCategory
from ..logging_system import LoggerSystem


class EnhancedFolderNavigator(QWidget):
    """
    Enhanced folder navigator combining CursorBLD navigation with Kiro optimization

    Features:
    - CursorBLD's intuitive folder browsing and history
    - Kiro's performance optimization and error handling
    - Accessibility enhancements and responsive design
    - Smart folder filtering and bookmarks
    """

    # Signals
    folder_selected = pyqtSignal(Path)
    folder_changed = pyqtSignal(Path)
    navigation_error = pyqtSignal(str, str)  # error_type, message

    def __init__(self,
                 config_manager: ConfigManager,
                 state_manager: StateManager,
                 logger_system: LoggerSystem = None):
        """
        Initialize the enhanced folder navigator

        Args:
            config_manager: Configuration manager instance
            state_manager: State manager instance
            logger_system: Logging system instance
        """
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Navigation state
        self.current_folder: Optional[Path] = None
        self.folder_history: List[Path] = []
        self.bookmarks: List[Path] = []
        self.max_history = 20

        # UI components
        self.address_bar: Optional[QLineEdit] = None
        self.folder_tree: Optional[QTreeView] = None
        self.file_system_model: Optional[QFileSystemModel] = None
        self.history_combo: Optional[QComboBox] = None

        # Performance optimization
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._delayed_folder_update)

        # Initialize UI
        self._initialize_ui()
        self._load_settings()
        self._connect_signals()

        self.logger_system.log_ai_operation(
            AIComponent.CURSOR,
            "folder_navigator_init",
            "Enhanced folder navigator initialized"
        )

    def _initialize_ui(self):
        """Initialize the user interface"""

        try:
            # Main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(5, 5, 5, 5)
            main_layout.setSpacing(5)

            # Create navigation controls
            self._create_navigation_controls()
            main_layout.addWidget(self.nav_controls)

            # Create folder tree
            self._create_folder_tree()
            main_layout.addWidget(self.folder_tree, 1)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "folder_navigator_ui_init"},
                AIComponent.CURSOR
            )

    def _create_navigation_controls(self):
        """Create navigation controls (CursorBLD style)"""

        self.nav_controls = QFrame()
        self.nav_controls.setFrameStyle(QFrame.Shape.StyledPanel)
        self.nav_controls.setMaximumHeight(80)

        nav_layout = QVBoxLayout(self.nav_controls)
        nav_layout.setContentsMargins(5, 5, 5, 5)
        nav_layout.setSpacing(5)

        # First row: navigation buttons and address bar
        first_row = QHBoxLayout()

        # Navigation buttons
        self.back_btn = QPushButton("←")
        self.back_btn.setMaximumWidth(30)
        self.back_btn.setToolTip("Go back")
        self.back_btn.clicked.connect(self._go_back)
        first_row.addWidget(self.back_btn)

        self.forward_btn = QPushButton("→")
        self.forward_btn.setMaximumWidth(30)
        self.forward_btn.setToolTip("Go forward")
        self.forward_btn.clicked.connect(self._go_forward)
        first_row.addWidget(self.forward_btn)

        self.up_btn = QPushButton("↑")
        self.up_btn.setMaximumWidth(30)
        self.up_btn.setToolTip("Go up one level")
        self.up_btn.clicked.connect(self._go_up)
        first_row.addWidget(self.up_btn)

        self.home_btn = QPushButton("🏠")
        self.home_btn.setMaximumWidth(30)
        self.home_btn.setToolTip("Go to home directory")
        self.home_btn.clicked.connect(self._go_home)
        first_row.addWidget(self.home_btn)

        # Address bar
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Enter folder path...")
        self.address_bar.returnPressed.connect(self._navigate_to_address)
        first_row.addWidget(self.address_bar, 1)

        # Browse button
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.open_folder_dialog)
        first_row.addWidget(browse_btn)

        nav_layout.addLayout(first_row)

        # Second row: history and bookmarks
        second_row = QHBoxLayout()

        # History dropdown
        history_label = QLabel("Recent:")
        second_row.addWidget(history_label)

        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(200)
        self.history_combo.currentTextChanged.connect(self._navigate_to_history)
        second_row.addWidget(self.history_combo, 1)

        # Bookmark button
        bookmark_btn = QPushButton("★")
        bookmark_btn.setMaximumWidth(30)
        bookmark_btn.setToolTip("Bookmark current folder")
        bookmark_btn.clicked.connect(self._bookmark_current_folder)
        second_row.addWidget(bookmark_btn)

        nav_layout.addLayout(second_row)

    def _create_folder_tree(self):
        """Create folder tree view (CursorBLD design with Kiro optimization)"""

        try:
            # Create tree view
            self.folder_tree = QTreeView()
            self.folder_tree.setHeaderHidden(True)
            self.folder_tree.setRootIsDecorated(True)
            self.folder_tree.setAlternatingRowColors(True)

            # Create file system model
            self.file_system_model = QFileSystemModel()
            self.file_system_model.setRootPath("")
            self.file_system_model.setFilter(
                self.file_system_model.filter() |
                self.file_system_model.Filter.NoDotAndDotDot
            )

            # Set model to tree view
            self.folder_tree.setModel(self.file_system_model)

            # Hide unnecessary columns
            for i in range(1, self.file_system_model.columnCount()):
                self.folder_tree.hideColumn(i)

            # Connect selection signal
            self.folder_tree.clicked.connect(self._on_tree_item_clicked)
            self.folder_tree.doubleClicked.connect(self._on_tree_item_double_clicked)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "folder_tree_create"},
                AIComponent.CURSOR
            )

    def _load_settings(self):
        """Load settings and restore state""

        try:
            # Load folder history
            history_data = self.config_manager.get_setting("ui.folder_history", [])
            self.folder_history = [Path(p) for p in history_data if Path(p).exists()]

            # Load bookmarks
            bookmarks_data = self.config_manager.get_setting("ui.bookmarks", [])
            self.bookmarks = [Path(p) for p in bookmarks_data if Path(p).exists()]

            # Load current folder
            current_folder_str = self.config_manager.get_setting("ui.current_folder")
            if current_folder_str:
                current_folder = Path(current_folder_str)
                if current_folder.exists():
                    self.navigate_to_folder(current_folder)
                else:
                    self.navigate_to_folder(Path.home())
            else:
                self.navigate_to_folder(Path.home())

            # Update UI
            self._update_history_combo()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "settings_load"},
                AIComponent.CURSOR
            )

    def _connect_signals(self):
        """Connect internal signals"""

        # Connect state manager changes
        self.state_manager.add_change_listener("current_folder", self._on_current_folder_changed)

    # Public methods

    def navigate_to_folder(self, folder_path: Path) -> bool:
        """Navigate to the specified folder"""

        try:
            if not folder_path.exists() or not folder_path.is_dir():
                self.navigation_error.emit("invalid_path", f"Invalid folder: {folder_path}")
                return False

            # Update current folder
            old_folder = self.current_folder
            self.current_folder = folder_path

            # Add to history
            if old_folder and old_folder != folder_path:
                self._add_to_history(old_folder)

            # Update UI
            self._update_ui_for_folder(folder_path)

            # Update configuration
            self.config_manager.set_setting("ui.current_folder", str(folder_path))

            # Emit signals
            self.folder_selected.emit(folder_path)
            self.folder_changed.emit(folder_path)

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "folder_navigate",
                f"Navigated to: {folder_path}"
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "navigate_to_folder", "folder": str(folder_path)},
                AIComponent.CURSOR
            )
            return False

    def open_folder_dialog(self):
        """Open folder selection dialog"""

        try:
            initial_dir = str(self.current_folder) if self.current_folder else str(Path.home())

            folder = QFileDialog.getExistingDirectory(
                self,
                "Select Folder",
                initial_dir
            )

            if folder:
                self.navigate_to_folder(Path(folder))

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "folder_dialog"},
                AIComponent.CURSOR
            )

    def get_current_folder(self) -> Optional[Path]:
        """Get the current folder"""
        return self.current_folder

    def get_folder_history(self) -> List[Path]:
        """Get folder history"""
        return self.folder_history.copy()

    def get_bookmarks(self) -> List[Path]:
        """Get bookmarks"""
        return self.bookmarks.copy()

    # Event handlers

    def _on_tree_item_clicked(self, index: QModelIndex):
        """Handle tree item click"""

        try:
            if index.isValid():
                file_path = Path(self.file_system_model.filePath(index))

                if file_path.is_dir():
                    # Delay navigation to avoid rapid updates
                    self.update_timer.stop()
                    self.update_timer.start(100)  # 100ms delay
                    self._pending_folder = file_path

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "tree_item_click"},
                AIComponent.CURSOR
            )

    def _on_tree_item_double_clicked(self, index: QModelIndex):
        """Handle tree item double click"""

        try:
            if index.isValid():
                file_path = Path(self.file_system_model.filePath(index))

                if file_path.is_dir():
                    self.navigate_to_folder(file_path)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "tree_item_double_click"},
                AIComponent.CURSOR
            )

    def _delayed_folder_update(self):
        """Handle delayed folder update (Kiro optimization)"""

        if hasattr(self, '_pending_folder'):
            folder = self._pending_folder
            delattr(self, '_pending_folder')

            # Only navigate if it's different from current
            if folder != self.current_folder:
                self.navigate_to_folder(folder)

    def _navigate_to_address(self):
        """Navigate to address bar path"""

        try:
            address = self.address_bar.text().strip()
            if address:
                folder_path = Path(address).expanduser().resolve()
                self.navigate_to_folder(folder_path)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "navigate_to_address", "address": address},
                AIComponent.CURSOR
            )

    def _navigate_to_history(self, folder_str: str):
        """Navigate to folder from history"""

        try:
            if folder_str and folder_str != "Select folder...":
                folder_path = Path(folder_str)
                if folder_path.exists():
                    self.navigate_to_folder(folder_path)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "navigate_to_history", "folder": folder_str},
                AIComponent.CURSOR
            )

    def _go_back(self):
        """Go back in history"""

        if self.folder_history:
            previous_folder = self.folder_history.pop()
            if previous_folder.exists():
                self.navigate_to_folder(previous_folder)

    def _go_forward(self):
        """Go forward in history (placeholder)"""

        # TODO: Implement forward navigation
        pass

    def _go_up(self):
        """Go up one directory level"""

        if self.current_folder and self.current_folder.parent != self.current_folder:
            self.navigate_to_folder(self.current_folder.parent)

    def _go_home(self):
        """Go to home directory"""

        self.navigate_to_folder(Path.home())

    def _bookmark_current_folder(self):
        """Bookmark the current folder"""

        try:
            if self.current_folder and self.current_folder not in self.bookmarks:
                self.bookmarks.append(self.current_folder)

                # Save bookmarks
                bookmarks_data = [str(p) for p in self.bookmarks]
                self.config_manager.set_setting("ui.bookmarks", bookmarks_data)

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR,
                    "folder_bookmark",
                    f"Bookmarked: {self.current_folder}"
                )

                QMessageBox.information(
                    self,
                    "Bookmark Added",
                    f"Folder bookmarked: {self.current_folder.name}"
                )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "bookmark_folder"},
                AIComponent.CURSOR
            )

    def _on_current_folder_changed(self, key: str, old_value: Any, new_value: Any):
        """Handle current folder change from state manager"""

        if isinstance(new_value, Path) and new_value != self.current_folder:
            self.navigate_to_folder(new_value)

    # UI update methods

    def _update_ui_for_folder(self, folder_path: Path):
        """Update UI elements for the new folder"""

        try:
            # Update address bar
            self.address_bar.setText(str(folder_path))

            # Update tree view selection
            index = self.file_system_model.index(str(folder_path))
            if index.isValid():
                self.folder_tree.setCurrentIndex(index)
                self.folder_tree.scrollTo(index)

            # Update navigation buttons
            self.back_btn.setEnabled(len(self.folder_history) > 0)
            self.up_btn.setEnabled(folder_path.parent != folder_path)

            # Update history combo
            self._update_history_combo()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "ui_update", "folder": str(folder_path)},
                AIComponent.CURSOR
            )

    def _add_to_history(self, folder_path: Path):
        """Add folder to history"""

        try:
            # Remove if already in history
            if folder_path in self.folder_history:
                self.folder_history.remove(folder_path)

            # Add to beginning
            self.folder_history.insert(0, folder_path)

            # Limit history size
            if len(self.folder_history) > self.max_history:
                self.folder_history = self.folder_history[:self.max_history]

            # Save to configuration
            history_data = [str(p) for p in self.folder_history]
            self.config_manager.set_setting("ui.folder_history", history_data)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "add_to_history", "folder": str(folder_path)},
                AIComponent.CURSOR
            )

    def _update_history_combo(self):
        """Update history combo box"""

        try:
            self.history_combo.clear()
            self.history_combo.addItem("Select folder...")

            for folder in self.folder_history:
                if folder.exists():
                    self.history_combo.addItem(str(folder))

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "history_combo_update"},
                AIComponent.CURSOR
            )

    # Context menu

    def contextMenuEvent(self, event):
        """Show context menu"""

        try:
            menu = QMenu(self)

            # Navigation actions
            if self.current_folder:
                open_action = menu.addAction("Open in File Manager")
                open_action.triggered.connect(self._open_in_file_manager)

                menu.addSeparator()

                bookmark_action = menu.addAction("Bookmark This Folder")
                bookmark_action.triggered.connect(self._bookmark_current_folder)

            # Bookmarks submenu
            if self.bookmarks:
                bookmarks_menu = menu.addMenu("Bookmarks")

                for bookmark in self.bookmarks:
                    if bookmark.exists():
                        action = bookmarks_menu.addAction(bookmark.name)
                        action.triggered.connect(
                            lambda checked, path=bookmark: self.navigate_to_folder(path)
                        )

                bookmarks_menu.addSeparator()
                clear_bookmarks_action = bookmarks_menu.addAction("Clear All Bookmarks")
                clear_bookmarks_action.triggered.connect(self._clear_bookmarks)

            menu.addSeparator()

            # History actions
            clear_history_action = menu.addAction("Clear History")
            clear_history_action.triggered.connect(self._clear_history)

            menu.exec(event.globalPos())

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "context_menu"},
                AIComponent.CURSOR
            )

    def _open_in_file_manager(self):
        """Open current folder in system file manager"""

        try:
            if self.current_folder:
                import subprocess
                import platform

                system = platform.system()
                if system == "Windows":
                    subprocess.run(["explorer", str(self.current_folder)])
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", str(self.current_folder)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(self.current_folder)])

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "open_in_file_manager"},
                AIComponent.CURSOR
            )

    def _clear_bookmarks(self):
        """Clear all bookmarks"""

        try:
            self.bookmarks.clear()
            self.config_manager.set_setting("ui.bookmarks", [])

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "bookmarks_clear",
                "All bookmarks cleared"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "clear_bookmarks"},
                AIComponent.CURSOR
            )

    def _clear_history(self):
        """Clear folder history"""

        try:
            self.folder_history.clear()
            self.config_manager.set_setting("ui.folder_history", [])
            self._update_history_combo()

            self.logger_system.log_ai_operation(
                AIComponent.CURSOR,
                "history_clear",
                "Folder history cleared"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "clear_history"},
                AIComponent.CURSOR
            )

    # Accessibility features (Kiro enhancement)

    def set_accessibility_mode(self, enabled: bool):
        """Enable or disable accessibility features"""

        try:
            if enabled:
                # Increase font size
                font = self.font()
                font.setPointSize(font.pointSize() + 2)
                self.setFont(font)

                # Add keyboard shortcuts
                self.address_bar.setToolTip("Press Enter to navigate to this path")

                # Enable focus indicators
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "accessibility_mode",
                f"Accessibility mode {'enabled' if enabled else 'disabled'}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR,
                {"operation": "accessibility_mode", "enabled": enabled},
                AIComponent.KIRO
            )

    # Performance optimization (Kiro enhancement)

    def optimize_for_large_directories(self, enabled: bool = True):
        """Optimize for large directories"""

        try:
            if enabled:
                # Reduce update frequency
                self.update_timer.setInterval(200)  # Increase delay

                # Limit visible items in tree
                if hasattr(self.folder_tree, 'setUniformRowHeights'):
                    self.folder_tree.setUniformRowHeights(True)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "large_directory_optimization",
                f"Large directory optimization {'enabled' if enabled else 'disabled'}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "large_directory_optimization", "enabled": enabled},
                AIComponent.KIRO
            )
