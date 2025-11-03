# PhotoGeoView モダン化計画

**作成日**: 2025年11月3日  
**現状分析と将来へのロードマップ**

---

## 📊 現状分析

### ✅ 良好な点
- uv.lockファイルが存在（uvは部分的に導入済み）
- Python 3.14.0環境（最新）
- ruff + mypyへの移行完了（モダンなlintツール）
- PEP 621準拠のpyproject.toml
- PEP 735のdependency-groups採用
- src/レイアウト採用（一部）

### ⚠️ 改善が必要な点

#### 1. **プロジェクト構造の古さ**
- ✗ ルートにmain.pyエントリーポイント（アンチパターン）
- ✗ `src/`配下に`__main__.py`がない
- ✗ `python -m photogeoview`で実行できない
- ✗ パッケージ構造が不明瞭

#### 2. **ビルドシステムの古さ**
- ✗ setuptools + wheel（レガシー）
- ✗ hatchling, PDM, Poetry等のモダンバックエンド未使用
- △ uv統合が中途半端

#### 3. **依存関係管理の問題**
- △ バージョン指定が緩い（`>=`のみ）
- ✗ 依存関係のロックが不完全
- ✗ dev依存とci依存が分離されているが、ci用途が不明瞭

#### 4. **技術スタックの古さ**
```toml
requires-python = ">=3.9"  # 3.9は2025年10月にEOL
Pillow>=9.0.0              # 古いバージョン（最新は10.x）
ExifRead>=3.3.2            # メンテナンス停止気味
folium>=0.14.0             # 古い（最新は0.18.x）
```

#### 5. **型ヒントとモダンPython機能**
- ？ Python 3.10+の機能（match文、Union演算子等）未使用の可能性
- ？ 型ヒント（PEP 604, 585）の一貫性
- ✗ target-version が "py39"（古い）

#### 6. **開発ツールチェーン**
- △ pre-commitは設定済みだが、最新版か不明
- ✗ CI/CDパイプラインの状態が不明
- ✗ コンテナ化（Docker）なし

---

## 📝 実施履歴

### ✅ Phase 2完了 (2025-11-03)
**ビルドシステムのモダン化**

実施内容:
1. ✅ setuptools + wheel → hatchling に移行
2. ✅ [tool.hatch.build.targets.wheel] 設定追加
3. ✅ [tool.hatch.build.targets.sdist] 設定追加
4. ✅ uv統合の完全化
   - `uv sync` で依存関係同期
   - `uv build` でビルド実行
5. ✅ Makefile更新
   - `make install` → `uv sync --all-groups`
   - `make build` → `uv build`

ビルド成果物:
- `photogeoview-1.0.0-py3-none-any.whl` (285KB)
- `photogeoview-1.0.0.tar.gz` (410KB)

テスト結果: ✅ 正常動作確認済み

---

## 🎯 モダン化ロードマップ

### Phase 1: プロジェクト構造の再編 (優先度: 🔴 HIGH)

#### 1.1 モダンなエントリーポイント構造
```
現状:
PhotoGeoView/
├── main.py                    # ❌ ルートにエントリーポイント
└── src/
    ├── core/
    ├── ui/
    └── integration/

目標:
PhotoGeoView/
└── src/
    └── photogeoview/          # パッケージ名を明確に
        ├── __init__.py
        ├── __main__.py        # ✅ python -m photogeoview
        ├── cli.py             # CLI実装
        ├── app.py             # アプリケーション本体
        ├── core/
        ├── ui/
        └── integration/
```

**実行方法**:
```bash
# 従来
python main.py

# モダン
python -m photogeoview
uv run photogeoview
photogeoview  # console_scripts経由
```

#### 1.2 パッケージ名の明確化
- `src/` 直下に複数ディレクトリ → `src/photogeoview/` に統合
- importパスを `from core.xxx` → `from photogeoview.core.xxx` に統一

---

### Phase 2: ビルドシステムのモダン化 (優先度: 🔴 HIGH)

#### 2.1 hatchling への移行
setuptools → hatchling（Python Packaging Authorityの推奨）

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/photogeoview"]
```

**メリット**:
- ✅ 高速ビルド
- ✅ 設定がシンプル
- ✅ uvとの相性が良い
- ✅ メンテナンス活発

#### 2.2 完全なuv統合
```bash
# 依存関係管理
uv pip compile pyproject.toml -o requirements.txt
uv pip sync requirements.txt

# 開発環境
uv venv
uv pip install -e ".[dev]"

# スクリプト実行
uv run photogeoview
uv run pytest
uv run ruff check
```

---

### Phase 3: 依存関係の最新化 (優先度: 🟡 MEDIUM)

#### 3.1 Python最小バージョンの引き上げ
```toml
requires-python = ">=3.10"  # 3.9はEOL、3.10推奨
# または
requires-python = ">=3.11"  # パフォーマンス向上大
```

#### 3.2 依存関係の更新
```toml
dependencies = [
    "PySide6>=6.9.1,<7.0",          # 上限指定
    "Pillow>=10.0.0,<11.0",         # 最新メジャー
    "piexif>=1.1.0,<2.0",           # ExifRead → piexif検討
    "folium>=0.18.0,<0.19",         # 最新版
    "psutil>=6.0.0,<7.0",           # 最新版
    "qt-theme-manager>=0.2.4,<0.3",
    "breadcrumb-addressbar>=0.2.1,<0.3",
]
```

#### 3.3 dependency-groupsの整理
```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=6.0.0",
    "pytest-qt>=4.4.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "pre-commit>=4.0.0",
]
test = [
    "pytest>=8.0.0",
    "pytest-cov>=6.0.0",
    "pytest-qt>=4.4.0",
    "pytest-xdist>=3.6.0",
]
lint = [
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]
security = [
    "bandit[toml]>=1.8.0",
    "safety>=3.0.0",
]
```

---

### Phase 4: モダンPython機能の活用 (優先度: 🟢 LOW)

#### 4.1 型ヒントの最新化
```python
# 古い
from typing import Union, Optional, List, Dict
def func(x: Union[str, int]) -> Optional[List[Dict[str, int]]]:
    ...

# モダン (Python 3.10+)
def func(x: str | int) -> list[dict[str, int]] | None:
    ...
```

#### 4.2 構造化パターンマッチング (Python 3.10+)
```python
# 古い
if isinstance(value, str):
    handle_string(value)
elif isinstance(value, int):
    handle_int(value)

# モダン
match value:
    case str():
        handle_string(value)
    case int():
        handle_int(value)
```

#### 4.3 その他のモダン機能
- dataclasses / Pydantic v2
- asyncio（適用可能な箇所）
- walrus演算子 `:=`
- f-string debugging `f"{var=}"`

---

### Phase 5: 開発ツールチェーンの強化 (優先度: 🟡 MEDIUM)

#### 5.1 タスクランナーの導入
**Option A: taskipy** (シンプル)
```toml
[tool.taskipy.tasks]
dev = "uv run photogeoview"
test = "uv run pytest"
lint = "uv run ruff check src/"
format = "uv run ruff format src/"
type-check = "uv run mypy src/"
```

**Option B: just** (Makefileの代替)
```justfile
# justfile
dev:
    uv run photogeoview

test:
    uv run pytest

lint:
    uv run ruff check src/
```

#### 5.2 pre-commit設定の最新化
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0  # 最新版に更新
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0  # 最新版
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

#### 5.3 GitHub Actions CI/CD
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest
```

---

### Phase 6: 配布パッケージング (優先度: � MEDIUM)

> **注**: Docker化は不要との結論に至りました。
> - デスクトップGUIアプリにDockerは不適切（X11フォワーディング等の複雑さ）
> - PySide6のリアルタイム性・スライダー操作にはネイティブ実行が必須
> - クロスプラットフォーム対応はPySide6自体の機能で十分

#### 6.1 PyInstallerによるネイティブビルド

**設定ファイル作成**: `photogeoview.spec`

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/photogeoview/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('config', 'config'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PhotoGeoView',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUIアプリなのでコンソール非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # Windows
)

# macOS向けアプリバンドル
app = BUNDLE(
    exe,
    name='PhotoGeoView.app',
    icon='assets/icon.icns',  # macOS
    bundle_identifier='com.photogeoview.app',
)
```

**ビルドコマンド**:
```bash
# 単一実行ファイル
pyinstaller photogeoview.spec

# または
uv run pyinstaller photogeoview.spec
```

#### 6.2 プラットフォーム別パッケージ

##### Windows
- **実行ファイル**: `PhotoGeoView.exe`
- **インストーラー**: Inno Setup / WiX Toolset
- **配布**: GitHub Releases / Microsoft Store（将来的）

##### macOS
- **アプリバンドル**: `PhotoGeoView.app`
- **配布形式**: `.dmg` イメージ
- **署名**: Apple Developer証明書（公開配布時）

##### Linux
- **AppImage**: 単一実行ファイル（推奨）
- **Flatpak**: サンドボックス、配布容易
- **Snap**: Ubuntu系での配布
- **.deb / .rpm**: 伝統的なパッケージ形式

#### 6.3 GitHub Actionsでの自動ビルド

```yaml
# .github/workflows/build-release.yml
name: Build Release Packages

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies
        run: |
          uv sync
          uv pip install pyinstaller
      - name: Build executable
        run: uv run pyinstaller photogeoview.spec
      - name: Create installer (optional)
        run: |
          # Inno Setupでインストーラー作成
          iscc setup-windows.iss
      - uses: actions/upload-artifact@v4
        with:
          name: PhotoGeoView-Windows
          path: dist/PhotoGeoView.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies
        run: |
          uv sync
          uv pip install pyinstaller
      - name: Build app bundle
        run: uv run pyinstaller photogeoview.spec
      - name: Create DMG
        run: |
          # create-dmgで.dmg作成
          npm install -g create-dmg
          create-dmg dist/PhotoGeoView.app dist/
      - uses: actions/upload-artifact@v4
        with:
          name: PhotoGeoView-macOS
          path: dist/*.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Install dependencies
        run: |
          uv sync
          uv pip install pyinstaller
      - name: Build executable
        run: uv run pyinstaller photogeoview.spec
      - name: Create AppImage
        run: |
          # AppImageでパッケージング
          wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
          chmod +x linuxdeploy-x86_64.AppImage
          ./linuxdeploy-x86_64.AppImage --appdir dist/PhotoGeoView --output appimage
      - uses: actions/upload-artifact@v4
        with:
          name: PhotoGeoView-Linux
          path: "*.AppImage"

  create-release:
    needs: [build-windows, build-macos, build-linux]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            PhotoGeoView-Windows/PhotoGeoView.exe
            PhotoGeoView-macOS/*.dmg
            PhotoGeoView-Linux/*.AppImage
```

#### 6.4 代替案: briefcase

PyInstallerの代替として、BeeWareの**briefcase**も検討可能：

```toml
# pyproject.toml
[tool.briefcase]
project_name = "PhotoGeoView"
bundle = "com.photogeoview"
version = "1.0.0"
url = "https://github.com/scottlz0310/PhotoGeoView"
license = "MIT"
author = "AI Integration Team"
author_email = "ai-team@photogeoview.com"

[tool.briefcase.app.photogeoview]
formal_name = "PhotoGeoView"
description = "AI統合写真地理情報ビューア"
sources = ["src/photogeoview"]
```

**ビルドコマンド**:
```bash
briefcase create      # プロジェクト構造作成
briefcase build       # ビルド
briefcase package     # パッケージング
briefcase run         # テスト実行
```

**メリット**:
- ✅ クロスプラットフォーム対応が統一的
- ✅ ストア配布（iOS/Android App Store）にも対応
- ✅ 設定がシンプル

---

## 📅 実装スケジュール

### Week 1: 基盤の再構築
- [ ] Phase 1.1: プロジェクト構造の再編
- [ ] Phase 1.2: パッケージ名の明確化
- [ ] Phase 2.1: hatchling移行

### Week 2: 依存関係の整理
- [ ] Phase 2.2: uv完全統合
- [ ] Phase 3.1: Python最小バージョン引き上げ
- [ ] Phase 3.2: 依存関係の更新
- [ ] Phase 3.3: dependency-groups整理

### Week 3: コード品質向上
- [ ] Phase 4: モダンPython機能の適用（漸進的）
- [ ] Phase 5.1: タスクランナー導入
- [ ] Phase 5.2: pre-commit更新

### Week 4: CI/CD・パッケージング
- [ ] Phase 5.3: GitHub Actions CI/CD設定
- [ ] Phase 6: 配布パッケージング（PyInstaller/briefcase）
- [ ] ドキュメント更新

---

## 🔄 移行戦略

### 段階的移行（推奨）
1. ✅ **後方互換性を保ちながら段階的に移行**
2. ✅ 各Phaseごとにテスト・検証
3. ✅ ドキュメント同時更新

### 一括移行（リスク高）
- ⚠️ 大規模な変更を一度に実施
- ⚠️ デバッグが困難
- ❌ 非推奨

---

## 💡 即座に実施可能な改善

### 今すぐできること（1時間以内）

1. **pyproject.tomlの小改善**
   ```toml
   [tool.ruff]
   target-version = "py310"  # py39 → py310
   line-length = 120
   ```

2. **依存関係のバージョン上限追加**
   ```toml
   "PySide6>=6.9.1,<7.0"  # 上限追加
   ```

3. **pre-commit自動更新**
   ```bash
   pre-commit autoupdate
   ```

4. **GitHub Actions基本設定追加**

---

## 🎓 参考資料

### パッケージング・ビルド
- [Python Packaging Guide](https://packaging.python.org/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Hatchling Documentation](https://hatch.pypa.io/)
- [PyInstaller Manual](https://pyinstaller.org/)
- [BeeWare Briefcase](https://briefcase.readthedocs.io/)

### コード品質
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)

### 標準とベストプラクティス
- [PEP 621](https://peps.python.org/pep-0621/) - Storing project metadata in pyproject.toml
- [PEP 735](https://peps.python.org/pep-0735/) - Dependency Groups
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)

### CI/CDと配布
- [GitHub Actions](https://docs.github.com/en/actions)
- [AppImage Documentation](https://docs.appimage.org/)
- [Flatpak Documentation](https://docs.flatpak.org/)

---

## ✅ 成功指標

モダン化完了時の状態:

### 構造とビルド
- ✅ `python -m photogeoview` で実行可能
- ✅ `uv run photogeoview` で実行可能
- ✅ hatchlingビルドバックエンド
- ✅ src/photogeoview/ パッケージ構造

### 依存関係と互換性
- ✅ Python 3.10+ 最小バージョン
- ✅ 依存関係に上限指定
- ✅ uv.lock完全統合

### 開発ツール
- ✅ GitHub Actions CI/CD稼働
- ✅ pre-commit hooks最新版
- ✅ ruff + mypy統合
- ✅ ruff target-version py310+

### 配布
- ✅ PyInstaller/briefcase設定完備
- ✅ クロスプラットフォームビルド自動化
- ✅ Windows .exe / macOS .app / Linux AppImage

### ドキュメント
- ✅ 型ヒント完全対応
- ✅ ドキュメント最新化
- ✅ ユーザーガイド更新

---

**次のステップ**: Phase 1から段階的に実装を開始しますか？
