# CI Simulation Tool - Usage Examples

## Overview

This document provides practical examples of using the CI Simulation Tool in various scenarios. Each example includes the command, expected output, and explanation of when to use it.

## Table of Contents

1. [Basic Usage Examples](#basic-usage-examples)
2. [Development Workflow Examples](#development-workflow-examples)
3. [Configuration Examples](#configuration-examples)
4. [Git Hooks Examples](#git-hooks-examples)
5. [Team Collaboration Examples](#team-collaboration-examples)
6. [Advanced Usage Examples](#advanced-usage-examples)
7. [Troubleshooting Examples](#troubleshooting-examples)
8. [Integration Examples](#integration-examples)

## Basic Usage Examples

### Example 1: First Time Setup

**Scenario:** You've just cloned the repository and want to set up the CI simulation tool.

```bash
# Check if the tool is available
python tools/ci/simulator.py --version

# List available checks
python tools/ci/simulator.py list

# Run a simple check to veing works
python tools/ci/simulator.py run code_quality --timeout 60
```

**Expected Output:**
```
CI Simulator v1.0.0

Available checks:
✓ code_quality - Code formatting and style checks
✓ test_runner - Unit and integration tests
✓ security_scanner - Security vulnerability scanning
✓ performance_analyzer - Performance benchmarking
✓ ai_component_tester - AI integration testing

============================================================
CI SIMULATION SUMMARY
============================================================
Duration: 45.23 seconds
Overall Status: SUCCESS
Python Versions: system

Executed 1 checks: ✓ 1 successful

Reports Generated:
• Markdown: reports/ci-simulation/ci_report_20240115_143022.md
============================================================
```

### Example 2: Quick Code Quality Check

**Scenario:** You've made some code changes and want to quickly check formatting and style.

```bash
python tools/ci/simulator.py run code_quality
```

**Expected Output:**
```
Starting CI simulation...
Executing 1 tasks...

Running code_quality check...
  ✓ Black formatting: PASSED (0 files reformatted)
  ✓ isort imports: PASSED (0 files modified)
  ✓ flake8 style: PASSED (0 violations found)
  ⚠ mypy types: WARNING (3 type hints missing)

============================================================
CI SIMULATION SUMMARY
============================================================
Duration: 12.45 seconds
Overall Status: WARNING
Python Versions: system

Executed 1 checks: ✓ 1 successful | ⚠ 1 warnings

Reports Generated:
• Markdown: reports/ci-simulation/ci_report_20240115_143522.md
============================================================
```

### Example 3: Run All Available Checks

**Scenario:** Before committing, you want to run all available checks to ensure everything is working.

```bash
python tools/ci/simulator.py run --all
```

**Expected Output:**
```
Starting CI simulation...
Executing 5 tasks...

Running checks in parallel (max 4)...
  ✓ code_quality: PASSED (12.3s)
  ✓ test_runner: PASSED (45.7s)
  ✓ security_scanner: PASSED (23.1s)
  ✓ performance_analyzer: PASSED (67.2s)
  ✓ ai_component_tester: PASSED (34.5s)

============================================================
CI SIMULATION SUMMARY
============================================================
Duration: 89.34 seconds
Overall Status: SUCCESS
Python Versions: system

Executed 5 checks: ✓ 5 successful

Reports Generated:
• Markdown: reports/ci-simulation/ci_report_20240115_144022.md
• JSON: reports/ci-simulation/ci_report_20240115_144022.json
============================================================
```

## Development Workflow Examples

### Example 4: Feature Development Workflow

**Scenario:** You're developing a new feature and want to use CI checks throughout the development process.

```bash
# 1. Start feature development
git checkout -b feature/photo-metadata-extraction

# 2. Make initial changes
# ... edit files ...

# 3. Quick check during development
python tools/ci/simulator.py run code_quality --timeout 30

# 4. Add tests and run test suite
python tools/ci/simulator.py run test_runner

# 5. Before committing, run comprehensive checks
python tools/ci/simulator.py run --all --exclude performance_analyzer

# 6. If all checks pass, commit
git add .
git commit -m "feat: Add photo metadata extraction functionality"

# 7. Before pushing, run full validation
python tools/ci/simulator.py run --all

# 8. Push the feature
git push origin feature/photo-metadata-extraction
```

### Example 5: Bug Fix Workflow

**Scenario:** You're fixing a bug and want to ensure the fix doesn't break anything.

```bash
# 1. Create bug fix branch
git checkout -b fix/gps-coordinate-parsing

# 2. Write test to reproduce the bug
# ... add test case ...

# 3. Verify the test fails (reproduces the bug)
python tools/ci/simulator.py run test_runner --verbose

# 4. Implement the fix
# ... fix the code ...

# 5. Verify the fix works
python tools/ci/simulator.py run test_runner

# 6. Run security scan to ensure no new vulnerabilities
python tools/ci/simulator.py run security_scanner

# 7. Full validation before committing
python tools/ci/simulator.py run --all
```

### Example 6: Code Review Preparation

**Scenario:** You're preparing code for review and want to generate comprehensive reports.

```bash
# 1. Run all checks with detailed reporting
python tools/ci/simulator.py run --all \
  --format both \
  --output-dir ./review-reports \
  --python-versions 3.10 3.11

# 2. Generate execution plan for reviewers
python tools/ci/simulator.py plan --all --format markdown > review-reports/execution-plan.md

# 3. Check the reports
ls -la review-reports/
cat review-reports/ci_report_*.md
```

**Generated Files:**
```
review-reports/
├── ci_report_20240115_145022.md
├── ci_report_20240115_145022.json
└── execution-plan.md
```

## Configuration Examples

### Example 7: Project-Specific Configuration

**Scenario:** You want to create a configuration file tailored to your project.

**File: `.kiro/ci-config.yml`**
```yaml
# PhotoGeoView Project Configuration
project:
  name: "PhotoGeoView"
  type: "qt_application"
  description: "AI-integrated photo geolocation viewer"

# Python versions used in this project
python_versions:
  - "3.10"
  - "3.11"

checks:
  code_quality:
    enabled: true
    # Project uses 88-character line length
    black:
      line_length: 88
      target_version: ["py310"]

    # Configure isort for this project's import style
    isort:
      profile: "black"
      known_first_party: ["photogeoview", "src"]

    # flake8 configuration
    flake8:
      max_line_length: 88
      ignore: ["E203", "W503"]  # Black compatibility
      exclude: ["migrations/", "venv/"]

    # mypy configuration - gradually increasing strictness
    mypy:
      strict: false
      warn_return_any: true
      ignore_missing_imports: true

  test_runner:
    enabled: true
    timeout: 300
    # Qt-specific settings
    qt_tests: true
    virtual_display: true
    coverage_threshold: 80

  security_scanner:
    enabled: true
    # Known false positives for this project
    safety:
      ignore_ids: [51668]  # Pillow vulnerability not applicable
    bandit:
      exclude_dirs: ["tests/", "examples/"]

  performance_analyzer:
    enabled: true
    regression_threshold: 25.0  # Stricter threshold for this project
    benchmark_timeout: 900

  ai_component_tester:
    enabled: true
    # Enable all AI integrations
    copilot: true
    cursor: true
    kiro: true
    # Test demo scripts
    test_demos: true

# Output configuration
output:
  directory: "reports/ci-simulation"
  formats: ["markdown", "json"]
  keep_history: 30

# Execution settings optimized for development machines
execution:
  max_parallel: 4
  timeout: 1800
  fail_fast: false

# Directory structure
directories:
  temp: "temp/ci-simulation"
  logs: "logs"
  reports: "reports/ci-simulation"
  history: ".kiro/ci-history"
```

**Usage:**
```bash
# The tool automatically uses this configuration
python tools/ci/simulator.py run --all
```

### Example 8: Environment-Specific Configuration

**Scenario:** You want different configurations for development vs. CI environments.

**Development Environment:**
```bash
# Set environment variables for development
export CI_PARALLEL=2
export CI_TIMEOUT=300
export CI_EXCLUDE_CHECKS="performance_analyzer"

python tools/ci/simulator.py run --all
```

**CI Environment:**
```bash
# Set environment variables for CI
export CI_PARALLEL=8
export CI_TIMEOUT=1800
export CI_PYTHON_VERSIONS="3.9,3.10,3.11"

python tools/ci/simulator.py run --all
```

## Git Hooks Examples

### Example 9: Setting Up Git Hooks

**Scenario:** You want to automatically run CI checks before commits and pushes.

```bash
# Install recommended hooks
python tools/ci/simulator.py hook setup

# Check hook status
python tools/ci/simulator.py hook status
```

**Expected Output:**
```
Setting up recommended Git hooks...

Installation Results: 2/2 successful
✅ pre-commit
✅ pre-push

Git Hook Status
==================================================
Git Repository: /path/to/PhotoGeoView
Git Directory: /path/to/PhotoGeoView/.git
Hooks Directory: /path/to/PhotoGeoView/.git/hooks

Hook Details:
------------------------------
pre-commit:
  Installed: True
  Our Hook: True
  Executable: True
  Installed At: 2024-01-15 14:50:22
  Checks: code_quality

pre-push:
  Installed: True
  Our Hook: True
  Executable: True
  Installed At: 2024-01-15 14:50:22
  Checks: code_quality, test_runner, security_scanner
```

### Example 10: Custom Hook Configuration

**Scenario:** You want to customize which checks run in Git hooks.

```bash
# Install pre-commit hook with specific checks
python tools/ci/simulator.py hook install pre-commit \
  --checks code_quality \
  --timeout 120

# Install pre-push hook with comprehensive checks
python tools/ci/simulator.py hook install pre-push \
  --checks code_quality test_runner security_scanner \
  --timeout 600

# Test the hooks
python tools/ci/simulator.py hook test pre-commit
```

### Example 11: Hook Troubleshooting

**Scenario:** Your Git hook is not working as expected.

```bash
# Check hook status
python tools/ci/simulator.py hook status

# Test hook manually
python tools/ci/simulator.py hook test pre-commit

# List all hooks
python tools/ci/simulator.py hook list --format json

# Reinstall if needed
python tools/ci/simulator.py hook uninstall pre-commit
python tools/ci/simulator.py hook install pre-commit --checks code_quality
```

## Team Collaboration Examples

### Example 12: Team Onboarding

**Scenario:** A new team member needs to set up the CI simulation tool.

**Onboarding Script (`scripts/setup-ci-tool.sh`):**
```bash
#!/bin/bash
set -e

echo "🚀 Setting up CI Simulation Tool for PhotoGeoView"
echo "=================================================="

# Check Python version
python_version=$(python --version 2>&1 | cut -d' ' -f2)
echo "✓ Python version: $python_version"

if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Python 3.10+ required. Please upgrade Python."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Verify installation
echo "🔍 Verifying installation..."
python tools/ci/simulator.py --version

# Setup Git hooks
echo "🪝 Setting up Git hooks..."
python tools/ci/simulator.py hook setup

# Run initial test
echo "🧪 Running initial test..."
python tools/ci/simulator.py run code_quality --timeout 60

echo "✅ Setup complete! You can now use:"
echo "   python tools/ci/simulator.py run --all"
echo ""
echo "📚 Read the documentation:"
echo "   - User Guide: tools/ci/docs/USER_GUIDE.md"
echo "   - Best Practices: tools/ci/docs/BEST_PRACTICES.md"
```

**Usage:**
```bash
chmod +x scripts/setup-ci-tool.sh
./scripts/setup-ci-tool.sh
```

### Example 13: Shared Team Configuration

**Scenario:** Your team wants to use consistent CI settings across all developers.

**Team Configuration (`tools/ci/team-config.yml`):**
```yaml
# PhotoGeoView Team Standards
# Maintained by: Development Team
# Last updated: 2024-01-15

team:
  name: "PhotoGeoView Development Team"
  standards_version: "1.2"

# Mandatory Python versions for testing
python_versions:
  - "3.10"  # Minimum supported
  - "3.11"  # Current development standard

# Team code quality standards
code_quality:
  line_length: 88
  import_style: "black"
  type_checking: "gradual"
  documentation: "required_for_public_api"

# Testing standards
testing:
  minimum_coverage: 80
  require_integration_tests: true
  require_performance_tests: false  # Only for critical paths

# Security standards
security:
  vulnerability_tolerance: "medium"
  require_security_review: true
  scan_dependencies: true

# Performance standards
performance:
  regression_threshold: 30.0
  benchmark_timeout: 600
  memory_limit: "2GB"

# AI integration standards
ai_integration:
  test_all_components: true
  require_demo_validation: true
  compatibility_matrix:
    copilot: "required"
    cursor: "required"
    kiro: "required"
```

**Usage:**
```bash
# Use team configuration
python tools/ci/simulator.py run --config tools/ci/team-config.yml --all
```

## Advanced Usage Examples

### Example 14: Multiple Python Version Testing

**Scenario:** You want to test your code against multiple Python versions.

```bash
# Test against specific Python versions
python tools/ci/simulator.py run --all \
  --python-versions 3.9 3.10 3.11 \
  --format json \
  --output-dir ./multi-python-results
```

**Expected Output:**
```
Starting CI simulation...
Testing against Python versions: 3.9, 3.10, 3.11

Python 3.9:
  ✓ code_quality: PASSED (15.2s)
  ✓ test_runner: PASSED (52.1s)
  ✓ security_scanner: PASSED (28.3s)

Python 3.10:
  ✓ code_quality: PASSED (14.8s)
  ✓ test_runner: PASSED (48.7s)
  ✓ security_scanner: PASSED (26.9s)

Python 3.11:
  ✓ code_quality: PASSED (13.9s)
  ✓ test_runner: PASSED (45.3s)
  ✓ security_scanner: PASSED (25.1s)

============================================================
CI SIMULATION SUMMARY
============================================================
Duration: 156.78 seconds
Overall Status: SUCCESS
Python Versions: 3.9, 3.10, 3.11

Executed 9 checks: ✓ 9 successful
============================================================
```

### Example 15: Performance Regression Detection

**Scenario:** You want to detect performance regressions in your code.

```bash
# Run performance analysis with baseline comparison
python tools/ci/simulator.py run performance_analyzer \
  --format both \
  --output-dir ./performance-results
```

**Expected Output:**
```
Running performance_analyzer check...

Benchmark Results:
  📊 Image Processing: 1.23s (baseline: 1.15s, +6.9% slower)
  📊 GPS Parsing: 0.45s (baseline: 0.48s, -6.3% faster)
  📊 Database Queries: 2.34s (baseline: 2.89s, -19.0% faster)
  📊 UI Rendering: 0.78s (baseline: 0.72s, +8.3% slower)

⚠️ Performance Regression Detected:
  - Image Processing: 6.9% slower (threshold: 30%)
  - UI Rendering: 8.3% slower (threshold: 30%)

Overall Performance: ACCEPTABLE (no regressions exceed threshold)
```

### Example 16: Security Vulnerability Scanning

**Scenario:** You want to scan for security vulnerabilities in dependencies and code.

```bash
# Run comprehensive security scan
python tools/ci/simulator.py run security_scanner \
  --format both \
  --output-dir ./security-results
```

**Expected Output:**
```
Running security_scanner check...

Safety Dependency Scan:
  ✓ Scanned 127 packages
  ✓ No known vulnerabilities found

Bandit Code Security Scan:
  ✓ Scanned 45 Python files
  ⚠️ Found 2 low severity issues:
    - src/utils/crypto.py:23: Use of insecure MD5 hash
    - src/config/settings.py:67: Hardcoded password (test data)

Security Summary:
  - High severity: 0
  - Medium severity: 0
  - Low severity: 2
  - Total issues: 2

Overall Security: ACCEPTABLE (no high/medium severity issues)
```

### Example 17: AI Component Integration Testing

**Scenario:** You want to test all AI component integrations.

```bash
# Test AI components
python tools/ci/simulator.py run ai_component_tester \
  --verbose \
  --format markdown \
  --output-dir ./ai-test-results
```

**Expected Output:**
```
Running ai_component_tester check...

Testing AI Components:

Copilot Integration:
  ✓ Configuration validation: PASSED
  ✓ API connectivity: PASSED
  ✓ Code completion test: PASSED
  ✓ Demo script execution: PASSED

Cursor Integration:
  ✓ Configuration validation: PASSED
  ✓ Theme system test: PASSED
  ✓ UI component test: PASSED
  ✓ Demo script execution: PASSED

Kiro Integration:
  ✓ Configuration validation: PASSED
  ✓ Architecture validation: PASSED
  ✓ Integration test suite: PASSED
  ✓ Demo script execution: PASSED

AI Integration Summary:
  - Total components tested: 3
  - Successful tests: 12/12
  - Failed tests: 0/12
  - Overall status: SUCCESS
```

## Troubleshooting Examples

### Example 18: Debugging Failed Checks

**Scenario:** A check is failing and you need to debug the issue.

```bash
# Run with verbose output for debugging
python tools/ci/simulator.py run code_quality --verbose

# Check specific tool availability
python tools/ci/simulator.py info code_quality

# Test individual tools
python -m black --version
python -m mypy --version
python -m flake8 --version
```

**Debug Output:**
```
DEBUG: Starting code_quality check
DEBUG: Black executable found at: /usr/local/bin/black
DEBUG: Running: black --check --diff .
DEBUG: Black output: would reformat 3 files
DEBUG: Black exit code: 1

ERROR: Code formatting issues found:
--- src/main.py
+++ src/main.py
@@ -15,7 +15,8 @@
     def process_image(self, image_path):
-        if not os.path.exists(image_path): return None
+        if not os.path.exists(image_path):
+            return None
         return self.extract_metadata(image_path)
```

### Example 19: Fixing Configuration Issues

**Scenario:** Your configuration file has errors and you need to fix them.

```bash
# Validate configuration
python -c "
import yaml
try:
    with open('.kiro/ci-config.yml') as f:
        config = yaml.safe_load(f)
    print('✓ Configuration is valid')
except yaml.YAMLError as e:
    print(f'❌ Configuration error: {e}')
"

# Use default configuration if yours is broken
python tools/ci/simulator.py run --config tools/ci/templates/ci_config_template.yaml
```

### Example 20: Environment Issues

**Scenario:** You're having environment-related issues.

```bash
# Check environment
python tools/ci/simulator.py list --detailed

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check installed packages
pip list | grep -E "(black|mypy|flake8|isort)"

# Test Qt environment (if applicable)
python -c "
import os
print('QT_QPA_PLATFORM:', os.environ.get('QT_QPA_PLATFORM', 'not set'))
print('DISPLAY:', os.environ.get('DISPLAY', 'not set'))
try:
    import PyQt5
    print('✓ PyQt5 available')
except ImportError:
    print('❌ PyQt5 not available')
"
```

## Integration Examples

### Example 21: IDE Integration

**Scenario:** You want to integrate the CI tool with your IDE.

**VS Code Task Configuration (`.vscode/tasks.json`):**
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "CI: Quick Check",
            "type": "shell",
            "command": "python",
            "args": ["tools/ci/simulator.py", "run", "code_quality", "--timeout", "60"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": []
        },
        {
            "label": "CI: Full Check",
            "type": "shell",
            "command": "python",
            "args": ["tools/ci/simulator.py", "run", "--all"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": true,
                "panel": "shared"
            },
            "problemMatcher": []
        },
        {
            "label": "CI: Security Scan",
            "type": "shell",
            "command": "python",
            "args": ["tools/ci/simulator.py", "run", "security_scanner"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": []
        }
    ]
}
```

**PyCharm External Tool Configuration:**
- Program: `python`
- Arguments: `tools/ci/simulator.py run --all`
- Working directory: `$ProjectFileDir$`

### Example 22: Makefile Integration

**Scenario:** You want to integrate CI checks into your project's Makefile.

**Makefile:**
```makefile
# CI Simulation Tool Integration

.PHONY: ci-quick ci-full ci-security ci-performance ci-setup ci-clean

# Quick development checks
ci-quick:
	python tools/ci/simulator.py run code_quality --timeout 60

# Full CI simulation
ci-full:
	python tools/ci/simulator.py run --all

# Security-focused checks
ci-security:
	python tools/ci/simulator.py run security_scanner --format both

# Performance analysis
ci-performance:
	python tools/ci/simulator.py run performance_analyzer --format json

# Setup CI tool and hooks
ci-setup:
	pip install -r requirements.txt
	python tools/ci/simulator.py hook setup

# Clean up CI artifacts
ci-clean:
	rm -rf reports/ci-simulation/ci_report_*
	rm -rf .kiro/ci-history/old-*
	rm -rf temp/ci-simulation/

# Development workflow targets
dev-check: ci-quick
pre-commit: ci-full
pre-push: ci-full ci-security

# Help target
ci-help:
	@echo "Available CI targets:"
	@echo "  ci-quick      - Quick code quality checks"
	@echo "  ci-full       - Full CI simulation"
	@echo "  ci-security   - Security vulnerability scanning"
	@echo "  ci-performance - Performance analysis"
	@echo "  ci-setup      - Setup CI tool and Git hooks"
	@echo "  ci-clean      - Clean up CI artifacts"
```

**Usage:**
```bash
# Quick check during development
make ci-quick

# Full validation before commit
make ci-full

# Security scan
make ci-security
```

### Example 23: Docker Integration

**Scenario:** You want to run CI checks in a Docker container for consistency.

**Dockerfile.ci:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    xvfb \
    python3-pyqt5 \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment variables for headless operation
ENV QT_QPA_PLATFORM=offscreen
ENV DISPLAY=:99

# Default command
CMD ["python", "tools/ci/simulator.py", "run", "--all"]
```

**Docker Compose (docker-compose.ci.yml):**
```yaml
version: '3.8'

services:
  ci-simulation:
    build:
      context: .
      dockerfile: Dockerfile.ci
    volumes:
      - .:/app
      - ci-reports:/app/reports
    environment:
      - CI_PARALLEL=4
      - CI_TIMEOUT=1800
    command: python tools/ci/simulator.py run --all --format both

volumes:
  ci-reports:
```

**Usage:**
```bash
# Build CI container
docker build -f Dockerfile.ci -t photogeoview-ci .

# Run CI checks in container
docker run --rm -v $(pwd):/app photogeoview-ci

# Using docker-compose
docker-compose -f docker-compose.ci.yml up --build
```

These examples demonstrate the flexibility and power of the CI Simulation Tool across various development scenarios. Use them as starting points and adapt them to your specific project needs and workflow requirements.
