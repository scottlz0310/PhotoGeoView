#!/usr/bin/env python3
"""
MapViewer単体テスト
"""

import sys
sys.path.insert(0, '/home/hiro/Repository/PhotoGeoView')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from src.modules.map_viewer import MapViewer

class TestMapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MapViewer単体テスト")
        self.setGeometry(100, 100, 800, 600)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QVBoxLayout(central_widget)

        # MapViewerを追加
        self.map_viewer = MapViewer()
        layout.addWidget(self.map_viewer)

        # テストデータでマーカーを追加
        self.add_test_markers()

    def add_test_markers(self):
        """テスト用マーカーを追加"""
        # 東京の写真
        tokyo_coords = (35.699778, 139.771700)
        self.map_viewer.add_marker(
            "tokyo_photo",
            tokyo_coords,
            "東京の写真",
            "撮影日時: 2024-01-01 12:00:00<br>カメラ: Canon EOS R5"
        )

        # ロンドンの写真
        london_coords = (51.504106, -0.074575)
        self.map_viewer.add_marker(
            "london_photo",
            london_coords,
            "ロンドンブリッジ",
            "撮影日時: 2024-02-15 15:30:00<br>カメラ: Sony A7R IV"
        )

        # 地図の中心を東京に設定
        self.map_viewer.set_center(tokyo_coords)

def main():
    app = QApplication(sys.argv)

    window = TestMapWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
