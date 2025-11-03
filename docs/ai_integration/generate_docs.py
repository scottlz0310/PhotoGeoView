#!/usr/bin/env python3
"""
AI統合ドキュメント生成スクリプト

PhotoGeoViewプロジェクトの統合ドキュメントを自動生成します。

使用方法:
    python generate_docs.py [--update-headers] [--output-dir OUTPUT_DIR]

作成者: Kiro AI統合システム
作成日: 2025年1月26日
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.integration.documentation_system import DocumentationSystem


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="PhotoGeoView AI統合ドキュメント生成ツール"
    )

    parser.add_argument(
        "--update-headers", action="store_true", help="ファイルヘッダーを更新する"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "docs" / "ai_integration",
        help="出力ディレクトリ（デフォルト: docs/ai_integration）",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="実際の変更は行わず、処理内容のみ表示"
    )

    args = parser.parse_args()

    print("PhotoGeoView AI統合ドキュメント生成ツール")
    print("=" * 50)

    # ドキュメントシステム初期化
    doc_system = DocumentationSystem(project_root)

    # 統合ドキュメント生成
    print(f"出力ディレクトリ: {args.output_dir}")

    if not args.dry_run:
        doc_system.generate_integration_documentation(args.output_dir)
        print("✓ 統合ドキュメントを生成しました")
    else:
        print("（dry-run モード: 実際の生成は行いません）")

    # ファイルヘッダー更新
    if args.update_headers:
        print("\nファイルヘッダーを更新中...")
        updated_files = doc_system.update_file_headers(dry_run=args.dry_run)

        if updated_files:
            print(f"✓ {len(updated_files)}個のファイルを更新しました:")
            for file_path in updated_files[:10]:  # 最初の10個のみ表示
                print(f"  - {file_path.relative_to(project_root)}")

            if len(updated_files) > 10:
                print(f"  ... 他 {len(updated_files) - 10}個のファイル")
        else:
            print("更新対象のファイルがありませんでした")

    print("\n処理完了!")


if __name__ == "__main__":
    main()
