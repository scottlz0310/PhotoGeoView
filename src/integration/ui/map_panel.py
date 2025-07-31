"""
Map Panel - 地図表示パネル

PyQtWebEngineを使用した地図表示パネル。
foliumで生成されたHTML地図を表示し、GPS座標に基づいて地図を更新。
PyQtWebEngineが利用できない場合の代替表示も提供。

Author: Kiro AI Integration System
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..state_manager import StateManager


class MapPanel(QWidget):
    """
    地図表示パネル

    機能:
    - PyQtWebEngineを使用したHTML地図表示
    - GPS座標に基づく地図更新
    - 地図操作（ズーム・パン）
    - PyQtWebEngineが利用できない場合の代替表示
    - 複数画像の位置情報表示
    """

    # シグナル
    map_loaded = pyqtSignal(float, float)  # latitude, longitude
    map_error = pyqtSignal(str)  # error message
    location_selected = pyqtSignal(float, float)  # lat, lon

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

        # 現在の座標
        self.current_latitude: Optional[float] = None
        self.current_longitude: Optional[float] = None

        # 複数画像の位置情報
        self.image_locations: List[Dict[str, Any]] = []

        # 一時ファイル管理
        self.temp_html_file: Optional[Path] = None

        # UI初期化
        self._setup_ui()



    def show_fallback_message(self):
        """フォールバック表示"""
        error_label = QLabel("""
        地図の初期化に失敗しました。

        以下を確認してください：
        • PyQt6-WebEngineがインストールされているか
        • システムにWebEngineの依存関係があるか

        地図機能は利用できませんが、他の機能は正常に動作します。
        """)
        error_label.setStyleSheet("""
            QLabel {
                color: #cc0000;
                background-color: #ffe6e6;
                border: 1px solid #cc0000;
                border-radius: 5px;
                padding: 20px;
                font-size: 12px;
            }
        """)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 既存のウィジェットを削除
        if hasattr(self, 'map_widget'):
            self.layout().removeWidget(self.map_widget)
            self.map_widget.deleteLater()

        # エラーメッセージを追加
        self.layout().addWidget(error_label)
        self.map_widget = error_label

        # ログ出力
        self.logger_system.log_ai_operation(
            AIComponent.KIRO,
            "webengine_fallback",
            "WebEngine初期化失敗 - フォールバック表示",
        )

    def _setup_ui(self):
        """UIの初期化"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # タイトル
            title_label = QLabel("地図表示")
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

            # コントロールエリア
            self._create_controls()
            layout.addWidget(self.controls_widget)

            # 地図表示エリア
            self._create_map_display()
            layout.addWidget(self.map_widget)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "map_panel_setup"}, AIComponent.KIRO
            )

    def _create_controls(self):
        """コントロールエリアを作成"""
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 5, 0, 5)

        # 座標表示
        self.coordinates_label = QLabel("座標: 未設定")
        self.coordinates_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #7f8c8d;
                padding: 5px 10px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        controls_layout.addWidget(self.coordinates_label)

        controls_layout.addStretch()

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
        self.refresh_button.clicked.connect(self._refresh_map)
        controls_layout.addWidget(self.refresh_button)

        # クリアボタン
        self.clear_button = QPushButton("クリア")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.clear_button.clicked.connect(self._clear_locations)
        controls_layout.addWidget(self.clear_button)

        # 全画面ボタン
        self.fullscreen_button = QPushButton("全画面")
        self.fullscreen_button.setStyleSheet("""
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
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        controls_layout.addWidget(self.fullscreen_button)

    def _create_map_display(self):
        """地図表示エリアを作成"""
        # 初期化中のプレースホルダー
        self.map_widget = QLabel("地図を初期化中...")
        self.map_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_widget.setStyleSheet("""
            QLabel {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #f8f9fa;
                color: #7f8c8d;
                padding: 20px;
                font-size: 14px;
            }
        """)

    def _show_placeholder(self):
        """プレースホルダーHTMLを表示"""
        try:
            placeholder_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>地図表示</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f8f9fa;
                        color: #7f8c8d;
                        text-align: center;
                    }
                    .placeholder {
                        margin-top: 50px;
                    }
                </style>
            </head>
            <body>
                <div class="placeholder">
                    <h2>地図表示エリア</h2>
                    <p>GPS座標を設定すると地図が表示されます</p>
                </div>
            </body>
            </html>
            """

            if WEBENGINE_AVAILABLE:
                self.map_widget.setHtml(placeholder_html)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "show_placeholder"}, AIComponent.KIRO
            )

    def set_coordinates(self, latitude: float, longitude: float):
        """座標を設定して地図を更新"""
        try:
            self.current_latitude = latitude
            self.current_longitude = longitude

            # 座標表示を更新
            self.coordinates_label.setText(f"座標: {latitude:.6f}, {longitude:.6f}")
            self.coordinates_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #27ae60;
                    padding: 5px 10px;
                    background-color: #ecf0f1;
                    border-radius: 3px;
                }
            """)

            # 地図を更新
            self._update_map()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_coordinates", "lat": latitude, "lon": longitude},
                AIComponent.KIRO
            )

    def add_image_location(self, image_path: Path, latitude: float, longitude: float, name: str = None):
        """画像の位置情報を追加"""
        try:
            location = {
                'path': image_path,
                'lat': latitude,
                'lon': longitude,
                'name': name or image_path.name
            }

            self.image_locations.append(location)
            self._update_map()

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "add_image_location",
                f"画像位置情報を追加: {location['name']} ({latitude:.6f}, {longitude:.6f})",
                context={"image_path": str(image_path), "latitude": latitude, "longitude": longitude},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "add_image_location", "image_path": str(image_path)},
                AIComponent.KIRO
            )

    def _update_map(self):
        """地図を更新"""
        try:
            if self.image_locations:
                locations_text = "地図情報\n\n"
                for i, location in enumerate(self.image_locations, 1):
                    locations_text += f"{i}. {location['name']}\n"
                    locations_text += f"   緯度: {location['lat']:.6f}°\n"
                    locations_text += f"   経度: {location['lon']:.6f}°\n\n"
                locations_text += "地図表示にはPyQtWebEngineが必要です"

                self.map_widget.setText(locations_text)
                self.map_widget.setStyleSheet("""
                    QLabel {
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        background-color: #f8f9fa;
                        color: #27ae60;
                        padding: 20px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)

                # 最新の座標でシグナルを発信
                latest = self.image_locations[-1]
                self.map_loaded.emit(latest['lat'], latest['lon'])

            elif self.current_latitude is not None and self.current_longitude is not None:
                map_info = f"地図情報\n\n緯度: {self.current_latitude:.6f}°\n経度: {self.current_longitude:.6f}°\n\n地図表示にはPyQtWebEngineが必要です"
                self.map_widget.setText(map_info)
                self.map_widget.setStyleSheet("""
                    QLabel {
                        border: 1px solid #bdc3c7;
                        border-radius: 3px;
                        background-color: #f8f9fa;
                        color: #27ae60;
                        padding: 20px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                # シグナルを発信
                self.map_loaded.emit(self.current_latitude, self.current_longitude)
            else:
                self._show_placeholder()

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "update_map",
                f"地図を更新: {len(self.image_locations)}個の位置情報",
                context={"locations_count": len(self.image_locations)},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_map"}, AIComponent.KIRO
            )
            self._show_error("地図の更新に失敗しました")

    def _create_multi_location_map(self, map_provider):
        """複数位置情報の地図を作成"""
        try:
            if not self.image_locations:
                return None

            # 中心座標の計算
            center_lat = sum(loc['lat'] for loc in self.image_locations) / len(self.image_locations)
            center_lon = sum(loc['lon'] for loc in self.image_locations) / len(self.image_locations)

            # 地図を作成
            map_obj = map_provider.create_map((center_lat, center_lon), 10)
            if not map_obj:
                return None

            # 各位置にマーカーを追加
            for location in self.image_locations:
                popup_text = f"""
                <div style="width: 200px;">
                    <b>{location['name']}</b><br>
                    <small>緯度: {location['lat']:.6f}</small><br>
                    <small>経度: {location['lon']:.6f}</small>
                </div>
                """
                map_provider.add_marker(
                    map_obj,
                    location['lat'],
                    location['lon'],
                    popup_text
                )

            # HTMLをレンダリング
            return map_provider.render_html(map_obj)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "create_multi_location_map"}, AIComponent.KIRO
            )
            return None

    def _show_error(self, message: str):
        """エラーメッセージを表示"""
        try:
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>エラー</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f8f9fa;
                        color: #e74c3c;
                        text-align: center;
                    }}
                    .error {{
                        margin-top: 50px;
                    }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>エラー</h2>
                    <p>{message}</p>
                </div>
            </body>
            </html>
            """

            if WEBENGINE_AVAILABLE:
                self.map_widget.setHtml(error_html)

            # シグナルを発信
            self.map_error.emit(message)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "show_error"}, AIComponent.KIRO
            )

    def _refresh_map(self):
        """地図を再読み込み"""
        self._update_map()

    def _clear_locations(self):
        """全ての位置情報をクリア"""
        try:
            self.image_locations.clear()
            self.current_latitude = None
            self.current_longitude = None

            # 座標表示をリセット
            self.coordinates_label.setText("座標: 未設定")
            self.coordinates_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #7f8c8d;
                    padding: 5px 10px;
                    background-color: #ecf0f1;
                    border-radius: 3px;
                }
            """)

            # 地図をリセット
            self._show_placeholder()

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "clear_locations",
                "地図位置情報をクリア",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "clear_locations"}, AIComponent.KIRO
            )

    def _toggle_fullscreen(self):
        """全画面表示の切り替え"""
        try:
            if self.isFullScreen():
                self.showNormal()
                self.fullscreen_button.setText("全画面")
            else:
                self.showFullScreen()
                self.fullscreen_button.setText("戻る")

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "toggle_fullscreen"}, AIComponent.KIRO
            )

    def get_current_coordinates(self) -> Optional[tuple]:
        """現在の座標を取得"""
        if self.current_latitude is not None and self.current_longitude is not None:
            return (self.current_latitude, self.current_longitude)
        return None

    def get_image_locations(self) -> List[Dict]:
        """画像位置情報のリストを取得"""
        return self.image_locations.copy()

    def closeEvent(self, event):
        """ウィンドウクローズ時のクリーンアップ"""
        try:
            # 一時ファイルのクリーンアップ
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
        except Exception:
            pass

        super().closeEvent(event)
