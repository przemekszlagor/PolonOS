#!/bin/bash
# ==============================================================================
# PolonOS KDE Plasma Theme Suite - Archive Builder
# Author: Przemysław Szlagor <przemyslaw.szlagor@polonos.org>
# License: GPLv3 / CC BY-SA 4.0
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="polonos-kde-theme-v1.0.tar.gz"

echo "======================================================================"
echo "      Pakowanie Motywu PolonOS do Pliku $PACKAGE_NAME                "
echo "======================================================================"

if [ ! -d "$SCRIPT_DIR/polonos-theme" ]; then
    echo "[-] błąd: Katalog polonos-theme nie istnieje."
    exit 1
fi

cp -f "$SCRIPT_DIR/install.sh" "$SCRIPT_DIR/polonos-theme/"
chmod +x "$SCRIPT_DIR/polonos-theme/install.sh"

# Compress into tar.gz
echo "[+] Tworzenie archiwum $PACKAGE_NAME z katalogu polonos-theme..."
cd "$SCRIPT_DIR"
tar -czf "$PACKAGE_NAME" "polonos-theme"

echo ""
echo "======================================================================"
echo " [✓] SUKCES! Utworzono plik archiwum: $SCRIPT_DIR/$PACKAGE_NAME "
echo "     Rozmiar pliku: $(du -h "$SCRIPT_DIR/$PACKAGE_NAME" | cut -f1)"
echo "======================================================================"
