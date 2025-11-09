#!/usr/bin/env python3
"""
スタンドアロンAI統合ドキュメント生成ツール

依存関係の問題を回避して、独立してドキュメントを生成します。

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class AIContributor(Enum):
    """AI貢献者の種類"""

    COPILOT = "GitHub Copilot (CS4Coding)"
    CURSOR = "Cursor (CursorBLD)"
    KIRO = "Kiro"


@dataclass
class FileAnalysis:
    """ファイル分析結果"""

    file_path: Path
    primary_contributor: AIContributor
    purpose: str
    ai_mentions: list[str]
    imports: list[str]
    functions: list[str]


class StandaloneDocGenerator:
    """スタンドアロンドキュメント生成器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_analyses: list[FileAnalysis] = []

        # AI識別パターン
        self.ai_patterns = {
            AIContributor.COPILOT: [
                r"CS4Coding",
                r"GitHub Copilot",
                r"copilot",
                r"EXIF.*解析",
                r"folium",
                r"地図.*表示",
                r"高精度",
                r"安定.*実装",
            ],
            AIContributor.CURSOR: [
                r"CursorBLD",
                r"Cursor",
                r"cursor",
                r"Qt.*Theme",
                r"UI/UX",
                r"テーマ.*システム",
                r"サムネイル",
                r"グリッド",
            ],
            AIContributor.KIRO: [
                r"Kiro",
                r"統合",
                r"最適化",
                r"パフォーマンス",
                r"品質管理",
                r"アーキテクチャ",
                r"監視",
            ],
        }

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """ファイルを分析してAI貢献度を判定"""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = ""

        # AI言及を検索
        ai_mentions = []
        contributor_scores = dict.fromkeys(AIContributor, 0)

        for contributor, patterns in self.ai_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    ai_mentions.extend(matches)
                    contributor_scores[contributor] += len(matches)

        # 主要貢献者を決定
        primary_contributor = max(contributor_scores.items(), key=lambda x: x[1])[0]
        if contributor_scores[primary_contributor] == 0:
            # デフォルトはファイルパスから推測
            if "ui" in str(file_path).lower() or "theme" in str(file_path).lower():
                primary_contributor = AIContributor.CURSOR
            elif "integration" in str(file_path).lower():
                primary_contributor = AIContributor.KIRO
            else:
                primary_contributor = AIContributor.COPILOT

        # 目的を抽出
        purpose = self._extract_purpose(content)

        # インポートを抽出
        imports = self._extract_imports(content)

        # 関数を抽出
        functions = self._extract_functions(content)

        return FileAnalysis(
            file_path=file_path,
            primary_contributor=primary_contributor,
            purpose=purpose,
            ai_mentions=ai_mentions,
            imports=imports,
            functions=functions,
        )

    def _extract_purpose(self, content: str) -> str:
        """ファイルの目的を抽出"""
        lines = content.split("\n")

        # docstringから抽出
        in_docstring = False
        docstring_lines = []

        for line in lines[:20]:  # 最初の20行のみチェック
            stripped = line.strip()
            if '"""' in stripped:
                if in_docstring:
                    break
                else:
                    in_docstring = True
                    after_quotes = stripped.split('"""', 1)
                    if len(after_quotes) > 1 and after_quotes[1]:
                        docstring_lines.append(after_quotes[1])
            elif in_docstring:
                docstring_lines.append(stripped)

        if docstring_lines:
            return " ".join(docstring_lines[:2])  # 最初の2行

        return "目的不明"

    def _extract_imports(self, content: str) -> list[str]:
        """インポート文を抽出"""
        imports = []
        import_pattern = r"^(?:from\s+(\S+)\s+)?import\s+(.+)$"

        for line in content.split("\n"):
            line = line.strip()
            match = re.match(import_pattern, line)
            if match:
                module = match.group(1) or match.group(2).split(",")[0].strip()
                if not module.startswith("."):
                    imports.append(module)

        return list(set(imports))[:10]  # 重複除去、最大10個

    def _extract_functions(self, content: str) -> list[str]:
        """関数・メソッドを抽出"""
        functions = []
        function_pattern = r"def\s+(\w+)\s*\("

        for line in content.split("\n"):
            match = re.search(function_pattern, line.strip())
            if match:
                func_name = match.group(1)
                if not func_name.startswith("_"):  # プライベート関数は除外
                    functions.append(func_name)

        return functions[:10]  # 最大10個

    def scan_project(self) -> None:
        """プロジェクト全体をスキャン"""
        src_path = self.project_root / "src"
        if not src_path.exists():
            return

        for file_path in src_path.rglob("*.py"):
            if file_path.is_file():
                try:
                    analysis = self.analyze_file(file_path)
                    self.file_analyses.append(analysis)
                except Exception as e:
                    print(f"ファイル分析エラー {file_path}: {e}")

    def generate_api_documentation(self) -> str:
        """APIドキュメントを生成"""
        doc_lines = [
            "# PhotoGeoView AI統合 APIドキュメント",
            "",
            f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "",
            "## 概要",
            "",
            "PhotoGeoViewプロジェクトは複数のAIエージェントによって開発されました:",
            "- **GitHub Copilot (CS4Coding)**: コア機能実装、EXIF解析、地図表示",
            "- **Cursor (CursorBLD)**: UI/UX設計、テーマシステム、サムネイル表示",
            "- **Kiro**: 統合・品質管理、パフォーマンス最適化",
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

        for analysis in self.file_analyses:
            contributor_files[analysis.primary_contributor].append(analysis)

        for contributor, analyses in contributor_files.items():
            if analyses:
                doc_lines.append(f"### {contributor.value}")
                doc_lines.append("")

                for analysis in sorted(analyses, key=lambda x: x.file_path.name):
                    doc_lines.append(f"#### {analysis.file_path.name}")
                    doc_lines.append(f"**目的**: {analysis.purpose}")
                    doc_lines.append("")

                    if analysis.functions:
                        doc_lines.append("**主要関数**:")
                        for func in analysis.functions[:5]:
                            doc_lines.append(f"- `{func}()`")
                        doc_lines.append("")

                    if analysis.imports:
                        doc_lines.append("**主要依存関係**:")
                        for imp in analysis.imports[:3]:
                            doc_lines.append(f"- {imp}")
                        doc_lines.append("")

                    doc_lines.append("---")
                    doc_lines.append("")

        return "\n".join(doc_lines)

    def generate_contribution_report(self) -> str:
        """AI貢献度レポートを生成"""
        report_lines = [
            "# PhotoGeoView AI貢献度レポート",
            "",
            f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "",
            "## 概要",
            "",
            "このレポートは、PhotoGeoViewプロジェクトにおける各AIエージェントの貢献度を分析したものです。",
            "",
            "## AI貢献者統計",
            "",
        ]

        # 統計計算
        contributor_stats = {
            AIContributor.COPILOT: {"files": 0, "functions": 0},
            AIContributor.CURSOR: {"files": 0, "functions": 0},
            AIContributor.KIRO: {"files": 0, "functions": 0},
        }

        total_files = len(self.file_analyses)

        for analysis in self.file_analyses:
            contributor_stats[analysis.primary_contributor]["files"] += 1
            contributor_stats[analysis.primary_contributor]["functions"] += len(analysis.functions)

        for contributor, stats in contributor_stats.items():
            file_percentage = (stats["files"] / total_files * 100) if total_files > 0 else 0

            report_lines.extend(
                [
                    f"### {contributor.value}",
                    f"- **担当ファイル数**: {stats['files']} ({file_percentage:.1f}%)",
                    f"- **実装関数数**: {stats['functions']}",
                    "",
                ]
            )

        # ファイル別詳細
        report_lines.extend(["## ファイル別AI貢献詳細", ""])

        for analysis in sorted(self.file_analyses, key=lambda x: x.file_path.name):
            report_lines.extend(
                [
                    f"### {analysis.file_path.name}",
                    f"**主要貢献者**: {analysis.primary_contributor.value}",
                    f"**目的**: {analysis.purpose}",
                    f"**関数数**: {len(analysis.functions)}",
                    "",
                ]
            )

            if analysis.ai_mentions:
                report_lines.append("**AI言及**:")
                for mention in list(set(analysis.ai_mentions))[:3]:
                    report_lines.append(f"- {mention}")
                report_lines.append("")

        return "\n".join(report_lines)

    def generate_troubleshooting_guide(self) -> str:
        """トラブルシューティングガイドを生成"""
        guide_lines = [
            "# PhotoGeoView トラブルシューティングガイド",
            "",
            f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "",
            "## AI コンポーネント別問題解決",
            "",
            "### GitHub Copilot (CS4Coding) 関連の問題",
            "",
            "**対象モジュール**: コア機能、EXIF解析、地図表示",
            "",
        ]

        # CS4Coding関連ファイルを抽出
        copilot_files = [a for a in self.file_analyses if a.primary_contributor == AIContributor.COPILOT]
        if copilot_files:
            guide_lines.append("**関連ファイル**:")
            for analysis in copilot_files[:5]:
                guide_lines.append(f"- `{analysis.file_path.name}`: {analysis.purpose}")
            guide_lines.append("")

        guide_lines.extend(
            [
                "#### よくある問題:",
                "1. **EXIF情報が正しく読み取れない**",
                "   - 原因: 画像ファイルの破損またはEXIF情報の欠如",
                "   - 解決方法: ファイル形式と権限を確認",
                "",
                "2. **地図が表示されない**",
                "   - 原因: ネットワーク接続またはfolium統合の問題",
                "   - 解決方法: インターネット接続を確認",
                "",
                "### Cursor (CursorBLD) 関連の問題",
                "",
                "**対象モジュール**: UI/UX、テーマシステム、サムネイル表示",
                "",
            ]
        )

        # Cursor関連ファイルを抽出
        cursor_files = [a for a in self.file_analyses if a.primary_contributor == AIContributor.CURSOR]
        if cursor_files:
            guide_lines.append("**関連ファイル**:")
            for analysis in cursor_files[:5]:
                guide_lines.append(f"- `{analysis.file_path.name}`: {analysis.purpose}")
            guide_lines.append("")

        guide_lines.extend(
            [
                "#### よくある問題:",
                "1. **テーマが正しく適用されない**",
                "   - 原因: Qt-Theme-Managerの設定問題",
                "   - 解決方法: テーマファイルの存在を確認",
                "",
                "2. **サムネイルが表示されない**",
                "   - 原因: 画像処理ライブラリの問題",
                "   - 解決方法: Pillowライブラリを再インストール",
                "",
                "### Kiro 統合システム関連の問題",
                "",
                "**対象モジュール**: 統合制御、パフォーマンス監視、キャッシュシステム",
                "",
            ]
        )

        # Kiro関連ファイルを抽出
        kiro_files = [a for a in self.file_analyses if a.primary_contributor == AIContributor.KIRO]
        if kiro_files:
            guide_lines.append("**関連ファイル**:")
            for analysis in kiro_files[:5]:
                guide_lines.append(f"- `{analysis.file_path.name}`: {analysis.purpose}")
            guide_lines.append("")

        guide_lines.extend(
            [
                "#### よくある問題:",
                "1. **統合コンポーネント間の通信エラー**",
                "   - 原因: インターフェース不整合",
                "   - 解決方法: 設定ファイルを確認",
                "",
                "2. **パフォーマンス低下**",
                "   - 原因: キャッシュシステムの問題",
                "   - 解決方法: キャッシュをクリア",
                "",
                "## 緊急時の対応",
                "",
                "1. **アプリケーションが起動しない**",
                "   - 設定ファイルをリセット",
                "   - 依存関係を再インストール",
                "",
                "2. **データが失われた**",
                "   - バックアップから復元",
                "   - ログファイルを確認",
                "",
            ]
        )

        return "\n".join(guide_lines)

    def generate_all_documentation(self, output_dir: Path) -> None:
        """すべてのドキュメントを生成"""
        output_dir.mkdir(parents=True, exist_ok=True)

        print("プロジェクトをスキャン中...")
        self.scan_project()
        print(f"✓ {len(self.file_analyses)}個のファイルを分析しました")

        # APIドキュメント生成
        print("APIドキュメントを生成中...")
        api_doc = self.generate_api_documentation()
        (output_dir / "api_documentation.md").write_text(api_doc, encoding="utf-8")
        print("✓ APIドキュメントを生成しました")

        # 貢献度レポート生成
        print("AI貢献度レポートを生成中...")
        contribution_report = self.generate_contribution_report()
        (output_dir / "ai_contribution_report.md").write_text(contribution_report, encoding="utf-8")
        print("✓ AI貢献度レポートを生成しました")

        # トラブルシューティングガイド生成
        print("トラブルシューティングガイドを生成中...")
        troubleshooting_guide = self.generate_troubleshooting_guide()
        (output_dir / "troubleshooting_guide.md").write_text(troubleshooting_guide, encoding="utf-8")
        print("✓ トラブルシューティングガイドを生成しました")

        print(f"\n統合ドキュメントを生成しました: {output_dir}")


def main():
    """メイン実行関数"""
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "docs" / "ai_integration"

    print("PhotoGeoView AI統合ドキュメント生成ツール")
    print("=" * 50)

    generator = StandaloneDocGenerator(project_root)
    generator.generate_all_documentation(output_dir)


if __name__ == "__main__":
    main()
