#!/usr/bin/env python3
"""
PhotoGeoView 画像表示・サムネイル生成デバッグ用テストコード
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
import traceback

class ImageDebugTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Debug Tester")
        self.setGeometry(100, 100, 800, 600)
        
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # テスト画像パス（適宜変更してください）
        self.test_image_path = None
        
        # ボタン
        btn_test_load = QPushButton("1. 画像読み込みテスト")
        btn_test_load.clicked.connect(self.test_image_loading)
        layout.addWidget(btn_test_load)
        
        btn_test_thumbnail = QPushButton("2. サムネイル生成テスト")
        btn_test_thumbnail.clicked.connect(self.test_thumbnail_generation)
        layout.addWidget(btn_test_thumbnail)
        
        btn_test_display = QPushButton("3. 画像表示テスト")
        btn_test_display.clicked.connect(self.test_image_display)
        layout.addWidget(btn_test_display)
        
        # ログ表示用ラベル
        self.log_label = QLabel("ログがここに表示されます")
        self.log_label.setWordWrap(True)
        self.log_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        layout.addWidget(self.log_label)
        
        # 画像表示用ラベル
        self.image_label = QLabel("画像がここに表示されます")
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        
        # テスト用画像パスを探す
        self.find_test_image()
    
    def find_test_image(self):
        """テスト用画像を探す"""
        # 一般的な画像ファイルの拡張子
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
        
        # 現在のディレクトリから画像を探す
        current_dir = Path('.')
        for ext in image_extensions:
            for img_file in current_dir.glob(f'**/*{ext}'):
                if img_file.is_file():
                    self.test_image_path = str(img_file)
                    self.log(f"テスト用画像を発見: {self.test_image_path}")
                    return
        
        self.log("テスト用画像が見つかりません。手動で画像パスを設定してください。")
    
    def log(self, message):
        """ログメッセージを表示"""
        current_text = self.log_label.text()
        if current_text == "ログがここに表示されます":
            self.log_label.setText(message)
        else:
            self.log_label.setText(f"{current_text}\n{message}")
    
    def test_image_loading(self):
        """画像読み込みテスト"""
        if not self.test_image_path:
            self.log("❌ テスト画像パスが設定されていません")
            return
        
        try:
            # ファイル存在確認
            if not os.path.exists(self.test_image_path):
                self.log(f"❌ ファイルが存在しません: {self.test_image_path}")
                return
            
            # ファイルサイズ確認
            file_size = os.path.getsize(self.test_image_path)
            self.log(f"✅ ファイル存在確認 OK: {self.test_image_path} ({file_size} bytes)")
            
            # QPixmapで読み込みテスト
            pixmap = QPixmap(self.test_image_path)
            if pixmap.isNull():
                self.log("❌ QPixmapでの読み込み失敗")
                return
            
            self.log(f"✅ QPixmap読み込み OK: {pixmap.width()}x{pixmap.height()}")
            
            # QImageで読み込みテスト
            qimage = QImage(self.test_image_path)
            if qimage.isNull():
                self.log("❌ QImageでの読み込み失敗")
                return
            
            self.log(f"✅ QImage読み込み OK: {qimage.width()}x{qimage.height()}, Format: {qimage.format()}")
            
        except Exception as e:
            self.log(f"❌ 画像読み込みエラー: {str(e)}")
            traceback.print_exc()
    
    def test_thumbnail_generation(self):
        """サムネイル生成テスト"""
        if not self.test_image_path:
            self.log("❌ テスト画像パスが設定されていません")
            return
        
        try:
            # オリジナル画像読み込み
            pixmap = QPixmap(self.test_image_path)
            if pixmap.isNull():
                self.log("❌ オリジナル画像の読み込み失敗")
                return
            
            original_size = (pixmap.width(), pixmap.height())
            self.log(f"オリジナルサイズ: {original_size}")
            
            # サムネイル生成（複数のサイズでテスト）
            thumbnail_sizes = [64, 128, 256]
            
            for size in thumbnail_sizes:
                try:
                    # アスペクト比を保持してリサイズ
                    thumbnail = pixmap.scaled(
                        size, size, 
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    if thumbnail.isNull():
                        self.log(f"❌ サムネイル生成失敗 (サイズ: {size})")
                    else:
                        self.log(f"✅ サムネイル生成成功 {size}x{size}: {thumbnail.width()}x{thumbnail.height()}")
                
                except Exception as e:
                    self.log(f"❌ サムネイル生成エラー (サイズ: {size}): {str(e)}")
            
        except Exception as e:
            self.log(f"❌ サムネイル生成テストエラー: {str(e)}")
            traceback.print_exc()
    
    def test_image_display(self):
        """画像表示テスト"""
        if not self.test_image_path:
            self.log("❌ テスト画像パスが設定されていません")
            return
        
        try:
            # 画像読み込み
            pixmap = QPixmap(self.test_image_path)
            if pixmap.isNull():
                self.log("❌ 画像表示用の読み込み失敗")
                return
            
            # ラベルサイズに合わせてスケール
            label_size = self.image_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size.width() - 20, 
                label_size.height() - 20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # ラベルに設定
            self.image_label.setPixmap(scaled_pixmap)
            self.log(f"✅ 画像表示成功: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
        except Exception as e:
            self.log(f"❌ 画像表示エラー: {str(e)}")
            traceback.print_exc()


def main():
    app = QApplication(sys.argv)
    
    # デバッグ情報表示
    print("=== PyQt6画像デバッグ情報 ===")
    print(f"PyQt6バージョン: {app.instance().applicationVersion()}")
    print(f"利用可能な画像フォーマット: {QImage().supportedImageFormats()}")
    
    window = ImageDebugTester()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()