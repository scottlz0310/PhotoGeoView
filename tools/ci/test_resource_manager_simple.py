#!/usr/bin/env python3
"""
Simple test for ResourceManager to verify basic functionality
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resource_manager import ResourceManager, get_resource_manager


def test_basic_functionality():
    """Test basic resource manager functionality."""
    print("Testing ResourceManager basic functionality...")

    # Initialize resource manager
    config = {
        "monitoring_enabled": False,  # Disable monitoring for testing
        "max_memory_percent": 80.0,
        "max_disk_percent": 90.0,
    }
    manager = ResourceManager(config)
    print("✓ ResourceManager initialized successfully")

    # Test resource usage collection
    usage = manager.get_resource_usage()
    assert usage.memory_percent >= 0
    assert usage.disk_percent >= 0
    print("✓ Resource usage collection works")

    # Test temporary resource registration
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(b"test data")

    resource_id = manager.register_temp_resource(temp_path, "file")
    assert resource_id in manager.temp_resources
    assert manager.temp_resources[resource_id].path == temp_path
    print("✓ Temporary resource registration works")

    # Test resource cleanup
    success = manager.cleanup_resource(resource_id)
    assert success
    assert resource_id not in manager.temp_resources
    assert not os.path.exists(temp_path)
    print("✓ Resource cleanup works")

    # Test temp directory context manager
    with manager.temp_directory(prefix="test_") as temp_dir:
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
        temp_dir_path = temp_dir

    # Directory should be cleaned up after context
    assert not os.path.exists(temp_dir_path)
    print("✓ Temp directory context manager works")

    # Test temp file context manager
    with manager.temp_file(prefix="test_", suffix=".txt") as temp_file:
        temp_file.write("test content")
        temp_file_path = temp_file.name
        assert os.path.exists(temp_file_path)

    # File should be cleaned up after context
    assert not os.path.exists(temp_file_path)
    print("✓ Temp file context manager works")

    # Test resource statistics
    stats = manager.get_resource_statistics()
    assert "current_usage" in stats
    assert "tracked_resources" in stats
    assert "limits" in stats
    print("✓ Resource statistics work")

    # Test resource report generation
    report = manager.generate_resource_report()
    assert "Resource Usage Report" in report
    assert "Current Resource Usage" in report
    print("✓ Resource report generation works")

    # Test global resource manager
    global_manager = get_resource_manager()
    assert global_manager is not None
    print("✓ Global resource manager works")

    print("\nAll tests passed! ✅")


def test_cleanup_functionality():
    """Test cleanup functionality."""
    print("\nTesting cleanup functionality...")

    manager = ResourceManager({"monitoring_enabled": False})

    # Create some temporary files
    temp_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(f"test data {i}".encode())
            temp_files.append(f.name)
            manager.register_temp_resource(f.name, "file")

    print(f"✓ Created {len(temp_files)} temporary files")

    # Verify files exist
    for temp_file in temp_files:
        assert os.path.exists(temp_file)

    # Test cleanup_all
    manager.cleanup_all()

    # Verify files are cleaned up
    for temp_file in temp_files:
        assert not os.path.exists(temp_file)

    assert len(manager.temp_resources) == 0
    print("✓ cleanup_all() works correctly")


if __name__ == "__main__":
    test_basic_functionality()
    test_cleanup_functionality()
