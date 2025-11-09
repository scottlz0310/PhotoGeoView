"""
BreadcrumbWidget フォールバック実装

breadcrumb_addressbarライブラリが利用できない場合の代替実装
"""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class BreadcrumbSegment(QPushButton):
    """ブレッドクラムセグメント"""

    def __init__(self, text: str, path: Path, parent=None):
        super().__init__(text, parent)
        self.path = path
        self.setFlat(True)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 4px 8px;
                margin: 0px 2px;
                background-color: transparent;
                color: #0066cc;
                text-decoration: underline;
            }
            QPushButton:hover {
                background-color: #e6f3ff;
                border-radius: 3px;
            }
            QPushButton:pressed {
                background-color: #cce6ff;
            }
        """)


class BreadcrumbSeparator(QLabel):
    """ブレッドクラム区切り文字"""

    def __init__(self, parent=None):
        super().__init__(">", parent)
        self.setStyleSheet("""
            QLabel {
                color: #666666;
                margin: 0px 4px;
                font-weight: normal;
            }
        """)


class BreadcrumbWidgetFallback(QWidget):
    """
    BreadcrumbWidget フォールバック実装

    breadcrumb_addressbarが利用できない場合の代替実装
    """

    # シグナル
    pathChanged = Signal(str)
    folderSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = Path.home()
        self.segments = []
        self.separators = []
        self.max_segments = 6  # 表示する最大セグメント数

        self.setup_ui()
        self.update_breadcrumb()

    def setup_ui(self):
        """UIをセットアップ"""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(0)

        # フレームでブレッドクラムを囲む
        self.frame = QFrame()
        self.frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 2px;
            }
        """)

        self.frame_layout = QHBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(4, 2, 4, 2)
        self.frame_layout.setSpacing(0)

        self.layout.addWidget(self.frame)
        self.layout.addStretch()

    def setPath(self, path: str):
        """パスを設定"""
        try:
            new_path = Path(path).resolve()
            if new_path != self.current_path:
                self.current_path = new_path
                self.update_breadcrumb()
                self.pathChanged.emit(str(self.current_path))
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid path: {path} - {e}")

    def getPath(self) -> str:
        """現在のパスを取得"""
        return str(self.current_path)

    def update_breadcrumb(self):
        """ブレッドクラム表示を更新"""
        # 既存のウィジェットをクリア
        self.clear_breadcrumb()

        # パス部分を取得
        parts = self.current_path.parts

        # セグメント数が多い場合は省略
        if len(parts) > self.max_segments:
            # 最初の部分
            self.add_segment(parts[0], Path(parts[0]))

            # 省略記号
            ellipsis = QLabel("...")
            ellipsis.setStyleSheet("color: #666666; margin: 0px 4px;")
            self.frame_layout.addWidget(ellipsis)
            self.separators.append(ellipsis)

            # 最後の数セグメント
            start_idx = len(parts) - (self.max_segments - 2)
            for i, part in enumerate(parts[start_idx:], start_idx):
                if i > start_idx:
                    self.add_separator()

                # パスを構築
                segment_path = Path(*parts[: i + 1])
                self.add_segment(part, segment_path)
        else:
            # 全セグメントを表示
            for i, part in enumerate(parts):
                if i > 0:
                    self.add_separator()

                # パスを構築
                segment_path = Path(*parts[: i + 1])
                self.add_segment(part, segment_path)

    def add_segment(self, text: str, path: Path):
        """セグメントを追加"""
        segment = BreadcrumbSegment(text, path)
        segment.clicked.connect(lambda: self.on_segment_clicked(path))
        self.frame_layout.addWidget(segment)
        self.segments.append(segment)

    def add_separator(self):
        """区切り文字を追加"""
        separator = BreadcrumbSeparator()
        self.frame_layout.addWidget(separator)
        self.separators.append(separator)

    def on_segment_clicked(self, path: Path):
        """セグメントクリック時の処理"""
        self.setPath(str(path))
        self.folderSelected.emit(str(path))

    def clear_breadcrumb(self):
        """ブレッドクラム表示をクリア"""
        # セグメントをクリア
        for segment in self.segments:
            segment.deleteLater()
        self.segments.clear()

        # 区切り文字をクリア
        for separator in self.separators:
            separator.deleteLater()
        self.separators.clear()


# breadcrumb_addressbarからのインポートを試行し、失敗した場合はフォールバックを使用
try:
    from breadcrumb_addressbar import BreadcrumbWidget
except (ImportError, AttributeError):
    BreadcrumbWidget = BreadcrumbWidgetFallback
