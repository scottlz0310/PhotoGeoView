#!/usr/bin/env python3
"""
PhotoGeoView専用画像メタデータ処理システム
Pillowの代替として機能特化したライブラリ構成
"""

import exifread
import piexif
from PIL.ExifTags import TAGS, GPSTAGS
import cv2
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QImage, QPixmap
import folium
import os
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Optional, Tuple, List
import hashlib
from PyQt6.QtWidgets import QApplication
import sys


class PhotoMetadataProcessor:
    """写真メタデータ処理の中核クラス"""

    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.tiff', '.tif']

    def extract_comprehensive_metadata(self, image_path: str) -> Dict:
        """
        包括的なメタデータ抽出
        EXIF、GPS、カメラ情報など全て取得
        """
        metadata = {
            'file_info': self._get_file_info(image_path),
            'exif_data': {},
            'gps_data': {},
            'camera_info': {},
            'datetime_info': {},
            'technical_info': {},
            'classification_tags': []
        }

        try:
            # Method 1: exifreadによる詳細EXIF取得
            with open(image_path, 'rb') as f:
                exif_tags = exifread.process_file(f, details=True)
                metadata['exif_data'] = self._process_exif_tags(exif_tags)

            # Method 2: piexifによるGPS特化処理
            exif_dict = piexif.load(image_path)
            metadata['gps_data'] = self._extract_gps_data(exif_dict)

            # カメラ情報分類
            metadata['camera_info'] = self._classify_camera_info(metadata['exif_data'])

            # 日時情報分類
            metadata['datetime_info'] = self._classify_datetime_info(metadata['exif_data'])

            # 技術情報分類
            metadata['technical_info'] = self._classify_technical_info(metadata['exif_data'])

            # 分類タグ生成
            metadata['classification_tags'] = self._generate_classification_tags(metadata)

        except Exception as e:
            metadata['error'] = str(e)

        return metadata

    def _get_file_info(self, image_path: str) -> Dict:
        """ファイル基本情報取得"""
        path_obj = Path(image_path)
        stat = path_obj.stat()

        return {
            'filename': path_obj.name,
            'extension': path_obj.suffix.lower(),
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'created_time': datetime.fromtimestamp(stat.st_ctime),
            'modified_time': datetime.fromtimestamp(stat.st_mtime),
            'file_hash': self._calculate_file_hash(image_path)
        }

    def _calculate_file_hash(self, image_path: str) -> str:
        """ファイルハッシュ計算（重複検出用）"""
        hash_md5 = hashlib.md5()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _process_exif_tags(self, exif_tags: Dict) -> Dict:
        """EXIF タグの処理と整理"""
        processed = {}

        for tag, value in exif_tags.items():
            try:
                # 文字列化して格納
                processed[tag] = str(value)
            except:
                processed[tag] = "読取不可"

        return processed

    def _extract_gps_data(self, exif_dict: Dict) -> Dict:
        """GPS データ特化抽出"""
        gps_data = {}

        if 'GPS' not in exif_dict:
            return gps_data

        gps_info = exif_dict['GPS']

        # GPS座標変換
        if piexif.GPSIFD.GPSLatitude in gps_info and piexif.GPSIFD.GPSLongitude in gps_info:
            lat = self._convert_gps_coordinate(
                gps_info[piexif.GPSIFD.GPSLatitude],
                gps_info.get(piexif.GPSIFD.GPSLatitudeRef, b'N')
            )
            lon = self._convert_gps_coordinate(
                gps_info[piexif.GPSIFD.GPSLongitude],
                gps_info.get(piexif.GPSIFD.GPSLongitudeRef, b'E')
            )

            gps_data['latitude'] = lat
            gps_data['longitude'] = lon
            gps_data['coordinates'] = (lat, lon)

        # 高度情報
        if piexif.GPSIFD.GPSAltitude in gps_info:
            altitude_raw = gps_info[piexif.GPSIFD.GPSAltitude]
            altitude = altitude_raw[0] / altitude_raw[1] if altitude_raw[1] != 0 else 0
            gps_data['altitude'] = altitude

        # GPS日時
        if piexif.GPSIFD.GPSDateStamp in gps_info:
            gps_data['gps_date'] = gps_info[piexif.GPSIFD.GPSDateStamp].decode()

        return gps_data

    def _convert_gps_coordinate(self, coord_tuple, ref):
        """GPS座標をdecimal度に変換"""
        degrees = coord_tuple[0][0] / coord_tuple[0][1]
        minutes = coord_tuple[1][0] / coord_tuple[1][1]
        seconds = coord_tuple[2][0] / coord_tuple[2][1]

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        if ref in [b'S', b'W']:
            decimal = -decimal

        return decimal

    def _classify_camera_info(self, exif_data: Dict) -> Dict:
        """カメラ情報の分類"""
        camera_info = {}

        # カメラメーカー・モデル
        for key, value in exif_data.items():
            if 'Make' in key:
                camera_info['make'] = value
            elif 'Model' in key:
                camera_info['model'] = value
            elif 'LensModel' in key:
                camera_info['lens'] = value

        return camera_info

    def _classify_datetime_info(self, exif_data: Dict) -> Dict:
        """日時情報の分類"""
        datetime_info = {}

        for key, value in exif_data.items():
            if 'DateTime' in key:
                try:
                    # EXIF日時フォーマットをパース
                    dt = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                    datetime_info[key.lower()] = {
                        'raw': value,
                        'parsed': dt,
                        'year': dt.year,
                        'month': dt.month,
                        'day': dt.day,
                        'hour': dt.hour
                    }
                except:
                    datetime_info[key.lower()] = {'raw': value, 'parsed': None}

        return datetime_info

    def _classify_technical_info(self, exif_data: Dict) -> Dict:
        """技術情報の分類"""
        tech_info = {}

        # 撮影設定
        settings_mapping = {
            'FNumber': 'aperture',
            'ExposureTime': 'shutter_speed',
            'ISOSpeedRatings': 'iso',
            'FocalLength': 'focal_length',
            'Flash': 'flash',
            'WhiteBalance': 'white_balance',
            'ExposureMode': 'exposure_mode'
        }

        for exif_key, tech_key in settings_mapping.items():
            for key, value in exif_data.items():
                if exif_key in key:
                    tech_info[tech_key] = value
                    break

        return tech_info

    def _generate_classification_tags(self, metadata: Dict) -> List[str]:
        """メタデータベースの分類タグ生成"""
        tags = []

        # カメラベースタグ
        camera = metadata.get('camera_info', {})
        if 'make' in camera:
            tags.append(f"camera:{camera['make']}")
        if 'model' in camera:
            tags.append(f"model:{camera['model']}")

        # 日時ベースタグ
        datetime_info = metadata.get('datetime_info', {})
        for dt_key, dt_data in datetime_info.items():
            if dt_data.get('parsed'):
                dt = dt_data['parsed']
                tags.extend([
                    f"year:{dt.year}",
                    f"month:{dt.month:02d}",
                    f"season:{self._get_season(dt.month)}"
                ])
                break

        # GPS ベースタグ
        gps = metadata.get('gps_data', {})
        if 'coordinates' in gps:
            tags.append("geotagged:true")
            # 地域判定（簡易版）
            lat, lon = gps['coordinates']
            region = self._determine_region(lat, lon)
            if region:
                tags.append(f"region:{region}")
        else:
            tags.append("geotagged:false")

        # 技術仕様ベースタグ
        tech = metadata.get('technical_info', {})
        if 'iso' in tech:
            try:
                iso_val = int(str(tech['iso']).split()[0])
                if iso_val >= 1600:
                    tags.append("lowlight:true")
                tags.append(f"iso_range:{self._get_iso_range(iso_val)}")
            except:
                pass

        return list(set(tags))  # 重複除去

    def _get_season(self, month: int) -> str:
        """月から季節判定"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"

    def _determine_region(self, lat: float, lon: float) -> str:
        """座標から地域判定（簡易版）"""
        if 24 <= lat <= 46 and 123 <= lon <= 146:
            return "japan"
        elif 37 <= lat <= 42 and -125 <= lon <= -117:
            return "usa_west"
        elif 25 <= lat <= 49 and -95 <= lon <= -67:
            return "usa_east"
        elif 36 <= lat <= 71 and -11 <= lon <= 32:
            return "europe"
        else:
            return "other"

    def _get_iso_range(self, iso: int) -> str:
        """ISO値から範囲分類"""
        if iso <= 200:
            return "low"
        elif iso <= 800:
            return "medium"
        elif iso <= 3200:
            return "high"
        else:
            return "ultra_high"


class OptimizedThumbnailGenerator:
    """最適化されたサムネイル生成器"""

    def __init__(self):
        self.cache = {}

    def generate_thumbnail(self, image_path: str, size: int = 256) -> Tuple[Optional[QPixmap], str]:
        """
        高品質サムネイル生成
        """
        cache_key = f"{image_path}_{size}"
        if cache_key in self.cache:
            return self.cache[cache_key], "キャッシュから取得"

        try:
            # OpenCVで高品質読み込み
            img = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if img is None:
                return None, "画像読み込み失敗"

            # アスペクト比保持リサイズ
            h, w = img.shape[:2]
            if w > h:
                new_w, new_h = size, int(size * h / w)
            else:
                new_w, new_h = int(size * w / h), size

            # 高品質リサイズ
            thumbnail = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

            # エッジ強調（オプション）
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            thumbnail = cv2.filter2D(thumbnail, -1, kernel * 0.1 + np.eye(3) * 0.9)

            # BGR → RGB変換
            thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)

            # QPixmap変換
            h, w, ch = thumbnail_rgb.shape
            bytes_per_line = ch * w

            q_image = QImage(
                thumbnail_rgb.data, w, h, bytes_per_line,
                QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(q_image)

            # キャッシュに保存
            self.cache[cache_key] = pixmap

            return pixmap, f"生成成功 {new_w}x{new_h}"

        except Exception as e:
            return None, f"エラー: {str(e)}"


class GeoMapGenerator:
    """ジオタグベースの地図生成器"""

    def __init__(self):
        self.photo_locations = []

    def add_photo_location(self, metadata: Dict, image_path: str):
        """写真の位置情報を追加"""
        gps_data = metadata.get('gps_data', {})
        if 'coordinates' in gps_data:
            self.photo_locations.append({
                'path': image_path,
                'coordinates': gps_data['coordinates'],
                'metadata': metadata,
                'filename': metadata['file_info']['filename']
            })

    def generate_map(self, output_path: str = "photo_map.html") -> str:
        """フォトマップ生成"""
        if not self.photo_locations:
            return "位置情報付きの写真がありません"

        # 中心座標計算
        lats = [loc['coordinates'][0] for loc in self.photo_locations]
        lons = [loc['coordinates'][1] for loc in self.photo_locations]

        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)

        # Foliumマップ作成
        photo_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='OpenStreetMap'
        )

        # 各写真の位置にマーカー追加
        for i, location in enumerate(self.photo_locations):
            lat, lon = location['coordinates']

            # ポップアップ情報作成
            popup_html = self._create_popup_html(location)

            # マーカー追加
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=location['filename'],
                icon=folium.Icon(color='blue', icon='camera')
            ).add_to(photo_map)

        # HTML保存
        photo_map.save(output_path)
        return f"地図を {output_path} に保存しました"

    def _create_popup_html(self, location: Dict) -> str:
        """マーカーポップアップのHTML作成"""
        metadata = location['metadata']

        html = f"""
        <div style='width:250px'>
            <h4>{location['filename']}</h4>
            <p><strong>座標:</strong> {location['coordinates'][0]:.6f}, {location['coordinates'][1]:.6f}</p>
        """

        # カメラ情報
        camera = metadata.get('camera_info', {})
        if camera:
            html += f"<p><strong>カメラ:</strong> {camera.get('make', '')} {camera.get('model', '')}</p>"

        # 撮影日時
        datetime_info = metadata.get('datetime_info', {})
        for dt_key, dt_data in datetime_info.items():
            if dt_data.get('parsed'):
                html += f"<p><strong>撮影日時:</strong> {dt_data['parsed'].strftime('%Y-%m-%d %H:%M:%S')}</p>"
                break

        html += "</div>"
        return html


# 使用例とテストコード
def test_photo_processing():
    app = QApplication(sys.argv)  # 追加: Qtアプリケーションの初期化
    processor = PhotoMetadataProcessor()
    thumbnail_gen = OptimizedThumbnailGenerator()
    map_gen = GeoMapGenerator()

    # テスト画像を探す
    test_images = []
    for ext in ['.jpg', '.jpeg']:
        test_images.extend(Path('.').rglob(f'*{ext}'))

    if not test_images:
        print("テスト用JPEG画像が見つかりません")
        return

    print("=== PhotoGeoView メタデータ処理テスト ===")

    for img_path in test_images[:3]:  # 最初の3枚をテスト
        print(f"\n📸 処理中: {img_path.name}")

        # 1. メタデータ抽出
        metadata = processor.extract_comprehensive_metadata(str(img_path))

        print(f"  ✅ ファイル情報: {metadata['file_info']['size_mb']:.2f}MB")
        print(f"  ✅ 分類タグ: {metadata['classification_tags']}")

        if metadata['gps_data']:
            print(f"  🗺️ GPS: {metadata['gps_data']['coordinates']}")
            map_gen.add_photo_location(metadata, str(img_path))

        # 2. サムネイル生成
        thumbnail, msg = thumbnail_gen.generate_thumbnail(str(img_path), 128)
        print(f"  🖼️ サムネイル: {msg}")

    # 3. 地図生成
    if map_gen.photo_locations:
        map_result = map_gen.generate_map("test_photo_map.html")
        print(f"\n🗺️ {map_result}")

    print("\n✅ テスト完了")
    app.quit()  # 追加: Qtアプリケーションの終了


if __name__ == '__main__':
    test_photo_processing()
