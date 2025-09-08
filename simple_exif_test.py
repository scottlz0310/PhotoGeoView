#!/usr/bin/env python3
"""
シンプルなEXIF表示テスト
"""

import sys
from pathlib import Path

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_exif_extraction():
    """EXIF抽出のみをテスト"""
    try:
        from integration.config_manager import ConfigManager
        from integration.logging_system import LoggerSystem
        from integration.image_processor import CS4CodingImageProcessor

        print("✅ モジュールのインポートに成功しました")

        # 設定とロガーを初期化
        config_manager = ConfigManager()
        logger_system = LoggerSystem()

        # 画像プロセッサーを初期化
        image_processor = CS4CodingImageProcessor(config_manager, logger_system)

        # テスト用の画像を探す
        test_image = Path("/home/hiro/Samples/taiwan-jiufen.jpg")
        if not test_image.exists():
            test_image = Path("demo_data/test_image.jpg")

        if not test_image.exists():
            print("❌ テスト画像が見つかりません")
            return False

        print(f"📷 テスト画像: {test_image}")

        # EXIF情報を抽出
        exif_data = image_processor.extract_exif(test_image)

        if not exif_data:
            print("❌ EXIF情報が取得できませんでした")
            return False

        print(f"✅ EXIF情報を取得しました ({len(exif_data)}件)")

        # 主要な情報を表示
        important_keys = [
            "Camera Make", "Camera Model", "Date Taken", "Date Original",
            "F-Number", "Exposure Time", "ISO Speed", "Focal Length",
            "GPS Latitude", "GPS Longitude", "GPS Coordinates"
        ]

        print("\n📋 主要なEXIF情報:")
        for key in important_keys:
            if key in exif_data:
                print(f"   {key}: {exif_data[key]}")

        # GPS情報の確認
        has_gps = any(key.startswith("GPS") for key in exif_data.keys())
        if has_gps:
            print("✅ GPS情報が含まれています")
            gps_keys = [key for key in exif_data.keys() if key.startswith("GPS")]
            print(f"   GPS関連キー: {gps_keys}")
        else:
            print("⚠️ GPS情報が含まれていません")

        return True

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚀 シンプルなEXIF表示テストを開始します")

    success = test_exif_extraction()

    if success:
        print("\n✅ EXIF抽出機能は正常に動作しています")
        print("💡 問題はUI表示部分にある可能性があります")
    else:
        print("\n❌ EXIF抽出機能に問題があります")

if __name__ == "__main__":
    main()
