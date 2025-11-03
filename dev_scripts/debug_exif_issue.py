#!/usr/bin/env python3
"""
EXIF情報表示問題のデバッグスクリプト

このスクリプトは、EXIF情報が表示されない問題を特定するために作成されました。
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


def test_exif_extraction():
    """EXIF抽出機能をテスト"""
    print("\n🔍 EXIF抽出機能のテスト開始")

    # 設定とロガーを初期化
    config_manager = ConfigManager()
    logger_system = LoggerSystem()

    # 画像プロセッサーを初期化
    image_processor = CS4CodingImageProcessor(config_manager, logger_system)

    # テスト用の画像ファイルを探す
    test_dirs = [
        Path("demo_data"),
        Path("assets"),
        Path("examples"),
        Path("test-data"),
        Path(),
    ]

    image_extensions = [".jpg", ".jpeg", ".png", ".tiff", ".tif"]
    test_image = None

    for test_dir in test_dirs:
        if test_dir.exists():
            for ext in image_extensions:
                images = list(test_dir.glob(f"*{ext}"))
                if images:
                    test_image = images[0]
                    break
            if test_image:
                break

    if not test_image:
        print("❌ テスト用の画像ファイルが見つかりません")
        print("📁 以下のディレクトリを確認しました:")
        for test_dir in test_dirs:
            print(f"   - {test_dir}")
        return False

    print(f"📷 テスト画像: {test_image}")

    # EXIF情報を抽出
    try:
        exif_data = image_processor.extract_exif(test_image)

        if not exif_data:
            print("❌ EXIF情報が取得できませんでした")
            return False

        print(f"✅ EXIF情報を取得しました ({len(exif_data)}件)")

        # 主要なEXIF情報を表示
        important_keys = [
            "Camera Make",
            "Camera Model",
            "Date Taken",
            "Date Original",
            "F-Number",
            "Exposure Time",
            "ISO Speed",
            "Focal Length",
            "GPS Latitude",
            "GPS Longitude",
            "GPS Coordinates",
        ]

        print("\n📋 主要なEXIF情報:")
        for key in important_keys:
            if key in exif_data:
                print(f"   {key}: {exif_data[key]}")

        # GPS情報の確認
        has_gps = any(key.startswith("GPS") for key in exif_data.keys())
        if has_gps:
            print("✅ GPS情報が含まれています")
        else:
            print("⚠️ GPS情報が含まれていません")

        # 全EXIF情報を表示（デバッグ用）
        print(f"\n🔧 全EXIF情報 ({len(exif_data)}件):")
        for key, value in exif_data.items():
            print(f"   {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ EXIF抽出中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_library_availability():
    """必要なライブラリの可用性をテスト"""
    print("\n📚 ライブラリの可用性チェック")

    libraries = {
        "exifread": "EXIF情報読み取り",
        "PIL": "画像処理",
        "cv2": "OpenCV画像処理",
    }

    for lib_name, description in libraries.items():
        try:
            if lib_name == "exifread":
                import exifread
            elif lib_name == "PIL":
                from PIL import Image
            elif lib_name == "cv2":
                import cv2

            print(f"✅ {lib_name}: {description} - 利用可能")
        except ImportError:
            print(f"❌ {lib_name}: {description} - 利用不可")


def main():
    """メイン関数"""
    print("🚀 EXIF情報表示問題のデバッグを開始します")

    # ライブラリの可用性をチェック
    test_library_availability()

    # EXIF抽出機能をテスト
    success = test_exif_extraction()

    if success:
        print("\n✅ EXIF抽出機能は正常に動作しています")
        print("💡 問題はUI側の表示処理にある可能性があります")
    else:
        print("\n❌ EXIF抽出機能に問題があります")
        print("💡 ライブラリのインストールまたは画像ファイルを確認してください")


if __name__ == "__main__":
    main()
