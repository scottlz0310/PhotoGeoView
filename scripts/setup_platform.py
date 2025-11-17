#!/usr/bin/env python3
"""
プラットフォーム固有のセットアップスクリプト
PhotoGeoView AI統合版 - マルチプラットフォーム対応
"""

import os
import platform
import sys
from pathlib import Path


def detect_platform():
    """現在のプラットフォームを検出"""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def setup_linux():
    """Linux固有のセットアップ"""
    print("🐧 Linux環境のセットアップ中...")

    # 必要なシステムパッケージの確認
    required_packages = [
        "libxkbcommon-x11-0",
        "libxcb-icccm4",
        "libxcb-image0",
        "libgl1-mesa-glx",
        "libegl1-mesa",
    ]

    print("必要なシステムパッケージ:")
    for package in required_packages:
        print(f"  - {package}")

    # 仮想ディスプレイの設定
    os.environ["QT_QPA_PLATFORM"] = "xcb"  # デフォルトはxcb
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"

    print("✅ Linux環境セットアップ完了")


def setup_macos():
    """macOS固有のセットアップ"""
    print("🍎 macOS環境のセットアップ中...")

    # Qt6のパスを設定（PySide6）
    try:
        import PySide6

        qt_plugin_path = Path(PySide6.__file__).parent / "Qt6" / "plugins"
        if qt_plugin_path.exists():
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(qt_plugin_path)
            print(f"Qt plugin path: {qt_plugin_path}")
    except ImportError:
        print("⚠️ PySide6がインストールされていません")

    # macOS固有の環境変数
    os.environ["QT_MAC_WANTS_LAYER"] = "1"

    # Homebrewのパスを確認
    homebrew_paths = ["/opt/homebrew/bin", "/usr/local/bin"]
    for path in homebrew_paths:
        if Path(path).exists() and path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{path}:{os.environ.get('PATH', '')}"

    print("✅ macOS環境セットアップ完了")


def setup_windows():
    """Windows固有のセットアップ"""
    print("🪟 Windows環境のセットアップ中...")

    # Windows固有の環境変数設定
    os.environ["QT_QPA_PLATFORM"] = "windows"

    # Visual C++ Redistributableの確認
    try:
        import ctypes

        # 基本的なWindows DLLの確認
        ctypes.windll.kernel32
        print("✅ Windows DLL確認完了")
    except Exception as e:
        print(f"⚠️ Windows DLL確認エラー: {e}")

    # パスの区切り文字を正規化
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"].replace("/", "\\")

    print("✅ Windows環境セットアップ完了")


def verify_qt_installation():
    """Qt/PySide6インストールの確認"""
    print("🔍 Qt/PySide6インストール確認中...")

    try:
        import PySide6
        from PySide6.QtCore import __version__ as PYSIDE_VERSION
        from PySide6.QtCore import __version_info__ as _
        from PySide6.QtWidgets import QApplication

        print(f"✅ PySide6 version: {PYSIDE_VERSION}")

        # QApplicationの作成テスト
        app = QApplication([])
        print("✅ QApplication作成成功")
        app.quit()

        return True

    except ImportError as e:
        print(f"❌ PySide6インポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ Qt初期化エラー: {e}")
        return False


def setup_development_environment():
    """開発環境の追加セットアップ"""
    print("🛠️ 開発環境セットアップ中...")

    # ログディレクトリの作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    print(f"✅ ログディレクトリ作成: {log_dir}")

    # キャッシュディレクトリの作成
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    print(f"✅ キャッシュディレクトリ作成: {cache_dir}")

    # 状態ディレクトリの作成
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    print(f"✅ 状態ディレクトリ作成: {state_dir}")

    # レポートディレクトリの作成
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    print(f"✅ レポートディレクトリ作成: {reports_dir}")


def main():
    """メイン実行関数"""
    print("🚀 PhotoGeoView プラットフォーム固有セットアップ")
    print("=" * 50)

    # プラットフォーム検出
    try:
        current_platform = detect_platform()
        print(f"🔍 検出されたプラットフォーム: {current_platform}")
        print(f"🔍 詳細情報: {platform.platform()}")
        print(f"🔍 Python version: {sys.version}")
        print()

        # プラットフォーム固有のセットアップ
        if current_platform == "linux":
            setup_linux()
        elif current_platform == "macos":
            setup_macos()
        elif current_platform == "windows":
            setup_windows()

        print()

        # Qt/PySide6の確認
        qt_ok = verify_qt_installation()

        print()

        # 開発環境セットアップ
        setup_development_environment()

        print()
        print("=" * 50)
        if qt_ok:
            print("✅ プラットフォームセットアップ完了！")
            print("🎉 PhotoGeoViewを起動する準備ができました")
        else:
            print("⚠️ プラットフォームセットアップ完了（Qt/PySide6に問題あり）")
            print("📝 PySide6の再インストールを検討してください:")
            print("   pip install --upgrade PySide6")

        return 0 if qt_ok else 1

    except Exception as e:
        print(f"❌ セットアップエラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
