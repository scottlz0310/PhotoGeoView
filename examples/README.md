# PhotoGeoView AI統合 デモ・サンプル集

このフォルダには、PhotoGeoViewプロジェクトの各コンポーネントをテスト・デモンストレーションするためのスクリプトが含まれています。

## 📁 ファイル構成

| ファイル名 | 説明 | 対応コンポーネント |
|-----------|------|------------------|
| `demo_config_manager.py` | 設定管理システムのデモ | Task 2: 統合設定管理 |
| `demo_image_processor.py` | 画像処理機能のデモ | CS4Coding画像処理 |
| `demo_data_validation_migration.py` | データ検証・移行のデモ | Task 7: データ検証・移行 |
| `demo_kiro_components.py` | Kiro統合コンポーネント | Kiro: 統合管理システム |
| `demo_kiro_integration.py` | Kiro統合レイヤー | Kiro: パフォーマンス・キャッシュ |

## 🚀 実行方法

各デモスクリプトはプロジェクトルートから実行してください：

```bash
# 設定管理のデモ
python examples/demo_config_manager.py

# 画像処理のデモ
python examples/demo_image_processor.py

# データ検証・移行のデモ
python examples/demo_data_validation_migration.py

# Kiroコンポーネントのデモ
python examples/demo_kiro_components.py

# Kiro統合システムのデモ
python examples/demo_kiro_integration.py
```

## 🎯 目的

- **開発テスト**: 各コンポーネントの動作確認
- **機能デモ**: AI統合システムの機能紹介
- **パフォーマンス測定**: システム性能の評価
- **学習・理解**: コードの使用例・サンプル

## 📋 注意事項

- デモ実行前に依存関係がインストールされていることを確認してください
- 一部のデモは仮想的なデータを使用します
- ログファイルは `logs/` フォルダに出力されます
- パフォーマンステストは時間がかかる場合があります

## 🔧 開発者向け情報

これらのファイルは以下の理由でプロジェクトルートから `examples/` フォルダに移動されました：

1. **プロジェクト構造の整理**: ルートフォルダの整理
2. **用途の明確化**: 実行ファイルと例・デモの分離
3. **メンテナンスの向上**: 関連ファイルのグループ化

Author: Kiro AI Integration System
Date: 2025年7月26日
