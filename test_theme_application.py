#!/usr/bin/env python3
"""
テーマ適用の実際のテスト

実際のPhotoGeoViewアプリケーションでテーマ適用をテストします。

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit, QHBoxLayout
    from PySide6.QtCore import Qt

    # 統合システムをインポート
    from src.integration.config_manager import ConfigManager
    from src.integration.state_manager import StateManager
    from src.integration.logging_system import LoggerSystem
    from src.integration.ui.theme_manager import IntegratedThemeManager

except ImportError as e:
    print(f"❌ 必要なモジュールのインポートに失敗しました: {e}")
    print("PySide6とプロジェクトの依存関係を確認してください。")
    sys.exit(1)

class ThemeTestWindow(QMainWindow):
    """テーマテスト用ウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhotoGeoView テーマ適用テスト")
        self.setGeometry(100, 100, 1000, 700)

        # テーママネージャーのインスタンスを作成
        try:
            logger_system = LoggerSystem()
            config_manager = ConfigManager(logger_system=logger_system)
            state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

            self.theme_manager = IntegratedThemeManager(
                config_manager=config_manager,
                state_manager=state_manager,
                logger_system=logger_system,
                main_window=self
            )
            print("✅ テーママネージャーが正常に初期化されました")
        except Exception as e:
            print(f"❌ テーママネージャーの初期化に失敗: {e}")
            import traceback
            print(f"詳細: {traceback.format_exc()}")
            self.theme_manager = None

        self.setup_ui()

        # 初期テーマを適用
        if self.theme_manager:
            self.apply_theme("default")

    def setup_ui(self):
        """UIの設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # タイトル
        title = QLabel("PhotoGeoView テーマ適用テスト")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # 現在のテーマ表示
        self.current_theme_label = QLabel("現在のテーマ: 読み込み中...")
        self.current_theme_label.setStyleSheet("font-size: 16px; margin: 10px;")
        layout.addWidget(self.current_theme_label)

        # テーマ切り替えボタン
        button_layout = QHBoxLayout()

        themes_to_test = [
            ("default", "デフォルト"),
            ("dark", "ダーク"),
            ("light", "ライト"),
            ("blue", "ブルー"),
            ("green", "グリーン"),
            ("high_contrast", "ハイコントラスト")
        ]

        for theme_id, theme_name in themes_to_test:
            button = QPushButton(f"{theme_name}テーマ")
            button.clicked.connect(lambda checked, t=theme_id: self.apply_theme(t))
            button.setMinimumHeight(40)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        # サンプルUI要素
        sample_layout = QVBoxLayout()

        # サンプルラベル
        sample_label = QLabel("これはサンプルテキストです。テーマが適用されると色が変わります。")
        sample_label.setStyleSheet("font-size: 14px; padding: 10px; border: 1px solid gray; margin: 5px;")
        sample_layout.addWidget(sample_label)

        # サンプルボタン
        sample_button = QPushButton("サンプルボタン")
        sample_button.setMinimumHeight(35)
        sample_layout.addWidget(sample_button)

        # サンプルテキストエリア
        self.sample_text = QTextEdit()
        self.sample_text.setPlainText("これはサンプルテキストエリアです。\nテーマが適用されると背景色とテキスト色が変わります。")
        self.sample_text.setMaximumHeight(100)
        sample_layout.addWidget(self.sample_text)

        layout.addLayout(sample_layout)

        # ログ表示エリア
        log_label = QLabel("テーマ適用ログ:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(log_label)

        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        self.log_display.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_display)

    def apply_theme(self, theme_name: str):
        """テーマを適用"""
        if not self.theme_manager:
            self.log_display.append("❌ テーママネージャーが利用できません")
            return

        try:
            self.log_display.append(f"🔄 テーマ '{theme_name}' を適用中...")

            # テーマを適用
            success = self.theme_manager.apply_theme(theme_name)

            if success:
                self.log_display.append(f"✅ テーマ '{theme_name}' の適用に成功しました")
                self.current_theme_label.setText(f"現在のテーマ: {theme_name}")

                # テーマ情報を表示
                theme_config = self.theme_manager.get_theme_config(theme_name)
                if theme_config:
                    colors = theme_config.get('color_scheme', {})
                    self.log_display.append(f"   背景色: {colors.get('background', 'N/A')}")
                    self.log_display.append(f"   テキスト色: {colors.get('foreground', 'N/A')}")
                    self.log_display.append(f"   プライマリ色: {colors.get('primary', 'N/A')}")

            else:
                self.log_display.append(f"❌ テーマ '{theme_name}' の適用に失敗しました")

        except Exception as e:
            self.log_display.append(f"❌ テーマ適用中にエラー: {e}")
            import traceback
            self.log_display.append(f"詳細: {traceback.format_exc()}")

def main():
    """メイン関数"""
    app = QApplication(sys.argv)

    # アプリケーションの基本設定
    app.setApplicationName("PhotoGeoView テーマテスト")
    app.setApplicationVersion("1.0.0")

    # テストウィンドウの作成と表示
    window = ThemeTestWindow()
    window.show()

    print("🎨 テーマテストウィンドウを表示しました")
    print("各テーマボタンをクリックしてテーマの変化を確認してください")

    # イベントループの開始
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
