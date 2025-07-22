#!/usr/bin/env python3
"""
地図表示デバッグテスト
"""

import folium
import tempfile
import os
from pathlib import Path
from src.modules.exif_parser import ExifParser

def test_simple_map():
    """シンプルな地図生成テスト"""
    print("=== シンプルな地図生成テスト ===")

    # 東京の座標で地図を作成
    tokyo_map = folium.Map(
        location=[35.6762, 139.6503],
        zoom_start=10,
        tiles='OpenStreetMap'
    )

    # マーカーを追加
    folium.Marker(
        location=[35.6762, 139.6503],
        popup="東京",
        tooltip="東京",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(tokyo_map)

    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        tokyo_map.save(f.name)
        print(f"地図を保存しました: {f.name}")

        # ファイルサイズを確認
        size = os.path.getsize(f.name)
        print(f"ファイルサイズ: {size} bytes")

        # ファイルの最初の部分を表示
        with open(f.name, 'r') as read_f:
            content = read_f.read(500)  # 最初の500文字
            print(f"HTMLの開始部分:\n{content}...")

        return f.name

def test_gps_extraction():
    """GPS情報抽出テスト"""
    print("\n=== GPS情報抽出テスト ===")

    parser = ExifParser()
    test_images = [
        '/home/hiro/Repository/photomap-explorer/test_images/PIC001.jpg',
        '/home/hiro/Repository/PhotoGeoView/tests/test_data/images/with_gps/england-london-bridge.jpg'
    ]

    gps_found = []

    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n画像テスト: {Path(image_path).name}")
            exif_data = parser.parse_exif(image_path)

            if 'gps' in exif_data:
                gps = exif_data['gps']
                if 'latitude' in gps and 'longitude' in gps:
                    lat, lon = gps['latitude'], gps['longitude']
                    print(f"  GPS座標: {lat:.6f}, {lon:.6f}")
                    gps_found.append((Path(image_path).name, lat, lon))
                else:
                    print("  GPS情報が不完全です")
            else:
                print("  GPS情報が見つかりませんでした")
        else:
            print(f"画像が見つかりません: {image_path}")

    return gps_found

def test_gps_map(gps_data):
    """GPS情報を使用した地図生成テスト"""
    print("\n=== GPS情報を使用した地図生成テスト ===")

    if not gps_data:
        print("GPS情報付きの画像がありません")
        return None

    # 最初の画像の座標を中心とする
    center_lat = gps_data[0][1]
    center_lon = gps_data[0][2]

    # 地図を作成
    photo_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # 各画像の位置にマーカーを追加
    for image_name, lat, lon in gps_data:
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>{image_name}</b><br>GPS: {lat:.6f}, {lon:.6f}",
            tooltip=image_name,
            icon=folium.Icon(color="blue", icon="camera")
        ).add_to(photo_map)
        print(f"マーカー追加: {image_name} ({lat:.6f}, {lon:.6f})")

    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        photo_map.save(f.name)
        print(f"GPS地図を保存しました: {f.name}")

        # ファイルサイズを確認
        size = os.path.getsize(f.name)
        print(f"ファイルサイズ: {size} bytes")

        return f.name

if __name__ == "__main__":
    try:
        # 基本的な地図テスト
        simple_map_file = test_simple_map()

        # GPS情報の抽出テスト
        gps_data = test_gps_extraction()

        # GPS地図生成テスト
        if gps_data:
            gps_map_file = test_gps_map(gps_data)
            print(f"\n生成された地図ファイル:")
            print(f"  シンプル地図: {simple_map_file}")
            print(f"  GPS地図: {gps_map_file}")
        else:
            print("\nGPS情報付きの画像が見つからなかったため、GPS地図は生成されませんでした")

        print("\n=== テスト完了 ===")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
