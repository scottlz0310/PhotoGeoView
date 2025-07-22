"""
ゼブラスタイル表示確認ツール
実際のUIでゼブラスタイルがどのように見えるかを確認
"""

import sys
import json
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_zebra_visibility():
    """各テーマのゼブラスタイルの視認性を分析"""

    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return

    print("🔍 ゼブラスタイル視認性分析")
    print("=" * 60)

    theme_styles = config.get("theme_styles", {})

    for theme_name, theme_data in theme_styles.items():
        colors = theme_data.get("colors", {})

        base_color = colors.get("input_background", "#ffffff")
        zebra_color = colors.get("zebra_alternate", base_color)
        text_color = colors.get("foreground", "#000000")

        # RGB変換
        base_rgb = hex_to_rgb(base_color)
        zebra_rgb = hex_to_rgb(zebra_color)

        # 色差計算（簡易）
        color_diff = abs(sum(base_rgb) - sum(zebra_rgb)) / 3

        # 視認性レベル判定
        if color_diff < 5:
            visibility = "❌ 見えない"
        elif color_diff < 15:
            visibility = "⚠️  見にくい"
        elif color_diff < 30:
            visibility = "🟡 普通"
        else:
            visibility = "✅ はっきり見える"

        print(f"{theme_name:12} | 基準色: {base_color} | ゼブラ色: {zebra_color} | 色差: {color_diff:3.0f} | {visibility}")


def hex_to_rgb(hex_color):
    """16進数カラーをRGBに変換"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def suggest_zebra_improvements():
    """ゼブラスタイルが見にくいテーマの改善案を提示"""

    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return

    theme_styles = config.get("theme_styles", {})
    needs_improvement = []

    print(f"\n🛠️  ゼブラスタイル改善提案:")
    print("-" * 60)

    for theme_name, theme_data in theme_styles.items():
        colors = theme_data.get("colors", {})

        base_color = colors.get("input_background", "#ffffff")
        zebra_color = colors.get("zebra_alternate", base_color)

        base_rgb = hex_to_rgb(base_color)
        zebra_rgb = hex_to_rgb(zebra_color)

        color_diff = abs(sum(base_rgb) - sum(zebra_rgb)) / 3

        if color_diff < 15:  # 見にくい場合
            needs_improvement.append(theme_name)

            # 改善案生成
            base_luminance = sum(base_rgb) / 3

            if base_luminance > 128:  # 明るい背景
                # より暗いゼブラ色を提案
                factor = 0.9
            else:  # 暗い背景
                # より明るいゼブラ色を提案
                factor = 1.1

            improved_rgb = tuple(min(255, max(0, int(c * factor))) for c in base_rgb)
            improved_color = f"#{improved_rgb[0]:02x}{improved_rgb[1]:02x}{improved_rgb[2]:02x}"

            print(f"   {theme_name:12}: {zebra_color} → {improved_color} (色差改善)")

    if not needs_improvement:
        print("   全テーマのゼブラスタイルが適切に設定されています！")
    else:
        print(f"\n   改善が必要なテーマ: {len(needs_improvement)}個")


if __name__ == "__main__":
    analyze_zebra_visibility()
    suggest_zebra_improvements()
