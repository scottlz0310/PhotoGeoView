#!/usr/bin/env python3
"""
Qt-Theme-Breadcrumb機能デモンストレーション

新しく実装された機能を実際に動作させながら説明するためのデモスクリプト

Author: Kiro AI Integration System
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import QApplication, QMessageBox

    from src.integration.config_manager import ConfigManager
    from src.integration.logging_system import LoggerSystem
    from src.integration.services.file_system_watcher import FileSystemWatcher
    from src.ui.theme_manager import ThemeManagerWidget
    from src.ui.breadcrumb_bar import BreadcrumbAddressBar

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"依存関係が不足しています: {e}")
    DEPENDENCIES_AVAILABLE = False


class QtThemeBreadcrumbDemo:
    """Qt-Theme-Breadcrumb機能のデモンストレーションクラス"""

    def __init__(self):
        self.app = None
        self.config_manager = None
        self.logger_system = None
        self.file_system_watcher = None
        self.theme_manager = None
        self.breadcrumb_bar = None

    def setup_demo_environment(self):
        """デモ環境のセットアップ"""
        print("🚀 Qt-Theme-Breadcrumb機能デモを開始します...")
        print("=" * 60)

        if not DEPENDENCIES_AVAILABLE:
            print("❌ 必要な依存関係が不足しています")
            return False

        try:
            # Qt Application初期化
            if not QApplication.instance():
                self.app = QApplication([])

            # コアシステム初期化
            self.logger_system = LoggerSystem()
            self.config_manager = ConfigManager(logger_system=self.logger_system)
            self.file_system_watcher = FileSystemWatcher(
                logger_system=self.logger_system,
                enable_monitoring=True
            )

            # UI コンポーネント初期化
            self.theme_manager = ThemeManagerWidget(
                self.config_manager,
                self.logger_system
            )

            self.breadcrumb_bar = BreadcrumbAddressBar(
                self.file_system_watcher,
                self.logger_system,
                self.config_manager
            )

            print("✅ デモ環境のセットアップが完了しました")
            return True

        except Exception as e:
            print(f"❌ セットアップエラー: {e}")
            return False

    def demo_theme_management(self):
        """テーマ管理機能のデモ"""
        print("\n🎨 1. テーマ管理機能のデモンストレーション")
        print("-" * 40)

        # 利用可能なテーマを表示
        available_themes = self.theme_manager.get_available_themes()
        print(f"📋 利用可能なテーマ: {len(available_themes)}個")

        for theme_info in available_themes:
            print(f"   • {theme_info.display_name}: {theme_info.description}")

        # テーマ切り替えデモ
        print("\n🔄 テーマ切り替えデモ:")
        themes_to_demo = ["default", "dark"]

        for theme_name in themes_to_demo:
            print(f"   → {theme_name}テーマに切り替え中...")
            success = self.theme_manager.apply_theme(theme_name)
            if success:
                print(f"   ✅ {theme_name}テーマが適用されました")
            else:
                print(f"   ❌ {theme_name}テーマの適用に失敗しました")
            time.sleep(1)  # デモ用の待機

        # キーボードショートカット情報
        shortcuts = self.theme_manager.get_keyboard_shortcuts_info()
        print("\n⌨️  利用可能なキーボードショートカット:")
        for shortcut, description in shortcuts.items():
            print(f"   • {shortcut}: {description}")

    def demo_breadcrumb_navigation(self):
        """ブレッドクラムナビゲーション機能のデモ"""
        print("\n🧭 2. ブレッドクラムナビゲーション機能のデモンストレーション")
        print("-" * 50)

        # テスト用パスの準備
        test_paths = [
            Path.home(),
            Path.home() / "Documents" if (Path.home() / "Documents").exists() else Path.home(),
            Path("/tmp") if Path("/tmp").exists() else Path.home()
        ]

        print("📍 パスナビゲーションデモ:")
        for i, test_path in enumerate(test_paths, 1):
            print(f"   {i}. {test_path} に移動中...")
            success = self.breadcrumb_bar.set_current_path(test_path)
            if success:
                print(f"   ✅ 正常に移動しました")
            else:
                print(f"   ❌ 移動に失敗しました")
            time.sleep(1)  # デモ用の待機

        # キーボードショートカット情報
        shortcuts = self.breadcrumb_bar.get_keyboard_shortcuts_info()
        print("\n⌨️  ブレッドクラム用キーボードショートカット:")
        for shortcut,in shortcuts.items():
            print(f"   • {shortcut}: {description}")

    def demo_integration_features(self):
        """統合機能のデモ"""
        print("\n🔗 3. 統合機能のデモンストレーション")
        print("-" * 35)

        # ファイルシステム監視デモ
        print("📁 ファイルシステム監視機能:")
        test_path = Path.home()

        print(f"   → {test_path} の監視を開始...")
        watch_started = self.file_system_watcher.start_watching(test_path)
        if watch_started:
            print("   ✅ ファイルシステム監視が開始されました")
            time.sleep(2)

            print("   → 監視を停止...")
            self.file_system_watcher.stop_watching()
            print("   ✅ ファイルシステム監視が停止されました")
        else:
            print("   ❌ ファイルシステム監視の開始に失敗しました")

        # エラーハンドリングデモ
        print("\n🛡️  エラーハンドリング機能:")

        # 存在しないテーマの適用テスト
        print("   → 存在しないテーマの適用テスト...")
        invalid_theme_result = self.theme_manager.apply_theme("nonexistent_theme")
        if not invalid_theme_result:
            print("   ✅ 無効なテーマは適切に拒否されました")
        else:
            print("   ⚠️  無効なテーマが適用されてしまいました")

        # 存在しないパスへのナビゲーションテスト
        print("   → 存在しないパスへのナビゲーションテスト...")
        invalid_path = Path("/nonexistent/path/that/should/not/exist")
        invalid_path_result = self.breadcrumb_bar.set_current_path(invalid_path)
        if not invalid_path_result:
            print("   ✅ 無効なパスは適切に拒否されました")
        else:
            print("   ⚠️  無効なパスに移動してしまいました")

    def demo_performance_features(self):
        """パフォーマンス機能のデモ"""
        print("\n⚡ 4. パフォーマンス機能のデモンストレーション")
        print("-" * 40)

        # テーマ切り替えパフォーマンステスト
        print("🏃 テーマ切り替えパフォーマンステスト:")

        start_time = time.time()
        theme_switches = 0

        for theme in ["default", "dark", "default"]:
            if self.theme_manager.apply_theme(theme):
                theme_switches += 1

        end_time = time.time()
        total_time = end_time - start_time

        print(f"   • 実行時間: {total_time:.3f}秒")
        print(f"   • テーマ切り替え回数: {theme_switches}回")
        print(f"   • 平均切り替え時間: {total_time/max(theme_switches, 1):.3f}秒/回")

        if total_time < 1.0:
            print("   ✅ パフォーマンス: 優秀")
        elif total_time < 3.0:
            print("   ✅ パフォーマンス: 良好")
        else:
            print("   ⚠️  パフォーマンス: 改善の余地あり")

        # ナビゲーションパフォーマンステスト
        print("\n🧭 ナビゲーションパフォーマンステスト:")

        start_time = time.time()
        navigation_operations = 0

        test_paths = [Path.home(), Path("/tmp") if Path("/tmp").exists() else Path.home()]
        for path in test_paths:
            if self.breadcrumb_bar.set_current_path(path):
                navigation_operations += 1

        end_time = time.time()
        total_time = end_time - start_time

        print(f"   • 実行時間: {total_time:.3f}秒")
        print(f"   • ナビゲーション操作回数: {navigation_operations}回")
        print(f"   • 平均操作時間: {total_time/max(navigation_operations, 1):.3f}秒/回")

        if total_time < 0.5:
            print("   ✅ パフォーマンス: 優秀")
        elif total_time < 2.0:
            print("   ✅ パフォーマンス: 良好")
        else:
            print("   ⚠️  パフォーマンス: 改善の余地あり")

    def show_usage_tips(self):
        """使用方法のヒント表示"""
        print("\n💡 5. 使用方法のヒントとベストプラクティス")
        print("-" * 45)

        tips = [
            "🎨 作業内容に応じてテーマを選択しましょう（写真編集時はPhotographyテーマ）",
            "⌨️  キーボードショートカットを活用して効率的に操作しましょう",
            "🧭 ブレッドクラムとフォルダナビゲーターを組み合わせて使用しましょう",
            "🌙 長時間作業時はダークテーマで目の疲労を軽減しましょう",
            "📁 大量のファイルがあるフォルダでは処理に時間がかかることがあります",
            "🔄 設定は自動的に保存され、次回起動時に復元されます"
        ]

        for tip in tips:
            print(f"   {tip}")

    def run_full_demo(self):
        """完全なデモの実行"""
        if not self.setup_demo_environment():
            return False

        try:
            # 各機能のデモを順番に実行
            self.demo_theme_management()
            self.demo_breadcrumb_navigation()
            self.demo_integration_features()
            self.demo_performance_features()
            self.show_usage_tips()

            # デモ完了メッセージ
            print("\n" + "=" * 60)
            print("🎉 Qt-Theme-Breadcrumb機能デモが完了しました！")
            print("=" * 60)
            print()
            print("📚 詳細な使用方法は USER_GUIDE_QT_THEME_BREADCRUMB.md をご覧ください")
            print("🚀 実際にアプリケーションを起動して機能をお試しください:")
            print("   python main.py")
            print()

            return True

        except Exception as e:
            print(f"\n❌ デモ実行中にエラーが発生しました: {e}")
            return False

    def interactive_demo(self):
        """インタラクティブなデモ"""
        print("\n🎮 インタラクティブデモモード")
        print("=" * 30)
        print("以下の機能を試すことができます:")
        print("1. テーマ切り替え")
        print("2. パスナビゲーション")
        print("3. パフォーマンステスト")
        print("4. 全機能デモ")
        print("0. 終了")

        while True:
            try:
                choice = input("\n選択してください (0-4): ").strip()

                if choice == "0":
                    print("👋 デモを終了します")
                    break
                elif choice == "1":
                    self.demo_theme_management()
                elif choice == "2":
                    self.demo_breadcrumb_navigation()
                elif choice == "3":
                    self.demo_performance_features()
                elif choice == "4":
                    self.run_full_demo()
                    break
                else:
                    print("❌ 無効な選択です。0-4の数字を入力してください。")

            except KeyboardInterrupt:
                print("\n👋 デモを終了します")
                break
            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")


def main():
    """メイン実行関数"""
    demo = QtThemeBreadcrumbDemo()

    print("🎯 Qt-Theme-Breadcrumb機能デモンストレーション")
    print("=" * 50)
    print("このデモでは、新しく実装された機能を実際に動作させながら説明します。")
    print()

    # デモモードの選択
    print("デモモードを選択してください:")
    print("1. 自動デモ（全機能を順番に実行）")
    print("2. インタラクティブデモ（機能を選択して実行）")
    print("0. 終了")

    try:
        choice = input("\n選択してください (0-2): ").strip()

        if choice == "0":
            print("👋 デモを終了します")
            return 0
        elif choice == "1":
            success = demo.run_full_demo()
            return 0 if success else 1
        elif choice == "2":
            if demo.setup_demo_environment():
                demo.interactive_demo()
                return 0
            else:
                return 1
        else:
            print("❌ 無効な選択です")
            return 1

    except KeyboardInterrupt:
        print("\n👋 デモを終了します")
        return 0
    except Exception as e:
        print(f"❌ デモ実行エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
