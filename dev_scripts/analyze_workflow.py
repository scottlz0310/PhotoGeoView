#!/usr/bin/env python3
"""
GitHub Actions ログ分析スクリプト
失敗したワークフローのログを分析し、問題の特定と修正提案を行います
"""

import sys
from pathlib import Path

from github_actions_ai_analyzer import GitHubActionsAnalyzer


def main() -> None:
    """メイン関数"""
    log_file = Path("failed_steps_log.txt")

    if not log_file.exists():
        print(f"エラー: {log_file} が見つかりません")
        sys.exit(1)

    print("GitHub Actions ログ分析を開始します...")

    # アナライザーを初期化
    analyzer = GitHubActionsAnalyzer()

    # ログファイルを分析
    try:
        analysis_result = analyzer.analyze_log_file(str(log_file))
        print("\n=== 分析結果 ===")
        print(analysis_result)

    except Exception as e:
        print(f"分析中にエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
