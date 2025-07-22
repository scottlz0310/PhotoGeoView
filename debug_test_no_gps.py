#!/usr/bin/env python3
"""
Enhanced debug test script for No GPS message functionality
"""

import sys
import os
import tempfile
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import QUrl
from src.modules.map_viewer import MapViewer

class DebugTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug No GPS Message Test")
        self.setGeometry(100, 100, 1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Map viewer
        self.map_viewer = MapViewer()
        layout.addWidget(self.map_viewer, 3)  # 3/4 of the space

        # Debug text area
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(150)
        self.debug_text.setPlainText("Debug information will appear here...\n")
        layout.addWidget(self.debug_text, 1)  # 1/4 of the space

        # Test buttons
        btn_layout = QVBoxLayout()

        # Test GPS photo button
        gps_btn = QPushButton("Test Photo with GPS (Tokyo)")
        gps_btn.clicked.connect(self.test_gps_photo)
        btn_layout.addWidget(gps_btn)

        # Test no GPS photo button
        no_gps_btn = QPushButton("Test Photo without GPS")
        no_gps_btn.clicked.connect(self.test_no_gps_photo)
        btn_layout.addWidget(no_gps_btn)

        # Check temp files button
        check_btn = QPushButton("Check Temp Files")
        check_btn.clicked.connect(self.check_temp_files)
        btn_layout.addWidget(check_btn)

        # Clear debug button
        clear_btn = QPushButton("Clear Debug")
        clear_btn.clicked.connect(self.clear_debug)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        self.log_debug("Debug test window initialized")

    def log_debug(self, message):
        """Add debug message to text area"""
        self.debug_text.append(f"[DEBUG] {message}")
        print(f"[DEBUG] {message}")

    def test_gps_photo(self):
        """Test photo with GPS information"""
        self.log_debug("Testing GPS photo...")
        self.map_viewer.set_current_photo(
            "/test/photo_with_gps.jpg",
            35.6762, 139.6503  # Tokyo coordinates
        )
        stats = self.map_viewer.get_photo_statistics()
        self.log_debug(f"Statistics after GPS photo: {stats}")

    def test_no_gps_photo(self):
        """Test photo without GPS information"""
        self.log_debug("Testing no-GPS photo...")
        photo_path = "/test/photo_without_gps.jpg"

        # Call set_current_photo without coordinates
        self.map_viewer.set_current_photo(photo_path)

        # Check statistics
        stats = self.map_viewer.get_photo_statistics()
        self.log_debug(f"Statistics after no-GPS photo: {stats}")

        # Check if photo is in no-GPS set
        no_gps_photos = self.map_viewer.get_photos_without_gps()
        self.log_debug(f"Photos without GPS: {no_gps_photos}")

        # Check temp directory for HTML files
        self.check_temp_files()

    def check_temp_files(self):
        """Check temporary directory for HTML files"""
        temp_dir = tempfile.gettempdir()
        self.log_debug(f"Temp directory: {temp_dir}")

        # Check for our HTML files
        html_files = [
            "photogeoview_map.html",
            "photogeoview_no_gps.html",
            "photogeoview_error.html"
        ]

        for filename in html_files:
            filepath = os.path.join(temp_dir, filename)
            exists = os.path.exists(filepath)
            self.log_debug(f"{filename}: {'EXISTS' if exists else 'NOT FOUND'}")

            if exists:
                # Check file size and modification time
                stat = os.stat(filepath)
                self.log_debug(f"  Size: {stat.st_size} bytes, Modified: {stat.st_mtime}")

        # Check current web view URL
        current_url = self.map_viewer.web_view.url()
        self.log_debug(f"Current WebView URL: {current_url.toString()}")

    def clear_debug(self):
        """Clear debug text"""
        self.debug_text.clear()
        self.debug_text.setPlainText("Debug cleared...\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = DebugTestWindow()
    window.show()

    print("Enhanced debug test application started")
    print("Use buttons to test GPS/no-GPS functionality")

    sys.exit(app.exec())
