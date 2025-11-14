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

import logging
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Windows環境でのUTF-8出力設定
if sys.platform == "win32":
    # PYTHONIOENCODINGが設定されていない場合、UTF-8を使用するよう設定
    if "PYTHONIOENCODING" not in os.environ:
        os.environ["PYTHONIOENCODING"] = "utf-8"

    # Windows コンソールのコードページをUTF-8に設定（実行時）
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    except Exception:
        # 設定に失敗しても続行
        pass

    # stdoutとstderrのエンコーディングを強制的にUTF-8に再設定
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
    except Exception:
        # エンコーディング設定に失敗した場合は続行
        pass


def setup_logging():
    """ログシステムをセットアップ"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "photogeoview.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
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
        "",
    ]

    for line in banner_lines:
        logger.info(line)
        print(line)  # コンソールにも表示


def check_environment():
    """環境をチェック"""
    logger = logging.getLogger(__name__)

    try:
        import folium  # noqa: F401
        import PIL  # noqa: F401
        import PySide6  # noqa: F401

        # PySide6 WebEngine初期化はQApplication初期化後に行う

        message = "✅ 必要な依存関係が確認されました"
        logger.info(message)
        print(message)
        return True
    except ImportError as e:
        error_msg = f"❌ 依存関係が不足しています: {e}"
        install_msg = "以下のコマンドで依存関係をインストールしてください (pyproject.toml を使用):"
        cmd_msg = "pip install ."

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
        from PySide6.QtWidgets import QApplication

        from photogeoview.integration.config_manager import ConfigManager
        from photogeoview.integration.controllers import AppController
        from photogeoview.integration.logging_system import LoggerSystem
        from photogeoview.integration.state_manager import StateManager
        from photogeoview.integration.ui.main_window import IntegratedMainWindow

        logger = logging.getLogger(__name__)

        qt_msg = "🔧 Qt アプリケーションを初期化中..."
        logger.info(qt_msg)
        print(qt_msg)

        # WebEngine/WSL対策（QApplication作成前に必要）
        try:
            from PySide6.QtCore import Qt

            # GPUが使えない環境（WSL/リモート等）での安定化
            os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
            os.environ.setdefault(
                "QTWEBENGINE_CHROMIUM_FLAGS",
                "--no-sandbox --disable-gpu --disable-gpu-compositing "
                "--disable-software-rasterizer --in-process-gpu",
            )
            os.environ.setdefault("QT_OPENGL", "software")

            QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
            print("✅ WebEngine用OpenGL設定完了")
        except Exception as e:
            print(f"⚠️  WebEngine用設定エラー: {e}")

        app = QApplication(sys.argv)
        app.setApplicationName("PhotoGeoView AI Integration")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("AI Development Team")

        # PySide6 WebEngine早期初期化（QApplication初期化後）
        try:
            from photogeoview.integration.utils.webengine_checker import (
                get_webengine_status,
                initialize_webengine_safe,
            )

            # WebEngineの状態をチェック
            status = get_webengine_status()
            if status["available"]:
                print("✅ PyQtWebEngine利用可能")

                # 初期化を実行
                success, message = initialize_webengine_safe()
                if success:
                    print("✅ PyQtWebEngine初期化完了")
                else:
                    print(f"⚠️  PyQtWebEngine初期化エラー: {message}")
            else:
                print("⚠️  PyQtWebEngineが利用できません")
                for error in status["error_messages"]:
                    print(f"   - {error}")

        except ImportError as e:
            print(f"⚠️  WebEngineチェッカーが利用できません: {e}")
        except Exception as e:
            print(f"⚠️  PyQtWebEngine初期化エラー: {e}")

        components_msg = "🎯 システムコンポーネントを初期化中..."
        logger.info(components_msg)
        print(components_msg)

        logger_system = LoggerSystem()
        config_manager = ConfigManager(logger_system=logger_system)
        state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

        controller_msg = "🎯 アプリケーションコントローラーを初期化中..."
        logger.info(controller_msg)
        print(controller_msg)

        controller = AppController(config_manager=config_manager, logger_system=logger_system)

        # メインウィンドウを作成・表示
        window_msg = "🖼️  メインウィンドウを表示中..."
        logger.info(window_msg)
        print(window_msg)

        main_window = IntegratedMainWindow(
            config_manager=config_manager,
            state_manager=state_manager,
            logger_system=logger_system,
        )

        show_msg = "📺 ウィンドウを表示します..."
        logger.info(show_msg)
        print(show_msg)

        # Windows対策: ウィンドウ属性を設定してから表示
        from PySide6.QtCore import Qt

        try:
            # ウィンドウを作成したことをアプリケーションに通知
            main_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
            main_window.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)

            print("DEBUG: About to call main_window.show()...")
            logger.info("DEBUG: About to call main_window.show()...")

            # Windowsでは先にactivateWindow()を呼ぶと安定する場合がある
            main_window.activateWindow()
            main_window.raise_()
            main_window.show()

            print("DEBUG: main_window.show() returned successfully")
            logger.info("DEBUG: main_window.show() returned successfully")
        except Exception as e:
            error_msg = f"❌ show()呼び出し中にエラー発生: {e}"
            print(error_msg)
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            raise

        shown_msg = "📺 ウィンドウが表示されました"
        logger.info(shown_msg)
        print(shown_msg)

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

        try:
            exit_code = app.exec()
            logger.info(f"アプリケーション正常終了 (exit code: {exit_code})")
            print(f"アプリケーション正常終了 (exit code: {exit_code})")
            sys.exit(exit_code)
        except Exception as e:
            logger.error(f"イベントループ中にエラー発生: {e}")
            print(f"❌ イベントループ中にエラー発生: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

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
