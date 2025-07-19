"""
PhotoGeoView Application Entry Point
Main application launcher and initialization
"""

import sys
import os
from pathlib import Path
from typing import Optional

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication, QMessageBox

# Import application modules
from src.core.logger import get_logger, LoggerManager
from src.core.settings import init_settings
from src.ui.main_window import MainWindow

logger = get_logger(__name__)


class PhotoGeoViewApplication(QApplication):
    """
    Main PhotoGeoView application class
    Handles application lifecycle and initialization
    """

    def __init__(self, argv: list[str]):
        """Initialize the application"""
        super().__init__(argv)

        # Set application properties
        self.setApplicationName("PhotoGeoView")
        self.setApplicationVersion("1.0.0")
        self.setApplicationDisplayName("PhotoGeoView - Photo Geolocation Viewer")
        self.setOrganizationName("PhotoGeoView")
        self.setOrganizationDomain("photogeoview.org")

        # Initialize logging first
        LoggerManager.initialize()
        self.logger = get_logger(__name__)

        # Initialize settings
        self.settings = init_settings()

        # Main window
        self.main_window: Optional[MainWindow] = None

        # Set application attributes for high DPI support
        # self.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        # self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        self.logger.info("PhotoGeoView application initialized")

    def initialize_ui(self) -> bool:
        """
        Initialize the user interface

        Returns:
            True if UI initialized successfully, False otherwise
        """
        try:
            # Create and show main window
            self.main_window = MainWindow()
            self.main_window.show()

            self.logger.info("UI initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize UI: {e}")
            self.show_error_dialog("Initialization Error",
                                 f"Failed to initialize user interface:\n{e}")
            return False

    def show_error_dialog(self, title: str, message: str) -> None:
        """Show error dialog to user"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
        except Exception as e:
            self.logger.error(f"Failed to show error dialog: {e}")

    def run(self) -> int:
        """
        Run the application

        Returns:
            Application exit code
        """
        try:
            # Initialize UI
            if not self.initialize_ui():
                return 1

            # Setup signal handlers for graceful shutdown
            self.aboutToQuit.connect(self.cleanup)

            self.logger.info("Starting PhotoGeoView main event loop")

            # Start event loop
            return self.exec()

        except Exception as e:
            self.logger.error(f"Fatal application error: {e}")
            self.show_error_dialog("Fatal Error",
                                 f"A fatal error occurred:\n{e}")
            return 1

    def cleanup(self) -> None:
        """Cleanup resources before application exit"""
        try:
            self.logger.info("Cleaning up application resources")

            # Save settings if main window exists
            if self.main_window:
                self.main_window.save_window_state()

            self.logger.info("PhotoGeoView application cleanup complete")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def check_dependencies() -> bool:
    """
    Check if all required dependencies are available

    Returns:
        True if all dependencies available, False otherwise
    """
    missing_deps: list[str] = []

    try:
        import PyQt6  # noqa: F401
    except ImportError:
        missing_deps.append("PyQt6")

    try:
        from PyQt6 import QtWebEngineWidgets  # noqa: F401
    except ImportError:
        missing_deps.append("PyQt6-WebEngine")

    try:
        import PIL  # noqa: F401
    except ImportError:
        missing_deps.append("Pillow")

    try:
        import exifread  # noqa: F401
    except ImportError:
        missing_deps.append("exifread")

    try:
        import folium  # noqa: F401
    except ImportError:
        missing_deps.append("folium")

    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        logger.error("Please install missing dependencies using:")
        logger.error("pip install -r requirements.txt")
        return False

    return True


def setup_environment() -> None:
    """Setup application environment"""
    # Ensure required directories exist
    base_path = Path(__file__).parent

    required_dirs = [
        base_path / "logs",
        base_path / "config",
        base_path / "assets" / "icons",
        base_path / "assets" / "themes"
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Set environment variables for Qt
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


def main() -> int:
    """
    Main entry point for PhotoGeoView application

    Returns:
        Application exit code
    """
    try:
        # Setup environment first
        setup_environment()

        # Check dependencies
        if not check_dependencies():
            return 1

        # Create and run application
        app = PhotoGeoViewApplication(sys.argv)
        return app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0

    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
