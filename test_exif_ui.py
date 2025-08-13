#!/usr/bin/env python3
"""
EXIF UI表示テスト

EXIFパネルが正常に表示されるかをテストします。
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from integration.config_manager import ConfigManager
    from integration.logging_system import LoggerSystem
    from integration.state_manager import StateManager
    from integration.ui.exif_panel import EXIFPanel
    print("✅ モジュールのインポートに成功しました")
except ImportError as e:
    print(f"❌ モジュールのインポートに失敗しました: {e}")
    sys.exit(1)

class TestWindow(QMainWindow):
    """テスト用のメインウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXIF Panel Test")
        self.setGeometry(100, 100, 800, 600)

        # 設定とロガーを初期化
        self.config_manager = ConfigManager()
        self.logger_system = LoggerSystem()
        self.state_manager = StateManager(self.config_manager, self.logger_system)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QVBoxLayout(central_widget)

        # EXIFパネルを作成
        self.exif_panel = EXIFPanel(
            self.config_manager,
            self.state_manager,
            self.logger_system
        )

        layout.addWidget(self.exif_panel)

        # テスト用の画像を設定
        self.test_images()

    def test_images(self):
        """テスト用の画像を設定"""
        test_dirs = [
            Path("demo_data"),
            Path("/home/hiro/Samples"),
            Path("assets"),
            Path("examples"),
        ]

        image_extensions = [".jpg", ".jpeg", ".png", ".tiff", ".tif"]

        for test_dir in test_dirs:
            if test_dir.exists():
                for ext in image_extensions:
                    images = list(test_dir.glob(f"*{ext}"))
                    if images:
                        test_image = images[0]
                        print(f"📷 テスト画像を設定: {test_image}")
                        self.exif_panel.set_image(test_image)
                        return

        print("⚠️ テスト用の画像が見つかりませんでした")

def main():
    """メイン関数"""
    print("🚀 EXIF UI表示テストを開始します")

    app = QApplication(sys.argv)

    # テストウィンドウを作成
    window = TestWindow()
    window.show()

    print("✅ テストウィンドウを表示しました")
    print("💡 ウィンドウを閉じるとテストが終了します")

    # アプリケーションを実行
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
