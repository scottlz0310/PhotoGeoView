# PhotoGeoView テーマシステム実装詳細

## 🎨 現在のテーマシステム実装

### 📁 設定ファイルベースの管理

#### config.json でのテーマ管理
```json
{
    "ui": {
        "current_theme": "dark_blue.xml",
        "theme_manager_enabled": true,
        "selected_themes": [
            "light_blue.xml",
            "dark_blue.xml"
        ],
        "theme_toggle_index": 1,
        // ... その他のUI設定
    }
}
```

**設定項目の詳細:**
- `current_theme`: 現在適用中のテーマ名
- `theme_manager_enabled`: テーマ管理機能の有効/無効
- `selected_themes`: ユーザーが選択したテーマリスト（循環切り替え用）
- `theme_toggle_index`: 現在の切り替えインデックス

### 🔧 フォールバックテーマシステム

Qt Theme Managerが利用できない場合、独自のCSS-basedテーマシステムを使用：

#### 1. テーマ分類システム
```python
# 16種類のテーマを2つのカテゴリに分類
Dark Themes (8):
- dark_blue.xml, dark_cyan.xml, dark_lightgreen.xml, dark_orange.xml
- dark_pink.xml, dark_purple.xml, dark_red.xml, dark_teal.xml

Light Themes (8):
- light_blue.xml, light_cyan.xml, light_cyan_500.xml, light_lightgreen.xml
- light_orange.xml, light_pink.xml, light_purple.xml, light_red.xml
```

#### 2. 動的CSS生成
```python
def _apply_fallback_theme(self, theme_name: str) -> bool:
    # ベーススタイルシートを選択
    if 'dark' in theme_name.lower():
        stylesheet = self._get_dark_stylesheet()
    else:
        stylesheet = self._get_light_stylesheet()

    # カラーバリエーションを適用
    color_variant = self._extract_color_from_theme_name(theme_name)
    stylesheet = self._apply_color_variant(stylesheet, color_variant)

    # アプリケーションに適用
    app.setStyleSheet(stylesheet)
    return True
```

### 🎨 CSSテーマシステムの詳細

#### ダークテーマのベーススタイル
```css
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}
QFrame {
    background-color: #3c3c3c;
    border: 1px solid #555555;
}
QToolBar {
    background-color: #404040;
    border: none;
}
QToolBar QToolButton {
    background-color: #505050;
    border: 1px solid #666666;
    border-radius: 3px;
    padding: 5px;
    margin: 2px;
}
QToolBar QToolButton:hover {
    background-color: #606060;
}
```

#### ライトテーマのベーススタイル
```css
QMainWindow {
    background-color: #f0f0f0;
    color: #000000;
}
QFrame {
    background-color: #ffffff;
    border: 1px solid #cccccc;
}
QToolBar {
    background-color: #e6e6e6;
    border: none;
}
QToolBar QToolButton {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 5px;
    margin: 2px;
}
```

### 🌈 カラーバリエーションシステム

#### 色別アクセントカラー
```python
color_map = {
    'blue': '#3f7cac',      # ブルー系
    'cyan': '#17a2b8',      # シアン系
    'lightgreen': '#28a745', # グリーン系
    'orange': '#fd7e14',    # オレンジ系
    'pink': '#e83e8c',      # ピンク系
    'purple': '#6f42c1',    # パープル系
    'red': '#dc3545',       # レッド系
    'teal': '#20c997'       # ティール系
}
```

#### 動的カラー適用
```css
QToolBar QToolButton:checked {
    background-color: {accent_color};
    color: white;
}
QPushButton:pressed {
    background-color: {accent_color};
    color: white;
}
```

### ⚙️ 実装の特徴

#### 1. **設定ベース管理**
- JSON設定ファイルでテーマ状態を永続化
- ユーザー選択テーマの記憶機能
- 循環切り替えのインデックス管理

#### 2. **フォールバックシステム**
- Qt Theme Manager利用不可時の自動切り替え
- CSS-basedの独自テーマエンジン
- 16テーマ全対応の完全互換性

#### 3. **動的スタイル生成**
- テーマ名から自動でカラーバリエーション抽出
- ベーススタイル + カラーアクセントの組み合わせ
- リアルタイムCSS適用

#### 4. **カテゴリ管理**
- Dark/Light テーマの自動分類
- カテゴリ間の智能的切り替え
- ユーザーフレンドリーな表示名

### 🔄 テーマ切り替えフロー

```
1. ユーザーがテーマ切り替えを要求
   ↓
2. ThemeController が切り替えロジックを処理
   ↓
3. ThemeManager がテーマを適用
   ├── Qt Theme Manager が利用可能な場合
   │   └── Qt Theme Manager で適用
   └── 利用不可能な場合（現在の状況）
       └── フォールバックCSSシステムで適用
   ↓
4. 設定ファイル（config.json）に状態を保存
   ↓
5. UI要素（ステータスバー等）に反映
```

### 📊 現在の状況

✅ **動作している機能:**
- 16テーマの完全リスト管理
- ダーク/ライト分類システム
- CSSベースのフォールバックテーマ
- 設定ファイルでの状態永続化
- テーマ切り替え・循環機能

⚠️ **制限事項:**
- Qt Theme Manager の高品質テーマは利用不可
- CSSベースのため、制限的なスタイリング
- テーマファイル（.xml）の実際の読み込みは未実装

### 💡 改善案

Qt Theme Manager を完全に活用するには：

1. **テーマファイルの作成**: 16種類の.xmlテーマファイルを作成
2. **Qt Theme Manager初期化修正**: インポート・初期化の問題を解決
3. **混合システム**: Qt Theme Manager + フォールバック の併用

現在の実装は安定して動作しており、基本的なテーマ切り替え機能は完全に実装されています。
