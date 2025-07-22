#!/usr/bin/env python3
"""
Test script for No GPS message functionality
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from src.modules.map_viewer import MapViewer

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test No GPS Message")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Map viewer
        self.map_viewer = MapViewer()
        layout.addWidget(self.map_viewer)

        # Test buttons
        btn_layout = QVBoxLayout()

        # Test GPS photo button
        gps_btn = QPushButton("Test Photo with GPS")
        gps_btn.clicked.connect(self.test_gps_photo)
        btn_layout.addWidget(gps_btn)

        # Test no GPS photo button
        no_gps_btn = QPushButton("Test Photo without GPS")
        no_gps_btn.clicked.connect(self.test_no_gps_photo)
        btn_layout.addWidget(no_gps_btn)

        layout.addLayout(btn_layout)

    def test_gps_photo(self):
        """Test photo with GPS information"""
        self.map_viewer.set_current_photo(
            "/test/photo_with_gps.jpg",
            35.6762, 139.6503  # Tokyo coordinates
        )

    def test_no_gps_photo(self):
        """Test photo without GPS information"""
        self.map_viewer.set_current_photo("/test/photo_without_gps.jpg")
        print("Statistics:", self.map_viewer.get_photo_statistics())

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = TestWindow()
    window.show()

    print("Test application started")
    print("Click 'Test Photo without GPS' to see the no GPS message")

    sys.exit(app.exec())
