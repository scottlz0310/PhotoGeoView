"""
Theme Config Data Models

Data models for Qt theme management system with validation.
Supports theme configuration, custom themes, and theme metadata.

Author: Kiro AI Integration System
Requirements: 5.1, 5.2, 5.3
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class ThemeType(Enum):
    """Theme type enumeration"""

    BUILT_IN = "built_in"
    CUSTOM = "custom"
    IMPORTED = "imported"

class ValidationError(Exception):
    """Theme validation error"""

    pass

@dataclass
class FontConfig:
    """Font configuration for themes"""

    family: str
    size: int
    weight: str = "normal"
    style: str = "normal"

    def __post_init__(self):
        """Validate font configuration"""
        if self.size <= 0:
            raise ValidationError(f"Font size must be positive, got {self.size}")

        valid_weights = [
            "normal",
            "bold",
            "lighter",
            "bolder",
            "100",
            "200",
            "300",
            "400",
            "500",
            "600",
            "700",
            "800",
            "900",
        ]
        if self.weight not in valid_weights:
            raise ValidationError(f"Invalid font weight: {self.weight}")

        valid_styles = ["normal", "italic", "oblique"]
        if self.style not in valid_styles:
            raise ValidationError(f"Invalid font style: {self.style}")

    def to_css(self) -> str:
        """Convert to CSS font specification"""
        return f"{self.style} {self.weight} {self.size}px {self.family}"

@dataclass
class ColorScheme:
    """Color scheme configuration with validation"""

    primary: str
    secondary: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    accent: str
    error: str
    warning: str
    success: str

    def __post_init__(self):
        """Validate color values"""
        color_fields = [
            "primary",
            "secondary",
            "background",
            "surface",
            "text_primary",
            "text_secondary",
            "accent",
            "error",
            "warning",
            "success",
        ]

        for field_name in color_fields:
            color_value = getattr(self, field_name)
            if not self._is_valid_color(color_value):
                raise ValidationError(
                    f"Invalid color value for {field_name}: {color_value}"
                )

    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Validate color format (hex, rgb, rgba, named colors)"""
        if not isinstance(color, str):
            return False

        # Hex colors
        if re.match(r"^#[0-9A-Fa-f]{6}$", color) or re.match(
            r"^#[0-9A-Fa-f]{3}$", color
        ):
            return True

        # RGB/RGBA colors
        if re.match(r"^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(,\s*[\d.]+)?\s*\)$", color):
            return True

        # Named colors (basic set)
        named_colors = {
            "black",
            "white",
            "red",
            "green",
            "blue",
            "yellow",
            "cyan",
            "magenta",
            "gray",
            "grey",
            "darkgray",
            "darkgrey",
            "lightgray",
            "lightgrey",
            "transparent",
        }
        return color.lower() in named_colors

    @property
    def is_dark_theme(self) -> bool:
        """Determine if this is a dark theme based on background color"""
        bg_color = self.background
        if bg_color.startswith("#"):
            # Convert hex to RGB and calculate luminance
            hex_color = bg_color.lstrip("#")
            if len(hex_color) == 3:
                hex_color = "".join([c * 2 for c in hex_color])

            r, g, b = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance < 0.5

        return False

@dataclass
class ThemeConfiguration:
    """
    Comprehensive theme configuration data model with validation

    Supports both built-in and custom themes with full validation
    and metadata tracking.
    """

    # Basic theme information
    name: str
    display_name: str
    description: str
    author: str
    version: str
    theme_type: ThemeType = ThemeType.BUILT_IN

    # Color configuration
    colors: ColorScheme = None

    # Font configuration
    fonts: dict[str, FontConfig] = field(default_factory=dict)

    # Style properties
    styles: dict[str, str] = field(default_factory=dict)

    # Custom properties for extensibility
    custom_properties: dict[str, Any] = field(default_factory=dict)

    # File system information
    file_path: Path | None = None
    is_custom: bool = False

    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    last_used: datetime | None = None

    # Validation status
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation and setup"""
        # Set default display name if not provided
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").replace("-", " ").title()

        # Set theme type based on is_custom flag
        if self.is_custom:
            self.theme_type = ThemeType.CUSTOM

        # Initialize default color scheme if not provided
        if self.colors is None:
            self.colors = self._get_default_colors()

        # Initialize default fonts if not provided
        if not self.fonts:
            self.fonts = self._get_default_fonts()

        # Validate the configuration
        self.validate()

    def _get_default_colors(self) -> ColorScheme:
        """Get default color scheme"""
        return ColorScheme(
            primary="#2196F3",
            secondary="#FFC107",
            background="#FFFFFF",
            surface="#F5F5F5",
            text_primary="#212121",
            text_secondary="#757575",
            accent="#FF5722",
            error="#F44336",
            warning="#FF9800",
            success="#4CAF50",
        )

    def _get_default_fonts(self) -> dict[str, FontConfig]:
        """Get default font configuration"""
        return {
            "default": FontConfig("Arial", 12),
            "heading": FontConfig("Arial", 16, "bold"),
            "small": FontConfig("Arial", 10),
            "monospace": FontConfig("Courier New", 12),
        }

    def validate(self) -> bool:
        """
        Validate theme configuration

        Returns:
            True if valid, False otherwise
        """
        self.validation_errors.clear()

        # Validate required fields
        if not self.name:
            self.validation_errors.append("Theme name is required")

        if not self.version:
            self.validation_errors.append("Theme version is required")

        # Validate name format (no spaces, special characters)
        if self.name and not re.match(r"^[a-zA-Z0-9_-]+$", self.name):
            self.validation_errors.append(
                "Theme name must contain only letters, numbers, underscores, and hyphens"
            )

        # Validate version format (semantic versioning)
        if self.version and not re.match(r"^\d+\.\d+\.\d+$", self.version):
            self.validation_errors.append(
                "Theme version must follow semantic versioning (x.y.z)"
            )

        # Validate colors
        try:
            if self.colors:
                # ColorScheme validation happens in __post_init__
                pass
        except ValidationError as e:
            self.validation_errors.append(f"Color validation error: {e!s}")

        # Validate fonts
        for font_name, _font_config in self.fonts.items():
            try:
                # FontConfig validation happens in __post_init__
                pass
            except ValidationError as e:
                self.validation_errors.append(
                    f"Font '{font_name}' validation error: {e!s}"
                )

        # Validate file path if provided
        if self.file_path and not self.file_path.exists():
            self.validation_errors.append(
                f"Theme file does not exist: {self.file_path}"
            )

        self.is_valid = len(self.validation_errors) == 0
        return self.is_valid

    def to_dict(self) -> dict[str, Any]:
        """Convert theme configuration to dictionary"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "theme_type": self.theme_type.value,
            "colors": {
                "primary": self.colors.primary,
                "secondary": self.colors.secondary,
                "background": self.colors.background,
                "surface": self.colors.surface,
                "text_primary": self.colors.text_primary,
                "text_secondary": self.colors.text_secondary,
                "accent": self.colors.accent,
                "error": self.colors.error,
                "warning": self.colors.warning,
                "success": self.colors.success,
            },
            "fonts": {
                name: {
                    "family": font.family,
                    "size": font.size,
                    "weight": font.weight,
                    "style": font.style,
                }
                for name, font in self.fonts.items()
            },
            "styles": self.styles,
            "custom_properties": self.custom_properties,
            "is_custom": self.is_custom,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThemeConfiguration":
        """Create theme configuration from dictionary"""
        # Parse colors
        colors_data = data.get("colors", {})
        colors = ColorScheme(**colors_data) if colors_data else None

        # Parse fonts
        fonts_data = data.get("fonts", {})
        fonts = {}
        for name, font_data in fonts_data.items():
            fonts[name] = FontConfig(**font_data)

        # Parse dates
        created_date = datetime.fromisoformat(
            data.get("created_date", datetime.now().isoformat())
        )
        modified_date = datetime.fromisoformat(
            data.get("modified_date", datetime.now().isoformat())
        )

        return cls(
            name=data["name"],
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            version=data["version"],
            theme_type=ThemeType(data.get("theme_type", "built_in")),
            colors=colors,
            fonts=fonts,
            styles=data.get("styles", {}),
            custom_properties=data.get("custom_properties", {}),
            is_custom=data.get("is_custom", False),
            created_date=created_date,
            modified_date=modified_date,
            usage_count=data.get("usage_count", 0),
        )

    def save_to_file(self, file_path: Path) -> bool:
        """
        Save theme configuration to file

        Args:
            file_path: Path to save the theme file

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            self.file_path = file_path
            self.modified_date = datetime.now()
            return True

        except Exception as e:
            self.validation_errors.append(f"Failed to save theme file: {e!s}")
            return False

    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional["ThemeConfiguration"]:
        """
        Load theme configuration from file

        Args:
            file_path: Path to the theme file

        Returns:
            ThemeConfiguration instance or None if failed
        """
        try:
            if not file_path.exists():
                return None

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            theme = cls.from_dict(data)
            theme.file_path = file_path
            return theme

        except Exception:
            return None

    def increment_usage(self):
        """Increment usage count and update last used timestamp"""
        self.usage_count += 1
        self.last_used = datetime.now()

    def get_css_variables(self) -> str:
        """Generate CSS custom properties for the theme"""
        css_vars = []

        # Color variables
        if self.colors:
            css_vars.extend(
                [
                    f"--color-primary: {self.colors.primary};",
                    f"--color-secondary: {self.colors.secondary};",
                    f"--color-background: {self.colors.background};",
                    f"--color-surface: {self.colors.surface};",
                    f"--color-text-primary: {self.colors.text_primary};",
                    f"--color-text-secondary: {self.colors.text_secondary};",
                    f"--color-accent: {self.colors.accent};",
                    f"--color-error: {self.colors.error};",
                    f"--color-warning: {self.colors.warning};",
                    f"--color-success: {self.colors.success};",
                ]
            )

        # Font variables
        for name, font in self.fonts.items():
            css_vars.append(f"--font-{name}: {font.to_css()};")

        return "\n".join([":root {"] + [f"  {var}" for var in css_vars] + ["}"])

@dataclass
class ThemeInfo:
    """
    Lightweight theme information for theme selection UI
    """

    name: str
    display_name: str
    description: str
    author: str
    version: str
    theme_type: ThemeType
    is_dark: bool
    preview_colors: dict[str, str]
    is_available: bool = True
    file_path: Path | None = None

    @classmethod
    def from_theme_config(cls, config: ThemeConfiguration) -> "ThemeInfo":
        """Create ThemeInfo from ThemeConfiguration"""
        preview_colors = {}
        if config.colors:
            preview_colors = {
                "primary": config.colors.primary,
                "background": config.colors.background,
                "text": config.colors.text_primary,
            }

        return cls(
            name=config.name,
            display_name=config.display_name,
            description=config.description,
            author=config.author,
            version=config.version,
            theme_type=config.theme_type,
            is_dark=config.colors.is_dark_theme if config.colors else False,
            preview_colors=preview_colors,
            file_path=config.file_path,
        )
