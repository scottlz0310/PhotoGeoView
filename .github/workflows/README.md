# GitHub Actions ワークフロー構成

このディレクトリには、PhotoGeoViewプロジェクトのCI/CDワークフローが含まれています。

## アクティブなワークフロー

### 1. CI/CD (`ci.yml`)

**目的**: メインの継続的インテグレーション/デプロイメント

**トリガー**:

- `main`ブランチへのプッシュ
- `main`ブランチへのプルリクエスト

**実行内容**:

- Python 3.12, 3.13, 3.14でのマルチバージョンテスト
- コード品質チェック (ruff lint/format, mypy)
- テスト実行とカバレッジ計測 (pytest + codecov)
- パッケージビルド (hatchling)
- セキュリティスキャン (bandit, safety)

**技術**: uv (高速パッケージマネージャー)

---

### 2. マルチプラットフォーム CI/CD (`multiplatform-ci-simple.yml`)

**目的**: クロスプラットフォーム互換性の検証

**トリガー**:

- `main`, `ai-integration-main`ブランチへのプッシュ/PR
- 手動トリガー (workflow_dispatch)

**実行内容**:

- Ubuntu, Windows, macOSでの動作確認
- Python 3.9, 3.10, 3.11でのテスト
- プラットフォーム固有の問題の検出

**使用シーン**: リリース前の最終確認、プラットフォーム固有の問題調査

---

### 3. AI Quality Improvement (`ai-quality-improvement.yml`)

**目的**: AI統合コンポーネントの品質保証

**トリガー**:

- 毎日午前9時（スケジュール実行）
- `main`, `develop`ブランチへのプッシュ/PR
- 手動トリガー (workflow_dispatch)

**実行内容**:

- AI統合コンポーネントの品質解析
- AI貢献度の測定とレポート生成
- パフォーマンス回帰検出
- コードドキュメント整合性チェック

**使用シーン**: AI統合の継続的な品質改善、定期的な健全性チェック

---

## アーカイブされたワークフロー

`../workflows-archived/`ディレクトリには、以前使用していたが現在は非アクティブなワークフローが保存されています:

- `basic-ci.yml`: 旧CI設定（pip使用、Python 3.9-3.11）
- `simple-ci.yml`: シンプルCI設定（カスタムツール使用）

これらは参考として保持していますが、GitHub Actionsでは実行されません。

---

## ワークフロー選択ガイド

| シナリオ | 推奨ワークフロー |
|---------|----------------|
| 通常の開発・PR | `ci.yml` (自動実行) |
| リリース前確認 | `multiplatform-ci-simple.yml` (手動実行) |
| AI機能の品質確認 | `ai-quality-improvement.yml` (自動/手動) |
| すべて確認 | すべてのワークフローを手動実行 |

---

## 技術スタック

- **パッケージマネージャー**: uv (Astral)
- **ビルドシステム**: hatchling
- **リンター**: ruff
- **型チェック**: mypy
- **テスト**: pytest + pytest-cov
- **セキュリティ**: bandit, safety
- **CI/CD**: GitHub Actions

---

## 更新履歴

- 2025-11-03: ワークフロー整理、modern-ci.yml → ci.ymlにリネーム
- 2025-11-03: uv統合、Python 3.12-3.14対応
- 2025-11-03: hatchling移行
