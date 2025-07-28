"""
Virtual Display Management Module

This module provides functionality to manage virtual displays for headless GUI testing.
It's separated from qt_manager.py for better modularity and reusability.

Author: Kiro (AI Integration and Quality Assurance)
"""

import os
import subprocess
import platform
import shutil
import time
import signal
from typing import Dict, Optional
import logging

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


class DisplayManager:
    """Manages virtual display for headless GUI testin"""

    def __init__(self, display_number: int = 99):
        self.display_number = display_number
        self.xvfb_process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.platform = platform.system().lower()

    def is_virtual_display_needed(self) -> bool:
        """Check if virtual display is needed for the current environment."""
        # Virtual display is only needed on Linux systems
        if self.platform != "linux":
            logger.debug(f"Virtual display not needed on {self.platform}")
            return False

        # Check if we're in a headless environment
        display = os.environ.get("DISPLAY")
        if not display:
            logger.debug("No DISPLAY environment variable, virtual display needed")
            return True

        # Check if X11 is accessible
        try:
            result = run_command_with_timeout(["xset", "q"], timeout=5)
            if result.returncode == 0:
                logger.debug("X11 display accessible, virtual display not needed")
                return False
            else:
                logger.debug("X11 display not accessible, virtual display needed")
                return True
        except Exception as e:
            logger.debug(
                f"Cannot check X11 accessibility: {e}, assuming virtual display needed"
            )
            return True

    def check_xvfb_availability(self) -> CheckResult:
        """Check if Xvfb is available on the system."""
        if not self.is_virtual_display_needed():
            return CheckResult(
                name="check_xvfb",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output="Xvfb not needed on this platform",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={"xvfb_needed": False},
            )

        # Check for xvfb-run (wrapper script)
        xvfb_run_path = shutil.which("xvfb-run")
        xvfb_path = shutil.which("Xvfb")

        if xvfb_run_path:
            return CheckResult(
                name="check_xvfb",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output=f"xvfb-run available at {xvfb_run_path}",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={
                    "xvfb_needed": True,
                    "xvfb_run_available": True,
                    "xvfb_run_path": xvfb_run_path,
                    "xvfb_available": bool(xvfb_path),
                    "xvfb_path": xvfb_path,
                },
            )
        elif xvfb_path:
            return CheckResult(
                name="check_xvfb",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output=f"Xvfb available at {xvfb_path}",
                errors=[],
                warnings=["xvfb-run wrapper not available, using Xvfb directly"],
                suggestions=["Consider installing xvfb package for xvfb-run wrapper"],
                metadata={
                    "xvfb_needed": True,
                    "xvfb_run_available": False,
                    "xvfb_available": True,
                    "xvfb_path": xvfb_path,
                },
            )
        else:
            return CheckResult(
                name="check_xvfb",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=["Xvfb not available"],
                warnings=[],
                suggestions=self._get_xvfb_installation_suggestions(),
                metadata={
                    "xvfb_needed": True,
                    "xvfb_run_available": False,
                    "xvfb_available": False,
                },
            )

    def _get_xvfb_installation_suggestions(self) -> list:
        """Get platform-specific Xvfb installation suggestions."""
        if self.platform == "linux":
            return [
                "Install Xvfb:",
                "  Ubuntu/Debian: sudo apt-get install xvfb",
                "  CentOS/RHEL: sudo yum install xorg-x11-server-Xvfb",
                "  Fedora: sudo dnf install xorg-x11-server-Xvfb",
                "  Arch Linux: sudo pacman -S xorg-server-xvfb",
            ]
        else:
            return ["Xvfb is only available on Linux systems"]

    def start_virtual_display(
        self, width: int = 1024, height: int = 768, depth: int = 24
    ) -> CheckResult:
        """
        Start virtual display using Xvfb.

        Args:
            width: Display width in pixels
            height: Display height in pixels
            depth: Color depth in bits

        Returns:
            CheckResult with startup status
        """
        if not self.is_virtual_display_needed():
            return CheckResult(
                name="start_virtual_display",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output="Virtual display not needed on this platform",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={"display_needed": False},
            )

        if self.is_running:
            return CheckResult(
                name="start_virtual_display",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output=f"Virtual display already running on :{self.display_number}",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={
                    "display_needed": True,
                    "already_running": True,
                    "display_number": self.display_number,
                },
            )

        # Check Xvfb availability first
        xvfb_check = self.check_xvfb_availability()
        if xvfb_check.status == CheckStatus.FAILURE:
            return xvfb_check

        try:
            # Find an available display number
            original_display = self.display_number
            while self._is_display_in_use(self.display_number):
                self.display_number += 1
                if self.display_number > 199:  # Reasonable upper limit
                    self.display_number = original_display
                    break

            logger.info(f"Starting virtual display on :{self.display_number}")

            # Start Xvfb
            cmd = [
                "Xvfb",
                f":{self.display_number}",
                "-screen",
                "0",
                f"{width}x{height}x{depth}",
                "-ac",  # Disable access control
                "+extension",
                "GLX",  # Enable GLX extension
                "+render",  # Enable RENDER extension
                "-noreset",  # Don't reset after last client exits
                "-nolisten",
                "tcp",  # Don't listen on TCP
            ]

            self.xvfb_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,  # Create new process group
            )

            # Wait a moment for Xvfb to start
            time.sleep(2)

            # Check if process is still running
            if self.xvfb_process.poll() is None:
                self.is_running = True
                os.environ["DISPLAY"] = f":{self.display_number}"

                # Verify display is working
                verify_result = self._verify_display()
                if verify_result.status != CheckStatus.SUCCESS:
                    # Clean up and return verification error
                    self.stop_virtual_display()
                    return verify_result

                return CheckResult(
                    name="start_virtual_display",
                    status=CheckStatus.SUCCESS,
                    duration=0.0,
                    output=f"Virtual display started on :{self.display_number} ({width}x{height}x{depth})",
                    errors=[],
                    warnings=[],
                    suggestions=[],
                    metadata={
                        "display_needed": True,
                        "display_number": self.display_number,
                        "display_env": f":{self.display_number}",
                        "resolution": f"{width}x{height}x{depth}",
                    },
                )
            else:
                # Process died
                stdout, stderr = self.xvfb_process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"

                return CheckResult(
                    name="start_virtual_display",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=stdout.decode() if stdout else "",
                    errors=[f"Xvfb failed to start: {error_msg}"],
                    warnings=[],
                    suggestions=[
                        "Check if display number is available",
                        "Verify Xvfb installation",
                        "Check system resources and permissions",
                    ],
                    metadata={"display_needed": True},
                )

        except Exception as e:
            return CheckResult(
                name="start_virtual_display",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Failed to start virtual display: {str(e)}"],
                warnings=[],
                suggestions=["Check Xvfb installation and system resources"],
                metadata={"display_needed": True},
            )

    def _is_display_in_use(self, display_num: int) -> bool:
        """Check if a display number is already in use."""
        lock_file = f"/tmp/.X{display_num}-lock"
        return os.path.exists(lock_file)

    def _verify_display(self) -> CheckResult:
        """Verify that the virtual display is working."""
        try:
            # Try to query the display
            result = run_command_with_timeout(["xset", "q"], timeout=10)
            if result.returncode == 0:
                return CheckResult(
                    name="verify_display",
                    status=CheckStatus.SUCCESS,
                    duration=0.0,
                    output="Display verification successful",
                    errors=[],
                    warnings=[],
                    suggestions=[],
                    metadata={},
                )
            else:
                return CheckResult(
                    name="verify_display",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=result.stdout,
                    errors=[f"Display verification failed: {result.stderr}"],
                    warnings=[],
                    suggestions=["Check Xvfb process and display configuration"],
                    metadata={},
                )
        except Exception as e:
            return CheckResult(
                name="verify_display",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Display verification error: {str(e)}"],
                warnings=[],
                suggestions=["Install xset utility or check X11 tools"],
                metadata={},
            )

    def stop_virtual_display(self) -> CheckResult:
        """Stop the virtual display."""
        if not self.is_running or not self.xvfb_process:
            return CheckResult(
                name="stop_virtual_display",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output="No virtual display to stop",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={},
            )

        try:
            logger.info("Stopping virtual display")

            # Send SIGTERM to the process group
            os.killpg(os.getpgid(self.xvfb_process.pid), signal.SIGTERM)

            # Wait for process to terminate
            try:
                self.xvfb_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                logger.warning("Xvfb didn't terminate gracefully, force killing")
                os.killpg(os.getpgid(self.xvfb_process.pid), signal.SIGKILL)
                self.xvfb_process.wait()

            self.is_running = False
            self.xvfb_process = None

            # Clean up environment variable
            if (
                "DISPLAY" in os.environ
                and os.environ["DISPLAY"] == f":{self.display_number}"
            ):
                del os.environ["DISPLAY"]

            # Clean up lock file if it exists
            lock_file = f"/tmp/.X{self.display_number}-lock"
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass  # Ignore cleanup errors

            return CheckResult(
                name="stop_virtual_display",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output=f"Virtual display :{self.display_number} stopped",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={},
            )

        except Exception as e:
            return CheckResult(
                name="stop_virtual_display",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Failed to stop virtual display: {str(e)}"],
                warnings=[],
                suggestions=["Check process status manually with 'ps aux | grep Xvfb'"],
                metadata={},
            )

    def get_display_environment(self) -> Dict[str, str]:
        """Get environment variables for the virtual display."""
        if self.is_running:
            return {
                "DISPLAY": f":{self.display_number}",
                "XAUTHORITY": "",  # Disable X authority for headless testing
            }
        return {}

    def run_with_display(
        self, command: list, timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """
        Run a command with the virtual display environment.

        Args:
            command: Command to run
            timeout: Timeout in seconds

        Returns:
            CompletedProcess result
        """
        env = os.environ.copy()
        env.update(self.get_display_environment())

        return run_command_with_timeout(command, timeout=timeout, env=env)

    def __enter__(self):
        """Context manager entry."""
        result = self.start_virtual_display()
        if result.status == CheckStatus.FAILURE:
            raise RuntimeError(f"Failed to start virtual display: {result.errors}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_virtual_display()
