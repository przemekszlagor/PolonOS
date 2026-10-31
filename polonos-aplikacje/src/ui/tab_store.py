import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QPlainTextEdit, QButtonGroup, QCheckBox, QSplitter
)
from PyQt6.QtCore import Qt, QProcess, QSize
from PyQt6.QtGui import QFont, QIcon, QColor
from ui.assets_helper import get_logo_pixmap

class AppDetailDialog(QDialog):
    def __init__(self, app_data, apt_manager, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.apt_manager = apt_manager
        self.process = None
        self.setWindowTitle(f"Program: {app_data['name']}")
        self.setFixedSize(620, 440)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        lbl_icon = QLabel()
        icon = QIcon.fromTheme(self.app_data.get('icon', 'package-x-generic'))
        if not icon.isNull():
            lbl_icon.setPixmap(icon.pixmap(56, 56))
        else:
            lbl_icon.setPixmap(get_logo_pixmap(48, 48))

        header_layout.addWidget(lbl_icon)

        title_box = QVBoxLayout()
        lbl_name = QLabel(self.app_data['name'])
        font_t = QFont()
        font_t.setPointSize(16)
        font_t.setBold(True)
        lbl_name.setFont(font_t)
        lbl_name.setStyleSheet("color: #ffffff;")

        lbl_pkg = QLabel(f"Pakiet: {self.app_data['package']}  |  Kategoria: {self.app_data.get('category', 'System')}  |  Licencja: {self.app_data.get('license', 'Open Source')}")
        lbl_pkg.setStyleSheet("color: #a1a1aa; font-size: 12px;")

        is_inst = self.apt_manager.is_package_installed(self.app_data['package'])
        inst_type = self.apt_manager.get_install_type(self.app_data['package']) if self.apt_manager else None
        if is_inst:
            type_badge = " (Flatpak)" if inst_type == "flatpak" else ""
            self.lbl_status = QLabel(f"✓ Zainstalowano w systemie{type_badge}")
            self.lbl_status.setStyleSheet("color: #34d399; font-weight: bold;")
        else:
            self.lbl_status = QLabel("• Dostępny do instalacji")
            self.lbl_status.setStyleSheet("color: #fbbf24;")

        title_box.addWidget(lbl_name)
        title_box.addWidget(lbl_pkg)
        title_box.addWidget(self.lbl_status)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        desc_box = QFrame()
        desc_box.setObjectName("card_frame")
        d_layout = QVBoxLayout(desc_box)
        d_layout.setContentsMargins(16, 14, 16, 14)

        lbl_desc_t = QLabel("Opis programu:")
        lbl_desc_t.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px;")

        lbl_desc = QLabel(self.app_data.get('description', self.app_data.get('short_desc', 'Brak szczegółowego opisu.')))
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #d4d4d8; font-size: 13px; line-height: 1.5;")

        d_layout.addWidget(lbl_desc_t)
        d_layout.addWidget(lbl_desc)
        d_layout.addStretch()

        layout.addWidget(desc_box, 1)

        self.console = QPlainTextEdit()
        self.console.setObjectName("console_output")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(85)
        self.console.setVisible(False)
        layout.addWidget(self.console)

        self.footer = QHBoxLayout()
        self.btn_close = QPushButton("Zamknij")
        self.btn_close.clicked.connect(self.accept)

        if is_inst:
            self.btn_action = QPushButton("Odinstaluj program")
            self.btn_action.setObjectName("danger_btn")
            self.btn_action.clicked.connect(self.uninstall_app)
        else:
            self.btn_action = QPushButton("Zainstaluj program")
            self.btn_action.setObjectName("primary_btn")
            self.btn_action.clicked.connect(self.install_app)

        self.footer.addWidget(self.btn_close)
        self.footer.addStretch()
        self.footer.addWidget(self.btn_action)

        layout.addLayout(self.footer)

    def install_app(self):
        pkg = self.app_data['package']
        shell_cmd = (
            "export DEBIAN_FRONTEND=noninteractive; "
            f"apt-get install -y {pkg} || (apt-get update -q && apt-get install -y {pkg})"
        )
        self.run_apt_cmd(["sh", "-c", shell_cmd], "Instalowanie")

    def uninstall_app(self):
        pkg = self.app_data['package']
        inst_type = self.apt_manager.get_install_type(pkg) if self.apt_manager else None
        if inst_type == "flatpak":
            fp_id = self.apt_manager.get_installed_flatpak_id(pkg)
            import subprocess
            subprocess.run(["flatpak", "uninstall", "--user", "-y", "--noninteractive", fp_id], capture_output=True)
            self.run_apt_cmd(
                ["sh", "-c", f"flatpak uninstall --system -y --noninteractive {fp_id} || flatpak uninstall -y --noninteractive {fp_id} || true"],
                "Usuwanie pakietu Flatpak"
            )
        else:
            rem_pkgs = self.apt_manager.get_removable_apt_packages(pkg) if self.apt_manager else [pkg]
            pkgs_str = " ".join(rem_pkgs)
            self.run_apt_cmd(
                ["sh", "-c", f"export DEBIAN_FRONTEND=noninteractive; apt-get remove -y {pkgs_str}"],
                "Usuwanie"
            )

    def run_apt_cmd(self, apt_args, action_name):
        self.btn_action.setEnabled(False)
        self.console.setVisible(True)
        self.console.appendPlainText(f"[PolonOS] {action_name} pakietu {self.app_data['package']}...")

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(
            lambda: self.console.appendPlainText(self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore').strip())
        )
        self.process.readyReadStandardError.connect(
            lambda: self.console.appendPlainText(self.process.readAllStandardError().data().decode('utf-8', errors='ignore').strip())
        )
        self.process.finished.connect(self.on_process_finished)

        cmd = "pkexec"
        args = apt_args
        self.process.start(cmd, args)

    def on_process_finished(self, exit_code, exit_status):
        if exit_code == 0:
            self.console.appendPlainText("\n[PolonOS] ✓ Operacja zakończona sukcesem!")
            self.apt_manager.refresh_installed_cache()
            is_inst = self.apt_manager.is_package_installed(self.app_data['package'])
            self.lbl_status.setText("✓ Zainstalowano pomyślnie" if is_inst else "• Odinstalowano pomyślnie")
            self.lbl_status.setStyleSheet("color: #34d399; font-weight: bold;" if is_inst else "color: #a1a1aa; font-weight: bold;")

            self.btn_action.setVisible(False)
            self.btn_close.setObjectName("primary_btn")
            self.btn_close.style().unpolish(self.btn_close)
            self.btn_close.style().polish(self.btn_close)
        else:
            self.console.appendPlainText(f"\n[PolonOS] Wystąpił błąd (kod {exit_code}).")
            self.btn_action.setEnabled(True)

class BatchOperationDialog(QDialog):
    def __init__(self, apps, action="install", apt_manager=None, parent=None):
        super().__init__(parent)
        self.apps = apps
        self.action = action
        self.apt_manager = apt_manager
        self.process = None
        action_title = "Zbiorcza instalacja programów" if action == "install" else "Zbiorcze odinstalowywanie programów"
        self.setWindowTitle(action_title)
        self.setFixedSize(620, 480)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        lbl_title = QLabel(f"Wybrane programy do {'zainstalowania' if self.action == 'install' else 'odinstalowania'} ({len(self.apps)}):")
        font_t = QFont()
        font_t.setPointSize(14)
        font_t.setBold(True)
        lbl_title.setFont(font_t)
        lbl_title.setStyleSheet("color: #ffffff;")
        layout.addWidget(lbl_title)

        pkg_frame = QFrame()
        pkg_frame.setObjectName("card_frame")
        pf_layout = QVBoxLayout(pkg_frame)
        pf_layout.setContentsMargins(12, 10, 12, 10)

        pkg_names = [f"• {app['name']} ({app['package']})" for app in self.apps]
        lbl_pkgs = QLabel("\n".join(pkg_names[:10]) + (f"\n... oraz {len(pkg_names)-10} innych" if len(pkg_names) > 10 else ""))
        lbl_pkgs.setStyleSheet("color: #d4d4d8; font-size: 13px; line-height: 1.4;")
        pf_layout.addWidget(lbl_pkgs)
        layout.addWidget(pkg_frame)

        self.lbl_status = QLabel("Kliknij przycisk poniżej, aby rozpocząć operację.")
        self.lbl_status.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        self.console = QPlainTextEdit()
        self.console.setObjectName("console_output")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(130)
        self.console.setVisible(False)
        layout.addWidget(self.console)

        self.footer = QHBoxLayout()
        self.btn_close = QPushButton("Zamknij")
        self.btn_close.clicked.connect(self.accept)

        if self.action == "install":
            self.btn_action = QPushButton(f"Rozpocznij instalację ({len(self.apps)})")
            self.btn_action.setObjectName("primary_btn")
        else:
            self.btn_action = QPushButton(f"Rozpocznij usuwanie ({len(self.apps)})")
            self.btn_action.setObjectName("danger_btn")

        self.btn_action.clicked.connect(self.run_batch)

        self.footer.addWidget(self.btn_close)
        self.footer.addStretch()
        self.footer.addWidget(self.btn_action)

        layout.addLayout(self.footer)

    def run_batch(self):
        self.btn_action.setEnabled(False)
        self.console.setVisible(True)
        self.lbl_status.setText("Trwa wykonywanie operacji w systemie...")
        self.lbl_status.setStyleSheet("color: #fbbf24; font-weight: bold;")

        packages = [app['package'] for app in self.apps]
        self.console.appendPlainText(f"[PolonOS] Uruchamianie procedury dla {len(packages)} pakietów...")

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(
            lambda: self.console.appendPlainText(self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore').strip())
        )
        self.process.readyReadStandardError.connect(
            lambda: self.console.appendPlainText(self.process.readAllStandardError().data().decode('utf-8', errors='ignore').strip())
        )
        self.process.finished.connect(self.on_process_finished)

        cmd = "pkexec"
        if self.action == "install":
            pkgs_str = " ".join(packages)
            shell_cmd = (
                "export DEBIAN_FRONTEND=noninteractive; "
                f"apt-get install -y {pkgs_str} || (apt-get update -q && apt-get install -y {pkgs_str})"
            )
            args = ["sh", "-c", shell_cmd]
        else:
            apt_pkgs = []
            fp_pkgs = []
            for app in self.apps:
                fp_id = self.apt_manager.get_installed_flatpak_id(app['package']) if self.apt_manager else None
                if fp_id:
                    fp_pkgs.append(fp_id)
                else:
                    rem = self.apt_manager.get_removable_apt_packages(app['package']) if self.apt_manager else [app['package']]
                    apt_pkgs.extend(rem)

            if fp_pkgs:
                import subprocess
                subprocess.run(["flatpak", "uninstall", "--user", "-y", "--noninteractive"] + fp_pkgs, capture_output=True)

            subcmds = ["export DEBIAN_FRONTEND=noninteractive"]
            if apt_pkgs:
                subcmds.append(f"apt-get remove -y {' '.join(apt_pkgs)}")
            if fp_pkgs:
                subcmds.append(f"(flatpak uninstall --system -y --noninteractive {' '.join(fp_pkgs)} || flatpak uninstall -y --noninteractive {' '.join(fp_pkgs)} || true)")

            args = ["sh", "-c", " && ".join(subcmds) if len(subcmds) > 1 else "true"]

        self.process.start(cmd, args)

    def on_process_finished(self, exit_code, exit_status):
        if exit_code == 0:
            self.console.appendPlainText(f"\n[PolonOS] ✓ Operacja dla {len(self.apps)} programów zakończona pomyślnie!")
            self.apt_manager.refresh_installed_cache()
            self.lbl_status.setText("✓ Wszystkie wybrane programy zostały pomyślnie przetworzone!")
            self.lbl_status.setStyleSheet("color: #34d399; font-weight: bold;")

            self.btn_action.setVisible(False)
            self.btn_close.setObjectName("primary_btn")
            self.btn_close.style().unpolish(self.btn_close)
            self.btn_close.style().polish(self.btn_close)
        else:
            self.console.appendPlainText(f"\n[PolonOS] Wystąpił błąd podczas operacji (kod {exit_code}).")
            self.lbl_status.setText("Wystąpił błąd podczas instalacji/usuwania.")
            self.lbl_status.setStyleSheet("color: #f87171; font-weight: bold;")
            self.btn_action.setEnabled(True)

class TabStore(QWidget):
    CATEGORIES = [
        "Wszystkie", "Biuro", "Internet", "Grafika",
        "Multimedia", "Narzędzia", "Edukacja", "Gry", "Programowanie"
    ]

    def __init__(self, apt_manager, parent=None):
        super().__init__(parent)
        self.apt_manager = apt_manager
        self.catalog = []
        self.current_items = []
        self.selected_category = "Wszystkie"
        self.checked_packages = set()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj programu lub pakietu APT (np. vlc, gimp, htop, libreoffice)...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.search_edit.returnPressed.connect(self.filter_apps)

        self.chk_all_apt = QCheckBox("Przeszukuj wszystkie pakiety repozytorium APT")
        self.chk_all_apt.setStyleSheet("color: #d4d4d8; font-size: 12px;")
        self.chk_all_apt.setChecked(True)
        self.chk_all_apt.toggled.connect(self.filter_apps)

        btn_reload = QPushButton("Odśwież listę")
        btn_reload.clicked.connect(self.load_catalog)

        top_bar.addWidget(self.search_edit, 3)
        top_bar.addWidget(self.chk_all_apt)
        top_bar.addWidget(btn_reload)

        main_layout.addLayout(top_bar)

        pills_layout = QHBoxLayout()
        pills_layout.setSpacing(6)
        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)

        for i, cat in enumerate(self.CATEGORIES):
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setProperty("class", "category_pill")
            if cat == "Wszystkie":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, c=cat: self.on_category_changed(c))
            self.category_group.addButton(btn, i)
            pills_layout.addWidget(btn)

        pills_layout.addStretch()

        self.lbl_count = QLabel("Programów: 0")
        self.lbl_count.setStyleSheet("color: #71717a; font-size: 12px; font-weight: bold;")
        pills_layout.addWidget(self.lbl_count)

        main_layout.addLayout(pills_layout)

        batch_bar = QFrame()
        batch_bar.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 6px;
                padding: 6px 12px;
            }
        """)
        bb_layout = QHBoxLayout(batch_bar)
        bb_layout.setContentsMargins(10, 4, 10, 4)
        bb_layout.setSpacing(12)

        self.chk_select_all = QCheckBox("Zaznacz widoczne")
        self.chk_select_all.setStyleSheet("color: #ffffff; font-weight: 500; font-size: 12px;")
        self.chk_select_all.clicked.connect(self.toggle_select_all)

        self.lbl_selected_count = QLabel("Zaznaczono: 0")
        self.lbl_selected_count.setStyleSheet("color: #c22e45; font-weight: bold; font-size: 12px;")

        self.btn_batch_install = QPushButton("Zainstaluj zaznaczone")
        self.btn_batch_install.setObjectName("primary_btn")
        self.btn_batch_install.setEnabled(False)
        self.btn_batch_install.clicked.connect(self.batch_install_checked)

        self.btn_batch_uninstall = QPushButton("Odinstaluj zaznaczone")
        self.btn_batch_uninstall.setObjectName("danger_btn")
        self.btn_batch_uninstall.setEnabled(False)
        self.btn_batch_uninstall.clicked.connect(self.batch_uninstall_checked)

        self.btn_clear_sel = QPushButton("Odznacz wszystko")
        self.btn_clear_sel.clicked.connect(self.clear_selection)
        self.btn_clear_sel.setEnabled(False)

        bb_layout.addWidget(self.chk_select_all)
        bb_layout.addWidget(self.lbl_selected_count)
        bb_layout.addStretch()
        bb_layout.addWidget(self.btn_clear_sel)
        bb_layout.addWidget(self.btn_batch_install)
        bb_layout.addWidget(self.btn_batch_uninstall)

        main_layout.addWidget(batch_bar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "Stan", "Program / Pakiet", "Kategoria", "Krótki opis", "Akcja"])

        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 48)

        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 130)

        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(2, 230)

        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 110)

        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 125)

        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.setStyleSheet("QTableWidget::item { padding: 0px 6px; }")
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.table.cellDoubleClicked.connect(lambda r, c: self.on_row_double_clicked(r))

        splitter.addWidget(self.table)

        self.inspector_frame = QFrame()
        self.inspector_frame.setObjectName("card_frame")
        self.inspector_frame.setStyleSheet("""
            QFrame#card_frame {
                background-color: #1e1e1e;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        insp_layout = QHBoxLayout(self.inspector_frame)
        insp_layout.setContentsMargins(14, 8, 14, 8)
        insp_layout.setSpacing(16)

        self.insp_icon = QLabel()
        self.insp_icon.setFixedSize(44, 44)
        self.insp_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        insp_layout.addWidget(self.insp_icon)

        insp_info = QVBoxLayout()
        insp_info.setSpacing(2)

        self.insp_title = QLabel("Wybierz program z listy")
        font_it = QFont()
        font_it.setPointSize(13)
        font_it.setBold(True)
        self.insp_title.setFont(font_it)
        self.insp_title.setStyleSheet("color: #ffffff;")

        self.insp_meta = QLabel("Zaznacz checkboxy, aby zainstalować wiele programów naraz, lub kliknij podwójnie wiersz.")
        self.insp_meta.setStyleSheet("color: #a1a1aa; font-size: 11px;")

        self.insp_desc = QLabel("")
        self.insp_desc.setStyleSheet("color: #d4d4d8; font-size: 12px;")
        self.insp_desc.setWordWrap(True)

        insp_info.addWidget(self.insp_title)
        insp_info.addWidget(self.insp_meta)
        insp_info.addWidget(self.insp_desc)

        insp_layout.addLayout(insp_info, 1)

        self.btn_insp_action = QPushButton("Szczegóły programu")
        self.btn_insp_action.setObjectName("primary_btn")
        self.btn_insp_action.clicked.connect(self.open_selected_details)
        self.btn_insp_action.setEnabled(False)

        insp_layout.addWidget(self.btn_insp_action, alignment=Qt.AlignmentFlag.AlignVCenter)

        splitter.addWidget(self.inspector_frame)
        splitter.setSizes([450, 110])

        main_layout.addWidget(splitter)

    def load_catalog(self):
        self.catalog = self.apt_manager.get_featured_catalog()
        self.filter_apps()

    def on_category_changed(self, category):
        self.selected_category = category
        self.filter_apps()

    def on_search_changed(self, text):
        if len(text.strip()) == 0 or len(text.strip()) >= 2:
            self.filter_apps()

    def filter_apps(self):
        query = self.search_edit.text().strip().lower()
        search_all_apt = self.chk_all_apt.isChecked()

        filtered = []

        for app in self.catalog:
            match_cat = (self.selected_category == "Wszystkie") or (app.get('category', '').lower() == self.selected_category.lower())
            match_query = not query or (
                query in app['name'].lower() or
                query in app.get('description', '').lower() or
                query in app['package'].lower() or
                query in app.get('short_desc', '').lower()
            )
            if match_cat and match_query:
                filtered.append(app)

        if search_all_apt and query and len(query) >= 2:
            apt_results = self.apt_manager.search_apt_packages(query, limit=100)
            existing_pkgs = {a['package'] for a in filtered}
            for res in apt_results:
                if res['package'] not in existing_pkgs:
                    if self.selected_category == "Wszystkie" or res.get('category', '').lower() == self.selected_category.lower():
                        filtered.append(res)

        self.current_items = filtered
        self.populate_table(filtered)

    def populate_table(self, items):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.lbl_count.setText(f"Programów w liście: {len(items)}")

        for row_idx, app in enumerate(items):
            self.table.insertRow(row_idx)

            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            cb = QCheckBox()
            cb.setChecked(app['package'] in self.checked_packages)
            cb.toggled.connect(lambda checked, p=app['package']: self.on_pkg_checkbox_toggled(p, checked))
            cb_layout.addWidget(cb)
            self.table.setCellWidget(row_idx, 0, cb_widget)

            is_inst = self.apt_manager.is_package_installed(app['package'])
            status_text = "✓ Zainstalowany" if is_inst else "• Dostępny"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("#34d399") if is_inst else QColor("#a1a1aa"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, status_item)

            name_text = f"{app['name']}  ({app['package']})"
            name_item = QTableWidgetItem(name_text)
            icon = QIcon.fromTheme(app.get('icon', 'package-x-generic'))
            if not icon.isNull():
                name_item.setIcon(icon)
            self.table.setItem(row_idx, 2, name_item)

            cat_item = QTableWidgetItem(app.get('category', 'System'))
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, cat_item)

            desc_text = app.get('short_desc', app.get('description', ''))
            desc_item = QTableWidgetItem(desc_text)
            self.table.setItem(row_idx, 4, desc_item)

            btn_details = QPushButton("Szczegóły")
            btn_details.setFixedSize(90, 28)
            btn_details.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_details.setStyleSheet(
                "QPushButton { background-color: #27272a; color: #f4f4f5; border: 1px solid #3f3f46;"
                " border-radius: 5px; padding: 0px 6px; font-size: 12px; min-height: 26px; max-height: 26px; }"
                "QPushButton:hover { background-color: #3f3f46; border-color: #c22e45; color: #ffffff; }"
            )
            btn_details.clicked.connect(lambda _, a=app: self.open_app_details(a))

            cell_widget = QWidget()
            cell_widget.setStyleSheet("background: transparent;")
            cw_layout = QHBoxLayout(cell_widget)
            cw_layout.setContentsMargins(0, 0, 0, 0)
            cw_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cw_layout.addWidget(btn_details, 0, Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row_idx, 5, cell_widget)

        self.table.blockSignals(False)
        self.update_batch_buttons()

        if items:
            self.table.selectRow(0)

    def on_pkg_checkbox_toggled(self, package, is_checked):
        if is_checked:
            self.checked_packages.add(package)
        else:
            self.checked_packages.discard(package)
        self.update_batch_buttons()

    def update_batch_buttons(self):
        count = len(self.checked_packages)
        self.lbl_selected_count.setText(f"Zaznaczono: {count}")
        self.btn_clear_sel.setEnabled(count > 0)

        uninstalled_count = sum(1 for pkg in self.checked_packages if not self.apt_manager.is_package_installed(pkg))
        installed_count = sum(1 for pkg in self.checked_packages if self.apt_manager.is_package_installed(pkg))

        self.btn_batch_install.setEnabled(uninstalled_count > 0)
        self.btn_batch_install.setText(f"Zainstaluj zaznaczone ({uninstalled_count})" if uninstalled_count > 0 else "Zainstaluj zaznaczone")

        self.btn_batch_uninstall.setEnabled(installed_count > 0)
        self.btn_batch_uninstall.setText(f"Odinstaluj zaznaczone ({installed_count})" if installed_count > 0 else "Odinstaluj zaznaczone")

    def toggle_select_all(self):
        is_checked = self.chk_select_all.isChecked()
        for row in range(self.table.rowCount()):
            cw = self.table.cellWidget(row, 0)
            if cw:
                cb = cw.findChild(QCheckBox)
                if cb:
                    cb.blockSignals(True)
                    cb.setChecked(is_checked)
                    cb.blockSignals(False)
            if row < len(self.current_items):
                pkg = self.current_items[row]['package']
                if is_checked:
                    self.checked_packages.add(pkg)
                else:
                    self.checked_packages.discard(pkg)
        self.update_batch_buttons()

    def clear_selection(self):
        self.checked_packages.clear()
        self.chk_select_all.setChecked(False)
        for row in range(self.table.rowCount()):
            cw = self.table.cellWidget(row, 0)
            if cw:
                cb = cw.findChild(QCheckBox)
                if cb:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        self.update_batch_buttons()

    def batch_install_checked(self):
        all_apps = {a['package']: a for a in (self.catalog + self.current_items)}
        to_install = []
        for pkg in self.checked_packages:
            if not self.apt_manager.is_package_installed(pkg):
                app_info = all_apps.get(pkg, {'package': pkg, 'name': pkg, 'category': 'System'})
                to_install.append(app_info)

        if to_install:
            dlg = BatchOperationDialog(to_install, action="install", apt_manager=self.apt_manager, parent=self)
            dlg.exec()
            self.checked_packages.clear()
            self.load_catalog()

    def batch_uninstall_checked(self):
        all_apps = {a['package']: a for a in (self.catalog + self.current_items)}
        to_remove = []
        for pkg in self.checked_packages:
            if self.apt_manager.is_package_installed(pkg):
                app_info = all_apps.get(pkg, {'package': pkg, 'name': pkg, 'category': 'System'})
                to_remove.append(app_info)

        if to_remove:
            dlg = BatchOperationDialog(to_remove, action="remove", apt_manager=self.apt_manager, parent=self)
            dlg.exec()
            self.checked_packages.clear()
            self.load_catalog()

    def on_table_selection_changed(self):
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_items):
            app = self.current_items[row]
            self.insp_title.setText(f"{app['name']} ({app['package']})")
            is_inst = self.apt_manager.is_package_installed(app['package'])
            inst_type = self.apt_manager.get_install_type(app['package']) if self.apt_manager else None
            type_str = " (Flatpak)" if inst_type == "flatpak" else ""
            self.insp_meta.setText(f"Kategoria: {app.get('category', 'System')}  |  Stan: {'✓ Zainstalowano w systemie' + type_str if is_inst else '• Do pobrania z repozytorium PolonOS'}")
            self.insp_desc.setText(app.get('short_desc', ''))

            icon = QIcon.fromTheme(app.get('icon', 'package-x-generic'))
            if not icon.isNull():
                self.insp_icon.setPixmap(icon.pixmap(44, 44))
            else:
                self.insp_icon.setPixmap(get_logo_pixmap(36, 36))

            self.btn_insp_action.setEnabled(True)

    def on_row_double_clicked(self, row):
        if 0 <= row < len(self.current_items):
            self.open_app_details(self.current_items[row])

    def open_selected_details(self):
        selected_rows = self.table.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.current_items):
                self.open_app_details(self.current_items[row])

    def open_app_details(self, app_data):
        dialog = AppDetailDialog(app_data, self.apt_manager, self)
        dialog.exec()
        self.load_catalog()
