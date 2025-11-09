"""
洗練されたテーマ選択UIコンポーネント

プレビュー機能付きのテーマ選択ダイアログとトグルボタンを提供します。
- テーマ一覧のプレビュー表示
- リアルタイムプレビュー機能
- 押し込まれた状態のボタン表示
- トグルボタンでのテーマ切り替え

Author: Kiro AI Integration System
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class ThemePreviewWidget(QWidget):
    """テーマプレビュー用ウィジェット"""

    def __init__(
        self,
        theme_name: str,
        theme_data: dict[str, Any],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.theme_name = theme_name
        self.theme_data = theme_data
        self.setFixedSize(200, 120)
        self.setup_ui()

    def setup_ui(self):
        """プレビューUIの設定"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # テーマ名ラベル
        name_label = QLabel(self.theme_data.get("display_name", self.theme_name))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(name_label)

        # プレビューエリア
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Shape.Box)
        preview_frame.setFixedSize(180, 80)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(4, 4, 4, 4)

        # サンプルUI要素のプレビュー
        sample_button = QPushButton("Button")
        sample_button.setFixedSize(60, 20)
        sample_label = QLabel("Sample Text")
        sample_label.setFixedSize(80, 16)

        preview_layout.addWidget(sample_button, alignment=Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(sample_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(preview_frame)

        # テーマ情報
        info_label = QLabel(f"Type: {self.theme_data.get('type', 'Unknown')}")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 10px; color: gray;")
        layout.addWidget(info_label)

        self.apply_theme_preview()

    def apply_theme_preview(self):
        """テーマプレビューの適用"""
        try:
            # テーマデータからスタイルシートを生成
            stylesheet = self._generate_preview_stylesheet()
            self.setStyleSheet(stylesheet)
        except Exception:
            # プレビュー適用に失敗した場合のフォールバック
            self.setStyleSheet("")

    def _generate_preview_stylesheet(self) -> str:
        """プレビュー用スタイルシートの生成"""
        colors = self.theme_data.get("colors", {})

        # 基本色の取得
        bg_color = colors.get("background", "#ffffff")
        text_color = colors.get("text", "#000000")
        accent_color = colors.get("accent", "#0078d4")
        border_color = colors.get("border", "#cccccc")

        return f"""
        QWidget {{
            background-color: {bg_color};
            color: {text_color};
        }}
        QPushButton {{
            background-color: {accent_color};
            color: white;
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 2px;
        }}
        QLabel {{
            color: {text_color};
        }}
        QFrame {{
            border: 1px solid {border_color};
            background-color: {bg_color};
        }}
        """


class ThemeSelectionDialog(QDialog):
    """洗練されたテーマ選択ダイアログ"""

    theme_selected = Signal(str)  # 選択されたテーマ名
    theme_applied = Signal(list)  # 適用されたテーマ名リスト(複数選択対応)

    def __init__(self, theme_manager: Any, parent: QWidget | None = None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.selected_themes: list[str] = []  # 複数選択対応
        self.preview_widgets: dict[str, ThemePreviewWidget] = {}
        self.original_theme: str | None = None  # 元のテーマを保存
        self.setup_ui()
        self.load_saved_selections()

    def setup_ui(self):
        """ダイアログUIの設定"""
        self.setWindowTitle("テーマ選択")
        self.setModal(True)
        self.resize(800, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # タイトル
        title_label = QLabel("アプリケーションのテーマを選択してください")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 説明
        description_label = QLabel(
            "テーマをクリックして選択してください(複数選択可能)。選択したテーマは適用後にトグル切り替えできます。"
        )
        description_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(description_label)

        # テーマグリッド
        self.create_theme_grid(layout)

        # ボタンエリア
        self.create_button_area(layout)

        # 現在のテーマを選択状態にする
        self.select_current_theme()

    def load_saved_selections(self):
        """保存された選択を読み込む"""
        try:
            # メインウィンドウから選択されたテーマリストを取得
            if hasattr(self.parent(), "theme_toggle_button"):
                toggle_button = self.parent().theme_toggle_button
                if hasattr(toggle_button, "selected_themes"):
                    self.selected_themes = toggle_button.selected_themes.copy()

                    # 選択状態の更新
                    for frame in self.findChildren(SelectableThemeFrame):
                        frame.set_selected(frame.theme_name in self.selected_themes)

                    # 選択状態表示の更新
                    self.update_selection_label()

                    # ボタンの有効化
                    self.apply_button.setEnabled(len(self.selected_themes) > 0)
        except Exception:
            # エラー時は現在のテーマのみを選択
            pass

    def create_theme_grid(self, parent_layout: QVBoxLayout) -> None:
        """テーマグリッドの作成"""
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # グリッドコンテナ
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(12)

        # テーマの追加
        self.populate_theme_grid()

        scroll_area.setWidget(grid_widget)
        parent_layout.addWidget(scroll_area)

    def populate_theme_grid(self):
        """テーマグリッドの構築"""
        theme_names = self.theme_manager.get_available_themes()
        current_theme_name = self.theme_manager.get_current_theme()

        row = 0
        col = 0
        max_cols = 3

        for theme_name in theme_names:
            # テーマデータの取得
            theme_data = self._get_theme_data(theme_name)

            # プレビューウィジェットの作成
            preview_widget = ThemePreviewWidget(theme_name, theme_data)
            self.preview_widgets[theme_name] = preview_widget

            # 選択可能なフレームでラップ
            selectable_frame = SelectableThemeFrame(
                preview_widget,
                theme_name,
                theme_data.get("display_name", theme_name),
                is_current=(theme_name == current_theme_name),
            )
            selectable_frame.theme_clicked.connect(self.on_theme_clicked)

            # グリッドに追加
            self.grid_layout.addWidget(selectable_frame, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _get_theme_data(self, theme_name: str) -> dict[str, Any]:
        """テーマデータの取得"""
        try:
            # SimpleThemeManagerからテーマ情報を取得
            theme_info = self.theme_manager.get_theme_info(theme_name)

            if theme_info:
                return {
                    "display_name": theme_info.get("display_name", theme_name),
                    "description": theme_info.get("description", f"{theme_name} theme"),
                    "type": "Built-in" if theme_name in ["default", "dark", "light"] else "Custom",
                    "colors": self._extract_colors_from_theme(theme_name),
                }
        except Exception:
            pass

        # フォールバック
        return {
            "display_name": theme_name,
            "description": f"{theme_name} theme",
            "type": "Unknown",
            "colors": {
                "background": "#ffffff",
                "text": "#000000",
                "accent": "#0078d4",
                "border": "#cccccc",
            },
        }

    def _extract_colors_from_theme(self, theme_name: str) -> dict[str, str]:
        """テーマから色情報を抽出"""
        try:
            # テーママネージャーのプレビュー色取得機能を使用
            if hasattr(self.theme_manager, "_get_preview_colors"):
                return self.theme_manager._get_preview_colors(theme_name)
        except Exception:
            pass

        # デフォルト色
        return {
            "background": "#ffffff",
            "text": "#000000",
            "accent": "#0078d4",
            "border": "#cccccc",
        }

    def create_button_area(self, parent_layout):
        """ボタンエリアの作成"""
        button_layout = QHBoxLayout()

        # 選択状態表示
        self.selection_label = QLabel("選択されたテーマ: なし")
        self.selection_label.setStyleSheet("color: gray; font-style: italic;")
        button_layout.addWidget(self.selection_label)

        # スペーサー
        button_layout.addStretch()

        # 適用ボタン
        self.apply_button = QPushButton("選択したテーマを適用")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_selected_themes)
        self.apply_button.setDefault(True)
        button_layout.addWidget(self.apply_button)

        # キャンセルボタン
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        parent_layout.addLayout(button_layout)

    def on_theme_clicked(self, theme_name: str):
        """テーマクリック時の処理(トグル選択)"""
        current_theme = self.theme_manager.get_current_theme()

        # 現在のテーマは選択解除できない
        if theme_name == current_theme:
            return

        # トグル選択
        if theme_name in self.selected_themes:
            self.selected_themes.remove(theme_name)
        else:
            self.selected_themes.append(theme_name)

        # 選択状態の更新
        for frame in self.findChildren(SelectableThemeFrame):
            frame.set_selected(frame.theme_name in self.selected_themes)

        # 選択状態表示の更新
        self.update_selection_label()

        # ボタンの有効化
        self.apply_button.setEnabled(len(self.selected_themes) > 0)

        # 最初の選択テーマをプレビュー
        if self.selected_themes:
            self.preview_first_selected_theme()

    def update_selection_label(self):
        """選択状態表示の更新"""
        if not self.selected_themes:
            self.selection_label.setText("選択されたテーマ: なし")
            self.selection_label.setStyleSheet("color: gray; font-style: italic;")
        else:
            theme_names = [self._get_theme_display_name(name) for name in self.selected_themes]
            self.selection_label.setText(f"選択されたテーマ: {', '.join(theme_names)}")
            self.selection_label.setStyleSheet("color: #0078d4; font-weight: bold;")

    def _get_theme_display_name(self, theme_name: str) -> str:
        """テーマの表示名を取得"""
        try:
            theme_info = self.theme_manager.get_theme_info(theme_name)
            return theme_info.get("display_name", theme_name) if theme_info else theme_name
        except Exception:
            return theme_name

    def preview_first_selected_theme(self):
        """最初の選択テーマをプレビュー"""
        if self.selected_themes:
            try:
                # 元のテーマを保存(初回のみ)
                if self.original_theme is None:
                    self.original_theme = self.theme_manager.get_current_theme()

                # 最初の選択テーマを適用
                self.theme_manager.apply_theme(self.selected_themes[0])

            except Exception:
                # プレビュー失敗時の処理
                pass

    def apply_selected_themes(self):
        """選択されたテーマを適用"""
        if self.selected_themes:
            # 最初のテーマを適用
            success = self.theme_manager.apply_theme(self.selected_themes[0])
            if success:
                # 選択されたテーマリストを送信
                self.theme_applied.emit(self.selected_themes)
                self.theme_selected.emit(self.selected_themes[0])
            self.accept()

    def select_current_theme(self):
        """現在のテーマを選択状態にする(選択解除不可)"""
        current_theme = self.theme_manager.get_current_theme()
        if current_theme:
            # 現在のテーマを選択リストに追加(既に存在する場合は追加しない)
            if current_theme not in self.selected_themes:
                self.selected_themes.append(current_theme)

            # 選択状態の更新
            for frame in self.findChildren(SelectableThemeFrame):
                is_current = frame.theme_name == current_theme
                frame.set_selected(frame.theme_name in self.selected_themes)
                frame.set_current_theme(is_current)  # 現在のテーマをマーク

            # 選択状態表示の更新
            self.update_selection_label()

            # ボタンの有効化
            self.apply_button.setEnabled(len(self.selected_themes) > 0)

            # 最初の選択テーマをプレビュー
            if self.selected_themes:
                self.preview_first_selected_theme()


class SelectableThemeFrame(QFrame):
    """選択可能なテーマフレーム"""

    theme_clicked = Signal(str)  # テーマ名

    def __init__(
        self,
        preview_widget: ThemePreviewWidget,
        theme_name: str,
        display_name: str,
        is_current: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.preview_widget = preview_widget
        self.theme_name = theme_name
        self.display_name = display_name
        self.is_current = is_current
        self.is_selected = False

        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """UIの設定"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # プレビューウィジェット
        layout.addWidget(self.preview_widget)

        # 現在のテーマ表示
        if self.is_current:
            current_label = QLabel("現在のテーマ")
            current_label.setAlignment(Qt.AlignCenter)
            current_label.setStyleSheet("color: green; font-size: 10px; font-weight: bold;")
            layout.addWidget(current_label)

        # クリックイベントの設定
        self.mousePressEvent = self.on_mouse_press

    def setup_style(self):
        """スタイルの設定"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.update_selection_style()

    def update_selection_style(self):
        """選択状態に応じたスタイル更新"""
        if self.is_current:
            # 現在のテーマ(選択解除不可)
            self.setStyleSheet("""
                QFrame {
                    border: 3px solid #28a745;
                    background-color: #f8fff9;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 3px solid #28a745;
                    background-color: #f0fff0;
                }
            """)
        elif self.is_selected:
            # 選択されたテーマ
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #0078d4;
                    background-color: #f0f8ff;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 2px solid #0078d4;
                    background-color: #e6f3ff;
                }
            """)
        else:
            # 未選択のテーマ
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #e0e0e0;
                    background-color: white;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 2px solid #0078d4;
                    background-color: #f8f9fa;
                }
            """)

    def set_selected(self, selected: bool):
        """選択状態の設定"""
        self.is_selected = selected
        self.update_selection_style()

    def set_current_theme(self, is_current: bool):
        """現在のテーマかどうかを設定"""
        self.is_current = is_current
        self.update_selection_style()

        # 現在のテーマの場合は選択状態にする
        if is_current:
            self.is_selected = True

    def on_mouse_press(self, event):
        """マウスクリック時の処理"""
        if event.button() == Qt.LeftButton:
            # 現在のテーマは選択解除できない
            if not self.is_current:
                self.theme_clicked.emit(self.theme_name)


class ThemeToggleButton(QToolButton):
    """テーマ切り替えトグルボタン(選択テーマのみ)"""

    theme_changed = Signal(str)  # 新しいテーマ名

    def __init__(self, theme_manager, parent: QWidget | None = None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.current_theme_index = 0
        self.selected_themes = []  # 選択されたテーマリスト
        self.available_themes = []

        self.setup_ui()
        self.load_themes()
        # 初期状態で現在のテーマを表示
        self.update_button_text()

    def set_selected_themes(self, themes: list[str]):
        """選択されたテーマリストを設定"""
        self.selected_themes = themes
        self.load_themes()  # テーマリストを再読み込み

    def setup_ui(self):
        """UIの設定"""
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setPopupMode(QToolButton.DelayedPopup)

        # アイコンの設定
        self.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        # メニューの作成
        self.create_theme_menu()

        # 初期テキストの設定
        self.update_button_text()

        # クリックイベントの接続
        self.clicked.connect(self.next_theme)

        # ▼マークを非表示にするスタイルシート
        self.setStyleSheet("""
            QToolButton::menu-button {
                width: 0px;
                border: none;
            }
        """)

    def create_theme_menu(self):
        """テーマメニューの作成"""
        self.theme_menu = QMenu(self)

    def show_theme_menu(self):
        """テーマメニューを表示"""
        if self.theme_menu and self.available_themes:
            # ボタンの位置にメニューを表示
            self.theme_menu.exec_(self.mapToGlobal(self.rect().bottomLeft()))

    def load_themes(self):
        """利用可能なテーマの読み込み"""
        try:
            # 選択されたテーマがある場合はそれのみ、なければ全テーマ
            theme_names = self.selected_themes or self.theme_manager.get_available_themes()

            self.available_themes = []

            # テーマ名からテーマ情報オブジェクトを作成
            for theme_name in theme_names:
                theme_info = self.theme_manager.get_theme_info(theme_name)
                if theme_info:
                    # SimpleThemeManagerのテーマ情報をThemeInfo形式に変換
                    from dataclasses import dataclass

                    @dataclass
                    class ThemeInfo:
                        name: str
                        display_name: str
                        description: str

                    self.available_themes.append(
                        ThemeInfo(
                            name=theme_name,
                            display_name=theme_info.get("display_name", theme_name),
                            description=theme_info.get("description", f"{theme_name} theme"),
                        )
                    )

            # 現在のテーマのインデックスを取得
            current_theme_name = self.theme_manager.get_current_theme()
            if current_theme_name:
                for i, theme_info in enumerate(self.available_themes):
                    if theme_info.name == current_theme_name:
                        self.current_theme_index = i
                        break
                else:
                    # 現在のテーマが見つからない場合は最初のテーマを選択
                    if self.available_themes:
                        self.current_theme_index = 0
            else:
                # 現在のテーマがない場合は最初のテーマを選択
                if self.available_themes:
                    self.current_theme_index = 0

            self.update_theme_menu()
            self.update_button_text()

        except Exception:
            # テーマ読み込み失敗時の処理
            self.available_themes = []
            self.update_button_text()  # ボタンテキストを更新

    def update_theme_menu(self):
        """テーマメニューの更新"""
        self.theme_menu.clear()
        for i, theme_info in enumerate(self.available_themes):
            action = QAction(theme_info.display_name, self)
            action.setData(i)
            action.triggered.connect(lambda checked, idx=i: self.on_theme_selected(idx))
            # 現在のテーマにチェックマーク
            if i == self.current_theme_index:
                action.setCheckable(True)
                action.setChecked(True)
            self.theme_menu.addAction(action)

    def update_button_text(self):
        """ボタンテキストの更新"""
        if self.available_themes:
            current_theme = self.available_themes[self.current_theme_index]
            self.setText(f"テーマ切替: {current_theme.name}")
        else:
            # テーマが読み込めない場合は現在のテーマを表示
            try:
                current_theme_name = self.theme_manager.get_current_theme()
                if current_theme_name:
                    self.setText(f"テーマ切替: {current_theme_name}")
                else:
                    self.setText("テーマ切替")
            except Exception:
                self.setText("テーマ切替")

    def on_theme_selected(self, theme_index: int):
        """テーマ選択時の処理"""
        if 0 <= theme_index < len(self.available_themes):
            theme_info = self.available_themes[theme_index]
            # テーマの適用
            if self.theme_manager.apply_theme(theme_info.name):
                self.current_theme_index = theme_index
                self.update_button_text()
                self.theme_changed.emit(theme_info.name)
                # メニューの更新
                self.update_theme_menu()

    def next_theme(self):
        """次のテーマに切り替え"""
        if len(self.available_themes) > 1:
            next_index = (self.current_theme_index + 1) % len(self.available_themes)
            self.on_theme_selected(next_index)
        elif len(self.available_themes) == 1:
            # テーマが1つしかない場合は何もしない
            pass
        else:
            # テーマがない場合はメニューを表示
            self.show_theme_menu()

    def previous_theme(self):
        """前のテーマに切り替え"""
        if len(self.available_themes) > 1:
            prev_index = (self.current_theme_index - 1) % len(self.available_themes)
            self.on_theme_selected(prev_index)


class AdvancedThemeSelector(QWidget):
    """高度なテーマ選択コンポーネント"""

    theme_applied = Signal(str)  # 適用されたテーマ名

    def __init__(self, theme_manager, parent: QWidget | None = None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setup_ui()

    def setup_ui(self):
        """UIの設定"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # トグルボタン
        self.toggle_button = ThemeToggleButton(self.theme_manager)
        self.toggle_button.theme_changed.connect(self.theme_applied.emit)
        layout.addWidget(self.toggle_button)

        # 詳細選択ボタン
        self.detail_button = QPushButton("詳細選択")
        self.detail_button.clicked.connect(self.open_theme_dialog)
        layout.addWidget(self.detail_button)

        # スペーサー
        layout.addStretch()

    def open_theme_dialog(self):
        """テーマ選択ダイアログを開く"""
        dialog = ThemeSelectionDialog(self.theme_manager, self)
        dialog.theme_selected.connect(self.on_theme_selected)
        dialog.exec()

    def on_theme_selected(self, theme_name: str):
        """テーマ選択時の処理"""
        self.theme_applied.emit(theme_name)
        # トグルボタンの更新
        self.toggle_button.load_themes()
