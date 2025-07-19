# PhotoGeoView

📸 **写真のEXIF情報とGPS位置情報を視覚的に表示するPython/PyQt6アプリケーション**

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-Latest-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 概要

PhotoGeoViewは、デジタル写真のEXIF情報を詳細に表示し、GPS座標が含まれている場合は地図上にその位置を表示する高機能な画像ビューアーです。写真家やデジタル画像を扱う専門家にとって必要な情報を直感的なインターフェースで提供します。

## ✨ 主要機能

### 📋 EXIF情報表示
- **55個以上のEXIFフィールド**に対応
- **カテゴリ別整理表示**（ファイル情報、カメラ情報、露出設定、GPS位置情報）
- **テキスト選択可能**で情報のコピーが容易
- **バックグラウンド処理**によるスムーズな表示

### 🗺️ GPS位置表示
- **インタラクティブ地図**でのGPS座標表示
- **複数の地図プロバイダー**対応
- **フルスクリーンモード**での詳細確認
- **マーカークリック**で画像情報の表示

### 🖼️ 画像ビューア
- **高品質画像表示**
- **ズーム・パン機能**
- **フルスクリーン表示**
- **画像ナビゲーション**（前/次画像）

### 📁 ファイル管理
- **直感的なファイルブラウザー**
- **サムネイル表示**
- **フォルダナビゲーション履歴**
- **画像ファイルの自動検出**

### 🎨 テーマシステム
- **複数のテーマ**（ダーク/ライト系）
- **テーマの動的切り替え**
- **設定の永続化**
- **カスタムテーマ対応**

## 🚀 インストール

### 必要環境
- Python 3.13以上
- PyQt6
- 追加ライブラリ（requirements.txtを参照）

### セットアップ
```bash
# リポジトリのクローン
git clone https://github.com/scottlz0310/PhotoGeoView.git
cd PhotoGeoView

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

## 🎯 使用方法

### 基本的な使用
```bash
# アプリケーションの起動
python main.py
```

### 主な操作
1. **フォルダを開く**: ツールバーのフォルダアイコンをクリック
2. **画像を選択**: 左パネルのファイルブラウザーまたはサムネイル表示から選択
3. **EXIF情報確認**: 左下パネルにカテゴリ別に表示
4. **GPS位置確認**: 右下の地図パネルで位置を確認
5. **テーマ変更**: ツールバーのテーマボタンで切り替え

## 📁 プロジェクト構成

```
PhotoGeoView/
├── main.py                 # アプリケーションエントリーポイント
├── requirements.txt        # 依存関係
├── LICENSE                # ライセンス
├── README.md              # このファイル
├── src/                   # ソースコード
│   ├── core/              # コアモジュール
│   │   ├── logger.py      # ログシステム
│   │   └── settings.py    # 設定管理
│   ├── ui/                # ユーザーインターフェース
│   │   ├── main_window.py # メインウィンドウ
│   │   ├── theme_manager.py # テーマ管理
│   │   └── controllers/   # UIコントローラー
│   ├── modules/           # 機能モジュール
│   │   ├── exif_info.py   # EXIF情報表示
│   │   ├── file_browser.py # ファイルブラウザー
│   │   ├── image_viewer.py # 画像ビューアー
│   │   ├── map_viewer.py  # 地図ビューアー
│   │   └── thumbnail_view.py # サムネイル表示
│   └── utils/             # ユーティリティ
│       ├── exif_processor.py # EXIF処理
│       ├── gps_utils.py   # GPS座標処理
│       └── file_utils.py  # ファイル操作
├── config/                # 設定ファイル
├── assets/                # リソースファイル
├── docs/                  # ドキュメント
└── tests/                 # テストファイル
```

## 🔧 対応ファイル形式

### 画像形式
- **JPEG** (.jpg, .jpeg) - フル対応
- **PNG** (.png) - EXIF対応
- **TIFF** (.tif, .tiff) - フル対応
- **BMP** (.bmp) - 基本対応
- **GIF** (.gif) - 基本対応

### EXIF情報
- **カメラ情報**: メーカー、モデル、レンズ情報
- **撮影設定**: ISO、絞り値、シャッタースピード、焦点距離
- **GPS情報**: 緯度、経度、撮影位置
- **ファイル情報**: サイズ、更新日時、解像度
- **その他**: フラッシュ設定、ホワイトバランス、露出モード

## 🧪 テスト

```bash
# すべてのテストを実行
python tests/run_all_tests.py

# 個別テスト
python tests/test_exif_reading.py      # EXIF読み取りテスト
python tests/test_exif_detailed.py     # 詳細EXIFテスト
python tests/test_integration.py       # 統合テスト
```

## 📝 設定

アプリケーションの設定は `config/config.json` で管理されます：

```json
{
  "ui": {
    "current_theme": "dark_blue.xml",
    "window_size": [1200, 800],
    "panel_layout": "default"
  },
  "folders": {
    "last_opened_folder": "",
    "recent_folders": []
  },
  "advanced": {
    "auto_save_settings": true,
    "save_interval_seconds": 300
  }
}
```

## 🚨 トラブルシューティング

### 一般的な問題

**EXIF情報が表示されない**
```bash
# 必要なライブラリが正しくインストールされているか確認
pip install exifread pillow
```

**地図が表示されない**
- インターネット接続を確認
- ファイアウォール設定を確認

**アプリケーションが起動しない**
```bash
# 依存関係を再インストール
pip install -r requirements.txt --force-reinstall
```

### ログファイル
問題の詳細は以下のログファイルで確認できます：
- `logs/debug.log` - デバッグ情報
- `logs/error.log` - エラーログ
- `logs/info.log` - 一般ログ

## 🤝 貢献

プロジェクトへの貢献を歓迎します！

### 開発環境のセットアップ
```bash
# 開発用の追加依存関係
pip install -r requirements-dev.txt

# プリコミットフックの設定
pre-commit install
```

### コントリビューション手順
1. プロジェクトをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルをご覧ください。

## 👏 謝辞

- **PyQt6** - 優れたGUIフレームワーク
- **exifread** - EXIF情報の読み取り
- **OpenStreetMap** - 地図データの提供

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/scottlz0310/PhotoGeoView/issues)
- **Discussions**: [GitHub Discussions](https://github.com/scottlz0310/PhotoGeoView/discussions)

## 🔄 更新履歴

### Version 1.0.0 (2025-07-19)
- ✨ 初回リリース
- 📋 EXIF情報表示機能
- 🗺️ GPS位置表示機能
- 🖼️ 画像ビューアー
- 🎨 テーマシステム
- 📁 ファイル管理機能

---

**PhotoGeoView** - あなたの写真をより深く理解するためのツール 📸✨
