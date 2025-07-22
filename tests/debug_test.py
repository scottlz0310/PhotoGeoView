#!/usr/bin/env python3
"""
全画面モードのレイアウト復帰問題を詳細にデバッグするテストコード
スプリッターの最小サイズ制約に関する問題を調査
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QPushButton,
    QLabel,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.core.logger import setup_logging, get_logger


class SplitterDebugWidget(QFrame):
    """スプリッター動作を詳細にデバッグするためのウィジェット"""

    def __init__(self, name: str, color: str = "#f0f0f0"):
        super().__init__()
        self.name = name
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"background-color: {color}; border: 2px solid #999;")

        layout = QVBoxLayout(self)

        # タイトル
        title = QLabel(f"📋 {name}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # サイズ情報
        self.size_info = QLabel("サイズ: 0x0")
        self.size_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.size_info)

        # 最小サイズ情報
        self.min_size_info = QLabel("最小: 0x0")
        self.min_size_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.min_size_info)

        # 最大サイズ情報
        self.max_size_info = QLabel("最大: 0x0")
        self.max_size_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.max_size_info)

        # ストレッチ
        layout.addStretch()

        # 最小サイズ設定ボタン
        btn_layout = QVBoxLayout()

        btn_default = QPushButton("デフォルト最小サイズ")
        btn_default.clicked.connect(self.set_default_minimum_size)
        btn_layout.addWidget(btn_default)

        btn_zero = QPushButton("最小サイズ (0,0)")
        btn_zero.clicked.connect(self.set_zero_minimum_size)
        btn_layout.addWidget(btn_zero)

        btn_large = QPushButton("最小サイズ (200,150)")
        btn_large.clicked.connect(self.set_large_minimum_size)
        btn_layout.addWidget(btn_large)

        layout.addLayout(btn_layout)

        # タイマーでサイズ情報を更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_size_info)
        self.timer.start(500)  # 0.5秒ごと

    def set_default_minimum_size(self):
        """デフォルト最小サイズを設定"""
        self.setMinimumSize(100, 80)
        print(f"{self.name}: デフォルト最小サイズ (100, 80) を設定")

    def set_zero_minimum_size(self):
        """最小サイズを (0,0) に設定"""
        self.setMinimumSize(0, 0)
        print(f"{self.name}: 最小サイズ (0, 0) を設定")

    def set_large_minimum_size(self):
        """大きな最小サイズを設定"""
        self.setMinimumSize(200, 150)
        print(f"{self.name}: 最小サイズ (200, 150) を設定")

    def update_size_info(self):
        """サイズ情報を更新"""
        size = self.size()
        min_size = self.minimumSize()
        max_size = self.maximumSize()

        self.size_info.setText(f"サイズ: {size.width()}x{size.height()}")
        self.min_size_info.setText(f"最小: {min_size.width()}x{min_size.height()}")

        if max_size.width() == 16777215 and max_size.height() == 16777215:
            self.max_size_info.setText("最大: 制限なし")
        else:
            self.max_size_info.setText(f"最大: {max_size.width()}x{max_size.height()}")


class FullscreenLayoutDebugger(QMainWindow):
    """全画面レイアウト問題のデバッガー"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.setWindowTitle("PhotoGeoView - 全画面レイアウト問題デバッガー")
        self.setGeometry(100, 100, 1200, 800)

        # 状態フラグ
        self.image_fullscreen = False
        self.map_fullscreen = False
        self.saved_main_sizes = None
        self.saved_right_sizes = None

        self.setup_ui()

    def setup_ui(self):
        """UIセットアップ"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)

        # コントロールパネル
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # メインスプリッター
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左パネル
        self.left_panel = SplitterDebugWidget("左パネル (フォルダ・サムネイル)", "#e8f4f8")
        self.main_splitter.addWidget(self.left_panel)

        # 右スプリッター
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)

        # 画像パネル
        self.image_panel = SplitterDebugWidget("画像パネル", "#f8f4e8")
        self.right_splitter.addWidget(self.image_panel)

        # 地図パネル
        self.map_panel = SplitterDebugWidget("地図パネル", "#e8f8e8")
        self.right_splitter.addWidget(self.map_panel)

        self.main_splitter.addWidget(self.right_splitter)

        # 初期サイズ設定
        self.main_splitter.setSizes([300, 700])
        self.right_splitter.setSizes([400, 300])

        main_layout.addWidget(self.main_splitter, 1)

        # ログ出力エリア
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(200)
        self.log_area.setPlainText("デバッグログがここに表示されます...\n")
        main_layout.addWidget(self.log_area)

    def create_control_panel(self) -> QWidget:
        """コントロールパネルを作成"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(100)

        layout = QVBoxLayout(panel)

        # タイトル
        title = QLabel("🔧 全画面モードレイアウト問題デバッガー")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ボタンレイアウト
        btn_layout = QHBoxLayout()

        # 画像全画面ボタン
        self.image_fullscreen_btn = QPushButton("画像全画面ON")
        self.image_fullscreen_btn.clicked.connect(self.toggle_image_fullscreen)
        btn_layout.addWidget(self.image_fullscreen_btn)

        # 地図全画面ボタン
        self.map_fullscreen_btn = QPushButton("地図全画面ON")
        self.map_fullscreen_btn.clicked.connect(self.toggle_map_fullscreen)
        btn_layout.addWidget(self.map_fullscreen_btn)

        btn_layout.addStretch()

        # レイアウト情報ボタン
        info_btn = QPushButton("📊 レイアウト情報")
        info_btn.clicked.connect(self.log_layout_info)
        btn_layout.addWidget(info_btn)

        # クリアボタン
        clear_btn = QPushButton("🗑️ ログクリア")
        clear_btn.clicked.connect(lambda: self.log_area.clear())
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        return panel

    def toggle_image_fullscreen(self):
        """画像全画面モードを切り替え"""
        if not self.image_fullscreen:
            self.log("=== 画像全画面モード開始 ===")
            self.image_fullscreen = True
            self.image_fullscreen_btn.setText("画像全画面OFF")
            self.show_image_fullscreen()
        else:
            self.log("=== 画像全画面モード終了 ===")
            self.image_fullscreen = False
            self.image_fullscreen_btn.setText("画像全画面ON")
            self.restore_image_normal_layout()

    def toggle_map_fullscreen(self):
        """地図全画面モードを切り替え"""
        if not self.map_fullscreen:
            self.log("=== 地図全画面モード開始 ===")
            self.map_fullscreen = True
            self.map_fullscreen_btn.setText("地図全画面OFF")
            self.show_map_fullscreen()
        else:
            self.log("=== 地図全画面モード終了 ===")
            self.map_fullscreen = False
            self.map_fullscreen_btn.setText("地図全画面ON")
            self.restore_map_normal_layout()

    def save_current_layout(self):
        """現在のレイアウトを保存"""
        self.saved_main_sizes = self.main_splitter.sizes()
        self.saved_right_sizes = self.right_splitter.sizes()
        self.log(f"レイアウト保存: main={self.saved_main_sizes}, right={self.saved_right_sizes}")

    def show_image_fullscreen(self):
        """画像全画面表示"""
        self.save_current_layout()

        self.log("最小サイズを (0,0) に設定...")
        self.image_panel.setMinimumSize(0, 0)
        self.map_panel.setMinimumSize(0, 0)

        self.log("パネル可視性を変更...")
        self.left_panel.setVisible(False)
        self.map_panel.setVisible(False)

        total_width = self.main_splitter.width()
        self.log(f"スプリッターサイズを調整: [0, {total_width}]")
        self.main_splitter.setSizes([0, total_width])

    def show_map_fullscreen(self):
        """地図全画面表示"""
        self.save_current_layout()

        self.log("最小サイズを (0,0) に設定...")
        self.image_panel.setMinimumSize(0, 0)
        self.map_panel.setMinimumSize(0, 0)

        self.log("パネル可視性を変更...")
        self.left_panel.setVisible(False)
        self.image_panel.setVisible(False)

        total_width = self.main_splitter.width()
        self.log(f"スプリッターサイズを調整: [0, {total_width}]")
        self.main_splitter.setSizes([0, total_width])

    def restore_image_normal_layout(self):
        """画像全画面から通常レイアウトに復元"""
        self.log("通常レイアウトに復元開始...")

        # 【重要】パネルの最小サイズを復元
        self.log("パネルの最小サイズを復元...")
        self.left_panel.setMinimumSize(100, 80)  # 適切な最小サイズを設定
        self.image_panel.setMinimumSize(150, 100)
        self.map_panel.setMinimumSize(150, 100)

        self.log("すべてのパネルを表示に設定...")
        self.left_panel.setVisible(True)
        self.image_panel.setVisible(True)
        self.map_panel.setVisible(True)

        if self.saved_main_sizes and self.saved_right_sizes:
            self.log(f"保存されたサイズを復元: main={self.saved_main_sizes}, right={self.saved_right_sizes}")

            # レイアウト更新を強制
            QApplication.processEvents()

            self.main_splitter.setSizes(self.saved_main_sizes)
            self.right_splitter.setSizes(self.saved_right_sizes)

            # 復元後の確認
            QTimer.singleShot(100, self.verify_restoration)
        else:
            self.log("保存されたサイズがありません。デフォルトサイズを設定...")
            self.main_splitter.setSizes([300, 700])
            self.right_splitter.setSizes([400, 300])

    def restore_map_normal_layout(self):
        """地図全画面から通常レイアウトに復元"""
        self.log("通常レイアウトに復元開始...")

        # 【重要】パネルの最小サイズを復元
        self.log("パネルの最小サイズを復元...")
        self.left_panel.setMinimumSize(100, 80)
        self.image_panel.setMinimumSize(150, 100)
        self.map_panel.setMinimumSize(150, 100)

        self.log("すべてのパネルを表示に設定...")
        self.left_panel.setVisible(True)
        self.image_panel.setVisible(True)
        self.map_panel.setVisible(True)

        if self.saved_main_sizes and self.saved_right_sizes:
            self.log(f"保存されたサイズを復元: main={self.saved_main_sizes}, right={self.saved_right_sizes}")

            # レイアウト更新を強制
            QApplication.processEvents()

            self.main_splitter.setSizes(self.saved_main_sizes)
            self.right_splitter.setSizes(self.saved_right_sizes)

            # 復元後の確認
            QTimer.singleShot(100, self.verify_restoration)
        else:
            self.log("保存されたサイズがありません。デフォルトサイズを設定...")
            self.main_splitter.setSizes([300, 700])
            self.right_splitter.setSizes([400, 300])

    def verify_restoration(self):
        """復元の検証"""
        actual_main = self.main_splitter.sizes()
        actual_right = self.right_splitter.sizes()

        self.log(f"復元結果確認: main={actual_main}, right={actual_right}")

        if self.saved_main_sizes and actual_main != self.saved_main_sizes:
            self.log("⚠️ メインスプリッターサイズの復元に問題があります")

        if self.saved_right_sizes and actual_right != self.saved_right_sizes:
            self.log("⚠️ 右スプリッターサイズの復元に問題があります")

    def log_layout_info(self):
        """レイアウト情報をログ出力"""
        self.log("=== 現在のレイアウト情報 ===")

        # スプリッターサイズ
        main_sizes = self.main_splitter.sizes()
        right_sizes = self.right_splitter.sizes()
        self.log(f"メインスプリッター: {main_sizes}")
        self.log(f"右スプリッター: {right_sizes}")

        # パネルの表示状態
        self.log(f"左パネル表示: {self.left_panel.isVisible()}")
        self.log(f"画像パネル表示: {self.image_panel.isVisible()}")
        self.log(f"地図パネル表示: {self.map_panel.isVisible()}")

        # パネルのサイズ制約
        for name, panel in [("左", self.left_panel), ("画像", self.image_panel), ("地図", self.map_panel)]:
            size = panel.size()
            min_size = panel.minimumSize()
            max_size = panel.maximumSize()
            self.log(f"{name}パネル - サイズ:{size.width()}x{size.height()}, "
                     f"最小:{min_size.width()}x{min_size.height()}, "
                     f"最大:{max_size.width()}x{max_size.height()}")

        self.log("============================")

    def log(self, message: str):
        """ログ出力"""
        self.log_area.append(f"[{self.get_timestamp()}] {message}")
        # 自動スクロール
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_area.setTextCursor(cursor)

        # コンソールにも出力
        print(f"[DEBUG] {message}")

    def get_timestamp(self) -> str:
        """タイムスタンプ取得"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")


def main():
    """メイン関数"""
    # ロガー設定
    setup_logging()
    logger = get_logger(__name__)
    logger.info("全画面レイアウトデバッガーを開始します")

    app = QApplication(sys.argv)

    # デバッガーウィンドウを作成
    debugger = FullscreenLayoutDebugger()
    debugger.show()

    # 初期レイアウト情報をログ出力
    QTimer.singleShot(1000, debugger.log_layout_info)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
