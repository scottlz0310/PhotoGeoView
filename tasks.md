# PhotoGeoView Tauri版 実装タスクリスト

**作成日**: 2025-12-29
**対象バージョン**: v3.0.0

このファイルは実装時の目安となるタスクリストです。チェックボックスにチェックを入れながら進めてください。

---

## Phase 1: 基盤構築

### 1.1 プロジェクト初期化

- [ ] Tauriプロジェクト初期化 (`pnpm create tauri-app`)
- [ ] Git管理下に追加
- [ ] package.jsonの基本設定
  - [ ] プロジェクト名・バージョン更新
  - [ ] スクリプト定義 (dev, build, test等)
- [ ] Rust依存関係の追加 (Cargo.toml)
  - [ ] serde, serde_json
  - [ ] tauri-plugin-dialog
  - [ ] tauri-plugin-fs (必要に応じて)

### 1.2 開発環境セットアップ

- [ ] TypeScript設定 (tsconfig.json)
- [ ] Biome設定 (biome.json) - Electron版から流用
- [ ] Lefthook設定 (lefthook.yml) - Electron版から流用
- [ ] .gitignore更新
- [ ] VSCode設定 (.vscode/settings.json)
  - [ ] Rust Analyzer
  - [ ] Biome拡張機能

### 1.3 基本的なUI構造

- [ ] Vite + React + TypeScript環境確認
- [ ] TailwindCSS v4セットアップ
  - [ ] postcss.config.cjs
  - [ ] tailwind.config.js
- [ ] 3ペインレイアウト実装
  - [ ] 左パネル (PhotoList)
  - [ ] 中央パネル (MapView)
  - [ ] 右パネル (PhotoDetail)
- [ ] react-resizable-panelsでリサイズ可能にする

### 1.4 Tauri Command通信テスト

- [ ] Hello World Command実装 (Rust側)
- [ ] フロントエンドからCommand呼び出しテスト
- [ ] エラーハンドリング確認

---

## Phase 2: コア機能実装

### 2.1 ファイル選択機能

- [ ] tauri-plugin-dialogセットアップ
- [ ] ファイル選択ダイアログ実装
  - [ ] 単一ファイル選択
  - [ ] 複数ファイル選択
  - [ ] フィルター設定 (.jpg, .jpeg, .png, .tiff, .webp)
- [ ] ファイルパスをフロントエンドに返却

### 2.2 EXIF読み取り機能 (Rust)

- [ ] `kamadak-exif`クレート追加
- [ ] EXIF読み取りモジュール作成 (src-tauri/src/commands/exif.rs)
  - [ ] GPS緯度・経度取得
  - [ ] 撮影日時取得
  - [ ] カメラ情報取得
- [ ] Tauri Command: `read_photo_exif(path: String)` 実装
- [ ] エラーハンドリング (EXIF情報がない場合)
- [ ] 複数ファイルの並列処理 (`rayon`)

### 2.3 データモデル定義

- [ ] TypeScript型定義 (src/types/photo.ts)
  ```typescript
  interface PhotoData {
    path: string;
    filename: string;
    gps?: { lat: number; lng: number };
    datetime?: string;
    camera?: { make: string; model: string };
    thumbnail?: string; // Base64
  }
  ```
- [ ] Rust構造体定義 (src-tauri/src/models/photo.rs)
  ```rust
  #[derive(Serialize, Deserialize)]
  struct PhotoData { ... }
  ```

### 2.4 状態管理 (Zustand)

- [ ] Zustand Storeセットアップ
- [ ] `usePhotoStore`実装
  - [ ] `photos: PhotoData[]`
  - [ ] `selectedPhoto: PhotoData | null`
  - [ ] `addPhotos(photos: PhotoData[])`
  - [ ] `selectPhoto(path: string)`
  - [ ] `removePhoto(path: string)`

### 2.5 地図表示 (React Leaflet)

- [ ] React Leaflet v5インストール
- [ ] 基本的な地図コンポーネント実装
  - [ ] OpenStreetMapタイル表示
  - [ ] 初期位置・ズームレベル設定
- [ ] マーカー表示
  - [ ] GPS情報からマーカー配置
  - [ ] マーカークリックで写真選択
- [ ] 地図タイル切替機能
  - [ ] OpenStreetMap
  - [ ] Google Maps (APIキー必要)
  - [ ] Satellite

### 2.6 写真サムネイル一覧

- [ ] サムネイル生成 (Rust)
  - [ ] `image`クレート追加
  - [ ] Tauri Command: `generate_thumbnail(path: String)` 実装
  - [ ] リサイズ処理 (200x200px, Lanczos3)
  - [ ] Base64エンコードして返却
- [ ] サムネイル一覧コンポーネント (PhotoList)
  - [ ] 仮想スクロール対応 (@tanstack/react-virtual)
  - [ ] 遅延ローディング
  - [ ] クリックで写真選択
  - [ ] 撮影日時でソート

### 2.7 写真詳細表示

- [ ] 写真拡大表示コンポーネント (PhotoDetail)
  - [ ] 画像ロード・表示
  - [ ] ズーム・パン操作 (react-zoom-pan-pinch)
- [ ] EXIF情報表示
  - [ ] GPS座標
  - [ ] 撮影日時
  - [ ] カメラ情報
  - [ ] その他メタデータ

---

## Phase 3: 既存資産の移植

### 3.1 UIコンポーネント移植

- [ ] shadcn/uiコンポーネントセットアップ
  - [ ] Button
  - [ ] Dialog
  - [ ] DropdownMenu
  - [ ] Tooltip
  - [ ] Progress
- [ ] Electron版から流用可能なコンポーネント移植
  - [ ] レイアウトコンポーネント
  - [ ] 設定ダイアログ
  - [ ] アバウトダイアログ

### 3.2 国際化 (i18n)

- [ ] i18next + react-i18nextセットアップ
- [ ] 翻訳ファイル移植
  - [ ] src/i18n/locales/en.json (Electron版から流用)
  - [ ] src/i18n/locales/ja.json (Electron版から流用)
- [ ] 言語切替機能実装
  - [ ] 設定ダイアログに言語選択
  - [ ] Zustand Storeで言語状態管理

### 3.3 テーマ (ダークモード/ライトモード)

- [ ] next-themesセットアップ
- [ ] テーマ切替機能実装
  - [ ] システム設定に従う
  - [ ] ライトモード
  - [ ] ダークモード
- [ ] TailwindCSSダークモードスタイル適用

### 3.4 設定管理

- [ ] 設定データ構造定義
  ```typescript
  interface AppSettings {
    language: 'en' | 'ja';
    theme: 'light' | 'dark' | 'system';
    defaultMapTile: 'osm' | 'google' | 'satellite';
  }
  ```
- [ ] 設定の永続化 (Rust側)
  - [ ] 設定ファイル読み書き (JSON形式)
  - [ ] Tauri Command: `get_settings()`, `save_settings()`
- [ ] 設定ダイアログ実装

---

## Phase 4: 高度な機能

### 4.1 フィルタリング機能

- [ ] 日付範囲フィルター
  - [ ] UI実装 (date-fns使用)
  - [ ] フィルター適用ロジック
- [ ] 位置範囲フィルター (地図上で範囲選択)
  - [ ] 矩形選択ツール
  - [ ] 範囲内の写真を抽出

### 4.2 エクスポート機能

- [ ] CSV形式エクスポート
  - [ ] Rust側実装 (csv crate)
  - [ ] Tauri Command: `export_to_csv(photos, path)`
  - [ ] ファイル保存ダイアログ
- [ ] KML形式エクスポート (Google Earth用)
  - [ ] Rust側実装
  - [ ] Tauri Command: `export_to_kml(photos, path)`

### 4.3 パフォーマンス最適化

- [ ] 大量ファイル処理の最適化
  - [ ] プログレスバー表示
  - [ ] Tauri Eventで進捗通知
  - [ ] キャンセル機能
- [ ] サムネイルキャッシュ
  - [ ] ディスクキャッシュ (Rust側)
  - [ ] メモリキャッシュ (フロントエンド側)
- [ ] 仮想スクロールの最適化

### 4.4 エラーハンドリング改善

- [ ] Rust側エラー型統一 (thiserror, anyhow)
- [ ] フロントエンドエラー表示 (sonner toast)
- [ ] ログ出力 (tracing crate)

---

## Phase 5: 仕上げ

### 5.1 テスト

#### フロントエンド

- [ ] Vitestセットアップ
- [ ] ユニットテスト
  - [ ] コンポーネントテスト (React Testing Library)
  - [ ] カスタムフックテスト
  - [ ] Zustand Storeテスト
- [ ] E2Eテスト (Playwright + Tauri)
  - [ ] 写真読み込みフロー
  - [ ] 地図操作
  - [ ] エクスポート

#### バックエンド

- [ ] Rustユニットテスト (`cargo test`)
  - [ ] EXIF読み取りテスト
  - [ ] 画像処理テスト
  - [ ] エラーハンドリングテスト
- [ ] カバレッジ計測 (tarpaulin)

### 5.2 ビルド設定

- [ ] Tauri設定最適化 (tauri.conf.json)
  - [ ] アプリ名・バージョン
  - [ ] アイコン設定
  - [ ] ウィンドウ設定 (最小サイズ、デフォルトサイズ)
  - [ ] メニュー定義
  - [ ] ファイルアソシエーション設定
- [ ] Windows用ビルド設定
  - [ ] NSIS設定
  - [ ] アイコン (icon.ico)
- [ ] macOS用ビルド設定
  - [ ] DMG設定
  - [ ] アイコン (icon.icns)
- [ ] Linux用ビルド設定
  - [ ] AppImage設定

### 5.3 CI/CDセットアップ

- [ ] GitHub Actions設定
  - [ ] .github/workflows/ci.yml (テスト・リント)
  - [ ] .github/workflows/release.yml (ビルド・リリース)
- [ ] クロスプラットフォームビルド確認
  - [ ] Windows (x64)
  - [ ] macOS (Intel + Apple Silicon)
  - [ ] Linux (AppImage)

### 5.4 ドキュメント整備

- [ ] README.md更新
  - [ ] Tauri版の説明
  - [ ] インストール方法
  - [ ] ビルド方法
  - [ ] 開発方法
- [ ] CHANGELOG.md作成
- [ ] コントリビューションガイド (CONTRIBUTING.md)
- [ ] ライセンス確認 (LICENSE)

### 5.5 リリース準備

- [ ] バージョン番号確定 (v3.0.0)
- [ ] リリースノート作成
- [ ] スクリーンショット・デモGIF作成
- [ ] GitHub Release作成

---

## 追加タスク（優先度低）

### オプション機能

- [ ] ドラッグ&ドロップ対応
- [ ] 最近開いたファイル一覧
- [ ] EXIF情報の手動編集
- [ ] マーカーのドラッグ移動
- [ ] プラグインシステム

### パフォーマンス

- [ ] ベンチマークテスト (criterion)
- [ ] メモリプロファイリング
- [ ] 起動時間計測・最適化

---

## 完了基準

すべてのPhase 1-5のタスクが完了し、以下の条件を満たすこと：

- [ ] Windows/macOS/Linuxで正常にビルド可能
- [ ] 100枚の写真を3秒以内に読み込み可能
- [ ] 基本機能（ファイル選択、EXIF読み取り、地図表示、写真表示）が動作
- [ ] テストカバレッジ: フロントエンド70%以上、バックエンド80%以上
- [ ] ドキュメントが整備されている

---

**タスク進捗の記録方法**:
- チェックボックスに `[x]` でチェック
- 実装中のタスクには日付をコメント追記: `- [ ] タスク名 <!-- 2025-12-30開始 -->`
- 完了時にもコメント追記: `- [x] タスク名 <!-- 2025-12-30完了 -->`
