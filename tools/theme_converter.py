#!/usr/bin/env python3
"""
Theme Settings Converter

既存のtheme_settings.jsonを新しいThemeConfiguration形式に変換するスクリプト
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict


def convert_old_theme_to_new(old_theme: Dict[str, Any]) -> Dict[str, Any]:
    """古いテーマ形式を新しいThemeConfiguration形式に変換"""

    # 基本情報
    new_theme = {
        "name": old_theme.get("name", "unknown"),
        "display_name": old_theme.get("display_name", "Unknown Theme"),
        "description": old_theme.get("description", ""),
        "version": "1.0.0",
        "author": "Theme Converter",
        "qt_theme_name": old_theme.get("name", "default"),
        "style_sheet": "",
        "color_scheme": {},
        "icon_theme": "default",
        "window_style": {},
        "button_style": {},
        "menu_style": {},
        "toolbar_style": {},
        "accessibility_features": {
            "high_contrast": old_theme.get("name") == "high_contrast",
            "large_fonts": False,
            "screen_reader_support": True,
            "keyboard_navigation": True,
            "focus_indicators": True,
        },
        "performance_settings": {
            "animation_enabled": True,
            "transparency_enabled": True,
            "shadow_effects": True,
            "gradient_rendering": True,
            "anti_aliasing": True,
        },
        "custom_properties": {},
        "created_date": "2024-01-01T00:00:00",
        "last_modified": "2024-01-01T00:00:00",
        "usage_count": 0,
    }

    # カラースキームの変換
    color_scheme = {}

    # 基本色
    if "backgroundColor" in old_theme:
        color_scheme["background"] = old_theme["backgroundColor"]
    if "textColor" in old_theme:
        color_scheme["foreground"] = old_theme["textColor"]
    if "primaryColor" in old_theme:
        color_scheme["primary"] = old_theme["primaryColor"]
    if "accentColor" in old_theme:
        color_scheme["accent"] = old_theme["accentColor"]

    # パネル関連
    if "panel" in old_theme:
        panel = old_theme["panel"]
        if "border" in panel:
            color_scheme["border"] = panel["border"]
        if "background" in panel:
            color_scheme["secondary"] = panel["background"]

    # テキスト関連
    if "text" in old_theme:
        text = old_theme["text"]
        if "secondary" in text:
            color_scheme["secondary"] = text["secondary"]
        if "muted" in text:
            color_scheme["disabled"] = text["muted"]
        if "success" in text:
            color_scheme["success"] = text["success"]
        if "warning" in text:
            color_scheme["warning"] = text["warning"]
        if "error" in text:
            color_scheme["error"] = text["error"]

    # ボタン関連
    if "button" in old_theme:
        button = old_theme["button"]
        if "hover" in button:
            color_scheme["hover"] = button["hover"]
        if "pressed" in button:
            color_scheme["selected"] = button["pressed"]

    # 入力関連
    if "input" in old_theme:
        input_theme = old_theme["input"]
        if "focus" in input_theme:
            color_scheme["info"] = input_theme["focus"]

    # デフォルト値の設定
    if "background" not in color_scheme:
        color_scheme["background"] = "#ffffff"
    if "foreground" not in color_scheme:
        color_scheme["foreground"] = "#000000"
    if "primary" not in color_scheme:
        color_scheme["primary"] = "#007acc"
    if "secondary" not in color_scheme:
        color_scheme["secondary"] = "#6c757d"
    if "accent" not in color_scheme:
        color_scheme["accent"] = "#17a2b8"
    if "border" not in color_scheme:
        color_scheme["border"] = "#dee2e6"
    if "hover" not in color_scheme:
        color_scheme["hover"] = "#f8f9fa"
    if "selected" not in color_scheme:
        color_scheme["selected"] = "#e3f2fd"
    if "success" not in color_scheme:
        color_scheme["success"] = "#28a745"
    if "warning" not in color_scheme:
        color_scheme["warning"] = "#ffc107"
    if "error" not in color_scheme:
        color_scheme["error"] = "#dc3545"
    if "info" not in color_scheme:
        color_scheme["info"] = "#17a2b8"
    if "disabled" not in color_scheme:
        color_scheme["disabled"] = "#6c757d"

    new_theme["color_scheme"] = color_scheme

    # スタイルシートの生成
    style_sheet = f"""
QMainWindow {{
    background-color: {color_scheme.get("background", "#ffffff")};
    color: {color_scheme.get("foreground", "#000000")};
}}

QGroupBox {{
    border: 1px solid {color_scheme.get("border", "#dee2e6")};
    border-radius: 3px;
    margin-top: 5px;
    padding-top: 5px;
    background-color: {color_scheme.get("secondary", "#f8f9fa")};
}}

QGroupBox::title {{
    color: {color_scheme.get("primary", "#007acc")};
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}}

QPushButton {{
    background-color: {color_scheme.get("primary", "#007acc")};
    color: {color_scheme.get("foreground", "#ffffff")};
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {color_scheme.get("hover", "#0056b3")};
}}

QPushButton:pressed {{
    background-color: {color_scheme.get("selected", "#004085")};
}}

QLabel {{
    color: {color_scheme.get("foreground", "#000000")};
}}

QTextEdit {{
    background-color: {color_scheme.get("background", "#ffffff")};
    color: {color_scheme.get("foreground", "#000000")};
    border: 1px solid {color_scheme.get("border", "#dee2e6")};
    border-radius: 3px;
    padding: 5px;
}}
"""

    new_theme["style_sheet"] = style_sheet.strip()

    return new_theme


def convert_theme_file(input_file: Path, output_file: Path) -> bool:
    """テーマファイルを変換"""
    try:
        print(f"変換中: {input_file} -> {output_file}")

        # 入力ファイルを読み込み
        with open(input_file, encoding="utf-8") as f:
            old_data = json.load(f)

        # 利用可能なテーマを取得
        if "available_themes" not in old_data:
            print("エラー: available_themesセクションが見つかりません")
            return False

        available_themes = old_data["available_themes"]
        converted_themes = []

        # 各テーマを変換
        for theme_name, theme_data in available_themes.items():
            print(f"  テーマ '{theme_name}' を変換中...")
            converted_theme = convert_old_theme_to_new(theme_data)
            converted_themes.append(converted_theme)

        # 出力ファイルに保存
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(converted_themes, f, ensure_ascii=False, indent=2)

        print(f"変換完了: {len(converted_themes)}個のテーマを変換しました")
        return True

    except Exception as e:
        print(f"変換エラー: {e}")
        return False


def main() -> None:
    """メイン関数"""
    # ファイルパスを設定
    current_dir = Path(__file__).parent.parent
    input_file = current_dir / "config" / "custom_themes" / "theme_settings.json"
    output_file = current_dir / "config" / "custom_themes" / "converted_themes.json"

    print("=== Theme Settings Converter ===")
    print(f"入力ファイル: {input_file}")
    print(f"出力ファイル: {output_file}")
    print()

    # 入力ファイルの存在確認
    if not input_file.exists():
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        sys.exit(1)

    # 変換実行
    if convert_theme_file(input_file, output_file):
        print("\n変換が正常に完了しました！")
        print(f"新しいテーマファイル: {output_file}")
        print("\n使用方法:")
        print("1. 既存のtheme_settings.jsonをバックアップ")
        print("2. converted_themes.jsonをtheme_settings.jsonにリネーム")
        print("3. アプリケーションを再起動")
    else:
        print("\n変換に失敗しました。")
        sys.exit(1)


if __name__ == "__main__":
    main()
