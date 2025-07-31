#!/usr/bin/env python3
"""
サムネイル表示機能のテストスクリプト

このスクリプトは、サムネイル表示機能が正常に動作するかテストします。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from src.integration.config_manager import ConfigManager
from src.integration.state_manager import StateManager
from src.integration.logging_system import LoggerSystem
from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid

def test_thumbnail_display():
    """サムネイル表示のテスト"""

    app = QApplication(sys.argv)

    # システムコンポーネントを初期化
    logger_system = LoggerSystem()
    config_manager = ConfigManager(logger_system=logger_system)
    state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

    # テストウィンドウを作成
    window = QMainWindow()
    window.setWindowTitle("サムネイル表示テスト")
    window.setGeometry(100, 100, 800, 600)

    # 中央ウィジェット
    central_widget = QWidget()
    window.setCentralWidget(central_widget)

    layout = QVBoxLayout(central_widget)

    # サムネイルグリッドを作成
    thumbnail_grid = OptimizedThumbnailGrid(
        config_manager=config_manager,
        state_manager=state_manager,
        logger_system=logger_system
    )

    layout.addWidget(thumbnail_grid)

    # テスト用画像ファイルのパス
    test_folder = Path.home() / "Samples"

    if test_folder.exists():
        # 画像ファイルを検索
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        image_files = []

        for ext in image_extensions:
            image_files.extend(test_folder.glob(f"*{ext}"))
            image_files.extend(test_folder.glob(f"*{ext.upper()}"))

        print(f"テスト用画像ファイル: {len(image_files)}個")
        for img in image_files:
            print(f"  - {img.name}")

        if image_files:
            # サムネイルグリッドに画像を設定
            thumbnail_grid.set_image_list(image_files)
            print("サムネイル表示を開始しました")
        else:
            print("テスト用画像ファイルが見つかりませんでした")
    else:
        print(f"テストフォルダが見つかりません: {test_folder}")

    # ウィンドウを表示
    window.show()

    print("テストウィンドウが表示されました。ウィンドウを閉じるとテストが終了します。")

    # アプリケーションを実行
    sys.exit(app.exec())

if __name__ == "__main__":
    test_thumbnail_display()
