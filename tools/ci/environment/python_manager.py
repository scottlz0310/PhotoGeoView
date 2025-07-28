"""
Python Version Detection and Management Module

This module provides functionality to detect, manage, and validate Python versions
for CI/CD simulation. It supports pyenv, conda, and system Python installations.

Author: Kiro (AI Integration and Quality Assurance)
"""

import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import logging
import shutil
import json

try:
    from ..models import CheckResult, CheckStatus
    from ..utils import run_command
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from models import CheckResult, CheckStatus
    from utils import run_command

# Create a wrapper for timeout functionality
def run_command_with_timeout(command, timeout=30, env=None):
    """Wrapper to provide timeout functionality."""
    import subprocess
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
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


class PythonVersionInfo:
    """Information about a Python version installation."""

    def __init__(self, version: str, executable: str, source: str, is_available: bool = True):
        self.version = version
        self.executable = executable
        self.source = source  # 'system', 'pyenv', 'conda'
        self.is_available = is_available
        self.venv_path: Optional[str] = None

    def __str__(self) -> str:
        return f"Python {self.version} ({self.source}) at {self.executable}"

    def to_dict(self) -> Dict:
        return {
            'version': self.version,
            'executable': self.executable,
            'source': self.source,
            'is_available': self.is_available,
            'venv_path': self.venv_path
        }


class PythonVersionManager:
    """Manages Python version detection and virtual environment creation."""

    SUPPORTED_VERSIONS = ['3.9', '3.10', '3.11']
    VENV_BASE_DIR = Path('.ci-venvs')

    def __init__(self):
        self.discovered_versions: Dict[str, PythonVersionInfo] = {}
        self.current_python = PythonVersionInfo(
            version=f"{sys.version_info.major}.{sys.version_info.minor}",
            executable=sys.executable,
            source='current',
            is_available=True
        )

    def discover_python_versions(self) -> Dict[str, PythonVersionInfo]:
        """
        Discover available Python versions from various sources.

        Returns:
            Dict mapping version strings to PythonVersionInfo objects
        """
        logger.info("Discovering available Python versions...")

        # Clear previous discoveries
        self.discovered_versions.clear()

        # Add current Python version
        current_version = self.current_python.version
        if current_version in self.SUPPORTED_VERSIONS:
            self.discovered_versions[current_version] = self.current_python

        # Discover from pyenv
        self._discover_pyenv_versions()

        # Discover from conda
        self._discover_conda_versions()

        # Discover from system
        self._discover_system_versions()

        logger.info(f"Discovered {len(self.discovered_versions)} Python versions")
        for version, info in self.discovered_versions.items():
            logger.info(f"  {info}")

        return self.discovered_versions

    def _discover_pyenv_versions(self) -> None:
        """Discover Python versions managed by pyenv."""
        try:
            # Check if pyenv is available
            result = run_command_with_timeout(['pyenv', '--version'], timeout=10)
            if result.returncode != 0:
                logger.debug("pyenv not available")
                return

            # Get list of installed versions
            result = run_command_with_timeout(['pyenv', 'versions', '--bare'], timeout=30)
            if result.returncode != 0:
                logger.warning("Failed to get pyenv versions")
                return

            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue

                version_name = line.strip()
                # Extract major.minor version
                version_parts = version_name.split('.')
                if len(version_parts) >= 2:
                    major_minor = f"{version_parts[0]}.{version_parts[1]}"

                    if major_minor in self.SUPPORTED_VERSIONS:
                        # Get the executable path
                        executable_result = run_command_with_timeout(
                            ['pyenv', 'prefix', version_name], timeout=10
                        )
                        if executable_result.returncode == 0:
                            prefix = executable_result.stdout.strip()
                            executable = os.path.join(prefix, 'bin', 'python')
                            if os.path.exists(executable):
                                self.discovered_versions[major_minor] = PythonVersionInfo(
                                    version=major_minor,
                                    executable=executable,
                                    source='pyenv'
                                )
                                logger.debug(f"Found pyenv Python {major_minor} at {executable}")

        except Exception as e:
            logger.debug(f"Error discovering pyenv versions: {e}")

    def _discover_conda_versions(self) -> None:
        """Discover Python versions managed by conda."""
        try:
            # Check if conda is available
            result = run_command_with_timeout(['conda', '--version'], timeout=10)
            if result.returncode != 0:
                logger.debug("conda not available")
                return

            # Get list of environments
            result = run_command_with_timeout(['conda', 'env', 'list', '--json'], timeout=30)
            if result.returncode != 0:
                logger.warning("Failed to get conda environments")
                return

            env_data = json.loads(result.stdout)
            for env_path in env_data.get('envs', []):
                # Check for python executable in environment
                python_exe = os.path.join(env_path, 'bin', 'python')
                if not os.path.exists(python_exe):
                    python_exe = os.path.join(env_path, 'python.exe')  # Windows

                if os.path.exists(python_exe):
                    # Get version
                    version_result = run_command_with_timeout(
                        [python_exe, '--version'], timeout=10
                    )
                    if version_result.returncode == 0:
                        version_output = version_result.stdout.strip()
                        if version_output.startswith('Python '):
                            version_str = version_output[7:]  # Remove 'Python '
                            version_parts = version_str.split('.')
                            if len(version_parts) >= 2:
                                major_minor = f"{version_parts[0]}.{version_parts[1]}"

                                if major_minor in self.SUPPORTED_VERSIONS:
                                    # Only add if not already found from a better source
                                    if major_minor not in self.discovered_versions:
                                        self.discovered_versions[major_minor] = PythonVersionInfo(
                                            version=major_minor,
                                            executable=python_exe,
                                            source='conda'
                                        )
                                        logger.debug(f"Found conda Python {major_minor} at {python_exe}")

        except Exception as e:
            logger.debug(f"Error discovering conda versions: {e}")

    def _discover_system_versions(self) -> None:
        """Discover system Python versions."""
        for version in self.SUPPORTED_VERSIONS:
            if version in self.discovered_versions:
                continue  # Already found from better source

            # Try common executable names
            executables = [
                f'python{version}',
                f'python{version.replace(".", "")}',
                'python3',
                'python'
            ]

            for exe_name in executables:
                try:
                    exe_path = shutil.which(exe_name)
                    if exe_path:
                        # Verify version
                        result = run_command_with_timeout([exe_path, '--version'], timeout=10)
                        if result.returncode == 0:
                            version_output = result.stdout.strip()
                            if version_output.startswith('Python '):
                                version_str = version_output[7:]
                                version_parts = version_str.split('.')
                                if len(version_parts) >= 2:
                                    major_minor = f"{version_parts[0]}.{version_parts[1]}"

                                    if major_minor == version:
                                        self.discovered_versions[version] = PythonVersionInfo(
                                            version=version,
                                            executable=exe_path,
                                            source='system'
                                        )
                                        logger.debug(f"Found system Python {version} at {exe_path}")
                                        break
                except Exception as e:
                    logger.debug(f"Error checking {exe_name}: {e}")

    def get_available_versions(self) -> List[str]:
        """Get list of available Python versions."""
        if not self.discovered_versions:
            self.discover_python_versions()
        return list(self.discovered_versions.keys())

    def get_missing_versions(self) -> List[str]:
        """Get list of supported versions that are not available."""
        available = set(self.get_available_versions())
        supported = set(self.SUPPORTED_VERSIONS)
        return list(supported - available)

    def check_version_compatibility(self, required_versions: List[str] = None) -> CheckResult:
        """
        Check Python version compatibility.

        Args:
            required_versions: List of required versions. Defaults to SUPPORTED_VERSIONS.

        Returns:
            CheckResult with compatibility status
        """
        if required_versions is None:
            required_versions = self.SUPPORTED_VERSIONS

        available_versions = self.get_available_versions()
        missing_versions = [v for v in required_versions if v not in available_versions]

        errors = []
        warnings = []
        suggestions = []

        if missing_versions:
            errors.append(f"Missing Python versions: {', '.join(missing_versions)}")
            suggestions.extend([
                "Install missing Python versions using:",
                "  - pyenv: pyenv install <version>",
                "  - conda: conda create -n py<version> python=<version>",
                "  - System package manager (apt, yum, brew, etc.)"
            ])

        if len(available_versions) < len(required_versions):
            warnings.append(f"Only {len(available_versions)}/{len(required_versions)} required Python versions available")

        status = CheckStatus.SUCCESS if not missing_versions else CheckStatus.FAILURE
        if missing_versions and available_versions:
            status = CheckStatus.WARNING  # Partial availability

        return CheckResult(
            name="python_version_compatibility",
            status=status,
            duration=0.0,
            output=f"Available versions: {', '.join(available_versions)}",
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata={
                'available_versions': available_versions,
                'missing_versions': missing_versions,
                'discovered_versions': {v: info.to_dict() for v, info in self.discovered_versions.items()}
            }
        )

    def create_virtual_environment(self, python_version: str, force_recreate: bool = False) -> CheckResult:
        """
        Create a virtual environment for the specified Python version.

        Args:
            python_version: Python version (e.g., '3.9')
            force_recreate: Whether to recreate if already exists

        Returns:
            CheckResult with creation status
        """
        if python_version not in self.discovered_versions:
            return CheckResult(
                name=f"create_venv_{python_version}",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Python {python_version} not available"],
                warnings=[],
                suggestions=["Install Python {python_version} first".format(python_version=python_version)],
                metadata={}
            )

        python_info = self.discovered_versions[python_version]
        venv_path = self.VENV_BASE_DIR / f"py{python_version}"

        # Check if already exists
        if venv_path.exists() and not force_recreate:
            python_info.venv_path = str(venv_path)
            return CheckResult(
                name=f"create_venv_{python_version}",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output=f"Virtual environment already exists at {venv_path}",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={'venv_path': str(venv_path)}
            )

        # Create directory
        venv_path.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing if force recreate
        if venv_path.exists() and force_recreate:
            shutil.rmtree(venv_path)

        try:
            # Create virtual environment
            logger.info(f"Creating virtual environment for Python {python_version} at {venv_path}")
            venv.create(venv_path, with_pip=True)

            python_info.venv_path = str(venv_path)

            return CheckResult(
                name=f"create_venv_{python_version}",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output=f"Virtual environment created at {venv_path}",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={'venv_path': str(venv_path)}
            )

        except Exception as e:
            return CheckResult(
                name=f"create_venv_{python_version}",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Failed to create virtual environment: {str(e)}"],
                warnings=[],
                suggestions=["Check Python installation and permissions"],
                metadata={}
            )

    def get_venv_python_executable(self, python_version: str) -> Optional[str]:
        """Get the Python executable path for a virtual environment."""
        if python_version not in self.discovered_versions:
            return None

        python_info = self.discovered_versions[python_version]
        if not python_info.venv_path:
            return None

        venv_path = Path(python_info.venv_path)

        # Try different possible paths
        possible_paths = [
            venv_path / 'bin' / 'python',  # Unix-like
            venv_path / 'Scripts' / 'python.exe',  # Windows
            venv_path / 'Scripts' / 'python',  # Windows alternative
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    def install_requirements_in_venv(self, python_version: str, requirements_file: str = 'requirements.txt') -> CheckResult:
        """Install requirements in the virtual environment."""
        venv_python = self.get_venv_python_executable(python_version)
        if not venv_python:
            return CheckResult(
                name=f"install_requirements_{python_version}",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Virtual environment for Python {python_version} not found"],
                warnings=[],
                suggestions=[f"Create virtual environment for Python {python_version} first"],
                metadata={}
            )

        if not os.path.exists(requirements_file):
            return CheckResult(
                name=f"install_requirements_{python_version}",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Requirements file {requirements_file} not found"],
                warnings=[],
                suggestions=["Create requirements.txt file"],
                metadata={}
            )

        try:
            logger.info(f"Installing requirements in Python {python_version} virtual environment")
            result = run_command_with_timeout([
                venv_python, '-m', 'pip', 'install', '-r', requirements_file
            ], timeout=300)  # 5 minutes timeout

            if result.returncode == 0:
                return CheckResult(
                    name=f"install_requirements_{python_version}",
                    status=CheckStatus.SUCCESS,
                    duration=0.0,
                    output=result.stdout,
                    errors=[],
                    warnings=[],
                    suggestions=[],
                    metadata={}
                )
            else:
                return CheckResult(
                    name=f"install_requirements_{python_version}",
                    status=CheckStatus.FAILURE,
                    duration=0.0,
                    output=result.stdout,
                    errors=[result.stderr] if result.stderr else ["Installation failed"],
                    warnings=[],
                    suggestions=["Check requirements.txt for compatibility issues"],
                    metadata={}
                )

        except Exception as e:
            return CheckResult(
                name=f"install_requirements_{python_version}",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Failed to install requirements: {str(e)}"],
                warnings=[],
                suggestions=["Check virtual environment and requirements file"],
                metadata={}
            )

    def cleanup_virtual_environments(self) -> CheckResult:
        """Clean up all created virtual environments."""
        if not self.VENV_BASE_DIR.exists():
            return CheckResult(
                name="cleanup_venvs",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output="No virtual environments to clean up",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={}
            )

        try:
            shutil.rmtree(self.VENV_BASE_DIR)

            # Clear venv paths from discovered versions
            for python_info in self.discovered_versions.values():
                python_info.venv_path = None

            return CheckResult(
                name="cleanup_venvs",
                status=CheckStatus.SUCCESS,
                duration=0.0,
                output=f"Cleaned up virtual environments at {self.VENV_BASE_DIR}",
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={}
            )

        except Exception as e:
            return CheckResult(
                name="cleanup_venvs",
                status=CheckStatus.FAILURE,
                duration=0.0,
                output="",
                errors=[f"Failed to clean up virtual environments: {str(e)}"],
                warnings=[],
                suggestions=["Check permissions and try manual cleanup"],
                metadata={}
            )
