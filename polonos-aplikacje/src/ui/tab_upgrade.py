from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDialog, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QProcess
from PyQt6.QtGui import QFont, QDesktopServices

from ui.assets_helper import get_logo_pixmap

class UpgradeCheckWorker(QThread):
    data_loaded = pyqtSignal(dict)

    def __init__(self, dist_upgrader):
        super().__init__()
        self.dist_upgrader = dist_upgrader

    def run(self):
        self.data_loaded.emit(self.dist_upgrader.check_for_upgrades())

class DistUpgradeDialog(QDialog):
    def __init__(self, upgrade_data, dist_upgrader, parent=None):
        super().__init__(parent)
        self.upgrade_data = upgrade_data
        self.dist_upgrader = dist_upgrader
        self.process = None
        self.upgrade_succeeded = False
        self.setWindowTitle(f"Aktualizacja do {upgrade_data.get('release_name', 'PolonOS')}")
        self.setFixedSize(620, 440)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel(f"Aktualizacja systemu do {self.upgrade_data.get('release_name', 'nowej wersji')}")
        f = QFont()
        f.setPointSize(15)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #ffffff;")
        layout.addWidget(title)

        changelog = self.upgrade_data.get("changelog_pl", "")
        if changelog:
            desc = QLabel(changelog)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #d4d4d8; font-size: 13px;")
            layout.addWidget(desc)

        self.lbl_state = QLabel(
            "Przed kontynuowaniem upewnij się, że utworzyłeś migawkę w programie Timeshift. "
            "Kliknij przycisk poniżej, aby rozpocząć aktualizację."
        )
        self.lbl_state.setWordWrap(True)
        self.lbl_state.setStyleSheet("color: #fbbf24; font-size: 12px;")
        layout.addWidget(self.lbl_state)

        self.console = QPlainTextEdit()
        self.console.setObjectName("console_output")
        self.console.setReadOnly(True)
        layout.addWidget(self.console, 1)

        footer = QHBoxLayout()
        self.btn_close = QPushButton("Zamknij")
        self.btn_close.clicked.connect(self.accept)

        self.btn_run = QPushButton(f"Rozpocznij aktualizację ({self.upgrade_data.get('latest_version', '')})")
        self.btn_run.setObjectName("primary_btn")
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.clicked.connect(self.start_process)

        footer.addWidget(self.btn_close)
        footer.addStretch()
        footer.addWidget(self.btn_run)
        layout.addLayout(footer)

    def start_process(self):
        self.btn_run.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.lbl_state.setText("Trwa aktualizowanie systemu PolonOS. Nie wyłączaj komputera...")
        self.lbl_state.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")

        shell_cmd = self.dist_upgrader.build_upgrade_shell_command(self.upgrade_data)
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
        self.process.finished.connect(self.on_finished)
        self.process.start("pkexec", ["sh", "-c", shell_cmd])

    def on_finished(self, exit_code, _exit_status):
        self.btn_close.setEnabled(True)
        if exit_code == 0:
            self.upgrade_succeeded = True
            self.dist_upgrader.reload_os_info()
            self.lbl_state.setText("✓ Aktualizacja zakończona pomyślnie! Uruchom ponownie komputer.")
            self.lbl_state.setStyleSheet("color: #34d399; font-weight: bold; font-size: 13px;")
            self.btn_run.setVisible(False)
            self.btn_close.setObjectName("primary_btn")
            self.btn_close.style().unpolish(self.btn_close)
            self.btn_close.style().polish(self.btn_close)
        else:
            self.lbl_state.setText(f"Aktualizacja została przerwana lub wystąpił błąd (kod {exit_code}).")
            self.lbl_state.setStyleSheet("color: #f87171; font-weight: bold; font-size: 13px;")
            self.btn_run.setEnabled(True)

class TabUpgrade(QWidget):
    POLONOS_URL = "https://polonos.org"
    dist_upgrade_available_changed = pyqtSignal(bool)

    def __init__(self, dist_upgrader, parent=None, auto_check=True):
        super().__init__(parent)
        self.dist_upgrader = dist_upgrader
        self.worker = None
        self.latest_upgrade_data = None
        self.init_ui()
        if auto_check and self.dist_upgrader.is_polonos:
            self.check_upgrades()

    @staticmethod
    def _title(text, size=18):
        lbl = QLabel(text)
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        return lbl

    @staticmethod
    def _text(text, color="#a1a1aa", size=13):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-size: {size}px; background: transparent; border: none;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        return lbl

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 30, 40, 30)
        outer.addStretch(1)

        column = QWidget()
        column.setMaximumWidth(720)
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(18)

        if self.dist_upgrader.is_polonos:
            self._build_polonos_view(col)
        else:
            self._build_foreign_view(col)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(column, 1)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch(2)

    def _main_card(self):
        card = QFrame()
        card.setObjectName("upgrade_card")
        card.setStyleSheet("""
            QFrame#upgrade_card {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #232323, stop:1 #1b1b1b);
                border: 1px solid #2d2d2d;
                border-radius: 14px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(12)
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent; border: none;")
        pm = get_logo_pixmap(84, 84)
        if not pm.isNull():
            logo.setPixmap(pm)
        lay.addWidget(logo)
        return card, lay

    def _build_foreign_view(self, col):
        card, lay = self._main_card()
        card.setStyleSheet(card.styleSheet().replace("#2d2d2d", "#7f1d1d"))

        lay.addWidget(self._title(f"Używasz systemu {self.dist_upgrader.pretty_name}"))
        lay.addWidget(self._text(
            "Aktualizacja do systemu PolonOS jest niemożliwa.<br>"
            "Ten moduł działa wyłącznie w systemie PolonOS.",
            color="#fca5a5", size=14))
        lay.addWidget(self._text(
            f'Zainstaluj system PolonOS — zobacz: '
            f'<a href="{self.POLONOS_URL}" style="color:#e15265; font-weight:bold;">polonos.org</a>',
            color="#d4d4d8", size=14))
        lay.itemAt(lay.count() - 1).widget().setOpenExternalLinks(True)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn = QPushButton("Przejdź do polonos.org")
        btn.setObjectName("primary_btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.POLONOS_URL)))
        btn_row.addWidget(btn)
        btn_row.addStretch()
        lay.addSpacing(6)
        lay.addLayout(btn_row)
        col.addWidget(card)

    def _build_polonos_view(self, col):
        card, lay = self._main_card()

        lay.addWidget(self._text("Zainstalowana wersja", size=12))
        self.lbl_installed_ver = self._title(self.dist_upgrader.pretty_name, size=22)
        lay.addWidget(self.lbl_installed_ver)

        self.lbl_status = self._text("Sprawdzanie dostępności nowej wersji PolonOS...", size=14)
        lay.addWidget(self.lbl_status)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()
        self.btn_check = QPushButton("Sprawdź ponownie")
        self.btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_check.clicked.connect(self.check_upgrades)
        self.btn_upgrade = QPushButton("Aktualizuj system")
        self.btn_upgrade.setObjectName("primary_btn")
        self.btn_upgrade.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upgrade.setEnabled(False)
        self.btn_upgrade.clicked.connect(self.start_dist_upgrade)
        btn_row.addWidget(self.btn_check)
        btn_row.addWidget(self.btn_upgrade)
        btn_row.addStretch()
        lay.addSpacing(6)
        lay.addLayout(btn_row)
        col.addWidget(card)

        ts = QFrame()
        ts.setObjectName("warning_box")
        ts_lay = QHBoxLayout(ts)
        ts_lay.setContentsMargins(18, 14, 18, 14)
        ts_lay.setSpacing(16)
        txt = QVBoxLayout()
        txt.setSpacing(4)
        t1 = QLabel("Zalecane: utwórz migawkę systemu w Timeshift")
        t1.setObjectName("warning_title")
        t2 = QLabel("Przed aktualizacją systemu zaleca się utworzenie migawki systemowej. "
                    "W razie problemów pozwoli ona przywrócić system do stanu sprzed aktualizacji.")
        t2.setObjectName("warning_desc")
        t2.setWordWrap(True)
        txt.addWidget(t1)
        txt.addWidget(t2)
        ts_lay.addLayout(txt, 1)
        btn_ts = QPushButton("Otwórz Timeshift")
        btn_ts.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ts.clicked.connect(self.dist_upgrader.launch_timeshift_backup)
        ts_lay.addWidget(btn_ts, alignment=Qt.AlignmentFlag.AlignVCenter)
        col.addWidget(ts)

    def check_upgrades(self):
        self.lbl_status.setText("Sprawdzanie dostępności nowej wersji PolonOS...")
        self.lbl_status.setStyleSheet("color: #a1a1aa; font-size: 14px; background: transparent; border: none;")
        self.btn_check.setEnabled(False)
        self.worker = UpgradeCheckWorker(self.dist_upgrader)
        self.worker.data_loaded.connect(self.on_check_completed)
        self.worker.start()

    def on_check_completed(self, data):
        self.latest_upgrade_data = data
        self.btn_check.setEnabled(True)
        has_upg = bool(data.get('upgrade_available'))
        self.dist_upgrade_available_changed.emit(has_upg)
        if has_upg:
            self.lbl_status.setText(f"Dostępna jest nowa wersja: {data['release_name']}")
            self.lbl_status.setStyleSheet("color: #34d399; font-size: 15px; font-weight: bold; background: transparent; border: none;")
            self.btn_upgrade.setEnabled(True)
            self.btn_upgrade.setText(f"Aktualizuj do {data['release_name']}")
        else:
            self.lbl_status.setText("✓ Posiadasz najnowszą wersję PolonOS")
            self.lbl_status.setStyleSheet("color: #34d399; font-size: 14px; background: transparent; border: none;")
            self.btn_upgrade.setEnabled(False)
            self.btn_upgrade.setText("Aktualizuj system")

    def start_dist_upgrade(self):
        if not self.latest_upgrade_data or not self.latest_upgrade_data.get('upgrade_available'):
            return
        dlg = DistUpgradeDialog(self.latest_upgrade_data, self.dist_upgrader, self)
        dlg.exec()
        if dlg.upgrade_succeeded:
            self.lbl_installed_ver.setText(self.dist_upgrader.pretty_name)
            self.check_upgrades()
