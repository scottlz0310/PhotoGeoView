"""
Ufunctions for CI Simulation Tool

This module provides common utility functions used across
different components of the CI simulation system.
"""

import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def ensure_directory_exists(path: str) -> Path:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        path: Directory path to create

    Returns:
        Path object for the created directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path object pointing to the project root
    """
    current_path = Path(__file__).resolve()
    # Navigate up from tools/ci/utils.py to project root
    return current_path.parent.parent.parent


def get_python_executable(version: Optional[str] = None) -> Optional[str]:
    """
    Get the path to a Python executable for the specified version.

    Args:
        version: Python version string (e.g., "3.9", "3.10")

    Returns:
        Path to Python executable or None if not found
    """
    if version is None:
        return sys.executable

    # Try common Python executable patterns
    possible_names = [
        f"python{version}",
        f"python{version.replace('.', '')}",
        "python3",
        "python",
    ]

    for name in possible_names:
        executable = shutil.which(name)
        if executable:
            # Verify version matches
            try:
                result = subprocess.run(
                    [executable, "--version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and version in result.stdout:
                    return executable
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                continue

    return None


def run_command(
    command: List[str],
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    capture_output: bool = True,
) -> Tuple[int, str, str]:
    """
    Run a command and return the result.

    Args:
        command: Command and arguments as a list
        cwd: Working directory for the command
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        # Prepare environment to prevent Git hook loops
        env = os.environ.copy()
        if command and command[0] == 'git':
            env['CI_SIMULATION_RUNNING'] = 'true'
            env['SKIP_CI_HOOKS'] = 'true'

        result = subprocess.run(
            command, cwd=cwd, timeout=timeout, capture_output=capture_output,
            text=True, env=env
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except subprocess.SubprocessError as e:
        return -1, "", str(e)


def is_tool_available(tool_name: str) -> bool:
    """
    Check if a command-line tool is available.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if the tool is available in PATH
    """
    return shutil.which(tool_name) is not None


def get_file_list(
    directory: str,
    extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> List[str]:
    """
    Get a list of files in a directory with optional filtering.

    Args:
        directory: Directory to search
        extensions: List of file extensions to include (e.g., ['.py', '.md'])
        exclude_patterns: List of patterns to exclude

    Returns:
        List of file paths
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return []

    files = []
    for file_path in directory_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Check extension filter
        if extensions and file_path.suffix not in extensions:
            continue

        # Check exclude patterns
        if exclude_patterns:
            relative_path = str(file_path.relative_to(directory_path))
            if any(pattern in relative_path for pattern in exclude_patterns):
                continue

        files.append(str(file_path))

    return sorted(files)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        log_file: Path to log file (optional)
        level: Logging level
        format_string: Custom format string

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger = logging.getLogger("ci_simulation")
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        ensure_directory_exists(os.path.dirname(log_file))
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def generate_timestamp(format_string: str = "%Y%m%d_%H%M%S") -> str:
    """
    Generate a timestamp string.

    Args:
        format_string: strftime format string

    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_string)


def safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Safe filename string
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in invalid_chars:
        safe_name = safe_name.replace(char, "_")

    # Remove leading/trailing whitespace and dots
    safe_name = safe_name.strip(" .")

    # Ensure it's not empty
    if not safe_name:
        safe_name = "unnamed"

    return safe_name


def get_git_info() -> Dict[str, str]:
    """
    Get current Git repository information.

    Returns:
        Dictionary with Git information (branch, commit, etc.)
    """
    git_info = {}

    try:
        # Get current branch
        returncode, stdout, _ = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        )
        if returncode == 0:
            git_info["branch"] = stdout.strip()

        # Get current commit hash
        returncode, stdout, _ = run_command(["git", "rev-parse", "HEAD"])
        if returncode == 0:
            git_info["commit"] = stdout.strip()[:8]

        # Get commit message
        returncode, stdout, _ = run_command(["git", "log", "-1", "--pretty=%s"])
        if returncode == 0:
            git_info["message"] = stdout.strip()

        # Check for uncommitted changes
        returncode, stdout, _ = run_command(["git", "status", "--porcelain"])
        if returncode == 0:
            git_info["dirty"] = bool(stdout.strip())

    except Exception:
        # If Git is not available or we're not in a Git repo
        pass

    return git_info
