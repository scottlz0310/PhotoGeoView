#!/usr/bin/env python3
"""
Git Hooks Setup Script for PhotoGeoView

Gitフックの設定と管理を行うスクリプト
"""

import os
import shutil
import stat
from pathlib import Path


def setup_hooks():
    """Gitフックをセットアップ"""
    project_root = Path.cwd()
    hooks_dir = project_root / ".git" / "hooks"

    if not hooks_dir.exists():
        print("❌ .git/hooks ディレクトリが見つかりません")
        print("   Gitリポジトリのルートで実行してください")
        return False

    # pre-commit フック
    pre_commit_content = """#!/bin/sh
# PhotoGeoView Simple CI Pre-commit Hook
# Updated for simple CI system

echo "🔍 Running CI checks before commit..."

# Check if we're in the right directory
if [ ! -f "ci.py" ]; then
    echo "❌ ci.py not found. Please run from project root."
    exit 1
fi

# Get list of staged files for targeted checking
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|yml|yaml|json|md)$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "ℹ️  No relevant files staged for commit. Skipping CI checks."
    exit 0
fi

echo "📁 Checking staged files: $(echo $STAGED_FILES | wc -w) files"

# Run simple CI with timeout
echo "⏳ Running CI checks (timeout: 120s)..."
timeout 120 python ci.py --no-report

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ CI checks timed out after 120 seconds"
    echo "💡 Consider running checks manually: python ci.py"
    exit 1
elif [ $EXIT_CODE -ne 0 ]; then
    echo "❌ CI checks failed. Commit aborted."
    echo "💡 Run 'python ci.py' for detailed results"
    echo "💡 Use 'git commit --no-verify' to bypass this check (not recommended)"
    exit 1
fi

echo "✅ CI checks passed. Proceeding with commit."
exit 0"""

    # pre-push フック
    pre_push_content = """#!/bin/sh
# PhotoGeoView Simple CI Pre-push Hook
# Updated for simple CI system

echo "🚀 Running comprehensive CI checks before push..."

# Check if we're in the right directory
if [ ! -f "ci.py" ]; then
    echo "❌ ci.py not found. Please run from project root."
    exit 1
fi

# Get information about what's being pushed
remote="$1"
url="$2"

echo "📡 Pushing to: $remote ($url)"

# Read from stdin to get the refs being pushed
while read local_ref local_sha remote_ref remote_sha; do
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        # Branch is being deleted, skip checks
        echo "🗑️  Branch deletion detected, skipping CI checks"
        continue
    fi

    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch, check all commits
        range="$local_sha"
        echo "🆕 New branch detected"
    else
        # Existing branch, check new commits
        range="$remote_sha..$local_sha"
        echo "📝 Checking new commits: $range"
    fi

    # Get list of changed files in the push
    CHANGED_FILES=$(git diff --name-only "$range" | grep -E '\\.(py|yml|yaml|json|md)$' || true)

    if [ -n "$CHANGED_FILES" ]; then
        echo "📁 Files changed in push: $(echo $CHANGED_FILES | wc -w) files"
        break
    fi
done

# Run comprehensive CI checks with timeout
echo "⏳ Running full CI checks (timeout: 300s)..."
timeout 300 python ci.py --format json

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ CI checks timed out after 300 seconds"
    echo "💡 Consider running checks manually: python ci.py"
    exit 1
elif [ $EXIT_CODE -ne 0 ]; then
    echo "❌ CI checks failed. Push aborted."
    echo "💡 Run 'python ci.py' for detailed results"
    echo "💡 Use 'git push --no-verify' to bypass this check (not recommended)"
    exit 1
fi

echo "✅ CI checks passed. Proceeding with push."
exit 0"""

    # フックファイルを作成
    hooks = [("pre-commit", pre_commit_content), ("pre-push", pre_push_content)]

    for hook_name, content in hooks:
        hook_file = hooks_dir / hook_name

        # バックアップを作成（既存ファイルがある場合）
        if hook_file.exists():
            backup_file = hooks_dir / f"{hook_name}.backup"
            shutil.copy2(hook_file, backup_file)
            print(f"📋 既存の{hook_name}をバックアップ: {backup_file}")

        # 新しいフックファイルを作成
        with open(hook_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 実行権限を付与
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

        print(f"✅ {hook_name} フックを設定しました")

    print("\n🎉 Gitフックのセットアップが完了しました！")
    print("\n📝 使用方法:")
    print("  • git commit 時に自動的にCI チェックが実行されます")
    print("  • git push 時に包括的なCI チェックが実行されます")
    print("  • --no-verify オプションでフックをスキップできます")

    return True


def remove_hooks():
    """Gitフックを削除"""
    project_root = Path.cwd()
    hooks_dir = project_root / ".git" / "hooks"

    hooks_to_remove = ["pre-commit", "pre-push"]

    for hook_name in hooks_to_remove:
        hook_file = hooks_dir / hook_name
        if hook_file.exists():
            hook_file.unlink()
            print(f"🗑️  {hook_name} フックを削除しました")

        # バックアップがあれば復元
        backup_file = hooks_dir / f"{hook_name}.backup"
        if backup_file.exists():
            shutil.move(backup_file, hook_file)
            print(f"📋 {hook_name} のバックアップを復元しました")

    print("✅ Gitフックの削除が完了しました")


def status_hooks():
    """Gitフックの状態を確認"""
    project_root = Path.cwd()
    hooks_dir = project_root / ".git" / "hooks"

    if not hooks_dir.exists():
        print("❌ .git/hooks ディレクトリが見つかりません")
        return

    print("📋 Gitフックの状態:")
    print("=" * 40)

    hooks_to_check = ["pre-commit", "pre-push"]

    for hook_name in hooks_to_check:
        hook_file = hooks_dir / hook_name

        if hook_file.exists():
            # ファイルの内容をチェック
            with open(hook_file, encoding="utf-8") as f:
                content = f.read()

            if "PhotoGeoView Simple CI" in content:
                print(f"✅ {hook_name}: 設定済み (Simple CI)")
            elif "PhotoGeoView CI Simulation" in content:
                print(f"⚠️  {hook_name}: 古い設定 (要更新)")
            else:
                print(f"❓ {hook_name}: カスタム設定")

            # 実行権限をチェック
            if os.access(hook_file, os.X_OK):
                print("   実行権限: ✅")
            else:
                print("   実行権限: ❌")
        else:
            print(f"❌ {hook_name}: 未設定")

        # バックアップファイルの確認
        backup_file = hooks_dir / f"{hook_name}.backup"
        if backup_file.exists():
            print("   バックアップ: 📋 あり")


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="PhotoGeoView Git Hooks Setup")
    parser.add_argument("action", choices=["setup", "remove", "status"], help="実行するアクション")

    args = parser.parse_args()

    if args.action == "setup":
        setup_hooks()
    elif args.action == "remove":
        remove_hooks()
    elif args.action == "status":
        status_hooks()


if __name__ == "__main__":
    main()
