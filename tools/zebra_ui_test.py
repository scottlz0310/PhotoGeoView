"""
ゼブラスタイル修正後のリアルUIテスト
実際のアプリケーションでゼブラスタイルが正しく動作するかテスト
"""

import sys
import json
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem, QPushButton
    from PyQt6.QtCore import Qt
    from src.ui.theme_manager import ThemeManager
    from src.core.settings import Settings

    class ZebraTestWindow(QMainWindow):
        """ゼブラスタイルテスト用ウィンドウ"""

        def __init__(self):
            super().__init__()
            self.setWindowTitle("ゼブラスタイル修正テスト")
            self.setGeometry(300, 300, 600, 400)

            # 中央ウィジェット
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # テーマ切り替えボタン
            self.theme_button = QPushButton("テーマ切替: dark")
            self.theme_button.clicked.connect(self.toggle_theme)
            layout.addWidget(self.theme_button)

            # テスト用ツリーウィジェット
            self.tree = QTreeWidget()
            self.tree.setHeaderLabel("フォルダ階層テスト")
            self.tree.setAlternatingRowColors(True)  # ゼブラスタイル有効化

            # テストデータ追加
            for i in range(10):
                item = QTreeWidgetItem(self.tree)
                item.setText(0, f"フォルダ{i+1:02d}")

                # 子アイテム追加
                for j in range(3):
                    child = QTreeWidgetItem(item)
                    child.setText(0, f"サブフォルダ{j+1}")

            layout.addWidget(self.tree)

            # テーマ管理初期化
            self.themes = ["dark", "light", "blue", "green", "orange", "yellow"]
            self.current_theme_index = 0

            # テーママネージャー（モックバージョン）
            self.apply_theme_styles()

        def toggle_theme(self):
            """テーマを切り替え"""
            self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)
            current_theme = self.themes[self.current_theme_index]
            self.theme_button.setText(f"テーマ切替: {current_theme}")
            self.apply_theme_styles()

        def apply_theme_styles(self):
            """現在のテーマのスタイルを適用"""
            current_theme = self.themes[self.current_theme_index]

            # 設定ファイルからテーマ色を読み込み
            config_path = project_root / "config" / "theme_styles.json"

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                theme_data = config['theme_styles'][current_theme]
                colors = theme_data['colors']
                template = theme_data['stylesheet_template']

                # テンプレートに色を埋め込み
                stylesheet = template.format(**colors)

                # スタイル適用
                self.setStyleSheet(stylesheet)

                print(f"🎨 {current_theme}テーマ適用完了")
                print(f"   ベース背景: {colors.get('input_background', 'N/A')}")
                print(f"   ゼブラ背景: {colors.get('zebra_alternate', 'N/A')}")
                print(f"   前景色: {colors.get('foreground', 'N/A')}")
                print()

            except Exception as e:
                print(f"❌ テーマ適用エラー: {e}")

    def main():
        """メイン関数"""
        print("🦓 ゼブラスタイル修正後リアルUIテスト開始")
        print("=" * 50)

        app = QApplication(sys.argv)

        # テストウィンドウ表示
        window = ZebraTestWindow()
        window.show()

        print("🖼️  テストウィンドウが表示されました。")
        print("   - 'テーマ切替'ボタンでテーマを変更してください")
        print("   - ツリー項目の交互背景色（ゼブラスタイル）を確認してください")
        print("   - ウィンドウを閉じてテストを終了してください")

        # アプリケーション実行
        app.exec()

        print("🎯 ゼブラスタイルテスト完了")

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("PyQt6環境が必要です。代わりに設定ファイル確認テストを実行します。")

    # 設定ファイルの検証
    config_path = project_root / "config" / "theme_styles.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print("\n📋 修正後設定ファイル検証:")
        print("-" * 40)

        for theme_name in ["dark", "light", "blue", "green"]:
            if theme_name in config['theme_styles']:
                colors = config['theme_styles'][theme_name]['colors']
                zebra_color = colors.get('zebra_alternate', '未設定')
                template = config['theme_styles'][theme_name].get('stylesheet_template', '')
                has_zebra_css = 'alternate-background-color' in template

                print(f"{theme_name:8} | ゼブラ色: {zebra_color:9} | CSS対応: {'✅' if has_zebra_css else '❌'}")

        print("\n✅ 設定ファイル検証完了！")

    except Exception as e:
        print(f"❌ 設定ファイル検証エラー: {e}")
