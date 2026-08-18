# PolonOS KDE Plasma Theme Suite

Official, unified KDE Plasma Global Theme suite for **PolonOS**.

- **Author**: Przemysław Szlagor
- **Project**: PolonOS (https://polonos.org)
- **License**: GNU General Public License v3.0 / Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)

---

## Overview

The PolonOS Theme Suite delivers a seamless, state-of-the-art visual environment designed specifically for KDE Plasma. The visual identity reflects the core PolonOS brand identity, wallpaper collection (`GRAPHIC/WALLPAPER`), and application suite (e.g. *PolonOS Kalendarz*).

### Included Components

1. **Color Schemes (`color-schemes/`)**:
   - `PolonOSDark.colors`: Dark obsidian slate (`#161616`) with crimson accents (`#c22e45` / `#9b1b30`).
   - `PolonOSLight.colors`: Crisp light background (`#fafafa`) with rose crimson accents (`#e15265` / `#f43f5e`).
2. **Global Themes (Look and Feel)**:
   - `org.polonos.dark`: Full dark desktop workspace configuration.
   - `org.polonos.light`: Full light desktop workspace configuration.
3. **Plasma Desktop Themes (`plasma/desktoptheme/`)**:
   - `PolonOS-Dark` & `PolonOS-Light` desktop panel, system tray, and widget themes.
4. **Window Decorations (`kwin/decorations/`)**:
   - `PolonOS-Dark` & `PolonOS-Light` window titlebar styles with custom action buttons and focus highlights.
5. **SDDM Login Screen Theme (`sddm/polonos-sddm/`)**:
   - PolonOS SDDM login screen styled with PolonOS background, user avatar emblem, crimson primary login button, session manager, and power controls.
6. **Splash Screen (`contents/splash/`)**:
   - Plasma startup screen featuring animated PolonOS emblem and progress indicator.
7. **Icon Theme Base (`icons/PolonOS-Icons/`)**:
   - Scalable icon structure with circular emblem guidelines (`index.theme`), inheriting Breeze-Dark/Breeze.

---

## Design System & Color Palette

| Element | Dark Mode (PolonOS Dark) | Light Mode (PolonOS Light) |
| :--- | :--- | :--- |
| **Window Background** | `#161616` (22, 22, 22) | `#fafafa` (250, 250, 250) |
| **Surface / Cards** | `#1e1e1e` / `#242424` | `#ffffff` / `#f4f4f5` |
| **Primary Accent** | `#c22e45` (194, 46, 69) | `#e15265` (225, 82, 101) |
| **Selection / Active** | `#9b1b30` (155, 27, 48) | `#d9384b` (217, 56, 75) |
| **Primary Text** | `#f4f4f5` (244, 244, 245) | `#27272a` (39, 39, 42) |
| **Muted Text** | `#a1a1aa` (161, 161, 170) | `#71717a` (113, 113, 122) |
| **Borders** | `#2d2d2d` (45, 45, 45) | `#e4e4e7` (228, 228, 231) |
| **Primary Font** | **Inter** | **Inter** |

---

## Installation & Distribution

### 1. Standalone Package Creation
To build the standalone `.tar.gz` distribution archive, run:
```bash
./pack.sh
```
This generates `polonos-kde-theme-v1.0.tar.gz` containing all theme assets and the automated installer.

### 2. Installing on any PC running KDE Plasma
Extract the generated tarball and run the installer:

**User Installation** (Installs to `~/.local/share/`):
```bash
./install.sh
```

**System-Wide Installation** (Installs to `/usr/share/` for all users & SDDM):
```bash
sudo ./install.sh --system
```

---

## Applying the Theme in KDE Plasma

1. Open **System Settings** -> **Appearance** -> **Global Theme**.
2. Select **PolonOS Dark** or **PolonOS Light**.
3. Check "Apply desktop layout" if desired and click **Apply**.
4. To apply the SDDM login screen, go to **System Settings** -> **Colors & Themes** -> **Login Screen (SDDM)** and select **PolonOS SDDM Theme**.

---

## License

Copyright (C) 2026 Przemysław Szlagor <przemyslaw.szlagor@polonos.org>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
