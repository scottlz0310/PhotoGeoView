"""
Markdown Report Generator for CI Simulation Results

This module provides comprehensive Markdown report generation capabilities,
creating detailed, human-readable reports with error summaries and fix suggestions.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from ..interfaces import ReporterInterface
from ..models import SimulationResult, CheckResult, CheckStatus, SeverityLevel, RegressionIssue


class MarkdownReporter(ReporterInterface):
    """
    Comprehensive Markdown report generator for CI simulation results.

    Generates detailed, human-readable reports with:
    - Executive summary
    - Detailed check results
    - Error analysis and fix suggestions
    - Performance regression analysis
    - Historical trends (when available)
    """

    @property
    def format_name(self) -> str:
        """Return the name of the report format."""
        return "markdown"

    @property
    def file_extension(self) -> str:
        """Return the file extension for Markdown reports."""
        return ".md"

    def generate_report(self, result: SimulationResult, output_path: str) -> str:
        """
        Generate a comprehensive Markdown report from simulation results.

        Args:
            result: SimulationResult containing all check outcomes
            output_path: Path where the report should be saved

        Returns:
            Path to the generated report file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generate reporntent
        report_content = self._generate_report_content(result)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return output_path

    def _generate_report_content(self, result: SimulationResult) -> str:
        """Generate the complete Markdown report content."""
        sections = [
            self._generate_header(result),
            self._generate_executive_summary(result),
            self._generate_check_results_summary(result),
            self._generate_detailed_results(result),
            self._generate_regression_analysis(result),
            self._generate_error_analysis(result),
            self._generate_fix_suggestions(result),
            self._generate_configuration_info(result),
            self._generate_footer()
        ]

        return "\n\n".join(filter(None, sections))

    def _generate_header(self, result: SimulationResult) -> str:
        """Generate report header with title and metadata."""
        status_emoji = self._get_status_emoji(result.overall_status)

        return f"""# CI/CD Simulation Report {status_emoji}

**Generated:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {result.total_duration:.2f} seconds
**Overall Status:** {result.overall_status.value.upper()}
**Python Versions:** {', '.join(result.python_versions_tested) if result.python_versions_tested else 'Default'}"""

    def _generate_executive_summary(self, result: SimulationResult) -> str:
        """Generate executive summary section."""
        total_checks = len(result.check_results)
        successful_checks = len(result.successful_checks)
        failed_checks = len(result.failed_checks)

        success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 0

        summary = f"""## Executive Summary

{result.summary}

### Quick Stats
- **Total Checks:** {total_checks}
- **Successful:** {successful_checks} ({success_rate:.1f}%)
- **Failed:** {failed_checks}
- **Success Rate:** {self._get_success_rate_indicator(success_rate)}"""

        if result.regression_issues:
            summary += f"\n- **Regressions Detected:** {len(result.regression_issues)} ⚠️"

        return summary

    def _generate_check_results_summary(self, result: SimulationResult) -> str:
        """Generate check results summary table."""
        if not result.check_results:
            return "## Check Results\n\nNo checks were executed."

        table_rows = ["| Check | Status | Duration | Issues |", "|-------|--------|----------|--------|"]

        for check_name, check_result in result.check_results.items():
            status_indicator = self._get_status_emoji(check_result.status)
            duration = f"{check_result.duration:.2f}s"
            issues = len(check_result.errors) + len(check_result.warnings)
            issues_text = f"{issues} issues" if issues > 0 else "✓"

            table_rows.append(f"| {check_name} | {status_indicator} {check_result.status.value} | {duration} | {issues_text} |")

        return f"""## Check Results Summary

{chr(10).join(table_rows)}"""

    def _generate_detailed_results(self, result: SimulationResult) -> str:
        """Generate detailed results for each check."""
        if not result.check_results:
            return ""

        sections = ["## Detailed Check Results"]

        for check_name, check_result in result.check_results.items():
            sections.append(self._generate_check_detail(check_name, check_result))

        return "\n\n".join(sections)

    def _generate_check_detail(self, check_name: str, check_result: CheckResult) -> str:
        """Generate detailed information for a single check."""
        status_emoji = self._get_status_emoji(check_result.status)

        detail = f"""### {check_name} {status_emoji}

**Status:** {check_result.status.value.upper()}
**Duration:** {check_result.duration:.2f} seconds"""

        if check_result.python_version:
            detail += f"  \n**Python Version:** {check_result.python_version}"

        # Add output if available
        if check_result.output.strip():
            detail += f"\n\n**Output:**\n```\n{check_result.output.strip()}\n```"

        # Add errors
        if check_result.errors:
            detail += f"\n\n**Errors ({len(check_result.errors)}):**"
            for i, error in enumerate(check_result.errors, 1):
                detail += f"\n{i}. {error}"

        # Add warnings
        if check_result.warnings:
            detail += f"\n\n**Warnings ({len(check_result.warnings)}):**"
            for i, warning in enumerate(check_result.warnings, 1):
                detail += f"\n{i}. ⚠️ {warning}"

        # Add suggestions
        if check_result.suggestions:
            detail += f"\n\n**Suggestions:**"
            for i, suggestion in enumerate(check_result.suggestions, 1):
                detail += f"\n{i}. 💡 {suggestion}"

        # Add metadata if relevant
        if check_result.metadata:
            relevant_metadata = {k: v for k, v in check_result.metadata.items()
                               if k not in ['internal_id', 'temp_files']}
            if relevant_metadata:
                detail += f"\n\n**Additional Information:**"
                for key, value in relevant_metadata.items():
                    detail += f"\n- **{key.replace('_', ' ').title()}:** {value}"

        return detail

    def _generate_regression_analysis(self, result: SimulationResult) -> str:
        """Generate regression analysis section."""
        if not result.regression_issues:
            return ""

        sections = ["## Performance Regression Analysis"]

        # Group by severity
        by_severity = {}
        for issue in result.regression_issues:
            severity = issue.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)

        # Generate summary
        total_regressions = len(result.regression_issues)
        sections.append(f"**Total Regressions Detected:** {total_regressions}")

        # Add severity breakdown
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        for severity in severity_order:
            if severity in by_severity:
                count = len(by_severity[severity])
                emoji = self._get_severity_emoji(SeverityLevel(severity))
                sections.append(f"- **{severity.title()}:** {count} {emoji}")

        # Detailed regression information
        sections.append("### Regression Details")

        for severity in severity_order:
            if severity not in by_severity:
                continue

            issues = by_severity[severity]
            emoji = self._get_severity_emoji(SeverityLevel(severity))
            sections.append(f"#### {severity.title()} Severity {emoji}")

            for issue in issues:
                change_direction = "↗️" if issue.current_value > issue.baseline_value else "↘️"
                sections.append(f"""**{issue.test_name}**
- **Baseline:** {issue.baseline_value:.2f} {issue.metric_type}
- **Current:** {issue.current_value:.2f} {issue.metric_type} {change_direction}
- **Change:** {issue.regression_percentage:+.1f}%
- **Description:** {issue.description}""")

        return "\n\n".join(sections)

    def _generate_error_analysis(self, result: SimulationResult) -> str:
        """Generate error analysis and categorization."""
        all_errors = []
        all_warnings = []

        for check_result in result.check_results.values():
            all_errors.extend([(check_result.name, error) for error in check_result.errors])
            all_warnings.extend([(check_result.name, warning) for warning in check_result.warnings])

        if not all_errors and not all_warnings:
            return ""

        sections = ["## Error Analysis"]

        if all_errors:
            sections.append(f"### Errors ({len(all_errors)})")
            error_categories = self._categorize_errors(all_errors)

            for category, errors in error_categories.items():
                sections.append(f"#### {category} ({len(errors)})")
                for check_name, error in errors[:5]:  # Limit to first 5 per category
                    sections.append(f"- **{check_name}:** {error}")
                if len(errors) > 5:
                    sections.append(f"- ... and {len(errors) - 5} more similar errors")

        if all_warnings:
            sections.append(f"### Warnings ({len(all_warnings)})")
            for check_name, warning in all_warnings[:10]:  # Limit to first 10 warnings
                sections.append(f"- **{check_name}:** ⚠️ {warning}")
            if len(all_warnings) > 10:
                sections.append(f"- ... and {len(all_warnings) - 10} more warnings")

        return "\n\n".join(sections)

    def _generate_fix_suggestions(self, result: SimulationResult) -> str:
        """Generate fix suggestions based on common error patterns."""
        all_suggestions = []

        for check_result in result.check_results.values():
            all_suggestions.extend(check_result.suggestions)

        # Add automatic suggestions based on error patterns
        auto_suggestions = self._generate_automatic_suggestions(result)
        all_suggestions.extend(auto_suggestions)

        if not all_suggestions:
            return ""

        sections = ["## Fix Suggestions"]

        # Remove duplicates while preserving order
        unique_suggestions = []
        seen = set()
        for suggestion in all_suggestions:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)

        for i, suggestion in enumerate(unique_suggestions, 1):
            sections.append(f"{i}. 💡 {suggestion}")

        return "\n\n".join(sections)

    def _generate_configuration_info(self, result: SimulationResult) -> str:
        """Generate configuration information section."""
        if not result.configuration:
            return ""

        sections = ["## Configuration"]

        for key, value in result.configuration.items():
            if isinstance(value, (dict, list)):
                sections.append(f"**{key.replace('_', ' ').title()}:**")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        sections.append(f"- {sub_key}: {sub_value}")
                else:
                    for item in value:
                        sections.append(f"- {item}")
            else:
                sections.append(f"**{key.replace('_', ' ').title()}:** {value}")

        return "\n\n".join(sections)

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return f"""---

*Report generated by PhotoGeoView CI Simulation Tool*
*Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""

    def _get_status_emoji(self, status: CheckStatus) -> str:
        """Get emoji representation for check status."""
        emoji_map = {
            CheckStatus.SUCCESS: "✅",
            CheckStatus.FAILURE: "❌",
            CheckStatus.WARNING: "⚠️",
            CheckStatus.SKIPPED: "⏭️",
            CheckStatus.IN_PROGRESS: "🔄"
        }
        return emoji_map.get(status, "❓")

    def _get_severity_emoji(self, severity: SeverityLevel) -> str:
        """Get emoji representation for severity level."""
        emoji_map = {
            SeverityLevel.CRITICAL: "🔴",
            SeverityLevel.HIGH: "🟠",
            SeverityLevel.MEDIUM: "🟡",
            SeverityLevel.LOW: "🔵",
            SeverityLevel.INFO: "ℹ️"
        }
        return emoji_map.get(severity, "❓")

    def _get_success_rate_indicator(self, success_rate: float) -> str:
        """Get visual indicator for success rate."""
        if success_rate >= 90:
            return f"{success_rate:.1f}% 🟢"
        elif success_rate >= 70:
            return f"{success_rate:.1f}% 🟡"
        else:
            return f"{success_rate:.1f}% 🔴"

    def _categorize_errors(self, errors: List[tuple]) -> Dict[str, List[tuple]]:
        """Categorize errors by type for better organization."""
        categories = {
            "Syntax Errors": [],
            "Import Errors": [],
            "Type Errors": [],
            "Test Failures": [],
            "Security Issues": [],
            "Performance Issues": [],
            "Configuration Errors": [],
            "Other Errors": []
        }

        for check_name, error in errors:
            error_lower = error.lower()

            if any(keyword in error_lower for keyword in ['syntax', 'invalid syntax', 'unexpected token']):
                categories["Syntax Errors"].append((check_name, error))
            elif any(keyword in error_lower for keyword in ['import', 'module', 'no module named']):
                categories["Import Errors"].append((check_name, error))
            elif any(keyword in error_lower for keyword in ['type', 'mypy', 'annotation']):
                categories["Type Errors"].append((check_name, error))
            elif any(keyword in error_lower for keyword in ['test', 'assert', 'failed']):
                categories["Test Failures"].append((check_name, error))
            elif any(keyword in error_lower for keyword in ['security', 'vulnerability', 'bandit', 'safety']):
                categories["Security Issues"].append((check_name, error))
            elif any(keyword in error_lower for keyword in ['performance', 'slow', 'timeout', 'memory']):
                categories["Performance Issues"].append((check_name, error))
            elif any(keyword in error_lower for keyword in ['config', 'configuration', 'setting']):
                categories["Configuration Errors"].append((check_name, error))
            else:
                categories["Other Errors"].append((check_name, error))

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _generate_automatic_suggestions(self, result: SimulationResult) -> List[str]:
        """Generate automatic fix suggestions based on error patterns."""
        suggestions = []

        # Analyze failed checks for common patterns
        failed_checks = result.failed_checks

        # Check for common issues
        has_import_errors = any('import' in ' '.join(check.errors).lower() for check in failed_checks)
        has_type_errors = any('mypy' in check.name.lower() for check in failed_checks if not check.is_successful)
        has_format_errors = any('black' in check.name.lower() or 'isort' in check.name.lower()
                               for check in failed_checks)
        has_test_failures = any('test' in check.name.lower() for check in failed_checks)
        has_security_issues = any('security' in check.name.lower() for check in failed_checks)

        if has_import_errors:
            suggestions.append("Check your Python environment and ensure all required dependencies are installed")
            suggestions.append("Run 'pip install -r requirements.txt' to install missing dependencies")

        if has_type_errors:
            suggestions.append("Review type annotations and ensure they match the actual usage")
            suggestions.append("Consider adding '# type: ignore' comments for unavoidable type issues")

        if has_format_errors:
            suggestions.append("Run 'black .' and 'isort .' to automatically fix formatting issues")

        if has_test_failures:
            suggestions.append("Review test failures and update tests to match current implementation")
            suggestions.append("Check if test data or fixtures need to be updated")

        if has_security_issues:
            suggestions.append("Review security scan results and update vulnerable dependencies")
            suggestions.append("Consider using 'pip-audit' for additional security scanning")

        if result.regression_issues:
            suggestions.append("Investigate performance regressions and optimize affected code paths")
            suggestions.append("Consider profiling the application to identify bottlenecks")

        return suggestions
