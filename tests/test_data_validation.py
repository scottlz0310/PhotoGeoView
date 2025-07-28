"""
Test suite for Data Validation System - Task 7 Implementation

Tests the data validation functionality for AI integration models.

Author: Kiro AI Integration System
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.integration.data_validation import DataValidator, ValidationResult, ValidationSeverity
from src.integration.models import ImageMetadata, ThemeConfiguration, ApplicationState, ProcessingStatus, AIComponent
from src.integration.logging_system import LoggerSystem
from src.integration.error_handling import IntegratedErrorHandler


class TestDataValidator:
    """Test suite for DataValidator"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def validator(self):
        """Create DataValidator instance for testing"""
        logger_system = LoggerSystem()
        error_handler = IntegratedErrorHandler(logger_system)
        return DataValidator(logger_system, error_handler)

    @pytest.fixture
    def sample_image_metadata(self, temp_dir):
        """Create sample ImageMetadata for testing"""
        test_image = temp_dir / "test_image.jpg"
        test_image.write_text("fake image content")

        return ImageMetadata(
            file_path=test_image,
            file_size=1024,
            created_date=datetime.now(),
            modified_date=datetime.now(),
            file_format=".jpg",
            camera_make="Canon",
            camera_model="EOS R5",
            latitude=35.6762,
            longitude=139.6503,
            width=1920,
            height=1080,
            processing_status=ProcessingStatus.COMPLETED,
            ai_processor=AIComponent.COPILOT
        )

    @pytest.fixture
    def sample_theme_configuration(self):
        """Create sample ThemeConfiguration for testing"""
        return ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            description="A test theme",
            version="1.0.0",
            color_scheme={
                "background": "#ffffff",
                "foreground": "#000000",
                "primary": "#007acc",
                "secondary": "#6c757d"
            },
            accessibility_features={
                "keyboard_navigation": True,
                "focus_indicators": True,
                "high_contrast": False
            }
        )

    @pytest.fixture
    def sample_application_state(self, temp_dir):
        """Create sample ApplicationState for testing"""
        test_folder = temp_dir / "test_folder"
        test_folder.mkdir()

        return ApplicationState(
            current_folder=test_folder,
            current_theme="default",
            thumbnail_size=150,
            performance_mode="balanced",
            image_sort_mode="name",
            fit_mode="fit_window",
            exif_display_mode="detailed",
            image_sort_ascending=True
        )

    def test_validator_initialization(self, validator):
        """Test DataValidator initialization"""
        assert validator is not None
        assert validator.validation_rules is not None
        assert validator.supported_image_formats is not None
        assert validator.gps_ranges is not None
        assert validator.color_patterns is not None

    def test_validate_image_metadata_valid(self, validator, sample_image_metadata):
        """Test validation of valid ImageMetadata"""
        result = validator.validate_image_metadata(sample_image_metadata)

        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_image_metadata_missing_required_fields(self, validator):
        """Test validation with missing required fields"""
        # Create ImageMetadata with missing required fields
        metadata = ImageMetadata(
            file_path=None,  # Missing required field
            file_size=None,  # Missing required field
            created_date=datetime.now(),
            modified_date=datetime.now()
        )

        result = validator.validate_image_metadata(metadata)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("file_path" in error["field"] for error in result.errors)
        assert any("file_size" in error["field"] for error in result.errors)

    def test_validate_image_metadata_invalid_gps(self, validator, sample_image_metadata):
        """Test validation with invalid GPS coordinates"""
        # Set invalid GPS coordinates
        sample_image_metadata.latitude = 95.0  # Invalid latitude (> 90)
        sample_image_metadata.longitude = 185.0  # Invalid longitude (> 180)

        result = validator.validate_image_metadata(sample_image_metadata)

        assert not result.is_valid
        assert len(result.errors) >= 2
        assert any("latitude" in error["field"] for error in result.errors)
        assert any("longitude" in error["field"] for error in result.errors)

    def test_validate_image_metadata_nonexistent_file(self, validator, temp_dir):
        """Test validation with non-existent file"""
        nonexistent_file = temp_dir / "nonexistent.jpg"

        metadata = ImageMetadata(
            file_path=nonexistent_file,
            file_size=1024,
            created_date=datetime.now(),
            modified_date=datetime.now()
        )

        result = validator.validate_image_metadata(metadata)

        # Should have warnings about non-existent file
        assert len(result.warnings) > 0
        assert any("does not exist" in warning["message"] for warning in result.warnings)

    def test_validate_image_metadata_unsupported_format(self, validator, temp_dir):
        """Test validation with unsupported image format"""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("fake content")

        metadata = ImageMetadata(
            file_path=unsupported_file,
            file_size=1024,
            created_date=datetime.now(),
            modified_date=datetime.now()
        )

        result = validator.validate_image_metadata(metadata)

        # Should have warnings about unsupported format
        assert len(result.warnings) > 0
        assert any("Unsupported image format" in warning["message"] for warning in result.warnings)

    def test_validate_theme_configuration_valid(self, validator, sample_theme_configuration):
        """Test validation of valid ThemeConfiguration"""
        result = validator.validate_theme_configuration(sample_theme_configuration)

        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_theme_configuration_missing_required_fields(self, validator):
        """Test validation with missing required fields"""
        theme = ThemeConfiguration(
            name="",  # Empty required field
            display_name="",  # Empty required field
            color_scheme={}
        )

        result = validator.validate_theme_configuration(theme)

        assert not result.is_valid
        assert len(result.errors) >= 2
        assert any("name" in error["field"] for error in result.errors)
        assert any("display_name" in error["field"] for error in result.errors)

    def test_validate_theme_configuration_invalid_name(self, validator):
        """Test validation with invalid theme name"""
        theme = ThemeConfiguration(
            name="invalid name with spaces!",  # Invalid characters
            display_name="Valid Display Name",
            color_scheme={}
        )

        result = validator.validate_theme_configuration(theme)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("name" in error["field"] and "alphanumeric" in error["message"] for error in result.errors)

    def test_validate_theme_configuration_invalid_colors(self, validator):
        """Test validation with invalid color formats"""
        theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            color_scheme={
                "background": "invalid_color",  # Invalid color format
                "foreground": "#gggggg",  # Invalid hex color
                "primary": "#007acc",  # Valid color
                "secondary": "rgb(255, 0, 0)"  # Valid RGB color
            }
        )

        result = validator.validate_theme_configuration(theme)

        assert not result.is_valid
        assert len(result.errors) >= 2
        assert any("color_scheme" in error["field"] and "Invalid color format" in error["message"] for error in result.errors)

    def test_validate_theme_configuration_missing_required_colors(self, validator):
        """Test validation with missing required colors"""
        theme = ThemeConfiguration(
            name="test_theme",
            display_name="Test Theme",
            color_scheme={
                "background": "#ffffff",
                # Missing required colors: foreground, primary, secondary
            }
        )

        result = validator.validate_theme_configuration(theme)

        # Should have warnings about missing required colors
        assert len(result.warnings) >= 3
        assert any("Missing required color" in warning["message"] for warning in result.warnings)

    def test_validate_application_state_valid(self, validator, sample_application_state):
        """Test validation of valid ApplicationState"""
        result = validator.validate_application_state(sample_application_state)

        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_application_state_invalid_thumbnail_size(self, validator, sample_application_state):
        """Test validation with invalid thumbnail size"""
        sample_application_state.thumbnail_size = 1000  # Outside recommended range

        result = validator.validate_application_state(sample_application_state)

        # Should have warnings about thumbnail size
        assert len(result.warnings) > 0
        assert any("thumbnail_size" in warning["field"] for warning in result.warnings)

    def test_validate_application_state_invalid_performance_mode(self, validator, sample_application_state):
        """Test validation with invalid performance mode"""
        sample_application_state.performance_mode = "invalid_mode"

        result = validator.validate_application_state(sample_application_state)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("performance_mode" in error["field"] for error in result.errors)

    def test_validate_application_state_invalid_sort_mode(self, validator, sample_application_state):
        """Test validation with invalid sort mode"""
        sample_application_state.image_sort_mode = "invalid_sort"

        result = validator.validate_application_state(sample_application_state)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("image_sort_mode" in error["field"] for error in result.errors)

    def test_validate_application_state_nonexistent_folder(self, validator, temp_dir):
        """Test validation with non-existent current folder"""
        nonexistent_folder = temp_dir / "nonexistent_folder"

        state = ApplicationState(
            current_folder=nonexistent_folder,
            current_theme="default",
            performance_mode="balanced"
        )

        result = validator.validate_application_state(state)

        # Should have warnings about non-existent folder
        assert len(result.warnings) > 0
        assert any("does not exist" in warning["message"] for warning in result.warnings)

    def test_validate_all_models(self, validator, sample_image_metadata, sample_theme_configuration, sample_application_state):
        """Test validation of multiple models at once"""
        results = validator.validate_all_models(
            image_metadata=sample_image_metadata,
            theme_config=sample_theme_configuration,
            app_state=sample_application_state
        )

        assert isinstance(results, dict)
        assert "image_metadata" in results
        assert "theme_configuration" in results
        assert "application_state" in results

        # All should be valid
        for model_name, result in results.items():
            assert isinstance(result, ValidationResult)
            assert result.is_valid

    def test_color_validation(self, validator):
        """Test color format validation"""
        # Valid colors
        assert validator._is_valid_color("#ffffff")
        assert validator._is_valid_color("#000")
        assert validator._is_valid_color("rgb(255, 0, 0)")
        assert validator._is_valid_color("rgba(255, 0, 0, 0.5)")

        # Invalid colors
        assert not validator._is_valid_color("invalid")
        assert not validator._is_valid_color("#gggggg")
        assert not validator._is_valid_color("rgb(256, 0, 0)")  # Invalid RGB value
        assert not validator._is_valid_color(123)  # Not a string

    def test_validation_result_properties(self):
        """Test ValidationResult properties and methods"""
        result = ValidationResult(is_valid=True)

        # Test initial state
        assert result.is_valid
        assert result.total_issues == 0
        assert not result.has_errors
        assert not result.has_warnings

        # Add issues
        result.add_issue(ValidationSeverity.WARNING, "test_field", "Test warning")
        result.add_issue(ValidationSeverity.ERROR, "test_field", "Test error")
        result.add_issue(ValidationSeverity.INFO, "test_field", "Test info")

        # Test updated state
        assert not result.is_valid  # Should be False due to error
        assert result.total_issues == 3
        assert result.has_errors
        assert result.has_warnings
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.info) == 1

    def test_validation_with_exception_handling(self, validator):
        """Test validation with exception handling"""
        # Create invalid metadata that might cause exceptions
        invalid_metadata = Mock()
        invalid_metadata.file_path = "not_a_path_object"
        invalid_metadata.processing_status = "not_an_enum"

        # Should handle exceptions gracefully
        result = validator.validate_image_metadata(invalid_metadata)

        # Should have critical errors due to exceptions
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any(error["field"] == "validation_error" for error in result.errors)


class TestValidationResult:
    """Test suite for ValidationResult"""

    def test_validation_result_creation(self):
        """Test ValidationResult creation"""
        result = ValidationResult(is_valid=True)

        assert result.is_valid
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.info, list)
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.info) == 0

    def test_add_issue_error(self):
        """Test adding error issues"""
        result = ValidationResult(is_valid=True)

        result.add_issue(ValidationSeverity.ERROR, "test_field", "Test error", "test_value")

        assert not result.is_valid  # Should become False
        assert len(result.errors) == 1
        assert result.errors[0]["field"] == "test_field"
        assert result.errors[0]["message"] == "Test error"
        assert result.errors[0]["value"] == "test_value"
        assert "timestamp" in result.errors[0]

    def test_add_issue_warning(self):
        """Test adding warning issues"""
        result = ValidationResult(is_valid=True)

        result.add_issue(ValidationSeverity.WARNING, "test_field", "Test warning")

        assert result.is_valid  # Should remain True
        assert len(result.warnings) == 1
        assert result.warnings[0]["field"] == "test_field"
        assert result.warnings[0]["message"] == "Test warning"

    def test_add_issue_info(self):
        """Test adding info issues"""
        result = ValidationResult(is_valid=True)

        result.add_issue(ValidationSeverity.INFO, "test_field", "Test info")

        assert result.is_valid  # Should remain True
        assert len(result.info) == 1
        assert result.info[0]["field"] == "test_field"
        assert result.info[0]["message"] == "Test info"

    def test_add_issue_critical(self):
        """Test adding critical issues"""
        result = ValidationResult(is_valid=True)

        result.add_issue(ValidationSeverity.CRITICAL, "test_field", "Test critical")

        assert not result.is_valid  # Should become False
        assert len(result.errors) == 1  # Critical issues go to errors


if __name__ == "__main__":
    pytest.main([__file__])
