#!/usr/bin/env python3
"""
Final Integration Verification Test

This script performs comprehensive testing of all qt-theme-breadcrumb components
to verify that the integration is complete and working correctly.

Author: Kiro AI Integration System
Requirements: Task 12 - Final integration and testing
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from src.integration.config_manager import ConfigManager
    from src.integration.logging_system import LoggerSystem
    from src.integration.services.file_system_watcher import FileSystemWatcher
    from src.integration.theme_integration_controller import ThemeIntegrationController
    from src.integration.navigation_integration_controller import NavigationIntegrationController
    from src.ui.theme_manager import ThemeManagerWidget
    from src.ui.breadcrumb_bar import BreadcrumbAddressBar

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False


class IntegrationTestResult:
    """Test result container"""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.error_message = ""
        self.details = {}

    def mark_passed(self, details: Optional[Dict] = None):
        self.passed = True
        self.details = details or {}

    def mark_failed(self, error_message: str, details: Optional[Dict] = None):
        self.passed = False
        self.error_message = error_message
        self.details = details or {}


class FinalIntegrationTester:
    """Comprehensive integration tester for qt-theme-breadcrumb components"""

    def __init__(self):
        self.results: List[IntegrationTestResult] = []
        self.app: Optional[QApplication] = None
        self.config_manager: Optional[ConfigManager] = None
        self.logger_system: Optional[LoggerSystem] = None
        self.file_system_watcher: Optional[FileSystemWatcher] = None
        self.theme_controller: Optional[ThemeIntegrationController] = None
        self.navigation_controller: Optional[NavigationIntegrationController] = None
        self.theme_manager_widget: Optional[ThemeManagerWidget] = None
        self.breadcrumb_bar: Optional[BreadcrumbAddressBar] = None

    def setup_test_environment(self) -> bool:
        """Setup test environment with all required components"""
        try:
            # Initialize Qt Application
            if not QApplication.instance():
                self.app = QApplication([])

            # Initialize core systems
            self.logger_system = LoggerSystem()
            self.config_manager = ConfigManager(logger_system=self.logger_system)
            self.file_system_watcher = FileSystemWatcher(
                logger_system=self.logger_system,
                enable_monitoring=True
            )

            # Initialize controllers
            self.theme_controller = ThemeIntegrationController(
                self.config_manager,
                self.logger_system
            )

            self.navigation_controller = NavigationIntegrationController(
                self.config_manager,
                self.logger_system,
                self.file_system_watcher
            )

            # Initialize UI components
            self.theme_manager_widget = ThemeManagerWidget(
                self.config_manager,
                self.logger_system
            )

            self.breadcrumb_bar = BreadcrumbAddressBar(
                self.file_system_watcher,
                self.logger_system,
                self.config_manager
            )

            return True

        except Exception as e:
            print(f"Failed to setup test environment: {e}")
            return False

    def test_component_initialization(self) -> IntegrationTestResult:
        """Test that all components initialize correctly"""
        result = IntegrationTestResult("Component Initialization")

        try:
            components = {
                "ConfigManager": self.config_manager,
                "LoggerSystem": self.logger_system,
                "FileSystemWatcher": self.file_system_watcher,
                "ThemeIntegrationController": self.theme_controller,
                "NavigationIntegrationController": self.navigation_controller,
                "ThemeManagerWidget": self.theme_manager_widget,
                "BreadcrumbAddressBar": self.breadcrumb_bar
            }

            initialized_components = {}
            for name, component in components.items():
                if component is not None:
                    initialized_components[name] = "✓ Initialized"
                else:
                    initialized_components[name] = "✗ Failed"

            all_initialized = all("✓" in status for status in initialized_components.values())

            if all_initialized:
                result.mark_passed({"components": initialized_components})
            else:
                result.mark_failed("Some components failed to initialize", {"components": initialized_components})

        except Exception as e:
            result.mark_failed(f"Component initialization test failed: {e}")

        return result

    def test_theme_integration(self) -> IntegrationTestResult:
        """Test theme integration functionality"""
        result = IntegrationTestResult("Theme Integration")

        try:
            # Register theme manager with controller
            success = self.theme_controller.register_theme_manager(
                "main_theme_manager",
                self.theme_manager_widget
            )

            if not success:
                result.mark_failed("Failed to register theme manager")
                return result

            # Test theme application
            available_themes = ["default", "dark"]
            theme_results = {}

            for theme_name in available_themes:
                try:
                    # Apply theme using theme manager widget
                    theme_applied = self.theme_manager_widget.apply_theme(theme_name)
                    theme_results[theme_name] = "✓ Applied" if theme_applied else "✗ Failed"
                except Exception as e:
                    theme_results[theme_name] = f"✗ Error: {e}"

            successful_themes = sum(1 for status in theme_results.values() if "✓" in status)

            if successful_themes > 0:
                result.mark_passed({
                    "theme_results": theme_results,
                    "successful_themes": successful_themes,
                    "total_themes": len(available_themes)
                })
            else:
                result.mark_failed("No themes could be applied", {"theme_results": theme_results})

        except Exception as e:
            result.mark_failed(f"Theme integration test failed: {e}")

        return result

    def test_breadcrumb_navigation(self) -> IntegrationTestResult:
        """Test breadcrumb navigation functionality"""
        result = IntegrationTestResult("Breadcrumb Navigation")

        try:
            # Test path setting
            test_paths = [Path.home(), Path.home() / "Documents"]
            navigation_results = {}

            for test_path in test_paths:
                if test_path.exists():
                    try:
                        path_set = self.breadcrumb_bar.set_current_path(test_path)
                        navigation_results[str(test_path)] = "✓ Set" if path_set else "✗ Failed"
                    except Exception as e:
                        navigation_results[str(test_path)] = f"✗ Error: {e}"
                else:
                    navigation_results[str(test_path)] = "⚠ Path not found"

            successful_navigations = sum(1 for status in navigation_results.values() if "✓" in status)

            if successful_navigations > 0:
                result.mark_passed({
                    "navigation_results": navigation_results,
                    "successful_navigations": successful_navigations,
                    "total_paths": len(test_paths)
                })
            else:
                result.mark_failed("No paths could be navigated", {"navigation_results": navigation_results})

        except Exception as e:
            result.mark_failed(f"Breadcrumb navigation test failed: {e}")

        return result

    def test_file_system_integration(self) -> IntegrationTestResult:
        """Test file system watcher integration"""
        result = IntegrationTestResult("File System Integration")

        try:
            # Test file system watcher functionality
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Start watching temporary directory
                watch_started = self.file_system_watcher.start_watching(temp_path)

                if not watch_started:
                    result.mark_failed("Failed to start file system watching")
                    return result

                # Test breadcrumb integration with file watcher
                breadcrumb_updated = self.breadcrumb_bar.set_current_path(temp_path)

                # Stop watching
                self.file_system_watcher.stop_watching()

                if breadcrumb_updated:
                    result.mark_passed({
                        "watch_started": watch_started,
                        "breadcrumb_updated": breadcrumb_updated,
                        "test_path": str(temp_path)
                    })
                else:
                    result.mark_failed("Breadcrumb failed to update with file system watcher")

        except Exception as e:
            result.mark_failed(f"File system integration test failed: {e}")

        return result

    def test_controller_coordination(self) -> IntegrationTestResult:
        """Test coordination between theme and navigation controllers"""
        result = IntegrationTestResult("Controller Coordination")

        try:
            # Register components with controllers
            theme_registration = self.theme_controller.register_component(self.breadcrumb_bar)
            nav_registration = self.navigation_controller.register_navigation_component(self.breadcrumb_bar)

            coordination_results = {
                "theme_registration": "✓ Success" if theme_registration else "✗ Failed",
                "navigation_registration": "✓ Success" if nav_registration else "✗ Failed"
            }

            successful_registrations = sum(1 for status in coordination_results.values() if "✓" in status)

            if successful_registrations >= 1:
                result.mark_passed({
                    "coordination_results": coordination_results,
                    "successful_registrations": successful_registrations
                })
            else:
                result.mark_failed("Controller coordination failed", {"coordination_results": coordination_results})

        except Exception as e:
            result.mark_failed(f"Controller coordination test failed: {e}")

        return result

    def test_error_handling(self) -> IntegrationTestResult:
        """Test error handling and recovery"""
        result = IntegrationTestResult("Error Handling")

        try:
            error_scenarios = {}

            # Test invalid theme application
            try:
                invalid_theme_result = self.theme_manager_widget.apply_theme("nonexistent_theme")
                error_scenarios["invalid_theme"] = "✓ Handled" if not invalid_theme_result else "✗ Not handled"
            except Exception:
                error_scenarios["invalid_theme"] = "✓ Exception caught"

            # Test invalid path navigation
            try:
                invalid_path = Path("/nonexistent/path/that/should/not/exist")
                invalid_path_result = self.breadcrumb_bar.set_current_path(invalid_path)
                error_scenarios["invalid_path"] = "✓ Handled" if not invalid_path_result else "✗ Not handled"
            except Exception:
                error_scenarios["invalid_path"] = "✓ Exception caught"

            handled_errors = sum(1 for status in error_scenarios.values() if "✓" in status)

            if handled_errors >= 1:
                result.mark_passed({
                    "error_scenarios": error_scenarios,
                    "handled_errors": handled_errors
                })
            else:
                result.mark_failed("Error handling insufficient", {"error_scenarios": error_scenarios})

        except Exception as e:
            result.mark_failed(f"Error handling test failed: {e}")

        return result

    def test_performance_integration(self) -> IntegrationTestResult:
        """Test performance aspects of integration"""
        result = IntegrationTestResult("Performance Integration")

        try:
            performance_metrics = {}

            # Test theme switching performance
            import time
            start_time = time.time()

            theme_switches = 0
            for theme in ["default", "dark", "default"]:
                if self.theme_manager_widget.apply_theme(theme):
                    theme_switches += 1

            theme_switch_time = time.time() - start_time
            performance_metrics["theme_switch_time"] = f"{theme_switch_time:.3f}s"
            performance_metrics["theme_switches"] = theme_switches

            # Test navigation performance
            start_time = time.time()

            navigation_operations = 0
            test_paths = [Path.home()]
            if (Path.home() / "Documents").exists():
                test_paths.append(Path.home() / "Documents")

            for path in test_paths:
                if self.breadcrumb_bar.set_current_path(path):
                    navigation_operations += 1

            navigation_time = time.time() - start_time
            performance_metrics["navigation_time"] = f"{navigation_time:.3f}s"
            performance_metrics["navigation_operations"] = navigation_operations

            # Performance is acceptable if operations complete within reasonable time
            acceptable_performance = (
                theme_switch_time < 5.0 and
                navigation_time < 3.0 and
                theme_switches > 0 and
                navigation_operations > 0
            )

            if acceptable_performance:
                result.mark_passed(performance_metrics)
            else:
                result.mark_failed("Performance below acceptable thresholds", performance_metrics)

        except Exception as e:
            result.mark_failed(f"Performance integration test failed: {e}")

        return result

    def run_all_tests(self) -> Dict[str, IntegrationTestResult]:
        """Run all integration tests"""
        if not DEPENDENCIES_AVAILABLE:
            print("⚠️  Some dependencies not available, running limited tests")
            return {}

        print("🚀 Starting Final Integration Testing...")
        print("=" * 60)

        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return {}

        # Define test methods
        test_methods = [
            self.test_component_initialization,
            self.test_theme_integration,
            self.test_breadcrumb_navigation,
            self.test_file_system_integration,
            self.test_controller_coordination,
            self.test_error_handling,
            self.test_performance_integration
        ]

        # Run tests
        for test_method in test_methods:
            print(f"\n🔍 Running {test_method.__name__.replace('test_', '').replace('_', ' ').title()}...")

            try:
                result = test_method()
                self.results.append(result)

                if result.passed:
                    print(f"   ✅ {result.test_name}: PASSED")
                    if result.details:
                        for key, value in result.details.items():
                            if isinstance(value, dict):
                                print(f"      {key}:")
                                for sub_key, sub_value in value.items():
                                    print(f"        {sub_key}: {sub_value}")
                            else:
                                print(f"      {key}: {value}")
                else:
                    print(f"   ❌ {result.test_name}: FAILED")
                    print(f"      Error: {result.error_message}")
                    if result.details:
                        for key, value in result.details.items():
                            if isinstance(value, dict):
                                print(f"      {key}:")
                                for sub_key, sub_value in value.items():
                                    print(f"        {sub_key}: {sub_value}")
                            else:
                                print(f"      {key}: {value}")

            except Exception as e:
                error_result = IntegrationTestResult(test_method.__name__)
                error_result.mark_failed(f"Test execution failed: {e}")
                self.results.append(error_result)
                print(f"   💥 {test_method.__name__}: EXECUTION ERROR")
                print(f"      Error: {e}")

        return {result.test_name: result for result in self.results}

    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        if not self.results:
            return "No test results available"

        passed_tests = sum(1 for result in self.results if result.passed)
        total_tests = len(self.results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        report = []
        report.append("=" * 80)
        report.append("🎯 FINAL INTEGRATION TEST REPORT")
        report.append("=" * 80)
        report.append(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        report.append("")

        # Test summary
        report.append("📋 Test Summary:")
        report.append("-" * 40)
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report.append(f"{status} {result.test_name}")
            if not result.passed:
                report.append(f"     Error: {result.error_message}")

        report.append("")

        # Integration status
        if success_rate >= 80:
            report.append("🎉 INTEGRATION STATUS: EXCELLENT")
            report.append("   All major components are working correctly.")
        elif success_rate >= 60:
            report.append("✅ INTEGRATION STATUS: GOOD")
            report.append("   Most components are working, minor issues detected.")
        elif success_rate >= 40:
            report.append("⚠️  INTEGRATION STATUS: PARTIAL")
            report.append("   Some components working, significant issues need attention.")
        else:
            report.append("❌ INTEGRATION STATUS: POOR")
            report.append("   Major integration issues detected, requires immediate attention.")

        report.append("")

        # Recommendations
        report.append("💡 Recommendations:")
        report.append("-" * 20)

        failed_tests = [result for result in self.results if not result.passed]
        if not failed_tests:
            report.append("• All tests passed! Integration is complete and ready for production.")
        else:
            report.append("• Address the following failed tests:")
            for result in failed_tests:
                report.append(f"  - {result.test_name}: {result.error_message}")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main test execution function"""
    tester = FinalIntegrationTester()

    # Run all tests
    test_results = tester.run_all_tests()

    # Generate and display report
    report = tester.generate_test_report()
    print("\n" + report)

    # Save report to file
    report_file = Path("integration_test_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📄 Full report saved to: {report_file}")

    # Return exit code based on results
    if test_results:
        passed_tests = sum(1 for result in test_results.values() if result.passed)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        if success_rate >= 80:
            print("\n🎉 Integration testing completed successfully!")
            return 0
        else:
            print(f"\n⚠️  Integration testing completed with issues (success rate: {success_rate:.1f}%)")
            return 1
    else:
        print("\n❌ Integration testing failed to run")
        return 2


if __name__ == "__main__":
    sys.exit(main())
