#!/usr/bin/env python3
"""
Theme Management Demo

Demonstrates the enhanced theme management capabilities.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.ui.theme_manager import IntegratedThemeManager


def create_sample_themes():
    """Create sample custom themes"""

    themes = {
        "sunset": {
            "name": "sunset",
            "display_name": "サンセット",
            "description": "夕焼けをイメージした暖かいテーマ",
            "primaryColor": "#ff6b35",
            "accentColor": "#f7931e",
            "backgroundColor": "#2c1810",
            "textColor": "#fff8dc",
            "button": {
                "background": "#ff6b35",
                "text": "#ffffff",
                "hover": "#e55a2b",
                "pressed": "#cc4f24",
                "border": "#e55a2b",
            },
            "panel": {
                "background": "#2c1810",
                "border": "#4a2f1f",
                "header": {
                    "background": "#3d2418",
                    "text": "#fff8dc",
                    "border": "#4a2f1f",
                },
            },
            "text": {"primary": "#fff8dc", "secondary": "#f4e4bc", "muted": "#d4c4a8"},
        },
        "ocean_breeze": {
            "name": "ocean_breeze",
            "display_name": "オーシャンブリーズ",
            "description": "海の風をイメージした爽やかなテーマ",
            "primaryColor": "#006994",
            "accentColor": "#00a8cc",
            "backgroundColor": "#f0f8ff",
            "textColor": "#003d5c",
            "button": {
                "background": "#00a8cc",
                "text": "#ffffff",
                "hover": "#0091b3",
                "pressed": "#007a99",
                "border": "#0091b3",
            },
            "panel": {
                "background": "#f0f8ff",
                "border": "#b3d9f2",
                "header": {
                    "background": "#e6f3ff",
                    "text": "#003d5c",
                    "border": "#b3d9f2",
                },
            },
            "text": {"primary": "#003d5c", "secondary": "#005580", "muted": "#4d7ea8"},
        },
        "forest_night": {
            "name": "forest_night",
            "display_name": "フォレストナイト",
            "description": "夜の森をイメージした深いグリーンテーマ",
            "primaryColor": "#0d2818",
            "accentColor": "#2d5a3d",
            "backgroundColor": "#0d2818",
            "textColor": "#c8e6c9",
            "button": {
                "background": "#2d5a3d",
                "text": "#ffffff",
                "hover": "#3d6b4d",
                "pressed": "#1d4a2d",
                "border": "#3d6b4d",
            },
            "panel": {
                "background": "#0d2818",
                "border": "#1d3d28",
                "header": {
                    "background": "#1d3d28",
                    "text": "#c8e6c9",
                    "border": "#1d3d28",
                },
            },
            "text": {"primary": "#c8e6c9", "secondary": "#a5d6a7", "muted": "#81c784"},
        },
    }

    return themes


def demo_theme_management():
    """Demonstrate theme management features"""
    print("🎨 PhotoGeoView テーマ管理デモ")
    print("=" * 50)

    # Initialize components
    logger_system = LoggerSystem()
    config_manager = ConfigManager(
        config_dir=Path("config"), logger_system=logger_system
    )
    from src.integration.state_manager import StateManager

    state_manager = StateManager(config_manager, logger_system)
    theme_manager = IntegratedThemeManager(config_manager, state_manager, logger_system)

    print("✅ テーママネージャー初期化完了")
    print(f"📋 現在利用可能なテーマ数: {len(theme_manager.get_available_themes())}")

    # Create sample themes
    sample_themes = create_sample_themes()

    print("\n🎨 サンプルテーマを追加中...")
    added_themes = []

    for theme_name, theme_config in sample_themes.items():
        if theme_manager.add_custom_theme(theme_name, theme_config):
            added_themes.append(theme_name)
            print(f"  ✅ {theme_config['display_name']} ({theme_name}) 追加成功")
        else:
            print(f"  ⚠️  {theme_config['display_name']} ({theme_name}) 既に存在")

    print("\n📊 テーマ統計:")
    all_themes = theme_manager.get_available_themes()
    print(f"  総テーマ数: {len(all_themes)}")

    # Show theme categories
    builtin_count = 0
    custom_count = 0

    for theme_name in all_themes:
        theme_config = theme_manager.get_theme_config(theme_name)
        if theme_config and theme_name in sample_themes:
            custom_count += 1
        else:
            builtin_count += 1

    print(f"  内蔵テーマ: {builtin_count}")
    print(f"  カスタムテーマ: {custom_count}")

    # Demonstrate theme switching
    print("\n🔄 テーマ切り替えデモ:")
    current_theme = theme_manager.get_current_theme()
    print(f"  現在のテーマ: {current_theme}")

    # Try switching to custom themes
    for theme_name in added_themes[:2]:  # Try first 2 added themes
        if theme_manager.apply_theme(theme_name):
            theme_config = theme_manager.get_theme_config(theme_name)
            print(f"  ✅ {theme_config['display_name']} に切り替え成功")
        else:
            print(f"  ❌ {theme_name} への切り替え失敗")

    # Export a theme
    if added_themes:
        export_theme = added_themes[0]
        export_path = f"exported_{export_theme}.json"
        print(f"\n📤 テーマエクスポート: {export_theme}")

        if theme_manager.export_theme(export_theme, export_path):
            print(f"  ✅ {export_path} にエクスポート成功")

            # Show file size
            try:
                file_size = Path(export_path).stat().st_size
                print(f"  📁 ファイルサイズ: {file_size} bytes")
            except:
                pass
        else:
            print("  ❌ エクスポート失敗")

    # Theme cycling demo
    print("\n🔄 テーマサイクリングデモ:")
    original_theme = theme_manager.get_current_theme()

    for i in range(3):
        theme_manager.cycle_theme()
        new_theme = theme_manager.get_current_theme()
        theme_config = theme_manager.get_theme_config(new_theme)
        display_name = (
            theme_config.get("display_name", new_theme) if theme_config else new_theme
        )
        print(f"  {i + 1}. {display_name} ({new_theme})")

    # Restore original theme
    theme_manager.apply_theme(original_theme)
    print(f"  🔙 元のテーマに復元: {original_theme}")

    print("\n🎉 テーマ管理デモ完了！")
    print("💡 config/qt_theme_settings.json を編集してテーマをカスタマイズできます")

    # Cleanup exported files
    try:
        for theme_name in added_themes:
            export_file = Path(f"exported_{theme_name}.json")
            if export_file.exists():
                export_file.unlink()
    except:
        pass


if __name__ == "__main__":
    try:
        demo_theme_management()
    except KeyboardInterrupt:
        print("\n\n⏹️  デモを中断しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
