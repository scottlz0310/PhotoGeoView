# Archived Workflows

このディレクトリには、過去に使用されていたが現在は非アクティブなGitHub Actionsワークフローが保存されています。

## アーカイブされたワークフロー

### 1. `basic-ci.yml`
- **用途**: 基本的なCI/CD（旧バージョン）
- **特徴**: pip使用、Python 3.9-3.11対応
- **アーカイブ理由**: ci.ymlに統合・置き換え（uv統合、Python 3.12-3.14対応）

### 2. `simple-ci.yml`
- **用途**: シンプルなCI設定
- **特徴**: カスタムCIツール使用
- **アーカイブ理由**: 標準的なGitHub Actions CI/CDに統合

### 3. `ai-integration-ci.yml`
- **用途**: AI統合関連のCI
- **特徴**: AI統合機能のテスト
- **アーカイブ理由**: ai-quality-improvement.ymlに機能統合

### 4. `ai-integration-tests.yml`
- **用途**: AI統合テスト専用ワークフロー
- **特徴**: AI統合コンポーネントのテスト
- **アーカイブ理由**: メインCI/CDワークフローに統合

### 5. `ci-simulator.yml`
- **用途**: CIシミュレーター実行
- **特徴**: カスタムCIシミュレーションツール
- **アーカイブ理由**: 標準GitHub Actions CI/CDに移行

---

## 現在のアクティブなワークフロー

アクティブなワークフローについては、`../workflows/README.md` を参照してください。

主なワークフロー:
- **ci.yml** - メインCI/CD（Python 3.12-3.14、uv統合）
- **multiplatform-ci-simple.yml** - クロスプラットフォームテスト
- **ai-quality-improvement.yml** - AI品質保証

---

## 注意事項

- このディレクトリのワークフローファイルは、GitHub Actionsでは実行されません
- 参考・履歴保存目的でのみ保持しています
- 削除せずに保管することで、過去の設定を参照できます
