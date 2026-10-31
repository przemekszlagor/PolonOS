#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if "/usr/lib/python3/dist-packages" not in sys.path and os.path.isdir("/usr/lib/python3/dist-packages"):
    sys.path.append("/usr/lib/python3/dist-packages")

from PyQt6.QtWidgets import QApplication
from urllib.parse import unquote, urlparse
from ui.main_window import MainWindow

def _extract_deb_arg(argv):
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        candidate = arg
        if candidate.startswith("file://"):
            candidate = unquote(urlparse(candidate).path)
        if candidate.lower().endswith(".deb") and os.path.isfile(candidate):
            return os.path.abspath(candidate)
    return None

def main():
    start_in_tray = "--tray" in sys.argv
    deb_file_path = _extract_deb_arg(sys.argv)
    if deb_file_path:
        start_in_tray = False

    app = QApplication(sys.argv)
    app.setApplicationName("PolonOS Aplikacje")
    app.setDesktopFileName("polonos-aplikacje")
    app.setOrganizationName("PolonOS")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(start_in_tray=start_in_tray, deb_file_path=deb_file_path)
    if not start_in_tray:
        window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
