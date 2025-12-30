# Electron版 PhotoGeoView (v2.2.1)

このディレクトリには、Tauri移行前のElectron版PhotoGeoViewのソースコードとビルド成果物が保管されています。

## アーカイブ内容

- `src/` - Electronアプリケーションのソースコード
  - `main/` - Electronメインプロセス
  - `preload/` - プリロードスクリプト
  - `renderer/` - Reactレンダラープロセス
- `tests/` - テストコード（単体テスト・E2Eテスト）
- `electron.vite.config.ts` - Electron Vite設定
- `vitest.config.ts` - Vitest設定
- `playwright.config.*` - Playwright E2E設定
- `dist/`, `coverage/`, `playwright-report/`, `test-results/` - ビルド成果物

## アーカイブ日時

- 日付: 2025-12-29
- バージョン: 2.2.1
- ブランチ: tauri-rewrite
- 理由: Tauri v2への完全リライトのため

## 参考情報

Electron版の詳細な仕様や実装については、このディレクトリ内のソースコードを参照してください。
