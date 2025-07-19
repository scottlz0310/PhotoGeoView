#!/usr/bin/env python3
"""
Test Qt Theme Manager integration with actual PyQt6 application
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt
from src.core.settings import SettingsManager
from src.ui.theme_manager import ThemeManager

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theme Manager Integration Test")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add test widgets
        self.status_label = QLabel("Theme Manager Test")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Theme buttons
        self.dark_button = QPushButton("Apply Dark Blue Theme")
        self.dark_button.clicked.connect(lambda: self.apply_theme('dark_blue'))
        layout.addWidget(self.dark_button)

        self.light_button = QPushButton("Apply Light Blue Theme")
        self.light_button.clicked.connect(lambda: self.apply_theme('light_blue'))
        layout.addWidget(self.light_button)

        self.cyan_button = QPushButton("Apply Light Cyan Theme")
        self.cyan_button.clicked.connect(lambda: self.apply_theme('light_cyan'))
        layout.addWidget(self.cyan_button)

        # Initialize theme manager
        self.settings = SettingsManager()
        self.theme_manager = ThemeManager(self.settings)

        # Connect theme changed signal
        self.theme_manager.theme_changed.connect(self.on_theme_changed)

        # Update status
        self.update_status()

    def apply_theme(self, theme_name: str):
        """Apply selected theme"""
        success = self.theme_manager.apply_theme(theme_name)
        self.status_label.setText(f"Applied theme: {theme_name} - {'Success' if success else 'Failed'}")

    def on_theme_changed(self, theme_name: str):
        """Handle theme change signal"""
        print(f"Theme changed signal received: {theme_name}")

    def update_status(self):
        """Update status information"""
        current_theme = self.theme_manager.get_current_theme()
        config_count = len(self.theme_manager.theme_configs)
        self.status_label.setText(
            f"Current Theme: {current_theme} | Config Themes: {config_count}"
        )

def main():
    app = QApplication(sys.argv)

    # Create and show main window
    window = TestMainWindow()
    window.show()

    print("=== Theme Manager Integration Test ===")
    print("Qt Application created successfully")
    print(f"Available themes: {len(window.theme_manager.available_themes)}")
    print(f"Config themes loaded: {len(window.theme_manager.theme_configs)}")
    print("Click buttons to test theme switching...")

    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
