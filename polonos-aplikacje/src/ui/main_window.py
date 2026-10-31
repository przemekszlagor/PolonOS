import os
import json
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QGridLayout,
    QProgressBar, QCheckBox, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from ui.styles import POLONOS_DARK_STYLE
from ui.tab_updates import TabUpdates
from ui.tab_store import TabStore
from ui.tab_upgrade import TabUpgrade
from ui.about_dialog import AboutDialog
from ui.deb_installer_dialog import (
    SettingsDialog, DebPackageDialog, load_app_settings
)
from ui.assets_helper import get_logo_pixmap, get_logo_icon, get_tray_icon

from backend.apt_manager import AptManager
from backend.dist_upgrader import DistUpgrader

AUTOSTART_FILENAME = "polonos-aplikacje.desktop"
CHECK_INTERVAL_SECONDS = 6 * 60 * 60

def get_update_state_path():
    config_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(config_dir, "polonos-aplikacje", "update_state.json")

def load_update_state():
    path = get_update_state_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {
        "last_check_timestamp": 0.0,
        "last_check_iso": "",
        "pkg_updates_count": 0,
        "dist_upgrade_available": False
    }

def save_update_state(last_check_timestamp: float, pkg_updates_count: int, dist_upgrade_available: bool):
    path = get_update_state_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "last_check_timestamp": float(last_check_timestamp),
            "last_check_iso": datetime.fromtimestamp(last_check_timestamp).isoformat(timespec="seconds") if last_check_timestamp > 0 else "",
            "pkg_updates_count": int(pkg_updates_count),
            "dist_upgrade_available": bool(dist_upgrade_available)
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except OSError:
        pass

def get_user_autostart_path():
    config_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(config_dir, "autostart", AUTOSTART_FILENAME)

def get_system_autostart_path():
    return os.path.join("/etc/xdg/autostart", AUTOSTART_FILENAME)

def is_autostart_enabled():
    user_path = get_user_autostart_path()
    if os.path.exists(user_path):
        try:
            with open(user_path, "r", encoding="utf-8") as f:
                content = f.read()
            for line in content.splitlines():
                line_s = line.strip().lower()
                if line_s == "hidden=true" or line_s == "x-kde-autostart-enabled=false":
                    return False
            return True
        except Exception:
            return False
    return os.path.exists(get_system_autostart_path())

def set_autostart_enabled(enabled: bool):
    user_path = get_user_autostart_path()
    try:
        os.makedirs(os.path.dirname(user_path), exist_ok=True)
        if enabled:
            desktop_entry = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=PolonOS Aplikacje (Demon aktualizacji)\n"
                "Comment=Monitoruje dostępność aktualizacji w zasobniku systemowym PolonOS\n"
                "Exec=/usr/bin/polonos-aplikacje --tray\n"
                "Icon=polonos-aplikacje\n"
                "Terminal=false\n"
                "Categories=System;PackageManager;\n"
                "X-KDE-autostart-after=panel\n"
                "X-KDE-StartupNotify=false\n"
                "Hidden=false\n"
            )
            with open(user_path, "w", encoding="utf-8") as f:
                f.write(desktop_entry)
        else:
            if os.path.exists(get_system_autostart_path()):
                desktop_entry = (
                    "[Desktop Entry]\n"
                    "Type=Application\n"
                    "Name=PolonOS Aplikacje\n"
                    "Hidden=true\n"
                )
                with open(user_path, "w", encoding="utf-8") as f:
                    f.write(desktop_entry)
            else:
                if os.path.exists(user_path):
                    os.remove(user_path)
    except OSError:
        pass

class AppInitWorker(QThread):
    init_finished = pyqtSignal()

    def __init__(self, apt_manager):
        super().__init__()
        self.apt_manager = apt_manager

    def run(self):
        self.apt_manager.refresh_installed_cache()
        self.init_finished.emit()

class MainWindow(QMainWindow):
    def __init__(self, start_in_tray=False, deb_file_path=None):
        super().__init__()
        self._start_in_tray = start_in_tray
        self._initial_deb_path = deb_file_path
        self._force_quit = False

        saved_state = load_update_state()
        self._last_check_ts = float(saved_state.get("last_check_timestamp", 0.0))
        self._pkg_updates_count = int(saved_state.get("pkg_updates_count", 0))
        self._dist_upgrade_available = bool(saved_state.get("dist_upgrade_available", False))

        self.setWindowTitle("PolonOS Aplikacje")
        self.resize(1080, 720)
        self.setMinimumSize(900, 600)

        self.setWindowIcon(get_logo_icon())

        self.apt_manager = AptManager()
        self.dist_upgrader = DistUpgrader()

        self.setStyleSheet(POLONOS_DARK_STYLE)

        self.init_ui()
        self.init_tray_daemon()

        QTimer.singleShot(150, self.start_background_loading)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header_bar = QFrame()
        header_bar.setObjectName("header_bar")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(20, 14, 20, 14)

        logo_label = QLabel()
        logo_pm = get_logo_pixmap(44, 44)
        if not logo_pm.isNull():
            logo_label.setPixmap(logo_pm)
        else:
            logo_label.setFixedSize(44, 44)
            logo_label.setStyleSheet("background-color: #c22e45; border-radius: 8px;")

        header_layout.addWidget(logo_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        lbl_title = QLabel("PolonOS Aplikacje")
        lbl_title.setObjectName("header_title")

        lbl_sub = QLabel("Centrum aktualizacji i zarządzania oprogramowaniem")
        lbl_sub.setObjectName("header_subtitle")

        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        btn_settings = QPushButton("Ustawienia")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self.show_settings)

        btn_about = QPushButton("O programie")
        btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_about.clicked.connect(self.show_about)

        header_layout.addWidget(btn_settings)
        header_layout.addWidget(btn_about)

        main_layout.addWidget(header_bar)

        content_container = QWidget()
        self.grid_layout = QGridLayout(content_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        self.tab_updates = TabUpdates(self.apt_manager, self, auto_load=False)
        self.tab_store = TabStore(self.apt_manager, self)
        self.tab_upgrade = TabUpgrade(self.dist_upgrader, self, auto_check=False)

        self.tab_updates.updates_count_changed.connect(self.on_pkg_updates_count_changed)
        self.tab_upgrade.dist_upgrade_available_changed.connect(self.on_dist_upgrade_changed)

        self.tabs.addTab(self.tab_updates, "Aktualizacje systemowe")
        self.tabs.addTab(self.tab_store, "Menedżer programów")
        self.tabs.addTab(self.tab_upgrade, "Aktualizacja PolonOS")

        self.tabs.setEnabled(False)

        self.grid_layout.addWidget(self.tabs, 0, 0)

        self.loading_card = QFrame()
        self.loading_card.setObjectName("loading_card")
        self.loading_card.setStyleSheet("""
            QFrame#loading_card {
                background-color: #1a1a1a;
                border: 2px solid #c22e45;
                border-radius: 12px;
                min-width: 460px;
                max-width: 520px;
                padding: 24px;
            }
        """)

        card_layout = QVBoxLayout(self.loading_card)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_logo = QLabel()
        card_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not logo_pm.isNull():
            card_logo.setPixmap(logo_pm.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        card_layout.addWidget(card_logo)

        lbl_loading_msg = QLabel("Czekaj, trwa ładowanie aplikacji...")
        font_msg = QFont()
        font_msg.setPointSize(15)
        font_msg.setBold(True)
        lbl_loading_msg.setFont(font_msg)
        lbl_loading_msg.setStyleSheet("color: #ffffff;")
        lbl_loading_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_loading_msg)

        lbl_loading_sub = QLabel("Inicjalizacja repozytoriów i przygotowywanie bazy pakietów PolonOS")
        lbl_loading_sub.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        lbl_loading_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_loading_sub)

        self.init_progress = QProgressBar()
        self.init_progress.setRange(0, 0)
        self.init_progress.setFixedHeight(8)
        self.init_progress.setTextVisible(False)
        self.init_progress.setStyleSheet("""
            QProgressBar {
                background-color: #111111;
                border: 1px solid #2d2d2d;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c22e45, stop:1 #e15265);
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.init_progress)

        self.grid_layout.addWidget(self.loading_card, 0, 0, Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(content_container, 1)

        bottom_bar = QFrame()
        bottom_bar.setObjectName("bottom_bar")
        bottom_bar.setStyleSheet("""
            QFrame#bottom_bar {
                background-color: #1a1a1a;
                border-top: 1px solid #2d2d2d;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 10, 20, 10)

        self.chk_autostart = QCheckBox("Uruchamiaj aplikację przy starcie systemu (demon aktualizacji w zasobniku)")
        self.chk_autostart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_autostart.setStyleSheet("color: #d4d4d8; font-size: 13px;")
        self.chk_autostart.setChecked(is_autostart_enabled())
        self.chk_autostart.toggled.connect(self.on_autostart_toggled)

        bottom_layout.addWidget(self.chk_autostart)
        bottom_layout.addStretch()

        main_layout.addWidget(bottom_bar)

    def init_tray_daemon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(get_tray_icon(has_updates=False))
        self.tray_icon.setToolTip("PolonOS Aplikacje — System aktualny")

        tray_menu = QMenu(self)
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                color: #f4f4f5;
                border: 1px solid #2d2d2d;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #c22e45;
                color: #ffffff;
            }
        """)

        act_open = QAction("Otwórz PolonOS Aplikacje", self)
        act_open.triggered.connect(self.restore_from_tray)
        tray_menu.addAction(act_open)

        act_check = QAction("Sprawdź aktualizacje teraz", self)
        act_check.triggered.connect(self.check_all_updates_now)
        tray_menu.addAction(act_check)

        tray_menu.addSeparator()

        act_quit = QAction("Zakończ całkowicie", self)
        act_quit.triggered.connect(self.quit_application)
        tray_menu.addAction(act_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.refresh_tray_state()
        self.tray_icon.show()

        self.update_timer = QTimer(self)
        self.update_timer.setInterval(60 * 1000)
        self.update_timer.timeout.connect(self.check_scheduled_updates)
        self.update_timer.start()

        if not self._start_in_tray or self.is_check_due():
            QTimer.singleShot(300, self.check_all_updates_now)

    def is_check_due(self) -> bool:
        if self._last_check_ts <= 0:
            return True
        return (time.time() - self._last_check_ts) >= CHECK_INTERVAL_SECONDS

    def check_scheduled_updates(self):
        if self.is_check_due():
            self.check_all_updates_now()

    def on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.MiddleClick
        ):
            self.restore_from_tray()

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if self.tab_updates.update_data is None or self.is_check_due():
            self.check_all_updates_now()
        if self._pkg_updates_count > 0:
            self.tabs.setCurrentIndex(0)
        elif self._dist_upgrade_available:
            self.tabs.setCurrentIndex(2)

    def check_all_updates_now(self):
        self._last_check_ts = time.time()
        save_update_state(self._last_check_ts, self._pkg_updates_count, self._dist_upgrade_available)
        self.tab_updates.load_updates()
        if self.dist_upgrader.is_polonos:
            self.tab_upgrade.check_upgrades()

    def on_pkg_updates_count_changed(self, count: int):
        self._pkg_updates_count = count
        self._last_check_ts = time.time()
        save_update_state(self._last_check_ts, self._pkg_updates_count, self._dist_upgrade_available)
        self.refresh_tray_state()

    def on_dist_upgrade_changed(self, available: bool):
        self._dist_upgrade_available = available
        self._last_check_ts = time.time()
        save_update_state(self._last_check_ts, self._pkg_updates_count, self._dist_upgrade_available)
        self.refresh_tray_state()

    def refresh_tray_state(self):
        has_updates = (self._pkg_updates_count > 0) or self._dist_upgrade_available
        self.tray_icon.setIcon(get_tray_icon(has_updates=has_updates))

        if self._pkg_updates_count > 0 and self._dist_upgrade_available:
            self.tray_icon.setToolTip(
                f"PolonOS Aplikacje — Dostępne aktualizacje ({self._pkg_updates_count} pakietów) oraz nowe wydanie PolonOS!"
            )
        elif self._pkg_updates_count > 0:
            self.tray_icon.setToolTip(
                f"PolonOS Aplikacje — Dostępne aktualizacje: {self._pkg_updates_count} pakietów"
            )
        elif self._dist_upgrade_available:
            self.tray_icon.setToolTip(
                "PolonOS Aplikacje — Dostępna nowa wersja systemu PolonOS!"
            )
        else:
            self.tray_icon.setToolTip("PolonOS Aplikacje — System jest aktualny")

    def on_autostart_toggled(self, checked: bool):
        set_autostart_enabled(checked)

    def closeEvent(self, event):
        if not self._force_quit and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def quit_application(self):
        self._force_quit = True
        self.tray_icon.hide()
        QApplication.quit()

    def start_background_loading(self):
        self.worker = AppInitWorker(self.apt_manager)
        self.worker.init_finished.connect(self.on_init_completed)
        self.worker.start()

    def on_init_completed(self):
        self.tab_store.load_catalog()
        self.loading_card.setVisible(False)
        self.tabs.setEnabled(True)

        if self._initial_deb_path and os.path.isfile(self._initial_deb_path):
            deb_path = self._initial_deb_path
            self._initial_deb_path = None
            QTimer.singleShot(100, lambda: self.open_deb_installer(deb_path))
            return

        if not self._start_in_tray:
            settings = load_app_settings()
            if not settings.get("first_run_completed", False):
                QTimer.singleShot(150, lambda: self.show_settings(is_first_run=True))

    def show_settings(self, is_first_run=False):
        dialog = SettingsDialog(
            self,
            is_first_run=bool(is_first_run),
            on_deb_open_requested=self.open_deb_installer
        )
        dialog.exec()

    def open_deb_installer(self, deb_path: str):
        if not deb_path or not os.path.isfile(deb_path):
            return
        dlg = DebPackageDialog(deb_path, apt_manager=self.apt_manager, parent=self)
        dlg.exec()
        self.tab_store.load_catalog()
        self.tab_updates.load_updates()

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()
