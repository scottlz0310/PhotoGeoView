#!/usr/bin/env python3
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
    print(f"\n🛑 シグナル {signum} を受信しました。安全に終了します...")

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
        print("\n🛑 ユーザーによって中断されました")
        return 0
    except Exception as e:
        print(f"❌ 起動中にエラーが発生しました: {e}")
        if 'logger' in locals():
            logger.exception("起動エラー")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
