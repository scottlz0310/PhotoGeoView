"""
Core Data Models for CI Simulation Tool

This module defines the fundamental data structures used throughout
the CI simulation system, including check results, simulation outcomes,
and regression analysis data.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json


class CheckStatus(Enum):
    """Status enumeration for check results."""

    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class SeverityLevel(Enum):
    """Severity levels for issues and regressions."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CheckResult:
    """
    Represents the result of a single CI check.

    This is the fundamental unit of check execution results,
    containing all necessary information about what was checked,
    the outcome, and any associated metadata.
    """

    name: str
    status: CheckStatus
    duration: float
    output: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    python_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert CheckResult to dictionary for serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "duration": self.duration,
            "output": self.output,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "python_version": self.python_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckResult":
        """Create CheckResult from dictionary."""
        return cls(
            name=data["name"],
            status=CheckStatus(data["status"]),
            duration=data["duration"],
            output=data.get("output", ""),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            suggestions=data.get("suggestions", []),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now().isoformat())
            ),
            python_version=data.get("python_version"),
        )

    @property
    def is_successful(self) -> bool:
        """Check if the result represents a successful check."""
        return self.status in [CheckStatus.SUCCESS, CheckStatus.WARNING]

    @property
    def has_errors(self) -> bool:
        """Check if the result has any errors."""
        return len(self.errors) > 0 or self.status == CheckStatus.FAILURE


@dataclass
class RegressionIssue:
    """
    Represents a performance or quality regression detected during analysis.

    Used primarily by the performance analyzer to track degradations
    in benchmark results or other measurable metrics.
    """

    test_name: str
    baseline_value: float
    current_value: float
    regression_percentage: float
    severity: SeverityLevel
    description: str
    metric_type: str = "performance"  # performance, memory, quality, etc.
    threshold_exceeded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert RegressionIssue to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "regression_percentage": self.regression_percentage,
            "severity": self.severity.value,
            "description": self.description,
            "metric_type": self.metric_type,
            "threshold_exceeded": self.threshold_exceeded,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionIssue":
        """Create RegressionIssue from dictionary."""
        return cls(
            test_name=data["test_name"],
            baseline_value=data["baseline_value"],
            current_value=data["current_value"],
            regression_percentage=data["regression_percentage"],
            severity=SeverityLevel(data["severity"]),
            description=data["description"],
            metric_type=data.get("metric_type", "performance"),
            threshold_exceeded=data.get("threshold_exceeded", False),
        )


@dataclass
class SimulationResult:
    """
    Comprehensive result of a complete CI simulation run.

    This aggregates all individual check results and provides
    overall status and summary information for the entire simulation.
    """

    overall_status: CheckStatus
    total_duration: float
    check_results: Dict[str, CheckResult]
    python_versions_tested: List[str]
    summary: str
    report_paths: Dict[str, str] = field(default_factory=dict)  # format -> path
    regression_issues: List[RegressionIssue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    configuration: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert SimulationResult to dictionary for serialization."""
        return {
            "overall_status": self.overall_status.value,
            "total_duration": self.total_duration,
            "check_results": {
                name: result.to_dict() for name, result in self.check_results.items()
            },
            "python_versions_tested": self.python_versions_tested,
            "summary": self.summary,
            "report_paths": self.report_paths,
            "regression_issues": [issue.to_dict() for issue in self.regression_issues],
            "timestamp": self.timestamp.isoformat(),
            "configuration": self.configuration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationResult":
        """Create SimulationResult from dictionary."""
        return cls(
            overall_status=CheckStatus(data["overall_status"]),
            total_duration=data["total_duration"],
            check_results={
                name: CheckResult.from_dict(result_data)
                for name, result_data in data.get("check_results", {}).items()
            },
            python_versions_tested=data.get("python_versions_tested", []),
            summary=data.get("summary", ""),
            report_paths=data.get("report_paths", {}),
            regression_issues=[
                RegressionIssue.from_dict(issue_data)
                for issue_data in data.get("regression_issues", [])
            ],
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now().isoformat())
            ),
            configuration=data.get("configuration", {}),
        )

    @property
    def is_successful(self) -> bool:
        """Check if the overall simulation was successful."""
        return self.overall_status in [CheckStatus.SUCCESS, CheckStatus.WARNING]

    @property
    def failed_checks(self) -> List[CheckResult]:
        """Get list of failed checks."""
        return [
            result for result in self.check_results.values() if not result.is_successful
        ]

    @property
    def successful_checks(self) -> List[CheckResult]:
        """Get list of successful checks."""
        return [
            result for result in self.check_results.values() if result.is_successful
        ]

    def get_checks_by_status(self, status: CheckStatus) -> List[CheckResult]:
        """Get all checks with a specific status."""
        return [
            result for result in self.check_results.values() if result.status == status
        ]

    def save_to_file(self, filepath: str) -> None:
        """Save simulation result to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> "SimulationResult":
        """Load simulation result from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class CheckTask:
    """
    Represents a task to be executed by the check orchestrator.

    Used internally by the orchestrator to manage check execution,
    dependencies, and resource allocation.
    """

    name: str
    check_type: str
    python_version: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    priority: int = 0  # Higher numbers = higher priority
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate task configuration after initialization."""
        if not self.name:
            raise ValueError("Task name cannot be empty")
        if not self.check_type:
            raise ValueError("Check type cannot be empty")


# Type aliases for better code readability
CheckResultDict = Dict[str, CheckResult]
ConfigDict = Dict[str, Any]
MetadataDict = Dict[str, Any]
