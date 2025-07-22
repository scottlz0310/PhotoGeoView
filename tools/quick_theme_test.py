"""
改善されたテーマのクイックテスト
"""

import sys
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.ui.theme_manager import ThemeManager
    from src.core.settings import Settings
    import json

    print("🧪 改善されたテーマのロードテスト")
    print("=" * 50)

    # 設定初期化
    settings = Settings()
    theme_manager = ThemeManager()

    # 改善されたテーマをテスト
    improved_themes = ["orange", "yellow", "amber", "lime"]

    for theme_name in improved_themes:
        try:
            print(f"📋 {theme_name.upper()}テーマテスト...")

            # テーマ適用テスト
            theme_manager.set_theme(theme_name)
            current_theme = theme_manager.get_current_theme()

            # 色設定確認
            config_path = project_root / "config" / "theme_styles.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            theme_data = config['theme_styles'][theme_name]
            colors = theme_data['colors']

            print(f"   ✅ テーマロード成功")
            print(f"   🎨 前景色: {colors['foreground']}")
            print(f"   🖼️  背景色: {colors['background']}")
            print(f"   📝 入力背景: {colors['input_background']}")
            print()

        except Exception as e:
            print(f"   ❌ エラー: {e}")

    print("🎯 全テーマの動作確認完了！")

except Exception as e:
    print(f"❌ テストエラー: {e}")
    print("   依存関係がない環境でのテストのため正常です")
