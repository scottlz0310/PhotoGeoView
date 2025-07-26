# PhotoGeoView AI統合品質レポート

生成日時: 1753496086.5019069

## 概要

- **総ファイル数**: 26
- **総問題数**: 128
- **総合スコア**: 0.0/100

## 重要度別問題数

- **acceptable**: 94件
- **poor**: 28件
- **critical**: 6件

## AI コンポーネント別問題数

- **copilot**: 7件
- **cursor**: 21件
- **kiro**: 100件

## 詳細問題一覧

### config_manager.py:38
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '__init__' が長すぎます (52行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:230
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_get_default_ai_config' が長すぎます (51行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:441
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'set_setting' が長すぎます (49行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:509
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'set_ai_config' が長すぎます (44行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:555
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'update_ai_config' が長すぎます (48行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:792
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'export_config' が長すぎます (41行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:835
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'import_config' が長すぎます (50行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:1186
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_save_application_state_to_file' が長すぎます (42行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:1230
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_load_application_state' が長すぎます (55行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### config_manager.py:780
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'add_change_listener' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### config_manager.py:786
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'remove_change_listener' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### controllers.py:48
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '__init__' が長すぎます (58行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### controllers.py:108
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'initialize' が長すぎます (41行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### controllers.py:151
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_initialize_ai_components' が長すぎます (45行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### controllers.py:532
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'load_folder_contents' が長すぎます (52行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### controllers.py:641
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'shutdown' が長すぎます (47行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### controllers.py:246
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'save_application_state' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### controllers.py:280
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'register_event_handler' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### controllers.py:288
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'unregister_event_handler' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### controllers.py:298
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'emit_event' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### controllers.py:592
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'add_to_cache' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### controllers.py:605
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'clear_cache' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### controllers.py:641
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'shutdown' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### data_validation.py:289
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'validate_application_state' が長すぎます (60行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### data_validation.py:40
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'add_issue' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### data_validation.py:1
- **重要度**: acceptable
- **タイプ**: insufficient_ai_integration
- **AI コンポーネント**: kiro
- **問題**: 統合ファイルでAI言及が不足しています
- **提案**: 複数のAIコンポーネントとの統合を明確にしてください

### doc_templates.py:289
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'example_usage' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### documentation_system.py:275
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'generate_file_header' が長すぎます (55行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### documentation_system.py:332
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'generate_unified_api_documentation' が長すぎます (58行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### documentation_system.py:629
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'update_file_headers' が長すぎます (42行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### documentation_system.py:675
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'main' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### error_handling.py:116
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 'handle_error' が長すぎます (37行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### error_handling.py:253
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_get_recovery_suggestions' が長すぎます (40行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### image_processor.py:222
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: copilot
- **問題**: 関数 'generate_thumbnail' が長すぎます (60行, 推奨: 50行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### image_processor.py:392
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: copilot
- **問題**: 関数 '_parse_exifread_tags' が長すぎます (58行, 推奨: 50行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### image_processor.py:833
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: copilot
- **問題**: 関数 'clear_cache' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### image_processor.py:890
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: copilot
- **問題**: 関数 'shutdown' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### logging_system.py:117
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '__init__' が長すぎます (39行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### logging_system.py:185
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_setup_file_handlers' が長すぎます (43行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### logging_system.py:260
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 'log_ai_operation' が長すぎます (34行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### logging_system.py:374
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 'create_performance_metrics' が長すぎます (31行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:254
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'get_performance_metrics' が長すぎます (47行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:411
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_collect_metrics' が長すぎます (44行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:523
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_create_alert' が長すぎます (52行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:828
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_collect_enhanced_metrics' が長すぎます (60行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:942
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_emit_performance_alert' が長すぎます (52行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:1121
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'get_performance_summary' が長すぎます (53行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:579
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'add_alert_handler' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:584
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'remove_alert_handler' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:655
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'clear_alerts' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:660
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'update_thresholds' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:694
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'shutdown' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:745
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'set_optimizer' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:749
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'start_monitoring' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:777
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'stop_monitoring' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:1059
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'add_alert_handler' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:1064
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'remove_alert_handler' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:1069
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'record_operation_time' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:1097
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'update_thresholds' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_monitor.py:1176
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'cleanup' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_optimizer.py:357
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_detect_bottlenecks' が長すぎます (42行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_optimizer.py:487
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_optimize_cache_performance' が長すぎます (42行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_optimizer.py:240
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'start_optimization' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_optimizer.py:268
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'stop_optimization' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_optimizer.py:631
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'get_resource' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_optimizer.py:667
- **重要度**: acceptable
- **タイプ**: missing_type_hint
- **AI コンポーネント**: kiro
- **問題**: 関数 'return_resource' の引数 'resource' に型ヒントがありません
- **提案**: 型ヒントを追加してください

### performance_optimizer.py:667
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'return_resource' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### performance_optimizer.py:697
- **重要度**: acceptable
- **タイプ**: missing_type_hint
- **AI コンポーネント**: kiro
- **問題**: 関数 'submit_async_task' の引数 'coro' に型ヒントがありません
- **提案**: 型ヒントを追加してください

### performance_optimizer.py:809
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'cleanup' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:51
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '__init__' が長すぎます (57行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### state_manager.py:339
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_notify_change_listeners' が長すぎます (41行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### state_manager.py:482
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'save_state' が長すぎます (51行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### state_manager.py:535
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_load_state' が長すぎます (42行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### state_manager.py:289
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'add_change_listener' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:302
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'remove_change_listener' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:315
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'add_global_listener' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:327
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'remove_global_listener' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:738
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'clear_history' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:745
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'reset_state' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:753
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'shutdown' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### state_manager.py:1
- **重要度**: acceptable
- **タイプ**: insufficient_ai_integration
- **AI コンポーネント**: kiro
- **問題**: 統合ファイルでAI言及が不足しています
- **提案**: 複数のAIコンポーネントとの統合を明確にしてください

### main_window.py:103
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_initialize_ui' が長すぎます (31行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### main_window.py:136
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_create_menu_bar' が長すぎます (41行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### main_window.py:616
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 'closeEvent' が長すぎます (36行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### ui_integration_controller.py:135
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_setup_ui_connections' が長すぎます (34行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### ui_integration_controller.py:218
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_load_folder_async' が長すぎます (42行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### unified_cache.py:106
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'put' が長すぎます (43行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### unified_cache.py:330
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'get' が長すぎます (42行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### unified_cache.py:374
- **重要度**: acceptable
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'put' が長すぎます (42行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### unified_cache.py:40
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'update_hit_rate' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### unified_cache.py:171
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'clear' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### unified_cache.py:455
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'clear' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### unified_cache.py:684
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'update_cache_config' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### unified_cache.py:707
- **重要度**: acceptable
- **タイプ**: missing_return_type
- **AI コンポーネント**: kiro
- **問題**: 関数 'shutdown' に戻り値の型ヒントがありません
- **提案**: 戻り値の型ヒントを追加してください

### config_migration.py:561
- **重要度**: critical
- **タイプ**: syntax_error
- **AI コンポーネント**: cursor
- **問題**: 構文エラー: unexpected indent
- **提案**: 構文エラーを修正してください

### data_migration.py:25
- **重要度**: critical
- **タイプ**: syntax_error
- **AI コンポーネント**: cursor
- **問題**: 構文エラー: invalid syntax
- **提案**: 構文エラーを修正してください

### logging.py:148
- **重要度**: critical
- **タイプ**: syntax_error
- **AI コンポーネント**: cursor
- **問題**: 構文エラー: expected ':'
- **提案**: 構文エラーを修正してください

### folder_navigator.py:706
- **重要度**: critical
- **タイプ**: syntax_error
- **AI コンポーネント**: cursor
- **問題**: 構文エラー: unterminated triple-quoted string literal (detected at line 728)
- **提案**: 構文エラーを修正してください

### theme_manager.py:705
- **重要度**: critical
- **タイプ**: syntax_error
- **AI コンポーネント**: cursor
- **問題**: 構文エラー: unexpected indent
- **提案**: 構文エラーを修正してください

### thumbnail_grid.py:178
- **重要度**: critical
- **タイプ**: syntax_error
- **AI コンポーネント**: cursor
- **問題**: 構文エラー: unmatched ')'
- **提案**: 構文エラーを修正してください

### config_manager.py:133
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_load_default_config' が長すぎます (66行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### controllers.py:390
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'process_image' が長すぎます (90行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### controllers.py:685
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### data_validation.py:138
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'validate_image_metadata' が長すぎます (86行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### data_validation.py:226
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'validate_theme_configuration' が長すぎます (61行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### doc_templates.py:34
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_load_default_templates' が長すぎます (142行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### doc_templates.py:308
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### doc_templates.py:309
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### documentation_system.py:392
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'generate_troubleshooting_guide' が長すぎます (122行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### documentation_system.py:563
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_generate_contribution_report' が長すぎます (64行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### documentation_system.py:476
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### documentation_system.py:481
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### documentation_system.py:535
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### documentation_system.py:561
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### documentation_system.py:669
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### documentation_system.py:686
- **重要度**: poor
- **タイプ**: improper_logging
- **AI コンポーネント**: kiro
- **問題**: print文の代わりにloggingを使用してください
- **提案**: logging.info() または適切なログレベルを使用してください

### error_handling.py:155
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_create_error_context' が長すぎます (50行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### image_processor.py:96
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: copilot
- **問題**: 関数 'load_image' が長すぎます (83行, 推奨: 50行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### image_processor.py:284
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: copilot
- **問題**: 関数 'extract_exif' が長すぎます (78行, 推奨: 50行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### image_processor.py:685
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: copilot
- **問題**: 関数 '_create_image_metadata' が長すぎます (81行, 推奨: 50行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_monitor.py:68
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '__init__' が長すぎます (66行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_optimizer.py:73
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '__init__' が長すぎます (68行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### performance_optimizer.py:143
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '_initialize_strategies' が長すぎます (95行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### state_manager.py:178
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 'set_state_value' が長すぎます (67行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### main_window.py:50
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '__init__' が長すぎます (51行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### ui_integration_controller.py:67
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '__init__' が長すぎます (66行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### ui_integration_controller.py:401
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: cursor
- **問題**: 関数 '_prepare_map_async' が長すぎます (52行, 推奨: 30行以下)
- **提案**: 関数を小さな関数に分割することを検討してください

### unified_cache.py:235
- **重要度**: poor
- **タイプ**: function_length
- **AI コンポーネント**: kiro
- **問題**: 関数 '__init__' が長すぎます (61行, 推奨: 40行以下)
- **提案**: 関数を小さな関数に分割することを検討してください
