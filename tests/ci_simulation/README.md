# CI Simulation Tool Test Suite

This directory contains comprehensive tests for the CI simulation tool, including unit tests, integration tests, and performance tests.

## Test Structure

```
tests/ci_simulation/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Pytest configuration and fixtures
├── README.md                      # This file
├── run_unit_tests.py             # Unit test runner
│
├── test_models.py                 # Unit tests for data models
├── test_interfaces.py             # Unit tests for interfaces
├── test_config_manager.py         # Unit tests for configuration management
├── test_checkers.py               # Unit tests for all checker implementations
├── test_environment_managers.py   # Unit tests for environment managers
├── test_reporters.py              # Unit tests for report generators
├── test_orchestrator_and_error_handling.py  # Unit tests for orchestration and error handling
│
└── integration/                   # Integration tests
    ├── __init__.py
    ├── run_integration_tests.py   # Integration test runner
    ├── test_end_to_end_simulation.py        # End-to-end workflow tests
    ├── test_configuration_integration.py   # Configuration system integration tests
    └── test_error_recovery_integration.py  # Error recovery integration tests
```

## Runnin

### Unit Tests

Run all unit tests:
```bash
python tests/ci_simulation/run_unit_tests.py
```

Run specific component tests:
```bash
python tests/ci_simulation/run_unit_tests.py --component models
python tests/ci_simulation/run_unit_tests.py --component checkers
python tests/ci_simulation/run_unit_tests.py --component config
```

Run with coverage:
```bash
python tests/ci_simulation/run_unit_tests.py --coverage
```

Run in parallel:
```bash
python tests/ci_simulation/run_unit_tests.py --parallel
```

### Integration Tests

Run all integration tests:
```bash
python tests/ci_simulation/integration/run_integration_tests.py
```

Run specific integration test suites:
```bash
python tests/ci_simulation/integration/run_integration_tests.py --suite end_to_end
python tests/ci_simulation/integration/run_integration_tests.py --suite configuration
python tests/ci_simulation/integration/run_integration_tests.py --suite error_recovery
```

Run with verbose output and coverage:
```bash
python tests/ci_simulation/integration/run_integration_tests.py --verbose --coverage
```

### Using pytest directly

You can also run tests directly with pytest:

```bash
# Run all unit tests
pytest tests/ci_simulation/ -m "not integration"

# Run all integration tests
pytest tests/ci_simulation/ -m "integration"

# Run specific test file
pytest tests/ci_simulation/test_models.py

# Run with coverage
pytest tests/ci_simulation/ --cov=tools.ci --cov-report=html
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation:

- **Models Tests** (`test_models.py`): Test data models, serialization, and validation
- **Interfaces Tests** (`test_interfaces.py`): Test abstract interfaces and factory patterns
- **Configuration Tests** (`test_config_manager.py`): Test configuration loading, validation, and environment overrides
- **Checkers Tests** (`test_checkers.py`): Test all checker implementations (code quality, security, performance, etc.)
- **Environment Tests** (`test_environment_managers.py`): Test Python, Qt, and display environment management
- **Reporters Tests** (`test_reporters.py`): Test report generation in various formats
- **Orchestrator Tests** (`test_orchestrator_and_error_handling.py`): Test check orchestration and error handling

### Integration Tests

Integration tests verify complete workflows using real project files:

- **End-to-End Tests** (`test_end_to_end_simulation.py`): Complete CI simulation workflows
- **Configuration Integration** (`test_configuration_integration.py`): Configuration system with real files
- **Error Recovery Integration** (`test_error_recovery_integration.py`): Error handling and recovery scenarios

## Test Fixtures and Utilities

### Common Fixtures (conftest.py)

- `temp_dir`: Temporary directory for test files
- `sample_config`: Sample configuration for testing
- `sample_check_result`: Sample check result objects
- `sample_simulation_result`: Sample simulation result objects
- `mock_checker`: Mock checker implementation
- `mock_subprocess`: Mock subprocess execution
- `project_root`: Project root directory path

### Test Utilities

- `MockChecker`: Configurable mock checker for testing
- `MockEnvironment`: Mock environment for testing environment managers
- Automatic cleanup of test files after each test

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow tests that may be skipped
- `@pytest.mark.performance`: Performance-related tests

## Coverage Requirements

The test suite aims for high code coverage:

- **Unit Tests**: >90% coverage of individual components
- **Integration Tests**: >80% coverage of complete workflows
- **Overall**: >85% total coverage

## Dependencies

Test dependencies are defined in the main `requirements.txt`:

- `pytest`: Test framework
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Mocking utilities
- `pytest-timeout`: Test timeout handling
- `pytest-xdist`: Parallel test execution

## Continuous Integration

Tests are designed to run in CI environments:

- All external dependencies are mocked in unit tests
- Integration tests use temporary directories and cleanup automatically
- Tests are platform-independent (Windows, Linux, macOS)
- Parallel execution is supported for faster CI runs

## Writing New Tests

### Unit Test Guidelines

1. Test one component at a time
2. Mock external dependencies
3. Use descriptive test names
4. Include both positive and negative test cases
5. Test error conditions and edge cases

### Integration Test Guidelines

1. Test complete workflows
2. Use real project files when possible
3. Clean up temporary files
4. Mark slow tests appropriately
5. Test error recovery scenarios

### Example Unit Test

```python
def test_check_result_creation(self):
    """Test basic CheckResult creation."""
    result = CheckResult(
        name="test_check",
        status=CheckStatus.SUCCESS,
        duration=1.5
    )

    assert result.name == "test_check"
    assert result.status == CheckStatus.SUCCESS
    assert result.duration == 1.5
    assert result.is_successful is True
```

### Example Integration Test

```python
@pytest.mark.integration
def test_full_simulation_workflow(self, project_files_setup):
    """Test complete CI simulation workflow."""
    project_dir = project_files_setup

    simulator = CISimulator(str(project_dir / "ci-config.yaml"))
    result = simulator.run(checks=["code_quality", "tests"])

    assert isinstance(result, SimulationResult)
    assert result.overall_status in [CheckStatus.SUCCESS, CheckStatus.WARNING]
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Missing Dependencies**: Install test dependencies with `pip install -r requirements.txt`
3. **Permission Errors**: Ensure write permissions for temporary directories
4. **Timeout Errors**: Increase timeout for slow integration tests

### Debug Mode

Run tests with debug output:
```bash
pytest tests/ci_simulation/ -v -s --tb=long
```

### Test Isolation

If tests interfere with each other:
```bash
pytest tests/ci_simulation/ --forked
```
