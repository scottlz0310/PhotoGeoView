#!/usr/bin/env python3
"""
CI Integration Tool

This script helps integrate the CI simulator with existing project workflows
and provides utilities for managing CI configuration and execution.

AI Contributors:
- Kiro: CI integration system design and implementation

Created by: Kiro AI Integration System
Created on: 2025-01-30
"""

import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import argparse


class CIIntegrator:
    """
    CI Integration manager that helps integrate the CI simulator
    with existing project workflows and build processes.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.ci_simulator_path = self.project_root / "tools" / "ci" / "simulator.py"

    def validate_integration(self) -> Dict[str, Any]:
        """
        Validate that the CI simulator is properly integrated with the project

        Returns:
            Dictionary containing validation results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "SUCCESS",
            "checks": {},
            "recommendations": []
        }

        # Check if CI simulator exists
        if self.ci_simulator_path.exists():
            results["checks"]["ci_simulator_exists"] = {
                "status": "SUCCESS",
                "message": "CI simulator found"
            }
        else:
            results["checks"]["ci_simulator_exists"] = {
                "status": "FAILURE",
                "message": "CI simulator not found"
            }
            results["overall_status"] = "FAILURE"
            results["recommendations"].append("Install CI simulator components")

        # Check pyproject.toml integration
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'ci-simulator' in content:
                    results["checks"]["pyproject_integration"] = {
                        "status": "SUCCESS",
                        "message": "CI simulator integrated in pyproject.toml"
                    }
                else:
                    results["checks"]["pyproject_integration"] = {
                        "status": "WARNING",
                        "message": "CI simulator not found in pyproject.toml scripts"
                    }
                    results["recommendations"].append("Add CI simulator to pyproject.toml scripts")

            except Exception as e:
                results["checks"]["pyproject_integration"] = {
                    "status": "FAILURE",
                    "message": f"Error reading pyproject.toml: {e}"
                }
                results["overall_status"] = "FAILURE"
        else:
            results["checks"]["pyproject_integration"] = {
                "status": "WARNING",
                "message": "pyproject.toml not found"
            }

        # Check Makefile integration
        makefile_path = self.project_root / "Makefile"
        if makefile_path.exists():
            try:
                with open(makefile_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'tools.ci.simulator' in content:
                    results["checks"]["makefile_integration"] = {
                        "status": "SUCCESS",
                        "message": "CI simulator integrated in Makefile"
                    }
                else:
                    results["checks"]["makefile_integration"] = {
                        "status": "WARNING",
                        "message": "CI simulator not found in Makefile"
                    }
                    results["recommendations"].append("Add CI simulator targets to Makefile")

            except Exception as e:
                results["checks"]["makefile_integration"] = {
                    "status": "FAILURE",
                    "message": f"Error reading Makefile: {e}"
                }
        else:
            results["checks"]["makefile_integration"] = {
                "status": "INFO",
                "message": "Makefile not found (optional)"
            }

        # Check required directories
        required_dirs = [
            "tools/ci",
            "reports",
            "logs",
            ".kiro/ci-history"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                results["checks"][f"directory_{dir_path.replace('/', '_')}"] = {
                    "status": "SUCCESS",
                    "message": f"Directory {dir_path} exists"
                }
            else:
                results["checks"][f"directory_{dir_path.replace('/', '_')}"] = {
                    "status": "WARNING",
                    "message": f"Directory {dir_path} missing (will be created automatically)"
                }

        # Check CI simulator functionality
        if self.ci_simulator_path.exists():
            try:
                result = subprocess.run([
                    sys.executable, "-m", "tools.ci.simulator",
                    "list", "--format", "json"
                ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    results["checks"]["ci_simulator_functional"] = {
                        "status": "SUCCESS",
                        "message": "CI simulator is functional"
                    }

                    # Parse available checks
                    try:
                        output_data = json.loads(result.stdout)
                        available_checks = output_data.get("available_checks", [])
                        results["available_checks"] = available_checks
                        results["checks"]["available_checks_count"] = {
                            "status": "INFO",
                            "message": f"{len(available_checks)} checks available"
                        }
                    except json.JSONDecodeError:
                        pass

                else:
                    results["checks"]["ci_simulator_functional"] = {
                        "status": "FAILURE",
                        "message": f"CI simulator failed to run: {result.stderr}"
                    }
                    results["overall_status"] = "FAILURE"

            except subprocess.TimeoutExpired:
                results["checks"]["ci_simulator_functional"] = {
                    "status": "FAILURE",
                    "message": "CI simulator timed out"
                }
                results["overall_status"] = "FAILURE"
            except Exception as e:
                results["checks"]["ci_simulator_functional"] = {
                    "status": "FAILURE",
                    "message": f"Error testing CI simulator: {e}"
                }
                results["overall_status"] = "FAILURE"

        # Set overall status based on failures
        failure_count = sum(1 for check in results["checks"].values()
                          if check["status"] == "FAILURE")
        if failure_count > 0:
            results["overall_status"] = "FAILURE"
        elif any(check["status"] == "WARNING" for check in results["checks"].values()):
            results["overall_status"] = "WARNING"

        return results

    def run_integration_test(self) -> bool:
        """
        Run a comprehensive integration test to ensure CI simulator
        works properly with the project.

        Returns:
            True if integration test passes
        """
        print("Running CI integration test...")

        try:
            # Run a quick CI check to test integration
            result = subprocess.run([
                sys.executable, "-m", "tools.ci.simulator",
                "run", "--checks", "code_quality",
                "--format", "json",
                "--output-dir", "temp/integration-test"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ Integration test passed")

                # Clean up test output
                test_dir = self.project_root / "temp" / "integration-test"
                if test_dir.exists():
                    shutil.rmtree(test_dir)

                return True
            else:
                print("❌ Integration test failed")
                print(f"Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Integration test timed out")
            return False
        except Exception as e:
            print(f"❌ Integration test error: {e}")
            return False

    def setup_git_hooks(self) -> Dict[str, bool]:
        """
        Set up recommended Git hooks for CI integration.

        Returns:
            Dictionary mapping hook types to success status
        """
        print("Setting up Git hooks...")

        results = {}

        try:
            # Install pre-commit hook
            result = subprocess.run([
                sys.executable, "-m", "tools.ci.simulator",
                "hook", "setup"
            ], cwd=self.project_root, capture_output=True, text=True)

            results["setup"] = result.returncode == 0

            if result.returncode == 0:
                print("✅ Git hooks set up successfully")
            else:
                print("❌ Git hooks setup failed")
                print(f"Error: {result.stderr}")

        except Exception as e:
            print(f"❌ Git hooks setup error: {e}")
            results["setup"] = False

        return results

    def generate_integration_report(self, output_path: Optional[Path] = None) -> Path:
        """
        Generate a comprehensive integration report.

        Args:
            output_path: Optional path for the report file

        Returns:
            Path to the generated report
        """
        if output_path is None:
            output_path = self.project_root / "reports" / "ci-integration-report.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Run validation
        validation_results = self.validate_integration()

        # Generate report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# CI Integration Report\n\n")
            f.write(f"**Generated:** {validation_results['timestamp']}\n")
            f.write(f"**Overall Status:** {validation_results['overall_status']}\n\n")

            f.write("## Integration Checks\n\n")

            for check_name, check_result in validation_results["checks"].items():
                status_icon = {
                    "SUCCESS": "✅",
                    "WARNING": "⚠️",
                    "FAILURE": "❌",
                    "INFO": "ℹ️"
                }.get(check_result["status"], "❓")

                f.write(f"### {check_name.replace('_', ' ').title()}\n\n")
                f.write(f"{status_icon} **Status:** {check_result['status']}\n\n")
                f.write(f"**Message:** {check_result['message']}\n\n")

            if validation_results.get("available_checks"):
                f.write("## Available CI Checks\n\n")
                for check in validation_results["available_checks"]:
                    f.write(f"- {check}\n")
                f.write("\n")

            if validation_results["recommendations"]:
                f.write("## Recommendations\n\n")
                for recommendation in validation_results["recommendations"]:
                    f.write(f"- {recommendation}\n")
                f.write("\n")

            f.write("## Usage Examples\n\n")
            f.write("### Run all CI checks\n")
            f.write("```bash\n")
            f.write("make ci-full\n")
            f.write("# or\n")
            f.write("python -m tools.ci.simulator run --checks all\n")
            f.write("```\n\n")

            f.write("### Run quick checks\n")
            f.write("```bash\n")
            f.write("make ci-quick\n")
            f.write("# or\n")
            f.write("python -m tools.ci.simulator run --checks code_quality test_runner --fail-fast\n")
            f.write("```\n\n")

            f.write("### Build with CI\n")
            f.write("```bash\n")
            f.write("make build\n")
            f.write("# or\n")
            f.write("python scripts/build_with_ci.py\n")
            f.write("```\n\n")

            f.write("### Deploy with CI\n")
            f.write("```bash\n")
            f.write("make deploy\n")
            f.write("# or\n")
            f.write("python tools/create_deployment_package.py\n")
            f.write("```\n\n")

        print(f"Integration report generated: {output_path}")
        return output_path

    def update_github_actions(self) -> bool:
        """
        Update GitHub Actions workflow to use the CI simulator.

        Returns:
            True if update was successful
        """
        workflow_path = self.project_root / ".github" / "workflows" / "ai-integration-ci.yml"

        if not workflow_path.exists():
            print("GitHub Actions workflow not found")
            return False

        try:
            # Read current workflow
            with open(workflow_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if CI simulator is already integrated
            if 'tools.ci.simulator' in content:
                print("GitHub Actions workflow already uses CI simulator")
                return True

            # Create backup
            backup_path = workflow_path.with_suffix('.yml.backup')
            shutil.copy2(workflow_path, backup_path)
            print(f"Created backup: {backup_path}")

            # Add CI simulator integration step
            ci_step = """
    - name: Run CI Simulator
      env:
        QT_QPA_PLATFORM: offscreen
        DISPLAY: ':99'
      run: |
        xvfb-run -a python -m tools.ci.simulator run --checks all --format json --output-dir reports/ci-simulation
        echo "CI simulation completed"
"""

            # Insert the step after dependency installation
            lines = content.split('\n')
            new_lines = []

            for i, line in enumerate(lines):
                new_lines.append(line)

                # Insert CI simulator step after pip install
                if 'pip install -r requirements.txt' in line:
                    new_lines.extend(ci_step.split('\n'))

            # Write updated workflow
            with open(workflow_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))

            print("✅ GitHub Actions workflow updated with CI simulator")
            return True

        except Exception as e:
            print(f"❌ Failed to update GitHub Actions workflow: {e}")
            return False


def main():
    """Main entry point for the CI integration tool."""
    parser = argparse.ArgumentParser(description="CI Integration Tool")
    parser.add_argument("command", choices=[
        "validate", "test", "setup-hooks", "report", "update-github-actions"
    ], help="Command to execute")
    parser.add_argument("--output", type=Path, help="Output path for reports")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown",
                       help="Output format")

    args = parser.parse_args()

    integrator = CIIntegrator()

    if args.command == "validate":
        results = integrator.validate_integration()

        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            print("CI Integration Validation")
            print("=" * 40)
            print(f"Overall Status: {results['overall_status']}")
            print()

            for check_name, check_result in results["checks"].items():
                status_icon = {
                    "SUCCESS": "✅",
                    "WARNING": "⚠️",
                    "FAILURE": "❌",
                    "INFO": "ℹ️"
                }.get(check_result["status"], "❓")

                print(f"{status_icon} {check_name}: {check_result['message']}")

            if results["recommendations"]:
                print("\nRecommendations:")
                for rec in results["recommendations"]:
                    print(f"  - {rec}")

        return 0 if results["overall_status"] != "FAILURE" else 1

    elif args.command == "test":
        success = integrator.run_integration_test()
        return 0 if success else 1

    elif args.command == "setup-hooks":
        results = integrator.setup_git_hooks()
        success = all(results.values())
        return 0 if success else 1

    elif args.command == "report":
        report_path = integrator.generate_integration_report(args.output)
        print(f"Report generated: {report_path}")
        return 0

    elif args.command == "update-github-actions":
        success = integrator.update_github_actions()
        return 0 if success else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
