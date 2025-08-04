#!/usr/bin/env python3
"""
テーマ選択UIデモスクリプト

新しいテーマ選択UI（theme_selector.py）とSimpleThemeManagerの連携をデモします。
- プレビュー機能付きテーマ選択ダイアログ
- トグルボタンでのテーマ切り替え
- リアルタイムプレビュー機能

使用方法:
    python examples/demo_theme_selector.py

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.ui.theme_manager_simple import SimpleThemeManager
from src.ui.theme_selector import ThemeSelectionDialog


class ThemeSelectorDemo(QMainWindow):
    """テーマ選択UIデモウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("テーマ選択UI デモ")
        self.resize(800, 600)

        # システムコンポーネントの初期化
        self.logger_system = LoggerSystem()
        self.config_manager = ConfigManager(logger_system=self.logger_system)
        self.theme_manager = SimpleThemeManager(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )

        # 選択されたテーマの管理
        self.selected_themes = []
        self.current_theme_index = 0

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """UIの設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # タイトル
        title_label = QLabel("🎨 テーマ選択UI デモ")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 説明
        description_label = QLabel(
            "新しいテーマ選択UIの機能をテストできます。\n"
            "下のボタンでテーマ選択ダイアログを開き、プレビュー機能をお試しください。"
        )
        description_label.setStyleSheet("font-size: 14px; color: gray; margin-bottom: 20px;")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description_label)

        # 現在のテーマ表示
        self.current_theme_label = QLabel("現在のテーマ: 読み込み中...")
        self.current_theme_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; border: 2px solid #ccc; border-radius: 5px;")
        self.current_theme_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_theme_label)

        # ボタンエリア
        button_layout = QHBoxLayout()

        # テーマ選択ダイアログを開くボタン
        self.open_dialog_button = QPushButton("🎨 テーマ設定")
        self.open_dialog_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.open_dialog_button.clicked.connect(self.open_theme_dialog)
        button_layout.addWidget(self.open_dialog_button)

        # テーマ切り替えボタン
        self.theme_toggle_button = QPushButton("テーマ切替")
        self.theme_toggle_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.theme_toggle_button.clicked.connect(self.toggle_theme)
        button_layout.addWidget(self.theme_toggle_button)

        layout.addLayout(button_layout)

        # ログ表示エリア
        log_label = QLabel("📝 ログ:")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(self.log_text)

        # 初期状態の更新
        self.update_current_theme_display()
        self.update_toggle_button_text()

    def setup_connections(self):
        """シグナル接続の設定"""
        # テーママネージャーのシグナル
        self.theme_manager.theme_changed.connect(self.on_theme_changed)
        self.theme_manager.theme_applied.connect(self.on_theme_applied)
        self.theme_manager.theme_error.connect(self.on_theme_error)

    def update_current_theme_display(self):
        """現在のテーマ表示を更新"""
        current_theme = self.theme_manager.get_current_theme()
        self.current_theme_label.setText(f"現在のテーマ: {current_theme}")
        self.log_message(f"現在のテーマ: {current_theme}")

    def open_theme_dialog(self):
        """テーマ選択ダイアログを開く"""
        self.log_message("テーマ選択ダイアログを開いています...")
        dialog = ThemeSelectionDialog(self.theme_manager, self)
        dialog.theme_applied.connect(self.on_themes_applied_from_dialog)
        dialog.exec()

    def toggle_theme(self):
        """選択されたテーマを循環切り替え"""
        if not self.selected_themes:
            self.log_message("選択されたテーマがありません。テーマ設定でテーマを選択してください。")
            return

        if len(self.selected_themes) == 1:
            self.log_message(f"選択されたテーマは1つだけです: {self.selected_themes[0]}")
            return

        # 次のテーマに切り替え
        self.current_theme_index = (self.current_theme_index + 1) % len(self.selected_themes)
        next_theme = self.selected_themes[self.current_theme_index]
        
        self.log_message(f"テーマを切り替え: {next_theme}")
        self.theme_manager.apply_theme(next_theme)
        self.update_toggle_button_text()

    def update_toggle_button_text(self):
        """テーマ切り替えボタンのテキストを更新"""
        if self.selected_themes:
            current_theme = self.selected_themes[self.current_theme_index]
            self.theme_toggle_button.setText(f"テーマ切替: {current_theme}")
        else:
            self.theme_toggle_button.setText("テーマ切替")

    def on_themes_applied_from_dialog(self, theme_list: list):
        """ダイアログからテーマが適用された時の処理"""
        self.selected_themes = theme_list
        self.current_theme_index = 0
        
        if self.selected_themes:
            # 最初のテーマを適用
            first_theme = self.selected_themes[0]
            self.log_message(f"選択されたテーマ: {self.selected_themes}")
            self.log_message(f"最初のテーマを適用: {first_theme}")
            self.theme_manager.apply_theme(first_theme)
            self.update_toggle_button_text()
        else:
            self.log_message("テーマが選択されていません")
            self.update_toggle_button_text()





    def on_theme_changed(self, old_theme: str, new_theme: str):
        """テーマが変更された時の処理"""
        self.log_message(f"テーマが変更されました: {old_theme} → {new_theme}")
        self.update_current_theme_display()

    def on_theme_applied(self, theme_name: str):
        """テーマが適用された時の処理"""
        self.log_message(f"テーマが適用されました: {theme_name}")
        self.update_current_theme_display()

    def on_theme_error(self, theme_name: str, error_message: str):
        """テーマエラーが発生した時の処理"""
        self.log_message(f"テーマエラー ({theme_name}): {error_message}")

    def log_message(self, message: str):
        """ログメッセージを表示"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)

        # ログテキストを最下部にスクロール
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """メイン関数"""
    print("🎨 テーマ選択UI デモを起動中...")

    app = QApplication(sys.argv)
    app.setApplicationName("Theme Selector Demo")
    app.setApplicationVersion("1.0.0")

    # デモウィンドウを作成・表示
    demo_window = ThemeSelectorDemo()
    demo_window.show()

    print("✅ デモウィンドウが表示されました")
    print("📋 機能:")
    print("  - トグルボタンでテーマ切り替え")
    print("  - 詳細選択ボタンでプレビュー付きダイアログ")
    print("  - 手動テストボタンでダイアログとテーマ循環")
    print("  - ログエリアで動作確認")

    # Qtイベントループを開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
