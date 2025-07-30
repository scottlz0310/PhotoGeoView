#!/usr/bin/env python3
"""
CI Integration Setup Script

This script sets up the CI simulator integration with the existing project
structure and configures all necessary components.

AI貢献者:
- Kiro: CI統合セットアップシステム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月30日
"""

import sys
import subprocess
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional


class CIIntegrationSetup:
    """CI統合セットアップ"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def setup_directories(self) -> bool:
        """必要なディレクトリの作成"""
        print("Setting up required directories...")

        directories = [
            "reports/ci-simulation",
            "logs",
            ".kiro/ci-history",
            "temp/ci-simulation",
            "tools/ci/templates"
        ]

        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {directory}")

            return True

        except Exception as e:
            print(f"❌ Error creating directories: {e}")
            return False

    def setup_gitignore(self) -> bool:
        """gitignore設定の更新"""
        print("Updating .gitignore...")

        gitignore_path = self.project_root / ".gitignore"

        ci_ignore_entries = [
            "",
            "# CI Simulation files",
            "reports/ci-simulation/",
            "temp/ci-simulation/",
            ".kiro/ci-history/",
            "logs/ci-simulation.log",
            "logs/performance.log",
            "logs/security-scan.log",
            "",
            "# CI build artifacts",
            "build/ci-reports/",
            "dist/",
            "*.egg-info/",
            "",
            "# Coverage reports",
            "htmlcov/",
            ".coverage",
            "coverage.xml",
            "",
            "# Pytest cache",
            ".pytest_cache/",
            "",
            "# MyPy cache",
            ".mypy_cache/",
            "",
            "# Performance benchmarks",
            "benchmark.json",
            "performance_baseline.json"
        ]

        try:
            # Read existing .gitignore
            existing_content = ""
            if gitignore_path.exists():
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()

            # Check if CI entries already exist
            if "# CI Simulation files" in existing_content:
                print("✅ .gitignore already contains CI simulation entries")
                return True

            # Append CI entries
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n".join(ci_ignore_entries))

            print("✅ Updated .gitignore with CI simulation entries")
            return True

        except Exception as e:
            print(f"❌ Error updating .gitignore: {e}")
            return False

    def install_dependencies(self) -> bool:
        """依存関係のインストール"""
        print("Installing CI dependencies...")

        try:
            # Install project with CI dependencies
            result = subprocess.run([
                sys.executable,
                "-m", "pip", "install", "-e", ".[ci]"
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to install CI dependencies: {result.stderr}")
                return False

            print("✅ CI dependencies installed successfully")
            return True

        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False

    def setup_git_hooks(self) -> bool:
        """Git hooksのセットアップ"""
        print("Setting up Git hooks...")

        try:
            # Check if we're in a Git repository
            result = subprocess.run([
                "git", "rev-parse", "--git-dir"
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print("⚠️ Not in a Git repository, skipping Git hooks setup")
                return True

            # Install recommended hooks
            result = subprocess.run([
                sys.executable,
                "-m", "tools.ci.simulator",
                "hook", "setup"
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"⚠️ Git hooks setup failed: {result.stderr}")
                print("You can set up hooks manually later using: make setup-hooks")
                return True  # Don't fail the entire setup

            print("✅ Git hooks set up successfully")
            return True

        except Exception as e:
            print(f"⚠️ Error setting up Git hooks: {e}")
            return True  # Don't fail the entire setup

    def create_default_config(self) -> bool:
        """デフォルト設定ファイルの作成"""
        print("Creating default CI configuration...")

        config_dir = self.project_root / ".kiro" / "settings"
        config_dir.mkdir(parents=True, exist_ok=True)

        ci_config_path = config_dir / "ci_simulator.json"

        default_config = {
            "enabled": True,
            "default_python_versions": ["3.9", "3.10", "3.11"],
            "timeout": 1800,
            "parallel_jobs": 4,
            "fail_fast": False,
            "checks": {
                "code_quality": {
                    "enabled": True,
                    "auto_fix": False,
                    "tools": {
                        "black": {"enabled": True, "line_length": 88},
                        "isort": {"enabled": True, "profile": "black"},
                        "flake8": {"enabled": True, "max_line_length": 88},
                        "mypy": {"enabled": True, "strict": False}
                    }
                },
                "test_runner": {
                    "enabled": True,
                    "coverage_threshold": 80.0,
                    "test_types": ["unit", "integration", "ai_compatibility"]
                },
                "security_scanner": {
                    "enabled": True,
                    "fail_on_high": False,
                    "tools": {
                        "safety": {"enabled": True},
                        "bandit": {"enabled": True, "confidence": "medium"}
                    }
                },
                "performance_analyzer": {
                    "enabled": True,
                    "regression_threshold": 30.0,
                    "benchmark_iterations": 3
                },
                "ai_component_tester": {
                    "enabled": True,
                    "demo_tests": True,
                    "components": ["copilot", "cursor", "kiro"]
                }
            },
            "directories": {
                "reports": "reports/ci-simulation",
                "logs": "logs",
                "history": ".kiro/ci-history",
                "temp": "temp/ci-simulation"
            },
            "git_hooks": {
                "pre_commit": {
                    "enabled": True,
                    "checks": ["code_quality", "test_runner"]
                },
                "pre_push": {
                    "enabled": False,
                    "checks": ["all"]
                }
            },
            "notifications": {
                "slack_webhook": "",
                "email_recipients": [],
                "github_status": True
            },
            "ai_integration": {
                "quality_threshold": 70.0,
                "components": {
                    "copilot": {"focus": "core_functionality", "quality_weight": 1.2},
                    "cursor": {"focus": "ui_ux", "quality_weight": 1.0},
                    "kiro": {"focus": "integration", "quality_weight": 1.5}
                }
            }
        }

        try:
            if ci_config_path.exists():
                print("✅ CI configuration already exists")
                return True

            with open(ci_config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            print("✅ Default CI configuration created")
            return True

        except Exception as e:
            print(f"❌ Error creating CI configuration: {e}")
            return False

    def create_template_files(self) -> bool:
        """テンプレートファイルの作成"""
        print("Creating template files...")

        templates_dir = self.project_root / "tools" / "ci" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Pre-commit hook template
        pre_commit_template = '''#!/bin/sh
# PhotoGeoView CI Simulator Pre-commit Hook
# Generated by CI Integration Setup

echo "Running CI simulation pre-commit checks..."

# Run CI simulator with pre-commit checks
python -m tools.ci.simulator run --checks code_quality test_runner --fail-fast --quiet

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "❌ Pre-commit checks failed. Commit aborted."
    echo "Run 'make ci-quick' to see detailed results."
    echo "Use 'git commit --no-verify' to bypass checks (not recommended)."
    exit 1
fi

echo "✅ Pre-commit checks passed."
exit 0
'''

        # Report template
        report_template = '''# CI Simulation Report

**Generated:** {{timestamp}}
**Duration:** {{duration}} seconds
**Status:** {{status}}
**Python Versions:** {{python_versions}}

## Summary

{{summary}}

## Check Results

{{#check_results}}
### {{name}}

- **Status:** {{status}}
- **Duration:** {{duration}}s

{{#errors}}
**Errors:**
{{#errors}}
- {{.}}
{{/errors}}
{{/errors}}

{{#warnings}}
**Warnings:**
{{#warnings}}
- {{.}}
{{/warnings}}
{{/warnings}}

{{#suggestions}}
**Suggestions:**
{{#suggestions}}
- {{.}}
{{/suggestions}}
{{/suggestions}}

{{/check_results}}

## AI Integration Quality

{{#ai_quality}}
- **Overall Score:** {{overall_score}}/100
- **Copilot Components:** {{copilot_score}}/100
- **Cursor Components:** {{cursor_score}}/100
- **Kiro Components:** {{kiro_score}}/100
{{/ai_quality}}

---
*Generated by PhotoGeoView CI Simulator*
'''

        try:
            # Write pre-commit hook template
            pre_commit_path = templates_dir / "pre_commit_hook.sh"
            with open(pre_commit_path, "w", encoding="utf-8") as f:
                f.write(pre_commit_template)

            # Write report template
            report_template_path = templates_dir / "report_template.md"
            with open(report_template_path, "w", encoding="utf-8") as f:
                f.write(report_template)

            print("✅ Template files created")
            return True

        except Exception as e:
            print(f"❌ Error creating template files: {e}")
            return False

    def validate_setup(self) -> bool:
        """セットアップの検証"""
        print("Validating CI integration setup...")

        try:
            # Test CI simulator functionality
            result = subprocess.run([
                sys.executable,
                "-m", "tools.ci.simulator",
                "list"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                print(f"❌ CI simulator validation failed: {result.stderr}")
                return False

            print("✅ CI integration setup validation passed")
            return True

        except subprocess.TimeoutExpired:
            print("❌ CI simulator validation timed out")
            return False
        except Exception as e:
            print(f"❌ Setup validation error: {e}")
            return False

    def setup_all(self) -> bool:
        """全てのセットアップを実行"""
        print("=" * 60)
        print("PhotoGeoView CI Integration Setup")
        print("=" * 60)

        setup_steps = [
            ("Setting up directories", self.setup_directories),
            ("Updating .gitignore", self.setup_gitignore),
            ("Installing dependencies", self.install_dependencies),
            ("Creating default configuration", self.create_default_config),
            ("Creating template files", self.create_template_files),
            ("Setting up Git hooks", self.setup_git_hooks),
            ("Validating setup", self.validate_setup)
        ]

        all_successful = True

        for step_name, step_func in setup_steps:
            print(f"\n{step_name}:")
            print("-" * 40)
            try:
                success = step_func()
                if not success:
                    all_successful = False
                    print(f"❌ {step_name} failed")
            except Exception as e:
                print(f"❌ {step_name} error: {e}")
                all_successful = False

        # Print summary
        print("\n" + "=" * 60)
        print("SETUP SUMMARY")
        print("=" * 60)

        if all_successful:
            print("🎉 CI integration setup completed successfully!")
            print("\nNext steps:")
            print("1. Run 'make ci' to test the integration")
            print("2. Run 'make validate-ci-integration' to validate")
            print("3. Commit your changes to activate Git hooks")
            print("\nUseful commands:")
            print("- make ci-quick    # Quick CI checks")
            print("- make ci-full     # Comprehensive CI checks")
            print("- make setup-hooks # Setup Git hooks manually")
        else:
            print("❌ Some setup steps failed.")
            print("Please review the errors above and fix them manually.")

        return all_successful


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="CI統合セットアップスクリプト")
    parser.add_argument("--project-root", type=Path, help="プロジェクトルートパス")
    parser.add_argument("--skip-hooks", action="store_true", help="Git hooksセットアップをスキップ")
    parser.add_argument("--skip-deps", action="store_true", help="依存関係インストールをスキップ")

    args = parser.parse_args()

    project_root = args.project_root or Path(__file__).parent.parent
    setup = CIIntegrationSetup(project_root)

    # Skip certain steps if requested
    if args.skip_hooks:
        setup.setup_git_hooks = lambda: True
    if args.skip_deps:
        setup.install_dependencies = lambda: True

    success = setup.setup_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
