"""
地図表示機能を提供するモジュール
PhotoGeoView プロジェクト用の地図表示機能
"""

import os
import tempfile
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage

import folium

from src.core.logger import get_logger
from src.core.settings import get_settings


class MapViewer(QWidget):
    """地図表示ウィジェット"""

    # シグナル定義
    map_loaded = pyqtSignal()  # 地図読み込み完了時に発信
    marker_clicked = pyqtSignal(str)  # マーカークリック時に発信

    def __init__(self, parent=None):
        """
        MapViewerの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.settings = get_settings()

        # 地図データ
        self._map_data: Optional[folium.Map] = None
        self._markers: Dict[str, Dict[str, Any]] = {}
        self._temp_html_file: Optional[str] = None

        # 地図設定
        self._center: Tuple[float, float] = (35.6762, 139.6503)  # 東京
        self._zoom: int = 10
        self._tile_layer: str = "OpenStreetMap"

        # UI初期化
        self._init_ui()
        self._init_map()

        self.logger.debug("MapViewerを初期化しました")

    def _init_ui(self) -> None:
        """UIの初期化"""
        # メインレイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ツールバー
        self._init_toolbar()
        layout.addLayout(self.toolbar_layout)

        # 地図表示エリア
        self._init_map_area()
        layout.addWidget(self.map_frame, 1)

    def _init_toolbar(self) -> None:
        """ツールバーの初期化"""
        self.toolbar_layout = QHBoxLayout()

        # ズームアウトボタン
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setToolTip("ズームアウト")
        self.zoom_out_button.setMaximumWidth(30)

        # ズームレベル表示
        self.zoom_label = QLabel("10")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setMinimumWidth(30)

        # ズームインボタン
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setToolTip("ズームイン")
        self.zoom_in_button.setMaximumWidth(30)

        # リセットボタン
        self.reset_button = QPushButton("リセット")
        self.reset_button.setToolTip("地図をリセット")

        # 全画面ボタン
        self.fullscreen_button = QPushButton("全画面")
        self.fullscreen_button.setToolTip("全画面表示")

        # ツールバーに追加
        self.toolbar_layout.addWidget(self.zoom_out_button)
        self.toolbar_layout.addWidget(self.zoom_label)
        self.toolbar_layout.addWidget(self.zoom_in_button)
        self.toolbar_layout.addStretch()
        self.toolbar_layout.addWidget(self.reset_button)
        self.toolbar_layout.addWidget(self.fullscreen_button)

    def _init_map_area(self) -> None:
        """地図表示エリアの初期化"""
        self.map_frame = QFrame()
        self.map_frame.setFrameStyle(QFrame.Shape.StyledPanel)

        # WebEngineビュー
        self.web_view = QWebEngineView()
        self.web_view.setMinimumSize(400, 300)

        # カスタムページを作成（JavaScript通信用）
        self.web_page = CustomWebPage()
        self.web_view.setPage(self.web_page)

        # JavaScript通信の設定
        self.web_page.marker_clicked.connect(self._on_marker_clicked)

        # レイアウト
        map_layout = QVBoxLayout(self.map_frame)
        map_layout.addWidget(self.web_view)

    def _init_map(self) -> None:
        """地図の初期化"""
        try:
            # 設定から地図設定を取得
            map_settings = self.settings.get_map_settings()
            self._center = tuple(
                map_settings.get("default_center", [35.6762, 139.6503])
            )
            self._zoom = map_settings.get("default_zoom", 10)
            self._tile_layer = map_settings.get("tile_layer", "OpenStreetMap")

            # Folium地図を作成
            self._create_folium_map()

            # 地図を表示
            self._load_map()

        except Exception as e:
            self.logger.error(f"地図の初期化に失敗しました: {e}")
            self._show_error_message("地図の初期化に失敗しました")

    def _create_folium_map(self) -> None:
        """Folium地図を作成"""
        try:
            # 地図を作成
            self._map_data = folium.Map(
                location=self._center,
                zoom_start=self._zoom,
                tiles=self._tile_layer,
                control_scale=True,
            )

            # カスタムJavaScriptを追加
            self._add_custom_javascript()

            self.logger.debug("Folium地図を作成しました")

        except Exception as e:
            self.logger.error(f"Folium地図の作成に失敗しました: {e}")
            raise

    def _add_custom_javascript(self) -> None:
        """カスタムJavaScriptを追加"""
        if not self._map_data:
            return

        # マーカークリックイベント用のJavaScript
        js_code = """
        <script>
        // マーカークリックイベントの設定
        function setupMarkerClick() {
            // 既存のマーカーにクリックイベントを追加
            var markers = document.querySelectorAll('.leaflet-marker-icon');
            markers.forEach(function(marker) {
                marker.addEventListener('click', function(e) {
                    var markerId = this.getAttribute('data-marker-id');
                    if (markerId) {
                        // Qtにイベントを送信
                        if (typeof qt !== 'undefined' && qt.webChannelTransport) {
                            qt.webChannelTransport.send(JSON.stringify({
                                type: 'marker_clicked',
                                marker_id: markerId
                            }));
                        }
                    }
                });
            });
        }

        // ページ読み込み完了時に実行
        document.addEventListener('DOMContentLoaded', function() {
            setupMarkerClick();
        });

        // 地図読み込み完了時に実行
        if (typeof L !== 'undefined') {
            L.map.on('load', function() {
                setupMarkerClick();
            });
        }
        </script>
        """

        # HTMLにJavaScriptを追加
        self._map_data.get_root().html.add_child(folium.Element(js_code))

    def _load_map(self) -> None:
        """地図を読み込み"""
        try:
            if not self._map_data:
                self.logger.error("地図データがありません")
                return

            # 一時HTMLファイルを作成
            self._temp_html_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            )

            # 地図をHTMLとして保存
            self._map_data.save(self._temp_html_file.name)
            self._temp_html_file.close()

            # WebEngineでHTMLを読み込み
            url = QUrl.fromLocalFile(self._temp_html_file.name)
            self.web_view.load(url)

            # ズームレベルを更新
            self.zoom_label.setText(str(self._zoom))

            self.logger.debug("地図を読み込みました")

        except Exception as e:
            self.logger.error(f"地図の読み込みに失敗しました: {e}")
            self._show_error_message("地図の読み込みに失敗しました")

    def add_marker(
        self,
        marker_id: str,
        coordinates: Tuple[float, float],
        title: str = "",
        description: str = "",
    ) -> bool:
        """
        マーカーを追加

        Args:
            marker_id: マーカーID
            coordinates: 座標 (緯度, 経度)
            title: マーカータイトル
            description: マーカー説明

        Returns:
            追加成功の場合True
        """
        try:
            if not self._map_data:
                self.logger.error("地図データがありません")
                return False

            # マーカー情報を保存
            self._markers[marker_id] = {
                "coordinates": coordinates,
                "title": title,
                "description": description,
            }

            # Foliumマーカーを追加
            folium.Marker(
                location=coordinates,
                popup=f"<b>{title}</b><br>{description}",
                tooltip=title,
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(self._map_data)

            # 地図を再読み込み
            self._reload_map()

            self.logger.debug(f"マーカーを追加しました: {marker_id}")
            return True

        except Exception as e:
            self.logger.error(f"マーカーの追加に失敗しました: {marker_id}, エラー: {e}")
            return False

    def remove_marker(self, marker_id: str) -> bool:
        """
        マーカーを削除

        Args:
            marker_id: マーカーID

        Returns:
            削除成功の場合True
        """
        try:
            if marker_id in self._markers:
                del self._markers[marker_id]

                # 地図を再作成（Foliumでは個別マーカー削除が困難なため）
                self._create_folium_map()

                # 残りのマーカーを再追加
                for mid, marker_data in self._markers.items():
                    folium.Marker(
                        location=marker_data["coordinates"],
                        popup=f"<b>{marker_data['title']}</b><br>{marker_data['description']}",
                        tooltip=marker_data["title"],
                        icon=folium.Icon(color="red", icon="info-sign"),
                    ).add_to(self._map_data)

                # 地図を再読み込み
                self._reload_map()

                self.logger.debug(f"マーカーを削除しました: {marker_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"マーカーの削除に失敗しました: {marker_id}, エラー: {e}")
            return False

    def clear_markers(self) -> None:
        """すべてのマーカーを削除"""
        try:
            self._markers.clear()
            self._create_folium_map()
            self._reload_map()
            self.logger.debug("すべてのマーカーを削除しました")

        except Exception as e:
            self.logger.error(f"マーカーのクリアに失敗しました: {e}")

    def set_center(self, coordinates: Tuple[float, float]) -> None:
        """
        地図の中心を設定

        Args:
            coordinates: 座標 (緯度, 経度)
        """
        try:
            self._center = coordinates
            self._create_folium_map()
            self._reload_map()
            self.logger.debug(f"地図の中心を設定しました: {coordinates}")

        except Exception as e:
            self.logger.error(f"地図の中心設定に失敗しました: {e}")

    def set_zoom(self, zoom_level: int) -> None:
        """
        ズームレベルを設定

        Args:
            zoom_level: ズームレベル
        """
        try:
            self._zoom = max(1, min(18, zoom_level))
            self._create_folium_map()
            self._reload_map()
            self.zoom_label.setText(str(self._zoom))
            self.logger.debug(f"ズームレベルを設定しました: {zoom_level}")

        except Exception as e:
            self.logger.error(f"ズームレベルの設定に失敗しました: {e}")

    def zoom_in(self) -> None:
        """ズームイン"""
        self.set_zoom(self._zoom + 1)

    def zoom_out(self) -> None:
        """ズームアウト"""
        self.set_zoom(self._zoom - 1)

    def reset_map(self) -> None:
        """地図をリセット"""
        try:
            # 設定から初期値を取得
            map_settings = self.settings.get_map_settings()
            self._center = tuple(
                map_settings.get("default_center", [35.6762, 139.6503])
            )
            self._zoom = map_settings.get("default_zoom", 10)

            # マーカーをクリア
            self.clear_markers()

            # 地図を再作成
            self._create_folium_map()
            self._reload_map()

            self.logger.debug("地図をリセットしました")

        except Exception as e:
            self.logger.error(f"地図のリセットに失敗しました: {e}")

    def _reload_map(self) -> None:
        """地図を再読み込み"""
        try:
            if self._temp_html_file and os.path.exists(self._temp_html_file.name):
                # 既存のHTMLファイルを更新
                self._map_data.save(self._temp_html_file.name)

                # WebEngineで再読み込み
                url = QUrl.fromLocalFile(self._temp_html_file.name)
                self.web_view.load(url)

                self.logger.debug("地図を再読み込みしました")

        except Exception as e:
            self.logger.error(f"地図の再読み込みに失敗しました: {e}")

    def _on_marker_clicked(self, marker_id: str) -> None:
        """
        マーカークリック時の処理

        Args:
            marker_id: マーカーID
        """
        self.logger.debug(f"マーカーがクリックされました: {marker_id}")
        self.marker_clicked.emit(marker_id)

    def _show_error_message(self, message: str) -> None:
        """
        エラーメッセージを表示

        Args:
            message: エラーメッセージ
        """
        self.web_view.setHtml(
            f"""
        <html>
        <body style="display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: Arial, sans-serif;">
            <div style="text-align: center; color: #666;">
                <h3>地図読み込みエラー</h3>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """
        )

    def get_markers(self) -> Dict[str, Dict[str, Any]]:
        """
        マーカー情報を取得

        Returns:
            マーカー情報辞書
        """
        return self._markers.copy()

    def get_center(self) -> Tuple[float, float]:
        """
        地図の中心座標を取得

        Returns:
            中心座標 (緯度, 経度)
        """
        return self._center

    def get_zoom(self) -> int:
        """
        現在のズームレベルを取得

        Returns:
            ズームレベル
        """
        return self._zoom

    def closeEvent(self, event) -> None:
        """クローズイベント"""
        # 一時ファイルを削除
        if self._temp_html_file and os.path.exists(self._temp_html_file.name):
            try:
                os.unlink(self._temp_html_file.name)
            except Exception as e:
                self.logger.error(f"一時ファイルの削除に失敗しました: {e}")

        super().closeEvent(event)


class CustomWebPage(QWebEnginePage):
    """カスタムWebページ（JavaScript通信用）"""

    # シグナル定義
    marker_clicked = pyqtSignal(str)  # マーカークリック時に発信

    def __init__(self, parent=None):
        """
        CustomWebPageの初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """JavaScriptコンソールメッセージの処理"""
        self.logger.debug(f"JavaScript: {message} (line {lineNumber})")

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        """ナビゲーション要求の処理"""
        # ローカルファイルのみ許可
        if url.scheme() == "file":
            return True
        return False
