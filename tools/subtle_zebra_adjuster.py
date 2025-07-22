"""
控えめなゼブラスタイル生成ツール
視認性を保ちつつ、過度なコントラストを避ける
"""

import sys
import json
from pathlib import Path
from typing import Dict, Tuple

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.theme_accessibility import ColorAccessibilityAnalyzer


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """16進数カラーをRGBに変換"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """RGBを16進数カラーに変換"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def generate_subtle_zebra_color(base_color: str, target_diff: float = 10.0) -> str:
    """控えめなゼブラ色を生成（目標色差10程度）"""
    base_rgb = hex_to_rgb(base_color)
    base_luminance = sum(base_rgb) / 3

    # より控えめな調整係数
    if base_luminance > 200:  # 非常に明るい背景
        factor = 0.96  # 4%暗く（控えめ）
    elif base_luminance > 128:  # 明るい背景
        factor = 0.95  # 5%暗く
    elif base_luminance > 64:   # 中間の背景
        factor = 1.05  # 5%明るく
    else:  # 暗い背景
        factor = 1.08  # 8%明るく

    # 色差が目標値に近くなるよう微調整
    zebra_rgb = tuple(min(255, max(0, int(c * factor))) for c in base_rgb)
    current_diff = abs(sum(base_rgb) - sum(zebra_rgb)) / 3

    # 目標色差に調整
    if current_diff < target_diff * 0.7:  # 色差が小さすぎる場合
        if base_luminance > 128:
            factor = 0.93  # より暗く
        else:
            factor = 1.12  # より明るく
        zebra_rgb = tuple(min(255, max(0, int(c * factor))) for c in base_rgb)
    elif current_diff > target_diff * 1.5:  # 色差が大きすぎる場合
        if base_luminance > 128:
            factor = 0.97  # より控えめに暗く
        else:
            factor = 1.04  # より控えめに明るく
        zebra_rgb = tuple(min(255, max(0, int(c * factor))) for c in base_rgb)

    return rgb_to_hex(zebra_rgb)


def generate_subtle_zebra_themes() -> Dict:
    """全テーマの控えめなゼブラ色を生成"""

    # 現在の設定を読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

    theme_styles = config.get("theme_styles", {})
    subtle_updates = {}

    print("🎨 控えめなゼブラスタイル生成")
    print("=" * 50)

    for theme_name, theme_data in theme_styles.items():
        colors = theme_data.get("colors", {})
        base_color = colors.get("input_background", "#ffffff")
        current_zebra = colors.get("zebra_alternate", base_color)

        # 新しい控えめなゼブラ色を生成
        new_zebra = generate_subtle_zebra_color(base_color, target_diff=10.0)

        # 色差計算
        base_rgb = hex_to_rgb(base_color)
        current_zebra_rgb = hex_to_rgb(current_zebra)
        new_zebra_rgb = hex_to_rgb(new_zebra)

        current_diff = abs(sum(base_rgb) - sum(current_zebra_rgb)) / 3
        new_diff = abs(sum(base_rgb) - sum(new_zebra_rgb)) / 3

        subtle_updates[theme_name] = {
            "base_color": base_color,
            "old_zebra": current_zebra,
            "new_zebra": new_zebra,
            "old_diff": current_diff,
            "new_diff": new_diff
        }

        # 改善状況表示
        if new_diff < current_diff:
            improvement = "📉 より控えめに"
        elif new_diff > current_diff:
            improvement = "📈 少し強調"
        else:
            improvement = "➡️  変更なし"

        print(f"{theme_name:12}: {current_diff:4.1f} → {new_diff:4.1f} {improvement}")

    return subtle_updates


def apply_subtle_zebra_colors():
    """控えめなゼブラ色を適用"""

    subtle_updates = generate_subtle_zebra_themes()

    if not subtle_updates:
        print("❌ ゼブラ色の生成に失敗しました")
        return False

    # 設定ファイル読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return False

    # バックアップ作成
    backup_path = config_path.with_suffix('.json.backup_subtle_zebra')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n🔒 バックアップ作成: {backup_path}")

    # ゼブラ色を更新
    theme_styles = config.get("theme_styles", {})
    updated_count = 0

    print(f"\n🎯 控えめなゼブラ色適用:")

    for theme_name, update_data in subtle_updates.items():
        if theme_name in theme_styles:
            new_zebra = update_data["new_zebra"]
            theme_styles[theme_name]["colors"]["zebra_alternate"] = new_zebra
            updated_count += 1
            print(f"   ✅ {theme_name:12}: {update_data['old_zebra']} → {new_zebra}")

    # 更新された設定を保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 控えめなゼブラスタイル適用完了!")
    print(f"   更新テーマ数: {updated_count}/{len(subtle_updates)}")

    return True


def validate_subtle_zebra_accessibility():
    """控えめなゼブラ色でもアクセシビリティが保たれるか確認"""

    analyzer = ColorAccessibilityAnalyzer()

    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return False

    theme_styles = config.get("theme_styles", {})

    print(f"\n📊 控えめゼブラスタイルのアクセシビリティ検証:")
    print("-" * 60)

    good_themes = 0
    total_themes = len(theme_styles)

    for theme_name, theme_data in theme_styles.items():
        analysis = analyzer.analyze_theme_accessibility(theme_data)
        score = analysis.get("accessibility_score", 0)
        zebra_contrast = analysis.get("zebra_analysis", {}).get("min_contrast", 0)

        if score >= 80:
            good_themes += 1
            icon = "✅"
        else:
            icon = "❌"

        print(f"   {icon} {theme_name:12}: スコア {score:3d}点 | ゼブラ: {zebra_contrast:.1f}")

    accessibility_rate = good_themes / total_themes * 100

    print(f"\n📈 結果:")
    print(f"   高アクセシビリティ: {good_themes}/{total_themes} ({accessibility_rate:.1f}%)")

    if accessibility_rate >= 90:
        print(f"   🎉 優秀！控えめなゼブラでもアクセシビリティを維持しています")
        return True
    else:
        print(f"   ⚠️  一部テーマでアクセシビリティが低下している可能性があります")
        return False


if __name__ == "__main__":
    print("🦓 控えめなゼブラスタイル調整ツール")
    print("=" * 60)

    # 控えめなゼブラ色生成・表示
    subtle_updates = generate_subtle_zebra_themes()

    if subtle_updates:
        print(f"\n📋 変更サマリー:")
        significant_changes = sum(1 for data in subtle_updates.values()
                                if abs(data["old_diff"] - data["new_diff"]) > 2)
        print(f"   大幅変更: {significant_changes}/{len(subtle_updates)}テーマ")

        # 控えめなゼブラ色を適用
        if apply_subtle_zebra_colors():
            # アクセシビリティ検証
            validate_subtle_zebra_accessibility()
        else:
            print("❌ 適用に失敗しました")
    else:
        print("❌ ゼブラ色の生成に失敗しました")
