# 開発用スクリプト

PhotoGeoViewの開発デバッグサイクルを自動化するスクリプト集です。

## 📋 利用可能なスクリプト

### デバッグサイクル自動化

```bash
# フルデバッグサイクルを実行（推奨）
pnpm dev:debug
```

**実行内容** (claude.md 7.5 デバッグフロー準拠):
1. ログファイル削除
2. 既存プロセスキル (tauri, vite)
3. TypeScript型チェック
4. Viteビルド
5. ビルドエラー確認
6. Tauri開発サーバー起動
7. ログファイル確認 (停止後)

### ログ管理

```bash
# ログファイルをクリーンアップ
pnpm logs:clean

# ログファイルを表示
pnpm logs:view

# ログファイルをリアルタイム監視 (別ターミナル推奨)
pnpm logs:watch
```

## 🔍 デバッグワークフロー例

### 基本的な使い方

```bash
# ターミナル1: デバッグサイクル実行
pnpm dev:debug

# ターミナル2: ログをリアルタイム監視
pnpm logs:watch
```

### 問題が発生した場合

1. **ビルドエラー**:
   - TypeScript型エラー → コードを修正
   - Viteビルドエラー → 設定やインポートを確認

2. **ランタイムエラー**:
   - ログファイルを確認: `pnpm logs:view`
   - エラー箇所を特定して修正
   - 再度 `pnpm dev:debug` を実行

3. **プロセスが残っている**:
   ```bash
   pkill -f tauri
   pkill -f vite
   pnpm dev:debug
   ```

## 📁 ログファイルの場所

### 開発用ローカルログ
- `logs/photogeoview.log` (このスクリプトが管理)

### Tauriアプリログ
Tauri plugin-logが自動的に以下の場所にログを出力します:

**Linux/WSL**:
```
~/.local/share/com.tauri.dev/logs/photogeoview.log
```

**macOS**:
```
~/Library/Logs/com.tauri.dev/photogeoview.log
```

**Windows**:
```
%APPDATA%\com.tauri.dev\logs\photogeoview.log
```

アプリ起動時にログファイルの場所がコンソールに表示されます。

## 🛠️ トラブルシューティング

### スクリプトが実行できない

```bash
# 実行権限を付与
chmod +x scripts/*.sh
```

### ログが表示されない

1. Tauriアプリが正常に起動したか確認
2. ログレベル設定を確認 (src-tauri/src/lib.rs)
3. ログファイルのパスを確認

### ポート5173が使用中

```bash
# Viteプロセスを停止
pkill -f vite

# または別のポートを使用 (vite.config.ts で設定変更)
```

## 📝 カスタマイズ

スクリプトは `scripts/` ディレクトリ内で編集可能:

- `dev-debug.sh`: デバッグサイクルのカスタマイズ
- `logs-clean.sh`: ログクリーンアップ処理
- `logs-view.sh`: ログ表示方法
- `logs-watch.sh`: ログ監視設定

## 🔗 関連ドキュメント

- [claude.md 7.5](../docs/claude.md#75-デバッグフロー): デバッグフローの詳細
- [TAURI_MIGRATION_PLAN.md](../docs/TAURI_MIGRATION_PLAN.md): Tauri移行計画
- [tasks.md](../tasks.md): 実装タスクリスト
