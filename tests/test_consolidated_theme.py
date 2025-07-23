#!/usr/bin/env python3
"""
統合されたテーマ設定システムのテスト
qt_theme_user_settings.json を廃止し、user_settings.json に統合
"""

import json
import os
import sys
from pathlib import Path

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

def test_theme_consolidation():
    """テーマ設定の統合テスト"""
    print("🎨 統合テーマ設定システムテスト開始")
    print("=" * 50)

    try:
        # ConfigManagerの初期化（QApplicationは不要）
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()

        print("✅ ConfigManager初期化成功")

        # ユーザー設定ディレクトリの確認
        user_config_dir = config_manager.user_config_dir
        user_settings_path = user_config_dir / "user_settings.json"
        qt_theme_path = user_config_dir / "qt_theme_user_settings.json"

        print(f"📁 ユーザー設定ディレクトリ: {user_config_dir}")
        print(f"📄 user_settings.json: {'存在' if user_settings_path.exists() else '未作成'}")
        print(f"📄 qt_theme_user_settings.json: {'存在' if qt_theme_path.exists() else '未作成'}")

        # 現在のテーマ管理設定を確認
        theme_manager_settings = config_manager.get_user_setting('ui.theme_manager', {})
        print(f"🎨 現在のテーマ管理設定:")
        for key, value in theme_manager_settings.items():
            print(f"   {key}: {value}")

        # テーマ関連メソッドのテスト
        print("\n🔍 テーマ関連メソッドテスト:")
        print(f"  current_theme: {config_manager.get_current_theme()}")
        print(f"  default_theme: {config_manager.get_default_theme()}")
        print(f"  available_themes: {len(config_manager.get_available_themes())}個")

        # テーマ変更テスト
        print("\n🔄 テーマ変更テスト:")
        original_theme = config_manager.get_current_theme()
        test_theme = "blue" if original_theme != "blue" else "green"

        print(f"  変更前: {original_theme}")
        config_manager.set_current_theme(test_theme)
        print(f"  変更後: {config_manager.get_current_theme()}")

        # 設定が正しく保存されているかチェック
        updated_settings = config_manager.get_user_setting('ui.theme_manager', {})
        print(f"  設定ファイル確認: {updated_settings.get('current_theme', 'なし')}")

        # 元のテーマに戻す
        config_manager.set_current_theme(original_theme)
        print(f"  復元完了: {config_manager.get_current_theme()}")

        print("\n✅ 統合テーマ設定システムテスト完了")
        return True

    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_file_contents():
    """設定ファイルの内容確認"""
    print("\n📋 設定ファイル内容確認")
    print("=" * 30)

    try:
        from src.core.config_manager import get_config_manager
        config_manager = get_config_manager()

        user_settings_path = config_manager.user_config_dir / "user_settings.json"
        qt_theme_path = config_manager.user_config_dir / "qt_theme_user_settings.json"

        # user_settings.json の内容
        if user_settings_path.exists():
            with open(user_settings_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            print("📄 user_settings.json:")
            print(json.dumps(user_data, indent=2, ensure_ascii=False))
        else:
            print("📄 user_settings.json: 存在しません")

        # qt_theme_user_settings.json の内容
        if qt_theme_path.exists():
            with open(qt_theme_path, 'r', encoding='utf-8') as f:
                qt_data = json.load(f)
            print("\n📄 qt_theme_user_settings.json:")
            print(json.dumps(qt_data, indent=2, ensure_ascii=False))
        else:
            print("\n📄 qt_theme_user_settings.json: 存在しません")

    except Exception as e:
        print(f"❌ ファイル内容確認中にエラー: {e}")

def main():
    """メイン実行"""
    success = test_theme_consolidation()
    check_file_contents()

    if success:
        print("\n🎉 すべてのテストに成功！")
        print("💡 qt_theme_user_settings.json の廃止準備完了")
    else:
        print("\n⚠️  テストに失敗。修正が必要です。")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
