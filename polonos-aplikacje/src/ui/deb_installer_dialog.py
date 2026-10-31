import os
import json
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QPlainTextEdit, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont
from ui.assets_helper import get_logo_pixmap, get_logo_icon

DEB_MIME_TYPES = [
    "application/vnd.debian.binary-package",
    "application/x-deb",
    "application/x-debian-package"
]

DESKTOP_ID = "polonos-aplikacje.desktop"

def get_settings_path():
    config_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(config_dir, "polonos-aplikacje", "settings.json")

def load_app_settings():
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {
        "first_run_completed": False,
        "associate_deb_files": is_deb_associated()
    }

def save_app_settings(settings: dict):
    path = get_settings_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except OSError:
        pass

def get_mimeapps_path():
    config_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(config_dir, "mimeapps.list")

def is_deb_associated() -> bool:
    mimeapps = get_mimeapps_path()
    if os.path.exists(mimeapps):
        try:
            with open(mimeapps, "r", encoding="utf-8") as f:
                content = f.read()
            for mime in DEB_MIME_TYPES:
                if f"{mime}={DESKTOP_ID}" in content:
                    return True
        except Exception:
            pass

    try:
        res = subprocess.run(
            ["xdg-mime", "query", "default", "application/vnd.debian.binary-package"],
            capture_output=True, text=True, timeout=3
        )
        if DESKTOP_ID in res.stdout:
            return True
    except Exception:
        pass
    return False

def set_deb_association(enabled: bool):
    mimeapps = get_mimeapps_path()
    try:
        os.makedirs(os.path.dirname(mimeapps), exist_ok=True)
        lines = []
        if os.path.exists(mimeapps):
            with open(mimeapps, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(f"{m}=") for m in DEB_MIME_TYPES):
                if not enabled and DESKTOP_ID in stripped:
                    continue
                elif enabled:
                    continue
            cleaned_lines.append(line)

        if enabled:
            if "[Default Applications]" not in [l.strip() for l in cleaned_lines]:
                if cleaned_lines and cleaned_lines[-1].strip() != "":
                    cleaned_lines.append("")
                cleaned_lines.append("[Default Applications]")

            out_lines = []
            inserted = False
            for line in cleaned_lines:
                out_lines.append(line)
                if line.strip() == "[Default Applications]" and not inserted:
                    for m in DEB_MIME_TYPES:
                        out_lines.append(f"{m}={DESKTOP_ID}")
                    inserted = True
            cleaned_lines = out_lines

        with open(mimeapps, "w", encoding="utf-8") as f:
            f.write("\n".join(cleaned_lines) + "\n")

        if enabled:
            try:
                subprocess.run(
                    ["xdg-mime", "default", DESKTOP_ID] + DEB_MIME_TYPES,
                    capture_output=True, timeout=4
                )
            except Exception:
                pass
    except OSError:
        pass

class SettingsDialog(QDialog):
    def __init__(self, parent=None, is_first_run=False, on_deb_open_requested=None):
        super().__init__(parent)
        self.is_first_run = is_first_run
        self.on_deb_open_requested = on_deb_open_requested
        self.setWindowTitle("Ustawienia — PolonOS Aplikacje")
        self.setWindowIcon(get_logo_icon())
        self.setFixedSize(560, 410 if not is_first_run else 440)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_label = QLabel()
        logo_pm = get_logo_pixmap(52, 52)
        if not logo_pm.isNull():
            icon_label.setPixmap(logo_pm)
        header_layout.addWidget(icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        lbl_title = QLabel(
            "Witaj w PolonOS Aplikacje! Skonfiguruj ustawienia"
            if self.is_first_run else "Ustawienia programu PolonOS Aplikacje"
        )
        font_t = QFont()
        font_t.setPointSize(14)
        font_t.setBold(True)
        lbl_title.setFont(font_t)
        lbl_title.setStyleSheet("color: #ffffff;")

        lbl_sub = QLabel(
            "Wybierz, czy program ma domyślnie otwierać i instalować pobrane pakiety .deb."
        )
        lbl_sub.setStyleSheet("color: #a1a1aa; font-size: 12px;")

        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        deb_card = QFrame()
        deb_card.setObjectName("card_frame")
        deb_layout = QVBoxLayout(deb_card)
        deb_layout.setContentsMargins(16, 14, 16, 14)
        deb_layout.setSpacing(8)

        lbl_deb_h = QLabel("Obsługa plików instalacyjnych Debian (.deb)")
        lbl_deb_h.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px;")

        lbl_deb_desc = QLabel(
            "Czy chcesz powiązać PolonOS Aplikacje z plikami .deb? "
            "Gdy ta opcja jest włączona, dwukrotne kliknięcie dowolnego pliku .deb w menedżerze plików "
            "(np. Dolphin) otworzy instalator PolonOS Aplikacje i pozwoli zainstalować program jednym kliknięciem."
        )
        lbl_deb_desc.setWordWrap(True)
        lbl_deb_desc.setStyleSheet("color: #d4d4d8; font-size: 12px; line-height: 1.4;")

        self.chk_deb_assoc = QCheckBox("Powiąż pliki .deb z programem PolonOS Aplikacje (zalecane)")
        self.chk_deb_assoc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_deb_assoc.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; margin-top: 4px;")

        settings = load_app_settings()
        if self.is_first_run and not settings.get("first_run_completed", False):
            self.chk_deb_assoc.setChecked(True)
        else:
            self.chk_deb_assoc.setChecked(is_deb_associated())

        deb_layout.addWidget(lbl_deb_h)
        deb_layout.addWidget(lbl_deb_desc)
        deb_layout.addWidget(self.chk_deb_assoc)

        if self.on_deb_open_requested is not None:
            btn_row = QHBoxLayout()
            btn_pick_deb = QPushButton("Zainstaluj plik .deb z dysku...")
            btn_pick_deb.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_pick_deb.clicked.connect(self.pick_and_open_deb)
            btn_row.addWidget(btn_pick_deb)
            btn_row.addStretch()
            deb_layout.addLayout(btn_row)

        layout.addWidget(deb_card)

        layout.addStretch()

        footer = QHBoxLayout()
        if self.is_first_run:
            btn_skip = QPushButton("Nie teraz")
            btn_skip.clicked.connect(self.reject_first_run)
            footer.addWidget(btn_skip)
        else:
            btn_cancel = QPushButton("Anuluj")
            btn_cancel.clicked.connect(self.reject)
            footer.addWidget(btn_cancel)

        footer.addStretch()

        btn_save = QPushButton("Zapisz ustawienia")
        btn_save.setObjectName("primary_btn")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_and_close)
        footer.addWidget(btn_save)

        layout.addLayout(footer)

    def pick_and_open_deb(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz pakiet Debian (.deb) do zainstalowania",
            os.path.expanduser("~"),
            "Pakiety Debian (*.deb)"
        )
        if file_path and os.path.isfile(file_path):
            self.save_and_close()
            if self.on_deb_open_requested:
                self.on_deb_open_requested(file_path)

    def reject_first_run(self):
        set_deb_association(False)
        save_app_settings({
            "first_run_completed": True,
            "associate_deb_files": False
        })
        self.reject()

    def save_and_close(self):
        assoc = self.chk_deb_assoc.isChecked()
        set_deb_association(assoc)
        save_app_settings({
            "first_run_completed": True,
            "associate_deb_files": assoc
        })
        self.accept()

class DebPackageDialog(QDialog):
    def __init__(self, deb_path: str, apt_manager=None, parent=None):
        super().__init__(parent)
        self.deb_path = os.path.abspath(deb_path)
        self.apt_manager = apt_manager
        self.process = None
        self.meta = self._parse_deb_metadata(self.deb_path)

        pkg_title = self.meta.get("Package", os.path.basename(self.deb_path))
        self.setWindowTitle(f"Instalator pakietu .deb: {pkg_title}")
        self.setWindowIcon(get_logo_icon())
        self.setFixedSize(640, 480)
        self.setModal(True)
        self.init_ui()

    @staticmethod
    def _parse_deb_metadata(deb_path: str) -> dict:
        info = {
            "Package": os.path.basename(deb_path),
            "Version": "nieznana",
            "Architecture": "all",
            "Maintainer": "brak danych",
            "Installed-Size": "",
            "Description": "Pakiet instalacyjny Debian (.deb)."
        }
        if not os.path.isfile(deb_path):
            return info
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C"
            res = subprocess.run(
                ["dpkg-deb", "-I", deb_path],
                capture_output=True, text=True, timeout=6, env=env
            )
            if res.returncode == 0:
                desc_lines = []
                in_desc = False
                for line in res.stdout.splitlines():
                    if in_desc:
                        if line.startswith("  ") or line.startswith("\t"):
                            desc_lines.append(line.strip())
                            continue
                        else:
                            in_desc = False
                    stripped = line.strip()
                    for field in ("Package", "Version", "Architecture", "Maintainer", "Installed-Size"):
                        if stripped.startswith(f"{field}:"):
                            info[field] = stripped.split(":", 1)[1].strip()
                    if stripped.startswith("Description:"):
                        first_desc = stripped.split(":", 1)[1].strip()
                        if first_desc:
                            desc_lines.append(first_desc)
                        in_desc = True
                if desc_lines:
                    info["Description"] = "\n".join(desc_lines)
        except Exception:
            pass
        return info

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        icon_label = QLabel()
        logo_pm = get_logo_pixmap(56, 56)
        if not logo_pm.isNull():
            icon_label.setPixmap(logo_pm)
        header_layout.addWidget(icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        pkg_name = self.meta.get("Package", os.path.basename(self.deb_path))
        pkg_ver = self.meta.get("Version", "")
        pkg_arch = self.meta.get("Architecture", "")
        pkg_maint = self.meta.get("Maintainer", "")
        inst_size_kb = self.meta.get("Installed-Size", "")
        try:
            size_str = f"{float(inst_size_kb) / 1024:.1f} MB" if inst_size_kb else f"{os.path.getsize(self.deb_path) / (1024 * 1024):.1f} MB"
        except Exception:
            size_str = "b/d"

        lbl_name = QLabel(f"{pkg_name} ({pkg_ver})")
        font_t = QFont()
        font_t.setPointSize(16)
        font_t.setBold(True)
        lbl_name.setFont(font_t)
        lbl_name.setStyleSheet("color: #ffffff;")

        lbl_meta = QLabel(f"Architektura: {pkg_arch}  |  Rozmiar: {size_str}\nOpiekun: {pkg_maint}")
        lbl_meta.setStyleSheet("color: #a1a1aa; font-size: 12px;")

        is_already_installed = self.apt_manager.is_package_installed(pkg_name) if self.apt_manager else False
        if is_already_installed:
            self.lbl_status = QLabel("✓ Pakiet jest już zainstalowany w systemie (możesz zainstalować ponownie / zaktualizować)")
            self.lbl_status.setStyleSheet("color: #34d399; font-weight: bold; font-size: 12px;")
        else:
            self.lbl_status = QLabel(f"• Plik gotowy do instalacji: {os.path.basename(self.deb_path)}")
            self.lbl_status.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 12px;")

        title_box.addWidget(lbl_name)
        title_box.addWidget(lbl_meta)
        title_box.addWidget(self.lbl_status)
        header_layout.addLayout(title_box, 1)
        layout.addLayout(header_layout)

        desc_box = QFrame()
        desc_box.setObjectName("card_frame")
        d_layout = QVBoxLayout(desc_box)
        d_layout.setContentsMargins(16, 12, 16, 12)

        lbl_desc_title = QLabel("Opis pakietu:")
        lbl_desc_title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px;")

        lbl_desc = QLabel(self.meta.get("Description", ""))
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #d4d4d8; font-size: 12px; line-height: 1.4;")

        d_layout.addWidget(lbl_desc_title)
        d_layout.addWidget(lbl_desc)
        d_layout.addStretch()
        layout.addWidget(desc_box, 1)

        self.console = QPlainTextEdit()
        self.console.setObjectName("console_output")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(110)
        self.console.setVisible(False)
        layout.addWidget(self.console)

        footer = QHBoxLayout()
        self.btn_close = QPushButton("Zamknij")
        self.btn_close.clicked.connect(self.accept)

        btn_label = "Zainstaluj pakiet ponownie" if is_already_installed else "Zainstaluj pakiet .deb"
        self.btn_install = QPushButton(btn_label)
        self.btn_install.setObjectName("primary_btn")
        self.btn_install.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_install.clicked.connect(self.install_deb_file)

        footer.addWidget(self.btn_close)
        footer.addStretch()
        footer.addWidget(self.btn_install)
        layout.addLayout(footer)

    def install_deb_file(self):
        if not os.path.isfile(self.deb_path):
            self.lbl_status.setText("Nie znaleziono pliku .deb na dysku.")
            self.lbl_status.setStyleSheet("color: #f87171; font-weight: bold;")
            return

        self.btn_install.setEnabled(False)
        self.console.setVisible(True)
        self.console.appendPlainText(f"[PolonOS] Instalowanie pliku {self.deb_path}...")

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(
            lambda: self.console.appendPlainText(
                self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore").strip()
            )
        )
        self.process.readyReadStandardError.connect(
            lambda: self.console.appendPlainText(
                self.process.readAllStandardError().data().decode("utf-8", errors="ignore").strip()
            )
        )
        self.process.finished.connect(self.on_install_finished)

        escaped_path = self.deb_path.replace("'", "'\\''")
        shell_cmd = (
            "export DEBIAN_FRONTEND=noninteractive; "
            f"apt-get install -y --reinstall --allow-downgrades '{escaped_path}' "
            f"|| (dpkg -i --force-overwrite '{escaped_path}' && apt-get install -f -y)"
        )
        self.process.start("pkexec", ["sh", "-c", shell_cmd])

    def on_install_finished(self, exit_code, _exit_status):
        if exit_code == 0:
            if self.apt_manager:
                self.apt_manager.refresh_installed_cache()
            self.console.appendPlainText("\n[PolonOS] ✓ Pakiet .deb został zainstalowany pomyślnie!")
            self.lbl_status.setText("✓ Pakiet został pomyślnie zainstalowany w systemie!")
            self.lbl_status.setStyleSheet("color: #34d399; font-weight: bold; font-size: 13px;")
            self.btn_install.setVisible(False)
            self.btn_close.setObjectName("primary_btn")
            self.btn_close.style().unpolish(self.btn_close)
            self.btn_close.style().polish(self.btn_close)
        else:
            self.console.appendPlainText(f"\n[PolonOS] Błąd podczas instalacji pakietu (kod {exit_code}).")
            self.lbl_status.setText(f"Instalacja nie powiodła się (kod {exit_code}).")
            self.lbl_status.setStyleSheet("color: #f87171; font-weight: bold;")
            self.btn_install.setEnabled(True)
