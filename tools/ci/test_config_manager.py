#!/usr/bin/env python3
"""
Test script for ConfigManager functionality.

This script tests the configuration loading, validation, and environment
variable override functionality.
"""

import os
import tempfile
import json
import yaml
from pathlib import Path
from config_manager import ConfigManager


def test_default_config():
    """Test default configuration loading."""
    print("Testing default configuration...")

    config_manager = ConfigManager()
    config = config_manager.get_config()

    assert config["python_versions"] == ["3.9", "3.10", "3.11"]
    assert "code_quality" in config["enabled_checks"]
    assert config["timeout_seconds"] == 1800
    assert config["parallel_execution"] is True

    print("✓ Default configuration test passed")


def test_yaml_config():
    """Test YAML configuration loading."""
    print("Testing YAML configuration loading...")

    test_config = {
        "python_versions": ["3.9", "3.10"],
        "timeout_seconds": 900,
        "auto_fix": True,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        yaml.dump(test_config, f)
        temp_path = f.name

    try:
        config_manager = ConfigManager(temp_path)
        config = config_manager.get_config()

        assert config["python_versions"] == ["3.9", "3.10"]
        assert config["timeout_seconds"] == 900
        assert config["auto_fix"] is True

        print("✓ YAML configuration test passed")
    finally:
        os.unlink(temp_path)


def test_json_config():
    """Test JSON configuration loading."""
    print("Testing JSON configuration loading...")

    test_config = {
        "python_versions": ["3.11"],
        "performance_threshold": 25.0,
        "parallel_execution": False,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_config, f)
        temp_path = f.name

    try:
        config_manager = ConfigManager(temp_path)
        config = config_manager.get_config()

        assert config["python_versions"] == ["3.11"]
        assert config["performance_threshold"] == 25.0
        assert config["parallel_execution"] is False

        print("✓ JSON configuration test passed")
    finally:
        os.unlink(temp_path)


def test_env_overrides():
    """Test environment variable overrides."""
    print("Testing environment variable overrides...")

    # Set environment variables
    os.environ["CI_PYTHON_VERSIONS"] = "3.9,3.11"
    os.environ["CI_TIMEOUT"] = "600"
    os.environ["CI_AUTO_FIX"] = "true"
    os.environ["CI_PARALLEL"] = "false"

    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()

        assert config["python_versions"] == ["3.9", "3.11"]
        assert config["timeout_seconds"] == 600
        assert config["auto_fix"] is True
        assert config["parallel_execution"] is False

        print("✓ Environment variable override test passed")
    finally:
        # Clean up environment variables
        for var in ["CI_PYTHON_VERSIONS", "CI_TIMEOUT", "CI_AUTO_FIX", "CI_PARALLEL"]:
            if var in os.environ:
                del os.environ[var]


def test_config_methods():
    """Test configuration accessor methods."""
    print("Testing configuration accessor methods...")

    config_manager = ConfigManager()

    # Test getter methods
    assert isinstance(config_manager.get_python_versions(), list)
    assert isinstance(config_manager.get_enabled_checks(), list)
    assert isinstance(config_manager.get_timeout(), int)
    assert isinstance(config_manager.get_output_directory(), str)
    assert isinstance(config_manager.is_parallel_execution_enabled(), bool)
    assert isinstance(config_manager.is_auto_fix_enabled(), bool)
    assert isinstance(config_manager.get_performance_threshold(), float)
    assert isinstance(config_manager.get_ai_components(), dict)
    assert isinstance(config_manager.get_report_formats(), list)

    # Test check enablement
    assert config_manager.is_check_enabled("code_quality")
    assert not config_manager.is_check_enabled("nonexistent_check")

    print("✓ Configuration accessor methods test passed")


def test_config_validation():
    """Test configuration validation."""
    print("Testing configuration validation...")

    # Test invalid configuration
    invalid_config = {
        "python_versions": [],  # Empty list should fail
        "timeout_seconds": -1,  # Negative timeout should fail
        "performance_threshold": 150,  # > 100 should fail
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(invalid_config, f)
        temp_path = f.name

    try:
        try:
            ConfigManager(temp_path)
            assert False, "Should have raised validation error"
        except ValueError:
            print("✓ Configuration validation correctly caught invalid config")
    finally:
        os.unlink(temp_path)


def test_default_config_creation():
    """Test default configuration file creation."""
    print("Testing default configuration file creation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test-config.yml"

        config_manager = ConfigManager()
        config_manager.create_default_config_file(str(config_path))

        assert config_path.exists()

        # Load and verify the created config
        new_config_manager = ConfigManager(str(config_path))
        config = new_config_manager.get_config()

        assert "python_versions" in config
        assert "enabled_checks" in config

        print("✓ Default configuration file creation test passed")


def main():
    """Run all tests."""
    print("Running ConfigManager tests...\n")

    try:
        test_default_config()
        test_yaml_config()
        test_json_config()
        test_env_overrides()
        test_config_methods()
        test_config_validation()
        test_default_config_creation()

        print("\n✅ All ConfigManager tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
