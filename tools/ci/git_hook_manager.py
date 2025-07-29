"""
Git Hook Manager for CI Simulation Tool

This module provides comprehensive Git hook management functionality,
including installation, configuration, and execution of CI simulation hooks.
"""

import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime


class GitHookManager:
    """
    Manages Git hooks for CI simulation integration.

    Provides functionality to install, configure, and manage Git hooks
    that automatically run CI simulation checks at appropriate times.
    """

    SUPPORTED_HOOKS = {
        'pre-commit': {
            'description': 'Run fast checks before commit',
            'default_checks': ['code_quality'],
            'timeout': 300  # 5 minutes
        },
        'pre-push': {
            'description': 'Run comprehensive checks before push',
            'default_checks': ['code_quality', 'test_runner', 'security_scanner'],
            'timeout': 1800  # 30 minutes
        },
        'commit-msg': {
            'description': 'Validate commit message format',
            'default_checks': [],
            'timeout': 30
        }
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Git hook manager.

        Args:
            config: Configuration dicti
    """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.git_dir = self._find_git_directory()
        self.hooks_dir = self.git_dir / 'hooks' if self.git_dir else None

    def _find_git_directory(self) -> Optional[Path]:
        """
        Find the Git directory for the current repository.

        Returns:
            Path to .git directory or None if not in a Git repository
        """
        current_dir = Path.cwd()

        # Look for .git directory in current and parent directories
        for path in [current_dir] + list(current_dir.parents):
            git_dir = path / '.git'
            if git_dir.exists():
                if git_dir.is_file():
                    # Handle Git worktrees
                    with open(git_dir, 'r') as f:
                        git_dir_content = f.read().strip()
                        if git_dir_content.startswith('gitdir: '):
                            git_dir = Path(git_dir_content[8:])
                return git_dir

        return None

    def is_git_repository(self) -> bool:
        """
        Check if current directory is in a Git repository.

        Returns:
            True if in a Git repository
        """
        return self.git_dir is not None

    def install_hook(self, hook_type: str, checks: Optional[List[str]] = None,
                    force: bool = False) -> bool:
        """
        Install a Git hook for CI simulation.

        Args:
            hook_type: Type of hook to install ('pre-commit', 'pre-push', etc.)
            checks: List of checks to run in the hook (default: hook-specific defaults)
            force: Whether to overwrite existing hooks

        Returns:
            True if hook was installed successfully
        """
        if not self.is_git_repository():
            self.logger.error("Not in a Git repository")
            return False

        if hook_type not in self.SUPPORTED_HOOKS:
            self.logger.error(f"Unsupported hook type: {hook_type}")
            return False

        try:
            # Ensure hooks directory exists
            self.hooks_dir.mkdir(exist_ok=True)

            hook_path = self.hooks_dir / hook_type

            # Check if hook already exists
            if hook_path.exists() and not force:
                self.logger.warning(f"Hook {hook_type} already exists. Use --force to overwrite.")
                return False

            # Backup existing hook if it exists
            if hook_path.exists():
                backup_path = hook_path.with_suffix('.backup')
                hook_path.rename(backup_path)
                self.logger.info(f"Backed up existing hook to {backup_path}")

            # Generate hook script
            hook_script = self._generate_hook_script(hook_type, checks)

            # Write hook script
            with open(hook_path, 'w', encoding='utf-8') as f:
                f.write(hook_script)

            # Make hook executable
            self._make_executable(hook_path)

            # Save hook configuration
            self._save_hook_config(hook_type, checks)

            self.logger.info(f"Successfully installed {hook_type} hook")
            return True

        except Exception as e:
            self.logger.error(f"Failed to install {hook_type} hook: {e}")
            return False

    def uninstall_hook(self, hook_type: str) -> bool:
        """
        Uninstall a Git hook.

        Args:
            hook_type: Type of hook to uninstall

        Returns:
            True if hook was uninstalled successfully
        """
        if not self.is_git_repository():
            self.logger.error("Not in a Git repository")
            return False

        try:
            hook_path = self.hooks_dir / hook_type

            if not hook_path.exists():
                self.logger.warning(f"Hook {hook_type} does not exist")
                return True

            # Check if it's our hook
            if not self._is_our_hook(hook_path):
                self.logger.warning(f"Hook {hook_type} was not created by CI Simulator")
                return False

            # Remove hook
            hook_path.unlink()

            # Restore backup if it exists
            backup_path = hook_path.with_suffix('.backup')
            if backup_path.exists():
                backup_path.rename(hook_path)
                self.logger.info(f"Restored backup hook from {backup_path}")

            # Remove hook configuration
            self._remove_hook_config(hook_type)

            self.logger.info(f"Successfully uninstalled {hook_type} hook")
            return True

        except Exception as e:
            self.logger.error(f"Failed to uninstall {hook_type} hook: {e}")
            return False

    def list_hooks(self) -> Dict[str, Dict[str, Any]]:
        """
        List all installed hooks and their status.

        Returns:
            Dictionary with hook information
        """
        hooks_info = {}

        if not self.is_git_repository():
            return hooks_info

        for hook_type in self.SUPPORTED_HOOKS:
            hook_path = self.hooks_dir / hook_type

            hooks_info[hook_type] = {
                'installed': hook_path.exists(),
                'is_ours': self._is_our_hook(hook_path) if hook_path.exists() else False,
                'executable': self._is_executable(hook_path) if hook_path.exists() else False,
                'description': self.SUPPORTED_HOOKS[hook_type]['description'],
                'config': self._load_hook_config(hook_type)
            }

        return hooks_info

    def test_hook(self, hook_type: str) -> bool:
        """
        Test a Git hook by running it manually.

        Args:
            hook_type: Type of hook to test

        Returns:
            True if hook executed successfully
        """
        if not self.is_git_repository():
            self.logger.error("Not in a Git repository")
            return False

        hook_path = self.hooks_dir / hook_type

        if not hook_path.exists():
            self.logger.error(f"Hook {hook_type} is not installed")
            return False

        try:
            self.logger.info(f"Testing {hook_type} hook...")

            # Run the hook
            result = subprocess.run(
                [str(hook_path)],
                capture_output=True,
                text=True,
                timeout=self.SUPPORTED_HOOKS[hook_type]['timeout']
            )

            if result.returncode == 0:
                self.logger.info(f"Hook {hook_type} test passed")
                if result.stdout:
                    self.logger.debug(f"Hook output: {result.stdout}")
                return True
            else:
                self.logger.error(f"Hook {hook_type} test failed with exit code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Hook error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Hook {hook_type} test timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to test {hook_type} hook: {e}")
            return False

    def _generate_hook_script(self, hook_type: str, checks: Optional[List[str]] = None) -> str:
        """
        Generate Git hook script content.

        Args:
            hook_type: Type of hook
            checks: List of checks to run

        Returns:
            Hook script content
        """
        if checks is None:
            checks = self.SUPPORTED_HOOKS[hook_type]['default_checks']

        python_executable = sys.executable
        simulator_path = Path(__file__).parent / 'simulator.py'
        simulator_path = simulator_path.resolve()

        # Get hook configuration
        hook_config = self.SUPPORTED_HOOKS[hook_type]
        timeout = hook_config['timeout']

        # Build check arguments
        check_args = ' '.join(checks) if checks else ''

        # Generate script based on hook type
        if hook_type == 'pre-commit':
            return f"""#!/bin/sh
# PhotoGeoView CI Simulation Pre-commit Hook
# Generated by CI Simulator on {datetime.now().isoformat()}
# Checks: {', '.join(checks) if checks else 'none'}

echo "🔍 Running CI simulation before commit..."

# Get list of staged files for targeted checking
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|yml|yaml|json|md)$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "ℹ️  No relevant files staged for commit. Skipping CI checks."
    exit 0
fi

echo "📁 Checking staged files: $(echo $STAGED_FILES | wc -w) files"

# Run CI simulation with timeout
timeout {timeout} "{python_executable}" "{simulator_path}" run {check_args} --quiet

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ CI simulation timed out after {timeout} seconds"
    echo "💡 Consider running checks manually: python {simulator_path} run"
    exit 1
elif [ $EXIT_CODE -ne 0 ]; then
    echo "❌ CI simulation failed. Commit aborted."
    echo "💡 Run 'python {simulator_path} run' for detailed results"
    echo "💡 Use 'git commit --no-verify' to bypass this check (not recommended)"
    exit 1
fi

echo "✅ CI simulation passed. Proceeding with commit."
exit 0
"""

        elif hook_type == 'pre-push':
            return f"""#!/bin/sh
# PhotoGeoView CI Simulation Pre-push Hook
# Generated by CI Simulator on {datetime.now().isoformat()}
# Checks: {', '.join(checks) if checks else 'none'}

echo "🚀 Running comprehensive CI simulation before push..."

# Get information about what's being pushed
remote="$1"
url="$2"

# Read from stdin to get the refs being pushed
while read local_ref local_sha remote_ref remote_sha; do
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        # Branch is being deleted, skip checks
        continue
    fi

    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch, check all commits
        range="$local_sha"
    else
        # Existing branch, check new commits
        range="$remote_sha..$local_sha"
    fi

    # Get list of changed files in the push
    CHANGED_FILES=$(git diff --name-only "$range" | grep -E '\\.(py|yml|yaml|json|md)$' || true)

    if [ -n "$CHANGED_FILES" ]; then
        echo "📁 Checking changes in push: $(echo $CHANGED_FILES | wc -w) files"
        break
    fi
done

# Run comprehensive CI simulation with timeout
echo "⏳ Running full CI simulation (timeout: {timeout}s)..."
timeout {timeout} "{python_executable}" "{simulator_path}" run {check_args} --quiet

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ CI simulation timed out after {timeout} seconds"
    echo "💡 Consider running checks manually: python {simulator_path} run"
    exit 1
elif [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Full CI simulation failed. Push aborted."
    echo "💡 Run 'python {simulator_path} run' for detailed results"
    echo "💡 Use 'git push --no-verify' to bypass this check (not recommended)"
    exit 1
fi

echo "✅ Full CI simulation passed. Proceeding with push."
exit 0
"""

        elif hook_type == 'commit-msg':
            return f"""#!/bin/sh
# PhotoGeoView CI Simulation Commit Message Hook
# Generated by CI Simulator on {datetime.now().isoformat()}

commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\\(.+\\))?: .{{1,50}}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Invalid commit message format!"
    echo ""
    echo "Commit message should follow the format:"
    echo "  type(scope): description"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, test, chore"
    echo "Example: feat(auth): add user authentication"
    echo "Example: fix: resolve memory leak in image processing"
    echo ""
    exit 1
fi

echo "✅ Commit message format is valid."
exit 0
"""

        else:
            raise ValueError(f"Unsupported hook type: {hook_type}")

    def _make_executable(self, file_path: Path) -> None:
        """Make a file executable."""
        if os.name != 'nt':  # Unix-like systems
            current_permissions = file_path.stat().st_mode
            file_path.chmod(current_permissions | stat.S_IEXEC)
        # On Windows, files are executable by default

    def _is_executable(self, file_path: Path) -> bool:
        """Check if a file is executable."""
        if not file_path.exists():
            return False

        if os.name == 'nt':  # Windows
            return True  # Files are executable by default on Windows
        else:  # Unix-like systems
            return os.access(file_path, os.X_OK)

    def _is_our_hook(self, hook_path: Path) -> bool:
        """Check if a hook was created by CI Simulator."""
        if not hook_path.exists():
            return False

        try:
            with open(hook_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'PhotoGeoView CI Simulation' in content and 'Generated by CI Simulator' in content
        except Exception:
            return False

    def _save_hook_config(self, hook_type: str, checks: Optional[List[str]]) -> None:
        """Save hook configuration."""
        try:
            config_dir = Path('.kiro/ci-hooks')
            config_dir.mkdir(parents=True, exist_ok=True)

            config_file = config_dir / f'{hook_type}.json'

            config = {
                'hook_type': hook_type,
                'checks': checks or self.SUPPORTED_HOOKS[hook_type]['default_checks'],
                'installed_at': datetime.now().isoformat(),
                'timeout': self.SUPPORTED_HOOKS[hook_type]['timeout']
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Failed to save hook config: {e}")

    def _load_hook_config(self, hook_type: str) -> Optional[Dict[str, Any]]:
        """Load hook configuration."""
        try:
            config_file = Path('.kiro/ci-hooks') / f'{hook_type}.json'

            if not config_file.exists():
                return None

            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            self.logger.warning(f"Failed to load hook config: {e}")
            return None

    def _remove_hook_config(self, hook_type: str) -> None:
        """Remove hook configuration."""
        try:
            config_file = Path('.kiro/ci-hooks') / f'{hook_type}.json'

            if config_file.exists():
                config_file.unlink()

        except Exception as e:
            self.logger.warning(f"Failed to remove hook config: {e}")

    def get_hook_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of Git hooks.

        Returns:
            Dictionary with hook status information
        """
        status = {
            'git_repository': self.is_git_repository(),
            'git_dir': str(self.git_dir) if self.git_dir else None,
            'hooks_dir': str(self.hooks_dir) if self.hooks_dir else None,
            'hooks': {}
        }

        if self.is_git_repository():
            status['hooks'] = self.list_hooks()

        return status

    def install_recommended_hooks(self) -> Dict[str, bool]:
        """
        Install recommended hooks for the project.

        Returns:
            Dictionary mapping hook types to installation success
        """
        recommended_hooks = {
            'pre-commit': ['code_quality'],
            'pre-push': ['code_quality', 'test_runner', 'security_scanner']
        }

        results = {}

        for hook_type, checks in recommended_hooks.items():
            self.logger.info(f"Installing recommended {hook_type} hook...")
            results[hook_type] = self.install_hook(hook_type, checks, force=False)

        return results

    def update_hook(self, hook_type: str, checks: Optional[List[str]] = None) -> bool:
        """
        Update an existing hook with new configuration.

        Args:
            hook_type: Type of hook to update
            checks: New list of checks to run

        Returns:
            True if hook was updated successfully
        """
        if not self.is_git_repository():
            self.logger.error("Not in a Git repository")
            return False

        hook_path = self.hooks_dir / hook_type

        if not hook_path.exists():
            self.logger.error(f"Hook {hook_type} is not installed")
            return False

        if not self._is_our_hook(hook_path):
            self.logger.error(f"Hook {hook_type} was not created by CI Simulator")
            return False

        # Update is essentially a forced reinstall
        return self.install_hook(hook_type, checks, force=True)

    def validate_hooks(self) -> Dict[str, List[str]]:
        """
        Validate all installed hooks.

        Returns:
            Dictionary mapping hook types to validation errors
        """
        validation_results = {}

        if not self.is_git_repository():
            return {'general': ['Not in a Git repository']}

        hooks_info = self.list_hooks()

        for hook_type, info in hooks_info.items():
            errors = []

            if info['installed']:
                if not info['is_ours']:
                    errors.append('Hook was not created by CI Simulator')

                if not info['executable']:
                    errors.append('Hook is not executable')

                # Test hook execution
                if not self.test_hook(hook_type):
                    errors.append('Hook test execution failed')

            validation_results[hook_type] = errors

        return validation_results
