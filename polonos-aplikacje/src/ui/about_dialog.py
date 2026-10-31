import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from ui.assets_helper import get_logo_pixmap, get_logo_icon

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("O programie PolonOS Aplikacje")
        self.setWindowIcon(get_logo_icon())
        self.setFixedSize(560, 480)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        icon_label = QLabel()
        logo_pm = get_logo_pixmap(64, 64)
        if not logo_pm.isNull():
            icon_label.setPixmap(logo_pm)
        else:
            icon_label.setText("PolonOS")

        header_layout.addWidget(icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        lbl_name = QLabel("PolonOS Aplikacje")
        font_title = QFont()
        font_title.setPointSize(18)
        font_title.setBold(True)
        lbl_name.setFont(font_title)
        lbl_name.setStyleSheet("color: #ffffff;")

        lbl_ver = QLabel("Wersja 1.4.0 (KDE & Debian)")
        lbl_ver.setStyleSheet("color: #c22e45; font-weight: bold; font-size: 13px;")

        lbl_sub = QLabel("Menedżer aktualizacji i oprogramowania dystrybucji PolonOS")
        lbl_sub.setStyleSheet("color: #a1a1aa; font-size: 12px;")

        title_box.addWidget(lbl_name)
        title_box.addWidget(lbl_ver)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #2d2d2d;")
        layout.addWidget(line)

        desc_frame = QFrame()
        desc_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
                padding: 14px;
            }
            QLabel {
                color: #d4d4d8;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        desc_layout = QVBoxLayout(desc_frame)

        lbl_desc = QLabel(
            "<b>PolonOS Aplikacje</b> to oficjalne narzędzie graficzne przeznaczone dla użytkowników dystrybucji PolonOS. "
            "Umożliwia łatwą aktualizację pakietów systemowych, instalację i deinstalację programów oraz podnoszenie "
            "wersji całej dystrybucji bez konieczności używania konsoli.<br><br>"
            "<b>Podziękowania i Licencja Synaptic:</b><br>"
            "Program wykorzystuje rozwiązania, inspiracje oraz sprawdzony interfejs logiki menedżera pakietów <b>Synaptic (GPL-2.0)</b>. "
            "Składamy serdeczne podziękowania autorom oraz całej społeczności projektu Synaptic za wieloletni wkład w rozwój wolnego oprogramowania.<br><br>"
            "<i>Wydano na licencji GNU General Public License v2.0 (GPL-2.0).</i>"
        )
        lbl_desc.setWordWrap(True)
        desc_layout.addWidget(lbl_desc)

        layout.addWidget(desc_frame)

        footer_layout = QHBoxLayout()
        lbl_author = QLabel("Copyright © 2026 Zespół PolonOS (polonos.org)")
        lbl_author.setStyleSheet("color: #71717a; font-size: 11px;")

        btn_close = QPushButton("Zamknij")
        btn_close.setObjectName("primary_btn")
        btn_close.clicked.connect(self.accept)

        footer_layout.addWidget(lbl_author)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_close)

        layout.addLayout(footer_layout)
