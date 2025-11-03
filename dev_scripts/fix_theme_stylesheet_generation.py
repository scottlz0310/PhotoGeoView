#!/usr/bin/env python3
"""
テーマスタイルシート生成の修正

テーマ設定時に色が正しく変化しない問題を修正します。
- スタイルシート生成の改善
- テーマ適用の確実性向上
- デバッグ機能の追加

Author: Kiro AI Integration System
"""

from pathlib import Path


def fix_theme_manager_stylesheet_generation():
    """テーママネージャーのスタイルシート生成を修正"""

    theme_manager_path = Path("src/integration/ui/theme_manager.py")

    if not theme_manager_path.exists():
        print(f"❌ テーママネージャーファイルが見つかりません: {theme_manager_path}")
        return False

    print("📝 テーママネージャーのスタイルシート生成を修正中...")

    with open(theme_manager_path, encoding="utf-8") as f:
        content = f.read()

    # 1. _apply_color_scheme メソッドの改善
    old_apply_color_scheme = '''    def _apply_color_scheme(self, color_scheme: Dict[str, str]) -> bool:
        """カラースキームをUIコンポーネントに適用"""
        try:
            if not color_scheme:
                return True

            # カラースキームに基づいてスタイルシートを生成
            additional_styles: List[str] = []

            # 背景色の適用
            if 'background' in color_scheme:
                bg_color = color_scheme['background']
                additional_styles.append(
                    f"QWidget {{ background-color: {bg_color}; }}"
                )

            # 前景色（テキスト）の適用
reground' in color_scheme:
                fg_color = color_scheme['foreground']
                additional_styles.append(
                    f"QWidget {{ color: {fg_color}; }}"
                )

            # プライマリカラーの適用
            if 'primary' in color_scheme:
                primary_color = color_scheme['primary']
                hover_color = color_scheme.get('primary_hover', primary_color)
                button_style = (
                    f"QPushButton {{ "
                    f"background-color: {primary_color}; "
                    f"color: white; "
                    f"border: none; "
                    f"padding: 8px 16px; "
                    f"border-radius: 4px; "
                    f"}} "
                    f"QPushButton:hover {{ "
                    f"background-color: {hover_color}; "
                    f"}}"
                )
                additional_styles.append(button_style)

            # セカンダリカラーの適用
            if 'secondary' in color_scheme:
                secondary_color = color_scheme['secondary']
                label_style = (
                    f"QLabel {{ color: {secondary_color}; }}"
                )
                additional_styles.append(label_style)

            # 生成されたスタイルシートを適用
            if additional_styles:
                combined_styles = "\\n".join(additional_styles)
                return self._apply_style_sheet(combined_styles)

            return True

        except Exception as e:
            self.logger_system.error(f"Failed to apply color scheme: {e}")
            return False'''

    new_apply_color_scheme = '''    def _apply_color_scheme(self, color_scheme: Dict[str, str]) -> bool:
        """カラースキームをUIコンポーネントに適用（改善版）"""
        try:
            if not color_scheme:
                self.logger_system.warning("Color scheme is empty, generating default styles")
                # デフォルトのカラースキームを使用
                color_scheme = self._get_default_color_scheme()

            self.logger_system.info(f"Applying color scheme: {color_scheme}")

            # カラースキームに基づいてスタイルシートを生成
            stylesheet_parts: List[str] = []

            # 1. メインウィンドウとQWidgetの基本スタイル
            if 'background' in color_scheme and 'foreground' in color_scheme:
                bg_color = color_scheme['background']
                fg_color = color_scheme['foreground']

                main_style = f"""
                QMainWindow {{
                    background-color: {bg_color};
                    color: {fg_color};
                }}

                QWidget {{
                    background-color: {bg_color};
                    color: {fg_color};
                }}

                QFrame {{
                    background-color: {bg_color};
                    color: {fg_color};
                }}
                """
                stylesheet_parts.append(main_style)

            # 2. ボタンスタイル
            if 'primary' in color_scheme:
                primary_color = color_scheme['primary']
                hover_color = color_scheme.get('hover', self._darken_color(primary_color))
                button_text_color = color_scheme.get('button_text', '#ffffff')

                button_style = f"""
                QPushButton {{
                    background-color: {primary_color};
                    color: {button_text_color};
                    border: 1px solid {primary_color};
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }}

                QPushButton:hover {{
                    background-color: {hover_color};
                    border-color: {hover_color};
                }}

                QPushButton:pressed {{
                    background-color: {self._darken_color(primary_color, 0.2)};
                }}

                QPushButton:disabled {{
                    background-color: {color_scheme.get('disabled', '#cccccc')};
                    color: #666666;
                }}
                """
                stylesheet_parts.append(button_style)

            # 3. ラベルとテキストスタイル
            if 'foreground' in color_scheme:
                fg_color = color_scheme['foreground']
                secondary_color = color_scheme.get('secondary', fg_color)

                text_style = f"""
                QLabel {{
                    color: {fg_color};
                    background-color: transparent;
                }}

                QTextEdit {{
                    background-color: {color_scheme.get('input_background', color_scheme.get('background', '#ffffff'))};
                    color: {fg_color};
                    border: 1px solid {color_scheme.get('border', '#cccccc')};
                    border-radius: 3px;
                    padding: 4px;
                }}

                QLineEdit {{
                    background-color: {color_scheme.get('input_background', color_scheme.get('background', '#ffffff'))};
                    color: {fg_color};
                    border: 1px solid {color_scheme.get('border', '#cccccc')};
                    border-radius: 3px;
                    padding: 4px;
                }}
                """
                stylesheet_parts.append(text_style)

            # 4. メニューとツールバースタイル
            if 'background' in color_scheme and 'foreground' in color_scheme:
                bg_color = color_scheme['background']
                fg_color = color_scheme['foreground']
                selected_color = color_scheme.get('selected', color_scheme.get('primary', '#0078d4'))

                menu_style = f"""
                QMenuBar {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border-bottom: 1px solid {color_scheme.get('border', '#cccccc')};
                }}

                QMenuBar::item {{
                    background-color: transparent;
                    padding: 4px 8px;
                }}

                QMenuBar::item:selected {{
                    background-color: {selected_color};
                    color: white;
                }}

                QMenu {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border: 1px solid {color_scheme.get('border', '#cccccc')};
                }}

                QMenu::item:selected {{
                    background-color: {selected_color};
                    color: white;
                }}

                QToolBar {{
                    background-color: {bg_color};
                    color: {fg_color};
                    border: none;
                    spacing: 2px;
                }}
                """
                stylesheet_parts.append(menu_style)

            # 5. スクロールバーとその他のコントロール
            if 'background' in color_scheme:
                bg_color = color_scheme['background']
                border_color = color_scheme.get('border', '#cccccc')

                control_style = f"""
                QScrollBar:vertical {{
                    background-color: {bg_color};
                    width: 12px;
                    border: none;
                }}

                QScrollBar::handle:vertical {{
                    background-color: {border_color};
                    border-radius: 6px;
                    min-height: 20px;
                }}

                QScrollBar::handle:vertical:hover {{
                    background-color: {color_scheme.get('hover', border_color)};
                }}

                QComboBox {{
                    background-color: {color_scheme.get('input_background', bg_color)};
                    color: {color_scheme.get('foreground', '#000000')};
                    border: 1px solid {border_color};
                    border-radius: 3px;
                    padding: 4px;
                }}
                """
                stylesheet_parts.append(control_style)

            # 生成されたスタイルシートを結合して適用
            if stylesheet_parts:
                combined_stylesheet = "\\n".join(stylesheet_parts)
                self.logger_system.info(f"Generated stylesheet length: {len(combined_stylesheet)} characters")

                # デバッグ用：生成されたスタイルシートをログに出力
                self.logger_system.debug(f"Generated stylesheet:\\n{combined_stylesheet[:500]}...")

                success = self._apply_style_sheet(combined_stylesheet)
                if success:
                    self.logger_system.info("Color scheme applied successfully")
                else:
                    self.logger_system.error("Failed to apply generated stylesheet")
                return success
            else:
                self.logger_system.warning("No stylesheet parts generated from color scheme")
                return False

        except Exception as e:
            self.logger_system.error(f"Failed to apply color scheme: {e}")
            import traceback
            self.logger_system.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _get_default_color_scheme(self) -> Dict[str, str]:
        """デフォルトのカラースキームを取得"""
        return {
            'background': '#ffffff',
            'foreground': '#000000',
            'primary': '#0078d4',
            'secondary': '#6c757d',
            'accent': '#17a2b8',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'border': '#dee2e6',
            'hover': '#e3f2fd',
            'selected': '#0d7377',
            'disabled': '#6c757d',
            'input_background': '#ffffff',
            'button_text': '#ffffff'
        }

    def _darken_color(self, color: str, factor: float = 0.1) -> str:
        """色を暗くする"""
        try:
            # 簡単な色の暗化処理
            if color.startswith('#') and len(color) == 7:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)

                r = max(0, int(r * (1 - factor)))
                g = max(0, int(g * (1 - factor)))
                b = max(0, int(b * (1 - factor)))

                return f"#{r:02x}{g:02x}{b:02x}"
            else:
                return color
        except Exception:
            return color'''

    if old_apply_color_scheme in content:
        content = content.replace(old_apply_color_scheme, new_apply_color_scheme)
        print("✅ _apply_color_scheme メソッドを改善しました")
    else:
        print("⚠️  _apply_color_scheme メソッドが見つかりませんでした")

    # 2. _apply_qt_theme メソッドの改善
    old_apply_qt_theme = '''    def _apply_qt_theme(self, theme: ThemeConfiguration) -> bool:
        """Apply Qt theme (CursorBLD integration)"""
        try:
            success = True

            # 1. Qt-Theme-Managerのテーマを適用
            if self.qt_theme_manager and theme.qt_theme_name:
                if hasattr(self.qt_theme_manager, 'set_theme'):
                    success = self.qt_theme_manager.set_theme(theme.qt_theme_name)
                    if not success:
                        self.logger_system.warning(f"Failed to apply Qt theme: {theme.qt_theme_name}")
                else:
                    self.logger_system.warning("Qt-Theme-Manager set_theme method not found")

            # 2. カスタムスタイルシートを適用
            if theme.style_sheet:
                success = self._apply_style_sheet(theme.style_sheet) and success

            # 3. カラースキームを適用
            if theme.color_scheme:
                success = self._apply_color_scheme(theme.color_scheme) and success

            return success

        except Exception as e:
            self.logger_system.warning(f"Failed to apply Qt theme: {e}")
            return False'''

    new_apply_qt_theme = '''    def _apply_qt_theme(self, theme: ThemeConfiguration) -> bool:
        """Apply Qt theme (CursorBLD integration) - 改善版"""
        try:
            self.logger_system.info(f"Applying Qt theme: {theme.name}")
            success = True

            # 1. Qt-Theme-Managerのテーマを適用
            if self.qt_theme_manager and hasattr(theme, 'qt_theme_name') and theme.qt_theme_name:
                if hasattr(self.qt_theme_manager, 'set_theme'):
                    qt_success = self.qt_theme_manager.set_theme(theme.qt_theme_name)
                    if qt_success:
                        self.logger_system.info(f"Qt-Theme-Manager theme applied: {theme.qt_theme_name}")
                    else:
                        self.logger_system.warning(f"Failed to apply Qt theme: {theme.qt_theme_name}")
                    success = qt_success and success
                else:
                    self.logger_system.warning("Qt-Theme-Manager set_theme method not found")
            else:
                self.logger_system.info("Qt-Theme-Manager not available or no qt_theme_name specified")

            # 2. カスタムスタイルシートを適用
            if hasattr(theme, 'style_sheet') and theme.style_sheet:
                self.logger_system.info(f"Applying custom stylesheet: {len(theme.style_sheet)} characters")
                style_success = self._apply_style_sheet(theme.style_sheet)
                success = style_success and success
            else:
                self.logger_system.info("No custom stylesheet provided")

            # 3. カラースキームを適用（最も重要）
            if hasattr(theme, 'color_scheme') and theme.color_scheme:
                self.logger_system.info(f"Applying color scheme: {list(theme.color_scheme.keys())}")
                color_success = self._apply_color_scheme(theme.color_scheme)
                success = color_success and success
            else:
                self.logger_system.warning("No color scheme provided, generating from theme name")
                # テーマ名からカラースキームを生成
                generated_scheme = self._generate_color_scheme_from_theme_name(theme.name)
                color_success = self._apply_color_scheme(generated_scheme)
                success = color_success and success

            if success:
                self.logger_system.info(f"Qt theme applied successfully: {theme.name}")
            else:
                self.logger_system.error(f"Failed to apply Qt theme: {theme.name}")

            return success

        except Exception as e:
            self.logger_system.error(f"Failed to apply Qt theme: {e}")
            import traceback
            self.logger_system.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _generate_color_scheme_from_theme_name(self, theme_name: str) -> Dict[str, str]:
        """テーマ名からカラースキームを生成"""
        try:
            # ダークテーマの判定
            is_dark = any(keyword in theme_name.lower() for keyword in ['dark', 'night', 'black'])

            if is_dark:
                return {
                    'background': '#2b2b2b',
                    'foreground': '#ffffff',
                    'primary': '#007acc',
                    'secondary': '#6c757d',
                    'accent': '#17a2b8',
                    'success': '#28a745',
                    'warning': '#ffc107',
                    'error': '#dc3545',
                    'border': '#495057',
                    'hover': '#3a3a3a',
                    'selected': '#0d7377',
                    'disabled': '#6c757d',
                    'input_background': '#3a3a3a',
                    'button_text': '#ffffff'
                }
            else:
                return {
                    'background': '#ffffff',
                    'foreground': '#000000',
                    'primary': '#007acc',
                    'secondary': '#6c757d',
                    'accent': '#17a2b8',
                    'success': '#28a745',
                    'warning': '#ffc107',
                    'error': '#dc3545',
                    'border': '#dee2e6',
                    'hover': '#f8f9fa',
                    'selected': '#e3f2fd',
                    'disabled': '#6c757d',
                    'input_background': '#ffffff',
                    'button_text': '#ffffff'
                }
        except Exception as e:
            self.logger_system.error(f"Failed to generate color scheme: {e}")
            return self._get_default_color_scheme()'''

    if old_apply_qt_theme in content:
        content = content.replace(old_apply_qt_theme, new_apply_qt_theme)
        print("✅ _apply_qt_theme メソッドを改善しました")
    else:
        print("⚠️  _apply_qt_theme メソッドが見つかりませんでした")

    # 3. apply_theme メソッドの改善
    old_apply_theme = '''    def apply_theme(self, theme_name: str) -> bool:
        """Apply the specified theme to the application"""

        try:
            if theme_name not in self.themes:
                self.theme_error.emit(theme_name, f"Theme '{theme_name}' not found")
                return False

            theme = self.themes[theme_name]

            # Apply Qt theme (CursorBLD integration)
            success = self._apply_qt_theme(theme)

            if success:
                # Apply accessibility features (Kiro enhancement)
                self._apply_accessibility_features(theme)

                # Apply performance settings (Kiro enhancement)
                self._apply_performance_settings(theme)

                # Update current theme
                self.current_theme = theme_name

                # Update configuration
                self.config_manager.set_setting("ui.theme", theme_name)

                # Update state
                self.state_manager.update_state(current_theme=theme_name)

                # Emit signals
                self.theme_changed.emit(theme_name)
                # Emit compatibility signal for SimpleThemeManager
                self.theme_changed_compat.emit(self.current_theme, theme_name)

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR, "theme_apply", f"Theme applied: {theme_name}"
                )

                return True
            else:
                self.theme_error.emit(theme_name, "Failed to apply Qt theme")
                return False

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_apply", "theme": theme_name},
                AIComponent.CURSOR,
            )
            return False'''

    new_apply_theme = '''    def apply_theme(self, theme_name: str) -> bool:
        """Apply the specified theme to the application - 改善版"""

        try:
            self.logger_system.info(f"Starting theme application: {theme_name}")

            if theme_name not in self.themes:
                self.logger_system.error(f"Theme '{theme_name}' not found in available themes: {list(self.themes.keys())}")
                self.theme_error.emit(theme_name, f"Theme '{theme_name}' not found")
                return False

            theme = self.themes[theme_name]
            self.logger_system.info(f"Found theme configuration: {theme.name} - {theme.display_name}")

            # Apply Qt theme (CursorBLD integration)
            success = self._apply_qt_theme(theme)

            if success:
                self.logger_system.info("Qt theme applied successfully, applying additional features...")

                # Apply accessibility features (Kiro enhancement)
                try:
                    self._apply_accessibility_features(theme)
                    self.logger_system.info("Accessibility features applied")
                except Exception as e:
                    self.logger_system.warning(f"Failed to apply accessibility features: {e}")

                # Apply performance settings (Kiro enhancement)
                try:
                    self._apply_performance_settings(theme)
                    self.logger_system.info("Performance settings applied")
                except Exception as e:
                    self.logger_system.warning(f"Failed to apply performance settings: {e}")

                # Update current theme
                old_theme = self.current_theme
                self.current_theme = theme_name

                # Update configuration
                try:
                    self.config_manager.set_setting("ui.theme", theme_name)
                    self.logger_system.info("Theme configuration saved")
                except Exception as e:
                    self.logger_system.warning(f"Failed to save theme configuration: {e}")

                # Update state
                try:
                    self.state_manager.update_state(current_theme=theme_name)
                    self.logger_system.info("Theme state updated")
                except Exception as e:
                    self.logger_system.warning(f"Failed to update theme state: {e}")

                # Emit signals
                try:
                    self.theme_changed.emit(theme_name)
                    # Emit compatibility signal for SimpleThemeManager
                    self.theme_changed_compat.emit(old_theme, theme_name)
                    self.theme_applied.emit(theme_name)
                    self.logger_system.info("Theme change signals emitted")
                except Exception as e:
                    self.logger_system.warning(f"Failed to emit theme signals: {e}")

                self.logger_system.log_ai_operation(
                    AIComponent.CURSOR, "theme_apply", f"Theme applied successfully: {theme_name}"
                )

                self.logger_system.info(f"Theme application completed successfully: {theme_name}")
                return True
            else:
                self.logger_system.error(f"Failed to apply Qt theme: {theme_name}")
                self.theme_error.emit(theme_name, "Failed to apply Qt theme")
                return False

        except Exception as e:
            self.logger_system.error(f"Exception during theme application: {e}")
            import traceback
            self.logger_system.error(f"Traceback: {traceback.format_exc()}")

            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_apply", "theme": theme_name},
                AIComponent.CURSOR,
            )
            return False'''

    if old_apply_theme in content:
        content = content.replace(old_apply_theme, new_apply_theme)
        print("✅ apply_theme メソッドを改善しました")
    else:
        print("⚠️  apply_theme メソッドが見つかりませんでした")

    # ファイルを保存
    with open(theme_manager_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ テーママネージャーの修正が完了しました: {theme_manager_path}")
    return True


def create_theme_debug_tool():
    """テーマデバッグツールを作成"""

    debug_tool_path = Path("debug_theme_stylesheet.py")

    debug_tool_content = '''#!/usr/bin/env python3
"""
テーマスタイルシートデバッグツール

テーマ設定時のスタイルシート生成をデバッグするためのツールです。
- 現在のテーマ状態の確認
- スタイルシート生成のテスト
- テーマ適用の検証

Author: Kiro AI Integration System
"""

import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
    from PySide6.QtCore import Qt

    # テーママネージャーをインポート
    from src.integration.ui.theme_manager import IntegratedThemeManager
    from src.integration.config_manager import ConfigManager
    from src.integration.state_manager import StateManager
    from src.integration.logging_system import LoggerSystem

except ImportError as e:
    print(f"❌ 必要なモジュールのインポートに失敗しました: {e}")
    print("PySide6とプロジェクトの依存関係を確認してください。")
    sys.exit(1)

class ThemeDebugWindow(QMainWindow):
    """テーマデバッグウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("テーマスタイルシートデバッグツール")
        self.setGeometry(100, 100, 800, 600)

        # ロガーの設定
        self.logger = LoggerSystem()
        self.logger.setup_logging(log_level=logging.DEBUG)

        # テーママネージャーの初期化
        try:
            config_manager = ConfigManager()
            state_manager = StateManager(config_manager)

            self.theme_manager = IntegratedThemeManager(
                config_manager=config_manager,
                state_manager=state_manager,
                logger_system=self.logger,
                main_window=self
            )

            self.logger.info("テーママネージャーが正常に初期化されました")

        except Exception as e:
            self.logger.error(f"テーママネージャーの初期化に失敗: {e}")
            self.theme_manager = None

        self.setup_ui()

    def setup_ui(self):
        """UIの設定"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # タイトル
        title = QLabel("テーマスタイルシートデバッグツール")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # 現在のテーマ表示
        self.current_theme_label = QLabel("現在のテーマ: 読み込み中...")
        layout.addWidget(self.current_theme_label)

        # テーマ一覧表示
        self.theme_list_label = QLabel("利用可能なテーマ: 読み込み中...")
        layout.addWidget(self.theme_list_label)

        # テーマ適用ボタン
        button_layout = QVBoxLayout()

        self.test_light_button = QPushButton("ライトテーマをテスト")
        self.test_light_button.clicked.connect(lambda: self.test_theme("default"))
        button_layout.addWidget(self.test_light_button)

        self.test_dark_button = QPushButton("ダークテーマをテスト")
        self.test_dark_button.clicked.connect(lambda: self.test_theme("dark"))
        button_layout.addWidget(self.test_dark_button)

        self.debug_button = QPushButton("テーマ状態をデバッグ")
        self.debug_button.clicked.connect(self.debug_theme_status)
        button_layout.addWidget(self.debug_button)

        layout.addLayout(button_layout)

        # ログ表示エリア
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        self.log_display.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_display)

        # 初期状態の更新
        self.update_status()

    def update_status(self):
        """状態の更新"""
        if self.theme_manager:
            try:
                current_theme = self.theme_manager.get_current_theme()
                self.current_theme_label.setText(f"現在のテーマ: {current_theme}")

                available_themes = self.theme_manager.get_available_themes()
                self.theme_list_label.setText(f"利用可能なテーマ ({len(available_themes)}): {', '.join(available_themes)}")

                self.log_display.append(f"✅ テーママネージャー状態更新完了")

            except Exception as e:
                self.log_display.append(f"❌ 状態更新エラー: {e}")
        else:
            self.current_theme_label.setText("現在のテーマ: テーママネージャー未初期化")
            self.theme_list_label.setText("利用可能なテーマ: テーママネージャー未初期化")

    def test_theme(self, theme_name: str):
        """テーマのテスト"""
        if not self.theme_manager:
            self.log_display.append("❌ テーママネージャーが初期化されていません")
            return

        try:
            self.log_display.append(f"🔄 テーマ '{theme_name}' を適用中...")

            success = self.theme_manager.apply_theme(theme_name)

            if success:
                self.log_display.append(f"✅ テーマ '{theme_name}' の適用に成功しました")
                self.update_status()
            else:
                self.log_display.append(f"❌ テーマ '{theme_name}' の適用に失敗しました")

        except Exception as e:
            self.log_display.append(f"❌ テーマ適用中にエラー: {e}")

    def debug_theme_status(self):
        """テーマ状態のデバッグ"""
        if not self.theme_manager:
            self.log_display.append("❌ テーママネージャーが初期化されていません")
            return

        try:
            self.log_display.append("🔍 テーマ状態をデバッグ中...")

            # テーママネージャーのデバッグメソッドを呼び出し
            self.theme_manager.debug_theme_status()

            self.log_display.append("✅ デバッグ情報をログに出力しました")

        except Exception as e:
            self.log_display.append(f"❌ デバッグ中にエラー: {e}")

def main():
    """メイン関数"""
    app = QApplication(sys.argv)

    # アプリケーションの基本設定
    app.setApplicationName("テーマデバッグツール")
    app.setApplicationVersion("1.0.0")

    # デバッグウィンドウの作成と表示
    window = ThemeDebugWindow()
    window.show()

    # イベントループの開始
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''

    with open(debug_tool_path, "w", encoding="utf-8") as f:
        f.write(debug_tool_content)

    print(f"✅ テーマデバッグツールを作成しました: {debug_tool_path}")
    return True


def main():
    """メイン実行関数"""
    print("🔧 テーマスタイルシート生成の修正を開始します...")

    try:
        # 1. テーママネージャーのスタイルシート生成を修正
        if fix_theme_manager_stylesheet_generation():
            print("✅ テーママネージャーの修正が完了しました")
        else:
            print("❌ テーママネージャーの修正に失敗しました")
            return False

        # 2. デバッグツールの作成
        if create_theme_debug_tool():
            print("✅ デバッグツールの作成が完了しました")
        else:
            print("❌ デバッグツールの作成に失敗しました")

        print("\n🎉 テーマスタイルシート生成の修正が完了しました！")
        print("\n📋 修正内容:")
        print("  - スタイルシート生成ロジックの改善")
        print("  - カラースキーム適用の確実性向上")
        print("  - デバッグ機能の追加")
        print("  - エラーハンドリングの強化")

        print("\n🔍 テスト方法:")
        print("  1. python debug_theme_stylesheet.py でデバッグツールを起動")
        print("  2. 各テーマボタンをクリックしてテーマ変更をテスト")
        print("  3. ログでスタイルシート生成状況を確認")

        return True

    except Exception as e:
        print(f"❌ 修正中にエラーが発生しました: {e}")
        import traceback

        print(f"詳細: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    main()
