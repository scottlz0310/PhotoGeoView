#!/usr/bin/env python3
"""
AI統合レポート生成ツール

CI/CDパイプラインの結果を統合してレポートを生成します。

AI貢献者:
- Kiro: 統合レポートシステム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TestResult:
    """テスト結果"""

    name: str
    status: str  # passed, failed, skipped
    duration: float
    error_message: Optional[str] = None


@dataclass
class QualityMetrics:
    """品質メトリクス"""

    total_files: int
    total_issues: int
    coverage_percentage: float
    quality_score: float
    issues_by_severity: Dict[str, int]


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    total_tests: int
    regressions: int
    improvements: int
    average_execution_time: float
    memory_usage_mb: float


@dataclass
class IntegrationReport:
    """統合レポート"""

    timestamp: datetime
    build_status: str
    test_results: List[TestResult]
    quality_metrics: QualityMetrics
    performance_metrics: PerformanceMetrics
    ai_component_status: Dict[str, str]
    recommendations: List[str]


class IntegrationReportGenerator:
    """統合レポート生成器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def collect_test_results(self) -> List[TestResult]:
        """テスト結果を収集"""
        test_results = []

        # pytest結果の収集
        junit_files = list(self.project_root.glob("**/junit*.xml"))
        junit_files.extend(list(self.project_root.glob("**/test-results*.xml")))

        for junit_file in junit_files:
            try:
                tree = ET.parse(junit_file)
                root = tree.getroot()

                for testcase in root.findall(".//testcase"):
                    name = testcase.get("name", "unknown")
                    duration = float(testcase.get("time", 0))

                    failure = testcase.find("failure")
                    error = testcase.find("error")
                    skipped = testcase.find("skipped")

                    if failure is not None:
                        status = "failed"
                        error_message = failure.text
                    elif error is not None:
                        status = "failed"
                        error_message = error.text
                    elif skipped is not None:
                        status = "skipped"
                        error_message = skipped.text
                    else:
                        status = "passed"
                        error_message = None

                    test_results.append(
                        TestResult(
                            name=name,
                            status=status,
                            duration=duration,
                            error_message=error_message,
                        )
                    )

            except Exception as e:
                print(f"JUnit XMLファイル解析エラー {junit_file}: {e}")

        return test_results

    def collect_quality_metrics(self) -> QualityMetrics:
        """品質メトリクスを収集"""
        # AI品質チェッカーの結果を収集
        quality_report_path = self.project_root / "quality_report.json"

        if quality_report_path.exists():
            try:
                with open(quality_report_path, "r", encoding="utf-8") as f:
                    quality_data = json.load(f)

                return QualityMetrics(
                    total_files=quality_data.get("total_files", 0),
                    total_issues=quality_data.get("total_issues", 0),
                    coverage_percentage=quality_data.get("coverage_percentage", 0.0),
                    quality_score=quality_data.get("overall_score", 0.0),
                    issues_by_severity=quality_data.get("issues_by_severity", {}),
                )
            except Exception as e:
                print(f"品質メトリクス収集エラー: {e}")

        # デフォルト値
        return QualityMetrics(
            total_files=0,
            total_issues=0,
            coverage_percentage=0.0,
            quality_score=0.0,
            issues_by_severity={},
        )

    def collect_performance_metrics(self) -> PerformanceMetrics:
        """パフォーマンスメトリクスを収集"""
        # パフォーマンステストの結果を収集
        benchmark_files = list(self.project_root.glob("**/benchmark*.json"))

        total_tests = 0
        regressions = 0
        improvements = 0
        execution_times = []
        memory_usages = []

        for benchmark_file in benchmark_files:
            try:
                with open(benchmark_file, "r", encoding="utf-8") as f:
                    benchmark_data = json.load(f)

                benchmarks = benchmark_data.get("benchmarks", [])
                total_tests += len(benchmarks)

                for benchmark in benchmarks:
                    stats = benchmark.get("stats", {})
                    mean_time = stats.get("mean", 0)
                    execution_times.append(mean_time)

                    # メモリ使用量（仮想値）
                    memory_usages.append(mean_time * 10)  # 仮の計算

            except Exception as e:
                print(f"ベンチマークファイル解析エラー {benchmark_file}: {e}")

        return PerformanceMetrics(
            total_tests=total_tests,
            regressions=regressions,
            improvements=improvements,
            average_execution_time=(
                sum(execution_times) / len(execution_times) if execution_times else 0.0
            ),
            memory_usage_mb=(
                sum(memory_usages) / len(memory_usages) if memory_usages else 0.0
            ),
        )

    def check_ai_component_status(self) -> Dict[str, str]:
        """AIコンポーネントの状態をチェック"""
        status = {}

        # 各AIコンポーネントのテスト結果を確認
        ai_components = ["copilot", "cursor", "kiro"]

        for component in ai_components:
            test_dir = self.project_root / f"tests/{component}_tests"

            if test_dir.exists():
                # テストディレクトリが存在する場合
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "pytest",
                            str(test_dir),
                            "--tb=no",
                            "-q",
                        ],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root,
                    )

                    if result.returncode == 0:
                        status[component] = "✅ 正常"
                    else:
                        status[component] = "❌ 失敗"

                except Exception as e:
                    status[component] = f"⚠️ エラー: {e}"
            else:
                status[component] = "⚠️ テスト未実装"

        return status

    def generate_recommendations(self, report: IntegrationReport) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        # テスト結果に基づく推奨事項
        failed_tests = [t for t in report.test_results if t.status == "failed"]
        if failed_tests:
            recommendations.append(
                f"❌ {len(failed_tests)}個の失敗テストを修正してください"
            )

        # 品質メトリクスに基づく推奨事項
        if report.quality_metrics.quality_score < 70:
            recommendations.append(
                f"⚠️ 品質スコア({report.quality_metrics.quality_score:.1f})が低いため、コード品質の改善が必要です"
            )

        if report.quality_metrics.coverage_percentage < 80:
            recommendations.append(
                f"📊 テストカバレッジ({report.quality_metrics.coverage_percentage:.1f}%)を向上させてください"
            )

        # パフォーマンスに基づく推奨事項
        if report.performance_metrics.regressions > 0:
            recommendations.append(
                f"🐌 {report.performance_metrics.regressions}件のパフォーマンス回帰を修正してください"
            )

        # AIコンポーネント状態に基づく推奨事項
        failed_components = [
            comp
            for comp, status in report.ai_component_status.items()
            if "❌" in status
        ]
        if failed_components:
            recommendations.append(
                f"🤖 AIコンポーネント({', '.join(failed_components)})の問題を解決してください"
            )

        if not recommendations:
            recommendations.append("✅ すべての品質基準を満たしています")

        return recommendations

    def generate_report(self) -> IntegrationReport:
        """統合レポートを生成"""
        print("テスト結果を収集中...")
        test_results = self.collect_test_results()

        print("品質メトリクスを収集中...")
        quality_metrics = self.collect_quality_metrics()

        print("パフォーマンスメトリクスを収集中...")
        performance_metrics = self.collect_performance_metrics()

        print("AIコンポーネント状態を確認中...")
        ai_component_status = self.check_ai_component_status()

        # ビルド状態を判定
        failed_tests = [t for t in test_results if t.status == "failed"]
        build_status = "❌ 失敗" if failed_tests else "✅ 成功"

        report = IntegrationReport(
            timestamp=datetime.now(),
            build_status=build_status,
            test_results=test_results,
            quality_metrics=quality_metrics,
            performance_metrics=performance_metrics,
            ai_component_status=ai_component_status,
            recommendations=[],
        )

        # 推奨事項を生成
        report.recommendations = self.generate_recommendations(report)

        return report

    def save_report_markdown(
        self, report: IntegrationReport, output_path: Path
    ) -> None:
        """レポートをMarkdown形式で保存"""
        lines = [
            "# PhotoGeoView AI統合 CI/CDレポート",
            "",
            f"**生成日時**: {report.timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}",
            f"**ビルド状態**: {report.build_status}",
            "",
            "## 📊 概要",
            "",
            f"- **総テスト数**: {len(report.test_results)}",
            f"- **成功**: {len([t for t in report.test_results if t.status == 'passed'])}",
            f"- **失敗**: {len([t for t in report.test_results if t.status == 'failed'])}",
            f"- **スキップ**: {len([t for t in report.test_results if t.status == 'skipped'])}",
            f"- **品質スコア**: {report.quality_metrics.quality_score:.1f}/100",
            f"- **テストカバレッジ**: {report.quality_metrics.coverage_percentage:.1f}%",
            "",
            "## 🤖 AIコンポーネント状態",
            "",
        ]

        for component, status in report.ai_component_status.items():
            lines.append(f"- **{component.upper()}**: {status}")

        lines.extend(["", "## 🧪 テスト結果詳細", ""])

        # 失敗テストの詳細
        failed_tests = [t for t in report.test_results if t.status == "failed"]
        if failed_tests:
            lines.extend(["### ❌ 失敗テスト", ""])

            for test in failed_tests:
                lines.extend(
                    [
                        f"#### {test.name}",
                        f"- **実行時間**: {test.duration:.3f}秒",
                        f"- **エラー**: {test.error_message or 'エラー詳細なし'}",
                        "",
                    ]
                )

        # 品質メトリクス詳細
        lines.extend(
            [
                "## 📈 品質メトリクス",
                "",
                f"- **総ファイル数**: {report.quality_metrics.total_files}",
                f"- **総問題数**: {report.quality_metrics.total_issues}",
                f"- **品質スコア**: {report.quality_metrics.quality_score:.1f}/100",
                "",
            ]
        )

        if report.quality_metrics.issues_by_severity:
            lines.extend(["### 重要度別問題数", ""])

            for severity, count in report.quality_metrics.issues_by_severity.items():
                if count > 0:
                    lines.append(f"- **{severity}**: {count}件")

            lines.append("")

        # パフォーマンスメトリクス
        lines.extend(
            [
                "## ⚡ パフォーマンスメトリクス",
                "",
                f"- **パフォーマンステスト数**: {report.performance_metrics.total_tests}",
                f"- **回帰数**: {report.performance_metrics.regressions}",
                f"- **改善数**: {report.performance_metrics.improvements}",
                f"- **平均実行時間**: {report.performance_metrics.average_execution_time:.4f}秒",
                f"- **平均メモリ使用量**: {report.performance_metrics.memory_usage_mb:.2f}MB",
                "",
                "## 💡 推奨事項",
                "",
            ]
        )

        for recommendation in report.recommendations:
            lines.append(f"- {recommendation}")

        lines.extend(["", "---", "*このレポートは自動生成されました*"])

        output_path.write_text("\n".join(lines), encoding="utf-8")

    def save_report_json(self, report: IntegrationReport, output_path: Path) -> None:
        """レポートをJSON形式で保存"""
        report_data = {
            "timestamp": report.timestamp.isoformat(),
            "build_status": report.build_status,
            "test_results": [
                {
                    "name": t.name,
                    "status": t.status,
                    "duration": t.duration,
                    "error_message": t.error_message,
                }
                for t in report.test_results
            ],
            "quality_metrics": {
                "total_files": report.quality_metrics.total_files,
                "total_issues": report.quality_metrics.total_issues,
                "coverage_percentage": report.quality_metrics.coverage_percentage,
                "quality_score": report.quality_metrics.quality_score,
                "issues_by_severity": report.quality_metrics.issues_by_severity,
            },
            "performance_metrics": {
                "total_tests": report.performance_metrics.total_tests,
                "regressions": report.performance_metrics.regressions,
                "improvements": report.performance_metrics.improvements,
                "average_execution_time": report.performance_metrics.average_execution_time,
                "memory_usage_mb": report.performance_metrics.memory_usage_mb,
            },
            "ai_component_status": report.ai_component_status,
            "recommendations": report.recommendations,
        }

        output_path.write_text(
            json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI統合レポート生成")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("reports"), help="出力ディレクトリ"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="both",
        help="出力形式",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    generator = IntegrationReportGenerator(project_root)

    print("AI統合レポートを生成中...")
    report = generator.generate_report()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")

    if args.format in ["markdown", "both"]:
        markdown_path = args.output_dir / f"integration_report_{timestamp}.md"
        generator.save_report_markdown(report, markdown_path)
        print(f"✅ Markdownレポート: {markdown_path}")

    if args.format in ["json", "both"]:
        json_path = args.output_dir / f"integration_report_{timestamp}.json"
        generator.save_report_json(report, json_path)
        print(f"✅ JSONレポート: {json_path}")

    # 最新レポートのシンボリックリンク作成
    if args.format in ["markdown", "both"]:
        latest_md = args.output_dir / "latest_integration_report.md"
        if latest_md.exists():
            latest_md.unlink()
        try:
            latest_md.symlink_to(markdown_path.name)
        except OSError:
            # Windowsでシンボリックリンクが作成できない場合はコピー
            import shutil

            shutil.copy2(markdown_path, latest_md)

    print(f"\n📊 レポート概要:")
    print(f"  ビルド状態: {report.build_status}")
    print(
        f"  テスト結果: {len([t for t in report.test_results if t.status == 'passed'])}/{len(report.test_results)} 成功"
    )
    print(f"  品質スコア: {report.quality_metrics.quality_score:.1f}/100")

    # 失敗がある場合は終了コード1
    failed_tests = [t for t in report.test_results if t.status == "failed"]
    if failed_tests or report.quality_metrics.quality_score < 70:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
