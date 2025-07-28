#!/usr/bin/env python3
"""
Demo script to show .gitignore update functionality.

This script demonstrates how the ConfigManager can update the project's
.gitignore file with CI simulation patterns.
"""

from config_manager import ConfigManager


def main():
    """Demonstrate .gitignore update functionality."""
    print("CI/CD Simulation .gitignore Update Demo")
    print("=" * 40)

    # Create ConfigManager
    config_manager = ConfigManager()

    # Show current .gitignore status
    print("\n1. Current .gitignore status:")
    status = config_manager.get_gitignore_status()

    print(f"   - .gitignore exists: {status['gitignore_exists']}")
    print(f"   - Has CI patterns: {status['has_ci_patterns']}")
    print(f"   - Total lines: {status['total_lines']}")
    print(f"   - Is valid: {status['is_valid']}")
    print(f"   - Missing patterns: {len(status['missing_patterns'])}")

    if status['missing_patterns']:
        print("   - Missing patterns:")
        for pattern in status['missing_patterns'][:5]:  # Show first 5
            print(f"     * {pattern}")
        if len(status['missing_patterns']) > 5:
            print(f"     ... and {len(status['missing_patterns']) - 5} more")

    # Ask user if they want to update
    print("\n2. Update .gitignore with CI simulation patterns?")
    response = input("   Enter 'yes' to update, anything else to skip: ").strip().lower()

    if response == 'yes':
        print("\n3. Updating .gitignore...")

        # Create backup first
        backup_path = config_manager.gitignore_manager.create_backup()
        if backup_path:
            print(f"   - Created backup: {backup_path}")

        # Update .gitignore
        success = config_manager.update_gitignore()

        if success:
            print("   ✅ Successfully updated .gitignore with CI patterns")

            # Show updated status
            updated_status = config_manager.get_gitignore_status()
            print(f"   - New total lines: {updated_status['total_lines']}")
            print(f"   - Has CI patterns: {updated_status['has_ci_patterns']}")
            print(f"   - Missing patterns: {len(updated_status['missing_patterns'])}")

        else:
            print("   ❌ Failed to update .gitignore")

    else:
        print("\n3. Skipping .gitignore update")

    # Show available backups
    backups = config_manager.gitignore_manager.list_backups()
    if backups:
        print(f"\n4. Available backups ({len(backups)}):")
        for backup in backups[:3]:  # Show first 3
            print(f"   - {backup}")
        if len(backups) > 3:
            print(f"   ... and {len(backups) - 3} more")

    print("\nDemo completed!")


if __name__ == "__main__":
    main()
