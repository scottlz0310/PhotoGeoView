#!/usr/bin/env bash
# ログファイルをクリーンアップ

LOG_DIR="logs"

echo "🧹 ログファイルをクリーンアップ中..."

if [ -d "$LOG_DIR" ]; then
    rm -f "$LOG_DIR"/*.log
    echo "✓ ログファイルを削除しました"
else
    mkdir -p "$LOG_DIR"
    echo "✓ ログディレクトリを作成しました"
fi
