"""
.gitignore Management for CI/CD Simulation

This module handles .gitignore file management, including detection,
updating, and backup functionality for CI simulation-specific patterns.
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set


class GitignoreManager:
    """
    Manages .gitignore file updates for CI/CD simulation tool.

    Handles detection of existin, addition of CI-specific patterns,
    and backup functionality to prevent data loss.
    """

    # CI simulation specific patterns to add to .gitignore
    CI_SIMULATION_PATTERNS = [
        "# CI/CD Simulation generated files",
        "reports/ci-simulation/",
        ".kiro/ci-history/",
        "temp/ci-simulation/",
        "logs/ci-simulation.log",
        "logs/performance.log",
        "logs/security-scan.log",
        ".coverage",
        "htmlcov/",
        "coverage.xml",
        ".pytest_cache/",
        ".mypy_cache/",
        "*.pyc",
        "__pycache__/",
        ".tox/",
        ".bandit",
        ".safety-policy.json",
        "benchmark_results.json",
        "performance_baseline.json",
        "ci-simulation-*.json",
        "ci-simulation-*.md",
        "*.tmp",
        "*.temp",
        ".ci-temp/",
        "# End CI/CD Simulation patterns",
    ]

    def __init__(self, gitignore_path: str = ".gitignore"):
        """
        Initialize GitignoreManager.

        Args:
            gitignore_path: Path to .gitignore file (default: ".gitignore")
        """
        self.gitignore_path = Path(gitignore_path)
        self.logger = logging.getLogger(__name__)

    def _read_gitignore(self) -> List[str]:
        """
        Read current .gitignore file content.

        Returns:
            List of lines from .gitignore file.
        """
        try:
            if not self.gitignore_path.exists():
                self.logger.info(f".gitignore file not found at {self.gitignore_path}")
                return []
        except (PermissionError, OSError) as e:
            self.logger.warning(
                f"Cannot access .gitignore path {self.gitignore_path}: {e}"
            )
            return []

        try:
            with open(self.gitignore_path, "r", encoding="utf-8") as f:
                return [line.rstrip("\n\r") for line in f.readlines()]
        except Exception as e:
            self.logger.error(f"Failed to read .gitignore: {e}")
            return []

    def _write_gitignore(self, lines: List[str]) -> None:
        """
        Write lines to .gitignore file.

        Args:
            lines: List of lines to write to .gitignore.
        """
        try:
            # Ensure parent directory exists
            self.gitignore_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.gitignore_path, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")

            self.logger.info(f"Updated .gitignore file: {self.gitignore_path}")

        except Exception as e:
            self.logger.error(f"Failed to write .gitignore: {e}")
            raise

    def create_backup(self) -> Optional[str]:
        """
        Create backup of current .gitignore file.

        Returns:
            Path to backup file or None if backup failed.
        """
        if not self.gitignore_path.exists():
            self.logger.info("No .gitignore file to backup")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_path = self.gitignore_path.with_suffix(f".backup_{timestamp}")

        try:
            shutil.copy2(self.gitignore_path, backup_path)
            self.logger.info(f"Created .gitignore backup: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore .gitignore from backup file.

        Args:
            backup_path: Path to backup file.

        Returns:
            True if restore was successful, False otherwise.
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            return False

        try:
            shutil.copy2(backup_file, self.gitignore_path)
            self.logger.info(f"Restored .gitignore from backup: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False

    def detect_existing_patterns(self) -> Set[str]:
        """
        Detect existing patterns in .gitignore file.

        Returns:
            Set of existing patterns (normalized).
        """
        lines = self._read_gitignore()
        patterns = set()

        for line in lines:
            # Skip comments and empty lines
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.add(line)

        return patterns

    def has_ci_simulation_patterns(self) -> bool:
        """
        Check if .gitignore already contains CI simulation patterns.

        Returns:
            True if CI simulation patterns are present.
        """
        existing_patterns = self.detect_existing_patterns()

        # Check for key CI simulation patterns
        ci_patterns = {
            "reports/ci-simulation/",
            ".kiro/ci-history/",
            "temp/ci-simulation/",
        }

        return any(pattern in existing_patterns for pattern in ci_patterns)

    def get_missing_patterns(self) -> List[str]:
        """
        Get CI simulation patterns that are missing from .gitignore.

        Returns:
            List of missing patterns.
        """
        existing_patterns = self.detect_existing_patterns()
        missing_patterns = []

        for pattern in self.CI_SIMULATION_PATTERNS:
            # Skip comments
            if pattern.startswith("#"):
                continue

            pattern = pattern.strip()
            if pattern and pattern not in existing_patterns:
                missing_patterns.append(pattern)

        return missing_patterns

    def add_ci_simulation_patterns(self, create_backup: bool = True) -> bool:
        """
        Add CI simulation patterns to .gitignore file.

        Args:
            create_backup: Whether to create backup before modification.

        Returns:
            True if patterns were added successfully.
        """
        try:
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = self.create_backup()

            # Read current content
            current_lines = self._read_gitignore()

            # Check if CI patterns already exist
            if self.has_ci_simulation_patterns():
                self.logger.info("CI simulation patterns already exist in .gitignore")
                return True

            # Add CI simulation patterns
            updated_lines = current_lines.copy()

            # Add a blank line before CI patterns if file is not empty
            if updated_lines and updated_lines[-1].strip():
                updated_lines.append("")

            # Add CI simulation patterns
            updated_lines.extend(self.CI_SIMULATION_PATTERNS)

            # Write updated content
            self._write_gitignore(updated_lines)

            self.logger.info("Successfully added CI simulation patterns to .gitignore")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add CI simulation patterns: {e}")

            # Try to restore backup if it was created
            if backup_path:
                self.logger.info("Attempting to restore backup...")
                self.restore_backup(backup_path)

            return False

    def remove_ci_simulation_patterns(self, create_backup: bool = True) -> bool:
        """
        Remove CI simulation patterns from .gitignore file.

        Args:
            create_backup: Whether to create backup before modification.

        Returns:
            True if patterns were removed successfully.
        """
        try:
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = self.create_backup()

            # Read current content
            current_lines = self._read_gitignore()

            # Remove CI simulation patterns
            updated_lines = []
            in_ci_section = False

            for line in current_lines:
                if line.strip() == "# CI/CD Simulation generated files":
                    in_ci_section = True
                    continue
                elif line.strip() == "# End CI/CD Simulation patterns":
                    in_ci_section = False
                    continue
                elif not in_ci_section:
                    updated_lines.append(line)

            # Write updated content
            self._write_gitignore(updated_lines)

            self.logger.info(
                "Successfully removed CI simulation patterns from .gitignore"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove CI simulation patterns: {e}")

            # Try to restore backup if it was created
            if backup_path:
                self.logger.info("Attempting to restore backup...")
                self.restore_backup(backup_path)

            return False

    def update_gitignore(self, force: bool = False) -> bool:
        """
        Update .gitignore with CI simulation patterns if needed.

        Args:
            force: Force update even if patterns already exist.

        Returns:
            True if update was successful or not needed.
        """
        if not force and self.has_ci_simulation_patterns():
            self.logger.info("CI simulation patterns already present in .gitignore")
            return True

        return self.add_ci_simulation_patterns()

    def validate_gitignore(self) -> bool:
        """
        Validate .gitignore file format and content.

        Returns:
            True if .gitignore is valid.
        """
        try:
            lines = self._read_gitignore()

            # Basic validation - check if file is readable
            if lines is None:
                return False

            # Check for common issues
            for i, line in enumerate(lines, 1):
                # Check for invalid characters (basic check)
                if "\0" in line:
                    self.logger.warning(f"Invalid null character found at line {i}")
                    return False

            self.logger.info(".gitignore validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to validate .gitignore: {e}")
            return False

    def get_status(self) -> dict:
        """
        Get status information about .gitignore and CI patterns.

        Returns:
            Dictionary with status information.
        """
        return {
            "gitignore_exists": self.gitignore_path.exists(),
            "gitignore_path": str(self.gitignore_path),
            "has_ci_patterns": self.has_ci_simulation_patterns(),
            "missing_patterns": self.get_missing_patterns(),
            "total_lines": len(self._read_gitignore()),
            "is_valid": self.validate_gitignore(),
        }

    def list_backups(self) -> List[str]:
        """
        List available backup files.

        Returns:
            List of backup file paths.
        """
        backup_pattern = f"{self.gitignore_path.stem}.backup_*"
        backup_dir = self.gitignore_path.parent

        backups = []
        for backup_file in backup_dir.glob(backup_pattern):
            if backup_file.is_file():
                backups.append(str(backup_file))

        return sorted(backups, reverse=True)  # Most recent first

    def cleanup_old_backups(self, keep_count: int = 5) -> int:
        """
        Clean up old backup files, keeping only the most recent ones.

        Args:
            keep_count: Number of backup files to keep.

        Returns:
            Number of backup files removed.
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            return 0

        removed_count = 0
        for backup_path in backups[keep_count:]:
            try:
                os.remove(backup_path)
                removed_count += 1
                self.logger.info(f"Removed old backup: {backup_path}")
            except Exception as e:
                self.logger.warning(f"Failed to remove backup {backup_path}: {e}")

        return removed_count
