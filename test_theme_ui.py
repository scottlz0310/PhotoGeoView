#!/usr/bin/env python3
"""
Theme UI Test

Tests the theme selection UI functionality.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QComboBox
from PySide6.QtCore import Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.ui.theme_manager_simple import SimpleThemeManager


class ThemeTestWindow(QMainWindow):
    """Simple window to test theme functionality"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoGeoView Theme Test")
        self.setGeometry(100, 100, 600, 400)

        # Initialize theme manager
        self.logger_system = LoggerSystem()
        self.config_manager = ConfigManager(config_dir=Path("config"), logger_system=self.logger_system)
        self.theme_manager = SimpleThemeManager(self.config_manager, self.logger_system)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("PhotoGeoView Theme Selection Test")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # Current theme display
        self.current_theme_label = QLabel()
        self.update_current_theme_display()
        layout.addWidget(self.current_theme_label)

        # Theme selection combo box
        self.theme_combo = QComboBox()
        self.populate_theme_combo()
        layout.addWidget(self.theme_combo)

        # Apply button
        apply_button = QPushButton("Apply Selected Theme")
        apply_button.clicked.connect(self.apply_selected_theme)
        layout.addWidget(apply_button)

        # Theme info display
        self.theme_info_label = QLabel()
        self.theme_info_label.setWordWrap(True)
        layout.addWidget(self.theme_info_label)

        # Test buttons
        test_layout = QVBoxLayout()

        # Cycle theme button
        cycle_button = QPushButton("🔄 Cycle to Next Theme")
        cycle_button.clicked.connect(self.cycle_theme)
        test_layout.addWidget(cycle_button)

        # Toggle theme button
        toggle_button = QPushButton("🔀 Toggle Light/Dark")
        toggle_button.clicked.connect(self.toggle_theme)
        test_layout.addWidget(toggle_button)

        layout.addLayout(test_layout)

        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

    def populate_theme_combo(self):
        """Populate theme combo box"""
        self.theme_combo.clear()

        available_themes = self.theme_manager.get_available_themes()
        current_theme = self.theme_manager.get_current_theme()

        for theme_name in sorted(available_themes):
            theme_config = self.theme_manager.get_theme_config(theme_name)
            display_name = theme_config.get('display_name', theme_name.replace('_', ' ').title()) if theme_config else theme_name.replace('_', ' ').title()

            self.theme_combo.addItem(f"{display_name} ({theme_name})", theme_name)

            if theme_name == current_theme:
                self.theme_combo.setCurrentIndex(self.theme_combo.count() - 1)

    def connect_signals(self):
        ""heme manager signals"""
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        self.theme_manager.theme_applied.connect(self.on_theme_applied)
        self.theme_manager.theme_error.connect(self.on_theme_error)

        # Connect combo box
        self.theme_combo.currentTextChanged.connect(self.on_combo_selection_changed)

    def update_current_theme_display(self):
        """Update current theme display"""
        current_theme = self.theme_manager.get_current_theme()
        theme_config = self.theme_manager.get_theme_config(current_theme)

        if theme_config:
            display_name = theme_config.get('display_name', current_theme)
            description = theme_config.get('description', 'No description')
            primary_color = theme_config.get('primaryColor', '#000000')

            self.current_theme_label.setText(
                f"Current Theme: {display_name}\n"
                f"Description: {description}\n"
                f"Primary Color: {primary_color}"
            )
        else:
            self.current_theme_label.setText(f"Current Theme: {current_theme}")

    def on_combo_selection_changed(self, text):
        """Handle combo box selection change"""
        if text:
            # Extract theme name from display text
            theme_name = self.theme_combo.currentData()
            if theme_name:
                theme_config = self.theme_manager.get_theme_config(theme_name)
                if theme_config:
                    info = f"Theme: {theme_config.get('display_name', theme_name)}\n"
                    info += f"Description: {theme_config.get('description', 'No description')}\n"
                    info += f"Primary Color: {theme_config.get('primaryColor', 'N/A')}\n"
                    info += f"Background: {theme_config.get('backgroundColor', 'N/A')}\n"
                    info += f"Text Color: {theme_config.get('textColor', 'N/A')}"
                    self.theme_info_label.setText(info)

    def apply_selected_theme(self):
        """Apply the selected theme"""
        theme_name = self.theme_combo.currentData()
        if theme_name:
            success = self.theme_manager.apply_theme(theme_name)
            if success:
                self.status_label.setText(f"✅ Applied theme: {theme_name}")
            else:
                self.status_label.setText(f"❌ Failed to apply theme: {theme_name}")

    def cycle_theme(self):
        """Cycle to next theme"""
        self.theme_manager.cycle_theme()
        self.status_label.setText("🔄 Cycled to next theme")

    def toggle_theme(self):
        """Toggle between light and dark"""
        current = self.theme_manager.get_current_theme()
        if current == "light":
            self.theme_manager.apply_theme("dark")
        elif current == "dark":
            self.theme_manager.apply_theme("light")
        else:
            # Default to dark
            self.theme_manager.apply_theme("dark")

        self.status_label.setText("🔀 Toggled light/dark theme")

    def on_theme_changed(self, old_theme, new_theme):
        """Handle theme change"""
        self.update_current_theme_display()
        self.populate_theme_combo()  # Update combo selection
        print(f"Theme changed: {old_theme} -> {new_theme}")

    def on_theme_applied(self, theme_name):
        """Handle theme applied"""
        print(f"Theme applied: {theme_name}")

    def on_theme_error(self, theme_name, error_message):
        """Handle theme error"""
        self.status_label.setText(f"❌ Error with {theme_name}: {error_message}")
        print(f"Theme error: {theme_name} - {error_message}")


def main():
    """Main function"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("PhotoGeoView Theme Test")
    app.setApplicationVersion("1.0.0")

    # Create and show window
    window = ThemeTestWindow()
    window.show()

    # Show available themes
    print(f"Available themes: {len(window.theme_manager.get_available_themes())}")
    for theme in sorted(window.theme_manager.get_available_themes()):
        config = window.theme_manager.get_theme_config(theme)
        display_name = config.get('display_name', theme) if config else theme
        print(f"  - {display_name} ({theme})")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
