# CI Simulation Tool - API Reference

## Overview

This document provides comprehensive API documentation for the CI Simulation Tool. It covers all public classes, interfaces, methods, and configuration options available for developers who want to extend or integrate with the tool.

## Table of Contents

1. [Core Models](#core-models)
2. [Interfaces](#interfaces)
3. [Configuration](#configuration)
4. [Utilities](#utilities)
5. [Error Handling](#error-handling)
6. [Extension APIs](#extension-apis)

## Core Models

### CheckResult

Represents the result of a single check execution.

```python
@dataclass
class CheckResult:
    """Result of a single check execution."""

    name: str                      # Check name
    status: CheckStatus            # Execution status
    duration: float        # Execution time in seconds
    output: str                    # Check output
    errors: List[str]              # Error messages
    warnings: List[str]            # Warning messages
    suggestions: List[str]         # Improvement suggestions
    metadata: Dict[str, Any]       # Additional metadata
    timestamp: datetime            # Execution timestamp
    python_version: Optional[str]  # Python version used
```

**Properties:**
- `is_successful: bool` - True if status is SUCCESS
- `has_errors: bool` - True if errors list is not empty
- `has_warnings: bool` - True if warnings list is not empty

**Methods:**
- `to_dict() -> Dict[str, Any]` - Convert to dictionary
- `from_dict(data: Dict[str, Any]) -> CheckResult` - Create from dictionary
- `save_to_file(path: str) -> None` - Save to JSON file
- `load_from_file(path: str) -> CheckResult` - Load from JSON file

### CheckStatus

Enumeration of possible check statuses.

```python
class CheckStatus(Enum):
    """Possible check execution statuses."""

    SUCCESS = "success"     # Check passed successfully
    FAILURE = "failure"     # Check failed with errors
    WARNING = "warning"     # Check passed with warnings
    SKIPPED = "skipped"     # Check was skipped
```

### SimulationResult

Represents the result of a complete CI simulation run.

```python
@dataclass
class SimulationResult:
    """Result of a complete CI simulation."""

    overall_status: CheckStatus           # Overall execution status
    total_duration: float                 # Total execution time
    check_results: Dict[str, CheckResult] # Individual check results
    python_versions_tested: List[str]     # Python versions tested
    summary: str                          # Execution summary
    report_paths: Dict[str, str]          # Generated report paths
    regression_issues: List[RegressionIssue] # Performance regressions
    timestamp: datetime                   # Execution timestamp
    configuration: Dict[str, Any]         # Configuration used
```

**Properties:**
- `is_successful: bool` - True if overall status is SUCCESS
- `failed_checks: List[CheckResult]` - List of failed checks
- `warning_checks: List[CheckResult]` - List of checks with warnings
- `successful_checks: List[CheckResult]` - List of successful checks

**Methods:**
- `to_dict() -> Dict[str, Any]` - Convert to dictionary
- `save_to_file(path: str) -> None` - Save to JSON file
- `get_check_result(name: str) -> Optional[CheckResult]` - Get specific check result

### CheckTask

Represents a task to be executed by the orchestrator.

```python
@dataclass
class CheckTask:
    """A task to be executed by the check orchestrator."""

    name: str                      # Task name
    check_type: str                # Type of check to run
    config: Dict[str, Any]         # Task-specific configuration
    dependencies: List[str]        # Required dependencies
    python_version: Optional[str]  # Python version to use
    timeout: Optional[int]         # Task timeout in seconds
    priority: int                  # Execution priority (higher = first)
```

**Methods:**
- `is_ready(completed_tasks: Set[str]) -> bool` - Check if dependencies are met
- `to_dict() -> Dict[str, Any]` - Convert to dictionary

### RegressionIssue

Represents a performance regression detected during analysis.

```python
@dataclass
class RegressionIssue:
    """A performance regression issue."""

    test_name: str                 # Name of the test
    baseline_value: float          # Baseline performance value
    current_value: float           # Current performance value
    regression_percentage: float   # Percentage regression
    severity: SeverityLevel        # Issue severity
    description: str               # Human-readable description
    metric_type: str               # Type of metric (time, memory, etc.)
    threshold_exceeded: bool       # Whether threshold was exceeded
```

### SeverityLevel

Enumeration of issue severity levels.

```python
class SeverityLevel(Enum):
    """Severity levels for issues."""

    CRITICAL = "critical"   # Critical issues requiring immediate attention
    HIGH = "high"          # High priority issues
    MEDIUM = "medium"      # Medium priority issues
    LOW = "low"           # Low priority issues
    INFO = "info"         # Informational messages
```

## Interfaces

### CheckerInterface

Abstract base class for all checker implementations.

```python
class CheckerInterface(ABC):
    """Abstract base class for all checkers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the checker name."""
        pass

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the checker type."""
        pass

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """Return list of required dependencies."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the checker can run in current environment."""
        pass

    @abstractmethod
    def run_check(self, **kwargs) -> CheckResult:
        """Execute the check and return results."""
        pass

    def _setup(self) -> None:
        """Setup method called before check execution."""
        pass

    def _cleanup(self) -> None:
        """Cleanup method called after check execution."""
        pass

    def _handle_error(self, error: Exception) -> CheckResult:
        """Handle errors during check execution."""
        return CheckResult(
            name=self.name,
            status=CheckStatus.FAILURE,
            duration=0.0,
            output="",
            errors=[str(error)],
            warnings=[],
            suggestions=["Check the logs for more details"],
            metadata={}
        )
```

### ReporterInterface

Abstract base class for all reporter implementations.

```python
class ReporterInterface(ABC):
    """Abstract base class for all reporters."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name (e.g., 'markdown', 'json')."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension (e.g., '.md', '.json')."""
        pass

    @abstractmethod
    def generate_report(self, result: SimulationResult, output_path: str) -> str:
        """Generate a report and return the output path."""
        pass

    def validate_result(self, result: SimulationResult) -> List[str]:
        """Validate the simulation result before generating report."""
        errors = []
        if not result.check_results:
            errors.append("No check results to report")
        return errors
```

### EnvironmentManagerInterface

Abstract base class for environment managers.

```python
class EnvironmentManagerInterface(ABC):
    """Abstract base class for environment managers."""

    @abstractmethod
    def setup_environment(self, requirements: Dict[str, Any]) -> bool:
        """Set up the environment for check execution."""
        pass

    @abstractmethod
    def cleanup_environment(self) -> None:
        """Clean up the environment after execution."""
        pass

    @abstractmethod
    def is_environment_ready(self) -> bool:
        """Check if the environment is ready for execution."""
        pass

    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about the current environment."""
        return {}
```

### OrchestratorInterface

Abstract base class for check orchestrators.

```python
class OrchestratorInterface(ABC):
    """Abstract base class for check orchestrators."""

    @abstractmethod
    def execute_checks(self, tasks: List[CheckTask]) -> Dict[str, CheckResult]:
        """Execute a list of check tasks."""
        pass

    @abstractmethod
    def get_available_checks(self) -> List[str]:
        """Get list of available check types."""
        pass

    def validate_tasks(self, tasks: List[CheckTask]) -> List[str]:
        """Validate a list of tasks before execution."""
        return []
```

## Configuration

### ConfigDict

Type alias for configuration dictionaries.

```python
ConfigDict = Dict[str, Any]
```

### Configuration Schema

The configuration follows this schema:

```python
CONFIG_SCHEMA = {
    "project": {
        "name": str,
        "type": str,
        "description": Optional[str]
    },
    "python_versions": List[str],
    "checks": {
        str: {  # Check name
            "enabled": bool,
            "timeout": Optional[int],
            # Check-specific configuration
        }
    },
    "execution": {
        "max_parallel": int,
        "timeout": int,
        "fail_fast": bool
    },
    "output": {
        "directory": str,
        "formats": List[str],
        "keep_history": int
    },
    "directories": {
        "temp": str,
        "logs": str,
        "reports": str,
        "history": str
    }
}
```

### Configuration Manager

```python
class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional config file path."""
        pass

    def get_config(self) -> ConfigDict:
        """Get the complete configuration."""
        pass

    def get_check_config(self, check_name: str) -> ConfigDict:
        """Get configuration for a specific check."""
        pass

    def validate_config(self, config: ConfigDict) -> List[str]:
        """Validate configuration and return errors."""
        pass

    def update_gitignore(self) -> None:
        """Update .gitignore with CI simulation entries."""
        pass

    def get_python_versions(self) -> List[str]:
        """Get list of Python versions to test."""
        pass

    def is_check_enabled(self, check_name: str) -> bool:
        """Check if a specific check is enabled."""
        pass
```

## Utilities

### Command Execution

```python
def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:
    """
    Run a command and return the result.

    Args:
        cmd: Command and arguments to run
        cwd: Working directory
        timeout: Timeout in seconds
        env: Environment variables

    Returns:
        CompletedProcess with result

    Raises:
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails
    """
    pass
```

### Tool Availability

```python
def is_tool_available(tool_name: str) -> bool:
    """
    Check if a tool is available in the system PATH.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool is available, False otherwise
    """
    pass
```

### File System Utilities

```python
def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    pass

def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to project root
    """
    pass

def find_files(
    pattern: str,
    directory: Union[str, Path] = ".",
    recursive: bool = True
) -> List[Path]:
    """
    Find files matching a pattern.

    Args:
        pattern: Glob pattern to match
        directory: Directory to search in
        recursive: Whether to search recursively

    Returns:
        List of matching file paths
    """
    pass
```

### Python Environment

```python
def get_python_executable(version: Optional[str] = None) -> Optional[str]:
    """
    Get path to Python executable for a specific version.

    Args:
        version: Python version (e.g., '3.10')

    Returns:
        Path to Python executable or None if not found
    """
    pass

def get_python_version(executable: str) -> Optional[str]:
    """
    Get Python version for an executable.

    Args:
        executable: Path to Python executable

    Returns:
        Version string or None if not available
    """
    pass
```

### Formatting Utilities

```python
def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    pass

def format_file_size(bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        bytes: Size in bytes

    Returns:
        Formatted size string
    """
    pass
```

### Git Utilities

```python
def get_git_info() -> Dict[str, Any]:
    """
    Get Git repository information.

    Returns:
        Dictionary with Git information
    """
    pass

def is_git_repository(path: Union[str, Path] = ".") -> bool:
    """
    Check if a directory is a Git repository.

    Args:
        path: Directory path to check

    Returns:
        True if it's a Git repository
    """
    pass
```

## Error Handling

### Exception Classes

```python
class CISimulationError(Exception):
    """Base exception for CI simulation errors."""
    pass

class CheckerError(CISimulationError):
    """Error in checker execution."""

    def __init__(self, checker_name: str, message: str):
        self.checker_name = checker_name
        super().__init__(f"Checker '{checker_name}': {message}")

class ConfigurationError(CISimulationError):
    """Error in configuration."""
    pass

class EnvironmentError(CISimulationError):
    """Error in environment setup."""
    pass

class DependencyError(CISimulationError):
    """Error with dependencies."""
    pass

class TimeoutError(CISimulationError):
    """Timeout during execution."""

    def __init__(self, operation: str, timeout: int):
        self.operation = operation
        self.timeout = timeout
        super().__init__(f"Operation '{operation}' timed out after {timeout} seconds")
```

### Error Handler

```python
class ErrorHandler:
    """Handles errors and provides recovery strategies."""

    def __init__(self, config: ConfigDict):
        """Initialize with configuration."""
        pass

    def handle_checker_error(
        self,
        error: Exception,
        checker_name: str,
        context: Dict[str, Any]
    ) -> CheckResult:
        """
        Handle errors from checker execution.

        Args:
            error: The exception that occurred
            checker_name: Name of the checker
            context: Additional context information

        Returns:
            CheckResult with error information
        """
        pass

    def handle_timeout_error(
        self,
        operation: str,
        timeout: int,
        context: Dict[str, Any]
    ) -> CheckResult:
        """
        Handle timeout errors.

        Args:
            operation: Operation that timed out
            timeout: Timeout value in seconds
            context: Additional context information

        Returns:
            CheckResult with timeout information
        """
        pass

    def suggest_recovery_actions(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Suggest recovery actions for an error.

        Args:
            error: The exception that occurred
            context: Additional context information

        Returns:
            List of suggested recovery actions
        """
        pass
```

## Extension APIs

### Factory Classes

#### CheckerFactory

```python
class CheckerFactory:
    """Factory for creating checker instances."""

    _checkers: Dict[str, Type[CheckerInterface]] = {}

    @classmethod
    def register_checker(
        cls,
        name: str,
        checker_class: Type[CheckerInterface]
    ) -> None:
        """
        Register a checker class.

        Args:
            name: Checker name
            checker_class: Checker class
        """
        pass

    @classmethod
    def create_checker(
        cls,
        name: str,
        config: ConfigDict
    ) -> CheckerInterface:
        """
        Create a checker instance.

        Args:
            name: Checker name
            config: Configuration for the checker

        Returns:
            Checker instance

        Raises:
            ValueError: If checker is not registered
        """
        pass

    @classmethod
    def get_available_checkers(cls) -> List[str]:
        """Get list of available checker names."""
        pass

    @classmethod
    def is_checker_available(cls, name: str) -> bool:
        """Check if a checker is available."""
        pass
```

#### ReporterFactory

```python
class ReporterFactory:
    """Factory for creating reporter instances."""

    _reporters: Dict[str, Type[ReporterInterface]] = {}

    @classmethod
    def register_reporter(
        cls,
        format_name: str,
        reporter_class: Type[ReporterInterface]
    ) -> None:
        """Register a reporter class."""
        pass

    @classmethod
    def create_reporter(
        cls,
        format_name: str,
        config: ConfigDict
    ) -> ReporterInterface:
        """Create a reporter instance."""
        pass

    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of available report formats."""
        pass
```

### Plugin System

```python
class PluginManager:
    """Manages plugins and extensions."""

    def __init__(self):
        """Initialize the plugin manager."""
        pass

    def load_plugins(self, plugin_dir: Union[str, Path]) -> None:
        """
        Load plugins from a directory.

        Args:
            plugin_dir: Directory containing plugins
        """
        pass

    def register_plugin(self, plugin: Any) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance
        """
        pass

    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names."""
        pass
```

### Hooks System

```python
class HookManager:
    """Manages execution hooks."""

    def __init__(self):
        """Initialize the hook manager."""
        pass

    def register_hook(
        self,
        event: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a hook for an event.

        Args:
            event: Event name
            callback: Callback function
        """
        pass

    def trigger_hook(self, event: str, context: Dict[str, Any]) -> None:
        """
        Trigger hooks for an event.

        Args:
            event: Event name
            context: Event context
        """
        pass

    def get_registered_hooks(self) -> Dict[str, List[Callable]]:
        """Get all registered hooks."""
        pass
```

### Available Hook Events

- `before_simulation_start`: Before simulation starts
- `after_simulation_complete`: After simulation completes
- `before_check_start`: Before individual check starts
- `after_check_complete`: After individual check completes
- `on_error`: When an error occurs
- `on_timeout`: When a timeout occurs

## Usage Examples

### Creating a Custom Checker

```python
from interfaces import CheckerInterface, CheckerFactory
from models import CheckResult, CheckStatus

class MyCustomChecker(CheckerInterface):
    def __init__(self, config):
        self.config = config

    @property
    def name(self) -> str:
        return "my_custom_checker"

    @property
    def check_type(self) -> str:
        return "custom"

    @property
    def dependencies(self) -> List[str]:
        return []

    def is_available(self) -> bool:
        return True

    def run_check(self, **kwargs) -> CheckResult:
        # Implementation here
        return CheckResult(
            name=self.name,
            status=CheckStatus.SUCCESS,
            duration=1.0,
            output="Custom check completed",
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={}
        )

# Register the checker
CheckerFactory.register_checker('my_custom_checker', MyCustomChecker)
```

### Using the Configuration Manager

```python
from config_manager import ConfigManager

# Load configuration
config_manager = ConfigManager('my-config.yml')
config = config_manager.get_config()

# Get check-specific configuration
code_quality_config = config_manager.get_check_config('code_quality')

# Check if a check is enabled
if config_manager.is_check_enabled('security_scanner'):
    print("Security scanner is enabled")
```

### Creating a Custom Reporter

```python
from interfaces import ReporterInterface, ReporterFactory
from models import SimulationResult

class MyCustomReporter(ReporterInterface):
    def __init__(self, config):
        self.config = config

    @property
    def format_name(self) -> str:
        return "custom"

    @property
    def file_extension(self) -> str:
        return ".custom"

    def generate_report(self, result: SimulationResult, output_path: str) -> str:
        # Implementation here
        with open(output_path, 'w') as f:
            f.write(f"Custom report for {result.timestamp}")
        return output_path

# Register the reporter
ReporterFactory.register_reporter('custom', MyCustomReporter)
```

This API reference provides comprehensive documentation for all public interfaces and classes in the CI Simulation Tool. Use this reference when extending the tool or integrating it with other systems.
