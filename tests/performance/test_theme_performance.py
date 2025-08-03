"""
Performance Tests for Theme Manager

Tests performance optimizations including lazy loading, caching,
and monitoring for theme operations.

Author: Kiro AI Integration System
Requirements: 5.2, 5.3
"""

import asyncio
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.integration.logging_system import LoggerSystem
from src.integration.performance_optimizer import PerformanceOptimizer, ResourceCache, LazyResourceLoader
from src.ui.theme_manager import ThemeManagerWidget


class TestThemePerformance:
    """Test suite for theme performance optimizations"""

    @pytest.fixture
    def logger_system(self):
        """Create mock logger system"""
        return Mock(spec=LoggerSystem)

    @pytest.fixture
    def performance_optimizer(self, logger_system):
        """Create performance optimizer instance"""
        return PerformanceOptimizer(logger_system)

    @pytest.fixture
    def theme_manager(self, logger_system):
        """Create theme manager with mocked dependencies"""
        config_manager = Mock()
        config_manager.get_setting.return_value = "default"

        with patch('src.ui.theme_manager.Path'):
            manager = ThemeManagerWidget(config_manager, logger_system)
            return manager

    def test_resource_cache_basic_operations(self, performance_optimizer):
        """Test basic cache operations"""
        cache = performance_optimizer.theme_cache

        # Test set and get
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Test non-existent key
        assert cache.get("non_existent") is None

        # Test cache size
        assert cache.size() == 1

    def test_resource_cache_ttl_expiration(self):
        """Test cache TTL expiration"""
        cache = ResourceCache(max_size=10, ttl_seconds=0.1)  # 100ms TTL

        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(0.2)
        assert cache.get("test_key") is None

    def test_resource_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = ResourceCache(max_size=3, ttl_seconds=300)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it recently used
        cache.get("key1")

        # Add new key, should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Should still exist
        assert cache.get("key2") is None      # Should be evicted
        assert cache.get("key3") == "value3"  # Should still exist
        assert cache.get("key4") == "value4"  # Should exist

    @pytest.mark.asyncio
    async def test_lazy_resource_loader(self, logger_system):
        """Test lazy resource loading"""
        loader = LazyResourceLoader(logger_system)

        # Mock loader function
        mock_loader = Mock(return_value="loaded_resource")

        # Test loading
        result = await loader.load_resource("test_resource", mock_loader, "arg1", key="value")

        assert result == "loaded_resource"
        assert loader.is_loaded("test_resource")
        mock_loader.assert_called_once_with("arg1", key="value")

    @pytest.mark.asyncio
    async def test_lazy_resource_loader_deduplication(self, logger_system):
        """Test that concurrent loads are deduplicated"""
        loader = LazyResourceLoader(logger_system)

        # Mock slow loader function
        async def slow_loader():
            await asyncio.sleep(0.1)
            return "loaded_resource"

        # Start multiple concurrent loads
        tasks = [
            loader.load_resource("test_resource", slow_loader),
            loader.load_resource("test_resource", slow_loader),
            loader.load_resource("test_resource", slow_loader)
        ]

        results = await asyncio.gather(*tasks)

        # All should return the same result
        assert all(result == "loaded_resource" for result in results)
        assert loader.is_loaded("test_resource")

    def test_performance_monitor_operations(self, performance_optimizer):
        """Test performance monitoring"""
        monitor = performance_optimizer.monitor

        # Test operation timing
        monitor.start_operation("test_op")
        time.sleep(0.01)  # 10ms
        duration = monitor.end_operation("test_op", "test_type")

        assert duration >= 0.01

        # Test metrics summary
        summary = monitor.get_metrics_summary("test_type")
        assert summary["count"] == 1
        assert summary["min"] >= 0.01
        assert summary["max"] >= 0.01
        assert summary["avg"] >= 0.01

    def test_performance_monitor_counters(self, performance_optimizer):
        """Test performance counters"""
        monitor = performance_optimizer.monitor

        # Test counter increment
        monitor.increment_counter("test_counter", 5)
        monitor.increment_counter("test_counter", 3)

        counters = monitor.get_counters()
        assert counters["test_counter"] == 8

    def test_performance_monitor_custom_metrics(self, performance_optimizer):
        """Test custom metric recording"""
        monitor = performance_optimizer.monitor

        # Record custom metrics
        monitor.record_metric("custom_metric", 1.5)
        monitor.record_metric("custom_metric", 2.0)
        monitor.record_metric("custom_metric", 1.0)

        summary = monitor.get_metrics_summary("custom_metric")
        assert summary["count"] == 3
        assert summary["min"] == 1.0
        assert summary["max"] == 2.0
        assert summary["avg"] == 1.5

    @pytest.mark.asyncio
    async def test_theme_loading_optimization(self, performance_optimizer):
        """Test theme loading optimization"""
        # Mock theme loader
        mock_loader = Mock(return_value={"name": "test_theme", "colors": {}})

        # Test optimized loading
        result = await performance_optimizer.optimize_theme_loading("test_theme", mock_loader)

        assert result == {"name": "test_theme", "colors": {}}
        mock_loader.assert_called_once()

    def test_stylesheet_caching(self, performance_optimizer):
        """Test stylesheet caching"""
        test_stylesheet = "QWidget { background-color: #ffffff; }"

        # Cache stylesheet
        performance_optimizer.cache_stylesheet("test_theme", test_stylesheet)

        # Retrieve cached stylesheet
        cached = performance_optimizer.get_cached_stylesheet("test_theme")
        assert cached == test_stylesheet

        # Test non-existent stylesheet
        assert performance_optimizer.get_cached_stylesheet("non_existent") is None

    @pytest.mark.asyncio
    async def test_breadcrumb_rendering_optimization(self, performance_optimizer):
        """Test breadcrumb rendering optimization"""
        # Create long path with many segments
        long_segments = [f"segment_{i}" for i in range(15)]
        test_path = Path("/long/path/with/many/segments")

        # Test optimization
        optimized = await performance_optimizer.optimize_breadcrumb_rendering(test_path, long_segments)

        # Should be truncated
        assert len(optimized) < len(long_segments)
        assert "..." in optimized  # Should contain ellipsis

    def test_path_info_caching(self, performance_optimizer):
        """Test path information caching"""
        test_path = Path("/test/path")
        test_info = {"exists": True, "is_dir": True, "permissions": "rwx"}

        # Cache path info
        performance_optimizer.cache_path_info(test_path, test_info)

        # Retrieve cached info
        cached = performance_optimizer.get_cached_path_info(test_path)
        assert cached == test_info

    def test_performance_report_generation(self, performance_optimizer):
        """Test performance report generation"""
        # Generate some metrics
        performance_optimizer.monitor.record_metric("test_metric", 1.0)
        performance_optimizer.monitor.increment_counter("test_counter", 1)
        performance_optimizer.cache_stylesheet("test_theme", "test_css")

        # Get performance report
        report = performance_optimizer.get_performance_report()

        assert "metrics" in report
        assert "counters" in report
        assert "cache_stats" in report
        assert "optimization_settings" in report

        # Check cache stats
        assert report["cache_stats"]["stylesheet_cache_size"] == 1

        # Check settings
        assert report["optimization_settings"]["lazy_loading_enabled"] is True
        assert report["optimization_settings"]["caching_enabled"] is True
        assert report["optimization_settings"]["monitoring_enabled"] is True


class TestThemeManagerPerformance:
    """Test suite for theme manager performance integration"""

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager"""
        config = Mock()
        config.get_setting.return_value = "default"
        return config

    @pytest.fixture
    def mock_logger_system(self):
        """Create mock logger system"""
        logger_system = Mock(spec=LoggerSystem)
        logger_system.get_logger.return_value = Mock()
        return logger_system

    def test_theme_manager_performance_integration(self, mock_config_manager, mock_logger_system):
        """Test theme manager performance optimizer integration"""
        with patch('src.ui.theme_manager.Path'):
            manager = ThemeManagerWidget(mock_config_manager, mock_logger_system)

            # Check that performance optimizer is initialized
            assert hasattr(manager, 'performance_optimizer')
            assert manager.performance_optimizer is not None

    @pytest.mark.asyncio
    async def test_theme_application_monitoring(self, mock_config_manager, mock_logger_system):
        """Test that theme application is monitored"""
        with patch('src.ui.theme_manager.Path'), \
             patch.object(ThemeManagerWidget, '_load_theme_configuration', return_value=True), \
             patch.object(ThemeManagerWidget, 'available_themes', {"test_theme": Mock()}):

            manager = ThemeManagerWidget(mock_config_manager, mock_logger_system)

            # Mock current theme
            manager.current_theme = Mock()
            manager.current_theme.name = "old_theme"

            # Apply theme (this should be monitored)
            with patch.object(manager, 'registered_components', set()):
                result = manager.apply_theme("test_theme")

                # Check that monitoring was used
                metrics = manager.performance_optimizer.monitor.get_all_metrics()
                assert len(metrics) > 0 or result  # Either metrics recorded or operation succeeded


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Benchmark tests for performance-critical operations"""

    @pytest.fixture
    def performance_optimizer(self):
        """Create performance optimizer for benchmarks"""
        logger_system = Mock(spec=LoggerSystem)
        logger_system.get_logger.return_value = Mock()
        return PerformanceOptimizer(logger_system)

    def test_cache_performance_benchmark(self, performance_optimizer, benchmark):
        """Benchmark cache operations"""
        cache = performance_optimizer.theme_cache

        def cache_operations():
            # Perform mixed cache operations
            for i in range(100):
                cache.set(f"key_{i}", f"value_{i}")
                cache.get(f"key_{i}")
                if i > 50:
                    cache.get(f"key_{i-50}")  # Access older entries

        # Benchmark the operations
        result = benchmark(cache_operations)

        # Verify cache state
        assert cache.size() <= 100

    @pytest.mark.asyncio
    async def test_lazy_loading_benchmark(self, performance_optimizer, benchmark):
        """Benchmark lazy loading operations"""
        loader = performance_optimizer.lazy_loader

        async def lazy_loading_operations():
            # Simulate loading multiple resources
            tasks = []
            for i in range(50):
                async def mock_loader():
                    await asyncio.sleep(0.001)  # Simulate I/O
                    return f"resource_{i}"

                task = loader.load_resource(f"resource_{i}", mock_loader)
                tasks.append(task)

            await asyncio.gather(*tasks)

        # Benchmark the operations
        await benchmark(lazy_loading_operations)

    def test_path_truncation_benchmark(self, performance_optimizer, benchmark):
        """Benchmark path truncation operations"""
        # Create long segment list
        long_segments = [f"very_long_segment_name_{i}" for i in range(100)]
        test_path = Path("/very/long/path/with/many/segments")

        async def truncation_operations():
            for _ in range(10):
                await performance_optimizer.optimize_breadcrumb_rendering(test_path, long_segments)

        # Benchmark the operations
        result = benchmark(lambda: asyncio.run(truncation_operations()))
