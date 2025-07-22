"""
詳細なテーマアクセシビリティ分析結果表示ツール
"""

import sys
import json
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.theme_accessibility import analyze_all_themes


def display_detailed_analysis():
    """詳細な分析結果を表示"""
    config_path = Path(__file__).parent.parent / "config" / "theme_styles.json"
    results = analyze_all_themes(config_path)

    if "error" in results:
        print(f"エラー: {results['error']}")
        return

    analysis_results = results["analysis_results"]
    summary = results["summary"]

    print("=" * 60)
    print("テーマアクセシビリティ詳細分析結果")
    print("=" * 60)

    # サマリー表示
    print(f"\n📊 分析サマリー:")
    print(f"   総テーマ数: {summary['total_themes']}")
    print(f"   高アクセシビリティ(80点以上): {summary['good_accessibility_count']} ({summary['accessibility_percentage']}%)")
    print(f"   ゼブラスタイル問題あり: {summary['poor_zebra_count']}テーマ")

    # 各テーマの詳細
    print(f"\n📋 テーマ別詳細結果 (スコア順):")
    print("-" * 60)

    for theme_name, analysis in analysis_results.items():
        score = analysis.get("accessibility_score", 0)
        main_contrast = analysis.get("main_contrast", 0)
        zebra_min = analysis.get("zebra_analysis", {}).get("min_contrast", 0)

        # スコアに基づく評価アイコン
        if score >= 90:
            icon = "🟢"
        elif score >= 80:
            icon = "🟡"
        elif score >= 60:
            icon = "🟠"
        else:
            icon = "🔴"

        print(f"{icon} {theme_name:12} | スコア: {score:3d}点 | メイン: {main_contrast:.1f} | ゼブラ: {zebra_min:.1f}")

        # WCAG準拠状況
        wcag = analysis.get("wcag_compliance", {})
        compliance_status = []
        if wcag.get("aa_normal"):
            compliance_status.append("AA準拠")
        if not wcag.get("zebra_readable"):
            compliance_status.append("ゼブラ問題")

        if compliance_status:
            print(f"   └─ {' | '.join(compliance_status)}")

        # 改善提案がある場合
        recommendations = analysis.get("recommendations", [])
        if "アクセシビリティは良好です" not in recommendations:
            print(f"   └─ 改善案: {'; '.join(recommendations)}")

    # 問題のあるテーマの詳細
    print(f"\n⚠️  アクセシビリティ問題のあるテーマ詳細:")
    print("-" * 60)

    problem_themes = [(name, data) for name, data in analysis_results.items()
                     if data.get("accessibility_score", 0) < 80]

    if not problem_themes:
        print("問題のあるテーマはありません！")
    else:
        for theme_name, analysis in problem_themes:
            print(f"\n🔍 {theme_name}テーマ:")

            # 色情報表示
            zebra = analysis.get("zebra_analysis", {})
            print(f"   メインコントラスト: {analysis.get('main_contrast', 0):.2f}")
            print(f"   ゼブラ基準色: {zebra.get('base', 'N/A')} (コントラスト: {zebra.get('base_contrast', 0):.2f})")
            print(f"   ゼブラ交互色: {zebra.get('alternate', 'N/A')} (コントラスト: {zebra.get('alternate_contrast', 0):.2f})")

            # 改善提案
            recommendations = analysis.get("recommendations", [])
            for i, rec in enumerate(recommendations, 1):
                print(f"   改善案{i}: {rec}")

    # 推奨テーマ
    print(f"\n✅ 推奨高アクセシビリティテーマ:")
    print("-" * 60)

    good_themes = [(name, data) for name, data in analysis_results.items()
                   if data.get("accessibility_score", 0) >= 80]

    for theme_name, analysis in good_themes:
        score = analysis.get("accessibility_score", 0)
        print(f"   🌟 {theme_name:12} (スコア: {score}点)")


if __name__ == "__main__":
    display_detailed_analysis()
