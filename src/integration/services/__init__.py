"""
Services module for AI Integration

Contains service classes that provide business logic and data processing:
- FileDiscoveryService: Image file detection and validation
- FileSystemWatcher: File system monitoring
- CacheService: Unified caching functionality

Author: Kiro AI Integration System
"""

from .file_discovery_service import FileDiscoveryService
from .file_system_watcher import FileSystemWatcher, FileChangeType

__all__ = ["FileDiscoveryService", "FileSystemWatcher", "FileChangeType"]
