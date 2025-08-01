"""
Map Panel - 地図表示パネル

PyQtWebEngineを使用した地図表示パネル。
foliumで生成されたHTML地図を表示し、GPS座標に基づいて地図を更新。
PyQtWebEngineが利用できない場合の代替表示も提供。

Author: Kiro AI Integration System
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
    QFrame, QSizePolicy, QTextEdit, QScrollArea
)

# WebEngineの安全な初期化
WEBENGINE_AVAILABLE = False
QWebEngineView = None
QWebEngineSettings = None

# 直接インポートを試行（OpenGL設定が適用されている場合）
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile

    # 簡単な初期化テスト
    try:
        profile = QWebEngineProfile.defaultProfile()
        WEBENGINE_AVAILABLE = True
        print("✅ WebEngine直接初期化成功")
    except Exception as e:
        print(f"⚠️  WebEngine初期化テスト失敗: {e}")
        QWebEngineView = None
        QWebEngineSettings = None

except ImportError as e:
    print(f"⚠️  WebEngine直接インポート失敗: {e}")

    # フォールバック: webengine_checkerを使用
    try:
        from ..utils.webengine_checker import get_webengine_status, create_webengine_view
        webengine_status = get_webengine_status()
        if webengine_status["available"]:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebEngineCore import QWebEngineSettings
            WEBENGINE_AVAILABLE = True
            print("✅ WebEngineチェッカー経由で初期化成功")
    except ImportError:
        pass

# foliumのインポート
try:
    import folium
    from folium import plugins
    folium_available = True
except ImportError:
    folium_available = False
    folium = None
    plugins = None

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

        # 地図プロパティ
        self.current_map_file: Optional[str] = None
        self.photo_locations: Dict[str, Tuple[float, float]] = {}
        self.current_photo: Optional[str] = None
        self.default_location: Tuple[float, float] = (35.6762, 139.6503)  # Tokyo
        self.default_zoom: int = 10

        # 現在の座標
        self.current_latitude: Optional[float] = None
        self.current_longitude: Optional[float] = None

        # 複数画像の位置情報
        self.image_locations: List[Dict[str, Any]] = []

        # 一時ファイル管理
        self.temp_html_file: Optional[Path] = None

        # UIコンポーネント
        self.web_view: Optional[QWebEngineView] = None
        self.status_label: Optional[QLabel] = None
        self.map_widget: Optional[QWidget] = None

        # UI初期化
        self._setup_ui()
        self._setup_connections()

        # デフォルト地図で初期化
        self._initialize_map()

    def _setup_ui(self):
        """UIの初期化"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # タイトルバー（全画面ボタン付き）
            title_layout = QHBoxLayout()

            title_label = QLabel("🗺️ 地図表示")
            title_label.setStyleSheet("font-weight: bold; padding: 2px;")
            title_layout.addWidget(title_label)

            title_layout.addStretch()

            # 全画面ボタン
            fullscreen_btn = QPushButton("⛶")
            fullscreen_btn.setToolTip("全画面表示")
            fullscreen_btn.setFixedSize(24, 24)
            fullscreen_btn.clicked.connect(self._toggle_fullscreen)
            title_layout.addWidget(fullscreen_btn)

            layout.addLayout(title_layout)

            # 地図表示エリアの作成
            self._create_map_display_area(layout)

            # ステータスバー
            status_frame = QFrame()
            status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            status_frame.setMaximumHeight(30)

            status_layout = QHBoxLayout(status_frame)
            status_layout.setContentsMargins(5, 5, 5, 5)

            self.status_label = QLabel("準備完了")
            self.status_label.setStyleSheet("font-size: 11px; color: #666666;")
            status_layout.addWidget(self.status_label)

            status_layout.addStretch()

            # 地図コントロール
            reset_btn = QPushButton("🏠")
            reset_btn.setToolTip("デフォルト表示にリセット")
            reset_btn.setFixedSize(24, 24)
            reset_btn.clicked.connect(self._reset_view)
            status_layout.addWidget(reset_btn)

            refresh_btn = QPushButton("🔄")
            refresh_btn.setToolTip("地図を更新")
            refresh_btn.setFixedSize(24, 24)
            refresh_btn.clicked.connect(self._refresh_map)
            status_layout.addWidget(refresh_btn)

            layout.addWidget(status_frame)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "map_panel_setup"}, AIComponent.KIRO
            )

    def _create_map_display_area(self, layout):
        """地図表示エリアを作成"""
        try:
            # WebEngineが利用可能な場合
            if WEBENGINE_AVAILABLE and folium_available:
                # WebEngineViewを直接作成
                try:
                    self.web_view = QWebEngineView()
                    message = "WebEngineView created successfully"
                    print(f"✅ {message}")
                except Exception as e:
                    self.web_view = None
                    message = f"WebEngineView creation failed: {e}"
                    print(f"❌ {message}")

                if self.web_view:
                    self.web_view.setSizePolicy(
                        QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Expanding
                    )

                    # WebEngine設定
                    try:
                        settings = self.web_view.settings()
                        if settings and QWebEngineSettings is not None:
                            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
                            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
                    except Exception as e:
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "webengine_settings_warning",
                            f"WebEngine設定の適用に失敗: {e}",
                            level="WARNING"
                        )

                    layout.addWidget(self.web_view, 1)

                    if self.status_label:
                        self.status_label.setText("WebEngine地図表示モード")
                else:
                    # WebEngineViewの作成に失敗した場合
                    self._create_fallback_display()
                    if self.map_widget:
                        layout.addWidget(self.map_widget, 1)
            else:
                # WebEngineまたはfoliumが利用できない場合
                self._create_fallback_display()
                if self.map_widget:
                    layout.addWidget(self.map_widget, 1)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "create_map_display_area"}, AIComponent.KIRO
            )
            # エラーが発生した場合もフォールバック表示を作成
            self._create_fallback_display()
            if self.map_widget:
                layout.addWidget(self.map_widget, 1)

    def _create_fallback_display(self):
        """WebEngineが利用できない場合のフォールバック表示"""
        try:
            # スクロール可能なテキスト表示エリアを作成
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)

            # 地図情報表示用のテキストエリア
            self.map_widget = QTextEdit()
            self.map_widget.setReadOnly(True)
            self.map_widget.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    background-color: #f8f9fa;
                    color: #2c3e50;
                    padding: 10px;
                    font-size: 12px;
                    font-family: monospace;
                }
            """)

            # 初期メッセージ
            if not WEBENGINE_AVAILABLE:
                message = """🗺️ 地図表示 - テキストモード

⚠️  PyQtWebEngineが利用できないため、テキストベースの地図情報を表示します。

📍 現在の位置情報:
   まだ位置情報が設定されていません。

🔧 WebEngine地図表示を有効にするには:
   1. PyQtWebEngineをインストール: pip install PyQtWebEngine
   2. アプリケーションを再起動してください

📋 機能:
   • GPS座標の表示
   • 複数画像の位置情報一覧
   • 地図リンクの生成
"""
            elif not folium_available:
                message = """🗺️ 地図表示 - テキストモード

⚠️  Foliumが利用できないため、テキストベースの地図情報を表示します。

📍 現在の位置情報:
   まだ位置情報が設定されていません。

🔧 Folium地図表示を有効にするには:
   1. Foliumをインストール: pip install folium
   2. アプリケーションを再起動してください

📋 機能:
   • GPS座標の表示
   • 複数画像の位置情報一覧
   • 地図リンクの生成
"""
            else:
                message = """🗺️ 地図表示 - テキストモード

ℹ️  地図表示の初期化中です...

📍 現在の位置情報:
   まだ位置情報が設定されていません。

📋 機能:
   • GPS座標の表示
   • 複数画像の位置情報一覧
   • 地図リンクの生成
"""

            self.map_widget.setPlainText(message)
            scroll_area.setWidget(self.map_widget)
            self.map_widget = scroll_area

            if self.status_label:
                self.status_label.setText("テキストベース地図表示モード")

        except Exception as e:
            # 最後の手段として、シンプルなラベルを作成
            self.map_widget = QLabel("地図表示の初期化に失敗しました。")
            self.map_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.map_widget.setStyleSheet("""
                QLabel {
                    border: 1px solid #e74c3c;
                    border-radius: 3px;
                    background-color: #fdf2f2;
                    color: #e74c3c;
                    padding: 20px;
                    font-size: 12px;
                }
            """)

    def _setup_connections(self):
        """シグナル接続の設定"""
        try:
            if self.web_view:
                self.web_view.loadFinished.connect(self._on_map_loaded)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "setup_connections"}, AIComponent.KIRO
            )

    def _initialize_map(self):
        """デフォルト位置で地図を初期化"""
        try:
            if self.web_view and folium_available:
                # WebEngine地図の初期化
                self._create_map(self.default_location, self.default_zoom)
                if self.status_label:
                    self.status_label.setText("地図を初期化しました")
            else:
                # テキストベース表示の初期化
                self._update_fallback_display()
                if self.status_label:
                    self.status_label.setText("テキストベース地図表示を初期化しました")

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "initialize_map"}, AIComponent.KIRO
            )
            if self.web_view:
                self._show_error_message(f"地図の初期化に失敗しました: {e}")
            else:
                # テキストベース表示でもエラーを表示
                self._update_fallback_display()

    def _create_map(self, center: Tuple[float, float], zoom: int = 10, markers: Optional[Dict[str, Tuple[float, float]]] = None):
        """新しいFolium地図を作成"""
        try:
            if not folium_available or folium is None:
                return

            # Folium地図を作成
            map_obj = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )

            # 写真位置のマーカーを追加
            if markers:
                for photo_path, (lat, lon) in markers.items():
                    self._add_photo_marker(map_obj, photo_path, lat, lon)

            # 追加の地図レイヤー
            if hasattr(folium, 'TileLayer'):
                folium.TileLayer(
                    tiles='https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
                    attr='&copy; OpenStreetMap contributors, Tiles style by Humanitarian OpenStreetMap Team',
                    name='OpenStreetMap.HOT',
                    overlay=False,
                    control=True
                ).add_to(map_obj)

            # レイヤーコントロール
            if hasattr(folium, 'LayerControl'):
                folium.LayerControl().add_to(map_obj)

            # 全画面プラグイン
            if plugins and hasattr(plugins, 'Fullscreen'):
                plugins.Fullscreen().add_to(map_obj)

            # 一時ファイルに保存
            temp_dir = tempfile.gettempdir()
            self.current_map_file = os.path.join(temp_dir, "photogeoview_map.html")
            map_obj.save(self.current_map_file)

            # WebViewに読み込み
            if self.web_view:
                self.web_view.load(QUrl.fromLocalFile(self.current_map_file))

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "create_map"}, AIComponent.KIRO
            )
            self._show_error_message(f"地図の作成に失敗しました: {e}")

    def _add_photo_marker(self, map_obj: object, photo_path: str, lat: float, lon: float):
        """写真位置のマーカーを追加"""
        try:
            if not folium_available or folium is None:
                return

            photo_name = Path(photo_path).name

            # カスタムアイコンでマーカーを作成
            if hasattr(folium, 'Marker'):
                popup = None
                icon = None

                if hasattr(folium, 'Popup'):
                    popup = folium.Popup(f"📸 {photo_name}", max_width=200)

                if hasattr(folium, 'Icon'):
                    icon = folium.Icon(
                        icon='camera',
                        prefix='fa',
                        color='blue' if photo_path != self.current_photo else 'red'
                    )

                marker = folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    tooltip=photo_name,
                    icon=icon
                )

                marker.add_to(map_obj)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "add_photo_marker"}, AIComponent.KIRO
            )

    def set_coordinates(self, latitude: float, longitude: float):
        """座標を設定して地図を更新"""
        try:
            self.current_latitude = latitude
            self.current_longitude = longitude

            # 座標表示を更新
            if self.status_label:
                self.status_label.setText(f"座標: {latitude:.6f}, {longitude:.6f}")

            # 地図を更新
            if self.web_view:
                # WebEngine地図の更新
                self._update_map()
            else:
                # テキストベース表示の更新
                self._update_fallback_display()

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

            # photo_locationsにも追加
            self.photo_locations[str(image_path)] = (latitude, longitude)

            # 地図を更新
            if self.web_view:
                # WebEngine地図の更新
                self._update_map()
            else:
                # テキストベース表示の更新
                self._update_fallback_display()

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
            if self.photo_locations:
                # 全ての位置から中心点を計算
                lats = [lat for lat, _ in self.photo_locations.values()]
                lons = [lon for _, lon in self.photo_locations.values()]

                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)

                # 広がりに基づいて適切なズームレベルを決定
                lat_range = max(lats) - min(lats)
                lon_range = max(lons) - min(lons)
                max_range = max(lat_range, lon_range)

                if max_range < 0.01:
                    zoom = 15
                elif max_range < 0.1:
                    zoom = 12
                elif max_range < 1.0:
                    zoom = 8
                else:
                    zoom = 5

                self._create_map((center_lat, center_lon), zoom, self.photo_locations)

                if self.status_label:
                    self.status_label.setText(f"{len(self.photo_locations)}個の写真位置を表示中")

                # 最新の座標でシグナルを発信
                latest = list(self.photo_locations.values())[-1]
                self.map_loaded.emit(latest[0], latest[1])

            elif self.current_latitude is not None and self.current_longitude is not None:
                # 単一の座標
                self._create_map((self.current_latitude, self.current_longitude), 15)

                if self.status_label:
                    self.status_label.setText(f"座標: {self.current_latitude:.6f}, {self.current_longitude:.6f}")

                # シグナルを発信
                self.map_loaded.emit(self.current_latitude, self.current_longitude)
            else:
                # デフォルト地図を表示
                self._create_map(self.default_location, self.default_zoom)

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "update_map",
                f"地図を更新: {len(self.photo_locations)}個の位置情報",
                context={"locations_count": len(self.photo_locations)},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_map"}, AIComponent.KIRO
            )
            self._show_error_message("地図の更新に失敗しました")

    def _show_error_message(self, message: str):
        """エラーメッセージを表示"""
        try:
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>地図エラー</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f0f0f0;
                    }}
                    .error-container {{
                        text-align: center;
                        padding: 20px;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .error-icon {{
                        font-size: 48px;
                        color: #ff6b6b;
                        margin-bottom: 16px;
                    }}
                    .error-message {{
                        color: #666;
                        font-size: 16px;
                        margin-bottom: 8px;
                    }}
                    .error-details {{
                        color: #999;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error-icon">🗺️</div>
                    <div class="error-message">地図表示エラー</div>
                    <div class="error-details">{message}</div>
                </div>
            </body>
            </html>
            """

            # エラーHTMLを一時ファイルに保存
            temp_dir = tempfile.gettempdir()
            error_file = os.path.join(temp_dir, "photogeoview_error.html")

            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(error_html)

            if self.web_view:
                self.web_view.load(QUrl.fromLocalFile(error_file))

            if self.status_label:
                self.status_label.setText("地図の読み込みに失敗しました")

            # シグナルを発信
            self.map_error.emit(message)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "show_error_message"}, AIComponent.KIRO
            )

    def _on_map_loaded(self, success: bool):
        """地図読み込み完了の処理"""
        try:
            if success:
                if self.status_label:
                    self.status_label.setText("地図を読み込みました")
            else:
                if self.status_label:
                    self.status_label.setText("地図の読み込みに失敗しました")

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "on_map_loaded"}, AIComponent.KIRO
            )

    def _refresh_map(self):
        """地図を再読み込み"""
        try:
            if self.current_map_file and os.path.exists(self.current_map_file):
                if self.web_view:
                    self.web_view.reload()
                if self.status_label:
                    self.status_label.setText("地図を更新しました")
            else:
                self._initialize_map()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "refresh_map"}, AIComponent.KIRO
            )

    def _reset_view(self):
        """地図をデフォルト表示にリセット"""
        try:
            if self.photo_locations:
                # 全ての写真位置を表示
                self._update_map()
            else:
                # デフォルト位置にリセット
                self._create_map(self.default_location, self.default_zoom)
                if self.status_label:
                    self.status_label.setText("デフォルト表示にリセットしました")

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "reset_view"}, AIComponent.KIRO
            )

    def _toggle_fullscreen(self):
        """全画面表示の切り替え"""
        try:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "toggle_fullscreen"}, AIComponent.KIRO
            )

    def get_current_coordinates(self) -> Optional[Tuple[float, float]]:
        """現在の座標を取得"""
        if self.current_latitude is not None and self.current_longitude is not None:
            return (self.current_latitude, self.current_longitude)
        return None

    def get_image_locations(self) -> List[Dict[str, Any]]:
        """画像位置情報のリストを取得"""
        return self.image_locations.copy()

    def _update_fallback_display(self):
        """テキストベース表示を更新"""
        try:
            if not hasattr(self.map_widget, 'widget') or not hasattr(self.map_widget.widget(), 'setPlainText'):
                return

            text_widget = self.map_widget.widget()

            # 現在の位置情報を構築
            content = "🗺️ 地図表示 - テキストモード\n\n"

            if not WEBENGINE_AVAILABLE:
                content += "⚠️  PyQtWebEngineが利用できないため、テキストベースの地図情報を表示します。\n\n"
            elif not folium_available:
                content += "⚠️  Foliumが利用できないため、テキストベースの地図情報を表示します。\n\n"

            # 現在の座標情報
            content += "📍 現在の位置情報:\n"
            if self.current_latitude is not None and self.current_longitude is not None:
                content += f"   緯度: {self.current_latitude:.6f}\n"
                content += f"   経度: {self.current_longitude:.6f}\n"

                # Google Mapsリンク
                maps_url = f"https://www.google.com/maps?q={self.current_latitude},{self.current_longitude}"
                content += f"   🔗 Google Maps: {maps_url}\n"

                # OpenStreetMapリンク
                osm_url = f"https://www.openstreetmap.org/?mlat={self.current_latitude}&mlon={self.current_longitude}&zoom=15"
                content += f"   🔗 OpenStreetMap: {osm_url}\n"
            else:
                content += "   まだ位置情報が設定されていません。\n"

            content += "\n"

            # 複数画像の位置情報
            if self.image_locations:
                content += f"📸 画像位置情報 ({len(self.image_locations)}件):\n"
                for i, location in enumerate(self.image_locations, 1):
                    content += f"   {i}. {location['name']}\n"
                    content += f"      緯度: {location['lat']:.6f}, 経度: {location['lon']:.6f}\n"
                    maps_url = f"https://www.google.com/maps?q={location['lat']},{location['lon']}"
                    content += f"      🔗 {maps_url}\n"
                content += "\n"

            # 機能説明
            content += "📋 利用可能な機能:\n"
            content += "   • GPS座標の表示\n"
            content += "   • 複数画像の位置情報一覧\n"
            content += "   • 外部地図サービスへのリンク生成\n"

            if not WEBENGINE_AVAILABLE:
                content += "\n🔧 WebEngine地図表示を有効にするには:\n"
                content += "   1. PyQtWebEngineをインストール: pip install PyQtWebEngine\n"
                content += "   2. アプリケーションを再起動してください\n"
            elif not folium_available:
                content += "\n🔧 Folium地図表示を有効にするには:\n"
                content += "   1. Foliumをインストール: pip install folium\n"
                content += "   2. アプリケーションを再起動してください\n"

            text_widget.setPlainText(content)

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "update_fallback_display"}, AIComponent.KIRO
            )

    def closeEvent(self, event) -> None:
        """ウィンドウクローズ時のクリーンアップ"""
        try:
            # 一時ファイルのクリーンアップ
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
        except Exception:
            pass

        super().closeEvent(event)
