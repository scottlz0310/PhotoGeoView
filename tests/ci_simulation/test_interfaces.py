"""
Unit tests for core interfaces and abstract classes.
"""

import pytest
from unittest.mock import Mock, MagicMock
from abc import ABC

from interfaces import (
    CheckerInterface, EnvironmentManagerInterface, ReporterInterface,
    OrchestratorInterface, CheckerFactory, CISimulationError,
    CheckerError, EnvironmentError, ConfigurationError,pendencyError
)
from models import CheckResult, CheckStatus, SimulationResult, CheckTask


class ConcreteChecker(CheckerInterface):
    """Concrete implementation of CheckerInterface for testing."""

    def __init__(self, config):
        super().__init__(config)
        self._name = "test_checker"
        self._check_type = "test"
        self._dependencies = ["pytest"]

    @property
    def name(self):
        return self._name

    @property
    def check_type(self):
        return self._check_type

    @property
    def dependencies(self):
        return self._dependencies

    def is_available(self):
        return True

    def run_check(self, **kwargs):
        return CheckResult(
            name=self.name,
            status=CheckStatus.SUCCESS,
            duration=1.0,
            output="Test check completed"
        )


class ConcreteEnvironmentManager(EnvironmentManagerInterface):
    """Concrete implementation of EnvironmentManagerInterface for testing."""

    def setup_environment(self, requirements):
        return True

    def cleanup_environment(self):
        pass

    def is_environment_ready(self):
        return True


class ConcreteReporter(ReporterInterface):
    """Concrete implementation of ReporterInterface for testing."""

    @property
    def format_name(self):
        return "test"

    @property
    def file_extension(self):
        return ".test"

    def generate_report(self, result, output_path):
        return output_path


class ConcreteOrchestrator(OrchestratorInterface):
    """Concrete implementation of OrchestratorInterface for testing."""

    def execute_checks(self, tasks):
        return {}

    def resolve_dependencies(self, task_names):
        return task_names


class TestCheckerInterface:
    """Test cases for CheckerInterface."""

    def test_checker_interface_is_abstract(self):
        """Test that CheckerInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CheckerInterface({})

    def test_concrete_checker_implementation(self, sample_config):
        """Test concrete implementation of CheckerInterface."""
        checker = ConcreteChecker(sample_config)

        assert checker.name == "test_checker"
        assert checker.check_type == "test"
        assert checker.dependencies == ["pytest"]
        assert checker.is_available() is True
        assert checker.config == sample_config

    def test_checker_run_check(self, sample_config):
        """Test checker run_check method."""
        checker = ConcreteChecker(sample_config)
        result = checker.run_check()

        assert isinstance(result, CheckResult)
        assert result.name == "test_checker"
        assert result.status == CheckStatus.SUCCESS
        assert result.duration == 1.0

    def test_checker_validate_config(self, sample_config):
        """Test checker config validation."""
        checker = ConcreteChecker(sample_config)
        errors = checker.validate_config()
        assert errors == []

        # Test with invalid config
        invalid_checker = ConcreteChecker("not_a_dict")
        errors = invalid_checker.validate_config()
        assert len(errors) > 0
        assert "Configuration must be a dictionary" in errors[0]

    def test_checker_get_default_config(self, sample_config):
        """Test checker default config."""
        checker = ConcreteChecker(sample_config)
        default_config = checker.get_default_config()
        assert isinstance(default_config, dict)

    def test_checker_cleanup(self, sample_config):
        """Test checker cleanup method."""
        checker = ConcreteChecker(sample_config)
        # Should not raise any exceptions
        checker.cleanup()


class TestEnvironmentManagerInterface:
    """Test cases for EnvironmentManagerInterface."""

    def test_environment_manager_is_abstract(self):
        """Test that EnvironmentManagerInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EnvironmentManagerInterface()

    def test_concrete_environment_manager(self):
        """Test concrete implementation of EnvironmentManagerInterface."""
        manager = ConcreteEnvironmentManager()

        assert manager.setup_environment({}) is True
        assert manager.is_environment_ready() is True
        # cleanup_environment should not raise
        manager.cleanup_environment()


class TestReporterInterface:
    """Test cases for ReporterInterface."""

    def test_reporter_interface_is_abstract(self):
        """Test that ReporterInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ReporterInterface()

    def test_concrete_reporter(self, sample_simulation_result):
        """Test concrete implementation of ReporterInterface."""
        reporter = ConcreteReporter()

        assert reporter.format_name == "test"
        assert reporter.file_extension == ".test"

        output_path = "test_report.test"
        result_path = reporter.generate_report(sample_simulation_result, output_path)
        assert result_path == output_path

    def test_reporter_validate_output_path(self):
        """Test reporter output path validation."""
        reporter = ConcreteReporter()

        assert reporter.validate_output_path("report.test") is True
        assert reporter.validate_output_path("report.txt") is False


class TestOrchestratorInterface:
    """Test cases for OrchestratorInterface."""

    def test_orchestrator_interface_is_abstract(self):
        """Test that OrchestratorInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            OrchestratorInterface()

    def test_concrete_orchestrator(self, sample_check_tasks):
        """Test concrete implementation of OrchestratorInterface."""
        orchestrator = ConcreteOrchestrator()

        results = orchestrator.execute_checks(sample_check_tasks)
        assert isinstance(results, dict)

        task_names = ["task1", "task2"]
        resolved = orchestrator.resolve_dependencies(task_names)
        assert resolved == task_names


class TestCheckerFactory:
    """Test cases for CheckerFactory."""

    def test_register_checker(self, sample_config):
        """Test registering a checker with the factory."""
        CheckerFactory.register_checker("test_checker", ConcreteChecker)

        assert CheckerFactory.is_checker_available("test_checker")
        assert "test_checker" in CheckerFactory.get_available_checkers()

    def test_register_invalid_checker(self):
        """Test registering an invalid checker class."""
        class InvalidChecker:
            pass

        with pytest.raises(ValueError, match="Checker class must implement CheckerInterface"):
            CheckerFactory.register_checker("invalid", InvalidChecker)

    def test_create_checker(self, sample_config):
        """Test creating a checker instance."""
        CheckerFactory.register_checker("concrete_test", ConcreteChecker)

        checker = CheckerFactory.create_checker("concrete_test", sample_config)
        assert isinstance(checker, ConcreteChecker)
        assert checker.config == sample_config

    def test_create_unknown_checker(self, sample_config):
        """Test creating an unknown checker type."""
        with pytest.raises(ValueError, match="Unknown check type 'unknown'"):
            CheckerFactory.create_checker("unknown", sample_config)

    def test_get_available_checkers(self):
        """Test getting list of available checkers."""
        # Clear any existing checkers
        CheckerFactory._checkers.clear()

        CheckerFactory.register_checker("checker1", ConcreteChecker)
        CheckerFactory.register_checker("checker2", ConcreteChecker)

        available = CheckerFactory.get_available_checkers()
        assert "checker1" in available
        assert "checker2" in available
        assert len(available) == 2

    def test_is_checker_available(self):
        """Test checking if a checker is available."""
        CheckerFactory._checkers.clear()
        CheckerFactory.register_checker("available_checker", ConcreteChecker)

        assert CheckerFactory.is_checker_available("available_checker") is True
        assert CheckerFactory.is_checker_available("unavailable_checker") is False


class TestExceptionClasses:
    """Test cases for custom exception classes."""

    def test_ci_simulation_error(self):
        """Test CISimulationError base exception."""
        error = CISimulationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_checker_error(self):
        """Test CheckerError exception."""
        original_error = ValueError("Original error")
        error = CheckerError("test_checker", "Check failed", original_error)

        assert error.checker_name == "test_checker"
        assert error.original_error == original_error
        assert str(error) == "test_checker: Check failed"
        assert isinstance(error, CISimulationError)

    def test_checker_error_without_original(self):
        """Test CheckerError without original error."""
        error = CheckerError("test_checker", "Check failed")

        assert error.checker_name == "test_checker"
        assert error.original_error is None
        assert str(error) == "test_checker: Check failed"

    def test_environment_error(self):
        """Test EnvironmentError exception."""
        error = EnvironmentError("Environment setup failed")
        assert str(error) == "Environment setup failed"
        assert isinstance(error, CISimulationError)

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, CISimulationError)

    def test_dependency_error(self):
        """Test DependencyError exception."""
        missing_deps = ["pytest", "black"]
        error = DependencyError(missing_deps)

        assert error.missing_dependencies == missing_deps
        assert "Missing required dependencies: pytest, black" in str(error)
        assert isinstance(error, CISimulationError)

    def test_dependency_error_with_custom_message(self):
        """Test DependencyError with custom message."""
        missing_deps = ["mypy"]
        custom_message = "Type checker not available"
        error = DependencyError(missing_deps, custom_message)

        assert error.missing_dependencies == missing_deps
        assert str(error) == custom_message


class TestProtocols:
    """Test protocol definitions."""

    def test_configurable_protocol(self):
        """Test Configurable protocol."""
        class ConfigurableClass:
            def configure(self, config):
                self.config = config

        obj = ConfigurableClass()
        obj.configure({"key": "value"})
        assert obj.config == {"key": "value"}

    def test_validatable_protocol(self):
        """Test Validatable protocol."""
        class ValidatableClass:
            def __init__(self, valid=True):
                self.valid = valid

            def validate(self):
                return [] if self.valid else ["Invalid state"]

        valid_obj = ValidatableClass(True)
        invalid_obj = ValidatableClass(False)

        assert valid_obj.validate() == []
        assert invalid_obj.validate() == ["Invalid state"]

    def test_serializable_protocol(self):
        """Test Serializable protocol."""
        class SerializableClass:
            def __init__(self, data):
                self.data = data

            def to_dict(self):
                return {"data": self.data}

            @classmethod
            def from_dict(cls, data):
                return cls(data["data"])

        obj = SerializableClass("test_data")
        data_dict = obj.to_dict()
        restored_obj = SerializableClass.from_dict(data_dict)

        assert data_dict == {"data": "test_data"}
        assert restored_obj.data == "test_data"


class TestInterfaceIntegration:
    """Test integration between different interfaces."""

    def test_checker_with_factory(self, sample_config):
        """Test checker creation and usage through factory."""
        # Register checker
        CheckerFactory.register_checker("integration_test", ConcreteChecker)

        # Create checker through factory
        checker = CheckerFactory.create_checker("integration_test", sample_config)

        # Verify checker functionality
        assert checker.is_available()
        result = checker.run_check()
        assert result.status == CheckStatus.SUCCESS

        # Cleanup
        checker.cleanup()

    def test_multiple_interface_implementations(self, sample_config, sample_simulation_result):
        """Test using multiple interface implementations together."""
        # Create instances of different interfaces
        checker = ConcreteChecker(sample_config)
        env_manager = ConcreteEnvironmentManager()
        reporter = ConcreteReporter()
        orchestrator = ConcreteOrchestrator()

        # Test they work together
        assert checker.is_available()
        assert env_manager.is_environment_ready()

        report_path = reporter.generate_report(sample_simulation_result, "test.test")
        assert report_path == "test.test"

        tasks = [CheckTask("test", "test")]
        results = orchestrator.execute_checks(tasks)
        assert isinstance(results, dict)
