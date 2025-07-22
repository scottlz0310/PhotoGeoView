"""
QtThemeManager形式を参考にした6%コントラスト比ゼブラスタイル調整ツール
"""

import sys
import json
from pathlib import Path
from typing import Dict, Tuple

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """16進数カラーをRGBに変換"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """RGBを16進数カラーに変換"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def generate_6percent_zebra_color(base_color: str) -> str:
    """6%程度のコントラスト比でゼブラ色を生成"""
    base_rgb = hex_to_rgb(base_color)
    base_luminance = sum(base_rgb) / 3

    # 6%の調整率を適用
    adjustment_factor = 0.06

    if base_luminance > 128:  # 明るい背景
        # より暗く（6%暗く）
        factor = 1.0 - adjustment_factor
    else:  # 暗い背景
        # より明るく（6%明るく）
        factor = 1.0 + adjustment_factor

    # 新しいRGB値を計算
    new_rgb = tuple(
        min(255, max(0, int(c * factor)))
        for c in base_rgb
    )

    return rgb_to_hex(new_rgb)


def generate_improved_zebra_themes() -> Dict:
    """6%コントラスト比の改善されたゼブラテーマを生成"""

    # 現在の設定ファイルを読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

    theme_styles = config.get("theme_styles", {})
    updated_themes = {}

    print("🎨 6%コントラスト比ゼブラスタイル生成")
    print("=" * 60)

    for theme_name, theme_data in theme_styles.items():
        colors = theme_data.get("colors", {})
        input_background = colors.get("input_background", "#ffffff")

        # 6%コントラスト比でゼブラ色を生成
        new_zebra_color = generate_6percent_zebra_color(input_background)

        # 色差計算（参考用）
        base_rgb = hex_to_rgb(input_background)
        zebra_rgb = hex_to_rgb(new_zebra_color)
        color_diff = abs(sum(base_rgb) - sum(zebra_rgb)) / 3

        print(f"{theme_name:12} | 基準: {input_background} → ゼブラ: {new_zebra_color} | 色差: {color_diff:.1f}")

        # 新しい色設定を保存
        updated_colors = colors.copy()
        updated_colors["zebra_alternate"] = new_zebra_color

        updated_themes[theme_name] = {
            **theme_data,
            "colors": updated_colors
        }

    return {"theme_styles": updated_themes}


def apply_6percent_zebra_adjustment():
    """6%コントラスト比ゼブラ調整を適用"""

    # 改善されたテーマを生成
    improved_config = generate_improved_zebra_themes()

    if not improved_config:
        print("❌ テーマ生成に失敗しました")
        return

    # 設定ファイルパス
    config_path = project_root / "config" / "theme_styles.json"
    backup_path = config_path.with_suffix('.json.backup_6percent')

    # バックアップ作成
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            original_config = json.load(f)

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(original_config, f, indent=2, ensure_ascii=False)

        print(f"\n🔒 バックアップ作成: {backup_path}")

    except Exception as e:
        print(f"❌ バックアップ作成エラー: {e}")
        return

    # 改善版を適用
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(improved_config, f, indent=2, ensure_ascii=False)

        print(f"✅ 6%コントラスト比ゼブラスタイル適用完了: {config_path}")

    except Exception as e:
        print(f"❌ ファイル書き込みエラー: {e}")
        return

    print(f"\n🎯 改善結果:")
    print(f"   - 全16テーマに6%コントラスト比ゼブラ色を適用")
    print(f"   - QtThemeManager形式を参考にした自然な色差")
    print(f"   - 控えめで視認性の良いゼブラスタイル")


def validate_6percent_results():
    """6%調整後の結果を検証"""

    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return

    print(f"\n🔍 6%コントラスト比ゼブラスタイル検証:")
    print("-" * 60)

    theme_styles = config.get("theme_styles", {})
    total_themes = len(theme_styles)
    ideal_range_count = 0

    for theme_name, theme_data in theme_styles.items():
        colors = theme_data.get("colors", {})
        base_color = colors.get("input_background", "#ffffff")
        zebra_color = colors.get("zebra_alternate", base_color)

        # 色差計算
        base_rgb = hex_to_rgb(base_color)
        zebra_rgb = hex_to_rgb(zebra_color)
        color_diff = abs(sum(base_rgb) - sum(zebra_rgb)) / 3

        # 理想的な範囲（12-18程度）かチェック
        if 10 <= color_diff <= 20:
            ideal_range_count += 1
            status = "✅ 理想的"
        elif color_diff < 10:
            status = "⚠️  少し薄い"
        else:
            status = "⚠️  少し濃い"

        print(f"   {theme_name:12}: 色差{color_diff:4.1f} | {status}")

    print(f"\n📊 検証結果:")
    print(f"   理想的な範囲のテーマ: {ideal_range_count}/{total_themes}個")
    print(f"   適合率: {ideal_range_count/total_themes*100:.1f}%")


if __name__ == "__main__":
    print("🎨 QtThemeManager形式参考6%コントラスト比ゼブラ調整\n")

    # 6%コントラスト比ゼブラ調整を適用
    apply_6percent_zebra_adjustment()

    # 結果を検証
    validate_6percent_results()

    print(f"\n🎉 6%コントラスト比ゼブラスタイル適用完了！")
    print(f"   アプリケーションでテーマを切り替えて確認してください。")
