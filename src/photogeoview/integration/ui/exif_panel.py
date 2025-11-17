"""
EXIF Information Panel - EXIF情報表示パネル

exifreadライブラリを使用したEXIF情報表示機能。
位置情報をMAP表示機能に渡すための準備を含む。

Author: Kiro AI Integration System
"""

import contextlib
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config_manager import ConfigManager
from ..error_handling import ErrorCategory, IntegratedErrorHandler
from ..image_processor import CS4CodingImageProcessor
from ..logging_system import LoggerSystem
from ..models import AIComponent
from ..state_manager import StateManager


class EXIFPanel(QWidget):
    """
    EXIF情報表示パネル

    機能:
    - exifreadライブラリによるEXIF情報取得
    - 位置情報の表示とMAP機能への連携
    - カメラ情報、撮影設定の詳細表示
    - リアルタイム更新対応
    """

    # シグナル
    gps_coordinates_updated = Signal(float, float)  # latitude, longitude
    exif_data_updated = Signal(dict)  # exif_data

    def __init__(
        self,
        config_manager: ConfigManager,
        state_manager: StateManager,
        logger_system: LoggerSystem,
        theme_manager: object | None = None,
    ):
        logger_system.info("EXIFPanel.__init__: Starting initialization...")
        super().__init__()
        # QSSで特定できるようにオブジェクト名を設定
        self.setObjectName("exifPanel")

        logger_system.info("EXIFPanel.__init__: Setting up managers...")
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.logger_system = logger_system
        self.error_handler = IntegratedErrorHandler(logger_system)
        self.theme_manager = theme_manager
        self._last_exif_data: dict[str, Any] | None = None
        self._applying_panel_theme = False
        self._current_latitude: float | None = None
        self._current_longitude: float | None = None

        # テーマ変更シグナルの接続（一時的に無効化してデバッグ）
        logger_system.info("EXIFPanel.__init__: Skipping theme signal connection for debugging...")
        # if self.theme_manager:
        #     try:
        #         if hasattr(self.theme_manager, "theme_changed"):
        #             logger_system.info("EXIFPanel.__init__: Connecting to theme_changed signal...")
        #             self.theme_manager.theme_changed.connect(self._on_theme_changed)
        #             logger_system.info("EXIFPanel.__init__: Connected to theme_changed signal")
        #         elif hasattr(self.theme_manager, "theme_changed_compat"):
        #             logger_system.info("EXIFPanel.__init__: Connecting to theme_changed_compat signal...")
        #             self.theme_manager.theme_changed_compat.connect(self._on_theme_changed)
        #             logger_system.info("EXIFPanel.__init__: Connected to theme_changed_compat signal")
        #     except Exception as e:
        #         logger_system.warning(f"EXIFPanel.__init__: Failed to connect theme signals: {e}")

        # EXIF処理エンジン
        logger_system.info("EXIFPanel.__init__: Creating image processor...")
        self.image_processor = CS4CodingImageProcessor(config_manager, logger_system)

        # 現在の画像パス
        self.current_image_path: Path | None = None

        # UI初期化（統合版）
        logger_system.info("EXIFPanel.__init__: Setting up integrated UI...")
        try:
            self._setup_ui()
            logger_system.info("EXIFPanel.__init__: Integrated UI ready")
        except Exception as e:
            logger_system.error(f"EXIFPanel.__init__: Failed to setup integrated UI, falling back: {e}")
            self._setup_placeholder_ui()

        # 背景の自動塗りつぶしを有効化
        with contextlib.suppress(Exception):
            self.setAutoFillBackground(True)

        logger_system.info("EXIFPanel.__init__: Initialization complete")

        # 高さ設定の復元は不要(固定高さのため)

    def changeEvent(self, event):  # type: ignore[override]
        """Qtのスタイル/パレット変更時に再適用"""
        try:
            if event and event.type() in (
                QEvent.Type.PaletteChange,
                QEvent.Type.ApplicationPaletteChange,
                QEvent.Type.ThemeChange,
            ):
                self._apply_panel_theme()
                self._update_theme_styles()
        except Exception:
            pass
        finally:
            super().changeEvent(event)

    def _get_color(self, color_key: str, default: str = "#000000") -> str:
        """テーママネージャーから色を取得"""
        try:
            if self.theme_manager and hasattr(self.theme_manager, "get_color"):
                return self.theme_manager.get_color(color_key, default)
        except Exception:
            pass
        return default

    def _get_color_safe(self, color_key: str, default: str = "#000000") -> str:
        """安全な色取得(エラー時はデフォルト値を返す)"""
        return self._get_color(color_key, default)

    def _is_dark_theme(self) -> bool:
        """現在のテーマがダークテーマかどうかを判定"""
        try:
            if self.theme_manager and hasattr(self.theme_manager, "get_current_theme"):
                current_theme = self.theme_manager.get_current_theme()
                return "dark" in current_theme.lower()
        except Exception:
            pass
        return False

    def _apply_panel_theme(self):
        """パネル自体にテーマを適用"""
        if self._applying_panel_theme:
            return

        self._applying_panel_theme = True
        try:
            try:
                bg_color = self._get_color("background", "#ffffff")
                border_color = self._get_color("border", "#e0e0e0")

                self.setStyleSheet(f"""
                    QWidget#exifPanel {{
                        background-color: {bg_color};
                        border: 1px solid {border_color};
                        border-radius: 5px;
                    }}
                """)
                # パレットも同期
                pal = self.palette()
                pal.setColor(self.backgroundRole(), pal.window().color())
                self.setPalette(pal)
            except Exception:
                # エラー時はデフォルトスタイルを適用
                self.setStyleSheet("""
                    QWidget#exifPanel {
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 5px;
                    }
                """)
        finally:
            self._applying_panel_theme = False

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            # パネル自体のテーマを更新
            self._apply_panel_theme()

            # 現在のEXIFデータがある場合は再表示
            if hasattr(self, "_last_exif_data") and self._last_exif_data:
                self._create_integrated_sections(self._last_exif_data)
        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "theme_change"},
                AIComponent.KIRO,
            )

    def _setup_placeholder_ui(self):
        """統合UI構築に失敗した場合のフォールバックUI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        label = QLabel("EXIF Panel - Minimal UI")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def _setup_ui(self):
        """UIの初期化(統合版)"""
        try:
            # パネル自体の背景テーマを適用
            self._apply_panel_theme()

            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # タイトル
            self.title_label = QLabel("📷 画像情報・位置情報")
            title_fg = self._get_color("foreground", "#2c3e50")
            title_bg = self._get_color("hover", self._get_color("background", "#ecf0f1"))
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    font-weight: bold;
                    font-size: 14px;
                    color: {title_fg};
                    padding: 5px;
                    background-color: {title_bg};
                    border-radius: 3px;
                }}
            """)
            layout.addWidget(self.title_label)

            # 統合情報エリア(スクロール可能・300px固定)
            self._create_integrated_info_area()
            layout.addWidget(self.integrated_scroll_area)

            # サイズ調整コントロールパネルは削除(不要なため)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "exif_panel_setup"},
                AIComponent.KIRO,
            )

    def _create_integrated_info_area(self):
        """統合情報エリアを作成(EXIF + GPS情報)- 300px固定版"""
        # 統合情報スクロールエリア(300px固定)
        self.integrated_scroll_area = QScrollArea()
        self.integrated_scroll_area.setWidgetResizable(True)
        self.integrated_scroll_area.setFixedHeight(300)  # 300pxに固定
        scroll_border = self._get_color("border", "#bdc3c7")
        scroll_bg = self._get_color("background", "#ffffff")
        scroll_focus = self._get_color("primary", "#3498db")
        self.integrated_scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {scroll_border};
                border-radius: 3px;
                background-color: {scroll_bg};
            }}
            QScrollArea:focus {{
                border: 2px solid {scroll_focus};
            }}
        """)

        # 統合情報表示ウィジェット
        self.integrated_widget = QWidget()
        self.integrated_layout = QVBoxLayout(self.integrated_widget)
        self.integrated_layout.setContentsMargins(10, 10, 10, 10)
        self.integrated_layout.setSpacing(10)

        # 初期メッセージ
        self.initial_message_label = QLabel("📷 画像を選択してください")
        self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_color = self._get_color_safe("foreground", "#7f8c8d")
        msg_bg = self._get_color_safe("background", "#ffffff")
        self.initial_message_label.setStyleSheet(f"""
            QLabel {{
                color: {msg_color};
                background-color: {msg_bg};
                font-style: italic;
                font-size: 16px;
                padding: 20px;
                border: 1px solid {self._get_color_safe("border", "#e0e0e0")};
                border-radius: 5px;
                margin: 10px;
            }}
        """)
        self.integrated_layout.addWidget(self.initial_message_label)

        self.integrated_scroll_area.setWidget(self.integrated_widget)

    def _clear_layout(self, layout: QVBoxLayout | QGridLayout):
        """Safely clear all items from a layout (widgets and nested layouts)."""
        try:
            while layout.count():
                item = layout.takeAt(0)
                child_widget = item.widget()
                child_layout = item.layout()
                if child_widget is not None:
                    child_widget.setParent(None)
                    child_widget.deleteLater()
                elif child_layout is not None:
                    self._clear_layout(child_layout)
        except Exception:
            pass

    def _create_integrated_sections(self, exif_data: dict[str, Any]):
        """統合セクションを作成(EXIF + GPS情報)"""
        try:
            # デバッグログ開始
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    f"EXIF統合セクション作成開始: exif_data={len(exif_data) if exif_data else 0}件",
                )

            # 既存のウィジェットを確実にクリア
            self._clear_layout(self.integrated_layout)
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "レイアウトクリア完了",
                )

            if not exif_data:
                self.initial_message_label = QLabel("❌ EXIF情報が見つかりません")
                self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.initial_message_label.setStyleSheet(
                    f"color: {self._get_color('error', '#e74c3c')}; font-style: italic; font-size: 16px; padding: 20px;"
                )
                self.integrated_layout.addWidget(self.initial_message_label)
                if hasattr(self, "logger_system"):
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "exif_panel_debug",
                        "EXIFデータなしメッセージ表示",
                    )
                return

            # 1. ファイル情報セクション
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "ファイル情報セクション作成開始",
                )
            self._create_file_info_section(exif_data)

            # 2. カメラ情報セクション
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "カメラ情報セクション作成開始",
                )
            self._create_camera_info_section(exif_data)

            # 3. 撮影設定セクション
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "撮影設定セクション作成開始",
                )
            self._create_shooting_settings_section(exif_data)

            # 4. 撮影日時セクション
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "撮影日時セクション作成開始",
                )
            self._create_datetime_section(exif_data)

            # 5. GPS位置情報セクション(統合版)
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "GPS位置情報セクション作成開始",
                )
            self._create_gps_info_section(exif_data)

            # 6. デバッグ情報セクション(折りたたみ可能)
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "デバッグ情報セクション作成開始",
                )
            self._create_debug_section_integrated(exif_data)

            # 7. 地図連携コントロール
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "地図連携コントロール作成開始",
                )
            self._create_map_controls_integrated()

            # スクロールエリアに再バインド(安全策)
            try:
                self.integrated_scroll_area.setWidget(self.integrated_widget)
                self.integrated_scroll_area.setWidgetResizable(True)
            except Exception:
                pass

            # 再描画をトリガ(強化版)
            try:
                self.integrated_layout.invalidate()
                self.integrated_layout.update()
            except Exception:
                pass

            try:
                self.integrated_widget.adjustSize()
                self.integrated_widget.update()
                self.integrated_widget.repaint()
            except Exception:
                pass

            try:
                self.integrated_scroll_area.widget().adjustSize()
                self.integrated_scroll_area.update()
                self.integrated_scroll_area.repaint()
            except Exception:
                pass

            # 強制的にレイアウトを再計算
            try:
                self.integrated_scroll_area.setWidget(self.integrated_widget)
                self.integrated_scroll_area.setWidgetResizable(True)
            except Exception:
                pass

            # ログ
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_sections_created",
                    "EXIF統合セクションを再構築",
                )
        except Exception as e:
            # エラー時はユーザーにわかる形で表示
            self._show_error_message("EXIF情報セクションの構築中にエラーが発生しました")
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "create_integrated_sections"},
                AIComponent.KIRO,
            )

    def _create_file_info_section(self, exif_data: dict[str, Any]):
        """ファイル情報セクションを作成"""
        try:
            file_info: dict[str, str] = {}
            if "File Name" in exif_data:
                file_info["ファイル名"] = str(exif_data["File Name"])
            if "File Size" in exif_data:
                file_info["ファイルサイズ"] = str(exif_data["File Size"])
            if "Modified" in exif_data:
                file_info["更新日時"] = str(exif_data["Modified"])
            if "Extension" in exif_data:
                file_info["拡張子"] = str(exif_data["Extension"])

            # デバッグ用: 常にセクションを作成(空でも)
            if not file_info:
                file_info["デバッグ"] = "ファイル情報なし"

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    f"ファイル情報セクション作成: {len(file_info)}件",
                )

            file_section = self._create_info_section("📁 ファイル情報", file_info, "#34495e")
            self.integrated_layout.addWidget(file_section)

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "ファイル情報セクション追加完了",
                )
        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_error",
                    f"ファイル情報セクション作成エラー: {e!s}",
                )
            raise

    def _create_camera_info_section(self, exif_data: dict[str, Any]):
        """カメラ情報セクションを作成"""
        try:
            camera_info: dict[str, str] = {}
            if "Camera Make" in exif_data:
                camera_info["メーカー"] = str(exif_data["Camera Make"])
            if "Camera Model" in exif_data:
                camera_info["モデル"] = str(exif_data["Camera Model"])
            if "Lens Model" in exif_data:
                camera_info["レンズ"] = str(exif_data["Lens Model"])

            # デバッグ用: 常にセクションを作成(空でも)
            if not camera_info:
                camera_info["デバッグ"] = "カメラ情報なし"

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    f"カメラ情報セクション作成: {len(camera_info)}件",
                )

            camera_section = self._create_info_section("📸 カメラ情報", camera_info, "#8e44ad")
            self.integrated_layout.addWidget(camera_section)

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "カメラ情報セクション追加完了",
                )
        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_error",
                    f"カメラ情報セクション作成エラー: {e!s}",
                )
            raise

    def _create_shooting_settings_section(self, exif_data: dict[str, Any]):
        """撮影設定セクションを作成"""
        try:
            shooting_info: dict[str, str] = {}
            if "F-Number" in exif_data:
                shooting_info["F値"] = str(exif_data["F-Number"])
            if "Exposure Time" in exif_data:
                shooting_info["シャッター速度"] = str(exif_data["Exposure Time"])
            if "ISO Speed" in exif_data:
                shooting_info["ISO感度"] = str(exif_data["ISO Speed"])
            if "Focal Length" in exif_data:
                shooting_info["焦点距離"] = str(exif_data["Focal Length"])

            # デバッグ用: 常にセクションを作成(空でも)
            if not shooting_info:
                shooting_info["デバッグ"] = "撮影設定情報なし"

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    f"撮影設定セクション作成: {len(shooting_info)}件",
                )

            shooting_section = self._create_info_section("⚙️ 撮影設定", shooting_info, "#e67e22")
            self.integrated_layout.addWidget(shooting_section)

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "撮影設定セクション追加完了",
                )
        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_error",
                    f"撮影設定セクション作成エラー: {e!s}",
                )
            raise

    def _create_datetime_section(self, exif_data: dict[str, Any]):
        """撮影日時セクションを作成"""
        try:
            datetime_info: dict[str, str] = {}
            if "Date Taken" in exif_data:
                datetime_info["撮影日時"] = str(exif_data["Date Taken"])
            if "Date Original" in exif_data:
                datetime_info["元データ日時"] = str(exif_data["Date Original"])

            # デバッグ用: 常にセクションを作成(空でも)
            if not datetime_info:
                datetime_info["デバッグ"] = "日時情報なし"

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    f"撮影日時セクション作成: {len(datetime_info)}件",
                )

            datetime_section = self._create_info_section("📅 撮影日時", datetime_info, "#27ae60")
            self.integrated_layout.addWidget(datetime_section)

            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug",
                    "撮影日時セクション追加完了",
                )
        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_error",
                    f"撮影日時セクション作成エラー: {e!s}",
                )
            raise

    def _create_gps_info_section(self, exif_data: dict[str, Any]):
        """GPS位置情報セクションを作成(統合版)"""
        self.gps_group = QGroupBox("📍 位置情報 & 地図連携")
        border_col = self._get_color("border", "#3498db")
        title_col = self._get_color("primary", "#2980b9")
        self.gps_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {border_col};
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {title_col};
            }}
        """)

        gps_layout = QGridLayout(self.gps_group)
        gps_layout.setSpacing(8)

        # GPS座標情報を取得
        exif_data.get("GPS Latitude")
        exif_data.get("GPS Longitude")
        exif_data.get("GPS Altitude")
        exif_data.get("GPS Timestamp")
        exif_data.get("GPS Date")

        # 基本GPS座標情報
        coord_frame = QFrame()
        coord_frame.setFrameStyle(QFrame.Shape.Box)
        coord_border = self._get_color("border", "#bdc3c7")
        coord_frame.setStyleSheet(f"QFrame {{ border: 1px solid {coord_border}; border-radius: 3px; padding: 5px; }}")
        coord_layout = QGridLayout(coord_frame)
        coord_layout.setSpacing(5)

        # 緯度
        coord_layout.addWidget(QLabel("緯度:"), 0, 0)
        self.latitude_label = QLabel("Not available")
        self.latitude_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')}; font-weight: bold;")
        coord_layout.addWidget(self.latitude_label, 0, 1)

        # 経度
        coord_layout.addWidget(QLabel("経度:"), 1, 0)
        self.longitude_label = QLabel("Not available")
        self.longitude_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')}; font-weight: bold;")
        coord_layout.addWidget(self.longitude_label, 1, 1)

        # 高度
        coord_layout.addWidget(QLabel("高度:"), 2, 0)
        self.altitude_label = QLabel("Not available")
        self.altitude_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')};")
        coord_layout.addWidget(self.altitude_label, 2, 1)

        gps_layout.addWidget(coord_frame, 0, 0, 1, 2)

        # GPS時刻・日付情報
        time_frame = QFrame()
        time_frame.setFrameStyle(QFrame.Shape.Box)
        time_frame.setStyleSheet(f"QFrame {{ border: 1px solid {coord_border}; border-radius: 3px; padding: 5px; }}")
        time_layout = QGridLayout(time_frame)
        time_layout.setSpacing(5)

        # GPS時刻
        time_layout.addWidget(QLabel("GPS時刻:"), 0, 0)
        self.gps_time_label = QLabel("Not available")
        self.gps_time_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')};")
        time_layout.addWidget(self.gps_time_label, 0, 1)

        # GPS日付
        time_layout.addWidget(QLabel("GPS日付:"), 1, 0)
        self.gps_date_label = QLabel("Not available")
        self.gps_date_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')};")
        time_layout.addWidget(self.gps_date_label, 1, 1)

        gps_layout.addWidget(time_frame, 1, 0, 1, 2)

        self.integrated_layout.addWidget(self.gps_group)

    def _create_info_section(self, title: str, info_dict: dict[str, str], border_color: str = "#bdc3c7") -> QGroupBox:
        """情報セクションを作成(統合版)"""
        group = QGroupBox(title)

        # テーマから適切な色を取得
        border = self._get_color("border", border_color)
        bg = self._get_color("background", "#ffffff")
        fg = self._get_color("foreground", "#2c3e50")
        primary = self._get_color("primary", "#3498db")
        secondary = self._get_color("secondary", "#6c757d")

        # 背景と前景のコントラストを確保
        # 明度を計算してコントラストを確保
        bg_lightness = self._calculate_lightness(bg)
        fg_lightness = self._calculate_lightness(fg)

        # コントラスト比が不十分な場合、適切な色に調整
        if abs(bg_lightness - fg_lightness) < 0.3:
            if bg_lightness > 0.5:  # 明るい背景
                fg = self._get_color("primary", "#2c3e50")
            else:  # 暗い背景
                fg = self._get_color("foreground", "#ffffff")

        # セクションタイトルの色を設定
        title_color = primary if primary != bg else fg

        # ダークテーマかどうかを判定して、適切な色を選択
        is_dark_theme = self._is_dark_theme()

        if is_dark_theme:
            # ダークテーマ用の色
            border = "#4a4a4a"  # 暗いグレー
            bg = "#2d2d2d"  # 暗い背景
            fg = "#e0e0e0"  # 明るいテキスト
            title_color = "#5a9bd4"  # 青系のタイトル色
            secondary = "#a0a0a0"  # 明るいセカンダリ色
            hover_bg = "#3a3a3a"  # 暗いホバー背景
        else:
            # ライトテーマ用の色
            border = "#bdc3c7"  # 明るいグレー
            bg = "#ffffff"  # 白い背景
            fg = "#2c3e50"  # 暗いテキスト
            title_color = "#3498db"  # 青系のタイトル色
            secondary = "#6c757d"  # 暗いセカンダリ色
            hover_bg = "#f8f9fa"  # 明るいホバー背景

        # デバッグ情報をログに出力
        if hasattr(self, "logger_system"):
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "exif_section_colors",
                f"セクション色設定: {title} - border:{border}, bg:{bg}, fg:{fg}, title:{title_color}",
            )

        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {border};
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: {bg};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px 0 5px;
                color: {title_color};
                font-size: 13px;
                font-weight: bold;
            }}
            QLabel[value-role="value"] {{
                color: {fg};
                font-weight: bold;
                padding: 2px 4px;
                background-color: {hover_bg};
                border-radius: 3px;
            }}
            QLabel[value-role="key"] {{
                color: {secondary};
                font-weight: normal;
                padding: 2px 4px;
            }}
        """)

        layout = QGridLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 15, 10, 10)

        row = 0
        for key, value in info_dict.items():
            key_label = QLabel(f"{key}:")
            key_label.setProperty("value-role", "key")
            key_label.setStyleSheet(f"color: {secondary};")

            value_label = QLabel(str(value))
            value_label.setProperty("value-role", "value")
            value_label.setStyleSheet(f"color: {fg}; font-weight: bold;")

            layout.addWidget(key_label, row, 0)
            layout.addWidget(value_label, row, 1)
            row += 1

        return group

    def _calculate_lightness(self, color: str) -> float:
        """色の明度を計算(0.0-1.0)"""
        try:
            # #RRGGBB形式の色をRGB値に変換
            if color.startswith("#") and len(color) == 7:
                r = int(color[1:3], 16) / 255.0
                g = int(color[3:5], 16) / 255.0
                b = int(color[5:7], 16) / 255.0

                # 相対輝度を計算(WCAG 2.1準拠)
                return 0.2126 * r + 0.7152 * g + 0.0722 * b
        except (ValueError, IndexError):
            pass

        # デフォルト値
        return 0.5

    def _create_debug_section_integrated(self, exif_data: dict[str, Any]):
        """デバッグ情報セクションを作成(統合版)"""
        # デバッグ情報の折りたたみボタン
        self.debug_toggle_button = QPushButton("🔧 デバッグ情報を表示")
        self.debug_toggle_button.setCheckable(True)
        warn_bg = self._get_color("warning", "#f39c12")
        warn_hover = self._get_color("hover", "#e67e22")
        warn_checked = self._get_color("accent", "#d35400")
        btn_fg = self._get_color("foreground", "#ffffff")
        self.debug_toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {warn_bg};
                color: {btn_fg};
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
                text-align: left;
                margin-top: 5px;
            }}
            QPushButton:hover {{
                background-color: {warn_hover};
            }}
            QPushButton:checked {{
                background-color: {warn_checked};
            }}
        """)
        self.debug_toggle_button.clicked.connect(self._toggle_debug_info)
        self.integrated_layout.addWidget(self.debug_toggle_button)

        # デバッグ情報フレーム(初期状態では非表示)
        self.debug_frame = QFrame()
        self.debug_frame.setFrameStyle(QFrame.Shape.Box)
        self.debug_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {warn_bg};
                border-radius: 3px;
                padding: 10px;
                background-color: {self._get_color("background", "#fef9e7")};
                margin-top: 5px;
            }}
        """)
        self.debug_frame.setVisible(False)

        debug_layout = QVBoxLayout(self.debug_frame)
        debug_layout.setSpacing(8)

        # 生のEXIF GPS情報
        raw_gps_label = QLabel("📋 生のEXIF GPS情報:")
        raw_gps_label.setStyleSheet(f"font-weight: bold; color: {warn_checked};")
        debug_layout.addWidget(raw_gps_label)

        self.raw_gps_text = QTextEdit()
        self.raw_gps_text.setMaximumHeight(100)
        dbg_border = self._get_color("border", "#bdc3c7")
        self.raw_gps_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self._get_color("background", "#ffffff")};
                border: 1px solid {dbg_border};
                border-radius: 3px;
                font-family: monospace;
                font-size: 10px;
                padding: 5px;
            }}
        """)
        self.raw_gps_text.setPlainText("GPS情報なし")
        debug_layout.addWidget(self.raw_gps_text)

        # 座標変換情報
        conversion_label = QLabel("🔄 座標変換情報:")
        conversion_label.setStyleSheet(f"font-weight: bold; color: {warn_checked};")
        debug_layout.addWidget(conversion_label)

        self.conversion_info_label = QLabel("変換情報なし")
        self.conversion_info_label.setStyleSheet(f"""
            QLabel {{
                color: {self._get_color("foreground", "#7f8c8d")};
                font-size: 10px;
                background-color: {self._get_color("background", "#ffffff")};
                border: 1px solid {dbg_border};
                border-radius: 3px;
                padding: 5px;
            }}
        """)
        self.conversion_info_label.setWordWrap(True)
        debug_layout.addWidget(self.conversion_info_label)

        self.integrated_layout.addWidget(self.debug_frame)

    def _create_map_controls_integrated(self):
        """地図連携コントロールを作成(統合版)"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.Box)
        success_bg = self._get_color("success", "#27ae60")
        control_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {success_bg};
                border-radius: 3px;
                padding: 10px;
                margin-top: 5px;
            }}
        """)

        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(8)

        # 更新ボタン
        self.refresh_button = QPushButton("🔄 更新")
        press_bg = self._get_color("selected", "#21618c")
        btn_fg = self._get_color("foreground", "#ffffff")
        primary_bg = self._get_color("primary", "#3498db")
        primary_hover = self._get_color("hover", "#2980b9")
        self.refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary_bg};
                color: {btn_fg};
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {primary_hover};
            }}
            QPushButton:pressed {{
                background-color: {press_bg};
            }}
        """)
        self.refresh_button.clicked.connect(self._refresh_exif_data)
        control_layout.addWidget(self.refresh_button)

        # 地図表示ボタン
        self.map_button = QPushButton("🗺️ 地図上に表示")
        map_hover = self._get_color("hover", "#229954")
        map_press = self._get_color("selected", "#1e8449")
        self.map_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {success_bg};
                color: {btn_fg};
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {map_hover};
            }}
            QPushButton:pressed {{
                background-color: {map_press};
            }}
        """)
        self.map_button.clicked.connect(self._show_on_map)
        self.map_button.setEnabled(False)  # 初期状態では無効
        control_layout.addWidget(self.map_button)

        # 座標コピーボタン
        self.copy_coords_button = QPushButton("📋 座標をコピー")
        copy_bg = self._get_color("accent", "#9b59b6")
        copy_hover = self._get_color("hover", "#8e44ad")
        copy_press = self._get_color("selected", "#7d3c98")
        self.copy_coords_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {copy_bg};
                color: {btn_fg};
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {copy_hover};
            }}
            QPushButton:pressed {{
                background-color: {copy_press};
            }}
        """)
        self.copy_coords_button.clicked.connect(self._copy_coordinates)
        self.copy_coords_button.setEnabled(False)  # 初期状態では無効
        control_layout.addWidget(self.copy_coords_button)

        control_layout.addStretch()

        self.integrated_layout.addWidget(control_frame)

    def _refresh_exif_data(self):
        """現在の画像からEXIF情報を再取得"""
        try:
            if not self.current_image_path or not self.current_image_path.exists():
                if self.logger_system:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "exif_refresh_skipped",
                        "No image selected for EXIF refresh",
                        context={"has_image": bool(self.current_image_path)},
                    )
                return

            if self.logger_system:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_refresh_requested",
                    f"Refreshing EXIF data for {self.current_image_path.name}",
                )

            self._load_exif_data()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "refresh_exif_data"},
                AIComponent.KIRO,
            )

    def _show_on_map(self):
        """現在のGPS座標を地図に表示"""
        try:
            if self._current_latitude is None or self._current_longitude is None:
                if self.logger_system:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "map_show_unavailable",
                        "Map display requested without GPS coordinates",
                    )
                return

            if self.logger_system:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "map_show_requested",
                    f"Show on map requested: {self._current_latitude:.6f}, {self._current_longitude:.6f}",
                )

            self.gps_coordinates_updated.emit(self._current_latitude, self._current_longitude)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "show_on_map"},
                AIComponent.KIRO,
            )

    def _copy_coordinates(self):
        """座標をクリップボードにコピー"""
        try:
            if self._current_latitude is None or self._current_longitude is None:
                if self.logger_system:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "copy_coordinates_unavailable",
                        "Copy requested without GPS coordinates",
                    )
                return

            clipboard = QApplication.clipboard()
            if not clipboard:
                if self.logger_system:
                    self.logger_system.log_ai_operation(
                        AIComponent.KIRO,
                        "copy_coordinates_failed",
                        "Clipboard not available",
                    )
                return

            coords_text = f"{self._current_latitude:.6f}, {self._current_longitude:.6f}"
            clipboard.setText(coords_text)

            if self.logger_system:
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "copy_coordinates_success",
                    f"Coordinates copied: {coords_text}",
                )

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "copy_coordinates"},
                AIComponent.KIRO,
            )

    def _toggle_debug_info(self, checked: bool):
        """デバッグ情報の表示/非表示を切り替える"""
        try:
            if hasattr(self, "debug_frame") and self.debug_frame:
                self.debug_frame.setVisible(checked)

            if hasattr(self, "debug_toggle_button") and self.debug_toggle_button:
                label = "🔧 デバッグ情報を非表示" if checked else "🔧 デバッグ情報を表示"
                self.debug_toggle_button.setText(label)

            if hasattr(self, "logger_system"):
                state = "shown" if checked else "hidden"
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug_toggle",
                    f"Debug section {state}",
                )
        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug_toggle_error",
                    f"Toggle debug info failed: {e!s}",
                )

    def _update_debug_info(self, raw_gps_info: list[str] | None, conversion_info: list[str] | None):
        """GPSデバッグ情報を更新"""
        try:
            if hasattr(self, "raw_gps_text") and self.raw_gps_text:
                raw_text = "\n".join(raw_gps_info) if raw_gps_info else "GPS情報なし"
                self.raw_gps_text.setPlainText(raw_text)

            if hasattr(self, "conversion_info_label") and self.conversion_info_label:
                conv_text = "\n".join(conversion_info) if conversion_info else "変換情報なし"
                self.conversion_info_label.setText(conv_text)

        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_debug_update_error",
                    f"Update debug info failed: {e!s}",
                )

    def _show_error_message(self, message: str):
        """EXIFパネル内にエラーメッセージを表示"""
        try:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_error_message",
                    message,
                )

            if hasattr(self, "integrated_layout") and self.integrated_layout:
                self._clear_layout(self.integrated_layout)
                error_label = QLabel(f"⚠️ {message}")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                error_label.setWordWrap(True)
                error_label.setStyleSheet(
                    f"color: {self._get_color('error', '#e74c3c')};font-weight: bold; font-size: 14px; padding: 15px;"
                )
                self.integrated_layout.addWidget(error_label)
            else:
                # 最低限ログに残す
                if hasattr(self, "logger_system"):
                    self.logger_system.warning(f"EXIFPanel error message (no layout): {message}")
        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "exif_panel_error_display_failure",
                    f"Failed to show error message: {e!s}",
                )

    def set_image(self, image_path: Path):
        """画像を設定してEXIF情報を取得"""
        try:
            self.current_image_path = image_path
            self._load_exif_data()

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "set_image", "image_path": str(image_path)},
                AIComponent.KIRO,
            )

    def _load_exif_data(self):
        """EXIF情報を読み込み(統合版)"""
        if not self.current_image_path or not self.current_image_path.exists():
            self._clear_integrated_display()
            return

        try:
            # EXIF情報を取得
            exif_data = self.image_processor.extract_exif(self.current_image_path)
            self._last_exif_data = exif_data

            # 統合表示を更新
            self._create_integrated_sections(exif_data)

            # GPS情報を更新
            self._update_gps_display(exif_data)

            # シグナルを発信
            self.exif_data_updated.emit(exif_data)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.CORE_ERROR,
                {
                    "operation": "load_exif_data",
                    "image_path": str(self.current_image_path),
                },
                AIComponent.KIRO,
            )
            self._show_error_message("EXIF情報の読み込みに失敗しました")

    def apply_theme(self):
        """テーマ変更時にスタイルを再適用(安全版)"""
        try:
            # テーマ変更中はUIの更新を一時停止
            self.setUpdatesEnabled(False)

            # 既存のウィジェットを安全にクリア
            self._safe_clear_layout()

            # 少し待機してからUI再構築
            if hasattr(self, "_last_exif_data") and self._last_exif_data:
                self._create_integrated_sections(self._last_exif_data)
                self._update_gps_display(self._last_exif_data)
            elif hasattr(self, "current_image_path") and self.current_image_path and self.current_image_path.exists():
                self._load_exif_data()

            # UI更新を再開
            self.setUpdatesEnabled(True)
            self.update()

        except Exception as e:
            # エラー時もUI更新を再開
            self.setUpdatesEnabled(True)
            if hasattr(self, "error_handler"):
                self.error_handler.handle_error(
                    e,
                    ErrorCategory.UI_ERROR,
                    {"operation": "apply_theme_to_exif_panel"},
                    AIComponent.KIRO,
                )

    def _clear_integrated_display(self):
        """統合表示をクリア"""
        try:
            # 既存のウィジェットをクリア
            for i in reversed(range(self.integrated_layout.count())):
                child = self.integrated_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()

            # GPS情報をリセット
            self._current_latitude = None
            self._current_longitude = None
            if hasattr(self, "map_button") and self.map_button:
                self.map_button.setEnabled(False)
            if hasattr(self, "copy_coords_button") and self.copy_coords_button:
                self.copy_coords_button.setEnabled(False)

            # 初期メッセージを表示
            self.initial_message_label = QLabel("📷 画像を選択してください")
            self.initial_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.initial_message_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-style: italic;
                    font-size: 16px;
                    padding: 20px;
                }
            """)
            self.integrated_layout.addWidget(self.initial_message_label)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "clear_integrated_display"},
                AIComponent.KIRO,
            )

    def _update_gps_display(self, exif_data: dict[str, Any]):
        """GPS位置情報の表示を更新(統合版)"""
        try:
            # GPS座標を取得(文字列から数値に変換)
            latitude_str = exif_data.get("GPS Latitude")
            longitude_str = exif_data.get("GPS Longitude")
            altitude = exif_data.get("GPS Altitude")
            gps_time = exif_data.get("GPS Timestamp")

            # 現在の座標をリセット
            self._current_latitude = None
            self._current_longitude = None

            # デバッグ情報用の生データを保存
            raw_gps_info = []
            conversion_info = []

            # 緯度・経度を数値に変換
            latitude = None
            longitude = None

            if latitude_str:
                raw_gps_info.append(f"緯度 (生データ): {latitude_str}")
                try:
                    # "35.123456°" のような形式から数値を抽出
                    if isinstance(latitude_str, str) and "°" in latitude_str:
                        latitude = float(latitude_str.replace("°", ""))
                        conversion_info.append(f"緯度変換: '{latitude_str}' → {latitude:.6f}")
                    elif isinstance(latitude_str, (int, float)):
                        latitude = float(latitude_str)
                        conversion_info.append(f"緯度変換: {latitude_str} → {latitude:.6f}")
                except (ValueError, TypeError) as e:
                    conversion_info.append(f"緯度変換エラー: {e}")
                    latitude = None

            if longitude_str:
                raw_gps_info.append(f"経度 (生データ): {longitude_str}")
                try:
                    # "139.123456°" のような形式から数値を抽出
                    if isinstance(longitude_str, str) and "°" in longitude_str:
                        longitude = float(longitude_str.replace("°", ""))
                        conversion_info.append(f"経度変換: '{longitude_str}' → {longitude:.6f}")
                    elif isinstance(longitude_str, (int, float)):
                        longitude = float(longitude_str)
                        conversion_info.append(f"経度変換: {longitude_str} → {longitude:.6f}")
                except (ValueError, TypeError) as e:
                    conversion_info.append(f"経度変換エラー: {e}")
                    longitude = None

            # 高度情報をデバッグに追加
            if altitude is not None:
                raw_gps_info.append(f"高度 (生データ): {altitude}")

            # GPS時刻・日付をデバッグに追加
            if gps_time:
                raw_gps_info.append(f"GPS時刻: {gps_time}")
            gps_date = exif_data.get("GPS Date")
            if gps_date:
                raw_gps_info.append(f"GPS日付: {gps_date}")

            # デバッグ情報を更新
            self._update_debug_info(raw_gps_info, conversion_info)

            # 緯度表示
            if latitude is not None:
                self.latitude_label.setText(f"{latitude:.6f}°")
                self.latitude_label.setStyleSheet(f"color: {self._get_color('success', '#27ae60')}; font-weight: bold;")
            else:
                self.latitude_label.setText("Not available")
                self.latitude_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')}; font-weight: bold;")

            # 経度表示
            if longitude is not None:
                self.longitude_label.setText(f"{longitude:.6f}°")
                self.longitude_label.setStyleSheet(
                    f"color: {self._get_color('success', '#27ae60')}; font-weight: bold;"
                )
            else:
                self.longitude_label.setText("Not available")
                self.longitude_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')}; font-weight: bold;")

            # 高度表示
            if altitude is not None:
                self.altitude_label.setText(f"{altitude:.1f}m")
                self.altitude_label.setStyleSheet(f"color: {self._get_color('success', '#27ae60')};")
            else:
                self.altitude_label.setText("Not available")
                self.altitude_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')};")

            # GPS時刻表示
            if gps_time:
                self.gps_time_label.setText(str(gps_time))
                self.gps_time_label.setStyleSheet(f"color: {self._get_color('success', '#27ae60')};")
            else:
                self.gps_time_label.setText("Not available")
                self.gps_time_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')};")

            # GPS日付表示
            if gps_date:
                self.gps_date_label.setText(str(gps_date))
                self.gps_date_label.setStyleSheet(f"color: {self._get_color('success', '#27ae60')};")
            else:
                self.gps_date_label.setText("Not available")
                self.gps_date_label.setStyleSheet(f"color: {self._get_color('error', '#e74c3c')};")

            # ボタンの有効/無効を設定
            has_gps = latitude is not None and longitude is not None

            if has_gps:
                self._current_latitude = latitude
                self._current_longitude = longitude
            else:
                self._current_latitude = None
                self._current_longitude = None

            if hasattr(self, "map_button") and self.map_button:
                self.map_button.setEnabled(has_gps)
            if hasattr(self, "copy_coords_button") and self.copy_coords_button:
                self.copy_coords_button.setEnabled(has_gps)

            # GPS座標がある場合はシグナルを発信
            if has_gps:
                self.gps_coordinates_updated.emit(latitude, longitude)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                ErrorCategory.UI_ERROR,
                {"operation": "update_gps_display"},
                AIComponent.KIRO,
            )

    def deleteLater(self):
        """安全なウィジェット削除"""
        try:
            # UI更新を停止
            self.setUpdatesEnabled(False)

            # 子ウィジェットを安全に削除
            self._safe_clear_layout()

            # 親クラスのdeleteLaterを呼び出し
            super().deleteLater()

        except Exception:
            # エラーが発生しても親クラスのdeleteLaterは呼び出す
            super().deleteLater()

    # Theme helpers

    def _safe_clear_layout(self):
        """安全なレイアウトクリア(Segmentation fault対策)"""
        try:
            if hasattr(self, "integrated_layout") and self.integrated_layout:
                # 子ウィジェットを安全に削除
                while self.integrated_layout.count():
                    item = self.integrated_layout.takeAt(0)
                    if item:
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()

                        layout = item.layout()
                        if layout:
                            self._clear_nested_layout(layout)

                # レイアウトを無効化
                self.integrated_layout.invalidate()

        except Exception as e:
            if hasattr(self, "logger_system"):
                self.logger_system.log_ai_operation(
                    AIComponent.KIRO,
                    "safe_clear_layout_error",
                    f"安全なレイアウトクリア中にエラー: {e!s}",
                )

    def _clear_nested_layout(self, layout):
        """ネストしたレイアウトを安全にクリア"""
        try:
            while layout.count():
                item = layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

                    nested_layout = item.layout()
                    if nested_layout:
                        self._clear_nested_layout(nested_layout)
        except Exception:
            pass

    def _on_theme_changed(self, theme_name: str):
        """テーマ変更時の処理"""
        try:
            self.logger_system.log_ai_operation(
                AIComponent.KIRO,
                "exif_panel_theme_change",
                f"EXIFパネルのテーマ変更: {theme_name}",
            )
            self._update_theme_styles()
        except Exception as e:
            self.logger_system.error(f"EXIFパネルのテーマ変更処理でエラー: {e}")

    def _update_theme_styles(self):
        """テーマに基づいてスタイルを更新"""
        try:
            # タイトルラベルのスタイル更新
            if hasattr(self, "title_label"):
                title_fg = self._get_color_safe("foreground", "#2c3e50")
                title_bg = self._get_color_safe("hover", self._get_color_safe("background", "#ecf0f1"))
                self.title_label.setStyleSheet(f"""
                    QLabel {{
                        font-weight: bold;
                        font-size: 14px;
                        color: {title_fg};
                        padding: 5px;
                        background-color: {title_bg};
                        border-radius: 3px;
                    }}
                """)

            # スクロールエリアのスタイル更新
            if hasattr(self, "integrated_scroll_area"):
                scroll_border = self._get_color_safe("border", "#bdc3c7")
                scroll_bg = self._get_color_safe("background", "#ffffff")
                scroll_focus = self._get_color_safe("primary", "#3498db")
                self.integrated_scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        border: 1px solid {scroll_border};
                        border-radius: 3px;
                        background-color: {scroll_bg};
                    }}
                    QScrollArea:focus {{
                        border: 2px solid {scroll_focus};
                    }}
                """)

            # 初期メッセージラベルのスタイル更新
            if hasattr(self, "initial_message_label"):
                msg_color = self._get_color_safe("foreground", "#7f8c8d")
                msg_bg = self._get_color_safe("background", "#ffffff")
                self.initial_message_label.setStyleSheet(f"""
                    QLabel {{
                        color: {msg_color};
                        background-color: {msg_bg};
                        font-style: italic;
                        font-size: 16px;
                        padding: 20px;
                        border: 1px solid {self._get_color_safe("border", "#e0e0e0")};
                        border-radius: 5px;
                        margin: 10px;
                    }}
                """)

        except Exception as e:
            self.logger_system.error(f"EXIFパネルのテーマスタイル更新でエラー: {e}")

    def _is_dark_theme(self) -> bool:
        """現在のテーマがダークテーマかどうかを判定"""
        try:
            # アプリケーションのパレットから色を取得
            app = QApplication.instance()
            if app:
                palette = app.palette()

                # ウィンドウテキストの色の明度を計算
                window_text_color = palette.color(palette.ColorRole.WindowText)
                lightness = (
                    (window_text_color.red() + window_text_color.green() + window_text_color.blue()) / 3.0 / 255.0
                )

                # 明度が0.5より高い場合はダークテーマと判定
                return lightness > 0.5
        except Exception:
            pass

        return False
