#!/usr/bin/env python3
"""
テーマスタイルシートデバッグツール

テーマ設定時のスタイルシート生成をデバッグするためのツールです。
- 現在のテーマ状態の確認
- スタイルシート生成のテスト
- テーマ適用の検証

Author: Kiro AI Integration System
"""

import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QLabel,
        QMainWindow,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    from src.integration.config_manager import ConfigManager
    from src.integration.logging_system import LoggerSystem
    from src.integration.state_manager import StateManager

    # テーママネージャーをインポート
    from src.integration.ui.theme_manager import IntegratedThemeManager

except ImportError as e:
    print(f"❌ 必要なモジュールのインポートに失敗しました: {e}")
    print("PySide6とプロジェクトの依存関係を確認してください。")
    sys.exit(1)


class ThemeDebugWindow(QMainWindow):
    """テーマデバッグウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("テーマスタイルシートデバッグツール")
        self.setGeometry(100, 100, 800, 600)

        # ロガーの設定
        self.logger = LoggerSystem()
        # LoggerSystemの初期化（setup_loggingメソッドがない場合の対応）
        logging.basicConfig(level=logging.DEBUG)

        # テーママネージャーの初期化
        try:
            config_manager = ConfigManager()
            state_manager = StateManager(config_manager)

            self.theme_manager = IntegratedThemeManager(
                config_manager=config_manager,
                state_manager=state_manager,
                logger_system=self.logger,
                main_window=self,
            )

            self.logger.info("テーママネージャーが正常に初期化されました")

        except Exception as e:
            self.logger.error(f"テーママネージャーの初期化に失敗: {e}")
            self.theme_manager = None

        self.setup_ui()

    def setup_ui(self):
        """UIの設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # タイトル
        title = QLabel("テーマスタイルシートデバッグツール")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # 現在のテーマ表示
        self.current_theme_label = QLabel("現在のテーマ: 読み込み中...")
        layout.addWidget(self.current_theme_label)

        # テーマ一覧表示
        self.theme_list_label = QLabel("利用可能なテーマ: 読み込み中...")
        layout.addWidget(self.theme_list_label)

        # テーマ適用ボタン
        button_layout = QVBoxLayout()

        self.test_light_button = QPushButton("ライトテーマをテスト")
        self.test_light_button.clicked.connect(lambda: self.test_theme("default"))
        button_layout.addWidget(self.test_light_button)

        self.test_dark_button = QPushButton("ダークテーマをテスト")
        self.test_dark_button.clicked.connect(lambda: self.test_theme("dark"))
        button_layout.addWidget(self.test_dark_button)

        self.debug_button = QPushButton("テーマ状態をデバッグ")
        self.debug_button.clicked.connect(self.debug_theme_status)
        button_layout.addWidget(self.debug_button)

        layout.addLayout(button_layout)

        # ログ表示エリア
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        self.log_display.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_display)

        # 初期状態の更新
        self.update_status()

    def update_status(self):
        """状態の更新"""
        if self.theme_manager:
            try:
                current_theme = self.theme_manager.get_current_theme()
                self.current_theme_label.setText(f"現在のテーマ: {current_theme}")

                available_themes = self.theme_manager.get_available_themes()
                self.theme_list_label.setText(
                    f"利用可能なテーマ ({len(available_themes)}): {', '.join(available_themes)}"
                )

                self.log_display.append("✅ テーママネージャー状態更新完了")

            except Exception as e:
                self.log_display.append(f"❌ 状態更新エラー: {e}")
        else:
            self.current_theme_label.setText("現在のテーマ: テーママネージャー未初期化")
            self.theme_list_label.setText(
                "利用可能なテーマ: テーママネージャー未初期化"
            )

    def test_theme(self, theme_name: str):
        """テーマのテスト"""
        if not self.theme_manager:
            self.log_display.append("❌ テーママネージャーが初期化されていません")
            return

        try:
            self.log_display.append(f"🔄 テーマ '{theme_name}' を適用中...")

            success = self.theme_manager.apply_theme(theme_name)

            if success:
                self.log_display.append(
                    f"✅ テーマ '{theme_name}' の適用に成功しました"
                )
                self.update_status()
            else:
                self.log_display.append(
                    f"❌ テーマ '{theme_name}' の適用に失敗しました"
                )

        except Exception as e:
            self.log_display.append(f"❌ テーマ適用中にエラー: {e}")

    def debug_theme_status(self):
        """テーマ状態のデバッグ"""
        if not self.theme_manager:
            self.log_display.append("❌ テーママネージャーが初期化されていません")
            return

        try:
            self.log_display.append("🔍 テーマ状態をデバッグ中...")

            # テーママネージャーのデバッグメソッドを呼び出し
            self.theme_manager.debug_theme_status()

            self.log_display.append("✅ デバッグ情報をログに出力しました")

        except Exception as e:
            self.log_display.append(f"❌ デバッグ中にエラー: {e}")


def main():
    """メイン関数"""
    app = QApplication(sys.argv)

    # アプリケーションの基本設定
    app.setApplicationName("テーマデバッグツール")
    app.setApplicationVersion("1.0.0")

    # デバッグウィンドウの作成と表示
    window = ThemeDebugWindow()
    window.show()

    # イベントループの開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
