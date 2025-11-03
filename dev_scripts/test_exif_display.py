#!/usr/bin/env python3
"""
EXIF表示の動作確認スクリプト
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

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


class EXIFTestWindow(QMainWindow):
    """EXIF表示テスト用のウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXIF Display Test")
        self.setGeometry(100, 100, 600, 800)

        # 設定とロガーを初期化
        self.config_manager = ConfigManager()
        self.logger_system = LoggerSystem()
        self.state_manager = StateManager(self.config_manager, self.logger_system)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QVBoxLayout(central_widget)

        # ステータスラベル
        self.status_label = QLabel("EXIF表示テスト開始")
        self.status_label.setStyleSheet(
            "font-weight: bold; padding: 10px; background-color: #f0f0f0;"
        )
        layout.addWidget(self.status_label)

        # EXIFパネルを作成
        try:
            self.exif_panel = EXIFPanel(
                self.config_manager, self.state_manager, self.logger_system
            )
            layout.addWidget(self.exif_panel)
            self.status_label.setText("✅ EXIFパネルを作成しました")

            # テスト用の画像を設定
            self.test_images()

        except Exception as e:
            self.status_label.setText(f"❌ EXIFパネルの作成に失敗: {e}")
            print(f"EXIFパネル作成エラー: {e}")
            import traceback

            traceback.print_exc()

    def test_images(self):
        """テスト用の画像を設定"""
        test_dirs = [
            Path("/home/hiro/Samples"),
            Path("demo_data"),
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
                        self.status_label.setText(f"📷 テスト画像: {test_image.name}")

                        try:
                            self.exif_panel.set_image(test_image)
                            self.status_label.setText(
                                f"✅ EXIF情報を読み込みました: {test_image.name}"
                            )
                        except Exception as e:
                            self.status_label.setText(f"❌ EXIF読み込みエラー: {e}")
                            print(f"EXIF読み込みエラー: {e}")

                        return

        self.status_label.setText("⚠️ テスト用の画像が見つかりませんでした")
        print("⚠️ テスト用の画像が見つかりませんでした")


def main():
    """メイン関数"""
    print("🚀 EXIF表示テストを開始します")

    app = QApplication(sys.argv)

    # テストウィンドウを作成
    window = EXIFTestWindow()
    window.show()

    print("✅ テストウィンドウを表示しました")
    print("💡 ウィンドウを閉じるとテストが終了します")

    # アプリケーションを実行
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
