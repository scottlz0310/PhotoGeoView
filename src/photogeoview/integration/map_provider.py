"""
Map Provider - 地図表示プロバイダー

foliumを使用した地図表示機能の実装。
IMapProviderインターフェースを実装し、地図の作成、マーカーの追加、
HTMLレンダリングなどの機能を提供。

Author: Kiro AI Integration System
"""

from pathlib import Path
from typing import Any

import folium

from .config_manager import ConfigManager
from .error_handling import ErrorCategory, IntegratedErrorHandler
from .interfaces import IMapProvider
from .logging_system import LoggerSystem
from .models import AIComponent


class FoliumMapProvider(IMapProvider):
    """
    Folium-based map provider implementation

    Features:
    - Folium地図の作成と管理
    - マーカーの追加とカスタマイズ
    - HTMLレンダリング
    - 座標検証
    - エラーハンドリング
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        logger_system: LoggerSystem,
    ):
        self.config_manager = config_manager
        self.logger_system = logger_system
        self.error_handler = IntegratedErrorHandler(logger_system)

        # デフォルト設定
        self.default_zoom = self.config_manager.get_setting("core.map_zoom_default", 10)
        self.tile_layer = "OpenStreetMap"  # デフォルトタイルレイヤー

    def create_map(self, center: tuple[float, float], zoom: int = 10) -> Any:
        """
        Create a new folium map centered at the specified coordinates

        Args:
            center: (latitude, longitude) tuple for map center
            zoom: Initial zoom level

        Returns:
            Folium map object
        """
        try:
            lat, lon = center

            # 座標を検証
            if not self.validate_coordinates(lat, lon):
                raise ValueError(f"Invalid coordinates: {lat}, {lon}")

            # 地図を作成
            map_obj = folium.Map(
                location=[lat, lon],
                zoom_start=zoom,
                tiles=self.tile_layer,
                control_scale=True,
            )

            # ログ出力
            self.logger_system.log_info(
                f"地図を作成: 中心({lat:.6f}, {lon:.6f}), ズーム{zoom}",
                {"center": center, "zoom": zoom},
                AIComponent.COPILOT,
            )

            return map_obj

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "create_map", "center": center, "zoom": zoom},
                AIComponent.COPILOT,
            )
            return None

    def add_marker(self, map_obj: Any, lat: float, lon: float, popup: str = "") -> None:
        """
        Add a marker to the folium map

        Args:
            map_obj: Folium map object to add marker to
            lat: Latitude of marker
            lon: Longitude of marker
            popup: Optional popup text for marker
        """
        try:
            if not map_obj:
                return

            # 座標を検証
            if not self.validate_coordinates(lat, lon):
                self.logger_system.log_warning(
                    f"無効な座標でマーカーをスキップ: {lat}, {lon}",
                    {"lat": lat, "lon": lon},
                    AIComponent.COPILOT,
                )
                return

            # カスタムアイコンを作成
            icon = folium.Icon(color="red", icon="camera", prefix="fa")

            # マーカーを追加
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                icon=icon,
                tooltip=f"撮影位置: {lat:.6f}, {lon:.6f}",
            ).add_to(map_obj)

            # ログ出力
            self.logger_system.log_info(
                f"マーカーを追加: ({lat:.6f}, {lon:.6f})",
                {"lat": lat, "lon": lon, "popup": popup},
                AIComponent.COPILOT,
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "add_marker", "lat": lat, "lon": lon, "popup": popup},
                AIComponent.COPILOT,
            )

    def render_html(self, map_obj: Any) -> str:
        """
        Render folium map as HTML string

        Args:
            map_obj: Folium map object to render

        Returns:
            HTML representation of the map
        """
        try:
            if not map_obj:
                return ""

            # HTMLをレンダリング
            html_content = map_obj._repr_html_()

            # ログ出力
            self.logger_system.log_info(
                "地図をHTMLにレンダリング完了",
                {"html_length": len(html_content)},
                AIComponent.COPILOT,
            )

            return html_content

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "render_html"},
                AIComponent.COPILOT,
            )
            return ""

    def set_map_bounds(self, map_obj: Any, bounds: list[tuple[float, float]]) -> None:
        """
        Set folium map bounds to fit all specified coordinates

        Args:
            map_obj: Folium map object to modify
            bounds: List of (latitude, longitude) tuples
        """
        try:
            if not map_obj or not bounds:
                return

            # 有効な座標のみをフィルタリング
            valid_bounds = []
            for lat, lon in bounds:
                if self.validate_coordinates(lat, lon):
                    valid_bounds.append([lat, lon])

            if len(valid_bounds) >= 2:
                # 地図の境界を設定
                map_obj.fit_bounds(valid_bounds)

                # ログ出力
                self.logger_system.log_info(
                    f"地図境界を設定: {len(valid_bounds)}個の座標",
                    {"bounds_count": len(valid_bounds)},
                    AIComponent.COPILOT,
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "set_map_bounds", "bounds_count": len(bounds)},
                AIComponent.COPILOT,
            )

    def add_image_overlay(
        self,
        map_obj: Any,
        image_path: Path,
        bounds: tuple[tuple[float, float], tuple[float, float]],
    ) -> None:
        """
        Add an image overlay to the folium map

        Args:
            map_obj: Folium map object to add overlay to
            image_path: Path to overlay image
            bounds: ((south, west), (north, east)) bounds for overlay
        """
        try:
            if not map_obj or not image_path.exists():
                return

            # 境界座標を検証
            (south, west), (north, east) = bounds
            if not all(self.validate_coordinates(lat, lon) for lat, lon in [(south, west), (north, east)]):
                self.logger_system.log_warning(
                    "無効な境界座標でオーバーレイをスキップ",
                    {"bounds": bounds},
                    AIComponent.COPILOT,
                )
                return

            # 画像オーバーレイを追加
            folium.ImageOverlay(
                image=str(image_path),
                bounds=[[south, west], [north, east]],
                opacity=0.7,
                name="Image Overlay",
            ).add_to(map_obj)

            # ログ出力
            self.logger_system.log_info(
                f"画像オーバーレイを追加: {image_path.name}",
                {"image_path": str(image_path), "bounds": bounds},
                AIComponent.COPILOT,
            )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {
                    "operation": "add_image_overlay",
                    "image_path": str(image_path),
                    "bounds": bounds,
                },
                AIComponent.COPILOT,
            )

    def get_map_center(self, map_obj: Any) -> tuple[float, float]:
        """
        Get current center coordinates of the folium map

        Args:
            map_obj: Folium map object to query

        Returns:
            (latitude, longitude) tuple of map center
        """
        try:
            if not map_obj:
                return (0.0, 0.0)

            # 地図の中心座標を取得
            center = map_obj.location
            if center:
                return tuple(center)
            else:
                return (0.0, 0.0)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {"operation": "get_map_center"},
                AIComponent.COPILOT,
            )
            return (0.0, 0.0)

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Validate GPS coordinates

        Args:
            lat: Latitude to validate
            lon: Longitude to validate

        Returns:
            True if coordinates are valid, False otherwise
        """
        try:
            # 緯度の範囲: -90 から 90
            if not (-90 <= lat <= 90):
                return False

            # 経度の範囲: -180 から 180
            return -180 <= lon <= 180

        except (TypeError, ValueError):
            return False

    def create_map_with_marker(self, lat: float, lon: float, popup: str = "", zoom: int | None = None) -> str | None:
        """
        Create a map with a marker and return HTML

        Args:
            lat: Latitude
            lon: Longitude
            popup: Popup text for marker
            zoom: Zoom level (uses default if None)

        Returns:
            HTML string of the map, or None if failed
        """
        try:
            # 座標を検証
            if not self.validate_coordinates(lat, lon):
                self.logger_system.log_warning(
                    f"無効な座標で地図作成をスキップ: {lat}, {lon}",
                    {"lat": lat, "lon": lon},
                    AIComponent.COPILOT,
                )
                return None

            # ズームレベルを設定
            if zoom is None:
                zoom = self.default_zoom

            # 地図を作成
            map_obj = self.create_map((lat, lon), zoom)
            if not map_obj:
                return None

            # マーカーを追加
            self.add_marker(map_obj, lat, lon, popup)

            # HTMLをレンダリング
            html_content = self.render_html(map_obj)

            return html_content

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {
                    "operation": "create_map_with_marker",
                    "lat": lat,
                    "lon": lon,
                    "popup": popup,
                },
                AIComponent.COPILOT,
            )
            return None
