"""
EXIF Panel Theme Debug App

EXIFパネル単体のテーマ追随を検証する最小アプリ。

起動例:
  python tools/debug/exif_theme_debug.py --theme dark --image ~/Samples/sample.jpg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

sys.path.insert(0, str(Path(__file__).parents[2]))

from src.integration.config_manager import ConfigManager
from src.integration.logging_system import LoggerSystem
from src.integration.state_manager import StateManager
from src.integration.ui.exif_panel import EXIFPanel
from src.integration.ui.theme_manager import IntegratedThemeManager


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", default="dark")
    parser.add_argument("--image", type=str, default="")
    args = parser.parse_args()

    app = QApplication(sys.argv)

    logger = LoggerSystem()
    config = ConfigManager(logger_system=logger)
    state = StateManager(config_manager=config, logger_system=logger)

    win = QMainWindow()
    win.setWindowTitle("EXIF Theme Debug")
    central = QWidget()
    win.setCentralWidget(central)
    layout = QVBoxLayout(central)

    theme_manager = IntegratedThemeManager(config, state, logger, win)
    theme_manager.apply_theme(args.theme)

    panel = EXIFPanel(config, state, logger, theme_manager)
    layout.addWidget(panel)

    if args.image:
        p = Path(args.image).expanduser()
        if p.exists():
            panel.set_image(p)

    win.resize(900, 600)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
