# PhotoGeoView 統合戦略ドキュメント

## 概要

このドキュメントは、Copilot版 (`CS4Coding` ブランチ) と Cursor版 (`CursorBLD` ブランチ) の PhotoGeoView プロジェクトを統合するための戦略をまとめたものです。各環境の強みを活かし、最適なハイブリッド構成を目指します。

---

## 🧩 パネル別評価

| パネル | 採用元 | 理由 |
|--------|--------|------|
| メインウィンドウのツールバー | 🎯 Cursor版 | テーマ切替UIが直感的で操作性が高い |
| ファイル選択機能 | 🎯 Cursor版 | フォルダ選択・履歴機能が使いやすい |
| サムネイル機能 | 🎯 Cursor版 | Qtネイティブで高速表示、サイズ変更も柔軟 |
| EXIF表示部 | ✅ Copilot版 | GPS抽出・カメラ情報の表示が正確で詳細 |
| プレビュー部 | ✅ Copilot版 | PaintEventによるズーム・パンが滑らか |
| MAP部 | ✅ Copilot版 | folium連携が安定、マーカー表示も正確 |

---

## 🛠 統合方針

### UIベース：Cursor版
- `main_window.py` のUIレイアウトとツールバーをベースに採用
- `theme_manager.py` のUI連携を維持

### 機能ベース：Copilot版
- `modules/image_loader.py`：画像形式判定と読み込み処理
- `modules/map_viewer.py`：EXIFからの地図表示とマーカー処理
- `modules/exif_parser.py`：GPS抽出と例外処理の完成度が高い

---

## 📁 統合ブランチ構成案

```
PhotoGeoView/
├── src/
│   ├── ui/
│   │   └── main_window.py  ← Cursor版ベース
│   ├── modules/
│   │   ├── image_loader.py ← Copilot版流用
│   │   ├── map_viewer.py   ← Copilot版流用
│   │   └── exif_parser.py  ← Copilot版流用
│   ├── core/
│   │   └── config_manager.py ← 両版の良い部分を統合
│   └── utils/
│       └── theme_manager.py ← Cursor版ベース
├── config/
│   ├── app_config.json     ← 設定ファイル統合
│   └── theme_styles.json   ← テーマ設定
├── docs/
│   └── integration_plan.md ← このドキュメント
└── tests/
    └── integration_tests/  ← 統合テスト
```

---

## 🔄 統合手順

### Phase 1: 基盤準備
1. **新ブランチ作成**: `integration-main` ブランチを作成
2. **Cursor版UIベース**: `main_window.py` のレイアウトを採用
3. **設定システム統合**: 両版の設定管理を統一

### Phase 2: 機能統合
1. **画像処理**: Copilot版の `image_loader.py` を統合
2. **EXIF処理**: Copilot版の `exif_parser.py` を統合
3. **マップ機能**: Copilot版の `map_viewer.py` を統合

### Phase 3: UI統合
1. **サムネイル**: Cursor版の高速表示機能を維持
2. **テーマシステム**: Cursor版のテーマ切替UIを保持
3. **プレビュー**: Copilot版のズーム・パン機能を統合

### Phase 4: テスト・最適化
1. **統合テスト**: 各機能の連携確認
2. **パフォーマンス調整**: メモリ使用量とレスポンス最適化
3. **UI/UX調整**: 操作性の最終調整

---

## ⚙️ 技術的考慮事項

### 依存関係の統合
```python
# 統合後の主要依存関係
PyQt6>=6.5.0
Pillow>=10.0.0
folium>=0.14.0
piexif>=1.1.3
```

### 設定ファイル統合戦略
- **app_config.json**: アプリケーション全体設定
- **theme_styles.json**: テーマ・UI設定
- **user_preferences.json**: ユーザー個人設定（.gitignore対象）

### パフォーマンス最適化
- **サムネイル生成**: Qt6のネイティブ機能活用
- **メモリ管理**: 大量画像時のメモリリーク防止
- **非同期処理**: EXIF読み込みとマップ生成の並列化

---

## 🎯 期待される成果

### 機能面
- ✅ **高速なサムネイル表示** (Cursor版の強み)
- ✅ **正確なGPS情報抽出** (Copilot版の強み)
- ✅ **直感的なテーマ切替** (Cursor版の強み)
- ✅ **滑らかなプレビュー操作** (Copilot版の強み)

### 保守性
- 🔧 **統一されたコード構造**
- 🔧 **明確な責任分担**
- 🔧 **テストカバレッジ向上**

### ユーザー体験
- 🎨 **一貫したUI/UX**
- ⚡ **レスポンシブな操作感**
- 🔍 **正確な地図表示**

---

## 📝 実装ノート

### 重要なファイル統合
1. **main_window.py**: Cursor版をベースにCopilot版の機能メソッドを追加
2. **image_loader.py**: Copilot版をそのまま採用（例外処理が優秀）
3. **theme_manager.py**: Cursor版のUI連携を維持

### 設定ファイル除外
```gitignore
# 個人設定（統合後に追加）
config/user_preferences.json
cache/user_thumbnails/
logs/user_activity.log
```

### 統合後のブランチ戦略
- `main`: 安定版
- `integration-main`: 統合作業ブランチ
- `CS4Coding`: Copilot版（参考用）
- `CursorBLD`: Cursor版（参考用）

---

## 🚀 Next Steps

1. **統合ブランチ作成**: `git checkout -b integration-main`
2. **ベースコード準備**: Cursor版UIをベースに配置
3. **段階的統合**: Phase 1から順次実装
4. **継続的テスト**: 各Phaseでの動作確認

---

*このドキュメントは統合作業の進行に合わせて更新される予定です。*
