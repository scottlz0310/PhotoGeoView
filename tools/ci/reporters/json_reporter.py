"""
JSON Report Generator for CI Simulation Results

This module provides comprehensive JSON report generation capabilities,
creating structured, machadable reports for CI integration and API compatibility.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..interfaces import ReporterInterface
from ..models import (
    CheckResult,
    CheckStatus,
    RegressionIssue,
    SeverityLevel,
    SimulationResult,
)


class JSONReporter(ReporterInterface):
    """
    Comprehensive JSON report generator for CI simulation results.

    Generates structured, machine-readable reports with:
    - Complete simulation results in JSON format
    - CI/CD pipeline integration compatibility
    - API-compatible result structures
    - Detailed metadata for automated processing
    """

    @property
    def format_name(self) -> str:
        """Return the name of the report format."""
        return "json"

    @property
    def file_extension(self) -> str:
        """Return the file extension for JSON reports."""
        return ".json"

    def generate_report(self, result: SimulationResult, output_path: str) -> str:
        """
        Generate a comprehensive JSON report from simulation results.

        Args:
            result: SimulationResult containing all check outcomes
            output_path: Path where the report should be saved

        Returns:
            Path to the generated report file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generate report data
        report_data = self._generate_report_data(result)

        # Write to file with proper formatting
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                report_data,
                f,
                indent=2,
                ensure_ascii=False,
                default=self._json_serializer,
            )

        return output_path

    def _generate_report_data(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate the complete JSON report data structure."""
        return {
            "report_metadata": self._generate_report_metadata(result),
            "execution_summary": self._generate_execution_summary(result),
            "check_results": self._generate_check_results_data(result),
            "regression_analysis": self._generate_regression_data(result),
            "error_analysis": self._generate_error_analysis_data(result),
            "performance_metrics": self._generate_performance_metrics(result),
            "configuration": result.configuration,
            "ci_integration": self._generate_ci_integration_data(result),
            "api_compatibility": self._generate_api_compatibility_data(result),
        }

    def _generate_report_metadata(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate report metadata section."""
        return {
            "report_version": "1.0.0",
            "generator": "PhotoGeoView CI Simulation Tool",
            "format": "json",
            "generated_at": result.timestamp.isoformat(),
            "report_id": f"ci-sim-{result.timestamp.strftime('%Y%m%d-%H%M%S')}",
            "schema_version": "1.0",
        }

    def _generate_execution_summary(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate execution summary section."""
        total_checks = len(result.check_results)
        successful_checks = len(result.successful_checks)
        failed_checks = len(result.failed_checks)

        return {
            "overall_status": result.overall_status.value,
            "total_duration": result.total_duration,
            "summary_text": result.summary,
            "statistics": {
                "total_checks": total_checks,
                "successful_checks": successful_checks,
                "failed_checks": failed_checks,
                "success_rate": (
                    (successful_checks / total_checks * 100) if total_checks > 0 else 0
                ),
                "checks_by_status": {
                    status.value: len(result.get_checks_by_status(status))
                    for status in CheckStatus
                },
            },
            "python_versions_tested": result.python_versions_tested,
            "regression_count": len(result.regression_issues),
            "has_critical_issues": any(
                issue.severity == SeverityLevel.CRITICAL
                for issue in result.regression_issues
            )
            or any(not check.is_successful for check in result.check_results.values()),
        }

    def _generate_check_results_data(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate detailed check results data."""
        check_results_data = {}

        for check_name, check_result in result.check_results.items():
            check_results_data[check_name] = {
                "name": check_result.name,
                "status": check_result.status.value,
                "duration": check_result.duration,
                "timestamp": check_result.timestamp.isoformat(),
                "python_version": check_result.python_version,
                "output": check_result.output,
                "errors": check_result.errors,
                "warnings": check_result.warnings,
                "suggestions": check_result.suggestions,
                "metadata": check_result.metadata,
                "is_successful": check_result.is_successful,
                "has_errors": check_result.has_errors,
                "issue_count": len(check_result.errors) + len(check_result.warnings),
            }

        return {
            "individual_results": check_results_data,
            "summary_by_status": {
                status.value: [
                    check_name
                    for check_name, check_result in result.check_results.items()
                    if check_result.status == status
                ]
                for status in CheckStatus
            },
            "failed_checks_details": [
                {
                    "name": check.name,
                    "errors": check.errors,
                    "duration": check.duration,
                    "python_version": check.python_version,
                }
                for check in result.failed_checks
            ],
        }

    def _generate_regression_data(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate regression analysis data."""
        if not result.regression_issues:
            return {
                "has_regressions": False,
                "total_regressions": 0,
                "regressions_by_severity": {},
                "regression_details": [],
            }

        # Group by severity
        by_severity = {}
        for issue in result.regression_issues:
            severity = issue.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue.to_dict())

        return {
            "has_regressions": True,
            "total_regressions": len(result.regression_issues),
            "regressions_by_severity": {
                severity: len(issues) for severity, issues in by_severity.items()
            },
            "regression_details": [
                issue.to_dict() for issue in result.regression_issues
            ],
            "critical_regressions": [
                issue.to_dict()
                for issue in result.regression_issues
                if issue.severity == SeverityLevel.CRITICAL
            ],
            "performance_impact": self._calculate_performance_impact(
                result.regression_issues
            ),
        }

    def _generate_error_analysis_data(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate error analysis data."""
        all_errors = []
        all_warnings = []

        for check_result in result.check_results.values():
            for error in check_result.errors:
                all_errors.append(
                    {
                        "check_name": check_result.name,
                        "error_message": error,
                        "python_version": check_result.python_version,
                        "timestamp": check_result.timestamp.isoformat(),
                    }
                )

            for warning in check_result.warnings:
                all_warnings.append(
                    {
                        "check_name": check_result.name,
                        "warning_message": warning,
                        "python_version": check_result.python_version,
                        "timestamp": check_result.timestamp.isoformat(),
                    }
                )

        # Categorize errors
        error_categories = self._categorize_errors_for_json(all_errors)

        return {
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "errors": all_errors,
            "warnings": all_warnings,
            "error_categories": error_categories,
            "error_patterns": self._identify_error_patterns(all_errors),
            "most_common_errors": self._get_most_common_errors(all_errors),
        }

    def _generate_performance_metrics(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate performance metrics data."""
        check_durations = {
            name: check.duration for name, check in result.check_results.items()
        }

        durations = list(check_durations.values())

        return {
            "total_execution_time": result.total_duration,
            "check_durations": check_durations,
            "performance_statistics": {
                "average_check_duration": (
                    sum(durations) / len(durations) if durations else 0
                ),
                "longest_check": (
                    max(check_durations.items(), key=lambda x: x[1])
                    if durations
                    else None
                ),
                "shortest_check": (
                    min(check_durations.items(), key=lambda x: x[1])
                    if durations
                    else None
                ),
                "total_checks": len(durations),
            },
            "performance_thresholds": {
                "slow_checks": [
                    {"name": name, "duration": duration}
                    for name, duration in check_durations.items()
                    if duration > 30.0  # Checks taking more than 30 seconds
                ],
                "very_slow_checks": [
                    {"name": name, "duration": duration}
                    for name, duration in check_durations.items()
                    if duration > 60.0  # Checks taking more than 1 minute
                ],
            },
        }

    def _generate_ci_integration_data(self, result: SimulationResult) -> Dict[str, Any]:
        """Generate CI/CD integration compatible data."""
        return {
            "exit_code": 0 if result.is_successful else 1,
            "build_status": "PASSED" if result.is_successful else "FAILED",
            "test_results": {
                "total": len(result.check_results),
                "passed": len(result.successful_checks),
                "failed": len(result.failed_checks),
                "skipped": len(result.get_checks_by_status(CheckStatus.SKIPPED)),
            },
            "artifacts": {
                "reports": result.report_paths,
                "logs": self._get_log_file_paths(),
                "test_outputs": self._extract_test_outputs(result),
            },
            "environment": {
                "python_versions": result.python_versions_tested,
                "timestamp": result.timestamp.isoformat(),
                "duration": result.total_duration,
            },
            "quality_gates": {
                "passed": result.is_successful,
                "success_rate_threshold": 90.0,
                "actual_success_rate": (
                    len(result.successful_checks) / len(result.check_results) * 100
                    if result.check_results
                    else 0
                ),
                "critical_issues": len(
                    [
                        issue
                        for issue in result.regression_issues
                        if issue.severity == SeverityLevel.CRITICAL
                    ]
                ),
            },
        }

    def _generate_api_compatibility_data(
        self, result: SimulationResult
    ) -> Dict[str, Any]:
        """Generate API-compatible result structure."""
        return {
            "version": "1.0",
            "result": {
                "status": result.overall_status.value,
                "success": result.is_successful,
                "duration": result.total_duration,
                "timestamp": result.timestamp.isoformat(),
            },
            "checks": [
                {
                    "id": name,
                    "name": check.name,
                    "status": check.status.value,
                    "success": check.is_successful,
                    "duration": check.duration,
                    "errors": len(check.errors),
                    "warnings": len(check.warnings),
                    "metadata": check.metadata,
                }
                for name, check in result.check_results.items()
            ],
            "summary": {
                "total": len(result.check_results),
                "passed": len(result.successful_checks),
                "failed": len(result.failed_checks),
                "success_rate": (
                    len(result.successful_checks) / len(result.check_results) * 100
                    if result.check_results
                    else 0
                ),
            },
            "regressions": [
                {
                    "test": issue.test_name,
                    "severity": issue.severity.value,
                    "change": issue.regression_percentage,
                    "description": issue.description,
                }
                for issue in result.regression_issues
            ],
        }

    def _calculate_performance_impact(
        self, regression_issues: List[RegressionIssue]
    ) -> Dict[str, Any]:
        """Calculate overall performance impact from regressions."""
        if not regression_issues:
            return {"total_impact": 0, "average_regression": 0, "worst_regression": 0}

        performance_regressions = [
            issue for issue in regression_issues if issue.metric_type == "performance"
        ]

        if not performance_regressions:
            return {"total_impact": 0, "average_regression": 0, "worst_regression": 0}

        regression_percentages = [
            abs(issue.regression_percentage) for issue in performance_regressions
        ]

        return {
            "total_impact": sum(regression_percentages),
            "average_regression": sum(regression_percentages)
            / len(regression_percentages),
            "worst_regression": max(regression_percentages),
            "affected_tests": len(performance_regressions),
        }

    def _categorize_errors_for_json(
        self, errors: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize errors for JSON output."""
        categories = {
            "syntax_errors": [],
            "import_errors": [],
            "type_errors": [],
            "test_failures": [],
            "security_issues": [],
            "performance_issues": [],
            "configuration_errors": [],
            "other_errors": [],
        }

        for error in errors:
            error_message = error["error_message"].lower()

            if any(
                keyword in error_message
                for keyword in ["syntax", "invalid syntax", "unexpected token"]
            ):
                categories["syntax_errors"].append(error)
            elif any(
                keyword in error_message
                for keyword in ["import", "module", "no module named"]
            ):
                categories["import_errors"].append(error)
            elif any(
                keyword in error_message for keyword in ["type", "mypy", "annotation"]
            ):
                categories["type_errors"].append(error)
            elif any(
                keyword in error_message for keyword in ["test", "assert", "failed"]
            ):
                categories["test_failures"].append(error)
            elif any(
                keyword in error_message
                for keyword in ["security", "vulnerability", "bandit", "safety"]
            ):
                categories["security_issues"].append(error)
            elif any(
                keyword in error_message
                for keyword in ["performance", "slow", "timeout", "memory"]
            ):
                categories["performance_issues"].append(error)
            elif any(
                keyword in error_message
                for keyword in ["config", "configuration", "setting"]
            ):
                categories["configuration_errors"].append(error)
            else:
                categories["other_errors"].append(error)

        return categories

    def _identify_error_patterns(
        self, errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify common error patterns."""
        error_counts = {}

        for error in errors:
            # Normalize error message for pattern matching
            normalized = self._normalize_error_message(error["error_message"])
            if normalized not in error_counts:
                error_counts[normalized] = {
                    "pattern": normalized,
                    "count": 0,
                    "checks": [],
                    "example": error["error_message"],
                }
            error_counts[normalized]["count"] += 1
            error_counts[normalized]["checks"].append(error["check_name"])

        # Return patterns sorted by frequency
        patterns = list(error_counts.values())
        patterns.sort(key=lambda x: x["count"], reverse=True)

        return patterns[:10]  # Top 10 patterns

    def _normalize_error_message(self, error_message: str) -> str:
        """Normalize error message for pattern matching."""
        import re

        # Remove file paths and line numbers
        normalized = re.sub(r"/[^\s]+\.py:\d+", "<file>:<line>", error_message)
        normalized = re.sub(r"line \d+", "line <num>", normalized)
        normalized = re.sub(r"\d+", "<num>", normalized)

        # Remove quotes around variable names
        normalized = re.sub(r"'[^']*'", "<var>", normalized)
        normalized = re.sub(r'"[^"]*"', "<var>", normalized)

        return normalized.strip()

    def _get_most_common_errors(
        self, errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get most common error messages."""
        error_counts = {}

        for error in errors:
            message = error["error_message"]
            if message not in error_counts:
                error_counts[message] = {"message": message, "count": 0, "checks": []}
            error_counts[message]["count"] += 1
            error_counts[message]["checks"].append(error["check_name"])

        # Return top 5 most common errors
        common_errors = list(error_counts.values())
        common_errors.sort(key=lambda x: x["count"], reverse=True)

        return common_errors[:5]

    def _get_log_file_paths(self) -> List[str]:
        """Get paths to log files that might be generated."""
        log_paths = []
        log_dir = Path("logs")

        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                log_paths.append(str(log_file))

        return log_paths

    def _extract_test_outputs(self, result: SimulationResult) -> Dict[str, str]:
        """Extract test outputs from check results."""
        test_outputs = {}

        for check_name, check_result in result.check_results.items():
            if check_result.output.strip():
                test_outputs[check_name] = check_result.output.strip()

        return test_outputs

    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)
