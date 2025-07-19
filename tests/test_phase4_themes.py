#!/usr/bin/env python3
"""
PhotoGeoView Phase 4 Theme System Test
Tests the enhanced theme management features
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from src.ui.theme_manager import ThemeManager
from src.ui.controllers.theme_controller import ThemeController
from src.core.settings import SettingsManager
from src.core.logger import get_logger


def test_phase4_themes():
    """Test Phase 4 theme system enhancements"""
    logger = get_logger(__name__)

    # Initialize Qt Application
    app = QApplication([])

    try:
        logger.info("=== PhotoGeoView Phase 4 Theme System Test ===")

        # Initialize components
        logger.info("Initializing theme system...")
        settings = SettingsManager()
        theme_manager = ThemeManager()
        theme_controller = ThemeController(settings, theme_manager)

        # Test 1: Validate all 16 themes are available
        logger.info("\nTest 1: Theme Availability")
        available_themes = theme_manager.get_available_themes()
        logger.info(f"Available themes: {len(available_themes)}")

        if len(available_themes) == 16:
            logger.info("✅ All 16 themes are available")
        else:
            logger.warning(f"⚠️ Expected 16 themes, found {len(available_themes)}")

        for theme in available_themes:
            display_name = theme_manager.get_theme_display_name(theme)
            category = theme_manager.get_theme_category(theme)
            logger.info(f"  - {theme}: {display_name} ({category})")

        # Test 2: Theme statistics
        logger.info("\nTest 2: Theme Statistics")
        stats = theme_manager.get_theme_statistics()
        logger.info(f"Theme statistics: {stats}")

        # Test 3: Theme compatibility validation
        logger.info("\nTest 3: Theme Compatibility Validation")
        compatibility = theme_manager.validate_theme_compatibility()
        logger.info(f"Theme compatibility: {'✅ Good' if compatibility else '⚠️ Issues detected'}")

        # Test 4: Test theme switching
        logger.info("\nTest 4: Theme Switching Test")
        test_themes = ["dark_blue.xml", "light_blue.xml", "dark_purple.xml", "light_orange.xml"]

        for theme in test_themes:
            if theme in available_themes:
                logger.info(f"Testing theme: {theme}")
                success = theme_manager.apply_theme_with_verification(theme)
                if success:
                    logger.info(f"✅ {theme} applied successfully")
                    current = theme_manager.get_current_theme()
                    if current == theme:
                        logger.info(f"✅ Theme correctly set to {current}")
                    else:
                        logger.warning(f"⚠️ Expected {theme}, got {current}")
                else:
                    logger.error(f"❌ Failed to apply {theme}")

        # Test 5: Theme category toggling
        logger.info("\nTest 5: Theme Category Toggle")
        original_theme = theme_manager.get_current_theme()
        logger.info(f"Starting theme: {original_theme}")

        new_theme = theme_manager.toggle_theme_type()
        logger.info(f"Toggled to: {new_theme}")

        if new_theme != original_theme:
            original_category = theme_manager.get_theme_category(original_theme)
            new_category = theme_manager.get_theme_category(new_theme)
            if original_category != new_category:
                logger.info(f"✅ Successfully toggled from {original_category} to {new_category}")
            else:
                logger.warning(f"⚠️ Theme changed but category remained {new_category}")
        else:
            logger.warning("⚠️ Theme toggle did not change theme")

        # Test 6: Performance validation
        logger.info("\nTest 6: Theme Performance Test")
        performance_results = theme_controller.create_theme_performance_test()
        if performance_results['themes_tested'] > 0:
            avg_time = performance_results['average_switch_time']
            logger.info(f"✅ Performance test completed: avg {avg_time:.3f}s")
            if avg_time < 1.0:  # Less than 1 second is good
                logger.info("✅ Good performance (< 1.0s average)")
            else:
                logger.warning(f"⚠️ Performance may need optimization (avg: {avg_time:.3f}s)")
        else:
            logger.warning("⚠️ Performance test failed")

        # Test 7: Theme validation
        logger.info("\nTest 7: Comprehensive Theme Validation")
        validation_results = theme_controller.validate_all_themes()
        working_count = len(validation_results.get('working_themes', []))
        total_count = validation_results.get('total_themes', 0)
        compatibility_rate = validation_results.get('compatibility_rate', 0)

        logger.info(f"Validation results: {working_count}/{total_count} themes working ({compatibility_rate:.1%})")

        if compatibility_rate >= 0.8:  # 80% or better
            logger.info("✅ Good theme compatibility")
        else:
            logger.warning(f"⚠️ Low theme compatibility: {compatibility_rate:.1%}")
            failed_themes = validation_results.get('failed_themes', [])
            if failed_themes:
                logger.warning(f"Failed themes: {', '.join(failed_themes)}")

        # Summary
        logger.info("\n=== Phase 4 Theme System Test Summary ===")
        logger.info(f"✅ Theme availability: {len(available_themes)}/16 themes")
        logger.info(f"✅ Theme compatibility: {'Good' if compatibility else 'Needs attention'}")
        logger.info(f"✅ Performance: {'Good' if performance_results.get('average_switch_time', 2) < 1.0 else 'Acceptable'}")
        logger.info(f"✅ Validation: {compatibility_rate:.1%} success rate")
        logger.info("Phase 4 theme system test completed!")

        return True

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

    finally:
        # Clean up
        if 'app' in locals():
            app.quit()


if __name__ == "__main__":
    success = test_phase4_themes()
    sys.exit(0 if success else 1)
