from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QPlainTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QFont

class UpdateWorker(QThread):
    data_loaded = pyqtSignal(dict)

    def __init__(self, apt_manager):
        super().__init__()
        self.apt_manager = apt_manager

    def run(self):
        result = self.apt_manager.get_upgradable_packages()
        self.data_loaded.emit(result)

class TabUpdates(QWidget):
    updates_count_changed = pyqtSignal(int)

    def __init__(self, apt_manager, parent=None, auto_load=True):
        super().__init__(parent)
        self.apt_manager = apt_manager
        self.update_data = None
        self.process = None
        self.init_ui()
        if auto_load:
            self.load_updates()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.box_count = QFrame()
        self.box_count.setObjectName("stat_box")
        b1_layout = QVBoxLayout(self.box_count)
        lbl_c_title = QLabel("Pakiety do aktualizacji")
        lbl_c_title.setObjectName("stat_title")
        self.lbl_c_val = QLabel("Sprawdzanie...")
        self.lbl_c_val.setObjectName("stat_value")
        b1_layout.addWidget(lbl_c_title)
        b1_layout.addWidget(self.lbl_c_val)

        self.box_size = QFrame()
        self.box_size.setObjectName("stat_box")
        b2_layout = QVBoxLayout(self.box_size)
        lbl_s_title = QLabel("Rozmiar do pobrania")
        lbl_s_title.setObjectName("stat_title")
        self.lbl_s_val = QLabel("Sprawdzanie...")
        self.lbl_s_val.setObjectName("stat_value")
        b2_layout.addWidget(lbl_s_title)
        b2_layout.addWidget(self.lbl_s_val)

        self.box_status = QFrame()
        self.box_status.setObjectName("stat_box")
        b3_layout = QVBoxLayout(self.box_status)
        lbl_st_title = QLabel("Status systemu")
        lbl_st_title.setObjectName("stat_title")
        self.lbl_st_val = QLabel("Analiza repozytoriów")
        self.lbl_st_val.setObjectName("stat_value")
        self.lbl_st_val.setStyleSheet("color: #fbbf24; font-size: 16px;")
        b3_layout.addWidget(lbl_st_title)
        b3_layout.addWidget(self.lbl_st_val)

        stats_layout.addWidget(self.box_count)
        stats_layout.addWidget(self.box_size)
        stats_layout.addWidget(self.box_status)

        main_layout.addLayout(stats_layout)

        action_bar = QHBoxLayout()

        self.btn_update = QPushButton("Aktualizuj system")
        self.btn_update.setObjectName("primary_btn")
        font_btn = QFont()
        font_btn.setPointSize(12)
        font_btn.setBold(True)
        self.btn_update.setFont(font_btn)
        self.btn_update.clicked.connect(self.start_system_update)
        self.btn_update.setEnabled(False)

        self.btn_toggle_details = QPushButton("Ukryj szczegóły pakietów")
        self.btn_toggle_details.clicked.connect(self.toggle_details)

        self.btn_refresh = QPushButton("Odśwież listę")
        self.btn_refresh.clicked.connect(self.load_updates)

        action_bar.addWidget(self.btn_update)
        action_bar.addWidget(self.btn_toggle_details)
        action_bar.addStretch()
        action_bar.addWidget(self.btn_refresh)

        main_layout.addLayout(action_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nazwa pakietu", "Obecna wersja", "Nowa wersja", "Rozmiar pobierania"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.splitter.addWidget(self.table)

        self.console = QPlainTextEdit()
        self.console.setObjectName("console_output")
        self.console.setReadOnly(True)
        self.console.appendPlainText("[PolonOS] Oczekiwanie na wybór akcji...")
        self.console.setVisible(False)
        self.splitter.addWidget(self.console)

        main_layout.addWidget(self.splitter)

    def load_updates(self):
        self.lbl_c_val.setText("Sprawdzanie...")
        self.lbl_s_val.setText("Sprawdzanie...")
        self.lbl_st_val.setText("Szukanie zmian")
        self.lbl_st_val.setStyleSheet("color: #fbbf24; font-size: 16px;")
        self.btn_update.setEnabled(False)

        self.worker = UpdateWorker(self.apt_manager)
        self.worker.data_loaded.connect(self.on_updates_loaded)
        self.worker.start()

    def on_updates_loaded(self, data):
        self.update_data = data
        count = data['count']
        size_fmt = data['total_size_formatted']

        self.lbl_c_val.setText(f"{count} pakietów")
        self.lbl_s_val.setText(size_fmt)
        self.updates_count_changed.emit(count)

        if count == 0:
            self.lbl_st_val.setText("System aktualny ✓")
            self.lbl_st_val.setStyleSheet("color: #34d399; font-size: 16px;")
            self.btn_update.setEnabled(False)
            self.btn_update.setText("✓ System jest aktualny")
        else:
            self.lbl_st_val.setText("Dostępne aktualizacje")
            self.lbl_st_val.setStyleSheet("color: #f87171; font-size: 16px;")
            self.btn_update.setEnabled(True)
            self.btn_update.setText(f"Aktualizuj system ({count} pakietów - {size_fmt})")

        self.table.setRowCount(0)
        for pkg in data['packages']:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(pkg['name']))
            self.table.setItem(row, 1, QTableWidgetItem(pkg['current_ver']))
            self.table.setItem(row, 2, QTableWidgetItem(pkg['new_ver']))
            self.table.setItem(row, 3, QTableWidgetItem(pkg['size_formatted']))

    def toggle_details(self):
        is_vis = self.table.isVisible()
        self.table.setVisible(not is_vis)
        self.btn_toggle_details.setText("Ukryj szczegóły pakietów" if not is_vis else "Pokaż szczegóły pakietów")

    def start_system_update(self):
        self.btn_update.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.console.setVisible(True)
        self.console.appendPlainText(
            "\n[PolonOS] Uruchamianie pełnej aktualizacji pakietów systemowych (APT) oraz aplikacji (Flatpak)..."
        )

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_update_finished)

        update_script = (
            "export DEBIAN_FRONTEND=noninteractive; "
            "echo '[PolonOS] 1/2: Aktualizacja pakietów systemowych APT...'; "
            "apt-get update && apt-get dist-upgrade -y "
            "-o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'; "
            "if command -v flatpak >/dev/null 2>&1; then "
            "  echo '[PolonOS] 2/2: Aktualizacja aplikacji i środowisk Flatpak...'; "
            "  flatpak update -y --noninteractive || true; "
            "fi"
        )
        self.process.start("pkexec", ["sh", "-c", update_script])

    def on_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.console.appendPlainText(data.strip())

    def on_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.console.appendPlainText(data.strip())

    def on_update_finished(self, exit_code, exit_status):
        import shutil
        import subprocess
        if exit_code == 0 and shutil.which("flatpak"):
            try:
                res_user = subprocess.run(
                    ["flatpak", "update", "--user", "-y", "--noninteractive"],
                    capture_output=True, text=True, timeout=120
                )
                if res_user.stdout and res_user.stdout.strip():
                    self.console.appendPlainText(res_user.stdout.strip())
            except Exception:
                pass

        self.progress_bar.setVisible(False)
        self.btn_refresh.setEnabled(True)
        if exit_code == 0:
            self.console.appendPlainText("\n[PolonOS] ✓ Aktualizacja wszystkich pakietów i aplikacji zakończona pomyślnie!")
            self.lbl_st_val.setText("System aktualny ✓")
            self.lbl_st_val.setStyleSheet("color: #34d399; font-size: 16px;")
        else:
            self.console.appendPlainText(f"\n[PolonOS] Błąd podczas aktualizacji (kod wyjścia {exit_code}).")

        self.load_updates()
