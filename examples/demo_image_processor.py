#!/usr/bin/env python3
"""
CS4Coding ImageProcessor Demo

Demonstrates the integrated ImageProcessor functionality:
- Image loading and validation
- EXIF data extraction
- Performance monitoring
- Caching system

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path

# Add src to path - adjusted for examples folder
sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.image_processor import CS4CodingImageProcessor
from integration.config_manager import ConfigManager
from integration.logging_system import LoggerSystem


def main():
    """Main demo function"""

    print("=== CS4Coding ImageProcessor Demo ===\n")

    # Initialize components
    print("1. Initializing ImageProcessor...")
    config_manager = ConfigManager()
    logger_system = LoggerSystem()

    processor = CS4CodingImageProcessor(
        config_manager=config_manager,
        logger_system=logger_system
    )

    print(f"   ✓ ImageProcessor initialized")
    print(f"   ✓ Supported formats: {len(processor.get_supported_formats())}")
    print(f"   ✓ Libraries available: {processor.get_performance_stats()['libraries_available']}")

    # Test coordinate validation
    print("\n2. Testing GPS coordinate validation...")
    test_coords = [
        (40.7128, -74.0060, "New York City"),
        (35.6762, 139.6503, "Tokyo"),
        (51.5074, -0.1278, "London"),
        (91.0, 0.0, "Invalid (lat > 90)"),
        (0.0, 181.0, "Invalid (lon > 180)")
    ]

    for lat, lon, name in test_coords:
        valid = processor.validate_coordinates(lat, lon)
        status = "✓" if valid else "✗"
        print(f"   {status} {name}: ({lat}, {lon}) - {'Valid' if valid else 'Invalid'}")

    # Test coordinate formatting
    print("\n3. Testing coordinate formatting...")
    formatted = processor._format_coordinates(40.7128, -74.0060)
    print(f"   ✓ Formatted coordinates: {formatted}")

    # Test file size formatting
    print("\n4. Testing file size formatting...")
    test_sizes = [0, 512, 1024, 1048576, 1073741824]
    for size in test_sizes:
        formatted = processor._format_file_size(size)
        print(f"   ✓ {size} bytes = {formatted}")

    # Test rational number parsing
    print("\n5. Testing rational number parsing...")
    test_rationals = ["1/2", "3/4", "42", "invalid", "1/0"]
    for rational in test_rationals:
        result = processor._parse_rational(rational)
        print(f"   ✓ '{rational}' = {result}")

    # Test GPS coordinate conversion
    print("\n6. Testing GPS coordinate conversion...")
    # Simulate DMS format
    gps_coord = "[40, 42, 46.08]"
    gps_ref = "N"
    decimal = processor._convert_gps_to_decimal(gps_coord, gps_ref)
    print(f"   ✓ DMS {gps_coord} {gps_ref} = {decimal}°")

    # Test with different references
    for ref in ["N", "S", "E", "W"]:
        decimal = processor._convert_gps_to_decimal(gps_coord, ref)
        print(f"   ✓ {gps_coord} {ref} = {decimal}°")

    # Show performance statistics
    print("\n7. Performance Statistics:")
    stats = processor.get_performance_stats()
    for key, value in stats.items():
        if key != 'recent_processing_times':  # Skip long lists
            print(f"   ✓ {key}: {value}")

    # Test cache functionality
    print("\n8. Testing cache functionality...")
    print(f"   ✓ Initial cache sizes - Images: {stats['image_cache_size']}, Metadata: {stats['metadata_cache_size']}")

    processor.clear_cache()
    stats_after_clear = processor.get_performance_stats()
    print(f"   ✓ After clear - Images: {stats_after_clear['image_cache_size']}, Metadata: {stats_after_clear['metadata_cache_size']}")

    # Test image validation with different file types
    print("\n9. Testing image validation...")
    test_files = [
        "test.jpg",
        "test.png",
        "test.tiff",
        "test.txt",
        "test.pdf",
        "nonexistent.jpg"
    ]

    for filename in test_files:
        # Create temporary test file for supported formats
        test_path = Path(filename)
        if test_path.suffix.lower() in processor.get_supported_formats():
            test_path.write_bytes(b"fake image data")
        elif filename != "nonexistent.jpg":
            test_path.write_text("not an image")

        valid = processor.validate_image(test_path)
        status = "✓" if valid else "✗"
        print(f"   {status} {filename}: {'Valid' if valid else 'Invalid'}")

        # Clean up
        if test_path.exists():
            test_path.unlink()

    print("\n10. Shutting down...")
    processor.shutdown()
    logger_system.shutdown()

    print("   ✓ ImageProcessor shutdown complete")
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()
