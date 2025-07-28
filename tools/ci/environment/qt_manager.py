"""
Qt Dependencies and Virtual Display Management Module

This module provides functionality to detect Qt dependencies and manage virtual displays
for headless testing in CI/CD environments.

Author: Kiro (AI Integration and Quality Assurance)
"""

import os
import subprocess
import sys
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import time

try:
    from ..models import CheckResult, CheckStatus
    from ..utils import run_command
except ImportError:
    # Fallback for direct execution
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from models import CheckResult, CheckStatus
    from utils import run_command


# Create a wrapper for timeout functionality
def run_command_with_timeout(command, timeout=30, env=None):
    """Wrapper to provide timeout functionality."""
    import subprocess

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, env=env
        )
        return result
    except subprocess.TimeoutExpired:
        # Create a mock result for timeout
        class MockResult:
            def __init__(self):
                self.returncode = -1
                self.stdout = ""
                self.stderr = f"Command timed out after {timeout} seconds"

        return MockResult()


logger = logging.getLogger(__name__)


class QtDependencyInfo:
    """Information about Qt dependency availability."""

    def __init__(
        self, name: str, is_available: bool, version: str = "", path: str = ""
    ):
        self.name = name
        self.is_available = is_available
        self.version = version
        self.path = path
        self.installation_suggestions: List[str] = []

    def __str__(self) -> str:
        status = "available" if self.is_available else "missing"
        version_str = f" (v{self.version})" if self.version else ""
        return f"{self.name}: {status}{version_str}"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "is_available": self.is_available,
            "version": self.version,
            "path": self.path,
            "installation_suggestions": self.installation_suggestions,
        }


class QtManager:
    """Manages Qt dependencies detection and validation."""

    REQUIRED_QT_PACKAGES = ["PyQt5", "PyQt6", "PySide2", "PySide6"]

    SYSTEM_QT_LIBRARIES = [
        "libqt5core5a",  # Ubuntu/Debian Qt5
        "libqt6core6",  # Ubuntu/Debian Qt6
        "qt5-qtbase",  # CentOS/RHEL Qt5
        "qt6-qtbase",  # CentOS/RHEL Qt6
    ]

    def __init__(self):
        self.qt_packages: Dict[str, QtDependencyInfo] = {}
        self.system_libraries: Dict[str, QtDependencyInfo] = {}
        self.platform = platform.system().lower()

    def detect_qt_dependencies(self) -> Dict[str, QtDependencyInfo]:
        """
        Detect available Qt dependencies.

        Returns:
            Dict mapping package names to QtDependencyInfo objects
        """
        logger.info("Detecting Qt dependencies...")

        # Clear previous detections
        self.qt_packages.clear()
        self.system_libraries.clear()

        # Detect Python Qt packages
        self._detect_python_qt_packages()

        # Detect system Qt libraries
        self._detect_system_qt_libraries()

        logger.info(f"Detected {len(self.qt_packages)} Python Qt packages")
        for name, info in self.qt_packages.items():
            logger.info(f"  {info}")

        return self.qt_packages

    def _detect_python_qt_packages(self) -> None:
        """Detect Python Qt packages (PyQt5, PyQt6, PySide2, PySide6)."""
        for package in self.REQUIRED_QT_PACKAGES:
            try:
                # Try to import the package
                result = run_command_with_timeout(
                    [
                        sys.executable,
                        "-c",
                        f"import {package}; print({package}.__version__)",
                    ],
                    timeout=10,
                )

                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.qt_packages[package] = QtDependencyInfo(
                        name=package, is_available=True, version=version
                    )
                    logger.debug(f"Found {package} version {version}")
                else:
                    # Package not available
                    info = QtDependencyInfo(name=package, is_available=False)
                    info.installation_suggestions = (
                        self._get_package_installation_suggestions(package)
                    )
                    self.qt_packages[package] = info
                    logger.debug(f"{package} not available")

            except Exception as e:
                logger.debug(f"Error detecting {package}: {e}")
                info = QtDependencyInfo(name=package, is_available=False)
                info.installation_suggestions = (
                    self._get_package_installation_suggestions(package)
                )
                self.qt_packages[package] = info

    def _detect_system_qt_libraries(self) -> None:
        """Detect system Qt libraries."""
        if self.platform == "linux":
            self._detect_linux_qt_libraries()
        elif self.platform == "darwin":
            self._detect_macos_qt_libraries()
        elif self.platform == "windows":
            self._detect_windows_qt_libraries()

    def _detect_linux_qt_libraries(self) -> None:
        """Detect Qt libraries on Linux systems."""
        # Check using pkg-config
        qt_modules = ["Qt5Core", "Qt5Widgets", "Qt6Core", "Qt6Widgets"]

        for module in qt_modules:
            try:
                result = run_command_with_timeout(
                    ["pkg-config", "--modversion", module], timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.system_libraries[module] = QtDependencyInfo(
                        name=module, is_available=True, version=version
                    )
                    logger.debug(f"Found system {module} version {version}")
                else:
                    info = QtDependencyInfo(name=module, is_available=False)
                    info.installation_suggestions = (
                        self._get_system_qt_installation_suggestions()
                    )
                    self.system_libraries[module] = info

            except Exception as e:
                logger.debug(f"Error checking {module}: {e}")

        # Also check for common library files
        common_paths = [
            "/usr/lib/x86_64-linux-gnu",
            "/usr/lib64",
            "/usr/lib",
            "/lib/x86_64-linux-gnu",
            "/lib64",
            "/lib",
        ]

        qt_libs = ["libQt5Core.so", "libQt6Core.so"]
        for lib in qt_libs:
            found = False
            for path in common_paths:
                lib_path = Path(path) / lib
                if lib_path.exists():
                    qt_version = "5" if "5" in lib else "6"
                    lib_name = f"Qt{qt_version}Core"
                    if lib_name not in self.system_libraries:
                        self.system_libraries[lib_name] = QtDependencyInfo(
                            name=lib_name, is_available=True, path=str(lib_path)
                        )
                    found = True
                    break

            if not found:
                qt_version = "5" if "5" in lib else "6"
                lib_name = f"Qt{qt_version}Core"
                if lib_name not in self.system_libraries:
                    info = QtDependencyInfo(name=lib_name, is_available=False)
                    info.installation_suggestions = (
                        self._get_system_qt_installation_suggestions()
                    )
                    self.system_libraries[lib_name] = info

    def _detect_macos_qt_libraries(self) -> None:
        """Detect Qt libraries on macOS systems."""
        # Check Homebrew installations
        try:
            result = run_command_with_timeout(["brew", "list", "qt@5"], timeout=10)
            if result.returncode == 0:
                self.system_libraries["Qt5"] = QtDependencyInfo(
                    name="Qt5", is_available=True, path="/usr/local/opt/qt@5"
                )
        except:
            pass

        try:
            result = run_command_with_timeout(["brew", "list", "qt@6"], timeout=10)
            if result.returncode == 0:
                self.system_libraries["Qt6"] = QtDependencyInfo(
                    name="Qt6", is_available=True, path="/usr/local/opt/qt@6"
                )
        except:
            pass

    def _detect_windows_qt_libraries(self) -> None:
        """Detect Qt libraries on Windows systems."""
        # Check common Qt installation paths
        common_paths = [
            "C:\\Qt",
            "C:\\Program Files\\Qt",
            "C:\\Program Files (x86)\\Qt",
        ]

        for base_path in common_paths:
            if os.path.exists(base_path):
                for item in os.listdir(base_path):
                    if item.startswith("5.") or item.startswith("6."):
                        qt_version = "5" if item.startswith("5.") else "6"
                        self.system_libraries[f"Qt{qt_version}"] = QtDependencyInfo(
                            name=f"Qt{qt_version}",
                            is_available=True,
                            version=item,
                            path=os.path.join(base_path, item),
                        )

    def _get_package_installation_suggestions(self, package: str) -> List[str]:
        """Get installation suggestions for Python Qt packages."""
        suggestions = [
            f"pip install {package}",
            f"conda install {package}",
        ]

        if package in ["PyQt5", "PyQt6"]:
            suggestions.append(f"pip install {package} {package}-tools")

        return suggestions

    def _get_system_qt_installation_suggestions(self) -> List[str]:
        """Get installation suggestions for system Qt libraries."""
        if self.platform == "linux":
            return [
                "Ubuntu/Debian: sudo apt-get install qt5-default libqt5widgets5-dev",
                "Ubuntu/Debian (Qt6): sudo apt-get install qt6-base-dev",
                "CentOS/RHEL: sudo yum install qt5-qtbase-devel",
                "CentOS/RHEL (Qt6): sudo yum install qt6-qtbase-devel",
            ]
        elif self.platform == "darwin":
            return ["Homebrew: brew install qt@5", "Homebrew (Qt6): brew install qt@6"]
        elif self.platform == "windows":
            return [
                "Download Qt installer from https://www.qt.io/download",
                "Use vcpkg: vcpkg install qt5-base",
                "Use Chocolatey: choco install qt-opensource",
            ]
        else:
            return ["Install Qt development libraries for your platform"]

    def check_qt_availability(self) -> CheckResult:
        """
        Check Qt availability for testing.

        Returns:
            CheckResult with Qt availability status
        """
        if not self.qt_packages:
            self.detect_qt_dependencies()

        available_packages = [
            name for name, info in self.qt_packages.items() if info.is_available
        ]
        missing_packages = [
            name for name, info in self.qt_packages.items() if not info.is_available
        ]

        errors = []
        warnings = []
        suggestions = []

        if not available_packages:
            errors.append("No Qt packages available for testing")
            suggestions.extend(
                [
                    "Install at least one Qt package:",
                    "  pip install PyQt5  # Most common choice",
                    "  pip install PyQt6  # Latest version",
                    "  pip install PySide2  # Official Qt binding",
                    "  pip install PySide6  # Latest official binding",
                ]
            )
        elif len(available_packages) < 2:
            warnings.append(f"Only {len(available_packages)} Qt package(s) available")
            suggestions.append(
                "Consider installing additional Qt packages for better compatibility testing"
            )

        # Add specific installation suggestions for missing packages
        for package in missing_packages:
            if package in self.qt_packages:
                suggestions.extend(self.qt_packages[package].installation_suggestions)

        status = CheckStatus.SUCCESS if available_packages else CheckStatus.FAILURE
        if available_packages and missing_packages:
            status = CheckStatus.WARNING

        return CheckResult(
            name="qt_availability",
            status=status,
            duration=0.0,
            output=f"Available Qt packages: {', '.join(available_packages)}",
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata={
                "available_packages": available_packages,
                "missing_packages": missing_packages,
                "qt_packages": {
                    name: info.to_dict() for name, info in self.qt_packages.items()
                },
                "system_libraries": {
                    name: info.to_dict() for name, info in self.system_libraries.items()
                },
            },
        )

    def get_qt_environment_variables(self) -> Dict[str, str]:
        """Get Qt-related environment variables for testing."""
        env_vars = {}

        # Set QT_QPA_PLATFORM for headless testing
        env_vars["QT_QPA_PLATFORM"] = "offscreen"

        # Disable Qt accessibility features that might cause issues in headless mode
        env_vars["QT_ACCESSIBILITY"] = "0"

        # Set Qt logging rules to reduce noise
        env_vars["QT_LOGGING_RULES"] = "qt.qpa.xcb.warning=false"

        # Platform-specific settings
        if self.platform == "linux":
            # Ensure we don't try to connect to X11 display
            env_vars["DISPLAY"] = ":99"  # Virtual display
            env_vars["QT_X11_NO_MITSHM"] = "1"

        return env_vars


class VirtualDisplayManager:
    """Manages virtual display for headless GUI testing."""

    def __init__(self):
        self.display_number = 99
        self.xvfb_process: Optional[subprocess.Popen] = None
        self.is_running = False

    def is_virtual_display_needed(self) -> bool:
        """Check if virtual display is needed for the current environment."""
        # Virtual display is needed on Linux systems without a display
        if platform.system().lower() != "linux":
            return False

        # Check if we're in a headless environment
        display = os.environ.get("DISPLAY")
        if not display:
            return True

        # Check if X11 is accessible
        try:
            result = run_command_with_timeout(["xset", "q"], timeout=5)
            return result.returncode != 0
        except:
            return True

    def setup_virtual_display(self) -> CheckResult:
        """
        Set up virtual display using Xvfb.

        Returns:
            CheckResult with setup status
        """
        if not self.is_virtual_display_needed():
            return CheckResult(
                name="setup_virtual_display",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output="Virtual display not needed on this platform",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={"display_needed": False},
            )

        # Check if Xvfb is available
        if not shutil.which("xvfb-run") and not shutil.which("Xvfb"):
            return CheckResult(
                name="setup_virtual_display",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=["Xvfb not available"],
                warnings=[],
                suggestions=[
                    "Install Xvfb:",
                    "  Ubuntu/Debian: sudo apt-get install xvfb",
                    "  CentOS/RHEL: sudo yum install xorg-x11-server-Xvfb",
                    "  Or use xvfb-run wrapper",
                ],
                metadata={"display_needed": True},
            )

        try:
            # Start Xvfb
            logger.info(f"Starting virtual display on :{self.display_number}")

            self.xvfb_process = subprocess.Popen(
                [
                    "Xvfb",
                    f":{self.display_number}",
                    "-screen",
                    "0",
                    "1024x768x24",
                    "-ac",
                    "+extension",
                    "GLX",
                    "+render",
                    "-noreset",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait a moment for Xvfb to start
            time.sleep(2)

            # Check if process is still running
            if self.xvfb_process.poll() is None:
                self.is_running = True
                os.environ["DISPLAY"] = f":{self.display_number}"

                return CheckResult(
                    name="setup_virtual_display",
                    status=CheckStatus.SUCCESS,
                    duration=0.0,
                    output=f"Virtual display started on :{self.display_number}",
                    errors=[],
                    warnings=[],
                    suggestions=[],
                    metadata={
                        "display_needed": True,
                        "display_number": self.display_number,
                        "display_env": f":{self.display_number}",
                    },
                )
            else:
                # Process died
                stdout, stderr = self.xvfb_process.communicate()
                return CheckResult(
                    name="setup_virtual_display",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=stdout.decode() if stdout else "",
                    errors=[
                        f"Xvfb failed to start: {stderr.decode() if stderr else 'Unknown error'}"
                    ],
                    warnings=[],
                    suggestions=["Check Xvfb installation and permissions"],
                    metadata={"display_needed": True},
                )

        except Exception as e:
            return CheckResult(
                name="setup_virtual_display",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Failed to start virtual display: {str(e)}"],
                warnings=[],
                suggestions=["Check Xvfb installation and system resources"],
                metadata={"display_needed": True},
            )

    def cleanup_virtual_display(self) -> CheckResult:
        """Clean up virtual display."""
        if not self.is_running or not self.xvfb_process:
            return CheckResult(
                name="cleanup_virtual_display",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output="No virtual display to clean up",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={},
            )

        try:
            logger.info("Stopping virtual display")
            self.xvfb_process.terminate()

            # Wait for process to terminate
            try:
                self.xvfb_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                self.xvfb_process.kill()
                self.xvfb_process.wait()

            self.is_running = False
            self.xvfb_process = None

            # Clean up environment variable
            if (
                "DISPLAY" in os.environ
                and os.environ["DISPLAY"] == f":{self.display_number}"
            ):
                del os.environ["DISPLAY"]

            return CheckResult(
                name="cleanup_virtual_display",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output="Virtual display stopped",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={},
            )

        except Exception as e:
            return CheckResult(
                name="cleanup_virtual_display",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Failed to stop virtual display: {str(e)}"],
                warnings=[],
                suggestions=["Check process status manually"],
                metadata={},
            )

    def get_display_environment(self) -> Dict[str, str]:
        """Get environment variables for virtual display."""
        if self.is_running:
            return {"DISPLAY": f":{self.display_number}"}
        return {}


class QtEnvironmentManager:
    """Combined Qt and virtual display environment manager."""

    def __init__(self):
        self.qt_manager = QtManager()
        self.display_manager = VirtualDisplayManager()

    def setup_qt_environment(self) -> CheckResult:
        """Set up complete Qt testing environment."""
        results = []

        # Check Qt availability
        qt_result = self.qt_manager.check_qt_availability()
        results.append(qt_result)

        # Set up virtual display if needed
        display_result = self.display_manager.setup_virtual_display()
        results.append(display_result)

        # Determine overall status
        has_failure = any(r.status == CheckStatus.FAILURE for r in results)
        has_warning = any(r.status == CheckStatus.WARNING for r in results)

        if has_failure:
            overall_status = CheckStatus.FAILURE
        elif has_warning:
            overall_status = CheckStatus.WARNING
        else:
            overall_status = CheckStatus.SUCCESS

        # Combine results
        all_errors = []
        all_warnings = []
        all_suggestions = []
        all_output = []

        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_suggestions.extend(result.suggestions)
            if result.output:
                all_output.append(result.output)

        return CheckResult(
            name="qt_environment_setup",
            status=overall_status,
            duration=0.0,
            output="\n".join(all_output),
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metadata={
                "qt_result": qt_result.metadata,
                "display_result": display_result.metadata,
            },
        )

    def get_qt_test_environment(self) -> Dict[str, str]:
        """Get complete environment variables for Qt testing."""
        env_vars = {}

        # Add Qt environment variables
        env_vars.update(self.qt_manager.get_qt_environment_variables())

        # Add display environment variables
        env_vars.update(self.display_manager.get_display_environment())

        return env_vars

    def cleanup_qt_environment(self) -> CheckResult:
        """Clean up Qt testing environment."""
        return self.display_manager.cleanup_virtual_display()
