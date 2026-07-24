# Stylesheet definitions for PolonOS Calendar
# High-quality dark UI stylesheet mimicking premium modern web apps.
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKED_SVG_PATH = os.path.join(BASE_DIR, "checked.svg").replace("\\", "/")

DARK_STYLE_TEMPLATE = """
QMainWindow {
    background-color: #1a1a1e;
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
}

/* Sidebar styling */
#sidebar {
    background-color: #111113;
    border-right: 1px solid #27272a;
    min-width: 250px;
    max-width: 320px;
}

#sidebar QLabel {
    color: #f4f4f5;
    font-weight: bold;
}

/* Sidebar Accounts list styling */
#accounts_list {
    background-color: transparent;
    border: none;
}

#accounts_list::item {
    padding: 8px;
    border-radius: 6px;
    margin-bottom: 4px;
}

/* Scroll area styling */
QScrollArea {
    border: none;
    background-color: transparent;
}

/* General button styling */
QPushButton {
    background-color: #27272a;
    color: #f4f4f5;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3f3f46;
    border-color: #52525b;
}

QPushButton:pressed {
    background-color: #18181b;
}

/* Accent Button (Primary) */
QPushButton#primary_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
    color: #ffffff;
    border: none;
    font-weight: bold;
}

QPushButton#primary_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #4338ca);
}

QPushButton#primary_btn:pressed {
    background-color: #3730a3;
}

/* Delete / Action buttons */
QPushButton#danger_btn {
    background-color: #451a1a;
    color: #fca5a5;
    border: 1px solid #7f1d1d;
}

QPushButton#danger_btn:hover {
    background-color: #7f1d1d;
    color: #ffffff;
}

/* List widgets */
QListWidget {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    color: #e4e4e7;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #27272a;
}

QListWidget::item:selected {
    background-color: #3f3f46;
    color: #ffffff;
}

/* Line Edits & Comboboxes */
QLineEdit {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    color: #f4f4f5;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #6366f1;
}

/* Checkboxes */
QCheckBox {
    color: #d4d4d8;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #52525b;
    background-color: #18181b;
}

QCheckBox::indicator:hover {
    border-color: #6366f1;
}

QCheckBox::indicator:checked {
    background-color: #6366f1;
    border-color: #6366f1;
    image: url(CHECKED_SVG_URL);
}

/* Tooltips */
QToolTip {
    background-color: #18181b;
    color: #f4f4f5;
    border: 1px solid #27272a;
    border-radius: 4px;
    padding: 4px;
}

/* ScrollBars */
QScrollBar:vertical {
    background-color: #111113;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #27272a;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3f3f46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

/* Calendar Views Navigation & Container */
#view_container {
    background-color: #151518;
    border-radius: 8px;
}

#nav_bar {
    background-color: #111113;
    border-bottom: 1px solid #27272a;
    padding: 8px;
}

QLabel#month_year_label {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

/* Systray Popup Styling */
#systray_popup {
    background-color: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 12px;
}

#popup_title {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
    border-bottom: 1px solid #27272a;
    padding-bottom: 6px;
}

/* Event List Card inside Popup / Calendar views */
#event_card {
    background-color: #202024;
    border-radius: 8px;
    border-left: 4px solid #6366f1; /* Dynamic overwrite */
    padding: 8px 12px;
}

#event_card_title {
    font-weight: bold;
    color: #f4f4f5;
    font-size: 13px;
}

#event_card_time {
    color: #9ab3f5;
    font-size: 11px;
}

#event_card_loc {
    color: #a1a1aa;
    font-size: 11px;
}

/* Month view day cell */
#month_day_cell {
    background-color: #1c1c21;
    border: 1px solid #27272a;
    border-radius: 4px;
}

#month_day_cell[is_today="true"] {
    border: 1.5px solid #6366f1;
    background-color: #22222b;
}

#month_day_cell[is_other_month="true"] {
    background-color: #121215;
}

#month_day_number {
    font-weight: bold;
    font-size: 11px;
    color: #71717a;
}

#month_day_cell[is_today="true"] #month_day_number {
    color: #6366f1;
}

/* Month event dot container */
#month_event_dots_layout {
    margin-top: 4px;
}

/* Dialog styling */
QDialog {
    background-color: #18181b;
}

QDialog QLabel {
    color: #e4e4e7;
}
"""

DARK_STYLE = DARK_STYLE_TEMPLATE.replace("CHECKED_SVG_URL", CHECKED_SVG_PATH)
