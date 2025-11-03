#!/usr/bin/env python3
"""
詳細なEXIF情報表示問題のデバッグスクリプト

複数の画像ファイルをテストして、EXIF情報の詳細を確認します。
"""

import sys
from pathlib import Path

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from integration.config_manager import ConfigManager
    from integration.image_processor import CS4CodingImageProcessor
    from integration.logging_system import LoggerSystem

    print("✅ モジュールのインポートに成功しました")
except ImportError as e:
    print(f"❌ モジュールのインポートに失敗しました: {e}")
    sys.exit(1)


def test_multiple_images():
    """複数の画像でEXIF抽出をテスト"""
    print("\n🔍 複数画像でのEXIF抽出テスト開始")

    # 設定とロガーを初期化
    config_manager = ConfigManager()
    logger_system = LoggerSystem()

    # 画像プロセッサーを初期化
    image_processor = CS4CodingImageProcessor(config_manager, logger_system)

    # テスト用の画像ファイルを探す
    test_dirs = [Path("demo_data"), Path("assets"), Path("examples")]
    image_extensions = [".jpg", ".jpeg", ".png", ".tiff", ".tif"]
    test_images = []

    for test_dir in test_dirs:
        if test_dir.exists():
            for ext in image_extensions:
                images = list(test_dir.glob(f"*{ext}"))
                test_images.extend(images)

    if not test_images:
        print("❌ テスト用の画像ファイルが見つかりません")
        return False

    print(f"📷 見つかった画像ファイル: {len(test_images)}個")

    # 各画像をテスト
    for i, test_image in enumerate(test_images[:5]):  # 最大5つの画像をテスト
        print(f"\n--- 画像 {i + 1}: {test_image.name} ---")

        try:
            exif_data = image_processor.extract_exif(test_image)

            if not exif_data:
                print("❌ EXIF情報が取得できませんでした")
                continue

            print(f"✅ EXIF情報を取得しました ({len(exif_data)}件)")

            # カメラ情報
            camera_info = {}
            for key in ["Camera Make", "Camera Model", "Lens Model"]:
                if key in exif_data:
                    camera_info[key] = exif_data[key]

            if camera_info:
                print("📸 カメラ情報:")
                for key, value in camera_info.items():
                    print(f"   {key}: {value}")

            # 撮影設定
            settings_info = {}
            for key in ["F-Number", "Exposure Time", "ISO Speed", "Focal Length"]:
                if key in exif_data:
                    settings_info[key] = exif_data[key]

            if settings_info:
                print("⚙️ 撮影設定:")
                for key, value in settings_info.items():
                    print(f"   {key}: {value}")

            # GPS情報
            gps_info = {}
            for key in exif_data.keys():
                if key.startswith("GPS"):
                    gps_info[key] = exif_data[key]

            if gps_info:
                print("📍 GPS情報:")
                for key, value in gps_info.items():
                    print(f"   {key}: {value}")
            else:
                print("⚠️ GPS情報なし")

            # 日時情報
            date_info = {}
            for key in ["Date Taken", "Date Original"]:
                if key in exif_data:
                    date_info[key] = exif_data[key]

            if date_info:
                print("🕒 日時情報:")
                for key, value in date_info.items():
                    print(f"   {key}: {value}")

        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback

            traceback.print_exc()

    return True


def test_raw_exif_extraction():
    """生のEXIF抽出をテスト"""
    print("\n🔧 生のEXIF抽出テスト")

    try:
        import exifread
        from PIL import Image

        test_image = Path("demo_data/sample_image_1.jpg")
        if not test_image.exists():
            test_image = Path("demo_data/test_image.jpg")

        if not test_image.exists():
            print("❌ テスト画像が見つかりません")
            return

        print(f"📷 テスト画像: {test_image}")

        # exifreadでの抽出
        print("\n--- exifreadでの抽出 ---")
        try:
            with open(test_image, "rb") as f:
                tags = exifread.process_file(f, details=False)

                if tags:
                    print(f"✅ exifreadで{len(tags)}個のタグを取得")
                    for tag_key, tag_value in list(tags.items())[
                        :10
                    ]:  # 最初の10個を表示
                        print(f"   {tag_key}: {tag_value}")
                else:
                    print("❌ exifreadでタグが取得できませんでした")
        except Exception as e:
            print(f"❌ exifreadエラー: {e}")

        # PILでの抽出
        print("\n--- PILでの抽出 ---")
        try:
            with Image.open(test_image) as img:
                if hasattr(img, "_getexif"):
                    exif_dict = img._getexif()
                    if exif_dict:
                        print(f"✅ PILで{len(exif_dict)}個のタグを取得")
                        from PIL.ExifTags import TAGS

                        for tag_id, value in list(exif_dict.items())[
                            :10
                        ]:  # 最初の10個を表示
                            tag_name = TAGS.get(tag_id, f"Tag_{tag_id}")
                            print(f"   {tag_name}: {value}")
                    else:
                        print("❌ PILでEXIF辞書が取得できませんでした")
                else:
                    print("❌ PILでEXIF情報が利用できません")
        except Exception as e:
            print(f"❌ PILエラー: {e}")

    except ImportError as e:
        print(f"❌ ライブラリのインポートエラー: {e}")


def main():
    """メイン関数"""
    print("🚀 詳細なEXIF情報表示問題のデバッグを開始します")

    # 複数画像でのテスト
    test_multiple_images()

    # 生のEXIF抽出テスト
    test_raw_exif_extraction()


if __name__ == "__main__":
    main()
