"""
EXIF Panel Labels Configuration

This module provides theme-aware labels for the EXIF panel,
allowing labels to inherit theme styling and support multiple languages.

Author: Kiro AI Integration System
"""

from typing import Any

# Default English labels
DEFAULT_LABELS = {
    "file_information": {
        "title": "📁 File Information",
        "file_name": "File Name",
        "file_size": "File Size",
        "modified": "Modified",
        "extension": "Extension",
        "debug": "Debug",
        "no_file_info": "No file information",
    },
    "camera_information": {
        "title": "📸 Camera Information",
        "camera_make": "Camera Make",
        "camera_model": "Camera Model",
        "lens_model": "Lens Model",
        "debug": "Debug",
        "no_camera_info": "No camera information",
    },
    "shooting_settings": {
        "title": "⚙️ Shooting Settings",
        "f_number": "F-Number",
        "exposure_time": "Exposure Time",
        "iso_speed": "ISO Speed",
        "focal_length": "Focal Length",
        "debug": "Debug",
        "no_settings": "No shooting settings",
    },
    "shooting_date": {
        "title": "🕒 Shooting Date",
        "date_taken": "Date Taken",
        "date_original": "Date Original",
        "debug": "Debug",
        "no_date": "No shooting date",
    },
    "position_information": {
        "title": "📍 Position Information & Map Integration",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "altitude": "Altitude",
        "gps_time": "GPS Time",
        "gps_date": "GPS Date",
        "not_available": "Not available",
        "raw_data": "raw data",
        "conversion_error": "conversion error",
    },
    "debug_information": {
        "title": "🔧 Debug Information",
        "show_debug": "Show Debug Info",
        "hide_debug": "Hide Debug Info",
        "raw_gps_info": "Raw GPS EXIF Information:",
        "coordinate_conversion": "Coordinate Conversion Information:",
        "no_gps_info": "GPS information not available",
        "no_conversion_info": "No conversion information",
    },
    "buttons": {
        "refresh": "🔄 Refresh",
        "show_map": "🗺️ Show on Map",
        "copy_coordinates": "📋 Copy Coordinates",
        "select_image": "📷 Please select an image",
    },
    "messages": {
        "exif_read_error": "Failed to read EXIF information",
        "coordinates_copied": "GPS coordinates copied to clipboard",
    },
}

# Japanese labels (for future localization)
JAPANESE_LABELS = {
    "file_information": {
        "title": "📁 ファイル情報",
        "file_name": "ファイル名",
        "file_size": "ファイルサイズ",
        "modified": "更新日時",
        "extension": "拡張子",
        "debug": "デバッグ",
        "no_file_info": "ファイル情報なし",
    },
    "camera_information": {
        "title": "📸 カメラ情報",
        "camera_make": "メーカー",
        "camera_model": "モデル",
        "lens_model": "レンズ",
        "debug": "デバッグ",
        "no_camera_info": "カメラ情報なし",
    },
    "shooting_settings": {
        "title": "⚙️ 撮影設定",
        "f_number": "F値",
        "exposure_time": "シャッター速度",
        "iso_speed": "ISO感度",
        "focal_length": "焦点距離",
        "debug": "デバッグ",
        "no_settings": "撮影設定なし",
    },
    "shooting_date": {
        "title": "🕒 撮影日時",
        "date_taken": "撮影日時",
        "date_original": "元の撮影日時",
        "debug": "デバッグ",
        "no_date": "撮影日時なし",
    },
    "position_information": {
        "title": "📍 位置情報・地図連携",
        "latitude": "緯度",
        "longitude": "経度",
        "altitude": "高度",
        "gps_time": "GPS時刻",
        "gps_date": "GPS日付",
        "not_available": "未取得",
        "raw_data": "生データ",
        "conversion_error": "変換エラー",
    },
    "debug_information": {
        "title": "🔧 デバッグ情報",
        "show_debug": "デバッグ情報を表示",
        "hide_debug": "デバッグ情報を非表示",
        "raw_gps_info": "生のGPS EXIF情報:",
        "coordinate_conversion": "座標変換情報:",
        "no_gps_info": "GPS情報なし",
        "no_conversion_info": "変換情報なし",
    },
    "buttons": {
        "refresh": "🔄 更新",
        "show_map": "🗺️ 地図表示",
        "copy_coordinates": "📋 座標コピー",
        "select_image": "📷 画像を選択してください",
    },
    "messages": {
        "exif_read_error": "EXIF情報の読み込みに失敗しました",
        "coordinates_copied": "GPS座標をクリップボードにコピーしました",
    },
}

class EXIFLabelManager:
    """
    Manages EXIF panel labels with theme-aware styling
    """

    def __init__(self, language: str = "en"):
        """
        Initialize the label manager

        Args:
            language: Language code ("en" for English, "ja" for Japanese)
        """
        self.language = language
        self.labels = JAPANESE_LABELS if language == "ja" else DEFAULT_LABELS

    def get_label(self, section: str, key: str) -> str:
        """
        Get a label for the specified section and key

        Args:
            section: Label section (e.g., "file_information")
            key: Label key (e.g., "title")

        Returns:
            The label text
        """
        try:
            return self.labels.get(section, {}).get(key, f"{section}.{key}")
        except (KeyError, AttributeError):
            return f"{section}.{key}"

    def get_section_labels(self, section: str) -> dict[str, str]:
        """
        Get all labels for a section

        Args:
            section: Label section name

        Returns:
            Dictionary of labels for the section
        """
        return self.labels.get(section, {})

    def set_language(self, language: str) -> None:
        """
        Change the language

        Args:
            language: Language code ("en" or "ja")
        """
        self.language = language
        self.labels = JAPANESE_LABELS if language == "ja" else DEFAULT_LABELS

    def get_available_languages(self) -> list[str]:
        """Get list of available languages"""
        return ["en", "ja"]

    def export_labels_for_theme(self) -> dict[str, Any]:
        """
        Export labels in a format suitable for theme configuration

        Returns:
            Dictionary of labels organized by section
        """
        return {
            "exif_labels": self.labels,
            "language": self.language,
            "available_languages": self.get_available_languages(),
        }
