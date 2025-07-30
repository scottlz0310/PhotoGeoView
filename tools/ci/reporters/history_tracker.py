"""
History Tracking and Trend Analysis for CI Simulation Results

This module provides comprehensive history tracking capabilities,
storing execution results and analyzing trends over time to provide
improvement suggestions and quality metrics tracking.
"""

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List, Optional, Tuple

from ..models import (
    CheckResult,
    CheckStatus,
    RegressionIssue,
    SeverityLevel,
    SimulationResult,
)


@dataclass
class TrendData:
    """Represents trend data for a specific metric over time."""

    metric_name: str
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    trend_direction: str = "stable"  # "improving", "degrading", "stable"
    trend_strength: float = 0.0  # -1.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "values": self.values,
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
        }


@dataclass
class QualityMetrics:
    """Quality metrics for a specific time period."""

    timestamp: datetime
    success_rate: float
    total_checks: int
    failed_checks: int
    total_duration: float
    regression_count: int
    critical_issues: int
    error_count: int
    warning_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "success_rate": self.success_rate,
            "t": self.total_checks,
            "failed_checks": self.failed_checks,
            "total_duration": self.total_duration,
            "regression_count": self.regression_count,
            "critical_issues": self.critical_issues,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
        }


class HistoryTracker:
    """
    Comprehensive history tracker for CI simulation results.

    Provides functionality for:
    - Storing execution history
    - Analyzing trends over time
    - Generating improvement suggestions
    - Tracking quality metrics
    - Managing historical data retention
    """

    def __init__(self, history_dir: str = ".kiro/ci-history"):
        """
        Initialize the history tracker.

        Args:
            history_dir: Directory to store historical data
        """
        self.history_dir = Path(history_dir)
        self.trends_file = self.history_dir / "trends.json"
        self.metrics_file = self.history_dir / "quality_metrics.json"

        # Ensure history directory exists
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_execution_history(self, result: SimulationResult) -> str:
        """
        Save execution results to history.

        Args:
            result: SimulationResult to save

        Returns:
            Path to the saved history entry
        """
        # Create timestamped directory
        timestamp_str = result.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        execution_dir = self.history_dir / timestamp_str
        execution_dir.mkdir(exist_ok=True)

        # Save detailed results
        results_file = execution_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        # Save summary
        summary_file = execution_dir / "summary.md"
        self._save_execution_summary(result, summary_file)

        # Save benchmark data if available
        benchmark_data = self._extract_benchmark_data(result)
        if benchmark_data:
            benchmark_file = execution_dir / "benchmark.json"
            with open(benchmark_file, "w", encoding="utf-8") as f:
                json.dump(benchmark_data, f, indent=2, ensure_ascii=False)

        # Update trends and metrics
        self._update_trends(result)
        self._update_quality_metrics(result)

        return str(execution_dir)

    def get_execution_history(
        self, limit: Optional[int] = None
    ) -> List[SimulationResult]:
        """
        Retrieve execution history.

        Args:
            limit: Maximum number of results to return (most recent first)

        Returns:
            List of SimulationResult objects
        """
        history_entries = []

        # Get all execution directories
        execution_dirs = [
            d
            for d in self.history_dir.iterdir()
            if d.is_dir() and d.name != "__pycache__"
        ]

        # Sort by timestamp (newest first)
        execution_dirs.sort(key=lambda x: x.name, reverse=True)

        if limit:
            execution_dirs = execution_dirs[:limit]

        for execution_dir in execution_dirs:
            results_file = execution_dir / "results.json"
            if results_file.exists():
                try:
                    with open(results_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    history_entries.append(SimulationResult.from_dict(data))
                except Exception as e:
                    print(f"Warning: Could not load history entry {execution_dir}: {e}")

        return history_entries

    def analyze_trends(self, days: int = 30) -> Dict[str, TrendData]:
        """
        Analyze trends over the specified time period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary of trend data by metric name
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        history = self.get_execution_history()

        # Filter by date
        recent_history = [
            result for result in history if result.timestamp >= cutoff_date
        ]

        if len(recent_history) < 2:
            return {}

        # Sort by timestamp
        recent_history.sort(key=lambda x: x.timestamp)

        trends = {}

        # Analyze success rate trend
        success_rates = []
        timestamps = []
        for result in recent_history:
            if result.check_results:
                success_rate = (
                    len(result.successful_checks) / len(result.check_results) * 100
                )
                success_rates.append(success_rate)
                timestamps.append(result.timestamp)

        if success_rates:
            trends["success_rate"] = self._calculate_trend(
                "success_rate", success_rates, timestamps
            )

        # Analyze duration trend
        durations = [result.total_duration for result in recent_history]
        if durations:
            trends["execution_duration"] = self._calculate_trend(
                "execution_duration", durations, timestamps
            )

        # Analyze error count trend
        error_counts = []
        for result in recent_history:
            total_errors = sum(
                len(check.errors) for check in result.check_results.values()
            )
            error_counts.append(total_errors)

        if error_counts:
            trends["error_count"] = self._calculate_trend(
                "error_count", error_counts, timestamps
            )

        # Analyze regression trend
        regression_counts = [len(result.regression_issues) for result in recent_history]
        if regression_counts:
            trends["regression_count"] = self._calculate_trend(
                "regression_count", regression_counts, timestamps
            )

        # Save trends to file
        self._save_trends(trends)

        return trends

    def generate_improvement_suggestions(self, days: int = 30) -> List[str]:
        """
        Generate improvement suggestions based on historical trends.

        Args:
            days: Number of days to analyze for suggestions

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        trends = self.analyze_trends(days)
        history = self.get_execution_history(limit=10)

        if not history:
            return ["No historical data available for analysis"]

        # Analyze success rate trends
        if "success_rate" in trends:
            success_trend = trends["success_rate"]
            if success_trend.trend_direction == "degrading":
                suggestions.append(
                    f"Success rate has been declining over the past {days} days. "
                    "Consider reviewing recent changes and implementing additional quality checks."
                )
            elif success_trend.trend_direction == "improving":
                suggestions.append(
                    "Success rate is improving! Continue with current development practices."
                )

        # Analyze duration trends
        if "execution_duration" in trends:
            duration_trend = trends["execution_duration"]
            if duration_trend.trend_direction == "degrading":
                suggestions.append(
                    "Execution time is increasing. Consider optimizing slow checks or "
                    "implementing parallel execution for better performance."
                )

        # Analyze error patterns
        common_errors = self._analyze_common_errors(history)
        if common_errors:
            suggestions.append(
                f"Most common error types: {', '.join(common_errors[:3])}. "
                "Focus on addressing these recurring issues."
            )

        # Analyze regression patterns
        if "regression_count" in trends:
            regression_trend = trends["regression_count"]
            if regression_trend.trend_direction == "degrading":
                suggestions.append(
                    "Performance regressions are increasing. Implement stricter "
                    "performance testing and consider setting up performance budgets."
                )

        # Check for frequent failures
        frequent_failures = self._identify_frequent_failures(history)
        if frequent_failures:
            suggestions.append(
                f"Frequently failing checks: {', '.join(frequent_failures[:3])}. "
                "These checks may need attention or refactoring."
            )

        # Suggest optimizations based on check durations
        slow_checks = self._identify_slow_checks(history)
        if slow_checks:
            suggestions.append(
                f"Slowest checks: {', '.join(slow_checks[:3])}. "
                "Consider optimizing these checks to improve overall execution time."
            )

        # Python version specific suggestions
        python_version_issues = self._analyze_python_version_issues(history)
        if python_version_issues:
            suggestions.extend(python_version_issues)

        return (
            suggestions
            if suggestions
            else ["No specific improvement suggestions at this time"]
        )

    def cleanup_old_history(self, days_to_keep: int = 90) -> int:
        """
        Clean up old history entries.

        Args:
            days_to_keep: Number of days of history to retain

        Returns:
            Number of entries removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0

        for execution_dir in self.history_dir.iterdir():
            if not execution_dir.is_dir() or execution_dir.name in ["__pycache__"]:
                continue

            try:
                # Parse timestamp from directory name
                timestamp_str = execution_dir.name
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")

                if timestamp < cutoff_date:
                    shutil.rmtree(execution_dir)
                    removed_count += 1
            except ValueError:
                # Skip directories that don't match the expected format
                continue

        return removed_count

    def get_quality_metrics_history(self, days: int = 30) -> List[QualityMetrics]:
        """
        Get quality metrics history for the specified period.

        Args:
            days: Number of days to retrieve

        Returns:
            List of QualityMetrics objects
        """
        if not self.metrics_file.exists():
            return []

        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            cutoff_date = datetime.now() - timedelta(days=days)

            metrics = []
            for entry in data.get("metrics", []):
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp >= cutoff_date:
                    metrics.append(
                        QualityMetrics(
                            timestamp=timestamp,
                            success_rate=entry["success_rate"],
                            total_checks=entry["total_checks"],
                            failed_checks=entry["failed_checks"],
                            total_duration=entry["total_duration"],
                            regression_count=entry["regression_count"],
                            critical_issues=entry["critical_issues"],
                            error_count=entry["error_count"],
                            warning_count=entry["warning_count"],
                        )
                    )

            return sorted(metrics, key=lambda x: x.timestamp)

        except Exception as e:
            print(f"Warning: Could not load quality metrics: {e}")
            return []

    def _save_execution_summary(
        self, result: SimulationResult, summary_file: Path
    ) -> None:
        """Save a brief summary of the execution."""
        summary_content = f"""# CI Execution Summary

**Timestamp:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {result.overall_status.value.upper()}
**Duration:** {result.total_duration:.2f} seconds

## Quick Stats
- Total Checks: {len(result.check_results)}
- Successful: {len(result.successful_checks)}
- Failed: {len(result.failed_checks)}
- Regressions: {len(result.regression_issues)}

## Summary
{result.summary}
"""

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary_content)

    def _extract_benchmark_data(
        self, result: SimulationResult
    ) -> Optional[Dict[str, Any]]:
        """Extract benchmark data from simulation result."""
        benchmark_data = {}

        for check_name, check_result in result.check_results.items():
            if "benchmark" in check_result.metadata:
                benchmark_data[check_name] = check_result.metadata["benchmark"]

        return benchmark_data if benchmark_data else None

    def _update_trends(self, result: SimulationResult) -> None:
        """Update trend data with new result."""
        trends_data = {}

        if self.trends_file.exists():
            try:
                with open(self.trends_file, "r", encoding="utf-8") as f:
                    trends_data = json.load(f)
            except Exception:
                trends_data = {}

        # Update with current result
        timestamp = result.timestamp.isoformat()

        if "executions" not in trends_data:
            trends_data["executions"] = []

        execution_data = {
            "timestamp": timestamp,
            "success_rate": (
                len(result.successful_checks) / len(result.check_results) * 100
                if result.check_results
                else 0
            ),
            "duration": result.total_duration,
            "error_count": sum(
                len(check.errors) for check in result.check_results.values()
            ),
            "regression_count": len(result.regression_issues),
        }

        trends_data["executions"].append(execution_data)

        # Keep only last 100 executions
        trends_data["executions"] = trends_data["executions"][-100:]

        with open(self.trends_file, "w", encoding="utf-8") as f:
            json.dump(trends_data, f, indent=2, ensure_ascii=False)

    def _update_quality_metrics(self, result: SimulationResult) -> None:
        """Update quality metrics with new result."""
        metrics_data = {"metrics": []}

        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    metrics_data = json.load(f)
            except Exception:
                metrics_data = {"metrics": []}

        # Create new metrics entry
        total_errors = sum(len(check.errors) for check in result.check_results.values())
        total_warnings = sum(
            len(check.warnings) for check in result.check_results.values()
        )
        critical_issues = len(
            [
                issue
                for issue in result.regression_issues
                if issue.severity == SeverityLevel.CRITICAL
            ]
        )

        new_metrics = QualityMetrics(
            timestamp=result.timestamp,
            success_rate=(
                len(result.successful_checks) / len(result.check_results) * 100
                if result.check_results
                else 0
            ),
            total_checks=len(result.check_results),
            failed_checks=len(result.failed_checks),
            total_duration=result.total_duration,
            regression_count=len(result.regression_issues),
            critical_issues=critical_issues,
            error_count=total_errors,
            warning_count=total_warnings,
        )

        metrics_data["metrics"].append(new_metrics.to_dict())

        # Keep only last 200 entries
        metrics_data["metrics"] = metrics_data["metrics"][-200:]

        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)

    def _calculate_trend(
        self, metric_name: str, values: List[float], timestamps: List[datetime]
    ) -> TrendData:
        """Calculate trend for a specific metric."""
        if len(values) < 2:
            return TrendData(metric_name=metric_name)

        # Simple linear regression to determine trend
        n = len(values)
        x_values = list(range(n))

        # Calculate slope
        x_mean = mean(x_values)
        y_mean = mean(values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # Determine trend direction and strength
        if abs(slope) < 0.1:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = (
                "improving" if metric_name == "success_rate" else "degrading"
            )
        else:
            trend_direction = (
                "degrading" if metric_name == "success_rate" else "improving"
            )

        # Normalize slope to -1.0 to 1.0 range
        max_value = max(values) if values else 1
        trend_strength = (
            min(1.0, max(0.0, abs(slope) / max_value)) if max_value > 0 else 0
        )

        return TrendData(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
        )

    def _save_trends(self, trends: Dict[str, TrendData]) -> None:
        """Save calculated trends to file."""
        trends_dict = {name: trend.to_dict() for name, trend in trends.items()}
        trends_dict["last_updated"] = datetime.now().isoformat()

        with open(self.trends_file, "w", encoding="utf-8") as f:
            json.dump(trends_dict, f, indent=2, ensure_ascii=False)

    def _analyze_common_errors(self, history: List[SimulationResult]) -> List[str]:
        """Analyze common error patterns across history."""
        error_patterns = {}

        for result in history:
            for check in result.check_results.values():
                for error in check.errors:
                    # Normalize error message
                    normalized = self._normalize_error_for_pattern(error)
                    error_patterns[normalized] = error_patterns.get(normalized, 0) + 1

        # Return top 5 most common error patterns
        sorted_patterns = sorted(
            error_patterns.items(), key=lambda x: x[1], reverse=True
        )
        return [pattern for pattern, count in sorted_patterns[:5]]

    def _identify_frequent_failures(self, history: List[SimulationResult]) -> List[str]:
        """Identify checks that fail frequently."""
        failure_counts = {}
        total_runs = {}

        for result in history:
            for check_name, check in result.check_results.items():
                total_runs[check_name] = total_runs.get(check_name, 0) + 1
                if not check.is_successful:
                    failure_counts[check_name] = failure_counts.get(check_name, 0) + 1

        # Calculate failure rates
        failure_rates = {}
        for check_name in total_runs:
            if total_runs[check_name] >= 3:  # Only consider checks run at least 3 times
                failure_rate = (
                    failure_counts.get(check_name, 0) / total_runs[check_name]
                )
                if failure_rate >= 0.3:  # 30% or higher failure rate
                    failure_rates[check_name] = failure_rate

        # Return checks sorted by failure rate
        sorted_failures = sorted(
            failure_rates.items(), key=lambda x: x[1], reverse=True
        )
        return [check_name for check_name, rate in sorted_failures]

    def _identify_slow_checks(self, history: List[SimulationResult]) -> List[str]:
        """Identify consistently slow checks."""
        duration_stats = {}

        for result in history:
            for check_name, check in result.check_results.items():
                if check_name not in duration_stats:
                    duration_stats[check_name] = []
                duration_stats[check_name].append(check.duration)

        # Calculate average durations
        slow_checks = {}
        for check_name, durations in duration_stats.items():
            if len(durations) >= 3:  # Only consider checks run at least 3 times
                avg_duration = mean(durations)
                if avg_duration > 10.0:  # Checks taking more than 10 seconds on average
                    slow_checks[check_name] = avg_duration

        # Return checks sorted by average duration
        sorted_slow = sorted(slow_checks.items(), key=lambda x: x[1], reverse=True)
        return [check_name for check_name, duration in sorted_slow]

    def _analyze_python_version_issues(
        self, history: List[SimulationResult]
    ) -> List[str]:
        """Analyze Python version specific issues."""
        suggestions = []
        version_failures = {}

        for result in history:
            for check in result.check_results.values():
                if check.python_version and not check.is_successful:
                    version = check.python_version
                    if version not in version_failures:
                        version_failures[version] = 0
                    version_failures[version] += 1

        if version_failures:
            most_problematic = max(version_failures.items(), key=lambda x: x[1])
            suggestions.append(
                f"Python {most_problematic[0]} has the most failures ({most_problematic[1]}). "
                "Consider focusing testing efforts on this version."
            )

        return suggestions

    def _normalize_error_for_pattern(self, error: str) -> str:
        """Normalize error message for pattern matching."""
        import re

        # Remove file paths and line numbers
        normalized = re.sub(r"/[^\s]+\.py:\d+", "<file>", error)
        normalized = re.sub(r"line \d+", "line <num>", normalized)

        # Remove specific values but keep structure
        normalized = re.sub(r"\d+", "<num>", normalized)
        normalized = re.sub(r"'[^']*'", "<value>", normalized)

        return normalized.strip()[:100]  # Limit length
