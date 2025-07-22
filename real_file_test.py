#!/usr/bin/env python3
"""
Real file test for No GPS message functionality
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QFileDialog
from src.modules.map_viewer import MapViewer

class RealFileTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real File Test - No GPS Message")
        self.setGeometry(100, 100, 1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Map viewer
        self.map_viewer = MapViewer()
        layout.addWidget(self.map_viewer, 3)

        # Debug text area
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(150)
        self.debug_text.setPlainText("Real file test initialized...\n")
        layout.addWidget(self.debug_text, 1)

        # Test buttons
        btn_layout = QVBoxLayout()

        # Test with real no-GPS image
        no_gps_btn = QPushButton("Test with ScreenShot-tw.png (No GPS)")
        no_gps_btn.clicked.connect(self.test_real_no_gps_photo)
        btn_layout.addWidget(no_gps_btn)

        # Test with real GPS image
        gps_btn = QPushButton("Test with GPS image")
        gps_btn.clicked.connect(self.test_real_gps_photo)
        btn_layout.addWidget(gps_btn)

        # Select file button
        select_btn = QPushButton("Select Custom File")
        select_btn.clicked.connect(self.select_custom_file)
        btn_layout.addWidget(select_btn)

        layout.addLayout(btn_layout)

    def log_debug(self, message: str) -> None:
        """Add debug message to text area"""
        self.debug_text.append(f"[DEBUG] {message}")
        print(f"[DEBUG] {message}")

    def test_real_no_gps_photo(self):
        """Test with real image that has no GPS data"""
        photo_path = "/home/hiro/Repository/PhotoGeoView/tests/test_data/images/no_exif/ScreenShot-tw.png"

        if os.path.exists(photo_path):
            self.log_debug(f"Testing with real no-GPS file: {photo_path}")
            self.map_viewer.set_current_photo(photo_path)

            stats = self.map_viewer.get_photo_statistics()
            self.log_debug(f"Statistics: {stats}")

            no_gps_photos = self.map_viewer.get_photos_without_gps()
            self.log_debug(f"Photos without GPS: {list(no_gps_photos)}")
        else:
            self.log_debug(f"File not found: {photo_path}")

    def test_real_gps_photo(self):
        """Test with real image that has GPS data"""
        photo_path = "/home/hiro/Repository/PhotoGeoView/tests/test_data/images/with_gps/england-london-bridge.jpg"

        if os.path.exists(photo_path):
            self.log_debug(f"Testing with real GPS file: {photo_path}")
            # Here we would need to parse the EXIF data, but for testing we'll simulate
            # Let's check if this file actually has GPS data first by setting it without coordinates
            self.map_viewer.set_current_photo(photo_path)

            stats = self.map_viewer.get_photo_statistics()
            self.log_debug(f"Statistics: {stats}")
        else:
            self.log_debug(f"File not found: {photo_path}")

    def select_custom_file(self):
        """Allow user to select a custom file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Image File",
            "/home/hiro/Repository/PhotoGeoView/tests/test_data/images",
            "Image Files (*.jpg *.jpeg *.png *.gif *.bmp)"
        )

        if file_path:
            self.log_debug(f"Selected file: {file_path}")
            self.map_viewer.set_current_photo(file_path)

            stats = self.map_viewer.get_photo_statistics()
            self.log_debug(f"Statistics: {stats}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = RealFileTestWindow()
    window.show()

    print("Real file test application started")

    sys.exit(app.exec())
