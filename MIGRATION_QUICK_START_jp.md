# PhotoGeoView: Electron移行クイックスタートガイド

## クイックファクト

| メトリック | 値 |
|----------|-----|
| **現在の技術** | PySide6 + folium + PyQtWebEngine |
| **総行数** | 72,400 |
| **問題点** | 18,340行（25%）がクロスプラットフォーム回避策に充てられている |
| **WebEngine問題** | Linuxヘッドレス、Windows DLL、GPU可用性、メモリ（400-600MB） |
| **移行実現可能性** | 高 - よくドキュメント化され、モジュラーアーキテクチャ |
| **推奨アプローチ** | Electron + TypeScript + Pythonバックエンド（ハイブリッド） |
| **推奨理由** | TypeScriptはAI支援開発に最適、型安全性で保守性向上 |
| **タイムライン** | 15週間 + 4週間バッファー（合計19週間） |
| **チームサイズ** | 4人（1-2名のTypeScript/Electron開発者、1名のPythonバックエンド、1名のDevOps、1名のQA） |

---

## なぜElectronに移行するのか？

### 問題（現在のPySide6）
1. **WebEngineの複雑さ**: main.pyに145行以上の環境設定
2. **プラットフォーム固有のハック**: コードベース全体にヘッドレス検出、X11チェック、Windowsパス処理
3. **統合層のオーバーヘッド**: フレームワークの制限を補うためだけに存在する18,000行
4. **配布の苦痛**: PyInstaller + プラットフォーム固有ビルド vs. electron-builder統一アプローチ
5. **メモリ使用量**: WebEngineベースライン400-600MB（Chromiumフットプリント）

### 解決策（Electron + TypeScript）
- ✅ **TypeScript採用**: AI支援開発に最適、型安全性でバグ削減
- ✅ **最新技術スタック**: Vite 6、React 19、TailwindCSS v4、React Leaflet 4
- ✅ ネイティブChromium統合（ラッパーの複雑さなし）
- ✅ すべてのプラットフォーム用の単一コードベース
- ✅ プロフェッショナルな配布（electron-builder + electron-updater）
- ✅ 直接React Leaflet統合（foliumミドルウェアなし）
- ✅ 25-30%小さいコードベース（統合層削除）
- ✅ より大きな開発者プール（TypeScriptはAI時代の標準）
- ✅ より良いツール（Vite、Biome、Vitest - すべて高速）
- ✅ **保守性向上**: コンパイル時型チェック、エディタの補完強化

---

## アーキテクチャ: 現在 vs 提案

### 現在（PySide6）
```
main.py（317行の設定）
    ↓
PySide6/Qtフレームワーク
    ↓
統合層（18K行）
    ├── エラーハンドリング（プラットフォーム固有）
    ├── 設定管理
    ├── ロギングシステム
    ├── パフォーマンス監視
    ├── 状態管理
    └── サービス
        ├── ファイル検索
        ├── ファイルシステムウォッチャー
        └── キャッシュシステム
    ↓
コア機能
    ├── 画像プロセッサ（EXIF）
    ├── マッププロバイダー（folium）
    └── 画像ローダー
    ↓
PyQtWebEngine（Chromiumラッパー）
    ↓
folium → HTML → Leaflet.js
```

### 提案（Electron + TypeScript + Pythonバックエンド）
```
メインプロセス（TypeScript + Electron + Node.js）
    ├── ウィンドウ管理
    ├── 型安全なIPC通信
    └── ファイルシステムアクセス

レンダラープロセス（TypeScript + React 19）
    ├── UIコンポーネント（shadcn/ui）
    ├── 状態管理（Zustand - 型安全）
    ├── データフェッチング（TanStack Query v5）
    ├── スタイリング（TailwindCSS v4）
    ├── マップ（React Leaflet 4）
    └── 画像ギャラリー

ビルド・開発環境
    ├── Vite 6（高速ビルド・HMR）
    ├── electron-vite（Electron統合）
    ├── Vitest（高速テスト）
    ├── Biome（高速Linter/Formatter）
    └── TypeScript 5.7+（型システム）

バックエンドサービス（Python - オプション）
    ├── FastAPI（高速REST API）
    ├── Pydantic v2（型検証）
    ├── EXIF解析（Pythonまたはexifreader）
    ├── 画像処理（sharp 0.33 - 最速）
    ├── サムネイル生成
    └── uv（高速パッケージマネージャー）

通信
    型安全なIPCで軽量操作
    FastAPI REST APIで重い処理
```

---

## フェーズごとの実装

### フェーズ1: プロトタイプとセットアップ（第1-4週）

**目標**: 実行可能性の証明、IPC通信の確立

**タスク**:
1. **最新技術スタックでプロジェクト構造作成**
   ```bash
   # Vite + TypeScript + Electronテンプレート使用
   npm create @quick-start/electron@latest photogeoview-electron
   # または
   pnpm create electron-vite photogeoview-electron --template react-ts
   ```

2. **TypeScript設定と型安全なIPCブリッジセットアップ**
   - メインプロセス（TypeScript）
   - 型安全なプリロードスクリプト
   - レンダラーIPC型定義
   - Zodスキーマ検証（ランタイム型安全性）

3. **モダンUIフレームワークで基本ファイルブラウザー実装**
   - shadcn/ui コンポーネント使用
   - TailwindCSS v4スタイリング
   - Zustand状態管理
   - ディレクトリナビゲーション（型安全）
   - ファイルフィルタリング（画像のみ）

4. **FastAPI Pythonバックエンドスケルトン**
   - FastAPI + Pydantic v2セットアップ
   - uv（高速パッケージマネージャー）使用
   - 型安全なエンドポイント構造
   - CORS設定

5. **型安全な通信テスト**
   - TypeScript型定義付きIPCメッセージパッシング
   - ファイルシステム操作（型チェック）
   - エラーハンドリング（Result型パターン）

**成功基準**:
- ✅ Electronウィンドウが表示される
- ✅ ファイルブラウザーがフォルダーをナビゲート
- ✅ IPC通信が動作
- ✅ Pythonバックエンドがリクエストに応答

**成果物**:
- 基本UIを持つ動作するElectronアプリ
- 実行中のPythonバックエンドAPI
- IPCプロトコルのドキュメント

---

### フェーズ2: コア機能（第5-10週）

**目標**: コア機能（画像表示、EXIF、マップ）を移行

**タスク**:

#### 第5-6週: 画像処理（TypeScript）
1. **EXIF抽出（型安全）**
   ```typescript
   // 最新・最速のアプローチ
   import sharp from 'sharp';  // 0.33+ (最速)
   import ExifReader from 'exifreader';  // 活発にメンテ

   // 型定義
   interface ExifData {
     camera: {
       make: string;
       model: string;
       lens?: string;
     };
     exposure: {
       iso: number;
       aperture: number;
       shutterSpeed: string;
     };
     gps?: {
       latitude: number;
       longitude: number;
       altitude?: number;
     };
   }

   // sharp使用（最高速）
   const metadata = await sharp(imagePath).metadata();
   const tags = await ExifReader.load(imagePath);
   ```

2. **画像プレビュー（React 19）**
   - フル解像度画像読み込み（Suspense活用）
   - ズーム/パンコントロール（react-zoom-pan-pinch）
   - 回転（sharp経由）
   - TanStack Queryでキャッシング

3. **サムネイル生成（sharp - 最速）**
   - sharp 0.33使用（Pillowより高速）
   - TanStack Queryキャッシング戦略
   - React 19 Suspenseで遅延読み込み
   - Web Workerで並列処理

#### 第7-8週: データ表示（TypeScript + React 19）
1. **型安全なEXIFパネル（shadcn/ui）**
   ```typescript
   // 型定義でAI補完が効く
   interface ExifPanelProps {
     camera: CameraInfo;
     exposure: ExposureSettings;
     gps?: GPSData;
     timestamp: Date;
   }

   // shadcn/uiコンポーネント使用
   - カメラ情報（型安全）
   - 露出設定（Zodバリデーション）
   - GPS座標（型チェック）
   - TanStack Queryでリアルタイム更新
   ```

2. **仮想化画像グリッド（高パフォーマンス）**
   - @tanstack/react-virtual使用（大量画像対応）
   - TailwindCSS v4でレスポンシブ
   - Zustandで選択状態管理（型安全）
   - ソート/フィルタリング（TypeScript型推論）

#### 第9-10週: マップ統合（React Leaflet 4 + TypeScript）
1. **型安全なReact Leaflet統合**
   ```typescript
   // 最新のReact Leaflet 4使用
   import { MapContainer, TileLayer, Marker } from 'react-leaflet';
   import type { LatLngExpression } from 'leaflet';

   interface MapProps {
     center: LatLngExpression;
     markers: Array<{
       position: LatLngExpression;
       metadata: PhotoMetadata;
     }>;
   }

   // TypeScriptで型安全なマップコンポーネント
   const PhotoMap: React.FC<MapProps> = ({ center, markers }) => (
     <MapContainer center={center} zoom={10}>
       <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
       {markers.map((m) => (
         <Marker key={m.metadata.id} position={m.position} />
       ))}
     </MapContainer>
   );
   ```

2. **folium完全削除の恩恵**
   - Python HTML生成なし（ビルドが高速）
   - React統合で状態同期が簡単
   - TypeScriptで型安全
   - Viteホットリロードで開発高速化

3. **高度なマーカー機能**
   - react-leaflet-markercluster（型付き）
   - GPS位置の集約（TypeScript型推論）
   - カスタムマーカー（shadcn/uiアイコン）

**成功基準**:
- ✅ EXIFデータが抽出され表示される
- ✅ ズーム/パン付き画像プレビュー
- ✅ サムネイルがキャッシュされ遅延読み込み
- ✅ マーカー付きLeaflet.jsマップが表示
- ✅ Chromium設定不要

**成果物**:
- 画像表示機能
- EXIF表示パネル
- インタラクティブマップ
- パフォーマンスベンチマーク

---

### フェーズ3: UI移行（第11-13週）

**目標**: UIコンポーネントを移行、テーマシステムを実装

**タスク**:

1. Reactコンポーネントライブラリ
   ```javascript
   - MainWindow（レイアウト）
   - BreadcrumbBar（ナビゲーション）
   - ThumbnailGrid（画像リスト）
   - ImagePreview（ビューアー）
   - ExifPanel（メタデータ）
   - MapPanel（ビューアー）
   ```

2. テーマシステム（CSS変数）
   ```css
   :root {
     --theme-primary: #007bff;
     --theme-secondary: #6c757d;
     --theme-background: #ffffff;
     --theme-text: #000000;
     /* 16テーマバリアント */
   }
   ```

3. ナビゲーション
   - ブレッドクラムバー（Qtバージョンからロジックを再利用）
   - キーボードショートカット
   - 履歴管理

**成功基準**:
- ✅ すべてのUIコンポーネントがレンダリング
- ✅ 16テーマがスムーズに切り替わる
- ✅ レスポンシブレイアウト
- ✅ アクセシビリティ準拠

---

### フェーズ4: テストと仕上げ（第14-15週）

**目標**: 品質確保、パフォーマンス最適化

**タスク**:

1. クロスプラットフォームテスト
   - Windows 10/11
   - macOS（Intel + Apple Silicon）
   - Linux（Ubuntu、Fedora）

2. パフォーマンス最適化
   - バンドルサイズ削減
   - 起動時間
   - メモリ使用量

3. 自動デプロイ
   - electron-builder設定
   - コード署名（macOS、Windows）
   - 自動更新セットアップ

4. ドキュメント
   - 移行ガイド
   - 開発者セットアップ
   - アーキテクチャドキュメント
   - 既知の問題と回避策

**成功基準**:
- ✅ クロスプラットフォームテストに合格
- ✅ <500MB総サイズ
- ✅ <3秒起動
- ✅ <400MBメモリ使用量
- ✅ デプロイ自動化が動作

---

## コード再利用性マトリックス

### 高度に再利用可能（80-90%）
- ✅ EXIF解析ロジック（JavaScriptに変換）
- ✅ マッププロバイダーロジック（Leaflet.jsに切り替え）
- ✅ 設定管理（JSONは同じまま）
- ✅ ロギングパターン（JavaScriptで実装）
- ✅ エラーハンドリングパターン（JSで複製）
- ✅ テスト戦略（Jest + Playwright）

### 部分的に再利用可能（40-70%）
- ⚠️ 画像処理（Pillow → sharp）
- ⚠️ ファイル検索（Pythonサービス → Node.js fs）
- ⚠️ パフォーマンス監視（psutil → node-os-utils）
- ⚠️ テーマシステム（Qtスタイルシート → CSS）

### 再利用不可（0-40%）
- ❌ PySide6 UIコード（Reactへの完全書き直し）
- ❌ PyQtWebEngine統合（削除）
- ❌ foliumラッパー（Leaflet.jsを直接使用）
- ❌ Qt固有コンポーネント

---

## 技術スタックマッピング

| コンポーネント | PySide6 | Electron + TypeScript（最新） | 採用理由 |
|-------------|---------|------------------------|--------|
| **開発言語** | Python | **TypeScript 5.7+** | AI支援開発に最適、型安全性 |
| **GUIフレームワーク** | PySide6/Qt | **Electron 33+ + React 19** | React Compiler、最新機能 |
| **ビルドツール** | - | **Vite 6** + electron-vite | Webpackより10倍高速 |
| **UI/スタイリング** | Qt Widgets | **TailwindCSS v4** + shadcn/ui | ゼロランタイム、型安全 |
| **状態管理** | JSONファイル | **Zustand** | Reduxより軽量、型安全 |
| **データフェッチング** | - | **TanStack Query v5** | キャッシング、リトライ内蔵 |
| **マップ表示** | PyQtWebEngine → folium → Leaflet | **React Leaflet 4** | foliumなし、型安全 |
| **画像処理** | Pillow + exifread | **sharp 0.33** (最速) | Pillowより5-10倍高速 |
| **EXIF解析** | ExifRead (停滞) | **exifreader** | 活発にメンテ、型付き |
| **IPC** | Qtシグナル/スロット | 型安全なElectron IPC + Zod | ランタイム検証 |
| **テスト** | pytest + pytest-qt | **Vitest** + Playwright | Jestより5倍高速 |
| **Linter/Formatter** | Ruff + mypy | **Biome** | ESLint/Prettierより25倍高速 |
| **ビルド/配布** | PyInstaller | **electron-builder** + electron-updater | 自動更新内蔵 |
| **パッケージマネージャー** | pip/poetry | **pnpm** (フロント) + **uv** (Python) | npm/pipより高速 |
| **仮想化** | - | **@tanstack/react-virtual** | 大量データ対応 |

---

## 主要依存関係: 新 vs 旧

### 削除（PySide6スタック）
```python
# pyproject.toml - 削除される依存関係
PySide6>=6.8.0              # → Electron + TypeScript + React
folium>=0.18.0              # → React Leaflet 4
ExifRead>=3.0.0             # → exifreader (活発にメンテ)
qt-theme-manager>=0.2.4     # → TailwindCSS v4
breadcrumb-addressbar>=0.2.1 # → shadcn/ui コンポーネント
```

### 追加（最新Electronスタック - TypeScript）
```json
{
  // コアフレームワーク
  "electron": "^33.0.0",           // 最新安定版
  "electron-vite": "^2.0.0",       // Vite統合
  "electron-builder": "^25.0.0",   // ビルド・配布
  "electron-updater": "^6.0.0",    // 自動更新

  // TypeScript
  "typescript": "^5.7.0",          // 最新型システム
  "zod": "^3.23.0",                // ランタイム型検証

  // React 19 + 最新ツール
  "react": "^19.0.0",              // React 19
  "react-dom": "^19.0.0",
  "react-compiler": "^19.0.0",     // 自動最適化

  // ビルド・開発
  "vite": "^6.0.0",                // 超高速ビルド
  "@vitejs/plugin-react": "^4.3.0",
  "biome": "^1.9.0",               // 超高速Linter/Formatter

  // 状態管理・データフェッチング
  "zustand": "^5.0.0",             // 軽量状態管理
  "@tanstack/react-query": "^5.59.0", // データフェッチング
  "@tanstack/react-virtual": "^3.10.0", // 仮想化

  // UI・スタイリング
  "tailwindcss": "^4.0.0",         // TailwindCSS v4
  "@tailwindcss/typography": "^0.5.0",
  "tailwindcss-animate": "^1.0.0",
  "@radix-ui/react-*": "latest",   // shadcn/ui base
  "lucide-react": "^0.460.0",      // アイコン

  // マップ・画像
  "react-leaflet": "^4.2.0",       // マップ
  "leaflet": "^1.9.0",
  "sharp": "^0.33.0",              // 最速画像処理
  "exifreader": "^4.23.0",         // EXIF (活発にメンテ)

  // テスト
  "vitest": "^2.1.0",              // 超高速テスト
  "@vitest/ui": "^2.1.0",
  "playwright": "^1.48.0",         // E2Eテスト

  // ユーティリティ
  "pino": "^9.5.0",                // 高速ロガー
  "date-fns": "^4.1.0"             // 日付処理
}
```

### 維持（Pythonバックエンド - FastAPI + 最新ツール）
```python
# pyproject.toml - 最新・高速スタック
fastapi = "^0.115.0"        # Flask→FastAPIへ移行（より高速）
pydantic = "^2.9.0"         # Pydantic v2 (型検証)
uvicorn = "^0.32.0"         # ASGIサーバー
Pillow = "^10.4.0"          # 画像処理（必要なら）
psutil = "^6.0.0"           # システム監視

# パッケージマネージャー: uv使用（pipより10-100倍高速）
# uv add fastapi pydantic uvicorn
```

---

## リスク軽減

### リスク#1: 画像処理パフォーマンス
**リスク**: Node.js sharpがPython Pillowより遅い
**軽減策**: 重い操作にはPythonバックエンドサービスを維持
**影響**: パフォーマンスのためにわずかな複雑さを受け入れる

### リスク#2: 移行スケジュール遅延
**リスク**: 15週間は積極的
**軽減策**: 4週間バッファー、MVPを優先、nice-to-haveを延期
**影響**: 12週間でMVP、最後の4週間で仕上げ

### リスク#3: EXIF解析不完全
**リスク**: JavaScriptライブラリがexifreadほど完全ではない可能性
**軽減策**: exifreader（活発にメンテ、TypeScript型付き）使用、必要に応じてPythonにフォールバック
**影響**: exifreaderは完全な実装で99%カバレッジ、ギャップは最小限
**追加メリット**: TypeScript型定義でAIがEXIFタグを補完、開発効率向上

### リスク#4: プラットフォーム固有の問題
**リスク**: Electronにも独自の癖（コード署名、自動更新）
**軽減策**: すべてのプラットフォームで早期テスト、自動化テスト
**影響**: 開発後期に驚きなし

### リスク#5: パフォーマンス低下
**リスク**: ElectronがPythonネイティブより遅い可能性
**軽減策**:
- Vite 6の超高速ビルド活用
- React 19 Compiler（自動最適化）
- sharp 0.33（Pillowより5-10倍高速）
- TanStack Virtual（大量データ仮想化）
- Web Worker並列処理
- 早期プロファイル、Vitest benchmarkでホットパス最適化
**影響**: むしろ高速化が期待できる（250-400MB、60 FPS維持）
**追加メリット**: Viteホットリロードで開発体験が劇的に向上

---

## 成功指標

### コードメトリクス
- ✅ コードベース: 40-50K行（対現在72K）
- ✅ 統合層削除: 0行（対18K）
- ✅ プラットフォーム固有コード: <5%（対現在15-20%）
- ✅ テストカバレッジ: >80%

### パフォーマンスメトリクス
- ✅ 起動時間: <3秒
- ✅ メモリ使用量: <400MB（対現在400-600MB）
- ✅ バンドルサイズ: <200MB
- ✅ マップレンダリング: <500ms
- ✅ サムネイル生成: 画像あたり<100ms

### 品質メトリクス
- ✅ クロスプラットフォームテスト合格（Windows、macOS、Linux）
- ✅ 型カバレッジ: 100%（TypeScript）
- ✅ リンティング: エラーゼロ
- ✅ セキュリティスキャン: 脆弱性ゼロ

### ユーザー体験
- ✅ プラットフォームごとに単一インストーラー
- ✅ 自動更新が動作
- ✅ 設定不要
- ✅ レスポンシブUI（60 FPS）

---

## チーム構成

### 役割と責任

**リードElectron開発者（1-2人）**
- アーキテクチャ設計
- メイン/レンダラープロセス
- IPCブリッジ実装
- Reactコンポーネントライブラリ
- パフォーマンス最適化

**Pythonバックエンド開発者（1人）**
- バックエンドAPI設計
- EXIF処理
- 画像最適化
- データベース/状態管理
- Electronとの統合

**DevOpsエンジニア（1人）**
- electron-builder設定
- CI/CDパイプライン
- コード署名セットアップ
- 自動更新インフラストラクチャ
- デプロイ自動化

**QAエンジニア（1人）**
- クロスプラットフォームテスト
- リグレッションテスト
- パフォーマンスベンチマーク
- ユーザー受け入れテスト
- ドキュメント

---

## 意思決定チェックリスト

移行開始前に確認:

- [ ] チームにElectron経験がある（または学ぶ意欲がある）
- [ ] 15-19週間のタイムラインが許容可能
- [ ] 約5ヶ月間の4人チームの予算がある
- [ ] 移行後に古いPySide6コードを廃止するコミットメント
- [ ] Electronビルド用のCI/CDインフラストラクチャの準備完了
- [ ] コード署名証明書が利用可能（macOS/Windows）
- [ ] 配布チャネルの準備完了（GitHubリリース、自動更新サーバー）
- [ ] アーキテクチャ変更に関する利害関係者の承認

---

## 次のステップ

1. **第1週**: チームとこの分析をレビュー
2. **第2週**: 決定: Electron移行またはPySide6維持？
3. **第3-4週**: 移行する場合、詳細なプロジェクト計画を作成
4. **第5週以降**: フェーズ1（プロトタイプ）を開始

---

## 追加リソース

### ドキュメント
- 元の分析: `/CODEBASE_ANALYSIS.md`
- 現在のコードベース仕様: `/docs/specifications/PhotoGeoView_ProjectSpecification.md`
- マルチプラットフォーム問題: `/docs/guides/MULTIPLATFORM_SUPPORT.md`

### 理解すべき主要ファイル
- Main.py（WebEngine設定）
- map_panel.py（ヘッドレス検出、WebEngine回避策）
- integration/controllers.py（オーケストレーション）
- integration/image_processor.py（EXIF解析）

### 外部参照（最新技術スタック）

**Electron関連**
- [Electronドキュメント](https://www.electronjs.org/docs)
- [electron-vite](https://electron-vite.org/) - Vite統合
- [electron-builder](https://www.electron.build/) - ビルド・配布
- [electron-updater](https://www.electron.build/auto-update) - 自動更新

**TypeScript + React**
- [TypeScript 5.7](https://www.typescriptlang.org/)
- [React 19](https://react.dev/)
- [React Compiler](https://react.dev/learn/react-compiler) - 自動最適化
- [Zod](https://zod.dev/) - TypeScript型検証

**ビルド・開発ツール**
- [Vite 6](https://vite.dev/)
- [Vitest](https://vitest.dev/) - 超高速テスト
- [Biome](https://biomejs.dev/) - 超高速Linter/Formatter
- [Playwright](https://playwright.dev/) - E2Eテスト

**状態管理・データフェッチング**
- [Zustand](https://zustand-demo.pmnd.rs/)
- [TanStack Query v5](https://tanstack.com/query/latest)
- [TanStack Virtual](https://tanstack.com/virtual/latest)

**UI・スタイリング**
- [TailwindCSS v4](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/) - Reactコンポーネント
- [Radix UI](https://www.radix-ui.com/) - アクセシブルプリミティブ
- [Lucide React](https://lucide.dev/) - アイコン

**マップ・画像処理**
- [React Leaflet 4](https://react-leaflet.js.org/)
- [Leaflet.js](https://leafletjs.com/)
- [sharp](https://sharp.pixelplumbing.com/) - 最速画像処理
- [exifreader](https://github.com/mattiasw/ExifReader) - EXIF解析

**Python バックエンド**
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic v2](https://docs.pydantic.dev/)
- [uv](https://github.com/astral-sh/uv) - 超高速パッケージマネージャー

---

**レポート生成日**: 2025年11月14日
**推奨事項**: **TypeScript + Electron + Pythonバックエンド**のハイブリッドアプローチで移行
**推奨理由**:
- **TypeScript採用**: AI支援開発に最適、型安全性で保守性・開発速度向上
- **最新技術スタック**: Vite 6、React 19、TailwindCSS v4などすべて最新版
- **高速ツール**: Biome（Linter）、Vitest（テスト）、sharp（画像処理）すべて業界最速
- **保守的でない選択**: 問題が実際に起こってから対処するのではなく、最初から最新・最速のエコシステムを採用

**期待されるメリット**:
- コードベース25-30%削減
- クロスプラットフォーム安定性向上
- **劇的な開発体験向上**（TypeScript型推論、Viteホットリロード、AI補完）
- **パフォーマンス向上**（Pillowより5-10倍高速なsharp、React Compiler自動最適化）
- **将来性**（すべて活発にメンテされている最新技術）
