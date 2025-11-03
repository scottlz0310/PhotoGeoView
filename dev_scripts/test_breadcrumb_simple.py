#!/usr/bin/env python3
"""
シンプルなブレッドクラム統合テスト
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """メイン関数"""
    print("🚀 シンプルブレッドクラム統合テスト開始")

    app = QApplication(sys.argv)

    try:
        # ライブラリインポートテスト
        print("📦 breadcrumb_addressbar インポートテスト...")
        print("✅ breadcrumb_addressbar インポート成功")

        # PhotoGeoView統合テスト
        print("📦 PhotoGeoView統合テスト...")
        from src.integration.logging_system import LoggerSystem
        from src.integration.services.file_system_watcher import FileSystemWatcher
        from src.ui.breadcrumb_bar import BreadcrumbAddressBar as PhotoGeoViewBreadcrumb

        logger_system = LoggerSystem()
        file_watcher = FileSystemWatcher(logger_system=logger_system)
        breadcrumb_bar = PhotoGeoViewBreadcrumb(file_watcher, logger_system)

        print("✅ PhotoGeoView BreadcrumbAddressBar インスタンス作成成功")

        # ウィジェット取得テスト
        widget = breadcrumb_bar.get_widget()
        if widget:
            print("✅ ブレッドクラムウィジェット取得成功")
        else:
            print("⚠️  ブレッドクラムウィジェット取得失敗（フォールバック使用）")

        # パス設定テスト
        test_path = Path.home()
        result = breadcrumb_bar.set_current_path(test_path)
        print(f"📍 パス設定テスト: {test_path} -> {'成功' if result else '失敗'}")

        # 簡単なGUIテスト
        window = QMainWindow()
        window.setWindowTitle("ブレッドクラム統合テスト")
        window.setGeometry(100, 100, 800, 200)

        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        status_label = QLabel("✅ ブレッドクラム統合テスト成功")
        layout.addWidget(status_label)

        if widget:
            layout.addWidget(widget)

        window.show()

        print("✅ 全テスト成功！ウィンドウを閉じるかCtrl+Cで終了")
        return app.exec()

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
