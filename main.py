#!/usr/bin/env python3
"""
PhotoGeoView AI統合版メインアプリケーション起動スクリプト

このアプリケーションは3つのAIエージェントによる協調開発の成果物です：
- GitHub Copilot (CS4Coding): コア機能実装
- Cursor (CursorBLD): UI/UX設計とテーマシステム
- Kiro: 統合・品質管理とパフォーマンス最適化

使用方法:
    python main.py

Author: AI Integration Team (Copilot + Cursor + Kiro)
"""

import sys
from pathlib import Path
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """ログシステムをセットアップ"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "photogeoview.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def print_startup_banner():
    """起動バナーを表示"""
    print("=" * 60)
    print("🌟 PhotoGeoView AI統合版")
    print("=" * 60)
    print("🤖 AI協調開発システム:")
    print("  📷 GitHub Copilot (CS4Coding): EXIF解析・地図表示")
    print("  🎨 Cursor (CursorBLD): UI/UX・テーマシステム")
    print("  ⚡ Kiro: 統合制御・パフォーマンス最適化")
    print("=" * 60)
    print("🚀 アプリケーションを起動中...")
    print()

def check_environment():
    """環境をチェック"""
    try:
        import PyQt6  # noqa: F401
        import PIL  # noqa: F401
        import folium  # noqa: F401
        print("✅ 必要な依存関係が確認されました")
        return True
    except ImportError as e:
        print(f"❌ 依存関係が不足しています: {e}")
        print("以下のコマンドで依存関係をインストールしてください:")
        print("pip install -r requirements.txt")
        return False

def main():
    """メインアプリケーション起動"""
    try:
        print_startup_banner()
        setup_logging()

        # 環境チェック
        if not check_environment():
            sys.exit(1)

        # アプリケーションコントローラーをインポート・起動
        from src.integration.controllers import AppController
        from src.integration.ui.main_window import IntegratedMainWindow
        from src.integration.config_manager import ConfigManager
        from src.integration.state_manager import StateManager
        from src.integration.logging_system import LoggerSystem
        from PyQt6.QtWidgets import QApplication

        print("🔧 Qt アプリケーションを初期化中...")
        app = QApplication(sys.argv)
        app.setApplicationName("PhotoGeoView AI Integration")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("AI Development Team")

        print("🎯 システムコンポーネントを初期化中...")
        logger_system = LoggerSystem()
        config_manager = ConfigManager(logger_system=logger_system)
        state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

        print("🎯 アプリケーションコントローラーを初期化中...")
        controller = AppController(config_manager=config_manager, logger_system=logger_system)  # noqa: F841

        # メインウィンドウを作成・表示
        print("🖼️  メインウィンドウを表示中...")
        main_window = IntegratedMainWindow(
            config_manager=config_manager,
            state_manager=state_manager,
            logger_system=logger_system
        )
        main_window.show()
        print("✨ PhotoGeoView AI統合版が正常に起動しました！")
        print("📝 ログファイル: logs/photogeoview.log")
        print("🎨 テーマ切り替え、画像表示、地図機能をお楽しみください")
        print()

        # Qtイベントループを開始
        print("⏳ アプリケーション実行中... (終了するにはウィンドウを閉じるかCtrl+Cを押してください)")
        sys.exit(app.exec())

    except ImportError as e:
        print(f"❌ モジュールのインポートエラー: {e}")
        print("📁 プロジェクト構造を確認してください")
        print("🔧 依存関係が正しくインストールされているかチェックしてください")
        sys.exit(1)

    except Exception as e:
        logging.error(f"アプリケーション起動エラー: {e}")
        print(f"❌ 予期しないエラーが発生しました: {e}")
        print("📋 詳細はログファイルを確認してください: logs/photogeoview.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
