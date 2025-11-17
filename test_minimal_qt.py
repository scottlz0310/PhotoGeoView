#!/usr/bin/env python3
"""Minimal Qt window test"""

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


def main():
    print("Creating QApplication...")
    app = QApplication(sys.argv)

    print("Creating QMainWindow...")
    window = QMainWindow()
    window.setWindowTitle("Minimal Test Window")
    window.resize(400, 300)

    print("Adding central widget...")
    label = QLabel("Hello, Qt!")
    window.setCentralWidget(label)

    print("Showing window...")
    window.show()
    print("Window shown!")

    print("Starting event loop...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
