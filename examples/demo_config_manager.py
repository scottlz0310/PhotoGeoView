#!/usr/bin/env python3
"""
Configuration Manager Demo - Task 2 Implementation

Demonstrates the unified configuration management system for AI integration.

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path

# Add src to path for imports - adjusted for examples folder
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from photogeoview.integration.config_manager import ConfigManager


def main():
    """Demonstrate ConfigManager functionality"""

    print("=" * 60)
    print("Configuration Manager Demo - Task 2 Implementation")
    print("=" * 60)

    try:
        # Initialize components
        print("\n1. Initializing ConfigManager...")
        config_manager = ConfigManager()
        print("   ✓ ConfigManager initialized")

        # Demonstrate default configuration
        print("\n2. Default Configuration:")
        print(f"   App Name: {config_manager.get_setting('app.name')}")
        print(f"   App Version: {config_manager.get_setting('app.version')}")
        print(f"   UI Theme: {config_manager.get_setting('ui.theme')}")
        print(f"   Thumbnail Size: {config_manager.get_setting('ui.thumbnail_size')}")
        print(f"   Performance Mode: {config_manager.get_setting('performance.mode')}")

        # Demonstrate AI-specific configuration
        print("\n3. AI-Specific Configuration:")
        for ai_name in ["copilot", "cursor", "kiro"]:
            ai_config = config_manager.get_ai_config(ai_name)
            print(f"   {ai_name.upper()}: {len(ai_config)} settings loaded")

            # Show some specific settings
            if ai_name == "copilot":
                image_processing = ai_config.get("image_processing", {})
                print(
                    f"     - High Quality EXIF: {image_processing.get('high_quality_exif')}"
                )
                print(f"     - GPS Precision: {image_processing.get('gps_precision')}")
            elif ai_name == "cursor":
                theme_system = ai_config.get("theme_system", {})
                print(
                    f"     - Qt Theme Manager: {theme_system.get('qt_theme_manager')}"
                )
                print(f"     - Theme Count: {theme_system.get('theme_count')}")
            elif ai_name == "kiro":
                integration = ai_config.get("integration", {})
                print(
                    f"     - Performance Monitoring: {integration.get('performance_monitoring')}"
                )
                print(f"     - AI Coordination: {integration.get('ai_coordination')}")

        # Demonstrate configuration modification
        print("\n4. Configuration Modification:")
        print("   Changing UI theme to 'dark'...")
        config_manager.set_setting("ui.theme", "dark")
        print(f"   New theme: {config_manager.get_setting('ui.theme')}")

        print("   Updating thumbnail size to 200...")
        config_manager.set_setting("ui.thumbnail_size", 200)
        print(
            f"   New thumbnail size: {config_manager.get_setting('ui.thumbnail_size')}"
        )

        # Demonstrate AI configuration update
        print("\n5. AI Configuration Update:")
        copilot_updates = {
            "image_processing": {"high_quality_exif": False, "detailed_metadata": True}
        }
        config_manager.update_ai_config("copilot", copilot_updates)
        print("   ✓ Copilot configuration updated")

        updated_config = config_manager.get_ai_config("copilot")
        image_processing = updated_config.get("image_processing", {})
        print(f"   High Quality EXIF: {image_processing.get('high_quality_exif')}")
        print(f"   Detailed Metadata: {image_processing.get('detailed_metadata')}")

        # Demonstrate application state management
        print("\n6. Application State Management:")
        state = config_manager.get_application_state()
        print(f"   Current Theme: {state.current_theme}")
        print(f"   Thumbnail Size: {state.thumbnail_size}")
        print(f"   Session Duration: {state.session_duration:.2f} seconds")
        print(f"   Images Processed: {state.images_processed}")

        # Update application state
        print("\n   Updating application state...")
        config_manager.update_application_state(
            current_theme="dark",
            thumbnail_size=200,
            images_processed=15,
            performance_mode="performance",
        )

        updated_state = config_manager.get_application_state()
        print(f"   Updated Theme: {updated_state.current_theme}")
        print(f"   Updated Thumbnail Size: {updated_state.thumbnail_size}")
        print(f"   Updated Images Processed: {updated_state.images_processed}")
        print(f"   Updated Performance Mode: {updated_state.performance_mode}")

        # Demonstrate configuration persistence
        print("\n7. Configuration Persistence:")
        print("   Saving configuration...")
        config_manager.save_config()
        print("   ✓ Configuration saved to files")

        print("   Saving application state...")
        config_manager.save_application_state()
        print("   ✓ Application state saved")

        # Demonstrate configuration summary
        print("\n8. Configuration Summary:")
        summary = config_manager.get_config_summary()
        print(f"   Total Settings: {summary['total_settings']}")
        print("   AI Configurations:")
        for ai_name, count in summary["ai_configs"].items():
            print(f"     - {ai_name}: {count} settings")

        state_summary = config_manager.get_state_summary()
        print("   Application State:")
        print(f"     - Current Theme: {state_summary['current_theme']}")
        print(f"     - Images Processed: {state_summary['images_processed']}")
        print(f"     - Session Duration: {state_summary['session_duration']:.2f}s")

        # Demonstrate configuration export
        print("\n9. Configuration Export:")
        export_file = Path("config_export_demo.json")
        config_manager.export_config(export_file)
        print(f"   ✓ Configuration exported to {export_file}")

        # Show export file size
        if export_file.exists():
            size_kb = export_file.stat().st_size / 1024
            print(f"   Export file size: {size_kb:.1f} KB")

        # Demonstrate migration detection
        print("\n10. Migration Detection:")
        has_legacy = config_manager.has_legacy_configurations()
        print(f"   Legacy configurations detected: {has_legacy}")

        if has_legacy:
            print("   Running migration...")
            migration_result = config_manager.migrate_existing_configurations()
            print(f"   Migration status: {migration_result.get('status', 'unknown')}")
            print(
                f"   Files processed: {migration_result.get('total_files_processed', 0)}"
            )
            print(
                f"   Settings migrated: {migration_result.get('total_settings_migrated', 0)}"
            )

        # Demonstrate change listeners
        print("\n11. Change Listeners:")
        change_events = []

        def change_listener(key, old_value, new_value):
            change_events.append(f"{key}: {old_value} -> {new_value}")

        config_manager.add_change_listener(change_listener)

        # Make some changes
        config_manager.set_setting("ui.animation_enabled", False)
        config_manager.set_setting("performance.max_memory_mb", 1024)

        print(f"   Change events captured: {len(change_events)}")
        for event in change_events[-2:]:  # Show last 2 events
            print(f"     - {event}")

        config_manager.remove_change_listener(change_listener)

        # Demonstrate error handling
        print("\n12. Error Handling:")

        # Test invalid AI component
        invalid_config = config_manager.get_ai_config("invalid_ai")
        print(f"   Invalid AI config result: {len(invalid_config)} settings")

        # Test invalid setting key
        result = config_manager.get_setting("invalid.key.path", "default_value")
        print(f"   Invalid setting result: {result}")

        print("\n" + "=" * 60)
        print("Configuration Manager Demo Completed Successfully!")
        print("=" * 60)

        # Show final configuration state
        print("\nFinal Configuration State:")
        print(f"  - UI Theme: {config_manager.get_setting('ui.theme')}")
        print(f"  - Thumbnail Size: {config_manager.get_setting('ui.thumbnail_size')}")
        print(f"  - Performance Mode: {config_manager.get_setting('performance.mode')}")
        print(
            f"  - Images Processed: {config_manager.get_application_state().images_processed}"
        )

        # Cleanup
        if export_file.exists():
            export_file.unlink()
            print(f"\n✓ Cleaned up export file: {export_file}")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
