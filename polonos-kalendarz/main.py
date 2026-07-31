import sys
import os
import argparse

# Disable xdg-desktop-portal to prevent QDBus connection registration error and crash on Linux
os.environ["QT_NO_PORTAL"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket

# Ensure current directory is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.database import DatabaseManager
from src.google_sync import GoogleCalendarSync
from src.ui.main_window import MainWindow

def main():
    parser = argparse.ArgumentParser(description="PolonOS Kalendarz - Menedżer Kalendarza Google")
    parser.add_argument("--demo", action="store_true", help="Dodaje konto demo przy uruchomieniu, jeśli baza jest pusta")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("PolonOS Kalendarz")
    app.setApplicationDisplayName("PolonOS Kalendarz")
    app.setDesktopFileName("polonos-kalendarz")
    
    # Single Instance check using QLocalServer/QLocalSocket
    socket_name = "polonos-kalendarz-single-instance-socket"
    socket = QLocalSocket()
    socket.connectToServer(socket_name)
    if socket.waitForConnected(300):
        # Already running, notify first instance and exit
        socket.write(b"show")
        socket.waitForBytesWritten(300)
        socket.disconnectFromServer()
        sys.exit(0)
        
    local_server = QLocalServer()
    QLocalServer.removeServer(socket_name)
    local_server.listen(socket_name)
    
    # Modern Sans font
    font = QFont("Inter", 10)
    if not font.exactMatch():
        font = QFont("DejaVu Sans", 10)
    app.setFont(font)
    
    def get_logo_path():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "ui", "polonos-kalendarz-logo.png")
        if os.path.exists(logo_path):
            return logo_path
        
        # System fallbacks
        fallbacks = [
            "/opt/polonos-kalendarz/src/ui/polonos-kalendarz-logo.png",
            "/usr/share/pixmaps/polonos-kalendarz.png"
        ]
        for p in fallbacks:
            if os.path.exists(p):
                return p
        return ""

    # Set default window icon using brand logo
    logo_path = get_logo_path()
    if logo_path:
        app.setWindowIcon(QIcon(logo_path))
    else:
        app.setWindowIcon(QIcon.fromTheme("office-calendar"))

    # Initialize Database and Sync Manager
    db = DatabaseManager()
    sync = GoogleCalendarSync(db)

    # Handle --demo flag
    if args.demo:
        accounts = db.get_accounts()
        if not accounts:
            print("Wykryto parametr --demo i pustą bazę danych. Tworzenie konta demonstracyjnego...")
            sync.add_demo_account("test.user@gmail.com")

    # If no accounts are registered, we open the window but immediately pop up the AuthDialog.
    # Actually, MainWindow handles showing the dialog, or we can just start and let the user see the empty state and click "Dodaj konto".
    # Let's let the user see the empty state, it is more intuitive and less aggressive.
    window = MainWindow(db, sync)
    window.show()

    # Handle incoming single instance connections to restore the window
    def handle_new_connection():
        client_socket = local_server.nextPendingConnection()
        if client_socket:
            if client_socket.waitForReadyRead(300):
                msg = client_socket.readAll().data()
                if msg == b"show":
                    window.restore_window()
            client_socket.disconnectFromServer()
            client_socket.deleteLater()
            
    local_server.newConnection.connect(handle_new_connection)

    # If database is empty, prompt user to add account on first run
    if not db.get_accounts():
        window._on_add_account_clicked()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
