#!/usr/bin/env python3
"""
Test Qt Theme Manager configuration integration
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.settings import SettingsManager
from ui.theme_manager import ThemeManager

def test_theme_config():
    print("=== Qt Theme Manager Configuration Test ===")

    # Test config file
    config_path = Path("config/qt_themes.json")
    print(f"Config file exists: {config_path.exists()}")

    if config_path.exists():
        with open(config_path, 'r') as f:
            data = json.load(f)
            themes = data.get('themes', {})
            print(f"Themes in config file: {len(themes)}")

            # Show first few themes
            for i, (key, theme) in enumerate(themes.items()):
                if i < 3:
                    print(f"  - {key}: {theme.get('name', 'N/A')}")
                    print(f"    Primary: {theme.get('primaryColor', 'N/A')}")
                    print(f"    Background: {theme.get('backgroundColor', 'N/A')}")

    # Test theme manager
    print("\n=== Theme Manager Test ===")
    settings = SettingsManager()
    tm = ThemeManager(settings)

    print(f"Available themes: {len(tm.available_themes)}")
    print(f"Config themes loaded: {len(tm.theme_configs)}")

    # Test a specific theme
    test_theme = 'midnight_blue'
    print(f"\n=== Testing theme: {test_theme} ===")

    if test_theme in tm.theme_configs:
        config = tm.theme_configs[test_theme]
        print(f"Theme config found: {config.get('name', 'N/A')}")

        # Generate stylesheet
        stylesheet = tm._generate_stylesheet_from_config(config)
        print(f"Generated stylesheet length: {len(stylesheet)} characters")
        print("First 200 characters:")
        print(stylesheet[:200] + "...")
    else:
        print(f"Theme {test_theme} not found in config")

if __name__ == "__main__":
    test_theme_config()
