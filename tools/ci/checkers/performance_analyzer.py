"""
Performance Analyzer for CI Simulation Tool

This module implements comprehensive performance analysis including
benchmark test execution, timing measurement, memory usage monitoring,
and performance regression detection with detailed reporting.
"""

import subprocess
import sys
import os
import json
import time
import psutil
import threading
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from ..interfaces import CheckerInterface
    from ..models import CheckResult, CheckStatus, ConfigDict, RegressionIssue, SeverityLevel
except ImportError:
    from interfaces import CheckerInterface
    from models import CheckResult, CheckStatus, ConfigDict, RegressionIssue, SeverityLevel


@dataclass
class PerformanceMetric:
    """Represents a single performance metric measurement."""

    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Represents the result of a benchmark test."""

    test_name: str
    duration: float
    memory_peak: float
    memory_average: float
    cpu_peak: float
    cpu_average: float
    throughput: Optional[float] = None
    error_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: List[PerformanceMetric] = field(default_factory=list)


class PerformanceAnalyzer(CheckerInterface):
    """
    Comprehensive performance analyzer with benchmark execution and regression detection.

    This checker provides:
    - Benchmark test execution with timing measurement
    - Memory usage monitoring and reporting
    - Performance metrics collection and storage
    - Regression detection against baseline results
    - Trend analysis and performance reporting
    """

    def __init__(self, config: ConfigDict):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.benchmark_timeout = config.get('benchmark_timeout', 300)  # 5 minutes
        self.memory_sample_interval = config.get('memory_sample_interval', 0.1)  # 100ms
        self.regression_threshold = config.get('regression_threshold', 30.0)  # 30%
        self.baseline_file = Path(config.get('baseline_file', '.kiro/ci-history/performance_baseline.json'))
        self.results_dir = Path(config.get('results_dir', 'reports/ci-simulation/performance'))

        # Ensure directories exist
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Performance tracking
        self.current_results: List[BenchmarkResult] = []
        self.baseline_results: Optional[Dict[str, BenchmarkResult]] = None

    @property
    def name(self) -> str:
        return "Performance Analyzer"

    @property
    def check_type(self) -> str:
        return "performance"

    @property
    def dependencies(self) -> List[str]:
        return ["psutil", "pytest"]

    def is_available(self) -> bool:
        """Check if performance analyzer can run in current environment."""
        if self._is_available is not None:
            return self._is_available

        try:
            import psutil
            import pytest

            # Check if we can access system resources
            process = psutil.Process()
            process.memory_info()
            process.cpu_percent()

            self._is_available = True
            return True

        except ImportError as e:
            self.logger.warning(f"Missing dependency for performance analysis: {e}")
            self._is_available = False
            return False
        except Exception as e:
            self.logger.warning(f"Performance analyzer not available: {e}")
            self._is_available = False
            return False

    def run_check(self, **kwargs) -> CheckResult:
        """Execute performance analysis with benchmark tests."""
        start_time = time.time()

        try:
            if not self.is_available():
                return CheckResult(
                    name=self.name,
                    status=CheckStatus.SKIPPED,
                    duration=time.time() - start_time,
                    output="Performance analyzer dependencies not available",
                    warnings=["Install psutil and pytest to enable performance analysis"]
                )

            self.logger.info("Starting performance analysis...")

            # Load baseline if available
            self._load_baseline()

            # Run benchmark tests
            benchmark_results = self._run_benchmarks()

            # Collect performance metrics
            metrics = self._collect_performance_metrics()

            # Detect regressions if baseline exists
            regressions = []
            if self.baseline_results:
                regressions = self._detect_regressions(benchmark_results)

            # Save current results as potential new baseline
            self._save_results(benchmark_results, metrics)

            # Generate report
            report = self._generate_performance_report(benchmark_results, metrics, regressions)

            # Determine overall status
            status = CheckStatus.SUCCESS
            if regressions:
                critical_regressions = [r for r in regressions if r.severity == SeverityLevel.CRITICAL]
                if critical_regressions:
                    status = CheckStatus.FAILURE
                else:
                    status = CheckStatus.WARNING

            duration = time.time() - start_time

            return CheckResult(
                name=self.name,
                status=status,
                duration=duration,
                output=report,
                errors=[f"Critical regression: {r.description}" for r in regressions if r.severity == SeverityLevel.CRITICAL],
                warnings=[f"Performance regression: {r.description}" for r in regressions if r.severity != SeverityLevel.CRITICAL],
                suggestions=self._generate_performance_suggestions(benchmark_results, regressions),
                metadata={
                    'benchmark_count': len(benchmark_results),
                    'regression_count': len(regressions),
                    'total_duration': sum(r.duration for r in benchmark_results),
                    'peak_memory': max((r.memory_peak for r in benchmark_results), default=0),
                    'baseline_available': self.baseline_results is not None
                }
            )

        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAILURE,
                duration=time.time() - start_time,
                output=f"Performance analysis failed: {str(e)}",
                errors=[str(e)]
            )

    def _run_benchmarks(self) -> List[BenchmarkResult]:
        """Execute benchmark tests and collect results."""
        self.logger.info("Running benchmark tests...")

        benchmarks = [
            ("file_discovery", self._benchmark_file_discovery),
            ("image_processing", self._benchmark_image_processing),
            ("ui_responsiveness", self._benchmark_ui_responsiveness),
            ("memory_efficiency", self._benchmark_memory_efficiency),
            ("concurrent_operations", self._benchmark_concurrent_operations)
        ]

        results = []

        for benchmark_name, benchmark_func in benchmarks:
            try:
                self.logger.info(f"Running {benchmark_name} benchmark...")
                result = benchmark_func()
                results.append(result)
                self.logger.info(f"Completed {benchmark_name}: {result.duration:.2f}s")

            except Exception as e:
                self.logger.error(f"Benchmark {benchmark_name} failed: {e}")
                # Create a failed result
                results.append(BenchmarkResult(
                    test_name=benchmark_name,
                    duration=0.0,
                    memory_peak=0.0,
                    memory_average=0.0,
                    cpu_peak=0.0,
                    cpu_average=0.0,
                    error_rate=1.0
                ))

        self.current_results = results
        return results

    def _benchmark_file_discovery(self) -> BenchmarkResult:
        """Benchmark file discovery performance."""
        return self._run_benchmark_with_monitoring(
            "file_discovery",
            self._simulate_file_discovery,
            iterations=5
        )

    def _benchmark_image_processing(self) -> BenchmarkResult:
        """Benchmark image processing performance."""
        return self._run_benchmark_with_monitoring(
            "image_processing",
            self._simulate_image_processing,
            iterations=3
        )

    def _benchmark_ui_responsiveness(self) -> BenchmarkResult:
        """Benchmark UI responsiveness."""
        return self._run_benchmark_with_monitoring(
            "ui_responsiveness",
            self._simulate_ui_operations,
            iterations=10
        )

    def _benchmark_memory_efficiency(self) -> BenchmarkResult:
        """Benchmark memory efficiency."""
        return self._run_benchmark_with_monitoring(
            "memory_efficiency",
            self._simulate_memory_intensive_operations,
            iterations=3
        )

    def _benchmark_concurrent_operations(self) -> BenchmarkResult:
        """Benchmark concurrent operations performance."""
        return self._run_benchmark_with_monitoring(
            "concurrent_operations",
            self._simulate_concurrent_operations,
            iterations=2
        )

    def _run_benchmark_with_monitoring(self, test_name: str, test_func, iterations: int = 1) -> BenchmarkResult:
        """Run a benchmark test with resource monitoring."""
        durations = []
        memory_samples_all = []
        cpu_samples_all = []

        for i in range(iterations):
            # Resource monitoring setup
            process = psutil.Process()
            memory_samples = []
            cpu_samples = []
            monitoring_active = True

            def monitor_resources():
                while monitoring_active:
                    try:
                        memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
                        cpu_samples.append(process.cpu_percent())
                        time.sleep(self.memory_sample_interval)
                    except:
                        break

            monitor_thread = threading.Thread(target=monitor_resources)
            monitor_thread.daemon = True
            monitor_thread.start()

            # Run the actual test
            start_time = time.time()
            try:
                test_func()
                duration = time.time() - start_time
                durations.append(duration)
            finally:
                monitoring_active = False
                monitor_thread.join(timeout=1.0)

            memory_samples_all.extend(memory_samples)
            cpu_samples_all.extend(cpu_samples)

        # Calculate statistics
        avg_duration = statistics.mean(durations) if durations else 0.0
        memory_peak = max(memory_samples_all) if memory_samples_all else 0.0
        memory_avg = statistics.mean(memory_samples_all) if memory_samples_all else 0.0
        cpu_peak = max(cpu_samples_all) if cpu_samples_all else 0.0
        cpu_avg = statistics.mean(cpu_samples_all) if cpu_samples_all else 0.0

        return BenchmarkResult(
            test_name=test_name,
            duration=avg_duration,
            memory_peak=memory_peak,
            memory_average=memory_avg,
            cpu_peak=cpu_peak,
            cpu_average=cpu_avg,
            throughput=1.0 / avg_duration if avg_duration > 0 else 0.0
        )

    def _simulate_file_discovery(self):
        """Simulate file discovery operations."""
        # Simulate scanning directories and finding files
        test_dir = Path(".")
        files_found = 0

        for root, dirs, files in os.walk(test_dir):
            files_found += len(files)
            # Simulate processing time
            time.sleep(0.001)

            # Limit depth to avoid excessive scanning
            if len(Path(root).parts) > 5:
                dirs.clear()

        return files_found

    def _simulate_image_processing(self):
        """Simulate image processing operations."""
        # Simulate image processing tasks
        for i in range(50):
            # Simulate image loading and processing
            data = bytearray(1024 * 100)  # 100KB simulated image

            # Simulate processing operations
            for j in range(0, len(data), 1024):
                chunk = data[j:j+1024]
                # Simulate processing
                processed = bytes(x ^ 0xFF for x in chunk)

            time.sleep(0.01)  # Simulate I/O delay

    def _simulate_ui_operations(self):
        """Simulate UI operations."""
        # Simulate UI responsiveness tests
        operations = [
            lambda: time.sleep(0.005),  # Button click
            lambda: time.sleep(0.010),  # Menu navigation
            lambda: time.sleep(0.015),  # Window resize
            lambda: time.sleep(0.008),  # Scroll operation
        ]

        for op in operations:
            op()

    def _simulate_memory_intensive_operations(self):
        """Simulate memory-intensive operations."""
        # Simulate memory allocation and deallocation
        data_blocks = []

        try:
            # Allocate memory blocks
            for i in range(100):
                block = bytearray(1024 * 1024)  # 1MB blocks
                data_blocks.append(block)
                time.sleep(0.01)

            # Process the data
            for block in data_blocks:
                # Simulate processing
                for j in range(0, len(block), 1024):
                    chunk = block[j:j+1024]

        finally:
            # Clean up
            data_blocks.clear()

    def _simulate_concurrent_operations(self):
        """Simulate concurrent operations."""
        def worker_task(task_id: int):
            # Simulate concurrent work
            data = bytearray(1024 * 50)  # 50KB per task
            for i in range(100):
                # Simulate processing
                data[i % len(data)] = (data[i % len(data)] + 1) % 256
                if i % 10 == 0:
                    time.sleep(0.001)
            return task_id

        # Run tasks concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker_task, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]

        return len(results)

    def _collect_performance_metrics(self) -> List[PerformanceMetric]:
        """Collect additional performance metrics."""
        metrics = []

        try:
            # System metrics
            process = psutil.Process()

            metrics.append(PerformanceMetric(
                name="current_memory_usage",
                value=process.memory_info().rss / 1024 / 1024,  # MB
                unit="MB"
            ))

            metrics.append(PerformanceMetric(
                name="current_cpu_percent",
                value=process.cpu_percent(),
                unit="%"
            ))

            # System-wide metrics
            metrics.append(PerformanceMetric(
                name="system_memory_percent",
                value=psutil.virtual_memory().percent,
                unit="%"
            ))

            metrics.append(PerformanceMetric(
                name="system_cpu_percent",
                value=psutil.cpu_percent(),
                unit="%"
            ))

            # Disk I/O if available
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    metrics.append(PerformanceMetric(
                        name="disk_read_bytes",
                        value=disk_io.read_bytes,
                        unit="bytes"
                    ))

                    metrics.append(PerformanceMetric(
                        name="disk_write_bytes",
                        value=disk_io.write_bytes,
                        unit="bytes"
                    ))
            except:
                pass  # Disk I/O not available on all systems

        except Exception as e:
            self.logger.warning(f"Failed to collect some performance metrics: {e}")

        return metrics

    def _load_baseline(self):
        """Load baseline performance results."""
        try:
            if self.baseline_file.exists():
                with open(self.baseline_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.baseline_results = {}
                for test_name, result_data in data.get('benchmarks', {}).items():
                    self.baseline_results[test_name] = BenchmarkResult(
                        test_name=result_data['test_name'],
                        duration=result_data['duration'],
                        memory_peak=result_data['memory_peak'],
                        memory_average=result_data['memory_average'],
                        cpu_peak=result_data['cpu_peak'],
                        cpu_average=result_data['cpu_average'],
                        throughput=result_data.get('throughput'),
                        error_rate=result_data.get('error_rate', 0.0),
                        timestamp=datetime.fromisoformat(result_data['timestamp'])
                    )

                self.logger.info(f"Loaded baseline with {len(self.baseline_results)} benchmarks")
            else:
                self.logger.info("No baseline file found - this will be the first run")

        except Exception as e:
            self.logger.warning(f"Failed to load baseline: {e}")
            self.baseline_results = None

    def _save_results(self, benchmark_results: List[BenchmarkResult], metrics: List[PerformanceMetric]):
        """Save current results for future baseline comparison."""
        try:
            # Save detailed results
            timestamp = datetime.now()
            results_file = self.results_dir / f"performance_results_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

            results_data = {
                'timestamp': timestamp.isoformat(),
                'benchmarks': {
                    result.test_name: {
                        'test_name': result.test_name,
                        'duration': result.duration,
                        'memory_peak': result.memory_peak,
                        'memory_average': result.memory_average,
                        'cpu_peak': result.cpu_peak,
                        'cpu_average': result.cpu_average,
                        'throughput': result.throughput,
                        'error_rate': result.error_rate,
                        'timestamp': result.timestamp.isoformat()
                    }
                    for result in benchmark_results
                },
                'metrics': [
                    {
                        'name': metric.name,
                        'value': metric.value,
                        'unit': metric.unit,
                        'timestamp': metric.timestamp.isoformat(),
                        'metadata': metric.metadata
                    }
                    for metric in metrics
                ]
            }

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            # Update baseline if this run was successful
            if all(result.error_rate == 0.0 for result in benchmark_results):
                with open(self.baseline_file, 'w', encoding='utf-8') as f:
                    json.dump(results_data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Updated baseline with current results")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

    def _detect_regressions(self, current_results: List[BenchmarkResult]) -> List[RegressionIssue]:
        """Detect performance regressions against baseline."""
        if not self.baseline_results:
            return []

        regressions = []

        for current_result in current_results:
            baseline_result = self.baseline_results.get(current_result.test_name)
            if not baseline_result:
                continue

            # Check duration regression
            if baseline_result.duration > 0:
                duration_regression = ((current_result.duration - baseline_result.duration) / baseline_result.duration) * 100

                if duration_regression > self.regression_threshold:
                    severity = self._determine_severity(duration_regression)
                    regressions.append(RegressionIssue(
                        test_name=current_result.test_name,
                        baseline_value=baseline_result.duration,
                        current_value=current_result.duration,
                        regression_percentage=duration_regression,
                        severity=severity,
                        description=f"Duration regression in {current_result.test_name}: {duration_regression:.1f}% slower",
                        metric_type="duration",
                        threshold_exceeded=True
                    ))

            # Check memory regression
            if baseline_result.memory_peak > 0:
                memory_regression = ((current_result.memory_peak - baseline_result.memory_peak) / baseline_result.memory_peak) * 100

                if memory_regression > self.regression_threshold:
                    severity = self._determine_severity(memory_regression)
                    regressions.append(RegressionIssue(
                        test_name=current_result.test_name,
                        baseline_value=baseline_result.memory_peak,
                        current_value=current_result.memory_peak,
                        regression_percentage=memory_regression,
                        severity=severity,
                        description=f"Memory regression in {current_result.test_name}: {memory_regression:.1f}% more memory used",
                        metric_type="memory",
                        threshold_exceeded=True
                    ))

            # Check throughput regression (lower is worse)
            if baseline_result.throughput and current_result.throughput and baseline_result.throughput > 0:
                throughput_regression = ((baseline_result.throughput - current_result.throughput) / baseline_result.throughput) * 100

                if throughput_regression > self.regression_threshold:
                    severity = self._determine_severity(throughput_regression)
                    regressions.append(RegressionIssue(
                        test_name=current_result.test_name,
                        baseline_value=baseline_result.throughput,
                        current_value=current_result.throughput,
                        regression_percentage=throughput_regression,
                        severity=severity,
                        description=f"Throughput regression in {current_result.test_name}: {throughput_regression:.1f}% lower throughput",
                        metric_type="throughput",
                        threshold_exceeded=True
                    ))

        return regressions

    def _determine_severity(self, regression_percentage: float) -> SeverityLevel:
        """Determine severity level based on regression percentage."""
        if regression_percentage >= 100:  # 100% or more regression
            return SeverityLevel.CRITICAL
        elif regression_percentage >= 75:  # 75-99% regression
            return SeverityLevel.HIGH
        elif regression_percentage >= 50:  # 50-74% regression
            return SeverityLevel.MEDIUM
        else:  # 30-49% regression (below threshold would not be reported)
            return SeverityLevel.LOW

    def _generate_performance_report(self, benchmark_results: List[BenchmarkResult],
                                   metrics: List[PerformanceMetric],
                                   regressions: List[RegressionIssue]) -> str:
        """Generate comprehensive performance report."""
        report_lines = [
            "# Performance Analysis Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Benchmarks executed: {len(benchmark_results)}",
            f"- Total execution time: {sum(r.duration for r in benchmark_results):.2f}s",
            f"- Peak memory usage: {max((r.memory_peak for r in benchmark_results), default=0):.1f}MB",
            f"- Regressions detected: {len(regressions)}",
            ""
        ]

        # Benchmark results
        report_lines.extend([
            "## Benchmark Results",
            ""
        ])

        for result in benchmark_results:
            report_lines.extend([
                f"### {result.test_name}",
                f"- Duration: {result.duration:.3f}s",
                f"- Memory Peak: {result.memory_peak:.1f}MB",
                f"- Memory Average: {result.memory_average:.1f}MB",
                f"- CPU Peak: {result.cpu_peak:.1f}%",
                f"- CPU Average: {result.cpu_average:.1f}%",
            ])

            if result.throughput:
                report_lines.append(f"- Throughput: {result.throughput:.2f} ops/sec")

            if result.error_rate > 0:
                report_lines.append(f"- Error Rate: {result.error_rate:.1%}")

            report_lines.append("")

        # Regressions
        if regressions:
            report_lines.extend([
                "## Performance Regressions",
                ""
            ])

            for regression in regressions:
                report_lines.extend([
                    f"### {regression.test_name} ({regression.severity.value.upper()})",
                    f"- Metric: {regression.metric_type}",
                    f"- Baseline: {regression.baseline_value:.3f}",
                    f"- Current: {regression.current_value:.3f}",
                    f"- Regression: {regression.regression_percentage:.1f}%",
                    f"- Description: {regression.description}",
                    ""
                ])

        # System metrics
        if metrics:
            report_lines.extend([
                "## System Metrics",
                ""
            ])

            for metric in metrics:
                report_lines.append(f"- {metric.name}: {metric.value:.2f} {metric.unit}")

            report_lines.append("")

        return "\n".join(report_lines)

    def _generate_performance_suggestions(self, benchmark_results: List[BenchmarkResult],
                                        regressions: List[RegressionIssue]) -> List[str]:
        """Generate performance improvement suggestions."""
        suggestions = []

        # Analyze results for suggestions
        high_memory_tests = [r for r in benchmark_results if r.memory_peak > 500]  # >500MB
        slow_tests = [r for r in benchmark_results if r.duration > 10]  # >10s
        high_cpu_tests = [r for r in benchmark_results if r.cpu_peak > 80]  # >80%

        if high_memory_tests:
            suggestions.append(
                f"High memory usage detected in {len(high_memory_tests)} tests. "
                "Consider implementing memory pooling or reducing data structures size."
            )

        if slow_tests:
            suggestions.append(
                f"Slow execution detected in {len(slow_tests)} tests. "
                "Consider algorithm optimization or parallel processing."
            )

        if high_cpu_tests:
            suggestions.append(
                f"High CPU usage detected in {len(high_cpu_tests)} tests. "
                "Consider load balancing or reducing computational complexity."
            )

        # Regression-specific suggestions
        critical_regressions = [r for r in regressions if r.severity == SeverityLevel.CRITICAL]
        if critical_regressions:
            suggestions.append(
                f"Critical performance regressions detected in {len(critical_regressions)} tests. "
                "Immediate investigation and optimization required."
            )

        memory_regressions = [r for r in regressions if r.metric_type == "memory"]
        if memory_regressions:
            suggestions.append(
                "Memory usage regressions detected. Check for memory leaks or "
                "increased data structure sizes in recent changes."
            )

        duration_regressions = [r for r in regressions if r.metric_type == "duration"]
        if duration_regressions:
            suggestions.append(
                "Execution time regressions detected. Profile recent code changes "
                "for algorithmic inefficiencies or blocking operations."
            )

        if not suggestions:
            suggestions.append("Performance is within acceptable ranges. Continue monitoring.")

        return suggestions

    def save_baseline(self, results: Dict[str, Any]) -> None:
        """Save current results as new baseline."""
        try:
            with open(self.baseline_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved new baseline to {self.baseline_file}")
        except Exception as e:
            self.logger.error(f"Failed to save baseline: {e}")
            raise

    def compare_with_baseline(self, current_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current results with baseline and return comparison report."""
        if not self.baseline_results:
            return {
                "status": "no_baseline",
                "message": "No baseline available for comparison"
            }

        comparison = {
            "timestamp": datetime.now().isoformat(),
            "baseline_timestamp": None,
            "comparisons": {},
            "summary": {
                "improved": 0,
                "regressed": 0,
                "stable": 0
            }
        }

        # Find baseline timestamp
        try:
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
                comparison["baseline_timestamp"] = baseline_data.get("timestamp")
        except:
            pass

        for test_name, current_result in current_results.get("benchmarks", {}).items():
            if test_name in self.baseline_results:
                baseline_result = self.baseline_results[test_name]

                # Calculate changes
                duration_change = 0
                if baseline_result.duration > 0:
                    duration_change = ((current_result["duration"] - baseline_result.duration) / baseline_result.duration) * 100

                memory_change = 0
                if baseline_result.memory_peak > 0:
                    memory_change = ((current_result["memory_peak"] - baseline_result.memory_peak) / baseline_result.memory_peak) * 100

                # Determine status
                status = "stable"
                if abs(duration_change) > 10 or abs(memory_change) > 10:  # 10% threshold for significant change
                    if duration_change > 0 or memory_change > 0:  # Worse performance
                        status = "regressed"
                        comparison["summary"]["regressed"] += 1
                    else:  # Better performance
                        status = "improved"
                        comparison["summary"]["improved"] += 1
                else:
                    comparison["summary"]["stable"] += 1

                comparison["comparisons"][test_name] = {
                    "status": status,
                    "duration_change_percent": duration_change,
                    "memory_change_percent": memory_change,
                    "baseline_duration": baseline_result.duration,
                    "current_duration": current_result["duration"],
                    "baseline_memory": baseline_result.memory_peak,
                    "current_memory": current_result["memory_peak"]
                }

        return comparison

    def detect_performance_regression(self, threshold: float = 30.0) -> List[RegressionIssue]:
        """
        Detect performance regressions in current results against baseline.

        Args:
            threshold: Regression threshold percentage (default 30%)

        Returns:
            List of detected regression issues
        """
        if not self.current_results or not self.baseline_results:
            return []

        # Update thresholif provided
        original_threshold = self.regression_threshold
        self.regression_threshold = threshold

        try:
            regressions = self._detect_regressions(self.current_results)
            return regressions
        finally:
            # Restore original threshold
            self.regression_threshold = original_threshold

    def analyze_performance_trends(self, history_days: int = 30) -> Dict[str, Any]:
        """
        Analyze performance trends over the specified time period.

        Args:
            history_days: Number of days to analyze (default 30)

        Returns:
            Dictionary containing trend analysis results
        """
        try:
            # Load historical results
            history_files = []
            cutoff_date = datetime.now() - timedelta(days=history_days)

            for file_path in self.results_dir.glob("performance_results_*.json"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = file_path.stem.split('_', 2)[-1]  # Get the timestamp part
                    file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                    if file_date >= cutoff_date:
                        history_files.append((file_date, file_path))
                except:
                    continue  # Skip files with invalid timestamps

            # Sort by date
            history_files.sort(key=lambda x: x[0])

            if len(history_files) < 2:
                return {
                    "status": "insufficient_data",
                    "message": f"Need at least 2 data points for trend analysis, found {len(history_files)}"
                }

            # Load and analyze trends
            trends = {}
            test_data = {}  # test_name -> [(timestamp, metrics)]

            for file_date, file_path in history_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    for test_name, benchmark_data in data.get('benchmarks', {}).items():
                        if test_name not in test_data:
                            test_data[test_name] = []

                        test_data[test_name].append((
                            file_date,
                            {
                                'duration': benchmark_data['duration'],
                                'memory_peak': benchmark_data['memory_peak'],
                                'memory_average': benchmark_data['memory_average'],
                                'cpu_peak': benchmark_data['cpu_peak'],
                                'cpu_average': benchmark_data['cpu_average'],
                                'throughput': benchmark_data.get('throughput', 0)
                            }
                        ))
                except Exception as e:
                    self.logger.warning(f"Failed to load history file {file_path}: {e}")
                    continue

            # Calculate trends for each test
            for test_name, data_points in test_data.items():
                if len(data_points) < 2:
                    continue

                # Sort by timestamp
                data_points.sort(key=lambda x: x[0])

                trends[test_name] = self._calculate_trend_metrics(data_points)

            # Generate summary
            summary = self._generate_trend_summary(trends)

            return {
                "status": "success",
                "analysis_period_days": history_days,
                "data_points_analyzed": len(history_files),
                "tests_analyzed": len(trends),
                "trends": trends,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze performance trends: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _calculate_trend_metrics(self, data_points: List[Tuple[datetime, Dict[str, float]]]) -> Dict[str, Any]:
        """Calculate trend metrics for a specific test."""
        if len(data_points) < 2:
            return {"status": "insufficient_data"}

        # Extract time series data
        timestamps = [dp[0] for dp in data_points]
        durations = [dp[1]['duration'] for dp in data_points]
        memory_peaks = [dp[1]['memory_peak'] for dp in data_points]
        throughputs = [dp[1]['throughput'] for dp in data_points if dp[1]['throughput'] > 0]

        # Calculate trends (simple linear regression slope)
        def calculate_slope(values):
            if len(values) < 2:
                return 0.0

            n = len(values)
            x_values = list(range(n))  # Use indices as x values

            # Calculate slope using least squares
            sum_x = sum(x_values)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(x_values, values))
            sum_x2 = sum(x * x for x in x_values)

            if n * sum_x2 - sum_x * sum_x == 0:
                return 0.0

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            return slope

        duration_slope = calculate_slope(durations)
        memory_slope = calculate_slope(memory_peaks)
        throughput_slope = calculate_slope(throughputs) if throughputs else 0.0

        # Calculate percentage change from first to last
        duration_change = 0.0
        if durations[0] > 0:
            duration_change = ((durations[-1] - durations[0]) / durations[0]) * 100

        memory_change = 0.0
        if memory_peaks[0] > 0:
            memory_change = ((memory_peaks[-1] - memory_peaks[0]) / memory_peaks[0]) * 100

        throughput_change = 0.0
        if throughputs and throughputs[0] > 0:
            throughput_change = ((throughputs[-1] - throughputs[0]) / throughputs[0]) * 100

        # Determine trend direction
        def get_trend_direction(slope, change_percent):
            if abs(change_percent) < 5:  # Less than 5% change is considered stable
                return "stable"
            elif slope > 0 and change_percent > 0:
                return "worsening"  # For duration and memory, increasing is bad
            elif slope < 0 and change_percent < 0:
                return "improving"  # For duration and memory, decreasing is good
            else:
                return "stable"

        # For throughput, higher is better
        def get_throughput_trend_direction(slope, change_percent):
            if abs(change_percent) < 5:
                return "stable"
            elif slope > 0 and change_percent > 0:
                return "improving"  # Higher throughput is better
            elif slope < 0 and change_percent < 0:
                return "worsening"  # Lower throughput is worse
            else:
                return "stable"

        return {
            "status": "analyzed",
            "data_points": len(data_points),
            "time_span_days": (timestamps[-1] - timestamps[0]).days,
            "duration": {
                "trend_slope": duration_slope,
                "percent_change": duration_change,
                "direction": get_trend_direction(duration_slope, duration_change),
                "current_value": durations[-1],
                "baseline_value": durations[0]
            },
            "memory": {
                "trend_slope": memory_slope,
                "percent_change": memory_change,
                "direction": get_trend_direction(memory_slope, memory_change),
                "current_value": memory_peaks[-1],
                "baseline_value": memory_peaks[0]
            },
            "throughput": {
                "trend_slope": throughput_slope,
                "percent_change": throughput_change,
                "direction": get_throughput_trend_direction(throughput_slope, throughput_change),
                "current_value": throughputs[-1] if throughputs else 0,
                "baseline_value": throughputs[0] if throughputs else 0
            } if throughputs else None
        }

    def _generate_trend_summary(self, trends: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of trend analysis."""
        if not trends:
            return {"status": "no_trends"}

        summary = {
            "total_tests": len(trends),
            "improving": 0,
            "worsening": 0,
            "stable": 0,
            "concerning_trends": [],
            "positive_trends": []
        }

        for test_name, trend_data in trends.items():
            if trend_data.get("status") != "analyzed":
                continue

            duration_direction = trend_data["duration"]["direction"]
            memory_direction = trend_data["memory"]["direction"]

            # Count overall trend
            if duration_direction == "worsening" or memory_direction == "worsening":
                summary["worsening"] += 1

                # Add to concerning trends if significant
                duration_change = abs(trend_data["duration"]["percent_change"])
                memory_change = abs(trend_data["memory"]["percent_change"])

                if duration_change > 20 or memory_change > 20:  # >20% change is concerning
                    summary["concerning_trends"].append({
                        "test_name": test_name,
                        "duration_change": trend_data["duration"]["percent_change"],
                        "memory_change": trend_data["memory"]["percent_change"],
                        "severity": "high" if (duration_change > 50 or memory_change > 50) else "medium"
                    })

            elif duration_direction == "improving" or memory_direction == "improving":
                summary["improving"] += 1

                # Add to positive trends if significant improvement
                duration_change = abs(trend_data["duration"]["percent_change"])
                memory_change = abs(trend_data["memory"]["percent_change"])

                if duration_change > 15 or memory_change > 15:  # >15% improvement is notable
                    summary["positive_trends"].append({
                        "test_name": test_name,
                        "duration_improvement": -trend_data["duration"]["percent_change"],  # Negative change is improvement
                        "memory_improvement": -trend_data["memory"]["percent_change"],
                        "significance": "high" if (duration_change > 30 or memory_change > 30) else "medium"
                    })
            else:
                summary["stable"] += 1

        # Generate recommendations
        recommendations = []

        if summary["concerning_trends"]:
            high_concern = [t for t in summary["concerning_trends"] if t["severity"] == "high"]
            if high_concern:
                recommendations.append(
                    f"Critical: {len(high_concern)} tests show severe performance degradation (>50% regression). "
                    "Immediate investigation required."
                )

            medium_concern = [t for t in summary["concerning_trends"] if t["severity"] == "medium"]
            if medium_concern:
                recommendations.append(
                    f"Warning: {len(medium_concern)} tests show moderate performance degradation (20-50% regression). "
                    "Consider optimization efforts."
                )

        if summary["positive_trends"]:
            recommendations.append(
                f"Positive: {len(summary['positive_trends'])} tests show performance improvements. "
                "Good optimization work!"
            )

        if summary["stable"] == summary["total_tests"]:
            recommendations.append("All tests show stable performance trends. Continue current practices.")

        summary["recommendations"] = recommendations

        return summary

    def generate_regression_report(self, regressions: List[RegressionIssue], output_path: Optional[Path] = None) -> str:
        """
        Generate detailed regression report.

        Args:
            regressions: List of regression issues to report
            output_path: Optional path to save the report

        Returns:
            Path to the generated report
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.results_dir / f"regression_report_{timestamp}.md"

        # Generate report content
        report_lines = [
            "# Performance Regression Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Regression Threshold: {self.regression_threshold}%",
            "",
            "## Executive Summary",
            f"- Total regressions detected: {len(regressions)}",
            f"- Critical regressions: {len([r for r in regressions if r.severity == SeverityLevel.CRITICAL])}",
            f"- High severity regressions: {len([r for r in regressions if r.severity == SeverityLevel.HIGH])}",
            f"- Medium severity regressions: {len([r for r in regressions if r.severity == SeverityLevel.MEDIUM])}",
            f"- Low severity regressions: {len([r for r in regressions if r.severity == SeverityLevel.LOW])}",
            ""
        ]

        if not regressions:
            report_lines.extend([
                "## Result",
                "✅ No performance regressions detected!",
                "",
                "All performance metrics are within acceptable thresholds compared to the baseline.",
                ""
            ])
        else:
            # Group by severity
            by_severity = {}
            for regression in regressions:
                if regression.severity not in by_severity:
                    by_severity[regression.severity] = []
                by_severity[regression.severity].append(regression)

            # Report by severity (most severe first)
            severity_order = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]

            for severity in severity_order:
                if severity not in by_severity:
                    continue

                severity_regressions = by_severity[severity]
                report_lines.extend([
                    f"## {severity.value.upper()} Severity Regressions ({len(severity_regressions)})",
                    ""
                ])

                for regression in severity_regressions:
                    icon = "🔴" if severity == SeverityLevel.CRITICAL else "🟠" if severity == SeverityLevel.HIGH else "🟡" if severity == SeverityLevel.MEDIUM else "🔵"

                    report_lines.extend([
                        f"### {icon} {regression.test_name}",
                        f"**Metric:** {regression.metric_type}",
                        f"**Baseline Value:** {regression.baseline_value:.3f}",
                        f"**Current Value:** {regression.current_value:.3f}",
                        f"**Regression:** {regression.regression_percentage:.1f}%",
                        f"**Description:** {regression.description}",
                        ""
                    ])

            # Recommendations
            report_lines.extend([
                "## Recommendations",
                ""
            ])

            critical_count = len([r for r in regressions if r.severity == SeverityLevel.CRITICAL])
            if critical_count > 0:
                report_lines.extend([
                    f"🚨 **URGENT:** {critical_count} critical regressions require immediate attention:",
                    "- Review recent code changes that may have introduced performance issues",
                    "- Run profiling tools to identify bottlenecks",
                    "- Consider reverting recent changes if performance cannot be quickly restored",
                    ""
                ])

            memory_regressions = [r for r in regressions if r.metric_type == "memory"]
            if memory_regressions:
                report_lines.extend([
                    f"💾 **Memory Issues:** {len(memory_regressions)} memory-related regressions detected:",
                    "- Check for memory leaks in recent changes",
                    "- Review data structure sizes and caching strategies",
                    "- Consider memory profiling to identify allocation hotspots",
                    ""
                ])

            duration_regressions = [r for r in regressions if r.metric_type == "duration"]
            if duration_regressions:
                report_lines.extend([
                    f"⏱️ **Performance Issues:** {len(duration_regressions)} execution time regressions detected:",
                    "- Profile recent code changes for algorithmic inefficiencies",
                    "- Check for blocking I/O operations or network calls",
                    "- Consider parallel processing opportunities",
                    ""
                ])

            throughput_regressions = [r for r in regressions if r.metric_type == "throughput"]
            if throughput_regressions:
                report_lines.extend([
                    f"📈 **Throughput Issues:** {len(throughput_regressions)} throughput regressions detected:",
                    "- Review processing pipelines for bottlenecks",
                    "- Check resource utilization (CPU, memory, I/O)",
                    "- Consider load balancing and optimization strategies",
                    ""
                ])

        # Write report
        report_content = "\n".join(report_lines)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            self.logger.info(f"Generated regression report: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"Failed to write regression report: {e}")
            raise
