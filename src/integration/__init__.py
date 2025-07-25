"""
AI Integration Module for PhotoGeoView

This module provides the integration layer for combining GitHub Copilot (CS4Coding),
Cursor (CursorBLD), and Kiro implementations into a unified application.

Author: Kiro AI Integration System
Created: 2025-01-25
"""

__version__ = "1.0.0"
__author__ = "Kiro AI Integration System"

# Integration layer exports
from .interfaces import IImageProcessor, IThemeManager, IMapProvider, IConfigManager
from .controllers import AppController
from .models import ImageMetadata, ThemeConfiguration, ApplicationState
from .error_handling import IntegratedErrorHandler, ErrorCategory
from .logging_system import LoggerSystem
from .config_manager import ConfigManager
from .state_manager import StateManager

__all__ = [
    "IImageProcessor",
    "IThemeManager",
    "IMapProvider",
    "IConfigManager",
    "AppController",
    "ImageMetadata",
    "ThemeConfiguration",
    "ApplicationState",
    "IntegratedErrorHandler",
    "ErrorCategory",
    "LoggerSystem",
    "ConfigManager",
    "StateManager"
]
