"""
File utilities for EXIF processing
Shared functions for file operations and formatting
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from src.core.logger import get_logger

logger = get_logger(__name__)


class FileUtils:
    """Utility class for file operations"""

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format

        Args:
            size_bytes: File size in bytes

        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        try:
            if size_bytes == 0:
                return "0 B"

            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            size = float(size_bytes)

            while size >= 1024.0 and i < len(size_names) - 1:
                size /= 1024.0
                i += 1

            return f"{size:.1f} {size_names[i]}"

        except Exception as e:
            logger.debug(f"File size formatting error: {e}")
            return f"{size_bytes} B"

    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get basic file information

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file info or None
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return None

            stat_info = path_obj.stat()

            return {
                'File Name': path_obj.name,
                'File Size': FileUtils.format_file_size(stat_info.st_size),
                'Modified': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'Full Path': str(path_obj.absolute()),
                'Extension': path_obj.suffix.lower(),
                'Size Bytes': stat_info.st_size
            }

        except Exception as e:
            logger.warning(f"Error getting file info for {file_path}: {e}")
            return None

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """
        Check if file is a supported image format

        Args:
            file_path: Path to file

        Returns:
            True if file is an image
        """
        try:
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
            return Path(file_path).suffix.lower() in image_extensions
        except Exception:
            return False
