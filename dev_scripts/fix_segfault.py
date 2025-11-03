#!/usr/bin/env python3
"""
Segmentation fault修正スクリプト

EXIFパネルの安全性を向上させ、Segmentation faultを防止します。
"""

from pathlib import Path


def create_safe_exif_panel():
    """安全なEXIFパネルの修正を適用"""

    exif_panel_path = Path("src/integration/ui/exif_panel.py")

    if not exif_panel_path.exists():
        print(f"❌ EXIFパネルファイルが見つかりません: {exif_panel_path}")
        return False

    print("🔧 Segmentation fault対策を適用中...")

    # 現在のファイル内容を読み取り
    with open(exif_panel_path, encoding="utf-8") as f:
        content = f.read()

    fixes_applied = []

    # 修正1: テーマ変更時の安全性向上
    if "def apply_theme(self):" in content:
        old_apply_theme = '''    def apply_theme(self):
        """テーマ変更時にスタイルを再適用"""
        try:
            if self._last_exif_data:
                # 直近のEXIF表示をテーマ色で再構築
                self._create_integrated_sections(self._last_exif_data)
                self._update_gps_display(self._last_exif_data)
            elif self.current_image_path and self.current_image_path.exists():
                # EXIFを再読込して再構築
                self._load_exif_data()
            # どちらも無ければ何もしない（次回ロード時に新テーマが反映）
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "apply_theme_to_exif_panel"}, AIComponent.KIRO
            )'''

        new_apply_theme = '''    def apply_theme(self):
        """テーマ変更時にスタイルを再適用（安全版）"""
        try:
            # テーマ変更中はUIの更新を一時停止
            self.setUpdatesEnabled(False)

            # 既存のウィジェットを安全にクリア
            self._safe_clear_layout()

            # 少し待機してからUI再構築
            if hasattr(self, '_last_exif_data') and self._last_exif_data:
                self._create_integrated_sections(self._last_exif_data)
                self._update_gps_display(self._last_exif_data)
            elif hasattr(self, 'current_image_path') and self.current_image_path and self.current_image_path.exists():
                self._load_exif_data()

            # UI更新を再開
            self.setUpdatesEnabled(True)
            self.update()

        except Exception as e:
            # エラー時もUI更新を再開
            self.setUpdatesEnabled(True)
            if hasattr(self, 'error_handler'):
                self.error_handler.handle_error(
                    e, ErrorCategory.UI_ERROR, {"operation": "apply_theme_to_exif_panel"}, AIComponent.KIRO
                )'''

        if old_apply_theme in content:
            content = content.replace(old_apply_theme, new_apply_theme)
            fixes_applied.append("テーマ変更時の安全性を向上")

    # 修正2: 安全なレイアウトクリア機能を追加
    if "def _safe_clear_layout(self):" not in content:
        safe_clear_method = '''
    def _safe_clear_layout(self):
        """安全なレイアウトクリア（Segmentation fault対策）"""
        try:
            if hasattr(self, 'integrated_layout') and self.integrated_layout:
                # 子ウィジェットを安全に削除
                while self.integrated_layout.count():
                    item = self.integrated_layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()

                        layout = item.layout()
                        if layout:
                            self._clear_nested_layout(layout)

                # レイアウトを無効化
                self.integrated_layout.invalidate()

        except Exception as e:
            if hasattr(self, 'logger_system'):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "safe_clear_layout_error",
                    f"安全なレイアウトクリア中にエラー: {str(e)}",
                )

    def _clear_nested_layout(self, layout):
        """ネストしたレイアウトを安全にクリア"""
        try:
            while layout.count():
                item = layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

                    nested_layout = item.layout()
                    if nested_layout:
                        self._clear_nested_layout(nested_layout)
        except Exception:
            pass
'''

        # _get_colorメソッドの前に挿入
        if "def _get_color_safe(self," in content:
            content = content.replace(
                "    def _get_color_safe(self,",
                safe_clear_method + "\n    def _get_color_safe(self,",
            )
            fixes_applied.append("安全なレイアウトクリア機能を追加")

    # 修正3: ウィジェット削除時の安全性向上
    if "def deleteLater(self):" not in content:
        safe_delete_method = '''
    def deleteLater(self):
        """安全なウィジェット削除"""
        try:
            # UI更新を停止
            self.setUpdatesEnabled(False)

            # 子ウィジェットを安全に削除
            self._safe_clear_layout()

            # 親クラスのdeleteLaterを呼び出し
            super().deleteLater()

        except Exception as e:
            # エラーが発生しても親クラスのdeleteLaterは呼び出す
            super().deleteLater()
'''

        # クラスの最後に追加
        if "    # Theme helpers" in content:
            content = content.replace(
                "    # Theme helpers", safe_delete_method + "\n    # Theme helpers"
            )
            fixes_applied.append("安全なウィジェット削除機能を追加")

    # 修正4: 初期化時の安全性向上
    if "__init__" in content and "self.setUpdatesEnabled(False)" not in content:
        # __init__メソッドの最初にUI更新を無効化
        init_pattern = "def __init__("
        if init_pattern in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if init_pattern in line:
                    # __init__メソッドの開始を見つけた
                    # super().__init__()の後にUI更新無効化を追加
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if "super().__init__()" in lines[j]:
                            lines.insert(
                                j + 1, "        # UI更新を一時的に無効化（初期化中）"
                            )
                            lines.insert(j + 2, "        self.setUpdatesEnabled(False)")
                            break
                    break

            # __init__メソッドの最後でUI更新を有効化
            for i, line in enumerate(lines):
                if "self._restore_height_settings()" in line:
                    lines.insert(i + 1, "        # UI更新を有効化")
                    lines.insert(i + 2, "        self.setUpdatesEnabled(True)")
                    break

            content = "\n".join(lines)
            fixes_applied.append("初期化時の安全性を向上")

    # ファイルに書き戻し
    with open(exif_panel_path, "w", encoding="utf-8") as f:
        f.write(content)

    if fixes_applied:
        print("✅ 以下のSegmentation fault対策を適用しました:")
        for fix in fixes_applied:
            print(f"   - {fix}")
        return True
    else:
        print("ℹ️ 適用可能な修正が見つかりませんでした")
        return False


def main():
    """メイン関数"""
    print("🚀 Segmentation fault修正を開始します")

    success = create_safe_exif_panel()

    if success:
        print("\n✅ 修正が完了しました")
        print("💡 アプリケーションを再起動してください")
        print("\n⚠️ 注意事項:")
        print("   - テーマ変更は慎重に行ってください")
        print("   - 大量の画像を連続で選択しないでください")
        print("   - メモリ使用量を定期的に確認してください")
    else:
        print("\n⚠️ 修正は適用されませんでした")

    print("\n📝 Segmentation fault対策:")
    print("   1. テーマ変更時のUI更新を安全化")
    print("   2. レイアウトクリア処理を強化")
    print("   3. ウィジェット削除を安全化")
    print("   4. 初期化処理を改善")


if __name__ == "__main__":
    main()
