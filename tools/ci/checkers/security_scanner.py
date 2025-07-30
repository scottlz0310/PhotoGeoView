"""
Security Scanner for CI Simulation Tool

This module implements comprehensive security scanning including
safety vulnerability scanning for dependencies and bandit security
linting for code analysis with detailed reporting and fix suggestions.
"""

import subprocess
import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import time
from dataclasses import dataclass

try:
    from ..interfaces import CheckerInterface
    from ..models import CheckResult, CheckStatus, ConfigDict, SeverityLevel
except ImportError:
    from interfaces import CheckerInterface
    from models import CheckResult, CheckStatus, ConfigDict, SeverityLevel


@dataclass
class SecurityIssue:
    """Represents a security issue found by a scanner."""

    file_path: str
    line_number: Optional[int]
    column: Optional[int]
    rule_code: str
    message: str
    severity: SeverityLevel
    tool: str
    cve_id: Optional[str] = None
    package_name: Optional[str] = None
    vulnerable_version: Optional[str] = None
    fixed_version: Optional[str] = None


class SecurityScanner(CheckerInterface):
    """
    Comprehensive security scanner with safety and bandit integration.

    This checker provides:
    - Safety vulnerability scanning for dependencies
    - Bandit security linting forlysis
    - Detailed security reports with fix suggestions
    - CVE tracking and vulnerability assessment
    """

    def __init__(self, config: ConfigDict):
        """
        Initialize the security scanner.

        Args:
            config: Configuration dictionary containing scanner settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()

        # Scanner configuration
        self.safety_config = config.get('safety', {})
        self.bandit_config = config.get('bandit', {})

        # Default settings
        self.timeout = config.get('timeout', 300)  # 5 minutes default
        self.ignore_files = config.get('ignore_files', [
            '*/venv/*', '*/env/*', '*/.venv/*', '*/node_modules/*',
            '*/__pycache__/*', '*/build/*', '*/dist/*'
        ])

    @property
    def name(self) -> str:
        """Return the human-readable name of this checker."""
        return "Security Scanner"

    @property
    def check_type(self) -> str:
        """Return the type category of this checker."""
        return "security"

    @property
    def dependencies(self) -> List[str]:
        """Return list of external dependencies required by this checker."""
        return ["safety", "bandit"]

    def is_available(self) -> bool:
        """
        Check if this checker can run in the current environment.

        Returns:
            True if all dependencies are available and checker can run
        """
        if self._is_available is not None:
            return self._is_available

        try:
            # Check safety availability
            result = subprocess.run(
                [sys.executable, "-m", "safety", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            safety_available = result.returncode == 0

            # Check bandit availability
            result = subprocess.run(
                [sys.executable, "-m", "bandit", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            bandit_available = result.returncode == 0

            self._is_available = safety_available and bandit_available

            if not self._is_available:
                missing = []
                if not safety_available:
                    missing.append("safety")
                if not bandit_available:
                    missing.append("bandit")
                self.logger.warning(f"Security scanner dependencies not available: {missing}")

        except Exception as e:
            self.logger.error(f"Error checking security scanner availability: {e}")
            self._is_available = False

        return self._is_available

    def run_check(self, **kwargs) -> CheckResult:
        """
        Execute the main security check logic.

        Args:
            **kwargs: Checker-specific arguments

        Returns:
            CheckResult containing the outcome of the security checks
        """
        start_time = time.time()

        if not self.is_available():
            return CheckResult(
                name=self.name,
                status=CheckStatus.SKIPPED,
                duration=time.time() - start_time,
                output="Security scanner dependencies not available",
                errors=["Missing dependencies: safety and/or bandit"],
                suggestions=[
                    "Install safety: pip install safety",
                    "Install bandit: pip install bandit"
                ]
            )

        try:
            # Run safety check
            safety_result = self.run_safety_check()

            # Run bandit scan
            bandit_result = self.run_bandit_scan()

            # Combine results
            combined_result = self._combine_security_results(safety_result, bandit_result)
            combined_result.duration = time.time() - start_time

            return combined_result

        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
            return CheckResult(
                name=self.name,
                status=CheckStatus.FAILURE,
                duration=time.time() - start_time,
                output=f"Security scan failed: {str(e)}",
                errors=[str(e)],
                suggestions=["Check security scanner configuration and dependencies"]
            )

    def run_safety_check(self) -> CheckResult:
        """
        Run safety vulnerability check on dependencies.

        Returns:
            CheckResult containing safety scan results
        """
        start_time = time.time()

        try:
            # Build safety command
            cmd = [sys.executable, "-m", "safety", "check", "--json"]

            # Add configuration options
            if self.safety_config.get('ignore_ids'):
                for ignore_id in self.safety_config['ignore_ids']:
                    cmd.extend(["--ignore", str(ignore_id)])

            if self.safety_config.get('full_report'):
                cmd.append("--full-report")

            # Run safety check
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.project_root
            )

            # Parse safety output
            vulnerabilities = self._parse_safety_output(result.stdout, result.stderr)

            # Determine status
            if result.returncode == 0:
                status = CheckStatus.SUCCESS
                output = "No known security vulnerabilities found in dependencies"
            else:
                status = CheckStatus.FAILURE if vulnerabilities else CheckStatus.WARNING
                output = f"Found {len(vulnerabilities)} security vulnerabilities in dependencies"

            # Generate suggestions
            suggestions = self._generate_safety_suggestions(vulnerabilities)

            return CheckResult(
                name="Safety Vulnerability Check",
                status=status,
                duration=time.time() - start_time,
                output=output,
                errors=[vuln.message for vuln in vulnerabilities if vuln.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]],
                warnings=[vuln.message for vuln in vulnerabilities if vuln.severity in [SeverityLevel.MEDIUM, SeverityLevel.LOW]],
                suggestions=suggestions,
                metadata={
                    'vulnerabilities': [self._vulnerability_to_dict(vuln) for vuln in vulnerabilities],
                    'total_vulnerabilities': len(vulnerabilities),
                    'critical_count': len([v for v in vulnerabilities if v.severity == SeverityLevel.CRITICAL]),
                    'high_count': len([v for v in vulnerabilities if v.severity == SeverityLevel.HIGH]),
                    'medium_count': len([v for v in vulnerabilities if v.severity == SeverityLevel.MEDIUM]),
                    'low_count': len([v for v in vulnerabilities if v.severity == SeverityLevel.LOW])
                }
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="Safety Vulnerability Check",
                status=CheckStatus.FAILURE,
                duration=time.time() - start_time,
                output="Safety check timed out",
                errors=["Safety vulnerability check exceeded timeout"],
                suggestions=["Increase timeout or check network connectivity"]
            )
        except Exception as e:
            return CheckResult(
                name="Safety Vulnerability Check",
                status=CheckStatus.FAILURE,
                duration=time.time() - start_time,
                output=f"Safety check failed: {str(e)}",
                errors=[str(e)],
                suggestions=["Check safety installation and configuration"]
            )
    def run_bandit_scan(self) -> CheckResult:
        """
        Run bandit security linting on code.

        Returns:
            CheckResult containing bandit scan results
        """
        start_time = time.time()

        try:
            # Build bandit command
            cmd = [sys.executable, "-m", "bandit", "-r", ".", "-f", "json"]

            # Add configuration options
            if self.bandit_config.get('exclude_dirs'):
                exclude_dirs = ','.join(self.bandit_config['exclude_dirs'])
                cmd.extend(["-x", exclude_dirs])
            else:
                # Default exclusions
                cmd.extend(["-x", "venv,env,.venv,node_modules,__pycache__,build,dist"])

            if self.bandit_config.get('skip_tests'):
                cmd.extend(["-s", "B101"])  # Skip assert_used test

            if self.bandit_config.get('confidence_level'):
                cmd.extend(["-i", self.bandit_config['confidence_level']])

            # Run bandit scan
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.project_root
            )

            # Parse bandit output
            issues = self._parse_bandit_output(result.stdout, result.stderr)

            # Determine status
            critical_issues = [i for i in issues if i.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
            if critical_issues:
                status = CheckStatus.FAILURE
                output = f"Found {len(critical_issues)} critical/high security issues in code"
            elif issues:
                status = CheckStatus.WARNING
                output = f"Found {len(issues)} security issues in code"
            else:
                status = CheckStatus.SUCCESS
                output = "No security issues found in code"

            # Generate suggestions
            suggestions = self._generate_bandit_suggestions(issues)

            return CheckResult(
                name="Bandit Security Linting",
                status=status,
                duration=time.time() - start_time,
                output=output,
                errors=[issue.message for issue in critical_issues],
                warnings=[issue.message for issue in issues if issue.severity in [SeverityLevel.MEDIUM, SeverityLevel.LOW]],
                suggestions=suggestions,
                metadata={
                    'issues': [self._issue_to_dict(issue) for issue in issues],
                    'total_issues': len(issues),
                    'critical_count': len([i for i in issues if i.severity == SeverityLevel.CRITICAL]),
                    'high_count': len([i for i in issues if i.severity == SeverityLevel.HIGH]),
                    'medium_count': len([i for i in issues if i.severity == SeverityLevel.MEDIUM]),
                    'low_count': len([i for i in issues if i.severity == SeverityLevel.LOW])
                }
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="Bandit Security Linting",
                status=CheckStatus.FAILURE,
                duration=time.time() - start_time,
                output="Bandit scan timed out",
                errors=["Bandit security scan exceeded timeout"],
                suggestions=["Increase timeout or exclude large directories"]
            )
        except Exception as e:
            return CheckResult(
                name="Bandit Security Linting",
                status=CheckStatus.FAILURE,
n=time.time() - start_time,
                output=f"Bandit scan failed: {str(e)}",
                errors=[str(e)],
                suggestions=["Check bandit installation and configuration"]
            )

    def run_full_security_scan(self) -> Dict[str, CheckResult]:
        """
        Run both safety and bandit scans and return individual results.

        Returns:
            Dictionary containing individual scan results
        """
        results = {}

        # Run safety check
        results['safety'] = self.run_safety_check()

        # Run bandit scan
        results['bandit'] = self.run_bandit_scan()

        return results

    def generate_security_report(self, results: Dict[str, CheckResult]) -> str:
        """
        Generate a comprehensive security report from scan results.

        Args:
            results: Dictionary of scan results

        Returns:
            Formatted security report string
        """
        report_lines = []
        report_lines.append("# Security Scan Report")
        report_lines.append("")
        report_lines.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Overall summary
        total_issues = 0
        critical_issues = 0
        high_issues = 0

        for result in results.values():
            if result.metadata:
                total_issues += result.metadata.get('total_vulnerabilities', 0) + result.metadata.get('total_issues', 0)
                critical_issues += result.metadata.get('critical_count', 0)
                high_issues += result.metadata.get('high_count', 0)

        report_lines.append("## Summary")
        report_lines.append(f"- Total security issues: {total_issues}")
        report_lines.append(f"- Critical issues: {critical_issues}")
        report_lines.append(f"- High severity issues: {high_issues}")
        report_lines.append("")

        # Individual scan results
        for scan_name, result in results.items():
            report_lines.append(f"## {result.name}")
            report_lines.append(f"Status: {result.status.value.upper()}")
            report_lines.append(f"Duration: {result.duration:.2f}s")
            report_lines.append("")

            if result.errors:
                report_lines.append("### Errors")
                for error in result.errors:
                    report_lines.append(f"- {error}")
                report_lines.append("")

            if result.warnings:
                report_lines.append("### Warnings")
                for warning in result.warnings:
                    report_lines.append(f"- {warning}")
                report_lines.append("")

            if result.suggestions:
                report_lines.append("### Suggestions")
                for suggestion in result.suggestions:
                    report_lines.append(f"- {suggestion}")
                report_lines.append("")

            # Detailed findings
            if result.metadata:
                if 'vulnerabilities' in result.metadata:
                    vulnerabilities = result.metadata['vulnerabilities']
                    if vulnerabilities:
                        report_lines.append("### Vulnerabilities Found")
                        for vuln in vulnerabilities:
                            report_lines.append(f"- **{vuln['package_name']}** ({vuln['vulnerable_version']})")
                            report_lines.append(f"  - CVE: {vuln.get('cve_id', 'N/A')}")
                            report_lines.append(f"  - Severity: {vuln['severity']}")
                            report_lines.append(f"  - Fix: Upgrade to {vuln.get('fixed_version', 'latest')}")
                            report_lines.append("")

                if 'issues' in result.metadata:
                    issues = result.metadata['issues']
                    if issues:
                        report_lines.append("### Code Security Issues")
                        for issue in issues:
                            report_lines.append(f"- **{issue['file_path']}:{issue.get('line_number', '?')}**")
                            report_lines.append(f"  - Rule: {issue['rule_code']}")
                            report_lines.append(f"  - Severity: {issue['severity']}")
                            report_lines.append(f"  - Message: {issue['message']}")
                            report_lines.append("")

        return "\n".join(report_lines)

    def _combine_security_results(self, safety_result: CheckResult, bandit_result: CheckResult) -> CheckResult:
        """
        Combine safety and bandit results into a single result.

        Args:
            safety_result: Result from safety check
            bandit_result: Result from bandit scan

        Returns:
            Combined CheckResult
        """
        # Determine overall status
        if safety_result.status == CheckStatus.FAILURE or bandit_result.status == CheckStatus.FAILURE:
            overall_status = CheckStatus.FAILURE
        elif safety_result.status == CheckStatus.WARNING or bandit_result.status == CheckStatus.WARNING:
            overall_status = CheckStatus.WARNING
        else:
            overall_status = CheckStatus.SUCCESS

        # Combine outputs
        outputs = []
        if safety_result.output:
            outputs.append(f"Safety: {safety_result.output}")
        if bandit_result.output:
            outputs.append(f"Bandit: {bandit_result.output}")

        # Combine errors, warnings, and suggestions
        all_errors = safety_result.errors + bandit_result.errors
        all_warnings = safety_result.warnings + bandit_result.warnings
        all_suggestions = safety_result.suggestions + bandit_result.suggestions

        # Combine metadata
        combined_metadata = {
            'safety_result': safety_result.metadata,
            'bandit_result': bandit_result.metadata,
            'total_vulnerabilities': safety_result.metadata.get('total_vulnerabilities', 0),
            'total_code_issues': bandit_result.metadata.get('total_issues', 0)
        }

        return CheckResult(
            name=self.name,
            status=overall_status,
            duration=0,  # Will be set by caller
            output="; ".join(outputs),
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metadata=combined_metadata
        )

    def _parse_safety_output(self, stdout: str, stderr: str) -> List[SecurityIssue]:
        """
        Parse safety JSON output into SecurityIssue objects.

        Args:
            stdout: Safety command stdout
            stderr: Safety command stderr

        Returns:
            List of SecurityIssue objects
        """
        vulnerabilities = []

        try:
            if stdout.strip():
                data = json.loads(stdout)

                # Safety returns a list of vulnerabilities
                for vuln in data:
                    # Map safety severity to our severity levels
                    severity_map = {
                        'high': SeverityLevel.HIGH,
                        'medium': SeverityLevel.MEDIUM,
                        'low': SeverityLevel.LOW
                    }

                    severity = severity_map.get(vuln.get('severity', 'medium').lower(), SeverityLevel.MEDIUM)

                    vulnerabilities.append(SecurityIssue(
                        file_path="requirements.txt",  # Safety scans dependencies
                        line_number=None,
                        column=None,
                        rule_code=vuln.get('id', 'SAFETY-UNKNOWN'),
                        message=vuln.get('advisory', 'Security vulnerability detected'),
                        severity=severity,
                        tool='safety',
                        cve_id=vuln.get('cve'),
                        package_name=vuln.get('package_name'),
                        vulnerable_version=vuln.get('analyzed_version'),
                        fixed_version=vuln.get('fixed_in', [None])[0] if vuln.get('fixed_in') else None
                    ))

        except json.JSONDecodeError:
            # If JSON parsing fails, try to parse text output
            if stderr and "vulnerabilities found" in stderr.lower():
                # Basic text parsing fallback
                lines = stderr.split('\n')
                for line in lines:
                    if 'vulnerability' in line.lower():
                        vulnerabilities.append(SecurityIssue(
                            file_path="requirements.txt",
                            line_number=None,
                            column=None,
                            rule_code="SAFETY-PARSE-ERROR",
                            message=line.strip(),
                            severity=SeverityLevel.MEDIUM,
                            tool='safety'
                        ))
        except Exception as e:
            self.logger.error(f"Error parsing safety output: {e}")

        return vulnerabilities
    def _parse_bandit_output(self, stdout: str, stderr: str) -> List[SecurityIssue]:
        """
        Parse bandit JSON output into SecurityIssue objects.

        Args:
            stdout: Bandit command stdout
            stderr: Bandit command stderr

        Returns:
            List of SecurityIssue objects
        """
        issues = []

        try:
            if stdout.strip():
                data = json.loads(stdout)

                # Bandit returns results in 'results' key
                results = data.get('results', [])

                for result in results:
                    # Map bandit severity to our severity levels
                    severity_map = {
                        'HIGH': SeverityLevel.HIGH,
                        'MEDIUM': SeverityLevel.MEDIUM,
                        'LOW': SeverityLevel.LOW
                    }

                    severity = severity_map.get(result.get('issue_severity', 'MEDIUM'), SeverityLevel.MEDIUM)

                    issues.append(SecurityIssue(
                        file_path=result.get('filename', 'unknown'),
                        line_number=result.get('line_number'),
                        column=result.get('col_offset'),
                        rule_code=result.get('test_id', 'BANDIT-UNKNOWN'),
                        message=result.get('issue_text', 'Security issue detected'),
                        severity=severity,
                        tool='bandit'
                    ))

        except json.JSONDecodeError:
            # If JSON parsing fails, try to parse text output
            if stderr:
                lines = stderr.split('\n')
                for line in lines:
                    if 'Issue:' in line or 'Severity:' in line:
                        issues.append(SecurityIssue(
                            file_path="unknown",
                            line_number=None,
                            column=None,
                            rule_code="BANDIT-PARSE-ERROR",
                            message=line.strip(),
                            severity=SeverityLevel.MEDIUM,
                            tool='bandit'
                        ))
        except Exception as e:
            self.logger.error(f"Error parsing bandit output: {e}")

        return issues

    def _generate_safety_suggestions(self, vulnerabilities: List[SecurityIssue]) -> List[str]:
        """
        Generate fix suggestions for safety vulnerabilities.

        Args:
            vulnerabilities: List of security vulnerabilities

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if not vulnerabilities:
            suggestions.append("No security vulnerabilities found in dependencies")
            return suggestions

        # Group by package for better suggestions
        packages = {}
        for vuln in vulnerabilities:
            if vuln.package_name:
                if vuln.package_name not in packages:
                    packages[vuln.package_name] = []
                packages[vuln.package_name].append(vuln)

        for package_name, vulns in packages.items():
            # Find the highest fixed version
            fixed_versions = [v.fixed_version for v in vulns if v.fixed_version]
            if fixed_versions:
                latest_fix = max(fixed_versions)
                suggestions.append(f"Update {package_name} to version {latest_fix} or later")
            else:
                suggestions.append(f"Review security advisories for {package_name}")

        # General suggestions
        suggestions.extend([
            "Run 'pip install --upgrade' to update vulnerable packages",
            "Consider using 'pip-audit' for continuous monitoring",
            "Review and update requirements.txt regularly",
            "Use virtual environments to isolate dependencies"
        ])

        return suggestions

    def _generate_bandit_suggestions(self, issues: List[SecurityIssue]) -> List[str]:
        """
        Generate fix suggestions for bandit security issues.

        Args:
            issues: List of security issues

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if not issues:
            suggestions.append("No security issues found in code")
            return suggestions

        # Group by rule code for better suggestions
        rule_counts = {}
        for issue in issues:
            rule_counts[issue.rule_code] = rule_counts.get(issue.rule_code, 0) + 1

        # Provide specific suggestions based on common rules
        rule_suggestions = {
            'B101': 'Remove or replace assert statements in production code',
            'B102': 'Avoid using exec() function - use safer alternatives',
            'B103': 'Set file permissions explicitly instead of using 0o777',
            'B104': 'Bind to specific interfaces instead of 0.0.0.0',
            'B105': 'Use secure string formatting instead of % formatting',
            'B106': 'Use secure random number generation',
            'B107': 'Use secure XML parsing to prevent XXE attacks',
            'B108': 'Use secure temporary file creation',
            'B110': 'Avoid using try/except/pass - handle exceptions properly',
            'B201': 'Use secure Flask configurations',
            'B301': 'Use secure pickle alternatives like json',
            'B302': 'Use secure marshalling alternatives',
            'B303': 'Use secure MD5 alternatives like SHA-256',
            'B304': 'Use secure cipher modes and key sizes',
            'B305': 'Use secure cipher algorithms',
            'B306': 'Use secure random number generation',
            'B307': 'Use secure eval() alternatives',
            'B308': 'Use secure mark_safe() alternatives',
            'B309': 'Use secure HTTPSConnection instead of HTTPConnection',
            'B310': 'Use secure URL validation',
            'B311': 'Use secure random number generation',
            'B312': 'Use secure telnet alternatives like SSH',
            'B313': 'Use secure XML parsing libraries',
            'B314': 'Use secure XML parsing configurations',
            'B315': 'Use secure XML parsing to prevent XXE',
            'B316': 'Use secure XML parsing libraries',
            'B317': 'Use secure XML-RPC configurations',
            'B318': 'Use secure XML parsing libraries',
            'B319': 'Use secure XML parsing configurations',
            'B320': 'Use secure XML parsing to prevent XXE',
            'B321': 'Use secure FTP alternatives like SFTP',
            'B322': 'Use secure input validation',
            'B323': 'Use secure URL parsing',
            'B324': 'Use secure hash algorithms',
            'B325': 'Use secure temporary file creation',
            'B501': 'Use secure SSL/TLS configurations',
            'B502': 'Use secure SSL/TLS certificate validation',
            'B503': 'Use secure SSL/TLS configurations',
            'B504': 'Use secure SSL/TLS configurations',
            'B505': 'Use secure SSL/TLS configurations',
            'B506': 'Use secure YAML loading',
            'B507': 'Use secure SSH configurations',
            'B601': 'Use parameterized queries to prevent SQL injection',
            'B602': 'Use secure subprocess configurations',
            'B603': 'Use secure subprocess configurations',
            'B604': 'Use secure function calls',
            'B605': 'Use secure string formatting',
            'B606': 'Use secure subprocess configurations',
            'B607': 'Use absolute paths for executables',
            'B608': 'Use secure SQL query construction',
            'B609': 'Use secure wildcard imports',
            'B610': 'Use secure Django configurations',
            'B611': 'Use secure Django configurations'
        }

        for rule_code, count in rule_counts.items():
            if rule_code in rule_suggestions:
                suggestions.append(f"{rule_suggestions[rule_code]} ({count} occurrence{'s' if count > 1 else ''})")
            else:
                suggestions.append(f"Review and fix {rule_code} security issues ({count} occurrence{'s' if count > 1 else ''})")

        # General suggestions
        suggestions.extend([
            "Review bandit documentation for detailed fix guidance",
            "Consider using bandit configuration file to customize rules",
            "Implement security code review practices",
            "Use static analysis tools in CI/CD pipeline"
        ])

        return suggestions

    def _vulnerability_to_dict(self, vuln: SecurityIssue) -> Dict[str, Any]:
        """Convert SecurityIssue vulnerability to dictionary."""
        return {
            'file_path': vuln.file_path,
            'line_number': vuln.line_number,
            'rule_code': vuln.rule_code,
            'message': vuln.message,
            'severity': vuln.severity.value,
            'tool': vuln.tool,
            'cve_id': vuln.cve_id,
            'package_name': vuln.package_name,
            'vulnerable_version': vuln.vulnerable_version,
            'fixed_version': vuln.fixed_version
        }

    def _issue_to_dict(self, issue: SecurityIssue) -> Dict[str, Any]:
        """Convert SecurityIssue to dictionary."""
        return {
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'column': issue.column,
            'rule_code': issue.rule_code,
            'message': issue.message,
            'severity': issue.severity.value,
            'tool': issue.tool
        }

    def get_default_config(self) -> ConfigDict:
        """
        Get default configuration for the security scanner.

        Returns:
            Dictionary containing default configuration values
        """
        return {
            'timeout': 300,
            'safety': {
                'ignore_ids': [],
                'full_report': True
            },
            'bandit': {
                'exclude_dirs': ['venv', 'env', '.venv', 'node_modules', '__pycache__', 'build', 'dist'],
                'skip_tests': True,
                'confidence_level': 'LOW'
            },
            'ignore_files': [
                '*/venv/*', '*/env/*', '*/.venv/*', '*/node_modules/*',
                '*/__pycache__/*', '*/build/*', '*/dist/*'
            ]
        }

    def cleanup(self) -> None:
        """
        Perform any necessary cleanup after check execution.
        """
        # No specific cleanup needed for security scanner
        pass


# SecurityScanner is registered by the simulator during initialization
