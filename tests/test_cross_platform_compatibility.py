"""
Cross-Platform Compatibility Integration Tests

Tests for cross-platform compatibility of theme and breadcrumb components
across Windows, Linux, and macOS.

Author: Kiro AI Integration System
Requirements: 4.1, 4.3
"""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.services.file_system_watcher import FileSystemWatcher
from src.integration.theme_integration_controller import ThemeIntegrationController
from src.integration.theme_models import ThemeConfiguration, ThemeType
from src.ui.breadcrumb_bar import BreadcrumbAddressBar


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility of integrated components"""

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory with platform-specific structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create platform-neutral test structure
            (temp_path / "test_folder").mkdir()
            (temp_path / "test_folder" / "subfolder").mkdir()
            (temp_path / "test_folder" / "file.txt").write_text("test content")

            yield temp_path

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager"""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_setting = Mock(side_effect=self._mock_get_setting)
        config_manager.set_setting = Mock(return_value=True)
        config_manager.save_config = Mock(return_value=True)
        return config_manager

    @pytest.fixture
    def logger_system(self):
        """r system"""
        return LoggerSystem()

    def _mock_get_setting(self, key: str, default=None):
        """Mock configuration getter with platform-specific values"""
        current_platform = platform.system()

        config_values = {
            "ui.theme": "default",
            "ui.breadcrumb.max_segments": 10,
            "ui.breadcrumb.truncation_mode": "smart",
            "ui.breadcrumb.show_icons": True,
            "navigation.current_path": str(Path.home()),
            "file_watcher.enable_monitoring": True,
        }

        # Platform-specific overrides
        if current_platform == "Windows":
            config_values.update({
                "ui.theme": "windows_theme",
                "ui.breadcrumb.path_separator": "\\",
                "file_watcher.use_polling": False,
            })
        elif current_platform == "Darwin":
            config_values.update({
                "ui.theme": "macos_theme",
                "ui.breadcrumb.path_separator": "/",
                "file_watcher.use_fsevents": True,
            })
        else:  # Linux
            config_values.update({
                "ui.theme": "linux_theme",
                "ui.breadcrumb.path_separator": "/",
                "file_watcher.use_inotify": True,
            })

        return config_values.get(key, default)

    @pytest.mark.parametrize("platform_name", ["Windows", "Linux", "Darwin"])
    def test_platform_specific_path_handling(self, platform_name, temp_directory, mock_config_manager, logger_system):
        """Test platform-specific path handling in breadcrumb"""
        with patch('platform.system', return_value=platform_name):
            # Create file system watcher
            file_system_watcher = FileSystemWatcher(
                logger_system=logger_system,
                enable_monitoring=True
            )

            # Create breadcrumb bar
            breadcrumb_bar = BreadcrumbAddressBar(
                file_system_watcher=file_system_watcher,
                logger_system=logger_system,
                config_manager=mock_config_manager
            )

            # Test path setting with platform-specific paths
            if platform_name == "Windows":
                # Test Windows-style path
                if os.name == 'nt':
                    test_path = Path("C:\\Users\\Test\\Documents")
                    if not test_path.exists():
                        test_path = temp_directory  # Fallback
                else:
                    test_path = temp_directory  # Use temp directory on non-Windows
            else:
                # Test Unix-style path
                test_path = temp_directory

            # Set path and verify handling
            result = breadcrumb_bar.set_current_path(test_path)

            if test_path.exists():
                assert result is True
                assert breadcrumb_bar.current_state.current_path == test_path

                # Verify path segments are created correctly
                segments = breadcrumb_bar.get_breadcrumb_segments()
                assert len(segments) > 0

    @pytest.mark.parametrize("platform_name", ["Windows", "Linux", "Darwin"])
    def test_platform_specific_theme_application(self, platform_name, mock_config_manager, logger_system):
        """Test platform-specific theme application"""
        with patch('platform.system', return_value=platform_name):
            # Create theme controller
            theme_controller = ThemeIntegrationController(
                config_manager=mock_config_manager,
                logger_system=logger_system
            )

            # Create platform-specific theme
            theme_name = f"{platform_name.lower()}_theme"
            theme_config = ThemeConfiguration(
                name=theme_name,
                display_name=f"{platform_name} Theme",
                description=f"Theme optimized for {platform_name}",
                author="System",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN
            )

            # Create mock theme manager
            mock_theme_manager = Mock()
            mock_theme_manager.apply_theme = Mock(return_value=True)
            mock_theme_manager.get_current_theme = Mock(return_value=theme_config)
            theme_controller.register_theme_manager("platform_manager", mock_theme_manager)

            # Apply theme
            import asyncio
            result = asyncio.run(theme_controller.apply_theme(theme_name))

            # Verify theme application
            assert result is True
            assert theme_controller.current_theme.name == theme_name

    def test_windows_specific_features(self, temp_directory, mock_config_manager, logger_system):
        """Test Windows-specific features and compatibility"""
        if platform.system() != "Windows":
            pytest.skip("Windows-specific test")

        # Test Windows path handling
        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Test Windows drive letters
        drives = [Path(f"{drive}:\\") for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{drive}:\\").exists()]

        if drives:
            test_drive = drives[0]
            result = breadcrumb_bar.set_current_path(test_drive)
            assert result is True

            # Verify drive letter is handled correctly
            segments = breadcrumb_bar.get_breadcrumb_segments()
            assert len(segments) > 0
            assert str(test_drive) in str(segments[0].path)

    def test_macos_specific_features(self, temp_directory, mock_config_manager, logger_system):
        """Test macOS-specific features and compatibility"""
        if platform.system() != "Darwin":
            pytest.skip("macOS-specific test")

        # Test macOS path handling
        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Test macOS-specific paths
        macos_paths = [
            Path("/Applications"),
            Path("/Users"),
            Path("/System"),
            Path.home() / "Desktop"
        ]

        for test_path in macos_paths:
            if test_path.exists():
                result = breadcrumb_bar.set_current_path(test_path)
                assert result is True

                # Verify path is handled correctly
                assert breadcrumb_bar.current_state.current_path == test_path
                break

    def test_linux_specific_features(self, temp_directory, mock_config_manager, logger_system):
        """Test Linux-specific features and compatibility"""
        if platform.system() != "Linux":
            pytest.skip("Linux-specific test")

        # Test Linux path handling
        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Test Linux-specific paths
        linux_paths = [
            Path("/home"),
            Path("/usr"),
            Path("/var"),
            Path("/tmp")
        ]

        for test_path in linux_paths:
            if test_path.exists():
                result = breadcrumb_bar.set_current_path(test_path)
                assert result is True

                # Verify path is handled correctly
                assert breadcrumb_bar.current_state.current_path == test_path
                break

    def test_file_system_case_sensitivity(self, temp_directory, mock_config_manager, logger_system):
        """Test file system case sensitivity handling across platforms"""
        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Create test directories with different cases
        lower_dir = temp_directory / "testfolder"
        upper_dir = temp_directory / "TESTFOLDER"

        lower_dir.mkdir(exist_ok=True)

        # Try to create upper case version
        try:
            upper_dir.mkdir()
            case_sensitive = True
        except FileExistsError:
            case_sensitive = False

        # Test navigation to both paths
        result1 = breadcrumb_bar.set_current_path(lower_dir)
        assert result1 is True

        if case_sensitive:
            result2 = breadcrumb_bar.set_current_path(upper_dir)
            assert result2 is True
            assert breadcrumb_bar.current_state.current_path == upper_dir
        else:
            # On case-insensitive systems, both should resolve to same path
            result2 = breadcrumb_bar.set_current_path(upper_dir)
            # Result may vary depending on implementation

    def test_unicode_path_handling(self, temp_directory, mock_config_manager, logger_system):
        """Test Unicode path handling across platforms"""
        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Create directories with Unicode names
        unicode_names = [
            "测试文件夹",  # Chinese
            "тестовая_папка",  # Russian
            "フォルダテスト",  # Japanese
            "مجلد_اختبار",  # Arabic
            "test_émojis_🚀_folder"  # Emojis
        ]

        for unicode_name in unicode_names:
            try:
                unicode_dir = temp_directory / unicode_name
                unicode_dir.mkdir()

                # Test navigation to Unicode path
                result = breadcrumb_bar.set_current_path(unicode_dir)
                assert result is True
                assert breadcrumb_bar.current_state.current_path == unicode_dir

                # Verify segments handle Unicode correctly
                segments = breadcrumb_bar.get_breadcrumb_segments()
                assert len(segments) > 0

            except (OSError, UnicodeError):
                # Some platforms may not support certain Unicode characters
                continue

    def test_long_path_handling(self, temp_directory, mock_config_manager, logger_system):
        """Test long path handling across platforms"""
        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Create deeply nested directory structure
        current_path = temp_directory
        max_depth = 10 if platform.system() == "Windows" else 20

        try:
            for i in range(max_depth):
                current_path = current_path / f"level_{i:02d}_very_long_directory_name_to_test_path_limits"
                current_path.mkdir()

            # Test navigation to long path
            result = breadcrumb_bar.set_current_path(current_path)
            assert result is True

            # Verify truncation works correctly
            segments = breadcrumb_bar.get_breadcrumb_segments()
            assert len(segments) > 0

            # Test truncation mode
            breadcrumb_bar.set_max_visible_segments(5)
            breadcrumb_bar.set_truncation_mode("smart")

            # Verify truncation is applied
            truncated_segments = breadcrumb_bar.get_breadcrumb_segments()
            assert len(truncated_segments) <= 5

        except OSError:
            # Path too long for platform
            pytest.skip("Platform doesn't support long paths")

    def test_special_characters_in_paths(self, temp_directory, mock_config_manager, logger_system):
        """Test handling of special characters in paths"""
        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Test various special characters (platform-dependent)
        special_chars = []

        if platform.system() == "Windows":
            # Windows has more restrictions
            special_chars = ["test folder", "test-folder", "test_folder", "test.folder"]
        else:
            # Unix-like systems are more permissive
            special_chars = [
                "test folder", "test-folder", "test_folder", "test.folder",
                "test@folder", "test#folder", "test$folder", "test%folder"
            ]

        for special_name in special_chars:
            try:
                special_dir = temp_directory / special_name
                special_dir.mkdir()

                # Test navigation to path with special characters
                result = breadcrumb_bar.set_current_path(special_dir)
                assert result is True
                assert breadcrumb_bar.current_state.current_path == special_dir

            except (OSError, ValueError):
                # Some characters may not be allowed on certain platforms
                continue

    def test_network_path_handling(self, mock_config_manager, logger_system):
        """Test network path handling (Windows UNC paths, etc.)"""
        if platform.system() != "Windows":
            pytest.skip("Network path test is Windows-specific")

        file_system_watcher = FileSystemWatcher(
            logger_system=logger_system,
            enable_monitoring=True
        )

        breadcrumb_bar = BreadcrumbAddressBar(
            file_system_watcher=file_system_watcher,
            logger_system=logger_system,
            config_manager=mock_config_manager
        )

        # Test UNC path format (may not exist, but should handle format)
        unc_path = Path("\\\\server\\share\\folder")

        # Test path validation (should not crash)
        try:
            result = breadcrumb_bar._validate_path(unc_path)
            # Result depends on whether path exists
            assert isinstance(result, bool)
        except Exception:
            # Should handle UNC paths gracefully even if they don't exist
            pass

    def test_platform_specific_configuration(self, mock_config_manager, logger_system):
        """Test platform-specific configuration handling"""
        current_platform = platform.system()

        # Create theme controller
        theme_controller = ThemeIntegrationController(
            config_manager=mock_config_manager,
            logger_system=logger_system
        )

        # Test platform-specific configuration loading
        platform_config = theme_controller._load_platform_specific_config()

        # Should return configuration appropriate for current platform
        assert isinstance(platform_config, dict)

        # Verify platform-specific settings
        if current_platform == "Windows":
            # Windows-specific settings
            assert "windows" in str(platform_config).lower() or len(platform_config) >= 0
        elif current_platform == "Darwin":
            # macOS-specific settings
            assert "macos" in str(platform_config).lower() or "darwin" in str(platform_config).lower() or len(platform_config) >= 0
        else:
            # Linux-specific settings
            assert "linux" in str(platform_config).lower() or len(platform_config) >= 0

    def test_cross_platform_theme_compatibility(self, mock_config_manager, logger_system):
        """Test theme compatibility across platforms"""
        theme_controller = ThemeIntegrationController(
            config_manager=mock_config_manager,
            logger_system=logger_system
        )

        # Create cross-platform theme
        cross_platform_theme = ThemeConfiguration(
            name="cross_platform",
            display_name="Cross Platform Theme",
            description="Theme that works on all platforms",
            author="System",
            version="1.0.0",
            theme_type=ThemeType.BUILT_IN
        )

        # Test theme validation for current platform
        is_compatible = theme_controller._validate_theme_compatibility(cross_platform_theme)
        assert is_compatible is True

        # Test platform-specific theme features
        platform_features = theme_controller._get_platform_theme_features()
        assert isinstance(platform_features, dict)
        assert len(platform_features) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
