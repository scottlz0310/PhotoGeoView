# PhotoGeoView Electron Migration - Implementation Tasks

> 実装タスク管理 | Status: 🚧 In Progress
>
> このドキュメントは実装の進捗を追跡します。完了したタスクは✅でマークします。

## 📋 目次

- [Phase 0: 環境セットアップ](#phase-0-環境セットアップ)
- [Phase 1: プロトタイプ & セットアップ](#phase-1-プロトタイプ--セットアップ-第1-4週)
- [Phase 2: コア機能実装](#phase-2-コア機能実装-第5-10週)
- [Phase 3: UI完成](#phase-3-ui完成-第11-13週)
- [Phase 4: テストと仕上げ](#phase-4-テストと仕上げ-第14-15週)

---

## Phase 0: 環境セットアップ

### ✅ 0.1 プロジェクト初期化
- [x] electron-migration ブランチ作成
- [x] Electron + Vite + TypeScript + React 19 セットアップ
- [x] 基本プロジェクト構造作成
- [x] CI/CD (GitHub Actions) 設定
- [x] 移行ドキュメント追加
- [x] 初回コミット & プッシュ

### ✅ 0.2 開発環境確認
- [x] `pnpm dev` でアプリ起動確認
- [x] ホットリロード動作確認
- [x] TypeScript型チェック動作確認
- [x] Biome Linter 動作確認
- [x] WSL2でのElectronバイナリインストール問題解決
- [x] Biome設定更新（out/ディレクトリ除外）

---

## Phase 1: プロトタイプ & セットアップ (第1-4週)

### 🎯 目標
最新UI技術スタックで基本的なファイルブラウザーを実装し、Electron + TypeScript開発の基盤を確立する。

### 1.1 最新UI依存関係のインストール

**参照**: MIGRATION_QUICK_START_jp.md 第419-482行

#### ✅ 1.1.1 TailwindCSS v4 セットアップ
- [x] TailwindCSS v4 インストール
  ```bash
  pnpm add -D tailwindcss@next @tailwindcss/typography tailwindcss-animate @tailwindcss/postcss autoprefixer postcss
  ```
- [x] PostCSS設定（postcss.config.cjs作成、@tailwindcss/postcss使用）
- [x] グローバルCSS更新（@import "tailwindcss"、@theme使用）
- [x] App.tsxにTailwindクラス適用
- [x] ダークモード対応（prefers-color-scheme）
- [x] 動作確認完了

**TailwindCSS v4の変更点**:
- `tailwind.config.ts`不要（削除）
- `@tailwind`ディレクティブの代わりに`@import "tailwindcss"`使用
- `@theme`でCSS変数定義
- `@tailwindcss/postcss`プラグイン必須

#### ✅ 1.1.2 shadcn/ui セットアップ
- [x] shadcn/ui CLI インストール & マニュアル設定
  ```bash
  pnpm add class-variance-authority clsx tailwind-merge lucide-react
  ```
- [x] components.json 設定（Electronプロジェクト用にマニュアル作成）
- [x] 基本コンポーネントインストール
  - [x] Button
  - [x] Card
  - [x] Input
  - [x] Separator
- [x] Lucide React アイコン追加
- [x] 動作確認（サンプルコンポーネント表示）
- [x] TypeScriptパスエイリアス修正（`@renderer` → `src/renderer/src`）
- [x] cn()ユーティリティ関数作成

#### ✅ 1.1.3 状態管理・データフェッチング
- [x] Zustand インストール
  ```bash
  pnpm add zustand
  ```
- [x] TanStack Query v5 インストール
  ```bash
  pnpm add @tanstack/react-query @tanstack/react-query-devtools
  ```
- [x] 基本的なストア作成（appStore.ts）
  - [x] ディレクトリパス管理
  - [x] ファイル選択状態
  - [x] UI状態（サイドバー）
  - [x] テーマ設定
  - [x] Zustand devtools統合
- [x] QueryClient設定
  - [x] キャッシング戦略設定
  - [x] リトライ設定
  - [x] React Query Devtools追加
- [x] App.tsxでストア動作確認

#### ✅ 1.1.4 ユーティリティライブラリ
- [x] date-fns インストール
  ```bash
  pnpm add date-fns
  ```
- [x] clsx, tailwind-merge インストール（クラス名管理）
  ```bash
  pnpm add clsx tailwind-merge
  ```
- [x] cn() ユーティリティ関数作成（Phase 1.1.2で完了）

### 1.2 型安全なIPC通信の設計

**参照**: MIGRATION_QUICK_START_jp.md 第123-127行

#### 1.2.1 IPC型定義
- [ ] `src/types/ipc.ts` 作成
  - [ ] ファイルシステムAPI型定義
  - [ ] IPCチャンネル名の定数定義
- [ ] Zodスキーマ追加
  ```bash
  pnpm add zod
  ```
- [ ] IPC通信のバリデーションスキーマ作成

#### 1.2.2 メインプロセスハンドラー実装
- [ ] `src/main/handlers/` ディレクトリ作成
- [ ] ファイルシステムハンドラー実装
  - [ ] `getDirectoryContents` - ディレクトリ内容取得
  - [ ] `getFileInfo` - ファイル情報取得
  - [ ] `readImageMetadata` - 画像メタデータ取得（後で実装）
- [ ] エラーハンドリング（Result型パターン）

#### 1.2.3 プリロードスクリプト更新
- [ ] `src/preload/index.ts` にAPI追加
- [ ] 型定義ファイル `index.d.ts` 更新
- [ ] レンダラーから呼び出し可能な型安全API確立

### 1.3 基本ファイルブラウザーUI実装

**参照**: MIGRATION_QUICK_START_jp.md 第129-134行

#### 1.3.1 ディレクトリ構造作成
- [ ] `src/renderer/src/components/` 構造整理
  - [ ] `file-browser/` - ファイルブラウザー関連
  - [ ] `ui/` - shadcn/uiコンポーネント（自動生成）
  - [ ] `layout/` - レイアウトコンポーネント

#### 1.3.2 ファイルブラウザーコンポーネント
- [ ] `FileBrowser.tsx` 作成（親コンポーネント）
- [ ] `FileList.tsx` - ファイルリスト表示
- [ ] `FileItem.tsx` - 個別ファイルアイテム
- [ ] 画像ファイルフィルタリング（.jpg, .png, など）
- [ ] ディレクトリナビゲーション機能

#### 1.3.3 状態管理統合
- [ ] Zustand ストア作成
  - [ ] 現在のディレクトリパス
  - [ ] ファイルリスト
  - [ ] 選択中のファイル
- [ ] TanStack Query統合
  - [ ] ファイルリスト取得クエリ
  - [ ] キャッシング設定

#### 1.3.4 基本スタイリング
- [ ] TailwindCSSでレスポンシブレイアウト
- [ ] ダーク/ライトモード対応
- [ ] ローディング状態UI
- [ ] エラー状態UI

### 1.4 基本動作確認
- [ ] ファイルブラウザーでディレクトリ移動
- [ ] 画像ファイルのみフィルタリング表示
- [ ] ファイル選択状態の保持
- [ ] ホットリロードでの開発体験確認

---

## Phase 2: コア機能実装 (第5-10週)

### 🎯 目標
画像処理（EXIF、サムネイル）とマップ表示の実装。高パフォーマンスライブラリ（sharp、exifreader）を活用。

### 2.1 画像処理ライブラリのセットアップ

**参照**: MIGRATION_QUICK_START_jp.md 第166-207行

#### 2.1.1 sharp インストールと設定
- [ ] sharp インストール
  ```bash
  pnpm add sharp
  ```
- [ ] メインプロセスで画像処理ハンドラー作成
  - [ ] サムネイル生成ハンドラー
  - [ ] 画像リサイズハンドラー
- [ ] パフォーマンステスト（Pillowとの比較）

#### 2.1.2 exifreader セットアップ
- [ ] exifreader インストール
  ```bash
  pnpm add exifreader
  ```
- [ ] EXIF抽出ハンドラー実装
- [ ] TypeScript型定義作成
  ```typescript
  interface ExifData {
    camera: { make: string; model: string; lens?: string };
    exposure: { iso: number; aperture: number; shutterSpeed: string };
    gps?: { latitude: number; longitude: number; altitude?: number };
  }
  ```

### 2.2 画像プレビュー機能

#### 2.2.1 画像ビューアーコンポーネント
- [ ] `ImagePreview.tsx` 作成
- [ ] フル解像度画像読み込み
- [ ] React 19 Suspense活用
- [ ] TanStack Queryでキャッシング

#### 2.2.2 ズーム/パン機能
- [ ] react-zoom-pan-pinch インストール
  ```bash
  pnpm add react-zoom-pan-pinch
  ```
- [ ] ズームコントロール実装
- [ ] パンジェスチャー対応
- [ ] リセット機能

#### 2.2.3 画像回転
- [ ] sharp経由で回転処理
- [ ] UI回転ボタン
- [ ] EXIF Orientation対応

### 2.3 サムネイル生成システム

**参照**: MIGRATION_QUICK_START_jp.md 第203-207行

#### 2.3.1 高速サムネイル生成
- [ ] sharpでサムネイル生成（最速）
- [ ] キャッシュディレクトリ設定
- [ ] TanStack Query キャッシング戦略
- [ ] Web Worker並列処理（検討）

#### 2.3.2 サムネイルグリッド
- [ ] `ThumbnailGrid.tsx` 作成
- [ ] @tanstack/react-virtual インストール
  ```bash
  pnpm add @tanstack/react-virtual
  ```
- [ ] 仮想スクロール実装（大量画像対応）
- [ ] 遅延読み込み
- [ ] グリッドレイアウト（TailwindCSS Grid）

### 2.4 EXIF表示パネル

**参照**: MIGRATION_QUICK_START_jp.md 第209-231行

#### 2.4.1 型安全なEXIFパネル
- [ ] `ExifPanel.tsx` 作成
- [ ] shadcn/ui コンポーネント使用
  - [ ] Card
  - [ ] Table
  - [ ] Badge
- [ ] カメラ情報表示
- [ ] 露出設定表示
- [ ] GPS座標表示
- [ ] タイムスタンプ表示

#### 2.4.2 データフェッチング
- [ ] TanStack Query統合
- [ ] リアルタイム更新
- [ ] ローディング・エラー状態

### 2.5 マップ統合

**参照**: MIGRATION_QUICK_START_jp.md 第233-268行

#### 2.5.1 React Leaflet セットアップ
- [ ] React Leaflet インストール
  ```bash
  pnpm add react-leaflet leaflet
  pnpm add -D @types/leaflet
  ```
- [ ] Leaflet CSS追加
- [ ] 基本マップコンポーネント作成

#### 2.5.2 型安全なマップコンポーネント
- [ ] `PhotoMap.tsx` 作成（TypeScript型付き）
  ```typescript
  interface MapProps {
    center: LatLngExpression;
    markers: Array<{ position: LatLngExpression; metadata: PhotoMetadata }>;
  }
  ```
- [ ] マーカー表示
- [ ] ポップアップ情報
- [ ] カスタムマーカーアイコン（shadcn/ui）

#### 2.5.3 マーカークラスタリング
- [ ] react-leaflet-markercluster インストール
  ```bash
  pnpm add react-leaflet-markercluster
  ```
- [ ] 大量マーカー対応
- [ ] クラスター設定

### 2.6 統合テスト
- [ ] ファイル選択 → サムネイル表示
- [ ] サムネイルクリック → プレビュー表示
- [ ] EXIF表示
- [ ] GPS座標あり → マップ表示
- [ ] パフォーマンス確認（大量画像）

---

## Phase 3: UI完成 (第11-13週)

### 🎯 目標
完全なUIコンポーネントと16テーマシステムの実装。

### 3.1 レイアウトシステム

#### 3.1.1 メインレイアウト
- [ ] `MainLayout.tsx` 作成
- [ ] ヘッダー
- [ ] サイドバー（ファイルブラウザー）
- [ ] メインエリア（3ペイン）
  - [ ] サムネイルグリッド
  - [ ] 画像プレビュー
  - [ ] EXIF/マップパネル
- [ ] レスポンシブ対応

#### 3.1.2 ナビゲーション
- [ ] ブレッドクラムバー（shadcn/ui Breadcrumb）
- [ ] 履歴管理（前後移動）
- [ ] キーボードショートカット

### 3.2 テーマシステム

**参照**: 元のQt 16テーマシステム

#### 3.2.1 TailwindCSS テーマ設定
- [ ] CSS変数定義
  ```css
  :root {
    --theme-primary: #007bff;
    --theme-secondary: #6c757d;
    --theme-background: #ffffff;
    --theme-text: #000000;
  }
  ```
- [ ] 16テーマバリアント作成
  - [ ] Dark
  - [ ] Light
  - [ ] Material
  - [ ] Monokai
  - [ ] Dracula
  - [ ] その他11テーマ

#### 3.2.2 テーマ切り替え
- [ ] テーマセレクター UI
- [ ] Zustandでテーマ状態管理
- [ ] リアルタイムテーマ切り替え
- [ ] localStorage永続化

#### 3.2.3 カスタムテーマ
- [ ] カスタムテーマエディター（オプション）
- [ ] JSON エクスポート/インポート

### 3.3 追加UIコンポーネント

#### 3.3.1 shadcn/ui追加コンポーネント
- [ ] Dialog（モーダル）
- [ ] Dropdown Menu
- [ ] Tooltip
- [ ] Tabs
- [ ] Progress（ローディングバー）
- [ ] Toast（通知）

#### 3.3.2 カスタムコンポーネント
- [ ] ファイル情報カード
- [ ] 画像メタデータ表示
- [ ] 検索バー
- [ ] フィルター UI

### 3.4 アクセシビリティ
- [ ] キーボードナビゲーション
- [ ] ARIA属性
- [ ] フォーカス管理
- [ ] スクリーンリーダー対応

---

## Phase 4: テストと仕上げ (第14-15週)

### 🎯 目標
包括的なテスト、パフォーマンス最適化、配布準備。

### 4.1 テスト

#### 4.1.1 ユニットテスト (Vitest)
- [ ] コンポーネントテスト（@testing-library/react）
- [ ] ストアテスト（Zustand）
- [ ] ユーティリティ関数テスト
- [ ] カバレッジ >80%

#### 4.1.2 E2Eテスト (Playwright)
- [ ] Playwright設定
- [ ] 基本フロー
  - [ ] アプリ起動
  - [ ] ファイル選択
  - [ ] 画像表示
  - [ ] EXIF表示
  - [ ] マップ表示
- [ ] クロスプラットフォームテスト
  - [ ] Windows
  - [ ] macOS
  - [ ] Linux

### 4.2 パフォーマンス最適化

#### 4.2.1 React最適化
- [ ] React 19 Compiler活用確認
- [ ] 不要な再レンダリング削減
- [ ] メモ化（useMemo、useCallback）
- [ ] Code splitting

#### 4.2.2 バンドル最適化
- [ ] Vite bundleサイズ分析
- [ ] Tree-shaking確認
- [ ] 遅延読み込み
- [ ] アセット最適化

#### 4.2.3 パフォーマンス目標確認
- [ ] 起動時間 <3秒
- [ ] メモリ使用量 <400MB
- [ ] バンドルサイズ <200MB
- [ ] UI 60 FPS維持

### 4.3 配布準備

#### 4.3.1 electron-builder設定
- [ ] `electron-builder.yml` 作成
- [ ] アイコン設定
- [ ] アプリ署名設定（macOS/Windows）
- [ ] 自動更新設定（electron-updater）

#### 4.3.2 GitHub Actions更新
- [ ] ビルド成果物アップロード
- [ ] リリース自動化
- [ ] クロスプラットフォームビルド

#### 4.3.3 ドキュメント
- [ ] CHANGELOG.md
- [ ] ユーザーガイド
- [ ] 開発者ドキュメント
- [ ] トラブルシューティング

### 4.4 最終確認
- [ ] 全機能動作確認
- [ ] クロスプラットフォーム動作確認
- [ ] パフォーマンステスト
- [ ] セキュリティスキャン（Biome）
- [ ] 型カバレッジ100%確認

---

## 📊 進捗トラッキング

### 全体進捗

| Phase | タスク数 | 完了 | 進捗率 |
|-------|---------|-----|--------|
| Phase 0 | 12 | 12 | 100% ✅ |
| Phase 1 | 25 | 16 | 64% |
| Phase 2 | 35 | 0 | 0% |
| Phase 3 | 30 | 0 | 0% |
| Phase 4 | 25 | 0 | 0% |
| **合計** | **127** | **28** | **22.0%** |

### 現在のフォーカス

**🎯 Phase 1.2: 型安全なIPC通信の設計** - 次のステップ

---

## 🔗 参考リンク

- [MIGRATION_QUICK_START_jp.md](./MIGRATION_QUICK_START_jp.md) - 詳細な実装ガイド
- [CODEBASE_ANALYSIS_jp.md](./CODEBASE_ANALYSIS_jp.md) - 技術分析
- [元のPySide6実装](https://github.com/scottlz0310/PhotoGeoView/tree/main) - 参考用

---

## 📝 メモ・決定事項

### 技術的決定
- TypeScript strictモード有効
- Biome設定: セミコロンなし、シングルクォート
- コミットメッセージ: Conventional Commits形式

### 次回セッション時のTODO
1. ✅ ~~Phase 0.2 完了（開発環境確認）~~ → 完了
2. ✅ ~~Phase 1.1.1 開始（TailwindCSS v4セットアップ）~~ → 完了
3. ✅ ~~Phase 1.1.2: shadcn/ui セットアップ~~ → 完了
4. ✅ ~~Phase 1.1.3-1.1.4: 状態管理・データフェッチング・ユーティリティ~~ → 完了
5. 🎯 **Phase 1.2: 型安全なIPC通信の設計** ← 次はここから
   - IPC型定義作成（src/types/ipc.ts）
   - Zodスキーマ追加
   - メインプロセスハンドラー実装

### 📝 セッション記録

#### 2025-11-15 セッション 1
**完了項目**:
- ✅ Phase 0.2: 開発環境確認完了
  - pnpm dev 起動成功（WSL2でのElectron起動確認）
  - HMR (Hot Module Replacement) 動作確認
  - TypeScript型チェック合格
  - Biome linter 合格
- ✅ Phase 1.1.1: TailwindCSS v4 セットアップ完了
  - TailwindCSS v4の新しいCSS構文を採用
  - PostCSS設定完了
  - ダークモード対応

**技術的メモ**:
- TailwindCSS v4は`@import "tailwindcss"`と`@theme`を使用
- WSL2環境でのElectronバイナリ手動インストールが必要だった
- Viteキャッシュクリアが必要な場合: `rm -rf node_modules/.vite`

**次回への引き継ぎ**:
- 開発サーバーは起動中（バックグラウンド）
- 次はshadcn/uiのセットアップから開始

#### 2025-11-15 セッション 2
**完了項目**:
- ✅ Phase 1.1.2: shadcn/ui セットアップ完了
  - shadcn/ui基本依存関係インストール
  - cn()ユーティリティ関数作成
  - components.json マニュアル設定（Electronプロジェクト対応）
  - 基本コンポーネントインストール（Button, Card, Input, Separator）
  - Lucide React アイコン統合
  - App.tsxでコンポーネントデモ作成
  - CSS変数とprocess参照の修正

**技術的メモ**:
- shadcn/ui CLIはElectronプロジェクト構造を自動検出できないため、マニュアル設定が必要
- TypeScriptパスエイリアス: `@renderer` → `src/renderer/src` に修正
- Viteエイリアス設定も同様に修正
- shadcn/uiコンポーネントパスを`src/renderer/src/components/ui`に移動
- TailwindCSS v4の`@theme`とshadcn/uiのCSS変数を`@layer base`で統合
- レンダラープロセスで`process`オブジェクトは使用不可
- Biomeの自動フォーマット・インポート順序修正が動作

#### 2025-11-15 セッション 3
**完了項目**:
- ✅ Phase 1.1.3: 状態管理・データフェッチング完了
  - Zustand インストールと設定
  - appStore作成（ディレクトリパス、ファイル選択、UI状態、テーマ）
  - Zustand devtools統合
  - TanStack Query v5 インストール
  - QueryClient設定（キャッシング、リトライ戦略）
  - React Query Devtools追加
  - App.tsxでストア動作確認

- ✅ Phase 1.1.4: ユーティリティライブラリ完了
  - date-fns インストール

**技術的メモ**:
- Zustandストアは正常に動作（状態更新、読み取り確認済み）
- QueryClientProviderをmain.tsxに追加
- ストアのdevtoolsでデバッグ可能
- 実際のUI連携（サイドバー、テーマ切り替え）は後のフェーズで実装予定

**次回への引き継ぎ**:
- 開発サーバーは起動中（バックグラウンド）
- Phase 1.1完了（UI依存関係セットアップ）
- 次はPhase 1.2（型安全なIPC通信の設計）

---

**最終更新**: 2025-11-15
**次回レビュー予定**: Phase 1完了時
