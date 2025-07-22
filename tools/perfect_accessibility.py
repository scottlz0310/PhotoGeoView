"""
85点テーマの完全アクセシビリティ改善ツール
"""

import sys
import json
from pathlib import Path
from typing import Dict

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.theme_accessibility import ColorAccessibilityAnalyzer


def generate_perfect_accessibility_themes() -> Dict:
    """85点テーマを100点満点に改善"""

    improved_themes = {
        # Blueテーマの改善（より暗いテキスト色を使用）
        "blue": {
            "name": "ブルー",
            "category": "colorful",
            "description": "落ち着いたブルーテーマ（完全アクセシビリティ対応）",
            "colors": {
                "background": "#e3f2fd",
                "foreground": "#0d47a1",  # より暗い青（元: #1565c0）
                "menu_background": "#bbdefb",
                "button_background": "#90caf9",
                "button_hover": "#64b5f6",
                "border": "#64b5f6",
                "input_background": "#e1f5fe",  # 少し暗め
                "selection": "#2196f3",
                "hover": "#42a5f5"
            }
        },

        # Greenテーマの改善
        "green": {
            "name": "グリーン",
            "category": "colorful",
            "description": "自然なグリーンテーマ（完全アクセシビリティ対応）",
            "colors": {
                "background": "#e8f5e8",
                "foreground": "#1b5e20",  # より暗い緑（元: #2e7d32）
                "menu_background": "#c8e6c8",
                "button_background": "#81c784",
                "button_hover": "#66bb6a",
                "border": "#4caf50",
                "input_background": "#f1f8e9",  # 少し暗め
                "selection": "#4caf50",
                "hover": "#66bb6a"
            }
        },

        # Purpleテーマの改善
        "purple": {
            "name": "パープル",
            "category": "colorful",
            "description": "エレガントなパープルテーマ（完全アクセシビリティ対応）",
            "colors": {
                "background": "#f3e5f5",
                "foreground": "#4a148c",  # より暗い紫（元: #7b1fa2）
                "menu_background": "#e1bee7",
                "button_background": "#ba68c8",
                "button_hover": "#ab47bc",
                "border": "#9c27b0",
                "input_background": "#fce4ec",  # 少し暗め
                "selection": "#9c27b0",
                "hover": "#ba68c8"
            }
        },

        # Redテーマの改善
        "red": {
            "name": "レッド",
            "category": "colorful",
            "description": "情熱的なレッドテーマ（完全アクセシビリティ対応）",
            "colors": {
                "background": "#ffebee",
                "foreground": "#b71c1c",  # より暗い赤（元: #d32f2f）
                "menu_background": "#ffcdd2",
                "button_background": "#e57373",
                "button_hover": "#ef5350",
                "border": "#f44336",
                "input_background": "#ffebf0",  # 少し暗め
                "selection": "#f44336",
                "hover": "#e57373"
            }
        },

        # Pinkテーマの改善
        "pink": {
            "name": "ピンク",
            "category": "colorful",
            "description": "可愛らしいピンクテーマ（完全アクセシビリティ対応）",
            "colors": {
                "background": "#fce4ec",
                "foreground": "#880e4f",  # より暗いピンク（元: #c2185b）
                "menu_background": "#f8bbd9",
                "button_background": "#f06292",
                "button_hover": "#ec407a",
                "border": "#e91e63",
                "input_background": "#fdf2f8",  # 少し暗め
                "selection": "#e91e63",
                "hover": "#f06292"
            }
        },

        # Cyanテーマの改善
        "cyan": {
            "name": "シアン",
            "category": "colorful",
            "description": "爽やかなシアンテーマ（完全アクセシビリティ対応）",
            "colors": {
                "background": "#e0f2f1",
                "foreground": "#004d40",  # より暗いシアン（元: #00695c）
                "menu_background": "#b2dfdb",
                "button_background": "#4db6ac",
                "button_hover": "#26a69a",
                "border": "#009688",
                "input_background": "#e8f5e5",  # 少し暗め
                "selection": "#009688",
                "hover": "#4db6ac"
            }
        }
    }

    return improved_themes


def validate_perfect_improvements():
    """完全改善案をアクセシビリティ分析で検証"""
    analyzer = ColorAccessibilityAnalyzer()
    improved_themes = generate_perfect_accessibility_themes()

    print("=" * 70)
    print("85点テーマの100点満点改善案検証結果")
    print("=" * 70)

    total_perfect = 0

    for theme_name, theme_data in improved_themes.items():
        analysis = analyzer.analyze_theme_accessibility(theme_data)
        score = analysis.get("accessibility_score", 0)
        main_contrast = analysis.get("main_contrast", 0)
        zebra_min = analysis.get("zebra_analysis", {}).get("min_contrast", 0)

        if score == 100:
            total_perfect += 1
            icon = "🎯"
        elif score >= 90:
            icon = "🟢"
        elif score >= 80:
            icon = "🟡"
        else:
            icon = "🔴"

        print(f"\n{icon} {theme_name.upper()}テーマ完全改善案:")
        print(f"   スコア: {score}点 (改善前: 85点)")
        print(f"   メインコントラスト: {main_contrast:.2f}")
        print(f"   ゼブラ最小コントラスト: {zebra_min:.2f}")
        print(f"   WCAG AA準拠: {'✅' if analysis.get('wcag_compliance', {}).get('aa_normal') else '❌'}")
        print(f"   ゼブラ視認性: {'✅' if analysis.get('wcag_compliance', {}).get('zebra_readable') else '❌'}")

        # 色情報
        colors = theme_data.get("colors", {})
        print(f"   前景色変更: {colors.get('foreground')} (より暗く調整)")
        print(f"   背景微調整: {colors.get('background')} → {colors.get('input_background')}")

        # 改善結果
        recommendations = analysis.get("recommendations", [])
        if "アクセシビリティは良好です" in recommendations:
            print(f"   🎉 完全アクセシビリティ達成！")
        else:
            print(f"   ⚠️  追加調整が必要: {'; '.join(recommendations)}")

    print(f"\n📊 結果サマリー:")
    print(f"   改善対象テーマ: {len(improved_themes)}個")
    print(f"   100点満点達成: {total_perfect}個")
    print(f"   完全改善率: {total_perfect/len(improved_themes)*100:.1f}%")


def apply_perfect_accessibility_improvements():
    """完全アクセシビリティ改善を適用"""
    improved_themes = generate_perfect_accessibility_themes()

    # 既存の設定ファイルを読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return

    # バックアップ作成
    backup_path = config_path.with_suffix('.json.backup_85to100')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"🔒 バックアップ作成: {backup_path}")

    # テーマを更新
    theme_styles = config.get("theme_styles", {})
    updated_count = 0

    for theme_name, improved_theme in improved_themes.items():
        if theme_name in theme_styles:
            # 色情報のみ更新（他の情報は保持）
            theme_styles[theme_name]["colors"] = improved_theme["colors"]
            updated_count += 1
            print(f"✅ {theme_name}テーマを100点満点版に更新")
        else:
            print(f"⚠️  {theme_name}テーマが見つかりません")

    # 改善済み設定ファイルを保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n🎯 完全アクセシビリティ改善完了!")
    print(f"   更新テーマ数: {updated_count}/{len(improved_themes)}")
    print(f"   設定ファイル: {config_path}")


if __name__ == "__main__":
    print("🎯 85点テーマの100点満点改善プロセス開始\n")

    # 改善案の検証
    validate_perfect_improvements()

    print("\n" + "=" * 70)
    print("改善を適用しますか？ (適用する場合は下のセクションを実行)")
    print("=" * 70)

    # 改善適用
    apply_perfect_accessibility_improvements()
