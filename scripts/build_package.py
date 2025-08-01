#!/usr/bin/env python3
"""
プラットフォーム固有のパッケージ作成スクリプト
PhotoGeoView AI統合版 - マルチプラットフォーム対応
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import json


def get_platform_info():
    """プラットフォーム情報を取得"""
    system = platform.system().lower()
    arch = platform.machine().lower()

    platform_map = {
        'linux': 'Linux',
        'darwin': 'macOS',
        'windows': 'Windows'
    }

    arch_map = {
        'x86_64': 'x64',
        'amd64': 'x64',
        'arm64': 'arm64',
        'aarch64': 'arm64'
    }

    return {
        'system': platform_map.get(system, system),
        'arch': arch_map.get(arch, arch),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}"
    }


def create_pyinstaller_spec():
    """PyInstaller用のspecファイルを作成"""
    platform_info = get_platform_info()

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import

# プラットフォーム固有の設定
platform_system = "{platform_info['system']}"

block_cipher = None

# データファイルの設定
datas = [
    ('assets', 'assets'),
    ('config', 'config'),
    ('src/integration/ui/themes', 'src/integration/ui/themes'),
]

# 隠れたインポートの設定
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PIL',
    'PIL.Image',
    'PIL.ExifTags',
    'folium',
    'requests',
    'numpy',
    'src.integration.core.app_controller',
    'src.integration.ui.main_window',
    'src.integration.ui.exif_panel',
    'src.integration.ui.thumbnail_grid',
    'src.integration.ui.folder_navigator',
    'src.integration.ui.theme_manager',
    'src.copilot.image_processor',
    'src.cursor.ui_components',
    'src.kiro.performance_monitor',
]

# プラットフォーム固有の除外設定
excludes = []
if platform_system == "Linux":
    excludes.extend(['tkinter', '_tkinter'])
elif platform_system == "Windows":
    excludes.extend(['readline', 'termios'])
elif platform_system == "macOS":
    excludes.extend(['readline'])

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# プラットフォーム固有の実行ファイル設定
if platform_system == "Windows":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='PhotoGeoView',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
    )
elif platform_system == "macOS":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='PhotoGeoView',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='PhotoGeoView',
    )

    app = BUNDLE(
        coll,
        name='PhotoGeoView.app',
        icon='assets/icon.icns' if Path('assets/icon.icns').exists() else None,
        bundle_identifier='com.photogeoview.app',
        info_plist={{
            'CFBundleDisplayName': 'PhotoGeoView',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        }},
    )
else:  # Linux
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='PhotoGeoView',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
'''

    with open('PhotoGeoView.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("✅ PyInstaller specファイル作成完了")


def build_with_pyinstaller():
    """PyInstallerでビルド実行"""
    print("🔨 PyInstallerでビルド中...")

    try:
        # specファイルを使用してビルド
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'PhotoGeoView.spec'
        ], check=True, capture_output=True, text=True)

        print("✅ PyInstallerビルド完了")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstallerビルドエラー: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def create_linux_appimage():
    """Linux用AppImage作成"""
    print("🐧 Linux AppImage作成中...")

    # AppDirの構造を作成
    appdir = Path("dist/PhotoGeoView.AppDir")
    appdir.mkdir(parents=True, exist_ok=True)

    # 必要なディレクトリ構造
    (appdir / "usr" / "bin").mkdir(parents=True, exist_ok=True)
    (appdir / "usr" / "share" / "applications").mkdir(parents=True, exist_ok=True)
    (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True, exist_ok=True)

    # 実行ファイルをコピー
    if Path("dist/PhotoGeoView").exists():
        shutil.copy2("dist/PhotoGeoView", appdir / "usr" / "bin" / "PhotoGeoView")
        os.chmod(appdir / "usr" / "bin" / "PhotoGeoView", 0o755)

    # .desktopファイル作成
    desktop_content = """[Desktop Entry]
Type=Application
Name=PhotoGeoView
Comment=AI-powered photo geolocation viewer
Exec=PhotoGeoView
Icon=photogeoview
Categories=Graphics;Photography;
Terminal=false
"""

    with open(appdir / "PhotoGeoView.desktop", 'w') as f:
        f.write(desktop_content)

    with open(appdir / "usr" / "share" / "applications" / "PhotoGeoView.desktop", 'w') as f:
        f.write(desktop_content)

    # AppRunスクリプト作成
    apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/PhotoGeoView" "$@"
"""

    with open(appdir / "AppRun", 'w') as f:
        f.write(apprun_content)
    os.chmod(appdir / "AppRun", 0o755)

    print("✅ Linux AppImage構造作成完了")


def create_windows_installer():
    """Windows用インストーラー作成（NSIS使用想定）"""
    print("🪟 Windows用配布パッケージ準備中...")

    # 配布用ディレクトリ作成
    dist_dir = Path("dist/PhotoGeoView-Windows")
    dist_dir.mkdir(parents=True, exist_ok=True)

    # 実行ファイルをコピー
    if Path("dist/PhotoGeoView.exe").exists():
        shutil.copy2("dist/PhotoGeoView.exe", dist_dir / "PhotoGeoView.exe")

    # 必要なファイルをコピー
    files_to_copy = ["README.md", "LICENSE"]
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, dist_dir / file)

    # バッチファイル作成
    batch_content = """@echo off
echo Starting PhotoGeoView...
PhotoGeoView.exe
pause
"""

    with open(dist_dir / "run.bat", 'w') as f:
        f.write(batch_content)

    print("✅ Windows配布パッケージ準備完了")


def create_macos_dmg():
    """macOS用DMG作成"""
    print("🍎 macOS用配布パッケージ準備中...")

    # 配布用ディレクトリ作成
    dist_dir = Path("dist/PhotoGeoView-macOS")
    dist_dir.mkdir(parents=True, exist_ok=True)

    # .appファイルをコピー
    app_path = Path("dist/PhotoGeoView.app")
    if app_path.exists():
        shutil.copytree(app_path, dist_dir / "PhotoGeoView.app", dirs_exist_ok=True)

    # 必要なファイルをコピー
    files_to_copy = ["README.md", "LICENSE"]
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, dist_dir / file)

    print("✅ macOS配布パッケージ準備完了")


def create_build_info():
    """ビルド情報ファイル作成"""
    platform_info = get_platform_info()

    build_info = {
        "build_date": subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S'], text=True).strip(),
        "platform": platform_info,
        "git_commit": subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()[:8],
        "git_branch": subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip(),
        "python_version": sys.version,
        "build_system": "PyInstaller"
    }

    with open("dist/build_info.json", 'w', encoding='utf-8') as f:
        json.dump(build_info, f, indent=2, ensure_ascii=False)

    print("✅ ビルド情報ファイル作成完了")


def main():
    """メイン実行関数"""
    print("📦 PhotoGeoView パッケージ作成")
    print("=" * 50)

    platform_info = get_platform_info()
    print(f"🔍 プラットフォーム: {platform_info['system']} ({platform_info['arch']})")
    print(f"🔍 Python: {platform_info['python_version']}")
    print()

    try:
        # PyInstallerの確認
        try:
            import PyInstaller
            print(f"✅ PyInstaller version: {PyInstaller.__version__}")
        except ImportError:
            print("❌ PyInstallerがインストールされていません")
            print("pip install pyinstaller でインストールしてください")
            return 1

        # distディレクトリのクリーンアップ
        if Path("dist").exists():
            shutil.rmtree("dist")
        Path("dist").mkdir()

        # specファイル作成
        create_pyinstaller_spec()

        # PyInstallerでビルド
        if not build_with_pyinstaller():
            return 1

        # プラットフォーム固有のパッケージング
        if platform_info['system'] == 'Linux':
            create_linux_appimage()
        elif platform_info['system'] == 'Windows':
            create_windows_installer()
        elif platform_info['system'] == 'macOS':
            create_macos_dmg()

        # ビルド情報作成
        create_build_info()

        print()
        print("=" * 50)
        print("✅ パッケージ作成完了！")
        print(f"📁 出力ディレクトリ: dist/")

        # 作成されたファイルを表示
        print("📋 作成されたファイル:")
        for item in Path("dist").rglob("*"):
            if item.is_file():
                size = item.stat().st_size / (1024 * 1024)  # MB
                print(f"  - {item.relative_to('dist')} ({size:.1f} MB)")

        return 0

    except Exception as e:
        print(f"❌ パッケージ作成エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
