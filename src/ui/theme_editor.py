"""
Theme Editor Interface Components

Provides UI components for creating and editing custom themes.
Implements theme editor interface as specified in task 6 of the qt-theme-breadcrumb spec.

Author: Kiro AI Integration System
Requirements: 3.1, 3.2, 3.3, 3.4
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
    QColorDialog, QFontDialog, QSpinBox, QGroupBox,
    QScrollArea, QTabWidget, QMessageBox, QFileDialog,
    QProgressBar, QCheckBox, QSlider, QFrame
)

from ..integration.config_manager import ConfigManager
from ..integration.logging_system import LoggerSystem
from ..integration.theme_models import ThemeConfiguration, ColorScheme, FontConfig, ThemeType
from .theme_manager import ThemeManagerWidget


class ColorPickerWidget(QWidget):
    """Color picker widget with preview and validation"""

    color_changed = Signal(str, str)  # property_name, color_value

    def __init__(self, property_name: str, initial_color: str = "#000000", parent=None):
        super().__init__(parent)
        self.property_name = property_name
        self.current_color = initial_color

        self._setup_ui()
        self._connect_signals()
        self.set_color(initial_color)

    def _setup_ui(self):
        """Setup the color picker UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Color preview button
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 30)
        self.color_button.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #ccc;")

        # Color value input
        self.color_input = QLineEdit(self.current_color)
        self.color_input.setPlaceholderText("#RRGGBB or color name")

        # Color picker button
        self.picker_button = QPushButton("...")
        self.picker_button.setFixedSize(30, 30)

        layout.addWidget(self.color_button)
        layout.addWidget(self.color_input)
        layout.addWidget(self.picker_button)

    def _connect_signals(self):
        """Connect widget signals"""
        self.color_button.clicked.connect(self._open_color_dialog)
        self.pr_button.clicked.connect(self._open_color_dialog)
        self.color_input.textChanged.connect(self._on_color_input_changed)

    def _open_color_dialog(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.set_color(color.name())

    def _on_color_input_changed(self, text: str):
        """Handle color input text change"""
        if self._is_valid_color(text):
            self.set_color(text)

    def _is_valid_color(self, color: str) -> bool:
        """Validate color format"""
        try:
            QColor(color).isValid()
            return True
        except:
            return False

    def set_color(self, color: str):
        """Set the current color"""
        if self._is_valid_color(color):
            self.current_color = color
            self.color_button.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
            if self.color_input.text() != color:
                self.color_input.setText(color)
            self.color_changed.emit(self.property_name, color)

    def get_color(self) -> str:
        """Get the current color"""
        return self.current_color


class FontPickerWidget(QWidget):
    """Font picker widget with preview"""

    font_changed = Signal(str, dict)  # property_name, font_config

    def __init__(self, property_name: str, initial_font: FontConfig = None, parent=None):
        super().__init__(parent)
        self.property_name = property_name
        self.current_font = initial_font or FontConfig("Arial", 12)

        self._setup_ui()
        self._connect_signals()
        self._update_preview()

    def _setup_ui(self):
        """Setup the font picker UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Font controls
        controls_layout = QHBoxLayout()

        # Font family
        self.family_combo = QComboBox()
        self.family_combo.addItems([
            "Arial", "Helvetica", "Times New Roman", "Courier New",
            "Verdana", "Georgia", "Comic Sans MS", "Impact"
        ])
        self.family_combo.setCurrentText(self.current_font.family)

        # Font size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(self.current_font.size)

        # Font weight
        self.weight_combo = QComboBox()
        self.weight_combo.addItems(["normal", "bold", "lighter", "bolder"])
        self.weight_combo.setCurrentText(self.current_font.weight)

        # Font style
        self.style_combo = QComboBox()
        self.style_combo.addItems(["normal", "italic", "oblique"])
        self.style_combo.setCurrentText(self.current_font.style)

        # Font dialog button
        self.font_button = QPushButton("Choose Font...")

        controls_layout.addWidget(QLabel("Family:"))
        controls_layout.addWidget(self.family_combo)
        controls_layout.addWidget(QLabel("Size:"))
        controls_layout.addWidget(self.size_spin)
        controls_layout.addWidget(QLabel("Weight:"))
        controls_layout.addWidget(self.weight_combo)
        controls_layout.addWidget(QLabel("Style:"))
        controls_layout.addWidget(self.style_combo)
        controls_layout.addWidget(self.font_button)

        # Font preview
        self.preview_label = QLabel("Sample Text (AaBbCc 123)")
        self.preview_label.setMinimumHeight(40)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; padding: 5px;")

        layout.addLayout(controls_layout)
        layout.addWidget(self.preview_label)

    def _connect_signals(self):
        """Connect widget signals"""
        self.family_combo.currentTextChanged.connect(self._on_font_changed)
        self.size_spin.valueChanged.connect(self._on_font_changed)
        self.weight_combo.currentTextChanged.connect(self._on_font_changed)
        self.style_combo.currentTextChanged.connect(self._on_font_changed)
        self.font_button.clicked.connect(self._open_font_dialog)

    def _open_font_dialog(self):
        """Open font picker dialog"""
        current_font = QFont(self.current_font.family, self.current_font.size)
        current_font.setBold(self.current_font.weight == "bold")
        current_font.setItalic(self.current_font.style == "italic")

        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.current_font = FontConfig(
                family=font.family(),
                size=font.pointSize(),
                weight="bold" if font.bold() else "normal",
                style="italic" if font.italic() else "normal"
            )
            self._update_controls()
            self._update_preview()
            self._emit_font_changed()

    def _on_font_changed(self):
        """Handle font property change"""
        self.current_font = FontConfig(
            family=self.family_combo.currentText(),
            size=self.size_spin.value(),
            weight=self.weight_combo.currentText(),
            style=self.style_combo.currentText()
        )
        self._update_preview()
        self._emit_font_changed()

    def _update_controls(self):
        """Update control values"""
        self.family_combo.setCurrentText(self.current_font.family)
        self.size_spin.setValue(self.current_font.size)
        self.weight_combo.setCurrentText(self.current_font.weight)
        self.style_combo.setCurrentText(self.current_font.style)

    def _update_preview(self):
        """Update font preview"""
        font = QFont(self.current_font.family, self.current_font.size)
        font.setBold(self.current_font.weight == "bold")
        font.setItalic(self.current_font.style == "italic")
        self.preview_label.setFont(font)

    def _emit_font_changed(self):
        """Emit font changed signal"""
        font_dict = {
            "family": self.current_font.family,
            "size": self.current_font.size,
            "weight": self.current_font.weight,
            "style": self.current_font.style
        }
        self.font_changed.emit(self.property_name, font_dict)

    def set_font(self, font_config: FontConfig):
        """Set the current font"""
        self.current_font = font_config
        self._update_controls()
        self._update_preview()

    def get_font(self) -> FontConfig:
        """Get the current font"""
        return self.current_font


class ThemePreviewWidget(QWidget):
    """Widget for previewing theme changes in real-time"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.current_theme = None

    def _setup_ui(self):
        """Setup the preview UI"""
        layout = QVBoxLayout(self)

        # Preview frame
        self.preview_frame = QFrame()
        self.preview_frame.setFrameStyle(QFrame.Box)
        self.preview_frame.setMinimumSize(300, 200)

        preview_layout = QVBoxLayout(self.preview_frame)

        # Sample UI elements
        self.title_label = QLabel("Theme Preview")
        self.title_label.setObjectName("title")

        self.text_label = QLabel("This is sample text content")
        self.text_label.setObjectName("text")

        self.button = QPushButton("Sample Button")
        self.button.setObjectName("button")

        self.secondary_text = QLabel("Secondary text content")
        self.secondary_text.setObjectName("secondary")

        preview_layout.addWidget(self.title_label)
        preview_layout.addWidget(self.text_label)
        preview_layout.addWidget(self.button)
        preview_layout.addWidget(self.secondary_text)
        preview_layout.addStretch()

        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.preview_frame)

    def update_preview(self, theme: ThemeConfiguration):
        """Update preview with theme configuration"""
        self.current_theme = theme

        if not theme or not theme.colors:
            return

        # Generate stylesheet from theme
        stylesheet = f"""
        QFrame {{
            background-color: {theme.colors.background};
            color: {theme.colors.text_primary};
        }}

        QLabel#title {{
            color: {theme.colors.primary};
            font-weight: bold;
            font-size: 16px;
        }}

        QLabel#text {{
            color: {theme.colors.text_primary};
        }}

        QLabel#secondary {{
            color: {theme.colors.text_secondary};
        }}

        QPushButton#button {{
            background-color: {theme.colors.primary};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}

        QPushButton#button:hover {{
            background-color: {theme.colors.accent};
        }}
        """

        self.preview_frame.setStyleSheet(stylesheet)


class ThemeEditorDialog(QWidget):
    """Main theme editor dialog for creating and editing custom themes"""

    theme_saved = Signal(str)  # theme_name
    theme_cancelled = Signal()

    def __init__(self, theme_manager: ThemeManagerWidget, config_manager: ConfigManager,
                 logger_system: LoggerSystem, theme_config: ThemeConfiguration = None, parent=None):
        super().__init__(parent)

        self.theme_manager = theme_manager
        self.config_manager = config_manager
        self.logger = logger_system.get_logger(__name__)

        # Theme being edited (None for new theme)
        self.original_theme = theme_config
        self.current_theme = theme_config.copy() if theme_config else self._create_new_theme()

        self.setWindowTitle("Theme Editor" if theme_config else "New Theme")
        self.setMinimumSize(800, 600)

        self._setup_ui()
        self._connect_signals()
        self._load_theme_data()

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds

    def _create_new_theme(self) -> ThemeConfiguration:
        """Create a new theme configuration"""
        return ThemeConfiguration(
            name="new_theme",
            display_name="New Theme",
            description="Custom theme created with theme editor",
            author="User",
            version="1.0.0",
            theme_type=ThemeType.CUSTOM,
            is_custom=True
        )

    def _setup_ui(self):
        """Setup the theme editor UI"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Basic info tab
        self.basic_tab = self._create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "Basic Info")

        # Colors tab
        self.colors_tab = self._create_colors_tab()
        self.tab_widget.addTab(self.colors_tab, "Colors")

        # Fonts tab
        self.fonts_tab = self._create_fonts_tab()
        self.tab_widget.addTab(self.fonts_tab, "Fonts")

        # Preview tab
        self.preview_tab = self._create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "Preview")

        # Advanced tab
        self.advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "Advanced")

        layout.addWidget(self.tab_widget)

        # Button bar
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save Theme")
        self.save_as_button = QPushButton("Save As...")
        self.export_button = QPushButton("Export...")
        self.reset_button = QPushButton("Reset")
        self.cancel_button = QPushButton("Cancel")

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.save_as_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _create_basic_tab(self) -> QWidget:
        """Create basic information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Basic info form
        form_layout = QGridLayout()

        # Theme name
        form_layout.addWidget(QLabel("Theme Name:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("theme_name (no spaces)")
        form_layout.addWidget(self.name_input, 0, 1)

        # Display name
        form_layout.addWidget(QLabel("Display Name:"), 1, 0)
        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Theme Display Name")
        form_layout.addWidget(self.display_name_input, 1, 1)

        # Description
        form_layout.addWidget(QLabel("Description:"), 2, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Theme description...")
        form_layout.addWidget(self.description_input, 2, 1)

        # Author
        form_layout.addWidget(QLabel("Author:"), 3, 0)
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Theme author")
        form_layout.addWidget(self.author_input, 3, 1)

        # Version
        form_layout.addWidget(QLabel("Version:"), 4, 0)
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("1.0.0")
        form_layout.addWidget(self.version_input, 4, 1)

        layout.addLayout(form_layout)
        layout.addStretch()

        return tab

    def _create_colors_tab(self) -> QWidget:
        """Create colors configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scroll area for color pickers
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)

        # Color pickers
        self.color_pickers = {}
        color_properties = [
            ("primary", "Primary Color"),
            ("secondary", "Secondary Color"),
            ("background", "Background Color"),
            ("surface", "Surface Color"),
            ("text_primary", "Primary Text"),
            ("text_secondary", "Secondary Text"),
            ("accent", "Accent Color"),
            ("error", "Error Color"),
            ("warning", "Warning Color"),
            ("success", "Success Color")
        ]

        for i, (prop, label) in enumerate(color_properties):
            scroll_layout.addWidget(QLabel(f"{label}:"), i, 0)
            color_picker = ColorPickerWidget(prop)
            self.color_pickers[prop] = color_picker
            scroll_layout.addWidget(color_picker, i, 1)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return tab

    def _create_fonts_tab(self) -> QWidget:
        """Create fonts configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scroll area for font pickers
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Font pickers
        self.font_pickers = {}
        font_properties = [
            ("default", "Default Font"),
            ("heading", "Heading Font"),
            ("small", "Small Font"),
            ("monospace", "Monospace Font")
        ]

        for prop, label in font_properties:
            group = QGroupBox(label)
            group_layout = QVBoxLayout(group)

            font_picker = FontPickerWidget(prop)
            self.font_pickers[prop] = font_picker
            group_layout.addWidget(font_picker)

            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return tab

    def _create_preview_tab(self) -> QWidget:
        """Create theme preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Preview widget
        self.preview_widget = ThemePreviewWidget()
        layout.addWidget(self.preview_widget)

        # Preview controls
        controls_layout = QHBoxLayout()

        self.auto_preview_checkbox = QCheckBox("Auto Preview")
        self.auto_preview_checkbox.setChecked(True)

        self.update_preview_button = QPushButton("Update Preview")

        controls_layout.addWidget(self.auto_preview_checkbox)
        controls_layout.addWidget(self.update_preview_button)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        return tab

    def _create_advanced_tab(self) -> QWidget:
        """Create advanced configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Custom properties
        properties_group = QGroupBox("Custom Properties")
        properties_layout = QVBoxLayout(properties_group)

        self.properties_text = QTextEdit()
        self.properties_text.setPlaceholderText('{"custom_property": "value"}')
        properties_layout.addWidget(self.properties_text)

        # Validation
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(validation_group)

        self.validate_button = QPushButton("Validate Theme")
        self.validation_result = QLabel("Theme not validated")

        validation_layout.addWidget(self.validate_button)
        validation_layout.addWidget(self.validation_result)

        layout.addWidget(properties_group)
        layout.addWidget(validation_group)
        layout.addStretch()

        return tab

    def _connect_signals(self):
        """Connect widget signals"""
        # Basic info signals
        self.name_input.textChanged.connect(self._on_basic_info_changed)
        self.display_name_input.textChanged.connect(self._on_basic_info_changed)
        self.description_input.textChanged.connect(self._on_basic_info_changed)
        self.author_input.textChanged.connect(self._on_basic_info_changed)
        self.version_input.textChanged.connect(self._on_basic_info_changed)

        # Color picker signals
        for color_picker in self.color_pickers.values():
            color_picker.color_changed.connect(self._on_color_changed)

        # Font picker signals
        for font_picker in self.font_pickers.values():
            font_picker.font_changed.connect(self._on_font_changed)

        # Button signals
        self.save_button.clicked.connect(self._save_theme)
        self.save_as_button.clicked.connect(self._save_theme_as)
        self.export_button.clicked.connect(self._export_theme)
        self.reset_button.clicked.connect(self._reset_theme)
        self.cancel_button.clicked.connect(self._cancel_edit)

        # Preview signals
        self.update_preview_button.clicked.connect(self._update_preview)

        # Advanced signals
        self.validate_button.clicked.connect(self._validate_theme)
        self.properties_text.textChanged.connect(self._on_properties_changed)

    def _load_theme_data(self):
        """Load theme data into UI controls"""
        if not self.current_theme:
            return

        # Basic info
        self.name_input.setText(self.current_theme.name)
        self.display_name_input.setText(self.current_theme.display_name)
        self.description_input.setPlainText(self.current_theme.description)
        self.author_input.setText(self.current_theme.author)
        self.version_input.setText(self.current_theme.version)

        # Colors
        if self.current_theme.colors:
            colors = self.current_theme.colors
            for prop, picker in self.color_pickers.items():
                if hasattr(colors, prop):
                    picker.set_color(getattr(colors, prop))

        # Fonts
        for prop, picker in self.font_pickers.items():
            if prop in self.current_theme.fonts:
                picker.set_font(self.current_theme.fonts[prop])

        # Custom properties
        if self.current_theme.custom_properties:
            self.properties_text.setPlainText(
                json.dumps(self.current_theme.custom_properties, indent=2)
            )

        # Update preview
        self._update_preview()

    def _on_basic_info_changed(self):
        """Handle basic info changes"""
        self.current_theme.name = self.name_input.text()
        self.current_theme.display_name = self.display_name_input.text()
        self.current_theme.description = self.description_input.toPlainText()
        self.current_theme.author = self.author_input.text()
        self.current_theme.version = self.version_input.text()

        if self.auto_preview_checkbox.isChecked():
            self._update_preview()

    def _on_color_changed(self, property_name: str, color_value: str):
        """Handle color changes"""
        if hasattr(self.current_theme.colors, property_name):
            setattr(self.current_theme.colors, property_name, color_value)

            if self.auto_preview_checkbox.isChecked():
                self._update_preview()

    def _on_font_changed(self, property_name: str, font_config: dict):
        """Handle font changes"""
        self.current_theme.fonts[property_name] = FontConfig(**font_config)

        if self.auto_preview_checkbox.isChecked():
            self._update_preview()

    def _on_properties_changed(self):
        """Handle custom properties changes"""
        try:
            properties_text = self.properties_text.toPlainText().strip()
            if properties_text:
                self.current_theme.custom_properties = json.loads(properties_text)
            else:
                self.current_theme.custom_properties = {}
        except json.JSONDecodeError:
            # Invalid JSON, ignore for now
            pass

    def _update_preview(self):
        """Update theme preview"""
        self.preview_widget.update_preview(self.current_theme)

    def _validate_theme(self):
        """Validate current theme configuration"""
        is_valid = self.current_theme.validate()

        if is_valid:
            self.validation_result.setText("✓ Theme is valid")
            self.validation_result.setStyleSheet("color: green;")
        else:
            errors = "\n".join(self.current_theme.validation_errors)
            self.validation_result.setText(f"✗ Validation errors:\n{errors}")
            self.validation_result.setStyleSheet("color: red;")

    def _save_theme(self):
        """Save the current theme"""
        if not self._validate_before_save():
            return

        try:
            # Save theme to custom themes directory
            custom_theme_dir = Path("config/custom_themes")
            custom_theme_dir.mkdir(parents=True, exist_ok=True)

            theme_file = custom_theme_dir / f"{self.current_theme.name}.json"

            if self.current_theme.save_to_file(theme_file):
                # Update theme manager
                self.theme_manager.reload_themes()

                self.theme_saved.emit(self.current_theme.name)
                self.logger.info(f"Theme saved: {self.current_theme.name}")

                QMessageBox.information(self, "Success", f"Theme '{self.current_theme.display_name}' saved successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to save theme file.")

        except Exception as e:
            self.logger.error(f"Failed to save theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save theme: {str(e)}")

    def _save_theme_as(self):
        """Save theme with a new name"""
        name, ok = QLineEdit().getText(self, "Save Theme As", "Theme name:")
        if ok and name:
            old_name = self.current_theme.name
            self.current_theme.name = name
            self.current_theme.display_name = name.replace('_', ' ').title()

            self._save_theme()

            # Update UI
            self.name_input.setText(name)
            self.display_name_input.setText(self.current_theme.display_name)

    def _export_theme(self):
        """Export theme to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Theme", f"{self.current_theme.name}.json",
            "JSON files (*.json);;All files (*.*)"
        )

        if file_path:
            try:
                if self.current_theme.save_to_file(Path(file_path)):
                    QMessageBox.information(self, "Success", f"Theme exported to {file_path}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to export theme.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export theme: {str(e)}")

    def _reset_theme(self):
        """Reset theme to original state"""
        reply = QMessageBox.question(
            self, "Reset Theme", "Are you sure you want to reset all changes?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.original_theme:
                self.current_theme = self.original_theme.copy()
            else:
                self.current_theme = self._create_new_theme()

            self._load_theme_data()

    def _cancel_edit(self):
        """Cancel theme editing"""
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Changes", "You have unsaved changes. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

        self.theme_cancelled.emit()
        self.close()

    def _auto_save(self):
        """Auto-save theme (to temporary location)"""
        if self._has_unsaved_changes():
            try:
                temp_dir = Path("config/temp_themes")
                temp_dir.mkdir(parents=True, exist_ok=True)

                temp_file = temp_dir / f"{self.current_theme.name}_autosave.json"
                self.current_theme.save_to_file(temp_file)

                self.logger.debug(f"Auto-saved theme: {temp_file}")
            except Exception as e:
                self.logger.error(f"Auto-save failed: {e}")

    def _validate_before_save(self) -> bool:
        """Validate theme before saving"""
        if not self.current_theme.validate():
            errors = "\n".join(self.current_theme.validation_errors)
            QMessageBox.critical(self, "Validation Error", f"Cannot save theme due to validation errors:\n\n{errors}")
            return False

        return True

    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        if not self.original_theme:
            return True  # New theme always has changes

        # Compare current theme with original
        return self.current_theme.to_dict() != self.original_theme.to_dict()

    def closeEvent(self, event):
        """Handle window close event"""
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Unsaved Changes", "You have unsaved changes. Save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self._save_theme()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class ThemeImportDialog(QWidget):
    """Dialog for importing custom themes with validation"""

    theme_imported = Signal(str)  # theme_name
    import_cancelled = Signal()

    def __init__(self, theme_manager: ThemeManagerWidget, logger_system: LoggerSystem, parent=None):
        super().__init__(parent)

        self.theme_manager = theme_manager
        self.logger = logger_system.get_logger(__name__)

        self.setWindowTitle("Import Theme")
        self.setMinimumSize(500, 400)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the import dialog UI"""
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("Theme File")
        file_layout = QHBoxLayout(file_group)

        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select theme file...")
        self.browse_button = QPushButton("Browse...")

        file_layout.addWidget(self.file_path_input)
        file_layout.addWidget(self.browse_button)

        # Theme preview
        preview_group = QGroupBox("Theme Information")
        preview_layout = QVBoxLayout(preview_group)

        self.theme_info_text = QTextEdit()
        self.theme_info_text.setReadOnly(True)
        self.theme_info_text.setMaximumHeight(150)

        preview_layout.addWidget(self.theme_info_text)

        # Validation results
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(validation_group)

        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setMaximumHeight(100)

        validation_layout.addWidget(self.validation_text)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Buttons
        button_layout = QHBoxLayout()

        self.import_button = QPushButton("Import Theme")
        self.import_button.setEnabled(False)
        self.cancel_button = QPushButton("Cancel")

        button_layout.addWidget(self.import_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(file_group)
        layout.addWidget(preview_group)
        layout.addWidget(validation_group)
        layout.addWidget(self.progress_bar)
        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect widget signals"""
        self.browse_button.clicked.connect(self._browse_file)
        self.file_path_input.textChanged.connect(self._on_file_path_changed)
        self.import_button.clicked.connect(self._import_theme)
        self.cancel_button.clicked.connect(self._cancel_import)

    def _browse_file(self):
        """Browse for theme file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Theme File", "",
            "JSON files (*.json);;All files (*.*)"
        )

        if file_path:
            self.file_path_input.setText(file_path)

    def _on_file_path_changed(self, file_path: str):
        """Handle file path change"""
        if file_path and Path(file_path).exists():
            self._validate_theme_file(Path(file_path))
        else:
            self._clear_preview()

    def _validate_theme_file(self, file_path: Path):
        """Validate theme file and show preview"""
        try:
            # Load theme configuration
            theme_config = ThemeConfiguration.load_from_file(file_path)

            if theme_config:
                # Show theme information
                info_text = f"""
Name: {theme_config.name}
Display Name: {theme_config.display_name}
Description: {theme_config.description}
Author: {theme_config.author}
Version: {theme_config.version}
Type: {theme_config.theme_type.value}
                """.strip()

                self.theme_info_text.setPlainText(info_text)

                # Validate theme
                is_valid = theme_config.validate()

                if is_valid:
                    self.validation_text.setPlainText("✓ Theme file is valid and ready to import.")
                    self.validation_text.setStyleSheet("color: green;")
                    self.import_button.setEnabled(True)
                else:
                    errors = "\n".join(theme_config.validation_errors)
                    self.validation_text.setPlainText(f"✗ Validation errors:\n{errors}")
                    self.validation_text.setStyleSheet("color: red;")
                    self.import_button.setEnabled(False)
            else:
                self._show_invalid_file()

        except Exception as e:
            self.logger.error(f"Failed to validate theme file: {e}")
            self._show_invalid_file()

    def _show_invalid_file(self):
        """Show invalid file message"""
        self.theme_info_text.setPlainText("Invalid theme file format.")
        self.validation_text.setPlainText("✗ Unable to read theme file. Please check the file format.")
        self.validation_text.setStyleSheet("color: red;")
        self.import_button.setEnabled(False)

    def _clear_preview(self):
        """Clear preview information"""
        self.theme_info_text.clear()
        self.validation_text.clear()
        self.import_button.setEnabled(False)

    def _import_theme(self):
        """Import the selected theme"""
        file_path = Path(self.file_path_input.text())

        if not file_path.exists():
            QMessageBox.critical(self, "Error", "Theme file does not exist.")
            return

        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress

            # Import theme using theme manager
            if self.theme_manager.import_theme(file_path):
                self.progress_bar.setVisible(False)

                # Get theme name from file
                theme_config = ThemeConfiguration.load_from_file(file_path)
                theme_name = theme_config.name if theme_config else "unknown"

                self.theme_imported.emit(theme_name)
                self.logger.info(f"Theme imported successfully: {theme_name}")

                QMessageBox.information(self, "Success", f"Theme '{theme_name}' imported successfully!")
                self.close()
            else:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Error", "Failed to import theme.")

        except Exception as e:
            self.progress_bar.setVisible(False)
            self.logger.error(f"Failed to import theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to import theme: {str(e)}")

    def _cancel_import(self):
        """Cancel theme import"""
        self.import_cancelled.emit()
        self.close()
