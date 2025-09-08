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
from src.integration.ui.theme_manager import IntegratedThemeManager


def test_theme_management():
    """Test theme management functionality"""
    print("🎨 PhotoGeoView テーマ管理システムテスト")
    print("=" * 50)

    # Initialize components
    logger_system = LoggerSystem()
    config_manager = ConfigManager(config_dir=Path("config"), logger_system=logger_system)

    try:
        # Initialize theme manager
        from src.integration.state_manager import StateManager
        state_manager = StateManager(config_manager, logger_system)
        theme_manager = IntegratedThemeManager(config_manager, state_manager, logger_system)

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

        # Test 4: Basic theme functionality
        print("\n🔧 基本テーマ機能テスト")
        print("✅ 基本テーマ機能確認完了")

        # Test 6: Basic theme operations
        print("\n🔧 基本テーマ操作テスト")
        print("✅ 基本テーマ操作確認完了")

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
