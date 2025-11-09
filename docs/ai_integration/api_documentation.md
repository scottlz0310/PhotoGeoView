# PhotoGeoView AI統合 APIドキュメント

生成日時: 2025年11月09日 20:50:39

## 概要

PhotoGeoViewプロジェクトは複数のAIエージェントによって開発されました:
- **GitHub Copilot (CS4Coding)**: コア機能実装、EXIF解析、地図表示
- **Cursor (CursorBLD)**: UI/UX設計、テーマシステム、サムネイル表示
- **Kiro**: 統合・品質管理、パフォーマンス最適化

## AI貢献者別モジュール

### GitHub Copilot (CS4Coding)

#### __main__.py
**目的**: PhotoGeoView CLI エントリーポイント

**主要関数**:
- `main()`

**主要依存関係**:
- sys
- main as main_module
- traceback

---

#### exif_labels.py
**目的**: EXIF Panel Labels Configuration

**主要関数**:
- `get_label()`
- `get_section_labels()`
- `set_language()`
- `get_available_languages()`
- `export_labels_for_theme()`

**主要依存関係**:
- typing

---

#### image_loader.py
**目的**: 目的不明

---

#### image_processor.py
**目的**: CS4Coding ImageProcessor with Kiro Integration

**主要関数**:
- `load_image()`
- `generate_thumbnail()`
- `extract_exif()`
- `get_supported_formats()`
- `validate_image()`

**主要依存関係**:
- time
- exifread
- PIL

---

#### map_panel.py
**目的**: Map Panel - 地図表示パネル

**主要関数**:
- `set_coordinates()`
- `add_image_location()`
- `get_current_coordinates()`
- `show_no_gps_message()`
- `get_image_locations()`

**主要依存関係**:
- os
- PySide6.QtWidgets
- PySide6.QtWebEngineWidgets

---

#### map_provider.py
**目的**: Map Provider - 地図表示プロバイダー

**主要関数**:
- `create_map()`
- `add_marker()`
- `render_html()`
- `set_map_bounds()`
- `add_image_overlay()`

**主要依存関係**:
- pathlib
- typing
- folium

---

### Cursor (CursorBLD)

#### __init__.py
**目的**: PhotoGeoView - AI統合写真地理情報ビューア

---

#### __init__.py
**目的**: AI Integration Module for PhotoGeoView

---

#### __init__.py
**目的**: Integrated UI Components for AI Integration

---

#### breadcrumb_fallback.py
**目的**: BreadcrumbWidget フォールバック実装

**主要関数**:
- `setup_ui()`
- `setPath()`
- `getPath()`
- `update_breadcrumb()`
- `add_segment()`

**主要依存関係**:
- PySide6.QtWidgets
- logging
- pathlib

---

#### config_migration.py
**目的**: Configuration Migration Utilities for AI Integration

**主要関数**:
- `migrate_all_configurations()`
- `rollback_migration()`
- `get_migration_status()`

**主要依存関係**:
- json
- dataclasses
- enum

---

#### data_migration.py
**目的**: Data Migration Utilities for AI Integration

**主要関数**:
- `migrate_all_data()`
- `get_migration_status()`

**主要依存関係**:
- json
- dataclasses
- enum

---

#### error_handling.py
**目的**: Unified Error Handling System for AI Integration

**主要関数**:
- `handle_error()`
- `get_error_statistics()`
- `clear_error_history()`
- `register_recovery_handler()`
- `register_fallback_handler()`

**主要依存関係**:
- traceback
- dataclasses
- logging

---

#### file_discovery_errors.py
**目的**: FileDiscoveryService専用エラーハンドリングシステム

**主要関数**:
- `get_error_message()`
- `get_recovery_suggestions()`
- `handle_error()`
- `get_error_statistics()`
- `clear_error_history()`

**主要依存関係**:
- datetime
- dataclasses
- enum

---

#### folder_navigator.py
**目的**: Enhanced Folder Navigator for AI Integration - 拡張フォルダナビゲーター

**主要関数**:
- `stop_monitoring()`
- `navigate_to_folder()`
- `open_folder_dialog()`
- `get_current_folder()`
- `get_folder_history()`

**主要依存関係**:
- PySide6.QtWidgets
- pathlib
- PySide6.QtCore

---

#### interfaces.py
**目的**: Core Interfaces for AI Integration

**主要関数**:
- `load_image()`
- `generate_thumbnail()`
- `extract_exif()`
- `get_supported_formats()`
- `validate_image()`

**主要依存関係**:
- abc
- pathlib
- typing

---

#### logging.py
**目的**: Integrated Logging System for AI Integration

**主要関数**:
- `debug()`
- `info()`
- `warning()`
- `error()`
- `critical()`

**主要依存関係**:
- json
- threading
- logging

---

#### logging_system.py
**目的**: Unified Logging System for AI Integration

**主要関数**:
- `format()`
- `emit()`
- `flush_metrics()`
- `get_logger()`
- `log_ai_operation()`

**主要依存関係**:
- os
- json
- logging

---

#### models.py
**目的**: Unified Data Models for AI Integration

**主要関数**:
- `has_gps()`
- `gps_coordinates()`
- `aspect_ratio()`
- `megapixels()`
- `is_dark_theme()`

**主要依存関係**:
- dataclasses
- enum
- pathlib

---

#### theme_editor.py
**目的**: Theme Editor Interface Components

**主要関数**:
- `set_color()`
- `get_color()`
- `set_font()`
- `get_font()`
- `update_preview()`

**主要依存関係**:
- json
- PySide6.QtWidgets
- pathlib

---

#### theme_manager.py
**目的**: Integrated Theme Manager for AI Integration

**主要関数**:
- `get_available_themes()`
- `set_theme()`
- `set_main_window()`
- `get_available_themes()`
- `debug_theme_status()`

**主要依存関係**:
- json
- traceback
- PySide6.QtWidgets

---

#### theme_manager_fallback.py
**目的**: ThemeManager フォールバック実装

**主要関数**:
- `get_available_themes()`
- `get_current_theme()`
- `set_theme()`
- `apply_theme()`
- `get_theme_info()`

**主要依存関係**:
- PySide6.QtCore
- PySide6.QtWidgets
- qt_theme_manager

---

#### theme_models.py
**目的**: Theme Config Data Models

**主要関数**:
- `to_css()`
- `is_dark_theme()`
- `validate()`
- `to_dict()`
- `from_dict()`

**主要依存関係**:
- json
- dataclasses
- enum

---

#### theme_selector.py
**目的**: 洗練されたテーマ選択UIコンポーネント

**主要関数**:
- `setup_ui()`
- `apply_theme_preview()`
- `setup_ui()`
- `load_saved_selections()`
- `create_theme_grid()`

**主要依存関係**:
- dataclasses
- PySide6.QtWidgets
- PySide6.QtCore

---

#### thumbnail_grid.py
**目的**: Optimized Thumbnail Grid for AI Integration - 最適化サムネイルグリッド

**主要関数**:
- `set_theme_manager()`
- `changeEvent()`
- `set_thumbnail()`
- `set_exif_info()`
- `mousePressEvent()`

**主要依存関係**:
- time
- PySide6.QtGui
- PySide6.QtWidgets

---

#### ui_integration_controller.py
**目的**: UI Integration Controller for AI Integration

**主要関数**:
- `get_integration_state()`
- `set_thumbnail_size()`
- `refresh_current_folder()`
- `cleanup()`

**主要依存関係**:
- dataclasses
- PySide6.QtWidgets
- pathlib

---

### Kiro

#### __init__.py
**目的**: Services module for AI Integration

---

#### ai_integration_test_suite.py
**目的**: AI Integration Test Suite

**主要依存関係**:
- datetime
- dataclasses
- typing

---

#### breadcrumb_bar.py
**目的**: Breadcrumb Address Bar Wrapper Component

**主要関数**:
- `eventFilter()`
- `get_keyboard_shortcuts_info()`
- `set_accessibility_enabled()`
- `get_widget()`
- `set_current_path()`

**主要依存関係**:
- os
- time
- inspect

---

#### config_manager.py
**目的**: Unified Configuration Management System for AI Integration

**主要関数**:
- `get_setting()`
- `set_setting()`
- `get_ai_config()`
- `set_ai_config()`
- `update_ai_config()`

**主要依存関係**:
- json
- threading
- pathlib

---

#### controllers.py
**目的**: Central Application Controller for AI Integration

**主要関数**:
- `initialize()`
- `save_application_state()`
- `register_event_handler()`
- `unregister_event_handler()`
- `emit_event()`

**主要依存関係**:
- time
- threading
- logging

---

#### data_validation.py
**目的**: Data Validation System for AI Integration

**主要関数**:
- `add_issue()`
- `total_issues()`
- `has_errors()`
- `has_warnings()`
- `validate_image_metadata()`

**主要依存関係**:
- dataclasses
- enum
- pathlib

---

#### doc_templates.py
**目的**: AI統合ドキュメントテンプレートシステム

**主要関数**:
- `get_template()`
- `render_template()`
- `add_custom_template()`
- `list_templates()`
- `get_template_info()`

**主要依存関係**:
- datetime
- dataclasses
- logging

---

#### documentation_system.py
**目的**: AI統合ドキュメントシステム

**主要関数**:
- `analyze_file_contributions()`
- `generate_file_header()`
- `generate_unified_api_documentation()`
- `generate_troubleshooting_guide()`
- `scan_project_files()`

**主要依存関係**:
- dataclasses
- logging
- enum

---

#### exif_panel.py
**目的**: EXIF Information Panel - EXIF情報表示パネル

**主要関数**:
- `changeEvent()`
- `set_image()`
- `apply_theme()`
- `deleteLater()`

**主要依存関係**:
- PySide6.QtWidgets
- PySide6.QtCore
- pathlib

---

#### file_discovery_cache.py
**目的**: FileDiscoveryCache - ファイル検出結果キャッシュシステム

**主要関数**:
- `is_expired()`
- `is_expired()`
- `update_hit_rate()`
- `to_dict()`
- `cache_file_result()`

**主要依存関係**:
- time
- dataclasses
- threading

---

#### file_discovery_service.py
**目的**: FileDiscoveryService - 画像ファイル検出サービス

**主要関数**:
- `measure_performance()`
- `decorator()`
- `wrapper()`
- `discover_images()`
- `validate_image_file()`

**主要依存関係**:
- time
- os
- functools

---

#### file_system_watcher.py
**目的**: FileSystemWatcher - ファイルシステム監視サービス

**主要関数**:
- `start_watching()`
- `stop_watching()`
- `add_change_listener()`
- `remove_change_listener()`
- `get_watch_status()`

**主要依存関係**:
- time
- watchdog.observers
- watchdog.events

---

#### image_preview_panel.py
**目的**: Image Preview Panel - 画像プレビューパネル

**主要関数**:
- `set_image()`
- `set_zoom()`
- `paintEvent()`
- `wheelEvent()`
- `mousePressEvent()`

**主要依存関係**:
- PySide6.QtGui
- pathlib
- PySide6.QtCore

---

#### main_window.py
**目的**: Integrated Main Window for AI Integration

**主要関数**:
- `apply_theme()`
- `get_available_themes()`
- `get_current_theme()`
- `get_widget()`
- `set_current_path()`

**主要依存関係**:
- os
- ui.breadcrumb_bar
- PySide6.QtWidgets

---

#### memory_aware_file_discovery.py
**目的**: MemoryAwareFileDiscovery - メモリ管理機能付きファイル検出

**主要関数**:
- `is_high_usage()`
- `is_critical_usage()`
- `discover_images_with_memory_management()`
- `get_memory_status()`
- `force_memory_cleanup()`

**主要依存関係**:
- time
- dataclasses
- gc

---

#### navigation_integration_controller.py
**目的**: Navigation Integration Controller

**主要関数**:
- `register_navigation_component()`
- `unregister_navigation_component()`
- `register_navigation_manager()`
- `unregister_navigation_manager()`
- `navigate_to_path()`

**主要依存関係**:
- os
- threading
- pathlib

---

#### navigation_interfaces.py
**目的**: Navigation Integration Interfaces

**主要関数**:
- `resolve_path()`
- `validate_path()`
- `get_path_info()`
- `get_parent_path()`
- `list_child_paths()`

**主要依存関係**:
- typing
- abc
- pathlib

---

#### navigation_models.py
**目的**: Navigation State Models for Breadcrumb Functionality

**主要関数**:
- `update_access_info()`
- `refresh_state()`
- `to_dict()`
- `refresh()`
- `usage_percentage()`

**主要依存関係**:
- os
- dataclasses
- enum

---

#### paginated_file_discovery.py
**目的**: PaginatedFileDiscovery - 段階的ファイル読み込み機能

**主要関数**:
- `is_last_batch()`
- `initialize_folder()`
- `get_next_batch()`
- `has_more_files()`
- `reset_pagination()`

**主要依存関係**:
- time
- dataclasses
- pathlib

---

#### performance_dashboard.py
**目的**: Performance Monitoring Dashboard

**主要関数**:
- `to_dict()`
- `start_monitoring()`
- `stop_monitoring()`
- `get_current_metrics()`
- `get_metrics_summary()`

**主要依存関係**:
- time
- json
- os

---

#### performance_monitor.py
**目的**: Kiro Performance Monitor

**主要関数**:
- `start_monitoring()`
- `stop_monitoring()`
- `get_memory_usage()`
- `get_performance_metrics()`
- `log_operation_time()`

**主要依存関係**:
- os
- time
- dataclasses

---

#### performance_optimizer.py
**目的**: Performance Optimizer for Theme and Navigation Components

**主要関数**:
- `get()`
- `set()`
- `clear()`
- `size()`
- `is_loaded()`

**主要依存関係**:
- time
- threading
- pathlib

---

#### state_manager.py
**目的**: Unified State Manager for AI Integration

**主要関数**:
- `get_state()`
- `get_state_value()`
- `set_state_value()`
- `update_state()`
- `add_change_listener()`

**主要依存関係**:
- json
- dataclasses
- threading

---

#### theme_integration_controller.py
**目的**: Theme Integration Controller

**主要関数**:
- `register_theme_manager()`
- `unregister_theme_manager()`
- `register_component()`
- `unregister_component()`
- `get_registered_component()`

**主要依存関係**:
- threading
- typing
- datetime

---

#### theme_interfaces.py
**目的**: Theme Integration Interfaces

**主要関数**:
- `get_available_themes()`
- `load_theme()`
- `save_theme()`
- `delete_theme()`
- `validate_theme()`

**主要依存関係**:
- typing
- abc
- pathlib

---

#### theme_navigation_integration.py
**目的**: Theme and Navigation Integration Interfaces

**主要関数**:
- `get_current_theme()`
- `get_navigation_state()`
- `apply_theme_to_navigation()`
- `register_integrated_component()`
- `unregister_integrated_component()`

**主要依存関係**:
- typing
- abc
- collections.abc

---

#### unified_cache.py
**目的**: Unified Caching System for AI Integration

**主要関数**:
- `update_hit_rate()`
- `get()`
- `put()`
- `remove()`
- `clear()`

**主要依存関係**:
- dataclasses
- threading
- collections

---

#### user_notification_system.py
**目的**: User Notification System for Error Handling and Warnings

**主要関数**:
- `show_notification()`
- `dismiss_notification()`
- `dismiss_all_notifications()`
- `show_error()`
- `show_warning()`

**主要依存関係**:
- PySide6.QtWidgets
- enum
- PySide6.QtCore

---

#### webengine_checker.py
**目的**: WebEngine Checker - PyQtWebEngine利用可能性チェック

**主要関数**:
- `check_webengine_availability()`
- `initialize_webengine_safe()`
- `create_webengine_view()`
- `get_webengine_status()`

**主要依存関係**:
- PySide6.QtWebEngineCore
- PySide6.QtWebEngineWidgets

---
