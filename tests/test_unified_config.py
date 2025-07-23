#!/usr/bin/env python3
"""
統一設定システムのテストスクリプト
"""

import sys
import os
sys.path.insert(0, os.getcwd())

def test_config_manager():
    print('=== ConfigManager テスト ===')

    try:
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()
        print('✅ ConfigManager 初期化成功')

        # 基本設定テスト
        app_name = config_manager.get_app_config("app.name")
        print(f'アプリ名: {app_name}')

        cache_size = config_manager.get_app_config("cache.thumbnail_max_size_mb")
        print(f'キャッシュサイズ: {cache_size}MB')

        # テーマ設定テスト
        theme_engine = config_manager.get_theme_engine()
        print(f'テーマエンジン: {theme_engine}')

        default_theme = config_manager.get_default_theme()
        print(f'デフォルトテーマ: {default_theme}')

        current_theme = config_manager.get_current_theme()
        print(f'現在のテーマ: {current_theme}')

        available_themes = config_manager.get_available_themes()
        print(f'利用可能テーマ数: {len(available_themes)}')

        # パス設定テスト
        theme_paths = config_manager.get_theme_config_paths()
        print('テーマファイルパス:')
        for key, path in theme_paths.items():
            print(f'  {key}: {path}')

        print('✅ ConfigManager テスト完了')
        return True

    except Exception as e:
        print(f'❌ ConfigManager エラー: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_settings():
    print('\n=== Settings 互換レイヤーテスト ===')

    try:
        from src.core.settings import get_settings
        settings = get_settings()
        print('✅ Settings 初期化成功')

        # 基本アクセステスト
        app_name = settings.get("app.name")
        print(f'アプリ名 (get): {app_name}')

        # data プロパティテスト
        data_app_name = settings.data["app"]["name"]
        print(f'アプリ名 (data): {data_app_name}')

        # テーマ設定テスト
        ui_theme = settings.get("ui.theme_manager.current_theme")
        print(f'現在のテーマ (settings): {ui_theme}')

        print('✅ Settings 互換レイヤーテスト完了')
        return True

    except Exception as e:
        print(f'❌ Settings エラー: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_qt_theme_adapter():
    print('\n=== QtThemeManagerAdapter テスト ===')

    try:
        # QApplication が必要なので、ヘッドレステスト
        print('QtThemeManagerAdapter の基本import テスト...')

        # QtThemeManagerAdapter は QApplication が必要なため、モジュールレベルテストのみ
        from src.ui import qt_theme_manager_adapter
        print('✅ QtThemeManagerAdapter import 成功')

        return True

    except Exception as e:
        print(f'❌ QtThemeManagerAdapter エラー: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("統一設定システム総合テスト開始\n")

    results = []
    results.append(test_config_manager())
    results.append(test_settings())
    results.append(test_qt_theme_adapter())

    print(f"\n=== テスト結果サマリー ===")
    print(f"成功: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print("❌ 一部のテストが失敗しました")
        sys.exit(1)
