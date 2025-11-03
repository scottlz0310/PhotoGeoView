#!/usr/bin/env python3
"""
UIコンポーネントのテーマ統合テスト

EXIFパネルとサムネイルグリッドのテーマ追随をテストします。

Author: Kiro AI Integration System
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    # 統合システムをインポート
    from src.integration.config_manager import ConfigManager
    from src.integration.logging_system import LoggerSystem
    from src.integration.state_manager import StateManager
    from src.integration.ui.exif_panel import EXIFPanel
    from src.integration.ui.simple_thumbnail_grid import SimpleThumbnailGrid
    from src.integration.ui.theme_manager import IntegratedThemeManager

except ImportError as e:
    print(f"❌ 必要なモジュールのインポートに失敗しました: {e}")
    print("PySide6とプロジェクトの依存関係を確認してください。")
    sys.exit(1)


class UIThemeIntegrationTestWindow(QMainWindow):
    """UIコンポーネントのテーマ統合テスト用ウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UIコンポーネント テーマ統合テスト")
        self.setGeometry(100, 100, 1200, 800)

        # システムコンポーネントの初期化
        try:
            logger_system = LoggerSystem()
            config_manager = ConfigManager(logger_system=logger_system)
            state_manager = StateManager(
                config_manager=config_manager, logger_system=logger_system
            )

            self.theme_manager = IntegratedThemeManager(
                config_manager=config_manager,
                state_manager=state_manager,
                logger_system=logger_system,
                main_window=self,
            )
            print("✅ システムコンポーネントが正常に初期化されました")
        except Exception as e:
            print(f"❌ システムコンポーネントの初期化に失敗: {e}")
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
        title = QLabel("UIコンポーネント テーマ統合テスト")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)

        # 説明
        description = QLabel(
            "各テーマボタンをクリックして、EXIFパネルとサムネイルグリッドの色変化を確認してください"
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("font-size: 14px; color: gray; margin-bottom: 20px;")
        layout.addWidget(description)

        # テーマ切り替えボタン
        button_layout = QHBoxLayout()

        themes_to_test = [
            ("default", "デフォルト"),
            ("dark", "ダーク"),
            ("light", "ライト"),
            ("blue", "ブルー"),
            ("green", "グリーン"),
            ("high_contrast", "ハイコントラスト"),
        ]

        for theme_id, theme_name in themes_to_test:
            button = QPushButton(f"{theme_name}テーマ")
            button.clicked.connect(lambda checked, t=theme_id: self.apply_theme(t))
            button.setMinimumHeight(40)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        # UIコンポーネントのテストエリア
        components_layout = QHBoxLayout()

        # EXIFパネル
        if self.theme_manager:
            try:
                self.exif_panel = EXIFPanel(
                    config_manager=self.theme_manager.config_manager,
                    state_manager=self.theme_manager.state_manager,
                    logger_system=self.theme_manager.logger_system,
                    theme_manager=self.theme_manager,
                )
                components_layout.addWidget(self.exif_panel)
                print("✅ EXIFパネルを作成しました")
            except Exception as e:
                print(f"❌ EXIFパネルの作成に失敗: {e}")
                import traceback

                print(f"詳細: {traceback.format_exc()}")

        # サムネイルグリッド
        if self.theme_manager:
            try:
                self.thumbnail_grid = SimpleThumbnailGrid(
                    config_manager=self.theme_manager.config_manager,
                    state_manager=self.theme_manager.state_manager,
                    logger_system=self.theme_manager.logger_system,
                    theme_manager=self.theme_manager,
                )
                components_layout.addWidget(self.thumbnail_grid)
                print("✅ サムネイルグリッドを作成しました")
            except Exception as e:
                print(f"❌ サムネイルグリッドの作成に失敗: {e}")
                import traceback

                print(f"詳細: {traceback.format_exc()}")

        layout.addLayout(components_layout)

        # ログ表示エリア
        log_label = QLabel("テーマ適用ログ:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(log_label)

        self.log_display = QLabel("ログが表示されます...")
        self.log_display.setStyleSheet(
            "font-family: monospace; font-size: 12px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;"
        )
        self.log_display.setWordWrap(True)
        layout.addWidget(self.log_display)

    def apply_theme(self, theme_name: str):
        """テーマを適用"""
        if not self.theme_manager:
            self.log_display.setText("❌ テーママネージャーが利用できません")
            return

        try:
            self.log_display.setText(f"🔄 テーマ '{theme_name}' を適用中...")

            # テーマを適用
            success = self.theme_manager.apply_theme(theme_name)

            if success:
                log_text = f"✅ テーマ '{theme_name}' の適用に成功しました\n"

                # テーマ情報を表示
                theme_config = self.theme_manager.get_theme_config(theme_name)
                if theme_config:
                    colors = theme_config.get("color_scheme", {})
                    log_text += f"   背景色: {colors.get('background', 'N/A')}\n"
                    log_text += f"   テキスト色: {colors.get('foreground', 'N/A')}\n"
                    log_text += f"   プライマリ色: {colors.get('primary', 'N/A')}\n"
                    log_text += f"   ボーダー色: {colors.get('border', 'N/A')}"

                self.log_display.setText(log_text)

            else:
                self.log_display.setText(
                    f"❌ テーマ '{theme_name}' の適用に失敗しました"
                )

        except Exception as e:
            error_text = f"❌ テーマ適用中にエラー: {e}\n"
            import traceback

            error_text += f"詳細: {traceback.format_exc()}"
            self.log_display.setText(error_text)


def main():
    """メイン関数"""
    app = QApplication(sys.argv)

    # アプリケーションの基本設定
    app.setApplicationName("UIテーマ統合テスト")
    app.setApplicationVersion("1.0.0")

    # テストウィンドウの作成と表示
    window = UIThemeIntegrationTestWindow()
    window.show()

    print("🎨 UIテーマ統合テストウィンドウを表示しました")
    print("各テーマボタンをクリックしてUIコンポーネントのテーマ追随を確認してください")
    print("特に以下の点を確認してください：")
    print("  - EXIFパネルの枠と背景色の変化")
    print("  - サムネイルグリッドの枠と背景色の変化")
    print("  - テキスト色の適切な変化")

    # イベントループの開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
