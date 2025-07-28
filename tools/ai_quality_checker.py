#!/usr/bin/env python3
"""
AI統合品質チェッカー

各AIエージェントの開発基準に基づいた品質チェックを実行します。

AI貢献者:
- Kiro: 品質チェックシステム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json


class AIComponent(Enum):
    """AI コンポーネント"""
    COPILOT = "copilot"
    CURSOR = "cursor"
    KIRO = "kiro"


class QualityLevel(Enum):
    """品質レベル"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """品質問題"""
    file_path: Path
    line_number: int
    issue_type: str
    severity: QualityLevel
    message: str
    ai_component: AIComponent
    suggestion: str = ""


@dataclass
class QualityReport:
    """品質レポート"""
    total_files: int
    total_issues: int
    issues_by_severity: Dict[QualityLevel, int]
    issues_by_component: Dict[AIComponent, int]
    issues: List[QualityIssue]
    overall_score: float


class AIQualityChecker:
    """AI統合品質チェッカー"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[QualityIssue] = []

        # AI別品質基準
        self.quality_standards = {
            AIComponent.COPILOT: {
                'max_function_length': 50,
                'max_complexity': 10,
                'required_docstring': True,
                'required_type_hints': True,
                'error_handling_required': True,
                'performance_critical': True
            },
            AIComponent.CURSOR: {
                'max_function_length': 30,
                'max_complexity': 8,
                'required_docstring': True,
                'required_type_hints': False,
                'ui_consistency_required': True,
                'accessibility_required': True
            },
            AIComponent.KIRO: {
                'max_function_length': 40,
                'max_complexity': 12,
                'required_docstring': True,
                'required_type_hints': True,
                'integration_testing_required': True,
                'documentation_required': True
            }
        }

        # AI識別パターン
        self.ai_patterns = {
            AIComponent.COPILOT: [
                r'CS4Coding', r'GitHub Copilot', r'copilot',
                r'EXIF.*解析', r'folium', r'地図.*表示'
            ],
            AIComponent.CURSOR: [
                r'CursorBLD', r'Cursor', r'cursor',
                r'Qt.*Theme', r'UI/UX', r'テーマ.*システム'
            ],
            AIComponent.KIRO: [
                r'Kiro', r'統合', r'最適化', r'パフォーマンス'
            ]
        }

    def identify_ai_component(self, file_path: Path) -> AIComponent:
        """ファイルのAIコンポーネントを識別"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return AIComponent.KIRO  # デフォルト

        scores = {component: 0 for component in AIComponent}

        for component, patterns in self.ai_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                scores[component] += matches

        # ファイルパスからも推測
        file_str = str(file_path).lower()
        if 'ui' in file_str or 'theme' in file_str:
            scores[AIComponent.CURSOR] += 2
        elif 'integration' in file_str:
            scores[AIComponent.KIRO] += 2
        elif any(x in file_str for x in ['exif', 'map', 'image']):
            scores[AIComponent.COPILOT] += 2

        return max(scores.items(), key=lambda x: x[1])[0]

    def check_function_length(self, file_path: Path, tree: ast.AST, ai_component: AIComponent) -> None:
        """関数の長さをチェック"""
        max_length = self.quality_standards[ai_component]['max_function_length']

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_length = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0

                if func_length > max_length:
                    severity = QualityLevel.POOR if func_length > max_length * 1.5 else QualityLevel.ACCEPTABLE

                    self.issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="function_length",
                        severity=severity,
                        message=f"関数 '{node.name}' が長すぎます ({func_length}行, 推奨: {max_length}行以下)",
                        ai_component=ai_component,
                        suggestion=f"関数を小さな関数に分割することを検討してください"
                    ))

    def check_docstring_presence(self, file_path: Path, tree: ast.AST, ai_component: AIComponent) -> None:
        """docstringの存在をチェック"""
        if not self.quality_standards[ai_component]['required_docstring']:
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith('_'):  # プライベート関数は除外
                    has_docstring = (
                        node.body and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)
                    )

                    if not has_docstring:
                        self.issues.append(QualityIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="missing_docstring",
                            severity=QualityLevel.ACCEPTABLE,
                            message=f"{type(node).__name__} '{node.name}' にdocstringがありません",
                            ai_component=ai_component,
                            suggestion="適切なdocstringを追加してください"
                        ))

    def check_type_hints(self, file_path: Path, tree: ast.AST, ai_component: AIComponent) -> None:
        """型ヒントの存在をチェック"""
        if not self.quality_standards[ai_component]['required_type_hints']:
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_'):  # プライベート関数は除外
                    # 引数の型ヒントをチェック
                    for arg in node.args.args:
                        if arg.annotation is None and arg.arg != 'self':
                            self.issues.append(QualityIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                issue_type="missing_type_hint",
                                severity=QualityLevel.ACCEPTABLE,
                                message=f"関数 '{node.name}' の引数 '{arg.arg}' に型ヒントがありません",
                                ai_component=ai_component,
                                suggestion="型ヒントを追加してください"
                            ))

                    # 戻り値の型ヒントをチェック
                    if node.returns is None:
                        self.issues.append(QualityIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="missing_return_type",
                            severity=QualityLevel.ACCEPTABLE,
                            message=f"関数 '{node.name}' に戻り値の型ヒントがありません",
                            ai_component=ai_component,
                            suggestion="戻り値の型ヒントを追加してください"
                        ))

    def check_error_handling(self, file_path: Path, tree: ast.AST, ai_component: AIComponent) -> None:
        """エラーハンドリングをチェック"""
        if not self.quality_standards[ai_component].get('error_handling_required', False):
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_try_except = any(isinstance(child, ast.Try) for child in ast.walk(node))

                # ファイル操作や外部API呼び出しがある場合はエラーハンドリングが必要
                has_risky_operations = any(
                    isinstance(child, ast.Call) and
                    isinstance(child.func, ast.Attribute) and
                    child.func.attr in ['open', 'read', 'write', 'request', 'get', 'post']
                    for child in ast.walk(node)
                )

                if has_risky_operations and not has_try_except:
                    self.issues.append(QualityIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="missing_error_handling",
                        severity=QualityLevel.POOR,
                        message=f"関数 '{node.name}' にエラーハンドリングがありません",
                        ai_component=ai_component,
                        suggestion="try-except文を使用してエラーハンドリングを追加してください"
                    ))

    def check_ui_consistency(self, file_path: Path, content: str, ai_component: AIComponent) -> None:
        """UI一貫性をチェック（Cursor専用）"""
        if ai_component != AIComponent.CURSOR:
            return

        # Qt関連のチェック
        if 'PyQt' in content or 'PySide' in content:
            # テーマ適用の確認
            if 'setStyleSheet' in content and 'theme' not in content.lower():
                self.issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="ui_consistency",
                    severity=QualityLevel.ACCEPTABLE,
                    message="スタイルシートを直接設定していますが、テーマシステムの使用を検討してください",
                    ai_component=ai_component,
                    suggestion="統一されたテーマシステムを使用してください"
                ))

    def check_integration_quality(self, file_path: Path, content: str, ai_component: AIComponent) -> None:
        """統合品質をチェック（Kiro専用）"""
        if ai_component != AIComponent.KIRO:
            return

        # ログ使用の確認
        if 'print(' in content:
            print_lines = [i+1 for i, line in enumerate(content.split('\n')) if 'print(' in line]
            for line_num in print_lines:
                self.issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type="improper_logging",
                    severity=QualityLevel.POOR,
                    message="print文の代わりにloggingを使用してください",
                    ai_component=ai_component,
                    suggestion="logging.info() または適切なログレベルを使用してください"
                ))

        # AI統合パターンの確認
        if 'integration' in str(file_path).lower():
            ai_mentions = sum(1 for pattern_list in self.ai_patterns.values()
                            for pattern in pattern_list
                            if re.search(pattern, content, re.IGNORECASE))

            if ai_mentions < 2:
                self.issues.append(QualityIssue(
                    file_path=file_path,
                    line_number=1,
                    issue_type="insufficient_ai_integration",
                    severity=QualityLevel.ACCEPTABLE,
                    message="統合ファイルでAI言及が不足しています",
                    ai_component=ai_component,
                    suggestion="複数のAIコンポーネントとの統合を明確にしてください"
                ))

    def check_file(self, file_path: Path) -> None:
        """単一ファイルの品質をチェック"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.issues.append(QualityIssue(
                file_path=file_path,
                line_number=1,
                issue_type="file_read_error",
                severity=QualityLevel.CRITICAL,
                message=f"ファイル読み込みエラー: {e}",
                ai_component=AIComponent.KIRO,
                suggestion="ファイルのエンコーディングと権限を確認してください"
            ))
            return

        # AIコンポーネントを識別
        ai_component = self.identify_ai_component(file_path)

        # ASTパース
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.issues.append(QualityIssue(
                file_path=file_path,
                line_number=e.lineno or 1,
                issue_type="syntax_error",
                severity=QualityLevel.CRITICAL,
                message=f"構文エラー: {e.msg}",
                ai_component=ai_component,
                suggestion="構文エラーを修正してください"
            ))
            return

        # 各種チェックを実行
        self.check_function_length(file_path, tree, ai_component)
        self.check_docstring_presence(file_path, tree, ai_component)
        self.check_type_hints(file_path, tree, ai_component)
        self.check_error_handling(file_path, tree, ai_component)
        self.check_ui_consistency(file_path, content, ai_component)
        self.check_integration_quality(file_path, content, ai_component)

    def check_project(self) -> QualityReport:
        """プロジェクト全体の品質をチェック"""
        src_path = self.project_root / 'src'
        python_files = list(src_path.rglob('*.py')) if src_path.exists() else []

        for file_path in python_files:
            self.check_file(file_path)

        # 統計を計算
        issues_by_severity = {level: 0 for level in QualityLevel}
        issues_by_component = {component: 0 for component in AIComponent}

        for issue in self.issues:
            issues_by_severity[issue.severity] += 1
            issues_by_component[issue.ai_component] += 1

        # 総合スコアを計算（100点満点）
        severity_weights = {
            QualityLevel.CRITICAL: -20,
            QualityLevel.POOR: -10,
            QualityLevel.ACCEPTABLE: -3,
            QualityLevel.GOOD: 0,
            QualityLevel.EXCELLENT: 5
        }

        total_score = 100
        for issue in self.issues:
            total_score += severity_weights[issue.severity]

        overall_score = max(0, min(100, total_score))

        return QualityReport(
            total_files=len(python_files),
            total_issues=len(self.issues),
            issues_by_severity=issues_by_severity,
            issues_by_component=issues_by_component,
            issues=self.issues,
            overall_score=overall_score
        )

    def generate_report(self, report: QualityReport, output_path: Optional[Path] = None) -> str:
        """品質レポートを生成"""
        report_lines = [
            "# PhotoGeoView AI統合品質レポート",
            "",
            f"生成日時: {Path(__file__).stat().st_mtime}",
            "",
            "## 概要",
            "",
            f"- **総ファイル数**: {report.total_files}",
            f"- **総問題数**: {report.total_issues}",
            f"- **総合スコア**: {report.overall_score:.1f}/100",
            "",
            "## 重要度別問題数",
            ""
        ]

        for severity, count in report.issues_by_severity.items():
            if count > 0:
                report_lines.append(f"- **{severity.value}**: {count}件")

        report_lines.extend([
            "",
            "## AI コンポーネント別問題数",
            ""
        ])

        for component, count in report.issues_by_component.items():
            if count > 0:
                report_lines.append(f"- **{component.value}**: {count}件")

        if report.issues:
            report_lines.extend([
                "",
                "## 詳細問題一覧",
                ""
            ])

            for issue in sorted(report.issues, key=lambda x: (x.severity.value, str(x.file_path))):
                report_lines.extend([
                    f"### {issue.file_path.name}:{issue.line_number}",
                    f"- **重要度**: {issue.severity.value}",
                    f"- **タイプ**: {issue.issue_type}",
                    f"- **AI コンポーネント**: {issue.ai_component.value}",
                    f"- **問題**: {issue.message}",
                    f"- **提案**: {issue.suggestion}",
                    ""
                ])

        report_content = "\n".join(report_lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content, encoding='utf-8')

        return report_content


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='AI統合品質チェッカー')
    parser.add_argument('--output', '-o', type=Path, help='出力ファイルパス')
    parser.add_argument('--json', action='store_true', help='JSON形式で出力')
    parser.add_argument('--fail-on-critical', action='store_true', help='重大な問題がある場合は終了コード1で終了')

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    checker = AIQualityChecker(project_root)

    print("AI統合品質チェックを実行中...")
    report = checker.check_project()

    if args.json:
        # JSON出力
        json_data = {
            'total_files': report.total_files,
            'total_issues': report.total_issues,
            'overall_score': report.overall_score,
            'issues_by_severity': {k.value: v for k, v in report.issues_by_severity.items()},
            'issues_by_component': {k.value: v for k, v in report.issues_by_component.items()},
            'issues': [
                {
                    'file_path': str(issue.file_path),
                    'line_number': issue.line_number,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity.value,
                    'message': issue.message,
                    'ai_component': issue.ai_component.value,
                    'suggestion': issue.suggestion
                }
                for issue in report.issues
            ]
        }

        output = json.dumps(json_data, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output, encoding='utf-8')
        else:
            print(output)
    else:
        # Markdown出力
        output = checker.generate_report(report, args.output)
        if not args.output:
            print(output)

    print(f"\n品質チェック完了:")
    print(f"  ファイル数: {report.total_files}")
    print(f"  問題数: {report.total_issues}")
    print(f"  総合スコア: {report.overall_score:.1f}/100")

    # 重大な問題がある場合の終了処理
    if args.fail_on_critical and report.issues_by_severity[QualityLevel.CRITICAL] > 0:
        print(f"重大な問題が {report.issues_by_severity[QualityLevel.CRITICAL]} 件見つかりました")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
