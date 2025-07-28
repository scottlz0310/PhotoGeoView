"""
パフォーマンス回帰検出システム

AI統合後のパフォーマンス変化を監視し、回帰を検出します。

AI貢献者:
- Kiro: パフォーマンス回帰検出システム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class PerformanceLevel(Enum):
    """パフォーマンスレベル"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """パフォーマンスメトリクス"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    ai_component: str
    test_context: Dict[str, Any]


@dataclass
class PerformanceBenchmark:
    """パフォーマンスベンチマーク"""
    test_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    ai_component: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RegressionResult:
    """回帰検出結果"""
    test_name: str
    current_performance: float
    baseline_performance: float
    regression_percentage: float
    severity: PerformanceLevel
    is_regression: bool
    recommendation: str


class PerformanceRegressionDetector:
    """パフォーマンス回帰検出器"""

    def __init__(self, baseline_file: Path = None):
        self.baseline_file = baseline_file or Path("performance_baseline.json")
        self.current_results: List[PerformanceBenchmark] = []
        self.baseline_data: Dict[str, Any] = self._load_baseline()

        # 回帰しきい値（パーセンテージ）
        self.regression_thresholds = {
            PerformanceLevel.CRITICAL: 50.0,  # 50%以上の劣化
            PerformanceLevel.POOR: 30.0,      # 30%以上の劣化
            PerformanceLevel.ACCEPTABLE: 15.0, # 15%以上の劣化
            PerformanceLevel.GOOD: 5.0,       # 5%以上の劣化
        }

    def _load_baseline(self) -> Dict[str, Any]:
        """ベースラインデータを読み込み"""
        if self.bne_file.exists():
            try:
                with open(self.baseline_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"ベースライン読み込みエラー: {e}")
        return {}

    def _save_baseline(self, data: Dict[str, Any]) -> None:
        """ベースラインデータを保存"""
        try:
            with open(self.baseline_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"ベースライン保存エラー: {e}")

    def measure_performance(self, test_name: str, test_func: Callable,
                          ai_component: str, iterations: int = 5) -> PerformanceBenchmark:
        """パフォーマンスを測定"""
        import psutil
        import os

        execution_times = []
        memory_usages = []
        cpu_usages = []

        process = psutil.Process(os.getpid())

        for i in range(iterations):
            # CPU使用率測定開始
            cpu_percent_start = process.cpu_percent()

            # メモリ使用量測定開始
            memory_start = process.memory_info().rss / 1024 / 1024  # MB

            # 実行時間測定
            start_time = time.perf_counter()

            try:
                test_func()
                success = True
                error_message = None
            except Exception as e:
                success = False
                error_message = str(e)
                break

            end_time = time.perf_counter()

            # メモリ使用量測定終了
            memory_end = process.memory_info().rss / 1024 / 1024  # MB

            # CPU使用率測定終了
            time.sleep(0.1)  # CPU使用率の安定化
            cpu_percent_end = process.cpu_percent()

            execution_times.append(end_time - start_time)
            memory_usages.append(memory_end - memory_start)
            cpu_usages.append(max(cpu_percent_end - cpu_percent_start, 0))

        if success:
            avg_execution_time = statistics.mean(execution_times)
            avg_memory_usage = statistics.mean(memory_usages)
            avg_cpu_usage = statistics.mean(cpu_usages)
        else:
            avg_execution_time = float('inf')
            avg_memory_usage = float('inf')
            avg_cpu_usage = float('inf')

        benchmark = PerformanceBenchmark(
            test_name=test_name,
            execution_time=avg_execution_time,
            memory_usage=avg_memory_usage,
            cpu_usage=avg_cpu_usage,
            ai_component=ai_component,
            success=success,
            error_message=error_message
        )

        self.current_results.append(benchmark)
        return benchmark

    def detect_regression(self, benchmark: PerformanceBenchmark) -> RegressionResult:
        """回帰を検出"""
        baseline_key = f"{benchmark.test_name}_{benchmark.ai_component}"
        baseline = self.baseline_data.get(baseline_key)

        if not baseline:
            # ベースラインが存在しない場合は新規として扱う
            return RegressionResult(
                test_name=benchmark.test_name,
                current_performance=benchmark.execution_time,
                baseline_performance=0.0,
                regression_percentage=0.0,
                severity=PerformanceLevel.GOOD,
                is_regression=False,
                recommendation="新規テスト - ベースラインを設定してください"
            )

        baseline_time = baseline.get('execution_time', 0.0)
        current_time = benchmark.execution_time

        if baseline_time == 0 or current_time == float('inf'):
            regression_percentage = float('inf')
        else:
            regression_percentage = ((current_time - baseline_time) / baseline_time) * 100

        # 回帰レベルを判定
        severity = PerformanceLevel.EXCELLENT
        is_regression = False

        if regression_percentage > self.regression_thresholds[PerformanceLevel.CRITICAL]:
            severity = PerformanceLevel.CRITICAL
            is_regression = True
        elif regression_percentage > self.regression_thresholds[PerformanceLevel.POOR]:
            severity = PerformanceLevel.POOR
            is_regression = True
        elif regression_percentage > self.regression_thresholds[PerformanceLevel.ACCEPTABLE]:
            severity = PerformanceLevel.ACCEPTABLE
            is_regression = True
        elif regression_percentage > self.regression_thresholds[PerformanceLevel.GOOD]:
            severity = PerformanceLevel.GOOD
            is_regression = True

        # 推奨事項を生成
        recommendation = self._generate_recommendation(severity, regression_percentage, benchmark)

        return RegressionResult(
            test_name=benchmark.test_name,
            current_performance=current_time,
            baseline_performance=baseline_time,
            regression_percentage=regression_percentage,
            severity=severity,
            is_regression=is_regression,
            recommendation=recommendation
        )

    def _generate_recommendation(self, severity: PerformanceLevel,
                               regression_percentage: float,
                               benchmark: PerformanceBenchmark) -> str:
        """推奨事項を生成"""
        if severity == PerformanceLevel.CRITICAL:
            return f"重大なパフォーマンス劣化 ({regression_percentage:.1f}%) - 即座に修正が必要です"
        elif severity == PerformanceLevel.POOR:
            return f"パフォーマンス劣化 ({regression_percentage:.1f}%) - 最適化を検討してください"
        elif severity == PerformanceLevel.ACCEPTABLE:
            return f"軽微なパフォーマンス劣化 ({regression_percentage:.1f}%) - 監視を継続してください"
        elif severity == PerformanceLevel.GOOD:
            return f"わずかなパフォーマンス劣化 ({regression_percentage:.1f}%) - 許容範囲内です"
        else:
            if regression_percentage < 0:
                return f"パフォーマンス改善 ({abs(regression_percentage):.1f}%) - 良好です"
            else:
                return "パフォーマンス維持 - 良好です"

    def update_baseline(self) -> None:
        """現在の結果でベースラインを更新"""
        for benchmark in self.current_results:
            if benchmark.success:
                baseline_key = f"{benchmark.test_name}_{benchmark.ai_component}"
                self.baseline_data[baseline_key] = {
                    'execution_time': benchmark.execution_time,
                    'memory_usage': benchmark.memory_usage,
                    'cpu_usage': benchmark.cpu_usage,
                    'timestamp': benchmark.timestamp.isoformat(),
                    'ai_component': benchmark.ai_component
                }

        self._save_baseline(self.baseline_data)

    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """パフォーマンス回帰レポートを生成"""
        report_lines = [
            "# PhotoGeoView パフォーマンス回帰レポート",
            "",
            f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "",
            "## 概要",
            "",
            f"- **テスト実行数**: {len(self.current_results)}",
            f"- **成功テスト**: {sum(1 for r in self.current_results if r.success)}",
            f"- **失敗テスト**: {sum(1 for r in self.current_results if not r.success)}",
            "",
            "## パフォーマンス結果",
            ""
        ]

        regressions = []
        improvements = []

        for benchmark in self.current_results:
            if not benchmark.success:
                report_lines.extend([
                    f"### ❌ {benchmark.test_name} ({benchmark.ai_component})",
                    f"**エラー**: {benchmark.error_message}",
                    ""
                ])
                continue

            regression_result = self.detect_regression(benchmark)

            if regression_result.is_regression:
                regressions.append(regression_result)
                status_icon = "🔴" if regression_result.severity == PerformanceLevel.CRITICAL else "🟡"
            elif regression_result.regression_percentage < -5:  # 5%以上の改善
                improvements.append(regression_result)
                status_icon = "🟢"
            else:
                status_icon = "✅"

            report_lines.extend([
                f"### {status_icon} {benchmark.test_name} ({benchmark.ai_component})",
                f"- **実行時間**: {benchmark.execution_time:.4f}秒",
                f"- **メモリ使用量**: {benchmark.memory_usage:.2f}MB",
                f"- **CPU使用率**: {benchmark.cpu_usage:.1f}%",
                ""
            ])

            if regression_result.baseline_performance > 0:
                report_lines.extend([
                    f"- **ベースライン**: {regression_result.baseline_performance:.4f}秒",
                    f"- **変化率**: {regression_result.regression_percentage:+.1f}%",
                    f"- **推奨事項**: {regression_result.recommendation}",
                    ""
                ])

        # 回帰サマリー
        if regressions:
            report_lines.extend([
                "## 🔴 パフォーマンス回帰",
                ""
            ])

            for regression in sorted(regressions, key=lambda x: x.regression_percentage, reverse=True):
                report_lines.extend([
                    f"### {regression.test_name}",
                    f"- **劣化率**: {regression.regression_percentage:.1f}%",
                    f"- **重要度**: {regression.severity.value}",
                    f"- **推奨事項**: {regression.recommendation}",
                    ""
                ])

        # 改善サマリー
        if improvements:
            report_lines.extend([
                "## 🟢 パフォーマンス改善",
                ""
            ])

            for improvement in sorted(improvements, key=lambda x: x.regression_percentage):
                report_lines.extend([
                    f"### {improvement.test_name}",
                    f"- **改善率**: {abs(improvement.regression_percentage):.1f}%",
                    f"- **現在**: {improvement.current_performance:.4f}秒",
                    f"- **ベースライン**: {improvement.baseline_performance:.4f}秒",
                    ""
                ])

        report_content = "\n".join(report_lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content, encoding='utf-8')

        return report_content


# テスト用のサンプル関数
def sample_image_processing_test():
    """サンプル画像処理テスト"""
    import time
    import random

    # 画像処理のシミュレーション
    time.sleep(random.uniform(0.01, 0.05))

    # メモリ使用のシミュレーション
    data = [random.random() for _ in range(10000)]
    result = sum(data)

    return result


def sample_ui_rendering_test():
    """サンプルUIレンダリングテスト"""
    import time
    import random

    # UIレンダリングのシミュレーション
    time.sleep(random.uniform(0.005, 0.02))

    # DOM操作のシミュレーション
    elements = []
    for i in range(1000):
        elements.append(f"element_{i}")

    return len(elements)


def sample_integration_test():
    """サンプル統合テスト"""
    import time
    import random

    # 統合処理のシミュレーション
    time.sleep(random.uniform(0.02, 0.08))

    # データ処理のシミュレーション
    data = {}
    for i in range(5000):
        data[f"key_{i}"] = random.random()

    return len(data)


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='パフォーマンス回帰検出')
    parser.add_argument('--update-baseline', action='store_true', help='ベースラインを更新')
    parser.add_argument('--output', '-o', type=Path, help='レポート出力パス')
    parser.add_argument('--iterations', '-i', type=int, default=5, help='測定回数')

    args = parser.parse_args()

    detector = PerformanceRegressionDetector()

    print("パフォーマンステストを実行中...")

    # サンプルテストを実行
    detector.measure_performance(
        "image_processing",
        sample_image_processing_test,
        "copilot",
        args.iterations
    )

    detector.measure_performance(
        "ui_rendering",
        sample_ui_rendering_test,
        "cursor",
        args.iterations
    )

    detector.measure_performance(
        "integration_processing",
        sample_integration_test,
        "kiro",
        args.iterations
    )

    # レポート生成
    report = detector.generate_report(args.output)

    if not args.output:
        print("\n" + report)

    # ベースライン更新
    if args.update_baseline:
        detector.update_baseline()
        print("ベースラインを更新しました")

    # 回帰検出結果の確認
    regressions = []
    for benchmark in detector.current_results:
        if benchmark.success:
            regression_result = detector.detect_regression(benchmark)
            if regression_result.is_regression:
                regressions.append(regression_result)

    if regressions:
        print(f"\n⚠️  {len(regressions)}件のパフォーマンス回帰が検出されました")
        for regression in regressions:
            print(f"  - {regression.test_name}: {regression.regression_percentage:.1f}%劣化")
        sys.exit(1)
    else:
        print("\n✅ パフォーマンス回帰は検出されませんでした")
        sys.exit(0)


if __name__ == "__main__":
    main()
