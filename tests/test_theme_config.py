#!/usr/bin/env python3
"""
Test Qt Theme Manager configuration integration
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.settings import SettingsManager
from src.ui.theme_manager import ThemeManager

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
    test_theme = 'dark_blue'
    print(f"\n=== Testing theme: {test_theme} ===")

    if test_theme in tm.theme_configs:
        config = tm.theme_configs[test_theme]
        print(f"Theme config found: {config.get('name', 'N/A')}")

        # Test theme application
        success = tm.apply_theme(test_theme)
        print(f"Theme application success: {success}")

        if success:
            print("✅ Qt Theme Manager configuration file integration successful!")
        else:
            print("❌ Theme application failed")
    else:
        print(f"Theme {test_theme} not found in config")

if __name__ == "__main__":
    test_theme_config()
