# PhotoGeoView - AI統合写真地理情報ビューア

PhotoGeoViewは、写真のEXIF情報から撮影場所を抽出し、地図上に表示するPyQt6ベースの写真管理アプリケーションです。このプロジェクトは複数のAIエージェントによる協調開発の成果物です。

## 🤖 AI協調開発

このプロジェクトは以下の3つのAIエージェントによって開発されました：

### GitHub Copilot (CS4Coding)
- **専門分野**: コア機能実装
- **主要貢献**: EXIF解析、地図表示、画像処理の安定実装

### Cursor (CursorBLD)
- **専門分野**: UI/UX設計
- **主要貢献**: テーマシステム、サムネイル表示、直感的なインターフェース

### Kiro
- **専門分野**: 統合・品質管理
- **主要貢献**: パフォーマンス最適化、統合制御、ドキュメント生成

## 🎯 主要機能

### 📁 ファイル管理
- 画像ファイルのフィルタリング表示
- フォルダナビゲーション
- 履歴機能

### 🖼️ 画像表示
- 高速サムネイル生成
- ズーム・パン操作
- EXIF情報詳細表示

### 🗺️ 地図表示
- GPS座標からの撮影場所表示
- インタラクティブ地図操作
- 撮影位置マーカー

### 🎨 テーマシステム
- 16種類のテーマサポート
- リアルタイムテーマ切り替え
- アクセシビリティ対応

## 🏗️ アーキテクチャ

```
PhotoGeoView/
├── src/
│   ├── integration/          # Kiro統合システム
│   ├── ui/                   # CursorBLD UIコンポーネント
│   ├── modules/              # CS4Coding コア機能
│   └── core/                 # 共通機能
├── docs/
│   └── ai_integration/       # AI統合ドキュメント
├── config/                   # 設定ファイル
└── tests/                    # テストスイート
```

## 📚 ドキュメント

### AI統合ドキュメント
詳細なAI貢献度情報とAPIドキュメントは以下をご覧ください：

- **[AI統合ドキュメント](docs/ai_integration/README.md)** - 包括的なドキュメント一覧
- **[APIドキュメント](docs/ai_integration/api_documentation.md)** - 統合API仕様
- **[AI貢献度レポート](docs/ai_integration/ai_contribution_report.md)** - 各AIの貢献分析
- **[トラブルシューティング](docs/ai_integration/troubleshooting_guide.md)** - 問題解決ガイド

### プロジェクト仕様
- **[プロジェクト仕様書](docs/PhotoGeoView_ProjectSpecification.md)** - 完全仕様
- **[統合計画](docs/integration_plan.md)** - AI統合戦略

## 🚀 セットアップ

### 必要要件
- Python 3.9以上
- PySide6
- 依存関係は `pyproject.toml` の `[project.dependencies]` を参照

### インストール
```bash
# リポジトリをクローン
git clone https://github.com/your-username/PhotoGeoView.git
cd PhotoGeoView

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール（pyproject.tomlを使用）
pip install .

# アプリケーションを実行
python main.py
```

## 🧪 テスト

```bash
# 統合テストを実行
python -m pytest tests/

# AI統合テストを実行
python -m pytest tests/integration_tests/

# パフォーマンステストを実行
python -m pytest tests/performance_tests/
```

## 📊 AI貢献統計

| AI エージェント | ファイル数 | 関数数 | 専門分野 |
|----------------|-----------|--------|----------|
| GitHub Copilot | 2 (7.7%) | 10 | コア機能 |
| Cursor | 14 (53.8%) | 92 | UI/UX |
| Kiro | 10 (38.5%) | 86 | 統合・品質 |

## 🔧 開発

### ドキュメント生成
```bash
# AI統合ドキュメントを生成
python docs/ai_integration/standalone_doc_generator.py

# ファイルヘッダーを更新
python docs/ai_integration/generate_docs.py --update-headers
```

### 品質チェック
```bash
# コード品質チェック
python -m flake8 src/

# 型チェック
python -m mypy src/

# テストカバレッジ
python -m pytest --cov=src tests/
```

## 🤝 貢献

このプロジェクトはAI協調開発の実験的取り組みです。各AIエージェントの役割分担：

1. **機能追加**: GitHub Copilot が主導
2. **UI改善**: Cursor が主導
3. **統合・最適化**: Kiro が主導

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルをご覧ください。

## 🙏 謝辞

このプロジェクトは複数のAIエージェントによる協調開発の成果です。各AIの特性を活かした役割分担により、単独では実現できない高品質なアプリケーションを構築することができました。

---

*このREADMEは Kiro AI統合システムによって生成されました*
*最終更新: 2025年7月26日*
