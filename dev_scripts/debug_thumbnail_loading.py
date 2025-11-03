#!/usr/bin/env python3
"""
サムネイル読み込み問題のデバッグスクリプト

OptimizedThumbnailGridの動作を詳細に調査します。

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

    from integration.config_manager import ConfigManager
    from integration.logging_system import LoggerSystem
    from integration.state_manager import StateManager
    from integration.ui.thumbnail_grid import OptimizedThumbnailGrid

except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("必要なモジュールが見つかりません")
    sys.exit(1)


class DebugWindow(QMainWindow):
    """デバッグ用のウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("サムネイル読み込みデバッグ")
        self.setGeometry(100, 100, 800, 600)

        # システム初期化
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.logger_system = LoggerSystem()

        self._setup_ui()

    def _setup_ui(self):
        """UI設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # サムネイルグリッド
        self.thumbnail_grid = OptimizedThumbnailGrid(
            self.config_manager,
            self.state_manager,
            self.logger_system,
            None,  # テーママネージャーなし
        )
        layout.addWidget(self.thumbnail_grid)

        # テスト用の画像を読み込み
        demo_folder = Path("/home/hiro/Samples")
        if demo_folder.exists():
            image_files = list(demo_folder.glob("*.jpg")) + list(
                demo_folder.glob("*.png")
            )
            if image_files:
                print(f"🔍 テスト画像を発見: {len(image_files)}個")
                for img in image_files:
                    print(f"  - {img}")

                # show_loading_stateをテスト
                print("⏳ show_loading_state をテスト中...")
                self.thumbnail_grid.show_loading_state(
                    "デバッグ: フォルダをスキャン中..."
                )

                # 2秒後にset_image_listを呼び出し
                from PySide6.QtCore import QTimer

                QTimer.singleShot(2000, lambda: self._test_set_image_list(image_files))
            else:
                print("❌ テスト画像が見つかりません")
        else:
            print("❌ Samplesフォルダが見つかりません")

    def _test_set_image_list(self, image_files):
        """set_image_listをテスト"""
        print(f"📋 set_image_list をテスト中: {len(image_files)}個の画像")
        self.thumbnail_grid.set_image_list(image_files)


def main():
    """メイン処理"""
    print("🔍 サムネイル読み込みデバッグ開始")

    app = QApplication(sys.argv)

    try:
        window = DebugWindow()
        window.show()

        print("✅ デバッグウィンドウを表示しました")
        print("📋 確認項目:")
        print("• show_loading_stateが正しく表示されるか")
        print("• set_image_listが正しく動作するか")
        print("• サムネイルが実際に読み込まれるか")

        return app.exec()

    except Exception as e:
        print(f"❌ デバッグ実行エラー: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
