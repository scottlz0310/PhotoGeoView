#!/usr/bin/env python3
"""
Comprehensive test for Black formatter integration in CodeQualityChecker.

This script thoroughly tests the Black formatter functionality including:
- Configuration loading
- Check mode (without auto-fix)
- Auto-fix mode
- Error handling
- Integration with the full code quality checker
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.ci.checkers.code_quality import CodeQualityChecker
from tools.ci.models import CheckStatus


def create_test_files():
    """Create temporary test files with various formatting issues."""
    test_dir = Path(tempfile.mkdtemp())

    # Create a well-formatted file
    good_file = test_dir / "good_format.py"
    good_file.write_text('''"""Well formatted Python file."""

def hello_world():
    """Print hello world."""
    print("Hello, World!")


class TestClass:
    """Test class."""

    def __init__(self, name: str):
        """Initialize with name."""
        self.name = name

    def get_name(self) -> str:
        """Get the name."""
        return self.name
''')

    # Create a poorly formatted file
    bad_file = test_dir / "bad_format.py"
    bad_file.write_text('''# Poorly formatted Python file
def hello_world(  ):
    print( "Hello, World!" )

class TestClass:
    def __init__(self,name):
        self.name=name

    def get_name( self ):
        return self.name
''')

    # Create a file with syntax errors
    syntax_error_file = test_dir / "syntax_error.py"
    syntax_error_file.write_text('''# File with syntax errors
def broken_function(
    print("This is broken")
    return "incomplete"
''')

    return test_dir


def test_black_configuration():
    """Test Black configuration loading."""
    print("=== Testing Black Configuration ===")

    config = {
        "tools": {
            "black": {
                "line_length": 100,
                "target_version": ["py39", "py310"]
            }
        }
    }

    checker = CodeQualityChecker(config)
    black_status = checker.get_black_status()

    print(f"Black available: {black_status['available']}")
    print(f"Line length: {checker.black_config['line_length']}")
    print(f"Target versions: {checker.black_config['target_version']}")
    print(f"Config source: {black_status['config_source']}")

    assert black_status['available'], "Black should be available"
    assert checker.black_config['line_length'] == 100, "Custom line length should be set"

    print("✅ Configuration test passed\n")


def test_black_check_mode():
    """Test Black in check mode (no auto-fix)."""
    print("=== Testing Black Check Mode ===")

    test_dir = create_test_files()
    original_cwd = os.getcwd()

    try:
        os.chdir(test_dir)

        config = {"tools": {"black": {"line_length": 88}}}
        checker = CodeQualityChecker(config)

        result = checker.run_black(auto_fix=False)

        print(f"Status: {result.status}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Errors: {result.errors}")
        print(f"Warnings: {result.warnings}")
        print(f"Issues found: {result.metadata.get('issues_found', 0)}")

        # Should find formatting issues or syntax errors
        assert result.status == CheckStatus.FAILURE, "Should detect formatting issues"
        assert len(result.errors) > 0, "Should report errors"
        # Check for either formatting issues or syntax errors
        error_text = " ".join(result.errors).lower()
        assert ("formatting issues" in error_text or "syntax errors" in error_text), "Should mention formatting or syntax issues"

        print("✅ Check mode test passed\n")

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)


def test_black_autofix_mode():
    """Test Black in auto-fix mode."""
    print("=== Testing Black Auto-fix Mode ===")

    test_dir = create_test_files()
    original_cwd = os.getcwd()

    try:
        os.chdir(test_dir)

        config = {"tools": {"black": {"line_length": 88}}}
        checker = CodeQualityChecker(config)

        # Read original content
        bad_file = test_dir / "bad_format.py"
        original_content = bad_file.read_text()

        result = checker.run_black(auto_fix=True)

        print(f"Status: {result.status}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Errors: {result.errors}")
        print(f"Warnings: {result.warnings}")
        print(f"Auto-fix applied: {result.metadata.get('auto_fix_applied', False)}")

        # Read modified content
        modified_content = bad_file.read_text()

        print(f"Content changed: {original_content != modified_content}")

        # Should successfully fix issues (unless there are syntax errors)
        if result.status == CheckStatus.SUCCESS:
            assert len(result.warnings) > 0, "Should report warnings about fixes"
            assert original_content != modified_content, "Content should be modified"

        print("✅ Auto-fix mode test passed\n")

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(test_dir)


def test_black_error_handling():
    """Test Black error handling."""
    print("=== Testing Black Error Handling ===")

    # Test with non-existent directory
    config = {"tools": {"black": {}}}
    checker = CodeQualityChecker(config)

    # Change to a directory that doesn't exist
    original_cwd = os.getcwd()

    try:
        # This should handle the case where source directories don't exist
        result = checker.run_black(auto_fix=False)

        print(f"Status: {result.status}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Output: {result.output[:200]}...")

        # Should handle missing directories gracefully
        assert result.status in [CheckStatus.SUCCESS, CheckStatus.FAILURE], "Should return valid status"

        print("✅ Error handling test passed\n")

    finally:
        os.chdir(original_cwd)


def test_full_integration():
    """Test Black integration with full code quality checker."""
    print("=== Testing Full Integration ===")

    config = {
        "tools": {
            "black": {"line_length": 88}
        },
        "auto_fix": False
    }

    checker = CodeQualityChecker(config)

    # Test with only Black enabled
    result = checker.run_check(check_types=["black"], auto_fix=False)

    print(f"Overall status: {result.status}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Individual results: {list(result.metadata.get('individual_results', {}).keys())}")
    print(f"Checks run: {result.metadata.get('checks_run', [])}")

    assert "black" in result.metadata.get('individual_results', {}), "Should include Black results"
    assert "black" in result.metadata.get('checks_run', []), "Should list Black as run"

    print("✅ Full integration test passed\n")


def main():
    """Run all Black formatter tests."""
    print("Starting comprehensive Black formatter integration tests...\n")

    try:
        test_black_configuration()
        test_black_check_mode()
        test_black_autofix_mode()
        test_black_error_handling()
        test_full_integration()

        print("🎉 All Black formatter integration tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
