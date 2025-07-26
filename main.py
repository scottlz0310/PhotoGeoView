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
    logger = logging.getLogger(__name__)

    banner_lines = [
        "=" * 60,
        "🌟 PhotoGeoView AI統合版",
        "=" * 60,
        "🤖 AI協調開発システム:",
        "  📷 GitHub Copilot (CS4Coding): EXIF解析・地図表示",
        "  🎨 Cursor (CursorBLD): UI/UX・テーマシステム",
        "  ⚡ Kiro: 統合制御・パフォーマンス最適化",
        "=" * 60,
        "🚀 アプリケーションを起動中...",
        ""
    ]

    for line in banner_lines:
        logger.info(line)
        print(line)  # コンソールにも表示

def check_environment():
    """環境をチェック"""
    logger = logging.getLogger(__name__)

    try:
        import PyQt6  # noqa: F401
        import PIL  # noqa: F401
        import folium  # noqa: F401

        message = "✅ 必要な依存関係が確認されました"
        logger.info(message)
        print(message)
        return True
    except ImportError as e:
        error_msg = f"❌ 依存関係が不足しています: {e}"
        install_msg = "以下のコマンドで依存関係をインストールしてください:"
        cmd_msg = "pip install -r requirements.txt"

        logger.error(error_msg)
        logger.info(install_msg)
        logger.info(cmd_msg)

        print(error_msg)
        print(install_msg)
        print(cmd_msg)
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

        logger = logging.getLogger(__name__)

        qt_msg = "🔧 Qt アプリケーションを初期化中..."
        logger.info(qt_msg)
        print(qt_msg)

        app = QApplication(sys.argv)
        app.setApplicationName("PhotoGeoView AI Integration")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("AI Development Team")

        components_msg = "🎯 システムコンポーネントを初期化中..."
        logger.info(components_msg)
        print(components_msg)

        logger_system = LoggerSystem()
        config_manager = ConfigManager(logger_system=logger_system)
        state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

        controller_msg = "🎯 アプリケーションコントローラーを初期化中..."
        logger.info(controller_msg)
        print(controller_msg)

        controller = AppController(config_manager=config_manager, logger_system=logger_system)  # noqa: F841

        # メインウィンドウを作成・表示
        window_msg = "🖼️  メインウィンドウを表示中..."
        logger.info(window_msg)
        print(window_msg)

        main_window = IntegratedMainWindow(
            config_manager=config_manager,
            state_manager=state_manager,
            logger_system=logger_system
        )
        main_window.show()

        success_msg = "✨ PhotoGeoView AI統合版が正常に起動しました！"
        log_msg = "📝 ログファイル: logs/photogeoview.log"
        enjoy_msg = "🎨 テーマ切り替え、画像表示、地図機能をお楽しみください"

        logger.info(success_msg)
        logger.info(log_msg)
        logger.info(enjoy_msg)

        print(success_msg)
        print(log_msg)
        print(enjoy_msg)
        print()

        # Qtイベントループを開始
        run_msg = "⏳ アプリケーション実行中... (終了するにはウィンドウを閉じるかCtrl+Cを押してください)"
        logger.info(run_msg)
        print(run_msg)

        sys.exit(app.exec())

    except ImportError as e:
        logger = logging.getLogger(__name__)
        import_error = f"❌ モジュールのインポートエラー: {e}"
        structure_msg = "📁 プロジェクト構造を確認してください"
        deps_msg = "🔧 依存関係が正しくインストールされているかチェックしてください"

        logger.error(import_error)
        logger.info(structure_msg)
        logger.info(deps_msg)

        print(import_error)
        print(structure_msg)
        print(deps_msg)
        sys.exit(1)

    except Exception as e:
        logger = logging.getLogger(__name__)
        error_msg = f"❌ 予期しないエラーが発生しました: {e}"
        detail_msg = "📋 詳細はログファイルを確認してください: logs/photogeoview.log"

        logger.error(f"アプリケーション起動エラー: {e}")
        logger.info(detail_msg)

        print(error_msg)
        print(detail_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
