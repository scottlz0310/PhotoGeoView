# GitHub Actions AI Analyzer 統合ガイド

## 📖 概要

このガイドでは、PhotoGeoViewプロジェクトで開発されたAI解析機能を[GitHub Actions AI Analyzer](https://github.com/scottlz0310/Github-Actions-AI-Analyzer)リポジトリに統合する方法を説明します。

## 🎯 統合の目的

- **自動的なテスト品質向上**: AIによる継続的な品質監視と改善
- **問題の早期発見**: エラーや警告の自動検出と分析
- **改善提案の自動生成**: 具体的な修正アクションの提案
- **品質メトリクスの追跡**: 時系列での品質変化の監視

## 🚀 統合手順

### 1. ファイルの追加

以下のファイルをGitHub Actions AI Analyzerリポジトリに追加します：

```bash
# AI解析ツール
tools/github_actions_ai_analyzer_enhanced.py

# GitHub Actionsワークフロー
.github/workflows/ai-quality-improvement.yml

# 統合ガイド
docs/ai_quality_integration_guide.md
```

### 2. 依存関係の更新

`pyproject.toml` の `[project.dependencies]` に以下の依存関係を追加：

```txt
# AI解析用の追加依存関係
pytest>=7.0.0
pytest-cov>=4.0.0
flake8>=6.0.0
black>=23.0.0
isort>=5.12.0
mypy>=1.0.0
```

### 3. ディレクトリ構造の確認

以下のディレクトリ構造を確保：

```
Github-Actions-AI-Analyzer/
├── .github/
│   └── workflows/
│       └── ai-quality-improvement.yml
├── tools/
│   └── github_actions_ai_analyzer_enhanced.py
├── docs/
│   └── ai_quality_integration_guide.md
├── reports/          # 解析レポート保存用
├── logs/             # ログファイル保存用
└── quality-reports/  # 品質レポート保存用
```

## 🔧 設定とカスタマイズ

### 1. ワークフローの設定

`.github/workflows/ai-quality-improvement.yml`の設定を調整：

```yaml
# 実行タイミングの調整
on:
  push:
    branches: [ main, develop ]  # 対象ブランチを調整
  schedule:
    - cron: '0 9 * * *'  # 実行時刻を調整

# 環境変数の設定
env:
  PYTHON_VERSION: '3.11'  # Pythonバージョンを調整
```

### 2. 解析パターンのカスタマイズ

`tools/github_actions_ai_analyzer_enhanced.py`のパターンを調整：

```python
self.patterns = {
    # 既存のパターン
    "error": r"ERROR|FAILED|FAILURE|exit code 1",

    # プロジェクト固有のパターンを追加
    "project_specific": r"your_pattern_here",

    # 言語固有のパターン
    "python_error": r"Python.*error|SyntaxError|ImportError",
    "javascript_error": r"npm.*error|yarn.*error|node.*error",
    "java_error": r"maven.*error|gradle.*error|compilation.*error"
}
```

### 3. 品質メトリクスの調整

品質スコアの計算方法をカスタマイズ：

```python
# 品質スコアの重み付けを調整
quality_weights = {
    "test_coverage": 0.3,
    "build_success_rate": 0.25,
    "error_frequency": 0.2,
    "warning_frequency": 0.15,
    "performance_score": 0.1
}
```

## 📊 使用方法

### 1. 手動実行

GitHub Actionsの手動実行：

1. GitHubリポジトリの「Actions」タブに移動
2. 「AI Quality Improvement」ワークフローを選択
3. 「Run workflow」ボタンをクリック
4. 実行結果を確認

### 2. 自動実行

スケジュール実行の設定：

```yaml
# 毎日午前9時に実行
schedule:
  - cron: '0 9 * * *'

# 毎週月曜日の午前9時に実行
schedule:
  - cron: '0 9 * * 1'
```

### 3. プルリクエスト時の実行

プルリクエスト作成時に自動実行：

```yaml
on:
  pull_request:
    branches: [ main ]
```

## 📈 結果の確認

### 1. GitHub Actions実行結果

- **AI解析**: 基本的な解析とレポート生成
- **品質改善提案**: 具体的な改善アクションの提案
- **自動修正**: コードフォーマットの自動修正
- **品質レポート**: 包括的な品質レポートの生成

### 2. アーティファクトの確認

実行後に以下のアーティファクトが生成されます：

- `ai-analysis-results`: AI解析結果
- `quality-reports`: 品質レポート

### 3. レポートの内容

生成されるレポートには以下が含まれます：

- **概要**: 総レポート数、成功/失敗数
- **品質メトリクス**: 総合品質スコア
- **共通の問題**: 頻繁に発生する問題
- **改善提案**: 具体的な修正アクション
- **自動改善アクション**: 推奨される自動化

## 🔍 トラブルシューティング

### 1. よくある問題

**問題**: AI解析ツールが実行されない
**解決策**:
- Pythonパスの確認
- 依存関係のインストール確認
- ファイルパスの確認

**問題**: レポートが生成されない
**解決策**:
- レポートディレクトリの存在確認
- 権限設定の確認
- ログファイルの確認

**問題**: 品質スコアが期待と異なる
**解決策**:
- パターンマッチングの調整
- 重み付けの調整
- 基準値の見直し

### 2. デバッグ方法

```bash
# ローカルでの実行
python tools/github_actions_ai_analyzer_enhanced.py

# 詳細ログの有効化
export LOG_LEVEL=DEBUG
python tools/github_actions_ai_analyzer_enhanced.py

# 特定のレポートのみ解析
python -c "
from tools.github_actions_ai_analyzer_enhanced import EnhancedGitHubActionsAnalyzer
analyzer = EnhancedGitHubActionsAnalyzer()
result = analyzer.analyze_ci_report('reports/ci_report_20250802_083932.json')
print(result)
"
```

## 🚀 拡張機能

### 1. カスタム解析ルール

プロジェクト固有の解析ルールを追加：

```python
def add_custom_patterns(self):
    """カスタムパターンを追加"""
    self.patterns.update({
        "custom_error": r"your_custom_error_pattern",
        "business_logic_error": r"business.*error|logic.*error"
    })
```

### 2. 外部API連携

他のサービスとの連携：

```python
def integrate_with_external_services(self):
    """外部サービスとの連携"""
    # Slack通知
    # Jira連携
    # メール通知
    pass
```

### 3. 機械学習による予測

MLモデルによる品質予測：

```python
def predict_quality_trends(self):
    """品質トレンドの予測"""
    # 過去のデータを分析
    # 将来の品質を予測
    # 改善提案を生成
    pass
```

## 📞 サポート

### 1. 問題の報告

GitHub Issuesで問題を報告：

1. [GitHub Actions AI Analyzer Issues](https://github.com/scottlz0310/Github-Actions-AI-Analyzer/issues)
2. 問題の詳細な説明
3. 再現手順の提供
4. ログファイルの添付

### 2. 貢献

プルリクエストでの貢献：

1. 機能ブランチの作成
2. 変更の実装
3. テストの追加
4. ドキュメントの更新
5. プルリクエストの作成

### 3. 連絡先

- **Email**: scottlz0310@gmail.com
- **GitHub**: [@scottlz0310](https://github.com/scottlz0310)
- **Issues**: [GitHub Issues](https://github.com/scottlz0310/Github-Actions-AI-Analyzer/issues)

## 📄 ライセンス

この統合機能はMITライセンスの下で提供されています。

---

⭐ この統合ガイドが役に立ったら、リポジトリにスターを付けてください！
