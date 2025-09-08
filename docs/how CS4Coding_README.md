# PhotoGeoView

写真のEXIF情報から撮影場所を抽出し、地図上に表示するPySide6ベースの写真管理アプリケーションです。

## 🎯 主要機能

### 📁 ファイル管理機能
- **フォルダ・ファイル管理**: 画像ファイルのみフィルタリングして表示
- **アドレスバー**: フォルダ選択ボタンで選択、カレントフォルダをテキスト表示
- **ナビゲーション**: フォルダ移動・履歴機能

### 🖼️ 画像表示・管理機能
- **サムネイル表示**: 写真のサムネイル一覧表示
- **サムネイルサイズ変更**: サムネイルエリアの右クリックでサイズ変更可能
- **画像プレビュー**: 選択した写真の表示、ズーム・パン機能
- **EXIF情報表示**: 撮影日時、カメラ情報、GPS座標等の詳細情報

### 🗺️ 地図表示機能
- **地図表示**: EXIF位置情報を基にした撮影場所の地図表示
- **地図操作**: ズーム・パン操作が可能
- **撮影位置マーカー**: 写真の撮影場所にマーカー表示

### 🎨 テーマ・UI機能
- **テーマシステム**: Qt-Theme-Managerで16種類のテーマサポート
- **テーマ切り替え**: トグルボタンで簡単切り替え
- **テーマ設定**: ボタン右クリックでテーマ種類設定可能
- **パネル最大化**: 画像・地図パネルで全画面ボタン設定、戻るボタンで通常表示

## 🚀 セットアップ

### 必要条件
- Python 3.8以上
- PySide6
- その他の依存関係（pyproject.toml参照）

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/your-username/PhotoGeoView.git
cd PhotoGeoView
```

2. 仮想環境を作成・アクティベート
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows
```

3. 依存関係をインストール
```bash
pip install .
```

4. アプリケーションを実行
```bash
python main.py
```

## 📦 依存関係

```
PySide6>=6.9.1
PySide6-WebEngine>=6.9.1
exifread>=3.0.0
folium>=0.14.0
qt-theme-manager>=0.1.0
```

## 🏗️ プロジェクト構造

```
📦 PhotoGeoView/
├── 🚀 main.py                         # アプリケーションエントリーポイント
├── 📚 README.md                       # プロジェクト概要・セットアップ
├── 📋 pyproject.toml                  # Python依存関係定義
├── 🔒 .gitignore                      # Git除外設定
├── 📂 src/                            # ソースコードメイン
│   ├── 🎨 ui/                         # ユーザーインターフェース
│   │   ├── 🏠 main_window.py          # メインウィンドウ実装
│   │   └── 🎭 theme_manager.py        # テーマ管理機能
│   ├── ⚙️ core/                       # コア機能・ユーティリティ
│   │   ├── 🎮 controller.py           # アプリケーション制御ロジック
│   │   ├── ⚙️ settings.py             # 設定管理
│   │   ├── 📝 logger.py               # ログ設定・管理
│   │   └── 🔧 utils.py                # ユーティリティ関数
│   └── 📦 modules/                    # 機能別モジュール
│       ├── 🖼️ image_loader.py         # 画像読み込み機能
│       ├── 🖼️ thumbnail_generator.py  # サムネイル生成機能
│       ├── 📊 exif_parser.py          # EXIFデータ解析
│       ├── 🗺️ map_viewer.py           # 地図表示機能
│       └── 👁️ image_viewer.py         # 画像表示機能
├── ⚙️ config/                         # 設定ディレクトリ
│   ├── 📝 config.json                 # 設定ファイル（永続化含む）
│   └── 📋 logging.json                # ログ設定ファイル
├── 📁 logs/                           # ログ出力ディレクトリ
├── 🎨 assets/                         # リソースファイル
│   ├── 🎯 icons/                      # アイコン画像
│   └── 🎭 themes/                     # テーマファイル
├── 🧪 tests/                          # テストファイル
└── 📚 docs/                           # ドキュメント
```

## 🎨 UI設計

メインウィンドウは以下の4つの主要エリアで構成されます：

1. **ヘッダーエリア（上部）**: アドレスバー、ナビゲーションボタン、テーマ切り替えボタン
2. **左パネル（ファイル管理）**: フォルダツリー、サムネイルグリッド、詳細情報パネル
3. **右上パネル（画像プレビュー）**: メイン画像表示、ズーム・パン操作対応
4. **右下パネル（地図表示）**: インタラクティブ地図、撮影位置マーカー

## 🧪 テスト

### 基本動作テスト
```bash
python simple_test.py
```

### 単体テスト
```bash
python -m pytest tests/
```

## 📝 開発状況

### ✅ 完了済み
- [x] プロジェクト構造構築
- [x] ログ機能実装
- [x] 設定管理機能実装
- [x] ユーティリティ関数実装
- [x] テーマ管理基盤実装
- [x] メインウィンドウ基本構造実装
- [x] 画像読み込み機能実装
- [x] EXIF解析機能実装
- [x] サムネイル生成機能実装
- [x] 画像表示機能実装
- [x] 地図表示機能実装

### 🚧 進行中
- [ ] フォルダナビゲーション機能
- [ ] ファイル選択・フィルタリング機能
- [ ] 画像・地図パネルの統合
- [ ] 全画面表示機能

### 📋 予定
- [ ] 履歴機能
- [ ] 検索機能
- [ ] エクスポート機能
- [ ] プラグインシステム

## 🤝 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- [PySide6](https://doc.qt.io/qtforpython/) - GUIフレームワーク
- [Folium](https://python-visualization.github.io/folium/) - 地図表示ライブラリ
- [exifread](https://github.com/ianare/exif-py) - EXIF情報読み込みライブラリ

## 📞 サポート

問題や質問がある場合は、[Issues](https://github.com/your-username/PhotoGeoView/issues)で報告してください。
