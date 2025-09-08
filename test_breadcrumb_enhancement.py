#!/usr/bin/env python3
"""
Test script for enhanced breadcrumb functionality
"""

import sys
from pathlib import Path

from breadcrumb_addressbar import BreadcrumbAddressBar
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget


def test_enhanced_breadcrumb():
    """Test the enhanced breadcrumb functionality"""
    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Enhanced Breadcrumb Test")
    window.resize(800, 200)

    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)

    # Create layout
    layout = QVBoxLayout(central_widget)

    # Create breadcrumb widget
    breadcrumb = BreadcrumbAddressBar()

    # Test enhanced popup functionality
    print("Testing enhanced breadcrumb functionality...")
    print(f"Show popup for all buttons: {breadcrumb.getShowPopupForAllButtons()}")
    print(f"Popup position offset: {breadcrumb.getPopupPositionOffset()}")

    # Set a test path
    test_path = str(Path.home() / "Documents" / "Photos" / "Vacation" / "2024")
    breadcrumb.setPath(test_path)
    print(f"Set test path: {test_path}")

    # Add to layout
    layout.addWidget(breadcrumb)

    # Show window
    window.show()

    print("Window displayed. Click any breadcrumb button to test enhanced popup functionality.")
    print("All buttons should now show a folder selection popup when clicked.")

    return app.exec()


if __name__ == "__main__":
    sys.exit(test_enhanced_breadcrumb())
