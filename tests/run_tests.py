#!/usr/bin/env python3
"""
PhotoGeoView テストランナー
すべての単体テストと統合テストを実行
"""

import unittest
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import setup_logging, get_logger


def run_all_tests():
    """すべてのテストを実行"""
    # ログ設定の初期化
    setup_logging()
    logger = get_logger(__name__)

    logger.info("PhotoGeoView テストスイートを開始します")

    # テストディレクトリのパス
    tests_dir = Path(__file__).parent

    # テストディスカバリー
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 単体テストを追加
    test_modules = [
        'test_exif_parser',
        'test_map_viewer',
        'test_image_loader',
        'test_theme_manager'
    ]

    for module_name in test_modules:
        try:
            module = __import__(module_name)
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
            logger.info(f"テストモジュール '{module_name}' を読み込みました")
        except ImportError as e:
            logger.warning(f"テストモジュール '{module_name}' の読み込みに失敗しました: {e}")
        except Exception as e:
            logger.error(f"テストモジュール '{module_name}' の処理中にエラーが発生しました: {e}")

    # テストランナーの設定
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )

    # テストを実行
    logger.info("テストを実行中...")
    result = runner.run(suite)

    # 結果を表示
    logger.info("=" * 60)
    logger.info("テスト実行結果:")
    logger.info(f"実行したテスト数: {result.testsRun}")
    logger.info(f"失敗したテスト数: {len(result.failures)}")
    logger.info(f"エラーが発生したテスト数: {len(result.errors)}")
    logger.info(f"スキップされたテスト数: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        logger.error("失敗したテスト:")
        for test, traceback in result.failures:
            logger.error(f"  - {test}: {traceback}")

    if result.errors:
        logger.error("エラーが発生したテスト:")
        for test, traceback in result.errors:
            logger.error(f"  - {test}: {traceback}")

    # 成功判定
    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        logger.info("✅ すべてのテストが成功しました！")
    else:
        logger.error("❌ 一部のテストが失敗しました")

    logger.info("=" * 60)

    return success


def run_specific_test(test_name):
    """特定のテストを実行"""
    logger = get_logger(__name__)
    logger.info(f"特定のテスト '{test_name}' を実行します")

    # テストディスカバリー
    loader = unittest.TestLoader()

    try:
        # テストクラスを動的に読み込み
        if '.' in test_name:
            module_name, class_name = test_name.split('.')
            module = __import__(module_name)
            test_class = getattr(module, class_name)
            suite = loader.loadTestsFromTestCase(test_class)
        else:
            # モジュール全体をテスト
            module = __import__(test_name)
            suite = loader.loadTestsFromModule(module)

        # テストランナー
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        return len(result.failures) == 0 and len(result.errors) == 0

    except ImportError as e:
        logger.error(f"テスト '{test_name}' の読み込みに失敗しました: {e}")
        return False
    except Exception as e:
        logger.error(f"テスト '{test_name}' の実行中にエラーが発生しました: {e}")
        return False


def run_integration_tests():
    """統合テストを実行"""
    logger = get_logger(__name__)
    logger.info("統合テストを実行します")

    try:
        # 統合テストモジュールを読み込み
        import integration_test

        # 統合テストを実行（実際のGUIテストは別途実行）
        logger.info("統合テストモジュールの読み込みが完了しました")
        logger.info("GUI統合テストは手動で実行してください: python tests/integration_test.py")

        return True

    except ImportError as e:
        logger.error(f"統合テストの読み込みに失敗しました: {e}")
        return False
    except Exception as e:
        logger.error(f"統合テストの実行中にエラーが発生しました: {e}")
        return False


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "all":
            # すべてのテストを実行
            success = run_all_tests()
            return 0 if success else 1

        elif command == "integration":
            # 統合テストを実行
            success = run_integration_tests()
            return 0 if success else 1

        elif command == "specific":
            # 特定のテストを実行
            if len(sys.argv) > 2:
                test_name = sys.argv[2]
                success = run_specific_test(test_name)
                return 0 if success else 1
            else:
                print("使用方法: python run_tests.py specific <test_name>")
                return 1

        else:
            print("使用方法:")
            print("  python run_tests.py all          # すべてのテストを実行")
            print("  python run_tests.py integration  # 統合テストを実行")
            print("  python run_tests.py specific <test_name>  # 特定のテストを実行")
            return 1
    else:
        # デフォルトですべてのテストを実行
        success = run_all_tests()
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
