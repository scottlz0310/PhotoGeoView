# CI Simulation Tool - Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting information for common issues encountered when using the CI Simulation Tool.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Runtime Errors](#runtime-errors)
4. [Configuration Problems](#configuration-problems)
5. [Performance Issues](#performance-issues)
6. [Git Hooks Issues](#git-hooks-issues)
7. [Platform-Specific Issues](#platform-specific-issues)
8. [Advanced Debugging](#advanced-debugging)
9. [FAQ](#faq)

## Quick Diagnostics

### Health Check Command

Run this command to quickly diagnose common issues:

```bash
python tools/ci/simulator.py list --detailed
```

This will show:
- Available checks and their status
- Missing dependencies
- Configuration issues
- System compatibility

### Environment Information

Gather environment information for troubleshooting:

```bash
# System information
python --version
git --version
pip --version

# Tool information
python tools/ci/simulator.py --version

# Check dependencies
python -c "import sys; print('Python path:', sys.path)"
```

### Log Files

Check these log files for detailed error information:

- `logs/ci-simulation.log` - Main application log
- `logs/performance.log` - Performance analysis logs
- `logs/security-scan.log` - Security scan logs
- `.kiro/ci-history/*/results.json` - Historical execution data

## Installation Issues

### Issue: Python Version Not Supported

**Symptoms:**
```
Error: Python 3.8 is not supported. Please use Python 3.9 or higher.
```

**Solutions:**

1. **Check current Python version:**
   ```bash
   python --version
   python3 --version
   ```

2. **Install correct Python version:**
   ```bash
   # Using pyenv (recommended)
   curl https://pyenv.run | bash
   pyenv install 3.11.0
   pyenv global 3.11.0

   # Using conda
   conda install python=3.11

   # Using system package manager (Ubuntu)
   sudo apt-get install python3.11
   ```

3. **Use specific Python version:**
   ```bash
   python3.11 tools/ci/simulator.py --version
   ```

### Issue: Missing Dependencies

**Symptoms:**
```
ModuleNotFoundError: No module named 'black'
ImportError: cannot import name 'CheckResult' from 'models'
```

**Solutions:**

1. **Install missing packages:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check virtual environment:**
   ```bash
   which python
   which pip
   # Ensure you're in the correct virtual environment
   ```

3. **Install specific tools:**
   ```bash
   # Code quality tools
   pip install black isort flake8 mypy

   # Security tools
   pip install safety bandit

   # Testing tools
   pip install pytest pytest-cov
   ```

4. **Verify installation:**
   ```bash
   python -c "import black, isort, flake8; print('Tools installed successfully')"
   ```

### Issue: Permission Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.x/site-packages'
```

**Solutions:**

1. **Use user installation:**
   ```bash
   pip install --user -r requirements.txt
   ```

2. **Use virtual environment:**
   ```bash
   python -m venv ci-env
   source ci-env/bin/activate
   pip install -r requirements.txt
   ```

3. **Fix permissions (Linux/macOS):**
   ```bash
   sudo chown -R $USER:$USER ~/.local/
   ```

### Issue: Build Failures

**Symptoms:**
```
Failed building wheel for package
error: Microsoft Visual C++ 14.0 is required
```

**Solutions:**

1. **Install build tools (Ubuntu/Debian):**
   ```bash
   sudo apt-get install build-essential python3-dev
   ```

2. **Install build tools (macOS):**
   ```bash
   xcode-select --install
   ```

3. **Install build tools (Windows):**
   - Download Visual Studio Build Tools
   - Install C++ build tools

4. **Use pre-compiled wheels:**
   ```bash
   pip install --only-binary=all -r requirements.txt
   ```

## Runtime Errors

### Issue: Tool Not Found

**Symptoms:**
```
Command 'black' not found
Tool 'mypy' is not available
```

**Solutions:**

1. **Check tool availability:**
   ```bash
   which black
   which mypy
   which flake8
   ```

2. **Install missing tools:**
   ```bash
   pip install black mypy flake8 isort
   ```

3. **Check PATH:**
   ```bash
   echo $PATH
   # Ensure pip installation directory is in PATH
   ```

4. **Use full path:**
   ```bash
   # Find tool location
   python -m black --version
   python -m mypy --version
   ```

### Issue: Qt Platform Errors

**Symptoms:**
```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
QApplication: invalid style override passed
```

**Solutions:**

1. **Install Qt system packages (Linux):**
   ```bash
   sudo apt-get install python3-pyqt5 python3-pyqt5-dev
   sudo apt-get install libxcb-xinerama0
   ```

2. **Set up virtual display:**
   ```bash
   sudo apt-get install xvfb
   export DISPLAY=:99
   Xvfb :99 -screen 0 1024x768x24 &
   ```

3. **Use offscreen platform:**
   ```bash
   export QT_QPA_PLATFORM=offscreen
   ```

4. **Install Qt libraries (macOS):**
   ```bash
   brew install pyqt5
   ```

### Issue: Memory Errors

**Symptoms:**
```
MemoryError: Unable to allocate array
Process killed due to memory usage
```

**Solutions:**

1. **Reduce parallel execution:**
   ```bash
   python tools/ci/simulator.py run --parallel 1
   ```

2. **Increase system memory or swap:**
   ```bash
   # Check memory usage
   free -h
   top
   ```

3. **Run checks individually:**
   ```bash
   python tools/ci/simulator.py run code_quality
   python tools/ci/simulator.py run test_runner
   ```

4. **Configure memory limits:**
   ```yaml
   # In ci-config.yml
   execution:
     memory_limit: "2GB"
     max_parallel: 2
   ```

### Issue: Timeout Errors

**Symptoms:**
```
TimeoutError: Check 'test_runner' exceeded timeout of 300 seconds
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   python tools/ci/simulator.py run --timeout 600
   ```

2. **Configure per-check timeouts:**
   ```yaml
   # In ci-config.yml
   checks:
     test_runner:
       timeout: 900
     performance_analyzer:
       timeout: 1200
   ```

3. **Optimize test execution:**
   ```bash
   # Run specific test categories
   python tools/ci/simulator.py run test_runner --exclude integration
   ```

## Configuration Problems

### Issue: Configuration File Not Found

**Symptoms:**
```
Warning: Configuration file not found, using defaults
```

**Solutions:**

1. **Create configuration file:**
   ```bash
   cp tools/ci/templates/ci_config_template.yaml tools/ci/ci-config.yml
   ```

2. **Specify configuration path:**
   ```bash
   python tools/ci/simulator.py run --config ./my-config.yml
   ```

3. **Use environment variable:**
   ```bash
   export CI_CONFIG_PATH="./my-config.yml"
   ```

### Issue: Invalid Configuration

**Symptoms:**
```
ConfigurationError: Invalid configuration format
YAML parsing error at line 15
```

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('ci-config.yml'))"
   ```

2. **Check indentation:**
   - Use spaces, not tabs
   - Maintain consistent indentation

3. **Use configuration template:**
   ```bash
   cp tools/ci/templates/ci_config_template.yaml ci-config.yml
   # Edit the template
   ```

### Issue: Check Not Available

**Symptoms:**
```
Warning: Check 'custom_check' is not available
```

**Solutions:**

1. **List available checks:**
   ```bash
   python tools/ci/simulator.py list
   ```

2. **Check spelling:**
   - Use exact check names: `code_quality`, `test_runner`, etc.

3. **Verify check implementation:**
   ```bash
   python tools/ci/simulator.py info code_quality
   ```

## Performance Issues

### Issue: Slow Execution

**Symptoms:**
- Tool takes very long to complete
- High CPU or memory usage
- System becomes unresponsive

**Solutions:**

1. **Enable parallel execution:**
   ```bash
   python tools/ci/simulator.py run --parallel 4
   ```

2. **Use selective execution:**
   ```bash
   # Run only necessary checks
   python tools/ci/simulator.py run code_quality
   ```

3. **Optimize configuration:**
   ```yaml
   # In ci-config.yml
   execution:
     max_parallel: 4
     timeout: 300
   checks:
     performance_analyzer:
       enabled: false  # Disable slow checks during development
   ```

4. **Monitor resource usage:**
   ```bash
   # Monitor during execution
   htop
   # or
   python tools/ci/simulator.py run --verbose
   ```

### Issue: Disk Space Problems

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Solutions:**

1. **Clean up old reports:**
   ```bash
   rm -rf reports/ci-simulation/old-*
   rm -rf .kiro/ci-history/old-*
   ```

2. **Configure cleanup:**
   ```yaml
   # In ci-config.yml
   cleanup:
     keep_reports: 10
     keep_history: 30
     auto_cleanup: true
   ```

3. **Use different output directory:**
   ```bash
   python tools/ci/simulator.py run --output-dir /tmp/ci-reports
   ```

## Git Hooks Issues

### Issue: Hook Installation Fails

**Symptoms:**
```
Error: Failed to install pre-commit hook
Permission denied: .git/hooks/pre-commit
```

**Solutions:**

1. **Check Git repository:**
   ```bash
   git status
   # Ensure you're in a Git repository
   ```

2. **Check permissions:**
   ```bash
   ls -la .git/hooks/
   chmod +x .git/hooks/pre-commit
   ```

3. **Manual installation:**
   ```bash
   cp tools/ci/templates/pre_commit_hook.sh .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

### Issue: Hook Execution Fails

**Symptoms:**
```
pre-commit hook failed with exit code 1
```

**Solutions:**

1. **Test hook manually:**
   ```bash
   python tools/ci/simulator.py hook test pre-commit
   ```

2. **Check hook configuration:**
   ```bash
   cat .git/hooks/pre-commit
   ```

3. **Debug hook execution:**
   ```bash
   # Add debug output to hook
   echo "Debug: Running CI simulation..." >> .git/hooks/pre-commit
   ```

### Issue: Hook Bypassed

**Symptoms:**
- Commits succeed without running checks
- Hook seems to be ignored

**Solutions:**

1. **Check hook executable:**
   ```bash
   ls -la .git/hooks/pre-commit
   # Should show executable permissions
   ```

2. **Verify hook content:**
   ```bash
   cat .git/hooks/pre-commit
   # Should contain CI simulation commands
   ```

3. **Test Git hooks:**
   ```bash
   git commit --dry-run
   ```

## Platform-Specific Issues

### Linux Issues

#### Issue: Display Server Problems

**Symptoms:**
```
Cannot connect to X server
DISPLAY environment variable not set
```

**Solutions:**

1. **Install virtual display:**
   ```bash
   sudo apt-get install xvfb
   ```

2. **Start virtual display:**
   ```bash
   Xvfb :99 -screen 0 1024x768x24 &
   export DISPLAY=:99
   ```

3. **Use xvfb-run:**
   ```bash
   xvfb-run -a python tools/ci/simulator.py run
   ```

#### Issue: Package Manager Problems

**Symptoms:**
```
E: Unable to locate package python3-pyqt5
```

**Solutions:**

1. **Update package lists:**
   ```bash
   sudo apt-get update
   ```

2. **Enable universe repository (Ubuntu):**
   ```bash
   sudo add-apt-repository universe
   ```

3. **Use alternative packages:**
   ```bash
   sudo apt-get install python3-pip
   pip3 install PyQt5
   ```

### macOS Issues

#### Issue: Xcode Tools Missing

**Symptoms:**
```
xcrun: error: invalid active developer path
```

**Solutions:**

1. **Install Xcode command line tools:**
   ```bash
   xcode-select --install
   ```

2. **Reset developer directory:**
   ```bash
   sudo xcode-select --reset
   ```

#### Issue: Homebrew Problems

**Symptoms:**
```
brew: command not found
```

**Solutions:**

1. **Install Homebrew:**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Add to PATH:**
   ```bash
   echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

### Windows Issues

#### Issue: Path Separator Problems

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'tools\ci\simulator.py'
```

**Solutions:**

1. **Use forward slashes:**
   ```cmd
   python tools/ci/simulator.py run
   ```

2. **Use PowerShell:**
   ```powershell
   python tools/ci/simulator.py run
   ```

#### Issue: Long Path Problems

**Symptoms:**
```
OSError: [Errno 36] File name too long
```

**Solutions:**

1. **Enable long paths (Windows 10+):**
   - Run `gpedit.msc`
   - Navigate to Computer Configuration > Administrative Templates > System > Filesystem
   - Enable "Enable Win32 long paths"

2. **Use shorter paths:**
   ```cmd
   cd C:\
   git clone <repository>
   ```

## Advanced Debugging

### Enable Debug Logging

```bash
# Environment variable
export CI_LOG_LEVEL=DEBUG

# Command line
python tools/ci/simulator.py run --verbose

# Configuration file
# In ci-config.yml
logging:
  level: DEBUG
  file: logs/debug.log
```

### Python Debugging

```bash
# Run with Python debugger
python -m pdb tools/ci/simulator.py run

# Add debug prints
python -c "
import sys
sys.path.insert(0, 'tools/ci')
from simulator import CISimulator
simulator = CISimulator()
print('Available checks:', simulator.orchestrator.get_available_checks())
"
```

### System Debugging

```bash
# Monitor system resources
htop
iotop
nethogs

# Check file descriptors
lsof -p <pid>

# Monitor disk usage
df -h
du -sh reports/
```

### Network Debugging

```bash
# Check network connectivity (for security scans)
ping pypi.org
curl -I https://pypi.org/simple/

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

## FAQ

### General Questions

**Q: Why is the tool running slowly?**
A: Common causes include:
- Running all checks simultaneously
- Large codebase with many files
- Insufficient system resources
- Network issues during security scans

Try using `--parallel 2` or running checks individually.

**Q: Can I run only specific checks?**
A: Yes, use:
```bash
python tools/ci/simulator.py run code_quality
python tools/ci/simulator.py run test_runner security_scanner
```

**Q: How do I skip failing checks temporarily?**
A: Use the exclude option:
```bash
python tools/ci/simulator.py run --all --exclude failing_check
```

### Configuration Questions

**Q: Where should I put my configuration file?**
A: You can use:
- `tools/ci/ci-config.yml` (tool-specific)
- `.kiro/ci-config.yml` (project-specific)
- Custom path with `--config` option

**Q: How do I disable a check permanently?**
A: In your configuration file:
```yaml
checks:
  check_name:
    enabled: false
```

**Q: Can I use different Python versions?**
A: Yes, specify them in configuration:
```yaml
python_versions:
  - "3.9"
  - "3.10"
  - "3.11"
```

### Error Questions

**Q: What does "Check not available" mean?**
A: The check's dependencies are not installed or the check is not implemented. Run:
```bash
python tools/ci/simulator.py list --detailed
```

**Q: Why do I get permission errors?**
A: Common causes:
- Not in a Git repository
- Insufficient file permissions
- Virtual environment issues

**Q: How do I fix Qt-related errors?**
A: Install Qt system packages and set environment variables:
```bash
sudo apt-get install python3-pyqt5
export QT_QPA_PLATFORM=offscreen
```

### Performance Questions

**Q: How can I make the tool faster?**
A: Try:
- Use `--parallel` for concurrent execution
- Run only necessary checks
- Use SSD storage for better I/O
- Increase system memory

**Q: Why does the first run take longer?**
A: The first run includes:
- Tool initialization
- Cache building
- Environment setup
- Baseline establishment

### Integration Questions

**Q: How do I integrate with my IDE?**
A: Most IDEs support external tools. Configure:
- Command: `python`
- Arguments: `tools/ci/simulator.py run`
- Working directory: project root

**Q: Can I use this in CI/CD pipelines?**
A: Yes, but it's designed for local use. For CI/CD, use your existing pipeline configuration.

**Q: How do I share configuration with my team?**
A: Commit your configuration files to version control:
```bash
git add .kiro/ci-config.yml tools/ci/ci-config.yml
git commit -m "Add CI simulation configuration"
```

## Getting Additional Help

If this troubleshooting guide doesn't resolve your issue:

1. **Check log files** for detailed error messages
2. **Run with verbose output** using `--verbose`
3. **Verify system requirements** and dependencies
4. **Test with minimal configuration** to isolate the problem
5. **Search existing issues** in the project repository
6. **Create a detailed bug report** with:
   - Operating system and version
   - Python version
   - Complete error message
   - Steps to reproduce
   - Configuration files (sanitized)

Remember to include relevant log files and configuration when seeking help!
