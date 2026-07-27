# Stylesheet definitions for PolonOS Calendar
# High-quality dark UI stylesheet mimicking premium modern web apps.
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKED_SVG_PATH = os.path.join(BASE_DIR, "checked.svg").replace("\\", "/")
# ==========================================
# System Light Style Template
# ==========================================
LIGHT_STYLE_TEMPLATE = """
QMainWindow {
    background-color: #fafafa;
    color: #27272a;
    font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
}

/* Sidebar styling */
#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #e4e4e7;
    min-width: 280px;
    max-width: 280px;
}

#sidebar QLabel {
    color: #27272a;
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
    background-color: #ffffff;
    color: #27272a;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #f4f4f5;
    border-color: #d4d4d8;
}

QPushButton:pressed {
    background-color: #e4e4e7;
}

/* Accent Button (Primary) */
QPushButton#primary_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e15265, stop:1 #f43f5e);
    color: #ffffff;
    border: none;
    font-weight: bold;
}

QPushButton#primary_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d9384b, stop:1 #e15265);
}

QPushButton#primary_btn:pressed {
    background-color: #b91c1c;
}

/* Delete / Action buttons */
QPushButton#danger_btn {
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
}

QPushButton#danger_btn:hover {
    background-color: #fca5a5;
    color: #7f1d1d;
}

/* List widgets */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    color: #27272a;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #f4f4f5;
}

QListWidget::item:selected {
    background-color: #fff1f2;
    color: #d9384b;
}

/* Line Edits & Comboboxes */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    color: #27272a;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #e15265;
}

/* Checkboxes */
QCheckBox {
    color: #27272a;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #d4d4d8;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #e15265;
}

QCheckBox::indicator:checked {
    background-color: #e15265;
    border-color: #e15265;
    image: url(CHECKED_SVG_URL);
}

/* Tooltips */
QToolTip {
    background-color: #ffffff;
    color: #27272a;
    border: 1px solid #e4e4e7;
    border-radius: 4px;
    padding: 4px;
}

/* ScrollBars */
QScrollBar:vertical {
    background-color: #ffffff;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #e4e4e7;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #d4d4d8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

/* Calendar Views Navigation & Container */
#view_container {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
}

#nav_bar {
    background-color: #ffffff;
    border-bottom: 1px solid #e4e4e7;
    padding: 8px;
}

QLabel#month_year_label {
    font-size: 18px;
    font-weight: bold;
    color: #27272a;
}

/* Systray Popup Styling */
#systray_popup {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 12px;
}

#popup_title {
    font-size: 14px;
    font-weight: bold;
    color: #27272a;
    border-bottom: 1px solid #e4e4e7;
    padding-bottom: 6px;
}

/* Event List Card inside Popup / Calendar views */
#event_card {
    background-color: #f4f4f5;
    border-radius: 8px;
    border-left: 4px solid #e15265; /* Dynamic overwrite */
    padding: 8px 12px;
}

#event_card_title {
    font-weight: bold;
    color: #27272a;
    font-size: 13px;
}

#event_card_time {
    color: #d9384b;
    font-size: 11px;
}

#event_card_loc {
    color: #71717a;
    font-size: 11px;
}

/* Month view day cell */
#month_day_cell {
    background-color: #ffffff;
    border: 1px solid #f4f4f5;
    border-radius: 6px;
}

#month_day_cell[is_today="true"] {
    border: 2px solid #e15265;
    background-color: #fff1f2;
}

#month_day_cell[is_other_month="true"] {
    background-color: #fafafa;
}

#month_day_number {
    font-weight: bold;
    font-size: 11px;
    color: #a1a1aa;
}

#month_day_cell[is_today="true"] #month_day_number {
    color: #d9384b;
}

/* Month event dot container */
#month_event_dots_layout {
    margin-top: 4px;
}

/* Dialog styling */
QDialog {
    background-color: #ffffff;
}

QDialog QLabel {
    color: #27272a;
}

/* Top bar styling */
#top_bar {
    background-color: #ffffff;
    border-bottom: 1px solid #e4e4e7;
}

#top_bar QLabel {
    color: #27272a;
}

/* Sidebar Account list QFrame */
#account_card {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
}

#account_email_label {
    color: #27272a;
    font-weight: bold;
    font-size: 11px;
}

/* Pinned All-day row and widget styling */
#allday_events_widget, #allday_row_widget {
    background-color: #f4f5f7;
    border-bottom: 1px solid #e4e4e7;
}
"""

LIGHT_STYLE = LIGHT_STYLE_TEMPLATE.replace("CHECKED_SVG_URL", CHECKED_SVG_PATH)


# ==========================================
# PolonOS Style Template (polonos.org scheme)
# ==========================================
POLONOS_STYLE_TEMPLATE = """
QMainWindow {
    background-color: #161616;
    color: #f4f4f5;
    font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
}

/* Sidebar styling */
#sidebar {
    background-color: #1e1e1e;
    border-right: 1px solid #2d2d2d;
    min-width: 250px;
    max-width: 320px;
}

#sidebar QLabel {
    color: #ffffff;
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
    background-color: #242424;
    color: #f4f4f5;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2d2d2d;
    border-color: #9b1b30;
}

QPushButton:pressed {
    background-color: #111111;
}

/* Accent Button (Primary) */
QPushButton#primary_btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #c22e45, stop:1 #9b1b30);
    color: #ffffff;
    border: none;
    font-weight: bold;
}

QPushButton#primary_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #9b1b30, stop:1 #7a1526);
}

QPushButton#primary_btn:pressed {
    background-color: #580f1b;
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
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    color: #e4e4e7;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #2d2d2d;
}

QListWidget::item:selected {
    background-color: #9b1b30;
    color: #ffffff;
}

/* Line Edits & Comboboxes */
QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    color: #f4f4f5;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #c22e45;
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
    border: 1.5px solid #2d2d2d;
    background-color: #1e1e1e;
}

QCheckBox::indicator:hover {
    border-color: #c22e45;
}

QCheckBox::indicator:checked {
    background-color: #c22e45;
    border-color: #c22e45;
    image: url(CHECKED_SVG_URL);
}

/* Tooltips */
QToolTip {
    background-color: #1e1e1e;
    color: #f4f4f5;
    border: 1px solid #2d2d2d;
    border-radius: 4px;
    padding: 4px;
}

/* ScrollBars */
QScrollBar:vertical {
    background-color: #111111;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #2d2d2d;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #9b1b30;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

/* Calendar Views Navigation & Container */
#view_container {
    background-color: #1c1c1c;
    border-radius: 8px;
}

#nav_bar {
    background-color: #111111;
    border-bottom: 1px solid #2d2d2d;
    padding: 8px;
}

QLabel#month_year_label {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

/* Systray Popup Styling */
#systray_popup {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 12px;
}

#popup_title {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
    border-bottom: 1px solid #2d2d2d;
    padding-bottom: 6px;
}

/* Event List Card inside Popup / Calendar views */
#event_card {
    background-color: #242424;
    border-radius: 8px;
    border-left: 4px solid #c22e45; /* Dynamic overwrite */
    padding: 8px 12px;
}

#event_card_title {
    font-weight: bold;
    color: #f4f4f5;
    font-size: 13px;
}

#event_card_time {
    color: #c22e45;
    font-size: 11px;
}

#event_card_loc {
    color: #a1a1aa;
    font-size: 11px;
}

/* Month view day cell */
#month_day_cell {
    background-color: #202020;
    border: 1px solid #2d2d2d;
    border-radius: 4px;
}

#month_day_cell[is_today="true"] {
    border: 1.5px solid #c22e45;
    background-color: #2b1b1f;
}

#month_day_cell[is_other_month="true"] {
    background-color: #161616;
}

#month_day_number {
    font-weight: bold;
    font-size: 11px;
    color: #71717a;
}

#month_day_cell[is_today="true"] #month_day_number {
    color: #c22e45;
}

/* Month event dot container */
#month_event_dots_layout {
    margin-top: 4px;
}

/* Dialog styling */
QDialog {
    background-color: #1e1e1e;
}

QDialog QLabel {
    color: #e4e4e7;
}

/* Top bar styling */
#top_bar {
    background-color: #111111;
    border-bottom: 1px solid #2d2d2d;
}

#top_bar QLabel {
    color: #ffffff;
}
"""

POLONOS_STYLE = POLONOS_STYLE_TEMPLATE.replace("CHECKED_SVG_URL", CHECKED_SVG_PATH)


# ==========================================
# Theme helpers and System Detection
# ==========================================
from PySide6.QtGui import QGuiApplication, QColor
from PySide6.QtCore import Qt

def is_system_dark_mode():
    return get_current_theme_mode() == "ciemny"

def get_system_style():
    return LIGHT_STYLE

def get_current_theme_mode():
    app = QGuiApplication.instance()
    if not app:
        return "jasny"
        
    theme_mode = app.property("theme_mode")
    if theme_mode is not None:
        return theme_mode
        
    # Read from database (slow fallback)
    try:
        from src.database import DatabaseManager
        db = DatabaseManager()
        theme_mode = db.get_setting("theme_mode", "jasny")
        # Migrate old settings
        if theme_mode in ("polonos", "ciemny"):
            theme_mode = "ciemny"
        else:
            theme_mode = "jasny"
    except Exception:
        theme_mode = "jasny"
        
    app.setProperty("theme_mode", theme_mode)
    return theme_mode

def get_theme_today_styles():
    theme_mode = get_current_theme_mode()
    if theme_mode == "ciemny":
        return {
            "accent": "#c22e45",
            "today_bg": "#2b1b1f",
            "today_border": "#c22e45"
        }
    else:
        return {
            "accent": "#e15265",
            "today_bg": "#fff1f2",
            "today_border": "#e15265"
        }

def get_timeline_colors():
    theme_mode = get_current_theme_mode()
    if theme_mode == "ciemny":
        return {
            "today_bg": QColor("#2b1b1f"),
            "line": QColor("#2d2d2d"),
            "text": QColor("#a1a1aa")
        }
    else:
        return {
            "today_bg": QColor("#fff1f2"),
            "line": QColor("#e4e4e7"),
            "text": QColor("#71717a")
        }
