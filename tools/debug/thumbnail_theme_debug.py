"""
Thumbnail Theme Debug App

サムネイル単体のテーマ追随問題を切り分けるための最小検証アプリ。

起動方法:
  python tools/debug/thumbnail_theme_debug.py --theme dark

依存:
  - PySide6
  - src.integration.ui.theme_manager.IntegratedThemeManager
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
from src.integration.ui.theme_manager import IntegratedThemeManager
from src.integration.ui.thumbnail_grid import OptimizedThumbnailGrid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", default="dark")
    args = parser.parse_args()

    app = QApplication(sys.argv)

    logger = LoggerSystem()
    config = ConfigManager(logger_system=logger)
    state = StateManager(config_manager=config, logger_system=logger)

    win = QMainWindow()
    win.setWindowTitle("Thumbnail Theme Debug")
    central = QWidget()
    win.setCentralWidget(central)
    layout = QVBoxLayout(central)

    theme_manager = IntegratedThemeManager(config, state, logger, win)
    theme_manager.apply_theme(args.theme)

    grid = OptimizedThumbnailGrid(config, state, logger, theme_manager)
    layout.addWidget(grid)

    # サンプル画像: ホームのPicturesやSamplesから数枚取得
    sample_dirs = [Path.home() / "Pictures", Path.home() / "Samples"]
    images = []
    for d in sample_dirs:
        if d.exists():
            images.extend(
                [
                    p
                    for p in d.iterdir()
                    if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
                ]
            )
        if len(images) >= 8:
            break
    grid.set_image_list(images[:8])

    win.resize(900, 600)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
