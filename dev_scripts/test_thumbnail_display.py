#!/usr/bin/env python3
"""
サムネイル表示機能のパフォーマンステストスクリプト

このスクリプトは、サムネイル表示機能のパフォーマンスを測定し、
問題箇所を特定します。
"""

import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.state_manager import StateManager
from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid


def test_thumbnail_performance():
    """サムネイル表示のパフォーマンステスト"""

    app = QApplication(sys.argv)

    # システムコンポーネントを初期化
    logger_system = LoggerSystem()
    config_manager = ConfigManager(logger_system=logger_system)
    state_manager = StateManager(
        config_manager=config_manager, logger_system=logger_system
    )

    # テストウィンドウを作成
    window = QMainWindow()
    window.setWindowTitle("サムネイルパフォーマンステスト")
    window.setGeometry(100, 100, 1000, 800)

    # 中央ウィジェット
    central_widget = QWidget()
    window.setCentralWidget(central_widget)

    layout = QVBoxLayout(central_widget)

    # パフォーマンス情報表示用ラベル
    performance_label = QLabel("パフォーマンス情報: 準備中...")
    layout.addWidget(performance_label)

    # テスト用ボタン
    test_button = QPushButton("パフォーマンステスト実行")
    layout.addWidget(test_button)

    # サムネイルグリッドを作成
    thumbnail_grid = OptimizedThumbnailGrid(
        config_manager=config_manager,
        state_manager=state_manager,
        logger_system=logger_system,
    )

    layout.addWidget(thumbnail_grid)

    # テスト用画像ファイルのパス
    test_folder = Path.home() / "Samples"

    def run_performance_test():
        """パフォーマンステストを実行"""
        if not test_folder.exists():
            performance_label.setText("テストフォルダが見つかりません")
            return

        # 画像ファイルを検索
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
        image_files = []

        for ext in image_extensions:
            image_files.extend(test_folder.glob(f"*{ext}"))
            image_files.extend(test_folder.glob(f"*{ext.upper()}"))

        if not image_files:
            performance_label.setText("テスト用画像ファイルが見つかりません")
            return

        performance_label.setText(
            f"テスト用画像ファイル: {len(image_files)}個\n"
            f"ファイル一覧: {', '.join([img.name for img in image_files])}"
        )

        # パフォーマンス測定開始
        start_time = time.time()

        # サムネイルグリッドに画像を設定
        thumbnail_grid.set_image_list(image_files)

        # パフォーマンス測定用タイマー
        def check_performance():
            elapsed = time.time() - start_time
            loaded_count = getattr(thumbnail_grid, "loaded_count", 0)
            total_count = getattr(thumbnail_grid, "total_count", 0)

            performance_label.setText(
                f"経過時間: {elapsed:.2f}秒\n"
                f"読み込み済み: {loaded_count}/{total_count}\n"
                f"読み込み速度: {loaded_count / elapsed:.2f}枚/秒"
                if elapsed > 0
                else "計算中..."
            )

            # まだ読み込み中の場合は継続
            if loaded_count < total_count:
                QTimer.singleShot(100, check_performance)
            else:
                final_time = time.time() - start_time
                performance_label.setText(
                    f"完了！\n"
                    f"総時間: {final_time:.2f}秒\n"
                    f"読み込み済み: {loaded_count}/{total_count}\n"
                    f"平均速度: {loaded_count / final_time:.2f}枚/秒"
                )

        # パフォーマンスチェック開始
        QTimer.singleShot(100, check_performance)

    # ボタンクリックでテスト実行
    test_button.clicked.connect(run_performance_test)

    # ウィンドウを表示
    window.show()

    print("パフォーマンステストウィンドウが表示されました。")
    print("「パフォーマンステスト実行」ボタンをクリックしてテストを開始してください。")

    # アプリケーションを実行
    sys.exit(app.exec())


if __name__ == "__main__":
    test_thumbnail_performance()
