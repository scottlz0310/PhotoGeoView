# PhotoGeoView AI統合 APIドキュメント

生成日時: 2025年07月26日 10:59:48

## 概要

PhotoGeoViewプロジェクトは複数のAIエージェントによって開発されました:
- **GitHub Copilot (CS4Coding)**: コア機能実装、EXIF解析、地図表示
- **Cursor (CursorBLD)**: UI/UX設計、テーマシステム、サムネイル表示
- **Kiro**: 統合・品質管理、パフォーマンス最適化

## AI貢献者別モジュール

### GitHub Copilot (CS4Coding)

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
- PIL
- time
- threading

---

### Cursor (CursorBLD)

#### __init__.py
**目的**: AI Integration Module for PhotoGeoView 

---

#### __init__.py
**目的**: Integrated UI Components for AI Integration 

---

#### config_migration.py
**目的**: Configuration Migration Utilities for AI Integration 

**主要関数**:
- `migrate_all_configurations()`
- `rollback_migration()`
- `get_migration_status()`
- `migrate_all_configurations()`
- `rollback_migration()`

**主要依存関係**:
- json
- datetime
- pathlib

---

#### data_migration.py
**目的**: Data Migration Utilities for AI Integration 

**主要関数**:
- `migrate_all_data()`
- `get_migration_status()`

**主要依存関係**:
- json
- datetime
- pathlib

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
- datetime
- pathlib
- sys

---

#### folder_navigator.py
**目的**: Enhanced Folder Navigator for AI Integration 

**主要関数**:
- `navigate_to_folder()`
- `open_folder_dialog()`
- `get_current_folder()`
- `get_folder_history()`
- `get_bookmarks()`

**主要依存関係**:
- PyQt6.QtWidgets
- platform
- datetime

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
- typing
- datetime
- pathlib

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
- logging.handlers

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
- json
- logging.handlers
- datetime

---

#### main_window.py
**目的**: Integrated Main Window for AI Integration 

**主要関数**:
- `closeEvent()`
- `show_progress()`
- `update_progress()`
- `hide_progress()`
- `get_current_folder()`

**主要依存関係**:
- PyQt6.QtWidgets
- pathlib
- sys

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
- datetime
- pathlib
- enum

---

#### theme_manager.py
**目的**: Integrated Theme Manager for AI Integration 

**主要関数**:
- `get_available_themes()`
- `apply_theme()`
- `get_theme_config()`
- `create_custom_theme()`
- `delete_custom_theme()`

**主要依存関係**:
- json
- PyQt6.QtWidgets
- pathlib

---

#### thumbnail_grid.py
**目的**: Optimized Thumbnail Grid for AI Integration 

**主要関数**:
- `set_thumbnail()`
- `set_exif_info()`
- `mousePressEvent()`
- `mouseDoubleClickEvent()`
- `mousePressEvent()`

**主要依存関係**:
- threading
- time
- PyQt6.QtWidgets

---

#### ui_integration_controller.py
**目的**: UI Integration Controller for AI Integration 

**主要関数**:
- `get_integration_state()`
- `set_thumbnail_size()`
- `refresh_current_folder()`
- `cleanup()`

**主要依存関係**:
- PyQt6.QtWidgets
- PyQt6.QtCore
- datetime

---

### Kiro

#### ai_integration_test_suite.py
**目的**: AI Integration Test Suite 

**主要依存関係**:
- json
- unittest
- time

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
- datetime

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
- threading
- time
- datetime

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
- datetime
- pathlib
- enum

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
- typing
- datetime
- pathlib

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
- json
- datetime
- pathlib

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
- threading
- time
- collections

---

#### performance_optimizer.py
**目的**: Performance Optimizer for AI Integration 

**主要関数**:
- `start_optimization()`
- `stop_optimization()`
- `create_resource_pool()`
- `get_resource()`
- `return_resource()`

**主要依存関係**:
- threading
- time
- collections

---

#### state_manager.py
**目的**: Unified State Manager for AI Integration 

**主要関数**:
- `get_state_value()`
- `set_state_value()`
- `update_state()`
- `add_change_listener()`
- `remove_change_listener()`

**主要依存関係**:
- json
- threading
- collections

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
- threading
- time
- collections

---
