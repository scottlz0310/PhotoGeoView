"""
EXIF Information Panel - EXIF情報表示パネル

exifreadライブラリを使用したEXIF情報表示機能。
位置情報をMAP表示機能に渡すための準備を含む。

Author: Kiro AI Integration System
"""

from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..image_processor import CS4CodingImageProcessor
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..state_manager import StateManager


class EXIFPanel(QWidget):
    """
    EXIF情報表示パネル

    機能:
    - exifreadライブラリによるEXIF情報取得
    - 位置情報の表示とMAP機能への連携
    - カメラ情報、撮影設定の詳細表示
    - リアルタイム更新対応
    """

    # シグナル
    gps_coordinates_updated = pyqtSignal(float, float)  # latitude, longitude
    exif_data_updated = pyqtSignal(dict)  # exif_data

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
        self.error_handler = IntegratedErrorHandler(logger_system)

        # EXIF処理エンジン
        self.image_processor = CS4CodingImageProcessor(
            config_manager, logger_system
        )

        # 現在の画像パス
        self.current_image_path: Optional[Path] = None

        # UI初期化
        self._setup_ui()

        # 保存された高さ設定を復元
        self._restore_height_settings()

    def _setup_ui(self):
        """UIの初期化（統合版）"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # タイトル
            title_label = QLabel("📷 画像情報・位置情報")
            title_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                    color: #2c3e50;
                    padding: 5px;
                    background-color: #ecf0f1;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(title_label)

            # 統合情報エリア（スクロール可能・高さ調整可能）
            self._create_integrated_info_area()
            layout.addWidget(self.integrated_scroll_area)

            # サイズ調整コントロールパネル
            layout.addWidget(self.size_control_panel)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "exif_panel_setup"},
                AIComponent.KIRO
            )

    def _create_integrated_info_area(self):
        """統合情報エリアを作成（EXIF + GPS情報）- 高さ調整可能版"""
        # 統合情報スクロールエリア（シンプル版）
        self.integrated_scroll_area = QScrollArea()
        self.integrated_scroll_area.setWidgetResizable(True)
        self.integrated_scroll_area.setMinimumHeight(400)  # 最小高さを400pxに設定（従来の倍）
        self.integrated_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QScrollArea:focus {
                border: 2px solid #3498db;
            }
        """)

        # 統合情報表示ウィジェット
        self.integrated_widget = QWidget()
        self.integrated_layout = QVBoxLayout(self.integrated_widget)
        self.integrated_layout.setContentsMargins(10, 10, 10, 10)
        self.integrated_layout.setSpacing(10)

        # 初期メッセージ
        self.initial_message_label = QLabel("📷 画像を選択してください")
        self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.initial_message_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                font-size: 16px;
                padding: 20px;
            }
        """)
        self.integrated_layout.addWidget(self.initial_message_label)

        self.integrated_scroll_area.setWidget(self.integrated_widget)

        # サイズ調整コントロールパネルを作成
        self._create_size_control_panel()

    def _create_size_control_panel(self):
        """サイズ調整コントロールパネルを作成"""
        from PyQt6.QtWidgets import QSlider

        self.size_control_panel = QWidget()
        self.size_control_panel.setFixedHeight(60)  # 固定高さに変更
        self.size_control_panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                margin-top: 5px;
            }
        """)

        control_layout = QHBoxLayout(self.size_control_panel)
        control_layout.setContentsMargins(8, 5, 8, 5)
        control_layout.setSpacing(8)

        # サイズ調整ラベル
        size_label = QLabel("📏")
        size_label.setStyleSheet("font-weight: bold; color: #495057;")
        control_layout.addWidget(size_label)

        # 高さ調整スライダー
        self.height_slider = QSlider(Qt.Orientation.Horizontal)
        self.height_slider.setMinimum(300)  # 最小300px
        self.height_slider.setMaximum(800)  # 最大800px
        self.height_slider.setValue(400)    # 初期値400px
        self.height_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 6px;
                background: #ecf0f1;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
            QSlider::sub-page:horizontal {
                background: #3498db;
                border-radius: 3px;
            }
        """)
        self.height_slider.valueChanged.connect(self._on_height_changed)
        control_layout.addWidget(self.height_slider)

        # 現在の高さ表示
        self.height_display = QLabel("400px")
        self.height_display.setStyleSheet("""
            QLabel {
                color: #495057;
                font-weight: bold;
                min-width: 45px;
                font-size: 10px;
            }
        """)
        control_layout.addWidget(self.height_display)

        # プリセットボタン（コンパクト版）
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(3)

        # コンパクトボタン
        compact_btn = QPushButton("📱")
        compact_btn.setToolTip("コンパクト (300px)")
        compact_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 3px 6px;
                border-radius: 3px;
                font-size: 10px;
                min-width: 20px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        compact_btn.clicked.connect(lambda: self._set_preset_height(300))
        preset_layout.addWidget(compact_btn)

        # 標準ボタン
        standard_btn = QPushButton("📄")
        standard_btn.setToolTip("標準 (400px)")
        standard_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 3px 6px;
                border-radius: 3px;
                font-size: 10px;
                min-width: 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        standard_btn.clicked.connect(lambda: self._set_preset_height(400))
        preset_layout.addWidget(standard_btn)

        # 拡張ボタン
        expanded_btn = QPushButton("📊")
        expanded_btn.setToolTip("拡張 (600px)")
        expanded_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 3px 6px;
                border-radius: 3px;
                font-size: 10px;
                min-width: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        expanded_btn.clicked.connect(lambda: self._set_preset_height(600))
        preset_layout.addWidget(expanded_btn)

        # 最大ボタン
        max_btn = QPushButton("🖥️")
        max_btn.setToolTip("最大 (800px)")
        max_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 3px 6px;
                border-radius: 3px;
                font-size: 10px;
                min-width: 20px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        max_btn.clicked.connect(lambda: self._set_preset_height(800))
        preset_layout.addWidget(max_btn)

        control_layout.addLayout(preset_layout)

    def _on_height_changed(self, value: int):
        """高さスライダーの値が変更された時の処理"""
        try:
            # スクロールエリアの高さを更新
            self.integrated_scroll_area.setMinimumHeight(value)

            # 表示ラベルを更新
            self.height_display.setText(f"{value}px")

            # 設定を保存
            self.config_manager.set_setting("ui.exif_panel_height", value)

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "exif_panel_height_changed",
                f"EXIF panel height changed to {value}px",
                context={"height": value},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "height_change", "value": value}, AIComponent.KIRO
            )

    def _set_preset_height(self, height: int):
        """プリセット高さを設定"""
        try:
            self.height_slider.setValue(height)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "set_preset_height", "height": height}, AIComponent.KIRO
            )

    def _restore_height_settings(self):
        """保存された高さ設定を復元"""
        try:
            # 保存された高さを取得（デフォルト: 400px）
            saved_height = self.config_manager.get_setting("ui.exif_panel_height", 400)

            # 範囲チェック
            saved_height = max(300, min(800, saved_height))

            # スクロールエリアの高さを設定
            self.integrated_scroll_area.setMinimumHeight(saved_height)

            # スライダーと表示を更新
            if hasattr(self, 'height_slider'):
                self.height_slider.setValue(saved_height)
            if hasattr(self, 'height_display'):
                self.height_display.setText(f"{saved_height}px")

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "exif_panel_height_restored",
                f"EXIF panel height restored to {saved_height}px",
                context={"height": saved_height},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "restore_height_settings"}, AIComponent.KIRO
            )

    def _create_integrated_sections(self, exif_data: Dict[str, Any]):
        """統合セクションを作成（EXIF + GPS情報）"""
        # 既存のウィジェットをクリア
        for i in reversed(range(self.integrated_layout.count())):
            child = self.integrated_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        if not exif_data:
            self.initial_message_label = QLabel("❌ EXIF情報が見つかりません")
            self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.initial_message_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-style: italic;
                    font-size: 16px;
                    padding: 20px;
                }
            """)
            self.integrated_layout.addWidget(self.initial_message_label)
            return

        # 1. ファイル情報セクション
        self._create_file_info_section(exif_data)

        # 2. カメラ情報セクション
        self._create_camera_info_section(exif_data)

        # 3. 撮影設定セクション
        self._create_shooting_settings_section(exif_data)

        # 4. 撮影日時セクション
        self._create_datetime_section(exif_data)

        # 5. GPS位置情報セクション（統合版）
        self._create_gps_info_section(exif_data)

        # 6. デバッグ情報セクション（折りたたみ可能）
        self._create_debug_section_integrated(exif_data)

        # 7. 地図連携コントロール
        self._create_map_controls_integrated()

    def _create_file_info_section(self, exif_data: Dict[str, Any]):
        """ファイル情報セクションを作成"""
        file_info = {}
        if self.current_image_path:
            file_info["ファイル名"] = self.current_image_path.name
        if "File Size" in exif_data:
            file_info["ファイルサイズ"] = exif_data["File Size"]
        if "File Format" in exif_data:
            file_info["ファイル形式"] = exif_data["File Format"]

        if file_info:
            file_section = self._create_info_section("📁 ファイル情報", file_info, "#34495e")
            self.integrated_layout.addWidget(file_section)

    def _create_camera_info_section(self, exif_data: Dict[str, Any]):
        """カメラ情報セクションを作成"""
        camera_info = {}
        if "Camera Make" in exif_data:
            camera_info["メーカー"] = exif_data["Camera Make"]
        if "Camera Model" in exif_data:
            camera_info["モデル"] = exif_data["Camera Model"]
        if "Lens Model" in exif_data:
            camera_info["レンズ"] = exif_data["Lens Model"]

        if camera_info:
            camera_section = self._create_info_section("📸 カメラ情報", camera_info, "#8e44ad")
            self.integrated_layout.addWidget(camera_section)

    def _create_shooting_settings_section(self, exif_data: Dict[str, Any]):
        """撮影設定セクションを作成"""
        settings_info = {}
        if "F-Number" in exif_data:
            settings_info["F値"] = exif_data["F-Number"]
        if "Exposure Time" in exif_data:
            settings_info["シャッター速度"] = exif_data["Exposure Time"]
        if "ISO Speed" in exif_data:
            settings_info["ISO感度"] = exif_data["ISO Speed"]
        if "Focal Length" in exif_data:
            settings_info["焦点距離"] = exif_data["Focal Length"]

        if settings_info:
            settings_section = self._create_info_section("⚙️ 撮影設定", settings_info, "#e67e22")
            self.integrated_layout.addWidget(settings_section)

    def _create_datetime_section(self, exif_data: Dict[str, Any]):
        """撮影日時セクションを作成"""
        date_info = {}
        if "Date Taken" in exif_data:
            date_info["撮影日時"] = exif_data["Date Taken"]
        if "Date Original" in exif_data:
            date_info["元の撮影日時"] = exif_data["Date Original"]

        if date_info:
            date_section = self._create_info_section("🕒 撮影日時", date_info, "#27ae60")
            self.integrated_layout.addWidget(date_section)

    def _create_gps_info_section(self, exif_data: Dict[str, Any]):
        """GPS位置情報セクションを作成（統合版）"""
        self.gps_group = QGroupBox("📍 位置情報・地図連携")
        self.gps_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2980b9;
            }
        """)

        gps_layout = QGridLayout(self.gps_group)
        gps_layout.setSpacing(8)

        # GPS座標情報を取得
        latitude_str = exif_data.get("GPS Latitude")
        longitude_str = exif_data.get("GPS Longitude")
        altitude = exif_data.get("GPS Altitude")
        gps_time = exif_data.get("GPS Timestamp")
        gps_date = exif_data.get("GPS Date")

        # 基本GPS座標情報
        coord_frame = QFrame()
        coord_frame.setFrameStyle(QFrame.Shape.Box)
        coord_frame.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 3px; padding: 5px; }")
        coord_layout = QGridLayout(coord_frame)
        coord_layout.setSpacing(5)

        # 緯度
        coord_layout.addWidget(QLabel("緯度:"), 0, 0)
        self.latitude_label = QLabel("未取得")
        self.latitude_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        coord_layout.addWidget(self.latitude_label, 0, 1)

        # 経度
        coord_layout.addWidget(QLabel("経度:"), 1, 0)
        self.longitude_label = QLabel("未取得")
        self.longitude_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        coord_layout.addWidget(self.longitude_label, 1, 1)

        # 高度
        coord_layout.addWidget(QLabel("高度:"), 2, 0)
        self.altitude_label = QLabel("未取得")
        self.altitude_label.setStyleSheet("color: #e74c3c;")
        coord_layout.addWidget(self.altitude_label, 2, 1)

        gps_layout.addWidget(coord_frame, 0, 0, 1, 2)

        # GPS時刻・日付情報
        time_frame = QFrame()
        time_frame.setFrameStyle(QFrame.Shape.Box)
        time_frame.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 3px; padding: 5px; }")
        time_layout = QGridLayout(time_frame)
        time_layout.setSpacing(5)

        # GPS時刻
        time_layout.addWidget(QLabel("GPS時刻:"), 0, 0)
        self.gps_time_label = QLabel("未取得")
        self.gps_time_label.setStyleSheet("color: #e74c3c;")
        time_layout.addWidget(self.gps_time_label, 0, 1)

        # GPS日付
        time_layout.addWidget(QLabel("GPS日付:"), 1, 0)
        self.gps_date_label = QLabel("未取得")
        self.gps_date_label.setStyleSheet("color: #e74c3c;")
        time_layout.addWidget(self.gps_date_label, 1, 1)

        gps_layout.addWidget(time_frame, 1, 0, 1, 2)

        self.integrated_layout.addWidget(self.gps_group)

    def _create_info_section(self, title: str, info_dict: Dict[str, str], border_color: str = "#bdc3c7") -> QGroupBox:
        """情報セクションを作成（統合版）"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {border_color};
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: {border_color};
            }}
        """)

        layout = QGridLayout(group)
        layout.setSpacing(5)

        row = 0
        for key, value in info_dict.items():
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            value_label = QLabel(str(value))
            value_label.setStyleSheet("color: #34495e;")

            layout.addWidget(key_label, row, 0)
            layout.addWidget(value_label, row, 1)
            row += 1

        return group

    def _create_debug_section_integrated(self, exif_data: Dict[str, Any]):
        """デバッグ情報セクションを作成（統合版）"""
        # デバッグ情報の折りたたみボタン
        self.debug_toggle_button = QPushButton("🔧 デバッグ情報を表示")
        self.debug_toggle_button.setCheckable(True)
        self.debug_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
                text-align: left;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:checked {
                background-color: #d35400;
            }
        """)
        self.debug_toggle_button.clicked.connect(self._toggle_debug_info)
        self.integrated_layout.addWidget(self.debug_toggle_button)

        # デバッグ情報フレーム（初期状態では非表示）
        self.debug_frame = QFrame()
        self.debug_frame.setFrameStyle(QFrame.Shape.Box)
        self.debug_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #f39c12;
                border-radius: 3px;
                padding: 10px;
                background-color: #fef9e7;
                margin-top: 5px;
            }
        """)
        self.debug_frame.setVisible(False)

        debug_layout = QVBoxLayout(self.debug_frame)
        debug_layout.setSpacing(8)

        # 生のEXIF GPS情報
        raw_gps_label = QLabel("📋 生のGPS EXIF情報:")
        raw_gps_label.setStyleSheet("font-weight: bold; color: #d35400;")
        debug_layout.addWidget(raw_gps_label)

        self.raw_gps_text = QTextEdit()
        self.raw_gps_text.setMaximumHeight(100)
        self.raw_gps_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-family: monospace;
                font-size: 10px;
                padding: 5px;
            }
        """)
        self.raw_gps_text.setPlainText("GPS情報なし")
        debug_layout.addWidget(self.raw_gps_text)

        # 座標変換情報
        conversion_label = QLabel("🔄 座標変換情報:")
        conversion_label.setStyleSheet("font-weight: bold; color: #d35400;")
        debug_layout.addWidget(conversion_label)

        self.conversion_info_label = QLabel("変換情報なし")
        self.conversion_info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10px;
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.conversion_info_label.setWordWrap(True)
        debug_layout.addWidget(self.conversion_info_label)

        self.integrated_layout.addWidget(self.debug_frame)

    def _create_map_controls_integrated(self):
        """地図連携コントロールを作成（統合版）"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.Box)
        control_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #27ae60;
                border-radius: 3px;
                padding: 10px;
                margin-top: 5px;
            }
        """)

        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(8)

        # 更新ボタン
        self.refresh_button = QPushButton("🔄 更新")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.refresh_button.clicked.connect(self._refresh_exif_data)
        control_layout.addWidget(self.refresh_button)

        # 地図表示ボタン
        self.map_button = QPushButton("🗺️ 地図表示")
        self.map_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.map_button.clicked.connect(self._show_on_map)
        self.map_button.setEnabled(False)  # 初期状態では無効
        control_layout.addWidget(self.map_button)

        # 座標コピーボタン
        self.copy_coords_button = QPushButton("📋 座標コピー")
        self.copy_coords_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        self.copy_coords_button.clicked.connect(self._copy_coordinates)
        self.copy_coords_button.setEnabled(False)  # 初期状態では無効
        control_layout.addWidget(self.copy_coords_button)

        control_layout.addStretch()

        self.integrated_layout.addWidget(control_frame)





    def set_image(self, image_path: Path):
        """画像を設定してEXIF情報を取得"""
        try:
            self.current_image_path = image_path
            self._load_exif_data()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_image", "image_path": str(image_path)},
                AIComponent.KIRO
            )

    def _load_exif_data(self):
        """EXIF情報を読み込み（統合版）"""
        if not self.current_image_path or not self.current_image_path.exists():
            self._clear_integrated_display()
            return

        try:
            # EXIF情報を取得
            exif_data = self.image_processor.extract_exif(self.current_image_path)

            # 統合表示を更新
            self._create_integrated_sections(exif_data)

            # GPS情報を更新
            self._update_gps_display(exif_data)

            # シグナルを発信
            self.exif_data_updated.emit(exif_data)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "load_exif_data", "image_path": str(self.current_image_path)},
                AIComponent.KIRO,
            )
            self._show_error_message("EXIF情報の読み込みに失敗しました")

    def _clear_integrated_display(self):
        """統合表示をクリア"""
        try:
            # 既存のウィジェットをクリア
            for i in reversed(range(self.integrated_layout.count())):
                child = self.integrated_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()

            # 初期メッセージを表示
            self.initial_message_label = QLabel("📷 画像を選択してください")
            self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.initial_message_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-style: italic;
                    font-size: 16px;
                    padding: 20px;
                }
            """)
            self.integrated_layout.addWidget(self.initial_message_label)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "clear_integrated_display"}, AIComponent.KIRO
            )



    def _update_gps_display(self, exif_data: Dict[str, Any]):
        """GPS位置情報の表示を更新（統合版）"""
        try:
            # GPS座標を取得（文字列から数値に変換）
            latitude_str = exif_data.get("GPS Latitude")
            longitude_str = exif_data.get("GPS Longitude")
            altitude = exif_data.get("GPS Altitude")
            gps_time = exif_data.get("GPS Timestamp")

            # デバッグ情報用の生データを保存
            raw_gps_info = []
            conversion_info = []

            # 緯度・経度を数値に変換
            latitude = None
            longitude = None

            if latitude_str:
                raw_gps_info.append(f"緯度（生データ）: {latitude_str}")
                try:
                    # "35.123456°" のような形式から数値を抽出
                    if isinstance(latitude_str, str) and "°" in latitude_str:
                        latitude = float(latitude_str.replace("°", ""))
                        conversion_info.append(f"緯度変換: '{latitude_str}' → {latitude:.6f}")
                    elif isinstance(latitude_str, (int, float)):
                        latitude = float(latitude_str)
                        conversion_info.append(f"緯度変換: {latitude_str} → {latitude:.6f}")
                except (ValueError, TypeError) as e:
                    conversion_info.append(f"緯度変換エラー: {e}")
                    latitude = None

            if longitude_str:
                raw_gps_info.append(f"経度（生データ）: {longitude_str}")
                try:
                    # "139.123456°" のような形式から数値を抽出
                    if isinstance(longitude_str, str) and "°" in longitude_str:
                        longitude = float(longitude_str.replace("°", ""))
                        conversion_info.append(f"経度変換: '{longitude_str}' → {longitude:.6f}")
                    elif isinstance(longitude_str, (int, float)):
                        longitude = float(longitude_str)
                        conversion_info.append(f"経度変換: {longitude_str} → {longitude:.6f}")
                except (ValueError, TypeError) as e:
                    conversion_info.append(f"経度変換エラー: {e}")
                    longitude = None

            # 高度情報をデバッグに追加
            if altitude is not None:
                raw_gps_info.append(f"高度（生データ）: {altitude}")

            # GPS時刻・日付をデバッグに追加
            if gps_time:
                raw_gps_info.append(f"GPS時刻: {gps_time}")
            gps_date = exif_data.get("GPS Date")
            if gps_date:
                raw_gps_info.append(f"GPS日付: {gps_date}")

            # デバッグ情報を更新
            self._update_debug_info(raw_gps_info, conversion_info)

            # 緯度表示
            if latitude is not None:
                self.latitude_label.setText(f"{latitude:.6f}°")
                self.latitude_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                self.latitude_label.setText("未取得")
                self.latitude_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

            # 経度表示
            if longitude is not None:
                self.longitude_label.setText(f"{longitude:.6f}°")
                self.longitude_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                self.longitude_label.setText("未取得")
                self.longitude_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

            # 高度表示
            if altitude is not None:
                self.altitude_label.setText(f"{altitude:.1f}m")
                self.altitude_label.setStyleSheet("color: #27ae60;")
            else:
                self.altitude_label.setText("未取得")
                self.altitude_label.setStyleSheet("color: #e74c3c;")

            # GPS時刻表示
            if gps_time:
                self.gps_time_label.setText(str(gps_time))
                self.gps_time_label.setStyleSheet("color: #27ae60;")
            else:
                self.gps_time_label.setText("未取得")
                self.gps_time_label.setStyleSheet("color: #e74c3c;")

            # GPS日付表示
            if gps_date:
                self.gps_date_label.setText(str(gps_date))
                self.gps_date_label.setStyleSheet("color: #27ae60;")
            else:
                self.gps_date_label.setText("未取得")
                self.gps_date_label.setStyleSheet("color: #e74c3c;")

            # ボタンの有効/無効を設定
            has_gps = latitude is not None and longitude is not None
            self.map_button.setEnabled(has_gps)
            self.copy_coords_button.setEnabled(has_gps)

            # GPS座標がある場合はシグナルを発信
            if has_gps:
                self.gps_coordinates_updated.emit(latitude, longitude)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_gps_display"}, AIComponent.KIRO
            )



    def _show_error_message(self, message: str):
        """エラーメッセージを表示（統合版）"""
        try:
            # 既存のウィジェットをクリア
            for i in reversed(range(self.integrated_layout.count())):
                child = self.integrated_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()

            error_label = QLabel(f"❌ {message}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-style: italic;
                    font-size: 16px;
                    padding: 20px;
                }
            """)
            self.integrated_layout.addWidget(error_label)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "show_error_message"}, AIComponent.KIRO
            )

    def _refresh_exif_data(self):
        """EXIF情報を再読み込み"""
        if self.current_image_path:
            self._load_exif_data()

    def _show_on_map(self):
        """地図上に表示"""
        try:
            if self.current_image_path:
                # 地図表示機能への連携
                # この部分は後でMAP表示機能と連携する
                self.logger_system.log_info(
                    "地図表示機能への連携要求",
                    {"image_path": str(self.current_image_path)},
                    AIComponent.KIRO,
                )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "show_on_map"}, AIComponent.KIRO
            )

    def _toggle_debug_info(self):
        """デバッグ情報の表示/非表示を切り替え"""
        try:
            is_visible = self.debug_frame.isVisible()
            self.debug_frame.setVisible(not is_visible)

            if not is_visible:
                self.debug_toggle_button.setText("🔧 デバッグ情報を非表示")
            else:
                self.debug_toggle_button.setText("🔧 デバッグ情報を表示")

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "toggle_debug_info"}, AIComponent.KIRO
            )

    def _update_debug_info(self, raw_gps_info: list, conversion_info: list):
        """デバッグ情報を更新"""
        try:
            # 生のGPS情報を表示
            if raw_gps_info:
                raw_text = "\n".join(raw_gps_info)
            else:
                raw_text = "GPS情報なし"

            self.raw_gps_text.setPlainText(raw_text)

            # 座標変換情報を表示
            if conversion_info:
                conversion_text = "\n".join(conversion_info)
            else:
                conversion_text = "変換情報なし"

            self.conversion_info_label.setText(conversion_text)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_debug_info"}, AIComponent.KIRO
            )

    def _copy_coordinates(self):
        """GPS座標をクリップボードにコピー"""
        try:
            from PyQt6.QtWidgets import QApplication

            # 現在の座標を取得
            coords = self.get_current_gps_coordinates()
            if coords:
                latitude, longitude = coords
                coord_text = f"{latitude:.6f}, {longitude:.6f}"

                # クリップボードにコピー
                clipboard = QApplication.clipboard()
                clipboard.setText(coord_text)

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "coordinates_copied",
                    f"GPS座標をクリップボードにコピー: {coord_text}",
                    context={"coordinates": coord_text},
                )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "copy_coordinates"}, AIComponent.KIRO
            )

    def get_current_gps_coordinates(self) -> Optional[tuple]:
        """現在のGPS座標を取得"""
        try:
            if self.current_image_path:
                exif_data = self.image_processor.extract_exif(self.current_image_path)
                latitude_str = exif_data.get("GPS Latitude")
                longitude_str = exif_data.get("GPS Longitude")

                # 文字列から数値に変換
                latitude = None
                longitude = None

                if latitude_str:
                    try:
                        if isinstance(latitude_str, str) and "°" in latitude_str:
                            latitude = float(latitude_str.replace("°", ""))
                        elif isinstance(latitude_str, (int, float)):
                            latitude = float(latitude_str)
                    except (ValueError, TypeError):
                        latitude = None

                if longitude_str:
                    try:
                        if isinstance(longitude_str, str) and "°" in longitude_str:
                            longitude = float(longitude_str.replace("°", ""))
                        elif isinstance(longitude_str, (int, float)):
                            longitude = float(longitude_str)
                    except (ValueError, TypeError):
                        longitude = None

                if latitude is not None and longitude is not None:
                    return (latitude, longitude)

            return None

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.CORE_ERROR, {"operation": "get_gps_coordinates"}, AIComponent.KIRO
            )
            return None
