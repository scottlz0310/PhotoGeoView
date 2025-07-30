"""
Check Orchestrator for CI Simulation Tool

This module implements the CheckOrchestrator class that manages the execution
of multiple checks with dependency resolution, parallel execution, and resource management.
"""

import asyncio
import concurrent.futures
import logging
import os
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from .interfaces import CheckerFactory, CheckerInterface, OrchestratorInterface
    from .models import CheckResult, CheckStatus, CheckTask, ConfigDict
except ImportError:
    from interfaces import CheckerFactory, CheckerInterface, OrchestratorInterface
    from models import CheckResult, CheckStatus, CheckTask, ConfigDict


class DependencyResolver:
    """
    Handles dependency resolution for check tasks using topological sorting.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def resolve_dependencies(self, tasks: List[CheckTask]) -> List[str]:
        """
        Resolve task dependencies and return execution order using topological sort.

        Args:
            tasks: List of CheckTask objects to resolve

        Returns:
            List of task names in dependency-resolved order

        Raises:
            ValueError: If circular dependencies are detected
        """
        # Build dependency graph
        graph = {}
        in_degree = {}
        task_map = {task.name: task for task in tasks}

        # Initialize graph and in-degree count
        for task in tasks:
            graph[task.name] = []
            in_degree[task.name] = 0

        # Build edges and count in-degrees
        for task in tasks:
            for dep in task.dependencies:
                if dep in task_map:
                    graph[dep].append(task.name)
                    in_degree[task.name] += 1
                else:
                    self.logger.warning(
                        f"Task '{task.name}' depends on unknown task '{dep}'"
                    )

        # Topological sort using Kahn's algorithm
        queue = deque([task for task in in_degree if in_degree[task] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for circular dependencies
        if len(result) != len(tasks):
            remaining = [task for task in in_degree if in_degree[task] > 0]
            raise ValueError(f"Circular dependency detected among tasks: {remaining}")

        return result

    def get_dependency_levels(self, tasks: List[CheckTask]) -> Dict[int, List[str]]:
        """
        Group tasks by dependency level for parallel execution.

        Args:
            tasks: List of CheckTask objects

        Returns:
            Dictionary mapping level to list of task names
        """
        resolved_order = self.resolve_dependencies(tasks)
        task_map = {task.name: task for task in tasks}
        levels = {}
        task_levels = {}

        # Assign levels based on dependencies
        for task_name in resolved_order:
            task = task_map[task_name]
            max_dep_level = -1

            for dep in task.dependencies:
                if dep in task_levels:
                    max_dep_level = max(max_dep_level, task_levels[dep])

            level = max_dep_level + 1
            task_levels[task_name] = level

            if level not in levels:
                levels[level] = []
            levels[level].append(task_name)

        return levels


class ResourceManager:
    """
    Manages system resources and throttling for check execution.
    """

    def __init__(self, config: ConfigDict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._active_tasks = 0
        self._max_parallel_tasks = self._calculate_max_parallel_tasks()
        self._memory_threshold = config.get("memory_threshold_percent", 80)
        self._cpu_threshold = config.get("cpu_threshold_percent", 90)

    def _calculate_max_parallel_tasks(self) -> int:
        """Calculate maximum number of parallel tasks based on system resources."""
        cpu_count = os.cpu_count() or 1
        max_from_config = self.config.get("max_parallel_tasks", cpu_count)

        # Conservative approach: use 75% of available cores
        recommended = max(1, int(cpu_count * 0.75))
        return min(max_from_config, recommended)

    def can_start_task(self) -> bool:
        """
        Check if a new task can be started based on resource availability.

        Returns:
            True if resources are available for a new task
        """
        with self._lock:
            if self._active_tasks >= self._max_parallel_tasks:
                return False

        # Check system resources
        try:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=0.1)

            if memory_percent > self._memory_threshold:
                self.logger.warning(f"Memory usage high: {memory_percent}%")
                return False

            if cpu_percent > self._cpu_threshold:
                self.logger.warning(f"CPU usage high: {cpu_percent}%")
                return False

            return True
        except Exception as e:
            self.logger.warning(f"Failed to check system resources: {e}")
            return self._active_tasks < self._max_parallel_tasks

    def acquire_task_slot(self) -> bool:
        """
        Acquire a slot for task execution.

        Returns:
            True if slot was acquired successfully
        """
        with self._lock:
            if self.can_start_task():
                self._active_tasks += 1
                return True
            return False

    def release_task_slot(self) -> None:
        """Release a task execution slot."""
        with self._lock:
            if self._active_tasks > 0:
                self._active_tasks -= 1

    @property
    def active_tasks(self) -> int:
        """Get number of currently active tasks."""
        with self._lock:
            return self._active_tasks

    @property
    def max_parallel_tasks(self) -> int:
        """Get maximum number of parallel tasks."""
        return self._max_parallel_tasks


class CheckOrchestrator(OrchestratorInterface):
    """
    Comprehensive check orchestrator with dependency management, parallel execution,
    and resource management capabilities.

    This orchestrator provides:
    - Dependency resolution using topological sorting
    - Parallel execution with resource throttling
    - Task filtering and selection
    - Comprehensive error handling and recovery
    """

    def __init__(self, config: ConfigDict):
        """
        Initialize the check orchestrator.

        Args:
            config: Configuration dictionary containing orchestrator settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.dependency_resolver = DependencyResolver()
        self.resource_manager = ResourceManager(config)
        self._checkers: Dict[str, CheckerInterface] = {}
        self._available_checks: Set[str] = set()
        self._initialize_checkers()

    def _initialize_checkers(self) -> None:
        """Initialize available checkers and determine which ones are available."""
        checker_configs = self.config.get("checkers", {})

        for check_type in CheckerFactory.get_available_checkers():
            try:
                checker_config = checker_configs.get(check_type, {})
                checker = CheckerFactory.create_checker(check_type, checker_config)

                if checker.is_available():
                    self._checkers[check_type] = checker
                    self._available_checks.add(check_type)
                    self.logger.info(f"Checker '{check_type}' is available")
                else:
                    self.logger.warning(f"Checker '{check_type}' is not available")

            except Exception as e:
                self.logger.error(f"Failed to initialize checker '{check_type}': {e}")

    def execute_checks(self, tasks: List[CheckTask]) -> Dict[str, CheckResult]:
        """
        Execute a list of check tasks with dependency resolution and parallel execution.

        Args:
            tasks: List of CheckTask objects to execute

        Returns:
            Dictionary mapping task names to their results
        """
        self.logger.info(f"Starting execution of {len(tasks)} tasks")
        start_time = time.time()

        # Filter tasks to only include available checks
        available_tasks = self._filter_available_tasks(tasks)
        if len(available_tasks) < len(tasks):
            unavailable = [t.name for t in tasks if t not in available_tasks]
            self.logger.warning(f"Skipping unavailable tasks: {unavailable}")

        # Resolve dependencies and group by levels
        try:
            dependency_levels = self.dependency_resolver.get_dependency_levels(
                available_tasks
            )
            self.logger.info(
                f"Resolved dependencies into {len(dependency_levels)} levels"
            )
        except ValueError as e:
            self.logger.error(f"Dependency resolution failed: {e}")
            return self._create_error_results(tasks, str(e))

        # Execute tasks level by level
        results = {}
        for level, task_names in sorted(dependency_levels.items()):
            self.logger.info(f"Executing level {level} with {len(task_names)} tasks")
            level_results = self._execute_task_level(
                [t for t in available_tasks if t.name in task_names]
            )
            results.update(level_results)

        execution_time = time.time() - start_time
        self.logger.info(f"Completed execution in {execution_time:.2f} seconds")

        return results

    def _filter_available_tasks(self, tasks: List[CheckTask]) -> List[CheckTask]:
        """Filter tasks to only include those with available checkers."""
        available_tasks = []
        for task in tasks:
            if task.check_type in self._available_checks:
                available_tasks.append(task)
            else:
                self.logger.warning(
                    f"Task '{task.name}' uses unavailable checker '{task.check_type}'"
                )
        return available_tasks

    def _execute_task_level(self, tasks: List[CheckTask]) -> Dict[str, CheckResult]:
        """Execute all tasks in a dependency level, potentially in parallel."""
        if not tasks:
            return {}

        # Sort tasks by priority (higher priority first)
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        # Execute tasks in parallel if possible
        if len(sorted_tasks) == 1 or self.resource_manager.max_parallel_tasks == 1:
            # Sequential execution
            return self._execute_tasks_sequential(sorted_tasks)
        else:
            # Parallel execution
            return self._execute_tasks_parallel(sorted_tasks)

    def _execute_tasks_sequential(
        self, tasks: List[CheckTask]
    ) -> Dict[str, CheckResult]:
        """Execute tasks sequentially."""
        results = {}
        for task in tasks:
            result = self._execute_single_task(task)
            results[task.name] = result
        return results

    def _execute_tasks_parallel(self, tasks: List[CheckTask]) -> Dict[str, CheckResult]:
        """Execute tasks in parallel using ThreadPoolExecutor."""
        results = {}
        max_workers = min(len(tasks), self.resource_manager.max_parallel_tasks)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._execute_single_task_with_throttling, task): task
                for task in tasks
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.name] = result
                except Exception as e:
                    self.logger.error(f"Task '{task.name}' failed with exception: {e}")
                    results[task.name] = self._create_error_result(task, str(e))

        return results

    def _execute_single_task_with_throttling(self, task: CheckTask) -> CheckResult:
        """Execute a single task with resource throttling."""
        # Wait for available resources
        while not self.resource_manager.acquire_task_slot():
            time.sleep(0.1)

        try:
            return self._execute_single_task(task)
        finally:
            self.resource_manager.release_task_slot()

    def _execute_single_task(self, task: CheckTask) -> CheckResult:
        """Execute a single check task."""
        self.logger.info(f"Executing task: {task.name}")
        start_time = time.time()

        try:
            checker = self._checkers.get(task.check_type)
            if not checker:
                return self._create_error_result(
                    task, f"Checker '{task.check_type}' not available"
                )

            # Prepare task arguments
            kwargs = task.metadata.copy()
            if task.python_version:
                kwargs["python_version"] = task.python_version

            # Execute the check with timeout
            if task.timeout:
                result = self._execute_with_timeout(checker, task.timeout, **kwargs)
            else:
                result = checker.run_check(**kwargs)

            # Update result metadata
            result.metadata.update(
                {
                    "task_name": task.name,
                    "execution_time": time.time() - start_time,
                    "python_version": task.python_version,
                }
            )

            self.logger.info(
                f"Task '{task.name}' completed with status: {result.status.value}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Task '{task.name}' failed: {e}")
            return self._create_error_result(task, str(e))
        finally:
            # Cleanup checker resources
            try:
                checker = self._checkers.get(task.check_type)
                if checker:
                    checker.cleanup()
            except Exception as e:
                self.logger.warning(f"Cleanup failed for task '{task.name}': {e}")

    def _execute_with_timeout(
        self, checker: CheckerInterface, timeout: float, **kwargs
    ) -> CheckResult:
        """Execute a checker with timeout."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(checker.run_check, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                self.logger.error(
                    f"Checker '{checker.name}' timed out after {timeout} seconds"
                )
                return CheckResult(
                    name=checker.name,
                    status=CheckStatus.FAILURE,
                    duration=timeout,
                    errors=[f"Check timed out after {timeout} seconds"],
                    output="Execution timed out",
                )

    def _create_error_result(self, task: CheckTask, error_message: str) -> CheckResult:
        """Create an error result for a failed task."""
        return CheckResult(
            name=task.name,
            status=CheckStatus.FAILURE,
            duration=0.0,
            errors=[error_message],
            output="",
            metadata={"task_name": task.name, "check_type": task.check_type},
        )

    def _create_error_results(
        self, tasks: List[CheckTask], error_message: str
    ) -> Dict[str, CheckResult]:
        """Create error results for all tasks."""
        return {
            task.name: self._create_error_result(task, error_message) for task in tasks
        }

    def resolve_dependencies(self, task_names: List[str]) -> List[str]:
        """
        Resolve dependencies and return execution order.

        Args:
            task_names: List of task names to execute

        Returns:
            List of task names in dependency-resolved order
        """
        # Create minimal tasks for dependency resolution
        tasks = []
        for name in task_names:
            # For now, we'll need to get dependency info from checker configuration
            # This is a simplified implementation
            tasks.append(CheckTask(name=name, check_type=name, dependencies=[]))

        return self.dependency_resolver.resolve_dependencies(tasks)

    def get_available_checks(self) -> List[str]:
        """Get list of available check types."""
        return list(self._available_checks)

    def is_check_available(self, check_type: str) -> bool:
        """Check if a specific check type is available."""
        return check_type in self._available_checks

    def validate_tasks(self, tasks: List[CheckTask]) -> List[str]:
        """
        Validate a list of tasks and return any validation errors.

        Args:
            tasks: List of CheckTask objects to validate

        Returns:
            List of validation error messages
        """
        errors = []

        for task in tasks:
            # Check if checker is available
            if task.check_type not in self._available_checks:
                errors.append(
                    f"Task '{task.name}': checker '{task.check_type}' not available"
                )

            # Validate dependencies
            for dep in task.dependencies:
                if not any(t.name == dep for t in tasks):
                    errors.append(
                        f"Task '{task.name}': dependency '{dep}' not found in task list"
                    )

        # Check for circular dependencies
        try:
            self.dependency_resolver.resolve_dependencies(tasks)
        except ValueError as e:
            errors.append(f"Dependency validation failed: {e}")

        return errors

    def create_task_from_config(self, name: str, config: Dict[str, Any]) -> CheckTask:
        """
        Create a CheckTask from configuration.

        Args:
            name: Task name
            config: Task configuration dictionary

        Returns:
            Configured CheckTask object
        """
        return CheckTask(
            name=name,
            check_type=config.get("type", name),
            python_version=config.get("python_version"),
            dependencies=config.get("dependencies", []),
            timeout=config.get("timeout"),
            priority=config.get("priority", 0),
            metadata=config.get("metadata", {}),
        )

    def filter_tasks_by_selection(
        self, tasks: List[CheckTask], selected_checks: List[str]
    ) -> List[CheckTask]:
        """
        Filter tasks based on selected check names with dependency resolution.

        Args:
            tasks: List of all available tasks
            selected_checks: List of check names to execute

        Returns:
            Filtered list of tasks including dependencies
        """
        if not selected_checks:
            return tasks

        # Validate selected checks
        invalid_checks = [
            check for check in selected_checks if check not in self._available_checks
        ]
        if invalid_checks:
            available = ", ".join(sorted(self._available_checks))
            raise ValueError(
                f"Invalid check names: {invalid_checks}. Available: {available}"
            )

        # Find tasks matching selected checks
        selected_tasks = []
        task_map = {task.name: task for task in tasks}

        for check_name in selected_checks:
            matching_tasks = [
                task
                for task in tasks
                if task.check_type == check_name or task.name == check_name
            ]
            if not matching_tasks:
                self.logger.warning(f"No tasks found for check '{check_name}'")
            else:
                selected_tasks.extend(matching_tasks)

        # Add dependencies recursively
        final_tasks = self._add_task_dependencies(selected_tasks, task_map)

        self.logger.info(
            f"Selected {len(selected_tasks)} tasks, including {len(final_tasks)} with dependencies"
        )
        return final_tasks

    def _add_task_dependencies(
        self, selected_tasks: List[CheckTask], task_map: Dict[str, CheckTask]
    ) -> List[CheckTask]:
        """
        Recursively add task dependencies to the selection.

        Args:
            selected_tasks: Initially selected tasks
            task_map: Mapping of task names to CheckTask objects

        Returns:
            List of tasks including all dependencies
        """
        result_tasks = set()
        to_process = deque(selected_tasks)

        while to_process:
            current_task = to_process.popleft()
            if current_task.name in result_tasks:
                continue

            result_tasks.add(current_task.name)

            # Add dependencies
            for dep_name in current_task.dependencies:
                if dep_name in task_map and dep_name not in result_tasks:
                    dep_task = task_map[dep_name]
                    to_process.append(dep_task)
                    self.logger.debug(
                        f"Added dependency '{dep_name}' for task '{current_task.name}'"
                    )

        return [task_map[name] for name in result_tasks if name in task_map]

    def validate_check_selection(self, selected_checks: List[str]) -> List[str]:
        """
        Validate selected check names and return validation errors.

        Args:
            selected_checks: List of check names to validate

        Returns:
            List of validation error messages
        """
        errors = []

        if not selected_checks:
            return errors

        # Check for invalid check names
        invalid_checks = [
            check for check in selected_checks if check not in self._available_checks
        ]
        if invalid_checks:
            available = ", ".join(sorted(self._available_checks))
            errors.append(
                f"Invalid check names: {invalid_checks}. Available checks: {available}"
            )

        # Check for duplicates
        duplicates = [
            check for check in set(selected_checks) if selected_checks.count(check) > 1
        ]
        if duplicates:
            errors.append(f"Duplicate check names: {duplicates}")

        return errors

    def get_check_info(self, check_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific check.

        Args:
            check_name: Name of the check to get info for

        Returns:
            Dictionary with check information or None if not found
        """
        if check_name not in self._available_checks:
            return None

        checker = self._checkers.get(check_name)
        if not checker:
            return None

        return {
            "name": checker.name,
            "check_type": checker.check_type,
            "dependencies": checker.dependencies,
            "is_available": checker.is_available(),
            "description": checker.__doc__ or "No description available",
        }

    def list_available_checks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about all available checks.

        Returns:
            Dictionary mapping check names to their information
        """
        checks_info = {}
        for check_name in sorted(self._available_checks):
            info = self.get_check_info(check_name)
            if info:
                checks_info[check_name] = info
        return checks_info

    def suggest_checks_for_files(self, file_paths: List[str]) -> List[str]:
        """
        Suggest relevant checks based on file paths.

        Args:
            file_pat: List of file paths to analyze

        Returns:
            List of suggested check names
        """
        suggestions = set()

        for file_path in file_paths:
            path = Path(file_path)

            # Python files
            if path.suffix == ".py":
                suggestions.update(["code_quality", "security_scanner", "test_runner"])

            # Test files
            if "test" in path.name.lower() or path.parent.name == "tests":
                suggestions.add("test_runner")

            # Configuration files
            if path.name in ["pyproject.toml", "setup.py", "requirements.txt"]:
                suggestions.update(["security_scanner", "code_quality"])

            # AI integration files
            if any(
                ai_name in path.name.lower()
                for ai_name in ["copilot", "cursor", "kiro"]
            ):
                suggestions.add("ai_component_tester")

        # Filter to only available checks
        return [check for check in suggestions if check in self._available_checks]

    def create_execution_plan(self, tasks: List[CheckTask]) -> Dict[str, Any]:
        """
        Create a detailed execution plan for the given tasks.

        Args:
            tasks: List of tasks to create plan for

        Returns:
            Dictionary containing execution plan details
        """
        try:
            dependency_levels = self.dependency_resolver.get_dependency_levels(tasks)

            plan = {
                "total_tasks": len(tasks),
                "execution_levels": len(dependency_levels),
                "estimated_duration": self._estimate_execution_time(tasks),
                "resource_requirements": self._estimate_resource_requirements(tasks),
                "execution_order": [],
            }

            for level, task_names in sorted(dependency_levels.items()):
                level_info = {
                    "level": level,
                    "tasks": task_names,
                    "parallel_execution": len(task_names) > 1,
                    "estimated_duration": (
                        max(
                            self._estimate_task_duration(task)
                            for task in tasks
                            if task.name in task_names
                        )
                        if task_names
                        else 0
                    ),
                }
                plan["execution_order"].append(level_info)

            return plan

        except Exception as e:
            self.logger.error(f"Failed to create execution plan: {e}")
            return {
                "error": str(e),
                "total_tasks": len(tasks),
                "execution_levels": 0,
                "estimated_duration": 0,
                "execution_order": [],
            }

    def _estimate_execution_time(self, tasks: List[CheckTask]) -> float:
        """Estimate total execution time for tasks."""
        # Simple estimation based on task types
        time_estimates = {
            "code_quality": 30.0,
            "test_runner": 120.0,
            "security_scanner": 45.0,
            "performance_analyzer": 180.0,
            "ai_component_tester": 90.0,
        }

        total_time = 0.0
        for task in tasks:
            base_time = time_estimates.get(task.check_type, 60.0)
            # Add some variance based on task priority and metadata
            total_time += base_time * (1.0 + task.priority * 0.1)

        # Account for parallel execution
        if self.resource_manager.max_parallel_tasks > 1:
            total_time *= 0.6  # Rough parallel execution speedup

        return total_time

    def _estimate_task_duration(self, task: CheckTask) -> float:
        """Estimate duration for a single task."""
        time_estimates = {
            "code_quality": 30.0,
            "test_runner": 120.0,
            "security_scanner": 45.0,
            "performance_analyzer": 180.0,
            "ai_component_tester": 90.0,
        }
        return time_estimates.get(task.check_type, 60.0)

    def _estimate_resource_requirements(self, tasks: List[CheckTask]) -> Dict[str, Any]:
        """Estimate resource requirements for tasks."""
        return {
            "max_parallel_tasks": min(
                len(tasks), self.resource_manager.max_parallel_tasks
            ),
            "estimated_memory_usage": len(tasks) * 100,  # MB per task
            "requires_display": any(
                task.check_type in ["test_runner", "ai_component_tester"]
                for task in tasks
            ),
            "requires_network": any(
                task.check_type in ["security_scanner"] for task in tasks
            ),
        }

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage information."""
        try:
            return {
                "active_tasks": self.resource_manager.active_tasks,
                "max_parallel_tasks": self.resource_manager.max_parallel_tasks,
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "available_checks": len(self._available_checks),
                "total_checkers": len(CheckerFactory.get_available_checkers()),
            }
        except Exception as e:
            self.logger.warning(f"Failed to get resource usage: {e}")
            return {
                "active_tasks": self.resource_manager.active_tasks,
                "max_parallel_tasks": self.resource_manager.max_parallel_tasks,
                "error": str(e),
            }
