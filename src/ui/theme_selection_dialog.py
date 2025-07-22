"""
テーマ選択ダイアログ
複数テーマを選択可能なダイアログウィンドウ
"""

from typing import List, Dict
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QCheckBox,
    QPushButton,
    QLabel,
    QScrollArea,
    QWidget,
    QFrame,
    QGroupBox,
    QButtonGroup,
    QRadioButton,
    QMessageBox,
    QSplitter,
    QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor

from src.core.logger import get_logger
from .theme_manager import ThemeManager


class ThemeSelectionDialog(QDialog):
    """テーマ選択ダイアログクラス"""

    # シグナル定義
    themes_applied = pyqtSignal(list)  # テーマ適用時に発信

    def __init__(self, theme_manager: ThemeManager, parent=None):
        """
        ダイアログの初期化

        Args:
            theme_manager: ThemeManagerインスタンス
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.theme_manager = theme_manager
        self.logger = get_logger(__name__)
        self.checkboxes = {}  # テーマ名 -> QCheckBox のマッピング
        self.preview_widget = None
        self.preview_theme = None

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self) -> None:
        """UIの初期化"""
        self.setWindowTitle("テーマ設定")
        self.setModal(True)
        self.resize(800, 600)

        # メインレイアウト
        main_layout = QVBoxLayout(self)

        # 説明ラベル
        info_label = QLabel(
            "使用したいテーマを選択してください。\n"
            "ツールバーのテーマ切替ボタンで、選択されたテーマを順次切り替えます。"
        )
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # 水平スプリッター（テーマ選択 | プレビュー）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左パネル：テーマ選択
        self._init_theme_selection_panel(splitter)

        # 右パネル：プレビュー
        self._init_preview_panel(splitter)

        # スプリッターの初期サイズ設定
        splitter.setSizes([500, 300])

        # ボタンパネル
        self._init_button_panel(main_layout)

    def _init_theme_selection_panel(self, parent) -> None:
        """テーマ選択パネルの初期化"""
        # スクロール可能なウィジェット
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        parent.addWidget(scroll_area)

        # スクロール内容ウィジェット
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 全選択・全解除ボタン
        control_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("すべて選択")
        self.select_all_btn.clicked.connect(self._select_all_themes)
        control_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("すべて解除")
        self.select_none_btn.clicked.connect(self._select_no_themes)
        control_layout.addWidget(self.select_none_btn)

        control_layout.addStretch()
        scroll_layout.addLayout(control_layout)

        # テーマをカテゴリ別に分類
        theme_categories = self._categorize_themes()

        # カテゴリ別にグループボックスを作成
        for category_name, themes in theme_categories.items():
            group_box = QGroupBox(category_name)
            group_layout = QGridLayout(group_box)

            row, col = 0, 0
            for theme_name in themes:
                theme_info = self.theme_manager.get_theme_info(theme_name)

                # チェックボックス
                checkbox = QCheckBox(theme_info["display_name"])
                checkbox.setToolTip(theme_info["description"])
                checkbox.stateChanged.connect(
                    lambda state, name=theme_name: self._on_theme_check_changed(name, state)
                )

                # プレビューボタン
                preview_btn = QPushButton("プレビュー")
                preview_btn.setMaximumWidth(80)
                preview_btn.clicked.connect(
                    lambda checked, name=theme_name: self._preview_theme(name)
                )

                # レイアウトに追加
                item_layout = QHBoxLayout()
                item_layout.addWidget(checkbox)
                item_layout.addWidget(preview_btn)
                item_layout.addStretch()

                item_widget = QWidget()
                item_widget.setLayout(item_layout)

                group_layout.addWidget(item_widget, row, col)

                # チェックボックスを保存
                self.checkboxes[theme_name] = checkbox

                col += 1
                if col >= 2:  # 2列レイアウト
                    col = 0
                    row += 1

            scroll_layout.addWidget(group_box)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)

    def _init_preview_panel(self, parent) -> None:
        """プレビューパネルの初期化"""
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        preview_layout = QVBoxLayout(preview_frame)

        # プレビューラベル
        preview_label = QLabel("テーマプレビュー")
        preview_label.setFont(QFont("", 12, QFont.Weight.Bold))
        preview_layout.addWidget(preview_label)

        # プレビューウィジェット
        self.preview_widget = QWidget()
        self.preview_widget.setMinimumHeight(200)
        self._create_preview_content()
        preview_layout.addWidget(self.preview_widget)

        # プレビュー情報
        self.preview_info = QTextEdit()
        self.preview_info.setMaximumHeight(100)
        self.preview_info.setReadOnly(True)
        self.preview_info.setText("テーマを選択してプレビューしてください")
        preview_layout.addWidget(self.preview_info)

        parent.addWidget(preview_frame)

    def _create_preview_content(self) -> None:
        """プレビュー用のウィジェットコンテンツを作成"""
        layout = QVBoxLayout(self.preview_widget)

        # サンプルウィジェット
        sample_label = QLabel("サンプルテキスト")
        sample_button = QPushButton("サンプルボタン")
        sample_checkbox = QCheckBox("サンプルチェックボックス")

        layout.addWidget(sample_label)
        layout.addWidget(sample_button)
        layout.addWidget(sample_checkbox)
        layout.addStretch()

    def _init_button_panel(self, parent_layout) -> None:
        """ボタンパネルの初期化"""
        button_layout = QHBoxLayout()

        # リセットボタン
        reset_btn = QPushButton("リセット")
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        # キャンセルボタン
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # 適用ボタン
        apply_btn = QPushButton("適用")
        apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_btn)

        # OKボタン
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._ok_clicked)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        parent_layout.addLayout(button_layout)

    def _categorize_themes(self) -> Dict[str, List[str]]:
        """テーマをカテゴリ別に分類"""
        categories = {
            "基本テーマ": [],
            "カラーテーマ": [],
            "ニュートラルテーマ": []
        }

        for theme_name in self.theme_manager.get_available_themes():
            theme_info = self.theme_manager.get_theme_info(theme_name)
            category = theme_info.get("category", "unknown")

            if category in ["dark", "light"]:
                categories["基本テーマ"].append(theme_name)
            elif category == "color":
                categories["カラーテーマ"].append(theme_name)
            elif category == "neutral":
                categories["ニュートラルテーマ"].append(theme_name)
            else:
                categories["カラーテーマ"].append(theme_name)  # デフォルト

        return categories

    def _load_current_settings(self) -> None:
        """現在の設定を読み込み"""
        enabled_themes = self.theme_manager.get_enabled_themes()

        for theme_name, checkbox in self.checkboxes.items():
            checkbox.setChecked(theme_name in enabled_themes)

    def _select_all_themes(self) -> None:
        """すべてのテーマを選択"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def _select_no_themes(self) -> None:
        """すべてのテーマを解除"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def _reset_to_defaults(self) -> None:
        """デフォルト設定にリセット"""
        # すべてのテーマを有効にする
        self._select_all_themes()

    def _on_theme_check_changed(self, theme_name: str, state: int) -> None:
        """テーマチェック状態変更時の処理"""
        # 最低1つのテーマは選択されている必要がある
        checked_count = sum(1 for cb in self.checkboxes.values() if cb.isChecked())

        if checked_count == 0:
            # 0個の場合は変更を取り消す
            self.checkboxes[theme_name].setChecked(True)
            QMessageBox.warning(
                self,
                "警告",
                "最低1つのテーマを選択する必要があります。"
            )

    def _preview_theme(self, theme_name: str) -> None:
        """テーマをプレビュー"""
        try:
            self.preview_theme = theme_name

            # プレビュー情報を更新
            theme_info = self.theme_manager.get_theme_info(theme_name)
            info_text = f"""
テーマ名: {theme_info['display_name']}
説明: {theme_info['description']}
カテゴリ: {theme_info.get('category', '不明')}

このテーマは現在プレビュー中です。
「適用」ボタンを押すと設定が保存されます。
            """.strip()
            self.preview_info.setText(info_text)

            # 簡単なスタイル適用でのプレビュー（制限的だが動作する）
            if theme_name == "dark":
                self.preview_widget.setStyleSheet("""
                    QWidget { background-color: #2b2b2b; color: #ffffff; }
                    QPushButton { background-color: #404040; border: 1px solid #555; padding: 5px; }
                """)
            elif theme_name == "light":
                self.preview_widget.setStyleSheet("""
                    QWidget { background-color: #ffffff; color: #000000; }
                    QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; padding: 5px; }
                """)
            else:
                # カラーテーマの場合はシンプルな色を適用
                color_map = {
                    "blue": "#1e3a8a", "green": "#166534", "purple": "#6b21a8",
                    "orange": "#c2410c", "red": "#dc2626", "pink": "#db2777",
                    "yellow": "#ca8a04", "brown": "#92400e", "gray": "#374151",
                    "cyan": "#0891b2", "teal": "#0d9488", "indigo": "#4338ca",
                    "lime": "#65a30d", "amber": "#d97706"
                }
                color = color_map.get(theme_name, "#374151")
                self.preview_widget.setStyleSheet(f"""
                    QWidget {{ background-color: {color}; color: white; }}
                    QPushButton {{ background-color: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); padding: 5px; }}
                """)

            self.logger.debug(f"テーマをプレビューしました: {theme_name}")

        except Exception as e:
            self.logger.error(f"テーマプレビューに失敗しました: {e}")

    def _apply_settings(self) -> None:
        """設定を適用"""
        selected_themes = [
            theme_name for theme_name, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]

        if not selected_themes:
            QMessageBox.warning(
                self,
                "警告",
                "最低1つのテーマを選択してください。"
            )
            return

        # テーマ設定を適用
        if self.theme_manager.set_enabled_themes(selected_themes):
            self.themes_applied.emit(selected_themes)
            self.logger.info(f"テーマ設定を適用しました: {selected_themes}")
        else:
            QMessageBox.critical(
                self,
                "エラー",
                "テーマ設定の適用に失敗しました。"
            )

    def _ok_clicked(self) -> None:
        """OKボタンクリック時の処理"""
        self._apply_settings()
        self.accept()

    def get_selected_themes(self) -> List[str]:
        """選択されたテーマリストを取得"""
        return [
            theme_name for theme_name, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        ]
