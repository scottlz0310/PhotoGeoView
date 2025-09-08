# CI Simulation Tool

CI/CDパイプラインをローカル環境で事前実行するためのシミュレーションツールです。GitHub Actionsワークフローと同等のチェックをコミット前に実行し、エラーを事前に発見・修正できます。

## プロジェクト構造

```
tools/ci/
├── __init__.py                    # パッケージ初期化
├── models.py                      # コアデータモデル
├── interfaces.py                  # 基底インターフェースと抽象クラス
├── utils.py                       # 共通ユーティリティ関数
├── config_manager.py              # 設定管理 (実装済み)
├── simulator.py                   # メインシミュレーター (未実装)
├── check_orchestrator.py          # チェック統制 (未実装)
├── checkers/                      # チェッカー実装
│   ├── __init__.py
│   ├── code_quality.py           # コード品質チェック (未実装)
│   ├── test_runner.py            # テスト実行 (未実装)
│   ├── security_scanner.py       # セキュリティスキャン (未実装)
│   ├── performance_analyzer.py   # パフォーマンス分析 (未実装)
│   └── ai_component_tester.py    # AIコンポーネントテスト (未実装)
├── environment/                   # 環境管理
│   ├── __init__.py
│   ├── python_manager.py         # Pythonバージョン管理 (未実装)
│   ├── qt_manager.py             # Qt依存関係管理 (未実装)
│   └── display_manager.py        # 仮想ディスプレイ管理 (未実装)
├── reporters/                     # レポート生成
│   ├── __init__.py
│   ├── markdown_reporter.py      # Markdownレポート (未実装)
│   ├── json_reporter.py          # JSONレポート (未実装)
│   └── history_tracker.py        # 履歴追跡 (未実装)
└── templates/                     # テンプレート
    ├── __init__.py
    ├── ci_config_template.yaml    # 設定テンプレート
    ├── report_template.md         # レポートテンプレート
    └── pre_commit_hook.sh         # pre-commitフック (未実装)
```

## 関連ディレクトリ

```
.kiro/ci-history/                  # CI実行履歴保存
reports/ci-simulation/             # 生成されるレポート
logs/                             # ログファイル
```

## コアデータモデル

### CheckResult
個別チェックの実行結果を表現するデータクラス。

```python
@dataclass
class CheckResult:
    name: str                      # チェック名
    status: CheckStatus            # 実行ステータス
    duration: float                # 実行時間（秒）
    output: str                    # 出力内容
    errors: List[str]              # エラーメッセージ
    warnings: List[str]            # 警告メッセージ
    suggestions: List[str]         # 修正提案
    metadata: Dict[str, Any]       # メタデータ
    timestamp: datetime            # 実行時刻
    python_version: Optional[str]  # Pythonバージョン
```

### SimulationResult
CI シミュレーション全体の結果を表現するデータクラス。

```python
@dataclass
class SimulationResult:
    overall_status: CheckStatus           # 全体ステータス
    total_duration: float                 # 総実行時間
    check_results: Dict[str, CheckResult] # 各チェック結果
    python_versions_tested: List[str]     # テスト対象Pythonバージョン
    summary: str                          # サマリー
    report_paths: Dict[str, str]          # レポートファイルパス
    regression_issues: List[RegressionIssue] # 回帰問題
    timestamp: datetime                   # 実行時刻
    configuration: Dict[str, Any]         # 使用した設定
```

### RegressionIssue
パフォーマンス回帰や品質低下を表現するデータクラス。

```python
@dataclass
class RegressionIssue:
    test_name: str                 # テスト名
    baseline_value: float          # ベースライン値
    current_value: float           # 現在値
    regression_percentage: float   # 回帰率
    severity: SeverityLevel        # 重要度
    description: str               # 説明
    metric_type: str               # メトリクス種別
    threshold_exceeded: bool       # 閾値超過フラグ
```

## 基底インターフェース

### CheckerInterface
すべてのチェッカー実装の基底抽象クラス。

```python
class CheckerInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def check_type(self) -> str: ...

    @property
    @abstractmethod
    def dependencies(self) -> List[str]: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def run_check(self, **kwargs) -> CheckResult: ...
```

### EnvironmentManagerInterface
環境管理コンポーネントの基底抽象クラス。

```python
class EnvironmentManagerInterface(ABC):
    @abstractmethod
    def setup_environment(self, requirements: Dict[str, Any]) -> bool: ...

    @abstractmethod
    def cleanup_environment(self) -> None: ...

    @abstractmethod
    def is_environment_ready(self) -> bool: ...
```

### ReporterInterface
レポート生成コンポーネントの基底抽象クラス。

```python
class ReporterInterface(ABC):
    @property
    @abstractmethod
    def format_name(self) -> str: ...

    @property
    @abstractmethod
    def file_extension(self) -> str: ...

    @abstractmethod
    def generate_report(self, result: SimulationResult, output_path: str) -> str: ...
```

## CheckerFactory

チェッカーインスタンスの作成と管理を行うファクトリークラス。

```python
# チェッカーの登録
CheckerFactory.register_checker("code_quality", CodeQualityChecker)

# チェッカーの作成
checker = CheckerFactory.create_checker("code_quality", config)

# 利用可能なチェッカーの取得
available_checkers = CheckerFactory.get_available_checkers()
```

## 例外クラス

- `CISimulationError`: 基底例外クラス
- `CheckerError`: チェッカー実行エラー
- `EnvironmentError`: 環境セットアップエラー
- `ConfigurationError`: 設定関連エラー
- `DependencyError`: 依存関係エラー

## ユーティリティ関数

`utils.py` には以下の共通機能が含まれています：

- `ensure_directory_exists()`: ディレクトリ作成
- `get_project_root()`: プロジェクトルート取得
- `get_python_executable()`: Python実行ファイル検索
- `run_command()`: コマンド実行
- `is_tool_available()`: ツール可用性チェック
- `format_duration()`: 時間フォーマット
- `setup_logging()`: ログ設定
- `get_git_info()`: Git情報取得

## テスト

コアモデルとインターフェースのテストは `test_core_models.py` で実行できます：

```bash
python tools/ci/test_core_models.py
```

## 設定

設定テンプレートは `templates/ci_config_template.yaml` にあります。このテンプレートを参考に、プロジェクト固有の設定ファイルを作成してください。

## 次のステップ

このタスクで作成された基盤の上に、以下のコンポーネントを順次実装していきます：

1. 設定管理システム (ConfigManager) - 実装済み
2. 環境セットアップと管理
3. コード品質チェックシステム
4. テストランナーシステム
5. セキュリティスキャンシステム
6. パフォーマンス分析システム
7. レポートシステム
8. チェック統制システム
9. メインCLIインターフェース

各コンポーネントは、ここで定義されたインターフェースと データモデルを使用して実装されます。
