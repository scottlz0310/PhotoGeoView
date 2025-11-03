#!/usr/bin/env python3
"""
Kiro Integration Components Demo

Demonstrates the Kiro integration layer components:
- PerformanceMonitor for system monitoring
- UnifiedCacheSystem for intelligent caching
- StateManager for centralized state management

Author: Kiro AI Integration System
"""

import sys
import time
from pathlib import Path

# Add src to path - adjusted for examples folder
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.config_manager import ConfigManager
from integration.logging_system import LoggerSystem
from integration.performance_monitor import KiroPerformanceMonitor
from integration.state_manager import StateManager
from integration.unified_cache import UnifiedCacheSystem


def main():
    """Main demo function"""

    print("=== Kiro Integration Components Demo ===\n")

    # Initialize core systems
    print("1. Initializing core systems...")
    config_manager = ConfigManager()
    logger_system = LoggerSystem()

    print("   ✓ ConfigManager initialized")
    print("   ✓ LoggerSystem initialized")

    # Initialize Kiro components
    print("\n2. Initializing Kiro components...")

    performance_monitor = KiroPerformanceMonitor(
        config_manager=config_manager, logger_system=logger_system
    )
    print("   ✓ PerformanceMonitor initialized")

    cache_system = UnifiedCacheSystem(
        config_manager=config_manager, logger_system=logger_system
    )
    print("   ✓ UnifiedCacheSystem initialized")

    state_manager = StateManager(
        config_manager=config_manager, logger_system=logger_system
    )
    print("   ✓ StateManager initialized")

    # Test PerformanceMonitor
    print("\n3. Testing PerformanceMonitor...")

    # Start monitoring
    performance_monitor.start_monitoring()
    print("   ✓ Performance monitoring started")

    # Get system info
    memory_stats = performance_monitor.get_memory_usage()
    print(f"   ✓ Memory usage: {memory_stats.get('process_rss_mb', 0):.1f} MB")

    # Log some operations
    performance_monitor.log_operation_time("demo_operation", 0.1)
    performance_monitor.log_operation_time("image_load", 0.5)
    performance_monitor.log_operation_time("ui_update", 0.05)
    print("   ✓ Operation times logged")

    # Get AI component status
    component_status = performance_monitor.get_ai_component_status()
    print(f"   ✓ AI component status: {component_status}")

    # Get performance summary
    perf_summary = performance_monitor.get_performance_summary()
    print(f"   ✓ Performance summary: {perf_summary.get('status', 'unknown')}")

    # Test UnifiedCacheSystem
    print("\n4. Testing UnifiedCacheSystem...")

    # Test basic cache operations
    cache_system.put("image", "test_image_1", b"fake image data 1")
    cache_system.put("thumbnail", "test_thumb_1", b"fake thumbnail data 1")
    cache_system.put("metadata", "test_meta_1", {"camera": "Canon", "iso": 400})
    print("   ✓ Data cached in different cache types")

    # Test cache retrieval
    cached_image = cache_system.get("image", "test_image_1")
    cached_thumb = cache_system.get("thumbnail", "test_thumb_1")
    cached_meta = cache_system.get("metadata", "test_meta_1")

    print(
        f"   ✓ Cache hits: Image={cached_image is not None}, Thumb={cached_thumb is not None}, Meta={cached_meta is not None}"
    )

    # Test specialized cache methods
    test_path = Path("demo_image.jpg")
    cache_system.cache_image(test_path, b"demo image data")
    cache_system.cache_thumbnail(test_path, (150, 150), b"demo thumbnail")
    cache_system.cache_metadata(test_path, {"demo": "metadata"})
    cache_system.cache_map((40.7128, -74.0060), 10, {"demo": "map"})
    print("   ✓ Specialized cache methods tested")

    # Get cache statistics
    cache_stats = cache_system.get_cache_stats()
    print("   ✓ Cache statistics:")
    for cache_type, stats in cache_stats.items():
        print(
            f"     - {cache_type}: {stats['entry_count']} entries, {stats['hit_rate']:.1%} hit rate"
        )

    # Get cache summary
    cache_summary = cache_system.get_cache_summary()
    print(f"   ✓ Total cache memory: {cache_summary.get('total_memory_mb', 0):.2f} MB")

    # Test StateManager
    print("\n5. Testing StateManager...")

    # Test basic state operations
    state_manager.set_state_value("current_theme", "dark")
    state_manager.set_state_value("thumbnail_size", 200)
    state_manager.set_state_value("performance_mode", "performance")
    print("   ✓ State values set")

    # Test state retrieval
    theme = state_manager.get_state_value("current_theme")
    thumb_size = state_manager.get_state_value("thumbnail_size")
    perf_mode = state_manager.get_state_value("performance_mode")
    print(f"   ✓ State values: theme={theme}, size={thumb_size}, mode={perf_mode}")

    # Test bulk update
    state_manager.update_state(
        current_theme="blue", thumbnail_size=250, image_sort_mode="date"
    )
    print("   ✓ Bulk state update completed")

    # Test state validation
    valid_size = state_manager.set_state_value("thumbnail_size", 300)
    invalid_size = state_manager.set_state_value("thumbnail_size", 1000)
    print(f"   ✓ State validation: valid={valid_size}, invalid={invalid_size}")

    # Test undo/redo
    can_undo = state_manager.can_undo()
    if can_undo:
        state_manager.undo()
        print("   ✓ State undo performed")

        can_redo = state_manager.can_redo()
        if can_redo:
            state_manager.redo()
            print("   ✓ State redo performed")

    # Get state summary
    state_summary = state_manager.get_state_summary()
    print(
        f"   ✓ State summary: {state_summary.get('current_theme')} theme, {state_summary.get('images_processed', 0)} images processed"
    )

    # Test component integration
    print("\n6. Testing component integration...")

    # Add state change listener
    state_changes = []

    def state_change_listener(event):
        state_changes.append(event.key)

    state_manager.add_global_listener(state_change_listener)

    # Make state changes while monitoring performance
    start_time = time.time()

    for i in range(5):
        # Cache some data
        cache_system.put("test", f"key_{i}", f"value_{i}")

        # Update state
        state_manager.set_state_value("images_processed", i + 1)

        # Log operation time
        operation_time = time.time() - start_time
        performance_monitor.log_operation_time(f"integration_test_{i}", operation_time)

        time.sleep(0.1)  # Small delay

    print(
        f"   ✓ Integration test completed: {len(state_changes)} state changes recorded"
    )

    # Test performance monitoring with cache operations
    print("\n7. Testing performance monitoring with cache operations...")

    cache_operations = 0
    for i in range(10):
        start_time = time.time()

        # Perform cache operations
        cache_system.put("perf_test", f"key_{i}", f"data_{i}" * 100)
        retrieved = cache_system.get("perf_test", f"key_{i}")

        operation_time = time.time() - start_time
        performance_monitor.log_operation_time("cache_perf_test", operation_time)

        if retrieved:
            cache_operations += 1

    print(
        f"   ✓ Performance test completed: {cache_operations} successful cache operations"
    )

    # Show final statistics
    print("\n8. Final Statistics:")

    # Performance statistics
    final_perf_summary = performance_monitor.get_performance_summary()
    print(f"   Performance: {final_perf_summary.get('status', 'unknown')}")

    # Cache statistics
    final_cache_summary = cache_system.get_cache_summary()
    print(
        f"   Cache: {final_cache_summary.get('total_entries', 0)} entries, {final_cache_summary.get('overall_hit_rate', 0):.1%} hit rate"
    )

    # State statistics
    final_state_summary = state_manager.get_performance_summary()
    print(
        f"   State: {final_state_summary.get('state_changes', 0)} changes, {final_state_summary.get('state_accesses', 0)} accesses"
    )

    # Cleanup
    print("\n9. Shutting down...")

    performance_monitor.stop_monitoring()
    print("   ✓ Performance monitoring stopped")

    cache_system.clear()
    print("   ✓ Cache cleared")

    state_manager.save_state()
    print("   ✓ State saved")

    # Shutdown components
    performance_monitor.shutdown()
    cache_system.shutdown()
    state_manager.shutdown()
    logger_system.shutdown()

    print("   ✓ All components shutdown")
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback

        traceback.print_exc()
