"""
Base Interfaces and Abstract Classes for CI Simulation Tool

This module defines the core interfaces and abstract base classes
that provide extensibility and consistency across all checker implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

try:
    from .models import CheckResult, CheckTask, ConfigDict, SimulationResult
except ImportError:
    from models import CheckResult, CheckTask, ConfigDict, SimulationResult


class CheckerInterface(ABC):
    """
    Abstract base class for all checker implementations.

    This interface ensures consistency across different types of checks
    (code quality, security, performance, etc.) and provides a common
    contract for the orchestrator to interact with all checkers.
    """

    def __init__(self, config: ConfigDict):
        """
        Initialize the checker with configuration.

        Args:
            config: Configuration dictionary containing checker-specific settings
        """
        self.config = config
        self._is_available: Optional[bool] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable name of this checker."""
        pass

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the type category of this checker (e.g., 'code_quality', 'security')."""
        pass

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """Return list of external dependencies required by this checker."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this checker can run in the current environment.

        Returns:
            True if all dependencies are available and checker can run
        """
        pass

    @abstractmethod
    def run_check(self, **kwargs) -> CheckResult:
        """
        Execute the main check logic.

        Args:
            **kwargs: Checker-specific arguments

        Returns:
            CheckResult containing the outcome of the check
        """
        pass

    def validate_config(self) -> List[str]:
        """
        Validate the checker configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        if not isinstance(self.config, dict):
            errors.append(f"{self.name}: Configuration must be a dictionary")
        return errors

    def get_default_config(self) -> ConfigDict:
        """
        Get default configuration for this checker.

        Returns:
            Dictionary containing default configuration values
        """
        return {}

    def cleanup(self) -> None:
        """
        Perform any necessary cleanup after check execution.

        This method is called after run_check() completes,
        regardless of success or failure.
        """
        pass


class EnvironmentManagerInterface(ABC):
    """
    Abstract base class for environment management components.

    Handles setup and management of execution environments,
    including Python versions, system dependencies, and virtual displays.
    """

    @abstractmethod
    def setup_environment(self, requirements: Dict[str, Any]) -> bool:
        """
        Set up the required environment for testing.

        Args:
            requirements: Dictionary specifying environment requirements

        Returns:
            True if environment setup was successful
        """
        pass

    @abstractmethod
    def cleanup_environment(self) -> None:
        """Clean up any temporary environment changes."""
        pass

    @abstractmethod
    def is_environment_ready(self) -> bool:
        """Check if the environment is properly configured."""
        pass


class ReporterInterface(ABC):
    """
    Abstract base class for report generators.

    Defines the interface for generating reports in different formats
    (Markdown, JSON, HTML, etc.) from simulation results.
    """

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the name of the report format (e.g., 'markdown', 'json')."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this report format (e.g., '.md', '.json')."""
        pass

    @abstractmethod
    def generate_report(self, result: SimulationResult, output_path: str) -> str:
        """
        Generate a report from simulation results.

        Args:
            result: SimulationResult containing all check outcomes
            output_path: Path where the report should be saved

        Returns:
            Path to the generated report file
        """
        pass

    def validate_output_path(self, output_path: str) -> bool:
        """
        Validate that the output path is suitable for this reporter.

        Args:
            output_path: Proposed output path

        Returns:
            True if the path is valid for this reporter
        """
        return output_path.endswith(self.file_extension)


class OrchestratorInterface(ABC):
    """
    Abstract base class for check orchestration.

    Manages the execution of multiple checks, handling dependencies,
    parallel execution, and resource management.
    """

    @abstractmethod
    def execute_checks(self, tasks: List[CheckTask]) -> Dict[str, CheckResult]:
        """
        Execute a list of check tasks.

        Args:
            tasks: List of CheckTask objects to execute

        Returns:
            Dictionary mapping task names to their results
        """
        pass

    @abstractmethod
    def resolve_dependencies(self, task_names: List[str]) -> List[str]:
        """
        Resolve dependencies and return execution order.

        Args:
            task_names: List of task names to execute

        Returns:
            List of task names in dependency-resolved order
        """
        pass


# Protocol definitions for type checking
class Configurable(Protocol):
    """Protocol for objects that can be configured."""

    def configure(self, config: ConfigDict) -> None:
        """Configure the object with the provided configuration."""
        ...


class Validatable(Protocol):
    """Protocol for objects that can validate their state."""

    def validate(self) -> List[str]:
        """Validate the object state and return any error messages."""
        ...


class Serializable(Protocol):
    """Protocol for objects that can be serialized to/from dictionaries."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Serializable":
        """Create object from dictionary representation."""
        ...


# Exception classes for the CI simulation system
class CISimulationError(Exception):
    """Base exception for CI simulation errors."""

    pass


class CheckerError(CISimulationError):
    """Exception raised by checker implementations."""

    def __init__(
        self,
        checker_name: str,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        self.checker_name = checker_name
        self.original_error = original_error
        super().__init__(f"{checker_name}: {message}")


class EnvironmentError(CISimulationError):
    """Exception raised when environment setup fails."""

    pass


class ConfigurationError(CISimulationError):
    """Exception raised for configuration-related errors."""

    pass


class DependencyError(CISimulationError):
    """Exception raised when required dependencies are missing."""

    def __init__(self, missing_dependencies: List[str], message: str = ""):
        self.missing_dependencies = missing_dependencies
        if not message:
            deps_str = ", ".join(missing_dependencies)
            message = f"Missing required dependencies: {deps_str}"
        super().__init__(message)


# Factory interface for creating checker instances
class CheckerFactory:
    """
    Factory class for creating checker instances.

    Provides a centralized way to instantiate checkers with proper
    configuration and dependency injection.
    """

    _checkers: Dict[str, type] = {}

    @classmethod
    def register_checker(cls, check_type: str, checker_class: type) -> None:
        """
        Register a checker class for a specific check type.

        Args:
            check_type: String identifier for the check type
            checker_class: Class that implements CheckerInterface
        """
        if not issubclass(checker_class, CheckerInterface):
            raise ValueError(f"Checker class must implement CheckerInterface")
        cls._checkers[check_type] = checker_class

    @classmethod
    def create_checker(cls, check_type: str, config: ConfigDict) -> CheckerInterface:
        """
        Create a checker instance for the specified type.

        Args:
            check_type: String identifier for the check type
            config: Configuration dictionary for the checker

        Returns:
            Configured checker instance

        Raises:
            ValueError: If check_type is not registered
        """
        if check_type not in cls._checkers:
            available = ", ".join(cls._checkers.keys())
            raise ValueError(
                f"Unknown check type '{check_type}'. Available: {available}"
            )

        checker_class = cls._checkers[check_type]
        return checker_class(config)

    @classmethod
    def get_available_checkers(cls) -> List[str]:
        """Get list of available checker types."""
        return list(cls._checkers.keys())

    @classmethod
    def is_checker_available(cls, check_type: str) -> bool:
        """Check if a checker type is available."""
        return check_type in cls._checkers
