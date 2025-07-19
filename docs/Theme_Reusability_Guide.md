# PhotoGeoView テーマシステム - 他プロジェクトでの再利用ガイド

## 🎨 現在のPhotoGeoViewテーマシステムの再利用可能性

### 📊 現在の実装状況

**✅ 再利用可能な機能:**
- 設定ファイル（JSON）ベースのテーマ管理
- テーマ名・カテゴリ管理システム
- ダーク/ライト切り替え機能
- テーマ状態の永続化

**⚠️ 制限事項:**
- カラーバリエーションは実質2種類（Dark/Light）のみ
- Qt Theme Manager未使用のフォールバック実装

## 🔧 他プロジェクトでの使用方法

### 1. **設定ファイルのカスタマイズ**

#### プロジェクト専用設定ファイルの作成
```json
{
    "ui": {
        "current_theme": "custom_dark.xml",
        "theme_manager_enabled": true,
        "selected_themes": [
            "custom_dark.xml",
            "custom_light.xml",
            "company_blue.xml"
        ],
        "theme_toggle_index": 0
    }
}
```

#### カスタムテーマ定義
```python
# カスタムテーマ設定をThemeManagerに追加
class CustomThemeManager(ThemeManager):
    def __init__(self, custom_themes=None):
        super().__init__()

        if custom_themes:
            self.available_themes = custom_themes
            self._rebuild_categories()
            self._rebuild_display_names()

    def _rebuild_categories(self):
        """カスタムテーマでカテゴリを再構築"""
        self.theme_categories = {
            'dark': [t for t in self.available_themes if 'dark' in t.lower()],
            'light': [t for t in self.available_themes if 'light' in t.lower()],
            'custom': [t for t in self.available_themes if 'custom' in t.lower()]
        }
```

### 2. **プロジェクト専用テーマの追加**

#### カスタムテーマ定義ファイル
```python
# project_themes.py
CUSTOM_THEMES = {
    "company_dark": {
        "name": "company_dark.xml",
        "display_name": "Company Dark",
        "category": "dark",
        "colors": {
            "primary": "#1a1a1a",
            "secondary": "#333333",
            "accent": "#0066cc",  # 企業カラー
            "text": "#ffffff"
        }
    },
    "company_light": {
        "name": "company_light.xml",
        "display_name": "Company Light",
        "category": "light",
        "colors": {
            "primary": "#ffffff",
            "secondary": "#f5f5f5",
            "accent": "#0066cc",  # 企業カラー
            "text": "#333333"
        }
    }
}
```

#### カスタムCSSの拡張
```python
def _get_custom_stylesheet(self, theme_config):
    """カスタムテーマ設定からCSSを生成"""
    colors = theme_config["colors"]

    return f"""
    QMainWindow {{
        background-color: {colors["primary"]};
        color: {colors["text"]};
    }}
    QToolBar QToolButton:checked {{
        background-color: {colors["accent"]};
        color: white;
    }}
    /* ... 他のスタイル定義 */
    """
```

### 3. **設定ファイル構造のカスタマイズ**

#### プロジェクト固有の設定クラス
```python
@dataclass
class CustomUISettings(UISettings):
    """プロジェクト専用UI設定"""
    custom_themes: List[Dict] = field(default_factory=list)
    brand_colors: Dict[str, str] = field(default_factory=dict)
    company_theme_enabled: bool = True

    def add_custom_theme(self, theme_config):
        """カスタムテーマを追加"""
        self.custom_themes.append(theme_config)

    def set_brand_colors(self, colors):
        """ブランドカラーを設定"""
        self.brand_colors.update(colors)
```

### 4. **動的テーマ管理**

#### プロジェクト起動時の設定読み込み
```python
class ProjectThemeManager:
    def __init__(self, config_file="project_config.json"):
        self.config_file = config_file
        self.load_project_themes()

    def load_project_themes(self):
        """プロジェクト専用テーマ設定を読み込み"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            # カスタムテーマを追加
            if "custom_themes" in config:
                self.register_custom_themes(config["custom_themes"])

        except FileNotFoundError:
            self.create_default_config()

    def register_custom_themes(self, themes):
        """カスタムテーマを登録"""
        for theme_name, theme_config in themes.items():
            self.theme_manager.add_custom_theme(theme_name, theme_config)
```

## 🌈 実用例

### A. **企業アプリケーション**
```python
# 企業ブランドカラーに合わせたテーマ
CORPORATE_THEMES = [
    "corporate_dark.xml",
    "corporate_light.xml",
    "corporate_blue.xml"  # 企業カラー
]
```

### B. **個人プロジェクト**
```python
# 好みに合わせたカスタムテーマ
PERSONAL_THEMES = [
    "midnight_purple.xml",
    "sunrise_orange.xml",
    "forest_green.xml"
]
```

### C. **アプリケーション群**
```python
# 複数アプリで統一されたテーマ
SUITE_THEMES = [
    "suite_professional.xml",
    "suite_casual.xml",
    "suite_accessibility.xml"  # アクセシビリティ対応
]
```

## 🚀 実装手順

### 1. **既存コードの流用**
```bash
# PhotoGeoViewから必要なファイルをコピー
cp src/ui/theme_manager.py your_project/
cp src/core/settings.py your_project/
cp config/config.json your_project/config/
```

### 2. **プロジェクト専用に修正**
- テーマリストをカスタマイズ
- 設定ファイル構造を調整
- カスタムCSSスタイルを定義

### 3. **テーマ設定ファイルの準備**
```json
{
    "themes": {
        "available_themes": ["theme1.xml", "theme2.xml"],
        "theme_categories": {
            "professional": ["pro_dark.xml", "pro_light.xml"],
            "casual": ["casual_blue.xml", "casual_green.xml"]
        },
        "custom_colors": {
            "brand_primary": "#0066cc",
            "brand_secondary": "#004499"
        }
    }
}
```

## 📋 現在の制約と対応

### **制約事項:**
- カラーバリエーションはCSS-basedのため限定的
- Qt Theme Manager本来の機能は未使用

### **対応方法:**
1. **段階的改善**: 基本機能から始めて徐々に拡張
2. **CSS拡張**: より詳細なカラーカスタマイズ
3. **設定ファイル活用**: JSON設定での柔軟な管理

## ✅ まとめ

PhotoGeoViewのテーマシステムは、**設定ファイルベース**で他プロジェクトでも再利用可能です。現在はダーク/ライトの2種類の実装ですが、設定ファイルとCSSカスタマイズにより、プロジェクトごとの要件に対応できる柔軟な基盤が整っています。
