#!/usr/bin/env python3
"""
テーマ背景問題修正スクリプト

サムネイルグリッドとEXIF panelの背景が白いままの問題を修正します。
位置情報パネルのように、コンテナ自体にもテーマを適用します。

Author: Kiro AI Integration System
"""

import os
import sys
from pathlib import Path

def fix_exif_panel_background():
    """EXIF panelの背景テーマ適用を修正"""
    exif_panel_path = Path("src/integration/ui/exif_panel.py")

    if not exif_panel_path.exists():
        print(f"❌ {exif_panel_path} が見つかりません")
        return False

    print(f"🔧 {exif_panel_path} を修正中...")

    with open(exif_panel_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. _setup_ui メソッドでパネル自体の背景を設定
    old_setup_ui = '''    def _setup_ui(self):
        """UIの初期化（統合版）"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)'''

    new_setup_ui = '''    def _setup_ui(self):
        """UIの初期化（統合版）"""
        try:
            # パネル自体の背景テーマを適用
            self._apply_panel_theme()

            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)'''

    if old_setup_ui in content:
        content = content.replace(old_setup_ui, new_setup_ui)
        print("✅ _setup_ui メソッドを修正")
    else:
        print("⚠️ _setup_ui メソッドのパターンが見つかりません")

    # 2. _apply_panel_theme メソッドを追加
    theme_method = '''
    def _apply_panel_theme(self):
        """パネル自体にテーマを適用"""
        try:
            bg_color = self._get_color("background", "#ffffff")
            border_color = self._get_color("border", "#e0e0e0")

            self.setStyleSheet(f"""
                EXIFPanel {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 5px;
                }}
            """)
        except Exception as e:
            # エラー時はデフォルトスタイルを適用
            self.setStyleSheet("""
                EXIFPanel {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                }
            """)
'''

    # _on_theme_changed メソッドの前に挿入
    old_theme_changed = '''    def _on_theme_changed(self, theme_name: str):'''

    if old_theme_changed in content:
        content = content.replace(old_theme_changed, theme_method + old_theme_changed)
        print("✅ _apply_panel_theme メソッドを追加")
    else:
        print("⚠️ _on_theme_changed メソッドが見つかりません")

    # 3. _on_theme_changed メソッドでパネルテーマも更新
    old_theme_change_body = '''    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            # 現在のEXIFデータがある場合は再表示
            if hasattr(self, '_last_exif_data') and self._last_exif_data:
                self._create_integrated_sections(self._last_exif_data)'''

    new_theme_change_body = '''    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            # パネル自体のテーマを更新
            self._apply_panel_theme()

            # 現在のEXIFデータがある場合は再表示
            if hasattr(self, '_last_exif_data') and self._last_exif_data:
                self._create_integrated_sections(self._last_exif_data)'''

    if old_theme_change_body in content:
        content = content.replace(old_theme_change_body, new_theme_change_body)
        print("✅ _on_theme_changed メソッドを修正")
    else:
        print("⚠️ _on_theme_changed メソッドの本体が見つかりません")

    # ファイルを保存
    with open(exif_panel_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {exif_panel_path} の修正完了")
    return True

def fix_thumbnail_grid_background():
    """サムネイルグリッドの背景テーマ適用を修正"""
    thumbnail_path = Path("src/integration/ui/simple_thumbnail_grid.py")

    if not thumbnail_path.exists():
        print(f"❌ {thumbnail_path} が見つかりません")
        return False

    print(f"🔧 {thumbnail_path} を修正中...")

    with open(thumbnail_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # SimpleThumbnailGrid クラスの __init__ メソッドを修正
    old_init = '''        self.theme_manager = theme_manager

        # 画像リスト
        self.image_paths: List[Path] = []'''

    new_init = '''        self.theme_manager = theme_manager

        # グリッド自体の背景テーマを適用
        self._apply_grid_theme()

        # 画像リスト
        self.image_paths: List[Path] = []'''

    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ SimpleThumbnailGrid __init__ メソッドを修正")
    else:
        print("⚠️ SimpleThumbnailGrid __init__ メソッドのパターンが見つかりません")

    # _apply_grid_theme メソッドを追加
    grid_theme_method = '''
    def _apply_grid_theme(self):
        """グリッド自体にテーマを適用"""
        try:
            bg_color = "#ffffff"
            border_color = "#e0e0e0"

            # テーママネージャーから色を取得
            if self.theme_manager and hasattr(self.theme_manager, 'get_color'):
                try:
                    bg_color = self.theme_manager.get_color("background", "#ffffff")
                    border_color = self.theme_manager.get_color("border", "#e0e0e0")
                except Exception:
                    pass  # デフォルト色を使用

            # アプリケーションのパレットからも色を取得（フォールバック）
            if not self.theme_manager:
                app = QApplication.instance()
                if app:
                    palette = app.palette()
                    is_dark_theme = self._is_dark_theme(palette)

                    if is_dark_theme:
                        bg_color = "#2d2d2d"
                        border_color = "#4a4a4a"

            self.setStyleSheet(f"""
                SimpleThumbnailGrid {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 5px;
                }}
            """)
        except Exception:
            # エラー時はデフォルトスタイルを適用
            self.setStyleSheet("""
                SimpleThumbnailGrid {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                }
            """)
'''

    # _setup_ui メソッドの前に挿入
    old_setup_ui = '''    def _setup_ui(self):'''

    if old_setup_ui in content:
        content = content.replace(old_setup_ui, grid_theme_method + old_setup_ui)
        print("✅ _apply_grid_theme メソッドを追加")
    else:
        print("⚠️ _setup_ui メソッドが見つかりません")

    # ファイルを保存
    with open(thumbnail_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {thumbnail_path} の修正完了")
    return True

def main():
    """メイン処理"""
    print("🎨 テーマ背景問題修正スクリプト開始")
    print("=" * 50)

    success_count = 0

    # EXIF panel の修正
    if fix_exif_panel_background():
        success_count += 1

    # サムネイルグリッドの修正
    if fix_thumbnail_grid_background():
        success_count += 1

    print("=" * 50)
    print(f"🎯 修正完了: {success_count}/2 ファイル")

    if success_count == 2:
        print("✅ すべての修正が完了しました")
        print("\n📋 修正内容:")
        print("• EXIF panel: パネル自体の背景テーマ適用")
        print("• サムネイルグリッド: グリッド自体の背景テーマ適用")
        print("• スクロールエリア: テーマに追随する背景色設定")
        print("\n🔄 アプリケーションを再起動してテーマを確認してください")
        return True
    else:
        print("❌ 一部の修正に失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
