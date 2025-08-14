#!/usr/bin/env python3
"""
テーマ背景修正のテストスクリプト

修正されたサムネイルグリッドとEXIF panelのテーマ適用をテストします。

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout
    from PySide6.QtCore import Qt

    from integration.config_manager import ConfigManager
    from integration.state_manager import StateManager
    from integration.logging_system import LoggerSystem
    from integration.theme_manager import ThemeManager
    from integration.ui.simple_thumbnail_grid import SimpleThumbnailGrid
    from integration.ui.exif_panel import EXIFPanel

except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("必要なモジュールが見つかりません")
    sys.exit(1)

class ThemeTestWindow(QMainWindow):
    """テーマテスト用のウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("テーマ背景修正テスト")
        self.setGeometry(100, 100, 1200, 800)

        # システム初期化
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.logger_system = LoggerSystem()
        self.theme_manager = ThemeManager(self.config_manager, self.logger_system)

        self._setup_ui()

        # ダークテーマを適用してテスト
        self.theme_manager.set_theme("dark")

    def _setup_ui(self):
        """UI設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        # サムネイルグリッド
        self.thumbnail_grid = SimpleThumbnailGrid(
            self.config_manager,
            self.state_manager,
            self.logger_system,
            self.theme_manager
        )
        layout.addWidget(self.thumbnail_grid, 2)

        # EXIF panel
        self.exif_panel = EXIFPanel(
            self.config_manager,
            self.state_manager,
            self.logger_system,
            self.theme_manager
        )
        layout.addWidget(self.exif_panel, 1)

        # テスト用の画像を読み込み
        demo_folder = Path("demo_data")
        if demo_folder.exists():
            self.thumbnail_grid.load_images_from_folder(demo_folder)

def main():
    """メイン処理"""
    print("🎨 テーマ背景修正テスト開始")

    app = QApplication(sys.argv)

    try:
        window = ThemeTestWindow()
        window.show()

        print("✅ テストウィンドウを表示しました")
        print("📋 確認項目:")
        print("• サムネイルグリッドの背景がテーマに追随しているか")
        print("• EXIF panelの背景がテーマに追随しているか")
        print("• 位置情報パネルと同様の見た目になっているか")

        return app.exec()

    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
