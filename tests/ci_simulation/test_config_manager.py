"""
Unit tests for configuration management system.
"""

import json
import os

# Import the config manager
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools", "ci"))

from config_manager import ConfigManager
from interfaces import ConfigurationError


class TestConfigManager:
    """Test casesigManager class."""

    def test_config_manager_creation(self):
        """Test basic ConfigManager creation."""
        config_manager = ConfigManager()
        assert config_manager.config_path is None
        assert isinstance(config_manager.config, dict)

    def test_config_manager_with_path(self, temp_dir):
        """Test ConfigManager creation with config path."""
        config_path = os.path.join(temp_dir, "test_config.yaml")
        config_manager = ConfigManager(config_path)
        assert config_manager.config_path == config_path

    def test_load_default_config(self):
        """Test loading default configuration."""
        config_manager = ConfigManager()
        config = config_manager.load_config()

        # Check that default config has required sections
        assert "python_versions" in config
        assert "checkers" in config
        assert "timeout" in config
        assert "parallel_jobs" in config
        assert "output_dir" in config

        # Check default values
        assert isinstance(config["python_versions"], list)
        assert isinstance(config["checkers"], dict)
        assert config["timeout"] > 0
        assert config["parallel_jobs"] > 0

    def test_load_yaml_config(self, temp_dir):
        """Test loading YAML configuration file."""
        config_data = {
            "python_versions": ["3.9", "3.10"],
            "timeout": 600,
            "checkers": {
                "code_quality": {"enabled": True},
                "security": {"enabled": False},
            },
        }

        config_path = os.path.join(temp_dir, "test_config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()

        assert config["python_versions"] == ["3.9", "3.10"]
        assert config["timeout"] == 600
        assert config["checkers"]["code_quality"]["enabled"] is True
        assert config["checkers"]["security"]["enabled"] is False

    def test_load_json_config(self, temp_dir):
        """Test loading JSON configuration file."""
        config_data = {
            "python_versions": ["3.11"],
            "timeout": 300,
            "checkers": {"performance": {"enabled": True, "threshold": 30.0}},
        }

        config_path = os.path.join(temp_dir, "test_config.json")
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()

        assert config["python_versions"] == ["3.11"]
        assert config["timeout"] == 300
        assert config["checkers"]["performance"]["threshold"] == 30.0

    def test_load_nonexistent_config(self, temp_dir):
        """Test loading non-existent configuration file."""
        config_path = os.path.join(temp_dir, "nonexistent.yaml")
        config_manager = ConfigManager(config_path)

        # Should fall back to default config
        config = config_manager.load_config()
        assert isinstance(config, dict)
        assert "python_versions" in config

    def test_load_invalid_yaml_config(self, temp_dir):
        """Test loading invalid YAML configuration."""
        config_path = os.path.join(temp_dir, "invalid.yaml")
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content: [")

        config_manager = ConfigManager(config_path)

        with pytest.raises(ConfigurationError):
            config_manager.load_config()

    def test_load_invalid_json_config(self, temp_dir):
        """Test loading invalid JSON configuration."""
        config_path = os.path.join(temp_dir, "invalid.json")
        with open(config_path, "w") as f:
            f.write('{"invalid": json content}')

        config_manager = ConfigManager(config_path)

        with pytest.raises(ConfigurationError):
            config_manager.load_config()

    def test_environment_variable_override(self):
        """Test environment variable configuration override."""
        with patch.dict(
            os.environ,
            {
                "CI_TIMEOUT": "900",
                "CI_PARALLEL_JOBS": "4",
                "CI_PYTHON_VERSIONS": "3.9,3.10,3.11",
            },
        ):
            config_manager = ConfigManager()
            config = config_manager.load_config()

            assert config["timeout"] == 900
            assert config["parallel_jobs"] == 4
            assert config["python_versions"] == ["3.9", "3.10", "3.11"]

    def test_get_python_versions(self, sample_config):
        """Test getting Python versions from config."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        versions = config_manager.get_python_versions()
        assert versions == ["3.9", "3.10", "3.11"]

    def test_get_python_versions_from_env(self):
        """Test getting Python versions from environment variable."""
        with patch.dict(os.environ, {"CI_PYTHON_VERSIONS": "3.8,3.9"}):
            config_manager = ConfigManager()
            versions = config_manager.get_python_versions()
            assert versions == ["3.8", "3.9"]

    def test_get_check_configuration(self, sample_config):
        """Test getting specific check configuration."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        code_quality_config = config_manager.get_check_configuration("code_quality")
        assert code_quality_config["enabled"] is True
        assert code_quality_config["black"]["enabled"] is True
        assert code_quality_config["black"]["line_length"] == 88

    def test_get_check_configuration_nonexistent(self, sample_config):
        """Test getting configuration for non-existent check."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        config = config_manager.get_check_configuration("nonexistent")
        assert config == {}

    def test_is_check_enabled(self, sample_config):
        """Test checking if a check is enabled."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        assert config_manager.is_check_enabled("code_quality") is True
        assert config_manager.is_check_enabled("security") is True
        assert config_manager.is_check_enabled("performance") is True
        assert config_manager.is_check_enabled("tests") is True

    def test_is_check_enabled_disabled(self):
        """Test checking disabled check."""
        config = {"checkers": {"disabled_check": {"enabled": False}}}
        config_manager = ConfigManager()
        config_manager.config = config

        assert config_manager.is_check_enabled("disabled_check") is False

    def test_is_check_enabled_nonexistent(self, sample_config):
        """Test checking non-existent check."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        assert config_manager.is_check_enabled("nonexistent") is False

    def test_get_timeout(self, sample_config):
        """Test getting timeout configuration."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        assert config_manager.get_timeout() == 300

    def test_get_timeout_with_override(self):
        """Test getting timeout with environment override."""
        with patch.dict(os.environ, {"CI_TIMEOUT": "600"}):
            config_manager = ConfigManager()
            assert config_manager.get_timeout() == 600

    def test_get_parallel_jobs(self, sample_config):
        """Test getting parallel jobs configuration."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        assert config_manager.get_parallel_jobs() == 2

    def test_get_parallel_jobs_with_override(self):
        """Test getting parallel jobs with environment override."""
        with patch.dict(os.environ, {"CI_PARALLEL_JOBS": "8"}):
            config_manager = ConfigManager()
            assert config_manager.get_parallel_jobs() == 8

    def test_get_output_directory(self, sample_config):
        """Test getting output directory configuration."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        assert config_manager.get_output_directory() == "reports"

    def test_get_output_directory_with_override(self):
        """Test getting output directory with environment override."""
        with patch.dict(os.environ, {"CI_OUTPUT_DIR": "/tmp/ci_reports"}):
            config_manager = ConfigManager()
            assert config_manager.get_output_directory() == "/tmp/ci_reports"

    def test_validate_config_valid(self, sample_config):
        """Test validating valid configuration."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        errors = config_manager.validate_config()
        assert errors == []

    def test_validate_config_missing_required(self):
        """Test validating configuration with missing required fields."""
        invalid_config = {
            "checkers": {}
            # Missing python_versions, timeout, etc.
        }
        config_manager = ConfigManager()
        config_manager.config = invalid_config

        errors = config_manager.validate_config()
        assert len(errors) > 0
        assert any("python_versions" in error for error in errors)
        assert any("timeout" in error for error in errors)

    def test_validate_config_invalid_types(self):
        """Test validating configuration with invalid types."""
        invalid_config = {
            "python_versions": "not_a_list",
            "timeout": "not_a_number",
            "parallel_jobs": "not_a_number",
            "checkers": "not_a_dict",
        }
        config_manager = ConfigManager()
        config_manager.config = invalid_config

        errors = config_manager.validate_config()
        assert len(errors) >= 4  # At least one error for each invalid field

    def test_merge_configs(self):
        """Test merging configuration dictionaries."""
        base_config = {
            "timeout": 300,
            "checkers": {
                "code_quality": {"enabled": True},
                "security": {"enabled": True},
            },
        }

        override_config = {
            "timeout": 600,
            "checkers": {
                "code_quality": {"enabled": False},
                "performance": {"enabled": True},
            },
        }

        config_manager = ConfigManager()
        merged = config_manager._merge_configs(base_config, override_config)

        assert merged["timeout"] == 600
        assert merged["checkers"]["code_quality"]["enabled"] is False
        assert merged["checkers"]["security"]["enabled"] is True
        assert merged["checkers"]["performance"]["enabled"] is True

    def test_resolve_config_path(self, temp_dir):
        """Test resolving configuration file path."""
        config_manager = ConfigManager()

        # Test with explicit path
        explicit_path = os.path.join(temp_dir, "explicit.yaml")
        resolved = config_manager._resolve_config_path(explicit_path)
        assert resolved == explicit_path

        # Test with None (should look for default files)
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path.endswith("ci-config.yaml")
            resolved = config_manager._resolve_config_path(None)
            assert resolved.endswith("ci-config.yaml")

    def test_apply_environment_overrides(self):
        """Test applying environment variable overrides."""
        config = {"timeout": 300, "parallel_jobs": 2, "python_versions": ["3.9"]}

        with patch.dict(
            os.environ,
            {
                "CI_TIMEOUT": "600",
                "CI_PARALLEL_JOBS": "4",
                "CI_PYTHON_VERSIONS": "3.10,3.11",
            },
        ):
            config_manager = ConfigManager()
            config_manager._apply_environment_overrides(config)

            assert config["timeout"] == 600
            assert config["parallel_jobs"] == 4
            assert config["python_versions"] == ["3.10", "3.11"]

    def test_save_config(self, temp_dir, sample_config):
        """Test saving configuration to file."""
        config_path = os.path.join(temp_dir, "saved_config.yaml")
        config_manager = ConfigManager()
        config_manager.config = sample_config

        config_manager.save_config(config_path)

        assert os.path.exists(config_path)

        # Verify saved content
        with open(config_path, "r") as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["timeout"] == sample_config["timeout"]
        assert saved_config["python_versions"] == sample_config["python_versions"]

    def test_reload_config(self, temp_dir):
        """Test reloading configuration."""
        config_data = {"timeout": 300}
        config_path = os.path.join(temp_dir, "reload_test.yaml")

        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        assert config["timeout"] == 300

        # Modify file
        config_data["timeout"] = 600
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Reload
        config = config_manager.reload_config()
        assert config["timeout"] == 600

    def test_get_checker_specific_config(self, sample_config):
        """Test getting checker-specific configuration."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        black_config = config_manager.get_checker_specific_config(
            "code_quality", "black"
        )
        assert black_config["enabled"] is True
        assert black_config["line_length"] == 88

        # Test non-existent checker
        nonexistent = config_manager.get_checker_specific_config("nonexistent", "tool")
        assert nonexistent == {}

    def test_update_checker_config(self, sample_config):
        """Test updating checker configuration."""
        config_manager = ConfigManager()
        config_manager.config = sample_config

        new_config = {"enabled": False, "line_length": 100}
        config_manager.update_checker_config("code_quality", "black", new_config)

        updated = config_manager.get_checker_specific_config("code_quality", "black")
        assert updated["enabled"] is False
        assert updated["line_length"] == 100

    def test_config_file_watching(self, temp_dir):
        """Test configuration file change detection."""
        config_path = os.path.join(temp_dir, "watch_test.yaml")
        config_data = {"timeout": 300}

        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        config_manager = ConfigManager(config_path)
        config_manager.load_config()

        original_mtime = config_manager._get_config_mtime()

        # Simulate file modification
        import time

        time.sleep(0.1)  # Ensure different timestamp
        config_data["timeout"] = 600
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        assert config_manager._has_config_changed()

        # After reload, should not detect change
        config_manager.reload_config()
        assert not config_manager._has_config_changed()


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_full_config_lifecycle(self, temp_dir):
        """Test complete configuration lifecycle."""
        config_path = os.path.join(temp_dir, "lifecycle_test.yaml")

        # Create initial config
        initial_config = {
            "python_versions": ["3.9"],
            "timeout": 300,
            "checkers": {"code_quality": {"enabled": True}},
        }

        with open(config_path, "w") as f:
            yaml.dump(initial_config, f)

        # Load config
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()

        # Validate
        errors = config_manager.validate_config()
        assert len(errors) == 0

        # Modify
        config_manager.update_checker_config("code_quality", "black", {"enabled": True})

        # Save
        config_manager.save_config(config_path)

        # Reload and verify
        new_manager = ConfigManager(config_path)
        new_config = new_manager.load_config()

        black_config = new_manager.get_checker_specific_config("code_quality", "black")
        assert black_config["enabled"] is True

    def test_config_with_environment_integration(self, temp_dir):
        """Test configuration with environment variable integration."""
        config_path = os.path.join(temp_dir, "env_integration.yaml")

        file_config = {"timeout": 300, "python_versions": ["3.9"]}

        with open(config_path, "w") as f:
            yaml.dump(file_config, f)

        with patch.dict(
            os.environ, {"CI_TIMEOUT": "600", "CI_PYTHON_VERSIONS": "3.10,3.11"}
        ):
            config_manager = ConfigManager(config_path)
            config = config_manager.load_config()

            # Environment should override file
            assert config["timeout"] == 600
            assert config["python_versions"] == ["3.10", "3.11"]
