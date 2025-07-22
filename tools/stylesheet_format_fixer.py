"""
スタイルシートフォーマット修正ツール
JSONの改行文字問題を解決
"""

import sys
import json
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_clean_stylesheet_template() -> str:
    """クリーンなスタイルシートテンプレートを生成（改行なし）"""

    return ("QWidget {{ background-color: {background}; color: {foreground}; }} "
            "QMainWindow {{ background-color: {background}; }} "
            "QMenuBar {{ background-color: {menu_background}; color: {foreground}; }} "
            "QToolBar {{ background-color: {menu_background}; border: none; }} "
            "QPushButton {{ background-color: {button_background}; border: 1px solid {border}; color: {foreground}; padding: 5px; }} "
            "QPushButton:hover {{ background-color: {button_hover}; }} "
            "QTreeView, QListView {{ background-color: {input_background}; alternate-background-color: {zebra_alternate}; color: {foreground}; border: 1px solid {border}; selection-background-color: {selection}; }} "
            "QTreeView::item:alternate, QListView::item:alternate {{ background-color: {zebra_alternate}; }} "
            "QTreeView::item:selected, QListView::item:selected {{ background-color: {selection}; }} "
            "QTreeView::item:hover, QListView::item:hover {{ background-color: {hover}; }} "
            "QTextEdit {{ background-color: {input_background}; color: {foreground}; border: 1px solid {border}; }}")


def fix_stylesheet_format():
    """スタイルシートフォーマットを修正"""
    print("🔧 スタイルシートフォーマット修正開始")
    print("=" * 50)

    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")
        return

    # バックアップ作成
    backup_path = config_path.with_suffix('.json.backup_format_fix')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"🔒 バックアップ作成: {backup_path}")

    # クリーンなテンプレート生成
    clean_template = generate_clean_stylesheet_template()

    # 全テーマのスタイルシートテンプレートを更新
    theme_styles = config.get("theme_styles", {})

    for theme_name, theme_data in theme_styles.items():
        theme_data["stylesheet_template"] = clean_template
        print(f"✅ {theme_name}テーマのスタイルシート修正完了")

    # デフォルトテンプレートも更新
    config["default_stylesheet_template"] = clean_template

    # 修正済み設定を保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n🎯 スタイルシートフォーマット修正完了!")
    print(f"   修正テーマ数: {len(theme_styles)}")
    print(f"   設定ファイル: {config_path}")


def test_template_formatting():
    """テンプレートフォーマットをテスト"""
    print("\n🧪 テンプレートフォーマットテスト")
    print("-" * 50)

    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # テストテーマでフォーマットテスト
        test_theme = config['theme_styles']['dark']
        colors = test_theme['colors']
        template = test_theme['stylesheet_template']

        try:
            # テンプレートに色を埋め込んでテスト
            formatted_css = template.format(**colors)

            print("✅ スタイルシートフォーマット正常")
            print(f"   長さ: {len(formatted_css)} 文字")
            print(f"   改行文字: {'含まれる' if '\\n' in formatted_css else '含まれない'}")
            print(f"   sample: {formatted_css[:100]}...")

        except Exception as e:
            print(f"❌ フォーマットエラー: {e}")

    except Exception as e:
        print(f"❌ テストエラー: {e}")


if __name__ == "__main__":
    print("🔧 スタイルシートフォーマット修正ツール")
    print("JSONの改行文字問題を解決してゼブラスタイルを正常動作させます\n")

    # フォーマット修正
    fix_stylesheet_format()

    # テスト
    test_template_formatting()
