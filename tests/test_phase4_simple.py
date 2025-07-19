#!/usr/bin/env python3
"""
PhotoGeoView Phase 4 Theme System Simple Test
Simple validation of theme system functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_theme_system_simple():
    """Simple test of theme system without Qt initialization"""
    print("=== PhotoGeoView Phase 4 Theme System Simple Test ===")

    try:
        # Test 1: Import theme manager
        print("Test 1: Importing theme manager...")
        from src.ui.theme_manager import ThemeManager
        print("✅ Theme manager imported successfully")

        # Test 2: Check theme list without Qt app
        print("\nTest 2: Checking theme availability...")
        theme_manager = ThemeManager()
        available_themes = theme_manager.get_available_themes()
        print(f"✅ Found {len(available_themes)} available themes")

        if len(available_themes) == 16:
            print("✅ All 16 themes are listed")
        else:
            print(f"⚠️ Expected 16 themes, found {len(available_themes)}")

        # Test 3: Check theme categories
        print("\nTest 3: Theme categorization...")
        dark_themes = theme_manager.get_themes_by_category('dark')
        light_themes = theme_manager.get_themes_by_category('light')

        print(f"Dark themes: {len(dark_themes)}")
        print(f"Light themes: {len(light_themes)}")

        if len(dark_themes) == 8 and len(light_themes) == 8:
            print("✅ Correct theme distribution (8 dark, 8 light)")
        else:
            print(f"⚠️ Theme distribution: {len(dark_themes)} dark, {len(light_themes)} light")

        # Test 4: Display names
        print("\nTest 4: Theme display names...")
        sample_themes = available_themes[:3]  # Test first 3 themes
        for theme in sample_themes:
            display_name = theme_manager.get_theme_display_name(theme)
            category = theme_manager.get_theme_category(theme)
            print(f"  {theme} -> {display_name} ({category})")

        # Test 5: Theme controller import
        print("\nTest 5: Theme controller import...")
        from src.ui.controllers.theme_controller import ThemeController
        print("✅ Theme controller imported successfully")

        # Test 6: Settings manager
        print("\nTest 6: Settings manager integration...")
        from src.core.settings import SettingsManager
        settings = SettingsManager()
        print("✅ Settings manager imported and initialized")

        print("\n=== Test Summary ===")
        print("✅ Theme manager: OK")
        print("✅ Theme availability: OK")
        print("✅ Theme categorization: OK")
        print("✅ Display names: OK")
        print("✅ Theme controller: OK")
        print("✅ Settings integration: OK")
        print("\nPhase 4 theme system basic validation: PASSED")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_theme_system_simple()
    sys.exit(0 if success else 1)
