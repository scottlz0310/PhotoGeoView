#!/usr/bin/env bash
# ログファイルを表示

LOG_FILE="logs/photogeoview.log"

if [ -f "$LOG_FILE" ]; then
    echo "📄 ログファイル: $LOG_FILE"
    echo "================================"
    cat "$LOG_FILE"
else
    echo "⚠️  ログファイルが見つかりません: $LOG_FILE"
    echo "   先に 'pnpm dev:debug' を実行してください"
fi
