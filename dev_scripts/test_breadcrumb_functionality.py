#!/usr/bin/env python3
"""
ブレッドクラム機能テスト

PhotoGeoViewに統合されたブレッドクラムアドレスバーの機能をテストします。
"""

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class BreadcrumbFunctionalityTestWindow(QMainWindow):
    """ブレッドクラム機能テスト用ウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ブレッドクラム機能テスト")
        self.setGeometry(100, 100, 1000, 600)

        # メインウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # タイトル
        title = QLabel("PhotoGeoView ブレッドクラム機能テスト")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # ステータス表示
        self.status_label = QLabel("初期化中...")
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; border-radius: 5px;"
        )
        layout.addWidget(self.status_label)

        # ブレッドクラム初期化
        self.init_breadcrumb(layout)

        # テストボタン群
        self.create_test_buttons(layout)

        # ログ表示
        self.log_label = QLabel("ログ: テスト開始")
        self.log_label.setStyleSheet(
            "padding: 10px; background-color: #f8f9fa; border-radius: 5px; font-family: monospace;"
        )
        self.log_label.setWordWrap(True)
        layout.addWidget(self.log_label)

        # 自動テスト開始
        QTimer.singleShot(1000, self.run_initial_tests)

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
                breadcrumb_widget.setMinimumHeight(50)
                layout.addWidget(breadcrumb_widget)
                self.status_label.setText("✅ ブレッドクラム初期化成功")
            else:
                self.status_label.setText("❌ ブレッドクラムウィジェット取得失敗")

            # シグナル接続
            self.breadcrumb_bar.path_changed.connect(self.on_path_changed)
            self.breadcrumb_bar.segment_clicked.connect(self.on_segment_clicked)
            self.breadcrumb_bar.breadcrumb_error.connect(self.on_breadcrumb_error)

        except Exception as e:
            self.status_label.setText(f"❌ ブレッドクラム初期化エラー: {e}")
            import traceback

            traceback.print_exc()

    def create_test_buttons(self, layout):
        """テストボタン群を作成"""
        button_layout = QHBoxLayout()

        # ホームディレクトリテスト
        home_button = QPushButton("🏠 ホームディレクトリ")
        home_button.clicked.connect(self.test_home_directory)
        button_layout.addWidget(home_button)

        # サンプルディレクトリテスト
        samples_button = QPushButton("📁 サンプルディレクトリ")
        samples_button.clicked.connect(self.test_samples_directory)
        button_layout.addWidget(samples_button)

        # ルートディレクトリテスト
        root_button = QPushButton("💻 ルートディレクトリ")
        root_button.clicked.connect(self.test_root_directory)
        button_layout.addWidget(root_button)

        # パス情報表示テスト
        info_button = QPushButton("ℹ️ パス情報表示")
        info_button.clicked.connect(self.show_path_info)
        button_layout.addWidget(info_button)

        layout.addLayout(button_layout)

    def run_initial_tests(self):
        """初期テスト実行"""
        try:
            # 初期パス設定
            home_path = Path.home()
            result = self.breadcrumb_bar.set_current_path(home_path)

            if result:
                self.log_message(f"✅ 初期パス設定成功: {home_path}")
                self.status_label.setText(
                    "✅ 初期テスト成功 - ブレッドクラム機能が利用可能です"
                )
            else:
                self.log_message(f"❌ 初期パス設定失敗: {home_path}")
                self.status_label.setText("❌ 初期テスト失敗")

        except Exception as e:
            self.log_message(f"❌ 初期テストエラー: {e}")
            self.status_label.setText(f"❌ 初期テストエラー: {e}")

    def test_home_directory(self):
        """ホームディレクトリテスト"""
        try:
            home_path = Path.home()
            result = self.breadcrumb_bar.set_current_path(home_path)
            self.log_message(
                f"🏠 ホームディレクトリテスト: {home_path} -> {'成功' if result else '失敗'}"
            )
        except Exception as e:
            self.log_message(f"❌ ホームディレクトリテストエラー: {e}")

    def test_samples_directory(self):
        """サンプルディレクトリテスト"""
        try:
            samples_path = Path.home() / "Samples"
            if samples_path.exists():
                result = self.breadcrumb_bar.set_current_path(samples_path)
                self.log_message(
                    f"📁 サンプルディレクトリテスト: {samples_path} -> {'成功' if result else '失敗'}"
                )
            else:
                # 存在しない場合はDocumentsを試す
                docs_path = Path.home() / "Documents"
                if docs_path.exists():
                    result = self.breadcrumb_bar.set_current_path(docs_path)
                    self.log_message(
                        f"📁 Documentsディレクトリテスト: {docs_path} -> {'成功' if result else '失敗'}"
                    )
                else:
                    self.log_message("⚠️ テスト用ディレクトリが見つかりません")
        except Exception as e:
            self.log_message(f"❌ サンプルディレクトリテストエラー: {e}")

    def test_root_directory(self):
        """ルートディレクトリテスト"""
        try:
            root_path = Path("/")
            result = self.breadcrumb_bar.set_current_path(root_path)
            self.log_message(
                f"💻 ルートディレクトリテスト: {root_path} -> {'成功' if result else '失敗'}"
            )
        except Exception as e:
            self.log_message(f"❌ ルートディレクトリテストエラー: {e}")

    def show_path_info(self):
        """パス情報表示"""
        try:
            # ブレッドクラムの現在の状態を表示
            current_state = self.breadcrumb_bar.current_state
            current_path = current_state.current_path
            segments = current_state.breadcrumb_segments

            info = f"📍 現在のパス: {current_path}\n"
            info += f"📋 セグメント数: {len(segments)}\n"

            if segments:
                info += "🔗 セグメント一覧:\n"
                for i, segment in enumerate(segments):
                    info += f"  {i + 1}. {segment.display_name} ({segment.path})\n"

            self.log_message(info)

        except Exception as e:
            self.log_message(f"❌ パス情報表示エラー: {e}")

    def on_path_changed(self, path):
        """パス変更シグナル処理"""
        self.log_message(f"📍 パス変更シグナル: {path}")

    def on_segment_clicked(self, index, path):
        """セグメントクリックシグナル処理"""
        self.log_message(f"🔗 セグメントクリック: インデックス={index}, パス={path}")

    def on_breadcrumb_error(self, error_type, error_message):
        """ブレッドクラムエラーシグナル処理"""
        self.log_message(f"❌ ブレッドクラムエラー [{error_type}]: {error_message}")

    def log_message(self, message):
        """ログメッセージを表示"""
        current_text = self.log_label.text()
        if current_text == "ログ: テスト開始":
            new_text = f"ログ:\n{message}"
        else:
            new_text = f"{current_text}\n{message}"

        # ログが長くなりすぎないように制限
        lines = new_text.split("\n")
        if len(lines) > 20:
            lines = lines[-20:]
            new_text = "\n".join(lines)

        self.log_label.setText(new_text)
        print(f"[ブレッドクラムテスト] {message}")


def main():
    """メイン関数"""
    print("🚀 ブレッドクラム機能テスト開始")

    app = QApplication(sys.argv)

    try:
        window = BreadcrumbFunctionalityTestWindow()
        window.show()

        print("✅ ブレッドクラム機能テスト準備完了")
        print("ウィンドウを閉じるかCtrl+Cでテスト終了")

        return app.exec()

    except Exception as e:
        print(f"❌ ブレッドクラム機能テストエラー: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
