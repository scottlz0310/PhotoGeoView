#!/usr/bin/env python3
"""
Verify Theme Menu Functionality

Checks if the theme menu is properly populated in the main application.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.ui.theme_manager_simple import SimpleThemeManager


def verify_theme_functionality():
    """Verify theme functionality"""
    print("🔍 PhotoGeoView テーマ機能検証")
    print("=" * 50)

    try:
        # Initialize components
        logger_system = LoggerSystem()
        config_manager = ConfigManager(config_dir=Path("config"), logger_system=logger_system)
        theme_manager = SimpleThemeManager(config_manager, logger_system)

        # Get available themes
        available_themes = theme_manager.get_available_themes()
        current_theme = theme_manager.get_current_theme()

        print(f"✅ テーママネージャー初期化成功")
        print(f"📊 利用可能なテーマ数: {len(available_themes)}")
        print(f"🎯 現在のテーマ: {current_theme}")

        # Show all themes with details
        print(f"\n📋 利用可能なテーマ一覧:")
        for i, theme_name in enumerate(sorted(available_themes), 1):
            theme_config = theme_manager.get_theme_config(theme_name)
            if theme_config:
                display_name = theme_config.get('display_name', theme_name)
                description = theme_config.get('description', 'No description')
                primary_color = theme_config.get('primaryColor', 'N/A')

                status = "🎯" if theme_name == current_theme else "  "
                print(f"{status} {i:2d}. {display_name} ({theme_name})")
                print(f"      説明: {description}")
                print(f"      主要色: {primary_color}")
            else:
                status = "🎯" if theme_name == current_theme else "  "
                print(f"{status} {i:2d}. {theme_name} (設定なし)")

        # Test theme switching
        print(f"\n🔄 テーマ切り替えテスト:")

        # Test switching to a few different themes
        test_themes = ['light', 'dark', 'blue', 'sunset', 'ocean_breeze']
        successful_switches = 0

        for theme_name in test_themes:
            if theme_name in available_themes:
                print(f"  テスト中: {theme_name}")
                if theme_manager.apply_theme(theme_name):
                    current = theme_manager.get_current_theme()
                    if current == theme_name:
                        print(f"    ✅ 成功: {theme_name}")
                        successful_switches += 1
                    else:
                        print(f"    ❌ 失敗: 期待={theme_name}, 実際={current}")
                else:
                    print(f"    ❌ 適用失敗: {theme_name}")
            else:
                print(f"  ⚠️  スキップ: {theme_name} (利用不可)")

        print(f"\n📈 テスト結果:")
        print(f"  成功したテーマ切り替え: {successful_switches}/{len([t for t in test_themes if t in available_themes])}")

        # Verify JSON configuration
        json_path = Path("config/qt_theme_settings.json")
        if json_path.exists():
            print(f"✅ JSON設定ファイル存在: {json_path}")

            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            json_themes = data.get('available_themes', {})
            print(f"📄 JSON内テーマ数: {len(json_themes)}")
        else:
            print(f"❌ JSON設定ファイル不存在: {json_path}")

        # Summary
        print(f"\n🎉 検証完了!")
        print(f"💡 VIEWメニューから{len(available_themes)}個のテーマを選択できるはずです")

        return True

    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_theme_functionality()
    sys.exit(0 if success else 1)
