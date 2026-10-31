#!/bin/bash
# Skrypt budowania pakietu .deb dla PolonOS Aplikacje
set -e

echo "=== Rozpoczynanie budowania pakietu .deb dla PolonOS Aplikacje ==="

# 1. Definiowanie katalogów
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build_deb_workspace"
PKG_DIR="$BUILD_DIR/polonos-aplikacje_1.4.0_amd64"

# Czyszczenie poprzednich buildów
rm -rf "$BUILD_DIR"
rm -f "$SCRIPT_DIR/polonos-aplikacje.deb" "$SCRIPT_DIR/polonos-aplikacje_1.0.0_amd64.deb" "$SCRIPT_DIR/polonos-aplikacje_1.4.0_amd64.deb"

# 2. Tworzenie struktury katalogów
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/pixmaps"
mkdir -p "$PKG_DIR/opt/polonos-aplikacje/src/ui"
mkdir -p "$PKG_DIR/opt/polonos-aplikacje/src/backend"
mkdir -p "$PKG_DIR/opt/polonos-aplikacje/src/assets"

# 3. Kopiowanie kodu źródłowego
echo "Kopiowanie plików źródłowych..."
cp "$SCRIPT_DIR/src/main.py" "$PKG_DIR/opt/polonos-aplikacje/src/"
touch "$PKG_DIR/opt/polonos-aplikacje/src/__init__.py"

cp "$SCRIPT_DIR/src/ui/styles.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
cp "$SCRIPT_DIR/src/ui/tab_updates.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
cp "$SCRIPT_DIR/src/ui/tab_store.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
cp "$SCRIPT_DIR/src/ui/tab_upgrade.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
cp "$SCRIPT_DIR/src/ui/main_window.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
cp "$SCRIPT_DIR/src/ui/about_dialog.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
cp "$SCRIPT_DIR/src/ui/deb_installer_dialog.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
cp "$SCRIPT_DIR/src/ui/assets_helper.py" "$PKG_DIR/opt/polonos-aplikacje/src/ui/"
touch "$PKG_DIR/opt/polonos-aplikacje/src/ui/__init__.py"

cp "$SCRIPT_DIR/src/backend/apt_manager.py" "$PKG_DIR/opt/polonos-aplikacje/src/backend/"
cp "$SCRIPT_DIR/src/backend/dist_upgrader.py" "$PKG_DIR/opt/polonos-aplikacje/src/backend/"
touch "$PKG_DIR/opt/polonos-aplikacje/src/backend/__init__.py"

# Kopiowanie zasobów graficznych (logo, check_icon.png, itp.)
mkdir -p "$PKG_DIR/opt/polonos-aplikacje/src/assets"
if [ -d "$SCRIPT_DIR/src/assets" ]; then
    cp -r "$SCRIPT_DIR/src/assets/"* "$PKG_DIR/opt/polonos-aplikacje/src/assets/" 2>/dev/null || true
fi
if [ -f "$SCRIPT_DIR/polonos-aplikacje.png" ]; then
    cp "$SCRIPT_DIR/polonos-aplikacje.png" "$PKG_DIR/opt/polonos-aplikacje/src/assets/polonos-aplikacje.png"
fi

# 4. Tworzenie skrótu uruchomieniowego w /usr/bin/polonos-aplikacje
echo "Tworzenie skrótu uruchomieniowego w /usr/bin/polonos-aplikacje..."
cat << 'EOF' > "$PKG_DIR/usr/bin/polonos-aplikacje"
#!/bin/bash
# Executable launcher for PolonOS Aplikacje
export QT_NO_PORTAL=1
export QT_USE_PORTAL=0
if [ -f /opt/polonos-aplikacje/.venv/bin/python3 ] && /opt/polonos-aplikacje/.venv/bin/python3 -c "import PyQt6" 2>/dev/null; then
    exec /opt/polonos-aplikacje/.venv/bin/python3 /opt/polonos-aplikacje/src/main.py "$@"
else
    exec /usr/bin/python3 /opt/polonos-aplikacje/src/main.py "$@"
fi
EOF
chmod 755 "$PKG_DIR/usr/bin/polonos-aplikacje"

# 5. Tworzenie pliku .desktop oraz autostartu KDE Plasma
echo "Tworzenie pliku desktop i autostartu..."
cp "$SCRIPT_DIR/polonos-aplikacje.desktop" "$PKG_DIR/usr/share/applications/polonos-aplikacje.desktop"

mkdir -p "$PKG_DIR/etc/xdg/autostart"
cat << 'EOF' > "$PKG_DIR/etc/xdg/autostart/polonos-aplikacje.desktop"
[Desktop Entry]
Type=Application
Name=PolonOS Aplikacje (Demon aktualizacji)
Comment=Monitoruje dostępność aktualizacji w zasobniku systemowym PolonOS
Exec=/usr/bin/polonos-aplikacje --tray
Icon=polonos-aplikacje
Terminal=false
Categories=System;PackageManager;
X-KDE-autostart-after=panel
X-KDE-StartupNotify=false
Hidden=false
EOF

# 6. Kopiowanie ikony aplikacji (branding PNG)
echo "Kopiowanie ikony aplikacji..."
if [ -f "$SCRIPT_DIR/polonos-aplikacje.png" ]; then
    cp "$SCRIPT_DIR/polonos-aplikacje.png" "$PKG_DIR/usr/share/pixmaps/polonos-aplikacje.png"
    mkdir -p "$PKG_DIR/usr/share/icons/hicolor/512x512/apps"
    cp "$SCRIPT_DIR/polonos-aplikacje.png" "$PKG_DIR/usr/share/icons/hicolor/512x512/apps/polonos-aplikacje.png"
elif [ -f "/usr/share/pixmaps/polonos-logo.png" ]; then
    cp "/usr/share/pixmaps/polonos-logo.png" "$PKG_DIR/usr/share/pixmaps/polonos-aplikacje.png"
else
    touch "$PKG_DIR/usr/share/pixmaps/polonos-aplikacje.png"
fi

# 7. Tworzenie pliku kontrolnego DEBIAN/control
echo "Tworzenie pliku kontrolnego DEBIAN/control..."
INSTALLED_SIZE="$(du -sk "$PKG_DIR" | cut -f1)"
cat << EOF > "$PKG_DIR/DEBIAN/control"
Package: polonos-aplikacje
Version: 1.4.0
Section: admin
Priority: optional
Architecture: all
Installed-Size: ${INSTALLED_SIZE}
Maintainer: Przemysław Szlagor <kontakt@polonos.org>
Depends: python3, python3-pyqt6, python3-apt, pkexec
Description: Menedżer aktualizacji systemowych, oprogramowania oraz dystrybucji PolonOS
 Oficjalna aplikacja graficzna dla PolonOS pozwalająca na jednoklikowe
 aktualizacje pakietów systemowych z podglądem rozmiaru pobierania,
 nowocześnie zaprojektowany instalator/deinstalator programów (GPL-2.0 Synaptic),
 graficzny instalator pakietów .deb oraz moduł bezpiecznych aktualizacji wydań
 dystrybucji PolonOS z integracją tworzenia kopii zapasowych Timeshift.
EOF

# 8. Tworzenie skryptu postinst
echo "Tworzenie skryptu postinst..."
cat << 'EOF' > "$PKG_DIR/DEBIAN/postinst"
#!/bin/bash
set -e

echo "PolonOS Aplikacje: Konfigurowanie uprawnień i skrótów..."
chmod -R 755 /opt/polonos-aplikacje || true
chmod 755 /usr/bin/polonos-aplikacje || true

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q || true
fi

echo "PolonOS Aplikacje: Konfiguracja zakończona pomyślnie!"
exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# 9. Tworzenie skryptu prerm
echo "Tworzenie skryptu prerm..."
cat << 'EOF' > "$PKG_DIR/DEBIAN/prerm"
#!/bin/bash
set -e

echo "PolonOS Aplikacje: Czyszczenie plików..."
rm -rf /opt/polonos-aplikacje

exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# 10. Budowanie pakietu deb za pomocą dpkg-deb
echo "Budowanie pakietu debianowego..."
chmod 755 "$PKG_DIR" "$PKG_DIR/DEBIAN"
chmod 644 "$PKG_DIR/DEBIAN/control"
dpkg-deb --build "$PKG_DIR" "$SCRIPT_DIR/polonos-aplikacje_1.4.0_amd64.deb"
cp "$SCRIPT_DIR/polonos-aplikacje_1.4.0_amd64.deb" "$SCRIPT_DIR/polonos-aplikacje.deb"

# Czyszczenie śmieci budowania
rm -rf "$BUILD_DIR"

echo "=== Sukces! Pakiet polonos-aplikacje_1.4.0_amd64.deb został utworzony! ==="
