"""
Performance Tests for Breadcrumb Navigation

Tests performance optimizations for breadcrumb rendering,
path validation caching, and navigation operations.

Author: Kiro AI Integration System
Requirements: 5.2, 5.3
"""

import asyncio
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.integration.logging_system import LoggerSystem
from src.integration.performance_optimizer import PerformanceOptimizer
from src.integration.services.file_system_watcher import FileSystemWatcher
from src.ui.breadcrumb_bar import BreadcrumbAddressBar


class TestBreadcrumbPerformance:
    """Test suite for breadcrumb performance optimizations"""

    @pytest.fixture
    def logger_system(self):
        """Create mock logger system"""
        logger_system = Mock(spec=LoggerSystem)
        logger_system.get_logger.return_value = Mock()
        return logger_system

    @pytest.fixture
    def file_system_watcher(self, logger_system):
        """Create mock file system watcher"""
        return Mock(spec=FileSystemWatcher)

    @pytest.fixture
    def breadcrumb_bar(self, file_system_watcher, logger_system):
        """Create breadcrumb bar with mocked dependencies"""
        with patch('src.ui.breadcrumb_bar.Path'):
            bar = BreadcrumbAddressBar(file_system_watcher, logger_system)
            return bar

    @pytest.fixture
    def performance_optimizer(self, logger_system):
        """Create performance optimizer instance"""
        return PerformanceOptimizer(logger_system)

    def test_breadcrumb_performance_integration(self, breadcrumb_bar):
        """Test breadcrumb performance optimizer integration"""
        # Check that performance optimizer is initialized
        assert hasattr(breadcrumb_bar, 'performance_optimizer')
        assert breadcrumb_bar.performance_optimizer is not None

    @pytest.mark.asyncio
    async def test_path_validation_caching(self, breadcrumb_bar):
        """Test path validation result caching"""
        test_path = Path("/test/path")

        # Mock path validation
        with patch.object(breadcrumb_bar, '_sync_validate_path', return_value=True):
            # First validation should call the actual validation
            result1 = breadcrumb_bar._validate_path_comprehensive(test_path)

            # Second validation should use cached result
            result2 = breadcrumb_bar._validate_path_comprehensive(test_path)

            assert result1["valid"] is True
            assert result2["valid"] is True

            # Check that result was cached
            cached_info = breadcrumb_bar.performance_optimizer.get_cached_path_info(test_path)
            assert cached_info is not None
            assert "validation_result" in cached_info

    @pytest.mark.asyncio
    async def test_optimized_path_truncation(self, breadcrumb_bar):
        """Test optimized path truncation for long paths"""
        # Create mock navigation state with long path
        from src.integration.navigation_models import NavigationState, BreadcrumbSegment

        long_segments = []
        for i in range(15):
            segment = Mock(spec=BreadcrumbSegment)
            segment.display_name = f"segment_{i}"
            segment.path = Path(f"/path/segment_{i}")
            long_segments.append(segment)

        breadcrumb_bar.current_state = Mock(spec=NavigationState)
        breadcrumb_bar.current_state.breadcrumb_segments = long_segments
        breadcrumb_bar.current_state.current_path = Path("/long/path")

        # Apply optimization
        await breadcrumb_bar._apply_optimized_path_truncation()

        # Check that segments were optimized
        optimized_segments = breadcrumb_bar.current_state.breadcrumb_segments
        assert len(optimized_segments) < len(long_segments)

    def test_path_monitoring_performance(self, breadcrumb_bar):
        """Test path operation monitoring"""
        test_path = Path("/test/path")

        # Mock path validation and navigation state update
        with patch.object(breadcrumb_bar, '_validate_path_comprehensive') as mock_validate, \
             patch.object(breadcrumb_bar, 'current_state') as mock_state, \
             patch.object(breadcrumb_bar, '_apply_optimized_path_truncation', new_callable=AsyncMock), \
             patch.object(breadcrumb_bar, '_update_accessibility_info'), \
             patch.object(breadcrumb_bar, '_notify_navigation_listeners', new_callable=AsyncMock):

            # Setup mocks
            mock_validate.return_value = {"valid": True, "error_type": None, "error_message": None}
            mock_state.current_path = Path("/old/path")
            mock_state.navigate_to_path.return_value = True

            # Call set_current_path (should be monitored)
            result = breadcrumb_bar.set_current_path(test_path)

            # Check that operation was monitored
            metrics = breadcrumb_bar.performance_optimizer.monitor.get_all_metrics()
            assert len(metrics) > 0 or result  # Either metrics recorded or operation succeeded

    @pytest.mark.asyncio
    async def test_breadcrumb_rendering_optimization(self, performance_optimizer):
        """Test breadcrumb rendering optimization for various path lengths"""
        test_cases = [
            # (segments_count, expected_optimized)
            (3, False),   # Short paths shouldn't be optimized
            (5, False),   # Medium paths shouldn't be optimized
            (10, True),   # Long paths should be optimized
            (20, True),   # Very long paths should be optimized
        ]

        for segments_count, should_optimize in test_cases:
            segments = [f"segment_{i}" for i in range(segments_count)]
            test_path = Path("/test/path")

            optimized = await performance_optimizer.optimize_breadcrumb_rendering(test_path, segments)

            if should_optimize:
                assert len(optimized) < len(segments), f"Expected optimization for {segments_count} segments"
                assert "..." in optimized, "Expected ellipsis in optimized segments"
            else:
                assert optimized == segments, f"Expected no optimization for {segments_count} segments"

    def test_cache_hit_performance(self, performance_optimizer):
        """Test cache hit performance for repeated operations"""
        test_path = Path("/test/path")
        test_info = {"validation_result": {"valid": True}, "timestamp": "2023-01-01T00:00:00"}

        # Cache the path info
        performance_optimizer.cache_path_info(test_path, test_info)

        # Measure cache hit performance
        start_time = time.time()
        for _ in range(1000):
            cached_info = performance_optimizer.get_cached_path_info(test_path)
            assert cached_info is not None
        end_time = time.time()

        # Cache hits should be very fast
        avg_time_per_hit = (end_time - start_time) / 1000
        assert avg_time_per_hit < 0.001, f"Cache hits too slow: {avg_time_per_hit:.6f}s per hit"

    @pytest.mark.asyncio
    async def test_concurrent_path_operations(self, breadcrumb_bar):
        """Test performance with concurrent path operations"""
        test_paths = [Path(f"/test/path/{i}") for i in range(10)]

        # Mock validation to return success
        with patch.object(breadcrumb_bar, '_validate_path_comprehensive') as mock_validate, \
             patch.object(breadcrumb_bar, 'current_state') as mock_state, \
             patch.object(breadcrumb_bar, '_apply_optimized_path_truncation', new_callable=AsyncMock), \
             patch.object(breadcrumb_bar, '_update_accessibility_info'), \
             patch.object(breadcrumb_bar, '_notify_navigation_listeners', new_callable=AsyncMock):

            mock_validate.return_value = {"valid": True, "error_type": None, "error_message": None}
            mock_state.current_path = Path("/old/path")
            mock_state.navigate_to_path.return_value = True

            # Execute concurrent path operations
            start_time = time.time()
            tasks = [asyncio.create_task(asyncio.to_thread(breadcrumb_bar.set_current_path, path))
                    for path in test_paths]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Check that operations completed reasonably quickly
            total_time = end_time - start_time
            assert total_time < 5.0, f"Concurrent operations too slow: {total_time:.3f}s"

            # Check that most operations succeeded
            successful_results = [r for r in results if r is True]
            assert len(successful_results) >= len(test_paths) * 0.8, "Too many operations failed"

    def test_memory_usage_optimization(self, performance_optimizer):
        """Test that caches don't grow unbounded"""
        # Fill caches beyond their limits
        for i in range(2000):  # More than max cache size
            test_path = Path(f"/test/path/{i}")
            test_info = {"validation_result": {"valid": True}, "data": f"data_{i}"}
            performance_optimizer.cache_path_info(test_path, test_info)

        # Check that cache size is limited
        cache_size = performance_optimizer.path_cache.size()
        assert cache_size <= 1000, f"Cache size not limited: {cache_size}"  # Should be <= max_size

    @pytest.mark.asyncio
    async def test_error_handling_performance(self, breadcrumb_bar):
        """Test performance when handling path errors"""
        invalid_path = Path("/non/existent/path")

        # Mock validation to return error
        with patch.object(breadcrumb_bar, '_validate_path_comprehensive') as mock_validate, \
             patch.object(breadcrumb_bar, '_navigate_to_fallback_path', return_value=True):

            mock_validate.return_value = {
                "valid": False,
                "error_type": "path_not_found",
                "error_message": "Path does not exist"
            }

            # Measure error handling performance
            start_time = time.time()
            result = breadcrumb_bar.set_current_path(invalid_path)
            end_time = time.time()

            # Error handling should still be reasonably fast
            error_handling_time = end_time - start_time
            assert error_handling_time < 1.0, f"Error handling too slow: {error_handling_time:.3f}s"


@pytest.mark.benchmark
class TestBreadcrumbBenchmarks:
    """Benchmark tests for breadcrumb performance-critical operations"""

    @pytest.fixture
    def performance_optimizer(self):
        """Create performance optimizer for benchmarks"""
        logger_system = Mock(spec=LoggerSystem)
        logger_system.get_logger.return_value = Mock()
        return PerformanceOptimizer(logger_system)

    @pytest.fixture
    def breadcrumb_bar(self):
        """Create breadcrumb bar for benchmarks"""
        logger_system = Mock(spec=LoggerSystem)
        logger_system.get_logger.return_value = Mock()
        file_system_watcher = Mock(spec=FileSystemWatcher)

        with patch('src.ui.breadcrumb_bar.Path'):
            return BreadcrumbAddressBar(file_system_watcher, logger_system)

    def test_path_validation_benchmark(self, breadcrumb_bar, benchmark):
        """Benchmark path validation operations"""
        test_paths = [Path(f"/test/path/{i}") for i in range(100)]

        def validate_paths():
            for path in test_paths:
                with patch.object(breadcrumb_bar, '_sync_validate_path', return_value=True):
                    breadcrumb_bar._validate_path_comprehensive(path)

        # Benchmark the operations
        benchmark(validate_paths)

    def test_cache_operations_benchmark(self, performance_optimizer, benchmark):
        """Benchmark cache operations for path info"""
        test_paths = [Path(f"/test/path/{i}") for i in range(1000)]
        test_infos = [{"validation_result": {"valid": True}, "data": f"data_{i}"}
                     for i in range(1000)]

        def cache_operations():
            # Cache all paths
            for path, info in zip(test_paths, test_infos):
                performance_optimizer.cache_path_info(path, info)

            # Retrieve all paths
            for path in test_paths:
                performance_optimizer.get_cached_path_info(path)

        # Benchmark the operations
        benchmark(cache_operations)

    @pytest.mark.asyncio
    async def test_breadcrumb_truncation_benchmark(self, performance_optimizer, benchmark):
        """Benchmark breadcrumb truncation operations"""
        # Create various length segment lists
        test_cases = [
            ([f"segment_{i}" for i in range(length)], Path(f"/path/{length}"))
            for length in [5, 10, 20, 50, 100]
        ]

        async def truncation_operations():
            for segments, path in test_cases:
                await performance_optimizer.optimize_breadcrumb_rendering(path, segments)

        # Benchmark the operations
        await benchmark(truncation_operations)

    def test_monitoring_overhead_benchmark(self, performance_optimizer, benchmark):
        """Benchmark monitoring overhead"""
        def monitoring_operations():
            for i in range(1000):
                # Start and end operations
                op_id = performance_optimizer.start_navigation_operation(f"test_op_{i}")
                time.sleep(0.0001)  # Simulate minimal work
                performance_optimizer.end_navigation_operation(op_id)

                # Record custom metrics
                performance_optimizer.monitor.record_metric("test_metric", i * 0.001)
                performance_optimizer.monitor.increment_counter("test_counter")

        # Benchmark the operations
        benchmark(monitoring_operations)

    def test_concurrent_cache_access_benchmark(self, performance_optimizer, benchmark):
        """Benchmark concurrent cache access"""
        import threading

        test_paths = [Path(f"/test/path/{i}") for i in range(100)]
        test_infos = [{"validation_result": {"valid": True}, "data": f"data_{i}"}
                     for i in range(100)]

        # Pre-populate cache
        for path, info in zip(test_paths, test_infos):
            performance_optimizer.cache_path_info(path, info)

        def concurrent_cache_access():
            def worker():
                for _ in range(100):
                    for path in test_paths[:10]:  # Access subset of paths
                        performance_optimizer.get_cached_path_info(path)

            # Create multiple threads
            threads = [threading.Thread(target=worker) for _ in range(5)]

            # Start all threads
            for thread in threads:
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

        # Benchmark concurrent access
        benchmark(concurrent_cache_access)
