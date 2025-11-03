"""
WebEngine Checker - PyQtWebEngine利用可能性チェック

PyQtWebEngineの利用可能性をチェックし、適切な初期化を行うユーティリティ。

Author: Kiro AI Integration System
"""

from typing import Optional, Tuple


def check_webengine_availability() -> Tuple[bool, str]:
    """
    PyQtWebEngineの利用可能性をチェック

    Returns:
        Tuple[bool, str]: (利用可能かどうか, エラーメッセージ)
    """
    try:
        # 基本的なインポートチェック
        from PySide6.QtWebEngineCore import QWebEngineProfile
        from PySide6.QtWebEngineWidgets import QWebEngineView

        # プロファイルの作成テスト
        profile = QWebEngineProfile.defaultProfile()

        return True, "PyQtWebEngine is available"

    except ImportError as e:
        return False, f"PyQtWebEngine import error: {e}"
    except Exception as e:
        return False, f"PyQtWebEngine initialization error: {e}"


def initialize_webengine_safe() -> Tuple[bool, str]:
    """
    安全なPyQtWebEngine初期化

    Returns:
        Tuple[bool, str]: (初期化成功かどうか, メッセージ)
    """
    try:
        from PySide6.QtWebEngineCore import QWebEngineProfile
        from PySide6.QtWebEngineWidgets import QWebEngineView

        # プロファイルを初期化
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)

        # ダミービューでプロセスを開始
        dummy_view = QWebEngineView()
        dummy_view.deleteLater()

        return True, "PyQtWebEngine initialized successfully"

    except Exception as e:
        return False, f"PyQtWebEngine initialization failed: {e}"


def create_webengine_view() -> Tuple[Optional[object], str]:
    """
    WebEngineViewを作成

    Returns:
        Tuple[Optional[object], str]: (WebEngineViewオブジェクト, メッセージ)
    """
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView

        view = QWebEngineView()
        return view, "WebEngineView created successfully"

    except Exception as e:
        return None, f"WebEngineView creation failed: {e}"


def get_webengine_status() -> dict:
    """
    WebEngineの詳細な状態を取得

    Returns:
        dict: 状態情報
    """
    status = {
        "available": False,
        "importable": False,
        "initializable": False,
        "view_creatable": False,
        "error_messages": [],
    }

    # インポートチェック
    try:
        from PySide6.QtWebEngineCore import QWebEngineProfile
        from PySide6.QtWebEngineWidgets import QWebEngineView

        status["importable"] = True
    except ImportError as e:
        status["error_messages"].append(f"Import error: {e}")
        return status

    # 初期化チェック
    try:
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        status["initializable"] = True
    except Exception as e:
        status["error_messages"].append(f"Initialization error: {e}")
        return status

    # ビュー作成チェック
    try:
        view = QWebEngineView()
        view.deleteLater()
        status["view_creatable"] = True
    except Exception as e:
        status["error_messages"].append(f"View creation error: {e}")
        return status

    status["available"] = True
    return status
