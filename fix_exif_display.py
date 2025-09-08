#!/usr/bin/env python3
"""
EXIF表示問題の修正スクリプト

EXIFパネルの表示問題を修正します。
"""

import sys
from pathlib import Path

def fix_exif_panel_display():
    """EXIFパネルの表示問題を修正"""

    exif_panel_path = Path("src/integration/ui/exif_panel.py")

    if not exif_panel_path.exists():
        print(f"❌ EXIFパネルファイルが見つかりません: {exif_panel_path}")
        return False

    print("🔧 EXIFパネルの表示問題を修正中...")

    # バックアップを作成
    backup_path = exif_panel_path.with_suffix(".py.backup")
    if not backup_path.exists():
        with open(exif_panel_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ バックアップを作成しました: {backup_path}")

    # 修正内容を適用
    fixes_applied = []

    with open(exif_panel_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修正1: _get_colorメソッドの改善
    if "_get_color" in content and "fallback" in content:
        # 既に修正済みの場合はスキップ
        if "def _get_color_safe" not in content:
            color_fix = '''
    def _get_color_safe(self, color_name: str, fallback: str = "#000000") -> str:
        """安全な色取得メソッド（フォールバック付き）"""
        try:
            if self.theme_manager and hasattr(self.theme_manager, 'get_color'):
                color = self.theme_manager.get_color(color_name, fallback)
                if color and color != "None":
                    return color
            return fallback
        except Exception:
            return fallback
'''
            # _get_colorメソッドの直前に挿入
            content = content.replace(
                "    def _get_color(self, color_name: str, fallback: str) -> str:",
                color_fix + "\n    def _get_color(self, color_name: str, fallback: str) -> str:"
            )
            fixes_applied.append("安全な色取得メソッドを追加")

    # 修正2: セクション作成時のエラーハンドリング強化
    if "def _create_info_section" in content:
        old_section = '''    def _create_info_section(self, title: str, info_dict: Dict[str, str], border_color: str = "#bdc3c7") -> QGroupBox:
        """情報セクションを作成（統合版）"""
        group = QGroupBox(title)
        border = self._get_color("border", border_color)
        bg = self._get_color("background", "#ffffff")
        fg = self._get_color("foreground", "#2c3e50")
        # 背景と前景が同色になってしまうテーマ向けのコントラスト確保
        if isinstance(fg, str) and isinstance(bg, str) and fg.lower() == bg.lower():
            alt = self._get_color("primary", "#2c3e50")
            fg = alt if alt.lower() != bg.lower() else "#000000"'''

        new_section = '''    def _create_info_section(self, title: str, info_dict: Dict[str, str], border_color: str = "#bdc3c7") -> QGroupBox:
        """情報セクションを作成（統合版）"""
        group = QGroupBox(title)
        border = self._get_color_safe("border", border_color)
        bg = self._get_color_safe("background", "#ffffff")
        fg = self._get_color_safe("foreground", "#2c3e50")

        # 背景と前景が同色になってしまうテーマ向けのコントラスト確保
        if isinstance(fg, str) and isinstance(bg, str) and fg.lower() == bg.lower():
            alt = self._get_color_safe("primary", "#2c3e50")
            fg = alt if alt.lower() != bg.lower() else "#000000"

        # デバッグ情報をログに出力
        if hasattr(self, 'logger_system'):
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "exif_section_colors",
                f"セクション色設定: {title} - border:{border}, bg:{bg}, fg:{fg}",
            )'''

        if old_section in content:
            content = content.replace(old_section, new_section)
            fixes_applied.append("セクション作成時の色設定を改善")

    # 修正3: レイアウト更新の強制
    if "self.integrated_widget.update()" in content:
        # 既に修正済み
        pass
    else:
        # レイアウト更新を強制する処理を追加
        old_update = '''            # 再描画をトリガ
            try:
                self.integrated_layout.invalidate()
            except Exception:
                pass
            self.integrated_widget.adjustSize()
            self.integrated_widget.update()
            try:
                self.integrated_scroll_area.widget().adjustSize()
            except Exception:
                pass
            self.integrated_scroll_area.update()'''

        new_update = '''            # 再描画をトリガ（強化版）
            try:
                self.integrated_layout.invalidate()
                self.integrated_layout.update()
            except Exception:
                pass

            try:
                self.integrated_widget.adjustSize()
                self.integrated_widget.update()
                self.integrated_widget.repaint()
            except Exception:
                pass

            try:
                self.integrated_scroll_area.widget().adjustSize()
                self.integrated_scroll_area.update()
                self.integrated_scroll_area.repaint()
            except Exception:
                pass

            # 強制的にレイアウトを再計算
            try:
                self.integrated_scroll_area.setWidget(self.integrated_widget)
                self.integrated_scroll_area.setWidgetResizable(True)
            except Exception:
                pass'''

        if old_update in content:
            content = content.replace(old_update, new_update)
            fixes_applied.append("レイアウト更新処理を強化")

    # 修正4: 初期メッセージの表示改善
    if "📷 画像を選択してください" in content:
        old_msg = '''            self.initial_message_label = QLabel("📷 画像を選択してください")
            self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.initial_message_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-style: italic;
                    font-size: 16px;
                    padding: 20px;
                }
            """)'''

        new_msg = '''            self.initial_message_label = QLabel("📷 画像を選択してください")
            self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_color = self._get_color_safe("foreground", "#7f8c8d")
            msg_bg = self._get_color_safe("background", "#ffffff")
            self.initial_message_label.setStyleSheet(f"""
                QLabel {{
                    color: {msg_color};
                    background-color: {msg_bg};
                    font-style: italic;
                    font-size: 16px;
                    padding: 20px;
                    border: 1px solid {self._get_color_safe("border", "#e0e0e0")};
                    border-radius: 5px;
                    margin: 10px;
                }}
            """)'''

        if old_msg in content:
            content = content.replace(old_msg, new_msg)
            fixes_applied.append("初期メッセージの表示を改善")

    # ファイルに書き戻し
    with open(exif_panel_path, 'w', encoding='utf-8') as f:
        f.write(content)

    if fixes_applied:
        print("✅ 以下の修正を適用しました:")
        for fix in fixes_applied:
            print(f"   - {fix}")
        return True
    else:
        print("ℹ️ 適用可能な修正が見つかりませんでした（既に修正済みの可能性があります）")
        return False

def main():
    """メイン関数"""
    print("🚀 EXIF表示問題の修正を開始します")

    success = fix_exif_panel_display()

    if success:
        print("\n✅ 修正が完了しました")
        print("💡 アプリケーションを再起動してください")
    else:
        print("\n⚠️ 修正は適用されませんでした")

    print("\n📝 修正内容:")
    print("   1. 安全な色取得メソッドの追加")
    print("   2. セクション作成時の色設定改善")
    print("   3. レイアウト更新処理の強化")
    print("   4. 初期メッセージの表示改善")

if __name__ == "__main__":
    main()
