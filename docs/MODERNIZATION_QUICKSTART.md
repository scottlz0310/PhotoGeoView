# PhotoGeoView モダン化: クイックスタートガイド

このガイドでは、モダン化計画の**Phase 1**を実装します。

## 🎯 Phase 1: プロジェクト構造の再編

### 実装内容

1. `src/photogeoview/` パッケージ構造の作成
2. `__main__.py` エントリーポイントの追加
3. `cli.py` コマンドラインインターフェースの実装
4. ルートの `main.py` の段階的廃止

### 作業手順

#### Step 1: 新しいパッケージ構造を作成

```bash
# 新しいディレクトリ構造
mkdir -p src/photogeoview
```

#### Step 2: 既存コードの移動

```bash
cd src
# core, ui, integration を photogeoview/ 配下に移動
mv core ui integration photogeoview/
```

#### Step 3: __init__.py の作成

`src/photogeoview/__init__.py` を作成し、パッケージメタデータを定義

#### Step 4: __main__.py の作成

`src/photogeoview/__main__.py` を作成し、エントリーポイントを実装

#### Step 5: pyproject.toml の更新

- `[project.scripts]` のエントリーポイントを更新
- パッケージパスを修正

#### Step 6: テストとインポートパスの更新

- すべてのインポート文を更新
- `from core.xxx` → `from photogeoview.core.xxx`

### 実行方法の変化

```bash
# 古い方法（廃止予定）
python main.py

# 新しい方法
python -m photogeoview
uv run python -m photogeoview
photogeoview  # コマンドラインツールとして
```

---

## 次のステップ

このPhase 1を実装しますか？それとも、まず小さな改善から始めますか？

1. **Phase 1を今すぐ実装** - 構造的な大改善
2. **小さな改善から開始** - pyproject.tomlの微調整、依存関係の更新など
