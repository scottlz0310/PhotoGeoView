# CI Simulation Tool - Installation Guide

## Overview

This guide provides detailed instructions for installing and setting up the CI Simulation Tool in your development environment.

## System Requirements

### Minimum Requirements

- **Operating System:** Linux, macOS, or Windows
- **Python:** 3.9 or higher (3.10+ recommended)
- **Git:** 2.0 or higher
- **Memory:** 2GB RAM minecommended
- **Disk Space:** 500MB for tool and dependencies

### Recommended Requirements

- **Python:** 3.11 (latest stable)
- **Memory:** 8GB RAM for parallel execution
- **CPU:** Multi-core processor for parallel checks
- **Virtual Environment:** conda, venv, or virtualenv

## Installation Methods

### Method 1: Direct Installation (Recommended)

This method assumes the CI simulation tool is already part of your project.

1. **Navigate to your project directory:**
   ```bash
   cd /path/to/your/project
   ```

2. **Verify Python version:**
   ```bash
   python --version
   # Should show Python 3.9 or higher
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   python tools/ci/simulator.py --version
   ```

5. **Run initial setup:**
   ```bash
   python tools/ci/simulator.py --setup-hooks
   ```

### Method 2: Virtual Environment Installation

1. **Create virtual environment:**
   ```bash
   # Using venv
   python -m venv ci-simulation-env
   source ci-simulation-env/bin/activate  # Linux/macOS
   # or
   ci-simulation-env\Scripts\activate     # Windows

   # Using conda
   conda create -n ci-simulation python=3.11
   conda activate ci-simulation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python tools/ci/simulator.py --version
   ```

### Method 3: Development Installation

For developers who want to modify or extend the tool:

1. **Clone or navigate to project:**
   ```bash
   cd /path/to/your/project
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

3. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Run tests to verify installation:**
   ```bash
   python -m pytest tools/ci/test_*.py
   ```

## System-Specific Setup

### Linux (Ubuntu/Debian)

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-dev python3-pip python3-venv
   ```

2. **For Qt applications (like PhotoGeoView):**
   ```bash
   sudo apt-get install -y python3-pyqt5 python3-pyqt5-dev
   sudo apt-get install -y xvfb  # For headless testing
   ```

3. **For security scanning:**
   ```bash
   sudo apt-get install -y build-essential
   ```

### macOS

1. **Install Homebrew (if not already installed):**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python:**
   ```bash
   brew install python@3.11
   ```

3. **For Qt applications:**
   ```bash
   brew install pyqt5
   ```

4. **Install Xcode command line tools:**
   ```bash
   xcode-select --install
   ```

### Windows

1. **Install Python from python.org or Microsoft Store**

2. **Install Git for Windows:**
   - Download from https://git-scm.com/download/win
   - Ensure Git is added to PATH

3. **Install Visual Studio Build Tools (for some dependencies):**
   - Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/

4. **For Qt applications:**
   ```cmd
   pip install PyQt5
   ```

## Tool Dependencies

The CI simulation tool requires various external tools depending on which checks you want to run:

### Code Quality Tools

```bash
# Essential code quality tools
pip install black isort flake8 mypy

# Optional but recommended
pip install pylint autopep8 yapf
```

### Testing Tools

```bash
# Core testing framework
pip install pytest pytest-cov pytest-xvfb

# Additional testing tools
pip install pytest-mock pytest-asyncio pytest-qt
```

### Security Tools

```bash
# Security scanning tools
pip install safety bandit

# Optional security tools
pip install semgrep
```

### Performance Tools

```bash
# Performance monitoring
pip install psutil memory-profiler

# Benchmarking
pip install pytest-benchmark
```

### AI Integration Tools

```bash
# For AI component testing
pip install requests aiohttp

# For configuration management
pip install pyyaml toml
```

## Configuration Setup

### 1. Create Configuration Directory

```bash
mkdir -p .kiro/settings
mkdir -p tools/ci/config
```

### 2. Create Basic Configuration

Create `tools/ci/ci-config.yml`:

```yaml
# Basic configuration
python_versions:
  - "3.10"  # Adjust to your available versions

checks:
  code_quality:
    enabled: true
  test_runner:
    enabled: true
  security_scanner:
    enabled: true
  performance_analyzer:
    enabled: false  # Enable when needed

output:
  directory: "reports/ci-simulation"
  formats: ["markdown"]

execution:
  max_parallel: 2
  timeout: 600
```

### 3. Project-Specific Configuration

Create `.kiro/ci-config.yml`:

```yaml
# Project-specific settings
project:
  name: "YourProject"
  type: "python_application"

# Override global settings
checks:
  code_quality:
    black:
      line_length: 88
    mypy:
      strict: false  # Adjust based on your project
```

## Environment Setup

### 1. Environment Variables

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# CI Simulation Tool settings
export CI_CONFIG_PATH="$HOME/.kiro/ci-config.yml"
export CI_LOG_LEVEL="INFO"
export CI_OUTPUT_DIR="./reports"

# Qt settings (for Qt applications)
export QT_QPA_PLATFORM="offscreen"
export DISPLAY=":99"
```

### 2. Virtual Display Setup (Linux)

For headless testing of GUI applications:

```bash
# Install Xvfb
sudo apt-get install xvfb

# Start virtual display
Xvfb :99 -screen 0 1024x768x24 &

# Or use xvfb-run for automatic management
alias ci-test="xvfb-run -a python tools/ci/simulator.py"
```

### 3. Git Configuration

Configure Git hooks directory (optional):

```bash
# Set custom hooks directory
git config core.hooksPath .githooks

# Or use default .git/hooks (recommended)
```

## Verification

### 1. Basic Functionality Test

```bash
# Check version
python tools/ci/simulator.py --version

# List available checks
python tools/ci/simulator.py list

# Run a simple check
python tools/ci/simulator.py run code_quality --timeout 60
```

### 2. Full System Test

```bash
# Run all available checks
python tools/ci/simulator.py run --timeout 300

# Check generated reports
ls -la reports/ci-simulation/
```

### 3. Git Hooks Test

```bash
# Install hooks
python tools/ci/simulator.py hook setup

# Test pre-commit hook
python tools/ci/simulator.py hook test pre-commit

# Check hook status
python tools/ci/simulator.py hook status
```

## Troubleshooting Installation

### Common Issues

#### 1. Python Version Issues

**Problem:** `Python version not supported`

**Solution:**
```bash
# Check Python version
python --version

# Install correct version using pyenv
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0
```

#### 2. Permission Errors

**Problem:** `Permission denied` during installation

**Solution:**
```bash
# Use user installation
pip install --user -r requirements.txt

# Or fix permissions
sudo chown -R $USER:$USER ~/.local/
```

#### 3. Missing System Dependencies

**Problem:** `Failed building wheel for package`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev build-essential

# macOS
xcode-select --install

# Windows
# Install Visual Studio Build Tools
```

#### 4. Qt Dependencies Issues

**Problem:** `Qt platform plugin could not be initialized`

**Solution:**
```bash
# Install Qt system packages
sudo apt-get install python3-pyqt5

# Set environment variables
export QT_QPA_PLATFORM=offscreen

# Install virtual display
sudo apt-get install xvfb
```

### Debug Installation

Enable verbose logging during installation:

```bash
# Verbose pip installation
pip install -v -r requirements.txt

# Debug tool execution
python tools/ci/simulator.py --verbose list
```

### Verify Dependencies

Check all required tools are available:

```bash
# Check Python tools
python -c "import black, isort, flake8, mypy; print('Code quality tools OK')"

# Check system tools
which git
which python

# Check Qt (if needed)
python -c "import PyQt5; print('Qt OK')"
```

## Post-Installation Setup

### 1. Team Setup

For team environments, create a setup script:

```bash
#!/bin/bash
# setup-ci-tool.sh

echo "Setting up CI Simulation Tool..."

# Check Python version
python_version=$(python --version 2>&1 | cut -d' ' -f2)
echo "Python version: $python_version"

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp tools/ci/config/ci-config.template.yml .kiro/ci-config.yml

# Install Git hooks
python tools/ci/simulator.py hook setup

echo "Setup complete! Run 'python tools/ci/simulator.py list' to verify."
```

### 2. IDE Integration

#### VS Code

Add to `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "CI Simulation",
            "type": "shell",
            "command": "python",
            "args": ["tools/ci/simulator.py", "run"],
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        }
    ]
}
```

#### PyCharm

Create a run configuration:
- Script path: `tools/ci/simulator.py`
- Parameters: `run`
- Working directory: `$ProjectFileDir$`

### 3. Continuous Integration

Add to your CI pipeline to ensure the tool works:

```yaml
# .github/workflows/ci-tool-test.yml
name: CI Tool Test
on: [push, pull_request]

jobs:
  test-ci-tool:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python tools/ci/simulator.py list
      - run: python tools/ci/simulator.py run --timeout 300
```

## Next Steps

After successful installation:

1. **Read the [User Guide](USER_GUIDE.md)** for detailed usage instructions
2. **Configure the tool** for your specific project needs
3. **Set up Git hooks** for automatic checking
4. **Train your team** on using the tool effectively
5. **Integrate with your IDE** for seamless development

## Getting Help

If you encounter issues during installation:

1. **Check the [Troubleshooting section](USER_GUIDE.md#troubleshooting)** in the User Guide
2. **Review log files** in the `logs/` directory
3. **Run with verbose output** using `--verbose` flag
4. **Check system requirements** and dependencies
5. **Consult the [FAQ](USER_GUIDE.md#faq)** for common questions

For additional support, please refer to the project documentation or contact the development team.
