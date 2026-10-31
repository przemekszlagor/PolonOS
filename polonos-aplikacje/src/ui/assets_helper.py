import os
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt

def get_logo_path():
    candidate_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "polonos-aplikacje.png")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "polonos-aplikacje.png")),
        "/opt/polonos-aplikacje/src/assets/polonos-aplikacje.png",
        "/usr/share/pixmaps/polonos-aplikacje.png",
        "/usr/share/pixmaps/polonos-logo.png",
        "/home/przemek/Pobrane/PolonOS-Projekt/PolonOS-Repo/polonos-aplikacje/polonos-aplikacje.png"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None

def get_logo_pixmap(width=44, height=44):
    path = get_logo_path()
    if path and os.path.exists(path):
        pm = QPixmap(path)
        if not pm.isNull():
            return pm.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return QPixmap()

def get_logo_icon():
    path = get_logo_path()
    if path and os.path.exists(path):
        return QIcon(path)
    return QIcon()

def get_tray_icon(has_updates=False):
    from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
    from PyQt6.QtCore import QRectF

    size = 64
    base_pm = get_logo_pixmap(size, size)
    if base_pm.isNull():
        base_pm = QPixmap(size, size)
        base_pm.fill(QColor("#c22e45"))

    if not has_updates:
        return QIcon(base_pm)

    canvas = QPixmap(size, size)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    painter.drawPixmap(0, 0, base_pm)

    badge_d = 28
    bx = size - badge_d - 1
    by = size - badge_d - 1
    badge_rect = QRectF(bx, by, badge_d, badge_d)

    painter.setPen(QPen(QColor("#161616"), 2.5))
    painter.setBrush(QBrush(QColor("#dc2626")))
    painter.drawEllipse(badge_rect)

    painter.setPen(QPen(QColor("#ffffff")))
    font = QFont("Sans Serif", 14)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "!")

    painter.end()
    return QIcon(canvas)

def get_check_icon_path():
    candidate_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "check_icon.png")),
        "/opt/polonos-aplikacje/src/assets/check_icon.png",
        "/tmp/polonos_check_icon.png"
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path

    try:
        from PyQt6.QtGui import QPainter, QPen, QColor
        fallback_path = "/tmp/polonos_check_icon.png"
        pm_check = QPixmap(18, 18)
        pm_check.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm_check)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor('#ffffff'), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(3, 9, 7, 13)
        painter.drawLine(7, 13, 15, 5)
        painter.end()
        pm_check.save(fallback_path)
        return fallback_path
    except Exception:
        return ""
