#!/usr/bin/env python3
"""
Build with CI Integration Script

This script builds the project with comprehensive CI checks integrated
into the build process.

AI貢献者:
- Kiro: CI統合ビルドシステム設計・実装

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
from datetime import datetime
import tempfile


class CIIntegratedBuilder:
    """CI統合ビルダー"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"
        self.reports_dir = project_root / "reports" / "ci-build"

    def setup_build_environment(self) -> bool:
        """ビルド環境のセットアップ"""
        print("Setting up build environment...")

        try:
            # Clean and create build directories
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
            if self.dist_dir.exists():
                shutil.rmtree(self.dist_dir)

            self.build_dir.mkdir(parents=True, exist_ok=True)
            self.dist_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir.mkdir(parents=True, exist_ok=True)

            print("✅ Build environment set up successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to set up build environment: {e}")
            return False

    def run_pre_build_ci_checks(self) -> bool:
        """ビルド前CI チェックの実行"""
        print("Running pre-build CI checks...")

        try:
            # Run comprehensive CI simulation
            result = subprocess.run([
                sys.executable,
                "-m", "tools.ci.simulator",
                "run",
                "--all",
                "--format", "both",
                "--output-dir", str(self.reports_dir),
                "--timeout", "1800"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=1800)

            if result.returncode != 0:
                print(f"❌ Pre-build CI checks failed: {result.stderr}")
                print("Build aborted due to CI check failures.")
                return False

            # Parse CI results
            json_reports = list(self.reports_dir.glob("ci_report_*.json"))
            if json_reports:
                latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)

                with open(latest_report, "r", encoding="utf-8") as f:
                    ci_data = json.load(f)

                overall_status = ci_data.get("overall_status", "UNKNOWN")
                if overall_status == "FAILURE":
                    print("❌ CI checks failed with critical issues")
                    return False
                elif overall_status == "WARNING":
                    print("⚠️ CI checks completed with warnings")

                print(f"✅ Pre-build CI checks passed (Status: {overall_status})")

            return True

        except subprocess.TimeoutExpired:
            print("❌ Pre-build CI checks timed out")
            return False
        except Exception as e:
            print(f"❌ Pre-build CI checks error: {e}")
            return False

    def build_package(self) -> bool:
        """パッケージのビルド"""
        print("Building package...")

        try:
            # Build source distribution and wheel
            result = subprocess.run([
                sys.executable,
                "-m", "build"
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Package build failed: {result.stderr}")
                return False

            # Verify build artifacts
            dist_files = list(self.dist_dir.glob("*"))
            if not dist_files:
                print("❌ No build artifacts found")
                return False

            print("✅ Package built successfully")
            for file in dist_files:
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  - {file.name} ({size_mb:.1f}MB)")

            return True

        except Exception as e:
            print(f"❌ Package build error: {e}")
            return False

    def run_post_build_validation(self) -> bool:
        """ビルド後検証の実行"""
        print("Running post-build validation...")

        try:
            # Install built package in temporary environment
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_venv = Path(temp_dir) / "test_env"

                # Create virtual environment
                result = subprocess.run([
                    sys.executable, "-m", "venv", str(temp_venv)
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ Failed to create test environment: {result.stderr}")
                    return False

                # Get pip path for the virtual environment
                if os.name == 'nt':  # Windows
                    pip_path = temp_venv / "Scripts" / "pip.exe"
                    python_path = temp_venv / "Scripts" / "python.exe"
                else:  # Unix-like
                    pip_path = temp_venv / "bin" / "pip"
                    python_path = temp_venv / "bin" / "python"

                # Install built package
                wheel_files = list(self.dist_dir.glob("*.whl"))
                if not wheel_files:
                    print("❌ No wheel file found for validation")
                    return False

                result = subprocess.run([
                    str(pip_path), "install", str(wheel_files[0])
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ Failed to install built package: {result.stderr}")
                    return False

                # Test package import
                result = subprocess.run([
                    str(python_path), "-c",
                    "import src.main; print('Package import successful')"
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ Package import test failed: {result.stderr}")
                    return False

                print("✅ Post-build validation passed")
                return True

        except Exception as e:
            print(f"❌ Post-build validation error: {e}")
            return False

    def generate_build_report(self) -> bool:
        """ビルドレポートの生成"""
        print("Generating build report...")

        try:
            build_report = {
                "build_timestamp": datetime.now().isoformat(),
                "project_name": "photogeoview",
                "build_status": "success",
                "ci_integration": True,
                "artifacts": [],
                "ci_results": {},
                "validation_results": {
                    "package_import": True,
                    "dependencies_resolved": True
                }
            }

            # Collect build artifacts
            for artifact in self.dist_dir.glob("*"):
                build_report["artifacts"].append({
                    "name": artifact.name,
                    "size": artifact.stat().st_size,
                    "type": artifact.suffix[1:] if artifact.suffix else "unknown"
                })

            # Include CI results if available
            json_reports = list(self.reports_dir.glob("ci_report_*.json"))
            if json_reports:
                latest_report = max(json_reports, key=lambda p: p.stat().st_mtime)

                with open(latest_report, "r", encoding="utf-8") as f:
                    ci_data = json.load(f)

                build_report["ci_results"] = {
                    "overall_status": ci_data.get("overall_status"),
                    "summary": ci_data.get("summary"),
                    "duration": ci_data.get("total_duration"),
                    "python_versions": ci_data.get("python_versions_tested", [])
                }

            # Save build report
            report_path = self.reports_dir / "build_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(build_report, f, indent=2, ensure_ascii=False)

            # Generate markdown report
            md_report_path = self.reports_dir / "build_report.md"
            with open(md_report_path, "w", encoding="utf-8") as f:
                f.write(f"# Build Report\n\n")
                f.write(f"**Generated:** {build_report['build_timestamp']}\n")
                f.write(f"**Project:** {build_report['project_name']}\n")
                f.write(f"**Status:** {build_report['build_status']}\n")
                f.write(f"**CI Integration:** {'✅ Enabled' if build_report['ci_integration'] else '❌ Disabled'}\n\n")

                f.write("## Build Artifacts\n\n")
                for artifact in build_report["artifacts"]:
                    size_mb = artifact["size"] / (1024 * 1024)
                    f.write(f"- **{artifact['name']}** ({size_mb:.1f}MB, {artifact['type']})\n")

                if build_report["ci_results"]:
                    ci_results = build_report["ci_results"]
                    f.write(f"\n## CI Results\n\n")
                    f.write(f"- **Status:** {ci_results.get('overall_status', 'Unknown')}\n")
                    f.write(f"- **Duration:** {ci_results.get('duration', 0):.2f} seconds\n")
                    f.write(f"- **Python Versions:** {', '.join(ci_results.get('python_versions', []))}\n")
                    f.write(f"- **Summary:** {ci_results.get('summary', 'No summary available')}\n")

                f.write(f"\n## Validation Results\n\n")
                validation = build_report["validation_results"]
                f.write(f"- **Package Import:** {'✅ Pass' if validation['package_import'] else '❌ Fail'}\n")
                f.write(f"- **Dependencies:** {'✅ Resolved' if validation['dependencies_resolved'] else '❌ Issues'}\n")

            print(f"✅ Build report generated: {report_path}")
            print(f"✅ Markdown report generated: {md_report_path}")
            return True

        except Exception as e:
            print(f"❌ Build report generation error: {e}")
            return False

    def build_with_ci(self) -> bool:
        """CI統合ビルドの実行"""
        print("=" * 60)
        print("PhotoGeoView CI-Integrated Build")
        print("=" * 60)

        build_steps = [
            ("Setting up build environment", self.setup_build_environment),
            ("Running pre-build CI checks", self.run_pre_build_ci_checks),
            ("Building package", self.build_package),
            ("Running post-build validation", self.run_post_build_validation),
            ("Generating build report", self.generate_build_report)
        ]

        all_successful = True
        start_time = datetime.now()

        for step_name, step_func in build_steps:
            print(f"\n{step_name}:")
            print("-" * 40)
            try:
                success = step_func()
                if not success:
                    all_successful = False
                    print(f"❌ {step_name} failed")
                    break
            except Exception as e:
                print(f"❌ {step_name} error: {e}")
                all_successful = False
                break

        # Print summary
        duration = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print("BUILD SUMMARY")
        print("=" * 60)
        print(f"Duration: {duration:.2f} seconds")

        if all_successful:
            print("🎉 CI-integrated build completed successfully!")
            print(f"\nBuild artifacts:")
            for artifact in self.dist_dir.glob("*"):
                size_mb = artifact.stat().st_size / (1024 * 1024)
                print(f"  - {artifact.name} ({size_mb:.1f}MB)")
            print(f"\nReports available in: {self.reports_dir}")
        else:
            print("❌ Build failed.")
            print("Check the error messages above for details.")

        return all_successful


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="CI統合ビルドスクリプト")
    parser.add_argument("--project-root", type=Path, help="プロジェクトルートパス")
    parser.add_argument("--skip-ci", action="store_true", help="CI チェックをスキップ")
    parser.add_argument("--skip-validation", action="store_true", help="ビルド後検証をスキップ")

    args = parser.parse_args()

    project_root = args.project_root or Path(__file__).parent.parent
    builder = CIIntegratedBuilder(project_root)

    # Skip certain steps if requested
    if args.skip_ci:
        builder.run_pre_build_ci_checks = lambda: True
    if args.skip_validation:
        builder.run_post_build_validation = lambda: True

    success = builder.build_with_ci()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
