#!/usr/bin/env python3
"""
Test script for integrated ConfigManager and GitignoreManager functionality.

This script tests the integration between configuration management and
.gitignore management features.
"""

import os
import tempfile
import json
from pathlib import Path
from config_manager import ConfigManager


def test_integrated_gitignore_management():
    """Test integrated .gitignore management through ConfigManager."""
    print("Testing integrated .gitignore management...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory for testing
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Create initial .gitignore
            gitignore_path = Path(".gitignore")
            initial_content = [
                "# Python",
                "__pycache__/",
                "*.pyc",
                "",
                "# IDE",
                ".vscode/",
            ]

            with open(gitignore_path, "w") as f:
                f.write("\n".join(initial_content))

            # Create ConfigManager
            config_manager = ConfigManager()

            # Test gitignore status
            status = config_manager.get_gitignore_status()
            assert status["gitignore_exists"] is True
            assert status["has_ci_patterns"] is False

            # Update .gitignore with CI patterns
            assert config_manager.update_gitignore() is True

            # Verify patterns were added
            updated_status = config_manager.get_gitignore_status()
            assert updated_status["has_ci_patterns"] is True

            # Verify original content is preserved
            with open(gitignore_path, "r") as f:
                content = f.read()

            for line in initial_content:
                if line.strip():  # Skip empty lines
                    assert line in content

            # Verify CI patterns were added
            assert "reports/ci-simulation/" in content
            assert ".kiro/ci-history/" in content

            print("✓ Integrated .gitignore management test passed")

        finally:
            os.chdir(original_cwd)


def test_config_with_gitignore_integration():
    """Test configuration loading with .gitignore integration."""
    print("Testing configuration with .gitignore integration...")

    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Create configuration file
            config_data = {
                "python_versions": ["3.9", "3.10"],
                "enabled_checks": ["code_quality", "unit_tests"],
                "auto_fix": True,
            }

            config_path = Path("ci-config.json")
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            # Create ConfigManager with specific config
            config_manager = ConfigManager(str(config_path))

            # Verify configuration was loaded
            config = config_manager.get_config()
            assert config["python_versions"] == ["3.9", "3.10"]
            assert config["auto_fix"] is True

            # Test .gitignore management
            assert config_manager.update_gitignore() is True

            # Verify .gitignore was created and updated
            gitignore_path = Path(".gitignore")
            assert gitignore_path.exists()

            status = config_manager.get_gitignore_status()
            assert status["has_ci_patterns"] is True

            print("✓ Configuration with .gitignore integration test passed")

        finally:
            os.chdir(original_cwd)


def test_gitignore_status_reporting():
    """Test detailed .gitignore status reporting."""
    print("Testing .gitignore status reporting...")

    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            config_manager = ConfigManager()

            # Test status with no .gitignore
            status = config_manager.get_gitignore_status()
            assert status["gitignore_exists"] is False
            assert status["has_ci_patterns"] is False
            assert status["total_lines"] == 0

            # Create .gitignore and update
            config_manager.update_gitignore()

            # Test status after update
            updated_status = config_manager.get_gitignore_status()
            assert updated_status["gitignore_exists"] is True
            assert updated_status["has_ci_patterns"] is True
            assert updated_status["total_lines"] > 0
            assert updated_status["is_valid"] is True
            assert len(updated_status["missing_patterns"]) == 0

            print("✓ .gitignore status reporting test passed")

        finally:
            os.chdir(original_cwd)


def test_error_handling():
    """Test error handling in integrated functionality."""
    print("Testing error handling...")

    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Create read-only directory to test permission errors
            readonly_dir = Path("readonly")
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # Read-only

            # Try to create .gitignore in read-only directory
            config_manager = ConfigManager()
            config_manager.gitignore_manager.gitignore_path = (
                readonly_dir / ".gitignore"
            )

            # This should handle the error gracefully
            result = config_manager.update_gitignore()
            # The result might be False due to permission error, which is expected
            # The important thing is that it doesn't crash

            print("✓ Error handling test passed")

        except Exception as e:
            # Clean up read-only directory
            readonly_dir.chmod(0o755)
            raise
        finally:
            # Clean up read-only directory
            if "readonly_dir" in locals():
                readonly_dir.chmod(0o755)
            os.chdir(original_cwd)


def main():
    """Run all integration tests."""
    print("Running integrated ConfigManager and GitignoreManager tests...\n")

    try:
        test_integrated_gitignore_management()
        test_config_with_gitignore_integration()
        test_gitignore_status_reporting()
        test_error_handling()

        print("\n✅ All integration tests passed!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise


if __name__ == "__main__":
    main()
