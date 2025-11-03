#!/usr/bin/env python3
"""
ブレッドクラムアドレスバー統合テスト

修正されたブレッドクラム統合が正しく動作するかテストします。
"""

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_breadcrumb_import():
    """ブレッドクラムライブラリのインポートテスト"""
    print("🔍 ブレッドクラムライブラリのインポートテスト...")

    try:
        from breadcrumb_addressbar import BreadcrumbAddressBar

        print("✅ breadcrumb_addressbar.BreadcrumbAddressBar インポート成功")

        # メソッドの存在確認
        methods = ["setPath", "getPath", "pathChanged", "folderSelected"]
        for method in methods:
            if hasattr(BreadcrumbAddressBar, method):
                print(f"✅ {method} メソッド/シグナル存在")
            else:
                print(f"❌ {method} メソッド/シグナル不存在")

        return True
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False


def test_photogeoview_breadcrumb():
    """PhotoGeoViewブレッドクラム統合テスト"""
    print("\n🔍 PhotoGeoViewブレッドクラム統合テスト...")

    try:
        from src.integration.logging_system import LoggerSystem
        from src.integration.services.file_system_watcher import FileSystemWatcher
        from src.ui.breadcrumb_bar import BreadcrumbAddressBar

        print("✅ PhotoGeoViewブレッドクラムモジュール インポート成功")

        # インスタンス作成テスト
        logger_system = LoggerSystem()
        file_watcher = FileSystemWatcher(logger_system=logger_system)
        breadcrumb_bar = BreadcrumbAddressBar(file_watcher, logger_system)

        print("✅ BreadcrumbAddressBar インスタンス作成成功")

        # ウィジェット取得テスト
        widget = breadcrumb_bar.get_widget()
        if widget:
            print("✅ ブレッドクラムウィジェット取得成功")
        else:
            print("⚠️  ブレッドクラムウィジェット取得失敗（フォールバック使用）")

        # パス設定テスト
        test_path = Path.home()
        result = breadcrumb_bar.set_current_path(test_path)
        if result:
            print(f"✅ パス設定成功: {test_path}")
        else:
            print(f"❌ パス設定失敗: {test_path}")

        return True

    except Exception as e:
        print(f"❌ PhotoGeoViewブレッドクラム統合エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


class BreadcrumbTestWindow(QMainWindow):
    """ブレッドクラムテスト用ウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ブレッドクラム統合テスト")
        self.setGeometry(100, 100, 800, 400)

        # メインウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # ステータスラベル
        self.status_label = QLabel("初期化中...")
        layout.addWidget(self.status_label)

        # ブレッドクラム初期化
        self.init_breadcrumb(layout)

        # テストボタン
        test_button = QPushButton("パス変更テスト")
        test_button.clicked.connect(self.test_path_change)
        layout.addWidget(test_button)

        # 自動テスト開始
        QTimer.singleShot(1000, self.run_auto_test)

    def init_breadcrumb(self, layout):
        """ブレッドクラム初期化"""
        try:
            from src.integration.logging_system import LoggerSystem
            from src.integration.services.file_system_watcher import FileSystemWatcher
            from src.ui.breadcrumb_bar import BreadcrumbAddressBar

            self.logger_system = LoggerSystem()
            self.file_watcher = FileSystemWatcher(logger_system=self.logger_system)
            self.breadcrumb_bar = BreadcrumbAddressBar(
                self.file_watcher, self.logger_system
            )

            # ウィジェット取得
            breadcrumb_widget = self.breadcrumb_bar.get_widget()
            if breadcrumb_widget:
                layout.addWidget(breadcrumb_widget)
                self.status_label.setText("✅ ブレッドクラム初期化成功")
            else:
                self.status_label.setText("⚠️  ブレッドクラムウィジェット取得失敗")

            # シグナル接続
            self.breadcrumb_bar.path_changed.connect(self.on_path_changed)
            self.breadcrumb_bar.breadcrumb_error.connect(self.on_breadcrumb_error)

        except Exception as e:
            self.status_label.setText(f"❌ ブレッドクラム初期化エラー: {e}")
            import traceback

            traceback.print_exc()

    def test_path_change(self):
        """パス変更テスト"""
        try:
            test_paths = [
                Path.home(),
                Path.home() / "Documents",
                Path("/"),
                Path.home(),
            ]

            for path in test_paths:
                if path.exists():
                    result = self.breadcrumb_bar.set_current_path(path)
                    print(f"パス変更テスト: {path} -> {'成功' if result else '失敗'}")
                    break
        except Exception as e:
            print(f"パス変更テストエラー: {e}")

    def run_auto_test(self):
        """自動テスト実行"""
        try:
            # 初期パス設定
            home_path = Path.home()
            result = self.breadcrumb_bar.set_current_path(home_path)

            if result:
                self.status_label.setText(f"✅ 自動テスト成功: {home_path}")
            else:
                self.status_label.setText(f"❌ 自動テスト失敗: {home_path}")

        except Exception as e:
            self.status_label.setText(f"❌ 自動テストエラー: {e}")

    def on_path_changed(self, path):
        """パス変更シグナル処理"""
        print(f"📍 パス変更シグナル受信: {path}")

    def on_breadcrumb_error(self, error_type, error_message):
        """ブレッドクラムエラーシグナル処理"""
        print(f"❌ ブレッドクラムエラー [{error_type}]: {error_message}")


def main():
    """メイン関数"""
    print("🚀 ブレッドクラム統合テスト開始")
    print("=" * 50)

    # 基本インポートテスト
    if not test_breadcrumb_import():
        print("❌ 基本インポートテストに失敗しました")
        return 1

    # PhotoGeoView統合テスト
    if not test_photogeoview_breadcrumb():
        print("❌ PhotoGeoView統合テストに失敗しました")
        return 1

    print("\n🎯 GUI統合テスト開始...")

    # GUI統合テスト
    app = QApplication(sys.argv)

    try:
        window = BreadcrumbTestWindow()
        window.show()

        print("✅ GUI統合テスト準備完了")
        print("ウィンドウを閉じるかCtrl+Cでテスト終了")

        return app.exec()

    except Exception as e:
        print(f"❌ GUI統合テストエラー: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
