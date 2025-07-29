# CI Simulation Tool - User Guide

## Overview

The CI Simulation Tool is a comprehensive local testing solution that replicates your GitHub Actions CI/CD pipeline before you commit code. It helps you catch errors early, ensuring your commits pass CI checks on the first try.

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Quick Start](#quick-start)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Configuration](#configuration)
6. [Git Hooks Integration](#git-hooks-integration)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)

## Installation and Setup

### Prerequisites

Before installing the CI Simulation Tool, ensure you have:

- **Python 3.9 or higher** (Python 3.10+ recommended)
- **Git** installed and configured
- **Virtual environment** (recommended)
- **System dependencies** for your project (Qt, display server, etc.)

### Installation Steps

1. **Navigate to your project directory:**
   ```bash
   cd /path/to/your/project
   ```

2. **Verify the tool is available:**
   ```bash
   python tools/ci/simulator.py --version
   ```

3. **Run initial setup:**
   ```bash
   python tools/ci/simulator.py --setup-hooks
   ```

### System Dependencies

The tool may require additional system packages depending on your project:

#### For Qt-based applications (like PhotoGeoView):
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5 xvfb

# macOS
brew install pyqt5

# Windows
# Qt dependencies are typically handled by pip
```

#### For security scanning:
```bash
pip install safety bandit
```

#### For code quality checks:
```bash
pip install black isort flake8 mypy
```

## Quick Start

### Run All Checks
```bash
python tools/ci/simulator.py run
```

### Run Specific Checks
```bash
python tools/ci/simulator.py run code_quality test_runner
```

### Interactive Mode
```bash
python tools/ci/simulator.py --interactive
```

## Basic Usage

### Command Structure

The basic command structure is:
```bash
python tools/ci/simulator.py [COMMAND] [OPTIONS] [ARGUMENTS]
```

### Available Commands

#### `run` - Execute CI Checks
Run one or more CI checks locally.

```bash
# Run all available checks
python tools/ci/simulator.py run

# Run specific checks
python tools/ci/simulator.py run code_quality security_scanner

# Run all checks except specific ones
python tools/ci/simulator.py run --all --exclude performance_analyzer

# Test multiple Python versions
python tools/ci/simulator.py run --python-versions 3.9 3.10 3.11
```

#### `list` - Show Available Checks
Display all available checks and their status.

```bash
# Simple list
python tools/ci/simulator.py list

# Detailed information
python tools/ci/simulator.py list --detailed

# JSON format
python tools/ci/simulator.py list --format json
```

#### `info` - Check Information
Get detailed information about a specific check.

```bash
python tools/ci/simulator.py info code_quality
```

#### `plan` - Show Execution Plan
Display the execution plan for selected checks.

```bash
# Plan for specific checks
python tools/ci/simulator.py plan code_quality test_runner

# Plan for all checks
python tools/ci/simulator.py plan
```

#### `hook` - Git Hook Management
Manage Git hooks for automatic CI simulation.

```bash
# Install pre-commit hook
python tools/ci/simulator.py hook install pre-commit

# List hook status
python tools/ci/simulator.py hook list

# Setup recommended hooks
python tools/ci/simulator.py hook setup
```

### Check Types

The tool supports several types of checks:

#### Code Quality (`code_quality`)
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Style and syntax checking
- **mypy** - Type checking

#### Test Runner (`test_runner`)
- Unit tests
- Integration tests
- AI compatibility tests
- Demo script validation

#### Security Scanner (`security_scanner`)
- **safety** - Dependency vulnerability scanning
- **bandit** - Code security analysis

#### Performance Analyzer (`performance_analyzer`)
- Benchmark execution
- Performance regression detection
- Memory usage analysis

#### AI Component Tester (`ai_component_tester`)
- Copilot integration tests
- Cursor compatibility tests
- Kiro component validation

## Advanced Features

### Multiple Python Versions

Test your code against multiple Python versions:

```bash
python tools/ci/simulator.py run --python-versions 3.9 3.10 3.11
```

The tool will:
- Detect available Python versions on your system
- Run tests in isolated environments
- Report version-specific issues
- Aggregate results across versions

### Parallel Execution

Control parallel execution for faster results:

```bash
# Limit to 2 parallel tasks
python tools/ci/simulator.py run --parallel 2

# Use all available CPU cores
python tools/ci/simulator.py run --parallel auto
```

### Custom Timeouts

Set timeouts for long-running checks:

```bash
# Global timeout of 5 minutes
python tools/ci/simulator.py run --timeout 300

# Per-check timeout configuration in config file
```

### Report Generation

Generate detailed reports in multiple formats:

```bash
# Markdown report
python tools/ci/simulator.py run --format markdown

# JSON report for automation
python tools/ci/simulator.py run --format json

# Both formats
python tools/ci/simulator.py run --format both

# Custom output directory
python tools/ci/simulator.py run --output-dir ./custom-reports
```

### Selective Execution

Run only the checks you need:

```bash
# Quick code qualit
hon tools/ci/simulator.py run code_quality

# Security-focused run
python tools/ci/simulator.py run security_scanner

# Everything except slow performance tests
python tools/ci/simulator.py run --all --exclude performance_analyzer
```

## Configuration

### Configuration File

Create a configuration file at `tools/ci/ci-config.yml`:

```yaml
# Python versions to test
python_versions:
  - "3.9"
  - "3.10"
  - "3.11"

# Check-specific configuration
checks:
  code_quality:
    enabled: true
    auto_fix: false
    black:
      line_length: 88
    isort:
      profile: "black"
    flake8:
      max_line_length: 88
      ignore: ["E203", "W503"]
    mypy:
      strict: true

  test_runner:
    enabled: true
    timeout: 300
    parallel: true
    coverage: true

  security_scanner:
    enabled: true
    safety:
      ignore_ids: []
    bandit:
      severity: "medium"

  performance_analyzer:
    enabled: true
    regression_threshold: 30.0
    benchmark_timeout: 600

# Output configuration
output:
  directory: "reports/ci-simulation"
  formats: ["markdown", "json"]
  keep_history: true

# Parallel execution
execution:
  max_parallel: 4
  timeout: 1800

# Directories
directories:
  temp: "temp/ci-simulation"
  logs: "logs"
  reports: "reports/ci-simulation"
  history: ".kiro/ci-history"
```

### Environment Variables

Override configuration with environment variables:

```bash
# Set Python versions
export CI_PYTHON_VERSIONS="3.9,3.10,3.11"

# Enable verbose logging
export CI_VERBOSE=true

# Set output directory
export CI_OUTPUT_DIR="./my-reports"

# Disable specific checks
export CI_DISABLE_CHECKS="performance_analyzer"
```

### Project-Specific Settings

Create `.kiro/ci-config.yml` for project-specific settings:

```yaml
# Project-specific overrides
project:
  name: "PhotoGeoView"
  type: "qt_application"

# AI integration specific settings
ai_integration:
  copilot:
    enabled: true
    test_demos: true
  cursor:
    enabled: true
    theme_tests: true
  kiro:
    enabled: true
    integration_tests: true

# Qt-specific configuration
qt:
  version: "5.15"
  display: "xvfb"
  environment:
    QT_QPA_PLATFORM: "offscreen"
```

## Git Hooks Integration

### Automatic Setup

Install recommended Git hooks:

```bash
python tools/ci/simulator.py hook setup
```

This installs:
- **pre-commit**: Quick checks before commit
- **pre-push**: Full checks before push

### Manual Hook Installation

Install specific hooks:

```bash
# Pre-commit hook with code quality checks
python tools/ci/simulator.py hook install pre-commit --checks code_quality

# Pre-push hook with all checks
python tools/ci/simulator.py hook install pre-push --checks all
```

### Hook Configuration

Hooks can be configured in `.git/hooks/ci-config.json`:

```json
{
  "pre-commit": {
    "checks": ["code_quality"],
    "fail_fast": true,
    "timeout": 120
  },
  "pre-push": {
    "checks": ["all"],
    "exclude": ["performance_analyzer"],
    "timeout": 600
  }
}
```

### Hook Management

```bash
# List hook status
python tools/ci/simulator.py hook list

# Test a hook
python tools/ci/simulator.py hook test pre-commit

# Uninstall a hook
python tools/ci/simulator.py hook uninstall pre-commit

# Show detailed hook status
python tools/ci/simulator.py hook status
```

## Troubleshooting

### Common Issues

#### 1. Python Version Not Found

**Problem:** `Python version 3.x not found`

**Solutions:**
- Install the required Python version using pyenv, conda, or system package manager
- Update your PATH to include the Python installation
- Use `--python-versions` to specify available versions only

```bash
# Check available Python versions
python tools/ci/simulator.py list --detailed

# Use only available versions
python tools/ci/simulator.py run --python-versions 3.10
```

#### 2. Qt Dependencies Missing

**Problem:** `Qt platform plugin could not be initialized`

**Solutions:**
- Install Qt system packages
- Set up virtual display for headless testing
- Configure Qt environment variables

```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5 xvfb

# Set environment variables
export QT_QPA_PLATFORM=offscreen
export DISPLAY=:99
```

#### 3. Permission Errors

**Problem:** `Permission denied when installing hooks`

**Solutions:**
- Check Git repository permissions
- Run with appropriate user permissions
- Verify `.git/hooks` directory exists and is writable

```bash
# Fix permissions
chmod +x .git/hooks/*
```

#### 4. Tool Dependencies Missing

**Problem:** `Command 'black' not found`

**Solutions:**
- Install missing tools
- Update your virtual environment
- Check tool availability

```bash
# Install code quality tools
pip install black isort flake8 mypy

# Install security tools
pip install safety bandit

# Check tool availability
python tools/ci/simulator.py list --detailed
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Verbose output
python tools/ci/simulator.py run --verbose

# Debug logging
export CI_LOG_LEVEL=DEBUG
python tools/ci/simulator.py run
```

### Log Files

Check log files for detailed error information:

- `logs/ci-simulation.log` - Main log file
- `logs/performance.log` - Performance analysis logs
- `logs/security-scan.log` - Security scan logs

### Getting Help

```bash
# General help
python tools/ci/simulator.py --help

# Command-specific help
python tools/ci/simulator.py run --help
python tools/ci/simulator.py hook --help

# Check information
python tools/ci/simulator.py info code_quality
```

## Best Practices

### 1. Regular Usage

- **Run before every commit:** Use Git hooks for automatic checking
- **Test multiple Python versions:** Ensure compatibility across versions
- **Review reports:** Check generated reports for trends and issues

### 2. Configuration Management

- **Use project-specific config:** Create `.kiro/ci-config.yml` for your project
- **Version control config:** Include configuration in your repository
- **Document custom settings:** Add comments to explain project-specific choices

### 3. Performance Optimization

- **Use selective execution:** Run only necessary checks during development
- **Parallel execution:** Use `--parallel` for faster results
- **Cache results:** The tool caches results to avoid redundant work

### 4. Team Collaboration

- **Shared configuration:** Use the same configuration across the team
- **Document setup:** Include setup instructions in your project README
- **Regular updates:** Keep the tool and its dependencies updated

### 5. CI/CD Integration

- **Local first:** Always run locally before pushing
- **Match CI configuration:** Ensure local checks match your CI pipeline
- **Report integration:** Use JSON reports for automation and monitoring

## FAQ

### General Questions

**Q: How does this tool relate to GitHub Actions?**
A: The tool replicates your GitHub Actions workflow locally, allowing you to catch issues before pushing code. It runs the same checks but in your local environment.

**Q: Can I use this with other CI systems?**
A: Yes, the tool is designed to work with any CI system. You can configure it to match your specific CI pipeline requirements.

**Q: Does this replace my CI pipeline?**
A: No, this tool complements your CI pipeline by providing early feedback. Your CI pipeline remains the authoritative source of truth.

### Technical Questions

**Q: How are multiple Python versions handled?**
A: The tool detects available Python versions on your system (pyenv, conda, system) and runs tests in isolated environments for each version.

**Q: What happens if a check fails?**
A: Failed checks are reported with detailed error messages and suggestions for fixes. The tool continues running other independent checks.

**Q: Can I add custom checks?**
A: Yes, the tool is extensible. You can create custom checkers by implementing the `CheckerInterface` and registering them with the `CheckerFactory`.

### Configuration Questions

**Q: Where should I put my configuration file?**
A: You can use:
- `tools/ci/ci-config.yml` for tool-specific settings
- `.kiro/ci-config.yml` for project-specific settings
- Environment variables for temporary overrides

**Q: How do I disable a specific check?**
A: You can:
- Set `enabled: false` in the configuration file
- Use `--exclude check_name` on the command line
- Set the `CI_DISABLE_CHECKS` environment variable

### Performance Questions

**Q: How can I make the tool run faster?**
A: You can:
- Use `--parallel` to run checks concurrently
- Use selective execution to run only necessary checks
- Configure appropriate timeouts
- Use caching (automatically handled by the tool)

**Q: Why is the first run slower?**
A: The first run may be slower due to:
- Tool installation and setup
- Cache building
- Environment preparation
- Baseline establishment for performance tests

### Troubleshooting Questions

**Q: What if I get permission errors?**
A: Check:
- Git repository permissions
- File system permissions for output directories
- Virtual environment activation
- User permissions for installing Git hooks

**Q: How do I report bugs or request features?**
A: Please:
- Check the troubleshooting section first
- Review existing issues in the project repository
- Provide detailed error messages and logs
- Include your configuration and environment details

---

For more detailed technical information, see the [Developer Documentation](DEVELOPER_GUIDE.md) and [API Reference](API_REFERENCE.md).
