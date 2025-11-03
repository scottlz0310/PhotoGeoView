"""
Integrated UI Components for AI Integration

Combines CursorBLD's excellent UI/UX design with Kiro's optimization:
- CursorBLD: Theme management, thumbnail display, navigation
- Kiro: Memory optimization, performance monitoring, accessibility

Author: Kiro AI Integration System
"""

from .folder_navigator import EnhancedFolderNavigator
from .main_window import IntegratedMainWindow
from .thumbnail_grid import OptimizedThumbnailGrid

__all__ = [
    "EnhancedFolderNavigator",
    "IntegratedMainWindow",
    "OptimizedThumbnailGrid",
]
