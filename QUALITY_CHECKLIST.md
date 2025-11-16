# 品質チェックリスト

> 最終更新: 2025-11-16

## 🎯 最終目標

- [ ] 80% テストカバレッジ
- [x] TypeScript strict mode
- [x] セキュリティチェック通過
- [ ] CI/CD オールグリーン

---

## Phase 1: TypeScript Strict Mode ✅

- [x] tsconfig.json で strict: true 有効化を試行
- [x] エラー箇所のリストアップ
- [x] noImplicitAny 対応
- [x] strictNullChecks 対応
- [x] 全strictオプション対応完了

**結果**: 既に strict: true が有効化されており、全てのstrictオプションに対応済みでした。

---

## Phase 2: テストカバレッジ 80%達成 ⏳

### コンポーネントテスト (目標: 50%カバレッジ)

- [ ] FileBrowser.tsx
- [ ] FileList.tsx
- [ ] FileItem.tsx
- [ ] ImagePreview.tsx
- [ ] ExifPanel.tsx
- [ ] FileFilters.tsx
- [ ] PhotoMap.tsx
- [ ] ThumbnailGrid.tsx
- [ ] App.tsx

### E2Eテスト (目標: 65%カバレッジ)

- [ ] Playwright環境セットアップ
- [ ] 基本フロー: アプリ起動 → ディレクトリ選択 → 画像表示
- [ ] 画像ナビゲーション
- [ ] フィルタリング機能
- [ ] EXIF・地図表示

### Main Processテスト (目標: 80%カバレッジ)

- [ ] fileSystem.ts handlers
- [ ] imageProcessing.ts handlers
- [ ] main/index.ts

---

## Phase 3: セキュリティチェック ✅

### 依存関係

- [x] pnpm audit セットアップ
- [x] 全セキュリティ脆弱性の解決
  - [x] happy-dom: 15.11.7 → 20.0.10 (Critical RCE 2件修正)
  - [x] electron: 33.4.11 → 39.2.1 (ASAR Integrity Bypass修正)
  - [x] electron-vite: 2.3.0 → 4.0.1 (esbuild脆弱性修正)
  - [x] vite: 6.4.1 → 7.2.2 (esbuild脆弱性修正)
  - [x] vitest: 2.1.9 → 4.0.9 (esbuild脆弱性修正)
- [x] 自動依存関係更新 (Renovate導入済み)
- [ ] CI/CDにセキュリティスキャン統合

**結果**: `pnpm audit` で "No known vulnerabilities found" ✅

### コードセキュリティ

- [ ] セキュリティルール追加 (Biome/ESLint)
- [ ] Electron Security Checklist 全項目確認
- [ ] Context Isolation 確認済み
- [ ] CSP設定

---

## Phase 4: CI/CD強化 ⏳

- [ ] Codecov/Coveralls 統合
- [ ] カバレッジバッジ追加
- [ ] キャッシュ最適化
- [ ] 自動リリースワークフロー

---

## Phase 5: ドキュメント ⏳

- [ ] CONTRIBUTING.md
- [ ] ARCHITECTURE.md
- [ ] USER_GUIDE.md
- [ ] API ドキュメント

---

## 📊 進捗

| 項目 | 現在 | 目標 | 状態 |
|------|------|------|------|
| カバレッジ | 20.12% | 80% | ⏳ |
| Strict Mode | ✅ | ✅ | ✅ |
| セキュリティ(依存関係) | ✅ | ✅ | ✅ |
| セキュリティ(コード) | 🟡 | ✅ | ⏳ |
| CI/CD | 🟡 | ✅ | ⏳ |
| ドキュメント | 🟡 | ✅ | ⏳ |

---

**完了フェーズ**: Phase 1 (TypeScript Strict Mode), Phase 3.1 (依存関係セキュリティ)

**次のタスク**: Phase 2 (テストカバレッジ 80%達成) または Phase 3.2 (コードセキュリティ)
