"""
AI統合ドキュメントシステム

PhotoGeoViewプロジェクトにおける複数AI開発成果の統合ドキュメント管理システム
各AIエージェントの貢献度を追跡し、統一されたドキュメントを生成します。

AI貢献者:
- GitHub Copilot (CS4Coding): コア機能実装
- Cursor (CursorBLD): UI/UX設計
- Kiro: 統合・品質管理・ドキュメント生成

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime
from enum import Enum
import json
import ast
import re
import logging


class AIContributor(Enum):
    """AI貢献者の種類"""

    COPILOT = "GitHub Copilot (CS4Coding)"
    CURSOR = "Cursor (CursorBLD)"
    KIRO = "Kiro"


class ContributionType(Enum):
    """貢献の種類"""

    CORE_FUNCTIONALITY = "コア機能"
    UI_UX_DESIGN = "UI/UX設計"
    INTEGRATION = "統合・最適化"
    TESTING = "テスト"
    DOCUMENTATION = "ドキュメント"
    ARCHITECTURE = "アーキテクチャ設計"


@dataclass
class AIContribution:
    """AI貢献情報"""

    contributor: AIContributor
    contribution_type: ContributionType
    description: str
    file_path: Path
    line_range: Optional[tuple] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # 貢献度の確信度 (0.0-1.0)


@dataclass
class FileDocumentation:
    """ファイルドキュメント情報"""

    file_path: Path
    primary_contributor: AIContributor
    contributions: List[AIContribution]
    purpose: str
    dependencies: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class DocumentationSystem:
    """
    AI統合ドキュメントシステム

    各AIエージェントの貢献を追跡し、統一されたドキュメントを生成します。
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.contributions: Dict[str, List[AIContribution]] = {}
        self.file_docs: Dict[str, FileDocumentation] = {}
        self.ai_attribution_patterns = self._load_attribution_patterns()

    def _load_attribution_patterns(self) -> Dict[AIContributor, List[str]]:
        """AI貢献者を識別するパターンを定義"""
        return {
            AIContributor.COPILOT: [
                r"CS4Coding",
                r"GitHub Copilot",
                r"copilot",
                r"高精度.*EXIF",
                r"folium.*統合",
                r"安定.*地図表示",
            ],
            AIContributor.CURSOR: [
                r"CursorBLD",
                r"Cursor",
                r"cursor",
                r"Qt.*Theme.*Manager",
                r"UI/UX",
                r"テーマ.*システム",
                r"サムネイル.*グリッド",
            ],
            AIContributor.KIRO: [
                r"Kiro",
                r"統合",
                r"最適化",
                r"パフォーマンス",
                r"品質管理",
                r"アーキテクチャ",
            ],
        }

    def analyze_file_contributions(self, file_path: Path) -> FileDocumentation:
        """
        ファイルのAI貢献度を分析

        Args:
            file_path: 分析対象ファイルのパス

        Returns:
            ファイルドキュメント情報
        """
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        contributions = self._extract_contributions_from_content(content, file_path)

        # 主要貢献者を決定
        primary_contributor = self._determine_primary_contributor(contributions)

        # ファイルの目的を抽出
        purpose = self._extract_file_purpose(content)

        # 依存関係を抽出
        dependencies = self._extract_dependencies(content)

        # APIエンドポイントを抽出
        api_endpoints = self._extract_api_endpoints(content)

        file_doc = FileDocumentation(
            file_path=file_path,
            primary_contributor=primary_contributor,
            contributions=contributions,
            purpose=purpose,
            dependencies=dependencies,
            api_endpoints=api_endpoints,
        )

        self.file_docs[str(file_path)] = file_doc
        return file_doc

    def _extract_contributions_from_content(
        self, content: str, file_path: Path
    ) -> List[AIContribution]:
        """コンテンツからAI貢献を抽出"""
        contributions = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            for contributor, patterns in self.ai_attribution_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        contribution_type = self._classify_contribution_type(
                            line, file_path
                        )

                        contribution = AIContribution(
                            contributor=contributor,
                            contribution_type=contribution_type,
                            description=line.strip(),
                            file_path=file_path,
                            line_range=(i + 1, i + 1),
                            confidence=self._calculate_confidence(pattern, line),
                        )
                        contributions.append(contribution)
                        break

        return contributions

    def _determine_primary_contributor(
        self, contributions: List[AIContribution]
    ) -> AIContributor:
        """主要貢献者を決定"""
        if not contributions:
            return AIContributor.KIRO  # デフォルト

        # 貢献度の重み付け計算
        contributor_scores = {}
        for contrib in contributions:
            score = contributor_scores.get(contrib.contributor, 0)
            contributor_scores[contrib.contributor] = score + contrib.confidence

        return max(contributor_scores.items(), key=lambda x: x[1])[0]

    def _classify_contribution_type(
        self, line: str, file_path: Path
    ) -> ContributionType:
        """貢献の種類を分類"""
        line_lower = line.lower()
        file_name = file_path.name.lower()

        if "ui" in line_lower or "theme" in line_lower or "ui" in file_name:
            return ContributionType.UI_UX_DESIGN
        elif "test" in line_lower or "test" in file_name:
            return ContributionType.TESTING
        elif "doc" in line_lower or "documentation" in line_lower:
            return ContributionType.DOCUMENTATION
        elif "integration" in line_lower or "統合" in line_lower:
            return ContributionType.INTEGRATION
        elif "architecture" in line_lower or "アーキテクチャ" in line_lower:
            return ContributionType.ARCHITECTURE
        else:
            return ContributionType.CORE_FUNCTIONALITY

    def _calculate_confidence(self, pattern: str, line: str) -> float:
        """パターンマッチの確信度を計算"""
        # より具体的なパターンほど高い確信度
        if len(pattern) > 10:
            return 0.9
        elif len(pattern) > 5:
            return 0.7
        else:
            return 0.5

    def _extract_file_purpose(self, content: str) -> str:
        """ファイルの目的を抽出"""
        lines = content.split("\n")

        # docstringから目的を抽出
        in_docstring = False
        docstring_lines = []

        for line in lines:
            stripped = line.strip()
            if '"""' in stripped:
                if in_docstring:
                    break
                else:
                    in_docstring = True
                    # 同じ行にdocstringの内容がある場合
                    after_quotes = stripped.split('"""', 1)
                    if len(after_quotes) > 1 and after_quotes[1]:
                        docstring_lines.append(after_quotes[1])
            elif in_docstring:
                docstring_lines.append(stripped)

        if docstring_lines:
            return " ".join(docstring_lines[:3])  # 最初の3行を使用

        return "目的不明"

    def _extract_dependencies(self, content: str) -> List[str]:
        """依存関係を抽出"""
        dependencies = []

        # import文を解析
        import_pattern = r"^(?:from\s+(\S+)\s+)?import\s+(.+)$"

        for line in content.split("\n"):
            line = line.strip()
            match = re.match(import_pattern, line)
            if match:
                module = match.group(1) or match.group(2).split(",")[0].strip()
                if not module.startswith("."):  # 相対importは除外
                    dependencies.append(module)

        return list(set(dependencies))  # 重複除去

    def _extract_api_endpoints(self, content: str) -> List[str]:
        """APIエンドポイントを抽出"""
        endpoints = []

        # クラスメソッドを検索
        class_method_pattern = r"def\s+(\w+)\s*\("

        for line in content.split("\n"):
            match = re.search(class_method_pattern, line.strip())
            if match:
                method_name = match.group(1)
                if not method_name.startswith("_"):  # プライベートメソッドは除外
                    endpoints.append(method_name)

        return endpoints

    def generate_file_header(self, file_path: Path) -> str:
        """
        ファイルヘッダーにAI貢献度情報を生成

        Args:
            file_path: 対象ファイルのパス

        Returns:
            AI貢献度情報を含むヘッダー文字列
        """
        file_doc = self.analyze_file_contributions(file_path)

        header_lines = [
            '"""',
            f"{file_path.name} - {file_doc.purpose}",
            "",
            "AI貢献者情報:",
            f"主要開発者: {file_doc.primary_contributor.value}",
            "",
        ]

        # 貢献者別の詳細情報
        contributor_details = {}
        for contrib in file_doc.contributions:
            if contrib.contributor not in contributor_details:
                contributor_details[contrib.contributor] = []
            contributor_details[contrib.contributor].append(contrib)

        for contributor, contribs in contribls.items():
            header_lines.append(f"{contributor.value}:")
            contribution_types = set(c.contribution_type for c in contribs)
            for contrib_type in contribution_types:
                header_lines.append(f"  - {contrib_type.value}")
            header_lines.append("")

        # 依存関係情報
        if file_doc.dependencies:
            header_lines.append("主要依存関係:")
            for dep in file_doc.dependencies[:5]:  # 最初の5つのみ表示
                header_lines.append(f"  - {dep}")
            header_lines.append("")

        # APIエンドポイント情報
        if file_doc.api_endpoints:
            header_lines.append("公開API:")
            for endpoint in file_doc.api_endpoints[:5]:  # 最初の5つのみ表示
                header_lines.append(f"  - {endpoint}()")
            header_lines.append("")

        header_lines.extend(
            [f'最終更新: {file_doc.last_updated.strftime("%Y年%m月%d日")}', '"""', ""]
        )

        return "\n".join(header_lines)

    def generate_unified_api_documentation(self) -> str:
        """
        統合APIドキュメントを生成

        Returns:
            統合APIドキュメントの文字列
        """
        doc_lines = [
            "# PhotoGeoView AI統合 APIドキュメント",
            "",
            f'生成日時: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}',
            "",
            "## 概要",
            "",
            "PhotoGeoViewプロジェクトは複数のAIエージェントによって開発されました:",
            "- **GitHub Copilot (CS4Coding)**: コア機能実装",
            "- **Cursor (CursorBLD)**: UI/UX設計",
            "- **Kiro**: 統合・品質管理",
            "",
            "## AI貢献者別モジュール",
            "",
        ]

        # AI貢献者別にファイルを分類
        contributor_files = {
            AIContributor.COPILOT: [],
            AIContributor.CURSOR: [],
            AIContributor.KIRO: [],
        }

        for file_doc in self.file_docs.values():
            contributor_files[file_doc.primary_contributor].append(file_doc)

        for contributor, files in contributor_files.items():
            if files:
                doc_lines.append(f"### {contributor.value}")
                doc_lines.append("")

                for file_doc in sorted(files, key=lambda x: x.file_path.name):
                    doc_lines.append(f"#### {file_doc.file_path.name}")
                    doc_lines.append(f"**目的**: {file_doc.purpose}")
                    doc_lines.append("")

                    if file_doc.api_endpoints:
                        doc_lines.append("**公開API**:")
                        for endpoint in file_doc.api_endpoints:
                            doc_lines.append(f"- `{endpoint}()`")
                        doc_lines.append("")

                    if file_doc.dependencies:
                        doc_lines.append("**主要依存関係**:")
                        for dep in file_doc.dependencies[:3]:
                            doc_lines.append(f"- {dep}")
                        doc_lines.append("")

                    doc_lines.append("---")
                    doc_lines.append("")

        return "\n".join(doc_lines)

    def generate_troubleshooting_guide(self) -> str:
        """
        AI コンポーネント識別付きトラブルシューティングガイドを生成

        Returns:
            トラブルシューティングガイドの文字列
        """
        guide_lines = [
            "# PhotoGeoView トラブルシューティングガイド",
            "",
            f'生成日時: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}',
            "",
            "## AI コンポーネント別問題解決",
            "",
            "### GitHub Copilot (CS4Coding) 関連の問題",
            "",
            "**対象モジュール**: コア機能、EXIF解析、地図表示",
            "",
            "#### よくある問題:",
            "1. **EXIF情報が正しく読み取れない**",
            "   - 原因: 画像ファイルの破損またはEXIF情報の欠如",
            "   - 解決方法: `exif_parser.py`のエラーハンドリングを確認",
            "   - 関連ファイル: `src/modules/exif_parser.py`",
            "",
            "2. **地図が表示されない**",
            "   - 原因: folium統合の問題またはネットワーク接続",
            "   - 解決方法: `map_viewer.py`の接続設定を確認",
            "   - 関連ファイル: `src/modules/map_viewer.py`",
            "",
            "3. **画像読み込みエラー**",
            "   - 原因: サポートされていない画像形式",
            "   - 解決方法: `image_loader.py`の対応形式を確認",
            "   - 関連ファイル: `src/modules/image_loader.py`",
            "",
            "### Cursor (CursorBLD) 関連の問題",
            "",
            "**対象モジュール**: UI/UX、テーマシステム、サムネイル表示",
            "",
            "#### よくある問題:",
            "1. **テーマが正しく適用されない**",
            "   - 原因: Qt-Theme-Managerの設定問題",
            "   - 解決方法: `theme_manager.py`の設定を確認",
            "   - 関連ファイル: `src/ui/theme_manager.py`",
            "",
            "2. **サムネイルが表示されない**",
            "   - 原因: サムネイル生成の失敗",
            "   - 解決方法: `thumbnail_generator.py`のキャッシュを確認",
            "   - 関連ファイル: `src/modules/thumbnail_generator.py`",
            "",
            "3. **UI レスポンスが遅い**",
            "   - 原因: 大量画像の同期処理",
            "   - 解決方法: 非同期処理の設定を確認",
            "   - 関連ファイル: `src/ui/main_window.py`",
            "",
            "### Kiro 統合システム関連の問題",
            "",
            "**対象モジュール**: 統合制御、パフォーマンス監視、キャッシュシステム",
            "",
            "#### よくある問題:",
            "1. **統合コンポーネント間の通信エラー**",
            "   - 原因: インターフェース不整合",
            "   - 解決方法: `controllers.py`の統合設定を確認",
            "   - 関連ファイル: `src/integration/controllers.py`",
            "",
            "2. **パフォーマンス低下**",
            "   - 原因: キャッシュシステムの問題",
            "   - 解決方法: `unified_cache.py`の設定を確認",
            "   - 関連ファイル: `src/integration/unified_cache.py`",
            "",
            "3. **ログ出力の問題**",
            "   - 原因: ログシステムの設定ミス",
            "   - 解決方法: `logging_system.py`の設定を確認",
            "   - 関連ファイル: `src/integration/logging_system.py`",
            "",
            "## 診断コマンド",
            "",
            "### システム状態確認",
            "```python",
            "from src.integration.controllers import AppController",
            "from src.integration.performance_monitor import KiroPerformanceMonitor",
            "",
            "# アプリケーション状態確認",
            "controller = AppController()",
            "status = controller.get_system_status()",
            'print(f"システム状態: {status}")',
            "",
            "# パフォーマンス監視",
            "monitor = KiroPerformanceMonitor()",
            "metrics = monitor.get_current_metrics()",
            'print(f"パフォーマンス: {metrics}")',
            "```",
            "",
            "### ログ確認",
            "```bash",
            "# エラーログ確認",
            "tail -f logs/error.log",
            "",
            "# 統合ログ確認",
            "tail -f logs/integration.log",
            "",
            "# パフォーマンスログ確認",
            "tail -f logs/performance.log",
            "```",
            "",
            "## 緊急時の対応",
            "",
            "1. **アプリケーションが起動しない**",
            "   - 設定ファイルをリセット: `config/app_config.json`を削除",
            "   - キャッシュをクリア: `cache/`フォルダを削除",
            "   - 依存関係を再インストール: `pip install -r requirements.txt`",
            "",
            "2. **データが失われた**",
            "   - バックアップから復元: `state/backup/`を確認",
            "   - ログから操作履歴を確認: `logs/user_activity.log`",
            "",
            "3. **パフォーマンスが著しく低下**",
            "   - メモリ使用量確認: タスクマネージャーでPythonプロセスを確認",
            "   - キャッシュサイズ確認: `cache/`フォルダのサイズを確認",
            "   - 一時的な解決: アプリケーションを再起動",
            "",
        ]

        return "\n".join(guide_lines)

    def scan_project_files(self, extensions: List[str] = None) -> None:
        """
        プロジェクト全体のファイルをスキャンしてドキュメント情報を収集

        Args:
            extensions: スキャン対象の拡張子リスト（デフォルト: ['.py']）
        """
        if extensions is None:
            extensions = [".py"]

        src_path = self.project_root / "src"
        if not src_path.exists():
            return

        for file_path in src_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    self.analyze_file_contributions(file_path)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    error_msg = f"ファイル分析エラー {file_path}: {e}"
                    logger.error(error_msg)
                    print(error_msg)  # ユーザーへの進行状況表示

    def generate_integration_documentation(self, output_dir: Path) -> None:
        """
        統合ドキュメントを生成してファイルに出力

        Args:
            output_dir: 出力ディレクトリ
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # プロジェクトファイルをスキャン
        self.scan_project_files()

        # APIドキュメント生成
        api_doc = self.generate_unified_api_documentation()
        (output_dir / "api_documentation.md").write_text(api_doc, encoding="utf-8")

        # トラブルシューティングガイド生成
        troubleshooting_guide = self.generate_troubleshooting_guide()
        (output_dir / "troubleshooting_guide.md").write_text(
            troubleshooting_guide, encoding="utf-8"
        )

        # AI貢献度レポート生成
        contribution_report = self._generate_contribution_report()
        (output_dir / "ai_contribution_report.md").write_text(
            contribution_report, encoding="utf-8"
        )

        logger = logging.getLogger(__name__)
        success_msg = f"統合ドキュメントを生成しました: {output_dir}"
        logger.info(success_msg)
        print(success_msg)  # ユーザーへの完了通知

    def _generate_contribution_report(self) -> str:
        """AI貢献度レポートを生成"""
        report_lines = [
            "# PhotoGeoView AI貢献度レポート",
            "",
            f'生成日時: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}',
            "",
            "## 概要",
            "",
            "このレポートは、PhotoGeoViewプロジェクトにおける各AIエージェントの貢献度を分析したものです。",
            "",
            "## AI貢献者統計",
            "",
        ]

        # 貢献者別統計
        contributor_stats = {}
        total_contributions = 0

        for file_doc in self.file_docs.values():
            for contrib in file_doc.contributions:
                if contrib.contributor not in contributor_stats:
                    contributor_stats[contrib.contributor] = {
                        "count": 0,
                        "types": set(),
                        "files": set(),
                    }

                contributor_stats[contrib.contributor]["count"] += 1
                contributor_stats[contrib.contributor]["types"].add(
                    contrib.contribution_type
                )
                contributor_stats[contrib.contributor]["files"].add(
                    str(contrib.file_path)
                )
                total_contributions += 1

        for contributor, stats in contributor_stats.items():
            percentage = (
                (stats["count"] / total_contributions * 100)
                if total_contributions > 0
                else 0
            )

            report_lines.extend(
                [
                    f"### {contributor.value}",
                    f'- **貢献数**: {stats["count"]} ({percentage:.1f}%)',
                    f'- **対象ファイル数**: {len(stats["files"])}',
                    f'- **貢献タイプ**: {", ".join([t.value for t in stats["types"]])}',
                    "",
                ]
            )

        # ファイル別詳細
        report_lines.extend(["## ファイル別AI貢献詳細", ""])

        for file_path, file_doc in sorted(self.file_docs.items()):
            report_lines.extend(
                [
                    f"### {Path(file_path).name}",
                    f"**主要貢献者**: {file_doc.primary_contributor.value}",
                    f"**目的**: {file_doc.purpose}",
                    "",
                ]
            )

            if file_doc.contributions:
                report_lines.append("**貢献詳細**:")
                for contrib in file_doc.contributions:
                    report_lines.append(
                        f"- {contrib.contributor.value}: {contrib.contribution_type.value}"
                    )
                report_lines.append("")

        return "\n".join(report_lines)

    def update_file_headers(self, dry_run: bool = True) -> List[Path]:
        """
        プロジェクト内のファイルヘッダーを更新

        Args:
            dry_run: True の場合、実際の更新は行わず対象ファイルのリストのみ返す

        Returns:
            更新対象ファイルのリスト
        """
        updated_files = []

        for file_path_str, file_doc in self.file_docs.items():
            file_path = Path(file_path_str)

            if not file_path.exists():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                new_header = self.generate_file_header(file_path)

                # 既存のヘッダーを検出して置換
                if content.startswith('"""'):
                    # 既存のdocstringを見つけて置換
                    end_pos = content.find('"""', 3)
                    if end_pos != -1:
                        new_content = new_header + content[end_pos + 3 :]
                    else:
                        new_content = new_header + content
                else:
                    # ヘッダーを先頭に追加
                    new_content = new_header + content

                if not dry_run:
                    file_path.write_text(new_content, encoding="utf-8")

                updated_files.append(file_path)

            except Exception as e:
                logger = logging.getLogger(__name__)
                error_msg = f"ファイルヘッダー更新エラー {file_path}: {e}"
                logger.error(error_msg)
                print(error_msg)  # ユーザーへのエラー通知

        return updated_files


# 使用例とテスト用の関数
def main():
    """ドキュメントシステムのテスト実行"""
    project_root = Path(__file__).parent.parent.parent
    doc_system = DocumentationSystem(project_root)

    # ドキュメント生成
    output_dir = project_root / "docs" / "ai_integration"
    doc_system.generate_integration_documentation(output_dir)

    # ファイルヘッダー更新（dry run）
    updated_files = doc_system.update_file_headers(dry_run=True)

    logger = logging.getLogger(__name__)
    update_msg = f"更新対象ファイル数: {len(updated_files)}"
    logger.info(update_msg)
    print(update_msg)  # ユーザーへの結果表示


if __name__ == "__main__":
    main()
