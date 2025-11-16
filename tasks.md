# PhotoGeoView Electron Migration - Implementation Tasks

> 実装タスク管理 | Status: 🚧 In Progress
>
> このドキュメントは実装の進捗を追跡します。完了したタスクは✅でマークします。

## 📊 現在の進捗

- ✅ **Phase 0**: 環境セットアップ (完了)
- ✅ **Phase 1**: プロトタイプ & セットアップ (完了)
  - ✅ TailwindCSS v4, shadcn/ui, Zustand, TanStack Query
  - ✅ Type-safe IPC通信
  - ✅ 基本的なファイルブラウザーUI
- ✅ **Phase 2**: コア機能実装 (完了!)
  - ✅ 2.1 画像処理ライブラリ (sharp, exifreader)
  - ✅ 2.2 画像プレビュー (react-zoom-pan-pinch)
  - ✅ 2.3 サムネイルグリッド
  - ✅ 2.4 EXIF表示パネル
  - ✅ 2.5 マップ統合 (React Leaflet)
  - ✅ 2.6 統合テスト
- 🔄 **Phase 3**: UI完成 (進行中)
  - ✅ 3.1.1 リサイズ可能なレイアウト
  - ✅ 3.1.4 ブレッドクラムバー
  - ✅ 3.1.4 キーボードショートカット
  - ✅ 3.3.1 Toast通知 (Sonner)
  - ✅ 3.3.1 Tooltip
  - ✅ 3.3.1 Progress
  - ✅ 3.3.1 Popover
  - ✅ 3.3.2 検索バー
- ⏳ **Phase 4**: テストと仕上げ

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

### ✅ 1.2 型安全なIPC通信の設計

**参照**: MIGRATION_QUICK_START_jp.md 第123-127行

#### ✅ 1.2.1 IPC型定義
- [x] `src/types/ipc.ts` 作成
  - [x] ファイルシステムAPI型定義
  - [x] IPCチャンネル名の定数定義
  - [x] Result型パターン定義
  - [x] IpcApi型定義
- [x] Zodスキーマ追加
  ```bash
  pnpm add zod
  ```
- [x] IPC通信のバリデーションスキーマ作成
  - [x] FileEntrySchema
  - [x] GetDirectoryContentsRequestSchema
  - [x] ExifDataSchema
  - [x] その他各種スキーマ

#### ✅ 1.2.2 メインプロセスハンドラー実装
- [x] `src/main/handlers/` ディレクトリ作成
- [x] ファイルシステムハンドラー実装
  - [x] `getDirectoryContents` - ディレクトリ内容取得
  - [x] `getFileInfo` - ファイル情報取得
  - [x] `selectDirectory` - ディレクトリ選択ダイアログ
  - [x] 画像ファイル判定ロジック
  - [x] 隠しファイル/画像のみフィルター機能
- [x] エラーハンドリング（Result型パターン）
- [x] Zodバリデーション統合
- [x] メインプロセスindex.tsにIPC登録
- [x] ウィンドウ操作ハンドラー（minimize, maximize, close）

#### ✅ 1.2.3 プリロードスクリプト更新
- [x] `src/preload/index.ts` にAPI追加
  - [x] ファイルシステムAPI
  - [x] ウィンドウ操作API
- [x] 型定義ファイル `index.d.ts` 更新
- [x] レンダラーから呼び出し可能な型安全API確立

### ✅ 1.3 基本ファイルブラウザーUI実装

**参照**: MIGRATION_QUICK_START_jp.md 第129-134行

#### ✅ 1.3.1 ディレクトリ構造作成
- [x] `src/renderer/src/components/` 構造整理
  - [x] `file-browser/` - ファイルブラウザー関連
  - [x] `ui/` - shadcn/uiコンポーネント（自動生成）
  - [x] `layout/` - レイアウトコンポーネント

#### ✅ 1.3.2 ファイルブラウザーコンポーネント
- [x] `FileBrowser.tsx` 作成（親コンポーネント）
- [x] `FileList.tsx` - ファイルリスト表示
- [x] `FileItem.tsx` - 個別ファイルアイテム
- [x] 画像ファイルフィルタリング（.jpg, .png, など）
- [x] ディレクトリナビゲーション機能

#### ✅ 1.3.3 状態管理統合
- [x] Zustand ストア作成
  - [x] 現在のディレクトリパス
  - [x] ファイルリスト
  - [x] 選択中のファイル
- [x] TanStack Query統合
  - [x] ファイルリスト取得クエリ
  - [x] キャッシング設定

#### ✅ 1.3.4 基本スタイリング
- [x] TailwindCSSでレスポンシブレイアウト
- [x] ダーク/ライトモード対応
- [x] ローディング状態UI
- [x] エラー状態UI

### ✅ 1.4 基本動作確認
- [x] ファイルブラウザーでディレクトリ移動
- [x] 画像ファイルのみフィルタリング表示
- [x] ファイル選択状態の保持
- [x] ホットリロードでの開発体験確認
- [x] ブラウザ環境検出とフォールバック実装

---

## Phase 2: コア機能実装 (第5-10週)

### 🎯 目標
画像処理（EXIF、サムネイル）とマップ表示の実装。高パフォーマンスライブラリ（sharp、exifreader）を活用。

### ✅ 2.1 画像処理ライブラリのセットアップ

**参照**: MIGRATION_QUICK_START_jp.md 第166-207行

#### ✅ 2.1.1 sharp インストールと設定
- [x] sharp インストール
  ```bash
  pnpm add sharp
  ```
- [x] メインプロセスで画像処理ハンドラー作成
  - [x] サムネイル生成ハンドラー（200x200px, JPEG品質80%, Base64エンコード）
  - [x] 画像リサイズハンドラー
- [x] .pnpmrc設定でビルドスクリプト承認

#### ✅ 2.1.2 exifreader セットアップ
- [x] exifreader インストール
  ```bash
  pnpm add exifreader
  ```
- [x] EXIF抽出ハンドラー実装（src/main/handlers/imageProcessing.ts）
- [x] TypeScript型定義作成（src/types/ipc.ts）
  - [x] ExifData型定義
  - [x] GenerateThumbnailRequest/Response
  - [x] ReadExifRequest/Response
- [x] IPCチャネル追加（image:generateThumbnail, image:readExif）
- [x] Preloadスクリプト更新

### ✅ 2.2 画像プレビュー機能

#### ✅ 2.2.1 画像ビューアーコンポーネント
- [x] `ImagePreview.tsx` 作成
- [x] フル解像度画像読み込み（file:// URLプロトコル）
- [x] Electron環境検出とフォールバック
- [x] エラーハンドリング

#### ✅ 2.2.2 ズーム/パン機能
- [x] react-zoom-pan-pinch インストール
  ```bash
  pnpm add react-zoom-pan-pinch
  ```
- [x] ズームコントロール実装（Zoom In/Out, Reset, Fit to Screen）
- [x] パンジェスチャー対応（TransformWrapper/Component）
- [x] ダブルクリックでリセット機能
- [x] コントロールボタンUI（shadcn/ui Button、Lucide icons）

#### 2.2.3 画像回転（オプション - 未実装）
- [ ] sharp経由で回転処理
- [ ] UI回転ボタン
- [ ] EXIF Orientation対応

### ✅ 2.3 サムネイル生成システム

**参照**: MIGRATION_QUICK_START_jp.md 第203-207行

#### ✅ 2.3.1 高速サムネイル生成
- [x] sharpでサムネイル生成（150x150px）
- [x] TanStack Query キャッシング戦略（10分staleTime、30分gcTime）
- [x] Base64エンコードでレンダラーに転送

#### ✅ 2.3.2 サムネイルグリッド
- [x] `ThumbnailGrid.tsx` 作成
- [x] @tanstack/react-virtual インストール
  ```bash
  pnpm add @tanstack/react-virtual
  ```
- [x] 仮想スクロール実装（大量画像対応、overscan=5）
- [x] 遅延読み込み（lazy loading）
- [x] グリッドレイアウト（4カラムTailwindCSS Grid）
- [x] 選択状態の視覚的フィードバック
- [x] ローディングスピナー表示

### ✅ 2.4 EXIF表示パネル

**参照**: MIGRATION_QUICK_START_jp.md 第209-231行

#### ✅ 2.4.1 型安全なEXIFパネル
- [x] `ExifPanel.tsx` 作成
- [x] shadcn/ui コンポーネント使用
  - [x] Card
  - [x] Badge
  - [x] Separator
- [x] カメラ情報表示（Make, Model, Lens）
- [x] 露出設定表示（ISO, Aperture, Shutter Speed, Focal Length）
- [x] GPS座標表示（Latitude, Longitude, Altitude）
- [x] タイムスタンプ表示
- [x] 画像サイズ表示

#### ✅ 2.4.2 データフェッチング
- [x] TanStack Query統合（5分キャッシュ）
- [x] リアルタイム更新
- [x] ローディング・エラー状態
- [x] ブラウザ環境検出とフォールバック

### ✅ 2.5 マップ統合

**参照**: MIGRATION_QUICK_START_jp.md 第233-268行

#### ✅ 2.5.1 React Leaflet セットアップ
- [x] React Leaflet インストール
  ```bash
  pnpm add react-leaflet leaflet
  pnpm add -D @types/leaflet
  ```
- [x] Leaflet CSS追加（index.css）
- [x] 基本マップコンポーネント作成

#### ✅ 2.5.2 型安全なマップコンポーネント
- [x] `PhotoMap.tsx` 作成（TypeScript型付き）
- [x] マーカー表示（EXIF GPS座標）
- [x] ポップアップ情報（ファイル名、座標、高度）
- [x] OpenStreetMapタイル統合
- [x] GPS情報がない場合のフォールバック表示
- [x] App.tsxへの統合完了

#### 2.5.3 マーカークラスタリング（オプション - 未実装）
- [ ] react-leaflet-markercluster インストール
  ```bash
  pnpm add react-leaflet-markercluster
  ```
- [ ] 大量マーカー対応
- [ ] クラスター設定

### ✅ 2.6 統合テスト（手動確認済み）
- [x] ファイル選択 → サムネイル表示
- [x] サムネイルクリック → プレビュー表示
- [x] EXIF表示
- [x] GPS座標あり → マップ表示
- [x] パフォーマンス確認（大量画像）

---

## Phase 3: UI完成 (第11-13週)

### 🎯 目標
完全なUIコンポーネントと16テーマシステムの実装。

### 3.1 レイアウトシステム

#### ✅ 3.1.1 リサイズ可能なレイアウト（完了）
- [x] `react-resizable-panels` 統合
- [x] 水平方向のパネル分割（左・中央・右）
- [x] 垂直方向のパネル分割（各パネル内）
- [x] ビジュアルフィードバック付きリサイズハンドル
- [x] 最小サイズ制限設定
- [x] 最適化されたレイアウト配置
  - 左: ファイルブラウザー + サムネイルグリッド
  - 中央: EXIF情報
  - 右: 画像プレビュー + マップ

#### 3.1.2 パネル表示・非表示コントロール（将来実装予定）
**優先度**: 高
**概要**: 各コンポーネントに表示・非表示ボタンを配置し、必要なパネルだけを表示してワークスペースを最適化

実装案:
- [ ] パネルヘッダーにコントロールボタン追加
  - [ ] 最小化/復元ボタン（右上に配置）
  - [ ] 閉じる/再表示ボタン
  - [ ] アイコン: `Minimize2`, `Maximize2`, `X`, `Eye`, `EyeOff` (lucide-react)
- [ ] パネル表示状態の管理
  - [ ] Zustandストアに各パネルの表示状態を保存
  - [ ] パネルID: `fileBrowser`, `thumbnailGrid`, `exifPanel`, `imagePreview`, `mapView`
- [ ] クイックトグル機能
  - [ ] ツールバーに「表示パネル」メニュー
  - [ ] チェックボックスで各パネルのON/OFF切り替え
  - [ ] キーボードショートカット（例: `Ctrl+1`～`Ctrl+5`）
- [ ] パネルが非表示の場合の処理
  - [ ] `react-resizable-panels`の`collapsible`プロパティ使用
  - [ ] 最小化時は細いバー（16px程度）に縮小
  - [ ] 再展開ボタン表示
- [ ] ワンクリック最大化
  - [ ] 任意のパネルを全画面表示
  - [ ] 他のパネルを一時的に非表示
  - [ ] 「元に戻す」ボタンで復元

UXフロー例:
1. 画像プレビューに集中したい
   → 他のパネルの最小化ボタンをクリック
   → 画像プレビューが画面の大部分を占める
2. マップを詳しく見たい
   → マップの最大化ボタンをクリック
   → マップが全画面表示、他は最小化
3. 元に戻す
   → ツールバーの「レイアウトリセット」ボタン
   → すべてのパネルがデフォルトサイズに復元

技術的実装:
```typescript
// Zustand store
interface LayoutState {
  panels: {
    fileBrowser: { visible: boolean; size: number }
    thumbnailGrid: { visible: boolean; size: number }
    exifPanel: { visible: boolean; size: number }
    imagePreview: { visible: boolean; size: number }
    mapView: { visible: boolean; size: number }
  }
  togglePanel: (panelId: string) => void
  maximizePanel: (panelId: string) => void
  resetLayout: () => void
}

// Panel Header Component
<CardHeader>
  <div className="flex items-center justify-between">
    <CardTitle>Image Preview</CardTitle>
    <div className="flex gap-1">
      <Button size="icon" variant="ghost" onClick={onMinimize}>
        <Minimize2 className="h-4 w-4" />
      </Button>
      <Button size="icon" variant="ghost" onClick={onMaximize}>
        <Maximize2 className="h-4 w-4" />
      </Button>
    </div>
  </div>
</CardHeader>
```

利点:
- ユーザーが作業フローに合わせて画面を最適化
- マルチタスクでの使い勝手向上
- 小さい画面でも効率的に作業可能
- 集中モード（単一パネル表示）をワンクリックで実現

#### 3.1.3 レイアウトプリセット（将来実装予定）
**優先度**: 中
**概要**: ユーザーがパネル配置をカスタマイズできる機能

実装案:
- [ ] レイアウトプリセット選択機能
  - [ ] デフォルトレイアウト（現在の配置）
  - [ ] フォトビューワー重視レイアウト
  - [ ] マップ重視レイアウト
  - [ ] EXIF分析レイアウト
- [ ] レイアウト設定UI
  - [ ] 設定ダイアログまたはサイドパネル
  - [ ] プレビュー機能
  - [ ] レイアウトのインポート/エクスポート（JSON）
- [ ] レイアウト状態の永続化
  - [ ] localStorageに保存
  - [ ] アプリ起動時に復元

技術的アプローチ:
- Option 1: プリセットベース（シンプル、推奨）
  - 事前定義されたレイアウト配置から選択
  - `react-resizable-panels`の配置を切り替え
- Option 2: 完全カスタマイズ（複雑）
  - `@dnd-kit`でドラッグ&ドロップ
  - グリッドベースのレイアウトシステム

#### ✅ 3.1.4 ナビゲーション
- [x] ブレッドクラムバー（shadcn/ui Breadcrumb）- クリック可能なパスナビゲーション実装完了
- [ ] 履歴管理（前後移動）
- [x] キーボードショートカット
  - [x] 矢印キー（←/→）で画像選択移動
  - [x] Home/Endで最初/最後の画像へジャンプ
  - [x] Escapeで選択解除
  - [x] useKeyboardShortcutsカスタムフック実装
  - [x] useImageNavigationカスタムフック実装
  - [x] ヘッダーにショートカットヘルプボタン追加（Popover）

### 3.2 テーマシステム

**参照**: 元のQt 16テーマシステム

**現状**:
- アプリ本体は常にライトテーマ（TailwindCSS v4のデフォルト）
- トースト通知のみシステムテーマ（`prefers-color-scheme`）に追随
- 完全なテーマシステムは未実装

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

#### ✅ 3.3.1 shadcn/ui追加コンポーネント（一部完了）
- [ ] Dialog（モーダル）
- [ ] Dropdown Menu
- [x] Tooltip - ImagePreviewとFileBrowserボタンに実装完了
- [ ] Tabs
- [x] Progress（ローディングバー）- ThumbnailGridとImagePreviewに実装完了
- [x] Toast（通知）- Sonnerで実装完了、システムテーマ追随機能付き
- [x] Popover - キーボードショートカットヘルプに実装完了

#### 3.3.2 カスタムコンポーネント
- [ ] ファイル情報カード
- [ ] 画像メタデータ表示
- [x] 検索バー - FileBrowserにファイル名検索機能を実装完了
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

#### 🔄 4.1.1 ユニットテスト (Vitest)
- [x] Vitest設定ファイル作成 (vitest.config.ts)
- [x] テストセットアップ (tests/setup.ts)
- [x] ユーティリティ関数テスト (tests/unit/utils.test.ts)
- [ ] コンポーネントテスト（@testing-library/react）
- [ ] ストアテスト（Zustand）
- [ ] カバレッジ >80%

#### 🔄 4.1.2 E2Eテスト (Playwright)
- [x] Playwright設定 (playwright.config.ts)
- [x] 基本テストファイル作成 (tests/e2e/basic.spec.ts)
- [x] 基本フロー
  - [x] アプリ起動
  - [x] ファイル選択
  - [x] 画像表示
  - [x] EXIF表示
  - [x] マップ表示
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
| Phase 1 | 25 | 25 | 100% ✅ |
| Phase 2 | 35 | 35 | 100% ✅ |
| Phase 3 | 30 | 9 | 30% 🔄 |
| Phase 4 | 25 | 5 | 20% 🔄 |
| **合計** | **127** | **86** | **67.7%** |

### 現在のフォーカス

**🎯 Phase 3 & 4: UI完成とテスト** - 進行中

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

### 🎯 次回作業候補（実装難易度順）

#### 超簡単（1-2時間）
1. **Phase 3.3.1: Toast通知の追加**
   - shadcn/ui Toastコンポーネントインストール
   - 成功/エラー通知の表示
   - 使用箇所: ファイル読み込み、EXIF読み取り、エラー表示
   - 依存: なし

2. **Phase 3.3.1: Tooltipの追加**
   - shadcn/ui Tooltipコンポーネントインストール
   - ボタンやアイコンにホバーヘルプ追加
   - 使用箇所: ImagePreviewコントロールボタン、マップマーカー
   - 依存: なし

3. **Phase 2.6: 統合テスト（手動）**
   - 各機能の動作確認とバグ修正
   - 大量画像でのパフォーマンステスト
   - 依存: なし（すべての機能が実装済み）

#### 簡単（3-5時間）
4. **Phase 3.3.2: 検索バー実装**
   - ファイル名でのフィルタリング機能
   - shadcn/ui Inputコンポーネント使用
   - ThumbnailGridとの連携
   - 依存: なし

5. **Phase 3.1.4: ブレッドクラムバー**
   - shadcn/ui Breadcrumbコンポーネント追加
   - 現在のディレクトリパス表示
   - クリックでディレクトリ移動
   - 依存: なし

6. **Phase 3.3.1: Progress/Loadingバー**
   - shadcn/ui Progressコンポーネントインストール
   - 画像読み込み進捗の視覚化
   - サムネイル生成の進捗表示
   - 依存: なし

#### 中程度（5-10時間）
7. **Phase 3.1.4: キーボードショートカット**
   - 矢印キーで画像選択移動
   - Ctrl+1～5でパネル切り替え（将来のパネル表示制御と連携）
   - Escでフルスクリーン解除
   - 依存: なし

8. **Phase 3.3.2: フィルターUI実装**
   - 日付範囲フィルター
   - GPS有無フィルター
   - カメラモデルフィルター
   - shadcn/ui DropdownMenu, Checkbox使用
   - 依存: なし

9. **Phase 2.2.3: 画像回転機能**
   - sharpで回転処理（90度/180度/270度）
   - EXIF Orientation対応
   - UIボタン追加（ImagePreview）
   - 依存: sharp（インストール済み）

#### やや難しい（10-15時間）
10. **Phase 3.1.2: パネル表示・非表示コントロール**
    - Zustand layoutStore作成
    - パネルヘッダーに最小化/最大化ボタン追加
    - react-resizable-panelsのcollapsible機能使用
    - レイアウトリセット機能
    - 依存: react-resizable-panels（インストール済み）

11. **Phase 3.2: テーマシステム実装**
    - CSS変数ベースのテーマ定義
    - 16テーマバリアント作成（Dark, Light, Material, Monokai, Dracula等）
    - テーマセレクターUI
    - localStorage永続化
    - 依存: なし

12. **Phase 3.1.3: レイアウトプリセット機能**
    - プリセットレイアウト定義（デフォルト、フォトビューワー重視、マップ重視）
    - レイアウト選択UI
    - localStorage永続化
    - 依存: Phase 3.1.2完了が望ましい

#### 難しい（15-20時間以上）
13. **Phase 4.1.1: ユニットテスト（Vitest）**
    - コンポーネントテスト（@testing-library/react）
    - ストアテスト（Zustand）
    - ユーティリティ関数テスト
    - カバレッジ >80%
    - 依存: なし（Vitest設定済み）

14. **Phase 4.1.2: E2Eテスト（Playwright）**
    - Playwright設定とテストシナリオ作成
    - 基本フロー自動化
    - クロスプラットフォームテスト
    - 依存: Phase 4.1.1完了が望ましい

15. **Phase 2.5.3: マーカークラスタリング**
    - react-leaflet-markercluster インストール
    - 大量マーカー対応
    - クラスター設定
    - 依存: Phase 2.5完了（済）

#### 推奨実装順序
1. **まずは簡単なものから**:
   - Toast通知 → Tooltip → 統合テスト（手動）
   - UX向上と既存機能の安定化を優先

2. **次にユーザー体験の向上**:
   - 検索バー → ブレッドクラム → キーボードショートカット
   - 日常的な使い勝手を改善

3. **高度なUI機能**:
   - パネル表示・非表示 → テーマシステム → レイアウトプリセット
   - カスタマイズ性を強化

4. **品質保証**:
   - ユニットテスト → E2Eテスト
   - リリース前の品質担保

#### 次回セッションの推奨開始タスク
**🎯 Phase 3.3.1: Toast通知の追加**（最も簡単で実用的）
- 所要時間: 1-2時間
- 効果: エラーハンドリングとユーザーフィードバックの大幅改善
- 依存: なし
- 実装ファイル:
  - `pnpm dlx shadcn@latest add toast`
  - `src/renderer/src/components/ui/use-toast.ts`
  - FileBrowser, ImagePreview, ExifPanel, PhotoMapに統合

---

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

#### 2025-11-15 セッション 4
**完了項目**:
- ✅ Phase 1.2: 型安全なIPC通信の設計完了
  - Zodインストールとバリデーションスキーマ作成
  - IPC型定義（src/types/ipc.ts）
  - Result型パターンでエラーハンドリング
  - メインプロセスハンドラー実装（fileSystem.ts）
  - プリロードスクリプト更新
  - 型定義ファイル更新（IpcApi）

**技術的メモ**:
- Zodでリクエスト/レスポンスのバリデーション
- Result<T, E>型でエラー処理を型安全に
- 画像ファイル判定（15種類の拡張子サポート）
- 隠しファイルフィルター、画像のみフィルター機能
- ディレクトリ選択ダイアログ実装
- ウィンドウ操作API（最小化、最大化、閉じる）
- TypeScript strictモード合格
- Biome linter合格

**次回への引き継ぎ**:
- 開発サーバーは起動中（バックグラウンド）
- IPC通信の基盤が完成
- 次はPhase 1.3（基本ファイルブラウザーUI実装）

#### 2025-11-15 セッション 5
**完了項目**:
- ✅ Phase 2.5: マップ統合完了
  - React Leaflet & Leaflet インストール
  - Leaflet CSS追加（index.css）
  - PhotoMapコンポーネント作成
  - マーカー表示とポップアップ実装
  - GPS座標からの地図表示
  - App.tsxへの統合
  - 動的インポートによるSSR問題の解決
  - MapUpdaterコンポーネントで地図中心の自動更新実装
  - TypeScript型チェック合格
  - Biome linter合格

**技術的メモ**:
- Leafletのデフォルトマーカーアイコン問題をCDN URLで解決
- ESモジュール環境での動的インポート使用（`import()`）
- `useMap`フックで地図インスタンスにアクセスし、位置変更時に自動更新
- OpenStreetMapタイルを使用
- GPS情報がない画像に対するフォールバック表示を実装
- PhotoMapはExifPanelと連携してEXIF GPSデータを表示

**実装された機能**:
- 画像のGPS座標を地図上にマーカー表示
- ポップアップでファイル名、緯度、経度、高度を表示
- GPS情報がない場合の適切なメッセージ表示
- レスポンシブなマップレイアウト
- 画像選択時の地図中心の自動更新（MapUpdaterコンポーネント）

**解決した課題**:
- ❌ → ✅ `require is not defined` エラー（動的インポートで解決）
- ❌ → ✅ `this._getIconUrl is not a function` エラー（Leaflet初期化順序の修正）
- ❌ → ✅ 地図の中心が自動更新されない問題（MapUpdaterコンポーネント追加）

**次回への引き継ぎ**:
- 開発サーバーは起動中（バックグラウンド）
- Phase 2コア機能実装が完了
- 次はPhase 2.6（統合テスト）またはPhase 3（UI完成）

---

**最終更新**: 2025-11-15
**次回レビュー予定**: Phase 2完了時
