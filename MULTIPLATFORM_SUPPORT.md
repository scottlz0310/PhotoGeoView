# PhotoGeoView マルチプラットフォーム対応

## 🎯 概要

PhotoGeoView AI統合版は、Windows、macOS、Linuxの3つの主要プラットフォームで動作するように設計されています。

## 🖥️ 対応プラットフォーム

| プラットフォーム | 対応状況 | Python版本 | 特記事項 |
|------------------|----------|------------|----------|
| **Linux (Ubuntu)** | ✅ 完全対応 | 3.9, 3.10, 3.11 | X11/Wayland対応 |
| **Windows** | ✅ 完全対応 | 3.9, 3.10, 3.11 | Windows 10/11推奨 |
| **macOS** | ✅ 完全対応 | 3.10, 3.11 | Intel/Apple Silicon対応 |

## 🚀 セットアップ手順

### 共通手順

1. **リポジトリのクローン**
```bash
git clone https://github.com/scottlz0310/PhotoGeoView.git
cd PhotoGeoView
```

2. **Python仮想環境の作成**
```bash
python -m venv venv
```

3. **仮想環境の有効化**
```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

4. **依存関係のインストール**
```bash
pip install -r requirements.txt
```

5. **プラットフォーム固有セットアップ**
```bash
python scripts/setup_platform.py
```

### Linux固有の手順

```bash
# システム依存関係のインストール
sudo apt-get update
sudo apt-get install -y xvfb libxkbcommon-x11-0 libxcb-icccm4 \
  libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-xinerama0 libxcb-xinput0 libxcb-xfixes0 libgl1-mesa-glx \
  libegl1-mesa libxrandr2 libxss1 libxcursor1 libxcomposite1 \
  libxi6 libxtst6

# アプリケーション起動
python main.py
```

### Windows固有の手順

```cmd
REM Visual C++ Redistributableが必要な場合があります
REM https://aka.ms/vs/17/release/vc_redist.x64.exe

REM アプリケーション起動
python main.py
```

### macOS固有の手順

```bash
# Homebrewでの依存関係インストール（オプション）
brew install qt6

# アプリケーション起動
python main.py
```

## 📦 パッケージ作成

### 全プラットフォーム共通

```bash
# PyInstallerのインストール
pip install pyinstaller

# パッケージ作成
python scripts/build_package.py
```

### プラットフォーム別出力

| プラットフォーム | 出力形式 | ファイル名 |
|------------------|----------|------------|
| Linux | AppImage | `PhotoGeoView-Linux.AppImage` |
| Windows | 実行ファイル | `PhotoGeoView.exe` |
| macOS | アプリケーション | `PhotoGeoView.app` |

## 🔧 CI/CD パイプライン

### GitHub Actions ワークフロー

- **ファイル**: `.github/workflows/multiplatform-ci.yml`
- **トリガー**: push, pull_request, manual dispatch
- **マトリックス**: 3プラットフォーム × 3Python版本

### テスト戦略

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ['3.9', '3.10', '3.11']
```

### 自動化されたチェック

1. **コード品質**: Black, isort, flake8, mypy
2. **単体テスト**: pytest with coverage
3. **統合テスト**: プラットフォーム固有テスト
4. **パッケージング**: 自動ビルド・アーティファクト生成

## 🐛 プラットフォーム固有の問題と解決策

### Linux

**問題**: X11ディスプレイが利用できない
```bash
# 解決策: 仮想ディスプレイの使用
export QT_QPA_PLATFORM=offscreen
# または
xvfb-run -a python main.py
```

**問題**: Qt依存関係の不足
```bash
# 解決策: 必要なパッケージのインストール
sudo apt-get install -y libxkbcommon-x11-0 libxcb-*
```

### Windows

**問題**: DLLが見つからない
```
# 解決策: Visual C++ Redistributableのインストール
# Microsoft公式サイトからダウンロード
```

**問題**: パスの区切り文字
```python
# 解決策: os.path.joinまたはPathlibの使用
from pathlib import Path
path = Path("folder") / "file.txt"
```

### macOS

**問題**: Qt plugin pathが見つからない
```bash
# 解決策: 環境変数の設定
export QT_QPA_PLATFORM_PLUGIN_PATH=$(python -c "import PyQt6; print(PyQt6.__path__[0])")/Qt6/plugins
```

**問題**: Apple Siliconでの互換性
```bash
# 解決策: Universal2バイナリまたはネイティブビルド
arch -arm64 python main.py  # Apple Silicon
arch -x86_64 python main.py # Intel Mac
```

## 📊 パフォーマンス比較

| プラットフォーム | 起動時間 | メモリ使用量 | パッケージサイズ |
|------------------|----------|--------------|------------------|
| Linux | ~2.5秒 | ~150MB | ~80MB |
| Windows | ~3.0秒 | ~180MB | ~120MB |
| macOS | ~2.8秒 | ~160MB | ~100MB |

*注: 実際の値は環境により異なります*

## 🔍 デバッグとトラブルシューティング

### 共通デバッグコマンド

```bash
# プラットフォーム情報の確認
python scripts/setup_platform.py

# 詳細ログでの実行
python main.py --debug --verbose

# Qt環境の確認
python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication([])
print('Qt version:', app.applicationVersion())
print('Platform:', sys.platform)
"
```

### ログファイルの場所

- **Linux**: `~/.local/share/PhotoGeoView/logs/`
- **Windows**: `%APPDATA%\PhotoGeoView\logs\`
- **macOS**: `~/Library/Application Support/PhotoGeoView/logs/`

## 🤝 コントリビューション

### プラットフォーム固有のテスト追加

1. `tests/platform_specific/` にテストファイルを追加
2. CI/CDワークフローでの自動実行を確認
3. プラットフォーム固有の問題をIssueで報告

### 新しいプラットフォームの追加

1. `scripts/setup_platform.py` に新しいプラットフォーム検出を追加
2. CI/CDマトリックスに新しいランナーを追加
3. パッケージング手順を `scripts/build_package.py` に追加

## 📚 参考資料

- [PyQt6 Documentation](https://doc.qt.io/qtforpython/)
- [PyInstaller Manual](https://pyinstaller.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Qt Cross-platform Development](https://doc.qt.io/qt-6/supported-platforms.html)

## 📝 更新履歴

| 日付 | 版本 | 変更内容 |
|------|------|----------|
| 2025-08-01 | 1.0.0 | 初回マルチプラットフォーム対応 |

---

**開発チーム**: GitHub Copilot (CS4Coding), Cursor (CursorBLD), Kiro
**最終更新**: 2025-08-01
