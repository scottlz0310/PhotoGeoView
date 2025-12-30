#!/usr/bin/env bash
# PhotoGeoView デバッグサイクル自動化スクリプト
# claude.md 7.5 デバッグフロー準拠

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログディレクトリ
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/photogeoview.log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PhotoGeoView デバッグサイクル${NC}"
echo -e "${BLUE}========================================${NC}"

# ステップ1: ログファイル削除
echo -e "\n${YELLOW}[1/6] ログファイルを削除...${NC}"
if [ -f "$LOG_FILE" ]; then
    rm -f "$LOG_FILE"
    echo -e "${GREEN}✓ ログファイルを削除しました${NC}"
else
    echo -e "${YELLOW}  (ログファイルは存在しませんでした)${NC}"
fi

# ステップ2: プロセスキル
echo -e "\n${YELLOW}[2/6] 既存プロセスをキル...${NC}"
pkill -f "tauri dev" 2>/dev/null && echo -e "${GREEN}✓ Tauriプロセスをキルしました${NC}" || echo -e "${YELLOW}  (実行中のプロセスはありませんでした)${NC}"
pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✓ Viteプロセスをキルしました${NC}" || true
sleep 1

# ステップ3: ビルド（型チェック + Viteビルド）
echo -e "\n${YELLOW}[3/6] ビルド実行...${NC}"
echo -e "${BLUE}  TypeScript型チェック...${NC}"
if pnpm typecheck; then
    echo -e "${GREEN}✓ TypeScript型チェック成功${NC}"
else
    echo -e "${RED}✗ TypeScript型チェック失敗${NC}"
    exit 1
fi

echo -e "${BLUE}  Viteビルド...${NC}"
if pnpm build:vite > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Viteビルド成功${NC}"
else
    echo -e "${RED}✗ Viteビルド失敗${NC}"
    exit 1
fi

# ステップ4: エラー確認（ビルドエラー）
echo -e "\n${YELLOW}[4/6] ビルドエラー確認...${NC}"
echo -e "${GREEN}✓ ビルドエラーなし${NC}"

# ステップ5: 起動
echo -e "\n${YELLOW}[5/6] Tauri開発サーバー起動...${NC}"
echo -e "${BLUE}  起動中... (Ctrl+C で停止)${NC}"
echo -e "${BLUE}  Vite: http://localhost:5173/${NC}"
echo -e "${BLUE}  ログ: $LOG_FILE${NC}"
echo ""

# ステップ6: ログ確認用に別ターミナル推奨メッセージ
echo -e "${YELLOW}別ターミナルでログ確認:${NC} ${GREEN}pnpm logs:watch${NC}"
echo ""

# Tauri起動（フォアグラウンド）
pnpm tauri dev

# Ctrl+C で停止した後
echo -e "\n${YELLOW}[6/6] ログファイル確認...${NC}"
if [ -f "$LOG_FILE" ]; then
    echo -e "${BLUE}最新のログ (最後の20行):${NC}"
    tail -20 "$LOG_FILE"
else
    echo -e "${YELLOW}  (ログファイルが生成されませんでした)${NC}"
fi
