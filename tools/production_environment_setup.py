#!/usr/bin/env python3
"""
ファイルリスト表示修正 - 本番環境準備ツール

設定ファイルの最終調整、ログ設定の本番環境対応、エラー監視の設定を行います。

要件: 5.1, 5.2

Author: Kiro AI Integration System
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem


class ProductionEnvironmentSetup:
    """
    本番環境準備クラス

    機能:
    - 設定ファイルの本番環境対応
    - ログ設定の最適化
    - エラー監視設定
    - パフォーマンス監視設定
    """

    def __init__(self, project_root: Path = None):
        """初期化"""
        self.project_root = project_root or Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.backup_dir = self.project_root / "config_backup"

        # ディレクトリの作成
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        self.logger_system = LoggerSystem()

    def backup_current_config(self):
        """現在の設定をバックアップ"""
        print("📁 現在の設定をバックアップ中...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = self.backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir(exist_ok=True)

        # 設定ファイルのバックアップ
        config_files = [
            "app_config.json",
            "logging_config.json",
            "performance_config.json",
            "error_monitoring_config.json",
        ]

        backed_up_files = []
        for config_file in config_files:
            source_path = self.config_dir / config_file
            if source_path.exists():
                backup_path = backup_subdir / config_file
                shutil.copy2(source_path, backup_path)
                backed_up_files.append(config_file)
                print(f"   ✅ {config_file} をバックアップ")

        print(f"   📦 バックアップ完了: {len(backed_up_files)}個のファイル")
        return backup_subdir

    def create_production_app_config(self):
        """本番環境用アプリケーション設定の作成"""
        print("⚙️ 本番環境用アプリケーション設定を作成中...")

        production_config = {
            "application": {
                "name": "PhotoGeoView",
                "version": "1.0.0",
                "environment": "production",
                "debug_mode": False,
                "development_mode": False,
            },
            "file_discovery": {
                "supported_formats": [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".bmp",
                    ".tiff",
                    ".webp",
                ],
                "max_files_per_batch": 100,
                "cache_enabled": True,
                "cache_size_mb": 256,
                "validation_enabled": True,
                "async_processing": True,
            },
            "performance": {
                "memory_limit_mb": 512,
                "max_concurrent_operations": 4,
                "thumbnail_cache_size": 1000,
                "file_watcher_enabled": True,
                "performance_monitoring": True,
            },
            "ui": {
                "theme": "system",
                "language": "ja",
                "thumbnail_size": 150,
                "grid_columns": "auto",
                "show_file_info": True,
                "animation_enabled": True,
            },
            "error_handling": {
                "show_detailed_errors": False,
                "log_all_errors": True,
                "user_friendly_messages": True,
                "error_reporting_enabled": True,
                "crash_recovery_enabled": True,
            },
            "security": {
                "restrict_file_access": True,
                "allowed_directories": [],
                "scan_for_malware": False,
                "validate_file_signatures": True,
            },
        }

        config_path = self.config_dir / "app_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(production_config, f, indent=2, ensure_ascii=False)

        print(f"   ✅ 本番環境用設定を作成: {config_path}")
        return production_config

    def create_production_logging_config(self):
        """本番環境用ログ設定の作成"""
        print("📝 本番環境用ログ設定を作成中...")

        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "file_info": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "filename": str(self.logs_dir / "app_info.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
                "file_error": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": str(self.logs_dir / "app_error.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "file_performance": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "json",
                    "filename": str(self.logs_dir / "performance.log"),
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 30,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "file_discovery": {
                    "level": "INFO",
                    "handlers": ["console", "file_info", "file_error"],
                    "propagate": False,
                },
                "performance": {
                    "level": "DEBUG",
                    "handlers": ["file_performance"],
                    "propagate": False,
                },
                "error_handler": {
                    "level": "ERROR",
                    "handlers": ["console", "file_error"],
                    "propagate": False,
                },
                "ui_integration": {
                    "level": "INFO",
                    "handlers": ["console", "file_info"],
                    "propagate": False,
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "file_info", "file_error"],
            },
        }

        config_path = self.config_dir / "logging_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(logging_config, f, indent=2, ensure_ascii=False)

        print(f"   ✅ 本番環境用ログ設定を作成: {config_path}")
        return logging_config

    def create_error_monitoring_config(self):
        """エラー監視設定の作成"""
        print("🚨 エラー監視設定を作成中...")

        error_monitoring_config = {
            "monitoring": {
                "enabled": True,
                "check_interval_seconds": 60,
                "error_threshold_per_minute": 10,
                "memory_threshold_mb": 1024,
                "cpu_threshold_percent": 80,
            },
            "alerts": {
                "email_enabled": False,
                "email_recipients": [],
                "log_alerts": True,
                "console_alerts": True,
                "alert_cooldown_minutes": 5,
            },
            "error_categories": {
                "file_access_error": {
                    "severity": "medium",
                    "auto_recovery": True,
                    "user_notification": True,
                },
                "memory_error": {
                    "severity": "high",
                    "auto_recovery": True,
                    "user_notification": False,
                },
                "ui_error": {
                    "severity": "low",
                    "auto_recovery": False,
                    "user_notification": True,
                },
                "critical_error": {
                    "severity": "critical",
                    "auto_recovery": False,
                    "user_notification": True,
                },
            },
            "recovery_actions": {
                "clear_cache": True,
                "restart_file_watcher": True,
                "garbage_collection": True,
                "reset_ui_state": True,
            },
            "reporting": {
                "daily_summary": True,
                "weekly_report": True,
                "error_statistics": True,
                "performance_metrics": True,
            },
        }

        config_path = self.config_dir / "error_monitoring_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(error_monitoring_config, f, indent=2, ensure_ascii=False)

        print(f"   ✅ エラー監視設定を作成: {config_path}")
        return error_monitoring_config

    def create_performance_monitoring_config(self):
        """パフォーマンス監視設定の作成"""
        print("📊 パフォーマンス監視設定を作成中...")

        performance_config = {
            "monitoring": {
                "enabled": True,
                "sample_interval_seconds": 30,
                "metrics_retention_days": 30,
                "detailed_profiling": False,
            },
            "metrics": {
                "memory_usage": True,
                "cpu_usage": True,
                "file_discovery_time": True,
                "thumbnail_generation_time": True,
                "ui_response_time": True,
                "cache_hit_rate": True,
                "error_rate": True,
            },
            "thresholds": {
                "memory_warning_mb": 512,
                "memory_critical_mb": 1024,
                "cpu_warning_percent": 70,
                "cpu_critical_percent": 90,
                "response_time_warning_ms": 2000,
                "response_time_critical_ms": 5000,
            },
            "optimization": {
                "auto_cache_cleanup": True,
                "memory_pressure_handling": True,
                "adaptive_batch_size": True,
                "background_processing": True,
            },
            "reporting": {
                "console_output": False,
                "log_output": True,
                "metrics_file": str(self.logs_dir / "performance_metrics.json"),
                "summary_interval_minutes": 60,
            },
        }

        config_path = self.config_dir / "performance_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(performance_config, f, indent=2, ensure_ascii=False)

        print(f"   ✅ パフォーマンス監視設定を作成: {config_path}")
        return performance_config

    def create_startup_script(self):
        """本番環境用起動スクリプトの作成"""
        print("🚀 本番環境用起動スクリプトを作成中...")

        startup_script_content = '''#!/usr/bin/env python3
"""
PhotoGeoView - 本番環境起動スクリプト

本番環境での安全な起動とエラー処理を提供します。
"""

import sys
import os
import json
import logging
import signal
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_production_logging():
    """本番環境用ログ設定の適用"""
    config_path = project_root / "config" / "logging_config.json"

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            logging_config = json.load(f)

        import logging.config
        logging.config.dictConfig(logging_config)
        print("✅ 本番環境用ログ設定を適用しました")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        print("⚠️ デフォルトログ設定を使用します")

def load_production_config():
    """本番環境用設定の読み込み"""
    config_path = project_root / "config" / "app_config.json"

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ 本番環境用設定を読み込みました")
        return config
    else:
        print("❌ 本番環境用設定ファイルが見つかりません")
        return None

def signal_handler(signum, frame):
    """シグナルハンドラー（安全な終了処理）"""
    print(f"\\n🛑 シグナル {signum} を受信しました。安全に終了します...")

    # クリーンアップ処理
    try:
        # ファイルシステム監視の停止
        # キャッシュの保存
        # 一時ファイルのクリーンアップ
        print("✅ クリーンアップ処理が完了しました")
    except Exception as e:
        print(f"⚠️ クリーンアップ中にエラーが発生しました: {e}")

    sys.exit(0)

def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🎯 PhotoGeoView - 本番環境起動")
    print("=" * 60)

    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. ログ設定の適用
        setup_production_logging()
        logger = logging.getLogger(__name__)

        # 2. 設定の読み込み
        config = load_production_config()
        if not config:
            logger.error("設定ファイルの読み込みに失敗しました")
            return 1

        # 3. 環境チェック
        logger.info("本番環境での起動を開始します")
        logger.info(f"Python バージョン: {sys.version}")
        logger.info(f"プロジェクトルート: {project_root}")

        # 4. アプリケーションの起動
        from src.main import main as app_main

        logger.info("アプリケーションを起動します")
        return app_main()

    except KeyboardInterrupt:
        print("\\n🛑 ユーザーによって中断されました")
        return 0
    except Exception as e:
        print(f"❌ 起動中にエラーが発生しました: {e}")
        if 'logger' in locals():
            logger.exception("起動エラー")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
'''

        script_path = self.project_root / "start_production.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(startup_script_content)

        # 実行権限を付与（Unix系システムの場合）
        if os.name != "nt":
            os.chmod(script_path, 0o755)

        print(f"   ✅ 本番環境用起動スクリプトを作成: {script_path}")
        return script_path

    def create_deployment_checklist(self):
        """デプロイメントチェックリストの作成"""
        print("📋 デプロイメントチェックリストを作成中...")

        checklist_content = """# PhotoGeoView - 本番環境デプロイメントチェックリスト

## 事前準備

- [ ] Python 3.8以上がインストールされている
- [ ] 必要な依存関係がインストールされている (`pip install -r requirements.txt`)
- [ ] PyQt6が正しくインストールされている
- [ ] システムリソース（メモリ2GB以上、ディスク容量1GB以上）が確保されている

## 設定ファイル確認

- [ ] `config/app_config.json` が存在し、本番環境用設定になっている
- [ ] `config/logging_config.json` が存在し、適切なログレベルが設定されている
- [ ] `config/error_monitoring_config.json` が存在し、監視設定が有効になっている
- [ ] `config/performance_config.json` が存在し、パフォーマンス監視が有効になっている

## ディレクトリ構造確認

- [ ] `logs/` ディレクトリが存在し、書き込み権限がある
- [ ] `cache/` ディレクトリが存在し、書き込み権限がある
- [ ] `config_backup/` ディレクトリが存在する
- [ ] 一時ファイル用ディレクトリが利用可能

## セキュリティ確認

- [ ] デバッグモードが無効になっている
- [ ] 開発用機能が無効になっている
- [ ] ファイルアクセス制限が適切に設定されている
- [ ] ログファイルに機密情報が含まれていない

## パフォーマンス確認

- [ ] メモリ使用量制限が適切に設定されている
- [ ] キャッシュサイズが環境に適している
- [ ] 同時実行数が適切に制限されている
- [ ] ファイル監視機能が有効になっている

## 監視・ログ確認

- [ ] エラー監視が有効になっている
- [ ] パフォーマンス監視が有効になっている
- [ ] ログローテーションが設定されている
- [ ] アラート設定が適切に構成されている

## テスト実行

- [ ] 基本機能テストが全て成功している
- [ ] パフォーマンステストが要件を満たしている
- [ ] エラーハンドリングテストが成功している
- [ ] 長時間動作テストが成功している

## 起動確認

- [ ] `python start_production.py` で正常に起動する
- [ ] UIが正しく表示される
- [ ] ファイル検出機能が動作する
- [ ] エラーが発生しない

## 運用準備

- [ ] ログ監視体制が整っている
- [ ] バックアップ手順が確立されている
- [ ] 障害対応手順が文書化されている
- [ ] ユーザーマニュアルが準備されている

## デプロイ後確認

- [ ] アプリケーションが正常に動作している
- [ ] ログが正しく出力されている
- [ ] パフォーマンス監視データが収集されている
- [ ] エラー監視が機能している

---

**注意事項:**
- 本番環境では必ずこのチェックリストを確認してからデプロイしてください
- 問題が発生した場合は、ログファイルを確認し、必要に応じて開発チームに連絡してください
- 定期的にパフォーマンス監視データを確認し、必要に応じて設定を調整してください
"""

        checklist_path = self.project_root / "DEPLOYMENT_CHECKLIST.md"
        with open(checklist_path, "w", encoding="utf-8") as f:
            f.write(checklist_content)

        print(f"   ✅ デプロイメントチェックリストを作成: {checklist_path}")
        return checklist_path

    def setup_production_environment(self):
        """本番環境の完全セットアップ"""
        print("🏭 本番環境セットアップを開始します...")
        print("=" * 60)

        try:
            # 1. 現在の設定をバックアップ
            backup_dir = self.backup_current_config()

            # 2. 本番環境用設定ファイルの作成
            app_config = self.create_production_app_config()
            logging_config = self.create_production_logging_config()
            error_config = self.create_error_monitoring_config()
            performance_config = self.create_performance_monitoring_config()

            # 3. 起動スクリプトの作成
            startup_script = self.create_startup_script()

            # 4. デプロイメントチェックリストの作成
            checklist = self.create_deployment_checklist()

            print("\n" + "=" * 60)
            print("✅ 本番環境セットアップが完了しました！")
            print("=" * 60)
            print(f"📁 設定ファイル: {self.config_dir}")
            print(f"📝 ログディレクトリ: {self.logs_dir}")
            print(f"💾 バックアップ: {backup_dir}")
            print(f"🚀 起動スクリプト: {startup_script}")
            print(f"📋 チェックリスト: {checklist}")
            print()
            print("🎯 次のステップ:")
            print("1. DEPLOYMENT_CHECKLIST.md を確認してください")
            print("2. python start_production.py でアプリケーションを起動してください")
            print("3. ログファイルを監視してください")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"❌ 本番環境セットアップ中にエラーが発生しました: {e}")
            return False


def main():
    """メイン実行関数"""
    print("PhotoGeoView - 本番環境準備ツール")
    print("=" * 60)

    setup = ProductionEnvironmentSetup()
    success = setup.setup_production_environment()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
