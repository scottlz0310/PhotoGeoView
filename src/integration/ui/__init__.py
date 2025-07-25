"""
Integrated UI Components for AI Integration

Combines CursorBLD's excellent UI/UX design with Kiro's optimization:
- CursorBLD: Theme management, thumbnail display, navigation
- Kiro: Memory optimization, performance monitoring, accessibility

Author: Kiro AI Integration System
"""

from .main_window import IntegratedMainWindow
from .theme_manager import IntegratedThemeManager
from .thumbnail_grid import OptimizedThumbnailGrid
from .folder_navigator import EnhancedFolderNavigator

__all__ = [
    "IntegratedMainWindow",
    "IntegratedThemeManager",
    "OptimizedThumbnailGrid",
    "EnhancedFolderNavigator"
]
