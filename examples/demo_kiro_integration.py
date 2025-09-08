#!/usr/bin/env python3
"""
Kiro Integration Layer Demo

Demonstrates the Kiro integration layer components:
- PerformanceMonitor for real-time system monitoring
- UnifiedCacheSystem for intelligent caching
- StateManager for centralized state management

Author: Kiro AI Integration System
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path - adjusted for examples folder
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.config_manager import ConfigManager
from integration.logging_system import LoggerSystem
from integration.models import AIComponent
from integration.performance_monitor import KiroPerformanceMonitor
from integration.state_manager import StateManager
from integration.unified_cache import UnifiedCacheSystem


async def main():
    """Main demo function"""

    print("=== Kiro Integration Layer Demo ===\n")

    # Initialize components
    print("1. Initializing Kiro Integration Components...")
    config_manager = ConfigManager()
    logger_system = LoggerSystem()

    # Initialize performance monitor
    performance_monitor = KiroPerformanceMonitor(
        config_manager=config_manager, logger_system=logger_system
    )

    # Initialize cache system
    cache_system = UnifiedCacheSystem(
        config_manager=config_manager, logger_system=logger_system
    )

    # Initialize state manager
    state_manager = StateManager(
        config_manager=config_manager, logger_system=logger_system
    )

    print("   ✓ PerformanceMonitor initialized")
    print("   ✓ UnifiedCacheSystem initialized")
    print("   ✓ StateManager initialized")

    # Start performance monitoring
    print("\n2. Starting Performance Monitoring...")
    performance_monitor.start_monitoring()
    print("   ✓ Performance monitoring started")

    # Demonstrate cache system
    print("\n3. Testing Unified Cache System...")

    # Test different cache types
    cache_types = ["images", "thumbnails", "metadata", "maps", "themes"]

    for cache_type in cache_types:
        # Put some test data
        test_key = f"test_{cache_type}_key"
        test_value = f"test_{cache_type}_data_" + "x" * 100  # Some data

        success = cache_system.put(
            cache_type, test_key, test_value, component=AIComponent.KIRO
        )
        print(f"   ✓ Cached data in {cache_type}: {success}")

        # Get the data back
        retrieved = cache_system.get(cache_type, test_key, component=AIComponent.KIRO)
        print(f"   ✓ Retrieved from {cache_type}: {retrieved is not None}")

    # Show cache statistics
    cache_stats = cache_system.get_stats()
    print(f"\n   Cache Statistics:")
    print(f"   - Total entries: {cache_stats['overall']['total_entries']}")
    print(f"   - Total size: {cache_stats['overall']['total_size_mb']:.2f} MB")
    print(f"   - Hit rate: {cache_stats['overall']['hit_rate']:.1%}")

    # Demonstrate state management
    print("\n4. Testing State Management...")

    # Set some state values
    state_changes = {
        "current_theme": "demo_theme",
        "thumbnail_size": 200,
        "performance_mode": "performance",
        "map_zoom": 15,
    }

    for key, value in state_changes.items():
        success = state_manager.set_state_value(key, value, component=AIComponent.KIRO)
        print(f"   ✓ Set {key} = {value}: {success}")

    # Get state values back
    for key in state_changes.keys():
        value = state_manager.get_state_value(key)
        print(f"   ✓ Retrieved {key} = {value}")

    # Show state summary
    state_summary = state_manager.get_state_summary()
    print(f"\n   State Summary:")
    print(f"   - Session duration: {state_summary['session_duration']:.1f}s")
    print(f"   - Current theme: {state_summary['current_theme']}")
    print(f"   - Performance mode: {state_summary['performance_mode']}")

    # Demonstrate performance monitoring
    print("\n5. Testing Performance Monitoring...")

    # Simulate some operations with timing
    operations = [
        ("image_load", 0.5),
        ("thumbnail_generation", 0.2),
        ("exif_extraction", 0.1),
        ("map_rendering", 0.8),
        ("theme_change", 0.05),
    ]

    for operation, duration in operations:
        # Simulate operation
        await asyncio.sleep(duration)

        # Log the operation time
        performance_monitor.log_operation_time(operation, duration)
        print(f"   ✓ Logged {operation}: {duration}s")

    # Get performance metrics
    perf_metrics = performance_monitor.get_performance_metrics()
    print(f"\n   Performance Metrics:")
    print(f"   - Memory usage: {perf_metrics['memory']['process_rss_mb']:.1f} MB")
    print(f"   - CPU usage: {perf_metrics['cpu']['process_percent']:.1f}%")

    ai_status = perf_metrics["ai_components"]
    for component, status in ai_status.items():
        print(f"   - {component} status: {status}")

    # Test state change listeners
    print("\n6. Testing State Change Notifications...")

    changes_received = []

    def state_change_listener(key, old_value, new_value):
        changes_received.append((key, old_value, new_value))
        print(
            f"   ✓ State change detected: {key} changed from {old_value} to {new_value}"
        )

    # Add listener
    state_manager.add_change_listener("current_theme", state_change_listener)

    # Change the theme
    state_manager.set_state_value("current_theme", "notification_test")

    # Remove listener
    state_manager.remove_change_listener("current_theme", state_change_listener)

    print(f"   ✓ Received {len(changes_received)} change notifications")

    # Test memory pressure simulation
    print("\n7. Testing Memory Pressure Handling...")

    pressure_callbacks_called = 0

    def memory_pressure_callback():
        nonlocal pressure_callbacks_called
        pressure_callbacks_called += 1
        print("   ✓ Memory pressure callback triggered")

    # Add memory pressure callback
    cache_system.add_memory_pressure_callback(memory_pressure_callback)

    # Fill cache with large data to potentially trigger memory pressure
    large_data = "x" * 1024 * 100  # 100KB per item
    for i in range(50):
        cache_system.put("general", f"large_item_{i}", large_data)

    print(f"   ✓ Added 50 large cache items")
    print(f"   ✓ Memory pressure callbacks called: {pressure_callbacks_called}")

    # Remove callback
    cache_system.remove_memory_pressure_callback(memory_pressure_callback)

    # Test performance recommendations
    print("\n8. Getting Performance Recommendations...")

    recommendations = performance_monitor.get_optimization_recommendations()
    if recommendations:
        for i, recommendation in enumerate(recommendations, 1):
            print(f"   {i}. {recommendation}")
    else:
        print("   ✓ No performance issues detected - system running optimally")

    # Test cache clearing
    print("\n9. Testing Cache Management...")

    # Show cache stats before clearing
    stats_before = cache_system.get_stats()
    print(f"   Cache entries before clear: {stats_before['overall']['total_entries']}")

    # Clear specific cache type
    cache_system.clear("general")

    # Show stats after clearing
    stats_after = cache_system.get_stats()
    print(
        f"   Cache entries after clearing 'general': {stats_after['overall']['total_entries']}"
    )

    # Test state persistence
    print("\n10. Testing State Persistence...")

    # Force save state
    state_manager.force_save()
    print("   ✓ State saved to disk")

    # Export state for backup
    export_path = Path("demo_state_export.json")
    success = state_manager.export_state(export_path)
    print(f"   ✓ State exported to {export_path}: {success}")

    # Clean up export file
    if export_path.exists():
        export_path.unlink()

    # Performance data export
    perf_export_path = Path("demo_performance_export.json")
    success = performance_monitor.export_performance_data(perf_export_path)
    print(f"   ✓ Performance data exported to {perf_export_path}: {success}")

    # Clean up performance export file
    if perf_export_path.exists():
        perf_export_path.unlink()

    # Final statistics
    print("\n11. Final System Statistics...")

    final_cache_stats = cache_system.get_stats()
    final_perf_metrics = performance_monitor.get_performance_metrics()
    final_state_summary = state_manager.get_state_summary()

    print(f"   Cache System:")
    print(f"   - Total cache hits: {final_cache_stats['overall']['total_hits']}")
    print(f"   - Total cache misses: {final_cache_stats['overall']['total_misses']}")
    print(f"   - Overall hit rate: {final_cache_stats['overall']['hit_rate']:.1%}")
    print(f"   - Memory usage: {final_cache_stats['overall']['total_size_mb']:.2f} MB")

    print(f"\n   Performance Monitor:")
    print(
        f"   - System memory: {final_perf_metrics['memory']['process_rss_mb']:.1f} MB"
    )
    print(f"   - CPU usage: {final_perf_metrics['cpu']['process_percent']:.1f}%")
    print(f"   - AI components monitored: {len(final_perf_metrics['ai_components'])}")

    print(f"\n   State Manager:")
    print(f"   - Session duration: {final_state_summary['session_duration']:.1f}s")
    print(
        f"   - State changes tracked: {len(final_state_summary['performance_operations'])}"
    )
    print(f"   - Current theme: {final_state_summary['current_theme']}")

    # Shutdown components
    print("\n12. Shutting down components...")

    performance_monitor.shutdown()
    print("   ✓ Performance monitor shutdown")

    cache_system.shutdown()
    print("   ✓ Cache system shutdown")

    state_manager.shutdown()
    print("   ✓ State manager shutdown")

    logger_system.shutdown()
    print("   ✓ Logger system shutdown")

    print("\n=== Demo Complete ===")
    print("\nKiro Integration Layer Components demonstrated:")
    print("✅ Real-time performance monitoring with alerting")
    print("✅ Multi-level intelligent caching system")
    print("✅ Centralized state management with persistence")
    print("✅ Cross-component integration and coordination")
    print("✅ Memory pressure handling and optimization")
    print("✅ Performance recommendations and data export")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback

        traceback.print_exc()
