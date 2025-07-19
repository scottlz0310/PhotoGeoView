"""
Map Viewer Module for PhotoGeoView
Provides interactive map display with photo location markers using PyQtWebEngine and Folium
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Tuple
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

            self.create_map(self.default_location, self.default_zoom)
            self.status_label.setText("Map initialized")

            logger.info("Map initialized with default location")

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
                self.status_label.setText(f"Showing {len(locations)} photo locations")

            else:
                # No locations, show default map
                self.create_map(self.default_location, self.default_zoom)
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
                # No location data available
                self.status_label.setText("No location data for selected photo")
                logger.warning(f"No location data available for {photo_path}")

        except Exception as e:
            logger.error(f"Error setting current photo: {e}")

    def clear_map(self) -> None:
        """Clear all markers and reset to default view"""
        try:
            self.photo_locations.clear()
            self.current_photo = None
            self.create_map(self.default_location, self.default_zoom)
            self.status_label.setText("Map cleared")

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

    def get_photo_count(self) -> int:
        """Get number of photos with location data"""
        return len(self.photo_locations)
