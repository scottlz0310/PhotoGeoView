"""
Panel Controller for PhotoGeoView
Manages panel interactions, connections, and event coordination
"""

from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import Optional, List

from src.core.logger import get_logger
from src.modules.file_browser import FileBrowser
from src.modules.thumbnail_view import ThumbnailView
from src.modules.exif_info import ExifInfoPanel
from src.modules.image_viewer import ImageViewer
from src.modules.map_viewer import MapViewer


class PanelController(QObject):
    """
    Controller for managing panel interactions and data flow
    Coordinates between file browser, thumbnails, image viewer, EXIF, and map
    """

    # Signals
    status_message = pyqtSignal(str)  # For status bar updates

    def __init__(self, parent=None):
        """Initialize panel controller"""
        super().__init__(parent)

        self.logger = get_logger(__name__)

        # Widget references (set later via setup_widgets)
        self.file_browser: Optional[FileBrowser] = None
        self.thumbnail_view: Optional[ThumbnailView] = None
        self.exif_panel: Optional[ExifInfoPanel] = None
        self.image_viewer: Optional[ImageViewer] = None
        self.map_viewer: Optional[MapViewer] = None

        self.logger.debug("Panel controller initialized")

    def setup_widgets(self, file_browser: FileBrowser, thumbnail_view: ThumbnailView,
                     exif_panel: ExifInfoPanel, image_viewer: ImageViewer,
                     map_viewer: MapViewer) -> None:
        """Setup widget references and connections"""
        self.file_browser = file_browser
        self.thumbnail_view = thumbnail_view
        self.exif_panel = exif_panel
        self.image_viewer = image_viewer
        self.map_viewer = map_viewer

        self.setup_widget_connections()
        self.logger.debug("Panel controller widgets configured")

    def setup_widget_connections(self) -> None:
        """Setup signal connections between widgets"""
        try:
            if not all([self.file_browser, self.thumbnail_view, self.exif_panel,
                       self.image_viewer, self.map_viewer]):
                self.logger.warning("Not all widgets available for connections")
                return

            # File browser connections
            self.file_browser.folder_changed.connect(self.on_folder_changed_handler)
            self.file_browser.file_selected.connect(self.on_file_selected_handler)

            # Thumbnail view connections
            self.thumbnail_view.image_selected.connect(self.on_image_selected_handler)
            self.thumbnail_view.image_double_clicked.connect(self.on_image_double_clicked_handler)

            # Image viewer connections
            self.image_viewer.fullscreen_requested.connect(self.on_fullscreen_requested)
            self.image_viewer.image_changed.connect(self.on_image_viewer_changed)

            # Map viewer connections
            self.map_viewer.fullscreen_requested.connect(self.on_map_fullscreen_requested)
            self.map_viewer.marker_clicked.connect(self.on_map_marker_clicked)

            # EXIF data loaded connection
            self.exif_panel.data_loaded.connect(self.on_exif_data_loaded)

            self.logger.debug("Widget connections established")

        except Exception as e:
            self.logger.error(f"Error setting up widget connections: {e}")

    def on_folder_changed_handler(self, folder_path: str) -> None:
        """Handle folder change from file browser"""
        try:
            if not self.file_browser:
                return

            # Get image files in the folder
            image_files = self.file_browser.get_image_files_in_current_path()

            # Update thumbnail view
            if self.thumbnail_view:
                self.thumbnail_view.load_images(image_files)

            # Clear EXIF panel
            if self.exif_panel:
                self.exif_panel.clear_info()

            self.logger.info(f"Folder changed to: {folder_path}, found {len(image_files)} images")

        except Exception as e:
            self.logger.error(f"Error handling folder change: {e}")

    def on_file_selected_handler(self, file_path: str) -> None:
        """Handle file selection from file browser"""
        try:
            # Update EXIF panel
            if self.exif_panel:
                self.exif_panel.load_file_info(file_path)

            # If it's an image file, load it in the image viewer
            if self.is_image_file(file_path) and self.image_viewer and self.file_browser:
                # Get all images in current folder for navigation
                image_files = self.file_browser.get_image_files_in_current_path()

                # Find the index of the selected file
                try:
                    current_index = image_files.index(file_path)
                except ValueError:
                    current_index = 0

                # Set the image list with correct index
                self.image_viewer.set_image_list(image_files, current_index)

                # Update map with GPS location if available
                self.update_map_for_image(file_path)

            # Update status
            self.status_message.emit(f"Selected: {Path(file_path).name}")

            self.logger.debug(f"File selected: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling file selection: {e}")

    def on_image_selected_handler(self, file_path: str) -> None:
        """Handle image selection from thumbnail view"""
        try:
            # Update EXIF panel
            if self.exif_panel:
                self.exif_panel.load_file_info(file_path)

            # Load image in viewer
            if self.image_viewer and self.file_browser:
                image_files = self.file_browser.get_image_files_in_current_path()

                # Find the index of the selected file
                try:
                    current_index = image_files.index(file_path)
                except ValueError:
                    current_index = 0

                # Set the image list with correct index
                self.image_viewer.set_image_list(image_files, current_index)

                # Update map with GPS location if available
                self.update_map_for_image(file_path)

            # Update status
            self.status_message.emit(f"Selected: {Path(file_path).name}")

            self.logger.debug(f"Image selected from thumbnails: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling image selection: {e}")

    def on_image_double_clicked_handler(self, file_path: str) -> None:
        """Handle image double-click from thumbnail view"""
        try:
            # Open image in viewer with fullscreen
            if self.image_viewer and self.file_browser:
                image_files = self.file_browser.get_image_files_in_current_path()

                # Find the index of the selected file
                try:
                    current_index = image_files.index(file_path)
                except ValueError:
                    current_index = 0

                # Set the image list with correct index
                self.image_viewer.set_image_list(image_files, current_index)

                # Trigger fullscreen mode
                self.on_fullscreen_requested()

            self.status_message.emit(f"Opening: {Path(file_path).name}")
            self.logger.info(f"Image double-clicked: {file_path}")

        except Exception as e:
            self.logger.error(f"Error handling image double-click: {e}")

    def on_fullscreen_requested(self) -> None:
        """Handle fullscreen request from image viewer"""
        try:
            # Emit signal for main window to handle
            # This will be connected by main window to its toggle_panel_maximize method
            self.logger.debug("Fullscreen requested")
        except Exception as e:
            self.logger.error(f"Error handling fullscreen request: {e}")

    def on_image_viewer_changed(self, image_path: str) -> None:
        """Handle image change in viewer (from navigation)"""
        try:
            # Update EXIF panel
            if self.exif_panel:
                self.exif_panel.load_file_info(image_path)

            # Update status
            self.status_message.emit(f"Viewing: {Path(image_path).name}")

            self.logger.debug(f"Image viewer changed to: {image_path}")
        except Exception as e:
            self.logger.error(f"Error handling image viewer change: {e}")

    def on_map_fullscreen_requested(self) -> None:
        """Handle fullscreen request from map viewer"""
        try:
            # Emit signal for main window to handle
            self.logger.debug("Map fullscreen requested")
        except Exception as e:
            self.logger.error(f"Error handling map fullscreen request: {e}")

    def on_map_marker_clicked(self, photo_path: str) -> None:
        """Handle marker click from map viewer"""
        try:
            # Load the clicked photo in image viewer
            if self.image_viewer and self.file_browser:
                image_files = self.file_browser.get_image_files_in_current_path()

                if photo_path in image_files:
                    try:
                        current_index = image_files.index(photo_path)
                        self.image_viewer.set_image_list(image_files, current_index)

                        # Update EXIF panel
                        if self.exif_panel:
                            self.exif_panel.load_file_info(photo_path)

                        self.status_message.emit(f"Viewing: {Path(photo_path).name}")
                        self.logger.info(f"Map marker clicked for: {photo_path}")
                    except ValueError:
                        self.logger.warning(f"Photo not found in current folder: {photo_path}")

        except Exception as e:
            self.logger.error(f"Error handling map marker click: {e}")

    def update_map_for_image(self, image_path: str) -> None:
        """Update map display for the selected image"""
        try:
            if not self.map_viewer or not self.exif_panel:
                return

            # Get GPS coordinates from EXIF panel
            if hasattr(self.exif_panel, 'get_gps_coordinates'):
                coordinates = self.exif_panel.get_gps_coordinates()
                if coordinates:
                    lat, lon = coordinates
                    self.map_viewer.set_current_photo(image_path, lat, lon)
                    self.logger.debug(f"Updated map for {image_path} at ({lat}, {lon})")
                else:
                    # No GPS data available
                    self.map_viewer.set_current_photo(image_path)
                    self.logger.debug(f"No GPS data for {image_path}")
            else:
                self.logger.warning("EXIF panel doesn't support GPS coordinate extraction")

        except Exception as e:
            self.logger.error(f"Error updating map for image: {e}")

    def on_exif_data_loaded(self, file_path: str, exif_data: dict) -> None:
        """Handle EXIF data loaded signal and update map if GPS coordinates are available"""
        try:
            if not self.map_viewer:
                return

            # GPS座標が含まれている場合のみ地図を更新
            if 'gps_coordinates' in exif_data:
                coordinates = exif_data['gps_coordinates']
                if coordinates and isinstance(coordinates, tuple) and len(coordinates) == 2:
                    lat, lon = coordinates
                    self.map_viewer.set_current_photo(file_path, lat, lon)
                    self.logger.debug(f"Map updated via EXIF signal for {file_path} at ({lat}, {lon})")

        except Exception as e:
            self.logger.error(f"Error handling EXIF data loaded signal: {e}")

    def update_map_with_folder_images(self) -> None:
        """Update map with all images in current folder that have GPS data"""
        try:
            if not self.file_browser or not self.map_viewer:
                return

            image_files = self.file_browser.get_image_files_in_current_path()
            photo_locations = {}

            for image_file in image_files:
                try:
                    # Temporarily load EXIF to check for GPS
                    from src.modules.exif_info import ExifInfoPanel
                    temp_exif = ExifInfoPanel()
                    temp_exif.load_file_info(image_file)

                    if hasattr(temp_exif, 'get_gps_coordinates'):
                        coordinates = temp_exif.get_gps_coordinates()
                        if coordinates:
                            photo_locations[image_file] = coordinates

                except Exception as e:
                    self.logger.debug(f"No GPS data for {image_file}: {e}")
                    continue

            # Update map with all photo locations
            if photo_locations:
                self.map_viewer.set_photo_locations(photo_locations)
                self.logger.info(f"Updated map with {len(photo_locations)} photo locations")
            else:
                self.map_viewer.clear_map()
                self.logger.debug("No photos with GPS data found")

        except Exception as e:
            self.logger.error(f"Error updating map with folder images: {e}")

    def is_image_file(self, file_path: str) -> bool:
        """Check if the file is a supported image file"""
        try:
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
            return Path(file_path).suffix.lower() in image_extensions
        except Exception:
            return False
