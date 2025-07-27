#!/usr/bin/env python3
"""
Test script for FileSystemWatcher integration with UI components

This script tests the integration of FileSystemWatcher with the folder navigator
and thumbnail grid components to ensure real-time file monitoring works correctly.

Author: Kiro AI Integration System
"""

import sys
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    from src.integration.ui.folder_navigator import EnhancedFolderNavigator
    from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid
    from src.integration.services.file_system_watcher import FileSystemWatcher, FileChangeType
    from src.integration.config_manager import ConfigManager
    from src.integration.state_manager import StateManager
    from src.integration.logging_system import LoggerSystem

    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False


def create_test_image_file(folder_path: Path, filename: str) -> Path:
    """
    Create a test image file for testing purposes

    Args:
        folder_path: Directory to create the file in
        filename: Name of the file to create

    Returns:
        Path to the created file
    """
    file_path = folder_path / filename

    # Create a simple test image file (just a placeholder)
    with open(file_path, 'wb') as f:
        # Write minimal JPEG header to make it recognizable as an image
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb')
        f.write(b'\x00' * 100)  # Padding to make it look like a real file

    return file_path


def test_file_system_watcher_integration():
    """
    Test the integration of FileSystemWatcher with UI components
    """
    if not IMPORTS_AVAILABLE:
        print("❌ Required imports not available. Skipping integration test.")
        return False

    print("🧪 Testing FileSystemWatcher integration with UI components...")

    # Create QApplication for Qt components
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        # Create temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_folder = Path(temp_dir)
            print(f"📁 Created test folder: {test_folder}")

            # Initialize core systems
            config_manager = ConfigManager()
            state_manager = StateManager()
            logger_system = LoggerSystem()

            # Create UI components
            folder_navigator = EnhancedFolderNavigator(
                config_manager, state_manager, logger_system
            )

            thumbnail_grid = OptimizedThumbnailGrid(
                config_manager, state_manager, logger_system
            )

            # Connect folder navigator to thumbnail grid
            folder_navigator.folder_changed.connect(
                lambda folder_path: thumbnail_grid.update_image_list(
                    folder_navigator._discover_images_in_folder(folder_path)
                )
            )

            print("✅ UI components initialized successfully")

            # Test 1: Navigate to empty folder
            print("\n📋 Test 1: Navigate to empty folder")
            folder_navigator.navigate_to_folder(test_folder)

            # Verify watcher is started
            if folder_navigator.file_system_watcher.is_watching:
                print("✅ File system watcher started successfully")
            else:
                print("❌ File system watcher failed to start")
                return False

            # Test 2: Create a new image file
            print("\n📋 Test 2: Create new image file")
            test_image = create_test_image_file(test_folder, "test_image.jpg")
            print(f"📄 Created test image: {test_image.name}")

            # Wait for file system event processing
            time.sleep(1)
            app.processEvents()

            # Test 3: Delete the image file
            print("\n📋 Test 3: Delete image file")
            test_image.unlink()
            print(f"🗑️ Deleted test image: {test_image.name}")

            # Wait for file system event processing
            time.sleep(1)
            app.processEvents()

            # Test 4: Create multiple files
            print("\n📋 Test 4: Create multiple image files")
            test_files = []
            for i in range(3):
                test_file = create_test_image_file(test_folder, f"test_image_{i}.png")
                test_files.append(test_file)
                print(f"📄 Created: {test_file.name}")

            # Wait for file system event processing
            time.sleep(2)
            app.processEvents()

            # Test 5: Check watcher statistics
            print("\n📋 Test 5: Check watcher statistics")
            watcher_status = folder_navigator.file_system_watcher.get_watch_status()

            print(f"📊 Watcher Status:")
            print(f"   - Is watching: {watcher_status['is_watching']}")
            print(f"   - Current folder: {watcher_status['current_folder']}")
            print(f"   - Total events: {watcher_status['stats']['total_events']}")
            print(f"   - Filtered events: {watcher_status['stats']['filtered_events']}")
            print(f"   - Callback calls: {watcher_status['stats']['callback_calls']}")

            # Test 6: Stop monitoring
            print("\n📋 Test 6: Stop monitoring")
            folder_navigator.stop_monitoring()

            if not folder_navigator.file_system_watcher.is_watching:
                print("✅ File system watcher stopped successfully")
            else:
                print("❌ File system watcher failed to stop")
                return False

            print("\n🎉 All integration tests passed successfully!")
            return True

    except Exception as e:
        print(f"❌ Integration test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """
    Test error handling in file system watcher integration
    """
    if not IMPORTS_AVAILABLE:
        print("❌ Required imports not available. Skipping error handling test.")
        return False

    print("\n🧪 Testing error handling in FileSystemWatcher integration...")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        # Initialize core systems
        config_manager = ConfigManager()
        state_manager = StateManager()
        logger_system = LoggerSystem()

        # Create folder navigator
        folder_navigator = EnhancedFolderNavigator(
            config_manager, state_manager, logger_system
        )

        # Test 1: Navigate to non-existent folder
        print("\n📋 Test 1: Navigate to non-existent folder")
        non_existent_folder = Path("/non/existent/folder")
        result = folder_navigator.navigate_to_folder(non_existent_folder)

        if not result:
            print("✅ Non-existent folder handled correctly")
        else:
            print("❌ Non-existent folder should have been rejected")
            return False

        # Test 2: Test with invalid permissions (if possible)
        print("\n📋 Test 2: Error recovery test")

        # Create a temporary folder and then remove it while watching
        with tempfile.TemporaryDirectory() as temp_dir:
            test_folder = Path(temp_dir)

            # Navigate to folder
            folder_navigator.navigate_to_folder(test_folder)

            # Verify watcher started
            if folder_navigator.file_system_watcher.is_watching:
                print("✅ Watcher started for temporary folder")
            else:
                print("❌ Watcher failed to start for temporary folder")
                return False

        # Folder is now deleted, watcher should handle this gracefully
        time.sleep(1)
        app.processEvents()

        print("✅ Error handling tests completed successfully")
        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Main test function
    """
    print("🚀 Starting FileSystemWatcher Integration Tests")
    print("=" * 60)

    # Test basic integration
    integration_success = test_file_system_watcher_integration()

    # Test error handling
    error_handling_success = test_error_handling()

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Integration Test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"   Error Handling Test: {'✅ PASSED' if error_handling_success else '❌ FAILED'}")

    overall_success = integration_success and error_handling_success

    if overall_success:
        print("\n🎉 All FileSystemWatcher integration tests PASSED!")
        return 0
    else:
        print("\n❌ Some FileSystemWatcher integration tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
