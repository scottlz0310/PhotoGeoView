"""
FileSystemWatcher のテスト

FileSystemWatcher クラスの基本機能をテストする。
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.integration.services.file_system_watcher import FileSystemWatcher, FileChangeType
from src.integration.logging_system import LoggerSystem


class TestFileSystemWatcher:
    """FileSystemWatcher のテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.logger_system = LoggerSystem()
        self.temp_dir = None

    def teardown_method(self):
        """各テストメソッドの後に実行されるクリーンアップ処理"""
        if hasattr(self, 'watcher') and self.watcher:
            self.watcher.stop_watching()

    def test_init_with_watchdog_available(self):
        """watchdog が利用可能な場合の初期化テスト"""
        with patch('src.integration.services.file_system_watcher.WATCHDOG_AVAILABLE', True):
            watcher = FileSystemWatcher(logger_system=self.logger_system)

            assert watcher.watchdog_available is True
            assert watcher.enable_monitoring is True
            assert watcher.is_watching is False
            assert watcher.current_folder is None
            assert len(watcher.change_listeners) == 0
            assert watcher.SUPPORTED_EXTENSIONS == {
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
            }

    def test_init_with_watchdog_unavailable(self):
        """watchdog が利用できない場合の初期化テスト"""
        with patch('src.integration.services.file_system_watcher.WATCHDOG_AVAILABLE', False):
            watcher = FileSystemWatcher(logger_system=self.logger_system)

            assert watcher.watchdog_available is False
            assert watcher.enable_monitoring is False
            assert watcher.is_watching is False

    def test_start_watching_nonexistent_folder(self):
        """存在しないフォルダの監視開始テスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)
        nonexistent_path = Path("/nonexistent/folder")

        result = watcher.start_watching(nonexistent_path)

        assert result is False
        assert watcher.is_watching is False
        assert watcher.current_folder is None

    def test_start_watching_file_instead_of_folder(self):
        """ファイルを指定した場合の監視開始テスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)

        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = Path(temp_file.name)
            result = watcher.start_watching(file_path)

            assert result is False
            assert watcher.is_watching is False
            assert watcher.current_folder is None

    @patch('src.integration.services.file_system_watcher.WATCHDOG_AVAILABLE', True)
    @patch('src.integration.services.file_system_watcher.Observer')
    def test_start_watching_success(self, mock_observer_class):
        """正常な監視開始テスト"""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = FileSystemWatcher(logger_system=self.logger_system)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = watcher.start_watching(temp_path)

            assert result is True
            assert watcher.is_watching is True
            assert watcher.current_folder == temp_path
            assert mock_observer.start.called
            assert mock_observer.schedule.called

    def test_stop_watching_when_not_watching(self):
        """監視していない状態での停止テスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)

        result = watcher.stop_watching()

        assert result is True
        assert watcher.is_watching is False

    @patch('src.integration.services.file_system_watcher.WATCHDOG_AVAILABLE', True)
    @patch('src.integration.services.file_system_watcher.Observer')
    def test_stop_watching_success(self, mock_observer_class):
        """正常な監視停止テスト"""
        mock_observer = Mock()
        mock_observer.is_alive.return_value = True  # Changed to True to trigger stop call
        mock_observer_class.return_value = mock_observer

        watcher = FileSystemWatcher(logger_system=self.logger_system)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            watcher.start_watching(temp_path)

            result = watcher.stop_watching()

            assert result is True
            assert watcher.is_watching is False
            assert watcher.current_folder is None
            assert mock_observer.stop.called

    def test_add_change_listener(self):
        """変更リスナー追加テスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)

        def test_callback(file_path, change_type, old_path=None):
            pass

        watcher.add_change_listener(test_callback)

        assert len(watcher.change_listeners) == 1
        assert test_callback in watcher.change_listeners

    def test_remove_change_listener(self):
        """変更リスナー削除テスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)

        def test_callback(file_path, change_type, old_path=None):
            pass

        watcher.add_change_listener(test_callback)
        watcher.remove_change_listener(test_callback)

        assert len(watcher.change_listeners) == 0
        assert test_callback not in watcher.change_listeners

    def test_get_watch_status(self):
        """監視状態取得テスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)

        status = watcher.get_watch_status()

        assert isinstance(status, dict)
        assert 'is_watching' in status
        assert 'current_folder' in status
        assert 'watchdog_available' in status
        assert 'enable_monitoring' in status
        assert 'listener_count' in status
        assert 'supported_extensions' in status
        assert 'stats' in status

        assert status['is_watching'] is False
        assert status['current_folder'] is None
        assert status['listener_count'] == 0

    def test_notify_listeners(self):
        """リスナー通知テスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)

        # モックコールバック関数
        callback_calls = []

        def test_callback(file_path, change_type, old_path=None):
            callback_calls.append((file_path, change_type, old_path))

        watcher.add_change_listener(test_callback)

        # 通知テスト
        test_path = Path("/test/image.jpg")
        watcher._notify_listeners(test_path, FileChangeType.CREATED)

        assert len(callback_calls) == 1
        assert callback_calls[0][0] == test_path
        assert callback_calls[0][1] == FileChangeType.CREATED
        assert callback_calls[0][2] is None

    def test_notify_listeners_with_error(self):
        """リスナー通知エラーテスト"""
        watcher = FileSystemWatcher(logger_system=self.logger_system)

        def error_callback(file_path, change_type, old_path=None):
            raise Exception("Test error")

        def success_callback(file_path, change_type, old_path=None):
            pass

        watcher.add_change_listener(error_callback)
        watcher.add_change_listener(success_callback)

        # エラーが発生してもクラッシュしないことを確認
        test_path = Path("/test/image.jpg")
        watcher._notify_listeners(test_path, FileChangeType.CREATED)

        # 統計にエラーが記録されることを確認
        assert watcher.watch_stats['errors'] > 0


if __name__ == "__main__":
    pytest.main([__file__])
