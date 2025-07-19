"""
EXIF情報解析機能を提供するモジュール
PhotoGeoView プロジェクト用のEXIFデータ処理機能
"""

import exifread
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from src.core.logger import get_logger
from src.core.utils import is_image_file


class ExifParser:
    """EXIF情報解析クラス"""

    def __init__(self):
        """ExifParserの初期化"""
        self.logger = get_logger(__name__)

    def parse_exif(self, file_path: str) -> Dict[str, Any]:
        """
        EXIF情報を解析

        Args:
            file_path: 画像ファイルパス

        Returns:
            EXIF情報辞書
        """
        try:
            if not is_image_file(file_path):
                self.logger.warning(f"画像ファイルではありません: {file_path}")
                return {}

            if not os.path.exists(file_path):
                self.logger.error(f"ファイルが存在しません: {file_path}")
                return {}

            # EXIF情報を読み込み
            with open(file_path, "rb") as f:
                tags = exifread.process_file(f, details=False)

            if not tags:
                self.logger.debug(f"EXIF情報が見つかりません: {file_path}")
                return {}

            # EXIF情報を解析
            exif_data = self._parse_tags(tags)

            self.logger.debug(f"EXIF情報を解析しました: {file_path}")
            return exif_data

        except Exception as e:
            self.logger.error(f"EXIF情報の解析に失敗しました: {file_path}, エラー: {e}")
            return {}

    def _parse_tags(self, tags: Dict) -> Dict[str, Any]:
        """
        EXIFタグを解析

        Args:
            tags: EXIFタグ辞書

        Returns:
            解析されたEXIF情報辞書
        """
        exif_data = {}

        try:
            # 撮影日時
            if "EXIF DateTimeOriginal" in tags:
                exif_data["datetime_original"] = self._parse_datetime(
                    str(tags["EXIF DateTimeOriginal"])
                )

            if "EXIF DateTime" in tags:
                exif_data["datetime"] = self._parse_datetime(str(tags["EXIF DateTime"]))

            # カメラ情報
            if "Image Make" in tags:
                exif_data["make"] = str(tags["Image Make"])

            if "Image Model" in tags:
                exif_data["model"] = str(tags["Image Model"])

            if "EXIF LensModel" in tags:
                exif_data["lens_model"] = str(tags["EXIF LensModel"])

            # 撮影設定
            if "EXIF ExposureTime" in tags:
                exif_data["exposure_time"] = str(tags["EXIF ExposureTime"])

            if "EXIF FNumber" in tags:
                exif_data["f_number"] = str(tags["EXIF FNumber"])

            if "EXIF ISOSpeedRatings" in tags:
                exif_data["iso"] = int(tags["EXIF ISOSpeedRatings"].values[0])

            if "EXIF FocalLength" in tags:
                exif_data["focal_length"] = str(tags["EXIF FocalLength"])

            # 画像サイズ
            if "EXIF ExifImageWidth" in tags:
                exif_data["width"] = int(tags["EXIF ExifImageWidth"].values[0])

            if "EXIF ExifImageLength" in tags:
                exif_data["height"] = int(tags["EXIF ExifImageLength"].values[0])

            # GPS情報
            gps_data = self._parse_gps_tags(tags)
            if gps_data:
                exif_data["gps"] = gps_data

            # その他の情報
            if "Image Software" in tags:
                exif_data["software"] = str(tags["Image Software"])

            if "EXIF Flash" in tags:
                exif_data["flash"] = str(tags["EXIF Flash"])

            if "EXIF WhiteBalance" in tags:
                exif_data["white_balance"] = str(tags["EXIF WhiteBalance"])

        except Exception as e:
            self.logger.error(f"EXIFタグの解析に失敗しました: {e}")

        return exif_data

    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        日時文字列を解析

        Args:
            datetime_str: 日時文字列

        Returns:
            解析されたdatetimeオブジェクト
        """
        try:
            # EXIFの日時形式: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            try:
                # 別の形式を試す
                return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            except ValueError:
                self.logger.warning(f"日時形式が認識できません: {datetime_str}")
                return None

    def _parse_gps_tags(self, tags: Dict) -> Optional[Dict[str, Any]]:
        """
        GPSタグを解析

        Args:
            tags: EXIFタグ辞書

        Returns:
            GPS情報辞書
        """
        gps_data = {}

        try:
            # GPS緯度
            if "GPS GPSLatitude" in tags and "GPS GPSLatitudeRef" in tags:
                lat = self._convert_to_degrees(tags["GPS GPSLatitude"].values)
                lat_ref = str(tags["GPS GPSLatitudeRef"].values[0])
                if lat_ref == "S":
                    lat = -lat
                gps_data["latitude"] = lat

            # GPS経度
            if "GPS GPSLongitude" in tags and "GPS GPSLongitudeRef" in tags:
                lon = self._convert_to_degrees(tags["GPS GPSLongitude"].values)
                lon_ref = str(tags["GPS GPSLongitudeRef"].values[0])
                if lon_ref == "W":
                    lon = -lon
                gps_data["longitude"] = lon

            # GPS高度
            if "GPS GPSAltitude" in tags:
                gps_data["altitude"] = float(tags["GPS GPSAltitude"].values[0])

            # GPS時刻
            if "GPS GPSTimeStamp" in tags:
                gps_time = tags["GPS GPSTimeStamp"].values
                if len(gps_time) >= 3:
                    hour = float(gps_time[0].num) / float(gps_time[0].den)
                    minute = float(gps_time[1].num) / float(gps_time[1].den)
                    second = float(gps_time[2].num) / float(gps_time[2].den)
                    gps_data["time"] = (
                        f"{int(hour):02d}:{int(minute):02d}:{int(second):02d}"
                    )

            # GPS日付
            if "GPS GPSDateStamp" in tags:
                gps_data["date"] = str(tags["GPS GPSDateStamp"].values[0])

        except Exception as e:
            self.logger.error(f"GPSタグの解析に失敗しました: {e}")

        return gps_data if gps_data else None

    def _convert_to_degrees(self, values) -> float:
        """
        GPS座標を度に変換

        Args:
            values: GPS座標値

        Returns:
            度単位の座標
        """
        try:
            degrees = float(values[0].num) / float(values[0].den)
            minutes = float(values[1].num) / float(values[1].den)
            seconds = float(values[2].num) / float(values[2].den)

            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        except Exception as e:
            self.logger.error(f"GPS座標の変換に失敗しました: {e}")
            return 0.0

    def get_gps_coordinates(self, file_path: str) -> Optional[Tuple[float, float]]:
        """
        GPS座標を取得

        Args:
            file_path: 画像ファイルパス

        Returns:
            (緯度, 経度)のタプル、GPS情報がない場合はNone
        """
        try:
            exif_data = self.parse_exif(file_path)

            if "gps" in exif_data:
                gps = exif_data["gps"]
                if "latitude" in gps and "longitude" in gps:
                    return (gps["latitude"], gps["longitude"])

            return None

        except Exception as e:
            self.logger.error(f"GPS座標の取得に失敗しました: {file_path}, エラー: {e}")
            return None

    def get_camera_info(self, file_path: str) -> Dict[str, str]:
        """
        カメラ情報を取得

        Args:
            file_path: 画像ファイルパス

        Returns:
            カメラ情報辞書
        """
        try:
            exif_data = self.parse_exif(file_path)

            camera_info = {}

            if "make" in exif_data:
                camera_info["make"] = exif_data["make"]

            if "model" in exif_data:
                camera_info["model"] = exif_data["model"]

            if "lens_model" in exif_data:
                camera_info["lens"] = exif_data["lens_model"]

            return camera_info

        except Exception as e:
            self.logger.error(
                f"カメラ情報の取得に失敗しました: {file_path}, エラー: {e}"
            )
            return {}

    def get_shooting_info(self, file_path: str) -> Dict[str, Any]:
        """
        撮影情報を取得

        Args:
            file_path: 画像ファイルパス

        Returns:
            撮影情報辞書
        """
        try:
            exif_data = self.parse_exif(file_path)

            shooting_info = {}

            if "datetime_original" in exif_data:
                shooting_info["datetime"] = exif_data["datetime_original"]

            if "exposure_time" in exif_data:
                shooting_info["exposure_time"] = exif_data["exposure_time"]

            if "f_number" in exif_data:
                shooting_info["f_number"] = exif_data["f_number"]

            if "iso" in exif_data:
                shooting_info["iso"] = exif_data["iso"]

            if "focal_length" in exif_data:
                shooting_info["focal_length"] = exif_data["focal_length"]

            if "flash" in exif_data:
                shooting_info["flash"] = exif_data["flash"]

            if "white_balance" in exif_data:
                shooting_info["white_balance"] = exif_data["white_balance"]

            return shooting_info

        except Exception as e:
            self.logger.error(f"撮影情報の取得に失敗しました: {file_path}, エラー: {e}")
            return {}

    def format_exif_info(self, file_path: str) -> str:
        """
        EXIF情報をフォーマットして文字列で返す

        Args:
            file_path: 画像ファイルパス

        Returns:
            フォーマットされたEXIF情報文字列
        """
        try:
            exif_data = self.parse_exif(file_path)

            if not exif_data:
                return "EXIF情報がありません"

            lines = []

            # 撮影日時
            if "datetime_original" in exif_data:
                lines.append(
                    f"撮影日時: {exif_data['datetime_original'].strftime('%Y-%m-%d %H:%M:%S')}"
                )

            # カメラ情報
            if "make" in exif_data and "model" in exif_data:
                lines.append(f"カメラ: {exif_data['make']} {exif_data['model']}")

            if "lens_model" in exif_data:
                lines.append(f"レンズ: {exif_data['lens_model']}")

            # 撮影設定
            if "exposure_time" in exif_data:
                lines.append(f"シャッター速度: {exif_data['exposure_time']}")

            if "f_number" in exif_data:
                lines.append(f"F値: {exif_data['f_number']}")

            if "iso" in exif_data:
                lines.append(f"ISO感度: {exif_data['iso']}")

            if "focal_length" in exif_data:
                lines.append(f"焦点距離: {exif_data['focal_length']}")

            # GPS情報
            if "gps" in exif_data:
                gps = exif_data["gps"]
                if "latitude" in gps and "longitude" in gps:
                    lines.append(f"緯度: {gps['latitude']:.6f}")
                    lines.append(f"経度: {gps['longitude']:.6f}")

                if "altitude" in gps:
                    lines.append(f"高度: {gps['altitude']:.1f}m")

            return "\n".join(lines)

        except Exception as e:
            self.logger.error(
                f"EXIF情報のフォーマットに失敗しました: {file_path}, エラー: {e}"
            )
            return "EXIF情報の読み込みに失敗しました"
