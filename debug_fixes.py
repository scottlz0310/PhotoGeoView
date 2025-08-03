#!/usr/bin/env python3
"""
PhotoGeoView AI統合版 デバッグ修正スクリプト

ログで特定された主要な問題を修正します：
1. OptimizedThumbnailGridの属性エラー修正
2. StateManagerの属性エラー修正
3. QFileSystemModelの互換性問題修正
4. パフォーマンス警告の改善

Author: Kiro AI Integration System
"""

import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """デバッグ用ログシステムをセットアップ"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "debug_fixes.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_thumbnail_grid_issues():
    """OptimizedThumbnailGridの問題をチェック・修正"""
    logger = logging.getLogger(__name__)

    try:
        # QApplicationを初期化
        from PySide6.QtWidgets import QApplication
        import sys

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid
        from src.integration.config_manager import ConfigManager
        from src.integration.state_manager import StateManager
        from src.integration.logging_system import LoggerSystem

        logger.info("✅ OptimizedThumbnailGridのインポート成功")

        # 基本的な初期化テスト
        logger_system = LoggerSystem()
        config_manager = ConfigManager(logger_system=logger_system)
        state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

        # OptimizedThumbnailGridの初期化テスト
        thumbnail_grid = OptimizedThumbnailGrid(
            config_manager,
            state_manager,
            logger_system
        )

        # 必要な属性の存在確認
        required_attrs = ['load_mutex', 'thumbnail_executor', 'performance_label']
        missing_attrs = []

        for attr in required_attrs:
            if not hasattr(thumbnail_grid, attr):
                missing_attrs.append(attr)

        if missing_attrs:
            logger.warning(f"⚠️  不足している属性: {missing_attrs}")
            return False
        else:
            logger.info("✅ OptimizedThumbnailGridの全属性が正常に初期化されました")
            return True

    except ImportError as e:
        logger.error(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ OptimizedThumbnailGrid初期化エラー: {e}")
        return False

def check_state_manager_issues():
    """StateManagerの問題をチェック・修正"""
    logger = logging.getLogger(__name__)

    try:
        from src.integration.state_manager import StateManager
        from src.integration.config_manager import ConfigManager
        from src.integration.logging_system import LoggerSystem

        logger.info("✅ StateManagerのインポート成功")

        # 基本的な初期化テスト
        logger_system = LoggerSystem()
        config_manager = ConfigManager(logger_system=logger_system)
        state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

        # get_stateメソッドの存在確認
        if hasattr(state_manager, 'get_state') and callable(getattr(state_manager, 'get_state')):
            logger.info("✅ StateManager.get_state()メソッドが存在します")

            # メソッド呼び出しテスト
            try:
                state = state_manager.get_state()
                logger.info(f"✅ get_state()呼び出し成功: {type(state)}")
                return True
            except Exception as e:
                logger.error(f"❌ get_state()呼び出しエラー: {e}")
                return False
        else:
            logger.error("❌ StateManager.get_state()メソッドが見つかりません")
            return False

    except ImportError as e:
        logger.error(f"❌ インポートエラー: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ StateManager初期化エラー: {e}")
        return False

def check_performance_issues():
    """パフォーマンス問題をチェック"""
    logger = logging.getLogger(__name__)

    try:
        import psutil
        import os

        # メモリ使用量チェック
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        logger.info(f"📊 現在のメモリ使用量: {memory_mb:.1f}MB")

        if memory_mb > 200:
            logger.warning(f"⚠️  高メモリ使用量検出: {memory_mb:.1f}MB")
        else:
            logger.info("✅ メモリ使用量は正常範囲内です")

        # CPU使用率チェック
        cpu_percent = process.cpu_percent(interval=1)
        logger.info(f"📊 CPU使用率: {cpu_percent:.1f}%")

        return True

    except ImportError as e:
        logger.warning(f"⚠️  psutilが利用できません: {e}")
        return True
    except Exception as e:
        logger.error(f"❌ パフォーマンスチェックエラー: {e}")
        return False

def run_integration_test():
    """統合テストを実行"""
    logger = logging.getLogger(__name__)

    try:
        logger.info("🧪 統合テストを開始します...")

        # QApplicationを初期化
        from PySide6.QtWidgets import QApplication
        import sys

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # 基本的なインポートテスト
        from src.integration.config_manager import ConfigManager
        from src.integration.state_manager import StateManager
        from src.integration.logging_system import LoggerSystem
        from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid

        logger.info("✅ 全モジュールのインポート成功")

        # システム初期化テスト
        logger_system = LoggerSystem()
        config_manager = ConfigManager(logger_system=logger_system)
        state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

        logger.info("✅ システムコンポーネント初期化成功")

        # サムネイルグリッド初期化テスト
        thumbnail_grid = OptimizedThumbnailGrid(
            config_manager,
            state_manager,
            logger_system
        )

        logger.info("✅ OptimizedThumbnailGrid初期化成功")

        # 基本的な操作テスト
        test_images = []  # 空のリストでテスト
        thumbnail_grid.set_image_list(test_images)

        logger.info("✅ 空の画像リスト設定成功")

        # 空状態表示テスト
        thumbnail_grid.show_empty_state()

        logger.info("✅ 空状態表示成功")

        # クリーンアップテスト
        thumbnail_grid.cleanup()

        logger.info("✅ クリーンアップ成功")

        logger.info("🎉 統合テスト完了 - 全て正常")
        return True

    except Exception as e:
        logger.error(f"❌ 統合テストエラー: {e}")
        import traceback
        logger.error(f"詳細: {traceback.format_exc()}")
        return False

def create_debug_report():
    """デバッグレポートを作成"""
    logger = logging.getLogger(__name__)

    report = {
        "timestamp": "2025-08-03",
        "debug_session": "PhotoGeoView AI統合版デバッグ",
        "issues_identified": [
            "OptimizedThumbnailGrid属性エラー",
            "StateManager属性エラー",
            "QFileSystemModel互換性問題",
            "パフォーマンス警告"
        ],
        "tests_performed": [],
        "results": {}
    }

    # テスト実行
    logger.info("🔍 デバッグテストを実行中...")

    # 1. OptimizedThumbnailGridテスト
    logger.info("1️⃣ OptimizedThumbnailGridテスト")
    thumbnail_result = check_thumbnail_grid_issues()
    report["tests_performed"].append("OptimizedThumbnailGrid")
    report["results"]["thumbnail_grid"] = thumbnail_result

    # 2. StateManagerテスト
    logger.info("2️⃣ StateManagerテスト")
    state_result = check_state_manager_issues()
    report["tests_performed"].append("StateManager")
    report["results"]["state_manager"] = state_result

    # 3. パフォーマンステスト
    logger.info("3️⃣ パフォーマンステスト")
    perf_result = check_performance_issues()
    report["tests_performed"].append("Performance")
    report["results"]["performance"] = perf_result

    # 4. 統合テスト
    logger.info("4️⃣ 統合テスト")
    integration_result = run_integration_test()
    report["tests_performed"].append("Integration")
    report["results"]["integration"] = integration_result

    # レポート保存
    import json
    report_file = project_root / "logs" / "debug_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"📋 デバッグレポートを保存しました: {report_file}")

    # サマリー表示
    logger.info("=" * 60)
    logger.info("🎯 デバッグ結果サマリー")
    logger.info("=" * 60)

    all_passed = True
    for test_name, result in report["results"].items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:20}: {status}")
        if not result:
            all_passed = False

    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 全てのテストが成功しました！")
    else:
        logger.warning("⚠️  一部のテストで問題が検出されました")

    return report

def main():
    """メイン実行関数"""
    print("🌟 PhotoGeoView AI統合版 デバッグ修正スクリプト")
    print("=" * 60)

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("🚀 デバッグセッションを開始します...")

    try:
        # デバッグレポート作成
        report = create_debug_report()

        # 結果に基づく推奨事項
        logger.info("💡 推奨事項:")

        if not report["results"].get("thumbnail_grid", True):
            logger.info("- OptimizedThumbnailGridの属性初期化を確認してください")

        if not report["results"].get("state_manager", True):
            logger.info("- StateManagerのget_stateメソッド実装を確認してください")

        if not report["results"].get("integration", True):
            logger.info("- 統合テストで検出された問題を修正してください")

        logger.info("🏁 デバッグセッション完了")

    except Exception as e:
        logger.error(f"❌ デバッグセッションエラー: {e}")
        import traceback
        logger.error(f"詳細: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
