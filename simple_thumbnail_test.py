#!/usr/bin/env python3
"""
シンプルなサムネイル表示テスト

基本的なサムネイル表示機能のみをテストします。
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QGridLayout, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

def create_simple_thumbnail_grid():
    """シンプルなサムネイルグリッドを作成"""

    app = QApplication(sys.argv)

    # メインウィンドウ
    window = QMainWindow()
    window.setWindowTitle("シンプルサムネイル表示テスト")
    window.setGeometry(100, 100, 800, 600)

    # スクロールエリア
    scroll_area = QScrollArea()
    window.setCentralWidget(scroll_area)

    # グリッドウィジェット
    grid_widget = QWidget()
    scroll_area.setWidget(grid_widget)
    scroll_area.setWidgetResizable(True)

    # グリッドレイアウト
    grid_layout = QGridLayout(grid_widget)
    grid_layout.setSpacing(10)

    # テスト用画像ファイル
    test_folder = Path.home() / "Samples"
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    image_files = []

    for ext in image_extensions:
        image_files.extend(test_folder.glob(f"*{ext}"))
        image_files.extend(test_folder.glob(f"*{ext.upper()}"))

    print(f"見つかった画像ファイル: {len(image_files)}個")

    # サムネイルを作成
    thumbnail_size = 150
    columns = 4
    row = 0
    col = 0

    for image_path in image_files:
        try:
            # 画像を読み込み
            pixmap = QPixmap(str(image_path))

            if not pixmap.isNull():
                # サムネイルサイズにスケール
                scaled_pixmap = pixmap.scaled(
                    thumbnail_size, thumbnail_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                # ラベルを作成
                label = QLabel()
                label.setPixmap(scaled_pixmap)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #ddd;
                        border-radius: 4px;
                        padding: 4px;
                        background-color: white;
                    }
                    QLabel:hover {
                        border-color: #007acc;
                    }
                """)

                # ツールチップにファイル名を設定
                label.setToolTip(image_path.name)

                # グリッドに追加
                grid_layout.addWidget(label, row, col)

                print(f"サムネイル作成成功: {image_path.name}")

                # 次の位置を計算
                col += 1
                if col >= columns:
                    col = 0
                    row += 1

            else:
                print(f"画像読み込み失敗: {image_path.name}")

        except Exception as e:
            print(f"エラー: {image_path.name} - {e}")

    # ウィンドウを表示
    window.show()

    print("サムネイル表示テスト完了。ウィンドウを閉じて終了してください。")

    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    create_simple_thumbnail_grid()
