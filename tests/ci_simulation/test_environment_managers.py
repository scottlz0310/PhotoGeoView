"""
Unit tests for environment management components.
"""

import os
import subprocess

# Import environment managers
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools", "ci"))

from environment.display_manager import DisplayManager
from environment.python_manager import PythonVersionManager
from environment.qt_manager import QtManager
from interfaces import EnvironmentError


class TestPythonVersionManager:
    """Test cases for PythonVersionManager."""

    def test_python_manager_creation(self):
        """Test PythonVersionManager creation."""
        manager = PythonVersionManager()
        assert manager.SUPPORTED_VERSIONS == ["3.9", "3.10", "3.11"]
        assert manager.current_python is not None

    @patch("subprocess.run")
    def test_get_current_python_version(self, mock_run):
        """Test getting current Python version."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Python 3.10.5"
        mock_run.return_value.stderr = ""

        manager = PythonManager()
        version = manager.get_current_python_version()

        assert version == "3.10.5"
        assert manager.current_version == "3.10.5"

    @patch("subprocess.run")
    def test_get_current_python_version_failure(self, mock_run):
        """Test getting Python version when command fails."""
        mock_run.side_effect = FileNotFoundError("python not found")

        manager = PythonManager()
        version = manager.get_current_python_version()

        assert version is None

    @patch("subprocess.run")
    def test_detect_available_versions_pyenv(self, mock_run):
        """Test detecting available Python versions with pyenv."""
        # Mock pyenv versions command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "  3.9.16\n* 3.10.11\n  3.11.3\n"
        mock_run.return_value.stderr = ""

        manager = PythonManager()
        versions = manager.detect_available_versions()

        assert "3.9.16" in versions
        assert "3.10.11" in versions
        assert "3.11.3" in versions
        assert len(versions) == 3

    @patch("subprocess.run")
    def test_detect_available_versions_conda(self, mock_run):
        """Test detecting available Python versions with conda."""

        # Mock conda failing, then conda env list succeeding
        def side_effect(*args, **kwargs):
            if "pyenv" in args[0]:
                raise FileNotFoundError("pyenv not found")
            elif "conda" in args[0] and "env" in args[0]:
                result = Mock()
                result.returncode = 0
                result.stdout = "base                  *  /opt/conda\npy39                     /opt/conda/envs/py39\npy310                    /opt/conda/envs/py310\n"
                result.stderr = ""
                return result
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = "3.10.5"
                result.stderr = ""
                return result

        mock_run.side_effect = side_effect

        manager = PythonManager()
        versions = manager.detect_available_versions()

        assert len(versions) >= 1  # At least the current version

    @patch("subprocess.run")
    def test_detect_available_versions_system_only(self, mock_run):
        """Test detecting versions when only system Python is available."""

        def side_effect(*args, **kwargs):
            if "pyenv" in args[0] or "conda" in args[0]:
                raise FileNotFoundError("command not found")
            else:
                result = Mock()
                result.returncode = 0
                result.stdout = "Python 3.10.5"
                result.stderr = ""
                return result

        mock_run.side_effect = side_effect

        manager = PythonManager()
        versions = manager.detect_available_versions()

        assert "3.10.5" in versions
        assert len(versions) == 1

    @patch("subprocess.run")
    def test_is_version_available(self, mock_run):
        """Test checking if a specific Python version is available."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Python 3.10.5"
        mock_run.return_value.stderr = ""

        manager = PythonManager()

        assert manager.is_version_available("3.10") is True
        assert manager.is_version_available("3.10.5") is True

    @patch("subprocess.run")
    def test_is_version_available_not_found(self, mock_run):
        """Test checking unavailable Python version."""
        mock_run.side_effect = FileNotFoundError("python3.8 not found")

        manager = PythonManager()

        assert manager.is_version_available("3.8") is False

    @patch("subprocess.run")
    def test_setup_virtual_environment(self, mock_run, temp_dir):
        """Test setting up virtual environment."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Virtual environment created"
        mock_run.return_value.stderr = ""

        manager = PythonManager()
        venv_path = os.path.join(temp_dir, "test_venv")

        success = manager.setup_virtual_environment(venv_path, "3.10")

        assert success is True
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_setup_virtual_environment_failure(self, mock_run, temp_dir):
        """Test virtual environment setup failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Failed to create virtual environment"

        manager = PythonManager()
        venv_path = os.path.join(temp_dir, "test_venv")

        success = manager.setup_virtual_environment(venv_path, "3.10")

        assert success is False

    @patch("subprocess.run")
    def test_activate_virtual_environment(self, mock_run, temp_dir):
        """Test activating virtual environment."""
        venv_path = os.path.join(temp_dir, "test_venv")
        os.makedirs(os.path.join(venv_path, "bin"), exist_ok=True)

        # Create fake activate script
        activate_script = os.path.join(venv_path, "bin", "activate")
        with open(activate_script, "w") as f:
            f.write("# Virtual environment activation script")

        manager = PythonManager()
        env_vars = manager.activate_virtual_environment(venv_path)

        assert "VIRTUAL_ENV" in env_vars
        assert env_vars["VIRTUAL_ENV"] == venv_path
        assert venv_path in env_vars["PATH"]

    def test_activate_nonexistent_virtual_environment(self, temp_dir):
        """Test activating non-existent virtual environment."""
        venv_path = os.path.join(temp_dir, "nonexistent_venv")

        manager = PythonManager()

        with pytest.raises(EnvironmentError):
            manager.activate_virtual_environment(venv_path)

    @patch("subprocess.run")
    def test_install_requirements(self, mock_run, temp_dir):
        """Test installing requirements in virtual environment."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Successfully installed packages"
        mock_run.return_value.stderr = ""

        # Create requirements file
        requirements_file = os.path.join(temp_dir, "pyproject.toml")
        with open(requirements_file, "w") as f:
            f.write("pytest>=7.0.0\nblack>=22.0.0\n")

        manager = PythonManager()
        success = manager.install_requirements(requirements_file)

        assert success is True
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_install_requirements_failure(self, mock_run, temp_dir):
        """Test requirements installation failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Failed to install packages"

        requirements_file = os.path.join(temp_dir, "requirements.txt")
        with open(requirements_file, "w") as f:
            f.write("nonexistent-package==999.999.999\n")

        manager = PythonManager()
        success = manager.install_requirements(requirements_file)

        assert success is False

    def test_setup_environment(self, temp_dir):
        """Test complete environment setup."""
        requirements = {
            "python_version": "3.10",
            "virtual_env": True,
            "venv_path": os.path.join(temp_dir, "test_venv"),
            "requirements_file": None,
        }

        manager = PythonManager()

        with (
            patch.object(manager, "is_version_available", return_value=True),
            patch.object(manager, "setup_virtual_environment", return_value=True),
        ):

            success = manager.setup_environment(requirements)
            assert success is True

    def test_setup_environment_unsupported_version(self):
        """Test environment setup with unsupported Python version."""
        requirements = {"python_version": "2.7", "virtual_env": True}

        manager = PythonManager()

        with patch.object(manager, "is_version_available", return_value=False):
            success = manager.setup_environment(requirements)
            assert success is False

    def test_cleanup_environment(self, temp_dir):
        """Test environment cleanup."""
        venv_path = os.path.join(temp_dir, "test_venv")
        os.makedirs(venv_path, exist_ok=True)

        manager = PythonManager()
        manager.active_venv = venv_path

        with patch("shutil.rmtree") as mock_rmtree:
            manager.cleanup_environment()
            mock_rmtree.assert_called_once_with(venv_path)

        assert manager.active_venv is None

    def test_is_environment_ready(self):
        """Test checking if environment is ready."""
        manager = PythonManager()

        # Without setup
        assert manager.is_environment_ready() is False

        # With setup
        manager.current_version = "3.10.5"
        assert manager.is_environment_ready() is True


class TestQtManager:
    """Test cases for QtManager."""

    def test_qt_manager_creation(self):
        """Test QtManager creation."""
        manager = QtManager()
        assert manager.required_packages == ["PyQt5", "PyQt6", "PySide2", "PySide6"]
        assert manager.available_qt is None

    @patch("importlib.import_module")
    def test_detect_qt_installation_pyqt5(self, mock_import):
        """Test detecting PyQt5 installation."""

        def side_effect(module_name):
            if module_name == "PyQt5":
                return Mock()
            else:
                raise ImportError(f"No module named '{module_name}'")

        mock_import.side_effect = side_effect

        manager = QtManager()
        qt_info = manager.detect_qt_installation()

        assert qt_info["available"] is True
        assert qt_info["version"] == "PyQt5"
        assert qt_info["packages"] == ["PyQt5"]

    @patch("importlib.import_module")
    def test_detect_qt_installation_multiple(self, mock_import):
        """Test detecting multiple Qt installations."""

        def side_effect(module_name):
            if module_name in ["PyQt5", "PySide6"]:
                return Mock()
            else:
                raise ImportError(f"No module named '{module_name}'")

        mock_import.side_effect = side_effect

        manager = QtManager()
        qt_info = manager.detect_qt_installation()

        assert qt_info["available"] is True
        assert len(qt_info["packages"]) == 2
        assert "PyQt5" in qt_info["packages"]
        assert "PySide6" in qt_info["packages"]

    @patch("importlib.import_module")
    def test_detect_qt_installation_none(self, mock_import):
        """Test when no Qt installation is found."""
        mock_import.side_effect = ImportError("No module found")

        manager = QtManager()
        qt_info = manager.detect_qt_installation()

        assert qt_info["available"] is False
        assert qt_info["packages"] == []

    @patch("subprocess.run")
    def test_check_system_qt_libraries_linux(self, mock_run):
        """Test checking system Qt libraries on Linux."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "libQt5Core.so.5\nlibQt5Gui.so.5\n"
        mock_run.return_value.stderr = ""

        manager = QtManager()

        with patch("platform.system", return_value="Linux"):
            libraries = manager.check_system_qt_libraries()

            assert len(libraries) > 0
            assert any("Qt5" in lib for lib in libraries)

    @patch("subprocess.run")
    def test_check_system_qt_libraries_windows(self, mock_run):
        """Test checking system Qt libraries on Windows."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Qt5Core.dll\nQt5Gui.dll\n"
        mock_run.return_value.stderr = ""

        manager = QtManager()

        with patch("platform.system", return_value="Windows"):
            libraries = manager.check_system_qt_libraries()

            assert len(libraries) > 0
            assert any("Qt5" in lib for lib in libraries)

    @patch("subprocess.run")
    def test_check_system_qt_libraries_macos(self, mock_run):
        """Test checking system Qt libraries on macOS."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "/usr/local/lib/QtCore.framework\n"
        mock_run.return_value.stderr = ""

        manager = QtManager()

        with patch("platform.system", return_value="Darwin"):
            libraries = manager.check_system_qt_libraries()

            assert len(libraries) > 0

    def test_setup_qt_environment_variables(self):
        """Test setting up Qt environment variables."""
        manager = QtManager()

        env_vars = manager.setup_qt_environment_variables()

        assert "QT_QPA_PLATFORM" in env_vars
        assert "QT_LOGGING_RULES" in env_vars
        assert env_vars["QT_QPA_PLATFORM"] == "offscreen"

    def test_setup_qt_environment_variables_with_display(self):
        """Test setting up Qt environment variables with display."""
        manager = QtManager()

        env_vars = manager.setup_qt_environment_variables(headless=False)

        # Should not set offscreen platform when not headless
        assert env_vars.get("QT_QPA_PLATFORM") != "offscreen"

    @patch("subprocess.run")
    def test_install_qt_dependencies_pip(self, mock_run):
        """Test installing Qt dependencies via pip."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Successfully installed PyQt5"
        mock_run.return_value.stderr = ""

        manager = QtManager()
        success = manager.install_qt_dependencies("PyQt5")

        assert success is True
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_install_qt_dependencies_failure(self, mock_run):
        """Test Qt dependencies installation failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Failed to install PyQt5"

        manager = QtManager()
        success = manager.install_qt_dependencies("PyQt5")

        assert success is False

    def test_setup_environment(self):
        """Test complete Qt environment setup."""
        requirements = {"qt_required": True, "headless": True, "preferred_qt": "PyQt5"}

        manager = QtManager()

        with patch.object(manager, "detect_qt_installation") as mock_detect:
            mock_detect.return_value = {
                "available": True,
                "version": "PyQt5",
                "packages": ["PyQt5"],
            }

            success = manager.setup_environment(requirements)
            assert success is True

    def test_setup_environment_no_qt_required(self):
        """Test environment setup when Qt is not required."""
        requirements = {"qt_required": False}

        manager = QtManager()
        success = manager.setup_environment(requirements)

        assert success is True

    def test_setup_environment_qt_missing(self):
        """Test environment setup when Qt is required but missing."""
        requirements = {"qt_required": True, "headless": True}

        manager = QtManager()

        with patch.object(manager, "detect_qt_installation") as mock_detect:
            mock_detect.return_value = {"available": False, "packages": []}

            success = manager.setup_environment(requirements)
            assert success is False

    def test_cleanup_environment(self):
        """Test Qt environment cleanup."""
        manager = QtManager()
        manager.qt_env_vars = {"QT_QPA_PLATFORM": "offscreen"}

        manager.cleanup_environment()

        assert manager.qt_env_vars == {}

    def test_is_environment_ready(self):
        """Test checking if Qt environment is ready."""
        manager = QtManager()

        # Without Qt available
        assert manager.is_environment_ready() is False

        # With Qt available
        manager.available_qt = "PyQt5"
        assert manager.is_environment_ready() is True


class TestDisplayManager:
    """Test cases for DisplayManager."""

    def test_display_manager_creation(self):
        """Test DisplayManager creation."""
        manager = DisplayManager()
        assert manager.display_number is None
        assert manager.xvfb_process is None

    @patch("subprocess.Popen")
    def test_start_virtual_display_success(self, mock_popen):
        """Test starting virtual display successfully."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        manager = DisplayManager()
        success = manager.start_virtual_display()

        assert success is True
        assert manager.display_number is not None
        assert manager.xvfb_process == mock_process

    @patch("subprocess.Popen")
    def test_start_virtual_display_failure(self, mock_popen):
        """Test virtual display start failure."""
        mock_popen.side_effect = FileNotFoundError("Xvfb not found")

        manager = DisplayManager()
        success = manager.start_virtual_display()

        assert success is False
        assert manager.xvfb_process is None

    @patch("subprocess.Popen")
    def test_start_virtual_display_custom_settings(self, mock_popen):
        """Test starting virtual display with custom settings."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        manager = DisplayManager()
        success = manager.start_virtual_display(
            display_number=99, screen_size="1920x1080", color_depth=24
        )

        assert success is True
        assert manager.display_number == 99

        # Check that custom settings were used in command
        call_args = mock_popen.call_args[0][0]
        assert ":99" in call_args
        assert "1920x1080x24" in call_args

    def test_stop_virtual_display(self):
        """Test stopping virtual display."""
        mock_process = Mock()

        manager = DisplayManager()
        manager.xvfb_process = mock_process
        manager.display_number = 99

        manager.stop_virtual_display()

        mock_process.terminate.assert_called_once()
        assert manager.xvfb_process is None
        assert manager.display_number is None

    def test_stop_virtual_display_force_kill(self):
        """Test force killing virtual display process."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Still running after terminate

        manager = DisplayManager()
        manager.xvfb_process = mock_process

        with patch("time.sleep"):  # Speed up the test
            manager.stop_virtual_display()

        mock_process.terminate.assert_called()
        mock_process.kill.assert_called()

    def test_get_display_environment_variables(self):
        """Test getting display environment variables."""
        manager = DisplayManager()
        manager.display_number = 99

        env_vars = manager.get_display_environment_variables()

        assert env_vars["DISPLAY"] == ":99"
        assert "XAUTHORITY" in env_vars

    def test_get_display_environment_variables_no_display(self):
        """Test getting environment variables when no display is active."""
        manager = DisplayManager()

        env_vars = manager.get_display_environment_variables()

        assert env_vars == {}

    @patch("subprocess.run")
    def test_is_display_available(self, mock_run):
        """Test checking if display is available."""
        mock_run.return_value.returncode = 0

        manager = DisplayManager()
        manager.display_number = 99

        available = manager.is_display_available()

        assert available is True

    @patch("subprocess.run")
    def test_is_display_available_not_running(self, mock_run):
        """Test checking display availability when not running."""
        mock_run.return_value.returncode = 1

        manager = DisplayManager()
        manager.display_number = 99

        available = manager.is_display_available()

        assert available is False

    def test_setup_environment_headless(self):
        """Test setting up headless environment."""
        requirements = {"headless": True, "display_required": True}

        manager = DisplayManager()

        with patch.object(manager, "start_virtual_display", return_value=True):
            success = manager.setup_environment(requirements)
            assert success is True

    def test_setup_environment_no_display_required(self):
        """Test environment setup when display is not required."""
        requirements = {"display_required": False}

        manager = DisplayManager()
        success = manager.setup_environment(requirements)

        assert success is True

    def test_setup_environment_display_start_failure(self):
        """Test environment setup when display start fails."""
        requirements = {"headless": True, "display_required": True}

        manager = DisplayManager()

        with patch.object(manager, "start_virtual_display", return_value=False):
            success = manager.setup_environment(requirements)
            assert success is False

    def test_cleanup_environment(self):
        """Test display environment cleanup."""
        mock_process = Mock()

        manager = DisplayManager()
        manager.xvfb_process = mock_process
        manager.display_number = 99

        manager.cleanup_environment()

        mock_process.terminate.assert_called_once()
        assert manager.xvfb_process is None
        assert manager.display_number is None

    def test_is_environment_ready(self):
        """Test checking if display environment is ready."""
        manager = DisplayManager()

        # Without display
        assert manager.is_environment_ready() is False

        # With display
        manager.display_number = 99
        with patch.object(manager, "is_display_available", return_value=True):
            assert manager.is_environment_ready() is True


class TestEnvironmentManagerIntegration:
    """Integration tests for environment managers."""

    def test_all_managers_implement_interface(self):
        """Test that all managers implement the interface correctly."""
        managers = [PythonManager(), QtManager(), DisplayManager()]

        for manager in managers:
            # Test required methods exist
            assert callable(getattr(manager, "setup_environment"))
            assert callable(getattr(manager, "cleanup_environment"))
            assert callable(getattr(manager, "is_environment_ready"))

    def test_combined_environment_setup(self, temp_dir):
        """Test setting up combined environment with all managers."""
        python_manager = PythonManager()
        qt_manager = QtManager()
        display_manager = DisplayManager()

        requirements = {
            "python_version": "3.10",
            "virtual_env": True,
            "venv_path": os.path.join(temp_dir, "test_venv"),
            "qt_required": True,
            "headless": True,
            "display_required": True,
        }

        with (
            patch.object(python_manager, "setup_environment", return_value=True),
            patch.object(qt_manager, "setup_environment", return_value=True),
            patch.object(display_manager, "setup_environment", return_value=True),
        ):

            # Setup all environments
            python_success = python_manager.setup_environment(requirements)
            qt_success = qt_manager.setup_environment(requirements)
            display_success = display_manager.setup_environment(requirements)

            assert python_success is True
            assert qt_success is True
            assert display_success is True

    def test_environment_cleanup_order(self):
        """Test proper cleanup order for all managers."""
        python_manager = PythonManager()
        qt_manager = QtManager()
        display_manager = DisplayManager()

        # Setup some state
        python_manager.active_venv = "/tmp/test_venv"
        qt_manager.qt_env_vars = {"QT_QPA_PLATFORM": "offscreen"}
        display_manager.display_number = 99
        display_manager.xvfb_process = Mock()

        # Cleanup in reverse order (display -> qt -> python)
        display_manager.cleanup_environment()
        qt_manager.cleanup_environment()
        python_manager.cleanup_environment()

        # Verify cleanup
        assert python_manager.active_venv is None
        assert qt_manager.qt_env_vars == {}
        assert display_manager.display_number is None

    def test_environment_readiness_check(self):
        """Test checking readiness of all environment managers."""
        python_manager = PythonManager()
        qt_manager = QtManager()
        display_manager = DisplayManager()

        # Initially not ready
        assert python_manager.is_environment_ready() is False
        assert qt_manager.is_environment_ready() is False
        assert display_manager.is_environment_ready() is False

        # Set up minimal state for readiness
        python_manager.current_version = "3.10.5"
        qt_manager.available_qt = "PyQt5"
        display_manager.display_number = 99

        with patch.object(display_manager, "is_display_available", return_value=True):
            assert python_manager.is_environment_ready() is True
            assert qt_manager.is_environment_ready() is True
            assert display_manager.is_environment_ready() is True
