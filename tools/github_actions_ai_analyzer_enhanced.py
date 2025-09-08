#!/usr/bin/env python3
"""
Enhanced GitHub Actions AI Analyzer

GitHub Actions AI Analyzerリポジトリ用に拡張されたAI解析ツール
自動的なテスト品質向上と継続的な改善を支援します。
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("enhanced_github_actions_ai_analyzer")


class EnhancedGitHubActionsAnalyzer:
    """拡張されたGitHub Actions AI解析クラス"""

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
            "dependency_error": r"pip.*error|npm.*error|yarn.*error",
            "build_error": r"build.*failed|compilation.*error",
            "network_error": r"timeout|connection.*failed|network.*error",
            "security_error": r"security.*vulnerability|CVE|vulnerability",
            "performance_issue": r"performance.*issue|slow|timeout",
            "quality_issue": r"code.*quality|style.*issue|lint.*error"
        }

        # 品質メトリクス
        self.quality_metrics = {
            "test_coverage": 0.0,
            "build_success_rate": 0.0,
            "error_frequency": 0.0,
            "warning_frequency": 0.0,
            "performance_score": 0.0
        }

    def analyze_ci_report(self, report_path: Path) -> Dict[str, Any]:
        """CIレポートを解析"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)

            analysis = {
                "file": str(report_path),
                "timestamp": report.get("timestamp", ""),
                "overall_status": report.get("overall_status", "UNKNOWN"),
                "total_duration": report.get("total_duration", 0),
                "issues": [],
                "recommendations": [],
                "quality_score": 0.0
            }

            # チェック結果を解析
            checks = report.get("checks", {})
            total_checks = len(checks)
            passed_checks = 0

            for check_name, check_data in checks.items():
                status = check_data.get("status", "unknown")
                message = check_data.get("message", "")
                duration = check_data.get("duration", 0)

                if status == "pass":
                    passed_checks += 1
                elif status == "warn" or status == "fail":
                    issue = {
                        "check": check_name,
                        "status": status,
                        "message": message,
                        "duration": duration
                    }
                    analysis["issues"].append(issue)

                    # 改善提案を生成
                    recommendation = self._generate_recommendation(check_name, status, message)
                    if recommendation:
                        analysis["recommendations"].append(recommendation)

            # 品質スコアを計算
            if total_checks > 0:
                analysis["quality_score"] = (passed_checks / total_checks) * 100

            return analysis

        except Exception as e:
            logger.error(f"CIレポート解析エラー: {e}")
            return {"error": str(e)}

    def analyze_log_file(self, log_path: Path) -> Dict[str, Any]:
        """ログファイルを解析"""
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()

            analysis = {
                "file": str(log_path),
                "patterns_found": {},
                "issues": [],
                "recommendations": [],
                "quality_metrics": {}
            }

            # パターンマッチング
            for pattern_name, pattern in self.patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis["patterns_found"][pattern_name] = {
                        "count": len(matches),
                        "examples": matches[:5]  # 最初の5つの例
                    }

            # 問題の特定
            if analysis["patterns_found"].get("error"):
                analysis["issues"].append({
                    "type": "error",
                    "description": "エラーが検出されました",
                    "count": analysis["patterns_found"]["error"]["count"]
                })

            if analysis["patterns_found"].get("windows_specific"):
                analysis["issues"].append({
                    "type": "windows_specific",
                    "description": "Windows固有の問題が検出されました",
                    "count": analysis["patterns_found"]["windows_specific"]["count"]
                })

            if analysis["patterns_found"].get("test_failure"):
                analysis["issues"].append({
                    "type": "test_failure",
                    "description": "テスト失敗が検出されました",
                    "count": analysis["patterns_found"]["test_failure"]["count"]
                })

            # 品質メトリクスを計算
            total_lines = len(content.split('\n'))
            error_count = analysis["patterns_found"].get("error", {}).get("count", 0)
            warning_count = analysis["patterns_found"].get("warning", {}).get("count", 0)

            analysis["quality_metrics"] = {
                "error_frequency": error_count / max(total_lines, 1) * 1000,  # 1000行あたり
                "warning_frequency": warning_count / max(total_lines, 1) * 1000,
                "total_issues": error_count + warning_count,
                "issue_density": (error_count + warning_count) / max(total_lines, 1)
            }

            # 改善提案を生成
            analysis["recommendations"] = self._generate_log_recommendations(analysis["patterns_found"])

            return analysis

        except Exception as e:
            logger.error(f"ログファイル解析エラー: {e}")
            return {"error": str(e)}

    def _generate_recommendation(self, check_name: str, status: str, message: str) -> Optional[str]:
        """チェック結果に基づく改善提案を生成"""
        recommendations = {
            "テストチェック": {
                "warn": "テストファイルの収集エラーを調査してください。pytest設定を確認し、テストディレクトリの構造を見直してください。",
                "fail": "テストの実行に失敗しています。テスト環境の設定と依存関係を確認してください。"
            },
            "構文チェック": {
                "warn": "構文エラーが検出されました。コードの構文を修正してください。",
                "fail": "重大な構文エラーがあります。コードの修正が必要です。"
            },
            "インポートチェック": {
                "warn": "インポートエラーが検出されました。依存関係とパス設定を確認してください。",
                "fail": "重要なモジュールのインポートに失敗しています。依存関係のインストールを確認してください。"
            },
            "依存関係チェック": {
                "warn": "依存関係の問題が検出されました。requirements.txtとパッケージバージョンを確認してください。",
                "fail": "依存関係の解決に失敗しています。パッケージマネージャーの設定を確認してください。"
            },
            "プロジェクト構造": {
                "warn": "プロジェクト構造に問題があります。ディレクトリ構造とファイル配置を確認してください。",
                "fail": "プロジェクト構造が不正です。基本的なディレクトリ構造を修正してください。"
            }
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
            recommendations.append("インポートエラーが検出されています。依存関係のインストールとパス設定を確認してください。")

        if patterns_found.get("permission_error"):
            recommendations.append("権限エラーが検出されています。ファイル権限とアクセス設定を確認してください。")

        if patterns_found.get("memory_error"):
            recommendations.append("メモリエラーが検出されています。メモリ使用量を最適化してください。")

        if patterns_found.get("coverage_error"):
            recommendations.append("カバレッジエラーが検出されています。カバレッジ設定とファイル生成を確認してください。")

        if patterns_found.get("qt_error"):
            recommendations.append("Qt関連のエラーが検出されています。Qt環境設定を確認してください。")

        if patterns_found.get("dependency_error"):
            recommendations.append("依存関係エラーが検出されています。パッケージマネージャーの設定とバージョン互換性を確認してください。")

        if patterns_found.get("build_error"):
            recommendations.append("ビルドエラーが検出されています。ビルド設定とコンパイラ設定を確認してください。")

        if patterns_found.get("network_error"):
            recommendations.append("ネットワークエラーが検出されています。ネットワーク設定とプロキシ設定を確認してください。")

        if patterns_found.get("security_error"):
            recommendations.append("セキュリティ問題が検出されています。セキュリティスキャンを実行し、脆弱性を修正してください。")

        if patterns_found.get("performance_issue"):
            recommendations.append("パフォーマンス問題が検出されています。コードの最適化とリソース使用量を確認してください。")

        if patterns_found.get("quality_issue"):
            recommendations.append("コード品質問題が検出されています。リンティングとコードスタイルを確認してください。")

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
            "quality_trends": [],
            "overall_quality_score": 0.0
        }

        # JSONレポートファイルを検索
        json_files = list(reports_dir.glob("ci_report_*.json"))
        analysis["total_reports"] = len(json_files)

        status_counts = {"pass": 0, "warn": 0, "fail": 0}
        all_issues = []
        all_recommendations = []
        quality_scores = []

        for json_file in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:  # 最新10件
            report_analysis = self.analyze_ci_report(json_file)

            if "error" not in report_analysis:
                status = report_analysis.get("overall_status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

                all_issues.extend(report_analysis.get("issues", []))
                all_recommendations.extend(report_analysis.get("recommendations", []))

                quality_score = report_analysis.get("quality_score", 0.0)
                quality_scores.append(quality_score)

                # 詳細なログ出力
                logger.info(f"解析完了: {json_file.name} - ステータス: {status} - 品質スコア: {quality_score:.1f}")
                if report_analysis.get("issues"):
                    logger.info(f"  問題: {len(report_analysis['issues'])}件")

        analysis["successful_reports"] = status_counts.get("pass", 0)
        analysis["warned_reports"] = status_counts.get("WARNING", 0)
        analysis["failed_reports"] = status_counts.get("fail", 0)

        # 品質スコアの計算
        if quality_scores:
            analysis["overall_quality_score"] = sum(quality_scores) / len(quality_scores)

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

    def generate_enhanced_report(self, analysis_results: Dict[str, Any]) -> str:
        """拡張された解析結果をレポート形式で出力"""
        report = []
        report.append("# Enhanced GitHub Actions AI 解析レポート")
        report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 概要
        report.append("## 📊 概要")
        report.append(f"- 総レポート数: {analysis_results.get('total_reports', 0)}")
        report.append(f"- 成功: {analysis_results.get('successful_reports', 0)}")
        report.append(f"- 警告: {analysis_results.get('warned_reports', 0)}")
        report.append(f"- 失敗: {analysis_results.get('failed_reports', 0)}")
        report.append(f"- 総合品質スコア: {analysis_results.get('overall_quality_score', 0.0):.1f}%")
        report.append("")

        # 品質メトリクス
        if analysis_results.get("overall_quality_score", 0) > 0:
            report.append("## 🎯 品質メトリクス")
            quality_score = analysis_results.get("overall_quality_score", 0.0)
            if quality_score >= 90:
                report.append(f"- **総合品質**: 🟢 優秀 ({quality_score:.1f}%)")
            elif quality_score >= 70:
                report.append(f"- **総合品質**: 🟡 良好 ({quality_score:.1f}%)")
            else:
                report.append(f"- **総合品質**: 🔴 要改善 ({quality_score:.1f}%)")
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

            if log_analysis.get("quality_metrics"):
                report.append("### 品質メトリクス")
                metrics = log_analysis["quality_metrics"]
                report.append(f"- エラー頻度: {metrics.get('error_frequency', 0):.2f} (1000行あたり)")
                report.append(f"- 警告頻度: {metrics.get('warning_frequency', 0):.2f} (1000行あたり)")
                report.append(f"- 総問題数: {metrics.get('total_issues', 0)}")
                report.append(f"- 問題密度: {metrics.get('issue_density', 0):.4f}")
                report.append("")

            if log_analysis.get("recommendations"):
                report.append("### ログ解析による改善提案")
                for i, recommendation in enumerate(log_analysis["recommendations"], 1):
                    report.append(f"{i}. {recommendation}")
                report.append("")

        # 自動改善アクション
        report.append("## 🤖 自動改善アクション")
        report.append("以下のアクションを自動的に実行することを推奨します：")
        report.append("")
        report.append("1. **テスト品質向上**: 失敗したテストの自動修正提案")
        report.append("2. **依存関係最適化**: 古いパッケージの自動更新")
        report.append("3. **コード品質改善**: リンティングエラーの自動修正")
        report.append("4. **パフォーマンス最適化**: ボトルネックの自動特定と修正")
        report.append("5. **セキュリティ強化**: 脆弱性の自動検出と修正")
        report.append("")

        return "\n".join(report)


def main():
    """メイン関数"""
    analyzer = EnhancedGitHubActionsAnalyzer()

    # レポートディレクトリ
    reports_dir = Path("reports")

    if not reports_dir.exists():
        logger.error("reportsディレクトリが見つかりません")
        sys.exit(1)

    # 複数レポートの解析
    logger.info("Enhanced GitHub Actionsレポートを解析中...")
    analysis_results = analyzer.analyze_multiple_reports(reports_dir)

    # CIシミュレーションログの解析
    logs_dir = Path("logs")
    if logs_dir.exists():
        logger.info("CIシミュレーションログを解析中...")
        ci_log_file = logs_dir / "ci-simulation.log"
        if ci_log_file.exists():
            log_analysis = analyzer.analyze_log_file(ci_log_file)
            analysis_results["log_analysis"] = log_analysis

    # 拡張レポート生成
    report = analyzer.generate_enhanced_report(analysis_results)

    # 結果を出力
    print(report)

    # ファイルに保存
    output_file = reports_dir / f"enhanced_ai_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"拡張解析レポートを保存しました: {output_file}")


if __name__ == "__main__":
    main()
