#!/usr/bin/env python3
"""
CI Simulator - Main CLI Interface

This module provides the main command-line interface for the CI/CD simulation tool.
It integrates all components and provides comprehensive functionality for running
CI checks locally before committing to the repository.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the tools/ci directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Try relative imports first (when used as module)
    from .check_orchestrator import CheckOrchestrator
    from .cli_parser import CLIParser
    from .config_manager import ConfigManager
    from .git_hook_manager import GitHookManager
    from .interfaces import CheckerFactory
    from .models import CheckStatus, CheckTask, SimulationResult
except ImportError:
    # Fall back to absolute imports (when run directly)
    from check_orchestrator import CheckOrchestrator
    from cli_parser import CLIParser
    from config_manager import ConfigManager
    from git_hook_manager import GitHookManager
    from interfaces import CheckerFactory
    from models import CheckStatus, CheckTask, SimulationResult


class CISimulator:
    """
    Main CI Simulator class that provides the primary interface for running
    CI/CD simulation checks locally.

    This class integrates all components of the CI simulation system:
    - Configuration management
    - Check orchestration
    - CLI argument parsing
    - Report generation
    - Git hook integration
    """

    VERSION = "1.0.0"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the CI Simulator.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.logger = self._setup_logging()

        # Initialize directories
        self._ensure_directories()

        # Register available checkers BEFORE initializing orchestrator
        self._register_checkers()

        # Initialize components that depend on registered checkers
        self.orchestrator = CheckOrchestrator(self.config)
        self.cli_parser = CLIParser(self.orchestrator)
        self.git_hook_manager = GitHookManager(self.config)

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger("ci_simulator")

        # Create logs directory if it doesn't exist
        logs_dir = Path(self.config.get("directories", {}).get("logs", "logs"))
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        log_level = logging.INFO
        if self.config.get("verbose", False):
            log_level = logging.DEBUG
        elif self.config.get("quiet", False):
            log_level = logging.WARNING

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(logs_dir / "ci-simulation.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )

        return logger

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = self.config.get("directories", {})

        for dir_type, dir_path in directories.items():
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {path}")

    def _register_checkers(self) -> None:
        """Register all available checker types."""
        # Import and register checker implementations
        try:
            # Try relative imports first (when used as module)
            try:
                from .checkers.code_quality import CodeQualityChecker
            except ImportError:
                from checkers.code_quality import CodeQualityChecker
            CheckerFactory.register_checker("code_quality", CodeQualityChecker)
        except ImportError as e:
            self.logger.warning(f"Code quality checker not available: {e}")

        try:
            try:
                from .checkers.test_runner import TestRunner
            except ImportError:
                from checkers.test_runner import TestRunner
            CheckerFactory.register_checker("test_runner", TestRunner)
        except ImportError as e:
            self.logger.warning(f"Test runner not available: {e}")

        try:
            try:
                from .checkers.security_scanner import SecurityScanner
            except ImportError:
                from checkers.security_scanner import SecurityScanner
            CheckerFactory.register_checker("security_scanner", SecurityScanner)
        except ImportError as e:
            self.logger.warning(f"Security scanner not available: {e}")

        try:
            try:
                from .checkers.performance_analyzer import PerformanceAnalyzer
            except ImportError:
                from checkers.performance_analyzer import PerformanceAnalyzer
            CheckerFactory.register_checker("performance_analyzer", PerformanceAnalyzer)
        except ImportError as e:
            self.logger.warning(f"Performance analyzer not available: {e}")

        try:
            try:
                from .checkers.ai_component_tester import AIComponentTester
            except ImportError:
                from checkers.ai_component_tester import AIComponentTester
            CheckerFactory.register_checker("ai_component_tester", AIComponentTester)
        except ImportError as e:
            self.logger.warning(f"AI component tester not available: {e}")

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Main entry point for running the CI simulator.

        Args:
            args: Command line arguments (default: sys.argv)

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Parse command line arguments
            parsed_args = self.cli_parser.parse_args(args)

            # Validate arguments
            validation_errors = self.cli_parser.validate_args(parsed_args)
            if validation_errors:
                for error in validation_errors:
                    self.logger.error(error)
                return 1

            # Execute the appropriate command
            if parsed_args.command == "run":
                return self._run_checks(parsed_args)
            elif parsed_args.command == "list":
                return self._list_checks(parsed_args)
            elif parsed_args.command == "info":
                return self._show_check_info(parsed_args)
            elif parsed_args.command == "plan":
                return self._show_execution_plan(parsed_args)
            elif parsed_args.command == "hook":
                return self._handle_hook_command(parsed_args)
            else:
                self.logger.error(f"Unknown command: {parsed_args.command}")
                return 1

        except KeyboardInterrupt:
            self.logger.info("Execution interrupted by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if self.config.get("verbose", False):
                import traceback

                traceback.print_exc()
            return 1

    def _run_checks(self, args: argparse.Namespace) -> int:
        """
        Execute CI checks based on parsed arguments.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code
        """
        self.logger.info("Starting CI simulation...")
        start_time = time.time()

        try:
            # Create tasks from arguments
            tasks = self.cli_parser.create_tasks_from_args(args)

            if not tasks:
                self.logger.warning("No tasks to execute")
                return 0

            # Filter tasks based on orchestrator availability
            available_tasks = self.orchestrator.filter_tasks_by_selection(
                tasks, [task.check_type for task in tasks]
            )

            if len(available_tasks) < len(tasks):
                unavailable_count = len(tasks) - len(available_tasks)
                self.logger.warning(
                    f"{unavailable_count} tasks skipped due to unavailable checkers"
                )

            if not available_tasks:
                self.logger.error("No available tasks to execute")
                return 1

            # Execute checks
            self.logger.info(f"Executing {len(available_tasks)} tasks...")
            check_results = self.orchestrator.execute_checks(available_tasks)

            # Calculate overall status
            overall_status = self._calculate_overall_status(check_results)
            total_duration = time.time() - start_time

            # Create simulation result
            simulation_result = SimulationResult(
                overall_status=overall_status,
                total_duration=total_duration,
                check_results=check_results,
                python_versions_tested=list(
                    set(
                        task.python_version
                        for task in available_tasks
                        if task.python_version
                    )
                )
                or ["system"],
                summary=self._generate_summary(check_results),
                configuration=self.config,
            )

            # Generate reports
            report_paths = self._generate_reports(simulation_result, args)
            simulation_result.report_paths = report_paths

            # Save execution history
            self._save_execution_history(simulation_result)

            # Print summary
            self._print_execution_summary(simulation_result)

            # Return appropriate exit code
            return 0 if simulation_result.is_successful else 1

        except Exception as e:
            self.logger.error(f"Check execution failed: {e}")
            return 1

    def _list_checks(self, args: argparse.Namespace) -> int:
        """List available checks."""
        try:
            self.cli_parser.print_available_checks(
                detailed=args.detailed, format_type=args.format
            )
            return 0
        except Exception as e:
            self.logger.error(f"Failed to list checks: {e}")
            return 1

    def _show_check_info(self, args: argparse.Namespace) -> int:
        """Show detailed information about a specific check."""
        try:
            self.cli_parser.print_check_info(args.check_name)
            return 0
        except Exception as e:
            self.logger.error(f"Failed to show check info: {e}")
            return 1

    def _show_execution_plan(self, args: argparse.Namespace) -> int:
        """Show execution plan for selected checks."""
        try:
            # Create tasks from arguments (similar to run command)
            tasks = []
            if args.checks:
                for check_name in args.checks:
                    tasks.append(CheckTask(name=check_name, check_type=check_name))
            else:
                # Use all available checks
                for check_name in self.orchestrator.get_available_checks():
                    tasks.append(CheckTask(name=check_name, check_type=check_name))

            # Apply exclusions
            if args.exclude:
                tasks = [task for task in tasks if task.check_type not in args.exclude]

            self.cli_parser.print_execution_plan(tasks, args.format)
            return 0
        except Exception as e:
            self.logger.error(f"Failed to show execution plan: {e}")
            return 1

    def _handle_hook_command(self, args: argparse.Namespace) -> int:
        """Handle Git hook management commands."""
        try:
            if not hasattr(args, "hook_action") or args.hook_action is None:
                self.logger.error(
                    "No hook action specified. Use 'hook --help' for available actions."
                )
                return 1

            if args.hook_action == "install":
                return self._install_hook(args)
            elif args.hook_action == "uninstall":
                return self._uninstall_hook(args)
            elif args.hook_action == "list":
                return self._list_hooks(args)
            elif args.hook_action == "test":
                return self._test_hook(args)
            elif args.hook_action == "status":
                return self._show_hook_status(args)
            elif args.hook_action == "setup":
                return self._setup_recommended_hooks(args)
            else:
                self.logger.error(f"Unknown hook action: {args.hook_action}")
                return 1

        except Exception as e:
            self.logger.error(f"Hook command failed: {e}")
            return 1

    def _install_hook(self, args: argparse.Namespace) -> int:
        """Install a Git hook."""
        success = self.git_hook_manager.install_hook(
            args.hook_type, args.checks, args.force
        )
        return 0 if success else 1

    def _uninstall_hook(self, args: argparse.Namespace) -> int:
        """Uninstall a Git hook."""
        success = self.git_hook_manager.uninstall_hook(args.hook_type)
        return 0 if success else 1

    def _list_hooks(self, args: argparse.Namespace) -> int:
        """List Git hooks."""
        try:
            hooks_info = self.git_hook_manager.list_hooks()

            if args.format == "json":
                print(json.dumps(hooks_info, indent=2))
            else:
                # Table format
                print("Git Hooks Status")
                print("=" * 50)

                if not hooks_info:
                    print("No hooks information available (not in a Git repository?)")
                    return 1

                for hook_type, info in hooks_info.items():
                    status_icon = (
                        "✅" if info["installed"] and info["is_ours"] else "❌"
                    )
                    print(f"{status_icon} {hook_type}")
                    print(f"   Description: {info['description']}")
                    print(f"   Installed: {info['installed']}")
                    if info["installed"]:
                        print(f"   Our Hook: {info['is_ours']}")
                        print(f"   Executable: {info['executable']}")
                        if info["config"]:
                            checks = info["config"].get("checks", [])
                            print(
                                f"   Checks: {', '.join(checks) if checks else 'none'}"
                            )
                    print()

            return 0
        except Exception as e:
            self.logger.error(f"Failed to list hooks: {e}")
            return 1

    def _test_hook(self, args: argparse.Namespace) -> int:
        """Test a Git hook."""
        success = self.git_hook_manager.test_hook(args.hook_type)
        return 0 if success else 1

    def _show_hook_status(self, args: argparse.Namespace) -> int:
        """Show comprehensive hook status."""
        try:
            status = self.git_hook_manager.get_hook_status()

            print("Git Hook Status")
            print("=" * 50)
            print(f"Git Repository: {status['git_repository']}")
            if status["git_dir"]:
                print(f"Git Directory: {status['git_dir']}")
                print(f"Hooks Directory: {status['hooks_dir']}")

            if status["hooks"]:
                print("\nHook Details:")
                print("-" * 30)
                for hook_type, info in status["hooks"].items():
                    print(f"{hook_type}:")
                    print(f"  Installed: {info['installed']}")
                    if info["installed"]:
                        print(f"  Our Hook: {info['is_ours']}")
                        print(f"  Executable: {info['executable']}")
                        if info["config"]:
                            print(
                                f"  Installed At: {info['config'].get('installed_at', 'unknown')}"
                            )
                            checks = info["config"].get("checks", [])
                            print(
                                f"  Checks: {', '.join(checks) if checks else 'none'}"
                            )
                    print()

            return 0
        except Exception as e:
            self.logger.error(f"Failed to show hook status: {e}")
            return 1

    def _setup_recommended_hooks(self, args: argparse.Namespace) -> int:
        """Setup recommended Git hooks."""
        try:
            print("Setting up recommended Git hooks...")
            results = self.git_hook_manager.install_recommended_hooks()

            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            print(f"\nInstallation Results: {success_count}/{total_count} successful")

            for hook_type, success in results.items():
                status_icon = "✅" if success else "❌"
                print(f"{status_icon} {hook_type}")

            return 0 if success_count == total_count else 1

        except Exception as e:
            self.logger.error(f"Failed to setup recommended hooks: {e}")
            return 1

    def _calculate_overall_status(self, check_results: Dict[str, Any]) -> CheckStatus:
        """Calculate overall status from individual check results."""
        if not check_results:
            return CheckStatus.SKIPPED

        statuses = [result.status for result in check_results.values()]

        if CheckStatus.FAILURE in statuses:
            return CheckStatus.FAILURE
        elif CheckStatus.WARNING in statuses:
            return CheckStatus.WARNING
        elif all(status == CheckStatus.SUCCESS for status in statuses):
            return CheckStatus.SUCCESS
        else:
            return CheckStatus.WARNING

    def _generate_summary(self, check_results: Dict[str, Any]) -> str:
        """Generate a summary of check results."""
        if not check_results:
            return "No checks were executed."

        total_checks = len(check_results)
        successful = sum(
            1
            for result in check_results.values()
            if result.status == CheckStatus.SUCCESS
        )
        failed = sum(
            1
            for result in check_results.values()
            if result.status == CheckStatus.FAILURE
        )
        warnings = sum(
            1
            for result in check_results.values()
            if result.status == CheckStatus.WARNING
        )
        skipped = sum(
            1
            for result in check_results.values()
            if result.status == CheckStatus.SKIPPED
        )

        summary_parts = [
            f"Executed {total_checks} checks:",
            f"✓ {successful} successful",
        ]

        if failed > 0:
            summary_parts.append(f"✗ {failed} failed")
        if warnings > 0:
            summary_parts.append(f"⚠ {warnings} warnings")
        if skipped > 0:
            summary_parts.append(f"- {skipped} skipped")

        return " | ".join(summary_parts)

    def _generate_reports(
        self, result: SimulationResult, args: argparse.Namespace
    ) -> Dict[str, str]:
        """Generate reports in requested formats."""
        report_paths = {}

        # Determine output directory
        output_dir = (
            Path(args.output_dir)
            if args.output_dir
            else Path(self.config["output_directory"])
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # Generate reports based on requested format
            if args.format in ["markdown", "both"]:
                from reporters.markdown_reporter import MarkdownReporter

                markdown_reporter = MarkdownReporter(self.config)
                markdown_path = output_dir / f"ci_report_{timestamp}.md"
                markdown_reporter.generate_report(result, str(markdown_path))
                report_paths["markdown"] = str(markdown_path)
                self.logger.info(f"Generated Markdown report: {markdown_path}")

            if args.format in ["json", "both"]:
                from reporters.json_reporter import JSONReporter

                json_reporter = JSONReporter(self.config)
                json_path = output_dir / f"ci_report_{timestamp}.json"
                json_reporter.generate_report(result, str(json_path))
                report_paths["json"] = str(json_path)
                self.logger.info(f"Generated JSON report: {json_path}")

        except ImportError as e:
            self.logger.warning(f"Report generation failed: {e}")
            # Fallback to basic report generation
            basic_report_path = output_dir / f"ci_report_{timestamp}.txt"
            self._generate_basic_report(result, basic_report_path)
            report_paths["basic"] = str(basic_report_path)

        return report_paths

    def _generate_basic_report(
        self, result: SimulationResult, output_path: Path
    ) -> None:
        """Generate a basic text report as fallback."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"CI Simulation Report\n")
            f.write(f"Generated: {result.timestamp}\n")
            f.write(f"Duration: {result.total_duration:.2f} seconds\n")
            f.write(f"Overall Status: {result.overall_status.value}\n")
            f.write(f"Python Versions: {', '.join(result.python_versions_tested)}\n\n")

            f.write(f"Summary: {result.summary}\n\n")

            f.write("Check Results:\n")
            f.write("-" * 50 + "\n")

            for name, check_result in result.check_results.items():
                f.write(
                    f"{name}: {check_result.status.value} ({check_result.duration:.2f}s)\n"
                )
                if check_result.errors:
                    for error in check_result.errors:
                        f.write(f"  Error: {error}\n")
                if check_result.warnings:
                    for warning in check_result.warnings:
                        f.write(f"  Warning: {warning}\n")
                f.write("\n")

    def _save_execution_history(self, result: SimulationResult) -> None:
        """Save execution history for trend analysis."""
        try:
            history_dir = Path(
                self.config.get("directories", {}).get("history", ".kiro/ci-history")
            )
            timestamp = result.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
            execution_dir = history_dir / timestamp
            execution_dir.mkdir(parents=True, exist_ok=True)

            # Save detailed results
            result.save_to_file(str(execution_dir / "results.json"))

            # Save summary
            summary_path = execution_dir / "summary.md"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"# CI Execution Summary\n\n")
                f.write(f"**Timestamp:** {result.timestamp}\n")
                f.write(f"**Duration:** {result.total_duration:.2f} seconds\n")
                f.write(f"**Status:** {result.overall_status.value}\n\n")
                f.write(f"**Summary:** {result.summary}\n")

            self.logger.debug(f"Saved execution history to: {execution_dir}")

        except Exception as e:
            self.logger.warning(f"Failed to save execution history: {e}")

    def _print_execution_summary(self, result: SimulationResult) -> None:
        """Print execution summary to console."""
        if self.config.get("quiet", False):
            return

        print("\n" + "=" * 60)
        print("CI SIMULATION SUMMARY")
        print("=" * 60)
        print(f"Duration: {result.total_duration:.2f} seconds")
        print(f"Overall Status: {result.overall_status.value.upper()}")
        print(f"Python Versions: {', '.join(result.python_versions_tested)}")
        print()
        print(result.summary)

        # Show failed checks details
        failed_checks = result.failed_checks
        if failed_checks:
            print(f"\nFailed Checks ({len(failed_checks)}):")
            print("-" * 30)
            for check in failed_checks:
                print(f"• {check.name}: {check.status.value}")
                if check.errors:
                    for error in check.errors[:2]:  # Show first 2 errors
                        print(f"  - {error}")
                    if len(check.errors) > 2:
                        print(f"  - ... and {len(check.errors) - 2} more errors")

        # Show report paths
        if result.report_paths:
            print(f"\nReports Generated:")
            for format_name, path in result.report_paths.items():
                print(f"• {format_name.title()}: {path}")

        print("=" * 60)

    def setup_git_hook(
        self, hook_type: str = "pre-commit", checks: Optional[List[str]] = None
    ) -> bool:
        """
        Set up Git hook for automatic CI simulation.

        Args:
            hook_type: Type of Git hook to install ('pre-commit', 'pre-push')
            checks: List of checks to run in the hook

        Returns:
            True if hook was set up successfully
        """
        return self.git_hook_manager.install_hook(hook_type, checks, force=True)

    def cleanup(self, keep_reports: bool = True) -> None:
        """
        Perform cleanup operations.

        Args:
            keep_reports: Whether to keep generated reports
        """
        try:
            # Clean up temporary files
            temp_dir = Path(
                self.config.get("directories", {}).get("temp", "temp/ci-simulation")
            )
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                self.logger.debug(f"Cleaned up temporary directory: {temp_dir}")

            # Optionally clean up old reports
            if not keep_reports:
                reports_dir = Path(
                    self.config.get("directories", {}).get(
                        "reports", "reports/ci-simulation"
                    )
                )
                if reports_dir.exists():
                    shutil.rmtree(reports_dir)
                    self.logger.debug(f"Cleaned up reports directory: {reports_dir}")

        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")

    def interactive_mode(self) -> int:
        """
        Run the simulator in interactive mode for check selection.

        Returns:
            Exit code
        """
        try:
            print("CI Simulator - Interactive Mode")
            print("=" * 40)

            # Show available checks
            available_checks = self.orchestrator.get_available_checks()
            if not available_checks:
                print("No checks available.")
                return 1

            print("Available checks:")
            for i, check in enumerate(available_checks, 1):
                print(f"{i}. {check}")

            print(f"{len(available_checks) + 1}. All checks")
            print("0. Exit")

            # Get user selection
            while True:
                try:
                    choice = input(
                        "\nSelect checks to run (comma-separated numbers): "
                    ).strip()
                    if choice == "0":
                        return 0

                    if choice == str(len(available_checks) + 1):
                        selected_checks = available_checks
                        break

                    # Parse comma-separated choices
                    choices = [int(c.strip()) for c in choice.split(",")]
                    selected_checks = [
                        available_checks[c - 1]
                        for c in choices
                        if 1 <= c <= len(available_checks)
                    ]

                    if selected_checks:
                        break
                    else:
                        print("Invalid selection. Please try again.")

                except (ValueError, IndexError):
                    print("Invalid input. Please enter numbers separated by commas.")

            # Run selected checks
            print(f"\nRunning selected checks: {', '.join(selected_checks)}")

            # Create mock args for selected checks
            class MockArgs:
                def __init__(self, checks):
                    self.command = "run"
                    self.checks = checks
                    self.exclude = None
                    self.python_versions = None
                    self.parallel = None
                    self.timeout = None
                    self.fail_fast = False
                    self.output_dir = None
                    self.format = "both"
                    self.quiet = False
                    self.verbose = False
                    self.all = False

            return self._run_checks(MockArgs(selected_checks))

        except KeyboardInterrupt:
            print("\nInteractive mode cancelled.")
            return 130
        except Exception as e:
            self.logger.error(f"Interactive mode failed: {e}")
            return 1


def main() -> int:
    """Main entry point for the CI simulator."""
    # Handle special cases
    if len(sys.argv) > 1:
        if sys.argv[1] == "--version":
            print(f"CI Simulator v{CISimulator.VERSION}")
            return 0
        elif sys.argv[1] == "--interactive":
            simulator = CISimulator()
            return simulator.interactive_mode()
        elif sys.argv[1] == "--setup-hook":
            simulator = CISimulator()
            hook_type = sys.argv[2] if len(sys.argv) > 2 else "pre-commit"
            success = simulator.setup_git_hook(hook_type)
            return 0 if success else 1
        elif sys.argv[1] == "--setup-hooks":
            simulator = CISimulator()
            results = simulator.git_hook_manager.install_recommended_hooks()
            success_count = sum(1 for success in results.values() if success)
            print(f"Installed {success_count}/{len(results)} recommended hooks")
            return 0 if success_count == len(results) else 1

    # Normal execution
    simulator = CISimulator()
    try:
        return simulator.run()
    finally:
        simulator.cleanup()


if __name__ == "__main__":
    sys.exit(main())
