"""
AI Component Tester for CI Simulation Tool

This module implements comprehensive AI component testing for Copilot, Cursor, and Kiro
components with demo script testing, AI compatibility verification, and integration testing.
"""

import subprocess
import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..interfaces import CheckerInterface
from ..models import CheckResult, CheckStatus, ConfigDict


@dataclass
class AIComponentInfo:
    """Information about an AI component."""

    name: str
    focus_area: str
    demo_scripts: List[str]
    test_files: List[str]
    config_files: List[str]
    dependencies: List[str]


@dataclass
class DemoTestResult:
    """Result of a demo script test."""

    script_name: str
    component: str
    status: str
    duration: float
    output: str
    error_message: Optional[str] = None


class AIComponentTester(CheckerInterface):
    """
    Comprehensive AI component tester for Copilot, Cursor, and Kiro.

    This checker provides:
    - AI-specific test execution (Copilot, Cursor, Kiro components)
    - Demo script testing functionality
    - AI compatibility verification
    - Integration testing between AI components
    """

    def __init__(self, config: ConfigDict):
        """
        Initialize the AI component tester.

        Args:
            config: Configuration dictionary containing AI testing settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()

        # Define AI components based on the AI integration guidelines
        self.ai_components = self._define_ai_components()

        # Load AI testing configuration
        self.ai_config = self._load_ai_config()

    @property
    def name(self) -> str:
        """Return the human-readable name of this checker."""
        return "AI Component Tester"

    @property
    def check_type(self) -> str:
        """Return the type category of this checker."""
        return "ai_testing"

    @property
    def dependencies(self) -> List[str]:
        """Return list of external dependencies required by this checker."""
        return ["pytest", "pytest-asyncio", "pytest-qt"]

    def _define_ai_components(self) -> Dict[str, AIComponentInfo]:
        """
        Define AI components based on the project structure.

        Returns:
            Dictionary mapping component names to their information
        """
        return {
            "copilot": AIComponentInfo(
                name="GitHub Copilot (CS4Coding)",
                focus_area="core_functionality",
                demo_scripts=[
                    "examples/demo_image_processor.py",
                    "examples/demo_config_manager.py",
                ],
                test_files=[
                    "tests/test_image_processor.py",
                    "tests/test_config_manager.py",
                    "tests/test_data_validation.py",
                ],
                config_files=[
                    "config/copilot_config.json",
                ],
                dependencies=["PyQt6", "Pillow", "piexif"],
            ),
            "cursor": AIComponentInfo(
                name="Cursor (CursorBLD)",
                focus_area="ui_ux",
                demo_scripts=[
                    "examples/demo_kiro_components.py",
                ],
                test_files=[
                    "tests/test_file_list_display_integration.py",
                    "tests/test_file_list_display_performance.py",
                    "tests/test_file_list_display_error_handling.py",
                ],
                config_files=[
                    "config/cursor_config.json",
                ],
                dependencies=["PyQt6", "PyQt6-WebEngine"],
            ),
            "kiro": AIComponentInfo(
                name="Kiro",
                focus_area="integration",
                demo_scripts=[
                    "examples/demo_kiro_integration.py",
                    "examples/demo_data_validation_migration.py",
                ],
                test_files=[
                    "tests/test_kiro_components.py",
                    "tests/ai_integration_test_suite.py",
                    "tests/test_final_integration_verification.py",
                ],
                config_files=[
                    "config/kiro_config.json",
                ],
                dependencies=["asyncio", "concurrent.futures"],
            ),
        }

    def _load_ai_config(self) -> Dict[str, Any]:
        """Load AI testing configuration."""
        config = self.config.get("ai_testing", {})

        # Default AI testing configuration
        default_config = {
            "timeout": 300,  # 5 minutes per component test
            "parallel_execution": True,
            "demo_script_timeout": 60,  # 1 minute per demo script
            "compatibility_checks": True,
            "integration_tests": True,
            "performance_benchmarks": False,  # Disabled by default for AI tests
        }

        return {**default_config, **config}

    def is_available(self) -> bool:
        """
        Check if AI testing dependencies are available.

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
            self.logger.warning(f"Missing AI testing tools: {missing_tools}")
            self._is_available = False
        else:
            self._is_available = True

        return self._is_available

    def _is_tool_available(self, tool: str) -> bool:
        """Check if a specific tool is available in the environment."""
        try:
            if tool == "pytest":
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            else:
                # For other tools, try to import them
                result = subprocess.run(
                    [sys.executable, "-c", f"import {tool.replace('-', '_')}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def run_check(self, **kwargs) -> CheckResult:
        """
        Execute comprehensive AI component testing.

        Args:
            **kwargs: Additional arguments including:
                - components: List of AI components to test
                - include_demos: Whether to run demo scripts
                - include_compatibility: Whether to run compatibility tests

        Returns:
            CheckResult containing the outcome of all AI component tests
        """
        start_time = time.time()
        components = kwargs.get("components", ["copilot", "cursor", "kiro"])
        include_demos = kwargs.get("include_demos", True)
        include_compatibility = kwargs.get("include_compatibility", True)

        self.logger.info(f"Starting AI component testing for: {components}")

        all_results = {}
        overall_status = CheckStatus.SUCCESS
        all_errors = []
        all_warnings = []
        all_suggestions = []
        combined_output = []

        # Test individual AI components
        for component in components:
            if component not in self.ai_components:
                self.logger.warning(f"Unknown AI component: {component}")
                continue

            component_result = self._test_ai_component(component, include_demos)
            all_results[component] = component_result
            combined_output.append(f"=== {component.title()} Component Tests ===\n{component_result.output}")

            if component_result.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                component_result.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(component_result.errors)
            all_warnings.extend(component_result.warnings)
            all_suggestions.extend(component_result.suggestions)

        # Run compatibility tests if requested
        if include_compatibility and len(components) > 1:
            compatibility_result = self._test_ai_compatibility(components)
            all_results["compatibility"] = compatibility_result
            combined_output.append(f"=== AI Compatibility Tests ===\n{compatibility_result.output}")

            if compatibility_result.status == CheckStatus.FAILURE:
                overall_status = CheckStatus.FAILURE
            elif (
                compatibility_result.status == CheckStatus.WARNING
                and overall_status == CheckStatus.SUCCESS
            ):
                overall_status = CheckStatus.WARNING

            all_errors.extend(compatibility_result.errors)
            all_warnings.extend(compatibility_result.warnings)
            all_suggestions.extend(compatibility_result.suggestions)

        duration = time.time() - start_time

        # Generate summary
        total_tests = sum(
            result.metadata.get("tests_run", 0)
            for result in all_results.values()
        )
        passed_tests = sum(
            result.metadata.get("tests_passed", 0)
            for result in all_results.values()
        )
        failed_tests = sum(
            result.metadata.get("tests_failed", 0)
            for result in all_results.values()
        )

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
                "components_tested": components,
                "total_tests": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
                "demos_included": include_demos,
                "compatibility_tested": include_compatibility,
                "configuration": self.ai_config,
            },
        )

    def _test_ai_component(self, component: str, include_demos: bool = True) -> CheckResult:
        """
        Test a specific AI component.

        Args:
            component: Name of the AI component to test
            include_demos: Whether to include demo script tests

        Returns:
            CheckResult containing the component test results
        """
        start_time = time.time()
        component_info = self.ai_components[component]

        self.logger.info(f"Testing {component_info.name}")

        test_results = []
        demo_results = []
        errors = []
        warnings = []
        suggestions = []

        # Run component-specific tests
        if component_info.test_files:
            test_results = self._run_component_tests(component, component_info.test_files)

        # Run demo scripts if requested
        if include_demos and component_info.demo_scripts:
            demo_results = self._run_demo_scripts(component, component_info.demo_scripts)

        # Analyze results
        total_tests = len(test_results) + len(demo_results)
        passed_tests = sum(1 for r in test_results + demo_results if r.status == "passed")
        failed_tests = sum(1 for r in test_results + demo_results if r.status == "failed")

        # Determine overall status
        if failed_tests > 0:
            status = CheckStatus.FAILURE
            errors.append(f"{failed_tests} out of {total_tests} tests failed for {component}")
        elif total_tests == 0:
            status = CheckStatus.WARNING
            warnings.append(f"No tests found for {component} component")
        else:
            status = CheckStatus.SUCCESS
            suggestions.append(f"All {component} component tests passed successfully")

        # Generate output
        output_lines = [f"Testing {component_info.name} ({component_info.focus_area})"]

        if test_results:
            output_lines.append(f"\nComponent Tests ({len(test_results)} tests):")
            for result in test_results:
                status_icon = "✅" if result.status == "passed" else "❌"
                output_lines.append(f"  {status_icon} {result.script_name}: {result.duration:.2f}s")
                if result.error_message:
                    output_lines.append(f"    Error: {result.error_message}")

        if demo_results:
            output_lines.append(f"\nDemo Scripts ({len(demo_results)} demos):")
            for result in demo_results:
                status_icon = "✅" if result.status == "passed" else "❌"
                output_lines.append(f"  {status_icon} {result.script_name}: {result.duration:.2f}s")
                if result.error_message:
                    output_lines.append(f"    Error: {result.error_message}")

        duration = time.time() - start_time

        return CheckResult(
            name=f"{component_info.name} Tests",
            status=status,
            duration=duration,
            output="\n".join(output_lines),
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata={
                "component": component,
                "focus_area": component_info.focus_area,
                "tests_run": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
                "test_results": [r.__dict__ for r in test_results],
                "demo_results": [r.__dict__ for r in demo_results],
                "dependencies_checked": self._check_component_dependencies(component_info),
            },
        )

    def _run_component_tests(self, component: str, test_files: List[str]) -> List[DemoTestResult]:
        """
        Run component-specific test files.

        Args:
            component: Name of the AI component
            test_files: List of test files to run

        Returns:
            List of test results
        """
        results = []

        for test_file in test_files:
            test_path = self.project_root / test_file
            if not test_path.exists():
                self.logger.warning(f"Test file not found: {test_file}")
                results.append(DemoTestResult(
                    script_name=test_file,
                    component=component,
                    status="skipped",
                    duration=0.0,
                    output="",
                    error_message=f"Test file not found: {test_file}"
                ))
                continue

            start_time = time.time()

            try:
                # Run pytest on the specific test file
                cmd = [
                    sys.executable, "-m", "pytest",
                    str(test_path),
                    "-v",
                    "--tb=short",
                    f"--timeout={self.ai_config['timeout']}"
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.ai_config["timeout"],
                    cwd=self.project_root,
                )

                duration = time.time() - start_time

                if result.returncode == 0:
                    status = "passed"
                    error_message = None
                else:
                    status = "failed"
                    error_message = result.stderr or "Test execution failed"

                results.append(DemoTestResult(
                    script_name=test_file,
                    component=component,
                    status=status,
                    duration=duration,
                    output=result.stdout,
                    error_message=error_message
                ))

            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                results.append(DemoTestResult(
                    script_name=test_file,
                    component=component,
                    status="failed",
                    duration=duration,
                    output="",
                    error_message="Test execution timed out"
                ))

            except Exception as e:
                duration = time.time() - start_time
                results.append(DemoTestResult(
                    script_name=test_file,
                    component=component,
                    status="failed",
                    duration=duration,
                    output="",
                    error_message=str(e)
                ))

        return results

    def _run_demo_scripts(self, component: str, demo_scripts: List[str]) -> List[DemoTestResult]:
        """
        Run demo scripts for a component.

        Args:
            component: Name of the AI component
            demo_scripts: List of demo scripts to run

        Returns:
            List of demo test results
        """
        results = []

        for demo_script in demo_scripts:
            demo_path = self.project_root / demo_script
            if not demo_path.exists():
                self.logger.warning(f"Demo script not found: {demo_script}")
                results.append(DemoTestResult(
                    script_name=demo_script,
                    component=component,
                    status="skipped",
                    duration=0.0,
                    output="",
                    error_message=f"Demo script not found: {demo_script}"
                ))
                continue

            start_time = time.time()

            try:
                # Setup environment for demo execution
                env = os.environ.copy()
                env.update(self._setup_demo_environment())

                # Run the demo script
                cmd = [sys.executable, str(demo_path)]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.ai_config["demo_script_timeout"],
                    cwd=self.project_root,
                    env=env,
                )

                duration = time.time() - start_time

                if result.returncode == 0:
                    status = "passed"
                    error_message = None
                else:
                    status = "failed"
                    error_message = result.stderr or "Demo script execution failed"

                results.append(DemoTestResult(
                    script_name=demo_script,
                    component=component,
                    status=status,
                    duration=duration,
                    output=result.stdout,
                    error_message=error_message
                ))

            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                results.append(DemoTestResult(
                    script_name=demo_script,
                    component=component,
                    status="failed",
                    duration=duration,
                    output="",
                    error_message="Demo script execution timed out"
                ))

            except Exception as e:
                duration = time.time() - start_time
                results.append(DemoTestResult(
                    script_name=demo_script,
                    component=component,
                    status="failed",
                    duration=duration,
                    output="",
                    error_message=str(e)
                ))

        return results

    def _test_ai_compatibility(self, components: List[str]) -> CheckResult:
        """
        Test compatibility between AI components.

        Args:
            components: List of AI components to test compatibility for

        Returns:
            CheckResult containing compatibility test results
        """
        start_time = time.time()
        self.logger.info(f"Testing AI compatibility between: {components}")

        compatibility_tests = []
        errors = []
        warnings = []
        suggestions = []

        # Run the AI integration test suite if available
        integration_test_path = self.project_root / "tests" / "ai_integration_test_suite.py"
        if integration_test_path.exists():
            compatibility_result = self._run_integration_test_suite()
            compatibility_tests.append(compatibility_result)
        else:
            warnings.append("AI integration test suite not found")

        # Test configuration compatibility
        config_compatibility = self._test_config_compatibility(components)
        compatibility_tests.extend(config_compatibility)

        # Test dependency compatibility
        dependency_compatibility = self._test_dependency_compatibility(components)
        compatibility_tests.extend(dependency_compatibility)

        # Analyze results
        total_tests = len(compatibility_tests)
        passed_tests = sum(1 for r in compatibility_tests if r.status == "passed")
        failed_tests = sum(1 for r in compatibility_tests if r.status == "failed")

        # Determine overall status
        if failed_tests > 0:
            status = CheckStatus.FAILURE
            errors.append(f"{failed_tests} out of {total_tests} compatibility tests failed")
        elif total_tests == 0:
            status = CheckStatus.WARNING
            warnings.append("No compatibility tests were run")
        else:
            status = CheckStatus.SUCCESS
            suggestions.append("All AI compatibility tests passed")

        # Generate output
        output_lines = [f"AI Compatibility Testing ({len(components)} components)"]
        output_lines.append(f"Components: {', '.join(components)}")

        if compatibility_tests:
            output_lines.append(f"\nCompatibility Tests ({len(compatibility_tests)} tests):")
            for result in compatibility_tests:
                status_icon = "✅" if result.status == "passed" else "❌"
                output_lines.append(f"  {status_icon} {result.script_name}: {result.duration:.2f}s")
                if result.error_message:
                    output_lines.append(f"    Error: {result.error_message}")

        duration = time.time() - start_time

        return CheckResult(
            name="AI Compatibility Tests",
            status=status,
            duration=duration,
            output="\n".join(output_lines),
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata={
                "components_tested": components,
                "tests_run": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": failed_tests,
                "compatibility_results": [r.__dict__ for r in compatibility_tests],
            },
        )

    def _run_integration_test_suite(self) -> DemoTestResult:
        """
        Run the AI integration test suite.

        Returns:
            DemoTestResult containing the integration test results
        """
        start_time = time.time()

        try:
            # Setup environment for integration tests
            env = os.environ.copy()
            env.update(self._setup_demo_environment())

            # Run the integration test suite
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/ai_integration_test_suite.py",
                "-v",
                "--tb=short",
                f"--timeout={self.ai_config['timeout']}"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.ai_config["timeout"],
                cwd=self.project_root,
                env=env,
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                status = "passed"
                error_message = None
            else:
                status = "failed"
                error_message = result.stderr or "Integration test suite failed"

            return DemoTestResult(
                script_name="ai_integration_test_suite.py",
                component="integration",
                status=status,
                duration=duration,
                output=result.stdout,
                error_message=error_message
            )

        except Exception as e:
            duration = time.time() - start_time
            return DemoTestResult(
                script_name="ai_integration_test_suite.py",
                component="integration",
                status="failed",
                duration=duration,
                output="",
                error_message=str(e)
            )

    def _test_config_compatibility(self, components: List[str]) -> List[DemoTestResult]:
        """
        Test configuration compatibility between AI components.

        Args:
            components: List of AI components to test

        Returns:
            List of configuration compatibility test results
        """
        results = []
        start_time = time.time()

        try:
            # Check if all component config files exist and are valid
            for component in components:
                component_info = self.ai_components[component]

                for config_file in component_info.config_files:
                    config_path = self.project_root / config_file

                    if not config_path.exists():
                        results.append(DemoTestResult(
                            script_name=f"config_check_{component}",
                            component=component,
                            status="failed",
                            duration=0.0,
                            output="",
                            error_message=f"Config file not found: {config_file}"
                        ))
                        continue

                    # Try to load and validate the config file
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            json.load(f)  # Validate JSON format

                        results.append(DemoTestResult(
                            script_name=f"config_check_{component}",
                            component=component,
                            status="passed",
                            duration=time.time() - start_time,
                            output=f"Config file valid: {config_file}",
                            error_message=None
                        ))

                    except json.JSONDecodeError as e:
                        results.append(DemoTestResult(
                            script_name=f"config_check_{component}",
                            component=component,
                            status="failed",
                            duration=time.time() - start_time,
                            output="",
                            error_message=f"Invalid JSON in {config_file}: {str(e)}"
                        ))

        except Exception as e:
            results.append(DemoTestResult(
                script_name="config_compatibility_test",
                component="compatibility",
                status="failed",
                duration=time.time() - start_time,
                output="",
                error_message=str(e)
            ))

        return results

    def _test_dependency_compatibility(self, components: List[str]) -> List[DemoTestResult]:
        """
        Test dependency compatibility between AI components.

        Args:
            components: List of AI components to test

        Returns:
            List of dependency compatibility test results
        """
        results = []
        start_time = time.time()

        try:
            # Collect all dependencies from all components
            all_dependencies = set()
            for component in components:
                component_info = self.ai_components[component]
                all_dependencies.update(component_info.dependencies)

            # Test each dependency
            for dependency in all_dependencies:
                try:
                    result = subprocess.run(
                        [sys.executable, "-c", f"import {dependency.replace('-', '_')}"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if result.returncode == 0:
                        results.append(DemoTestResult(
                            script_name=f"dependency_check_{dependency}",
                            component="compatibility",
                            status="passed",
                            duration=time.time() - start_time,
                            output=f"Dependency available: {dependency}",
                            error_message=None
                        ))
                    else:
                        results.append(DemoTestResult(
                            script_name=f"dependency_check_{dependency}",
                            component="compatibility",
                            status="failed",
                            duration=time.time() - start_time,
                            output="",
                            error_message=f"Dependency not available: {dependency}"
                        ))

                except Exception as e:
                    results.append(DemoTestResult(
                        script_name=f"dependency_check_{dependency}",
                        component="compatibility",
                        status="failed",
                        duration=time.time() - start_time,
                        output="",
                        error_message=f"Error checking {dependency}: {str(e)}"
                    ))

        except Exception as e:
            results.append(DemoTestResult(
                script_name="dependency_compatibility_test",
                component="compatibility",
                status="failed",
                duration=time.time() - start_time,
                output="",
                error_message=str(e)
            ))

        return results

    def _check_component_dependencies(self, component_info: AIComponentInfo) -> Dict[str, bool]:
        """
        Check if component dependencies are available.

        Args:
            component_info: Information about the AI component

        Returns:
            Dictionary mapping dependency names to availability status
        """
        dependency_status = {}

        for dependency in component_info.dependencies:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", f"import {dependency.replace('-', '_')}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                dependency_status[dependency] = result.returncode == 0
            except Exception:
                dependency_status[dependency] = False

        return dependency_status

    def _setup_demo_environment(self) -> Dict[str, str]:
        """
        Setup environment variables for demo execution.

        Returns:
            Dictionary of environment variables
        """
        env_vars = {}

        # Setup Qt environment for headless execution
        env_vars.update({
            "QT_QPA_PLATFORM": "offscreen",
            "QT_LOGGING_RULES": "*.debug=false",
        })

        # Setup display for GUI tests if needed
        if os.environ.get("CI") is not None:
            env_vars["DISPLAY"] = ":99"

        return env_vars

    def get_ai_component_status(self) -> Dict[str, Any]:
        """
        Get current AI component status and configuration.

        Returns:
            Dictionary containing AI component status information
        """
        status = {}

        for component_name, component_info in self.ai_components.items():
            status[component_name] = {
                "name": component_info.name,
                "focus_area": component_info.focus_area,
                "demo_scripts_available": len([
                    script for script in component_info.demo_scripts
                    if (self.project_root / script).exists()
                ]),
                "test_files_available": len([
                    test_file for test_file in component_info.test_files
                    if (self.project_root / test_file).exists()
                ]),
                "config_files_available": len([
                    config_file for config_file in component_info.config_files
                    if (self.project_root / config_file).exists()
                ]),
                "dependencies_available": self._check_component_dependencies(component_info),
            }

        return {
            "components": status,
            "configuration": self.ai_config,
            "dependencies_available": {
                dep: self._is_tool_available(dep) for dep in self.dependencies
            },
        }

    def cleanup(self) -> None:
        """Clean up any temporary files or resources."""
        # Clean up any temporary test files or demo outputs
        temp_files = [
            "demo_state_export.json",
            "demo_performance_export.json",
        ]

        for temp_file in temp_files:
            temp_path = self.project_root / temp_file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to clean up {temp_file}: {e}")
