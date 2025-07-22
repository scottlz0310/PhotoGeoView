#!/usr/bin/env python3
"""
地図HTMLファイル生成と確認テスト
"""

import sys
sys.path.insert(0, '/home/hiro/Repository/PhotoGeoView')

import folium
import tempfile
import os
from pathlib import Path

def create_test_map():
    """テスト用地図を作成してHTMLファイルを生成"""
    print("=== 地図HTML生成テスト ===")

    # 地図を作成
    test_map = folium.Map(
        location=[35.6762, 139.6503],
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # マーカーを追加
    folium.Marker(
        location=[35.6762, 139.6503],
        popup="<b>東京駅</b><br>テスト用マーカー",
        tooltip="東京駅",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(test_map)

    # 一時HTMLファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        test_map.save(f.name)
        file_path = f.name

    # ファイル情報を表示
    file_size = os.path.getsize(file_path)
    print(f"生成されたHTMLファイル: {file_path}")
    print(f"ファイルサイズ: {file_size} bytes")

    # HTMLの内容をチェック
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

        # 重要な要素のチェック
        checks = [
            ('Leaflet CSS', 'leaflet@1.9.3/dist/leaflet.css'),
            ('Leaflet JS', 'leaflet@1.9.3/dist/leaflet.js'),
            ('地図コンテナ', 'id="map_'),
            ('マーカー', 'L.marker'),
            ('ポップアップ', '東京駅'),
        ]

        print("\n=== HTMLコンテンツチェック ===")
        for check_name, check_string in checks:
            if check_string in content:
                print(f"✓ {check_name}: 見つかりました")
            else:
                print(f"✗ {check_name}: 見つかりませんでした")

        # CDNリンクの確認
        print("\n=== CDNリンクチェック ===")
        cdn_links = []
        lines = content.split('\n')
        for line in lines:
            if 'cdn.jsdelivr.net' in line or 'cdnjs.cloudflare.com' in line:
                cdn_links.append(line.strip())

        for link in cdn_links:
            print(f"CDN: {link}")

        # HTMLファイルの先頭部分を表示
        print("\n=== HTML先頭部分 ===")
        print(content[:800] + "..." if len(content) > 800 else content)

    return file_path

if __name__ == "__main__":
    try:
        html_file = create_test_map()
        print(f"\n生成されたHTMLファイル: {html_file}")
        print("ブラウザでファイルを開いて地図が表示されるか確認してください。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
