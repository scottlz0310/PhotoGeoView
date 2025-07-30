"""
Code Quality Checker for CI Simulation Tool

This module implements comprehensive code quality checks including
Black formatting, isort import sorting, flake8 style checking,
and mypy type checking with detailed error reporting and auto-fix capabilities.
"""

import subprocess
import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import time
from dataclasses import dataclass

try:
    from ..interfaces import CheckerInterface
    from ..models import CheckResult, CheckStatus, ConfigDict
except ImportError:
    from interfaces import CheckerInterface
    from models import CheckResult, CheckStatus, ConfigDict


@dataclass
class QualityIssue:
    """Represents aty issue found by a checker."""

    file_path: str
    line_number: int
    column: Optional[int]
    rule_code: str
    message: str
    severity: str
    tool: str


class CodeQualityChecker(CheckerInterface):
    """
    Comprehensive code quality checker with Black, isort, flake8, and mypy integration.

    This checker provides:
    - Black code formatting with auto-fix capability
    - Configuration file detection and parsing
    - Detailed error reporting with line numbers
    - Integration with pyproject.toml settings
    """

    def __init__(self, config: ConfigDict):
        """
        Initialize the code quality checker.

        Args:
            config: Configuration dictionary containing tool settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()
        self.pyproject_path = self.project_root / "pyproject.toml"

        # Load tool configurations
        self.black_config = self._load_black_config()
        self.isort_config = self._load_isort_config()
        self.flake8_config = self._load_flake8_config()
        self.mypy_config = self._load_mypy_config()

    @property
    def name(self) -> str:
        """Return the human-readable name of this checker."""
        return "Code Quality Checker"

    @property
    def check_type(self) -> str:
        """Return the type category of this checker."""
        return "code_quality"

    @property
    def dependencies(self) -> List[str]:
        """Return list of external dependencies required by this checker."""
        return ["black", "isort", "flake8", "mypy"]

    def is_available(self) -> bool:
        """
        Check if all required tools are available.

        Returns:
            True if all dependencies are available
        """
        if self._is_available is not None:
            return self._is_available

        missing_tools = []
        for tool in self.dependencies:
            if not self._is_tool_available(tool):
                missing_tools.append(tool)

        if missing_tools:
            self.logger.warning(f"Missing code quality tools: {missing_tools}")
            self._is_available = False
        else:
            self._is_available = True

        return self._is_available

    def _is_tool_available(self, tool: str) -> bool:
        """Check if a specific tool is available in the environment."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", tool, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _load_black_config(self) -> Dict[str, Any]:
        """Load Black configuration from pyproject.toml or use defaults."""
        config = self.config.get("tools", {}).get("black", {})

        # Default Black configuration
        default_config = {
            "line_length": 88,
            "target_version": ["py39", "py310", "py311"],
            "include": r"\.pyi?$",
            "extend_exclude": r"/(\.eggs|\.git|\.hg|\.mypy_cache|\.tox|\.venv|build|dist)/",
        }

        # Merge with provided configuration
        merged_config = {**default_config, **config}

        # Try to load from pyproject.toml if it exists
        if self.pyproject_path.exists():
            try:
                # Try to use tomllib (Python 3.11+) or fall back to tomli
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        tomllib = None

                if tomllib:
                    with open(self.pyproject_path, "rb") as f:
                        pyproject_data = tomllib.load(f)

                    black_config = pyproject_data.get("tool", {}).get("black", {})
                    merged_config.update(black_config)
                else:
                    self.logger.warning(
                        "tomllib/tomli not available, using default Black config"
                    )

            except ImportError:
                self.logger.warning(
                    "tomllib/tomli not available, using default Black config"
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to load Black config from pyproject.toml: {e}"
                )

        return merged_config

    def _load_isort_config(self) -> Dict[str, Any]:
        """Load isort configuration from pyproject.toml or use defaults."""
        config = self.config.get("tools", {}).get("isort", {})

        # Default isort configuration
        default_config = {
            "profile": "black",
            "multi_line_output": 3,
            "line_length": 88,
            "known_first_party": ["src"],
            "known_third_party": ["PyQt6", "PIL", "folium", "pytest"],
        }

        # Merge with provided configuration
        merged_config = {**default_config, **config}

        # Try to load from pyproject.toml if it exists
        if self.pyproject_path.exists():
            try:
                # Try to use tomllib (Python 3.11+) or fall back to tomli
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        tomllib = None

                if tomllib:
                    with open(self.pyproject_path, "rb") as f:
                        pyproject_data = tomllib.load(f)

                    isort_config = pyproject_data.get("tool", {}).get("isort", {})
                    merged_config.update(isort_config)
                else:
                    self.logger.warning(
                        "tomllib/tomli not available, using default isort config"
                    )

            except Exception as e:
                self.logger.warning(
                    f"Failed to load isort config from pyproject.toml: {e}"
                )

        return merged_config

    def _load_flake8_config(self) -> Dict[str, Any]:
        """Load flake8 configuration or use defaults."""
        config = self.config.get("tools", {}).get("flake8", {})

        # Default flake8 configuration
        default_config = {
            "max_line_length": 88,
            "ignore": ["E203", "W503"],
            "exclude": [".git", "__pycache__", "build", "dist", ".venv", ".eggs"],
        }

        return {**default_config, **config}

    def _load_mypy_config(self) -> Dict[str, Any]:
        """Load mypy configuration from pyproject.toml or use defaults."""
        config = self.config.get("tools", {}).get("mypy", {})

        # Default mypy configuration
        default_config = {
            "python_version": "3.9",
            "warn_return_any": True,
            "warn_unused_configs": True,
            "disallow_untyped_defs": True,
            "disallow_incomplete_defs": True,
            "check_untyped_defs": True,
            "no_implicit_optional": True,
            "warn_redundant_casts": True,
            "warn_unused_ignores": True,
            "strict_equality": True,
        }

        # Merge with provided configuration
        merged_config = {**default_config, **config}

        # Try to load from pyproject.toml if it exists
        if self.pyproject_path.exists():
            try:
                # Try to use tomllib (Python 3.11+) or fall back to tomli
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        tomllib = None

                if tomllib:
                    with open(self.pyproject_path, "rb") as f:
                        pyproject_data = tomllib.load(f)

                    mypy_config = pyproject_data.get("tool", {}).get("mypy", {})
                    merged_config.update(mypy_config)
                else:
                    self.logger.warning(
                        "tomllib/tomli not available, using default mypy config"
                    )

            except Exception as e:
                self.logger.warning(
                    f"Failed to load mypy config from pyproject.toml: {e}"
                )

        return merged_config

    def run_check(self, **kwargs) -> CheckResult:
        """
        Execute all code quality checks.

        Args:
            **kwargs: Additional arguments including:
                - auto_fix: Whether to automatically fix issues
                - check_types: List of specific checks to run

        Returns:
            CheckResult containing the outcome of all quality checks
        """
        start_time = time.time()
        auto_fix = kwargs.get("auto_fix", self.config.get("auto_fix", False))
        check_types = kwargs.get("check_types", ["black", "isort", "flake8", "mypy"])

        self.logger.info("Starting code quality checks")

        all_results = {}
        overall_status = CheckStatus.SUCCESS
        all_errors = []
        all_warnings = []
        all_suggestions = []
        combined_output = []

        # Run individual checks
        if "black" in check_types:
            black_result = self.run_black(auto_fix=auto_fix)
            all_results["black"] = black_result
            combined_output.append(f"=== Black Formatter ===\n{black_result.output}")

            if black_result.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                black_result.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(black_result.errors)
            all_warnings.extend(black_result.warnings)
            all_suggestions.extend(black_result.suggestions)

        if "isort" in check_types:
            isort_result = self.run_isort(auto_fix=auto_fix)
            all_results["isort"] = isort_result
            combined_output.append(
                f"=== isort Import Sorter ===\n{isort_result.output}"
            )

            if isort_result.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                isort_result.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(isort_result.errors)
            all_warnings.extend(isort_result.warnings)
            all_suggestions.extend(isort_result.suggestions)

        if "flake8" in check_types:
            flake8_result = self.run_flake8()
            all_results["flake8"] = flake8_result
            combined_output.append(
                f"=== flake8 Style Checker ===\n{flake8_result.output}"
            )

            if flake8_result.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                flake8_result.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(flake8_result.errors)
            all_warnings.extend(flake8_result.warnings)
            all_suggestions.extend(flake8_result.suggestions)

        if "mypy" in check_types:
            mypy_result = self.run_mypy()
            all_results["mypy"] = mypy_result
            combined_output.append(f"=== mypy Type Checker ===\n{mypy_result.output}")

            if mypy_result.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                mypy_result.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(mypy_result.errors)
            all_warnings.extend(mypy_result.warnings)
            all_suggestions.extend(mypy_result.suggestions)

        duration = time.time() - start_time

        return CheckResult(
            name=self.name,
            status=overall_status,
            duration=duration,
            output="\n\n".join(combined_output),
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metadata={
                "individual_results": {
                    name: result.to_dict() for name, result in all_results.items()
                },
                "auto_fix_enabled": auto_fix,
                "checks_run": check_types,
                "configuration": {
                    "black": self.black_config,
                    "isort": self.isort_config,
                    "flake8": self.flake8_config,
                    "mypy": self.mypy_config,
                },
            },
        )

    def run_black(self, auto_fix: bool = False) -> CheckResult:
        """
        Run Black formatter check with optional auto-fix.

        Args:
            auto_fix: Whether to automatically fix formatting issues

        Returns:
            CheckResult containing Black formatter results
        """
        start_time = time.time()
        self.logger.info(f"Running Black formatter (auto_fix={auto_fix})")

        # Build Black command
        cmd = [sys.executable, "-m", "black"]

        # Add configuration options
        if "line_length" in self.black_config:
            cmd.extend(["--line-length", str(self.black_config["line_length"])])

        if "target_version" in self.black_config:
            for version in self.black_config["target_version"]:
                cmd.extend(["--target-version", version])

        # Add check or fix mode
        if not auto_fix:
            cmd.append("--check")
            cmd.append("--diff")

        # Add source directories or current directory if none exist
        source_dirs = ["src", "tools", "tests"]
        existing_dirs = [d for d in source_dirs if Path(d).exists()]
        if existing_dirs:
            cmd.extend(existing_dirs)
        else:
            # If no standard directories exist, check current directory for Python files
            cmd.append(".")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=self.project_root,
            )

            duration = time.time() - start_time

            # Parse Black output
            issues = self._parse_black_output(result.stdout, result.stderr)

            if result.returncode == 0:
                status = CheckStatus.SUCCESS
                errors = []
                warnings = []
                suggestions = ["Code formatting is compliant with Black standards"]
                output = "✅ All files are properly formatted with Black"

            elif result.returncode == 1 or result.returncode == 123:
                # Black found formatting issues (exit code 1 for --check, 123 for syntax errors)
                if auto_fix and result.returncode == 1:
                    status = CheckStatus.SUCCESS
                    errors = []
                    warnings = [f"Fixed {len(issues)} formatting issues"]
                    suggestions = ["Files have been automatically formatted"]
                    output = (
                        f"🔧 Fixed {len(issues)} formatting issues:\n{result.stdout}"
                    )
                elif result.returncode == 123:
                    # Syntax error in one or more files
                    status = CheckStatus.FAILURE
                    errors = [f"Found syntax errors preventing formatting"]
                    if result.stderr:
                        errors.append(f"Error details: {result.stderr}")
                    warnings = []
                    suggestions = ["Fix syntax errors in the reported files before running Black"]
                    output = f"❌ Syntax errors found:\n{result.stderr}"
                else:
                    status = CheckStatus.FAILURE
                    errors = [f"Found {len(issues)} formatting issues"]
                    warnings = []
                    suggestions = [
                        "Run with auto_fix=True to automatically fix formatting issues"
                    ]
                    output = f"❌ Found formatting issues:\n{result.stdout}"
            else:
                # Black encountered an error
                status = CheckStatus.FAILURE
                errors = [f"Black failed with exit code {result.returncode}"]
                if result.stderr:
                    errors.append(f"Error output: {result.stderr}")
                warnings = []
                suggestions = [
                    "Check Black configuration and ensure all files are valid Python"
                ]
                output = f"❌ Black execution failed:\n{result.stderr}"

            return CheckResult(
                name="Black Formatter",
                status=status,
                duration=duration,
                output=output,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "issues_found": len(issues),
                    "auto_fix_applied": auto_fix and result.returncode == 1,
                    "command": " ".join(cmd),
                    "configuration": self.black_config,
                    "issues": [issue.__dict__ for issue in issues],
                },
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CheckResult(
                name="Black Formatter",
                status=CheckStatus.FAILURE,
                duration=duration,
                output="❌ Black execution timed out",
                errors=["Black execution timed out after 5 minutes"],
                warnings=[],
                suggestions=[
                    "Check for very large files or infinite loops in Black processing"
                ],
                metadata={"timeout": True, "command": " ".join(cmd)},
            )

        except Exception as e:
            duration = time.time() - start_time
            return CheckResult(
                name="Black Formatter",
                status=CheckStatus.FAILURE,
                duration=duration,
                output=f"❌ Black execution failed: {str(e)}",
                errors=[f"Failed to execute Black: {str(e)}"],
                warnings=[],
                suggestions=["Ensure Black is properly installed and accessible"],
                metadata={"exception": str(e), "command": " ".join(cmd)},
            )

    def _parse_black_output(self, stdout: str, stderr: str) -> List[QualityIssue]:
        """
        Parse Black output to extract formatting issues.

        Args:
            stdout: Standard output from Black
            stderr: Standard error from Black

        Returns:
            List of QualityIssue objects representing formatting problems
        """
        issues = []

        # Parse diff output for file changes
        if stdout:
            current_file = None
            for line in stdout.split("\n"):
                # Look for file headers in diff output
                if line.startswith("---") or line.startswith("+++"):
                    # Extract filename from diff header
                    match = re.search(r"[+-]{3}\s+(.+?)\s+\d{4}-\d{2}-\d{2}", line)
                    if match:
                        current_file = match.group(1)
                elif line.startswith("@@") and current_file:
                    # Extract line number from diff hunk header
                    match = re.search(r"@@\s+-(\d+),?\d*\s+\+(\d+),?\d*\s+@@", line)
                    if match:
                        line_num = int(match.group(2))
                        issues.append(
                            QualityIssue(
                                file_path=current_file,
                                line_number=line_num,
                                column=None,
                                rule_code="BLACK001",
                                message="Formatting required",
                                severity="error",
                                tool="black",
                            )
                        )

        # Parse error messages from stderr
        if stderr:
            for line in stderr.split("\n"):
                if line.strip():
                    issues.append(
                        QualityIssue(
                            file_path="unknown",
                            line_number=0,
                            column=None,
                            rule_code="BLACK_ERROR",
                            message=line.strip(),
                            severity="error",
                            tool="black",
                        )
                    )

        return issues

    def get_black_status(self) -> Dict[str, Any]:
        """
        Get current Black configuration and status.

        Returns:
            Dictionary containing Black status information
        """
        return {
            "available": self._is_tool_available("black"),
            "configuration": self.black_config,
            "config_source": (
                "pyproject.toml" if self.pyproject_path.exists() else "defaults"
            ),
        }

    def run_isort(self, auto_fix: bool = False) -> CheckResult:
        """
        Run isort import sorting check with optional auto-fix.

        Args:
            auto_fix: Whether to automatically fix import sorting issues

        Returns:
            CheckResult containing isort results
        """
        start_time = time.time()
        self.logger.info(f"Running isort import sorter (auto_fix={auto_fix})")

        # Build isort command
        cmd = [sys.executable, "-m", "isort"]

        # Add configuration options
        if "line_length" in self.isort_config:
            cmd.extend(["--line-length", str(self.isort_config["line_length"])])

        if "profile" in self.isort_config:
            cmd.extend(["--profile", self.isort_config["profile"]])

        # Add check or fix mode
        if not auto_fix:
            cmd.append("--check-only")
            cmd.append("--diff")

        # Add source directories
        source_dirs = ["src", "tools", "tests"]
        existing_dirs = [d for d in source_dirs if Path(d).exists()]
        cmd.extend(existing_dirs)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=self.project_root,
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                status = CheckStatus.SUCCESS
                errors = []
                warnings = []
                suggestions = ["Import sorting is compliant with isort standards"]
                output = "✅ All imports are properly sorted with isort"

            elif result.returncode == 1:
                # isort found sorting issues
                if auto_fix:
                    status = CheckStatus.SUCCESS
                    errors = []
                    warnings = ["Fixed import sorting issues"]
                    suggestions = ["Imports have been automatically sorted"]
                    output = f"🔧 Fixed import sorting issues:\n{result.stdout}"
                else:
                    status = CheckStatus.FAILURE
                    errors = ["Found import sorting issues"]
                    warnings = []
                    suggestions = [
                        "Run with auto_fix=True to automatically fix import sorting"
                    ]
                    output = f"❌ Found import sorting issues:\n{result.stdout}"
            else:
                # isort encountered an error
                status = CheckStatus.FAILURE
                errors = [f"isort failed with exit code {result.returncode}"]
                if result.stderr:
                    errors.append(f"Error output: {result.stderr}")
                warnings = []
                suggestions = [
                    "Check isort configuration and ensure all files are valid Python"
                ]
                output = f"❌ isort execution failed:\n{result.stderr}"

            return CheckResult(
                name="isort Import Sorter",
                status=status,
                duration=duration,
                output=output,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "auto_fix_applied": auto_fix and result.returncode == 1,
                    "command": " ".join(cmd),
                    "configuration": self.isort_config,
                },
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CheckResult(
                name="isort Import Sorter",
                status=CheckStatus.FAILURE,
                duration=duration,
                output="❌ isort execution timed out",
                errors=["isort execution timed out after 5 minutes"],
                warnings=[],
                suggestions=[
                    "Check for very large files or infinite loops in isort processing"
                ],
                metadata={"timeout": True, "command": " ".join(cmd)},
            )

        except Exception as e:
            duration = time.time() - start_time
            return CheckResult(
                name="isort Import Sorter",
                status=CheckStatus.FAILURE,
                duration=duration,
                output=f"❌ isort execution failed: {str(e)}",
                errors=[f"Failed to execute isort: {str(e)}"],
                warnings=[],
                suggestions=["Ensure isort is properly installed and accessible"],
                metadata={"exception": str(e), "command": " ".join(cmd)},
            )

    def run_flake8(self) -> CheckResult:
        """
        Run flake8 style checker.

        Returns:
            CheckResult containing flake8 results
        """
        start_time = time.time()
        self.logger.info("Running flake8 style checker")

        # Build flake8 command
        cmd = [sys.executable, "-m", "flake8"]

        # Add configuration options
        if "max_line_length" in self.flake8_config:
            cmd.extend(
                ["--max-line-length", str(self.flake8_config["max_line_length"])]
            )

        if "ignore" in self.flake8_config:
            ignore_codes = ",".join(self.flake8_config["ignore"])
            cmd.extend(["--ignore", ignore_codes])

        # Add source directories
        source_dirs = ["src", "tools", "tests"]
        existing_dirs = [d for d in source_dirs if Path(d).exists()]
        cmd.extend(existing_dirs)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=self.project_root,
            )

            duration = time.time() - start_time
            issues = self._parse_flake8_output(result.stdout)

            if result.returncode == 0:
                status = CheckStatus.SUCCESS
                errors = []
                warnings = []
                suggestions = ["Code style is compliant with flake8 standards"]
                output = "✅ No style violations found by flake8"

            else:
                status = CheckStatus.FAILURE
                errors = [f"Found {len(issues)} style violations"]
                warnings = []
                suggestions = [
                    "Fix the reported style violations to improve code quality"
                ]
                output = f"❌ Found {len(issues)} style violations:\n{result.stdout}"

            return CheckResult(
                name="flake8 Style Checker",
                status=status,
                duration=duration,
                output=output,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "violations_found": len(issues),
                    "command": " ".join(cmd),
                    "configuration": self.flake8_config,
                    "issues": [issue.__dict__ for issue in issues],
                },
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CheckResult(
                name="flake8 Style Checker",
                status=CheckStatus.FAILURE,
                duration=duration,
                output="❌ flake8 execution timed out",
                errors=["flake8 execution timed out after 5 minutes"],
                warnings=[],
                suggestions=[
                    "Check for very large files or infinite loops in flake8 processing"
                ],
                metadata={"timeout": True, "command": " ".join(cmd)},
            )

        except Exception as e:
            duration = time.time() - start_time
            return CheckResult(
                name="flake8 Style Checker",
                status=CheckStatus.FAILURE,
                duration=duration,
                output=f"❌ flake8 execution failed: {str(e)}",
                errors=[f"Failed to execute flake8: {str(e)}"],
                warnings=[],
                suggestions=["Ensure flake8 is properly installed and accessible"],
                metadata={"exception": str(e), "command": " ".join(cmd)},
            )

    def run_mypy(self) -> CheckResult:
        """
        Run mypy type checker.

        Returns:
            CheckResult containing mypy results
        """
        start_time = time.time()
        self.logger.info("Running mypy type checker")

        # Build mypy command
        cmd = [sys.executable, "-m", "mypy"]

        # Add configuration options
        if "python_version" in self.mypy_config:
            cmd.extend(["--python-version", self.mypy_config["python_version"]])

        # Add boolean flags
        bool_flags = [
            "warn_return_any",
            "warn_unused_configs",
            "disallow_untyped_defs",
            "disallow_incomplete_defs",
            "check_untyped_defs",
            "no_implicit_optional",
            "warn_redundant_casts",
            "warn_unused_ignores",
            "strict_equality",
        ]

        for flag in bool_flags:
            if self.mypy_config.get(flag, False):
                cmd.append(f"--{flag.replace('_', '-')}")

        # Add source directories
        source_dirs = ["src", "tools"]
        existing_dirs = [d for d in source_dirs if Path(d).exists()]
        cmd.extend(existing_dirs)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=self.project_root,
            )

            duration = time.time() - start_time
            issues = self._parse_mypy_output(result.stdout)

            if result.returncode == 0:
                status = CheckStatus.SUCCESS
                errors = []
                warnings = []
                suggestions = ["Type annotations are compliant with mypy standards"]
                output = "✅ No type errors found by mypy"

            else:
                status = CheckStatus.FAILURE
                errors = [f"Found {len(issues)} type errors"]
                warnings = []
                suggestions = ["Fix the reported type errors to improve code safety"]
                output = f"❌ Found {len(issues)} type errors:\n{result.stdout}"

            return CheckResult(
                name="mypy Type Checker",
                status=status,
                duration=duration,
                output=output,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                metadata={
                    "type_errors_found": len(issues),
                    "command": " ".join(cmd),
                    "configuration": self.mypy_config,
                    "issues": [issue.__dict__ for issue in issues],
                },
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CheckResult(
                name="mypy Type Checker",
                status=CheckStatus.FAILURE,
                duration=duration,
                output="❌ mypy execution timed out",
                errors=["mypy execution timed out after 5 minutes"],
                warnings=[],
                suggestions=[
                    "Check for very large files or infinite loops in mypy processing"
                ],
                metadata={"timeout": True, "command": " ".join(cmd)},
            )

        except Exception as e:
            duration = time.time() - start_time
            return CheckResult(
                name="mypy Type Checker",
                status=CheckStatus.FAILURE,
                duration=duration,
                output=f"❌ mypy execution failed: {str(e)}",
                errors=[f"Failed to execute mypy: {str(e)}"],
                warnings=[],
                suggestions=["Ensure mypy is properly installed and accessible"],
                metadata={"exception": str(e), "command": " ".join(cmd)},
            )

    def _parse_flake8_output(self, output: str) -> List[QualityIssue]:
        """
        Parse flake8 output to extract style violations.

        Args:
            output: Standard output from flake8

        Returns:
            List of QualityIssue objects representing style violations
        """
        issues = []

        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            # flake8 output format: filename:line:column: error_code message
            match = re.match(r"^([^:]+):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$", line)
            if match:
                file_path, line_num, column, error_code, message = match.groups()
                issues.append(
                    QualityIssue(
                        file_path=file_path,
                        line_number=int(line_num),
                        column=int(column),
                        rule_code=error_code,
                        message=message.strip(),
                        severity="error",
                        tool="flake8",
                    )
                )

        return issues

    def _parse_mypy_output(self, output: str) -> List[QualityIssue]:
        """
        Parse mypy output to extract type errors.

        Args:
            output: Standard output from mypy

        Returns:
            List of QualityIssue objects representing type errors
        """
        issues = []

        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            # mypy output format: filename:line: error: message
            match = re.match(r"^([^:]+):(\d+):\s+(error|warning|note):\s+(.+)$", line)
            if match:
                file_path, line_num, severity, message = match.groups()
                issues.append(
                    QualityIssue(
                        file_path=file_path,
                        line_number=int(line_num),
                        column=None,
                        rule_code="MYPY",
                        message=message.strip(),
                        severity=severity,
                        tool="mypy",
                    )
                )

        return issues

    def run_all_quality_checks(self, auto_fix: bool = False) -> Dict[str, CheckResult]:
        """
        Run all code quality checks.

        Args:
            auto_fix: Whether to automatically fix issues where possible

        Returns:
            Dictionary mapping check names to their results
        """
        results = {}

        # Run Black formatter
        results["black"] = self.run_black(auto_fix=auto_fix)

        # Run isort import sorter
        results["isort"] = self.run_isort(auto_fix=auto_fix)

        # Run flake8 style checker
        results["flake8"] = self.run_flake8()

        # Run mypy type checker
        results["mypy"] = self.run_mypy()

        return results
