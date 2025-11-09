# PhotoGeoView トラブルシューティングガイド

生成日時: 2025年11月09日 20:50:39

## AI コンポーネント別問題解決

### GitHub Copilot (CS4Coding) 関連の問題

**対象モジュール**: コア機能、EXIF解析、地図表示

**関連ファイル**:
- `__main__.py`: PhotoGeoView CLI エントリーポイント
- `image_processor.py`: CS4Coding ImageProcessor with Kiro Integration
- `map_provider.py`: Map Provider - 地図表示プロバイダー
- `image_loader.py`: 目的不明
- `exif_labels.py`: EXIF Panel Labels Configuration

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
- `__init__.py`: PhotoGeoView - AI統合写真地理情報ビューア
- `theme_manager_fallback.py`: ThemeManager フォールバック実装
- `theme_editor.py`: Theme Editor Interface Components
- `theme_selector.py`: 洗練されたテーマ選択UIコンポーネント
- `breadcrumb_fallback.py`: BreadcrumbWidget フォールバック実装

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
- `breadcrumb_bar.py`: Breadcrumb Address Bar Wrapper Component
- `theme_interfaces.py`: Theme Integration Interfaces
- `theme_navigation_integration.py`: Theme and Navigation Integration Interfaces
- `performance_monitor.py`: Kiro Performance Monitor
- `theme_integration_controller.py`: Theme Integration Controller

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
