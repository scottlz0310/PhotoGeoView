#!/usr/bin/env python3
"""
GitHub Actions AI Analyzer

GitHub ActionsのログをAIで解析し、問題の特定と改善提案を行うツール
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("github_actions_ai_analyzer")


class GitHubActionsAnalyzer:
    """GitHub Actionsログ解析クラス"""

    def __init__(self):
        self.analysis_results = {}
        self.patterns = {
            "error": r"ERROR|FAILED|FAILURE|exit code 1|Process completed with exit code 1",
            "warning": r"WARNING|WARN|warning",
            "timeout": r"timeout|TIMEOUT|timed out",
            "windows_specific": r"Windows|windows|WIN",
            "test_failure": r"test.*failed|FAILED.*test|pytest.*failed",
            "import_error": r"ImportError|ModuleNotFoundError|No module named",
            "permission_error": r"PermissionError|permission denied",
            "memory_error": r"MemoryError|out of memory|OOM",
            "coverage_error": r"coverage.*failed|Codecov.*failed",
            "qt_error": r"Qt|PyQt|QT_QPA_PLATFORM",
            "pytest_error": r"pytest.*error|collected.*error",
        }

    def analyze_ci_report(self, report_path: Path) -> Dict[str, Any]:
        """CIレポートを解析"""
        try:
            with open(report_path, encoding="utf-8") as f:
                report = json.load(f)

            analysis = {
                "file": str(report_path),
                "timestamp": report.get("timestamp", ""),
                "overall_status": report.get("overall_status", "UNKNOWN"),
                "total_duration": report.get("total_duration", 0),
                "issues": [],
                "recommendations": [],
            }

            # チェック結果を解析
            checks = report.get("checks", {})
            for check_name, check_data in checks.items():
                status = check_data.get("status", "unknown")
                message = check_data.get("message", "")
                duration = check_data.get("duration", 0)

                if status == "warn" or status == "fail":
                    issue = {
                        "check": check_name,
                        "status": status,
                        "message": message,
                        "duration": duration,
                    }
                    analysis["issues"].append(issue)

                    # 改善提案を生成
                    recommendation = self._generate_recommendation(check_name, status, message)
                    if recommendation:
                        analysis["recommendations"].append(recommendation)

            return analysis

        except Exception as e:
            logger.error(f"CIレポート解析エラー: {e}")
            return {"error": str(e)}

    def analyze_log_file(self, log_path: Path) -> Dict[str, Any]:
        """ログファイルを解析"""
        try:
            with open(log_path, encoding="utf-8") as f:
                content = f.read()

            analysis = {
                "file": str(log_path),
                "patterns_found": {},
                "issues": [],
                "recommendations": [],
            }

            # パターンマッチング
            for pattern_name, pattern in self.patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis["patterns_found"][pattern_name] = {
                        "count": len(matches),
                        "examples": matches[:5],  # 最初の5つの例
                    }

            # 問題の特定
            if analysis["patterns_found"].get("error"):
                analysis["issues"].append(
                    {
                        "type": "error",
                        "description": "エラーが検出されました",
                        "count": analysis["patterns_found"]["error"]["count"],
                    }
                )

            if analysis["patterns_found"].get("windows_specific"):
                analysis["issues"].append(
                    {
                        "type": "windows_specific",
                        "description": "Windows固有の問題が検出されました",
                        "count": analysis["patterns_found"]["windows_specific"]["count"],
                    }
                )

            if analysis["patterns_found"].get("test_failure"):
                analysis["issues"].append(
                    {
                        "type": "test_failure",
                        "description": "テスト失敗が検出されました",
                        "count": analysis["patterns_found"]["test_failure"]["count"],
                    }
                )

            # 改善提案を生成
            analysis["recommendations"] = self._generate_log_recommendations(analysis["patterns_found"])

            return analysis

        except Exception as e:
            logger.error(f"ログファイル解析エラー: {e}")
            return {"error": str(e)}

    def _generate_recommendation(self, check_name: str, status: str, message: str) -> str | None:
        """チェック結果に基づく改善提案を生成"""
        recommendations = {
            "テストチェック": {
                "warn": "テストファイルの収集エラーを調査してください。pytest設定を確認し、テストディレクトリの構造を見直してください。",
                "fail": "テストの実行に失敗しています。テスト環境の設定と依存関係を確認してください。",
            },
            "構文チェック": {
                "warn": "構文エラーが検出されました。コードの構文を修正してください。",
                "fail": "重大な構文エラーがあります。コードの修正が必要です。",
            },
            "インポートチェック": {
                "warn": "インポートエラーが検出されました。依存関係とパス設定を確認してください。",
                "fail": "重要なモジュールのインポートに失敗しています。依存関係のインストールを確認してください。",
            },
        }

        return recommendations.get(check_name, {}).get(status)

    def _generate_log_recommendations(self, patterns_found: Dict) -> List[str]:
        """ログパターンに基づく改善提案を生成"""
        recommendations = []

        if patterns_found.get("error"):
            recommendations.append("エラーが多数検出されています。ログの詳細を確認し、根本原因を特定してください。")

        if patterns_found.get("windows_specific"):
            recommendations.append("Windows固有の問題が検出されています。Windows環境でのテスト設定を見直してください。")

        if patterns_found.get("test_failure"):
            recommendations.append("テスト失敗が検出されています。テストケースとテスト環境を確認してください。")

        if patterns_found.get("import_error"):
            recommendations.append(
                "インポートエラーが検出されています。依存関係のインストールとパス設定を確認してください。"
            )

        if patterns_found.get("permission_error"):
            recommendations.append("権限エラーが検出されています。ファイル権限とアクセス設定を確認してください。")

        if patterns_found.get("memory_error"):
            recommendations.append("メモリエラーが検出されています。メモリ使用量を最適化してください。")

        if patterns_found.get("coverage_error"):
            recommendations.append(
                "カバレッジエラーが検出されています。カバレッジ設定とファイル生成を確認してください。"
            )

        if patterns_found.get("qt_error"):
            recommendations.append("Qt関連のエラーが検出されています。Qt環境設定を確認してください。")

        return recommendations

    def analyze_multiple_reports(self, reports_dir: Path) -> Dict[str, Any]:
        """複数のレポートを解析"""
        analysis = {
            "total_reports": 0,
            "successful_reports": 0,
            "failed_reports": 0,
            "warned_reports": 0,
            "trends": {},
            "common_issues": [],
            "recommendations": [],
        }

        # JSONレポートファイルを検索
        json_files = list(reports_dir.glob("ci_report_*.json"))
        analysis["total_reports"] = len(json_files)

        status_counts = {"pass": 0, "warn": 0, "fail": 0}
        all_issues = []
        all_recommendations = []

        for json_file in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:  # 最新10件
            report_analysis = self.analyze_ci_report(json_file)

            if "error" not in report_analysis:
                status = report_analysis.get("overall_status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

                all_issues.extend(report_analysis.get("issues", []))
                all_recommendations.extend(report_analysis.get("recommendations", []))

                # 詳細なログ出力
                logger.info(f"解析完了: {json_file.name} - ステータス: {status}")
                if report_analysis.get("issues"):
                    logger.info(f"  問題: {len(report_analysis['issues'])}件")

        analysis["successful_reports"] = status_counts.get("pass", 0)
        analysis["warned_reports"] = status_counts.get("WARNING", 0)
        analysis["failed_reports"] = status_counts.get("fail", 0)

        # 共通の問題を特定
        issue_types = {}
        for issue in all_issues:
            issue_type = issue.get("check", "unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        analysis["common_issues"] = [
            {"type": issue_type, "count": count}
            for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True)
        ]

        # 改善提案を統合
        analysis["recommendations"] = list(set(all_recommendations))

        return analysis

    def generate_report(self, analysis_results: Dict[str, Any]) -> str:
        """解析結果をレポート形式で出力"""
        report = []
        report.append("# GitHub Actions AI 解析レポート")
        report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 概要
        report.append("## 📊 概要")
        report.append(f"- 総レポート数: {analysis_results.get('total_reports', 0)}")
        report.append(f"- 成功: {analysis_results.get('successful_reports', 0)}")
        report.append(f"- 警告: {analysis_results.get('warned_reports', 0)}")
        report.append(f"- 失敗: {analysis_results.get('failed_reports', 0)}")
        report.append("")

        # 共通の問題
        if analysis_results.get("common_issues"):
            report.append("## 🚨 共通の問題")
            for issue in analysis_results["common_issues"]:
                report.append(f"- **{issue['type']}**: {issue['count']}回発生")
            report.append("")

        # 改善提案
        if analysis_results.get("recommendations"):
            report.append("## 💡 改善提案")
            for i, recommendation in enumerate(analysis_results["recommendations"], 1):
                report.append(f"{i}. {recommendation}")
            report.append("")

        # ログ解析結果
        if analysis_results.get("log_analysis"):
            log_analysis = analysis_results["log_analysis"]
            report.append("## 📋 CIシミュレーションログ解析")

            if log_analysis.get("patterns_found"):
                report.append("### 検出されたパターン")
                for pattern_name, pattern_data in log_analysis["patterns_found"].items():
                    count = pattern_data.get("count", 0)
                    report.append(f"- **{pattern_name}**: {count}回")
                report.append("")

            if log_analysis.get("issues"):
                report.append("### 検出された問題")
                for issue in log_analysis["issues"]:
                    report.append(f"- **{issue['type']}**: {issue['description']} ({issue['count']}回)")
                report.append("")

            if log_analysis.get("recommendations"):
                report.append("### ログ解析による改善提案")
                for i, recommendation in enumerate(log_analysis["recommendations"], 1):
                    report.append(f"{i}. {recommendation}")
                report.append("")

        return "\n".join(report)


def main():
    """メイン関数"""
    analyzer = GitHubActionsAnalyzer()

    # レポートディレクトリ
    reports_dir = Path("reports")

    if not reports_dir.exists():
        logger.error("reportsディレクトリが見つかりません")
        sys.exit(1)

    # 複数レポートの解析
    logger.info("GitHub Actionsレポートを解析中...")
    analysis_results = analyzer.analyze_multiple_reports(reports_dir)

    # CIシミュレーションログの解析
    logs_dir = Path("logs")
    if logs_dir.exists():
        logger.info("CIシミュレーションログを解析中...")
        ci_log_file = logs_dir / "ci-simulation.log"
        if ci_log_file.exists():
            log_analysis = analyzer.analyze_log_file(ci_log_file)
            analysis_results["log_analysis"] = log_analysis

    # レポート生成
    report = analyzer.generate_report(analysis_results)

    # 結果を出力
    print(report)

    # ファイルに保存
    output_file = reports_dir / f"ai_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"解析レポートを保存しました: {output_file}")


if __name__ == "__main__":
    main()
