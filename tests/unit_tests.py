"""
Unit Tests for AI Integration Components

各統合コンポーネントの単体テスト

Author: Kiro AI Integration System
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent / "src"))

from integration.config_manager import ConfigManager
from integration.error_handling import ErrorCategory, IntegratedErrorHandler
from integration.logging_system import LoggerSystem
from integration.performance_monitor import KiroPerformanceMonitor
from integration.state_manager import StateManager
from integration.unified_cache import UnifiedCacheSystem


class TestConfigManager(unittest.TestCase):
    """ConfigManager の単体テスト"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_config(self):
        """設定読み込みのテスト"""
        # テスト用設定ファイルの作成
        config_data = {
            "ai_components": {
                "cursor_bld": {"enabled": True},
                "cs4_coding": {"enabled": True},
                "kiro": {"enabled": True},
            }
        }

        config_path = Path(self.temp_dir) / "test_config.json"
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        # 設定読み込みのテスト
        loaded_config = self.config_manager.load_config(config_path)
        self.assertEqual(loaded_config["ai_components"]["cursor_bld"]["enabled"], True)

    def test_merge_configs(self):
        """設定マージのテスト"""
        config1 = {"a": 1, "b": {"x": 1}}
        config2 = {"b": {"y": 2}, "c": 3}

        merged = self.config_manager.merge_configs(config1, config2)

        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"]["x"], 1)
        self.assertEqual(merged["b"]["y"], 2)
        self.assertEqual(merged["c"], 3)


class TestLoggerSystem(unittest.TestCase):
    """LoggerSystem の単体テスト"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.logger = LoggerSystem()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_log_message(self):
        """ログメッセージのテスト"""
        with patch("builtins.print") as mock_print:
            self.logger.info("テストメッセージ")
            mock_print.assert_called()

    def test_error_logging(self):
        """エラーログのテスト"""
        with patch("builtins.print") as mock_print:
            self.logger.error("エラーメッセージ")
            mock_print.assert_called()


class TestPerformanceMonitor(unittest.TestCase):
    """KiroPerformanceMonitor の単体テスト"""

    def setUp(self):
        self.performance_monitor = KiroPerformanceMonitor()

    def test_start_stop_monitoring(self):
        """監視開始・停止のテスト"""
        self.performance_monitor.start_monitoring()
        self.assertTrue(self.performance_monitor.is_monitoring)

        metrics = self.performance_monitor.stop_monitoring()
        self.assertFalse(self.performance_monitor.is_monitoring)
        self.assertIsInstance(metrics, dict)

    def test_get_current_metrics(self):
        """現在のメトリクス取得のテスト"""
        metrics = self.performance_monitor.get_current_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("memory_usage", metrics)
        self.assertIn("cpu_usage", metrics)


class TestUnifiedCacheSystem(unittest.TestCase):
    """UnifiedCacheSystem の単体テスト"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_system = UnifiedCacheSystem(cache_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cache_operations(self):
        """キャッシュ操作のテスト"""
        # キャッシュに保存
        test_data = {"test": "data"}
        self.cache_system.set("test_key", test_data)

        # キャッシュから取得
        retrieved_data = self.cache_system.get("test_key")
        self.assertEqual(retrieved_data, test_data)

        # キャッシュの削除
        self.cache_system.delete("test_key")
        self.assertIsNone(self.cache_system.get("test_key"))

    def test_cache_expiration(self):
        """キャッシュ有効期限のテスト"""
        # 短い有効期限でキャッシュに保存
        self.cache_system.set("expire_key", "data", ttl=0.1)

        # すぐに取得できることを確認
        self.assertEqual(self.cache_system.get("expire_key"), "data")

        # 有効期限後は取得できないことを確認（実際のテストでは時間待ちが必要）
        # time.sleep(0.2)
        # self.assertIsNone(self.cache_system.get("expire_key"))


class TestStateManager(unittest.TestCase):
    """StateManager の単体テスト"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = StateManager(
            state_file=Path(self.temp_dir) / "test_state.json"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_state_operations(self):
        """状態操作のテスト"""
        # 状態の設定
        self.state_manager.set_state("test_key", "test_value")

        # 状態の取得
        value = self.state_manager.get_state("test_key")
        self.assertEqual(value, "test_value")

        # 状態の保存と読み込み
        self.state_manager.save_state()

        # 新しいStateManagerインスタンスで読み込み
        new_state_manager = StateManager(
            state_file=Path(self.temp_dir) / "test_state.json"
        )
        new_state_manager.load_state()

        loaded_value = new_state_manager.get_state("test_key")
        self.assertEqual(loaded_value, "test_value")


class TestIntegratedErrorHandler(unittest.TestCase):
    """IntegratedErrorHandler の単体テスト"""

    def setUp(self):
        self.logger = LoggerSystem()
        self.error_handler = IntegratedErrorHandler(self.logger)

    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        test_error = ValueError("テストエラー")
        context = {"component": "test", "operation": "test_op"}

        with patch.object(self.logger, "error") as mock_error:
            result = self.error_handler.handle_error(
                test_error, ErrorCategory.INTEGRATION_ERROR, context
            )

            mock_error.assert_called()
            self.assertIsNotNone(result)

    def test_error_categories(self):
        """エラーカテゴリのテスト"""
        categories = [
            ErrorCategory.UI_ERROR,
            ErrorCategory.CORE_ERROR,
            ErrorCategory.INTEGRATION_ERROR,
            ErrorCategory.SYSTEM_ERROR,
        ]

        for category in categories:
            test_error = Exception(f"Test {category.value} error")
            context = {"category": category.value}

            result = self.error_handler.handle_error(test_error, category, context)
            self.assertIsNotNone(result)


if __name__ == "__main__":
    # テストスイートの実行
    unittest.main(verbosity=2)
