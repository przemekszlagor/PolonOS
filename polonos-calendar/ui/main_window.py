import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QFrame, 
                             QStackedWidget, QDialog, QFileDialog, QCheckBox,
                             QMessageBox, QSystemTrayIcon, QMenu, QGraphicsDropShadowEffect,
                             QLineEdit, QApplication, QColorDialog, QSpinBox)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QUrl, QTimer
from PySide6.QtGui import QIcon, QAction, QColor, QCursor, QPixmap, QDesktopServices

from src.database import DatabaseManager
from src.google_sync import GoogleCalendarSync
from src.ui.calendar_views import DayView, WeekView, MonthView
from src.ui.systray_popup import SystrayPopup
from src.ui.styles import DARK_STYLE

PL_MONTHS = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
PL_MONTHS_GEN = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"]

def get_logo_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "polonos-calendar-logo.png")
    if os.path.exists(logo_path):
        return logo_path
    
    # System fallbacks
    fallbacks = [
        "/opt/polonos-calendar/src/ui/polonos-calendar-logo.png",
        "/usr/share/pixmaps/polonos-calendar.png"
    ]
    for p in fallbacks:
        if os.path.exists(p):
            return p
    return ""



class SyncWorker(QThread):
    """
    Worker thread to run Google Calendar sync in the background so the UI doesn't freeze.
    """
    finished = Signal(str, bool) # email, success

    def __init__(self, sync_manager, email):
        super().__init__()
        self.sync_manager = sync_manager
        self.email = email

    def run(self):
        try:
            success = self.sync_manager.sync_account(self.email)
            self.finished.emit(self.email, success)
        except Exception as e:
            print(f"Error in SyncWorker for {self.email}: {e}")
            self.finished.emit(self.email, False)


class LoginWorker(QThread):
    """
    Worker thread to run Google Calendar login in the background so the UI doesn't freeze.
    """
    login_finished = Signal(str, str) # email, error_message
    open_url = Signal(str)      # url to open in browser (main thread)

    def __init__(self, sync_manager):
        super().__init__()
        self.sync_manager = sync_manager

    def run(self):
        try:
            def browser_opener(url):
                self.open_url.emit(url)
            email = self.sync_manager.authenticate_real_account(browser_opener=browser_opener)
            self.login_finished.emit(email, "")
        except Exception as e:
            self.login_finished.emit("", str(e))


class NotificationSettingsDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Ustawienia powiadomień")
        self.resize(360, 220)
        self.setModal(True)
        
        # Dark style stylesheet matching the rest of the application
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e24;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 13px;
            }
            QSpinBox {
                background-color: #27272a;
                border: 1px solid #3f3f46;
                color: #ffffff;
                padding: 4px;
                padding-right: 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                background-color: #27272a;
                border-left: 1px solid #3f3f46;
                border-bottom: 1px solid #3f3f46;
                border-top-right-radius: 4px;
            }
            QSpinBox::up-button:hover {
                background-color: #3f3f46;
            }
            QSpinBox::up-button:pressed {
                background-color: #52525b;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                background-color: #27272a;
                border-left: 1px solid #3f3f46;
                border-bottom-right-radius: 4px;
            }
            QSpinBox::down-button:hover {
                background-color: #3f3f46;
            }
            QSpinBox::down-button:pressed {
                background-color: #52525b;
            }
            QSpinBox::up-arrow {
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #ffffff;
            }
            QSpinBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QPushButton {
                background-color: #27272a;
                color: #ffffff;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3f3f46;
                border-color: #52525b;
            }
            QPushButton#save_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
                border: none;
                font-weight: bold;
            }
            QPushButton#save_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #4338ca);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_lbl = QLabel("Konfiguracja powiadomień", self)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_lbl)
        
        # Checkbox: Enable notifications
        self.enabled_cb = QCheckBox("Włącz powiadomienia systemowe", self)
        enabled_val = self.db.get_setting("notifications_enabled", "1")
        self.enabled_cb.setChecked(enabled_val == "1")
        layout.addWidget(self.enabled_cb)
        
        # Lead time selector
        time_layout = QHBoxLayout()
        time_lbl = QLabel("Powiadom przed wydarzeniem (minuty):", self)
        self.time_sb = QSpinBox(self)
        self.time_sb.setRange(1, 120)
        lead_time_val = self.db.get_setting("notifications_lead_time", "15")
        try:
            self.time_sb.setValue(int(lead_time_val))
        except ValueError:
            self.time_sb.setValue(15)
            
        time_layout.addWidget(time_lbl)
        time_layout.addWidget(self.time_sb)
        layout.addLayout(time_layout)
        
        layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Anuluj", self)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Zapisz", self)
        save_btn.setObjectName("save_btn")
        save_btn.clicked.connect(self.save_settings)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def save_settings(self):
        enabled_str = "1" if self.enabled_cb.isChecked() else "0"
        lead_time_str = str(self.time_sb.value())
        
        self.db.set_setting("notifications_enabled", enabled_str)
        self.db.set_setting("notifications_lead_time", lead_time_str)
        self.accept()


class AuthDialog(QDialog):
    """
    Onboarding and Account Authentication Dialog.
    """
    account_added = Signal(str) # email

    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.login_worker = None
        self.setWindowTitle("Dodaj konto Google")
        self.setFixedSize(450, 260)
        self.setObjectName("auth_dialog")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(15)
        
        # Header
        title = QLabel("Zaloguj się do swojego konta Google", self)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        self.layout.addWidget(title)
        
        desc = QLabel(
            "Kliknięcie przycisku logowania otworzy oficjalną stronę Google w Twojej przeglądarce.",
            self
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a1a1aa; font-size: 12px; line-height: 16px;")
        self.layout.addWidget(desc)
        
        # Status Label
        self.status_lbl = QLabel(self)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size: 11px;")
        self.layout.addWidget(self.status_lbl)
        
        # Buttons layout
        self.btn_layout = QVBoxLayout()
        self.btn_layout.setSpacing(10)
        
        self.login_btn = QPushButton("Zaloguj przez Google (Otwórz przeglądarkę)", self)
        self.login_btn.setObjectName("primary_btn")
        self.login_btn.clicked.connect(self._on_login_clicked)
        
        self.btn_layout.addWidget(self.login_btn)
        self.layout.addLayout(self.btn_layout)
        
        self.close_btn = QPushButton("Anuluj", self)
        self.close_btn.clicked.connect(self.reject)
        self.layout.addWidget(self.close_btn)

    def _on_login_clicked(self):
        # Prevent starting multiple flows
        if self.login_worker and self.login_worker.isRunning():
            return
            
        self.status_lbl.setText("Uruchamianie logowania... Sprawdź okno przeglądarki.")
        self.status_lbl.setStyleSheet("color: #fbbf24; font-weight: bold;")
        self.login_btn.setEnabled(False)
        QApplication.processEvents()
        
        self.login_worker = LoginWorker(self.sync_manager)
        self.login_worker.open_url.connect(self._on_open_url)
        self.login_worker.login_finished.connect(self._on_login_worker_finished)
        self.login_worker.start()

    def _on_open_url(self, url):
        # Open URL safely in the main thread using webbrowser first, then QDesktopServices
        try:
            import webbrowser
            webbrowser.open(url, new=1, autoraise=True)
        except Exception:
            QDesktopServices.openUrl(QUrl(url))

    def _on_login_worker_finished(self, email, error):
        self.login_btn.setEnabled(True)
        self.status_lbl.setText("")
        
        if error:
            QMessageBox.critical(self, "Błąd logowania", f"Logowanie nie powiodło się:\n{error}")
        elif email:
            self.account_added.emit(email)
            QMessageBox.information(self, "Logowanie", f"Pomyślnie zalogowano konto: {email}")
            self.accept()


class MainWindow(QMainWindow):
    """
    Main Application Window.
    """
    def __init__(self, db_manager, sync_manager):
        super().__init__()
        self.db = db_manager
        self.sync_manager = sync_manager
        self.active_date = datetime.now()
        self.current_view_index = 1 # Default to Week View (0 = Day, 1 = Week, 2 = Month)
        self.sync_workers = {}
        
        self.setWindowTitle("PolonOS Calendar")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_STYLE)
        
        # Set Window Icon using Logo
        logo_path = get_logo_path()
        if logo_path:
            self.setWindowIcon(QIcon(logo_path))
        
        # Central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Setup UI parts
        self._setup_sidebar()
        self._setup_calendar_area()
        self._setup_systray()
        self.setup_notifications()
        
        # Load initial data
        self.reload_accounts_and_calendars()
        self.refresh_calendar_view()
        self.start_startup_sync()

    def _setup_sidebar(self):
        self.sidebar = QFrame(self)
        self.sidebar.setObjectName("sidebar")
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 15)
        sidebar_layout.setSpacing(15)
        
        # Logo at the top of the sidebar
        logo_path = get_logo_path()
        if logo_path:
            logo_lbl = QLabel(self.sidebar)
            pixmap = QPixmap(logo_path)
            logo_lbl.setPixmap(pixmap.scaledToWidth(180, Qt.SmoothTransformation))
            logo_lbl.setAlignment(Qt.AlignCenter)
            logo_lbl.setStyleSheet("margin-bottom: 5px;")
            sidebar_layout.addWidget(logo_lbl)
            
        # Sidebar title
        title = QLabel("MOJE KONTA", self.sidebar)
        title.setStyleSheet("font-size: 11px; font-weight: bold; color: #71717a; letter-spacing: 1px;")
        sidebar_layout.addWidget(title)
        
        # Scroll Area for accounts list
        self.accounts_scroll = QScrollArea(self.sidebar)
        self.accounts_scroll.setWidgetResizable(True)
        self.accounts_scroll.setFrameShape(QFrame.NoFrame)
        self.accounts_scroll.setStyleSheet("background: transparent;")
        
        self.accounts_container = QWidget(self.sidebar)
        self.accounts_container.setStyleSheet("background: transparent;")
        self.accounts_layout = QVBoxLayout(self.accounts_container)
        self.accounts_layout.setContentsMargins(0, 0, 0, 0)
        self.accounts_layout.setSpacing(12)
        self.accounts_layout.addStretch()
        
        self.accounts_scroll.setWidget(self.accounts_container)
        sidebar_layout.addWidget(self.accounts_scroll)
        
        # Add account button
        self.add_account_btn = QPushButton("Dodaj konto Google", self.sidebar)
        self.add_account_btn.setObjectName("primary_btn")
        self.add_account_btn.clicked.connect(self._on_add_account_clicked)
        sidebar_layout.addWidget(self.add_account_btn)
        
        self.main_layout.addWidget(self.sidebar)

    def _setup_calendar_area(self):
        self.calendar_area = QFrame(self)
        self.calendar_area.setObjectName("view_container")
        
        calendar_layout = QVBoxLayout(self.calendar_area)
        calendar_layout.setContentsMargins(0, 0, 0, 0)
        calendar_layout.setSpacing(0)
        
        # Nav Bar
        self.nav_bar = QFrame(self.calendar_area)
        self.nav_bar.setObjectName("nav_bar")
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(15, 10, 15, 10)
        
        # Navigation arrows
        self.prev_btn = QPushButton("<", self.nav_bar)
        self.prev_btn.setFixedWidth(36)
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        nav_layout.addWidget(self.prev_btn)
        
        self.today_btn = QPushButton("Dziś", self.nav_bar)
        self.today_btn.clicked.connect(self._on_today_clicked)
        nav_layout.addWidget(self.today_btn)
        
        self.next_btn = QPushButton(">", self.nav_bar)
        self.next_btn.setFixedWidth(36)
        self.next_btn.clicked.connect(self._on_next_clicked)
        nav_layout.addWidget(self.next_btn)
        
        # Active range text
        self.month_year_label = QLabel(self.nav_bar)
        self.month_year_label.setObjectName("month_year_label")
        self.month_year_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-left: 10px; color: #ffffff;")
        nav_layout.addWidget(self.month_year_label)
        
        nav_layout.addStretch()
        
        # Quick manual sync button
        self.sync_all_btn = QPushButton("Synchronizuj chmurę", self.nav_bar)
        self.sync_all_btn.setStyleSheet("font-size: 12px; color: #38bdf8; border-color: #0369a1; background-color: #0c1e2d;")
        self.sync_all_btn.clicked.connect(self.sync_all_accounts)
        nav_layout.addWidget(self.sync_all_btn)
        
        # Notifications config button
        self.notifications_btn = QPushButton("POWIADOMIENIA", self.nav_bar)
        self.notifications_btn.setStyleSheet("font-size: 12px; color: #a7f3d0; border-color: #065f46; background-color: #064e3b;")
        self.notifications_btn.clicked.connect(self.show_notification_settings)
        nav_layout.addWidget(self.notifications_btn)
        
        # View switcher Control
        self.view_switch_layout = QHBoxLayout()
        self.view_switch_layout.setSpacing(6)
        self.view_switch_layout.setContentsMargins(10, 0, 0, 0)
        
        self.day_btn = QPushButton("Dzień", self.nav_bar)
        self.week_btn = QPushButton("Tydzień", self.nav_bar)
        self.month_btn = QPushButton("Miesiąc", self.nav_bar)
        
        self.day_btn.clicked.connect(lambda: self.switch_view(0))
        self.week_btn.clicked.connect(lambda: self.switch_view(1))
        self.month_btn.clicked.connect(lambda: self.switch_view(2))
        
        self.view_switch_layout.addWidget(self.day_btn)
        self.view_switch_layout.addWidget(self.week_btn)
        self.view_switch_layout.addWidget(self.month_btn)
        nav_layout.addLayout(self.view_switch_layout)
        
        calendar_layout.addWidget(self.nav_bar)
        
        # Stacked Widget for Views
        self.stacked_views = QStackedWidget(self.calendar_area)
        
        self.day_view = DayView(self.stacked_views)
        self.day_view.event_clicked.connect(self.show_event_details)
        
        self.week_view = WeekView(self.stacked_views)
        self.week_view.event_clicked.connect(self.show_event_details)
        
        self.month_view = MonthView(self.stacked_views)
        self.month_view.day_clicked.connect(self._on_month_day_clicked)
        
        self.stacked_views.addWidget(self.day_view)
        self.stacked_views.addWidget(self.week_view)
        self.stacked_views.addWidget(self.month_view)
        
        calendar_layout.addWidget(self.stacked_views, 1)
        
        # Default view active style
        self.switch_view(self.current_view_index)
        
        self.main_layout.addWidget(self.calendar_area, 1)

    def _setup_systray(self):
        # Create Systray Icon
        self.tray_icon = QSystemTrayIcon(self)
        
        logo_path = get_logo_path()
        if logo_path:
            self.tray_icon.setIcon(QIcon(logo_path))
        else:
            # Fallback icon
            icon_path = "/usr/share/icons/Adwaita/scalable/apps/office-calendar-symbolic.svg"
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                self.tray_icon.setIcon(QIcon.fromTheme("office-calendar", QIcon.fromTheme("calendar")))
            
        # Create popup
        self.tray_popup = SystrayPopup(self.db)
        self.tray_popup.open_main_requested.connect(self.restore_window)
        
        # Context Menu
        self.tray_menu = QMenu(self)
        self.tray_menu.setStyleSheet("background-color: #18181b; color: #f4f4f5; border: 1px solid #27272a;")
        
        show_action = QAction("Pokaż Kalendarz", self)
        show_action.triggered.connect(self.restore_window)
        
        sync_action = QAction("Synchronizuj kalendarze", self)
        sync_action.triggered.connect(self.sync_all_accounts)
        
        exit_action = QAction("Zakończ program", self)
        exit_action.triggered.connect(self.exit_app)
        
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(sync_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger: # Left click
            if self.tray_popup.isVisible():
                self.tray_popup.hide()
            else:
                # Refresh upcoming list and position next to tray icon
                self.tray_popup.refresh_events()
                self.tray_popup.position_near_tray(self.tray_icon.geometry())
                self.tray_popup.show()
                self.tray_popup.activateWindow()

    def restore_window(self):
        self.showNormal()
        self.activateWindow()

    def exit_app(self):
        # Cleanly quit QApplication
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        # Override close button to ask user
        if self.tray_icon.isVisible():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Zamykanie PolonOS Calendar")
            msg_box.setText("Czy chcesz całkowicie zakończyć działanie aplikacji, czy tylko zamknąć okno (pozostawiając program w tle)?")
            
            # Custom buttons
            exit_btn = msg_box.addButton("Wyjdź całkowicie", QMessageBox.YesRole)
            hide_btn = msg_box.addButton("Pozostaw w tle", QMessageBox.NoRole)
            cancel_btn = msg_box.addButton("Anuluj", QMessageBox.RejectRole)
            
            msg_box.setDefaultButton(hide_btn)
            
            # Premium dark styling
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e24;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #27272a;
                    color: #ffffff;
                    border: 1px solid #3f3f46;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-weight: 500;
                    min-width: 90px;
                }
                QPushButton:hover {
                    background-color: #3f3f46;
                    border-color: #52525b;
                }
            """)
            
            msg_box.exec()
            
            clicked = msg_box.clickedButton()
            if clicked == exit_btn:
                self.tray_icon.hide()
                event.accept()
                QApplication.quit()
            elif clicked == hide_btn:
                self.hide()
                event.ignore()
            else:
                event.ignore()
        else:
            event.accept()

    def setup_notifications(self):
        self.notified_event_ids = set()
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_notifications)
        # Check every 30 seconds
        self.notification_timer.start(30000)
        
    def check_notifications(self):
        enabled = self.db.get_setting("notifications_enabled", "1")
        if enabled != "1":
            return
            
        lead_time_str = self.db.get_setting("notifications_lead_time", "15")
        try:
            lead_time = int(lead_time_str)
        except ValueError:
            lead_time = 15
            
        now = datetime.now()
        start_iso = now.isoformat()
        end_iso = (now + timedelta(minutes=lead_time)).isoformat()
        
        events = self.db.get_events_for_range(start_iso, end_iso)
        for event in events:
            if event.get('is_all_day', 0) == 1:
                continue
                
            event_id = event['id']
            if event_id not in self.notified_event_ids:
                start_dt = datetime.fromisoformat(event['start_time'])
                if start_dt > now:
                    self.notified_event_ids.add(event_id)
                    summary = event.get('summary', '(Bez tytułu)')
                    time_str = start_dt.strftime("%H:%M")
                    self.tray_icon.showMessage(
                        "Nadchodzące wydarzenie",
                        f"{summary} rozpoczyna się o {time_str}",
                        QSystemTrayIcon.Information,
                        10000
                    )

    def show_notification_settings(self):
        dialog = NotificationSettingsDialog(self.db, self)
        dialog.exec()

    def _on_add_account_clicked(self):
        dialog = AuthDialog(self.sync_manager, self)
        dialog.account_added.connect(self.on_account_added)
        dialog.exec()

    def on_account_added(self, email):
        self.reload_accounts_and_calendars()
        # Trigger background sync for the new account
        self.sync_account(email)

    def reload_accounts_and_calendars(self):
        # Clear sidebar list
        # Remove widgets from accounts layout except the bottom spacer
        for child in self.accounts_container.findChildren(QFrame):
            child.setParent(None)
            child.deleteLater()
            
        accounts = self.db.get_accounts()
        
        if not accounts:
            lbl = QLabel("Brak dodanych kont.\nKliknij przycisk poniżej,\naby dodać konto.", self.accounts_container)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #71717a; font-size: 11px; padding: 20px; line-height: 16px;")
            self.accounts_layout.insertWidget(0, lbl)
            return

        # Build list of accounts
        for acc in accounts:
            acc_frame = QFrame(self.accounts_container)
            acc_frame.setStyleSheet("""
                QFrame {
                    background-color: #18181b;
                    border: 1px solid #27272a;
                    border-radius: 8px;
                }
            """)
            acc_layout = QVBoxLayout(acc_frame)
            acc_layout.setContentsMargins(8, 8, 8, 8)
            acc_layout.setSpacing(6)
            
            # Account Header
            header_layout = QHBoxLayout()
            email_lbl = QLabel(acc['display_name'] or acc['email'], acc_frame)
            email_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px;")
            header_layout.addWidget(email_lbl, 1)
            
            # Delete button
            del_btn = QPushButton("Usuń", acc_frame)
            del_btn.setObjectName("danger_btn")
            del_btn.setFixedSize(QSize(45, 20))
            del_btn.setStyleSheet("""
                QPushButton {
                    font-size: 9px;
                    padding: 2px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            del_btn.clicked.connect(lambda checked=False, email=acc['email']: self.remove_account(email))
            header_layout.addWidget(del_btn)
            
            acc_layout.addLayout(header_layout)
            
            # Calendars List
            calendars = self.db.get_calendars(acc['email'])
            for cal in calendars:
                cal_layout = QHBoxLayout()
                cal_layout.setContentsMargins(4, 0, 4, 0)
                
                cb = QCheckBox(cal['summary'], acc_frame)
                cb.setChecked(bool(cal['selected']))
                cb.setStyleSheet("font-size: 11px; color: #d4d4d8;")
                # Update database on checkbox toggle
                cb.toggled.connect(
                    lambda checked, cid=cal['id']: self.on_calendar_toggled(cid, checked)
                )
                
                # Clickable color indicator button next to it
                color_btn = QPushButton(acc_frame)
                color_btn.setFixedSize(QSize(12, 12))
                color_btn.setCursor(Qt.PointingHandCursor)
                color_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {cal['color']};
                        border-radius: 6px;
                        border: 1px solid #111111;
                        max-width: 12px;
                        max-height: 12px;
                        min-width: 12px;
                        min-height: 12px;
                        padding: 0px;
                        margin: 0px;
                    }}
                    QPushButton:hover {{
                        border: 1px solid #ffffff;
                    }}
                """)
                color_btn.clicked.connect(
                    lambda checked=False, cid=cal['id'], curr_color=cal['color']: self.on_change_color_clicked(cid, curr_color)
                )
                
                cal_layout.addWidget(cb, 1)
                cal_layout.addWidget(color_btn)
                acc_layout.addLayout(cal_layout)
                
            self.accounts_layout.insertWidget(self.accounts_layout.count() - 1, acc_frame)

    def on_calendar_toggled(self, calendar_id, checked):
        self.db.set_calendar_selected(calendar_id, checked)
        self.refresh_calendar_view()

    def on_change_color_clicked(self, calendar_id, current_color_hex):
        initial_color = QColor(current_color_hex)
        color = QColorDialog.getColor(initial_color, self, "Wybierz kolor kalendarza")
        if color.isValid():
            new_color_hex = color.name()
            self.db.update_calendar_color(calendar_id, new_color_hex)
            self.reload_accounts_and_calendars()
            self.refresh_calendar_view()

    def remove_account(self, email):
        reply = QMessageBox.question(
            self, "Usuń konto", 
            f"Czy na pewno chcesz usunąć konto {email} i wszystkie powiązane wydarzenia z aplikacji?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_account(email)
            self.reload_accounts_and_calendars()
            self.refresh_calendar_view()

    def sync_account(self, email):
        """
        Launches account sync in a background thread.
        """
        if email in self.sync_workers:
            # Already syncing
            return
            
        self.sync_all_btn.setText("Synchronizacja...")
        self.sync_all_btn.setEnabled(False)
        
        worker = SyncWorker(self.sync_manager, email)
        worker.finished.connect(self._on_sync_finished)
        self.sync_workers[email] = worker
        worker.start()

    def sync_all_accounts(self):
        accounts = self.db.get_accounts()
        if not accounts:
            QMessageBox.information(self, "Synchronizacja", "Brak kont do zsynchronizowania.")
            return
            
        for acc in accounts:
            self.sync_account(acc['email'])

    def check_internet(self):
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5)
            sock.connect(("8.8.8.8", 53))
            sock.close()
            return True
        except Exception:
            return False

    def start_startup_sync(self):
        accounts = self.db.get_accounts()
        real_accounts = [acc for acc in accounts if not acc['is_demo']]
        if not real_accounts:
            return
            
        if not self.check_internet():
            return
            
        for acc in real_accounts:
            self.sync_account(acc['email'])

    def _on_sync_finished(self, email, success):
        # Clean up worker
        if email in self.sync_workers:
            self.sync_workers[email].wait()
            del self.sync_workers[email]
            
        # If all workers finished, restore sync button
        if not self.sync_workers:
            self.sync_all_btn.setText("Synchronizuj chmurę")
            self.sync_all_btn.setEnabled(True)
            
        if success:
            # Reload side list (for new calendars) and refresh views
            self.reload_accounts_and_calendars()
            self.refresh_calendar_view()
        else:
            QMessageBox.warning(self, "Błąd synchronizacji", f"Nie udało się zsynchronizować konta: {email}")

    # --- Calendar view navigation ---
    def switch_view(self, index):
        self.current_view_index = index
        self.stacked_views.setCurrentIndex(index)
        
        # Reset button styling to act as separate buttons
        normal_qss = "QPushButton { background-color: #27272a; border: 1px solid #3f3f46; color: #f4f4f5; border-radius: 6px; padding: 6px 12px; font-weight: 500; }"
        selected_qss = "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5); border: none; color: #ffffff; font-weight: bold; border-radius: 6px; padding: 6px 12px; }"
        
        self.day_btn.setStyleSheet(normal_qss)
        self.week_btn.setStyleSheet(normal_qss)
        self.month_btn.setStyleSheet(normal_qss)
        
        if index == 0:
            self.day_btn.setStyleSheet(selected_qss)
        elif index == 1:
            self.week_btn.setStyleSheet(selected_qss)
        elif index == 2:
            self.month_btn.setStyleSheet(selected_qss)
            
        self.refresh_calendar_view()

    def _on_prev_clicked(self):
        if self.current_view_index == 0: # Day
            self.active_date -= timedelta(days=1)
        elif self.current_view_index == 1: # Week
            self.active_date -= timedelta(days=7)
        elif self.current_view_index == 2: # Month
            # Subtract a month
            # Safe month subtraction
            first_of_this_month = self.active_date.replace(day=1)
            last_month = first_of_this_month - timedelta(days=1)
            self.active_date = last_month.replace(day=min(self.active_date.day, 28)) # safeguard days
            
        self.refresh_calendar_view()

    def _on_next_clicked(self):
        if self.current_view_index == 0: # Day
            self.active_date += timedelta(days=1)
        elif self.current_view_index == 1: # Week
            self.active_date += timedelta(days=7)
        elif self.current_view_index == 2: # Month
            # Add a month
            # Safe month addition
            if self.active_date.month == 12:
                self.active_date = self.active_date.replace(year=self.active_date.year + 1, month=1)
            else:
                self.active_date = self.active_date.replace(month=self.active_date.month + 1)
                
        self.refresh_calendar_view()

    def _on_today_clicked(self):
        self.active_date = datetime.now()
        self.refresh_calendar_view()

    def _on_month_day_clicked(self, date):
        self.active_date = date
        self.switch_view(0) # Go to Day View

    def show_event_details(self, event):
        start_dt = datetime.fromisoformat(event['start_time'])
        end_dt = datetime.fromisoformat(event['end_time'])
        time_str = f"{start_dt.strftime('%d.%m.%Y, %H:%M')} - {end_dt.strftime('%H:%M')}"
        
        QMessageBox.information(
            self, 
            event.get('summary', 'Szczegóły wydarzenia'),
            f"Tytuł: {event.get('summary', '(Bez tytułu)')}\n"
            f"Czas: {time_str}\n"
            f"Lokalizacja: {event.get('location', 'Brak')}\n"
            f"Kalendarz: {event.get('calendar_name', '')} ({event.get('account_name', '')})\n\n"
            f"Opis:\n{event.get('description', 'Brak')}"
        )

    def refresh_calendar_view(self):
        # Define ranges for fetching events from DB
        if self.current_view_index == 0: # Day View
            start_iso = self.active_date.replace(hour=0, minute=0, second=0).isoformat()
            end_iso = self.active_date.replace(hour=23, minute=59, second=59).isoformat()
            # Format: "22 lipca 2026"
            date_str = f"{self.active_date.day} {PL_MONTHS_GEN[self.active_date.month - 1]} {self.active_date.year}"
            self.month_year_label.setText(date_str)
            
            events = self.db.get_events_for_range(start_iso, end_iso)
            self.day_view.set_date_and_events(self.active_date, events)
            
        elif self.current_view_index == 1: # Week View
            # Get Monday of the week containing active_date
            monday = self.active_date - timedelta(days=self.active_date.weekday())
            start_iso = monday.replace(hour=0, minute=0, second=0).isoformat()
            sunday = monday + timedelta(days=6)
            end_iso = sunday.replace(hour=23, minute=59, second=59).isoformat()
            
            # Format title e.g. "20 lipca - 26 lipca 2026" or "27 lipca - 2 sierpnia 2026"
            if monday.month == sunday.month:
                week_str = f"{monday.day} - {sunday.day} {PL_MONTHS_GEN[sunday.month - 1]} {sunday.year}"
            else:
                week_str = f"{monday.day} {PL_MONTHS_GEN[monday.month - 1][:3]} - {sunday.day} {PL_MONTHS_GEN[sunday.month - 1][:3]} {sunday.year}"
            self.month_year_label.setText(week_str)
                
            events = self.db.get_events_for_range(start_iso, end_iso)
            self.week_view.set_week_and_events(monday, events)
            
        elif self.current_view_index == 2: # Month View
            # Get start of grid (Monday of the week containing 1st of month)
            year = self.active_date.year
            month = self.active_date.month
            
            first_day = datetime(year, month, 1)
            grid_start = first_day - timedelta(days=first_day.weekday())
            grid_end = grid_start + timedelta(days=41)
            
            start_iso = grid_start.replace(hour=0, minute=0, second=0).isoformat()
            end_iso = grid_end.replace(hour=23, minute=59, second=59).isoformat()
            
            # Format: "Lipiec 2026"
            self.month_year_label.setText(f"{PL_MONTHS[month - 1]} {year}")
            
            events = self.db.get_events_for_range(start_iso, end_iso)
            self.month_view.set_month_and_events(year, month, events)
