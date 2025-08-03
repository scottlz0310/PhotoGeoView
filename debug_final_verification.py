#!/usr/bin/env python3
"""
PhotoGeoView AI統合版 最終デバッグ検証スクリプト

全ての修正が正常に適用され、アプリケーションが安定して動作することを検証します。

検証項目:
1. フォールバック実装の動作確認
2. エラーログの減少確認
3. 主要機能の動作確認
4. パフォーマンス指標の確認

Author: Kiro AI Integration System
"""

import logging
import sys
import time
from pathlib import Path
import json
from datetime import datetime

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
            logging.FileHandler(log_dir / "debug_final_verification.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_fallback_implementations():
    """フォールバック実装の動作テスト"""
    logger = logging.getLogger(__name__)

    test_results = {}

    logger.info("🧪 フォールバック実装の動作テストを開始...")

    # QApplication初期化
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 1. BreadcrumbWidget フォールバック テスト
    logger.info("1️⃣ BreadcrumbWidget フテスト")
    try:
        from src.ui.breadcrumb_fallback import BreadcrumbWidgetFallback
        breadcrumb_widget = BreadcrumbWidgetFallback()

        # 基本機能テスト
        test_path = Path.home()
        breadcrumb_widget.set_path(str(test_path))
        current_path = breadcrumb_widget.get_path()

        if Path(current_path) == test_path:
            logger.info("✅ BreadcrumbWidget フォールバック動作正常")
            test_results["breadcrumb_fallback"] = True
        else:
            logger.error("❌ BreadcrumbWidget フォールバック動作異常")
            test_results["breadcrumb_fallback"] = False

    except Exception as e:
        logger.error(f"❌ BreadcrumbWidget フォールバックテストエラー: {e}")
        test_results["breadcrumb_fallback"] = False

    # 2. ThemeManager フォールバック テスト
    logger.info("2️⃣ ThemeManager フォールバック テスト")
    try:
        from src.ui.theme_manager_fallback import ThemeManagerFallback
        theme_manager = ThemeManagerFallback()

        # 基本機能テスト
        available_themes = theme_manager.get_available_themes()
        current_theme = theme_manager.get_current_theme()

        if len(available_themes) > 0 and current_theme in available_themes:
            logger.info("✅ ThemeManager フォールバック動作正常")
            test_results["theme_fallback"] = True
        else:
            logger.error("❌ ThemeManager フォールバック動作異常")
            test_results["theme_fallback"] = False

    except Exception as e:
        logger.error(f"❌ ThemeManager フォールバックテストエラー: {e}")
        test_results["theme_fallback"] = False

    return test_results

def test_integration_components():
    """統合コンポーネントの動作テスト"""
    logger = logging.getLogger(__name__)

    test_results = {}

    logger.info("🔧 統合コンポーネントの動作テストを開始...")

    # QApplication初期化
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        # 基本システムコンポーネント初期化
        from src.integration.config_manager import ConfigManager
        from src.integration.state_manager import StateManager
        from src.integration.logging_system import LoggerSystem

        logger_system = LoggerSystem()
        config_manager = ConfigManager(logger_system=logger_system)
        state_manager = StateManager(config_manager=config_manager, logger_system=logger_system)

        logger.info("✅ 基本システムコンポーネント初期化成功")
        test_results["system_components"] = True

        # UI コンポーネント初期化テスト
        from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid

        thumbnail_grid = OptimizedThumbnailGrid(
            config_manager,
            state_manager,
            logger_system
        )

        # 空状態テスト
        thumbnail_grid.show_empty_state()

        logger.info("✅ UI コンポーネント初期化成功")
        test_results["ui_components"] = True

        # クリーンアップ
        thumbnail_grid.cleanup()

    except Exception as e:
        logger.error(f"❌ 統合コンポーネントテストエラー: {e}")
        test_results["system_components"] = False
        test_results["ui_components"] = False

    return test_results

def analyze_error_logs():
    """エラーログの分析"""
    logger = logging.getLogger(__name__)

    logger.info("📊 エラーログの分析を開始...")

    log_file = project_root / "logs" / "photogeoview.log"

    if not log_file.exists():
        logger.warning("⚠️  ログファイルが見つかりません")
        return {"error_count": 0, "warning_count": 0, "analysis": "ログファイル未発見"}

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()

        # エラーと警告の数をカウント
        error_count = log_content.count("ERROR")
        warning_count = log_content.count("WARNING")

        # 特定のエラーパターンをチェック
        critical_errors = [
            "AttributeError",
            "ImportError",
            "ModuleNotFoundError",
            "has no attribute",
            "Failed to initialize"
        ]

        critical_error_count = 0
        for error_pattern in critical_errors:
            critical_error_count += log_content.count(error_pattern)

        logger.info(f"📈 エラー数: {error_count}")
        logger.info(f"📈 警告数: {warning_count}")
        logger.info(f"📈 重要エラー数: {critical_error_count}")

        # 改善状況の評価
        if critical_error_count == 0:
            status = "優秀"
        elif critical_error_count < 5:
            status = "良好"
        elif critical_error_count < 10:
            status = "普通"
        else:
            status = "要改善"

        logger.info(f"📊 全体的な状況: {status}")

        return {
            "error_count": error_count,
            "warning_count": warning_count,
            "critical_error_count": critical_error_count,
            "status": status,
            "analysis": f"エラー{error_count}件、警告{warning_count}件、重要エラー{critical_error_count}件"
        }

    except Exception as e:
        logger.error(f"❌ ログ分析エラー: {e}")
        return {"error_count": -1, "warning_count": -1, "analysis": f"分析エラー: {e}"}

def check_performance_metrics():
    """パフォーマンス指標の確認"""
    logger = logging.getLogger(__name__)

    logger.info("⚡ パフォーマンス指標の確認を開始...")

    try:
        import psutil
        import os

        # メモリ使用量
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        # CPU使用率
        cpu_percent = process.cpu_percent(interval=1)

        # ディスク使用量
        disk_usage = psutil.disk_usage(str(project_root))
        disk_free_gb = disk_usage.free / (1024**3)

        logger.info(f"💾 メモリ使用量: {memory_mb:.1f}MB")
        logger.info(f"🖥️  CPU使用率: {cpu_percent:.1f}%")
        logger.info(f"💿 ディスク空き容量: {disk_free_gb:.1f}GB")

        # パフォーマンス評価
        performance_score = 100

        if memory_mb > 500:
            performance_score -= 20
            logger.warning("⚠️  高メモリ使用量")

        if cpu_percent > 50:
            performance_score -= 15
            logger.warning("⚠️  高CPU使用率")

        if disk_free_gb < 1:
            performance_score -= 10
            logger.warning("⚠️  ディスク容量不足")

        logger.info(f"📊 パフォーマンススコア: {performance_score}/100")

        return {
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "disk_free_gb": disk_free_gb,
            "performance_score": performance_score
        }

    except ImportError:
        logger.warning("⚠️  psutilが利用できません")
        return {"status": "psutil_unavailable"}
    except Exception as e:
        logger.error(f"❌ パフォーマンス確認エラー: {e}")
        return {"status": f"error: {e}"}

def create_final_verification_report():
    """最終検証レポートを作成"""
    logger = logging.getLogger(__name__)

    logger.info("📋 最終検証レポートを作成中...")

    # 各テストを実行
    fallback_results = test_fallback_implementations()
    integration_results = test_integration_components()
    log_analysis = analyze_error_logs()
    performance_metrics = check_performance_metrics()

    # レポート作成
    report = {
        "timestamp": datetime.now().isoformat(),
        "verification_session": "PhotoGeoView AI統合版 最終デバッグ検証",
        "test_results": {
            "fallback_implementations": fallback_results,
            "integration_components": integration_results,
            "log_analysis": log_analysis,
            "performance_metrics": performance_metrics
        },
        "overall_status": "unknown",
        "recommendations": []
    }

    # 全体的な状況評価
    all_fallback_tests = all(fallback_results.values()) if fallback_results else False
    all_integration_tests = all(integration_results.values()) if integration_results else False
    log_status_good = log_analysis.get("critical_error_count", 999) < 5
    performance_good = performance_metrics.get("performance_score", 0) > 70

    success_count = sum([all_fallback_tests, all_integration_tests, log_status_good, performance_good])

    if success_count == 4:
        report["overall_status"] = "優秀"
        report["recommendations"].append("全ての検証項目が合格しました。アプリケーションは安定して動作しています。")
    elif success_count >= 3:
        report["overall_status"] = "良好"
        report["recommendations"].append("大部分の検証項目が合格しました。軽微な改善の余地があります。")
    elif success_count >= 2:
        report["overall_status"] = "普通"
        report["recommendations"].append("基本的な動作は確認できましたが、いくつかの問題があります。")
    else:
        report["overall_status"] = "要改善"
        report["recommendations"].append("複数の問題が検出されました。追加の修正が必要です。")

    # 具体的な推奨事項
    if not all_fallback_tests:
        report["recommendations"].append("フォールバック実装に問題があります。実装を確認してください。")

    if not all_integration_tests:
        report["recommendations"].append("統合コンポーネントに問題があります。初期化処理を確認してください。")

    if not log_status_good:
        report["recommendations"].append("エラーログに重要な問題があります。ログを詳細に確認してください。")

    if not performance_good:
        report["recommendations"].append("パフォーマンスに問題があります。リソース使用量を最適化してください。")

    # レポート保存
    report_file = project_root / "logs" / "final_verification_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"📋 最終検証レポートを保存しました: {report_file}")

    return report

def display_verification_summary(report):
    """検証結果サマリーを表示"""
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("🎯 最終デバッグ検証結果サマリー")
    logger.info("=" * 60)

    # 全体的な状況
    status_emoji = {
        "優秀": "🎉",
        "良好": "✅",
        "普通": "⚠️",
        "要改善": "❌"
    }

    overall_status = report["overall_status"]
    emoji = status_emoji.get(overall_status, "❓")

    logger.info(f"📊 全体的な状況: {emoji} {overall_status}")
    logger.info("")

    # 各テスト結果
    logger.info("📋 詳細テスト結果:")

    fallback_results = report["test_results"]["fallback_implementations"]
    for test_name, result in fallback_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name:25}: {status}")

    integration_results = report["test_results"]["integration_components"]
    for test_name, result in integration_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name:25}: {status}")

    # ログ分析結果
    log_analysis = report["test_results"]["log_analysis"]
    logger.info(f"  log_analysis            : 📊 {log_analysis.get('status', 'N/A')}")

    # パフォーマンス結果
    performance = report["test_results"]["performance_metrics"]
    if "performance_score" in performance:
        score = performance["performance_score"]
        logger.info(f"  performance_metrics     : ⚡ {score}/100")

    logger.info("=" * 60)

    # 推奨事項
    if report["recommendations"]:
        logger.info("💡 推奨事項:")
        for i, recommendation in enumerate(report["recommendations"], 1):
            logger.info(f"  {i}. {recommendation}")
        logger.info("=" * 60)

def main():
    """メイン実行関数"""
    print("🌟 PhotoGeoView AI統合版 最終デバッグ検証スクリプト")
    print("=" * 60)

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("🚀 最終デバッグ検証を開始します...")

    try:
        # 最終検証レポート作成
        report = create_final_verification_report()

        # 結果サマリー表示
        display_verification_summary(report)

        logger.info("🏁 最終デバッグ検証完了")

        # 終了コードを設定
        if report["overall_status"] in ["優秀", "良好"]:
            logger.info("✨ 検証成功！")
            return 0
        else:
            logger.warning("⚠️  検証で問題が検出されました")
            return 1

    except Exception as e:
        logger.error(f"❌ 最終検証エラー: {e}")
        import traceback
        logger.error(f"詳細: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
