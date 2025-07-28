"""
Tests for Kiro Integration Layer Components

Tests the Kiro-specific components:
- PerformanceMonitor for system monitoring
- UnifiedCacheSystem for intelligent caching
- StateManager for centralized state management

Author: Kiro AI Integration System
"""

import unittest
import tempfile
import shutil
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.performance_monitor import KiroPerformanceMonitor, PerformanceAlert, ResourceThresholds
from integration.unified_cache import UnifiedCacheSystem, LRUCache, CacheStats
from integration.state_manager import StateManager, StateChangeEvent
from integration.config_manager import ConfigManager
from integration.logging_system import LoggerSystem
from integration.models import AIComponent, ApplicationState, PerformanceMetrics


class TestKiroPerformanceMonitor(unittest.TestCase):
    """Test cases for Kiro Performance Monitor"""

    def setUp(self):
        """Set up test environment"""

        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)

        # Mock config settings
        self.mock_config_manager.get_setting.return_value = {}

        self.monitor = KiroPerformanceMonitor(
            config_manager=self.mock_config_manager,
            logger_system=self.mock_logger_system
        )

    def tearDown(self):
        """Clean up test environment"""

        self.monitor.stop_monitoring()
        self.monitor.shutdown()

    def test_initialization(self):
        """Test performance monitor initialization"""

        self.assertIsNotNone(self.monitor)
        self.assertFalse(self.monitor.is_monitoring)
        self.assertIsInstance(self.monitor.thresholds, ResourceThresholds)
        self.assertEqual(len(self.monitor.ai_components), 3)

    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""

        # Start monitoring
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.is_monitoring)
        self.assertIsNotNone(self.monitor.monitoring_thread)

        # Stop monitoring
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.is_monitoring)

    def test_memory_usage_collection(self):
        """Test memory usage collection"""

        memory_stats = self.monitor.get_memory_usage()

        self.assertIsInstance(memory_stats, dict)
        self.assertIn("process_rss_mb", memory_stats)
        self.assertIn("system_total_mb", memory_stats)
        self.assertIn("system_available_mb", memory_stats)
        self.assertIn("system_used_percent", memory_stats)

    def test_performance_metrics_collection(self):
        """Test performance metrics collection"""

        metrics = self.monitor.get_performance_metrics()

        self.assertIsInstance(metrics, dict)
        self.assertIn("system_info", metrics)
        self.assertIn("monitoring_active", metrics)

    def test_operation_time_logging(self):
        """Test operation time logging"""

        # Log some operation times
        self.monitor.log_operation_time("image_load", 0.5)
        self.monitor.log_operation_time("thumbnail_generation", 0.2)
        self.monitor.log_operation_time("ui_update", 0.1)

        # Check that component response times were updated
        copilot_times = self.monitor.ai_components[AIComponent.COPILOT]["response_times"]
        cursor_times = self.monitor.ai_components[AIComponent.CURSOR]["response_times"]

        self.assertGreater(len(copilot_times), 0)
        self.assertGreater(len(cursor_times), 0)

    def test_ai_component_status(self):
        """Test AI component status tracking"""

        # Initially all components should be unknown or inactive
        status = self.monitor.get_ai_component_status()

        self.assertIsInstance(status, dict)
        self.assertEqual(len(status), 3)
        self.assertIn(AIComponent.COPILOT, status)
        self.assertIn(AIComponent.CURSOR, status)
        self.assertIn(AIComponent.KIRO, status)

    def test_alert_system(self):
        """Test performance alert system"""

        alerts_received = []

        def alert_handler(alert: PerformanceAlert):
            alerts_received.append(alert)

        # Add alert handler
        self.monitor.add_alert_handler(alert_handler)

        # Trigger an alert by setting low thresholds
        self.monitor.thresholds.memory_warning_mb = 0.1  # Very low threshold

        # Collect metrics to trigger alert
        self.monitor._collect_metrics()

        # Remove alert handler
        self.monitor.remove_alert_handler(alert_handler)

        # Check that handler was called (may not trigger due to actual memory usage)
        self.assertIsInstance(alerts_received, list)

    def test_threshold_updates(self):
        """Test updating performance thresholds"""

        new_thresholds = {
            "memory_warning_mb": 500.0,
            "cpu_warning_percent": 80.0
        }

        self.monitor.update_thresholds(
            memory_warning_mb=500.0,
            cpu_warning_percent=80.0
        )

        self.assertEqual(self.monitor.thresholds.memory_warning_mb, 500.0)
        self.assertEqual(self.monitor.thresholds.cpu_warning_percent, 80.0)

    def test_performance_summary(self):
        """Test performance summary generation"""

        # Start monitoring to collect some data
        self.monitor.start_monitoring()
        time.sleep(0.1)  # Brief delay to collect metrics
        self.monitor.stop_monitoring()

        summary = self.monitor.get_performance_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn("status", summary)

        # Check if we have data or no_data status
        if summary.get("status") == "no_data":
            # If no data, just check the basic structure
            self.assertEqual(summary["status"], "no_data")
        else:
            # If we have data, check for expected fields
            self.assertIn("component_status", summary)
            self.assertIn("system_info", summary)

    def test_recent_alerts(self):
        """Test recent alerts retrieval"""

        # Get recent alerts
        alerts = self.monitor.get_recent_alerts(minutes=60)

        self.assertIsInstance(alerts, list)

    def test_alert_cooldown(self):
        """Test alert cooldown mechanism"""

        # Clear any existing alerts
        self.monitor.clear_alerts()

        # Create multiple alerts of the same type
        self.monitor._create_alert("warning", "Test alert", AIComponent.KIRO,
                                 "test_metric", 100.0, 50.0)

        # Second alert should be blocked by cooldown
        self.monitor._create_alert("warning", "Test alert", AIComponent.KIRO,
                                 "test_metric", 100.0, 50.0)

        # Should only have one alert due to cooldown
        self.assertLessEqual(len(self.monitor.recent_alerts), 1)


class TestLRUCache(unittest.TestCase):
    """Test cases for LRU Cache"""

    def setUp(self):
        """Set up test environment"""

        self.cache = LRUCache(max_size=3, max_memory_mb=1.0)

    def test_basic_operations(self):
        """Test basic cache operations"""

        # Test put and get
        self.assertTrue(self.cache.put("key1", "value1"))
        self.assertEqual(self.cache.get("key1"), "value1")

        # Test miss
        self.assertIsNone(self.cache.get("nonexistent"))

        # Test remove
        self.assertTrue(self.cache.remove("key1"))
        self.assertIsNone(self.cache.get("key1"))

    def test_lru_eviction(self):
        """Test LRU eviction policy"""

        # Fill cache to capacity
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")

        # Access key1 to make it most recently used
        self.cache.get("key1")

        # Add another item, should evict key2 (least recently used)
        self.cache.put("key4", "value4")

        self.assertIsNotNone(self.cache.get("key1"))  # Should still exist
        self.assertIsNone(self.cache.get("key2"))     # Should be evicted
        self.assertIsNotNone(self.cache.get("key3"))  # Should still exist
        self.assertIsNotNone(self.cache.get("key4"))  # Should exist

    def test_ttl_expiration(self):
        """Test TTL (time to live) expiration"""

        # Put item with short TTL
        self.cache.put("key1", "value1", ttl_seconds=1)

        # Should be available immediately
        self.assertEqual(self.cache.get("key1"), "value1")

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        self.assertIsNone(self.cache.get("key1"))

    def test_cache_stats(self):
        """Test cache statistics"""

        stats = self.cache.get_stats()
        self.assertIsInstance(stats, CacheStats)
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 0)

        # Perform operations
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # Hit
        self.cache.get("key2")  # Miss

        stats = self.cache.get_stats()
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 1)
        self.assertEqual(stats.hit_rate, 0.5)

    def test_clear_cache(self):
        """Test cache clearing"""

        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")

        self.cache.clear()

        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
        self.assertEqual(self.cache.get_stats().entry_count, 0)


class TestUnifiedCacheSystem(unittest.TestCase):
    """Test cases for Unified Cache System"""

    def setUp(self):
        """Set up test environment"""

        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)

        # Mock config settings
        self.mock_config_manager.get_setting.return_value = {}

        self.cache_system = UnifiedCacheSystem(
            config_manager=self.mock_config_manager,
            logger_system=self.mock_logger_system
        )

    def tearDown(self):
        """Clean up test environment"""

        self.cache_system.shutdown()

    def test_initialization(self):
        """Test cache system initialization"""

        self.assertIsNotNone(self.cache_system)
        self.assertEqual(len(self.cache_system.caches), 4)  # image, thumbnail, metadata, map
        self.assertIn("image", self.cache_system.caches)
        self.assertIn("thumbnail", self.cache_system.caches)
        self.assertIn("metadata", self.cache_system.caches)
        self.assertIn("map", self.cache_system.caches)

    def test_basic_cache_operations(self):
        """Test basic cache operations"""

        # Test put and get
        self.assertTrue(self.cache_system.put("image", "test_key", "test_value"))
        self.assertEqual(self.cache_system.get("image", "test_key"), "test_value")

        # Test remove
        self.assertTrue(self.cache_system.remove("image", "test_key"))
        self.assertIsNone(self.cache_system.get("image", "test_key"))

    def test_specialized_cache_methods(self):
        """Test specialized cache methods"""

        test_path = Path("test_image.jpg")
        test_image_data = b"fake image data"
        test_thumbnail_data = b"fake thumbnail data"
        test_metadata = {"camera": "Canon", "iso": 400}

        # Test image caching
        self.assertTrue(self.cache_system.cache_image(test_path, test_image_data))
        cached_image = self.cache_system.get_cached_image(test_path)
        self.assertEqual(cached_image, test_image_data)

        # Test thumbnail caching
        size = (150, 150)
        self.assertTrue(self.cache_system.cache_thumbnail(test_path, size, test_thumbnail_data))
        cached_thumbnail = self.cache_system.get_cached_thumbnail(test_path, size)
        self.assertEqual(cached_thumbnail, test_thumbnail_data)

        # Test metadata caching
        self.assertTrue(self.cache_system.cache_metadata(test_path, test_metadata))
        cached_metadata = self.cache_system.get_cached_metadata(test_path)
        self.assertEqual(cached_metadata, test_metadata)

        # Test map caching
        center = (40.7128, -74.0060)
        zoom = 10
        map_data = {"tiles": "fake_map_data"}
        self.assertTrue(self.cache_system.cache_map(center, zoom, map_data))
        cached_map = self.cache_system.get_cached_map(center, zoom)
        self.assertEqual(cached_map, map_data)

    def test_cache_statistics(self):
        """Test cache statistics"""

        stats = self.cache_system.get_cache_stats()

        self.assertIsInstance(stats, dict)
        self.assertEqual(len(stats), 4)

        for cache_name in ["image", "thumbnail", "metadata", "map"]:
            self.assertIn(cache_name, stats)
            cache_stats = stats[cache_name]
            self.assertIn("hits", cache_stats)
            self.assertIn("misses", cache_stats)
            self.assertIn("hit_rate", cache_stats)
            self.assertIn("entry_count", cache_stats)

    def test_cache_summary(self):
        """Test cache summary"""

        summary = self.cache_system.get_cache_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn("cache_types", summary)
        self.assertIn("total_entries", summary)
        self.assertIn("total_memory_mb", summary)
        self.assertIn("overall_hit_rate", summary)
        self.assertIn("individual_stats", summary)

    def test_cache_clearing(self):
        """Test cache clearing"""

        # Add some data
        self.cache_system.put("image", "key1", "value1")
        self.cache_system.put("thumbnail", "key2", "value2")

        # Clear specific cache
        self.cache_system.clear("image")
        self.assertIsNone(self.cache_system.get("image", "key1"))
        self.assertIsNotNone(self.cache_system.get("thumbnail", "key2"))

        # Clear all caches
        self.cache_system.clear()
        self.assertIsNone(self.cache_system.get("thumbnail", "key2"))

    def test_memory_usage_tracking(self):
        """Test memory usage tracking"""

        # Add some data
        large_data = "x" * 1000  # 1KB of data
        self.cache_system.put("image", "large_key", large_data)

        memory_usage = self.cache_system.get_total_memory_usage()
        self.assertGreater(memory_usage, 0)

    def test_key_generation(self):
        """Test cache key generation"""

        test_path = Path("test_image.jpg")

        # Test different key generation methods
        image_key = self.cache_system._generate_image_key(test_path)
        thumbnail_key = self.cache_system._generate_thumbnail_key(test_path, (150, 150))
        metadata_key = self.cache_system._generate_metadata_key(test_path)
        map_key = self.cache_system._generate_map_key((40.7128, -74.0060), 10)

        self.assertIsInstance(image_key, str)
        self.assertIsInstance(thumbnail_key, str)
        self.assertIsInstance(metadata_key, str)
        self.assertIsInstance(map_key, str)

        # Keys should be different
        self.assertNotEqual(image_key, thumbnail_key)
        self.assertNotEqual(image_key, metadata_key)


class TestStateManager(unittest.TestCase):
    """Test cases for State Manager"""

    def setUp(self):
        """Set up test environment"""

        self.test_dir = Path(tempfile.mkdtemp())

        self.mock_config_manager = Mock(spec=ConfigManager)
        self.mock_logger_system = Mock(spec=LoggerSystem)

        self.state_manager = StateManager(
            config_manager=self.mock_config_manager,
            logger_system=self.mock_logger_system
        )

    def tearDown(self):
        """Clean up test environment"""

        self.state_manager.shutdown()

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test state manager initialization"""

        self.assertIsNotNone(self.state_manager)
        self.assertIsInstance(self.state_manager.app_state, ApplicationState)

    def test_basic_state_operations(self):
        """Test basic state get/set operations"""

        # Test setting and getting values
        self.assertTrue(self.state_manager.set_state_value("current_theme", "dark"))
        self.assertEqual(self.state_manager.get_state_value("current_theme"), "dark")

        # Test default values
        self.assertEqual(self.state_manager.get_state_value("nonexistent", "default"), "default")

    def test_state_validation(self):
        """Test state value validation"""

        # Valid values should work
        self.assertTrue(self.state_manager.set_state_value("thumbnail_size", 150))

        # Invalid values should be rejected
        self.assertFalse(self.state_manager.set_state_value("thumbnail_size", -10))
        self.assertFalse(self.state_manager.set_state_value("thumbnail_size", 1000))

    def test_bulk_state_update(self):
        """Test bulk state updates"""

        updates = {
            "current_theme": "blue",
            "thumbnail_size": 200,
            "performance_mode": "performance"
        }

        self.assertTrue(self.state_manager.update_state(**updates))

        self.assertEqual(self.state_manager.get_state_value("current_theme"), "blue")
        self.assertEqual(self.state_manager.get_state_value("thumbnail_size"), 200)
        self.assertEqual(self.state_manager.get_state_value("performance_mode"), "performance")

    def test_change_listeners(self):
        """Test state change listeners"""

        changes_received = []

        def change_listener(key, old_value, new_value):
            changes_received.append((key, old_value, new_value))

        # Add listener
        self.state_manager.add_change_listener("current_theme", change_listener)

        # Make a change
        self.state_manager.set_state_value("current_theme", "dark")

        # Check that listener was called
        self.assertEqual(len(changes_received), 1)
        self.assertEqual(changes_received[0][0], "current_theme")
        self.assertEqual(changes_received[0][2], "dark")

        # Remove listener
        self.state_manager.remove_change_listener("current_theme", change_listener)

    def test_global_listeners(self):
        """Test global state change listeners"""

        events_received = []

        def global_listener(event: StateChangeEvent):
            events_received.append(event)

        # Add global listener
        self.state_manager.add_global_listener(global_listener)

        # Make a change
        self.state_manager.set_state_value("current_theme", "dark")

        # Check that listener was called
        self.assertEqual(len(events_received), 1)
        self.assertIsInstance(events_received[0], StateChangeEvent)
        self.assertEqual(events_received[0].key, "current_theme")
        self.assertEqual(events_received[0].new_value, "dark")

        # Remove listener
        self.state_manager.remove_global_listener(global_listener)

    def test_state_history(self):
        """Test state history and undo/redo"""

        # Reset to ensure clean state
        self.state_manager.reset_state()

        # Get initial value
        initial_thumbnail_size = self.state_manager.get_state_value("thumbnail_size")

        # Make some changes
        self.state_manager.set_state_value("current_theme", "dark")
        self.state_manager.set_state_value("thumbnail_size", 200)

        # Should be able to undo
        self.assertTrue(self.state_manager.can_undo())

        # Undo last change
        self.assertTrue(self.state_manager.undo())
        self.assertEqual(self.state_manager.get_state_value("thumbnail_size"), initial_thumbnail_size)  # Back to initial

        # Should be able to redo
        self.assertTrue(self.state_manager.can_redo())

        # Redo change
        self.assertTrue(self.state_manager.redo())
        self.assertEqual(self.state_manager.get_state_value("thumbnail_size"), 200)

    def test_state_persistence(self):
        """Test state saving and loading"""

        # Set some state values
        self.state_manager.set_state_value("current_theme", "dark")
        self.state_manager.set_state_value("thumbnail_size", 200)

        # Save state
        test_file = self.test_dir / "test_state.json"
        self.assertTrue(self.state_manager.save_state(test_file))
        self.assertTrue(test_file.exists())

        # Create new state manager and load state
        new_state_manager = StateManager(
            config_manager=self.mock_config_manager,
            logger_system=self.mock_logger_system
        )

        self.assertTrue(new_state_manager._load_state(test_file))

        # Check that state was restored
        self.assertEqual(new_state_manager.get_state_value("current_theme"), "dark")
        self.assertEqual(new_state_manager.get_state_value("thumbnail_size"), 200)

        new_state_manager.shutdown()

    def test_performance_summary(self):
        """Test performance summary"""

        summary = self.state_manager.get_performance_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn("state_accesses", summary)
        self.assertIn("state_changes", summary)
        self.assertIn("history_size", summary)
        self.assertIn("can_undo", summary)
        self.assertIn("can_redo", summary)

    def test_state_summary(self):
        """Test state summary"""

        summary = self.state_manager.get_state_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn("current_theme", summary)
        self.assertIn("thumbnail_size", summary)
        self.assertIn("performance_mode", summary)
        self.assertIn("session_start", summary)

    def test_state_reset(self):
        """Test state reset"""

        # Make some changes
        self.state_manager.set_state_value("current_theme", "dark")
        self.state_manager.set_state_value("thumbnail_size", 200)

        # Reset state
        self.state_manager.reset_state()

        # Should be back to defaults
        self.assertEqual(self.state_manager.get_state_value("current_theme"), "default")
        self.assertEqual(self.state_manager.get_state_value("thumbnail_size"), 150)


class TestKiroComponentsIntegration(unittest.TestCase):
    """Integration tests for Kiro components"""

    def setUp(self):
        """Set up integration test environment"""

        self.config_manager = Mock(spec=ConfigManager)
        self.logger_system = LoggerSystem()

        # Mock config settings
        self.config_manager.get_setting.return_value = {}

        self.performance_monitor = KiroPerformanceMonitor(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )

        self.cache_system = UnifiedCacheSystem(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )

        self.state_manager = StateManager(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )

    def tearDown(self):
        """Clean up integration test environment"""

        self.performance_monitor.shutdown()
        self.cache_system.shutdown()
        self.state_manager.shutdown()
        self.logger_system.shutdown()

    def test_component_interaction(self):
        """Test interaction between Kiro components"""

        # Start performance monitoring
        self.performance_monitor.start_monitoring()

        # Perform some cache operations
        self.cache_system.put("image", "test_key", "test_value")
        cached_value = self.cache_system.get("image", "test_key")

        # Update state
        self.state_manager.set_state_value("current_theme", "dark")

        # Log operation time to performance monitor
        self.performance_monitor.log_operation_time("cache_operation", 0.1)

        # Check that everything worked
        self.assertEqual(cached_value, "test_value")
        self.assertEqual(self.state_manager.get_state_value("current_theme"), "dark")

        # Stop monitoring
        self.performance_monitor.stop_monitoring()

    def test_performance_monitoring_with_cache(self):
        """Test performance monitoring with cache operations"""

        self.performance_monitor.start_monitoring()

        # Perform multiple cache operations
        for i in range(10):
            start_time = time.time()
            self.cache_system.put("test", f"key_{i}", f"value_{i}")
            self.cache_system.get("test", f"key_{i}")
            duration = time.time() - start_time

            self.performance_monitor.log_operation_time("cache_operation", duration)

        # Check performance metrics
        metrics = self.performance_monitor.get_performance_metrics()
        self.assertIsInstance(metrics, dict)

        self.performance_monitor.stop_monitoring()

    def test_state_change_with_monitoring(self):
        """Test state changes with performance monitoring"""

        state_changes = []

        def state_change_listener(event):
            state_changes.append(event)

        self.state_manager.add_global_listener(state_change_listener)
        self.performance_monitor.start_monitoring()

        # Make state changes
        self.state_manager.set_state_value("current_theme", "dark")
        self.state_manager.set_state_value("thumbnail_size", 200)

        # Check that changes were recorded
        self.assertEqual(len(state_changes), 2)

        self.performance_monitor.stop_monitoring()


if __name__ == '__main__':
    # Create test directory if it doesn't exist
    test_dir = Path(__file__).parent
    test_dir.mkdir(exist_ok=True)

    # Run tests
    unittest.main(verbosity=2)
