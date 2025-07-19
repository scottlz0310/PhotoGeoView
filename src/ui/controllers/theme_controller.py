"""
Theme Controller for PhotoGeoView
Manages theme selection, cycling, and context menu operations
"""

from PyQt6.QtWidgets import QMenu, QWidget
from PyQt6.QtCore import QObject, pyqtSignal, QPoint, Qt
from PyQt6.QtGui import QAction
from typing import Dict, Optional, List

from src.core.logger import get_logger
from src.core.settings import SettingsManager
from src.ui.theme_manager import ThemeManager


class ThemeController(QObject):
    """
    Controller for theme management operations
    Handles theme switching, menu operations, and user interactions
    """

    # Signals
    theme_applied = pyqtSignal(str)  # Emitted when theme is successfully applied
    status_message = pyqtSignal(str, int)  # For status bar updates (message, timeout)

    def __init__(self, settings: SettingsManager, theme_manager: ThemeManager, parent=None):
        """Initialize theme controller"""
        super().__init__(parent)

        self.logger = get_logger(__name__)
        self.settings = settings
        self.theme_manager = theme_manager

        # Theme actions storage for persistent menu
        self.theme_actions: Dict[str, QAction] = {}
        self.status_action: Optional[QAction] = None  # Reference for menu updates

        # Connect theme manager signals
        self.theme_manager.theme_changed.connect(self.on_theme_changed)

        self.logger.debug("Theme controller initialized")

    def toggle_theme(self) -> None:
        """Toggle between selected themes in order"""
        try:
            selected_themes = self.settings.ui.selected_themes

            # If no themes selected or only one theme, fall back to simple dark/light toggle
            if len(selected_themes) <= 1:
                current_theme = self.settings.ui.current_theme
                if 'dark' in current_theme.lower():
                    new_theme = "light_blue.xml"
                else:
                    new_theme = "dark_blue.xml"

                # Update selection to include both themes for future toggling
                self.settings.ui.selected_themes = [current_theme, new_theme]
                self.settings.ui.theme_toggle_index = 1
            else:
                # Cycle through selected themes
                current_index = self.settings.ui.theme_toggle_index
                next_index = (current_index + 1) % len(selected_themes)
                new_theme = selected_themes[next_index]
                self.settings.ui.theme_toggle_index = next_index

            # Apply the theme
            if self.theme_manager.apply_theme(new_theme):
                self.settings.ui.current_theme = new_theme
                self.settings.save()

                # Show which theme we're on in multi-theme mode
                if len(selected_themes) > 1:
                    theme_position = f" ({self.settings.ui.theme_toggle_index + 1}/{len(selected_themes)})"
                    display_name = new_theme.replace('.xml', '').replace('_', ' ').title()
                    self.status_message.emit(f"Theme: {display_name}{theme_position}", 2000)

                self.logger.info(f"Theme toggled to: {new_theme} (index {self.settings.ui.theme_toggle_index})")
            else:
                self.logger.error(f"Failed to apply theme: {new_theme}")

        except Exception as e:
            self.logger.error(f"Error toggling theme: {e}")

    def show_theme_menu(self, position: QPoint, parent_widget) -> None:
        """Show theme selection context menu with multiple selection support"""
        try:
            # Create persistent context menu that doesn't auto-close
            menu = QMenu(parent_widget)
            menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
            current_theme = self.settings.ui.current_theme
            selected_themes = self.settings.ui.selected_themes

            # Add header with instructions
            info_action = QAction("🎨 Multi-Theme Selector", parent_widget)
            info_action.setEnabled(False)
            font = info_action.font()
            font.setBold(True)
            info_action.setFont(font)
            menu.addAction(info_action)

            instruction_action = QAction("   → Click themes to add/remove from selection", parent_widget)
            instruction_action.setEnabled(False)
            menu.addAction(instruction_action)
            menu.addSeparator()

            # Store theme actions for updating display
            self.theme_actions = {}

            # Add available themes to menu with visual indicators
            for theme in self.theme_manager.available_themes:
                display_name = theme.replace('.xml', '').replace('_', ' ').title()

                # Add status indicators
                if theme == current_theme:
                    display_name = f"● {display_name} (Active)"
                elif theme in selected_themes:
                    display_name = f"✓ {display_name}"
                else:
                    display_name = f"   {display_name}"

                action = QAction(display_name, parent_widget)
                action.setCheckable(False)

                # Connect with a closure to avoid lambda issues
                def make_toggle_handler(theme_name: str, menu_ref: QMenu):
                    return lambda: self.toggle_theme_in_persistent_menu(theme_name, menu_ref)

                action.triggered.connect(make_toggle_handler(theme, menu))
                menu.addAction(action)
                self.theme_actions[theme] = action

            menu.addSeparator()

            # Add status and control buttons
            selection_count = len(selected_themes)
            status_text = f"📊 Selected: {selection_count} theme{'s' if selection_count != 1 else ''}"

            status_action = QAction(status_text, parent_widget)
            status_action.setEnabled(False)
            menu.addAction(status_action)
            self.status_action = status_action  # Store reference for updates

            menu.addSeparator()

            # Utility buttons
            clear_action = QAction("🗑️ Clear All", parent_widget)
            clear_action.triggered.connect(lambda: self.clear_and_update_menu(menu))
            menu.addAction(clear_action)

            select_all_action = QAction("✓ Select All", parent_widget)
            select_all_action.triggered.connect(lambda: self.select_all_and_update_menu(menu))
            menu.addAction(select_all_action)

            menu.addSeparator()

            # Close button
            close_action = QAction("✅ Done", parent_widget)
            close_action.triggered.connect(menu.close)
            font.setBold(True)
            close_action.setFont(font)
            menu.addAction(close_action)

            # Show menu at cursor position (better UX than toolbar position)
            global_pos = parent_widget.mapToGlobal(position)
            menu.popup(global_pos)

        except Exception as e:
            self.logger.error(f"Error showing theme menu: {e}")

    def toggle_theme_selection(self, theme_name: str) -> None:
        """Toggle theme selection for multi-theme cycling"""
        try:
            selected_themes = self.settings.ui.selected_themes.copy()

            if theme_name in selected_themes:
                # Remove from selection
                selected_themes.remove(theme_name)
                self.logger.info(f"Removed theme from selection: {theme_name}")
            else:
                # Add to selection
                selected_themes.append(theme_name)
                self.logger.info(f"Added theme to selection: {theme_name}")

            # Update settings
            self.settings.ui.selected_themes = selected_themes

            # Reset toggle index if selection changed
            if len(selected_themes) > 0:
                # Find current theme index in new selection, or reset to 0
                try:
                    current_index = selected_themes.index(self.settings.ui.current_theme)
                    self.settings.ui.theme_toggle_index = current_index
                except ValueError:
                    self.settings.ui.theme_toggle_index = 0

            self.settings.save()

        except Exception as e:
            self.logger.error(f"Error toggling theme selection {theme_name}: {e}")

    def toggle_theme_in_persistent_menu(self, theme_name: str, menu: QMenu) -> None:
        """Toggle theme selection and update the menu without closing it"""
        try:
            selected_themes = self.settings.ui.selected_themes.copy()
            current_theme = self.settings.ui.current_theme

            if theme_name in selected_themes:
                # Remove from selection (but don't allow removing the current theme if it's the only one)
                if len(selected_themes) > 1 or theme_name != current_theme:
                    selected_themes.remove(theme_name)
                    self.logger.info(f"Removed theme from selection: {theme_name}")
            else:
                # Add to selection
                selected_themes.append(theme_name)
                self.logger.info(f"Added theme to selection: {theme_name}")

            # Update settings
            self.settings.ui.selected_themes = selected_themes

            # Update toggle index if current theme is still in selection
            if current_theme in selected_themes:
                self.settings.ui.theme_toggle_index = selected_themes.index(current_theme)
            else:
                self.settings.ui.theme_toggle_index = 0

            self.settings.save()

            # Update menu display immediately
            self.refresh_menu_display(menu)

        except Exception as e:
            self.logger.error(f"Error toggling theme selection {theme_name}: {e}")

    def refresh_menu_display(self, menu: QMenu) -> None:
        """Refresh the menu display to show current selection state"""
        try:
            current_theme = self.settings.ui.current_theme
            selected_themes = self.settings.ui.selected_themes

            # Update theme action texts
            if hasattr(self, 'theme_actions'):
                for theme, action in self.theme_actions.items():
                    display_name = theme.replace('.xml', '').replace('_', ' ').title()

                    if theme == current_theme:
                        display_name = f"● {display_name} (Active)"
                    elif theme in selected_themes:
                        display_name = f"✓ {display_name}"
                    else:
                        display_name = f"   {display_name}"

                    action.setText(display_name)

            # Update status text
            if self.status_action is not None:
                selection_count = len(selected_themes)
                status_text = f"📊 Selected: {selection_count} theme{'s' if selection_count != 1 else ''}"
                self.status_action.setText(status_text)

        except Exception as e:
            self.logger.error(f"Error refreshing menu display: {e}")

    def clear_and_update_menu(self, menu: QMenu) -> None:
        """Clear all selections except current theme and update menu"""
        try:
            current_theme = self.settings.ui.current_theme
            self.settings.ui.selected_themes = [current_theme]
            self.settings.ui.theme_toggle_index = 0
            self.settings.save()
            self.logger.info("Cleared all theme selections")

            # Refresh menu
            self.refresh_menu_display(menu)

        except Exception as e:
            self.logger.error(f"Error clearing selections: {e}")

    def select_all_and_update_menu(self, menu: QMenu) -> None:
        """Select all themes and update menu"""
        try:
            # Select all available themes
            self.settings.ui.selected_themes = self.theme_manager.available_themes.copy()

            # Set current theme index
            current_theme = self.settings.ui.current_theme
            if current_theme in self.settings.ui.selected_themes:
                self.settings.ui.theme_toggle_index = self.settings.ui.selected_themes.index(current_theme)

            self.settings.save()
            self.logger.info("Selected all themes")

            # Refresh menu
            self.refresh_menu_display(menu)

        except Exception as e:
            self.logger.error(f"Error selecting all themes: {e}")

    def clear_theme_selection(self) -> None:
        """Clear all theme selections"""
        try:
            self.settings.ui.selected_themes = [self.settings.ui.current_theme]
            self.settings.ui.theme_toggle_index = 0
            self.settings.save()
            self.logger.info("Cleared all theme selections")

        except Exception as e:
            self.logger.error(f"Error clearing theme selection: {e}")

    def apply_selected_themes(self) -> None:
        """Apply the currently selected themes for cycling"""
        try:
            selected_themes = self.settings.ui.selected_themes
            if not selected_themes:
                return

            # Ensure current theme is in the selection
            if self.settings.ui.current_theme not in selected_themes:
                selected_themes.insert(0, self.settings.ui.current_theme)
                self.settings.ui.selected_themes = selected_themes

            self.settings.save()
            self.logger.info(f"Applied theme selection: {selected_themes}")

        except Exception as e:
            self.logger.error(f"Error applying selected themes: {e}")

    def select_theme(self, theme_name: str) -> None:
        """Select and apply a specific theme directly"""
        try:
            if self.theme_manager.apply_theme(theme_name):
                self.settings.ui.current_theme = theme_name

                # Update toggle index to match current theme if it's in selection
                selected_themes = self.settings.ui.selected_themes
                if theme_name in selected_themes:
                    self.settings.ui.theme_toggle_index = selected_themes.index(theme_name)

                self.settings.save()
                self.logger.info(f"Theme selected: {theme_name}")
            else:
                self.logger.error(f"Failed to apply theme: {theme_name}")

        except Exception as e:
            self.logger.error(f"Error selecting theme {theme_name}: {e}")

    def on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change event"""
        self.settings.ui.current_theme = theme_name
        self.theme_applied.emit(theme_name)
        self.logger.info(f"Theme changed to: {theme_name}")

    def validate_all_themes(self) -> dict:
        """
        Validate all 16 themes work properly with current system
        Phase 4: Complete theme validation

        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'total_themes': 0,
            'working_themes': [],
            'failed_themes': [],
            'compatibility_rate': 0.0,
            'recommendations': []
        }

        try:
            available_themes = self.theme_manager.get_available_themes()
            validation_results['total_themes'] = len(available_themes)

            # Store current theme to restore later
            original_theme = self.theme_manager.get_current_theme()

            for theme in available_themes:
                try:
                    self.logger.debug(f"Testing theme: {theme}")
                    success = self.theme_manager.apply_theme_with_verification(theme)

                    if success:
                        validation_results['working_themes'].append(theme)
                        self.logger.debug(f"Theme {theme} - OK")
                    else:
                        validation_results['failed_themes'].append(theme)
                        self.logger.warning(f"Theme {theme} - FAILED")

                except Exception as e:
                    validation_results['failed_themes'].append(theme)
                    self.logger.error(f"Theme {theme} validation error: {e}")

            # Calculate compatibility rate
            working_count = len(validation_results['working_themes'])
            total_count = validation_results['total_themes']
            validation_results['compatibility_rate'] = working_count / total_count if total_count > 0 else 0

            # Generate recommendations
            if validation_results['compatibility_rate'] < 0.8:
                validation_results['recommendations'].append("Low theme compatibility detected")
                validation_results['recommendations'].append("Consider updating Qt Theme Manager")

            if validation_results['failed_themes']:
                validation_results['recommendations'].append(f"Avoid using: {', '.join(validation_results['failed_themes'])}")

            # Restore original theme
            self.theme_manager.apply_theme(original_theme)

            self.logger.info(f"Theme validation complete: {working_count}/{total_count} themes working ({validation_results['compatibility_rate']:.1%})")

        except Exception as e:
            self.logger.error(f"Theme validation error: {e}")
            validation_results['recommendations'].append(f"Validation failed: {str(e)}")

        return validation_results

    def create_theme_performance_test(self) -> dict:
        """
        Test theme switching performance
        Phase 4: UI/UX optimization

        Returns:
            Performance test results
        """
        import time

        performance_results = {
            'average_switch_time': 0.0,
            'fastest_theme': '',
            'slowest_theme': '',
            'total_test_time': 0.0,
            'themes_tested': 0
        }

        try:
            themes_to_test = self.theme_manager.get_available_themes()[:5]  # Test first 5 themes
            original_theme = self.theme_manager.get_current_theme()

            switch_times = {}
            total_start_time = time.time()

            for theme in themes_to_test:
                start_time = time.time()
                success = self.theme_manager.apply_theme(theme)
                end_time = time.time()

                if success:
                    switch_time = end_time - start_time
                    switch_times[theme] = switch_time
                    self.logger.debug(f"Theme {theme} switch time: {switch_time:.3f}s")

            total_end_time = time.time()

            if switch_times:
                performance_results['average_switch_time'] = sum(switch_times.values()) / len(switch_times)
                performance_results['fastest_theme'] = min(switch_times, key=switch_times.get)
                performance_results['slowest_theme'] = max(switch_times, key=switch_times.get)
                performance_results['total_test_time'] = total_end_time - total_start_time
                performance_results['themes_tested'] = len(switch_times)

            # Restore original theme
            self.theme_manager.apply_theme(original_theme)

            self.logger.info(f"Theme performance test complete: avg {performance_results['average_switch_time']:.3f}s")

        except Exception as e:
            self.logger.error(f"Theme performance test error: {e}")

        return performance_results

    def apply_theme_with_animation_effect(self, theme_name: str) -> bool:
        """
        Apply theme with smooth transition effect
        Phase 4: Animation effects

        Args:
            theme_name: Theme to apply

        Returns:
            True if successful
        """
        try:
            # Future: Add fade transition effect here
            # For now, apply theme normally
            success = self.theme_manager.apply_theme_with_verification(theme_name)

            if success:
                # Emit status with visual feedback
                display_name = self.theme_manager.get_theme_display_name(theme_name)
                category = self.theme_manager.get_theme_category(theme_name)

                icon = "🌙" if category == 'dark' else "☀️"
                self.status_message.emit(f"{icon} {display_name}", 3000)

                # Update settings
                self.settings.ui.current_theme = theme_name
                self.settings.save()

            return success

        except Exception as e:
            self.logger.error(f"Error applying theme with animation: {e}")
            return False

    def get_theme_recommendations(self) -> List[str]:
        """
        Get theme recommendations based on current system and usage
        Phase 4: UI/UX optimization

        Returns:
            List of recommended theme names
        """
        try:
            recommendations = []

            # Get theme statistics
            stats = self.theme_manager.get_theme_statistics()

            # Basic recommendations
            if stats['qt_theme_manager_available']:
                recommendations.extend(['dark_blue.xml', 'light_blue.xml'])  # Safe defaults

                # Add variety recommendations
                recommendations.extend(['dark_purple.xml', 'light_orange.xml'])
            else:
                # Fallback theme recommendations
                recommendations = ['dark_blue.xml', 'light_blue.xml']

            self.logger.debug(f"Generated {len(recommendations)} theme recommendations")
            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating theme recommendations: {e}")
            return ['dark_blue.xml']  # Safe fallback

    def toggle_between_theme_categories(self) -> None:
        """
        Smart toggle between light and dark theme variants
        Phase 4: Enhanced theme switching
        """
        try:
            new_theme = self.theme_manager.toggle_theme_type()

            if new_theme != self.theme_manager.get_current_theme():
                # Update settings
                self.settings.ui.current_theme = new_theme
                self.settings.save()

                # Provide user feedback
                category = self.theme_manager.get_theme_category(new_theme)
                icon = "🌙" if category == 'dark' else "☀️"
                display_name = self.theme_manager.get_theme_display_name(new_theme)

                self.status_message.emit(f"{icon} Switched to {display_name}", 2500)
                self.logger.info(f"Theme category toggled to: {new_theme}")

        except Exception as e:
            self.logger.error(f"Error toggling theme categories: {e}")
