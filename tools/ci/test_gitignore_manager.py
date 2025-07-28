#!/usr/bin/env python3
"""
Test script for GitignoreManager functionality.

This script tests the .gitignore management, backup, and pattern detection functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
from gitignore_manager import GitignoreManager


def test_basic_functionality():
    """Test basic GitignoreManager functionality."""
    print("Testing basic GitignoreManager functionality...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Create initial .gitignore content
        initial_content = [
            "# Python",
            "__pycache__/",
            "*.pyc",
            "",
            "# IDE",
            ".vscode/",
            "*.swp"
        ]

        with open(gitignore_path, 'w') as f:
            f.write('\n'.join(initial_content))

        # Test GitignoreManager
        manager = GitignoreManager(str(gitignore_path))

        # Test pattern detection
        existing_patterns = manager.detect_existing_patterns()
        assert "__pycache__/" in existing_patterns
        assert "*.pyc" in existing_patterns
        assert ".vscode/" in existing_patterns

        # Test CI patterns detection (should be False initially)
        assert not manager.has_ci_simulation_patterns()

        print("✓ Basic functionality test passed")


def test_backup_functionality():
    """Test backup creation and restoration."""
    print("Testing backup functionality...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Create initial content
        original_content = "# Original content\n__pycache__/\n*.pyc\n"
        with open(gitignore_path, 'w') as f:
            f.write(original_content)

        manager = GitignoreManager(str(gitignore_path))

        # Create backup
        backup_path = manager.create_backup()
        assert backup_path is not None
        assert Path(backup_path).exists()

        # Modify original file
        modified_content = "# Modified content\n*.log\n"
        with open(gitignore_path, 'w') as f:
            f.write(modified_content)

        # Restore from backup
        assert manager.restore_backup(backup_path)

        # Verify restoration
        with open(gitignore_path, 'r') as f:
            restored_content = f.read()

        assert restored_content == original_content

        print("✓ Backup functionality test passed")


def test_ci_pattern_management():
    """Test CI pattern addition and removal."""
    print("Testing CI pattern management...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Create initial content
        initial_content = [
            "# Python",
            "__pycache__/",
            "*.pyc"
        ]

        with open(gitignore_path, 'w') as f:
            f.write('\n'.join(initial_content))

        manager = GitignoreManager(str(gitignore_path))

        # Test adding CI patterns
        assert manager.add_ci_simulation_patterns(create_backup=False)
        assert manager.has_ci_simulation_patterns()

        # Verify patterns were added
        updated_content = manager._read_gitignore()
        assert "# CI/CD Simulation generated files" in updated_content
        assert "reports/ci-simulation/" in updated_content
        assert ".kiro/ci-history/" in updated_content

        # Test removing CI patterns
        assert manager.remove_ci_simulation_patterns(create_backup=False)
        assert not manager.has_ci_simulation_patterns()

        # Verify original content is preserved
        final_content = manager._read_gitignore()
        for line in initial_content:
            assert line in final_content

        print("✓ CI pattern management test passed")


def test_missing_patterns_detection():
    """Test detection of missing CI patterns."""
    print("Testing missing patterns detection...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Create .gitignore with some CI patterns but not all
        partial_content = [
            "# Python",
            "__pycache__/",
            "reports/ci-simulation/",  # This is a CI pattern
            "*.pyc"
        ]

        with open(gitignore_path, 'w') as f:
            f.write('\n'.join(partial_content))

        manager = GitignoreManager(str(gitignore_path))

        # Get missing patterns
        missing = manager.get_missing_patterns()

        # Should have missing patterns since we only added one
        assert len(missing) > 0
        assert ".kiro/ci-history/" in missing
        assert "temp/ci-simulation/" in missing

        print("✓ Missing patterns detection test passed")


def test_status_information():
    """Test status information retrieval."""
    print("Testing status information...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Create .gitignore
        with open(gitignore_path, 'w') as f:
            f.write("__pycache__/\n*.pyc\n")

        manager = GitignoreManager(str(gitignore_path))

        # Get status
        status = manager.get_status()

        assert status['gitignore_exists'] is True
        assert status['gitignore_path'] == str(gitignore_path)
        assert status['has_ci_patterns'] is False
        assert status['total_lines'] == 2
        assert status['is_valid'] is True
        assert isinstance(status['missing_patterns'], list)

        print("✓ Status information test passed")


def test_backup_management():
    """Test backup listing and cleanup."""
    print("Testing backup management...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Create .gitignore
        with open(gitignore_path, 'w') as f:
            f.write("__pycache__/\n")

        manager = GitignoreManager(str(gitignore_path))

        # Create multiple backups
        import time
        backup_paths = []
        for i in range(3):
            backup_path = manager.create_backup()
            assert backup_path is not None
            backup_paths.append(backup_path)
            # Add small delay to ensure different timestamps
            time.sleep(0.1)

        # List backups
        backups = manager.list_backups()
        print(f"Created backups: {backup_paths}")
        print(f"Found backups: {backups}")
        assert len(backups) == 3

        # Cleanup old backups (keep only 1)
        removed_count = manager.cleanup_old_backups(keep_count=1)
        assert removed_count == 2

        # Verify only 1 backup remains
        remaining_backups = manager.list_backups()
        assert len(remaining_backups) == 1

        print("✓ Backup management test passed")


def test_validation():
    """Test .gitignore validation."""
    print("Testing .gitignore validation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Create valid .gitignore
        with open(gitignore_path, 'w') as f:
            f.write("__pycache__/\n*.pyc\n")

        manager = GitignoreManager(str(gitignore_path))

        # Test validation
        assert manager.validate_gitignore() is True

        print("✓ Validation test passed")


def test_nonexistent_gitignore():
    """Test handling of non-existent .gitignore file."""
    print("Testing non-existent .gitignore handling...")

    with tempfile.TemporaryDirectory() as temp_dir:
        gitignore_path = Path(temp_dir) / ".gitignore"

        # Don't create the file
        manager = GitignoreManager(str(gitignore_path))

        # Test operations on non-existent file
        assert manager.detect_existing_patterns() == set()
        assert not manager.has_ci_simulation_patterns()
        assert manager.create_backup() is None

        # Test adding patterns to non-existent file
        assert manager.add_ci_simulation_patterns(create_backup=False)
        assert gitignore_path.exists()
        assert manager.has_ci_simulation_patterns()

        print("✓ Non-existent .gitignore handling test passed")


def main():
    """Run all tests."""
    print("Running GitignoreManager tests...\n")

    try:
        test_basic_functionality()
        test_backup_functionality()
        test_ci_pattern_management()
        test_missing_patterns_detection()
        test_status_information()
        test_backup_management()
        test_validation()
        test_nonexistent_gitignore()

        print("\n✅ All GitignoreManager tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
