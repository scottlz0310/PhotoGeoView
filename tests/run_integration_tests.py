#!/usr/bin/env python3
"""
Integration Test Runner

AI統合テストの実行とレポート生成を行うメインスクリプト

Usage:
    python tests/run_integration_tests.py [--benchmark] [--unit] [--integration] [--all]

Author: Kiro AI Integration System
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from tests.ai_integration_test_suite import AIIntegrationTestSuite
from tests.performance_benchmarks import PerformanceBenchmarkSuite
from tests.unit_tests import unittest


def run_unit_tests():
    """単体テストの実行"""
    print("=" * 60)
    print("単体テストを実行中...")
    print("=" * 60)

    # unittest の実行
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_integration_tests():
    """統合テストの実行"""
    print("=" * 60)
    print("AI統合テストを実行中...")
    print("=" * 60)

    suite = AIIntegrationTestSuite()
    results = suite.run_all_tests()
    report_path = suite.generate_test_report()

    print(f"\n統合テスト結果:")
    print(f"  全体ステータス: {results['overall_status']}")
    print(f"  テスト数: {results['test_count']}")
    print(f"  所要時間: {results['total_duration']:.2f}秒")
    print(f"  レポート: {report_path}")

    return results['overall_status'] in ['all_passed', 'mostly_passed']


def run_performance_benchmarks():
    """パフォーマンスベンチマークの実行"""
    print("=" * 60)
    print("パフォーマンスベンチマークを実行中...")
    print("=" * 60)

    suite = PerformanceBenchmarkSuite()
    results = suite.run_all_benchmarks()
    report_path = suite.generate_benchmark_report()

    print(f"\nベンチマーク結果:")
    print(f"  レポート: {report_path}")

    # 主要な結果を表示
    if "comparison_summary" in results:
        summary = results["comparison_summary"]
        if "performance_improvement" in summary:
            improvement = summary["performance_improvement"]
            print(f"  統合実装のパフォーマンス改善: {improvement['duration_improvement']:.1f}%")

    return True


def generate_combined_report(unit_success, integration_success, benchmark_success):
    """統合レポートの生成"""
    report_dir = Path("tests/reports")
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"combined_test_report_{timestamp}.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# AI統合テスト総合レポート\n\n")
        f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## テスト結果サマリー\n\n")
        f.write(f"- 単体テスト: {'✅ 成功' if unit_success else '❌ 失敗'}\n")
        f.write(f"- 統合テスト: {'✅ 成功' if integration_success else '❌ 失敗'}\n")
        f.write(f"- パフォーマンステスト: {'✅ 成功' if benchmark_success else '❌ 失敗'}\n\n")

        overall_success = unit_success and integration_success and benchmark_success
        f.write(f"**総合結果: {'✅ 全テスト成功' if overall_success else '❌ 一部テスト失敗'}**\n\n")

        f.write("## 詳細レポート\n\n")
        f.write("詳細な結果は以下のファイルを参照してください:\n\n")
        f.write("- 統合テスト: `tests/reports/ai_integration_report.json`\n")
        f.write("- パフォーマンステスト: `tests/reports/performance_benchmark_report.json`\n\n")

        if not overall_success:
            f.write("## 推奨アクション\n\n")
            if not unit_success:
                f.write("- 単体テストの失敗を修正してください\n")
            if not integration_success:
                f.write("- AI統合の問題を調査・修正してください\n")
            if not benchmark_success:
                f.write("- パフォーマンスの問題を調査・修正してください\n")

    print(f"\n統合レポートを生成しました: {report_path}")
    return overall_success


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='AI統合テストランナー')
    parser.add_argument('--unit', action='store_true', help='単体テストのみ実行')
    parser.add_argument('--integration', action='store_true', help='統合テストのみ実行')
    parser.add_argument('--benchmark', action='store_true', help='ベンチマークのみ実行')
    parser.add_argument('--all', action='store_true', help='全テストを実行（デフォルト）')

    args = parser.parse_args()

    # デフォルトは全テスト実行
    if not any([args.unit, args.integration, args.benchmark]):
        args.all = True

    print("AI統合テストスイートを開始します")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    unit_success = True
    integration_success = True
    benchmark_success = True

    try:
        if args.unit or args.all:
            unit_success = run_unit_tests()

        if args.integration or args.all:
            integration_success = run_integration_tests()

        if args.benchmark or args.all:
            benchmark_success = run_performance_benchmarks()

        # 統合レポートの生成
        overall_success = generate_combined_report(
            unit_success, integration_success, benchmark_success
        )

        total_duration = time.time() - start_time

        print("=" * 60)
        print("テストスイート完了")
        print("=" * 60)
        print(f"総実行時間: {total_duration:.2f}秒")
        print(f"総合結果: {'✅ 成功' if overall_success else '❌ 失敗'}")

        return 0 if overall_success else 1

    except Exception as e:
        print(f"テスト実行中にエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
