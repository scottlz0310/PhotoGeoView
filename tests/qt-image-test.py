#!/usr/bin/env python3
"""
PyQt6ネイティブ画像処理デバッグコード（Pillow不使用）
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QImageReader, QImageWriter
import traceback

class ImageProcessor:
    """PyQt6ネイティブの画像処理クラス"""

    @staticmethod
    def get_supported_formats():
        """サポートされている画像フォーマット一覧を取得"""
        reader = QImageReader()
        supported_formats = []
        for fmt in reader.supportedImageFormats():
            supported_formats.append(fmt.data().decode())
        return supported_formats

    @staticmethod
    def load_image_safe(image_path):
        """安全な画像読み込み"""
        try:
            # QImageReaderを使用（より詳細なエラー情報が取得可能）
            reader = QImageReader(image_path)

            if not reader.canRead():
                return None, f"読み込み不可: {reader.errorString()}"

            # 画像情報を事前に取得
            size = reader.size()
            format_name = reader.format().data().decode()

            # 実際に画像を読み込み
            image = reader.read()

            if image.isNull():
                return None, f"読み込み失敗: {reader.errorString()}"

            return image, f"成功 - サイズ: {size.width()}x{size.height()}, フォーマット: {format_name}"

        except Exception as e:
            return None, f"例外エラー: {str(e)}"

    @staticmethod
    def create_thumbnail(image, size, method='smooth'):
        """サムネイル生成（複数の方法をテスト）"""
        if image.isNull():
            return None, "元画像がNull"

        try:
            # QImageからQPixmapに変換
            pixmap = QPixmap.fromImage(image)

            # スケーリング方法を選択
            if method == 'smooth':
                transform_mode = Qt.TransformationMode.SmoothTransformation
            elif method == 'fast':
                transform_mode = Qt.TransformationMode.FastTransformation
            else:
                transform_mode = Qt.TransformationMode.SmoothTransformation

            # アスペクト比を保持してスケール
            scaled_pixmap = pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                transform_mode
            )

            if scaled_pixmap.isNull():
                return None, "スケーリング失敗"

            return scaled_pixmap, f"成功 - {scaled_pixmap.width()}x{scaled_pixmap.height()}"

        except Exception as e:
            return None, f"サムネイル生成エラー: {str(e)}"

    @staticmethod
    def create_thumbnail_with_painter(image, size):
        """QPainterを使用したサムネイル生成"""
        if image.isNull():
            return None, "元画像がNull"

        try:
            # 出力用のQImageを作成
            output_image = QImage(size, size, QImage.Format.Format_ARGB32)
            output_image.fill(Qt.GlobalColor.transparent)

            # アスペクト比計算
            orig_width = image.width()
            orig_height = image.height()

            if orig_width > orig_height:
                new_width = size
                new_height = int((orig_height * size) / orig_width)
            else:
                new_height = size
                new_width = int((orig_width * size) / orig_height)

            # 中央配置の計算
            x = (size - new_width) // 2
            y = (size - new_height) // 2

            # QPainterで描画
            painter = QPainter(output_image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            # スケールして描画
            painter.drawImage(x, y, image.scaled(new_width, new_height, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
            painter.end()

            pixmap = QPixmap.fromImage(output_image)
            return pixmap, f"成功（QPainter） - {pixmap.width()}x{pixmap.height()}"

        except Exception as e:
            return None, f"QPainterサムネイル生成エラー: {str(e)}"


class PyQt6ImageDebugger(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6ネイティブ画像処理デバッガー")
        self.setGeometry(100, 100, 1000, 700)

        self.processor = ImageProcessor()
        self.current_image = None
        self.test_image_path = None

        self.setup_ui()
        self.find_test_image()

    def setup_ui(self):
        """UI設定"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # サポートフォーマット表示
        formats = self.processor.get_supported_formats()
        format_label = QLabel(f"サポート形式: {', '.join(formats)}")
        format_label.setWordWrap(True)
        layout.addWidget(format_label)

        # ボタンエリア
        button_layout = QHBoxLayout()

        btn_load = QPushButton("1. 画像読み込み詳細テスト")
        btn_load.clicked.connect(self.test_detailed_loading)
        button_layout.addWidget(btn_load)

        btn_thumb1 = QPushButton("2a. 標準サムネイル")
        btn_thumb1.clicked.connect(lambda: self.test_thumbnail_generation('smooth'))
        button_layout.addWidget(btn_thumb1)

        btn_thumb2 = QPushButton("2b. 高速サムネイル")
        btn_thumb2.clicked.connect(lambda: self.test_thumbnail_generation('fast'))
        button_layout.addWidget(btn_thumb2)

        btn_thumb3 = QPushButton("2c. Painterサムネイル")
        btn_thumb3.clicked.connect(self.test_painter_thumbnail)
        button_layout.addWidget(btn_thumb3)

        layout.addLayout(button_layout)

        # ログエリア
        self.log_label = QLabel("ログがここに表示されます...")
        self.log_label.setWordWrap(True)
        self.log_label.setStyleSheet("background-color: #f8f8f8; padding: 10px; border: 1px solid #ddd;")
        self.log_label.setMaximumHeight(150)
        layout.addWidget(self.log_label)

        # 画像表示エリア
        image_layout = QHBoxLayout()

        # オリジナル画像
        self.original_label = QLabel("オリジナル画像")
        self.original_label.setMinimumSize(300, 200)
        self.original_label.setStyleSheet("border: 2px solid #4CAF50; background: white;")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.original_label)

        # サムネイル画像
        self.thumbnail_label = QLabel("サムネイル")
        self.thumbnail_label.setMinimumSize(200, 200)
        self.thumbnail_label.setStyleSheet("border: 2px solid #FF9800; background: white;")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.thumbnail_label)

        layout.addLayout(image_layout)

    def find_test_image(self):
        """テスト用画像を探す"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']

        current_dir = Path('.')
        for ext in image_extensions:
            for img_file in current_dir.rglob(f'*{ext}'):
                if img_file.is_file() and img_file.stat().st_size > 0:
                    self.test_image_path = str(img_file)
                    self.log(f"テスト画像発見: {self.test_image_path}")
                    return

        self.log("⚠️ テスト用画像が見つかりません")

    def log(self, message):
        """ログ出力"""
        current = self.log_label.text()
        if current == "ログがここに表示されます...":
            self.log_label.setText(message)
        else:
            self.log_label.setText(f"{current}\n{message}")

        # スクロール（最新を表示）
        self.log_label.repaint()

    def test_detailed_loading(self):
        """詳細な画像読み込みテスト"""
        if not self.test_image_path:
            self.log("❌ テスト画像パスなし")
            return

        self.log(f"📁 テスト開始: {Path(self.test_image_path).name}")

        # ファイル基本情報
        file_size = os.path.getsize(self.test_image_path) / 1024  # KB
        self.log(f"📊 ファイルサイズ: {file_size:.1f}KB")

        # QImageReaderでの詳細読み込み
        image, message = self.processor.load_image_safe(self.test_image_path)
        self.log(f"🖼️ 読み込み結果: {message}")

        if image:
            self.current_image = image

            # オリジナル画像を表示
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(
                self.original_label.size() - self.original_label.contentsMargins(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.original_label.setPixmap(scaled)

            # 画像の詳細情報
            self.log(f"🔍 画像詳細: {image.width()}x{image.height()}, フォーマット: {image.format()}, 深度: {image.depth()}bit")
        else:
            self.current_image = None
            self.original_label.setText("読み込み失敗")

    def test_thumbnail_generation(self, method):
        """サムネイル生成テスト"""
        if not self.current_image:
            self.log("❌ 先に画像を読み込んでください")
            return

        self.log(f"🔄 サムネイル生成開始 ({method})")

        thumbnail, message = self.processor.create_thumbnail(self.current_image, 128, method)
        self.log(f"✂️ サムネイル結果: {message}")

        if thumbnail:
            self.thumbnail_label.setPixmap(thumbnail)
        else:
            self.thumbnail_label.setText("サムネイル失敗")

    def test_painter_thumbnail(self):
        """QPainter方式のサムネイル生成テスト"""
        if not self.current_image:
            self.log("❌ 先に画像を読み込んでください")
            return

        self.log("🎨 QPainterサムネイル生成開始")

        thumbnail, message = self.processor.create_thumbnail_with_painter(self.current_image, 128)
        self.log(f"🖌️ Painterサムネイル結果: {message}")

        if thumbnail:
            self.thumbnail_label.setPixmap(thumbnail)
        else:
            self.thumbnail_label.setText("Painterサムネイル失敗")


def main():
    app = QApplication(sys.argv)

    print("=== PyQt6ネイティブ画像処理デバッガー ===")
    print(f"Qt Version: {app.instance().applicationVersion()}")

    # QImageで利用可能なフォーマット確認
    reader = QImageReader()
    print(f"サポート読み込みフォーマット: {[fmt.data().decode() for fmt in reader.supportedImageFormats()]}")

    window = PyQt6ImageDebugger()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
