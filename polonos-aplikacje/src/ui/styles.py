POLONOS_DARK_STYLE = """
QMainWindow, QDialog {
    background-color: #161616;
    color: #f4f4f5;
    font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
}

QWidget {
    color: #f4f4f5;
    font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
}

#header_bar {
    background-color: #1e1e1e;
    border-bottom: 1px solid #2d2d2d;
    padding: 12px 20px;
}

#header_title {
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
}

#header_subtitle {
    font-size: 12px;
    color: #a1a1aa;
}

QTabWidget::pane {
    border: none;
    background-color: #161616;
}

QTabBar::tab {
    background-color: #1e1e1e;
    color: #a1a1aa;
    padding: 12px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #2d2d2d;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #161616;
    color: #c22e45;
    border-top: 3px solid #c22e45;
    border-left: 1px solid #2d2d2d;
    border-right: 1px solid #2d2d2d;
}

QTabBar::tab:hover:!selected {
    background-color: #242424;
    color: #ffffff;
}

#card_frame, .card_frame {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 10px;
    padding: 16px;
}

#card_frame:hover {
    border-color: #3f3f46;
}

#stat_box {
    background-color: #1a1a1a;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    padding: 16px;
}

#stat_title {
    color: #a1a1aa;
    font-size: 12px;
    font-weight: 500;
}

#stat_value {
    color: #ffffff;
    font-size: 22px;
    font-weight: bold;
    margin-top: 4px;
}

QPushButton {
    background-color: #242424;
    color: #f4f4f5;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2d2d2d;
    border-color: #9b1b30;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #111111;
}

QPushButton:disabled {
    background-color: #18181b;
    color: #52525b;
    border-color: #27272a;
}

QPushButton#primary_btn, QPushButton.primary_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c22e45, stop:1 #9b1b30);
    color: #ffffff;
    border: none;
    font-weight: bold;
    padding: 10px 22px;
    border-radius: 6px;
}

QPushButton#primary_btn:hover, QPushButton.primary_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d9384b, stop:1 #c22e45);
}

QPushButton#primary_btn:pressed, QPushButton.primary_btn:pressed {
    background-color: #580f1b;
}

QPushButton#primary_btn:disabled, QPushButton.primary_btn:disabled {
    background: #2a1a1d;
    color: #7a5a60;
}

QPushButton#success_btn {
    background-color: #065f46;
    color: #a7f3d0;
    border: 1px solid #047857;
    font-weight: bold;
}

QPushButton#success_btn:hover {
    background-color: #047857;
    color: #ffffff;
}

QPushButton#danger_btn {
    background-color: #451a1a;
    color: #fca5a5;
    border: 1px solid #7f1d1d;
    font-weight: bold;
}

QPushButton#danger_btn:hover {
    background-color: #7f1d1d;
    color: #ffffff;
}

QPushButton.table_btn {
    background-color: #27272a;
    color: #f4f4f5;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 500;
    min-height: 24px;
    max-height: 24px;
}

QPushButton.table_btn:hover {
    background-color: #3f3f46;
    color: #ffffff;
    border-color: #c22e45;
}

QPushButton.table_btn_primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c22e45, stop:1 #9b1b30);
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
    min-height: 24px;
    max-height: 24px;
}

QPushButton.table_btn_primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d9384b, stop:1 #c22e45);
}

QPushButton.table_btn_danger {
    background-color: #451a1a;
    color: #fca5a5;
    border: 1px solid #7f1d1d;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
    min-height: 24px;
    max-height: 24px;
}

QPushButton.table_btn_danger:hover {
    background-color: #7f1d1d;
    color: #ffffff;
}

#warning_box {
    background-color: #2e1d0c;
    border: 1px solid #78350f;
    border-left: 4px solid #f59e0b;
    border-radius: 8px;
    padding: 16px;
}

#warning_title {
    color: #fbbf24;
    font-size: 15px;
    font-weight: bold;
}

#warning_desc {
    color: #fef3c7;
    font-size: 13px;
    line-height: 1.4;
}

QLineEdit {
    background-color: #1a1a1a;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    color: #f4f4f5;
    padding: 9px 14px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #c22e45;
}

QPushButton.category_pill {
    background-color: #1a1a1a;
    color: #a1a1aa;
    border: 1px solid #2d2d2d;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
}

QPushButton.category_pill:hover {
    background-color: #27272a;
    color: #ffffff;
}

QPushButton.category_pill:checked {
    background-color: #c22e45;
    color: #ffffff;
    border-color: #c22e45;
    font-weight: bold;
}

QTableWidget, QListWidget {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    color: #f4f4f5;
    gridline-color: #27272a;
}

QTableWidget::item, QListWidget::item {
    padding: 8px;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #9b1b30;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #18181b;
    color: #a1a1aa;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #2d2d2d;
    font-weight: 600;
}

QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #111111;
    width: 8px;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #2d2d2d;
    min-height: 20px;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background-color: #c22e45;
}

QScrollBar::add-line, QScrollBar::sub-line {
    border: none;
    background: none;
}

QProgressBar {
    background-color: #1a1a1a;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c22e45, stop:1 #e15265);
    border-radius: 5px;
}

QPlainTextEdit#console_output {
    background-color: #0d0d0d;
    color: #38bdf8;
    font-family: 'Hack', 'Fira Code', 'DejaVu Sans Mono', monospace;
    font-size: 12px;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    padding: 10px;
}

QToolTip {
    background-color: #1e1e1e;
    color: #f4f4f5;
    border: 1px solid #2d2d2d;
    border-radius: 4px;
    padding: 6px;
}

QCheckBox {
    spacing: 6px;
    background: transparent;
    color: #f4f4f5;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #444444;
    background-color: #242424;
}

QCheckBox::indicator:hover {
    border-color: #c22e45;
}

QCheckBox::indicator:checked {
    background-color: #c22e45;
    border-color: #e15265;
    image: url("__CHECK_ICON_URL__");
}
"""

try:
    from ui.assets_helper import get_check_icon_path
    _chk_icon = get_check_icon_path() or ""
    POLONOS_DARK_STYLE = POLONOS_DARK_STYLE.replace("__CHECK_ICON_URL__", _chk_icon.replace("\\", "/"))
except Exception:
    pass
