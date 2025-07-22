"""
アクセシビリティ改善済みテーマ設定生成ツール
"""

import sys
import json
from pathlib import Path
from typing import Dict

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.theme_accessibility import ColorAccessibilityAnalyzer


def generate_improved_theme_colors() -> Dict:
    """アクセシビリティ改善済みの色設定を生成"""

    improved_themes = {
        # Limeテーマの改善（より暗いテキスト色を使用）
        "lime": {
            "name": "Lime (Improved)",
            "category": "colorful",
            "description": "明るい黄緑テーマ（アクセシビリティ改善版）",
            "colors": {
                "background": "#f9fbe7",
                "foreground": "#2e4832",  # より暗い緑（元: #4a4a4a）
                "menu_background": "#e8f5e8",
                "button_background": "#c8e6c9",
                "button_hover": "#a5d6a7",
                "border": "#81c784",
                "input_background": "#f1f8e9",  # 少し暗め（元: #f9fbe7）
                "selection": "#8bc34a",
                "hover": "#aed581"
            }
        },

        # Orangeテーマの改善（より暗いテキスト色、背景調整）
        "orange": {
            "name": "Orange (Improved)",
            "category": "colorful",
            "description": "オレンジテーマ（アクセシビリティ改善版）",
            "colors": {
                "background": "#fff3e0",
                "foreground": "#3d2914",  # 濃い茶色（元: #5d4037）
                "menu_background": "#fbe9a7",
                "button_background": "#ffb74d",
                "button_hover": "#ffa726",
                "border": "#ff9800",
                "input_background": "#ffebcd",  # より暗い背景（元: #fff3e0）
                "selection": "#ff9800",
                "hover": "#ffb74d"
            }
        },

        # Yellowテーマの改善（より暗いテキスト、背景調整）
        "yellow": {
            "name": "Yellow (Improved)",
            "category": "colorful",
            "description": "黄色テーマ（アクセシビリティ改善版）",
            "colors": {
                "background": "#fffde7",
                "foreground": "#3d3b00",  # 濃い黄土色（元: #5d4037）
                "menu_background": "#fff59d",
                "button_background": "#ffeb3b",
                "button_hover": "#ffcc02",
                "border": "#ffc107",
                "input_background": "#fffacd",  # より暗い背景（元: #fffde7）
                "selection": "#ffeb3b",
                "hover": "#fff176"
            }
        },

        # Amberテーマの改善（より暗いテキスト、背景調整）
        "amber": {
            "name": "Amber (Improved)",
            "category": "colorful",
            "description": "アンバーテーマ（アクセシビリティ改善版）",
            "colors": {
                "background": "#fff8e1",
                "foreground": "#3d2f00",  # 濃い琥珀色（元: #5d4037）
                "menu_background": "#ffecb3",
                "button_background": "#ffc107",
                "button_hover": "#ffb300",
                "border": "#ff9800",
                "input_background": "#fff4c4",  # より暗い背景（元: #fff8e1）
                "selection": "#ffc107",
                "hover": "#ffca28"
            }
        }
    }

    return improved_themes


def validate_improvements():
    """改善案をアクセシビリティ分析で検証"""
    analyzer = ColorAccessibilityAnalyzer()
    improved_themes = generate_improved_theme_colors()

    print("=" * 70)
    print("テーマアクセシビリティ改善案の検証結果")
    print("=" * 70)

    for theme_name, theme_data in improved_themes.items():
        analysis = analyzer.analyze_theme_accessibility(theme_data)
        score = analysis.get("accessibility_score", 0)
        main_contrast = analysis.get("main_contrast", 0)
        zebra_min = analysis.get("zebra_analysis", {}).get("min_contrast", 0)

        # スコア評価アイコン
        if score >= 90:
            icon = "🟢"
        elif score >= 80:
            icon = "🟡"
        else:
            icon = "🔴"

        print(f"\n{icon} {theme_name.upper()}テーマ改善案:")
        print(f"   スコア: {score}点 (改善前: 45-74点)")
        print(f"   メインコントラスト: {main_contrast:.2f}")
        print(f"   ゼブラ最小コントラスト: {zebra_min:.2f}")
        print(f"   WCAG AA準拠: {'✅' if analysis.get('wcag_compliance', {}).get('aa_normal') else '❌'}")
        print(f"   ゼブラ視認性: {'✅' if analysis.get('wcag_compliance', {}).get('zebra_readable') else '❌'}")

        # 色情報
        colors = theme_data.get("colors", {})
        print(f"   前景色: {colors.get('foreground')} (元テキスト色から変更)")
        print(f"   背景色: {colors.get('background')} → 入力背景: {colors.get('input_background')}")

        # 改善提案
        recommendations = analysis.get("recommendations", [])
        if "アクセシビリティは良好です" in recommendations:
            print(f"   ✅ アクセシビリティ改善完了！")
        else:
            print(f"   ⚠️  追加改善案: {'; '.join(recommendations)}")


def generate_theme_config_patch():
    """改善済みテーマ設定のJSONパッチを生成"""
    improved_themes = generate_improved_theme_colors()

    # 既存の設定ファイルを読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"既存設定読み込みエラー: {e}")
        return

    # テーマを更新
    theme_styles = config.get("theme_styles", {})

    for theme_name, improved_theme in improved_themes.items():
        if theme_name in theme_styles:
            # 既存テーマを更新
            theme_styles[theme_name].update(improved_theme)
            print(f"✅ {theme_name}テーマを改善版に更新")
        else:
            print(f"⚠️  {theme_name}テーマが見つかりません")

    # 改善済み設定ファイルを保存
    improved_config_path = project_root / "config" / "theme_styles_improved.json"

    with open(improved_config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n🎯 改善済み設定ファイル保存: {improved_config_path}")
    print("   元ファイルのバックアップと置換は手動で行ってください。")


if __name__ == "__main__":
    print("🔍 テーマアクセシビリティ改善案の生成と検証\n")

    # 改善案の検証
    validate_improvements()

    print("\n" + "=" * 70)

    # 改善済み設定ファイル生成
    generate_theme_config_patch()
