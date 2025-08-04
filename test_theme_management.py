#!/usr/bin/env python3
"""
Theme Management Test Script

Tests the enhanced SimpleThemeManager with JSON-based theme configuration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.ui.theme_manager_simple import SimpleThemeManager


def test_theme_management():
    """Test theme management functionality"""
    print("🎨 PhotoGeoView テーマ管理システムテスト")
    print("=" * 50)

    # Initialize components
    logger_system = LoggerSystem()
    config_manager = ConfigManager(config_dir=Path("config"), logger_system=logger_system)

    try:
        # Initialize theme manager
        theme_manager = SimpleThemeManager(config_manager, logger_system)

        print(f"✅ テーママネージャー初期化成功")

        # Test 1: List available themes
        available_themes = theme_manager.get_available_themes()
        print(f"📋 利用可能なテーマ数: {len(available_themes)}")
        print(f"   テーマ一覧: {', '.join(available_themes[:10])}{'...' if len(available_themes) > 10 else ''}")

        # Test 2: Get current theme
        current_theme = theme_manager.get_current_theme()
        print(f"🎯 現在のテーマ: {current_theme}")

        # Test 3: Get theme configuration
        if current_theme in available_themes:
            theme_config = theme_manager.get_theme_config(current_theme)
            if theme_config:
                print(f"⚙️  テーマ設定取得成功: {theme_config.get('display_name', current_theme)}")
                print(f"   説明: {theme_config.get('description', 'N/A')}")
                print(f"   主要色: {theme_config.get('primaryColor', 'N/A')}")

        # Test 4: Create a custom theme
        custom_theme_config = {
            "name": "test_custom",
            "display_name": "テストカスタム",
            "description": "テスト用のカスタムテーマ",
            "primaryColor": "#ff6b6b",
            "accentColor": "#4ecdc4",
            "backgroundColor": "#2c3e50",
            "textColor": "#ecf0f1",
            "button": {
                "background": "#e74c3c",
                "text": "#ffffff",
                "hover": "#c0392b",
                "pressed": "#a93226",
                "border": "#c0392b"
            },
            "panel": {
                "background": "#2c3e50",
                "border": "#34495e",
                "header": {
                    "background": "#34495e",
                    "text": "#ecf0f1",
                    "border": "#34495e"
                }
            },
            "text": {
                "primary": "#ecf0f1",
                "secondary": "#bdc3c7",
                "muted": "#95a5a6"
            }
        }

        print("\n🔧 カスタムテーマ追加テスト")
        if theme_manager.add_custom_theme("test_custom", custom_theme_config):
            print("✅ カスタムテーマ追加成功")

            # Verify theme was added
            updated_themes = theme_manager.get_available_themes()
            if "test_custom" in updated_themes:
                print("✅ テーマリストに追加確認")
            else:
                print("❌ テーマリストに見つからない")
        else:
            print("❌ カスタムテーマ追加失敗")

        # Test 5: Export theme
        print("\n📤 テーマエクスポートテスト")
        export_path = "exported_theme.json"
        if theme_manager.export_theme("test_custom", export_path):
            print(f"✅ テーマエクスポート成功: {export_path}")

            # Verify file exists
            if Path(export_path).exists():
                print("✅ エクスポートファイル確認")
            else:
                print("❌ エクスポートファイルが見つからない")
        else:
            print("❌ テーマエクスポート失敗")

        # Test 6: Update theme
        print("\n🔄 テーマ更新テスト")
        update_config = {
            "description": "更新されたテスト用カスタムテーマ",
            "primaryColor": "#9b59b6"
        }
        if theme_manager.update_theme("test_custom", update_config):
            print("✅ テーマ更新成功")

            # Verify update
            updated_config = theme_manager.get_theme_config("test_custom")
            if updated_config and updated_config.get("primaryColor") == "#9b59b6":
                print("✅ テーマ更新内容確認")
            else:
                print("❌ テーマ更新内容が反映されていない")
        else:
            print("❌ テーマ更新失敗")

        # Test 7: Remove custom theme
        print("\n🗑️  カスタムテーマ削除テスト")
        if theme_manager.remove_custom_theme("test_custom"):
            print("✅ カスタムテーマ削除成功")

            # Verify removal
            final_themes = theme_manager.get_available_themes()
            if "test_custom" not in final_themes:
                print("✅ テーマリストから削除確認")
            else:
                print("❌ テーマがまだリストに残っている")
        else:
            print("❌ カスタムテーマ削除失敗")

        # Test 8: Theme cycling
        print("\n🔄 テーマサイクリングテスト")
        original_theme = theme_manager.get_current_theme()
        theme_manager.cycle_theme()
        new_theme = theme_manager.get_current_theme()

        if new_theme != original_theme:
            print(f"✅ テーマサイクリング成功: {original_theme} → {new_theme}")
        else:
            print("ℹ️  テーマサイクリング: 変更なし（テーマが1つのみ）")

        print("\n🎉 テーマ管理システムテスト完了")
        return True

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        try:
            Path("exported_theme.json").unlink(missing_ok=True)
        except:
            pass


if __name__ == "__main__":
    success = test_theme_management()
    sys.exit(0 if success else 1)
