# CI Simulator Integration Guide

## Overview

The CI Simulator has been fully integrated into the PhotoGeoView project structure, providing comprehensive local CI/CD simulation capabilities that mirror the GitHub Actions workflows.

## Integration Components

### 1. Project Configuration Integration

#### pyproject.toml
- **Script entries**: `ci-simulator`, `pgv-ci`, `photogeoview-ci` commands
- **CI dependencies**: Comprehensive CI toolchain in `[project.optional-dependencies.ci]`
- **Tool configurations**: Black, isort, mypy, pytest, coverage, bandit settings
- **CI Simulator settings**: `[tool.ci_simulator]` section with default configurations

#### Makefile Integration
- **ci**: Standard CI checks (code quality + tests)
- **ci-quick**: Fast CI checks with fail-fast mode
- **ci-full**: Comprehensive CI checks with all Python versions
- **setup-hooks**: Git hooks installation
- **validate-ci-integration**: Integration validation
- **build-with-ci**: CI-integrated build process
- **deploy-production**: Production deployment with CI checks

### 2. Build Process Integration

#### CI-Integrated Build (`scripts/build_with_ci.py`)
1. **Pre-build CI checks**: Full CI simulation before building
2. **Package building**: Standard Python package build
3. **Post-build validation**: Package installation and import testing
4. **Build reporting**: Comprehensive build reports with CI results

#### Deployment Integration (`tools/create_deployment_package.py`)
- **CI simulation**: Runs full CI checks before deployment
- **Quality validation**: Ensures quality thresholds are met
- **Artifact creation**: Creates deployment packages with CI validation
- **Manifest generation**: Includes CI results in deployment manifest

### 3. Git Workflow Integration

#### Git Hooks
- **Pre-commit**: Runs code quality checks and unit tests
- **Pre-push**: Optional comprehensive CI checks
- **Hook management**: Install, uninstall, and status commands

#### GitHub Actions Integration
- **ai-integration-ci.yml**: Enhanced with CI simulator integration
- **ci-simulator.yml**: Dedicated CI simulator workflow
- **Deployment preparation**: Uses CI-integrated build process

### 4. Development Workflow Integration

#### Setup Scripts
- **`scripts/setup_ci_integration.py`**: Complete CI integration setup
- **`scripts/validate_ci_integration.py`**: Integration validation
- **Directory structure**: Automatic creation of required directories
- **Configuration**: Default CI simulator configuration

## Usage Guide

### Initial Setup

```bash
# Install with CI dependencies
pip install -e .[ci]

# Setup CI integration
python scripts/setup_ci_integration.py

# Validate integration
python scripts/validate_ci_integration.py
```

### Daily Development

```bash
# Quick CI checks before commit
make ci-quick

# Full CI simulation
make ci-full

# Setup Git hooks
make setup-hooks
```

### Build and Deployment

```bash
# CI-integrated build
make build-with-ci

# Production deployment
make deploy-production

# Manual CI-integrated build
python scripts/build_with_ci.py
```

### CI Simulator Commands

```bash
# List available checks
ci-simulator list

# Run specific checks
ci-simulator run --checks code_quality test_runner

# Run all checks with multiple Python versions
ci-simulator run --checks all --python-versions 3.9 3.10 3.11

# Git hook management
ci-simulator hook setup
ci-simulator hook status
```

## Directory Structure

```
project/
├── .kiro/
│   ├── ci-history/          # CI execution history
│   └── settings/
│       └── ci_simulator.json # CI configuration
├── reports/
│   ├── ci-simulation/       # CI simulation reports
│   └── ci-build/           # CI build reports
├── logs/                   # CI logs
├── temp/ci-simulation/     # Temporary CI files
├── scripts/
│   ├── setup_ci_integration.py
│   ├── validate_ci_integration.py
│   └── build_with_ci.py
└── tools/
    ├── ci/                 # CI simulator implementation
    └── create_deployment_package.py
```

## Configuration

### Default CI Configuration

The CI simulator uses configuration from multiple sources:

1. **pyproject.toml**: `[tool.ci_simulator]` section
2. **`.kiro/settings/ci_simulator.json`**: Detailed configuration
3. **Environment variables**: Runtime overrides
4. **Command line arguments**: Execution-specific settings

### Key Configuration Options

```toml
[tool.ci_simulator]
enabled = true
default_python_versions = ["3.9", "3.10", "3.11"]
timeout = 1800
parallel_jobs = 4
fail_fast = false

[tool.ci_simulator.checks]
code_quality = {enabled = true, auto_fix = false}
test_runner = {enabled = true, coverage_threshold = 80.0}
security_scanner = {enabled = true, fail_on_high = false}
performance_analyzer = {enabled = true, regression_threshold = 30.0}
ai_component_tester = {enabled = true, demo_tests = true}
```

## Integration Benefits

### 1. Consistent CI/CD Experience
- Local simulation matches GitHub Actions exactly
- Same tools, same configurations, same results
- Catch issues before pushing to remote

### 2. Faster Development Cycle
- Immediate feedback on code quality
- No waiting for remote CI to complete
- Fix issues locally before committing

### 3. Comprehensive Quality Assurance
- Multi-Python version testing
- Security vulnerability scanning
- Performance regression detection
- AI component integration testing

### 4. Automated Workflows
- Git hooks prevent bad commits
- CI-integrated builds ensure quality
- Deployment validation with CI checks

## Troubleshooting

### Common Issues

#### CI Simulator Not Found
```bash
# Ensure proper installation
pip install -e .[ci]

# Verify installation
ci-simulator --version
```

#### Git Hooks Not Working
```bash
# Check hook status
ci-simulator hook status

# Reinstall hooks
ci-simulator hook setup
```

#### Build Failures
```bash
# Validate CI integration
python scripts/validate_ci_integration.py

# Check build with CI
python scripts/build_with_ci.py --skip-ci
```

### Performance Issues

#### Slow CI Execution
- Reduce parallel jobs: `--parallel 2`
- Use fail-fast mode: `--fail-fast`
- Run specific checks only: `--checks code_quality`

#### Large Report Files
- Configure report retention in `.kiro/settings/ci_simulator.json`
- Clean old reports: `make clean`

## Advanced Usage

### Custom Check Selection
```bash
# Run only code quality checks
ci-simulator run --checks code_quality

# Exclude specific checks
ci-simulator run --exclude performance_analyzer

# Run with specific Python version
ci-simulator run --python-versions 3.11
```

### Report Formats
```bash
# Generate both Markdown and JSON reports
ci-simulator run --format both

# JSON only for CI integration
ci-simulator run --format json
```

### Integration with IDEs

#### VS Code Integration
Add to `.vscode/tasks.json`:
```json
{
    "label": "CI Quick Check",
    "type": "shell",
    "command": "make ci-quick",
    "group": "build",
    "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
    }
}
```

#### Pre-commit Integration
The CI simulator integrates with pre-commit hooks automatically when installed via `make setup-hooks`.

## Maintenance

### Regular Tasks

#### Update CI Configuration
```bash
# Edit configuration
vim .kiro/settings/ci_simulator.json

# Validate changes
python scripts/validate_ci_integration.py
```

#### Clean CI Artifacts
```bash
# Clean temporary files
make clean

# Clean all CI reports
rm -rf reports/ci-simulation/*
rm -rf .kiro/ci-history/*
```

#### Update Dependencies
```bash
# Update CI dependencies
pip install -e .[ci] --upgrade

# Validate after update
python scripts/validate_ci_integration.py
```

## Contributing

When contributing to the CI integration:

1. **Test changes**: Run `python scripts/validate_ci_integration.py`
2. **Update documentation**: Keep this guide current
3. **Maintain compatibility**: Ensure GitHub Actions workflows stay in sync
4. **Performance**: Consider impact on CI execution time

## Support

For CI integration issues:

1. **Check logs**: `logs/ci-simulation.log`
2. **Validate integration**: `python scripts/validate_ci_integration.py`
3. **Review configuration**: `.kiro/settings/ci_simulator.json`
4. **Test manually**: `ci-simulator run --checks all --verbose`

---

*This integration guide is maintained as part of the PhotoGeoView AI Integration project.*
