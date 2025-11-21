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
  - ✅ 2.2.3 画像回転機能 (90°/180°/270°対応、EXIF保持)
  - ✅ 2.3 サムネイルグリッド
  - ✅ 2.4 EXIF表示パネル
  - ✅ 2.5 マップ統合 (React Leaflet)
  - ✅ 2.6 統合テスト
- 🔄 **Phase 3**: UI完成 (進行中)
  - ✅ 3.1.1 リサイズ可能なレイアウト
  - ✅ 3.1.2 パネル表示・非表示コントロール
  - ✅ 3.1.4 ブレッドクラムバー
  - ✅ 3.1.4 ナビゲーション履歴
  - ✅ 3.1.4 キーボードショートカット
  - ✅ 3.3.1 Toast通知 (Sonner)
  - ✅ 3.3.1 Tooltip
  - ✅ 3.3.1 Progress
  - ✅ 3.3.1 Popover
  - ✅ 3.3.1 DropdownMenu
  - ✅ 3.3.1 Checkbox
  - ✅ 3.3.2 検索バー
  - ✅ 3.3.2 フィルターUI（日付範囲）
- ⏳ **Phase 4**: テストと仕上げ
- 🚀 **Phase 5**: 機能改善とWindows対応 (新規)

## 📋 目次

- [Phase 0: 環境セットアップ](#phase-0-環境セットアップ)
- [Phase 1: プロトタイプ & セットアップ](#phase-1-プロトタイプ--セットアップ-第1-4週)
- [Phase 2: コア機能実装](#phase-2-コア機能実装-第5-10週)
- [Phase 3: UI完成](#phase-3-ui完成-第11-13週)
- [Phase 4: テストと仕上げ](#phase-4-テストと仕上げ-第14-15週)
- [Phase 5: 機能改善とWindows対応](#phase-5-機能改善とwindows対応-202511計画)

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

#### ✅ 2.2.3 画像回転
- [x] sharp経由で回転処理（90°, 180°, 270°, -90°対応）
- [x] UI回転ボタン（左回転・右回転）
- [x] EXIF Orientation対応（withMetadata()でメタデータ保持）
- [x] GPS座標の正しい抽出処理
- [x] 回転後のEXIFキャッシュ無効化
- [x] カスタムプロトコルのクエリパラメータ対応

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

#### ✅ 3.1.2 パネル表示・非表示コントロール（完了）
**優先度**: 高（必須機能）
**概要**: 各コンポーネントに表示・非表示ボタンを配置し、必要なパネルだけを表示してワークスペースを最適化

実装完了:
- [x] パネルヘッダーにコントロールボタン追加
  - [x] 最小化ボタン（各パネルのヘッダーに配置）
  - [x] ImagePreviewはフローティングアイコンに統合
  - [x] アイコン: `Minimize2` (lucide-react)
  - [x] Tooltip表示（"Collapse panel"）
- [x] パネル表示状態の管理
  - [x] Zustandストアに各パネルの表示状態を保存
  - [x] パネルID: `fileBrowser`, `thumbnailGrid`, `exifPanel`, `imagePreview`, `mapView`
  - [x] `togglePanel` アクション実装
  - [x] `setPanelVisibility` アクション実装
- [x] クイックトグル機能
  - [x] ヘッダーに「Panels」ドロップダウンメニュー追加
  - [x] チェックボックスで各パネルのON/OFF切り替え
  - [x] Eye アイコン使用
- [x] パネルが非表示の場合の処理
  - [x] 条件付きレンダリングで完全に非表示
  - [x] `react-resizable-panels`のPanelResizeHandleも非表示
- [x] UI改善
  - [x] Reset Zoom アイコンを Maximize2 に変更（Rotate Right との差別化）
  - [x] ImagePreview のコントロールをフローティングアイコンに統合
  - [x] セパレーターでコントロールをグループ分け
  - [x] z-index 問題の解決（Leaflet マップ）

実装詳細:
- Zustand `appStore.ts`: `panelVisibility` 状態管理
- 各パネルコンポーネント: `Minimize2` ボタンと `TooltipProvider` 追加
- `App.tsx`: ヘッダーに `Panels` ドロップダウンメニュー追加
- `index.css`: Leaflet マップの z-index を 0 に制限

技術的実装:
```typescript
// Zustand store (appStore.ts)
panelVisibility: {
  fileBrowser: boolean
  thumbnailGrid: boolean
  exifPanel: boolean
  imagePreview: boolean
  mapView: boolean
}
togglePanel: (panelId: keyof AppState['panelVisibility']) => void
setPanelVisibility: (panelId: keyof AppState['panelVisibility'], visible: boolean) => void

// 条件付きレンダリング (App.tsx)
{panelVisibility.fileBrowser && (
  <>
    <Panel defaultSize={40} minSize={20}>
      <FileBrowser />
    </Panel>
    <PanelResizeHandle />
  </>
)}
```

利点:
- ユーザーが作業フローに合わせて画面を最適化
- マルチタスクでの使い勝手向上
- 小さい画面でも効率的に作業可能
- ヘッダーのドロップダウンメニューで一元管理

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
- [x] 履歴管理（前後移動）
  - [x] Zustandストアに履歴管理機能追加
  - [x] 戻る/進むボタンをFileBrowserに追加
  - [x] 履歴の状態に応じたボタンの有効/無効化
  - [x] 最大50エントリの履歴保持
  - [x] navigateToPath()による履歴記録
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
- [x] フィルター UI
  - [x] Zustandストアにフィルター状態追加
  - [x] FileFiltersコンポーネント作成（DropdownMenu）
  - [x] 日付範囲フィルター（ファイル更新日時ベース）実装
  - [x] GPS有無フィルターUI（機能は将来実装）
  - [x] カメラモデルフィルターUI（機能は将来実装）
  - [x] アクティブフィルター数表示
  - [x] フィルターリセット機能
  - [x] FileBrowserに統合
  - [ ] サムネイルグリッドへの適用（将来実装）
  - [ ] EXIF撮影日時でのフィルタリング（将来実装）
  - [ ] GPSフィルター実装（EXIF取得が必要、将来実装）
  - [ ] カメラモデルフィルター実装（EXIF取得が必要、将来実装）

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

#### ✅ 4.1.1 ユニットテスト (Vitest)
- [x] Vitest設定ファイル作成 (vitest.config.ts)
- [x] テストセットアップ (tests/setup.ts)
- [x] ユーティリティ関数テスト (tests/unit/utils.test.ts)
- [x] コンポーネントテスト（@testing-library/react）
- [x] ストアテスト（Zustand）
- [ ] カバレッジ >80% (現在70%)

#### ✅ 4.1.2 E2Eテスト (Playwright)
- [x] Playwright設定 (playwright.config.ts)
- [x] 基本テストファイル作成 (tests/e2e/basic.spec.ts)
- [x] シナリオテスト作成 (tests/e2e/scenarios.spec.ts)
- [x] 基本フロー
  - [x] アプリ起動
  - [x] ファイル選択
  - [x] 画像表示
  - [x] 画像ナビゲーション
  - [x] テーマ切り替え
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

## Phase 5: 機能改善とWindows対応 (2025/11計画)

### 🚨 優先課題: Windows版での動作不良
- [x] **ブレッドクラムアドレスバーの修正** [優先度: 高]
  - Windows特有のパス区切り文字(`\`)の問題を解決する
- [x] **地図表示エリアのリサイズ問題修正** [優先度: 高]
  - パネルリサイズ時にLeafletの`invalidateSize()`を呼び出す
- [x] **ピンアイコン消失問題の修正** [優先度: 高]
  - ズーム/パン時のマーカー再描画ロジックを確認

### 🛠️ プラットフォーム共通: UI改善
- [x] **上位フォルダ移行ボタンとリフレッシュ機能** [優先度: 高]
  - フォルダナビゲーションに「上へ」ボタンを追加
  - フォルダ内容を再読み込みするリフレッシュボタンを追加 (Windows 11ライクなUX)
- [ ] **パネル配置のカスタマイズ** [優先度: 高]
  - 設定メニューの実装
- [x] **パネル・スライダー位置の永続化** [優先度: 高]
  - `electron-store` または `localStorage` を使用してレイアウト状態を保存
- [x] **テーマ切替機能** [優先度: 中]
  - システム追随だけでなく、明示的なLight/Dark切り替えUIを追加
- [x] **自動更新機能** [優先度: 中]
  - GitHub Releaseを確認するロジックの実装
- [ ] **多言語対応** [優先度: 低]
  - i18nライブラリの導入検討

### 📦 プロダクション対応
- [x] **パッケージビルドの自動化** [優先度: 高]
  - GitHub Actionsでのマルチプラットフォームビルド設定
- [ ] **コード署名対応** [優先度: 高]
  - 自己署名証明書の生成と適用
- [x] **起動画面 (Splash Screen)** [優先度: 中]
  - アプリ起動時のローディング画面実装

### 🛡️ 品質管理・セキュリティ
- [ ] **E2Eテスト/統合テストの完成** [優先度: 高]
  - Playwrightテストの拡充
- [x] **セキュリティ対策** [優先度: 高]
  - CSP設定の強化
  - 機密情報漏洩対策
- [ ] **依存関係管理** [優先度: 高]
  - Renovate設定の運用確認

### 🔮 将来実装
- [ ] **Neutralino版の検討** [優先度: 低]
