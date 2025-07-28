"""
AI統合ドキュメントテンプレートシステム

統一されたドキュメント形式を提供するテンプレートシステム

AI貢献者:
- Kiro: テンプレートシステム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import logging


@dataclass
class DocumentTemplate:
    """ドキュメントテンプレート"""
    name: str
    template: str
    variables: List[str]
    description: str


class DocumentTemplateManager:
    """ドキュメントテンプレート管理システム"""

    def __init__(self):
        self.templates = self._load_default_templates()

    def _load_default_templates(self) -> Dict[str, DocumentTemplate]:
        """デフォルトテンプレートを読み込み"""
        templates = {}

        # ファイルヘッダーテンプレート
        templates['file_header'] = DocumentTemplate(
            name='file_header',
            template='''"""
{file_name} - {purpose}

{description}

AI貢献者情報:
主要開発者: {primary_contributor}

{contributor_details}

{dependencies_section}

{api_section}

最終更新: {last_updated}
作成者: {author}
"""''',
            variables=[
                'file_name', 'purpose', 'description', 'primary_contributor',
                'contributor_details', 'dependencies_section', 'api_section',
                'last_updated', 'author'
            ],
            description='Pythonファイル用のヘッダーテンプレート'
        )

        # APIドキュメントテンプレート
        templates['api_doc'] = DocumentTemplate(
            name='api_doc',
            template='''# {project_name} API ドキュメント

生成日時: {generation_date}

## 概要

{project_description}

## AI貢献者

{ai_contributors}

## モジュール一覧

{modules_list}

## 詳細API

{api_details}

---
*このドキュメントは自動生成されました*''',
            variables=[
                'project_name', 'generation_date', 'project_description',
                'ai_contributors', 'modules_list', 'api_details'
            ],
            description='統合APIドキュメントテンプレート'
        )

        # トラブルシューティングテンプレート
        templates['troubleshooting'] = DocumentTemplate(
            name='troubleshooting',
            template='''# {project_name} トラブルシューティングガイド

生成日時: {generation_date}

## 概要

{overview}

## AI コンポーネント別問題解決

{ai_component_sections}

## 一般的な問題と解決方法

{common_issues}

## 診断ツール

{diagnostic_tools}

## 緊急時の対応

{emergency_procedures}

---
*このガイドは自動生成されました*''',
            variables=[
                'project_name', 'generation_date', 'overview',
                'ai_component_sections', 'common_issues', 'diagnostic_tools',
                'emergency_procedures'
            ],
            description='トラブルシューティングガイドテンプレート'
        )

        # 貢献度レポートテンプレート
        templates['contribution_report'] = DocumentTemplate(
            name='contribution_report',
            template='''# {project_name} AI貢献度レポート

生成日時: {generation_date}

## プロジェクト概要

{project_overview}

## AI貢献者統計

{contributor_statistics}

## 貢献タイプ別分析

{contribution_type_analysis}

## ファイル別詳細

{file_details}

## 品質メトリクス

{quality_metrics}

## 推奨事項

{recommendations}

---
*このレポートは自動生成されました*''',
            variables=[
                'project_name', 'generation_date', 'project_overview',
                'contributor_statistics', 'contribution_type_analysis',
                'file_details', 'quality_metrics', 'recommendations'
            ],
            description='AI貢献度レポートテンプレート'
        )

        return templates

    def get_template(self, template_name: str) -> DocumentTemplate:
        """テンプレートを取得"""
        if template_name not in self.templates:
            raise ValueError(f"テンプレート '{template_name}' が見つかりません")
        return self.templates[template_name]

    def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """テンプレートをレンダリング"""
        template = self.get_template(template_name)

        # 必要な変数がすべて提供されているかチェック
        missing_vars = set(template.variables) - set(variables.keys())
        if missing_vars:
            # 不足している変数にデフォルト値を設定
            for var in missing_vars:
                variables[var] = f"[{var}未設定]"

        try:
            return template.template.format(**variables)
        except KeyError as e:
            raise ValueError(f"テンプレート変数エラー: {e}")

    def add_custom_template(self, template: DocumentTemplate) -> None:
        """カスタムテンプレートを追加"""
        self.templates[template.name] = template

    def list_templates(self) -> List[str]:
        """利用可能なテンプレート一覧を取得"""
        return list(self.templates.keys())

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """テンプレート情報を取得"""
        template = self.get_template(template_name)
        return {
            'name': template.name,
            'description': template.description,
            'variables': template.variables,
            'template_preview': template.template[:200] + '...' if len(template.template) > 200 else template.template
        }


class AIAttributionFormatter:
    """AI貢献度情報のフォーマッター"""

    @staticmethod
    def format_contributor_details(contributions: List[Any]) -> str:
        """貢献者詳細をフォーマット"""
        if not contributions:
            return "貢献情報なし"

        contributor_groups = {}
        for contrib in contributions:
            if contrib.contributor not in contributor_groups:
                contributor_groups[contrib.contributor] = []
            contributor_groups[contrib.contributor].append(contrib)

        details = []
        for contributor, contribs in contributor_groups.items():
            details.append(f"{contributor.value}:")

            # 貢献タイプ別にグループ化
            type_groups = {}
            for contrib in contribs:
                if contrib.contribution_type not in type_groups:
                    type_groups[contrib.contribution_type] = []
                type_groups[contrib.contribution_type].append(contrib)

            for contrib_type, type_contribs in type_groups.items():
                details.append(f"  - {contrib_type.value} ({len(type_contribs)}件)")

        return "\n".join(details)

    @staticmethod
    def format_dependencies_section(dependencies: List[str]) -> str:
        """依存関係セクションをフォーマット"""
        if not dependencies:
            return ""

        section = ["主要依存関係:"]
        for dep in dependencies[:5]:  # 最初の5つのみ
            section.append(f"  - {dep}")

        if len(dependencies) > 5:
            section.append(f"  ... 他 {len(dependencies) - 5}個")

        return "\n".join(section)

    @staticmethod
    def format_api_section(api_endpoints: List[str]) -> str:
        """APIセクションをフォーマット"""
        if not api_endpoints:
            return ""

        section = ["公開API:"]
        for endpoint in api_endpoints[:5]:  # 最初の5つのみ
            section.append(f"  - {endpoint}()")

        if len(api_endpoints) > 5:
            section.append(f"  ... 他 {len(api_endpoints) - 5}個")

        return "\n".join(section)

    @staticmethod
    def format_ai_contributors_section() -> str:
        """AI貢献者セクションをフォーマット"""
        return """- **GitHub Copilot (CS4Coding)**: コア機能実装、EXIF解析、地図表示
- **Cursor (CursorBLD)**: UI/UX設計、テーマシステム、サムネイル表示
- **Kiro**: 統合・品質管理、パフォーマンス最適化、ドキュメント生成"""


# 使用例
def example_usage():
    """テンプレートシステムの使用例"""
    template_manager = DocumentTemplateManager()
    formatter = AIAttributionFormatter()

    # ファイルヘッダーの生成例
    variables = {
        'file_name': 'example.py',
        'purpose': 'サンプルファイル',
        'description': 'テンプレートシステムの使用例を示すファイル',
        'primary_contributor': 'Kiro',
        'contributor_details': formatter.format_ai_contributors_section(),
        'dependencies_section': formatter.format_dependencies_section(['os', 'sys', 'pathlib']),
        'api_section': formatter.format_api_section(['main', 'process_data', 'generate_report']),
        'last_updated': datetime.now().strftime("%Y年%m月%d日"),
        'author': 'Kiro AI統合システム'
    }

    header = template_manager.render_template('file_header', variables)

    logger = logging.getLogger(__name__)
    logger.info("ファイルヘッダーテンプレートを生成しました")
    print("生成されたファイルヘッダー:")
    print(header)


if __name__ == "__main__":
    example_usage()
