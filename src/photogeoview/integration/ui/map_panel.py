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
from typing import Any

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# WebEngineの安全な初期化
WEBENGINE_AVAILABLE = False
QWebEngineView = None
QWebEngineSettings = None

# 直接インポートを試行(OpenGL設定が適用されている場合)
try:
    from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView

    # 簡単な初期化テスト
    try:
        profile = QWebEngineProfile.defaultProfile()
        WEBENGINE_AVAILABLE = True
        print("✅ WebEngine直接初期化成功")
    except Exception:
        print("⚠️  WebEngine初期化テスト失敗")
        QWebEngineView = None
        QWebEngineSettings = None

except ImportError as e:
    print(f"⚠️  WebEngine直接インポート失敗: {e}")

    # フォールバック: webengine_checkerを使用
    try:
        from ..utils.webengine_checker import get_webengine_status

        webengine_status = get_webengine_status()
        if webengine_status["available"]:
            from PySide6.QtWebEngineCore import QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView

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
    - 地図操作(ズーム・パン)
    - PyQtWebEngineが利用できない場合の代替表示
    - 複数画像の位置情報表示
    """

    # シグナル
    map_loaded = Signal(float, float)  # latitude, longitude
    map_error = Signal(str)  # error message
    location_selected = Signal(float, float)  # lat, lon

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
        self.current_map_file: str | None = None
        self.photo_locations: dict[str, tuple[float, float]] = {}
        self.current_photo: str | None = None
        self.default_location: tuple[float, float] = (35.6762, 139.6503)  # Tokyo
        self.default_zoom: int = 10

        # 現在の座標
        self.current_latitude: float | None = None
        self.current_longitude: float | None = None

        # 複数画像の位置情報
        self.image_locations: list[dict[str, Any]] = []

        # 一時ファイル管理
        self.temp_html_file: Path | None = None

        # UIコンポーネント
        self.web_view: QWebEngineView | None = None
        self.status_label: QLabel | None = None
        self.map_widget: QWidget | None = None

        # 全画面表示フラグ
        self.is_fullscreen_mode = False

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

            # タイトルバー(全画面ボタン付き)
            title_layout = QHBoxLayout()

            title_label = QLabel("🗺️ 地図表示")
            title_label.setStyleSheet("font-weight: bold; padding: 2px;")
            title_layout.addWidget(title_label)

            title_layout.addStretch()

            # 全画面ボタン
            self.fullscreen_button = QPushButton("⛶ 地図全画面")
            self.fullscreen_button.setToolTip(
                "地図をウィンドウいっぱいに表示 / 通常表示に戻る"
            )
            self.fullscreen_button.setFixedSize(90, 24)
            self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
            title_layout.addWidget(self.fullscreen_button)

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
            reset_btn = QPushButton("🏠 フォーカス")
            reset_btn.setToolTip("選択画像にフォーカス / デフォルト表示にリセット")
            reset_btn.setFixedSize(80, 24)
            reset_btn.clicked.connect(self._reset_view)
            status_layout.addWidget(reset_btn)

            # 全体表示ボタン
            overview_btn = QPushButton("🌍 全体")
            overview_btn.setToolTip("全ての画像位置を表示")
            overview_btn.setFixedSize(60, 24)
            overview_btn.clicked.connect(self._show_overview)
            status_layout.addWidget(overview_btn)

            layout.addWidget(status_frame)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "map_panel_setup"},
                AIComponent.KIRO,
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
                        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                    )

                    # WebEngine設定
                    try:
                        settings = self.web_view.settings()
                        if settings and QWebEngineSettings is not None:
                            settings.setAttribute(
                                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
                                True,
                            )
                            settings.setAttribute(
                                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
                                True,
                            )
                    except Exception as e:
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "webengine_settings_warning",
                            f"WebEngine設定の適用に失敗: {e}",
                            level="WARNING",
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
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_map_display_area"},
                AIComponent.KIRO,
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
            self.map_widget.setStyleSheet(
                """
                QTextEdit {
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    background-color: #f8f9fa;
                    color: #2c3e50;
                    padding: 10px;
                    font-size: 12px;
                    font-family: monospace;
                }
            """
            )

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

        except Exception:
            # 最後の手段として、シンプルなラベルを作成
            self.map_widget = QLabel("地図表示の初期化に失敗しました。")
            self.map_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.map_widget.setStyleSheet(
                """
                QLabel {
                    border: 1px solid #e74c3c;
                    border-radius: 3px;
                    background-color: #fdf2f2;
                    color: #e74c3c;
                    padding: 20px;
                    font-size: 12px;
                }
            """
            )

    def _setup_connections(self):
        """シグナル接続の設定"""
        try:
            if self.web_view:
                self.web_view.loadFinished.connect(self._on_map_loaded)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "setup_connections"},
                AIComponent.KIRO,
            )

    def _initialize_map(self):
        """デフォルト位置で地図を初期化"""
        try:
            if self.web_view and folium_available:
                # WebEngine地図の初期化 - ウェルカム画面を表示
                self._create_welcome_html()
                if self.status_label:
                    self.status_label.setText("GPS情報付き画像を選択してください")
            else:
                # テキストベース表示の初期化
                self._update_fallback_display()
                if self.status_label:
                    self.status_label.setText("テキストベース地図表示を初期化しました")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "initialize_map"},
                AIComponent.KIRO,
            )
            if self.web_view:
                self._show_error_message(f"地図の初期化に失敗しました: {e}")
            else:
                # テキストベース表示でもエラーを表示
                self._update_fallback_display()

    def _create_map(
        self,
        center: tuple[float, float],
        zoom: int = 10,
        markers: dict[str, tuple[float, float]] | None = None,
    ):
        """新しいFolium地図を作成"""
        try:
            if not folium_available or folium is None:
                return

            # Folium地図を作成
            map_obj = folium.Map(
                location=center, zoom_start=zoom, tiles="OpenStreetMap"
            )

            # 写真位置のマーカーを追加
            if markers:
                for photo_path, (lat, lon) in markers.items():
                    self._add_photo_marker(map_obj, photo_path, lat, lon)

            # 追加の地図レイヤー
            if hasattr(folium, "TileLayer"):
                folium.TileLayer(
                    tiles="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                    attr="&copy; OpenStreetMap contributors, Tiles style by Humanitarian OpenStreetMap Team",
                    name="OpenStreetMap.HOT",
                    overlay=False,
                    control=True,
                ).add_to(map_obj)

            # レイヤーコントロール
            if hasattr(folium, "LayerControl"):
                folium.LayerControl().add_to(map_obj)

            # 全画面プラグイン
            if plugins and hasattr(plugins, "Fullscreen"):
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

    def _add_photo_marker(
        self, map_obj: object, photo_path: str, lat: float, lon: float
    ):
        """写真位置のマーカーを追加"""
        try:
            if not folium_available or folium is None:
                return

            photo_name = Path(photo_path).name

            # カスタムアイコンでマーカーを作成
            if hasattr(folium, "Marker"):
                popup = None
                icon = None

                # 現在選択されている画像かどうかを判定
                is_current_photo = (
                    self.current_latitude == lat and self.current_longitude == lon
                )

                if hasattr(folium, "Popup"):
                    # より詳細なポップアップ情報
                    popup_content = f"""
                    <div style="text-align: center;">
                        <h4>📸 {photo_name}</h4>
                        <p><strong>座標:</strong><br/>
                        {lat:.6f}, {lon:.6f}</p>
                        {'<p style="color: red; font-weight: bold;">📍 現在選択中</p>' if is_current_photo else ""}
                    </div>
                    """
                    popup = folium.Popup(popup_content, max_width=250)

                if hasattr(folium, "Icon"):
                    # 現在選択されている画像は赤色、それ以外は青色
                    icon_color = "red" if is_current_photo else "blue"
                    icon = folium.Icon(icon="camera", prefix="fa", color=icon_color)

                marker = folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    tooltip=f"{photo_name}{' (選択中)' if is_current_photo else ''}",
                    icon=icon,
                )

                marker.add_to(map_obj)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "add_photo_marker"},
                AIComponent.KIRO,
            )

    def set_coordinates(
        self,
        latitude: float,
        longitude: float,
        focus_on_location: bool = True,
        image_path: str | None = None,
    ):
        """座標を設定して地図を更新"""
        try:
            self.current_latitude = latitude
            self.current_longitude = longitude

            # 現在選択されている画像のパスを更新
            if image_path:
                self.current_photo = image_path

            # 座標表示を更新
            if self.status_label:
                self.status_label.setText(f"座標: {latitude:.6f}, {longitude:.6f}")

            # 地図を更新
            if self.web_view:
                # WebEngine地図の更新
                if focus_on_location:
                    # 個別の位置にフォーカス
                    self._focus_on_location(latitude, longitude)
                else:
                    # 全体的な地図更新
                    self._update_map()
            else:
                # テキストベース表示の更新
                self._update_fallback_display()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_coordinates", "lat": latitude, "lon": longitude},
                AIComponent.KIRO,
            )

    def _focus_on_location(self, latitude: float, longitude: float):
        """特定の位置にフォーカスして地図を更新"""
        try:
            # 個別の位置に適切な縮尺でフォーカス
            # 他の画像との距離に基づいてズームレベルを調整
            zoom_level = self._calculate_optimal_zoom(latitude, longitude)

            # その位置のマーカーのみを表示
            single_marker = {f"current_{latitude}_{longitude}": (latitude, longitude)}

            self._create_map((latitude, longitude), zoom_level, single_marker)

            if self.status_label:
                self.status_label.setText(
                    f"フォーカス: {latitude:.6f}, {longitude:.6f}"
                )

            # シグナルを発信
            self.map_loaded.emit(latitude, longitude)

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "focus_on_location",
                f"位置にフォーカス: ({latitude:.6f}, {longitude:.6f})",
                context={
                    "latitude": latitude,
                    "longitude": longitude,
                    "zoom": zoom_level,
                },
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "focus_on_location", "lat": latitude, "lon": longitude},
                AIComponent.KIRO,
            )
            self._show_error_message("位置へのフォーカスに失敗しました")

    def _calculate_optimal_zoom(self, latitude: float, longitude: float) -> int:
        """最適なズームレベルを計算"""
        try:
            if not self.photo_locations:
                return 15  # デフォルトズーム

            # 他の画像との距離を計算
            distances = []
            for lat, lon in self.photo_locations.values():
                if lat != latitude or lon != longitude:
                    # 簡易的な距離計算(緯度経度の差)
                    lat_diff = abs(lat - latitude)
                    lon_diff = abs(lon - longitude)
                    distance = max(lat_diff, lon_diff)
                    distances.append(distance)

            if not distances:
                return 15  # 他の画像がない場合

            # 最も近い画像との距離に基づいてズームレベルを決定
            min_distance = min(distances)

            if min_distance < 0.001:  # 非常に近い(約100m以内)
                return 18
            elif min_distance < 0.01:  # 近い(約1km以内)
                return 16
            elif min_distance < 0.1:  # 中程度(約10km以内)
                return 14
            elif min_distance < 1.0:  # 遠い(約100km以内)
                return 12
            else:  # 非常に遠い
                return 10

        except Exception as e:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "zoom_calculation_error",
                f"ズームレベル計算エラー: {e}",
                level="WARNING",
            )
            return 15  # デフォルトズーム

    def add_image_location(
        self, image_path: Path, latitude: float, longitude: float, name: str | None = None
    ):
        """画像の位置情報を追加"""
        try:
            location = {
                "path": image_path,
                "lat": latitude,
                "lon": longitude,
                "name": name or image_path.name,
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
                context={
                    "image_path": str(image_path),
                    "latitude": latitude,
                    "longitude": longitude,
                },
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "add_image_location", "image_path": str(image_path)},
                AIComponent.KIRO,
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
                    self.status_label.setText(
                        f"{len(self.photo_locations)}個の写真位置を表示中"
                    )

                # 最新の座標でシグナルを発信
                latest = list(self.photo_locations.values())[-1]
                self.map_loaded.emit(latest[0], latest[1])

            elif (
                self.current_latitude is not None and self.current_longitude is not None
            ):
                # 単一の座標
                self._create_map((self.current_latitude, self.current_longitude), 15)

                if self.status_label:
                    self.status_label.setText(
                        f"座標: {self.current_latitude:.6f}, {self.current_longitude:.6f}"
                    )

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

    def _create_welcome_html(self):
        """初期状態用のウェルカムHTML表示を作成"""
        try:
            welcome_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>PhotoGeoView - 地図表示</title>
                <meta charset="utf-8">
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .welcome-container {
                        text-align: center;
                        padding: 40px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 16px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        max-width: 500px;
                    }
                    .welcome-icon {
                        font-size: 64px;
                        margin-bottom: 20px;
                        animation: pulse 2s infinite;
                    }
                    .welcome-title {
                        font-size: 28px;
                        font-weight: 600;
                        margin-bottom: 16px;
                        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                    }
                    .welcome-message {
                        font-size: 16px;
                        line-height: 1.6;
                        margin-bottom: 24px;
                        opacity: 0.9;
                    }
                    .instruction {
                        font-size: 14px;
                        padding: 16px;
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        border-left: 4px solid #4CAF50;
                        margin-top: 20px;
                    }
                    @keyframes pulse {
                        0% { transform: scale(1); }
                        50% { transform: scale(1.05); }
                        100% { transform: scale(1); }
                    }
                </style>
            </head>
            <body>
                <div class="welcome-container">
                    <div class="welcome-icon">🗺️</div>
                    <div class="welcome-title">PhotoGeoView 地図表示</div>
                    <div class="welcome-message">
                        GPS位置情報付きの写真を選択すると、<br>
                        撮影場所がこの地図に表示されます。
                    </div>
                    <div class="instruction">
                        💡 左側のフォルダーから画像フォルダーを選択し、<br>
                        GPS情報を含む写真をクリックしてください
                    </div>
                </div>
            </body>
            </html>
            """

            # ウェルカムHTMLを一時ファイルに保存
            temp_dir = tempfile.gettempdir()
            welcome_file = os.path.join(temp_dir, "photogeoview_welcome.html")

            with open(welcome_file, "w", encoding="utf-8") as f:
                f.write(welcome_html)

            if self.web_view:
                self.web_view.load(QUrl.fromLocalFile(welcome_file))

            if self.status_label:
                self.status_label.setText("GPS情報付き画像を選択してください")

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_welcome_html"},
                AIComponent.KIRO,
            )

    def _create_no_gps_html(self, image_name: str = ""):
        """GPS情報なし画像用のHTML表示を作成"""
        try:
            no_gps_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>PhotoGeoView - GPS情報なし</title>
                <meta charset="utf-8">
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
                        color: #2d3436;
                    }}
                    .no-gps-container {{
                        text-align: center;
                        padding: 40px;
                        background: rgba(255, 255, 255, 0.9);
                        border-radius: 16px;
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.3);
                        max-width: 500px;
                    }}
                    .no-gps-icon {{
                        font-size: 64px;
                        margin-bottom: 20px;
                        opacity: 0.7;
                    }}
                    .no-gps-title {{
                        font-size: 24px;
                        font-weight: 600;
                        margin-bottom: 16px;
                        color: #e17055;
                    }}
                    .image-name {{
                        font-size: 16px;
                        font-weight: 500;
                        margin-bottom: 20px;
                        padding: 12px;
                        background: rgba(116, 185, 255, 0.1);
                        border-radius: 8px;
                        color: #0984e3;
                    }}
                    .no-gps-message {{
                        font-size: 16px;
                        line-height: 1.6;
                        margin-bottom: 24px;
                        color: #636e72;
                    }}
                    .suggestion {{
                        font-size: 14px;
                        padding: 16px;
                        background: rgba(116, 185, 255, 0.1);
                        border-radius: 8px;
                        border-left: 4px solid #0984e3;
                        margin-top: 20px;
                        text-align: left;
                    }}
                    .suggestion-title {{
                        font-weight: 600;
                        margin-bottom: 8px;
                        color: #0984e3;
                    }}
                </style>
            </head>
            <body>
                <div class="no-gps-container">
                    <div class="no-gps-icon">📍</div>
                    <div class="no-gps-title">GPS情報が見つかりません</div>
                    {f'<div class="image-name">📸 {image_name}</div>' if image_name else ""}
                    <div class="no-gps-message">
                        この画像にはGPS位置情報が含まれていないため、<br>
                        地図上に撮影場所を表示できません。
                    </div>
                    <div class="suggestion">
                        <div class="suggestion-title">💡 GPS情報付き画像を撮影するには:</div>
                        • カメラやスマートフォンの位置情報設定をオンにする<br>
                        • 屋外で十分なGPS信号を受信できる場所で撮影する<br>
                        • 撮影時にGPS機能が有効になっていることを確認する
                    </div>
                </div>
            </body>
            </html>
            """

            # GPS情報なしHTMLを一時ファイルに保存
            temp_dir = tempfile.gettempdir()
            no_gps_file = os.path.join(temp_dir, "photogeoview_no_gps.html")

            with open(no_gps_file, "w", encoding="utf-8") as f:
                f.write(no_gps_html)

            if self.web_view:
                self.web_view.load(QUrl.fromLocalFile(no_gps_file))

            if self.status_label:
                status_msg = (
                    f"GPS情報なし: {image_name}"
                    if image_name
                    else "GPS情報が含まれていません"
                )
                self.status_label.setText(status_msg)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_no_gps_html"},
                AIComponent.KIRO,
            )

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

            with open(error_file, "w", encoding="utf-8") as f:
                f.write(error_html)

            if self.web_view:
                self.web_view.load(QUrl.fromLocalFile(error_file))

            if self.status_label:
                self.status_label.setText("地図の読み込みに失敗しました")

            # シグナルを発信
            self.map_error.emit(message)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_error_message"},
                AIComponent.KIRO,
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
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "on_map_loaded"},
                AIComponent.KIRO,
            )

    def _reset_view(self):
        """現在選択されている画像の位置にフォーカス、またはデフォルト表示にリセット"""
        try:
            # 現在選択されている画像がある場合はその位置にフォーカス
            if (
                self.current_latitude is not None
                and self.current_longitude is not None
                and self.current_photo is not None
            ):
                # 現在選択されている画像の位置にフォーカス
                self._focus_on_location(self.current_latitude, self.current_longitude)

                if self.status_label:
                    self.status_label.setText(
                        f"選択画像にフォーカス: {Path(self.current_photo).name}"
                    )

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "reset_to_selected_image",
                    f"選択画像にフォーカス: {self.current_photo}",
                    context={
                        "latitude": self.current_latitude,
                        "longitude": self.current_longitude,
                    },
                )

            elif self.photo_locations:
                # 選択されている画像がないが位置情報がある場合は全体表示
                self._update_map()

                if self.status_label:
                    self.status_label.setText(
                        f"{len(self.photo_locations)}個の写真位置を表示中"
                    )

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "reset_to_overview",
                    f"全体表示にリセット: {len(self.photo_locations)}個の位置情報",
                )

            else:
                # 位置情報がない場合はデフォルト位置にリセット
                self._create_map(self.default_location, self.default_zoom)

                if self.status_label:
                    self.status_label.setText("デフォルト表示にリセットしました")

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "reset_to_default",
                    "デフォルト位置にリセット",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e, ErrorCategory.UI_ERROR, {"operation": "reset_view"}, AIComponent.KIRO
            )

    def _show_overview(self):
        """全ての画像位置を表示"""
        try:
            if self.photo_locations:
                # 全体的な地図更新(全ての位置を表示)
                self._update_map()

                if self.status_label:
                    self.status_label.setText(
                        f"{len(self.photo_locations)}個の写真位置を表示中"
                    )

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "show_overview",
                    f"全体表示: {len(self.photo_locations)}個の位置情報",
                    context={"locations_count": len(self.photo_locations)},
                )
            else:
                # 位置情報がない場合はデフォルト表示
                self._reset_view()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_overview"},
                AIComponent.KIRO,
            )

    def _toggle_fullscreen(self):
        """地図パネルをウィンドウいっぱいに表示"""
        try:
            # 親ウィンドウを取得
            parent_window = self.window()

            if self.is_fullscreen_mode:
                # 通常表示に戻る
                self.is_fullscreen_mode = False

                # 地図パネルを元の親に戻す
                if hasattr(self, "_original_parent"):
                    self.setParent(self._original_parent)
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "debug_restore_parent",
                        f"地図パネルを元の親に戻しました: {type(self._original_parent).__name__}",
                        level="INFO",
                    )
                    delattr(self, "_original_parent")

                # 他のUI要素を再表示
                self._show_other_ui_elements()

                # ステータスバーを表示
                if hasattr(self, "status_label") and self.status_label:
                    self.status_label.setVisible(True)

                # 地図パネルのサイズを元に戻す
                self.setMaximumSize(16777215, 16777215)
                self.adjustSize()

                # ボタンテキストを元に戻す
                if hasattr(self, "fullscreen_button"):
                    self.fullscreen_button.setText("⛶ 地図全画面")

                # 元のフォーカスポリシーを復元
                if hasattr(self, "_original_focus_policy"):
                    self.setFocusPolicy(self._original_focus_policy)
                    delattr(self, "_original_focus_policy")

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exit_map_fullscreen",
                    "地図全画面表示を終了",
                )

            else:
                # 地図パネルを最大化
                self.is_fullscreen_mode = True

                # 他のUI要素を非表示
                self._hide_other_ui_elements()

                # ステータスバーを非表示(地図をより大きく表示)
                if hasattr(self, "status_label") and self.status_label:
                    self.status_label.setVisible(False)

                # 地図パネルを親ウィンドウの子ウィジェットとして配置
                parent = self.parent()
                if parent:
                    # 元の親を保存
                    self._original_parent = parent
                    # 親ウィンドウに直接配置
                    self.setParent(parent_window)
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "debug_reparent_to_window",
                        f"地図パネルを親ウィンドウに配置しました: {type(parent_window).__name__}",
                        level="INFO",
                    )

                # 地図パネルを確実に表示
                self.setVisible(True)
                self.raise_()  # 最前面に表示

                # 地図パネルをウィンドウいっぱいに表示
                self.setMaximumSize(16777215, 16777215)
                self.resize(parent_window.size())

                # 地図パネルを親ウィンドウの中央に配置
                self.move(0, 0)

                # 地図パネルの表示状態を強制的に確認
                if not self.isVisible():
                    self.show()
                    self.raise_()

                # 親ウィジェットの構造をデバッグ
                parent = self.parent()
                if parent:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "debug_parent_structure",
                        f"親ウィジェット: {type(parent).__name__}, サイズ={parent.size()}",
                        level="INFO",
                    )
                else:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "debug_no_parent",
                        "親ウィジェットが見つかりません",
                        level="WARNING",
                    )

                # 地図コンテンツを確実に表示・リサイズ
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_fullscreen_start",
                    f"全画面表示開始: 地図パネルサイズ={self.size()}, WebView={self.web_view is not None}, MapWidget={self.map_widget is not None}",
                    level="INFO",
                )

                if self.web_view:
                    # WebViewを確実に表示・リサイズ
                    self.web_view.setVisible(True)
                    self.web_view.resize(self.size())
                    self.web_view.reload()

                    # WebViewの表示状態を強制的に確認・修正
                    if not self.web_view.isVisible():
                        self.web_view.show()
                        self.web_view.raise_()

                    # 地図パネル自体も強制的に表示
                    self.show()
                    self.raise_()

                    # レイアウトを強制的に更新
                    self.updateGeometry()
                    self.update()

                    # さらに強制的にWebViewを表示
                    self.web_view.setVisible(True)
                    self.web_view.show()
                    self.web_view.raise_()

                    # 地図パネルも再度確認
                    self.setVisible(True)
                    self.show()
                    self.raise_()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "debug_webview_fullscreen",
                        f"WebView全画面表示: サイズ={self.size()}, 表示状態={self.web_view.isVisible()}, 親={self.web_view.parent()}, 地図パネル表示={self.isVisible()}",
                        level="INFO",
                    )
                elif self.map_widget:
                    # MapWidgetを確実に表示・リサイズ
                    self.map_widget.setVisible(True)
                    self.map_widget.resize(self.size())

                    # MapWidgetの表示状態を強制的に確認・修正
                    if not self.map_widget.isVisible():
                        self.map_widget.show()
                        self.map_widget.raise_()

                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "debug_mapwidget_fullscreen",
                        f"MapWidget全画面表示: サイズ={self.size()}, 表示状態={self.map_widget.isVisible()}, 親={self.map_widget.parent()}",
                        level="INFO",
                    )
                else:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "debug_no_map_content",
                        "地図コンテンツが見つかりません",
                        level="WARNING",
                    )

                # レイアウトを更新
                self.updateGeometry()
                self.update()

                # 地図が表示されない場合の代替手段:少し遅延してから地図を再描画
                QTimer.singleShot(100, self._refresh_map_content)

                # 最終的な表示状態を確認
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_final_state",
                    f"最終状態: 地図パネル表示={self.isVisible()}, WebView表示={self.web_view.isVisible() if self.web_view else 'N/A'}, サイズ={self.size()}",
                    level="INFO",
                )

                # ボタンテキストを「戻る」に変更
                if hasattr(self, "fullscreen_button"):
                    self.fullscreen_button.setText("⛶ 戻る")

                # フォーカスを確実に設定(ESCキーを受信するため)
                self.setFocus(Qt.FocusReason.OtherFocusReason)

                # フォーカスポリシーを一時的に強化
                self._original_focus_policy = self.focusPolicy()
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

                # ログ出力
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "enter_map_fullscreen",
                    "地図全画面表示を開始",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "toggle_fullscreen"},
                AIComponent.KIRO,
            )

    def _hide_other_ui_elements(self):
        """他のUI要素を非表示にする(安全な方法)"""
        try:
            # 親ウィンドウを取得
            parent_window = self.window()

            # 非表示にするウィジェットのリストを初期化
            if not hasattr(self, "_hidden_widgets"):
                self._hidden_widgets = []

            # メインスプリッターを探す
            from PySide6.QtWidgets import QSplitter

            main_splitter = None
            for child in parent_window.findChildren(QSplitter):
                # 最初に見つかったQSplitterをメインスプリッターとする
                main_splitter = child
                break

            if main_splitter:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_splitter_found",
                    f"メインスプリッター発見: {type(main_splitter).__name__}, 子要素数: {main_splitter.count()}",
                    level="INFO",
                )

                # メインスプリッターの子要素を非表示にする
                for i in range(main_splitter.count()):
                    widget = main_splitter.widget(i)
                    if widget and widget != self and widget.isVisible():
                        widget.setVisible(False)
                        self._hidden_widgets.append(widget)
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "debug_hide_widget",
                            f"ウィジェットを非表示: {type(widget).__name__}",
                            level="INFO",
                        )

                        # 左パネルスプリッター内の要素も非表示
                        if hasattr(widget, "count"):  # スプリッターの場合
                            for j in range(widget.count()):
                                sub_widget = widget.widget(j)
                                if sub_widget and sub_widget.isVisible():
                                    sub_widget.setVisible(False)
                                    self._hidden_widgets.append(sub_widget)
                                    self.logger_system.log_ai_operation(
                                        AIComponent.KIRO,
                                        "debug_hide_sub_widget",
                                        f"サブウィジェットを非表示: {type(sub_widget).__name__}",
                                        level="INFO",
                                    )
            else:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_splitter_not_found",
                    "メインスプリッターが見つかりませんでした",
                    level="WARNING",
                )

            # デバッグ用ログ
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "hide_ui_elements",
                f"非表示にしたウィジェット数: {len(self._hidden_widgets)}",
                level="INFO",
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "hide_other_ui_elements"},
                AIComponent.KIRO,
            )

    def _show_other_ui_elements(self):
        """他のUI要素を再表示する(安全な方法)"""
        try:
            # 非表示にしたウィジェットを再表示
            if hasattr(self, "_hidden_widgets"):
                for widget in self._hidden_widgets:
                    if widget and hasattr(widget, "setVisible"):
                        widget.setVisible(True)
                        self.logger_system.log_ai_operation(
                            AIComponent.KIRO,
                            "debug_show_widget",
                            f"ウィジェットを再表示: {type(widget).__name__}",
                            level="INFO",
                        )

                self._hidden_widgets.clear()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "show_ui_elements",
                    "全てのウィジェットを再表示しました",
                    level="INFO",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_other_ui_elements"},
                AIComponent.KIRO,
            )

    def _refresh_map_content(self):
        """地図コンテンツを再描画"""
        try:
            if self.web_view:
                # WebViewの地図を再描画
                if (
                    self.current_latitude is not None
                    and self.current_longitude is not None
                ):
                    self._focus_on_location(
                        self.current_latitude, self.current_longitude
                    )
                else:
                    self._update_map()

                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "debug_map_refresh",
                    "地図コンテンツを再描画しました",
                    level="INFO",
                )
            elif self.map_widget:
                # テキストベース地図を更新
                self._update_fallback_display()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "refresh_map_content"},
                AIComponent.KIRO,
            )

    def get_current_coordinates(self) -> tuple[float, float] | None:
        """現在の座標を取得"""
        if self.current_latitude is not None and self.current_longitude is not None:
            return (self.current_latitude, self.current_longitude)
        return None

    def show_no_gps_message(self, image_name: str = ""):
        """GPS情報がない画像用の表示"""
        try:
            if self.web_view:
                # WebEngine地図でGPS情報なし表示
                self._create_no_gps_html(image_name)
            else:
                # テキストベース表示でGPS情報なし表示
                self._update_fallback_display_no_gps(image_name)

            # ログ出力
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "show_no_gps_message",
                f"GPS情報なし表示: {image_name}",
                context={"image_name": image_name},
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_no_gps_message", "image_name": image_name},
                AIComponent.KIRO,
            )

    def get_image_locations(self) -> list[dict[str, Any]]:
        """画像位置情報のリストを取得"""
        return self.image_locations.copy()

    def _update_fallback_display(self):
        """テキストベース表示を更新"""
        try:
            if not hasattr(self.map_widget, "widget") or not hasattr(
                self.map_widget.widget(), "setPlainText"
            ):
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
                content += (
                    "   1. PyQtWebEngineをインストール: pip install PyQtWebEngine\n"
                )
                content += "   2. アプリケーションを再起動してください\n"
            elif not folium_available:
                content += "\n🔧 Folium地図表示を有効にするには:\n"
                content += "   1. Foliumをインストール: pip install folium\n"
                content += "   2. アプリケーションを再起動してください\n"

            text_widget.setPlainText(content)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_fallback_display"},
                AIComponent.KIRO,
            )

    def _update_fallback_display_no_gps(self, image_name: str = ""):
        """GPS情報なし画像用のテキストベース表示を更新"""
        try:
            if not hasattr(self.map_widget, "widget") or not hasattr(
                self.map_widget.widget(), "setPlainText"
            ):
                return

            text_widget = self.map_widget.widget()

            # GPS情報なし用のコンテンツを構築
            content = "🗺️ 地図表示 - テキストモード\n\n"

            if not WEBENGINE_AVAILABLE:
                content += "⚠️  PyQtWebEngineが利用できないため、テキストベースの地図情報を表示します。\n\n"
            elif not folium_available:
                content += "⚠️  Foliumが利用できないため、テキストベースの地図情報を表示します。\n\n"

            # GPS情報なしメッセージ
            content += "📍 GPS情報が見つかりません\n\n"

            if image_name:
                content += f"📸 選択された画像: {image_name}\n\n"

            content += "この画像にはGPS位置情報が含まれていないため、\n"
            content += "地図上に撮影場所を表示できません。\n\n"

            # GPS情報付き画像を撮影するためのヒント
            content += "💡 GPS情報付き画像を撮影するには:\n"
            content += "   • カメラやスマートフォンの位置情報設定をオンにする\n"
            content += "   • 屋外で十分なGPS信号を受信できる場所で撮影する\n"
            content += "   • 撮影時にGPS機能が有効になっていることを確認する\n\n"

            # 既存の画像位置情報があれば表示
            if self.image_locations:
                content += f"📸 他の画像の位置情報 ({len(self.image_locations)}件):\n"
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
                content += (
                    "   1. PyQtWebEngineをインストール: pip install PyQtWebEngine\n"
                )
                content += "   2. アプリケーションを再起動してください\n"
            elif not folium_available:
                content += "\n🔧 Folium地図表示を有効にするには:\n"
                content += "   1. Foliumをインストール: pip install folium\n"
                content += "   2. アプリケーションを再起動してください\n"

            text_widget.setPlainText(content)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_fallback_display_no_gps"},
                AIComponent.KIRO,
            )

    def keyPressEvent(self, event):
        """キーボードイベントの処理"""
        try:
            # ESCキーで地図全画面表示を終了
            if (
                event.key() == Qt.Key.Key_Escape and self.is_fullscreen_mode
            ) or event.key() == Qt.Key.Key_F11:
                self._toggle_fullscreen()
                event.accept()
                return

            super().keyPressEvent(event)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "keyPressEvent"},
                AIComponent.KIRO,
            )
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        """ウィンドウクローズ時のクリーンアップ"""
        try:
            # 一時ファイルのクリーンアップ
            if self.temp_html_file and self.temp_html_file.exists():
                self.temp_html_file.unlink()
        except Exception:
            pass

        super().closeEvent(event)
