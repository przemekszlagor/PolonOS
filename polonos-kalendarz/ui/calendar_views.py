from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QGridLayout, QSizePolicy, QPushButton)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from src.ui.styles import get_theme_today_styles, get_timeline_colors

# Constant for timeline height scaling
HOUR_HEIGHT = 60
TIME_COLUMN_WIDTH = 60

class ElidedLabel(QLabel):
    """
    A QLabel that automatically elides its text with '...' to fit its current width.
    """
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.full_text = text
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def setText(self, text):
        self.full_text = text
        self.update_elided_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_elided_text()

    def update_elided_text(self):
        metrics = self.fontMetrics()
        elided = metrics.elidedText(self.full_text, Qt.ElideRight, max(self.width(), 1))
        super().setText(elided)


def event_overlaps_day(event, date_str):
    """
    Checks if the event overlaps with the target date (represented as YYYY-MM-DD).
    Works correctly for both single-day and multi-day events.
    """
    day_start = f"{date_str}T00:00:00"
    day_end = f"{date_str}T23:59:59"
    return event['start_time'] <= day_end and event['end_time'] >= day_start



def resolve_layout_positions(cards, day_width, left_offset):
    """
    Given a list of EventCard widgets, computes their correct geometry positions
    based on overlap clustering and column division.
    Returns a list of tuples: (card, left, top, width, height)
    """
    if not cards:
        return []
        
    # 1. Parse card times
    parsed = []
    for card in cards:
        s_dt = datetime.fromisoformat(card.event_data['start_time'])
        e_dt = datetime.fromisoformat(card.event_data['end_time'])
        
        s_min = s_dt.hour * 60 + s_dt.minute
        e_min = e_dt.hour * 60 + e_dt.minute
        if e_min - s_min < 30:
            e_min = s_min + 30
            
        parsed.append({
            'card': card,
            'start': s_min,
            'end': e_min
        })
        
    # 2. Sort by start time
    parsed.sort(key=lambda x: x['start'])
    
    # 3. Cluster into overlapping groups (overlapping in time)
    groups = []
    for pc in parsed:
        placed_in_group = False
        for g in groups:
            # Check if this card overlaps with the group
            max_end = max(item['end'] for item in g)
            if pc['start'] < max_end:
                g.append(pc)
                placed_in_group = True
                break
        if not placed_in_group:
            groups.append([pc])
            
    # 4. Resolve columns within each group
    layout_results = []
    for group in groups:
        group.sort(key=lambda x: x['start'])
        columns = []
        for pc in group:
            col_placed = False
            for col_idx, col in enumerate(columns):
                if col[-1]['end'] <= pc['start']:
                    col.append(pc)
                    pc['col_idx'] = col_idx
                    col_placed = True
                    break
            if not col_placed:
                columns.append([pc])
                pc['col_idx'] = len(columns) - 1
                
        num_cols = len(columns)
        col_width = day_width / max(num_cols, 1)
        
        for pc in group:
            top = (pc['start'] / 60.0) * HOUR_HEIGHT
            height = ((pc['end'] - pc['start']) / 60.0) * HOUR_HEIGHT
            
            # Add padding
            left = left_offset + (pc['col_idx'] * col_width) + 2
            width = col_width - 4
            
            layout_results.append((pc['card'], left, top, width, height))
            
    return layout_results


def get_contrast_text_color(bg_hex):
    """
    Returns '#111115' for light backgrounds and '#ffffff' for dark backgrounds
    based on relative luminance.
    """
    if not bg_hex or not bg_hex.startswith('#'):
        return '#ffffff'
        
    try:
        hex_str = bg_hex.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join([c*2 for c in hex_str])
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        
        # Calculate relative luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        if luminance > 160: # Threshold for bright backgrounds (e.g. yellow, orange)
            return '#111115'
    except Exception:
        pass
        
    return '#ffffff'


class AllDayEventPill(QFrame):
    """
    A compact pill representing an all-day event.
    """
    clicked = Signal(dict)

    def __init__(self, event, parent=None):
        super().__init__(parent)
        self.event_data = event
        self.setObjectName("allday_pill")
        
        color = event.get('calendar_color', '#6366f1')
        self.setStyleSheet(f"""
            #allday_pill {{
                background-color: {color};
                border-radius: 4px;
                border: none;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)
        
        # Calculate contrast text color
        text_color = get_contrast_text_color(color)
        sub_text_style = "color: rgba(255, 255, 255, 0.7);" if text_color == "#ffffff" else "color: rgba(17, 17, 21, 0.7);"
        
        title_lbl = ElidedLabel(event.get('summary', '(Bez tytułu)'), self)
        title_lbl.setStyleSheet(f"font-weight: bold; color: {text_color}; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(title_lbl, 1)
        
        cal_name = event.get('calendar_name')
        if cal_name:
            cal_lbl = QLabel(f"[{cal_name}]", self)
            cal_lbl.setStyleSheet(f"{sub_text_style} font-size: 9px; background: transparent; border: none;")
            cal_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
            layout.addWidget(cal_lbl, 0)
            
        self.setFixedHeight(22)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.event_data)
        super().mousePressEvent(event)


class AllDayEventsWidget(QWidget):
    """
    Header widget in DayView showing all-day events with support for collapse/expand if > 5.
    """
    event_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_events = []
        self.expanded = False
        
        self.setObjectName("allday_events_widget")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 6, 15, 6)
        self.main_layout.setSpacing(4)
        
        # Heading label
        self.header_lbl = QLabel("Wydarzenia całodniowe:", self)
        self.header_lbl.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold;")
        self.main_layout.addWidget(self.header_lbl)
        
        # Container for pills
        self.pills_container = QWidget(self)
        self.pills_layout = QVBoxLayout(self.pills_container)
        self.pills_layout.setContentsMargins(0, 0, 0, 0)
        self.pills_layout.setSpacing(3)
        self.main_layout.addWidget(self.pills_container)
        
        # Expand/Collapse button
        self.toggle_btn = QPushButton(self)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #38bdf8;
                font-size: 11px;
                font-weight: bold;
                text-align: left;
                padding: 2px 0px;
            }
            QPushButton:hover {
                color: #7dd3fc;
                text-decoration: underline;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_expanded)
        self.main_layout.addWidget(self.toggle_btn)
        self.toggle_btn.hide()
        
        self.hide() # Hidden by default

    def set_events(self, events):
        self.all_events = events
        
        # Clear container layout
        for i in reversed(range(self.pills_layout.count())):
            item = self.pills_layout.takeAt(i)
            if item:
                w = item.widget()
                if w:
                    w.hide()
                    w.deleteLater()
                
        if not self.all_events:
            self.hide()
            return
            
        self.show()
        
        # Determine display count
        display_count = len(self.all_events)
        has_more = len(self.all_events) > 5
        
        if has_more and not self.expanded:
            display_count = 5
            
        # Add pills
        for idx in range(display_count):
            event = self.all_events[idx]
            pill = AllDayEventPill(event, self)
            pill.clicked.connect(self.event_clicked.emit)
            self.pills_layout.addWidget(pill)
            
        if has_more:
            self.toggle_btn.show()
            if self.expanded:
                self.toggle_btn.setText(f"▲ Zwiń wydarzenia całodniowe")
            else:
                self.toggle_btn.setText(f"▼ Pokaż więcej ({len(self.all_events) - 5})")
        else:
            self.toggle_btn.hide()

    def toggle_expanded(self):
        self.expanded = not self.expanded
        self.set_events(self.all_events)


class EventCard(QFrame):
    """
    A widget representing a single calendar event.
    """
    clicked = Signal(dict)

    def __init__(self, event, parent=None):
        super().__init__(parent)
        self.event_data = event
        self.setObjectName("event_card")
        
        # Parse times for display
        start_dt = datetime.fromisoformat(event['start_time'])
        end_dt = datetime.fromisoformat(event['end_time'])
        time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        
        # Color styling
        color = event.get('calendar_color', '#6366f1')
        from src.ui.styles import get_current_theme_mode
        theme_mode = get_current_theme_mode()
        if theme_mode == "ciemny":
            bg_color = "#27272c"
            title_color = "#f4f4f5"
            desc_color = "#a1a1aa"
        else:
            bg_color = "#f4f5f7"
            title_color = "#27272a"
            desc_color = "#52525b"
            
        self.setStyleSheet(f"""
            #event_card {{
                background-color: {bg_color};
                border-left: 4px solid {color};
                border-radius: 6px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        self.title_lbl = ElidedLabel(event.get('summary', '(Bez tytułu)'), self)
        self.title_lbl.setObjectName("event_card_title")
        self.title_lbl.setStyleSheet(f"font-weight: bold; color: {title_color}; font-size: 11px; border: none; background: transparent;")
        
        self.time_lbl = QLabel(time_str, self)
        self.time_lbl.setObjectName("event_card_time")
        self.time_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 500; border: none; background: transparent;")
        
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.time_lbl)
        
        # Location if present
        loc = event.get('location', '')
        self.loc_lbl = None
        if loc:
            self.loc_lbl = QLabel(loc, self)
            self.loc_lbl.setObjectName("event_card_loc")
            self.loc_lbl.setStyleSheet(f"color: {desc_color}; font-size: 10px; border: none; background: transparent;")
            self.loc_lbl.setWordWrap(True)
            layout.addWidget(self.loc_lbl)
            
        layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        
        # Adjust margins and spacing to maximize readable space
        if h < 45:
            self.layout().setContentsMargins(6, 2, 6, 2)
            self.layout().setSpacing(0)
            
            # Short event: Combine time prefix and title on a single line
            start_dt = datetime.fromisoformat(self.event_data['start_time'])
            time_prefix = start_dt.strftime('%H:%M')
            self.title_lbl.setText(f"{time_prefix} {self.event_data.get('summary', '(Bez tytułu)')}")
            self.time_lbl.hide()
            if self.loc_lbl:
                self.loc_lbl.hide()
        elif h < 75:
            self.layout().setContentsMargins(8, 4, 8, 4)
            self.layout().setSpacing(2)
            
            # Medium event: Show title and time, hide location
            self.title_lbl.setText(self.event_data.get('summary', '(Bez tytułu)'))
            self.time_lbl.show()
            if self.loc_lbl:
                self.loc_lbl.hide()
        else:
            self.layout().setContentsMargins(8, 4, 8, 4)
            self.layout().setSpacing(2)
            
            # Long event: Show title, time, and location
            self.title_lbl.setText(self.event_data.get('summary', '(Bez tytułu)'))
            self.time_lbl.show()
            if self.loc_lbl:
                self.loc_lbl.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.event_data)
        super().mousePressEvent(event)


class TimelineBackground(QWidget):
    """
    Background widget that draws horizontal hour lines.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_today = False
        
    def paintEvent(self, event):
        painter = QPainter(self)
        colors = get_timeline_colors()
        
        # Fill background explicitly to match the active theme
        from src.ui.styles import get_current_theme_mode
        theme_mode = get_current_theme_mode()
        bg_color = QColor("#1e1e24") if theme_mode == "ciemny" else QColor("#ffffff")
        painter.fillRect(self.rect(), bg_color)
        
        if self.is_today:
            rect = self.rect()
            rect.setLeft(TIME_COLUMN_WIDTH)
            painter.fillRect(rect, colors["today_bg"])
            
        pen = QPen(colors["line"], 1, Qt.SolidLine)
        painter.setPen(pen)
        
        for hour in range(24):
            y = hour * HOUR_HEIGHT
            # Draw line across widget
            painter.drawLine(TIME_COLUMN_WIDTH, y, self.width(), y)
            
            # Draw hour label
            painter.setPen(colors["text"])
            painter.drawText(10, y + 15, f"{hour:02d}:00")
            painter.setPen(QPen(colors["line"], 1, Qt.SolidLine))
            
        # Draw vertical divider line on the right edge
        painter.setPen(QPen(colors["line"], 1, Qt.SolidLine))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


class DayTimelineWidget(QWidget):
    """
    Displays a single day timeline where events are positioned absolutely.
    """
    event_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(24 * HOUR_HEIGHT)
        self.events = []
        self.cards = []
        self.bg = TimelineBackground(self)
        
    def set_events(self, events):
        self.events = events
        # Clear existing event cards immediately to avoid memory overlap
        for card in self.cards:
            card.hide()
            card.deleteLater()
        self.cards = []
            
        # Add new cards
        for event in self.events:
            card = EventCard(event, self)
            card.clicked.connect(self.event_clicked.emit)
            card.show()
            self.cards.append(card)
            
        self.update_card_geometries()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg.resize(self.size())
        self.update_card_geometries()

    def update_card_geometries(self):
        if not self.cards:
            return
            
        day_width = self.width() - TIME_COLUMN_WIDTH - 20
        left_offset = TIME_COLUMN_WIDTH + 10
        positions = resolve_layout_positions(self.cards, day_width, left_offset)
        
        for card, left, top, width, height in positions:
            card.setGeometry(left, top, width, height)


class DayView(QWidget):
    """
    Day view widget displaying pinned all-day events at the top and scrollable timeline below.
    """
    event_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Pinned All-Day Header
        self.all_day_widget = AllDayEventsWidget(self)
        self.all_day_widget.event_clicked.connect(self.event_clicked.emit)
        self.layout.addWidget(self.all_day_widget)
        
        # Scroll Area for timeline
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.timeline = DayTimelineWidget(self.scroll_area)
        self.timeline.event_clicked.connect(self.event_clicked.emit)
        self.scroll_area.setWidget(self.timeline)
        
        self.layout.addWidget(self.scroll_area, 1)
        
    def set_date_and_events(self, date, events):
        # Filter events for this specific date
        date_str = date.strftime("%Y-%m-%d")
        day_events = []
        for e in events:
            if event_overlaps_day(e, date_str):
                day_events.append(e)
                
        # Split into all-day and timed events
        all_day_events = [e for e in day_events if e.get('is_all_day', 0) == 1]
        timed_events = [e for e in day_events if e.get('is_all_day', 0) == 0]
        
        self.all_day_widget.set_events(all_day_events)
        self.timeline.set_events(timed_events)
        
        # Scroll to a reasonable hour (e.g. 08:00) on load
        self.scroll_area.verticalScrollBar().setValue(8 * HOUR_HEIGHT)


class WeekView(QWidget):
    """
    Week view widget displaying 7 columns side-by-side.
    """
    event_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header layout (days of the week)
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(TIME_COLUMN_WIDTH, 4, 10, 4)
        self.header_layout.setSpacing(0)
        self.header_labels = []
        
        for i in range(7):
            lbl = QLabel(self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold; padding: 4px;")
            self.header_layout.addWidget(lbl)
            self.header_labels.append(lbl)
            
        self.layout.addLayout(self.header_layout)
        
        # Pinned All-Day Row
        self.allday_row_widget = QWidget(self)
        self.allday_row_widget.setObjectName("allday_row_widget")
        self.allday_row_layout = QHBoxLayout(self.allday_row_widget)
        self.allday_row_layout.setContentsMargins(TIME_COLUMN_WIDTH, 2, 10, 2)
        self.allday_row_layout.setSpacing(4)
        
        self.allday_cells = []
        for i in range(7):
            cell = QWidget(self.allday_row_widget)
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(2, 2, 2, 2)
            cell_layout.setSpacing(2)
            self.allday_row_layout.addWidget(cell)
            self.allday_cells.append(cell)
            
        self.layout.addWidget(self.allday_row_widget)
        
        # Scrollable area containing the 7 day timelines
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.week_container = QWidget(self)
        self.week_container.setMinimumHeight(24 * HOUR_HEIGHT)
        self.week_grid_layout = QHBoxLayout(self.week_container)
        self.week_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.week_grid_layout.setSpacing(0)
        
        # Add hours background columns (only left one has labels)
        self.timelines = []
        for i in range(7):
            timeline = DayTimelineWidget(self.week_container)
            timeline.event_clicked.connect(self.event_clicked.emit)
            
            # Hide labels on columns 1-6, only show on column 0
            if i > 0:
                class CleanTimelineBackground(QWidget):
                    def __init__(self, parent=None):
                        super().__init__(parent)
                        self.is_today = False
                        
                    def paintEvent(self, ev):
                        painter = QPainter(self)
                        colors = get_timeline_colors()
                        
                        # Fill background explicitly to match the active theme
                        from src.ui.styles import get_current_theme_mode
                        theme_mode = get_current_theme_mode()
                        bg_color = QColor("#1e1e24") if theme_mode == "ciemny" else QColor("#ffffff")
                        painter.fillRect(self.rect(), bg_color)
                        
                        if self.is_today:
                            painter.fillRect(self.rect(), colors["today_bg"])
                        painter.setPen(colors["line"])
                        for h in range(24):
                            painter.drawLine(0, h * HOUR_HEIGHT, self.width(), h * HOUR_HEIGHT)
                            
                        # Draw vertical divider line on the right edge
                        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
                timeline.bg.deleteLater()
                timeline.bg = CleanTimelineBackground(timeline)
                # Overwrite standard coordinates with safe closure mapping
                def make_update_func(t_line):
                    def update_func():
                        t_cards = t_line.cards
                        if not t_cards: return
                        day_width = t_line.width() - 4
                        left_offset = 2
                        positions = resolve_layout_positions(t_cards, day_width, left_offset)
                        for card, left, top, width, height in positions:
                            card.setGeometry(left, top, width, height)
                    return update_func
                timeline.update_card_geometries = make_update_func(timeline)
                
            self.week_grid_layout.addWidget(timeline)
            self.timelines.append(timeline)
            
        self.scroll_area.setWidget(self.week_container)
        self.layout.addWidget(self.scroll_area)
        
    def set_week_and_events(self, start_date, events):
        """
        start_date is a datetime representing Monday of the week.
        """
        pl_weekdays = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nie"]
        
        # Determine if there are any all-day events for this week
        week_dates = [start_date + timedelta(days=i) for i in range(7)]
        week_date_strs = [d.strftime("%Y-%m-%d") for d in week_dates]
        
        has_any_allday = False
        for e in events:
            if e.get('is_all_day', 0) == 1:
                # check if it overlaps with any day of this week
                for ds in week_date_strs:
                    if event_overlaps_day(e, ds):
                        has_any_allday = True
                        break
                if has_any_allday:
                    break
                    
        if has_any_allday:
            self.allday_row_widget.show()
        else:
            self.allday_row_widget.hide()
            
        for i in range(7):
            day_date = week_dates[i]
            day_str = day_date.strftime("%d.%m")
            self.header_labels[i].setText(f"{pl_weekdays[i]}\n{day_str}")
            
            is_today = day_date.date() == datetime.now().date()
            
            # If it's today, highlight the header and all-day cell
            if is_today:
                styles = get_theme_today_styles()
                self.header_labels[i].setStyleSheet(f"color: {styles['accent']}; font-size: 11px; font-weight: bold; background-color: {styles['today_bg']}; border-radius: 4px; padding: 4px;")
                self.allday_cells[i].setStyleSheet(f"background-color: {styles['today_bg']}; border-radius: 4px;")
            else:
                self.header_labels[i].setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold; padding: 4px;")
                self.allday_cells[i].setStyleSheet("background-color: transparent;")
                
            # Update today flag on timeline background
            self.timelines[i].bg.is_today = is_today
            self.timelines[i].bg.update()
                
            # Clear previous pills in this day cell
            cell_layout = self.allday_cells[i].layout()
            for k in reversed(range(cell_layout.count())):
                item = cell_layout.takeAt(k)
                if item:
                    w = item.widget()
                    if w:
                        w.hide()
                        w.deleteLater()
                    
            # Filter events
            date_str = day_date.strftime("%Y-%m-%d")
            day_events = [e for e in events if event_overlaps_day(e, date_str)]
            
            all_day_events = [e for e in day_events if e.get('is_all_day', 0) == 1]
            timed_events = [e for e in day_events if e.get('is_all_day', 0) == 0]
            
            # Populate all-day events
            for event in all_day_events:
                pill = AllDayEventPill(event, self.allday_row_widget)
                pill.clicked.connect(self.event_clicked.emit)
                cell_layout.addWidget(pill)
                
            # Set timed events to timeline
            self.timelines[i].set_events(timed_events)
            
        self.scroll_area.verticalScrollBar().setValue(8 * HOUR_HEIGHT)


class MonthDayCell(QFrame):
    """
    A single day cell in the month view grid.
    """
    clicked = Signal(datetime)

    def __init__(self, date, is_current_month, events, parent=None):
        super().__init__(parent)
        self.date = date
        self.setObjectName("month_day_cell")
        self.setProperty("is_today", "true" if date.date() == datetime.now().date() else "false")
        self.setProperty("is_other_month", "false" if is_current_month else "true")
        
        # Styles are matched using QSS dynamic properties
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(40, 50)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Day Number
        lbl_num = QLabel(str(date.day), self)
        lbl_num.setObjectName("month_day_number")
        lbl_num.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        # Style label according to today / other month
        if date.date() == datetime.now().date():
            styles = get_theme_today_styles()
            lbl_num.setStyleSheet(f"color: {styles['accent']}; font-weight: bold; font-size: 11px;")
        elif not is_current_month:
            lbl_num.setStyleSheet("color: #3f3f46; font-size: 11px;")
        else:
            lbl_num.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold;")
            
        layout.addWidget(lbl_num)
        
        # Simplified event visualization (Dots) to ensure super fast loading!
        # Max 4 dots, color-matched to the source calendar
        dots_layout = QHBoxLayout()
        dots_layout.setContentsMargins(2, 2, 2, 2)
        dots_layout.setSpacing(3)
        dots_layout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        
        # Make tooltip text to show summary on hover
        tooltip_lines = []
        
        for idx, event in enumerate(events):
            if idx < 4:
                dot = QFrame(self)
                dot_color = event.get('calendar_color', '#6366f1')
                dot.setFixedSize(QSize(6, 6))
                dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 3px;")
                dots_layout.addWidget(dot)
                
            # Add to tooltip list
            start_dt = datetime.fromisoformat(event['start_time'])
            time_str = start_dt.strftime("%H:%M")
            tooltip_lines.append(f"• [{time_str}] {event.get('summary', '(Bez tytułu)')}")
            
        if len(events) > 4:
            # Indicator for more events
            lbl_more = QLabel(f"+{len(events)-4}", self)
            lbl_more.setStyleSheet("color: #71717a; font-size: 9px; font-weight: bold;")
            dots_layout.addWidget(lbl_more)
            
        layout.addLayout(dots_layout)
        layout.addStretch()
        
        # Set Tooltip
        if tooltip_lines:
            self.setToolTip("\n".join(tooltip_lines))
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.date)
        super().mousePressEvent(event)


class MonthView(QWidget):
    """
    Grid-based month view displaying weeks. Extremely lightweight.
    """
    day_clicked = Signal(datetime)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        
        # Weekday headers
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 4, 0, 4)
        pl_weekdays = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nie"]
        for day in pl_weekdays:
            lbl = QLabel(day, self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #71717a; font-size: 11px; font-weight: bold; padding: 2px;")
            self.header_layout.addWidget(lbl)
        self.layout.addLayout(self.header_layout)
        
        # Grid containing the cells
        self.grid_widget = QWidget(self)
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(2)
        
        self.layout.addWidget(self.grid_widget, 1)
        
    def set_month_and_events(self, year, month, events):
        # Clear grid immediately to avoid double layout assignment
        for child in self.grid_widget.findChildren(MonthDayCell):
            child.hide()
            child.deleteLater()
            
        # Calculate start of grid (Monday of the week containing 1st of month)
        first_day = datetime(year, month, 1)
        start_offset = first_day.weekday() # 0 = Monday, 6 = Sunday
        grid_start = first_day - timedelta(days=start_offset)
        
        # Draw 6 weeks (42 days)
        for i in range(42):
            cell_date = grid_start + timedelta(days=i)
            is_current_month = (cell_date.month == month and cell_date.year == year)
            
            # Filter events for this cell date
            date_str = cell_date.strftime("%Y-%m-%d")
            day_events = [e for e in events if event_overlaps_day(e, date_str)]
            
            cell = MonthDayCell(cell_date, is_current_month, day_events, self.grid_widget)
            cell.clicked.connect(self.day_clicked.emit)
            
            row = i // 7
            col = i % 7
            self.grid_layout.addWidget(cell, row, col)
            
        # Refresh styles
        self.style().unpolish(self.grid_widget)
        self.style().polish(self.grid_widget)
