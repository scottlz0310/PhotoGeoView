# Contributing to CI Simulation Tool

## Overview

We welcome contributions to the CI Simulation Tool! This document provides guidelines for contributing code, documentation, bug reports, and feature requests.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Code Style Guidelines](#code-style-guidelines)
4. [Testing Requirements](#testing-requirements)
5. [Submission Process](#submission-process)
6. [Code Review Process](#code-review-process)
7. [Documentation Guidelines](#documentation-guidelines)
8. [Issue Reporting](#issue-reporting)
9. [Feature Requests](#feature-requests)
10. [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.10+** installed
- **Git** configured with your name and email
- **Basic understanding** of the CI Simulation Tool architecture
- **Familiarity** with the project's coding standards

### First-Time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/PhotoGeoView.git
   cd PhotoGeoView
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-repo/PhotoGeoView.git
   ```
4. **Create development environment**:
   ```bash
   python -m venv ci-dev-env
   source ci-dev-env/bin/activate  # Linux/macOS
   # or
   ci-dev-env\Scripts\activate     # Windo

5. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```
6. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Development Environment

### Required Tools

Install these tools for development:

```bash
# Core development tools
pip install black isort flake8 mypy pytest pytest-cov

# Documentation tools
pip install sphinx sphinx-rtd-theme myst-parser

# Development utilities
pip install pre-commit tox ipython
```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python
- Black Formatter
- isort
- Pylance
- GitLens

**Settings (.vscode/settings.json):**
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm

Configure:
- Code style: Black (88 characters)
- Import optimization: isort
- Type checking: mypy
- Test runner: pytest

### Environment Variables

Set these for development:

```bash
export CI_LOG_LEVEL=DEBUG
export CI_CONFIG_PATH=tools/ci/ci-config.yml
export PYTHONPATH="${PYTHONPATH}:$(pwd)/tools/ci"
```

## Code Style Guidelines

### Python Style

We follow **PEP 8** with these specific requirements:

#### Formatting
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **String quotes**: Double quotes preferred
- **Trailing commas**: Required in multi-line structures

#### Code Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Third-party imports
import yaml
import pytest

# Local imports
from interfaces import CheckerInterface
from models import CheckResult, CheckStatus
from utils import run_command
```

#### Naming Conventions
- **Classes**: PascalCase (`CheckerInterface`)
- **Functions/Methods**: snake_case (`run_check`)
- **Variables**: snake_case (`check_result`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`)
- **Private members**: Leading underscore (`_internal_method`)

#### Type Hints
Type hints are **required** for all public APIs:

```python
def run_check(
    self,
    config: Dict[str, Any],
    timeout: Optional[int] = None
) -> CheckResult:
    """Run the check with given configuration."""
    pass
```

#### Docstrings
Use **Google-style docstrings**:

```python
def process_files(
    files: List[Path],
    config: Dict[str, Any]
) -> List[CheckResult]:
    """
    Process a list of files with the given configuration.

    Args:
        files: List of file paths to process
        config: Configuration dictionary

    Returns:
        List of check results for each file

    Raises:
        ValueError: If files list is empty
        ConfigurationError: If config is invalid

    Example:
        >>> files = [Path('test.py')]
        >>> config = {'timeout': 60}
        >>> results = process_files(files, config)
        >>> len(results)
        1
    """
    if not files:
        raise ValueError("Files list cannot be empty")

    # Implementation here
    pass
```

### Configuration Files

#### YAML Style
```yaml
# Use 2-space indentation
project:
  name: "PhotoGeoView"
  type: "qt_application"

# Group related settings
checks:
  code_quality:
    enabled: true
    timeout: 300

  test_runner:
    enabled: true
    coverage: true

# Use descriptive comments
execution:
  max_parallel: 4  # Adjust based on system resources
  timeout: 1800    # 30 minutes maximum
```

#### JSON Style
```json
{
  "project": {
    "name": "PhotoGeoView",
    "type": "qt_application"
  },
  "checks": {
    "code_quality": {
      "enabled": true,
      "timeout": 300
    }
  }
}
```

## Testing Requirements

### Test Coverage

- **Minimum coverage**: 80% for new code
- **Critical paths**: 95% coverage required
- **Public APIs**: 100% coverage required

### Test Types

#### Unit Tests
Test individual components in isolation:

```python
import pytest
from unittest.mock import Mock, patch

from checkers.code_quality import CodeQualityChecker
from models import CheckStatus


class TestCodeQualityChecker:
    @pytest.fixture
    def checker(self):
        config = {'timeout': 60}
        return CodeQualityChecker(config)

    def test_is_available_with_tools(self, checker):
        with patch('utils.is_tool_available', return_value=True):
            assert checker.is_available()

    def test_run_check_success(self, checker):
        with patch.object(checker, '_run_black', return_value=True):
            result = checker.run_check()
            assert result.status == CheckStatus.SUCCESS
```

#### Integration Tests
Test component interactions:

```python
import pytest
from pathlib import Path

from simulator import CISimulator


class TestCISimulatorIntegration:
    @pytest.fixture
    def temp_project(self, tmp_path):
        # Create test project structure
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "pyproject.toml").write_text("[tool.black]\nline-length = 88")
        return tmp_path

    def test_full_simulation_run(self, temp_project):
        simulator = CISimulator()
        # Change to temp directory and run simulation
        # Assert results
```

#### Performance Tests
Test performance characteristics:

```python
import pytest

def test_check_performance(benchmark):
    def run_check():
        # Check implementation
        pass

    result = benchmark(run_check)
    # Assert performance requirements
```

### Test Organization

```
tools/ci/tests/
├── unit/
│   ├── test_models.py
│   ├── test_config_manager.py
│   └── checkers/
│       ├── test_code_quality.py
│       └── test_security_scanner.py
├── integration/
│   ├── test_full_simulation.py
│   └── test_git_hooks.py
├── performance/
│   └── test_benchmarks.py
└── fixtures/
    ├── sample_configs/
    └── test_projects/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tools/ci --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m performance

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tools/ci/tests/unit/test_config_manager.py -v
```

## Submission Process

### Branch Naming

Use descriptive branch names:

- **Features**: `feature/add-custom-checker`
- **Bug fixes**: `fix/handle-timeout-errors`
- **Documentation**: `docs/update-api-reference`
- **Refactoring**: `refactor/simplify-orchestrator`
- **Tests**: `test/add-integration-tests`

### Commit Messages

Follow the **Conventional Commits** specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**
```bash
feat(checkers): add custom security scanner with bandit integration

- Implement SecurityScanner class with bandit support
- Add configuration options for severity levels
- Include comprehensive test coverage
- Update documentation with usage examples

Closes #123

fix(orchestrator): handle timeout errors gracefully

- Add proper timeout handling in check execution
- Return appropriate error status for timeouts
- Include timeout information in check results
- Add tests for timeout scenarios

docs(api): update checker interface documentation

- Add missing method documentation
- Include usage examples
- Fix typos in docstrings
- Update API reference
```

### Pull Request Process

1. **Create feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make changes** following code style guidelines

3. **Add tests** for new functionality

4. **Update documentation** as needed

5. **Run full test suite**:
   ```bash
   pytest --cov=tools/ci
   black tools/ci/
   isort tools/ci/
   flake8 tools/ci/
   mypy tools/ci/
   ```

6. **Commit changes** with descriptive messages

7. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

8. **Create pull request** on GitHub

### Pull Request Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Performance tests added/updated (if applicable)
- [ ] All tests pass locally
- [ ] Manual testing completed

## Documentation
- [ ] Code is self-documenting with clear variable names and comments
- [ ] Docstrings added/updated for public APIs
- [ ] User documentation updated (if applicable)
- [ ] API documentation updated (if applicable)

## Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation made
- [ ] No new warnings introduced
- [ ] All CI checks pass

## Related Issues
Closes #(issue number)

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Additional Notes
Any additional information that reviewers should know.
```

## Code Review Process

### Review Criteria

Reviewers will check for:

1. **Functionality**: Does the code work as intended?
2. **Code Quality**: Is the code clean, readable, and maintainable?
3. **Testing**: Are there adequate tests with good coverage?
4. **Documentation**: Is the code properly documented?
5. **Performance**: Are there any performance implications?
6. **Security**: Are there any security concerns?
7. **Compatibility**: Does it work across supported platforms?

### Review Timeline

- **Initial review**: Within 2-3 business days
- **Follow-up reviews**: Within 1-2 business days
- **Final approval**: After all feedback is addressed

### Addressing Feedback

1. **Read feedback carefully** and ask for clarification if needed
2. **Make requested changes** in separate commits
3. **Respond to comments** explaining your changes
4. **Request re-review** when ready

### Review Checklist

**For Contributors:**
- [ ] All CI checks pass
- [ ] Code follows style guidelines
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)

**For Reviewers:**
- [ ] Code functionality verified
- [ ] Code quality meets standards
- [ ] Test coverage is adequate
- [ ] Documentation is clear and complete
- [ ] No security or performance issues
- [ ] Backward compatibility maintained

## Documentation Guidelines

### Types of Documentation

1. **Code Documentation**: Docstrings and comments
2. **User Documentation**: Guides and tutorials
3. **API Documentation**: Reference material
4. **Developer Documentation**: Architecture and contribution guides

### Writing Style

- **Clear and concise**: Use simple, direct language
- **Consistent terminology**: Use the same terms throughout
- **Examples included**: Provide practical examples
- **Up-to-date**: Keep documentation current with code changes

### Documentation Structure

```markdown
# Title

## Overview
Brief description of the topic.

## Prerequisites
What users need before starting.

## Step-by-Step Instructions
1. First step
2. Second step
3. Third step

## Examples
Practical examples with code snippets.

## Troubleshooting
Common issues and solutions.

## See Also
Links to related documentation.
```

### Code Examples

Include working code examples:

```python
# Good example with context
from ci_simulator import CISimulator

# Create simulator instance
simulator = CISimulator('config.yml')

# Run specific checks
result = simulator.run(['code_quality', 'test_runner'])

# Check results
if result.is_successful:
    print("All checks passed!")
else:
    print(f"Failed checks: {result.failed_checks}")
```

## Issue Reporting

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for known solutions
3. **Try latest version** to see if issue is fixed
4. **Gather relevant information** about your environment

### Issue Template

```markdown
## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Environment
- OS: [e.g. Ubuntu 20.04, Windows 10, macOS 12]
- Python Version: [e.g. 3.10.5]
- CI Tool Version: [e.g. 1.0.0]
- Configuration: [attach relevant config files]

## Error Messages
```
Paste any error messages here
```

## Additional Context
Add any other context about the problem here.

## Possible Solution
If you have ideas about how to fix the issue, describe them here.
```

### Issue Labels

We use these labels to categorize issues:

- **bug**: Something isn't working
- **enhancement**: New feature or request
- **documentation**: Improvements or additions to documentation
- **good first issue**: Good for newcomers
- **help wanted**: Extra attention is needed
- **question**: Further information is requested
- **wontfix**: This will not be worked on

## Feature Requests

### Before Requesting

1. **Check existing requests** to avoid duplicates
2. **Consider the scope** - is it aligned with project goals?
3. **Think about implementation** - how would it work?
4. **Consider alternatives** - are there existing solutions?

### Feature Request Template

```markdown
## Feature Description
A clear and concise description of the feature you'd like to see.

## Problem Statement
What problem does this feature solve? What use case does it address?

## Proposed Solution
Describe how you envision this feature working.

## Alternative Solutions
Describe any alternative solutions or features you've considered.

## Implementation Ideas
If you have ideas about how to implement this, describe them here.

## Additional Context
Add any other context, mockups, or examples about the feature request here.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- **Be respectful** and considerate in all interactions
- **Be collaborative** and help others learn and grow
- **Be patient** with newcomers and those learning
- **Be constructive** in feedback and criticism
- **Be inclusive** and welcoming to all backgrounds and experience levels

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Request Comments**: Code review discussions
- **Documentation**: Comprehensive guides and references

### Getting Help

If you need help:

1. **Check the documentation** first
2. **Search existing issues** and discussions
3. **Ask specific questions** with relevant context
4. **Provide examples** of what you're trying to do
5. **Be patient** - maintainers are volunteers

### Recognition

We recognize contributors through:

- **Contributor list** in the README
- **Release notes** mentioning significant contributions
- **GitHub achievements** and badges
- **Community highlights** for exceptional contributions

## Conclusion

Thank you for contributing to the CI Simulation Tool! Your contributions help make the tool better for everyone. If you have questions about these guidelines or need help getting started, please don't hesitate to ask.

Remember:
- **Start small** with your first contribution
- **Ask questions** when you're unsure
- **Be patient** with the review process
- **Learn from feedback** and improve
- **Help others** when you can

Happy contributing! 🚀
