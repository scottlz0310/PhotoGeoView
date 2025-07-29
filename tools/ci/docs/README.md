# CI Simulation Tool - Documentation

## Overview

Welcome to the CI Simulation Tool documentation. This tool helps you run GitHub Actions CI/CD pipeline checks locally before committing, catching errors early and ensuring your commits pass CI on the first try.

## Quick Start

```bash
# Check if the tool is available
python tools/ci/simulator.py --version

# Run all available checks
python tools/ci/simulator.py run --all

# Set up Git hooks for automatic checking
python tools/ci/simulator.py hook setup
```

## Documentation Structure

### 📚 User Documentation

#### [User Guide](USER_GUIDE.md)
Comprehensive guide for using the CI Simulation Tool, including:
- Installation and setup instructions
- Basic and advanced usage examples
- Configuration options
- Git hooks integration
- Troubleshooting common issues
- Best practices and FAQ

#### [Installation Guide](INSTALLATION.md)
Detailed installation instructions for different platforms:
- System requirements and prerequisites
- Step-by-step installation procedures
- Platform-specific setup (Linux, macOS, Windows)
- Dependency management
- Verification and testing

#### [Best Practices Guide](BEST_PRACTICES.md)
Recommended practices for effective tool usage:
- Development workflow integration
- Configuration management strategies
- Performance optimization techniques
- Team collaboration approaches
- Security considerations
- Maintenance and updates

#### [Usage Examples](EXAMPLES.md)
Practical examples for common scenarios:
- Basic usage patterns
- Development workflow examples
- Configuration examples
- Git hooks setup
- Team collaboration scenarios
- Advanced usage patterns
- Troubleshooting examples

#### [Troubleshooting Guide](TROUBLESHOOTING.md)
Comprehensive troubleshooting information:
- Quick diagnostics
- Common installation issues
- Runtime error solutions
- Configuration problems
- Performance issues
- Platform-specific problems
- Advanced debugging techniques

### 🔧 Developer Documentation

#### [Developer Guide](DEVELOPER_GUIDE.md)
Technical documentation for developers who want to:
- Understand the tool's architecture
- Extend functionality with custom checks
- Contribute to the project
- Integrate with other tools
- Modify or customize behavior

#### [API Reference](API_REFERENCE.md)
Complete API documentation including:
- Core classes and interfaces
- Configuration options
- Extension points
- Integration APIs
- Data models and structures

## Quick Reference

### Common Commands

```bash
# List available checks
python tools/ci/simulator.py list

# Run specific checks
python tools/ci/simulator.py run code_quality test_runner

# Run all checks except specific ones
python tools/ci/simulator.py run --all --exclude performance_analyzer

# Test multiple Python versions
python tools/ci/simulator.py run --python-versions 3.10 3.11

# Generate detailed reports
python tools/ci/simulator.py run --all --format both

# Interactive mode
python tools/ci/simulator.py --interactive

# Git hooks management
python tools/ci/simulator.py hook setup
python tools/ci/simulator.py hook status
```

### Available Checks

| Check Type | Description | Dependencies |
|------------|-------------|--------------|
| `code_quality` | Code formatting and style checks (Black, isort, flake8, mypy) | black, isort, flake8, mypy |
| `test_runner` | Unit and integration tests | pytest, pytest-cov |
| `security_scanner` | Security vulnerability scanning | safety, bandit |
| `performance_analyzer` | Performance benchmarking and regression detection | psutil, pytest-benchmark |
| `ai_component_tester` | AI integration testing (Copilot, Cursor, Kiro) | requests, aiohttp |

### Configuration Files

| File | Purpose | Scope |
|------|---------|-------|
| `tools/ci/ci-config.yml` | Tool-wide configuration | Global defaults |
| `.kiro/ci-config.yml` | Project-specific configuration | Project overrides |
| Environment variables | Runtime configuration | Session-specific |

### Output Directories

| Directory | Contents | Purpose |
|-----------|----------|---------|
| `reports/ci-simulation/` | Generated reports | Analysis and review |
| `logs/` | Log files | Debugging and monitoring |
| `.kiro/ci-history/` | Execution history | Trend analysis |
| `temp/ci-simulation/` | Temporary files | Working space |

## Getting Help

### Documentation Navigation

- **New to the tool?** Start with the [Installation Guide](INSTALLATION.md)
- **Want to learn usage?** Read the [User Guide](USER_GUIDE.md)
- **Looking for examples?** Check the [Usage Examples](EXAMPLES.md)
- **Having issues?** Consult the [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Want to optimize usage?** Review [Best Practices](BEST_PRACTICES.md)
- **Need to extend the tool?** See the [Developer Guide](DEVELOPER_GUIDE.md)

### Command-Line Help

```bash
# General help
python tools/ci/simulator.py --help

# Command-specific help
python tools/ci/simulator.py run --help
python tools/ci/simulator.py hook --help

# Check-specific information
python tools/ci/simulator.py info code_quality
```

### Diagnostic Commands

```bash
# Check tool status
python tools/ci/simulator.py list --detailed

# Verify configuration
python tools/ci/simulator.py config validate

# Test installation
python tools/ci/simulator.py run code_quality --timeout 60
```

## Support and Contributing

### Getting Support

1. **Check the documentation** - Most questions are answered in the guides above
2. **Review troubleshooting** - Common issues and solutions are documented
3. **Check logs** - Look in `logs/ci-simulation.log` for detailed error information
4. **Run diagnostics** - Use `--verbose` flag for detailed output
5. **Search existing issues** - Check if your issue has been reported before

### Contributing

We welcome contributions! Please see the [Developer Guide](DEVELOPER_GUIDE.md) for:
- Development setup instructions
- Architecture overview
- Contribution guidelines
- Code style requirements
- Testing procedures

### Reporting Issues

When reporting issues, please include:
- Operating system and version
- Python version
- Complete error message
- Steps to reproduce
- Configuration files (sanitized)
- Log files (relevant portions)

## Version Information

- **Current Version:** 1.0.0
- **Minimum Python:** 3.9
- **Recommended Python:** 3.11
- **Supported Platforms:** Linux, macOS, Windows

## License and Credits

This tool is part of the PhotoGeoView project and follows the same licensing terms. See the main project documentation for license information.

### Acknowledgments

The CI Simulation Tool integrates with and builds upon several excellent open-source tools:
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Style checking
- **mypy** - Type checking
- **pytest** - Testing framework
- **safety** - Security scanning
- **bandit** - Security linting

---

**Last Updated:** January 15, 2024
**Documentation Version:** 1.0.0
