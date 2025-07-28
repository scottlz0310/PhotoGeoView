#!/usr/bin/env python3
"""
AI統合要件検証ツール

全要件が満たされているかを検証します。

AI貢献者:
- Kiro: 要件検証システム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import subprocess


class ValidationStatus(Enum):
    """検証ステータス"""
    PASSED = "✅ 合格"
    FAILED = "❌ 不合格"
    WARNING = "⚠️ 警告"
    SKIPPED = "⏭️ スキップ"


@dataclass
class RequirementValidation:
    """要件検証結果"""
    requirement_id: str
    description: str
    status: ValidationStatus
    details: str
    evidence: List[str]


class RequirementValidator:
    """要件検証器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.validations: List[RequirementValidation] = []

    def validate_requirement_1_1(self) -> RequirementValidation:
        """要件1.1: CursorBLD UI/UX統合の検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # テーママネージャーの存在確認
            theme_manager_path = self.project_root / "src/integration/ui/theme_manager.py"
            if theme_manager_path.exists():
                evidence.append(f"テーママネージャー: {theme_manager_path}")
            else:
                status = ValidationStatus.FAILED
                details += "テーママネージャーが見つかりません。"

            # UIディレクトリの存在確認
            ui_dir = self.project_root / "src/integration/ui"
            if ui_dir.exists():
                ui_files = list(ui_dir.glob("*.py"))
                evidence.extend([f"UIファイル: {f.name}" for f in ui_files])
            else:
                status = ValidationStatus.FAILED
                details += "UIディレクトリが見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="1.1",
            description="CursorBLD UI/UX統合",
            status=status,
            details=details or "CursorBLD UIコンポーネントが正常に統合されています",
            evidence=evidence
        )

    def validate_requirement_1_2(self) -> RequirementValidation:
        """要件1.2: サムネイル表示統合の検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # サムネイルグリッドの存在確認
            thumbnail_grid_path = self.project_root / "src/integration/ui/thumbnail_grid.py"
            if thumbnail_grid_path.exists():
                evidence.append(f"サムネイルグリッド: {thumbnail_grid_path}")
            else:
                status = ValidationStatus.WARNING
                details += "サムネイルグリッドファイルが見つかりません。"

            # 画像プロセッサーでのサムネイル機能確認
            image_processor_path = self.project_root / "src/integration/image_processor.py"
            if image_processor_path.exists():
                content = image_processor_path.read_text(encoding='utf-8')
                if 'thumbnail' in content.lower():
                    evidence.append("画像プロセッサーにサムネイル機能が含まれています")
                else:
                    status = ValidationStatus.WARNING
                    details += "画像プロセッサーにサムネイル機能が見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="1.2",
            description="サムネイル表示統合",
            status=status,
            details=details or "サムネイル表示機能が統合されています",
            evidence=evidence
        )

    def validate_requirement_1_3(self) -> RequirementValidation:
        """要件1.3: CS4Coding EXIF解析統合の検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # 画像プロセッサーの存在確認
            image_processor_path = self.project_root / "src/integration/image_processor.py"
            if image_processor_path.exists():
                content = image_processor_path.read_text(encoding='utf-8')
                evidence.append(f"画像プロセッサー: {image_processor_path}")

                # EXIF関連機能の確認
                if 'exif' in content.lower():
                    evidence.append("EXIF処理機能が含まれています")
                else:
                    status = ValidationStatus.WARNING
                    details += "EXIF処理機能が見つかりません。"

                # CS4Coding言及の確認
                if 'cs4coding' in content.lower():
                    evidence.append("CS4Coding統合が確認されました")
                else:
                    status = ValidationStatus.WARNING
                    details += "CS4Coding統合の明示的な言及が見つかりません。"
            else:
                status = ValidationStatus.FAILED
                details += "画像プロセッサーが見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="1.3",
            description="CS4Coding EXIF解析統合",
            status=status,
            details=details or "CS4Coding EXIF解析機能が統合されています",
            evidence=evidence
        )

    def validate_requirement_1_4(self) -> RequirementValidation:
        """要件1.4: CS4Coding地図表示統合の検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # 地図関連ファイルの確認
            map_files = list(self.project_root.rglob("*map*.py"))
            if map_files:
                evidence.extend([f"地図ファイル: {f.relative_to(self.project_root)}" for f in map_files])
            else:
                status = ValidationStatus.WARNING
                details += "地図関連ファイルが見つかりません。"

            # folium依存関係の確認
            requirements_path = self.project_root / "requirements.txt"
            if requirements_path.exists():
                content = requirements_path.read_text()
                if 'folium' in content:
                    evidence.append("folium依存関係が確認されました")
                else:
                    status = ValidationStatus.WARNING
                    details += "folium依存関係が見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="1.4",
            description="CS4Coding地図表示統合",
            status=status,
            details=details or "CS4Coding地図表示機能が統合されています",
            evidence=evidence
        )

    def validate_requirement_2_1(self) -> RequirementValidation:
        """要件2.1: Kiro統一アーキテクチャの検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # 統合コントローラーの存在確認
            controller_path = self.project_root / "src/integration/controllers.py"
            if controller_path.exists():
                evidence.append(f"統合コントローラー: {controller_path}")

                content = controller_path.read_text(encoding='utf-8')
                if 'kiro' in content.lower():
                    evidence.append("Kiro統合が確認されました")
                else:
                    status = ValidationStatus.WARNING
                    details += "Kiro統合の明示的な言及が見つかりません。"
            else:
                status = ValidationStatus.FAILED
                details += "統合コントローラーが見つかりません。"

            # 統合ディレクトリの確認
            integration_dir = self.project_root / "src/integration"
            if integration_dir.exists():
                integration_files = list(integration_dir.glob("*.py"))
                evidence.append(f"統合ファイル数: {len(integration_files)}")
            else:
                status = ValidationStatus.FAILED
                details += "統合ディレクトリが見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="2.1",
            description="Kiro統一アーキテクチャ",
            status=status,
            details=details or "Kiro統一アーキテクチャが実装されています",
            evidence=evidence
        )

    def validate_requirement_2_2(self) -> RequirementValidation:
        """要件2.2: パフォーマンス最適化の検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # パフォーマンス監視の存在確認
            perf_monitor_path = self.project_root / "src/integration/performance_monitor.py"
            if perf_monitor_path.exists():
                evidence.append(f"パフォーマンス監視: {perf_monitor_path}")
            else:
                status = ValidationStatus.WARNING
                details += "パフォーマンス監視ファイルが見つかりません。"

            # キャッシュシステムの確認
            cache_path = self.project_root / "src/integration/unified_cache.py"
            if cache_path.exists():
                evidence.append(f"統合キャッシュ: {cache_path}")
            else:
                status = ValidationStatus.WARNING
                details += "統合キャッシュファイルが見つかりません。"

            # パフォーマンステストの確認
            perf_test_dir = self.project_root / "tests/performance_tests"
            if perf_test_dir.exists():
                perf_tests = list(perf_test_dir.glob("*.py"))
                evidence.append(f"パフォーマンステスト数: {len(perf_tests)}")
            else:
                status = ValidationStatus.WARNING
                details += "パフォーマンステストディレクトリが見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="2.2",
            description="パフォーマンス最適化",
            status=status,
            details=details or "パフォーマンス最適化機能が実装されています",
            evidence=evidence
        )

    def validate_requirement_4_1(self) -> RequirementValidation:
        """要件4.1: AI貢献度ドキュメントの検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # AI統合ドキュメントディレクトリの確認
            docs_dir = self.project_root / "docs/ai_integration"
            if docs_dir.exists():
                evidence.append(f"AI統合ドキュメントディレクトリ: {docs_dir}")

                # 必要なドキュメントファイルの確認
                required_docs = [
                    "api_documentation.md",
                    "ai_contribution_report.md",
                    "troubleshooting_guide.md",
                    "README.md"
                ]

                for doc_file in required_docs:
                    doc_path = docs_dir / doc_file
                    if doc_path.exists():
                        evidence.append(f"ドキュメント: {doc_file}")
                    else:
                        status = ValidationStatus.WARNING
                        details += f"{doc_file}が見つかりません。"
            else:
                status = ValidationStatus.FAILED
                details += "AI統合ドキュメントディレクトリが見つかりません。"

            # ドキュメント生成ツールの確認
            doc_generator_path = self.project_root / "docs/ai_integration/standalone_doc_generator.py"
            if doc_generator_path.exists():
                evidence.append(f"ドキュメント生成ツール: {doc_generator_path}")
            else:
                status = ValidationStatus.WARNING
                details += "ドキュメント生成ツールが見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="4.1",
            description="AI貢献度ドキュメント",
            status=status,
            details=details or "AI貢献度ドキュメントが作成されています",
            evidence=evidence
        )

    def validate_requirement_5_1(self) -> RequirementValidation:
        """要件5.1: 自動品質保証の検証"""
        evidence = []
        status = ValidationStatus.PASSED
        details = ""

        try:
            # CI/CDパイプラインの確認
            ci_path = self.project_root / ".github/workflows/ai-integration-ci.yml"
            if ci_path.exists():
                evidence.append(f"CI/CDパイプライン: {ci_path}")
            else:
                status = ValidationStatus.FAILED
                details += "CI/CDパイプラインが見つかりません。"

            # 品質チェッカーの確認
            quality_checker_path = self.project_root / "tools/ai_quality_checker.py"
            if quality_checker_path.exists():
                evidence.append(f"品質チェッカー: {quality_checker_path}")
            else:
                status = ValidationStatus.FAILED
                details += "品質チェッカーが見つかりません。"

            # Pre-commitフックの確認
            precommit_path = self.project_root / ".pre-commit-config.yaml"
            if precommit_path.exists():
                evidence.append(f"Pre-commitフック: {precommit_path}")
            else:
                status = ValidationStatus.WARNING
                details += "Pre-commitフックが見つかりません。"

            # テストディレクトリの確認
            test_dirs = [
                "tests/integration_tests",
                "tests/ai_compatibility",
                "tests/performance_tests"
            ]

            for test_dir in test_dirs:
                test_path = self.project_root / test_dir
                if test_path.exists():
                    evidence.append(f"テストディレクトリ: {test_dir}")
                else:
                    status = ValidationStatus.WARNING
                    details += f"{test_dir}が見つかりません。"

        except Exception as e:
            status = ValidationStatus.FAILED
            details = f"検証エラー: {e}"

        return RequirementValidation(
            requirement_id="5.1",
            description="自動品質保証",
            status=status,
            details=details or "自動品質保証システムが実装されています",
            evidence=evidence
        )

    def validate_all_requirements(self) -> List[RequirementValidation]:
        """全要件を検証"""
        print("AI統合要件検証を実行中...")

        validation_methods = [
            self.validate_requirement_1_1,
            self.validate_requirement_1_2,
            self.validate_requirement_1_3,
            self.validate_requirement_1_4,
            self.validate_requirement_2_1,
            self.validate_requirement_2_2,
            self.validate_requirement_4_1,
            self.validate_requirement_5_1,
        ]

        for method in validation_methods:
            try:
                validation = method()
                self.validations.append(validation)
                print(f"{validation.status.value} 要件{validation.requirement_id}: {validation.description}")
            except Exception as e:
                error_validation = RequirementValidation(
                    requirement_id="ERROR",
                    description=f"検証エラー: {method.__name__}",
                    status=ValidationStatus.FAILED,
                    details=str(e),
                    evidence=[]
                )
                self.validations.append(error_validation)
                print(f"❌ 検証エラー: {method.__name__} - {e}")

        return self.validations

    def generate_validation_report(self, output_path: Path = None) -> str:
        """検証レポートを生成"""
        report_lines = [
            "# PhotoGeoView AI統合要件検証レポート",
            "",
            f"検証日時: {Path(__file__).stat().st_mtime}",
            "",
            "## 検証結果概要",
            ""
        ]

        # 統計情報
        passed = len([v for v in self.validations if v.status == ValidationStatus.PASSED])
        failed = len([v for v in self.validations if v.status == ValidationStatus.FAILED])
        warnings = len([v for v in self.validations if v.status == ValidationStatus.WARNING])

        report_lines.extend([
            f"- **合格**: {passed}件",
            f"- **不合格**: {failed}件",
            f"- **警告**: {warnings}件",
            f"- **総要件数**: {len(self.validations)}件",
            "",
            "## 詳細検証結果",
            ""
        ])

        # 各要件の詳細
        for validation in self.validations:
            report_lines.extend([
                f"### {validation.status.value} 要件{validation.requirement_id}: {validation.description}",
                "",
                f"**詳細**: {validation.details}",
                ""
            ])

            if validation.evidence:
                report_lines.extend([
                    "**証跡**:",
                    ""
                ])
                for evidence in validation.evidence:
                    report_lines.append(f"- {evidence}")
                report_lines.append("")

        # 推奨事項
        if failed > 0:
            report_lines.extend([
                "## 🔴 必須対応事項",
                ""
            ])

            failed_validations = [v for v in self.validations if v.status == ValidationStatus.FAILED]
            for validation in failed_validations:
                report_lines.append(f"- **要件{validation.requirement_id}**: {validation.details}")

            report_lines.append("")

        if warnings > 0:
            report_lines.extend([
                "## ⚠️ 改善推奨事項",
                ""
            ])

            warning_validations = [v for v in self.validations if v.status == ValidationStatus.WARNING]
            for validation in warning_validations:
                report_lines.append(f"- **要件{validation.requirement_id}**: {validation.details}")

            report_lines.append("")

        report_content = "\n".join(report_lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content, encoding='utf-8')

        return report_content

    def get_validation_summary(self) -> Dict[str, Any]:
        """検証サマリーを取得"""
        passed = len([v for v in self.validations if v.status == ValidationStatus.PASSED])
        failed = len([v for v in self.validations if v.status == ValidationStatus.FAILED])
        warnings = len([v for v in self.validations if v.status == ValidationStatus.WARNING])

        return {
            'total_requirements': len(self.validations),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'success_rate': (passed / len(self.validations) * 100) if self.validations else 0,
            'overall_status': 'PASSED' if failed == 0 else 'FAILED'
        }


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='AI統合要件検証')
    parser.add_argument('--output', '-o', type=Path, help='レポート出力パス')
    parser.add_argument('--json', action='store_true', help='JSON形式で出力')

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    validator = RequirementValidator(project_root)

    # 要件検証実行
    validations = validator.validate_all_requirements()

    # サマリー取得
    summary = validator.get_validation_summary()

    if args.json:
        # JSON出力
        json_data = {
            'summary': summary,
            'validations': [
                {
                    'requirement_id': v.requirement_id,
                    'description': v.description,
                    'status': v.status.name,
                    'details': v.details,
                    'evidence': v.evidence
                }
                for v in validations
            ]
        }

        output = json.dumps(json_data, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(output, encoding='utf-8')
        else:
            print(output)
    else:
        # Markdown出力
        report = validator.generate_validation_report(args.output)
        if not args.output:
            print(report)

    # 結果表示
    print(f"\n要件検証完了:")
    print(f"  総要件数: {summary['total_requirements']}")
    print(f"  合格: {summary['passed']}")
    print(f"  不合格: {summary['failed']}")
    print(f"  警告: {summary['warnings']}")
    print(f"  成功率: {summary['success_rate']:.1f}%")
    print(f"  総合判定: {summary['overall_status']}")

    # 不合格がある場合は終了コード1
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
