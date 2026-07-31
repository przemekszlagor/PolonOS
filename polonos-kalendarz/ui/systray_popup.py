from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QApplication)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QCursor, QScreen

class PopupEventCard(QFrame):
    """
    Compact card for upcoming events list inside the tray popup.
    """
    def __init__(self, event, parent=None):
        super().__init__(parent)
        self.setObjectName("event_card")
        
        # Color styling
        color = event.get('calendar_color', '#6366f1')
        self.setStyleSheet(f"""
            #event_card {{
                background-color: #202024;
                border-left: 4px solid {color};
                border-radius: 6px;
                margin-bottom: 6px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)
        
        title_lbl = QLabel(event.get('summary', '(Bez tytułu)'), self)
        title_lbl.setStyleSheet("font-weight: bold; color: #f4f4f5; font-size: 12px;")
        title_lbl.setWordWrap(True)
        
        # Time formatting
        start_dt = datetime.fromisoformat(event['start_time'])
        now = datetime.now()
        
        if start_dt.date() == now.date():
            day_str = "Dziś"
        elif start_dt.date() == (now + timedelta(days=1)).date():
            day_str = "Jutro"
        else:
            day_str = start_dt.strftime("%d.%m")
            
        time_str = f"{day_str}, {start_dt.strftime('%H:%M')}"
        time_lbl = QLabel(time_str, self)
        time_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
        
        layout.addWidget(title_lbl)
        layout.addWidget(time_lbl)
        
        # Source (Calendar and Account)
        source_str = f"{event.get('calendar_name', '')} ({event.get('account_name', '')})"
        source_lbl = QLabel(source_str, self)
        source_lbl.setStyleSheet("color: #71717a; font-size: 9px;")
        source_lbl.setWordWrap(True)
        layout.addWidget(source_lbl)

# To support the timedelta import in PopupEventCard
from datetime import timedelta

class SystrayPopup(QWidget):
    """
    A custom frameless popup window that shows next to the system tray.
    """
    open_main_requested = Signal()

    def __init__(self, db_manager, parent=None):
        # Use Qt.Popup flag so the window closes automatically when clicking outside
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Popup)
        self.db = db_manager
        
        self.setFixedSize(QSize(300, 400))
        self.setObjectName("systray_popup")
        self.setStyleSheet("""
            #systray_popup {
                background-color: #18181b;
                border: 1px solid #3f3f46;
                border-radius: 12px;
            }
        """)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)
        
        # Title
        title_lbl = QLabel("Nadchodzące wydarzenia", self)
        title_lbl.setObjectName("popup_title")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff; padding-bottom: 4px;")
        self.layout.addWidget(title_lbl)
        
        # Scroll Area for events
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")
        
        self.scroll_content = QWidget(self)
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
        
        # Bottom Button to Open Calendar
        self.open_btn = QPushButton("Otwórz pełny kalendarz", self)
        self.open_btn.setObjectName("primary_btn")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #4338ca);
            }
        """)
        self.open_btn.clicked.connect(self._on_open_clicked)
        self.layout.addWidget(self.open_btn)

    def refresh_events(self):
        # Clear previous cards
        for child in self.scroll_content.findChildren(PopupEventCard):
            child.hide()
            child.deleteLater()
            
        # Also clear "Brak wydarzeń" label
        for child in self.scroll_content.findChildren(QLabel):
            if child.objectName() == "no_events_label":
                child.hide()
                child.deleteLater()
                
        events = self.db.get_upcoming_events(limit=8)
        
        if not events:
            no_events = QLabel("Brak nadchodzących wydarzeń", self.scroll_content)
            no_events.setObjectName("no_events_label")
            no_events.setAlignment(Qt.AlignCenter)
            no_events.setStyleSheet("color: #71717a; font-size: 12px; padding: 20px;")
            self.scroll_layout.addWidget(no_events)
        else:
            for event in events:
                card = PopupEventCard(event, self.scroll_content)
                self.scroll_layout.addWidget(card)
                
        self.scroll_layout.addStretch()

    def position_near_tray(self, tray_icon_geometry=None):
        """
        Positions the popup next to the tray icon geometry or fallback to cursor position.
        """
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        
        popup_width = self.width()
        popup_height = self.height()
        
        # Fallback to cursor position if tray geometry is empty/invalid
        if tray_icon_geometry is None or tray_icon_geometry.isEmpty():
            cursor_pos = QCursor.pos()
            x = cursor_pos.x()
            y = cursor_pos.y()
        else:
            # Center of the tray icon
            x = tray_icon_geometry.center().x()
            y = tray_icon_geometry.center().y()
            
        # Adjust position so the popup is completely visible on screen
        # Usually tray is at the top or bottom panel
        # Bottom panel case (most common on Cinnamon/Mint):
        if y > screen_geo.height() * 0.7:
            # Position above tray
            pos_x = x - (popup_width // 2)
            pos_y = y - popup_height - 10
        # Top panel case:
        elif y < screen_geo.height() * 0.3:
            # Position below tray
            pos_x = x - (popup_width // 2)
            pos_y = y + 10
        # Right panel case:
        elif x > screen_geo.width() * 0.7:
            # Position left of tray
            pos_x = x - popup_width - 10
            pos_y = y - (popup_height // 2)
        # Left panel case:
        else:
            # Position right of tray
            pos_x = x + 10
            pos_y = y - (popup_height // 2)
            
        # Keep inside screen boundaries
        if pos_x < screen_geo.left():
            pos_x = screen_geo.left() + 5
        elif pos_x + popup_width > screen_geo.right():
            pos_x = screen_geo.right() - popup_width - 5
            
        if pos_y < screen_geo.top():
            pos_y = screen_geo.top() + 5
        elif pos_y + popup_height > screen_geo.bottom():
            pos_y = screen_geo.bottom() - popup_height - 5
            
        self.move(pos_x, pos_y)

    def _on_open_clicked(self):
        self.hide()
        self.open_main_requested.emit()
        
    def showEvent(self, event):
        self.refresh_events()
        super().showEvent(event)
