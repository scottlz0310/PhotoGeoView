"""
Data Validation System for AI Integration

Provides comprehensive validation for all data models used in the AI integration system.

Author: Kiro AI Integration System
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from .models import (
    ImageMetadata, ThemeConfiguration, ApplicationState,
    CacheEntry, PerformanceMetrics, ProcessingStatus, AIComponent
)
from .logging_system import LoggerSystem
from .error_handling import IntegratedErrorHandler, ErrorCategory


class ValidationSeverity(Enum):
    """Validation error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    info: List[Dict[str, Any]] = field(default_factory=list)

    def add_issue(self, severity: ValidationSeverity, field: str, message: str, value: Any = None):
        """Add a validation issue"""
        issue = {
            "field": field,
            "message": message,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

        if severity == ValidationSeverity.ERROR or severity == ValidationSeverity.CRITICAL:
            self.errors.append(issue)
            self.is_valid = False
        elif severity == ValidationSeverity.WARNING:
            self.warnings.append(issue)
        else:
            self.info.append(issue)

    @property
    def total_issues(self) -> int:
        """Get total number of issues"""
        return len(self.errors) + len(self.warnings) + len(self.info)

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0


class DataValidator:
    """
    Comprehensive data validator for AI integration models
    """

    def __init__(self,
                 logger_system: LoggerSystem = None,
                 error_handler: IntegratedErrorHandler = None):
        """Initialize the data validator"""
        self.logger_system = logger_system or LoggerSystem()
        self.error_handler = error_handler or IntegratedErrorHandler(self.logger_system)

        # Validation rules and constraints
        self.validation_rules = self._setup_validation_rules()

        # File format validation
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}

        # GPS coordinate ranges
        self.gps_ranges = {
            'latitude': (-90.0, 90.0),
            'longitude': (-180.0, 180.0),
            'altitude': (-1000.0, 10000.0)
        }

        # Color validation patterns
        self.color_patterns = {
            'hex': re.compile(r'^#[0-9A-Fa-f]{6}$'),
            'hex_short': re.compile(r'^#[0-9A-Fa-f]{3}$'),
            'rgb': re.compile(r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$'),
            'rgba': re.compile(r'^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[0-1]?\.?\d*\s*\)$')
        }

    def _setup_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Setup validation rules for different data types"""
        return {
            'image_metadata': {
                'required_fields': ['file_path', 'file_size', 'created_date', 'modified_date'],
                'file_size_range': (0, 1024 * 1024 * 1024),  # 0 to 1GB
                'image_dimension_range': (1, 50000),  # 1 to 50k pixels
                'iso_range': (50, 204800),  # Common ISO range
                'aperture_range': (0.5, 64.0),  # Common aperture range
                'focal_length_range': (1.0, 2000.0),  # Common focal length range in mm
            },
            'theme_configuration': {
                'required_fields': ['name', 'display_name'],
                'name_pattern': re.compile(r'^[a-zA-Z0-9_-]+$'),
                'version_pattern': re.compile(r'^\d+\.\d+\.\d+$'),
                'required_colors': ['background', 'foreground', 'primary', 'secondary'],
                'accessibility_requirements': {
                    'min_contrast_ratio': 4.5,  # WCAG AA standard
                    'required_features': ['keyboard_navigation', 'focus_indicators']
                }
            },
            'application_state': {
                'thumbnail_size_range': (50, 500),
                'zoom_range': (0.1, 10.0),
                'map_zoom_range': (1, 20),
                'performance_modes': ['performance', 'balanced', 'quality'],
                'sort_modes': ['name', 'date', 'size', 'type'],
                'fit_modes': ['fit_window', 'fit_width', 'actual_size'],
                'exif_display_modes': ['detailed', 'compact', 'minimal']
            }
        }

    def validate_image_metadata(self, metadata: ImageMetadata) -> ValidationResult:
        """Validate ImageMetadata instance"""
        result = ValidationResult(is_valid=True)
        rules = self.validation_rules['image_metadata']

        try:
            # Validate required fields
            for field in rules['required_fields']:
                if not hasattr(metadata, field) or getattr(metadata, field) is None:
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        field,
                        f"Required field '{field}' is missing or None"
                    )

            # Validate file path and existence
            if metadata.file_path:
                if not isinstance(metadata.file_path, Path):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        'file_path',
                        "File path must be a Path object",
                        type(metadata.file_path)
                    )
                elif not metadata.file_path.exists():
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        'file_path',
                        f"File does not exist: {metadata.file_path}"
                    )
                elif metadata.file_path.suffix.lower() not in self.supported_image_formats:
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        'file_path',
                        f"Unsupported image format: {metadata.file_path.suffix}",
                        metadata.file_path.suffix
                    )

            # Validate GPS coordinates
            if metadata.latitude is not None:
                lat_min, lat_max = self.gps_ranges['latitude']
                if not (lat_min <= metadata.latitude <= lat_max):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        'latitude',
                        f"Latitude {metadata.latitude} is outside valid range ({lat_min}-{lat_max})",
                        metadata.latitude
                    )

            if metadata.longitude is not None:
                lon_min, lon_max = self.gps_ranges['longitude']
                if not (lon_min <= metadata.longitude <= lon_max):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        'longitude',
                        f"Longitude {metadata.longitude} is outside valid range ({lon_min}-{lon_max})",
                        metadata.longitude
                    )

            # Validate processing status
            if not isinstance(metadata.processing_status, ProcessingStatus):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    'processing_status',
                    "Processing status must be a ProcessingStatus enum value",
                    type(metadata.processing_status)
                )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "data_validation",
                f"ImageMetadata validation completed: {result.total_issues} issues found"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "validate_image_metadata", "metadata_path": str(metadata.file_path)},
                AIComponent.KIRO
            )
            result.add_issue(
                ValidationSeverity.CRITICAL,
                'validation_error',
                f"Validation failed with exception: {str(e)}"
            )

        return result

    def validate_theme_configuration(self, theme: ThemeConfiguration) -> ValidationResult:
        """Validate ThemeConfiguration instance"""
        result = ValidationResult(is_valid=True)
        rules = self.validation_rules['theme_configuration']

        try:
            # Validate required fields
            for field in rules['required_fields']:
                if not hasattr(theme, field) or not getattr(theme, field):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        field,
                        f"Required field '{field}' is missing or empty"
                    )

            # Validate theme name format
            if theme.name and not rules['name_pattern'].match(theme.name):
                result.add_issue(
                    ValidationSeverity.ERROR,
                    'name',
                    "Theme name must contain only alphanumeric characters, underscores, and hyphens",
                    theme.name
                )

            # Validate color scheme
            if theme.color_scheme:
                for color_name in rules['required_colors']:
                    if color_name not in theme.color_scheme:
                        result.add_issue(
                            ValidationSeverity.WARNING,
                            'color_scheme',
                            f"Missing required color '{color_name}' in color scheme"
                        )
                    else:
                        color_value = theme.color_scheme[color_name]
                        if not self._is_valid_color(color_value):
                            result.add_issue(
                                ValidationSeverity.ERROR,
                                'color_scheme',
                                f"Invalid color format for '{color_name}': {color_value}",
                                color_value
                            )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "data_validation",
                f"ThemeConfiguration validation completed: {result.total_issues} issues found"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "validate_theme_configuration", "theme_name": theme.name},
                AIComponent.KIRO
            )
            result.add_issue(
                ValidationSeverity.CRITICAL,
                'validation_error',
                f"Validation failed with exception: {str(e)}"
            )

        return result

    def validate_application_state(self, state: ApplicationState) -> ValidationResult:
        """Validate ApplicationState instance"""
        result = ValidationResult(is_valid=True)
        rules = self.validation_rules['application_state']

        try:
            # Validate thumbnail size
            if state.thumbnail_size is not None:
                min_size, max_size = rules['thumbnail_size_range']
                if not (min_size <= state.thumbnail_size <= max_size):
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        'thumbnail_size',
                        f"Thumbnail size {state.thumbnail_size} is outside recommended range ({min_size}-{max_size})",
                        state.thumbnail_size
                    )

            # Validate performance mode
            if state.performance_mode not in rules['performance_modes']:
                result.add_issue(
                    ValidationSeverity.ERROR,
                    'performance_mode',
                    f"Invalid performance mode '{state.performance_mode}'. Must be one of: {rules['performance_modes']}",
                    state.performance_mode
                )

            # Validate file paths
            if state.current_folder is not None:
                if not isinstance(state.current_folder, Path):
                    result.add_issue(
                        ValidationSeverity.ERROR,
                        'current_folder',
                        "Current folder must be a Path object",
                        type(state.current_folder)
                    )
                elif not state.current_folder.exists():
                    result.add_issue(
                        ValidationSeverity.WARNING,
                        'current_folder',
                        f"Current folder does not exist: {state.current_folder}"
                    )

            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "data_validation",
                f"ApplicationState validation completed: {result.total_issues} issues found"
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.INTEGRATION_ERROR,
                {"operation": "validate_application_state"},
                AIComponent.KIRO
            )
            result.add_issue(
                ValidationSeverity.CRITICAL,
                'validation_error',
                f"Validation failed with exception: {str(e)}"
            )

        return result

    def _is_valid_color(self, color: str) -> bool:
        """Check if color string is in valid format"""
        if not isinstance(color, str):
            return False

        for pattern in self.color_patterns.values():
            if pattern.match(color):
                return True

        return False

    def validate_all_models(self,
                          image_metadata: Optional[ImageMetadata] = None,
                          theme_config: Optional[ThemeConfiguration] = None,
                          app_state: Optional[ApplicationState] = None) -> Dict[str, ValidationResult]:
        """Validate multiple models at once"""
        results = {}

        if image_metadata:
            results['image_metadata'] = self.validate_image_metadata(image_metadata)

        if theme_config:
            results['theme_configuration'] = self.validate_theme_configuration(theme_config)

        if app_state:
            results['application_state'] = self.validate_application_state(app_state)

        return results
