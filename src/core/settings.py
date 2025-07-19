"""
PhotoGeoView Settings Management
Handles application configuration, persistence, and validation
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field

from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WindowSettings:
    """Window positioning and size settings"""
    width: int = 1200
    height: int = 800
    x: int = 100
    y: int = 100
    maximized: bool = False
    remember_position: bool = True
    remember_size: bool = True


@dataclass
class UISettings:
    """User interface appearance settings"""
    current_theme: str = "dark_blue.xml"
    theme_manager_enabled: bool = True
    selected_themes: List[str] = field(default_factory=lambda: ["dark_blue.xml", "light_blue.xml"])
    theme_toggle_index: int = 0
    show_thumbnails: bool = True
    thumbnail_size: int = 128
    thumbnail_cache_size: int = 1000
    show_toolbar: bool = True
    show_status_bar: bool = True
    panel_splitter_state: Optional[bytes] = None
    image_panel_maximized: bool = False
    map_panel_maximized: bool = False


@dataclass
class FolderSettings:
    """Folder navigation and file handling settings"""
    last_opened_folder: str = ""
    recent_folders: List[str] = field(default_factory=lambda: [])
    max_recent_folders: int = 10
    show_hidden_files: bool = False
    supported_formats: List[str] = field(default_factory=lambda: [
        ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"
    ])


@dataclass
class ImageViewerSettings:
    """Image display and manipulation settings"""
    fit_to_window: bool = True
    zoom_factor: float = 1.0
    smooth_scaling: bool = True
    background_color: str = "#2b2b2b"
    show_exif_panel: bool = True
    auto_rotate: bool = True


@dataclass
class MapViewerSettings:
    """Map display and interaction settings"""
    default_zoom: int = 15
    tile_layer: str = "OpenStreetMap"
    show_satellite: bool = False
    marker_color: str = "red"
    marker_size: str = "medium"
    cluster_markers: bool = True
    show_photo_popup: bool = True


@dataclass
class PerformanceSettings:
    """Performance optimization settings"""
    max_thumbnail_cache_mb: int = 100
    preload_adjacent_images: bool = True
    lazy_load_thumbnails: bool = True
    max_concurrent_loads: int = 4
    image_cache_size: int = 50


@dataclass
class LoggingSettings:
    """Logging configuration settings"""
    level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    max_log_files: int = 5
    max_log_size_mb: int = 10


@dataclass
class AdvancedSettings:
    """Advanced application settings"""
    use_hardware_acceleration: bool = True
    check_for_updates: bool = True
    auto_save_settings: bool = True
    save_interval_seconds: int = 30
    backup_settings: bool = True


class SettingsManager:
    """
    Main settings management class for PhotoGeoView
    Handles loading, saving, validation, and access to all application settings
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize settings manager

        Args:
            config_path: Optional path to config file
        """
        self.logger = logger
        self._config_path = config_path or Path(__file__).parent.parent.parent / "config" / "config.json"
        self._backup_path = self._config_path.with_suffix('.json.backup')

        # Initialize setting categories
        self.window = WindowSettings()
        self.ui = UISettings()
        self.folders = FolderSettings()
        self.image_viewer = ImageViewerSettings()
        self.map_viewer = MapViewerSettings()
        self.performance = PerformanceSettings()
        self.logging = LoggingSettings()
        self.advanced = AdvancedSettings()

        # Load settings from file
        self.load()

        self.logger.info(f"Settings manager initialized with config: {self._config_path}")

    def load(self) -> bool:
        """
        Load settings from JSON configuration file

        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            if not self._config_path.exists():
                self.logger.warning(f"Config file not found: {self._config_path}")
                self.create_default_config()
                return True

            with open(self._config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Load each settings category
            self._load_category(config_data.get('window', {}), self.window)
            self._load_category(config_data.get('ui', {}), self.ui)
            self._load_category(config_data.get('folders', {}), self.folders)
            self._load_category(config_data.get('image_viewer', {}), self.image_viewer)
            self._load_category(config_data.get('map_viewer', {}), self.map_viewer)
            self._load_category(config_data.get('performance', {}), self.performance)
            self._load_category(config_data.get('logging', {}), self.logging)
            self._load_category(config_data.get('advanced', {}), self.advanced)

            self.logger.info("Settings loaded successfully")
            return True

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            return self._restore_from_backup()

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return self._restore_from_backup()

    def save(self) -> bool:
        """
        Save current settings to JSON configuration file

        Returns:
            True if successfully saved, False otherwise
        """
        try:
            # Create backup before saving
            if self._config_path.exists() and self.advanced.backup_settings:
                self._create_backup()

            config_data = {
                'window': asdict(self.window),
                'ui': asdict(self.ui),
                'folders': asdict(self.folders),
                'image_viewer': asdict(self.image_viewer),
                'map_viewer': asdict(self.map_viewer),
                'performance': asdict(self.performance),
                'logging': asdict(self.logging),
                'advanced': asdict(self.advanced)
            }

            # Ensure config directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)

            self.logger.info("Settings saved successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values"""
        self.logger.info("Resetting all settings to defaults")

        self.window = WindowSettings()
        self.ui = UISettings()
        self.folders = FolderSettings()
        self.image_viewer = ImageViewerSettings()
        self.map_viewer = MapViewerSettings()
        self.performance = PerformanceSettings()
        self.logging = LoggingSettings()
        self.advanced = AdvancedSettings()

        self.save()

    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value

        Args:
            category: Setting category (e.g., 'window', 'ui')
            key: Setting key within the category
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        try:
            category_obj = getattr(self, category, None)
            if category_obj is None:
                return default

            return getattr(category_obj, key, default)
        except Exception as e:
            self.logger.error(f"Failed to get setting {category}.{key}: {e}")
            return default

    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """
        Set a specific setting value

        Args:
            category: Setting category (e.g., 'window', 'ui')
            key: Setting key within the category
            value: New value to set

        Returns:
            True if successfully set, False otherwise
        """
        try:
            category_obj = getattr(self, category, None)
            if category_obj is None:
                self.logger.error(f"Unknown settings category: {category}")
                return False

            if not hasattr(category_obj, key):
                self.logger.error(f"Unknown setting key: {category}.{key}")
                return False

            setattr(category_obj, key, value)

            if self.advanced.auto_save_settings:
                self.save()

            self.logger.debug(f"Set {category}.{key} = {value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set setting {category}.{key}: {e}")
            return False

    def add_recent_folder(self, folder_path: str) -> None:
        """
        Add a folder to recent folders list

        Args:
            folder_path: Absolute path to the folder
        """
        if not folder_path or not os.path.exists(folder_path):
            return

        # Remove if already exists (to move to front)
        if folder_path in self.folders.recent_folders:
            self.folders.recent_folders.remove(folder_path)

        # Add to front
        self.folders.recent_folders.insert(0, folder_path)

        # Limit to max count
        if len(self.folders.recent_folders) > self.folders.max_recent_folders:
            self.folders.recent_folders = self.folders.recent_folders[:self.folders.max_recent_folders]

        if self.advanced.auto_save_settings:
            self.save()

        self.logger.debug(f"Added recent folder: {folder_path}")

    def get_recent_folders(self) -> List[str]:
        """
        Get list of recent folders (existing ones only)

        Returns:
            List of recent folder paths that still exist
        """
        existing_folders = [
            folder for folder in self.folders.recent_folders
            if os.path.exists(folder)
        ]

        # Update list if some folders no longer exist
        if len(existing_folders) != len(self.folders.recent_folders):
            self.folders.recent_folders = existing_folders
            if self.advanced.auto_save_settings:
                self.save()

        return existing_folders

    def _load_category(self, data: Dict[str, Any], category_obj: object) -> None:
        """Load data into a settings category object"""
        for key, value in data.items():
            if hasattr(category_obj, key):
                setattr(category_obj, key, value)

    def _create_backup(self) -> None:
        """Create a backup of the current config file"""
        try:
            if self._config_path.exists():
                import shutil
                shutil.copy2(self._config_path, self._backup_path)
                self.logger.debug("Config backup created")
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")

    def _restore_from_backup(self) -> bool:
        """Restore settings from backup file"""
        try:
            if self._backup_path.exists():
                import shutil
                shutil.copy2(self._backup_path, self._config_path)
                self.logger.info("Restored settings from backup")
                return self.load()
            else:
                self.logger.warning("No backup found, creating default config")
                self.create_default_config()
                return True
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            self.create_default_config()
            return True

    def create_default_config(self) -> None:
        """Create default configuration file"""
        self.logger.info("Creating default configuration")
        self.reset_to_defaults()
        self.save()


# Global settings instance
_settings_manager: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """
    Get the global settings manager instance

    Returns:
        Global SettingsManager instance
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def init_settings(config_path: Optional[Path] = None) -> SettingsManager:
    """
    Initialize the global settings manager

    Args:
        config_path: Optional path to config file

    Returns:
        Initialized SettingsManager instance
    """
    global _settings_manager
    _settings_manager = SettingsManager(config_path)
    return _settings_manager
