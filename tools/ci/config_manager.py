"""
Configuration Manager for CI/CD Simulation

This module handles configuration loading, validation, and management
for the CI/CD simulation tool.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

try:
    from .gitignore_manager import GitignoreManager
except ImportError:
    from gitignore_manager import GitignoreManager


@dataclass
class CIConfig:
    """Configuration data class for CI simulation settings"""

    python_versions: List[str]
    enabled_checks: List[str]
    timeout_seconds: int
    output_directory: str
    parallel_execution: bool
    auto_fix: bool
    git_hook_enabled: bool
    performance_threshold: float
    ai_components: Dict[str, bool]
    security_scan_enabled: bool
    report_formats: List[str]


class ConfigManager:
    """
    Manages configuration for CI/CD simulation tool.

    Supports YAML and JSON configuration files with environment variable
    overrides and default value generation.
    """

    DEFAULT_CONFIG = {
        "python_versions": ["3.9", "3.10", "3.11"],
        "enabled_checks": [
            "code_quality",
            "unit_tests",
            "integration_tests",
            "ai_compatibility",
            "security_scan",
            "performance_tests",
        ],
        "timeout_seconds": 1800,  # 30 minutes
        "output_directory": "reports/ci-simulation",
        "parallel_execution": True,
        "auto_fix": False,
        "git_hook_enabled": False,
        "performance_threshold": 30.0,  # 30% regression threshold
        "ai_components": {"copilot": True, "cursor": True, "kiro": True},
        "security_scan_enabled": True,
        "report_formats": ["markdown", "json"],
        "directories": {
            "history": ".kiro/ci-history",
            "reports": "reports/ci-simulation",
            "logs": "logs",
            "temp": "temp/ci-simulation",
        },
        "tools": {
            "black": {
                "enabled": True,
                "line_length": 88,
                "target_version": ["py39", "py310", "py311"],
            },
            "isort": {"enabled": True, "profile": "black", "multi_line_output": 3},
            "flake8": {
                "enabled": True,
                "max_line_length": 88,
                "ignore": ["E203", "W503"],
            },
            "mypy": {"enabled": True, "strict": True, "ignore_missing_imports": True},
            "safety": {"enabled": True, "ignore_ids": []},
            "bandit": {"enabled": True, "severity_level": "medium"},
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ConfigManager.

        Args:
            config_path: Path to configuration file. If None, searches for
                        default config files in standard locations.
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.gitignore_manager = GitignoreManager()
        self._load_config()

    def _find_config_file(self) -> Optional[str]:
        """
        Find configuration file in standard locations.

        Returns:
            Path to configuration file or None if not found.
        """
        search_paths = [
            ".kiro/ci-config.yml",
            ".kiro/ci-config.yaml",
            ".kiro/ci-config.json",
            "ci-config.yml",
            "ci-config.yaml",
            "ci-config.json",
        ]

        for path in search_paths:
            if Path(path).exists():
                self.logger.info(f"Found configuration file: {path}")
                return path

        return None

    def _load_config(self) -> None:
        """Load configuration from file or create default configuration."""
        # Start with default configuration
        self.config = self.DEFAULT_CONFIG.copy()

        # Find configuration file if not specified
        if not self.config_path:
            self.config_path = self._find_config_file()

        # Load from file if exists
        if self.config_path and Path(self.config_path).exists():
            try:
                self._load_from_file(self.config_path)
                self.logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                self.logger.warning(
                    f"Failed to load config from {self.config_path}: {e}"
                )
                self.logger.info("Using default configuration")
        else:
            self.logger.info("No configuration file found, using defaults")

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Validate configuration
        self._validate_config()

    def _load_from_file(self, file_path: str) -> None:
        """
        Load configuration from YAML or JSON file.

        Args:
            file_path: Path to configuration file.
        """
        path = Path(file_path)

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix.lower() in [".yml", ".yaml"]:
                file_config = yaml.safe_load(f)
            elif path.suffix.lower() == ".json":
                file_config = json.load(f)
            else:
                raise ValueError(
                    f"Unsupported configuration file format: {path.suffix}"
                )

        if file_config:
            # Deep merge with default configuration
            self._deep_merge(self.config, file_config)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Deep merge override dictionary into base dictionary.

        Args:
            base: Base dictionary to merge into.
            override: Override dictionary to merge from.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            "CI_PYTHON_VERSIONS": ("python_versions", lambda x: x.split(",")),
            "CI_TIMEOUT": ("timeout_seconds", int),
            "CI_OUTPUT_DIR": ("output_directory", str),
            "CI_PARALLEL": ("parallel_execution", lambda x: x.lower() == "true"),
            "CI_AUTO_FIX": ("auto_fix", lambda x: x.lower() == "true"),
            "CI_GIT_HOOK": ("git_hook_enabled", lambda x: x.lower() == "true"),
            "CI_PERF_THRESHOLD": ("performance_threshold", float),
            "CI_SECURITY_SCAN": (
                "security_scan_enabled",
                lambda x: x.lower() == "true",
            ),
        }

        for env_var, (config_key, converter) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    self.config[config_key] = converter(env_value)
                    self.logger.info(
                        f"Applied environment override: {env_var}={env_value}"
                    )
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Invalid environment variable {env_var}={env_value}: {e}"
                    )

    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Validate Python versions
        if not self.config.get("python_versions"):
            raise ValueError("At least one Python version must be specified")

        # Validate timeout
        if self.config.get("timeout_seconds", 0) <= 0:
            raise ValueError("Timeout must be positive")

        # Validate performance threshold
        threshold = self.config.get("performance_threshold", 0)
        if threshold < 0 or threshold > 100:
            raise ValueError("Performance threshold must be between 0 and 100")

        # Validate enabled checks
        valid_checks = {
            "code_quality",
            "unit_tests",
            "integration_tests",
            "ai_compatibility",
            "security_scan",
            "performance_tests",
        }
        enabled_checks = set(self.config.get("enabled_checks", []))
        invalid_checks = enabled_checks - valid_checks
        if invalid_checks:
            raise ValueError(f"Invalid checks specified: {invalid_checks}")

        self.logger.info("Configuration validation passed")

    def get_config(self) -> Dict[str, Any]:
        """
        Get complete configuration dictionary.

        Returns:
            Complete configuration dictionary.
        """
        return self.config.copy()

    def get_python_versions(self) -> List[str]:
        """
        Get list of Python versions to test.

        Returns:
            List of Python version strings.
        """
        return self.config.get("python_versions", [])

    def get_enabled_checks(self) -> List[str]:
        """
        Get list of enabled checks.

        Returns:
            List of enabled check names.
        """
        return self.config.get("enabled_checks", [])

    def get_check_configuration(self, check_name: str) -> Dict[str, Any]:
        """
        Get configuration for specific check.

        Args:
            check_name: Name of the check.

        Returns:
            Configuration dictionary for the check.
        """
        tools_config = self.config.get("tools", {})
        return tools_config.get(check_name, {})

    def is_check_enabled(self, check_name: str) -> bool:
        """
        Check if a specific check is enabled.

        Args:
            check_name: Name of the check.

        Returns:
            True if check is enabled, False otherwise.
        """
        return check_name in self.get_enabled_checks()

    def get_timeout(self) -> int:
        """
        Get timeout in seconds.

        Returns:
            Timeout in seconds.
        """
        return self.config.get("timeout_seconds", 1800)

    def get_output_directory(self) -> str:
        """
        Get output directory path.

        Returns:
            Output directory path.
        """
        return self.config.get("output_directory", "reports/ci-simulation")

    def get_directories(self) -> Dict[str, str]:
        """
        Get all directory configurations.

        Returns:
            Dictionary of directory configurations.
        """
        return self.config.get("directories", {})

    def is_parallel_execution_enabled(self) -> bool:
        """
        Check if parallel execution is enabled.

        Returns:
            True if parallel execution is enabled.
        """
        return self.config.get("parallel_execution", True)

    def is_auto_fix_enabled(self) -> bool:
        """
        Check if auto-fix is enabled.

        Returns:
            True if auto-fix is enabled.
        """
        return self.config.get("auto_fix", False)

    def get_performance_threshold(self) -> float:
        """
        Get performance regression threshold.

        Returns:
            Performance threshold as percentage.
        """
        return self.config.get("performance_threshold", 30.0)

    def get_ai_components(self) -> Dict[str, bool]:
        """
        Get AI component configuration.

        Returns:
            Dictionary of AI component enablement status.
        """
        return self.config.get("ai_components", {})

    def get_report_formats(self) -> List[str]:
        """
        Get enabled report formats.

        Returns:
            List of enabled report formats.
        """
        return self.config.get("report_formats", ["markdown", "json"])

    def create_default_config_file(self, file_path: str) -> None:
        """
        Create default configuration file.

        Args:
            file_path: Path where to create the configuration file.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix.lower() in [".yml", ".yaml"]:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, indent=2)
        elif path.suffix.lower() == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported configuration file format: {path.suffix}")

        self.logger.info(f"Created default configuration file: {file_path}")

    def save_config(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            file_path: Path to save configuration. If None, uses current config_path.
        """
        if not file_path:
            file_path = self.config_path

        if not file_path:
            raise ValueError("No configuration file path specified")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix.lower() in [".yml", ".yaml"]:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        elif path.suffix.lower() == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported configuration file format: {path.suffix}")

        self.logger.info(f"Saved configuration to: {file_path}")

    def update_gitignore(self) -> bool:
        """
        Update .gitignore file with CI simulation patterns.

        Returns:
            True if update was successful.
        """
        return self.gitignore_manager.update_gitignore()

    def get_gitignore_status(self) -> dict:
        """
        Get status of .gitignore file and CI patterns.

        Returns:
            Dictionary with gitignore status information.
        """
        return self.gitignore_manager.get_status()
