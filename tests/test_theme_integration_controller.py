"""
Unit Tests for Theme Integration Controller

Tests for ThemeIntegrationController covering:
- Theme manager registration and management
- Component registration and theme application
- Theme persistence and configuration
- Error handling and fallback mechanisms
- Notification system functionality

Author: Kiro AI Integration System
Requirements: 1.2, 1.3, 1.4, 5.1, 5.2
"""

import asyncio
from unittest.mock import Mock

import pytest

from src.integration.config_manager import ConfigManager
from src.integration.error_handling import ErrorCategory, IntegratedErrorHandler
from src.integration.logging_system import LoggerSystem
from src.integration.theme_integration_controller import ThemeIntegrationController
from src.integration.theme_interfaces import IThemeAware, IThemeManager
from src.integration.theme_models import (
    ThemeConfiguration,
    ThemeInfo,
    ThemeType,
)


class MockThemeAware(IThemeAware):
    """Mock theme-aware component for testing"""

    def __init__(self, name: str = "MockComponent"):
        self.name = name
        self.applied_theme = None
        self.apply_theme_called = False
        self.theme_properties = ["colors.primary", "colors.background", "fonts.default"]

    def apply_theme(self, theme: ThemeConfiguration) -> None:
        """Apply theme to the component"""
        self.applied_theme = theme
        self.apply_theme_called = True

    def get_theme_properties(self) -> list[str]:
        """Get list of theme properties used by this component"""
        return self.theme_properties


class MockThemeManager(IThemeManager):
    """Mock theme manager for testing"""

    def __init__(self, name: str = "MockManager"):
        self.name = name
        self.current_theme = None
        self.available_themes = {}
        self.registered_components = set()
        self.theme_change_listeners = []
        self.apply_theme_success = True

        # Create some default themes
        self._create_default_themes()

    def _create_default_themes(self):
        """Create default themes for testing"""
        themes = [
            ("default", "Default Light", False),
            ("dark", "Dark Theme", True),
            ("custom", "Custom Theme", False),
        ]

        for name, display_name, is_dark in themes:
            theme_info = ThemeInfo(
                name=name,
                display_name=display_name,
                description=f"Test theme: {name}",
                author="Test",
                version="1.0.0",
                theme_type=ThemeType.BUILT_IN,
                is_dark=is_dark,
                preview_colors={
                    "primary": "#007acc",
                    "background": "#ffffff",
                    "text": "#000000",
                },
                is_available=True,
            )
            self.available_themes[name] = theme_info

    def get_current_theme(self) -> ThemeConfiguration | None:
        """Get the currently active theme"""
        return self.current_theme

    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme to the application"""
        if not self.apply_theme_success:
            return False

        if theme_name in self.available_themes:
            theme_info = self.available_themes[theme_name]
            self.current_theme = ThemeConfiguration(
                name=theme_info.name,
                display_name=theme_info.display_name,
                description=theme_info.description,
                author=theme_info.author,
                version=theme_info.version,
                theme_type=theme_info.theme_type,
            )
            return True
        return False

    def register_component(self, component: IThemeAware) -> bool:
        """Register a component for theme updates"""
        self.registered_components.add(component)
        return True

    def unregister_component(self, component: IThemeAware) -> bool:
        """Unregister a component from theme updates"""
        if component in self.registered_components:
            self.registered_components.remove(component)
            return True
        return False

    def add_theme_change_listener(self, callback) -> bool:
        """Add a theme change listener"""
        self.theme_change_listeners.append(callback)
        return True

    def remove_theme_change_listener(self, callback) -> bool:
        """Remove a theme change listener"""
        if callback in self.theme_change_listeners:
            self.theme_change_listeners.remove(callback)
            return True
        return False

    def get_theme_property(self, property_path: str, default=None):
        """Get a theme property value"""
        return default

    def reload_themes(self) -> bool:
        """Reload all available themes"""
        return True

    def reset_to_default(self) -> bool:
        """Reset to default theme"""
        return self.apply_theme("default")

    def get_available_themes(self) -> list[ThemeInfo]:
        """Get list of available themes"""
        return list(self.available_themes.values())


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager"""
    config_manager = Mock(spec=ConfigManager)
    config_manager.get_setting = Mock(return_value=None)
    config_manager.set_setting = Mock(return_value=True)
    config_manager.save_config = Mock(return_value=True)
    config_manager.add_change_listener = Mock()
    return config_manager


@pytest.fixture
def mock_logger_system():
    """Create a mock logger system"""
    logger_system = Mock(spec=LoggerSystem)
    logger_system.get_logger = Mock(return_value=Mock())
    return logger_system


@pytest.fixture
def mock_error_handler():
    """Create a mock error handler"""
    error_handler = Mock(spec=IntegratedErrorHandler)
    error_handler.handle_error = Mock()
    return error_handler


@pytest.fixture
def theme_controller(mock_config_manager, mock_logger_system, mock_error_handler):
    """Create a theme integration controller for testing"""
    return ThemeIntegrationController(
        config_manager=mock_config_manager,
        logger_system=mock_logger_system,
        error_handler=mock_error_handler,
    )


@pytest.fixture
def mock_theme_manager():
    """Create a mock theme manager"""
    return MockThemeManager()


@pytest.fixture
def mock_theme_component():
    """Create a mock theme-aware component"""
    return MockThemeAware()


class TestThemeIntegrationController:
    """Test suite for ThemeIntegrationController"""

    def test_initialization(self, theme_controller, mock_config_manager):
        """Test controller initialization"""
        assert theme_controller.config_manager == mock_config_manager
        assert theme_controller.current_theme is None
        assert len(theme_controller.available_themes) == 0
        assert len(theme_controller.registered_components) == 0
        assert len(theme_controller.theme_managers) == 0
        assert theme_controller.fallback_theme == "default"

    def test_register_theme_manager(self, theme_controller, mock_theme_manager):
        """Test theme manager registration"""
        # Test successful registration
        result = theme_controller.register_theme_manager("test_manager", mock_theme_manager)
        assert result is True
        assert "test_manager" in theme_controller.theme_managers
        assert theme_controller.theme_managers["test_manager"] == mock_theme_manager

        # Test registration with same name (should replace)
        new_manager = MockThemeManager("new_manager")
        result = theme_controller.register_theme_manager("test_manager", new_manager)
        assert result is True
        assert theme_controller.theme_managers["test_manager"] == new_manager

    def test_unregister_theme_manager(self, theme_controller, mock_theme_manager):
        """Test theme manager unregistration"""
        # Register first
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Test successful unregistration
        result = theme_controller.unregister_theme_manager("test_manager")
        assert result is True
        assert "test_manager" not in theme_controller.theme_managers

        # Test unregistering non-existent manager
        result = theme_controller.unregister_theme_manager("non_existent")
        assert result is False

    def test_register_component(self, theme_controller, mock_theme_component):
        """Test component registration"""
        # Test successful registration
        result = theme_controller.register_component(mock_theme_component, "test_component")
        assert result is True
        assert mock_theme_component in theme_controller.registered_components
        assert theme_controller.component_registry["test_component"] == mock_theme_component

        # Test duplicate registration
        result = theme_controller.register_component(mock_theme_component, "test_component")
        assert result is True  # Should still return True but not duplicate

    def test_unregister_component(self, theme_controller, mock_theme_component):
        """Test component unregistration"""
        # Register first
        theme_controller.register_component(mock_theme_component, "test_component")

        # Test successful unregistration
        result = theme_controller.unregister_component(mock_theme_component, "test_component")
        assert result is True
        assert mock_theme_component not in theme_controller.registered_components
        assert "test_component" not in theme_controller.component_registry

        # Test unregistering non-existent component
        result = theme_controller.unregister_component(mock_theme_component)
        assert result is False

    def test_get_registered_component(self, theme_controller, mock_theme_component):
        """Test getting registered component by ID"""
        # Register component
        theme_controller.register_component(mock_theme_component, "test_component")

        # Test getting existing component
        component = theme_controller.get_registered_component("test_component")
        assert component == mock_theme_component

        # Test getting non-existent component
        component = theme_controller.get_registered_component("non_existent")
        assert component is None

    @pytest.mark.asyncio
    async def test_apply_theme_success(self, theme_controller, mock_theme_manager, mock_theme_component):
        """Test successful theme application"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)
        theme_controller.register_component(mock_theme_component)

        # Apply theme
        result = await theme_controller.apply_theme("default")

        assert result is True
        assert theme_controller.current_theme is not None
        assert theme_controller.current_theme.name == "default"
        assert mock_theme_component.apply_theme_called is True

    @pytest.mark.asyncio
    async def test_apply_theme_not_found(self, theme_controller, mock_theme_manager):
        """Test applying non-existent theme"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Apply non-existent theme
        result = await theme_controller.apply_theme("non_existent")

        # Should fallback to default theme
        assert result is True  # Fallback should succeed
        assert theme_controller.current_theme.name == "default"

    @pytest.mark.asyncio
    async def test_apply_theme_manager_failure(self, theme_controller, mock_theme_manager, mock_theme_component):
        """Test theme application when manager fails"""
        # Setup - make manager fail for non-default themes but succeed for default
        original_apply_theme = mock_theme_manager.apply_theme

        def selective_apply_theme(theme_name):
            success = theme_name == "default"
            if success:
                # Call original method to set up the theme properly
                return original_apply_theme(theme_name)
            return False

        mock_theme_manager.apply_theme = selective_apply_theme
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)
        theme_controller.register_component(mock_theme_component)

        # Apply non-default theme (should fail and fallback to default)
        result = await theme_controller.apply_theme("dark")

        # Should fallback to default theme
        assert result is True  # Fallback should succeed

    @pytest.mark.asyncio
    async def test_apply_theme_component_failure(self, theme_controller, mock_theme_manager):
        """Test theme application when component fails"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Create a component that raises an exception
        failing_component = Mock(spec=IThemeAware)
        failing_component.apply_theme = Mock(side_effect=Exception("Component error"))
        theme_controller.register_component(failing_component)

        # Apply theme
        result = await theme_controller.apply_theme("default")

        # Should still succeed (error handling)
        assert result is True
        assert theme_controller.current_theme is not None

    def test_add_theme_change_listener(self, theme_controller):
        """Test adding theme change listener"""
        callback = Mock()

        # Test successful addition
        result = theme_controller.add_theme_change_listener(callback)
        assert result is True
        assert callback in theme_controller.theme_change_listeners

        # Test duplicate addition
        result = theme_controller.add_theme_change_listener(callback)
        assert result is False

    def test_remove_theme_change_listener(self, theme_controller):
        """Test removing theme change listener"""
        callback = Mock()

        # Add first
        theme_controller.add_theme_change_listener(callback)

        # Test successful removal
        result = theme_controller.remove_theme_change_listener(callback)
        assert result is True
        assert callback not in theme_controller.theme_change_listeners

        # Test removing non-existent listener
        result = theme_controller.remove_theme_change_listener(callback)
        assert result is False

    @pytest.mark.asyncio
    async def test_theme_change_notification(self, theme_controller, mock_theme_manager):
        """Test theme change notification system"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Add listeners
        change_callback = Mock()
        applied_callback = Mock()
        theme_controller.add_theme_change_listener(change_callback)
        theme_controller.add_theme_applied_listener(applied_callback)

        # Apply theme
        await theme_controller.apply_theme("dark")

        # Check notifications were called
        change_callback.assert_called_once_with(None, "dark")
        applied_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_theme_error_notification(self, theme_controller, mock_theme_manager):
        """Test theme error notification system"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Add error listener
        error_callback = Mock()
        theme_controller.add_theme_error_listener(error_callback)

        # Try to apply non-existent theme (should trigger error before fallback)
        await theme_controller.apply_theme("non_existent")

        # Check error notification was called
        error_callback.assert_called()

    def test_get_current_theme(self, theme_controller):
        """Test getting current theme"""
        # Initially should be None
        assert theme_controller.get_current_theme() is None

        # Set a theme
        theme_config = ThemeConfiguration(
            name="test",
            display_name="Test Theme",
            description="Test",
            author="Test",
            version="1.0.0",
        )
        theme_controller.current_theme = theme_config

        assert theme_controller.get_current_theme() == theme_config

    def test_get_available_themes(self, theme_controller, mock_theme_manager):
        """Test getting available themes"""
        # Initially should be empty
        assert len(theme_controller.get_available_themes()) == 0

        # Register theme manager
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Should now have themes
        themes = theme_controller.get_available_themes()
        assert len(themes) > 0
        assert any(theme.name == "default" for theme in themes)

    def test_get_theme_history(self, theme_controller, mock_config_manager):
        """Test getting theme history"""
        # Mock history data
        history_data = [
            {"theme_name": "dark", "timestamp": "2023-01-01T12:00:00", "success": True},
            {
                "theme_name": "default",
                "timestamp": "2023-01-01T11:00:00",
                "success": True,
            },
        ]
        mock_config_manager.get_setting.return_value = history_data

        history = theme_controller.get_theme_history()
        assert history == history_data
        mock_config_manager.get_setting.assert_called_with("ui.theme_history", [])

    def test_get_performance_metrics(self, theme_controller):
        """Test getting performance metrics"""
        # Add some performance data
        theme_controller.theme_switch_times = [0.1, 0.2, 0.15]
        theme_controller.component_application_times = {"TestComponent": [0.05, 0.06, 0.04]}

        metrics = theme_controller.get_performance_metrics()

        assert metrics["total_theme_switches"] == 3
        assert metrics["average_switch_time"] == 0.15
        assert "TestComponent" in metrics["component_application_times"]

    @pytest.mark.asyncio
    async def test_reload_themes(self, theme_controller, mock_theme_manager):
        """Test reloading themes"""
        # Register theme manager
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Reload themes
        result = await theme_controller.reload_themes()
        assert result is True

    @pytest.mark.asyncio
    async def test_reset_to_default(self, theme_controller, mock_theme_manager):
        """Test resetting to default theme"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Apply different theme first
        await theme_controller.apply_theme("dark")
        assert theme_controller.current_theme.name == "dark"

        # Reset to default
        result = await theme_controller.reset_to_default()
        assert result is True
        assert theme_controller.current_theme.name == "default"

    def test_shutdown(self, theme_controller, mock_theme_manager, mock_theme_component):
        """Test controller shutdown"""
        # Setup some state
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)
        theme_controller.register_component(mock_theme_component, "test_component")
        theme_controller.add_theme_change_listener(Mock())

        # Shutdown
        theme_controller.shutdown()

        # Verify cleanup
        assert len(theme_controller.theme_change_listeners) == 0
        assert len(theme_controller.theme_applied_listeners) == 0
        assert len(theme_controller.theme_error_listeners) == 0
        assert len(theme_controller.registered_components) == 0
        assert len(theme_controller.component_registry) == 0
        assert len(theme_controller.theme_managers) == 0

    @pytest.mark.asyncio
    async def test_persistence_integration(self, theme_controller, mock_theme_manager, mock_config_manager):
        """Test theme persistence integration"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Apply theme
        await theme_controller.apply_theme("dark")

        # Verify persistence calls
        mock_config_manager.set_setting.assert_called()

        # Check that theme was saved to config
        calls = mock_config_manager.set_setting.call_args_list
        theme_calls = [call for call in calls if call[0][0] == "ui.theme"]
        assert len(theme_calls) > 0
        assert theme_calls[-1][0][1] == "dark"  # Last call should be for "dark" theme

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, theme_controller, mock_error_handler):
        """Test error handling integration"""
        # Try to apply theme without any managers (should trigger error handling)
        result = await theme_controller.apply_theme("non_existent")

        # Should have called error handler
        mock_error_handler.handle_error.assert_called()

        # Check error category
        call_args = mock_error_handler.handle_error.call_args
        assert call_args[0][1] == ErrorCategory.INTEGRATION_ERROR

    def test_thread_safety(self, theme_controller, mock_theme_manager):
        """Test thread safety of controller operations"""
        import threading
        import time

        # Register theme manager
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        results = []
        errors = []

        thread_id_counter = [0]  # Use list to make it mutable in nested function

        def register_components():
            try:
                thread_id = thread_id_counter[0]
                thread_id_counter[0] += 1

                for i in range(10):
                    component = MockThemeAware(f"thread_{thread_id}_component_{i}")
                    result = theme_controller.register_component(component, f"thread_{thread_id}_component_{i}")
                    results.append(result)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=register_components)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0  # No errors should occur
        assert len(theme_controller.registered_components) == 50  # All components registered
        assert len(theme_controller.component_registry) == 50  # All components in registry


class TestThemeIntegrationControllerEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_apply_theme_timeout(self, theme_controller, mock_theme_manager):
        """Test theme application timeout handling"""
        # Create a slow component
        slow_component = Mock(spec=IThemeAware)

        async def slow_apply_theme(theme):
            await asyncio.sleep(10)  # Longer than timeout

        slow_component.apply_theme = slow_apply_theme

        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)
        theme_controller.register_component(slow_component)
        theme_controller.theme_application_timeout = 0.1  # Very short timeout

        # Apply theme (should timeout but still succeed due to fallback)
        result = await theme_controller.apply_theme("default")
        assert result is True

    def test_config_manager_failure(self, mock_logger_system, mock_error_handler):
        """Test handling of config manager failures"""
        # Create a failing config manager
        failing_config = Mock(spec=ConfigManager)
        failing_config.get_setting = Mock(side_effect=Exception("Config error"))
        failing_config.set_setting = Mock(side_effect=Exception("Config error"))
        failing_config.add_change_listener = Mock(side_effect=Exception("Config error"))

        # Should not raise exception during initialization
        controller = ThemeIntegrationController(
            config_manager=failing_config,
            logger_system=mock_logger_system,
            error_handler=mock_error_handler,
        )

        # Should handle errors gracefully
        assert controller is not None
        mock_error_handler.handle_error.assert_called()

    @pytest.mark.asyncio
    async def test_async_listener_error_handling(self, theme_controller, mock_theme_manager):
        """Test error handling in async listeners"""
        # Setup
        theme_controller.register_theme_manager("test_manager", mock_theme_manager)

        # Add failing async listener
        async def failing_listener(old_theme, new_theme):
            raise Exception("Listener error")

        theme_controller.add_theme_change_listener(failing_listener)

        # Apply theme (should not fail despite listener error)
        result = await theme_controller.apply_theme("default")
        assert result is True

    def test_memory_cleanup(self, theme_controller, mock_theme_manager):
        """Test memory cleanup and leak prevention"""
        import gc
        import weakref

        # Register many components
        components = []
        weak_refs = []

        for i in range(100):
            component = MockThemeAware(f"component_{i}")
            components.append(component)
            weak_refs.append(weakref.ref(component))
            theme_controller.register_component(component, f"component_{i}")

        # Unregister all components
        for i, component in enumerate(components):
            theme_controller.unregister_component(component, f"component_{i}")

        # Clear local references
        del components
        gc.collect()

        # Check that components were properly cleaned up
        alive_refs = [ref for ref in weak_refs if ref() is not None]
        assert len(alive_refs) == 0  # All components should be garbage collected


if __name__ == "__main__":
    pytest.main([__file__])
