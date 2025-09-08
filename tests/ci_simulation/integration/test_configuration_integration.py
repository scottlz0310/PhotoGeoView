"""
Integration tests for configuration management and system integration.

These tests verify that the configuration system works correctly
with real configuration files and environment variables.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Add the tools/ci directory to the path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "tools" / "ci"))

from config_manager import ConfigManager
from models import CheckStatus
from simulator import CISimulator


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration management."""

    @pytest.fixture
    def config_files_setup(self, temp_dir):
        """Set up various configuration files for testing."""
        config_dir = Path(temp_dir) / "config_test"
        config_dir.mkdir()

        # Create YAML configuration
        yaml_config = {
            "python_versions": ["3.9", "3.10", "3.11"],
            "timeout": 600,
            "parallel_jobs": 4,
            "output_dir": "test_reports",
            "checkers": {
                "code_quality": {
                    "enabled": True,
                    "black": {"enabled": True, "line_length": 100},
                    "isort": {"enabled": True, "profile": "black"},
                    "flake8": {"enabled": True, "max_line_length": 100},
                    "mypy": {"enabled": True, "strict": True},
                },
                "security": {
                    "enabled": True,
                    "safety": {"enabled": True, "ignore": ["12345"]},
                    "bandit": {"enabled": True, "severity": "medium"},
                },
                "tests": {
                    "enabled": True,
                    "unit_tests": True,
                    "integration_tests": True,
                    "coverage_threshold": 85,
                },
                "performance": {
                    "enabled": True,
                    "regression_threshold": 25.0,
                    "baseline_file": "performance_baseline.json",
                },
            },
        }

        yaml_path = config_dir / "ci-config.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(yaml_config, f)

        # Create JSON configuration (alternative format)
        json_config = {
            "python_versions": ["3.10"],
            "timeout": 300,
            "parallel_jobs": 2,
            "checkers": {
                "code_quality": {"enabled": True},
                "security": {"enabled": False},
                "tests": {"enabled": True},
            },
        }

        json_path = config_dir / "ci-config.json"
        with open(json_path, "w") as f:
            json.dump(json_config, f)

        # Create minimal configuration
        minimal_config = {
            "python_versions": ["3.10"],
            "checkers": {"code_quality": {"enabled": True}},
        }

        minimal_path = config_dir / "minimal-config.yaml"
        with open(minimal_path, "w") as f:
            yaml.dump(minimal_config, f)

        # Create invalid configuration
        invalid_path = config_dir / "invalid-config.yaml"
        with open(invalid_path, "w") as f:
            f.write("invalid: yaml: content: [")

        return {
            "dir": config_dir,
            "yaml": yaml_path,
            "json": json_path,
            "minimal": minimal_path,
            "invalid": invalid_path,
        }

    def test_yaml_configuration_loading(self, config_files_setup):
        """Test loading YAML configuration file."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))
        config = config_manager.load_config()

        # Verify configuration was loaded correctly
        assert config["python_versions"] == ["3.9", "3.10", "3.11"]
        assert config["timeout"] == 600
        assert config["parallel_jobs"] == 4
        assert config["output_dir"] == "test_reports"

        # Verify nested configuration
        assert config["checkers"]["code_quality"]["enabled"] is True
        assert config["checkers"]["code_quality"]["black"]["line_length"] == 100
        assert config["checkers"]["security"]["safety"]["ignore"] == ["12345"]
        assert config["checkers"]["performance"]["regression_threshold"] == 25.0

    def test_json_configuration_loading(self, config_files_setup):
        """Test loading JSON configuration file."""
        config_manager = ConfigManager(str(config_files_setup["json"]))
        config = config_manager.load_config()

        # Verify configuration was loaded correctly
        assert config["python_versions"] == ["3.10"]
        assert config["timeout"] == 300
        assert config["parallel_jobs"] == 2

        # Verify checker configuration
        assert config["checkers"]["co"]["enabled"] is True
        assert config["checkers"]["security"]["enabled"] is False
        assert config["checkers"]["tests"]["enabled"] is True

    def test_minimal_configuration_with_defaults(self, config_files_setup):
        """Test minimal configuration with default value fallback."""
        config_manager = ConfigManager(str(config_files_setup["minimal"]))
        config = config_manager.load_config()

        # Verify minimal config was loaded
        assert config["python_versions"] == ["3.10"]
        assert config["checkers"]["code_quality"]["enabled"] is True

        # Verify defaults were applied
        assert "timeout" in config
        assert "parallel_jobs" in config
        assert config["timeout"] > 0
        assert config["parallel_jobs"] > 0

    def test_invalid_configuration_handling(self, config_files_setup):
        """Test handling of invalid configuration files."""
        config_manager = ConfigManager(str(config_files_setup["invalid"]))

        # Should raise ConfigurationError for invalid YAML
        from interfaces import ConfigurationError

        with pytest.raises(ConfigurationError):
            config_manager.load_config()

    def test_environment_variable_overrides(self, config_files_setup):
        """Test environment variable configuration overrides."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))

        # Set environment variables
        env_vars = {
            "CI_TIMEOUT": "900",
            "CI_PARALLEL_JOBS": "8",
            "CI_PYTHON_VERSIONS": "3.8,3.9,3.10",
            "CI_OUTPUT_DIR": "/tmp/ci_reports",
        }

        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()

            # Verify environment overrides took effect
            assert config["timeout"] == 900
            assert config["parallel_jobs"] == 8
            assert config["python_versions"] == ["3.8", "3.9", "3.10"]
            assert config["output_dir"] == "/tmp/ci_reports"

            # Verify non-overridden values remain from file
            assert config["checkers"]["code_quality"]["black"]["line_length"] == 100

    def test_configuration_validation(self, config_files_setup):
        """Test configuration validation."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))
        config = config_manager.load_config()

        # Validate the loaded configuration
        errors = config_manager.validate_config()

        # Should have no validation errors for valid config
        assert errors == []

        # Test with invalid configuration
        config_manager.config = {
            "python_versions": "not_a_list",  # Should be list
            "timeout": "not_a_number",  # Should be number
            "checkers": "not_a_dict",  # Should be dict
        }

        errors = config_manager.validate_config()
        assert len(errors) > 0
        assert any("python_versions" in error for error in errors)
        assert any("timeout" in error for error in errors)
        assert any("checkers" in error for error in errors)

    def test_configuration_with_simulator(self, config_files_setup):
        """Test configuration integration with CI simulator."""
        config_path = str(config_files_setup["yaml"])
        simulator = CISimulator(config_path)

        # Verify simulator loaded configuration correctly
        assert simulator.config_manager.config["timeout"] == 600
        assert simulator.config_manager.config["parallel_jobs"] == 4

        # Verify configuration affects simulator behavior
        assert simulator.config_manager.get_timeout() == 600
        assert simulator.config_manager.get_parallel_jobs() == 4
        assert simulator.config_manager.get_python_versions() == ["3.9", "3.10", "3.11"]

    def test_configuration_hot_reload(self, config_files_setup):
        """Test configuration hot reloading."""
        config_path = config_files_setup["yaml"]
        config_manager = ConfigManager(str(config_path))

        # Load initial configuration
        initial_config = config_manager.load_config()
        assert initial_config["timeout"] == 600

        # Modify configuration file
        modified_config = initial_config.copy()
        modified_config["timeout"] = 1200

        with open(config_path, "w") as f:
            yaml.dump(modified_config, f)

        # Reload configuration
        reloaded_config = config_manager.reload_config()

        # Verify changes were picked up
        assert reloaded_config["timeout"] == 1200

    def test_checker_specific_configuration(self, config_files_setup):
        """Test checker-specific configuration retrieval."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))
        config_manager.load_config()

        # Test getting checker-specific configuration
        black_config = config_manager.get_checker_specific_config(
            "code_quality", "black"
        )
        assert black_config["enabled"] is True
        assert black_config["line_length"] == 100

        safety_config = config_manager.get_checker_specific_config("security", "safety")
        assert safety_config["enabled"] is True
        assert safety_config["ignore"] == ["12345"]

        # Test non-existent checker configuration
        nonexistent_config = config_manager.get_checker_specific_config(
            "nonexistent", "tool"
        )
        assert nonexistent_config == {}

    def test_configuration_update_and_save(self, config_files_setup):
        """Test updating and saving configuration."""
        config_path = config_files_setup["yaml"]
        config_manager = ConfigManager(str(config_path))
        config_manager.load_config()

        # Update checker configuration
        new_black_config = {"enabled": True, "line_length": 120}
        config_manager.update_checker_config("code_quality", "black", new_black_config)

        # Save configuration
        config_manager.save_config(str(config_path))

        # Reload and verify changes
        new_manager = ConfigManager(str(config_path))
        new_config = new_manager.load_config()

        updated_black_config = new_manager.get_checker_specific_config(
            "code_quality", "black"
        )
        assert updated_black_config["line_length"] == 120

    def test_configuration_inheritance_and_merging(self, config_files_setup):
        """Test configuration inheritance and merging."""
        config_manager = ConfigManager(str(config_files_setup["minimal"]))

        # Load minimal config
        minimal_config = config_manager.load_config()

        # Should have defaults merged in
        assert "timeout" in minimal_config
        assert "parallel_jobs" in minimal_config

        # Should preserve explicit values
        assert minimal_config["python_versions"] == ["3.10"]
        assert minimal_config["checkers"]["code_quality"]["enabled"] is True

        # Should have default checker configurations
        assert "checkers" in minimal_config
        assert isinstance(minimal_config["checkers"], dict)


@pytest.mark.integration
class TestEnvironmentIntegration:
    """Integration tests for environment variable handling."""

    def test_comprehensive_environment_override(self, config_files_setup):
        """Test comprehensive environment variable override."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))

        # Set comprehensive environment overrides
        env_vars = {
            "CI_TIMEOUT": "1800",
            "CI_PARALLEL_JOBS": "16",
            "CI_PYTHON_VERSIONS": "3.8,3.9,3.10,3.11,3.12",
            "CI_OUTPUT_DIR": "/custom/output",
            "CI_CODE_QUALITY_ENABLED": "true",
            "CI_SECURITY_ENABLED": "false",
            "CI_TESTS_ENABLED": "true",
            "CI_PERFORMANCE_ENABLED": "false",
        }

        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()

            # Verify all overrides
            assert config["timeout"] == 1800
            assert config["parallel_jobs"] == 16
            assert config["python_versions"] == ["3.8", "3.9", "3.10", "3.11", "3.12"]
            assert config["output_dir"] == "/custom/output"

    def test_partial_environment_override(self, config_files_setup):
        """Test partial environment variable override."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))

        # Set only some environment variables
        env_vars = {"CI_TIMEOUT": "450", "CI_PYTHON_VERSIONS": "3.11"}

        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()

            # Verify overridden values
            assert config["timeout"] == 450
            assert config["python_versions"] == ["3.11"]

            # Verify non-overridden values remain from file
            assert config["parallel_jobs"] == 4  # From file
            assert config["output_dir"] == "test_reports"  # From file

    def test_environment_variable_type_conversion(self, config_files_setup):
        """Test proper type conversion of environment variables."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))

        env_vars = {
            "CI_TIMEOUT": "300",  # String -> int
            "CI_PARALLEL_JOBS": "2",  # String -> int
            "CI_PYTHON_VERSIONS": "3.9,3.10",  # String -> list
        }

        with patch.dict(os.environ, env_vars):
            config = config_manager.load_config()

            # Verify types were converted correctly
            assert isinstance(config["timeout"], int)
            assert isinstance(config["parallel_jobs"], int)
            assert isinstance(config["python_versions"], list)

            assert config["timeout"] == 300
            assert config["parallel_jobs"] == 2
            assert config["python_versions"] == ["3.9", "3.10"]

    def test_invalid_environment_variable_handling(self, config_files_setup):
        """Test handling of invalid environment variable values."""
        config_manager = ConfigManager(str(config_files_setup["yaml"]))

        # Set invalid environment variables
        env_vars = {
            "CI_TIMEOUT": "not_a_number",
            "CI_PARALLEL_JOBS": "invalid",
        }

        with patch.dict(os.environ, env_vars):
            # Should fall back to file values or defaults when env vars are invalid
            config = config_manager.load_config()

            # Should use file values since env vars are invalid
            assert config["timeout"] == 600  # From file
            assert config["parallel_jobs"] == 4  # From file


@pytest.mark.integration
class TestConfigurationPersistence:
    """Integration tests for configuration persistence and file management."""

    def test_configuration_backup_and_restore(self, config_files_setup, temp_dir):
        """Test configuration backup and restore functionality."""
        original_config_path = config_files_setup["yaml"]
        backup_dir = Path(temp_dir) / "backups"
        backup_dir.mkdir()

        config_manager = ConfigManager(str(original_config_path))
        original_config = config_manager.load_config()

        # Create backup
        backup_path = backup_dir / "config_backup.yaml"
        config_manager.save_config(str(backup_path))

        # Modify original
        modified_config = original_config.copy()
        modified_config["timeout"] = 9999
        config_manager.config = modified_config
        config_manager.save_config(str(original_config_path))

        # Restore from backup
        backup_manager = ConfigManager(str(backup_path))
        restored_config = backup_manager.load_config()

        # Verify restoration
        assert restored_config["timeout"] == original_config["timeout"]
        assert restored_config["parallel_jobs"] == original_config["parallel_jobs"]

    def test_configuration_migration(self, config_files_setup, temp_dir):
        """Test configuration format migration."""
        # Load YAML config
        yaml_manager = ConfigManager(str(config_files_setup["yaml"]))
        yaml_config = yaml_manager.load_config()

        # Save as JSON
        json_path = Path(temp_dir) / "migrated_config.json"
        with open(json_path, "w") as f:
            json.dump(yaml_config, f, indent=2)

        # Load JSON config
        json_manager = ConfigManager(str(json_path))
        json_config = json_manager.load_config()

        # Verify migration preserved data
        assert json_config["timeout"] == yaml_config["timeout"]
        assert json_config["python_versions"] == yaml_config["python_versions"]
        assert (
            json_config["checkers"]["code_quality"]["enabled"]
            == yaml_config["checkers"]["code_quality"]["enabled"]
        )

    def test_concurrent_configuration_access(self, config_files_setup):
        """Test concurrent access to configuration files."""
        config_path = str(config_files_setup["yaml"])

        # Create multiple config managers (simulating concurrent access)
        manager1 = ConfigManager(config_path)
        manager2 = ConfigManager(config_path)

        # Load configuration from both
        config1 = manager1.load_config()
        config2 = manager2.load_config()

        # Both should load the same configuration
        assert config1["timeout"] == config2["timeout"]
        assert config1["python_versions"] == config2["python_versions"]

        # Modify through one manager
        config1["timeout"] = 1500
        manager1.config = config1
        manager1.save_config(config_path)

        # Reload through second manager
        updated_config2 = manager2.reload_config()

        # Should see the changes
        assert updated_config2["timeout"] == 1500
