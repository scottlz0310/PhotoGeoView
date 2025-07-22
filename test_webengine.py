#!/usr/bin/env python3
"""
地図WebEngine設定テスト
"""

import sys
sys.path.insert(0, '/home/hiro/Repository/PhotoGeoView')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import Qt, QUrl

class TestWebEngineWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebEngine地図テスト")
        self.setGeometry(100, 100, 800, 600)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QVBoxLayout(central_widget)

        # WebEngineView
        self.web_view = QWebEngineView()

        # WebEngineの設定を有効化
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        layout.addWidget(self.web_view)

        # 読み込み完了コールバック
        self.web_view.loadFinished.connect(self.on_load_finished)

        # テスト用HTMLを読み込み
        self.load_test_html()

    def load_test_html(self):
        """テスト用HTMLを読み込み"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Leaflet Map Test</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css" />
            <style>
                #map { height: 500px; width: 100%; }
                body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
            </style>
        </head>
        <body>
            <h2>Leaflet Map Test</h2>
            <div id="map"></div>

            <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js"></script>
            <script>
                console.log('Script started');

                // Leafletライブラリの確認
                if (typeof L !== 'undefined') {
                    console.log('Leaflet loaded successfully');

                    // 地図を初期化
                    var map = L.map('map').setView([35.6762, 139.6503], 13);

                    // タイルレイヤーを追加
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '© OpenStreetMap contributors'
                    }).addTo(map);

                    // マーカーを追加
                    L.marker([35.6762, 139.6503])
                        .addTo(map)
                        .bindPopup('東京駅')
                        .openPopup();

                    console.log('Map initialized successfully');
                } else {
                    console.error('Leaflet not loaded!');
                    document.getElementById('map').innerHTML = '<p style="color:red;">Leafletライブラリが読み込まれませんでした。</p>';
                }
            </script>
        </body>
        </html>
        """

        self.web_view.setHtml(html_content)

    def on_load_finished(self, success):
        """読み込み完了時の処理"""
        if success:
            print("WebEngine読み込み完了: 成功")
        else:
            print("WebEngine読み込み完了: 失敗")

def main():
    app = QApplication(sys.argv)

    # グローバルWebEngine設定
    settings = QWebEngineSettings.globalSettings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

    window = TestWebEngineWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
