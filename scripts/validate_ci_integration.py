#!/usr/bin/env python3
"""
CI Integration Validation Script

This script validates that the CI simulator is properly integrated with the
existing project structure and build processes.

AI貢献者:
- Kiro: CI統合検証システム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月30日
"""

import sys
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil


class CIIntegrationValidator:
    """CI統合検証器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.validation_results = {}

    def validate_project_structure(self) -> bool:
        """プロジェクト構造の検証"""
        print("Validating project structure...")

        required_files = [
            "pyproject.toml",
            "requirements.txt",
            "Makefile",
            ".pre-commit-config.yaml",
            "tools/ci/simulator.py",
            "tools/create_deployment_package.py"
        ]

        required_directories = [
            "tools/ci",
            "tools/ci/checkers",
            "tools/ci/reporters",
            "tools/ci/environment",
            ".kiro/specs/ci-cd-simulation"
        ]

        missing_files = []
        missing_dirs = []

        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)

        for dir_path in required_directories:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)

        if missing_files or missing_dirs:
            print("❌ Missing required files/directories:")
            for file in missing_files:
                print(f"  - File: {file}")
            for dir in missing_dirs:
                print(f"  - Directory: {dir}")
            return False

        print("✅ Project structure validation passed")
        return True

    def validate_pyproject_integration(self) -> bool:
        """pyproject.toml統合の検証"""
        print("Validating pyproject.toml integration...")

        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            print("❌ pyproject.toml not found")
            return False

        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for CI simulator script entries
            if "ci-simulator" not in content:
                print("❌ CI simulator script entry not found in pyproject.toml")
                return False

            # Check for CI dependencies
            if "[project.optional-dependencies]" not in content:
                print("❌ Optional dependencies section not found")
                return False

            if "ci =" not in content:
                print("❌ CI dependencies not defined")
                return False

            # Check for CI simulator configuration
            if "[tool.ci_simulator]" not in content:
                print("❌ CI simulator configuration not found")
                return False

            print("✅ pyproject.toml integration validation passed")
            return True

        except Exception as e:
            print(f"❌ Error validating pyproject.toml: {e}")
            return False

    def validate_makefile_integration(self) -> bool:
        """Makefile統合の検証"""
        print("Validating Makefile integration...")

        makefile_path = self.project_root / "Makefile"
        if not makefile_path.exists():
            print("❌ Makefile not found")
            return False

        try:
            with open(makefile_path, "r", encoding="utf-8") as f:
                content = f.read()

            required_targets = [
                "ci:",
                "ci-quick:",
                "ci-full:",
                "setup-hooks:",
                "validate-ci-integration:"
            ]

            missing_targets = []
            for target in required_targets:
                if target not in content:
                    missing_targets.append(target)

            if missing_targets:
                print("❌ Missing Makefile targets:")
                for target in missing_targets:
                    print(f"  - {target}")
                return False

            print("✅ Makefile integration validation passed")
            return True

        except Exception as e:
            print(f"❌ Error validating Makefile: {e}")
            return False

    def validate_ci_simulator_functionality(self) -> bool:
        """CI simulator機能の検証"""
        print("Validating CI simulator functionality...")

        try:
            # Test CI simulator import
            result = subprocess.run([
                sys.executable,
                "-c",
                "from tools.ci.simulator import CISimulator; print('Import successful')"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                print(f"❌ CI simulator import failed: {result.stderr}")
                return False

            # Test CI simulator help
            result = subprocess.run([
                sys.executable,
                "-m", "tools.ci.simulator",
                "--help"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                print(f"❌ CI simulator help command failed: {result.stderr}")
                return False

            # Test CI simulator list command
            result = subprocess.run([
                sys.executable,
                "-m", "tools.ci.simulator",
                "list"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                print(f"❌ CI simulator list command failed: {result.stderr}")
                return False

            print("✅ CI simulator functionality validation passed")
            return True

        except subprocess.TimeoutExpired:
            print("❌ CI simulator functionality test timed out")
            return False
        except Exception as e:
            print(f"❌ Error validating CI simulator functionality: {e}")
            return False

    def validate_git_hook_integration(self) -> bool:
        """Git hook統合の検証"""
        print("Validating Git hook integration...")

        try:
            # Check if we're in a Git repository
            result = subprocess.run([
                "git", "rev-parse", "--git-dir"
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print("⚠️ Not in a Git repository, skipping Git hook validation")
                return True

            # Test Git hook status command
            result = subprocess.run([
                sys.executable,
                "-m", "tools.ci.simulator",
                "hook", "status"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                print(f"❌ Git hook status command failed: {result.stderr}")
                return False

            print("✅ Git hook integration validation passed")
            return True

        except subprocess.TimeoutExpired:
            print("❌ Git hook integration test timed out")
            return False
        except Exception as e:
            print(f"❌ Error validating Git hook integration: {e}")
            return False

    def validate_deployment_integration(self) -> bool:
        """デプロイメント統合の検証"""
        print("Validating deployment integration...")

        deployment_script = self.project_root / "tools" / "create_deployment_package.py"
        if not deployment_script.exists():
            print("❌ Deployment script not found")
            return False

        try:
            # Check if deployment script imports CI simulator functionality
            with open(deployment_script, "r", encoding="utf-8") as f:
                content = f.read()

            if "run_ci_simulation" not in content:
                print("❌ CI simulation not integrated in deployment script")
                return False

            if "tools.ci.simulator" not in content:
                print("❌ CI simulator not referenced in deployment script")
                return False

            # Test deployment script help
            result = subprocess.run([
                sys.executable,
                str(deployment_script),
                "--help"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                print(f"❌ Deployment script help failed: {result.stderr}")
                return False

            print("✅ Deployment integration validation passed")
            return True

        except subprocess.TimeoutExpired:
            print("❌ Deployment integration test timed out")
            return False
        except Exception as e:
            print(f"❌ Error validating deployment integration: {e}")
            return False

    def validate_github_actions_integration(self) -> bool:
        """GitHub Actions統合の検証"""
        print("Validating GitHub Actions integration...")

        workflows_dir = self.project_root / ".github" / "workflows"
        if not workflows_dir.exists():
            print("⚠️ GitHub workflows directory not found, skipping validation")
            return True

        required_workflows = [
            "ai-integration-ci.yml",
            "ai-integration-tests.yml",
            "ci-simulator.yml"
        ]

        missing_workflows = []
        for workflow in required_workflows:
            workflow_path = workflows_dir / workflow
            if not workflow_path.exists():
                missing_workflows.append(workflow)
                continue

            # Check if workflow references CI simulator
            try:
                with open(workflow_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if "tools.ci.simulator" not in content and workflow == "ci-simulator.yml":
                    print(f"⚠️ {workflow} doesn't reference CI simulator")

            except Exception as e:
                print(f"⚠️ Error reading {workflow}: {e}")

        if missing_workflows:
            print("❌ Missing GitHub workflow files:")
            for workflow in missing_workflows:
                print(f"  - {workflow}")
            return False

        print("✅ GitHub Actions integration validation passed")
        return True

    def run_integration_test(self) -> bool:
        """統合テストの実行"""
        print("Running integration test...")

        try:
            # Create temporary directory for test output
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Run a quick CI simulation test
                result = subprocess.run([
                    sys.executable,
                    "-m", "tools.ci.simulator",
                    "run",
                    "--checks", "code_quality",
                    "--format", "json",
                    "--output-dir", str(temp_path),
                    "--timeout", "300"
                ], cwd=self.project_root, capture_output=True, text=True, timeout=360)

                if result.returncode != 0:
                    print(f"❌ Integration test failed: {result.stderr}")
                    return False

                # Check if report was generated
                json_reports = list(temp_path.glob("ci_report_*.json"))
                if not json_reports:
                    print("❌ No CI report generated during integration test")
                    return False

                # Validate report content
                with open(json_reports[0], "r", encoding="utf-8") as f:
                    report_data = json.load(f)

                if "overall_status" not in report_data:
                    print("❌ Invalid CI report format")
                    return False

                print(f"✅ Integration test passed (Status: {report_data['overall_status']})")
                return True

        except subprocess.TimeoutExpired:
            print("❌ Integration test timed out")
            return False
        except Exception as e:
            print(f"❌ Integration test error: {e}")
            return False

    def validate_all(self) -> bool:
        """全ての検証を実行"""
        print("=" * 60)
        print("CI Integration Validation")
        print("=" * 60)

        validations = [
            ("Project Structure", self.validate_project_structure),
            ("pyproject.toml Integration", self.validate_pyproject_integration),
            ("Makefile Integration", self.validate_makefile_integration),
            ("CI Simulator Functionality", self.validate_ci_simulator_functionality),
            ("Git Hook Integration", self.validate_git_hook_integration),
            ("Deployment Integration", self.validate_deployment_integration),
            ("GitHub Actions Integration", self.validate_github_actions_integration),
            ("Integration Test", self.run_integration_test)
        ]

        results = {}
        all_passed = True

        for name, validation_func in validations:
            print(f"\n{name}:")
            print("-" * 40)
            try:
                result = validation_func()
                results[name] = result
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ Validation error: {e}")
                results[name] = False
                all_passed = False

        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        for name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {name}")

        if all_passed:
            print("\n🎉 All CI integration validations passed!")
            print("The CI simulator is properly integrated with the project.")
        else:
            print("\n❌ Some validations failed.")
            print("Please fix the issues before proceeding with deployment.")

        return all_passed


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="CI統合検証スクリプト")
    parser.add_argument("--project-root", type=Path, help="プロジェクトルートパス")
    parser.add_argument("--json", action="store_true", help="JSON形式で結果を出力")

    args = parser.parse_args()

    project_root = args.project_root or Path(__file__).parent.parent
    validator = CIIntegrationValidator(project_root)

    success = validator.validate_all()

    if args.json:
        result = {
            "success": success,
            "timestamp": "2025-01-30T00:00:00Z",
            "project_root": str(project_root),
            "validation_results": validator.validation_results
        }
        print(json.dumps(result, indent=2))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
