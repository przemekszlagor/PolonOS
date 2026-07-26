#!/bin/bash
# Skrypt budowania pakietu .deb dla PolonOS Calendar
set -e

echo "=== Rozpoczynanie budowania pakietu .deb ==="

# 1. Definiowanie katalogów
BUILD_DIR="build_deb_workspace"
PKG_DIR="$BUILD_DIR/polonos-calendar_1.0.0_amd64"

# Czyszczenie poprzednich buildów
rm -rf "$BUILD_DIR"
rm -f polonos-calendar.deb

# 2. Tworzenie struktury katalogów
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/pixmaps"
mkdir -p "$PKG_DIR/opt/polonos-calendar/src/ui"

# 3. Kopiowanie kodu źródłowego
echo "Kopiowanie plików źródłowych..."
cp src/main.py "$PKG_DIR/opt/polonos-calendar/src/"
cp src/database.py "$PKG_DIR/opt/polonos-calendar/src/"
cp src/google_sync.py "$PKG_DIR/opt/polonos-calendar/src/"
cp src/ui/__init__.py "$PKG_DIR/opt/polonos-calendar/src/ui/" 2>/dev/null || touch "$PKG_DIR/opt/polonos-calendar/src/ui/__init__.py"
touch "$PKG_DIR/opt/polonos-calendar/src/__init__.py"
cp src/ui/styles.py "$PKG_DIR/opt/polonos-calendar/src/ui/"
cp src/ui/calendar_views.py "$PKG_DIR/opt/polonos-calendar/src/ui/"
cp src/ui/systray_popup.py "$PKG_DIR/opt/polonos-calendar/src/ui/"
cp src/ui/main_window.py "$PKG_DIR/opt/polonos-calendar/src/ui/"
cp src/ui/checked.svg "$PKG_DIR/opt/polonos-calendar/src/ui/"
cp src/ui/polonos-calendar-logo.png "$PKG_DIR/opt/polonos-calendar/src/ui/"

# 3b. Kopiowanie pliku credentials.json (jeśli istnieje)
if [ -f "credentials.json" ]; then
    echo "Kopiowanie pliku credentials.json do pakietu..."
    cp credentials.json "$PKG_DIR/opt/polonos-calendar/"
else
    echo "Ostrzeżenie: Plik credentials.json nie został znaleziony. Pakiet zostanie zbudowany bez prekonfigurowanych kluczy."
fi

# 4. Tworzenie skrótu uruchomieniowego w /usr/bin/polonos-calendar
echo "Tworzenie skrótu uruchomieniowego..."
cat << 'EOF' > "$PKG_DIR/usr/bin/polonos-calendar"
#!/bin/bash
# Executable runner for PolonOS Calendar
export QT_NO_PORTAL=1
export QT_USE_PORTAL=0
/opt/polonos-calendar/.venv/bin/python3 /opt/polonos-calendar/src/main.py "$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/polonos-calendar"

# 5. Tworzenie pliku .desktop
echo "Tworzenie pliku desktop..."
cat << 'EOF' > "$PKG_DIR/usr/share/applications/polonos-calendar.desktop"
[Desktop Entry]
Name=PolonOS Calendar
Comment=Menedżer Kalendarza Google (systray)
Exec=/usr/bin/polonos-calendar
Icon=polonos-calendar
Terminal=false
Type=Application
Categories=Office;Calendar;Utility;
StartupNotify=true
EOF

# 6. Kopiowanie ikony aplikacji (branding PNG)
echo "Kopiowanie ikony aplikacji..."
cp polonos-calendar-logo.png "$PKG_DIR/usr/share/pixmaps/polonos-calendar.png"


# 7. Tworzenie pliku kontrolnego DEBIAN/control
echo "Tworzenie pliku kontrolnego..."
cat << 'EOF' > "$PKG_DIR/DEBIAN/control"
Package: polonos-calendar
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Przemek <przemek@example.com>
Depends: python3, curl
Description: Prosty i czytelny menedzer kalendarza Google z obsluga systray.
 Aplikacja pozwala na synchronizowanie wielu kont Google Calendar,
 umozliwia szybkie zarzadzanie widokami dnia, tygodnia i miesiaca,
 a takze dziala w tle w tacce systemowej, pokazujac nadchodzace
 wydarzenia po kliknieciu lewym przyciskiem myszy.
EOF

# 8. Tworzenie skryptu postinst (uruchamianego po instalacji)
echo "Tworzenie skryptu postinst..."
cat << 'EOF' > "$PKG_DIR/DEBIAN/postinst"
#!/bin/bash
set -e

echo "PolonOS Calendar: Konfigurowanie aplikacji..."

# 1. Inicjalizacja wirtualnego środowiska w /opt
echo "Tworzenie wirtualnego środowiska w /opt/polonos-calendar/.venv..."
python3 -m venv --without-pip /opt/polonos-calendar/.venv

# 2. Pobieranie i instalowanie pip
echo "Pobieranie instalatora pip..."
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
/opt/polonos-calendar/.venv/bin/python3 /tmp/get-pip.py
rm -f /tmp/get-pip.py

# 3. Instalowanie wymaganych bibliotek PySide6 i Google API
echo "Instalowanie zależności (PySide6, google-api-python-client, etc.)..."
/opt/polonos-calendar/.venv/bin/pip install --no-cache-dir PySide6 google-api-python-client google-auth-oauthlib google-auth-httplib2 requests

# 4. Ustawianie uprawnień
echo "Ustawianie uprawnień dla katalogu aplikacji..."
chmod -R 755 /opt/polonos-calendar

echo "PolonOS Calendar: Konfiguracja zakończona pomyślnie!"
exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# 9. Tworzenie skryptu prerm (uruchamianego przed odinstalowaniem)
echo "Tworzenie skryptu prerm..."
cat << 'EOF' > "$PKG_DIR/DEBIAN/prerm"
#!/bin/bash
set -e

echo "PolonOS Calendar: Czyszczenie plików przed usunięciem pakietu..."
rm -rf /opt/polonos-calendar

exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# 10. Budowanie pakietu deb za pomocą dpkg-deb
echo "Budowanie pakietu debianowego..."
dpkg-deb --build "$PKG_DIR" polonos-calendar.deb

# Czyszczenie śmieci budowania
rm -rf "$BUILD_DIR"

echo "=== Sukces! Pakiet polonos-calendar.deb został utworzony. ==="
