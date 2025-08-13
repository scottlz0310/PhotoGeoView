#!/usr/bin/env python3
"""
最小限のテスト
"""

import sys
from pathlib import Path

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """インポートテスト"""
    try:
        print("1. 基本モジュールのインポート...")
        from integration.config_manager import ConfigManager
        from integration.logging_system import LoggerSystem
        print("✅ 基本モジュールOK")

        print("2. EXIFパネルのインポート...")
        from integration.ui.exif_panel import EXIFPanel
        print("✅ EXIFパネルOK")

        print("3. 設定の初期化...")
        config_manager = ConfigManager()
        logger_system = LoggerSystem()
        print("✅ 設定初期化OK")

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🚀 最小限のテストを開始します")

    if test_imports():
        print("✅ 全てのテストが成功しました")
    else:
        print("❌ テストに失敗しました")

if __name__ == "__main__":
    main()
