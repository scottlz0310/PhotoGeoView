#!/usr/bin/env python3
"""
Data Validation and Migration Demo - Task 7 Implementation

Demonstrates the data validation and migration functionality for AI integration.

Author: Kiro AI Integration System
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add src to path for imports - adjusted for examples folder
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from integration.data_validation import DataValidator, ValidationSeverity
from integration.data_migration import DataMigrationManager, MigrationStatus
from integration.models import ImageMetadata, ThemeConfiguration, ApplicationState, ProcessingStatus, AIComponent
from integration.logging_system import LoggerSystem
from integration.error_handling import IntegratedErrorHandler


def create_sample_data():
    """Create sample data files for demonstration"""
    data_dir = Path("demo_data")
    data_dir.mkdir(exist_ok=True)

    # Create sample image files
    for i in range(3):
        img_file = data_dir / f"sample_image_{i+1}.jpg"
        img_file.write_text(f"fake image content {i+1}")

    # Create sample CursorBLD image cache
    cursor_cache = [
        {
            "path": str(data_dir / "sample_image_1.jpg"),
            "size": 1024000,
            "thumb_path": str(data_dir / "thumb_1.jpg"),
            "name": "Sample Image 1",
            "created": "2024-01-01 10:00:00",
            "modified": "2024-01-01 10:00:00"
        },
        {
            "path": str(data_dir / "sample_image_2.jpg"),
            "size": 2048000,
            "thumb_path": str(data_dir / "thumb_2.jpg"),
            "name": "Sample Image 2",
            "created": "2024-01-02 11:00:00",
            "modified": "2024-01-02 11:00:00"
        }
    ]

    with open(data_dir / "image_cache.json", 'w') as f:
        json.dump(cursor_cache, f, indent=2)

    # Create sample theme data
    theme_data = [
        {
            "theme_name": "dark_theme",
            "display_name": "Dark Theme",
            "colors": {
                "background": "#2b2b2b",
                "foreground": "#ffffff",
                "primary": "#007acc",
                "secondary": "#6c757d"
            },
            "qt_theme": "dark",
            "stylesheet": "QWidget { background-color: #2b2b2b; }"
        }
    ]

    with open(data_dir / "themes.json", 'w') as f:
        json.dump(theme_data, f, indent=2)

    # Create sample CS4Coding EXIF data
    exif_data = [
        {
            "image_path": str(data_dir / "sample_image_3.jpg"),
            "make": "Canon",
            "model": "EOS R5",
            "lens": "RF 24-70mm F2.8 L IS USM",
            "focal_length": 50.0,
            "f_number": 2.8,
            "exposure_time": "1/125",
            "iso_speed": 400,
            "gps_lat": 35.6762,
            "gps_lon": 139.6503,
            "gps_alt": 10.5,
            "image_width": 8192,
            "image_height": 5464
        }
    ]

    with open(data_dir / "exif_data.json", 'w') as f:
        json.dump(exif_data, f, indent=2)

    # Create sample legacy database
    db_file = data_dir / "photogeoview.db"
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL,
                size INTEGER,
                created TEXT,
                modified TEXT,
                width INTEGER,
                height INTEGER,
                camera_make TEXT,
                camera_model TEXT,
                iso INTEGER,
                aperture REAL,
                shutter_speed TEXT,
                latitude REAL,
                longitude REAL,
                altitude REAL
            )
        """)

        sample_images = [
            (str(data_dir / "legacy1.jpg"), 1500000, "2024-01-01 12:00:00", "2024-01-01 12:00:00",
             4000, 3000, "Sony", "A7R IV", 200, 4.0, "1/60", 51.5074, -0.1278, 50.0),
            (str(data_dir / "legacy2.jpg"), 1800000, "2024-01-02 13:00:00", "2024-01-02 13:00:00",
             6000, 4000, "Fujifilm", "X-T4", 400, 2.8, "1/125", 48.8566, 2.3522, 35.0)
        ]

        conn.executemany("""
            INSERT OR REPLACE INTO images (path, size, created, modified, width, height, camera_make,
                              camera_model, iso, aperture, shutter_speed, latitude, longitude, altitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_images)

    return data_dir


def demonstrate_data_validation():
    """Demonstrate data validation functionality"""
    print("\n" + "=" * 60)
    print("Data Validation Demonstration")
    print("=" * 60)

    # Initialize validator
    logger_system = LoggerSystem()
    error_handler = IntegratedErrorHandler(logger_system)
    validator = DataValidator(logger_system, error_handler)

    print("\n1. Validating ImageMetadata...")

    # Create valid ImageMetadata
    data_dir = Path("demo_data")
    valid_metadata = ImageMetadata(
        file_path=data_dir / "sample_image_1.jpg",
        file_size=1024000,
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

    result = validator.validate_image_metadata(valid_metadata)
    print(f"   Valid metadata validation: {'✓ PASSED' if result.is_valid else '✗ FAILED'}")
    print(f"   Issues found: {result.total_issues} (Errors: {len(result.errors)}, Warnings: {len(result.warnings)})")

    # Create invalid ImageMetadata
    invalid_metadata = ImageMetadata(
        file_path=Path("nonexistent.jpg"),  # Non-existent file
        file_size=1024000,
        created_date=datetime.now(),
        modified_date=datetime.now(),
        latitude=95.0,  # Invalid latitude
        longitude=185.0,  # Invalid longitude
        processing_status=ProcessingStatus.COMPLETED
    )

    result = validator.validate_image_metadata(invalid_metadata)
    print(f"   Invalid metadata validation: {'✓ PASSED' if result.is_valid else '✗ FAILED (Expected)'}")
    print(f"   Issues found: {result.total_issues} (Errors: {len(result.errors)}, Warnings: {len(result.warnings)})")

    if result.errors:
        print("   Error details:")
        for error in result.errors[:3]:  # Show first 3 errors
            print(f"     - {error['field']}: {error['message']}")

    print("\n2. Validating ThemeConfiguration...")

    # Create valid theme
    valid_theme = ThemeConfiguration(
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

    result = validator.validate_theme_configuration(valid_theme)
    print(f"   Valid theme validation: {'✓ PASSED' if result.is_valid else '✗ FAILED'}")
    print(f"   Issues found: {result.total_issues} (Errors: {len(result.errors)}, Warnings: {len(result.warnings)})")

    # Create invalid theme
    invalid_theme = ThemeConfiguration(
        name="invalid theme name!",  # Invalid characters
        display_name="",  # Empty required field
        color_scheme={
            "background": "invalid_color",  # Invalid color format
            "foreground": "#gggggg"  # Invalid hex color
        }
    )

    result = validator.validate_theme_configuration(invalid_theme)
    print(f"   Invalid theme validation: {'✓ PASSED' if result.is_valid else '✗ FAILED (Expected)'}")
    print(f"   Issues found: {result.total_issues} (Errors: {len(result.errors)}, Warnings: {len(result.warnings)})")

    print("\n3. Validating ApplicationState...")

    # Create valid application state
    valid_state = ApplicationState(
        current_folder=data_dir,
        current_theme="default",
        thumbnail_size=150,
        performance_mode="balanced",
        image_sort_mode="name",
        fit_mode="fit_window",
        exif_display_mode="detailed",
        image_sort_ascending=True
    )

    result = validator.validate_application_state(valid_state)
    print(f"   Valid state validation: {'✓ PASSED' if result.is_valid else '✗ FAILED'}")
    print(f"   Issues found: {result.total_issues} (Errors: {len(result.errors)}, Warnings: {len(result.warnings)})")

    # Create invalid application state
    invalid_state = ApplicationState(
        current_folder=Path("nonexistent_folder"),
        thumbnail_size=1000,  # Outside recommended range
        performance_mode="invalid_mode",  # Invalid mode
        image_sort_mode="invalid_sort",  # Invalid sort mode
        fit_mode="invalid_fit"  # Invalid fit mode
    )

    result = validator.validate_application_state(invalid_state)
    print(f"   Invalid state validation: {'✓ PASSED' if result.is_valid else '✗ FAILED (Expected)'}")
    print(f"   Issues found: {result.total_issues} (Errors: {len(result.errors)}, Warnings: {len(result.warnings)})")

    print("\n4. Validating Multiple Models...")

    results = validator.validate_all_models(
        image_metadata=valid_metadata,
        theme_config=valid_theme,
        app_state=valid_state
    )

    print(f"   Models validated: {len(results)}")
    for model_name, result in results.items():
        status = "✓ PASSED" if result.is_valid else "✗ FAILED"
        print(f"   {model_name}: {status} ({result.total_issues} issues)")


def demonstrate_data_migration():
    """Demonstrate data migration functionality"""
    print("\n" + "=" * 60)
    print("Data Migration Demonstration")
    print("=" * 60)

    # Initialize migration manager
    data_dir = Path("demo_data")
    logger_system = LoggerSystem()
    error_handler = IntegratedErrorHandler(logger_system)
    validator = DataValidator(logger_system, error_handler)

    migration_manager = DataMigrationManager(
        data_dir=data_dir,
        backup_dir=data_dir / "migration_backups",
        logger_system=logger_system,
        validator=validator
    )

    print("\n1. Migration Manager Status:")
    status = migration_manager.get_migration_status()
    print(f"   Data directory: {status['data_directory']}")
    print(f"   Backup directory: {status['backup_directory']}")
    print(f"   Available migrations: {len(status['available_migrations'])}")
    for migration in status['available_migrations']:
        print(f"     - {migration}")

    print("\n2. Running Data Migration...")

    # Run full migration
    migration_summary = migration_manager.migrate_all_data()

    print(f"   Migration completed for {len(migration_summary)} AI implementations")

    total_migrated = 0
    total_errors = 0

    for ai_name, results in migration_summary.items():
        if ai_name == "error":
            continue

        print(f"\n   {ai_name.upper()} Migration Results:")

        successful = sum(1 for r in results if r.status == MigrationStatus.SUCCESS)
        partial = sum(1 for r in results if r.status == MigrationStatus.PARTIAL)
        failed = sum(1 for r in results if r.status == MigrationStatus.FAILED)
        skipped = sum(1 for r in results if r.status == MigrationStatus.SKIPPED)

        migrated_count = sum(r.migrated_count for r in results)
        error_count = sum(len(r.errors) for r in results)

        total_migrated += migrated_count
        total_errors += error_count

        print(f"     Operations: {len(results)} total")
        print(f"     Status: {successful} successful, {partial} partial, {failed} failed, {skipped} skipped")
        print(f"     Objects migrated: {migrated_count}")
        print(f"     Errors: {error_count}")

        # Show details for each operation
        for result in results:
            status_symbol = {
                MigrationStatus.SUCCESS: "✓",
                MigrationStatus.PARTIAL: "⚠",
                MigrationStatus.FAILED: "✗",
                MigrationStatus.SKIPPED: "○"
            }.get(result.status, "?")

            print(f"       {status_symbol} {result.source_type} -> {result.target_model}: {result.migrated_count} objects")

            if result.errors:
                for error in result.errors[:2]:  # Show first 2 errors
                    print(f"         Error: {error}")

            if result.warnings:
                for warning in result.warnings[:2]:  # Show first 2 warnings
                    print(f"         Warning: {warning}")

    print(f"\n3. Migration Summary:")
    print(f"   Total objects migrated: {total_migrated}")
    print(f"   Total errors: {total_errors}")

    overall_status = "SUCCESS" if total_errors == 0 else "PARTIAL" if total_migrated > 0 else "FAILED"
    print(f"   Overall status: {overall_status}")

    # Check for migration report
    report_file = data_dir / "data_migration_report.json"
    if report_file.exists():
        print(f"   Migration report saved: {report_file}")

        # Show report size
        size_kb = report_file.stat().st_size / 1024
        print(f"   Report size: {size_kb:.1f} KB")

    # Check for migrated data files
    migrated_files = list(data_dir.glob("migrated_*.json"))
    if migrated_files:
        print(f"\n4. Migrated Data Files:")
        for file in migrated_files:
            size_kb = file.stat().st_size / 1024
            print(f"   {file.name}: {size_kb:.1f} KB")

    # Check backup files
    backup_dir = data_dir / "migration_backups"
    if backup_dir.exists():
        backup_files = list(backup_dir.glob("*"))
        if backup_files:
            print(f"\n5. Backup Files Created:")
            for file in backup_files:
                size_kb = file.stat().st_size / 1024
                print(f"   {file.name}: {size_kb:.1f} KB")


def demonstrate_integration():
    """Demonstrate integration of validation and migration"""
    print("\n" + "=" * 60)
    print("Validation & Migration Integration")
    print("=" * 60)

    data_dir = Path("demo_data")

    # Check for migrated data files
    migrated_files = list(data_dir.glob("migrated_*.json"))

    if not migrated_files:
        print("   No migrated data files found. Run migration first.")
        return

    print(f"\n1. Found {len(migrated_files)} migrated data files")

    # Initialize validator
    logger_system = LoggerSystem()
    error_handler = IntegratedErrorHandler(logger_system)
    validator = DataValidator(logger_system, error_handler)

    total_objects = 0
    total_valid = 0
    total_issues = 0

    for migrated_file in migrated_files:
        print(f"\n2. Validating {migrated_file.name}...")

        try:
            with open(migrated_file, 'r') as f:
                migrated_data = json.load(f)

            if not isinstance(migrated_data, list):
                migrated_data = [migrated_data]

            file_objects = len(migrated_data)
            file_valid = 0
            file_issues = 0

            # Determine model type from filename
            if "imagemetadata" in migrated_file.name.lower():
                model_type = "ImageMetadata"
            elif "themeconfiguration" in migrated_file.name.lower():
                model_type = "ThemeConfiguration"
            elif "applicationstate" in migrated_file.name.lower():
                model_type = "ApplicationState"
            else:
                print(f"   Unknown model type in {migrated_file.name}")
                continue

            print(f"   Model type: {model_type}")
            print(f"   Objects to validate: {file_objects}")

            # Validate each object (sample first few)
            sample_size = min(5, file_objects)
            for i, obj_data in enumerate(migrated_data[:sample_size]):
                try:
                    # Reconstruct object for validation
                    if model_type == "ImageMetadata":
                        obj = ImageMetadata(
                            file_path=Path(obj_data.get('file_path', '')),
                            file_size=obj_data.get('file_size', 0),
                            created_date=datetime.fromisoformat(obj_data.get('created_date', datetime.now().isoformat())),
                            modified_date=datetime.fromisoformat(obj_data.get('modified_date', datetime.now().isoformat())),
                            **{k: v for k, v in obj_data.items() if k not in ['file_path', 'file_size', 'created_date', 'modified_date']}
                        )
                        result = validator.validate_image_metadata(obj)
                    elif model_type == "ThemeConfiguration":
                        obj = ThemeConfiguration(**obj_data)
                        result = validator.validate_theme_configuration(obj)
                    elif model_type == "ApplicationState":
                        obj_data_copy = obj_data.copy()
                        if 'current_folder' in obj_data_copy and obj_data_copy['current_folder']:
                            obj_data_copy['current_folder'] = Path(obj_data_copy['current_folder'])
                        if 'selected_image' in obj_data_copy and obj_data_copy['selected_image']:
                            obj_data_copy['selected_image'] = Path(obj_data_copy['selected_image'])
                        obj = ApplicationState(**obj_data_copy)
                        result = validator.validate_application_state(obj)

                    if result.is_valid:
                        file_valid += 1

                    file_issues += result.total_issues

                    if i < 3:  # Show details for first 3 objects
                        status = "✓ VALID" if result.is_valid else "⚠ ISSUES"
                        print(f"     Object {i+1}: {status} ({result.total_issues} issues)")

                except Exception as e:
                    print(f"     Object {i+1}: ✗ ERROR - {str(e)}")

            if sample_size < file_objects:
                print(f"     ... and {file_objects - sample_size} more objects")

            total_objects += file_objects
            total_valid += file_valid
            total_issues += file_issues

            print(f"   File summary: {file_valid}/{sample_size} valid objects, {file_issues} total issues")

        except Exception as e:
            print(f"   Error processing {migrated_file.name}: {e}")

    print(f"\n3. Overall Validation Summary:")
    print(f"   Total migrated objects: {total_objects}")
    print(f"   Valid objects (sampled): {total_valid}")
    print(f"   Total validation issues: {total_issues}")

    if total_objects > 0:
        validity_rate = (total_valid / min(total_objects, len(migrated_files) * 5)) * 100  # Approximate based on sampling
        print(f"   Validity rate: {validity_rate:.1f}%")


def cleanup_demo_data():
    """Clean up demo data files"""
    data_dir = Path("demo_data")
    if data_dir.exists():
        import shutil
        shutil.rmtree(data_dir)
        print(f"\n✓ Cleaned up demo data directory: {data_dir}")


def main():
    """Main demonstration function"""
    print("=" * 60)
    print("Data Validation and Migration Demo - Task 7")
    print("=" * 60)

    try:
        # Create sample data
        print("\n1. Creating sample data...")
        data_dir = create_sample_data()
        print(f"   ✓ Sample data created in: {data_dir}")

        # Demonstrate data validation
        demonstrate_data_validation()

        # Demonstrate data migration
        demonstrate_data_migration()

        # Demonstrate integration
        demonstrate_integration()

        print("\n" + "=" * 60)
        print("Data Validation and Migration Demo Completed Successfully!")
        print("=" * 60)

        # Show final status
        print(f"\nFinal Status:")
        print(f"  - Sample data created and processed")
        print(f"  - Data validation demonstrated with various scenarios")
        print(f"  - Data migration completed for multiple AI implementations")
        print(f"  - Integration validation performed on migrated data")

        # Ask about cleanup
        response = input("\nClean up demo data files? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            cleanup_demo_data()
        else:
            print(f"\nDemo data preserved in: {data_dir}")
            print("You can manually delete this directory when no longer needed.")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
