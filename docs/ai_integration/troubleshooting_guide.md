# PhotoGeoView トラブルシューティングガイド

生成日時: 2025年07月26日 10:59:48

## AI コンポーネント別問題解決

### GitHub Copilot (CS4Coding) 関連の問題

**対象モジュール**: コア機能、EXIF解析、地図表示

**関連ファイル**:
- `image_loader.py`: 目的不明
- `image_processor.py`: CS4Coding ImageProcessor with Kiro Integration 

#### よくある問題:
1. **EXIF情報が正しく読み取れない**
   - 原因: 画像ファイルの破損またはEXIF情報の欠如
   - 解決方法: ファイル形式と権限を確認

2. **地図が表示されない**
   - 原因: ネットワーク接続またはfolium統合の問題
   - 解決方法: インターネット接続を確認

### Cursor (CursorBLD) 関連の問題

**対象モジュール**: UI/UX、テーマシステム、サムネイル表示

**関連ファイル**:
- `interfaces.py`: Core Interfaces for AI Integration 
- `__init__.py`: AI Integration Module for PhotoGeoView 
- `error_handling.py`: Unified Error Handling System for AI Integration 
- `models.py`: Unified Data Models for AI Integration 
- `logging_system.py`: Unified Logging System for AI Integration 

#### よくある問題:
1. **テーマが正しく適用されない**
   - 原因: Qt-Theme-Managerの設定問題
   - 解決方法: テーマファイルの存在を確認

2. **サムネイルが表示されない**
   - 原因: 画像処理ライブラリの問題
   - 解決方法: Pillowライブラリを再インストール

### Kiro 統合システム関連の問題

**対象モジュール**: 統合制御、パフォーマンス監視、キャッシュシステム

**関連ファイル**:
- `doc_templates.py`: AI統合ドキュメントテンプレートシステム 
- `data_validation.py`: Data Validation System for AI Integration 
- `controllers.py`: Central Application Controller for AI Integration 
- `performance_optimizer.py`: Performance Optimizer for AI Integration 
- `state_manager.py`: Unified State Manager for AI Integration 

#### よくある問題:
1. **統合コンポーネント間の通信エラー**
   - 原因: インターフェース不整合
   - 解決方法: 設定ファイルを確認

2. **パフォーマンス低下**
   - 原因: キャッシュシステムの問題
   - 解決方法: キャッシュをクリア

## 緊急時の対応

1. **アプリケーションが起動しない**
   - 設定ファイルをリセット
   - 依存関係を再インストール

2. **データが失われた**
   - バックアップから復元
   - ログファイルを確認
