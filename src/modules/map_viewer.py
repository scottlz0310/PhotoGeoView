"""
Map Viewer Module for PhotoGeoView
Provides interactive map display with photo location markers using PyQtWebEngine and Folium
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Tuple, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import pyqtSignal, QUrl

try:
    import folium
    from folium import plugins
    folium_available = True
except ImportError:
    folium_available = False
    folium = None
    plugins = None

from src.core.logger import get_logger

logger = get_logger(__name__)


class MapViewer(QWidget):
    """
    Interactive map viewer widget using PyQtWebEngine and Folium
    """

    # Signals
    fullscreen_requested = pyqtSignal()  # Request fullscreen mode
    marker_clicked = pyqtSignal(str)     # Photo path when marker clicked

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Map properties
        self.current_map_file: Optional[str] = None
        self.photo_locations: Dict[str, Tuple[float, float]] = {}
        self.photos_without_gps: set[str] = set()  # ジオタグなし画像を追跡
        self.current_photo: Optional[str] = None
        self.default_location: Tuple[float, float] = (35.6762, 139.6503)  # Tokyo
        self.default_zoom: int = 10

        # UI components
        self.web_view: QWebEngineView
        self.status_label: QLabel

        self.setup_ui()
        self.setup_connections()

        # Initialize with default map
        self.initialize_map()

        logger.debug("MapViewer initialized")

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title bar with fullscreen button
        title_layout = QHBoxLayout()

        title_label = QLabel("🗺️ Map Viewer")
        title_label.setStyleSheet("font-weight: bold; padding: 2px;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # Fullscreen button
        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setToolTip("Fullscreen view")
        fullscreen_btn.setFixedSize(24, 24)
        fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)
        title_layout.addWidget(fullscreen_btn)

        layout.addLayout(title_layout)

        # Web engine view for map display
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # Configure web engine settings
        settings = self.web_view.settings()
        if settings:
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        layout.addWidget(self.web_view, 1)

        # Status bar
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_frame.setMaximumHeight(30)

        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 5, 5, 5)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 11px; color: #666666;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # Map controls
        reset_btn = QPushButton("🏠")
        reset_btn.setToolTip("Reset to default view")
        reset_btn.setFixedSize(24, 24)
        reset_btn.clicked.connect(self.reset_view)
        status_layout.addWidget(reset_btn)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh map")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.clicked.connect(self.refresh_map)
        status_layout.addWidget(refresh_btn)

        layout.addWidget(status_frame)

        logger.debug("MapViewer UI setup complete")

    def setup_connections(self) -> None:
        """Setup signal connections"""
        try:
            # Web view connections
            self.web_view.loadFinished.connect(self.on_map_loaded)

            logger.debug("MapViewer connections established")

        except Exception as e:
            logger.error(f"Error setting up MapViewer connections: {e}")

    def initialize_map(self) -> None:
        """Initialize map with default location"""
        try:
            if not folium_available:
                self.show_error_message("Folium not available. Please install folium.")
                return

            # 初期状態では「画像を選択してください」メッセージを表示
            self.show_select_image_message()
            self.status_label.setText("Ready - Select an image to view location")

            logger.info("Map initialized with select image message")

        except Exception as e:
            logger.error(f"Error initializing map: {e}")
            self.show_error_message(f"Failed to initialize map: {e}")

    def create_map(self, center: Tuple[float, float], zoom: int = 10, markers: Optional[Dict[str, Tuple[float, float]]] = None) -> None:
        """Create a new Folium map"""
        try:
            if not folium_available or folium is None:
                return

            # Create folium map
            map_obj = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )

            # Add markers for photo locations
            if markers:
                for photo_path, (lat, lon) in markers.items():
                    self.add_photo_marker(map_obj, photo_path, lat, lon)

            # Add additional map layers
            if hasattr(folium, 'TileLayer'):
                folium.TileLayer(
                    tiles='https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
                    attr='&copy; OpenStreetMap contributors, Tiles style by Humanitarian OpenStreetMap Team',
                    name='OpenStreetMap.HOT',
                    overlay=False,
                    control=True
                ).add_to(map_obj)

            # Add layer control
            if hasattr(folium, 'LayerControl'):
                folium.LayerControl().add_to(map_obj)

            # Add fullscreen plugin
            if plugins and hasattr(plugins, 'Fullscreen'):
                plugins.Fullscreen().add_to(map_obj)

            # Save map to temporary file
            temp_dir = tempfile.gettempdir()
            self.current_map_file = os.path.join(temp_dir, "photogeoview_map.html")
            map_obj.save(self.current_map_file)

            # Load in web view
            self.web_view.load(QUrl.fromLocalFile(self.current_map_file))

            logger.debug(f"Map created and saved to {self.current_map_file}")

        except Exception as e:
            logger.error(f"Error creating map: {e}")
            self.show_error_message(f"Failed to create map: {e}")

    def add_photo_marker(self, map_obj: object, photo_path: str, lat: float, lon: float) -> None:
        """Add a marker for a photo location"""
        try:
            if not folium_available or folium is None:
                return

            photo_name = Path(photo_path).name

            # Create marker with custom icon
            if hasattr(folium, 'Marker'):
                popup = None
                icon = None

                if hasattr(folium, 'Popup'):
                    popup = folium.Popup(f"📸 {photo_name}", max_width=200)

                if hasattr(folium, 'Icon'):
                    icon = folium.Icon(
                        icon='camera',
                        prefix='fa',
                        color='blue' if photo_path != self.current_photo else 'red'
                    )

                marker = folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    tooltip=photo_name,
                    icon=icon
                )

                marker.add_to(map_obj)  # type: ignore

            logger.debug(f"Added marker for {photo_name} at ({lat}, {lon})")

        except Exception as e:
            logger.error(f"Error adding photo marker: {e}")

    def set_photo_locations(self, locations: Dict[str, Tuple[float, float]]) -> None:
        """Set multiple photo locations and update map"""
        try:
            self.photo_locations = locations.copy()

            if locations:
                # Calculate center point from all locations
                lats = [lat for lat, _ in locations.values()]
                lons = [lon for _, lon in locations.values()]

                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)

                # Determine appropriate zoom level based on spread
                lat_range = max(lats) - min(lats)
                lon_range = max(lons) - min(lons)
                max_range = max(lat_range, lon_range)

                if max_range < 0.01:
                    zoom = 15
                elif max_range < 0.1:
                    zoom = 12
                elif max_range < 1.0:
                    zoom = 8
                else:
                    zoom = 5

                self.create_map((center_lat, center_lon), zoom, locations)

                # ステータス表示を改善（ジオタグなし画像も考慮）
                gps_count = len(locations)
                no_gps_count = len(self.photos_without_gps)

                if no_gps_count > 0:
                    self.status_label.setText(f"Showing {gps_count} photo locations ({no_gps_count} photos without GPS)")
                else:
                    self.status_label.setText(f"Showing {gps_count} photo locations")

            else:
                # No locations, show default map
                self.create_map(self.default_location, self.default_zoom)

                # ジオタグなし画像のみの場合のメッセージ
                if len(self.photos_without_gps) > 0:
                    self.status_label.setText(f"No GPS locations available ({len(self.photos_without_gps)} photos without GPS)")
                else:
                    self.status_label.setText("No photo locations available")

            logger.info(f"Updated map with {len(locations)} photo locations")

        except Exception as e:
            logger.error(f"Error setting photo locations: {e}")
            self.show_error_message(f"Failed to update photo locations: {e}")

    def set_current_photo(self, photo_path: str, lat: Optional[float] = None, lon: Optional[float] = None) -> None:
        """Set current photo and center map on its location"""
        try:
            self.current_photo = photo_path

            # If coordinates provided, add/update location
            if lat is not None and lon is not None:
                self.photo_locations[photo_path] = (lat, lon)
                # ジオタグなし画像リストから削除（GPS情報が見つかった場合）
                self.photos_without_gps.discard(photo_path)

                # Create map centered on this photo
                self.create_map((lat, lon), 15, self.photo_locations)

                photo_name = Path(photo_path).name
                self.status_label.setText(f"Showing location for {photo_name}")

                logger.info(f"Centered map on {photo_name} at ({lat}, {lon})")

            elif photo_path in self.photo_locations:
                # Photo location already known
                lat, lon = self.photo_locations[photo_path]
                self.create_map((lat, lon), 15, self.photo_locations)

                photo_name = Path(photo_path).name
                self.status_label.setText(f"Showing location for {photo_name}")

            else:
                # No location data available - ジオタグなし画像として記録
                self.photos_without_gps.add(photo_path)
                photo_name = Path(photo_path).name
                self.show_no_gps_message(photo_name)
                self.status_label.setText(f"No location data for selected photo: {photo_name}")
                logger.info(f"Photo without GPS data: {photo_path}")

        except Exception as e:
            logger.error(f"Error setting current photo: {e}")

    def add_photo_without_gps(self, photo_path: str) -> None:
        """ジオタグなし画像を記録する"""
        try:
            self.photos_without_gps.add(photo_path)
            logger.debug(f"Added photo without GPS: {photo_path}")
        except Exception as e:
            logger.error(f"Error adding photo without GPS: {e}")

    def remove_photo_without_gps(self, photo_path: str) -> None:
        """ジオタグなし画像リストから削除する"""
        try:
            self.photos_without_gps.discard(photo_path)
            logger.debug(f"Removed photo from no-GPS list: {photo_path}")
        except Exception as e:
            logger.error(f"Error removing photo from no-GPS list: {e}")

    def get_photos_without_gps(self) -> set[str]:
        """ジオタグなし画像のリストを取得"""
        return self.photos_without_gps.copy()

    def clear_map(self) -> None:
        """Clear all markers and reset to default view"""
        try:
            self.photo_locations.clear()
            self.photos_without_gps.clear()  # ジオタグなし画像リストもクリア
            self.current_photo = None

            # 画像選択なしの状態に戻す
            self.show_select_image_message()
            self.status_label.setText("Map cleared - Select an image to view location")

            logger.debug("Map cleared")

        except Exception as e:
            logger.error(f"Error clearing map: {e}")

    def reset_view(self) -> None:
        """Reset map to default view"""
        try:
            if self.photo_locations:
                # Reset to show all photo locations
                self.set_photo_locations(self.photo_locations)
            else:
                # Reset to default location
                self.create_map(self.default_location, self.default_zoom)
                self.status_label.setText("Reset to default view")

            logger.debug("Map view reset")

        except Exception as e:
            logger.error(f"Error resetting map view: {e}")

    def refresh_map(self) -> None:
        """Refresh the map display"""
        try:
            if self.current_map_file and os.path.exists(self.current_map_file):
                self.web_view.reload()
                self.status_label.setText("Map refreshed")
                logger.debug("Map refreshed")
            else:
                self.initialize_map()

        except Exception as e:
            logger.error(f"Error refreshing map: {e}")

    def get_photo_statistics(self) -> Dict[str, int]:
        """写真の統計情報を取得"""
        return {
            'with_gps': len(self.photo_locations),
            'without_gps': len(self.photos_without_gps),
            'total': len(self.photo_locations) + len(self.photos_without_gps)
        }

    def show_no_gps_message(self, photo_name: str) -> None:
        """Display no GPS information message in the web view"""
        try:
            logger.debug(f"show_no_gps_message called for: {photo_name}")

            no_gps_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>No GPS Information</title>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }}
                    .no-gps-container {{
                        text-align: center;
                        padding: 40px;
                        background-color: rgba(255, 255, 255, 0.1);
                        border-radius: 20px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                        max-width: 500px;
                    }}
                    .no-gps-icon {{
                        font-size: 80px;
                        margin-bottom: 20px;
                        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
                    }}
                    .no-gps-title {{
                        font-size: 28px;
                        font-weight: bold;
                        margin-bottom: 16px;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    }}
                    .photo-name {{
                        font-size: 18px;
                        margin-bottom: 20px;
                        color: #f0f0f0;
                        background-color: rgba(0,0,0,0.2);
                        padding: 10px 20px;
                        border-radius: 10px;
                        display: inline-block;
                    }}
                    .no-gps-message {{
                        font-size: 16px;
                        line-height: 1.6;
                        margin-bottom: 20px;
                        color: #e0e0e0;
                    }}
                    .suggestion {{
                        font-size: 14px;
                        color: #c0c0c0;
                        font-style: italic;
                        margin-top: 20px;
                    }}
                    .info-box {{
                        background-color: rgba(255,255,255,0.1);
                        border-left: 4px solid #ffd700;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 0 10px 10px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="no-gps-container">
                    <div class="no-gps-icon">📍🚫</div>
                    <div class="no-gps-title">⚠️ GPS情報なし ⚠️</div>
                    <div class="photo-name">📸 {photo_name}</div>
                    <div class="no-gps-message">
                        <strong style="color: #ffff00; font-size: 20px;">この画像にはGPS位置情報が含まれていません！</strong><br><br>
                        地図上に位置を表示することができません。
                    </div>
                    <div class="info-box">
                        <strong>💡 ヒント</strong><br>
                        GPS機能を有効にしてカメラで撮影すると、<br>
                        位置情報が自動的に記録されます。
                    </div>
                    <div class="suggestion">
                        他の写真を選択して位置情報を確認してみてください
                    </div>
                </div>
            </body>
            </html>
            """

            # Save no GPS HTML to temp file
            temp_dir = tempfile.gettempdir()
            no_gps_file = os.path.join(temp_dir, "photogeoview_no_gps.html")

            logger.debug(f"Saving no-GPS HTML to: {no_gps_file}")

            with open(no_gps_file, 'w', encoding='utf-8') as f:
                f.write(no_gps_html)

            logger.debug(f"HTML file written, size: {len(no_gps_html)} chars")

            # Verify file exists
            if os.path.exists(no_gps_file):
                file_size = os.path.getsize(no_gps_file)
                logger.debug(f"HTML file verified: {file_size} bytes")
            else:
                logger.error(f"HTML file not found after writing: {no_gps_file}")

            # Load in web view
            file_url = QUrl.fromLocalFile(no_gps_file)
            logger.debug(f"Loading URL in WebView: {file_url.toString()}")
            self.web_view.load(file_url)

            logger.info(f"Showing no GPS message for {photo_name}")

        except Exception as e:
            logger.error(f"Error displaying no GPS message: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def show_select_image_message(self) -> None:
        """Display 'select image' message in the web view"""
        try:
            logger.debug("show_select_image_message called")

            select_image_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Select Image</title>
                <meta charset="UTF-8">
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                        color: white;
                    }
                    .select-image-container {
                        text-align: center;
                        padding: 40px;
                        background-color: rgba(255, 255, 255, 0.1);
                        border-radius: 20px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                        max-width: 500px;
                    }
                    .select-icon {
                        font-size: 80px;
                        margin-bottom: 20px;
                        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
                    }
                    .select-title {
                        font-size: 28px;
                        font-weight: bold;
                        margin-bottom: 16px;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    }
                    .select-message {
                        font-size: 18px;
                        line-height: 1.6;
                        margin-bottom: 20px;
                        color: #e0e0e0;
                    }
                    .instruction {
                        font-size: 16px;
                        color: #c0c0c0;
                        margin-top: 20px;
                        background-color: rgba(255,255,255,0.1);
                        padding: 15px;
                        border-radius: 10px;
                    }
                    .icon-animation {
                        animation: pulse 2s infinite;
                    }
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                        100% { transform: scale(1); }
                    }
                </style>
            </head>
            <body>
                <div class="select-image-container">
                    <div class="select-icon icon-animation">📸</div>
                    <div class="select-title">画像を選択してください</div>
                    <div class="select-message">
                        画像を選択すると、GPS位置情報がある場合は<br>
                        地図上に撮影場所が表示されます。
                    </div>
                    <div class="instruction">
                        👆 左側のフォルダから画像ファイルをクリックしてください
                    </div>
                </div>
            </body>
            </html>
            """

            # Save select image HTML to temp file
            temp_dir = tempfile.gettempdir()
            select_image_file = os.path.join(temp_dir, "photogeoview_select_image.html")

            logger.debug(f"Saving select-image HTML to: {select_image_file}")

            with open(select_image_file, 'w', encoding='utf-8') as f:
                f.write(select_image_html)

            logger.debug(f"HTML file written, size: {len(select_image_html)} chars")

            # Load in web view
            file_url = QUrl.fromLocalFile(select_image_file)
            logger.debug(f"Loading URL in WebView: {file_url.toString()}")
            self.web_view.load(file_url)

            logger.info("Showing select image message")

        except Exception as e:
            logger.error(f"Error displaying select image message: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def show_error_message(self, message: str) -> None:
        """Display error message in the web view"""
        try:
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Map Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f0f0f0;
                    }}
                    .error-container {{
                        text-align: center;
                        padding: 20px;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .error-icon {{
                        font-size: 48px;
                        color: #ff6b6b;
                        margin-bottom: 16px;
                    }}
                    .error-message {{
                        color: #666;
                        font-size: 16px;
                        margin-bottom: 8px;
                    }}
                    .error-details {{
                        color: #999;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error-icon">🗺️</div>
                    <div class="error-message">Map Display Error</div>
                    <div class="error-details">{message}</div>
                </div>
            </body>
            </html>
            """

            # Save error HTML to temp file
            temp_dir = tempfile.gettempdir()
            error_file = os.path.join(temp_dir, "photogeoview_error.html")

            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(error_html)

            self.web_view.load(QUrl.fromLocalFile(error_file))
            self.status_label.setText("Error loading map")

        except Exception as e:
            logger.error(f"Error displaying error message: {e}")

    def on_map_loaded(self, success: bool) -> None:
        """Handle map load completion"""
        try:
            if success:
                logger.debug("Map loaded successfully")
            else:
                logger.warning("Map failed to load")
                self.status_label.setText("Failed to load map")

        except Exception as e:
            logger.error(f"Error handling map load: {e}")

    def get_current_photo(self) -> Optional[str]:
        """Get current photo path"""
        return self.current_photo

    def has_photo_locations(self) -> bool:
        """Check if any photo locations are available"""
        return len(self.photo_locations) > 0

    def add_marker(
        self,
        marker_id: str,
        coordinates: Tuple[float, float],
        title: str = "",
        description: str = "",
    ) -> bool:
        """
        マーカーを追加 - コントローラーとの互換性のため

        Args:
            marker_id: マーカーID（ファイルパス）
            coordinates: 座標 (緯度, 経度)
            title: マーカータイトル
            description: マーカー説明

        Returns:
            追加成功の場合True
        """
        try:
            lat, lon = coordinates
            self.set_current_photo(marker_id, lat, lon)
            logger.debug(f"マーカーを追加しました: {marker_id} at ({lat}, {lon})")
            return True
        except Exception as e:
            logger.error(f"マーカーの追加に失敗しました: {marker_id}, エラー: {e}")
            return False

    def clear_markers(self) -> None:
        """すべてのマーカーを削除 - コントローラーとの互換性のため"""
        self.clear_map()

    def set_center(self, coordinates: Tuple[float, float]) -> None:
        """地図の中心を設定 - コントローラーとの互換性のため"""
        lat, lon = coordinates
        self.create_map((lat, lon), self.default_zoom, self.photo_locations)
