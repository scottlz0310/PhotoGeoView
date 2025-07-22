"""
フォルダナビゲーション機能を提供するモジュール
PhotoGeoView プロジェクト用のフォルダ管理機能
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QFileDialog,
    QFrame,
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QMutex
from PyQt6.QtGui import QIcon, QFont

from src.core.logger import get_logger
from src.core.settings import get_settings
from src.core.utils import normalize_path


class FolderNavigator(QWidget):
    """フォルダナビゲーションウィジェット"""

    # シグナル定義
    directory_selected = pyqtSignal(str)  # ディレクトリ選択時に発信
    directory_changed = pyqtSignal(str)  # ディレクトリ変更時に発信

    def __init__(self, parent=None):
        """
        FolderNavigatorの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # 現在のディレクトリ
        self._current_directory: str = ""

        # 履歴管理
        self._directory_history: List[str] = []
        self._history_index: int = -1
        self._max_history: int = 50  # 履歴の最大保存数

        # ナビゲーション状態
        self._is_navigating: bool = False

        # UI初期化
        self._init_ui()
        self._init_connections()

        # 初期ディレクトリを設定
        self._set_initial_directory()

        self.logger.debug("FolderNavigatorを初期化しました")

    def _init_ui(self) -> None:
        """UIの初期化"""
        # メインレイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # フォルダツリーのみを追加（アドレスバーとナビゲーションボタンは削除）
        self._init_folder_tree()
        layout.addWidget(self.folder_tree, 1)

    def _init_address_bar(self) -> None:
        """アドレスバーの初期化"""
        self.address_frame = QFrame()
        self.address_frame.setFrameStyle(QFrame.Shape.StyledPanel)

        address_layout = QHBoxLayout(self.address_frame)
        address_layout.setContentsMargins(5, 5, 5, 5)

        # フォルダ選択ボタン
        self.folder_button = QPushButton("📁")
        self.folder_button.setToolTip("フォルダを選択")
        self.folder_button.setMaximumWidth(30)

        # アドレスバー
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("フォルダパスを入力または選択してください")
        self.address_bar.setReadOnly(True)

        # アドレスバーに追加
        address_layout.addWidget(self.folder_button)
        address_layout.addWidget(self.address_bar)

    def _init_navigation_buttons(self) -> None:
        """ナビゲーションボタンの初期化"""
        self.nav_layout = QHBoxLayout()

        # 戻るボタン
        self.back_button = QPushButton("←")
        self.back_button.setToolTip("戻る")
        self.back_button.setMaximumWidth(30)
        self.back_button.setEnabled(False)

        # 進むボタン
        self.forward_button = QPushButton("→")
        self.forward_button.setToolTip("進む")
        self.forward_button.setMaximumWidth(30)
        self.forward_button.setEnabled(False)

        # 上位フォルダボタン
        self.up_button = QPushButton("↑")
        self.up_button.setToolTip("上位フォルダ")
        self.up_button.setMaximumWidth(30)
        self.up_button.setEnabled(False)

        # ナビゲーションレイアウトに追加
        self.nav_layout.addWidget(self.back_button)
        self.nav_layout.addWidget(self.forward_button)
        self.nav_layout.addWidget(self.up_button)
        self.nav_layout.addStretch()

    def _init_folder_tree(self) -> None:
        """フォルダツリーの初期化"""
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel("フォルダ")
        self.folder_tree.setColumnCount(1)
        self.folder_tree.setRootIsDecorated(True)
        self.folder_tree.setAlternatingRowColors(True)

        # フォルダツリーの設定
        self.folder_tree.setMinimumHeight(200)
        self.folder_tree.setExpandsOnDoubleClick(True)
        self.folder_tree.setItemsExpandable(True)

        # フォルダアイコンを設定
        self._setup_folder_icons()

    def _setup_folder_icons(self) -> None:
        """フォルダアイコンの設定"""
        # システムアイコンを使用（利用可能な場合）
        try:
            # フォルダアイコンを設定
            folder_icon = self.style().standardIcon(
                self.style().StandardPixmap.SP_DirIcon
            )
            self.folder_tree.setIconSize(
                folder_icon.actualSize(folder_icon.availableSizes()[0])
            )
        except Exception as e:
            self.logger.debug(f"フォルダアイコンの設定に失敗しました: {e}")

    def _init_connections(self) -> None:
        """シグナル・スロット接続の初期化"""
        # フォルダツリー接続のみ（ボタンは削除済み）
        self.folder_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.folder_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)

    def _set_initial_directory(self) -> None:
        """初期ディレクトリを設定"""
        try:
            # 設定から初期ディレクトリを取得
            initial_dir = self.settings.get("app.initial_directory", "")

            if initial_dir and os.path.exists(initial_dir):
                self.set_directory(initial_dir)
            else:
                # デフォルトはホームディレクトリ
                home_dir = str(Path.home())
                self.set_directory(home_dir)

        except Exception as e:
            self.logger.error(f"初期ディレクトリの設定に失敗しました: {e}")
            # フォールバック
            self.set_directory(str(Path.home()))

    def set_directory(self, directory_path: str) -> bool:
        """
        ディレクトリを設定

        Args:
            directory_path: ディレクトリパス

        Returns:
            設定成功の場合True
        """
        try:
            if not os.path.exists(directory_path):
                self.logger.error(f"ディレクトリが存在しません: {directory_path}")
                return False

            if not os.path.isdir(directory_path):
                self.logger.error(f"パスがディレクトリではありません: {directory_path}")
                return False

            # パスを正規化
            normalized_path = normalize_path(directory_path)

            # 現在のディレクトリと同じ場合は何もしない
            if normalized_path == self._current_directory:
                return True

            self.logger.info(f"ディレクトリを設定: {normalized_path}")

            # 現在のディレクトリを更新
            old_directory = self._current_directory
            self._current_directory = normalized_path

            # 履歴に追加（ナビゲーション中でない場合のみ）
            if old_directory:  # 初回設定時は履歴に追加しない
                self._add_to_history(old_directory)

            # UIを更新
            self._update_address_bar()
            self._update_navigation_buttons()
            self._update_folder_tree()

            # シグナルを発信
            self.directory_changed.emit(normalized_path)
            self.directory_selected.emit(normalized_path)

            return True

        except Exception as e:
            self.logger.error(
                f"ディレクトリの設定に失敗しました: {directory_path}, エラー: {e}"
            )
            return False

    def _update_address_bar(self) -> None:
        """アドレスバーを更新（削除済みのため何もしない）"""
        pass

    def _update_folder_tree(self) -> None:
        """フォルダツリーを更新"""
        try:
            self.folder_tree.clear()

            if not self._current_directory:
                return

            # ルートアイテムを作成
            root_item = self._create_tree_item(self._current_directory, is_root=True)
            self.folder_tree.addTopLevelItem(root_item)

            # サブディレクトリを追加
            self._add_subdirectories(root_item, self._current_directory)

            # ルートアイテムを展開
            root_item.setExpanded(True)

            # ルートアイテムを選択
            self.folder_tree.setCurrentItem(root_item)

        except Exception as e:
            self.logger.error(f"フォルダツリーの更新に失敗しました: {e}")

    def _create_tree_item(self, path: str, is_root: bool = False) -> QTreeWidgetItem:
        """
        ツリーアイテムを作成

        Args:
            path: ディレクトリパス
            is_root: ルートアイテムかどうか

        Returns:
            ツリーアイテム
        """
        try:
            item = QTreeWidgetItem()

            if is_root:
                # ルートアイテムの場合は絶対パスを表示
                display_name = path
            else:
                # サブディレクトリの場合はディレクトリ名のみ表示
                display_name = Path(path).name

            item.setText(0, display_name)
            item.setData(0, Qt.ItemDataRole.UserRole, path)

            # フォルダアイコンを設定
            try:
                folder_icon = self.style().standardIcon(
                    self.style().StandardPixmap.SP_DirIcon
                )
                item.setIcon(0, folder_icon)
            except Exception:
                pass

            return item

        except Exception as e:
            self.logger.error(f"ツリーアイテムの作成に失敗しました: {e}")
            return QTreeWidgetItem()

    def _add_subdirectories(
        self, parent_item: QTreeWidgetItem, parent_path: str
    ) -> None:
        """
        サブディレクトリを追加

        Args:
            parent_item: 親アイテム
            parent_path: 親ディレクトリパス
        """
        try:
            # サブディレクトリを取得
            subdirs = []
            try:
                for item in os.listdir(parent_path):
                    item_path = os.path.join(parent_path, item)
                    if os.path.isdir(item_path) and not item.startswith("."):
                        subdirs.append((item, item_path))
            except PermissionError:
                # アクセス権限がない場合はスキップ
                return
            except Exception as e:
                self.logger.debug(
                    f"サブディレクトリの取得に失敗しました: {parent_path}, エラー: {e}"
                )
                return

            # 名前でソート
            subdirs.sort(key=lambda x: x[0].lower())

            # サブディレクトリを追加
            for name, path in subdirs:
                child_item = self._create_tree_item(path)
                parent_item.addChild(child_item)

                # 子ディレクトリも追加（遅延読み込み）
                child_item.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )

        except Exception as e:
            self.logger.error(f"サブディレクトリの追加に失敗しました: {e}")

    def _select_folder(self) -> None:
        """フォルダ選択ダイアログを表示"""
        try:
            current_dir = (
                self._current_directory if self._current_directory else str(Path.home())
            )

            directory = QFileDialog.getExistingDirectory(
                self, "フォルダを選択", current_dir, QFileDialog.Option.ShowDirsOnly
            )

            if directory:
                self.set_directory(directory)

        except Exception as e:
            self.logger.error(f"フォルダ選択に失敗しました: {e}")

    def _go_back(self) -> None:
        """履歴を戻る"""
        try:
            if self._history_index > 0:
                self._history_index -= 1
                directory = self._directory_history[self._history_index]
                self._navigate_to_directory(directory)

        except Exception as e:
            self.logger.error(f"履歴の戻るに失敗しました: {e}")

    def _go_forward(self) -> None:
        """履歴を進む"""
        try:
            if self._history_index < len(self._directory_history) - 1:
                self._history_index += 1
                directory = self._directory_history[self._history_index]
                self._navigate_to_directory(directory)

        except Exception as e:
            self.logger.error(f"履歴の進むに失敗しました: {e}")

    def _go_up(self) -> None:
        """上位ディレクトリに移動"""
        try:
            if self._current_directory:
                parent_dir = str(Path(self._current_directory).parent)
                if parent_dir != self._current_directory:
                    self.set_directory(parent_dir)

        except Exception as e:
            self.logger.error(f"上位ディレクトリへの移動に失敗しました: {e}")

    def _navigate_to_directory(self, directory_path: str) -> None:
        """
        指定されたディレクトリに移動（履歴更新なし）

        Args:
            directory_path: ディレクトリパス
        """
        try:
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                return

            self._is_navigating = True

            # 現在のディレクトリを更新
            self._current_directory = normalize_path(directory_path)

            # UIを更新
            self._update_address_bar()
            self._update_navigation_buttons()
            self._update_folder_tree()

            # シグナルを発信
            self.directory_changed.emit(self._current_directory)

            self._is_navigating = False

        except Exception as e:
            self.logger.error(f"ディレクトリへの移動に失敗しました: {e}")
            self._is_navigating = False

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        ツリーアイテムクリック時の処理

        Args:
            item: クリックされたアイテム
            column: クリックされた列
        """
        try:
            if self._is_navigating:
                return

            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and path != self._current_directory:
                self.set_directory(path)

        except Exception as e:
            self.logger.error(f"ツリーアイテムクリックの処理に失敗しました: {e}")

    def _on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        ツリーアイテムダブルクリック時の処理

        Args:
            item: ダブルクリックされたアイテム
            column: ダブルクリックされた列
        """
        try:
            if self._is_navigating:
                return

            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and path != self._current_directory:
                self.set_directory(path)

        except Exception as e:
            self.logger.error(f"ツリーアイテムダブルクリックの処理に失敗しました: {e}")

    def get_current_directory(self) -> str:
        """
        現在のディレクトリを取得

        Returns:
            現在のディレクトリパス
        """
        return self._current_directory

    def get_directory_history(self) -> List[str]:
        """
        ディレクトリ履歴を取得

        Returns:
            ディレクトリ履歴リスト
        """
        return self._directory_history.copy()

    def clear_history(self) -> None:
        """履歴をクリア"""
        try:
            self._directory_history.clear()
            self._history_index = -1
            self._update_navigation_buttons()
            self.logger.info("ディレクトリ履歴をクリアしました")

        except Exception as e:
            self.logger.error(f"履歴のクリアに失敗しました: {e}")

    def can_go_back(self) -> bool:
        """戻ることができるかチェック"""
        return self._history_index > 0

    def can_go_forward(self) -> bool:
        """進むことができるかチェック"""
        return self._history_index < len(self._directory_history) - 1

    def go_back(self) -> bool:
        """履歴の前のディレクトリに戻る"""
        try:
            if self.can_go_back():
                self._history_index -= 1
                directory = self._directory_history[self._history_index]
                self._is_navigating = True
                self.set_directory(directory)
                self._is_navigating = False
                self._update_navigation_buttons()
                self.logger.info(f"履歴で戻りました: {directory}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"戻る操作に失敗しました: {e}")
            self._is_navigating = False
            return False

    def go_forward(self) -> bool:
        """履歴の次のディレクトリに進む"""
        try:
            if self.can_go_forward():
                self._history_index += 1
                directory = self._directory_history[self._history_index]
                self._is_navigating = True
                self.set_directory(directory)
                self._is_navigating = False
                self._update_navigation_buttons()
                self.logger.info(f"履歴で進みました: {directory}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"進む操作に失敗しました: {e}")
            self._is_navigating = False
            return False

    def go_up(self) -> bool:
        """上位ディレクトリに移動"""
        try:
            current_path = Path(self._current_directory)
            parent_path = current_path.parent
            if parent_path != current_path:  # ルートディレクトリでない場合
                self.set_directory(str(parent_path))
                self.logger.info(f"上位ディレクトリに移動: {parent_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"上位ディレクトリへの移動に失敗しました: {e}")
            return False

    def _add_to_history(self, directory: str) -> None:
        """ディレクトリを履歴に追加"""
        try:
            if self._is_navigating:
                return

            # 現在と同じディレクトリは追加しない
            if directory == self._current_directory:
                return

            # 履歴の現在位置以降を削除（新しいブランチを作る）
            if self._history_index >= 0 and self._history_index < len(self._directory_history) - 1:
                self._directory_history = self._directory_history[:self._history_index + 1]

            # 新しいディレクトリを履歴に追加
            self._directory_history.append(directory)
            self._history_index = len(self._directory_history) - 1

            # 履歴の最大数を超えた場合、古いものを削除
            if len(self._directory_history) > self._max_history:
                self._directory_history = self._directory_history[1:]
                self._history_index -= 1

            self._update_navigation_buttons()

        except Exception as e:
            self.logger.error(f"履歴への追加に失敗しました: {e}")

    def _update_navigation_buttons(self) -> None:
        """ナビゲーションボタンの状態を更新（空実装）"""
        # ツールバーから制御するため、ここでは何もしない
        pass
