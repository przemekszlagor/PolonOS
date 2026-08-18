#!/bin/bash
# ==============================================================================
# PolonOS KDE Plasma Theme Suite - Automated Installer
# Author: Przemysław Szlagor <przemyslaw.szlagor@polonos.org>
# License: GPLv3 / CC BY-SA 4.0
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME_DIR="$SCRIPT_DIR"

if [ -d "$SCRIPT_DIR/polonos-theme" ]; then
    THEME_DIR="$SCRIPT_DIR/polonos-theme"
fi

TARGET_MODE="user"
if [ "$1" == "--system" ] || [ "$EUID" -eq 0 ]; then
    TARGET_MODE="system"
fi

if [ "$TARGET_MODE" == "system" ]; then
    BASE_DIR="/usr/share"
    echo "[+] System-wide installation selected (target: /usr/share)."
    if [ "$EUID" -ne 0 ]; then
        echo "[-] Error: System installation requires root permissions. Please run with sudo."
        exit 1
    fi
else
    BASE_DIR="$HOME/.local/share"
    echo "[+] User mode installation selected (target: $HOME/.local/share)."
fi

echo "======================================================================"
echo "          Instalacja Motywu PolonOS KDE Plasma Theme Suite            "
echo "======================================================================"

COLOR_SCHEMES_DIR="$BASE_DIR/color-schemes"
LOOK_FEEL_DIR="$BASE_DIR/plasma/look-and-feel"
PLASMA_THEMES_DIR="$BASE_DIR/plasma/desktoptheme"
AURORAE_DIR="$BASE_DIR/aurorae/themes"
SDDM_DIR="$BASE_DIR/sddm/themes"
ICONS_DIR="$BASE_DIR/icons"
WALLPAPERS_DIR="$BASE_DIR/wallpapers"

mkdir -p "$COLOR_SCHEMES_DIR" "$LOOK_FEEL_DIR" "$PLASMA_THEMES_DIR" "$AURORAE_DIR" "$SDDM_DIR" "$ICONS_DIR" "$WALLPAPERS_DIR"

# Cleanup invalid decorations folder to prevent KWin plugin fallback
rm -rf "$BASE_DIR/kwin/decorations/PolonOS-Dark" "$BASE_DIR/kwin/decorations/PolonOS-Light" 2>/dev/null || true
rm -rf "$HOME/.local/share/kwin/decorations/PolonOS-Dark" "$HOME/.local/share/kwin/decorations/PolonOS-Light" 2>/dev/null || true

# 1. Color Schemes
echo "[+] Instalacja schematów kolorów (Dark & Light)..."
if [ -d "$THEME_DIR/color-schemes" ]; then
    cp -rf "$THEME_DIR/color-schemes/"*.colors "$COLOR_SCHEMES_DIR/"
    echo "[✓] Schematy kolorów zostały zainstalowane w: $COLOR_SCHEMES_DIR"
fi

# 2. Look & Feel (Global Themes)
echo "[+] Instalacja motywów globalnych Look & Feel..."
if [ -d "$THEME_DIR/plasma/look-and-feel" ]; then
    cp -rf "$THEME_DIR/plasma/look-and-feel/"* "$LOOK_FEEL_DIR/"
    echo "[✓] Motywy globalne zostały zainstalowane w: $LOOK_FEEL_DIR"
fi

# 3. Plasma Desktop Themes (Windows 12 Style)
echo "[+] Instalacja styli pulpitu Plasma (PolonOS-Dark & Light)..."
if [ -d "$THEME_DIR/plasma/desktoptheme" ]; then
    cp -rf "$THEME_DIR/plasma/desktoptheme/"* "$PLASMA_THEMES_DIR/"
    echo "[✓] Style pulpitu Plasma zostały zainstalowane w: $PLASMA_THEMES_DIR"
fi

# 4. KWin / Aurorae Window Decorations (Windows 12 Style)
echo "[+] Instalacja obramowań okien Aurorae (Windows 12 Dark/Light)..."
if [ -d "$THEME_DIR/aurorae/themes" ]; then
    cp -rf "$THEME_DIR/aurorae/themes/"* "$AURORAE_DIR/"
    mkdir -p "$HOME/.local/share/aurorae/themes"
    cp -rf "$THEME_DIR/aurorae/themes/"* "$HOME/.local/share/aurorae/themes/" 2>/dev/null || true
    echo "[✓] Obramowania okien Aurorae zostały zainstalowane w: $AURORAE_DIR"
fi

# 5. SDDM Theme
echo "[+] Instalacja ekranu logowania SDDM..."
if [ -d "$THEME_DIR/sddm/polonos-sddm" ]; then
    if [ "$TARGET_MODE" == "system" ]; then
        cp -rf "$THEME_DIR/sddm/polonos-sddm" "$SDDM_DIR/"
        echo "[✓] Motyw SDDM został zainstalowany w: $SDDM_DIR/polonos-sddm"
    else
        mkdir -p "$HOME/.local/share/sddm/themes"
        cp -rf "$THEME_DIR/sddm/polonos-sddm" "$HOME/.local/share/sddm/themes/"
        echo "[✓] Motyw SDDM został zainstalowany lokalnie w: $HOME/.local/share/sddm/themes/polonos-sddm"
    fi
fi

# 6. Icons with PolonOS Start Menu Logo
echo "[+] Instalacja zestawu ikon z logotypem PolonOS..."
if [ -d "$THEME_DIR/icons/PolonOS-Icons" ]; then
    cp -rf "$THEME_DIR/icons/PolonOS-Icons" "$ICONS_DIR/"
    echo "[✓] Zestaw ikon został zainstalowany w: $ICONS_DIR/PolonOS-Icons"
fi

# 7. Official Wallpapers
echo "[+] Instalacja oficjalnej tapety PolonOS..."
if [ -d "$THEME_DIR/wallpapers/PolonOS" ]; then
    cp -rf "$THEME_DIR/wallpapers/PolonOS" "$WALLPAPERS_DIR/"
    echo "[✓] Tapeta PolonOS została zainstalowana w: $WALLPAPERS_DIR/PolonOS"
fi

echo ""
echo "======================================================================"
echo "   [✓] SUKCES! Motyw PolonOS został pomyślnie zainstalowany!        "
echo "======================================================================"
echo "Wybranie 'PolonOS Dark' lub 'PolonOS Light' w Ustawieniach systemowych"
echo "automatycznie aktywuje kolorystykę, obramowania okien, tapetę i ekran powitalny."
echo "======================================================================"
