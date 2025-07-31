"""
EXIF Information Panel - EXIF情報表示パネル

exifreadライブラリを使用したEXIF情報表示機能。
位置情報をMAP表示機能に渡すための準備を含む。

Author: Kiro AI Integration System
"""

from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QGroupBox,
    QGridLayout,
    QPushButton,
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
        
    def _setup_ui(self):
        """UIの初期化"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)
            
            # タイトル
            title_label = QLabel("EXIF情報")
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
            
            # スクロール可能なEXIF情報エリア
            self._create_exif_scroll_area()
            layout.addWidget(self.exif_scroll_area)
            
            # 位置情報エリア
            self._create_gps_section()
            layout.addWidget(self.gps_group)
            
            # 更新ボタン
            self._create_control_buttons()
            layout.addWidget(self.control_widget)
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                ErrorCategory.UI_ERROR, 
                {"operation": "exif_panel_setup"}, 
                AIComponent.KIRO
            )
    
    def _create_exif_scroll_area(self):
        """EXIF情報のスクロールエリアを作成"""
        self.exif_scroll_area = QScrollArea()
        self.exif_scroll_area.setWidgetResizable(True)
        self.exif_scroll_area.setMaximumHeight(300)
        self.exif_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ffffff;
            }
        """)
        
        # EXIF情報表示ウィジェット
        self.exif_widget = QWidget()
        self.exif_layout = QVBoxLayout(self.exif_widget)
        self.exif_layout.setContentsMargins(10, 10, 10, 10)
        
        # 初期メッセージ
        self.exif_info_label = QLabel("画像を選択してください")
        self.exif_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.exif_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.exif_layout.addWidget(self.exif_info_label)
        
        self.exif_scroll_area.setWidget(self.exif_widget)
    
    def _create_gps_section(self):
        """GPS位置情報セクションを作成"""
        self.gps_group = QGroupBox("位置情報")
        self.gps_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
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
        
        # 緯度
        gps_layout.addWidget(QLabel("緯度:"), 0, 0)
        self.latitude_label = QLabel("未取得")
        self.latitude_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        gps_layout.addWidget(self.latitude_label, 0, 1)
        
        # 経度
        gps_layout.addWidget(QLabel("経度:"), 1, 0)
        self.longitude_label = QLabel("未取得")
        self.longitude_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        gps_layout.addWidget(self.longitude_label, 1, 1)
        
        # 高度
        gps_layout.addWidget(QLabel("高度:"), 2, 0)
        self.altitude_label = QLabel("未取得")
        self.altitude_label.setStyleSheet("color: #e74c3c;")
        gps_layout.addWidget(self.altitude_label, 2, 1)
        
        # GPS時刻
        gps_layout.addWidget(QLabel("GPS時刻:"), 3, 0)
        self.gps_time_label = QLabel("未取得")
        self.gps_time_label.setStyleSheet("color: #e74c3c;")
        gps_layout.addWidget(self.gps_time_label, 3, 1)
        
        # GPS日付
        gps_layout.addWidget(QLabel("GPS日付:"), 4, 0)
        self.gps_date_label = QLabel("未取得")
        self.gps_date_label.setStyleSheet("color: #e74c3c;")
        gps_layout.addWidget(self.gps_date_label, 4, 1)
    
    def _create_control_buttons(self):
        """コントロールボタンを作成"""
        self.control_widget = QWidget()
        control_layout = QHBoxLayout(self.control_widget)
        control_layout.setContentsMargins(0, 5, 0, 0)
        
        # 更新ボタン
        self.refresh_button = QPushButton("更新")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 15px;
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
        self.map_button = QPushButton("地図表示")
        self.map_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 5px 15px;
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
        
        control_layout.addStretch()
    
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
        """EXIF情報を読み込み"""
        if not self.current_image_path or not self.current_image_path.exists():
            self._clear_exif_display()
            return
        
        try:
            # EXIF情報を取得
            exif_data = self.image_processor.extract_exif(self.current_image_path)
            
            # 表示を更新
            self._update_exif_display(exif_data)
            
            # 位置情報を更新
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
    
    def _update_exif_display(self, exif_data: Dict[str, Any]):
        """EXIF情報の表示を更新"""
        try:
            # 既存のウィジェットをクリア
            for i in reversed(range(self.exif_layout.count())):
                child = self.exif_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()
            
            if not exif_data:
                self.exif_info_label = QLabel("EXIF情報が見つかりません")
                self.exif_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.exif_info_label.setStyleSheet("color: #e74c3c; font-style: italic;")
                self.exif_layout.addWidget(self.exif_info_label)
                return
            
            # ファイル情報
            file_group = self._create_info_group("ファイル情報", {
                "ファイル名": self.current_image_path.name if self.current_image_path else "",
                "ファイルサイズ": exif_data.get("File Size", "不明"),
                "ファイル形式": exif_data.get("File Format", "不明"),
            })
            self.exif_layout.addWidget(file_group)
            
            # カメラ情報
            camera_info = {}
            if "Camera Make" in exif_data:
                camera_info["メーカー"] = exif_data["Camera Make"]
            if "Camera Model" in exif_data:
                camera_info["モデル"] = exif_data["Camera Model"]
            if "Lens Model" in exif_data:
                camera_info["レンズ"] = exif_data["Lens Model"]
            
            if camera_info:
                camera_group = self._create_info_group("カメラ情報", camera_info)
                self.exif_layout.addWidget(camera_group)
            
            # 撮影設定
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
                settings_group = self._create_info_group("撮影設定", settings_info)
                self.exif_layout.addWidget(settings_group)
            
            # 撮影日時
            date_info = {}
            if "Date Taken" in exif_data:
                date_info["撮影日時"] = exif_data["Date Taken"]
            if "Date Original" in exif_data:
                date_info["元の撮影日時"] = exif_data["Date Original"]
            
            if date_info:
                date_group = self._create_info_group("撮影日時", date_info)
                self.exif_layout.addWidget(date_group)
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_exif_display"}, AIComponent.KIRO
            )
    
    def _create_info_group(self, title: str, info_dict: Dict[str, str]) -> QGroupBox:
        """情報グループを作成"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #34495e;
            }
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
    
    def _update_gps_display(self, exif_data: Dict[str, Any]):
        """GPS位置情報の表示を更新"""
        try:
            # GPS座標を取得（文字列から数値に変換）
            latitude_str = exif_data.get("GPS Latitude")
            longitude_str = exif_data.get("GPS Longitude")
            altitude = exif_data.get("GPS Altitude")
            gps_time = exif_data.get("GPS Timestamp")
            
            # 緯度・経度を数値に変換
            latitude = None
            longitude = None
            
            if latitude_str:
                try:
                    # "35.123456°" のような形式から数値を抽出
                    if isinstance(latitude_str, str) and "°" in latitude_str:
                        latitude = float(latitude_str.replace("°", ""))
                    elif isinstance(latitude_str, (int, float)):
                        latitude = float(latitude_str)
                except (ValueError, TypeError):
                    latitude = None
            
            if longitude_str:
                try:
                    # "139.123456°" のような形式から数値を抽出
                    if isinstance(longitude_str, str) and "°" in longitude_str:
                        longitude = float(longitude_str.replace("°", ""))
                    elif isinstance(longitude_str, (int, float)):
                        longitude = float(longitude_str)
                except (ValueError, TypeError):
                    longitude = None
            
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
            gps_date = exif_data.get("GPS Date")
            if gps_date:
                self.gps_date_label.setText(str(gps_date))
                self.gps_date_label.setStyleSheet("color: #27ae60;")
            else:
                self.gps_date_label.setText("未取得")
                self.gps_date_label.setStyleSheet("color: #e74c3c;")
            
            # 地図表示ボタンの有効/無効を設定
            has_gps = latitude is not None and longitude is not None
            self.map_button.setEnabled(has_gps)
            
            # GPS座標がある場合はシグナルを発信
            if has_gps:
                self.gps_coordinates_updated.emit(latitude, longitude)
                
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_gps_display"}, AIComponent.KIRO
            )
    
    def _clear_exif_display(self):
        """EXIF表示をクリア"""
        try:
            # 既存のウィジェットをクリア
            for i in reversed(range(self.exif_layout.count())):
                child = self.exif_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()
            
            # 初期メッセージを表示
            self.exif_info_label = QLabel("画像を選択してください")
            self.exif_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.exif_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
            self.exif_layout.addWidget(self.exif_info_label)
            
            # GPS情報をクリア
            self.latitude_label.setText("未取得")
            self.longitude_label.setText("未取得")
            self.altitude_label.setText("未取得")
            self.gps_time_label.setText("未取得")
            self.gps_date_label.setText("未取得")
            
            # 地図表示ボタンを無効化
            self.map_button.setEnabled(False)
            
        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "clear_exif_display"}, AIComponent.KIRO
            )
    
    def _show_error_message(self, message: str):
        """エラーメッセージを表示"""
        try:
            # 既存のウィジェットをクリア
            for i in reversed(range(self.exif_layout.count())):
                child = self.exif_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()
            
            error_label = QLabel(message)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #e74c3c; font-style: italic;")
            self.exif_layout.addWidget(error_label)
            
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