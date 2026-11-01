#!/bin/bash
# Skrypt przygotowujący kumulatywną paczkę aktualizacyjną PolonOS (Wariant Hybrydowy 1+3)
# Użycie: ./przygotuj-aktualizacje.sh <NOWA_WERSJA> ["Opis zmian"]
# Przykład: ./przygotuj-aktualizacje.sh 1.4 "Nowe aplikacje PolonOS, poprawki KDE i wsparcie GPU"

set -e

NEW_VER="${1:-1.4}"
CHANGELOG="${2:-Aktualizacja systemu PolonOS do wersji ${NEW_VER}-KDE wraz z najnowszymi aplikacjami i poprawkami systemowymi.}"
RELEASE_DATE="$(date +%Y-%m-%d)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$SCRIPT_DIR/build_upgrade_pkg"
PKG_NAME="polonos-upgrade-${NEW_VER}"
TARGET_ARCHIVE="$SCRIPT_DIR/${PKG_NAME}.tar.gz"

echo "=== Przygotowywanie kumulatywnej paczki aktualizacyjnej PolonOS ${NEW_VER} ==="

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR/$PKG_NAME/debs"
mkdir -p "$WORK_DIR/$PKG_NAME/assets"

# 1. Zbieranie wszystkich aktualnych pakietów .deb z repozytorium (bez duplikatów tych samych pakietów)
echo "[1/4] Kopiowanie pakietów .deb..."
while IFS= read -r deb_file; do
    pkg_id="$(dpkg-deb -f "$deb_file" Package 2>/dev/null || basename "$deb_file" .deb)"
    cp -f "$deb_file" "$WORK_DIR/$PKG_NAME/debs/${pkg_id}.deb"
done < <(find "$SCRIPT_DIR" -maxdepth 3 -name "*.deb" | sort)

if [ -f "$SCRIPT_DIR/polonos-welcome" ]; then
    cp -f "$SCRIPT_DIR/polonos-welcome" "$WORK_DIR/$PKG_NAME/assets/polonos-welcome"
fi

# 2. Tworzenie kumulatywnego skryptu migracyjnego (obsługuje skok z 1.0, 1.1, 1.2, 1.3 -> NEW_VER)
echo "[2/4] Generowanie skryptu migracyjnego upgrade.sh..."
cat << EOF > "$WORK_DIR/$PKG_NAME/upgrade.sh"
#!/bin/bash
# Kumulatywny skrypt aktualizacyjny PolonOS -> Wersja ${NEW_VER}
# Obsługuje bezpieczne przejście z wersji 1.0, 1.1, 1.2, 1.3 oraz nowszych.
set -e

export DEBIAN_FRONTEND=noninteractive
UPGRADE_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"

echo "[PolonOS] Rozpoczynanie aktualizacji systemu do wersji PolonOS ${NEW_VER}-KDE..."

# Krok 1: Odświeżenie repozytoriów i aktualizacja pakietów bazowych
echo "[PolonOS] Krok 1/4: Aktualizacja pakietów bazowych systemu..."
apt-get update -q
apt-get dist-upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"

# Krok 2: Instalacja / aktualizacja wszystkich autorskich aplikacji PolonOS (.deb)
echo "[PolonOS] Krok 2/4: Instalacja aplikacji i komponentów PolonOS ${NEW_VER}..."
if ls "\$UPGRADE_DIR/debs/"*.deb >/dev/null 2>&1; then
    dpkg -i --force-overwrite "\$UPGRADE_DIR/debs/"*.deb || true
    apt-get install -f -y
fi
if [ -f "\$UPGRADE_DIR/assets/polonos-welcome" ]; then
    cp -f "\$UPGRADE_DIR/assets/polonos-welcome" /usr/bin/polonos-welcome
    chmod 755 /usr/bin/polonos-welcome
fi

# Krok 3: Kumulatywne poprawki systemowe (dla użytkowników migrujących z 1.0, 1.1, 1.2, 1.3)
echo "[PolonOS] Krok 3/4: Stosowanie konfiguracji systemowych PolonOS ${NEW_VER}..."
# Usunięcie ewentualnego sztywnego autologowania SDDM ze starszych wydań (1.0-1.2)
if [ -f /etc/sddm.conf ]; then
    sed -i '/\[Autologin\]/,/^\[/ s/^User=user/#User=user/' /etc/sddm.conf 2>/dev/null || true
fi

# Krok 4: Aktualizacja plików identyfikacyjnych systemu do wersji ${NEW_VER}
echo "[PolonOS] Krok 4/4: Aktualizacja oznaczeń wersji systemu do PolonOS ${NEW_VER}-KDE..."
cat << 'LSBRELEASE' > /etc/lsb-release
DISTRIB_ID=PolonOS
DISTRIB_RELEASE=${NEW_VER}
DISTRIB_CODENAME=trixie
DISTRIB_DESCRIPTION="PolonOS ${NEW_VER}-KDE"
LSBRELEASE

cat << 'OSRELEASE' > /usr/lib/os-release
PRETTY_NAME="PolonOS ${NEW_VER}-KDE"
NAME="PolonOS"
VERSION_ID="${NEW_VER}"
VERSION="${NEW_VER} (Debian Trixie)"
VERSION_CODENAME=trixie
ID=polonos
ID_LIKE=debian
HOME_URL="https://polonos.org/"
SUPPORT_URL="https://polonos.org/"
BUG_REPORT_URL="https://polonos.org/"
OSRELEASE

rm -f /etc/os-release
cp -f /usr/lib/os-release /etc/os-release 2>/dev/null || ln -sf ../usr/lib/os-release /etc/os-release

echo "PolonOS ${NEW_VER}-KDE \\n \\l" > /etc/issue

# Odświeżenie bazy skrótów pulpitowych
update-desktop-database -q 2>/dev/null || true
apt-get autoremove -y -q || true

echo "[PolonOS] ✓ Aktualizacja do wersji PolonOS ${NEW_VER}-KDE zakończona pomyślnie!"
EOF
chmod 755 "$WORK_DIR/$PKG_NAME/upgrade.sh"

# 3. Pakowanie archiwum .tar.gz
echo "[3/4] Tworzenie archiwum ${TARGET_ARCHIVE}..."
tar -czf "$TARGET_ARCHIVE" -C "$WORK_DIR" "$PKG_NAME"
rm -rf "$WORK_DIR"

# 4. Aktualizacja pliku polonos-release.json
echo "[4/4] Aktualizacja manifestu polonos-release.json..."
cat << EOF > "$SCRIPT_DIR/polonos-release.json"
{
    "latest_version": "${NEW_VER}",
    "release_name": "PolonOS ${NEW_VER}-KDE",
    "release_date": "${RELEASE_DATE}",
    "min_supported_version": "1.0",
    "package_url": "https://github.com/przemekszlagor/PolonOS/releases/download/v${NEW_VER}/${PKG_NAME}.tar.gz",
    "changelog_pl": "${CHANGELOG}",
    "warning_pl": "Przed rozpoczęciem aktualizacji zaleca się utworzenie migawki systemu w programie Timeshift."
}
EOF

echo ""
echo "=== GOTOWE! ==="
echo "1. Utworzono paczkę aktualizacyjną: $TARGET_ARCHIVE"
echo "2. Zaktualizowano manifest:         $SCRIPT_DIR/polonos-release.json"
echo ""
echo "Aby udostępnić aktualizację użytkownikom:"
echo " - Wgraj plik '${PKG_NAME}.tar.gz' do zakładki Releases (tag v${NEW_VER}) na GitHubie (przemekszlagor/PolonOS)."
echo " - Wykonaj git commit & git push dla pliku 'polonos-release.json'."
