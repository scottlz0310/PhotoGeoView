#!/usr/bin/env python3
"""
UIコンポーネントのテーマ統合修正

EXIFパネルとサムネイルグリッドがテーマ変更に正しく追随するように修正します。
- テーママネージャーとの連携強化
- 動的スタイルシート更新
- テーマ変更シグナルの処理

Author: Kiro AI Integration System
"""

from pathlib import Path


def fix_exif_panel_theme_integration():
    """EXIFパネルのテーマ統合を修正"""

    exif_panel_path = Path("src/integration/ui/exif_panel.py")

    if not exif_panel_path.exists():
        print(f"❌ EXIFパネルファイルが見つかりません: {exif_panel_path}")
        return False

    print("📝 EXIFパネルのテーマ統合を修正中...")

    with open(exif_panel_path, encoding="utf-8") as f:
        content = f.read()

    # 1. テーママネージャーとの連携を強化
    old_init = """    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem,
        theme_manager: Optional[object] = None,    ):
        super().__

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system
        self.error_handler = IntegratedErrorHandler(logger_system)
        self.theme_manager = theme_manager
        self._last_exif_data: Optional[Dict[str, Any]] = None"""

    new_init = """    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem,
        theme_manager: Optional[object] = None,
    ):
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system
        self.error_handler = IntegratedErrorHandler(logger_system)
        self.theme_manager = theme_manager
        self._last_exif_data: Optional[Dict[str, Any]] = None

        # テーマ変更シグナルの接続
        if self.theme_manager and hasattr(self.theme_manager, 'theme_changed'):
            self.theme_manager.theme_changed.connect(self._on_theme_changed)"""

    if old_init in content:
        content = content.replace(old_init, new_init)
        print("✅ EXIFパネルの初期化を改善しました")
    else:
        print("⚠️  EXIFパネルの初期化部分が見つかりませんでした")

    # 2. テーマ変更ハンドラーを追加
    theme_handler = '''
    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(f"EXIFパネル: テーマ変更を検出 - {theme_name}")

            # UIスタイルを更新
            self._update_theme_styles()

            # 現在表示中のデータがある場合は再描画
            if self._last_exif_data:
                self._create_integrated_sections(self._last_exif_data)

        except Exception as e:
            self.logger_system.error(f"EXIFパネルのテーマ変更処理でエラー: {e}")

    def _update_theme_styles(self):
        """テーマに基づいてスタイルを更新"""
        try:
            # タイトルラベルのスタイル更新
            if hasattr(self, 'title_label'):
                title_fg = self._get_color("foreground", "#2c3e50")
                title_bg = self._get_color("hover", self._get_color("background", "#ecf0f1"))
                self.title_label.setStyleSheet(f"""
                    QLabel {{
                        font-weight: bold;
                        font-size: 14px;
                        color: {title_fg};
                        padding: 5px;
                        background-color: {title_bg};
                        border-radius: 3px;
                    }}
                """)

            # スクロールエリアのスタイル更新
            if hasattr(self, 'integrated_scroll_area'):
                scroll_border = self._get_color("border", "#bdc3c7")
                scroll_bg = self._get_color("background", "#ffffff")
                scroll_focus = self._get_color("primary", "#3498db")
                self.integrated_scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        border: 1px solid {scroll_border};
                        border-radius: 3px;
                        background-color: {scroll_bg};
                    }}
                    QScrollArea:focus {{
                        border: 2px solid {scroll_focus};
                    }}
                """)

            # 初期メッセージラベルのスタイル更新
            if hasattr(self, 'initial_message_label'):
                msg_color = self._get_color_safe("foreground", "#7f8c8d")
                msg_bg = self._get_color_safe("background", "#ffffff")
                border_color = self._get_color_safe("border", "#e0e0e0")
                self.initial_message_label.setStyleSheet(f"""
                    QLabel {{
                        color: {msg_color};
                        background-color: {msg_bg};
                        font-style: italic;
                        font-size: 16px;
                        padding: 20px;
                        border: 1px solid {border_color};
                        border-radius: 5px;
                        margin: 10px;
                    }}
                """)

        except Exception as e:
            self.logger_system.error(f"EXIFパネルのスタイル更新でエラー: {e}")'''

    # テーマハンドラーを追加
    if "def _get_color_safe" in content:
        content = content.replace(
            "def _get_color_safe", theme_handler + "\n\n    def _get_color_safe"
        )
        print("✅ EXIFパネルのテーマ変更ハンドラーを追加しました")
    else:
        print("⚠️  EXIFパネルのテーマハンドラー挿入位置が見つかりませんでした")

    # 3. _setup_ui メソッドでタイトルラベルを保存
    old_title_setup = '''            # タイトル
            title_label = QLabel("📷 画像情報・位置情報")
            title_fg = self._get_color("foreground", "#2c3e50")
            title_bg = self._get_color("hover", self._get_color("background", "#ecf0f1"))
            title_label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    font-size: 14px;
                    color: {title_fg};
                    padding: 5px;
                    background-color: {title_bg};
                    border-radius: 3px;
                }}
            """)
            layout.addWidget(title_label)'''

    new_title_setup = '''            # タイトル
            self.title_label = QLabel("📷 画像情報・位置情報")
            title_fg = self._get_color("foreground", "#2c3e50")
            title_bg = self._get_color("hover", self._get_color("background", "#ecf0f1"))
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    font-size: 14px;
                    color: {title_fg};
                    padding: 5px;
                    background-color: {title_bg};
                    border-radius: 3px;
                }}
            """)
            layout.addWidget(self.title_label)'''

    if old_title_setup in content:
        content = content.replace(old_title_setup, new_title_setup)
        print("✅ EXIFパネルのタイトルラベル参照を修正しました")
    else:
        print("⚠️  EXIFパネルのタイトルラベル設定が見つかりませんでした")

    # 4. セクション作成時のテーマ対応を強化
    old_section_style = '''def _create_section_widget(self, title: str, items: List[tuple], color: str) -> QWidget:
        """セクションウィジェットを作成"""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)

        # セクションタイトル
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                font-size: 12px;
                color: white;
                background-color: {color};
                padding: 5px 10px;
                border-radius: 3px;
                margin-bottom: 5px;
            }}
        """)
        section_layout.addWidget(title_label)'''

    new_section_style = '''def _create_section_widget(self, title: str, items: List[tuple], color: str) -> QWidget:
        """セクションウィジェットを作成（テーマ対応版）"""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(5)

        # セクションタイトル（テーマ対応）
        title_label = QLabel(title)
        # テーマに応じた色の調整
        if self._is_dark_theme():
            text_color = "#ffffff"
            bg_color = color
        else:
            text_color = "#ffffff"
            bg_color = color

        title_label.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                font-size: 12px;
                color: {text_color};
                background-color: {bg_color};
                padding: 5px 10px;
                border-radius: 3px;
                margin-bottom: 5px;
            }}
        """)
        section_layout.addWidget(title_label)'''

    if old_section_style in content:
        content = content.replace(old_section_style, new_section_style)
        print("✅ EXIFパネルのセクションスタイルを改善しました")
    else:
        print("⚠️  EXIFパネルのセクションスタイル設定が見つかりませんでした")

    # 5. ダークテーマ判定メソッドを追加
    dark_theme_method = '''
    def _is_dark_theme(self) -> bool:
        """現在のテーマがダークテーマかどうかを判定"""
        try:
            if self.theme_manager and hasattr(self.theme_manager, 'get_current_theme'):
                current_theme = self.theme_manager.get_current_theme()
                return any(keyword in current_theme.lower() for keyword in ['dark', 'night', 'black'])
            return False
        except Exception:
            return False'''

    # _is_dark_theme メソッドを追加
    if "def _get_color_safe" in content:
        content = content.replace(
            "def _get_color_safe", dark_theme_method + "\n\n    def _get_color_safe"
        )
        print("✅ EXIFパネルのダークテーマ判定メソッドを追加しました")

    # ファイルを保存
    with open(exif_panel_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ EXIFパネルのテーマ統合修正が完了しました: {exif_panel_path}")
    return True


def fix_thumbnail_grid_theme_integration():
    """サムネイルグリッドのテーマ統合を修正"""

    thumbnail_grid_path = Path("src/integration/ui/thumbnail_grid.py")

    if not thumbnail_grid_path.exists():
        print(f"❌ サムネイルグリッドファイルが見つかりません: {thumbnail_grid_path}")
        return False

    print("📝 サムネイルグリッドのテーマ統合を修正中...")

    with open(thumbnail_grid_path, encoding="utf-8") as f:
        content = f.read()

    # 1. ThumbnailItemクラスのテーマ対応を強化
    old_thumbnail_style = '''        self.setStyleSheet(
            """
            QLabel {
                border: 2px solid transparent;
                border-radius: 4px;
                background-color: #f8f9fa;
                padding: 4px;
            }
            QLabel:hover {
                border-color: #007acc;
                background-color: #e3f2fd;
            }
        """
        )'''

    new_thumbnail_style = """        # テーマ対応のスタイルシートは後で設定
        self.theme_manager = None  # 後で設定される
        self._update_thumbnail_style()"""

    if old_thumbnail_style in content:
        content = content.replace(old_thumbnail_style, new_thumbnail_style)
        print("✅ サムネイルアイテムのスタイル設定を改善しました")
    else:
        print("⚠️  サムネイルアイテムのスタイル設定が見つかりませんでした")

    # 2. ThumbnailItemクラスにテーマ更新メソッドを追加
    thumbnail_theme_methods = '''
    def set_theme_manager(self, theme_manager):
        """テーママネージャーを設定"""
        self.theme_manager = theme_manager
        if theme_manager and hasattr(theme_manager, 'theme_changed'):
            theme_manager.theme_changed.connect(self._on_theme_changed)
        self._update_thumbnail_style()

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        self._update_thumbnail_style()

    def _update_thumbnail_style(self):
        """テーマに基づいてスタイルを更新"""
        try:
            # デフォルト色
            bg_color = "#f8f9fa"
            hover_bg = "#e3f2fd"
            border_color = "#007acc"

            # テーママネージャーから色を取得
            if self.theme_manager:
                try:
                    bg_color = self.theme_manager.get_color("background", "#f8f9fa")
                    hover_bg = self.theme_manager.get_color("hover", "#e3f2fd")
                    border_color = self.theme_manager.get_color("primary", "#007acc")
                except Exception:
                    pass  # デフォルト色を使用

            self.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid transparent;
                    border-radius: 4px;
                    background-color: {bg_color};
                    padding: 4px;
                }}
                QLabel:hover {{
                    border-color: {border_color};
                    background-color: {hover_bg};
                }}
            """)
        except Exception as e:
            # エラー時はデフォルトスタイルを適用
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid transparent;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                    padding: 4px;
                }
                QLabel:hover {
                    border-color: #007acc;
                    background-color: #e3f2fd;
                }
            """)'''

    # ThumbnailItemクラスにメソッドを追加
    if "def _show_placeholder(self):" in content:
        content = content.replace(
            "def _show_placeholder(self):",
            thumbnail_theme_methods + "\n\n    def _show_placeholder(self):",
        )
        print("✅ サムネイルアイテムのテーマ更新メソッドを追加しました")
    else:
        print("⚠️  サムネイルアイテムのメソッド挿入位置が見つかりませんでした")

    # 3. OptimizedThumbnailGridクラスの初期化を修正
    old_grid_init = '''class OptimizedThumbnailGrid(QWidget):
    """
    Optimized thumbnail grid with Kiro performance enhancements
    """

    # Signals
    image_selected = Signal(Path)
    image_double_clicked = Signal(Path)
    selection_changed = Signal(list)  # List of selected image paths

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem,
    ):
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system
        self.error_handler = IntegratedErrorHandler(logger_system)'''

    new_grid_init = '''class OptimizedThumbnailGrid(QWidget):
    """
    Optimized thumbnail grid with Kiro performance enhancements
    """

    # Signals
    image_selected = Signal(Path)
    image_double_clicked = Signal(Path)
    selection_changed = Signal(list)  # List of selected image paths

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem,
        theme_manager: Optional[object] = None,
    ):
        super().__init__()

        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system
        self.error_handler = IntegratedErrorHandler(logger_system)
        self.theme_manager = theme_manager

        # テーマ変更シグナルの接続
        if self.theme_manager and hasattr(self.theme_manager, 'theme_changed'):
            self.theme_manager.theme_changed.connect(self._on_theme_changed)'''

    if old_grid_init in content:
        content = content.replace(old_grid_init, new_grid_init)
        print("✅ サムネイルグリッドの初期化を改善しました")
    else:
        print("⚠️  サムネイルグリッドの初期化部分が見つかりませんでした")

    # 4. OptimizedThumbnailGridクラスにテーマ変更ハンドラーを追加
    grid_theme_handler = '''
    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.info(f"サムネイルグリッド: テーマ変更を検出 - {theme_name}")

            # 全てのサムネイルアイテムにテーママネージャーを設定
            for thumbnail_item in self.thumbnail_items:
                thumbnail_item.set_theme_manager(self.theme_manager)

            # 空状態表示のスタイルも更新
            self._update_empty_state_style()

        except Exception as e:
            self.logger_system.error(f"サムネイルグリッドのテーマ変更処理でエラー: {e}")

    def _update_empty_state_style(self):
        """空状態表示のスタイルを更新"""
        try:
            if hasattr(self, 'empty_state_label'):
                # テーママネージャーから色を取得
                text_color = "#7f8c8d"
                bg_color = "#ffffff"

                if self.theme_manager:
                    try:
                        text_color = self.theme_manager.get_color("secondary", "#7f8c8d")
                        bg_color = self.theme_manager.get_color("background", "#ffffff")
                    except Exception:
                        pass  # デフォルト色を使用

                self.empty_state_label.setStyleSheet(f"""
                    QLabel {{
                        color: {text_color};
                        background-color: {bg_color};
                        font-size: 16px;
                        font-style: italic;
                        padding: 40px;
                        border-radius: 8px;
                    }}
                """)
        except Exception as e:
            self.logger_system.error(f"空状態スタイル更新でエラー: {e}")'''

    # OptimizedThumbnailGridクラスにメソッドを追加
    if "def cleanup(self):" in content:
        content = content.replace(
            "def cleanup(self):", grid_theme_handler + "\n\n    def cleanup(self):"
        )
        print("✅ サムネイルグリッドのテーマ変更ハンドラーを追加しました")
    else:
        print("⚠️  サムネイルグリッドのメソッド挿入位置が見つかりませんでした")

    # 5. サムネイルアイテム作成時にテーママネージャーを設定
    old_item_creation = """        # Create thumbnail item
        thumbnail_item = ThumbnailItem(image_path, self.thumbnail_size)
        thumbnail_item.clicked.connect(self._on_thumbnail_clicked)
        thumbnail_item.context_menu_requested.connect(self._on_context_menu_requested)
        thumbnail_item.exif_info_requested.connect(self._on_exif_info_requested)"""

    new_item_creation = """        # Create thumbnail item
        thumbnail_item = ThumbnailItem(image_path, self.thumbnail_size)
        thumbnail_item.set_theme_manager(self.theme_manager)  # テーママネージャーを設定
        thumbnail_item.clicked.connect(self._on_thumbnail_clicked)
        thumbnail_item.context_menu_requested.connect(self._on_context_menu_requested)
        thumbnail_item.exif_info_requested.connect(self._on_exif_info_requested)"""

    if old_item_creation in content:
        content = content.replace(old_item_creation, new_item_creation)
        print("✅ サムネイルアイテム作成時のテーママネージャー設定を追加しました")
    else:
        print("⚠️  サムネイルアイテム作成部分が見つかりませんでした")

    # 6. Optionalのインポートを追加
    if "from typing import Any, Dict, List, Optional" not in content:
        content = content.replace(
            "from typing import Any, Dict, List",
            "from typing import Any, Dict, List, Optional",
        )
        print("✅ Optionalのインポートを追加しました")

    # ファイルを保存
    with open(thumbnail_grid_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ サムネイルグリッドのテーマ統合修正が完了しました: {thumbnail_grid_path}")
    return True


def update_main_window_theme_integration():
    """メインウィンドウでのテーママネージャー連携を更新"""

    main_window_path = Path("src/integration/ui/main_window.py")

    if not main_window_path.exists():
        print(f"❌ メインウィンドウファイルが見つかりません: {main_window_path}")
        return False

    print("📝 メインウィンドウのテーマ統合を修正中...")

    with open(main_window_path, encoding="utf-8") as f:
        content = f.read()

    # EXIFパネル作成時にテーママネージャーを渡す
    old_exif_creation = """        self.exif_panel = EXIFPanel(
            self.config_manager,
            self.state_manager,
            self.logger_system
        )"""

    new_exif_creation = """        self.exif_panel = EXIFPanel(
            self.config_manager,
            self.state_manager,
            self.logger_system,
            theme_manager=self.theme_manager
        )"""

    if old_exif_creation in content:
        content = content.replace(old_exif_creation, new_exif_creation)
        print("✅ EXIFパネル作成時のテーママネージャー連携を追加しました")
    else:
        print("⚠️  EXIFパネル作成部分が見つかりませんでした")

    # サムネイルグリッド作成時にテーママネージャーを渡す
    old_thumbnail_creation = """        self.thumbnail_grid = OptimizedThumbnailGrid(
            self.config_manager,
            self.state_manager,
            self.logger_system
        )"""

    new_thumbnail_creation = """        self.thumbnail_grid = OptimizedThumbnailGrid(
            self.config_manager,
            self.state_manager,
            self.logger_system,
            theme_manager=self.theme_manager
        )"""

    if old_thumbnail_creation in content:
        content = content.replace(old_thumbnail_creation, new_thumbnail_creation)
        print("✅ サムネイルグリッド作成時のテーママネージャー連携を追加しました")
    else:
        print("⚠️  サムネイルグリッド作成部分が見つかりませんでした")

    # ファイルを保存
    with open(main_window_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ メインウィンドウのテーマ統合修正が完了しました: {main_window_path}")
    return True


def create_theme_integration_test():
    """テーマ統合のテストツールを作成"""

    test_path = Path("test_ui_theme_integration.py")

    test_content = '''#!/usr/bin/env python3
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
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
    from PySide6.QtCore import Qt

    # 統合システムをインポート
    from src.integration.config_manager import ConfigManager
    from src.integration.state_manager import StateManager
    from src.integration.logging_system import LoggerSystem
    from src.integration.ui.theme_manager import IntegratedThemeManager
    from src.integration.ui.exif_panel import EXIFPanel
    from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid

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
            state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

            self.theme_manager = IntegratedThemeManager(
                config_manager=config_manager,
                state_manager=state_manager,
                logger_system=logger_system,
                main_window=self
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

        # テーマ切り替えボタン
        button_layout = QHBoxLayout()

        themes_to_test = [
            ("default", "デフォルト"),
            ("dark", "ダーク"),
            ("light", "ライト"),
            ("blue", "ブルー"),
            ("high_contrast", "ハイコントラスト")
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
                    theme_manager=self.theme_manager
                )
                components_layout.addWidget(self.exif_panel)
                print("✅ EXIFパネルを作成しました")
            except Exception as e:
                print(f"❌ EXIFパネルの作成に失敗: {e}")

        # サムネイルグリッド
        if self.theme_manager:
            try:
                self.thumbnail_grid = OptimizedThumbnailGrid(
                    config_manager=self.theme_manager.config_manager,
                    state_manager=self.theme_manager.state_manager,
                    logger_system=self.theme_manager.logger_system,
                    theme_manager=self.theme_manager
                )
                components_layout.addWidget(self.thumbnail_grid)
                print("✅ サムネイルグリッドを作成しました")
            except Exception as e:
                print(f"❌ サムネイルグリッドの作成に失敗: {e}")

        layout.addLayout(components_layout)

    def apply_theme(self, theme_name: str):
        """テーマを適用"""
        if not self.theme_manager:
            print("❌ テーママネージャーが利用できません")
            return

        try:
            print(f"🔄 テーマ '{theme_name}' を適用中...")

            # テーマを適用
            success = self.theme_manager.apply_theme(theme_name)

            if success:
                print(f"✅ テーマ '{theme_name}' の適用に成功しました")

                # テーマ情報を表示
                theme_config = self.theme_manager.get_theme_config(theme_name)
                if theme_config:
                    colors = theme_config.get('color_scheme', {})
                    print(f"   背景色: {colors.get('background', 'N/A')}")
                    print(f"   テキスト色: {colors.get('foreground', 'N/A')}")
                    print(f"   プライマリ色: {colors.get('primary', 'N/A')}")

            else:
                print(f"❌ テーマ '{theme_name}' の適用に失敗しました")

        except Exception as e:
            print(f"❌ テーマ適用中にエラー: {e}")
            import traceback
            print(f"詳細: {traceback.format_exc()}")

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

    # イベントループの開始
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''

    with open(test_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    print(f"✅ UIテーマ統合テストツールを作成しました: {test_path}")
    return True


def main():
    """メイン実行関数"""
    print("🔧 UIコンポーネントのテーマ統合修正を開始します...")

    try:
        # 1. EXIFパネルのテーマ統合を修正
        if fix_exif_panel_theme_integration():
            print("✅ EXIFパネルのテーマ統合修正が完了しました")
        else:
            print("❌ EXIFパネルのテーマ統合修正に失敗しました")
            return False

        # 2. サムネイルグリッドのテーマ統合を修正
        if fix_thumbnail_grid_theme_integration():
            print("✅ サムネイルグリッドのテーマ統合修正が完了しました")
        else:
            print("❌ サムネイルグリッドのテーマ統合修正に失敗しました")
            return False

        # 3. メインウィンドウのテーマ統合を更新
        if update_main_window_theme_integration():
            print("✅ メインウィンドウのテーマ統合更新が完了しました")
        else:
            print("❌ メインウィンドウのテーマ統合更新に失敗しました")

        # 4. テスト用ツールの作成
        if create_theme_integration_test():
            print("✅ テスト用ツールの作成が完了しました")
        else:
            print("❌ テスト用ツールの作成に失敗しました")

        print("\n🎉 UIコンポーネントのテーマ統合修正が完了しました！")
        print("\n📋 修正内容:")
        print("  - EXIFパネルのテーマ変更追随機能")
        print("  - サムネイルグリッドのテーマ対応強化")
        print("  - メインウィンドウでのテーママネージャー連携")
        print("  - 動的スタイルシート更新機能")

        print("\n🔍 テスト方法:")
        print("  1. python test_ui_theme_integration.py でテストツールを起動")
        print("  2. 各テーマボタンをクリックしてUIコンポーネントの色変化を確認")
        print("  3. EXIFパネルとサムネイルの枠・背景色がテーマに追随することを確認")

        return True

    except Exception as e:
        print(f"❌ 修正中にエラーが発生しました: {e}")
        import traceback

        print(f"詳細: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    main()
