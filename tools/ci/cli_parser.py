"""
Command Line Interface Parser for CI Simulation Tool

This module provides comprehensive command-line argument parsing
for selective check execution and orchestrator configuration.
"""

import argparse
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

try:
    from .check_orchestrator import CheckOrchestrator
    from .models import CheckTask, ConfigDict
except ImportError:
    from check_orchestrator import CheckOrchestrator
    from models import CheckTask, ConfigDict


class CLIParser:
    """
    Command-line interface parser for CI simulation tool.

    Provides comprehensive argument parsing for check selection,
    configuration, and execution options.
    """

    def __init__(self, orchestrator: CheckOrchestrator):
        """
        Initialize CLI parser with orchestrator instance.

        Args:
            orchestrator: CheckOrchestrator instance for validation
        """
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog='ci-simulator',
            description='CI/CD Pipeline Simulation Tool for PhotoGeoView',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_epilog_text()
        )

        # Main command groups
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )

        # Run command (default)
        self._add_run_command(subparsers)

        # List command
        self._add_list_command(subparsers)

        # Info command
        self._add_info_command(subparsers)

        # Plan command
        self._add_plan_command(subparsers)

        # Hook command
        self._add_hook_command(subparsers)

        return parser

    def _add_run_command(self, subparsers) -> None:
        """Add the 'run' command for executing checks."""
        run_parser = subparsers.add_parser(
            'run',
            help='Execute CI checks',
            description='Execute selected CI checks with dependency resolution'
        )

        # Check selection
        run_parser.add_argument(
            'checks',
            nargs='*',
            help='Specific checks to run (default: all available checks)'
        )

        run_parser.add_argument(
            '--all',
            action='store_true',
            help='Run all available checks (explicit)'
        )

        run_parser.add_argument(
            '--exclude',
            nargs='+',
            metavar='CHECK',
            help='Exclude specific checks from execution'
        )

        # Python version selection
        run_parser.add_argument(
            '--python-versions',
            nargs='+',
            metavar='VERSION',
            help='Python versions to test against (e.g., 3.9 3.10 3.11)'
        )

        # Execution options
        run_parser.add_argument(
            '--parallel',
            type=int,
            metavar='N',
            help='Maximum number of parallel tasks (default: auto-detect)'
        )

        run_parser.add_argument(
            '--timeout',
            type=float,
            metavar='SECONDS',
            help='Global timeout for all checks in seconds'
        )

        run_parser.add_argument(
            '--fail-fast',
            action='store_true',
            help='Stop execution on first failure'
        )

        # Output options
        run_parser.add_argument(
            '--output-dir',
            type=Path,
            metavar='DIR',
            help='Directory for output reports (default: reports/ci-simulation/)'
        )

        run_parser.add_argument(
            '--format',
            choices=['markdown', 'json', 'both'],
            default='both',
            help='Report format (default: both)'
        )

        run_parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress non-essential output'
        )

        run_parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def _add_list_command(self, subparsers) -> None:
        """Add the 'list' command for showing available checks."""
        list_parser = subparsers.add_parser(
            'list',
            help='List available checks',
            description='Display information about available CI checks'
        )

        list_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information about each check'
        )

        list_parser.add_argument(
            '--format',
            choices=['table', 'json', 'yaml'],
            default='table',
            help='Output format (default: table)'
        )

    def _add_info_command(self, subparsers) -> None:
        """Add the 'info' command for showing check details."""
        info_parser = subparsers.add_parser(
            'info',
            help='Show detailed information about a specific check',
            description='Display comprehensive information about a CI check'
        )

        info_parser.add_argument(
            'check_name',
            help='Name of the check to get information about'
        )

    def _add_plan_command(self, subparsers) -> None:
        """Add the 'plan' command for showing execution plan."""
        plan_parser = subparsers.add_parser(
            'plan',
            help='Show execution plan',
            description='Display the execution plan for selected checks'
        )

        plan_parser.add_argument(
            'checks',
            nargs='*',
            help='Specific checks to plan (default: all available checks)'
        )

        plan_parser.add_argument(
            '--exclude',
            nargs='+',
            metavar='CHECK',
            help='Exclude specific checks from plan'
        )

        plan_parser.add_argument(
            '--format',
            choices=['table', 'json', 'graph'],
            default='table',
            help='Plan output format (default: table)'
        )

    def _add_hook_command(self, subparsers) -> None:
        """Add the 'hook' command for Git hook management."""
        hook_parser = subparsers.add_parser(
            'hook',
            help='Manage Git hooks',
            description='Install, configure, and manage Git hooks for CI simulation'
        )

        hook_subparsers = hook_parser.add_subparsers(
            dest='hook_action',
            help='Hook management actions',
            metavar='ACTION'
        )

        # Install hook
        install_parser = hook_subparsers.add_parser(
            'install',
            help='Install Git hook',
            description='Install a Git hook for CI simulation'
        )
        install_parser.add_argument(
            'hook_type',
            choices=['pre-commit', 'pre-push', 'commit-msg'],
            help='Type of hook to install'
        )
        install_parser.add_argument(
            '--checks',
            nargs='+',
            metavar='CHECK',
            help='Checks to run in the hook (default: hook-specific defaults)'
        )
        install_parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing hook'
        )

        # Uninstall hook
        uninstall_parser = hook_subparsers.add_parser(
            'uninstall',
            help='Uninstall Git hook',
            description='Remove a Git hook installed by CI Simulator'
        )
        uninstall_parser.add_argument(
            'hook_type',
            choices=['pre-commit', 'pre-push', 'commit-msg'],
            help='Type of hook to uninstall'
        )

        # List hooks
        list_parser = hook_subparsers.add_parser(
            'list',
            help='List Git hooks',
            description='Show status of all Git hooks'
        )
        list_parser.add_argument(
            '--format',
            choices=['table', 'json'],
            default='table',
            help='Output format (default: table)'
        )

        # Test hook
        test_parser = hook_subparsers.add_parser(
            'test',
            help='Test Git hook',
            description='Test a Git hook by running it manually'
        )
        test_parser.add_argument(
            'hook_type',
            choices=['pre-commit', 'pre-push', 'commit-msg'],
            help='Type of hook to test'
        )

        # Status command
        status_parser = hook_subparsers.add_parser(
            'status',
            help='Show hook status',
            description='Show comprehensive status of Git hooks'
        )

        # Setup recommended hooks
        setup_parser = hook_subparsers.add_parser(
            'setup',
            help='Setup recommended hooks',
            description='Install recommended Git hooks for the project'
        )

    def _get_epilog_text(self) -> str:
        """Get epilog text with examples."""
        return """
Examples:
  ci-simulator run                          # Run all available checks
  ci-simulator run code_quality test_runner # Run specific checks
  ci-simulator run --exclude security_scanner # Run all except security
  ci-simulator run --python-versions 3.9 3.10 # Test multiple Python versions
  ci-simulator list --detailed             # List all checks with details
  ci-simulator info code_quality           # Show details for specific check
  ci-simulator plan code_quality test_runner # Show execution plan

For more information, visit: https://github.com/PhotoGeoView/ci-simulation
        """

    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """
        Parse command-line arguments.

        Args:
            args: List of arguments to parse (default: sys.argv)

        Returns:
            Parsed arguments namespace
        """
        if args is None:
            args = sys.argv[1:]

        # Set default command if none provided
        if not args or (args[0] not in ['run', 'list', 'info', 'plan', 'hook'] and not args[0].startswith('-')):
            args = ['run'] + args

        return self.parser.parse_args(args)

    def validate_args(self, args: argparse.Namespace) -> List[str]:
        """
        Validate parsed arguments and return validation errors.

        Args:
            args: Parsed arguments namespace

        Returns:
            List of validation error messages
        """
        errors = []

        if args.command == 'run':
            errors.extend(self._validate_run_args(args))
        elif args.command == 'info':
            errors.extend(self._validate_info_args(args))
        elif args.command == 'plan':
            errors.extend(self._validate_plan_args(args))

        return errors

    def _validate_run_args(self, args: argparse.Namespace) -> List[str]:
        """Validate arguments for the 'run' command."""
        errors = []

        # Validate check selection
        if args.checks:
            check_errors = self.orchestrator.validate_check_selection(args.checks)
            errors.extend(check_errors)

        if args.exclude:
            exclude_errors = self.orchestrator.validate_check_selection(args.exclude)
            if exclude_errors:
                errors.append(f"Invalid exclude checks: {exclude_errors}")

        # Validate parallel tasks
        if args.parallel is not None:
            if args.parallel < 1:
                errors.append("Parallel tasks must be at least 1")
            elif args.parallel > 16:
                errors.append("Parallel tasks should not exceed 16 for stability")

        # Validate timeout
        if args.timeout is not None:
            if args.timeout <= 0:
                errors.append("Timeout must be positive")
            elif args.timeout < 10:
                errors.append("Timeout should be at least 10 seconds")

        # Validate output directory
        if args.output_dir:
            try:
                args.output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create output directory: {e}")

        return errors

    def _validate_info_args(self, args: argparse.Namespace) -> List[str]:
        """Validate arguments for the 'info' command."""
        errors = []

        if not self.orchestrator.is_check_available(args.check_name):
            available = ', '.join(self.orchestrator.get_available_checks())
            errors.append(f"Check '{args.check_name}' not available. Available: {available}")

        return errors

    def _validate_plan_args(self, args: argparse.Namespace) -> List[str]:
        """Validate arguments for the 'plan' command."""
        errors = []

        if args.checks:
            check_errors = self.orchestrator.validate_check_selection(args.checks)
            errors.extend(check_errors)

        if args.exclude:
            exclude_errors = self.orchestrator.validate_check_selection(args.exclude)
            if exclude_errors:
                errors.append(f"Invalid exclude checks: {exclude_errors}")

        return errors

    def create_tasks_from_args(self, args: argparse.Namespace) -> List[CheckTask]:
        """
        Create CheckTask objects from parsed arguments.

        Args:
            args: Parsed arguments namespace

        Returns:
            List of CheckTask objects
        """
        if args.command != 'run':
            return []

        # Determine which checks to run
        if args.all or not args.checks:
            selected_checks = self.orchestrator.get_available_checks()
        else:
            selected_checks = args.checks

        # Apply exclusions
        if args.exclude:
            selected_checks = [
                check for check in selected_checks
                if check not in args.exclude
            ]

        # Create tasks
        tasks = []
        python_versions = args.python_versions or [None]

        for check_name in selected_checks:
            for python_version in python_versions:
                task_name = f"{check_name}"
                if python_version:
                    task_name += f"_py{python_version}"

                task = CheckTask(
                    name=task_name,
                    check_type=check_name,
                    python_version=python_version,
                    timeout=args.timeout,
                    metadata={
                        'cli_args': vars(args),
                        'selected_explicitly': check_name in (args.checks or [])
                    }
                )
                tasks.append(task)

        return tasks

    def get_execution_config(self, args: argparse.Namespace) -> ConfigDict:
        """
        Create execution configuration from parsed arguments.

        Args:
            args: Parsed arguments namespace

        Returns:
            Configuration dictionary for orchestrator
        """
        config = {}

        if args.command == 'run':
            if args.parallel:
                config['max_parallel_tasks'] = args.parallel

            if args.fail_fast:
                config['fail_fast'] = True

            if args.output_dir:
                config['output_dir'] = str(args.output_dir)

            config['report_format'] = args.format
            config['quiet'] = args.quiet
            config['verbose'] = args.verbose

        return config

    def suggest_checks_from_files(self, file_paths: List[str]) -> List[str]:
        """
        Suggest relevant checks based on modified files.

        Args:
            file_paths: List of file paths that were modified

        Returns:
            List of suggested check names
        """
        return self.orchestrator.suggest_checks_for_files(file_paths)

    def print_help(self) -> None:
        """Print help message."""
        self.parser.print_help()

    def print_available_checks(self, detailed: bool = False, format_type: str = 'table') -> None:
        """
        Print available checks information.

        Args:
            detailed: Whether to show detailed information
            format_type: Output format ('table', 'json', 'yaml')
        """
        checks_info = self.orchestrator.list_available_checks()

        if format_type == 'json':
            import json
            print(json.dumps(checks_info, indent=2))
        elif format_type == 'yaml':
            try:
                import yaml
                print(yaml.dump(checks_info, default_flow_style=False))
            except ImportError:
                print("YAML format requires PyYAML package")
                format_type = 'table'

        if format_type == 'table':
            if not checks_info:
                print("No checks available")
                return

            print(f"Available Checks ({len(checks_info)}):")
            print("-" * 50)

            for check_name, info in checks_info.items():
                print(f"• {check_name}")
                if detailed:
                    print(f"  Type: {info.get('check_type', 'unknown')}")
                    print(f"  Available: {info.get('is_available', False)}")
                    if info.get('dependencies'):
                        deps = ', '.join(info['dependencies'])
                        print(f"  Dependencies: {deps}")
                    if info.get('description'):
                        desc = info['description'].split('\n')[0][:60]
                        print(f"  Description: {desc}")
                    print()

    def print_check_info(self, check_name: str) -> None:
        """
        Print detailed information about a specific check.

        Args:
            check_name: Name of the check to show info for
        """
        info = self.orchestrator.get_check_info(check_name)

        if not info:
            print(f"Check '{check_name}' not found")
            return

        print(f"Check Information: {check_name}")
        print("=" * (20 + len(check_name)))
        print(f"Name: {info['name']}")
        print(f"Type: {info['check_type']}")
        print(f"Available: {info['is_available']}")

        if info.get('dependencies'):
            deps = ', '.join(info['dependencies'])
            print(f"Dependencies: {deps}")
        else:
            print("Dependencies: None")

        if info.get('description'):
            print(f"\nDescription:")
            print(info['description'])

    def print_execution_plan(self, tasks: List[CheckTask], format_type: str = 'table') -> None:
        """
        Print execution plan for tasks.

        Args:
            tasks: List of tasks to create plan for
            format_type: Output format ('table', 'json', 'graph')
        """
        plan = self.orchestrator.create_execution_plan(tasks)

        if format_type == 'json':
            import json
            print(json.dumps(plan, indent=2))
            return

        # Table format
        print(f"Execution Plan ({plan['total_tasks']} tasks)")
        print("=" * 40)
        print(f"Total Tasks: {plan['total_tasks']}")
        print(f"Execution Levels: {plan['execution_levels']}")
        print(f"Estimated Duration: {plan['estimated_duration']:.1f} seconds")
        print()

        for level_info in plan['execution_order']:
            level = level_info['level']
            tasks_in_level = level_info['tasks']
            parallel = level_info['parallel_execution']
            duration = level_info['estimated_duration']

            print(f"Level {level}: {len(tasks_in_level)} task(s)")
            print(f"  Tasks: {', '.join(tasks_in_level)}")
            print(f"  Parallel: {'Yes' if parallel else 'No'}")
            print(f"  Estimated Duration: {duration:.1f} seconds")
            print()
