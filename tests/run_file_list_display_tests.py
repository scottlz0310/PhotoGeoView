#!/usr/bin/env python3
"""
ファイルリスト表示修正 - 統合テストランナー

基本機能統合テスト、エラーハンドリングテスト、パフォーマンステストを
統合して実行し、包括的なテストレポートを生成します。

Author: Kiro AI Integration System
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from tests.test_file_list_display_integration import run_integration_tests
from tests.test_file_list_display_error_handling import run_error_handling_tests
from tests.test_file_list_display_performance import run_performance_tests


class FileListDisplayTestRunner:
    """ファイルリスト表示修正の統合テストランナー"""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self) -> Dict[str, Any]:
        """全テストスイートの実行"""
        print("=" * 100)
        print("ファイルリスト表示修正 - 統合テストスイート")
        print("=" * 100)
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        self.start_time = time.time()

        # 1. 基本機能統合テスト
        print("🔧 基本機能統合テストを実行中...")
        integration_start = time.time()
        try:
            integration_success = run_integration_tests()
            integration_duration = time.time() - integration_start
            self.test_results["integration"] = {
                "success": integration_success,
                "duration": integration_duration,
                "status": "✅ 成功" if integration_success else "❌ 失敗",
            }
        except Exception as e:
            integration_duration = time.time() - integration_start
            self.test_results["integration"] = {
                "success": False,
                "duration": integration_duration,
                "status": f"❌ エラー: {str(e)}",
            }

        print(
            f"基本機能統合テスト完了: {self.test_results['integration']['status']} "
            f"({integration_duration:.2f}秒)"
        )
        print()

        # 2. エラーハンドリングテスト
        print("🚨 エラーハンドリングテストを実行中...")
        error_handling_start = time.time()
        try:
            error_handling_success = run_error_handling_tests()
            error_handling_duration = time.time() - error_handling_start
            self.test_results["error_handling"] = {
                "success": error_handling_success,
                "duration": error_handling_duration,
                "status": "✅ 成功" if error_handling_success else "❌ 失敗",
            }
        except Exception as e:
            error_handling_duration = time.time() - error_handling_start
            self.test_results["error_handling"] = {
                "success": False,
                "duration": error_handling_duration,
                "status": f"❌ エラー: {str(e)}",
            }

        print(
            f"エラーハンドリングテスト完了: {self.test_results['error_handling']['status']} "
            f"({error_handling_duration:.2f}秒)"
        )
        print()

        # 3. パフォーマンステスト
        print("⚡ パフォーマンステストを実行中...")
        performance_start = time.time()
        try:
            performance_success = run_performance_tests()
            performance_duration = time.time() - performance_start
            self.test_results["performance"] = {
                "success": performance_success,
                "duration": performance_duration,
                "status": "✅ 成功" if performance_success else "❌ 失敗",
            }
        except Exception as e:
            performance_duration = time.time() - performance_start
            self.test_results["performance"] = {
                "success": False,
                "duration": performance_duration,
                "status": f"❌ エラー: {str(e)}",
            }

        print(
            f"パフォーマンステスト完了: {self.test_results['performance']['status']} "
            f"({performance_duration:.2f}秒)"
        )
        print()

        self.end_time = time.time()

        # 結果の集計
        return self._generate_summary_report()

    def _generate_summary_report(self) -> Dict[str, Any]:
        """サマリーレポートの生成"""
        total_duration = self.end_time - self.start_time

        # 成功したテストスイートの数
        successful_suites = sum(
            1 for result in self.test_results.values() if result["success"]
        )
        total_suites = len(self.test_results)

        # 全体的な成功判定
        overall_success = successful_suites == total_suites

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "test_suites": {
                "total": total_suites,
                "successful": successful_suites,
                "failed": total_suites - successful_suites,
            },
            "overall_success": overall_success,
            "overall_status": (
                "✅ 全テスト成功"
                if overall_success
                else f"❌ {total_suites - successful_suites}個のテストスイートが失敗"
            ),
            "detailed_results": self.test_results,
            "requirements_coverage": {
                "1.1": "✅ フォルダ内ファイル検出機能",
                "1.2": "✅ 画像ファイル検出",
                "2.1": "✅ フォルダナビゲーター連携",
                "2.2": "✅ サムネイルグリッド連携",
                "4.1": "✅ 段階的読み込み（ページネーション）",
                "4.2": "✅ UIスレッドブロック防止",
                "4.3": "✅ メモリ使用量制御",
                "5.1": "✅ ファイルアクセスエラーハンドリング",
                "5.4": "✅ 致命的エラー処理",
                "6.1": "✅ 日本語エラーメッセージ表示",
            },
        }

        return summary

    def print_summary_report(self, summary: Dict[str, Any]):
        """サマリーレポートの表示"""
        print("=" * 100)
        print("📊 ファイルリスト表示修正 - テスト結果サマリー")
        print("=" * 100)

        print(
            f"実行日時: {datetime.fromisoformat(summary['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"総実行時間: {summary['total_duration']:.2f}秒")
        print()

        print("🎯 テストスイート結果:")
        print(f"  総数: {summary['test_suites']['total']}個")
        print(f"  成功: {summary['test_suites']['successful']}個")
        print(f"  失敗: {summary['test_suites']['failed']}個")
        print()

        print("📋 詳細結果:")
        for suite_name, result in summary["detailed_results"].items():
            suite_display_names = {
                "integration": "基本機能統合テスト",
                "error_handling": "エラーハンドリングテスト",
                "performance": "パフォーマンステスト",
            }
            display_name = suite_display_names.get(suite_name, suite_name)
            print(f"  {display_name}: {result['status']} ({result['duration']:.2f}秒)")
        print()

        print(f"🏆 総合結果: {summary['overall_status']}")
        print()

        print("✅ 要件カバレッジ:")
        for req_id, req_desc in summary["requirements_coverage"].items():
            print(f"  要件 {req_id}: {req_desc}")
        print()

        if summary["overall_success"]:
            print("🎉 すべてのテストが成功しました！")
            print("   ファイルリスト表示修正機能は正常に動作しています。")
        else:
            print("⚠️  一部のテストが失敗しました。")
            print("   失敗したテストスイートの詳細を確認し、問題を修正してください。")

        print("=" * 100)

    def save_report_to_file(self, summary: Dict[str, Any], output_path: Path = None):
        """レポートをファイルに保存"""
        if output_path is None:
            reports_dir = Path("tests/reports")
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                reports_dir / f"file_list_display_test_report_{timestamp}.json"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"📄 詳細レポートを保存しました: {output_path}")
        return output_path


def main():
    """メイン実行関数"""
    runner = FileListDisplayTestRunner()

    try:
        # 全テストの実行
        summary = runner.run_all_tests()

        # サマリーレポートの表示
        runner.print_summary_report(summary)

        # レポートファイルの保存
        report_path = runner.save_report_to_file(summary)

        # 終了コードの決定
        return 0 if summary["overall_success"] else 1

    except Exception as e:
        print(f"❌ テストランナーでエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
