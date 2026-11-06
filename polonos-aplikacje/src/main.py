#!/usr/bin/env python3
import sys
import os
import json
import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if "/usr/lib/python3/dist-packages" not in sys.path and os.path.isdir("/usr/lib/python3/dist-packages"):
    sys.path.append("/usr/lib/python3/dist-packages")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
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

def _get_ipc_socket_name() -> str:
    return f"/tmp/polonos-aplikacje-ipc-{os.getuid()}"

def _send_to_running_instance(socket_name: str, payload: dict) -> bool:
    sock = QLocalSocket()
    sock.connectToServer(socket_name)
    if not sock.waitForConnected(400):
        return False
    data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    sock.write(data)
    sock.flush()
    sock.waitForBytesWritten(500)
    sock.disconnectFromServer()
    return True

def _cleanup_legacy_instances():
    my_pid = os.getpid()
    my_uid = os.getuid()
    try:
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            pid = int(entry)
            if pid == my_pid:
                continue
            proc_dir = f"/proc/{pid}"
            try:
                if os.stat(proc_dir).st_uid != my_uid:
                    continue
                with open(f"{proc_dir}/cmdline", "rb") as f:
                    raw_args = f.read().split(b"\x00")
                args = [a.decode("utf-8", errors="ignore") for a in raw_args if a]
                if any(a.endswith("/polonos-aplikacje/src/main.py") for a in args if "\n" not in a):
                    os.kill(pid, signal.SIGTERM)
            except Exception:
                continue
    except Exception:
        pass

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

    socket_name = _get_ipc_socket_name()
    if deb_file_path:
        ipc_payload = {"action": "open_deb", "deb_path": deb_file_path}
    elif start_in_tray:
        ipc_payload = {"action": "noop"}
    else:
        ipc_payload = {"action": "activate"}

    if _send_to_running_instance(socket_name, ipc_payload):
        sys.exit(0)

    _cleanup_legacy_instances()

    QLocalServer.removeServer(socket_name)
    ipc_server = QLocalServer(app)
    ipc_server.listen(socket_name)

    window = MainWindow(start_in_tray=start_in_tray, deb_file_path=deb_file_path, ipc_server=ipc_server)
    if not start_in_tray:
        window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
