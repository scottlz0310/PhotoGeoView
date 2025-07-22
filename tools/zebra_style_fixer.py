"""
ゼブラスタイル実装修正ツール
QTreeView/QListViewの交互背景色を正しく実装
"""

import sys
import json
from pathlib import Path
from typing import Dict

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.theme_accessibility import ColorAccessibilityAnalyzer


def generate_zebra_enhanced_stylesheet() -> str:
    """ゼブラスタイル対応の完全スタイルシートテンプレートを生成"""

    return """QWidget {
    background-color: {background};
    color: {foreground};
}
QMainWindow {
    background-color: {background};
}
QMenuBar {
    background-color: {menu_background};
    color: {foreground};
}
QToolBar {
    background-color: {menu_background};
    border: none;
}
QPushButton {
    background-color: {button_background};
    border: 1px solid {border};
    color: {foreground};
    padding: 5px;
}
QPushButton:hover {
    background-color: {button_hover};
}
QTreeView, QListView {
    background-color: {input_background};
    alternate-background-color: {zebra_alternate};
    color: {foreground};
    border: 1px solid {border};
    selection-background-color: {selection};
}
QTreeView::item:alternate, QListView::item:alternate {
    background-color: {zebra_alternate};
}
QTreeView::item:selected, QListView::item:selected {
    background-color: {selection};
}
QTreeView::item:hover, QListView::item:hover {
    background-color: {hover};
}
QTextEdit {
    background-color: {input_background};
    color: {foreground};
    border: 1px solid {border};
}"""


def generate_zebra_colors_for_all_themes() -> Dict:
    """全テーマのゼブラ色を生成"""

    analyzer = ColorAccessibilityAnalyzer()

    # 既存の設定ファイルを読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

    theme_styles = config.get("theme_styles", {})
    enhanced_themes = {}

    for theme_name, theme_data in theme_styles.items():
        colors = theme_data.get("colors", {})
        base_bg = colors.get("input_background", colors.get("background", "#ffffff"))
        text_color = colors.get("foreground", "#000000")

        # ゼブラ色を生成
        zebra_analysis = analyzer.generate_zebra_colors(base_bg, text_color)

        # 新しい色セットを作成
        enhanced_colors = colors.copy()
        enhanced_colors["zebra_alternate"] = zebra_analysis["alternate"]

        # selection や hover が未定義の場合はデフォルト値を設定
        if "selection" not in enhanced_colors:
            enhanced_colors["selection"] = colors.get("button_hover", "#0078d4")
        if "hover" not in enhanced_colors:
            enhanced_colors["hover"] = colors.get("button_background", "#e0e0e0")

        enhanced_themes[theme_name] = {
            **theme_data,
            "colors": enhanced_colors,
            "zebra_contrast": zebra_analysis["min_contrast"]
        }

    return enhanced_themes


def fix_zebra_styling():
    """ゼブラスタイリング問題を修正"""
    print("🦓 ゼブラスタイル実装修正開始")
    print("=" * 60)

    # ゼブラ色を全テーマに生成
    enhanced_themes = generate_zebra_colors_for_all_themes()

    # 新しいスタイルシートテンプレートを生成
    new_template = generate_zebra_enhanced_stylesheet()

    # 既存設定を読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return

    # バックアップ作成
    backup_path = config_path.with_suffix('.json.backup_before_zebra')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"🔒 バックアップ作成: {backup_path}")

    # 全テーマを更新
    theme_styles = config.get("theme_styles", {})

    for theme_name, enhanced_theme in enhanced_themes.items():
        if theme_name in theme_styles:
            # 色情報とスタイルシートテンプレートを更新
            theme_styles[theme_name]["colors"] = enhanced_theme["colors"]
            theme_styles[theme_name]["stylesheet_template"] = new_template

            zebra_contrast = enhanced_theme.get("zebra_contrast", 0)
            print(f"✅ {theme_name:10} | ゼブラ色: {enhanced_theme['colors']['zebra_alternate']} | コントラスト: {zebra_contrast:.2f}")

    # デフォルトテンプレートも更新
    config["default_stylesheet_template"] = new_template

    # 修正済み設定を保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n🎯 ゼブラスタイル実装完了!")
    print(f"   修正テーマ数: {len(enhanced_themes)}")
    print(f"   新機能: alternate-background-color対応")
    print(f"   設定ファイル: {config_path}")


def validate_zebra_implementation():
    """ゼブラスタイル実装を検証"""
    print("\n🔍 ゼブラスタイル実装検証")
    print("-" * 60)

    analyzer = ColorAccessibilityAnalyzer()

    # 修正後の設定を読み込み
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return

    theme_styles = config.get("theme_styles", {})
    perfect_zebra_count = 0
    good_zebra_count = 0

    print(f"{'テーマ名':<12} | {'ベース背景':<9} | {'ゼブラ背景':<9} | {'コントラスト':<6} | {'評価'}")
    print("-" * 70)

    for theme_name, theme_data in theme_styles.items():
        colors = theme_data.get("colors", {})
        base_bg = colors.get("input_background", "#ffffff")
        zebra_bg = colors.get("zebra_alternate", "未設定")
        text_color = colors.get("foreground", "#000000")

        if zebra_bg != "未設定":
            contrast = analyzer.calculate_contrast_ratio(zebra_bg, text_color)

            if contrast >= 7.0:
                evaluation = "🟢 完璧"
                perfect_zebra_count += 1
            elif contrast >= 4.5:
                evaluation = "🟡 良好"
                good_zebra_count += 1
            elif contrast >= 3.0:
                evaluation = "🟠 可能"
            else:
                evaluation = "🔴 問題"

            print(f"{theme_name:<12} | {base_bg:<9} | {zebra_bg:<9} | {contrast:>6.2f} | {evaluation}")
        else:
            print(f"{theme_name:<12} | {base_bg:<9} | {'未設定':<9} | {'N/A':>6} | 🔴 未実装")

    total_themes = len(theme_styles)
    implemented_count = sum(1 for t in theme_styles.values()
                           if t.get("colors", {}).get("zebra_alternate", "未設定") != "未設定")

    print("\n📊 ゼブラスタイル実装状況:")
    print(f"   実装済み: {implemented_count}/{total_themes} ({implemented_count/total_themes*100:.1f}%)")
    print(f"   完璧レベル: {perfect_zebra_count}テーマ")
    print(f"   良好レベル: {good_zebra_count}テーマ")


if __name__ == "__main__":
    print("🦓 ファイルナビゲーター ゼブラスタイル修正ツール")
    print("画像で確認された表示問題を根本的に解決します\n")

    # ゼブラスタイル修正
    fix_zebra_styling()

    # 実装検証
    validate_zebra_implementation()
