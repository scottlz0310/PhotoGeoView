"""
AI Integration Module for PhotoGeoView

This module provides the integration layer for combining GitHub Copilot (CS4Coding),
Cursor (CursorBLD), and Kiro implementations into a unified application.

Author: Kiro AI Integration System
Created: 2025-01-25
"""

__version__ = "1.0.0"
__author__ = "Kiro AI Integration System"

from .config_manager import ConfigManager
from .controllers import AppController
from .error_handling import ErrorCategory, IntegratedErrorHandler

# Integration layer exports
from .interfaces import IConfigManager, IImageProcessor, IMapProvider, IThemeManager
from .logging_system import LoggerSystem
from .models import ApplicationState, ImageMetadata, ThemeConfiguration
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
    "StateManager",
]
