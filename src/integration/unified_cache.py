"""
Unified Caching System for AI Integration

Provides intelligent caching for images, thumbnails, and maps:
- Multi-level caching with LRU eviction
- Memory-aware cache management
- Cross-component cache sharing
- Performance optimization

Author: Kiro AI Integration System
"""

import threading
import time
import pickle
import hashlib
from typing import Any, Dict, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from collections import OrderedDict
from dataclasses import dataclass, field
import weakref

from .models import AIComponent, CacheEntry
from .config_manager import ConfigManager
from .error_handling import IntegratedErrorHandler, ErrorCategory
from .logging_system import LoggerSystem


@dataclass
class CacheStats:
    """Cache statistics data structure"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0

    def update_hit_rate(self):
        """Update hit rate calculation"""
        total = self.hits + self.misses
        self.hit_rate = self.hits / total if total > 0 else 0.0


class LRUCache:
    """
    LRU (Least Recently Used) cache implementation
    Thread-safe with configurable size limits
    """

    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100.0):
        """
        Initialize LRU cache

        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
        """

        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)

        # Thread-safe ordered dictionary for LRU behavior
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                # Check if entry is expired
                if entry.is_expired:
                    del self._cache[key]
                    self.stats.misses += 1
                    self.stats.entry_count = len(self._cache)
                    self.stats.update_hit_rate()
                    return None

                # Move to end (most recently used)
                self._cache.move_to_end(key)
                entry.access()

                self.stats.hits += 1
                self.stats.update_hit_rate()
                return entry.data

            self.stats.misses += 1
            self.stats.update_hit_rate()
            return None

    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Put item in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds

        Returns:
            True if item was cached successfully
        """

        with self._lock:
            try:
                # Calculate size of the value
                value_size = self._calculate_size(value)

                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    data=value,
                    size_bytes=value_size,
                    ttl_seconds=ttl_seconds
                )

                # Remove existing entry if present
                if key in self._cache:
                    old_entry = self._cache[key]
                    self.stats.size_bytes -= old_entry.size_bytes
                    del self._cache[key]

                # Check if we need to evict entries
                self._evict_if_needed(value_size)

                # Add new entry
                self._cache[key] = entry
                self.stats.size_bytes += value_size
                self.stats.entry_count = len(self._cache)

                return True

            except Exception:
                return False

    def remove(self, key: str) -> bool:
        """
        Remove item from cache

        Args:
            key: Cache key

        Returns:
            True if item was removed
        """

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                self.stats.size_bytes -= entry.size_bytes
                del self._cache[key]
                self.stats.entry_count = len(self._cache)
                return True
            return False

    def clear(self):
        """Clear all cache entries"""

        with self._lock:
            self._cache.clear()
            self.stats = CacheStats()

    def _evict_if_needed(self, new_entry_size: int):
        """Evict entries if cache limits would be exceeded"""

        # Check size limit
        while (len(self._cache) >= self.max_size or
               self.stats.size_bytes + new_entry_size > self.max_memory_bytes):

            if not self._cache:
                break

            # Remove least recently used item
            oldest_key, oldest_entry = self._cache.popitem(last=False)
            self.stats.size_bytes -= oldest_entry.size_bytes
            self.stats.evictions += 1

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of a value in bytes"""

        try:
            # Try to pickle the object to get size
            return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        except Exception:
            # Fallback size estimation
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, (list, tuple)):
                return sum(self._calculate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._calculate_size(k) + self._calculate_size(v)
                          for k, v in value.items())
            else:
                return 1024  # Default estimate

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            return self.stats

    def get_keys(self) -> List[str]:
        """Get all cache keys"""
        with self._lock:
            return list(self._cache.keys())


class UnifiedCacheSystem:
    """
    Unified caching system for all AI components

    Features:
    - Separate caches for different data types
    - Memory-aware management
    - Cross-component sharing
    - Performance monitoring
    """

    def __init__(self,
                 config_manager: ConfigManager = None,
                 logger_system: LoggerSystem = None):
        """
        Initialize unified cache system

        Args:
            config_manager: Configuration manager instance
            logger_system: Logging system instance
        """

        self.config_manager = config_manager
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger_system)

        # Cache configuration
        self.cache_config = self._load_cache_config()

        # Individual caches for different data types
        self.image_cache = LRUCache(
            max_size=self.cache_config.get("image_max_entries", 500),
            max_memory_mb=self.cache_config.get("image_max_memory_mb", 200.0)
        )

        self.thumbnail_cache = LRUCache(
            max_size=self.cache_config.get("thumbnail_max_entries", 1000),
            max_memory_mb=self.cache_config.get("thumbnail_max_memory_mb", 50.0)
        )

        self.metadata_cache = LRUCache(
            max_size=self.cache_config.get("metadata_max_entries", 2000),
            max_memory_mb=self.cache_config.get("metadata_max_memory_mb", 20.0)
        )

        self.map_cache = LRUCache(
            max_size=self.cache_config.get("map_max_entries", 100),
            max_memory_mb=self.cache_config.get("map_max_memory_mb", 30.0)
        )

        # Cache type mapping
        self.caches = {
            "image": self.image_cache,
            "thumbnail": self.thumbnail_cache,
            "metadata": self.metadata_cache,
            "map": self.map_cache
        }

        # Global cache lock for cross-cache operations
        self._global_lock = threading.RLock()

        # Cache monitoring
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(minutes=5)

        # Weak references to objects for automatic cleanup
        self.weak_refs: Dict[str, weakref.ref] = {}

        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "unified_cache_init",
            f"Unified cache system initialized with {len(self.caches)} cache types"
        )

    def _load_cache_config(self) -> Dict[str, Any]:
        """Load cache configuration from config manager"""

        default_config = {
            "image_max_entries": 500,
            "image_max_memory_mb": 200.0,
            "thumbnail_max_entries": 1000,
            "thumbnail_max_memory_mb": 50.0,
            "metadata_max_entries": 2000,
            "metadata_max_memory_mb": 20.0,
            "map_max_entries": 100,
            "map_max_memory_mb": 30.0,
            "cleanup_interval_minutes": 5,
            "enable_persistence": False,
            "persistence_path": "cache"
        }

        if self.config_manager:
            try:
                cache_config = self.config_manager.get_setting("cache", {})
                default_config.update(cache_config)
            except Exception as e:
                self.error_handler.handle_error(
                    e, ErrorCategory.CONFIGURATION_ERROR,
                    {"operation": "cache_config_load"},
                    AIComponent.KIRO
                )

        return default_config

    # Public cache interface

    def get(self, cache_type: str, key: str, component: AIComponent = AIComponent.KIRO) -> Optional[Any]:
        """
        Get item from specified cache

        Args:
            cache_type: Type of cache (image, thumbnail, metadata, map)
            key: Cache key
            component: AI component making the request

        Returns:
            Cached value or None if not found
        """

        try:
            if cache_type not in self.caches:
                return None

            cache = self.caches[cache_type]
            value = cache.get(key)

            # Log cache access
            if value is not None:
                self.logger_system.log_ai_operation(
                    component,
                    "cache_hit",
                    f"Cache hit: {cache_type}:{key}"
                )
            else:
                self.logger_system.log_ai_operation(
                    component,
                    "cache_miss",
                    f"Cache miss: {cache_type}:{key}"
                )

            return value

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_get", "cache_type": cache_type, "key": key},
                component
            )
            return None

    def put(self, cache_type: str, key: str, value: Any,
            ttl_seconds: Optional[int] = None,
            component: AIComponent = AIComponent.KIRO) -> bool:
        """
        Put item in specified cache

        Args:
            cache_type: Type of cache (image, thumbnail, metadata, map)
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            component: AI component making the request

        Returns:
            True if item was cached successfully
        """

        try:
            if cache_type not in self.caches:
                return False

            cache = self.caches[cache_type]
            success = cache.put(key, value, ttl_seconds)

            if success:
                self.logger_system.log_ai_operation(
                    component,
                    "cache_put",
                    f"Cached: {cache_type}:{key}"
                )

                # Perform cleanup if needed
                self._cleanup_if_needed()

            return success

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_put", "cache_type": cache_type, "key": key},
                component
            )
            return False

    def remove(self, cache_type: str, key: str, component: AIComponent = AIComponent.KIRO) -> bool:
        """
        Remove item from specified cache

        Args:
            cache_type: Type of cache
            key: Cache key
            component: AI component making the request

        Returns:
            True if item was removed
        """

        try:
            if cache_type not in self.caches:
                return False

            cache = self.caches[cache_type]
            success = cache.remove(key)

            if success:
                self.logger_system.log_ai_operation(
                    component,
                    "cache_remove",
                    f"Removed from cache: {cache_type}:{key}"
                )

            return success

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_remove", "cache_type": cache_type, "key": key},
                component
            )
            return False

    def clear(self, cache_type: Optional[str] = None):
        """
        Clear cache(s)

        Args:
            cache_type: Specific cache type to clear, or None to clear all
        """

        try:
            with self._global_lock:
                if cache_type:
                    if cache_type in self.caches:
                        self.caches[cache_type].clear()
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "cache_clear",
                            f"Cleared {cache_type} cache"
                        )
                else:
                    # Clear all caches
                    for cache_name, cache in self.caches.items():
                        cache.clear()

                    self.weak_refs.clear()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "cache_clear_all",
                        "Cleared all caches"
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_clear", "cache_type": cache_type},
                AIComponent.KIRO
            )

    # Specialized cache methods for different data types

    def cache_image(self, image_path: Path, image_data: Any, component: AIComponent = AIComponent.COPILOT) -> bool:
        """Cache image data"""
        key = self._generate_image_key(image_path)
        return self.put("image", key, image_data, component=component)

    def get_cached_image(self, image_path: Path, component: AIComponent = AIComponent.COPILOT) -> Optional[Any]:
        """Get cached image data"""
        key = self._generate_image_key(image_path)
        return self.get("image", key, component=component)

    def cache_thumbnail(self, image_path: Path, size: Tuple[int, int], thumbnail_data: Any,
                       component: AIComponent = AIComponent.CURSOR) -> bool:
        """Cache thumbnail data"""
        key = self._generate_thumbnail_key(image_path, size)
        return self.put("thumbnail", key, thumbnail_data, component=component)

    def get_cached_thumbnail(self, image_path: Path, size: Tuple[int, int],
                           component: AIComponent = AIComponent.CURSOR) -> Optional[Any]:
        """Get cached thumbnail data"""
        key = self._generate_thumbnail_key(image_path, size)
        return self.get("thumbnail", key, component=component)

    def cache_metadata(self, image_path: Path, metadata: Any, component: AIComponent = AIComponent.COPILOT) -> bool:
        """Cache image metadata"""
        key = self._generate_metadata_key(image_path)
        return self.put("metadata", key, metadata, component=component)

    def get_cached_metadata(self, image_path: Path, component: AIComponent = AIComponent.COPILOT) -> Optional[Any]:
        """Get cached image metadata"""
        key = self._generate_metadata_key(image_path)
        return self.get("metadata", key, component=component)

    def cache_map(self, center: Tuple[float, float], zoom: int, map_data: Any,
                  component: AIComponent = AIComponent.COPILOT) -> bool:
        """Cache map data"""
        key = self._generate_map_key(center, zoom)
        return self.put("map", key, map_data, ttl_seconds=3600, component=component)  # 1 hour TTL

    def get_cached_map(self, center: Tuple[float, float], zoom: int,
                      component: AIComponent = AIComponent.COPILOT) -> Optional[Any]:
        """Get cached map data"""
        key = self._generate_map_key(center, zoom)
        return self.get("map", key, component=component)

    # Key generation methods

    def _generate_image_key(self, image_path: Path) -> str:
        """Generate cache key for image"""
        try:
            stat = image_path.stat()
            return f"img_{image_path.stem}_{stat.st_size}_{int(stat.st_mtime)}"
        except Exception:
            return f"img_{image_path.stem}_{hash(str(image_path))}"

    def _generate_thumbnail_key(self, image_path: Path, size: Tuple[int, int]) -> str:
        """Generate cache key for thumbnail"""
        base_key = self._generate_image_key(image_path)
        return f"thumb_{base_key}_{size[0]}x{size[1]}"

    def _generate_metadata_key(self, image_path: Path) -> str:
        """Generate cache key for metadata"""
        base_key = self._generate_image_key(image_path)
        return f"meta_{base_key}"

    def _generate_map_key(self, center: Tuple[float, float], zoom: int) -> str:
        """Generate cache key for map"""
        lat, lon = center
        return f"map_{lat:.4f}_{lon:.4f}_{zoom}"

    # Cache management

    def _cleanup_if_needed(self):
        """Perform cleanup if interval has passed"""

        now = datetime.now()
        if now - self.last_cleanup >= self.cleanup_interval:
            self._cleanup_expired_entries()
            self.last_cleanup = now

    def _cleanup_expired_entries(self):
        """Clean up expired entries from all caches"""

        try:
            with self._global_lock:
                total_removed = 0

                for cache_name, cache in self.caches.items():
                    with cache._lock:
                        expired_keys = []

                        for key, entry in cache._cache.items():
                            if entry.is_expired:
                                expired_keys.append(key)

                        for key in expired_keys:
                            entry = cache._cache[key]
                            cache.stats.size_bytes -= entry.size_bytes
                            del cache._cache[key]
                            total_removed += 1

                        cache.stats.entry_count = len(cache._cache)

                if total_removed > 0:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "cache_cleanup",
                        f"Cleaned up {total_removed} expired cache entries"
                    )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_cleanup"},
                AIComponent.KIRO
            )

    # Statistics and monitoring

    def get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""

        try:
            stats = {}

            for cache_name, cache in self.caches.items():
                cache_stats = cache.get_stats()
                stats[cache_name] = {
                    "hits": cache_stats.hits,
                    "misses": cache_stats.misses,
                    "evictions": cache_stats.evictions,
                    "size_bytes": cache_stats.size_bytes,
                    "size_mb": cache_stats.size_bytes / 1024 / 1024,
                    "entry_count": cache_stats.entry_count,
                    "hit_rate": cache_stats.hit_rate
                }

            return stats

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_stats"},
                AIComponent.KIRO
            )
            return {}

    def get_total_memory_usage(self) -> float:
        """Get total memory usage across all caches in MB"""

        try:
            total_bytes = sum(cache.get_stats().size_bytes for cache in self.caches.values())
            return total_bytes / 1024 / 1024
        except Exception:
            return 0.0

    def get_cache_summary(self) -> Dict[str, Any]:
        """Get summary of cache system"""

        try:
            stats = self.get_cache_stats()

            total_hits = sum(s["hits"] for s in stats.values())
            total_misses = sum(s["misses"] for s in stats.values())
            total_entries = sum(s["entry_count"] for s in stats.values())
            total_memory_mb = self.get_total_memory_usage()

            overall_hit_rate = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0.0

            return {
                "cache_types": len(self.caches),
                "total_entries": total_entries,
                "total_memory_mb": total_memory_mb,
                "overall_hit_rate": overall_hit_rate,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "individual_stats": stats,
                "last_cleanup": self.last_cleanup.isoformat()
            }

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "cache_summary"},
                AIComponent.KIRO
            )
            return {"status": "error"}

    # Configuration management

    def update_cache_config(self, new_config: Dict[str, Any]):
        """Update cache configuration"""

        try:
            self.cache_config.update(new_config)

            # Save to configuration manager
            if self.config_manager:
                self.config_manager.set_setting("cache", self.cache_config)

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "cache_config_update",
                f"Cache configuration updated: {new_config}"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CONFIGURATION_ERROR,
                {"operation": "cache_config_update"},
                AIComponent.KIRO
            )

    def shutdown(self):
        """Shutdown the cache system"""

        try:
            # Clear all caches
            self.clear()

            # Clear weak references
            self.weak_refs.clear()

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "unified_cache_shutdown",
                "Unified cache system shutdown complete"
            )

        except Exception as e:
            self.logger_system.log_error(
                AIComponent.KIRO,
                e,
                "unified_cache_shutdown",
                {}
            )
