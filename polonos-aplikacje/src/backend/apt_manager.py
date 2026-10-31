import os
import subprocess
import re

class AptManager:

    def __init__(self):
        self._installed_cache = None
        self._flatpak_cache = None
        self._desktop_cache = None

    def get_upgradable_packages(self):
        packages = []
        total_bytes = 0

        try:
            import apt
            cache = apt.Cache()
            cache.upgrade(dist_upgrade=True)
            changes = cache.get_changes()
            for pkg in changes:
                if pkg.is_upgradable and pkg.marked_upgrade:
                    curr_ver = pkg.current_ver.version if pkg.current_ver else "brak"
                    new_ver = pkg.candidate.version if pkg.candidate else "brak"
                    size = pkg.candidate.size if pkg.candidate else 0
                    total_bytes += size
                    packages.append({
                        'name': pkg.name,
                        'current_ver': curr_ver,
                        'new_ver': new_ver,
                        'size_bytes': size,
                        'size_formatted': self.format_size(size)
                    })
        except Exception:
            cli_data = self._get_upgradable_cli()
            packages.extend(cli_data.get('packages', []))
            total_bytes += cli_data.get('total_size_bytes', 0)

        fp_packages, fp_bytes = self._get_flatpak_updates()
        packages.extend(fp_packages)
        total_bytes += fp_bytes

        return {
            'count': len(packages),
            'total_size_bytes': total_bytes,
            'total_size_formatted': self.format_size(total_bytes),
            'packages': packages
        }

    def _get_flatpak_updates(self):
        fp_packages = []
        fp_total_bytes = 0
        try:
            import shutil
            if not shutil.which("flatpak"):
                return fp_packages, 0

            installed_vers = {}
            for scope_arg in ([], ["--user"], ["--system"]):
                res_list = subprocess.run(
                    ["flatpak", "list"] + scope_arg + ["--columns=application,version,branch"],
                    capture_output=True, text=True, timeout=10
                )
                for line in res_list.stdout.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        app_id = parts[0].strip()
                        ver = parts[1].strip()
                        branch = parts[2].strip()
                        installed_vers[(app_id, branch)] = ver if ver else branch

            res_upd = subprocess.run(
                ["flatpak", "remote-ls", "--updates", "--columns=name,application,version,branch,download-size,commit"],
                capture_output=True, text=True, timeout=15
            )
            if res_upd.returncode == 0 and res_upd.stdout:
                seen = set()
                for line in res_upd.stdout.splitlines():
                    if not line.strip():
                        continue
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) >= 2:
                        name = parts[0] or parts[1]
                        app_id = parts[1]
                        new_ver = parts[2] if len(parts) >= 3 and parts[2] else ""
                        branch = parts[3] if len(parts) >= 4 and parts[3] else "stable"
                        size_str = parts[4] if len(parts) >= 5 else ""
                        remote_commit = parts[5] if len(parts) >= 6 else ""

                        key = (app_id, branch)
                        if key in seen:
                            continue
                        seen.add(key)

                        if remote_commit and self._is_flatpak_commit_already_installed_or_older(app_id, branch, remote_commit):
                            continue

                        curr_ver = installed_vers.get(key, branch)
                        if not new_ver:
                            new_ver = f"{branch} (aktualizacja)"

                        size_bytes = self._parse_size_to_bytes(size_str)
                        fp_total_bytes += size_bytes
                        fp_packages.append({
                            'name': f"{name} (Flatpak: {app_id})",
                            'current_ver': curr_ver,
                            'new_ver': new_ver,
                            'size_bytes': size_bytes,
                            'size_formatted': self.format_size(size_bytes) if size_bytes > 0 else (size_str or "b/d")
                        })
        except Exception:
            pass

        return fp_packages, fp_total_bytes

    @staticmethod
    def _is_flatpak_commit_already_installed_or_older(app_id, branch, remote_commit):
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        rc = remote_commit.strip().lower()
        if not rc:
            return False

        for scope in (["--user"], ["--system"], []):
            try:
                res = subprocess.run(
                    ["flatpak", "info"] + scope + [f"{app_id}//{branch}"],
                    capture_output=True, text=True, timeout=5, env=env
                )
                if res.returncode == 0 and res.stdout:
                    for line in res.stdout.splitlines():
                        line_s = line.strip()
                        if line_s.startswith("Commit:") or line_s.startswith("Parent:"):
                            local_hash = line_s.split(":", 1)[1].strip().lower()
                            if local_hash.startswith(rc) or rc.startswith(local_hash):
                                return True
            except Exception:
                continue
        return False

    @staticmethod
    def _parse_size_to_bytes(size_str):
        if not size_str:
            return 0
        try:
            s = size_str.replace("\xa0", " ").strip()
            match = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*([a-zA-Z]+)", s)
            if not match:
                return 0
            val = float(match.group(1).replace(",", "."))
            unit = match.group(2).lower()
            if unit in ("kb", "kib", "k"):
                return int(val * 1024)
            if unit in ("mb", "mib", "m"):
                return int(val * 1024 * 1024)
            if unit in ("gb", "gib", "g"):
                return int(val * 1024 * 1024 * 1024)
            if unit in ("b", "bytes"):
                return int(val)
        except Exception:
            pass
        return 0

    def _get_upgradable_cli(self):
        packages = []
        total_bytes = 0
        try:
            env = os.environ.copy()
            env["LC_ALL"] = "C"
            res = subprocess.run(["apt-get", "-s", "dist-upgrade"], capture_output=True, text=True, timeout=15, env=env)
            output = res.stdout

            for line in output.splitlines():
                if line.startswith("Inst "):
                    parts = line.split()
                    if len(parts) >= 3:
                        pkg_name = parts[1]
                        if parts[2].startswith("[") and len(parts) >= 4:
                            curr_ver = parts[2].strip("[]")
                            new_ver = parts[3].strip("()")
                        else:
                            curr_ver = "zainstalowana"
                            new_ver = parts[2].strip("()")
                        packages.append({
                            'name': pkg_name,
                            'current_ver': curr_ver,
                            'new_ver': new_ver,
                            'size_bytes': 0,
                            'size_formatted': "b/d"
                        })

            match = re.search(r"Need to get ([0-9.,]+\s*\wB) of archives", output, re.IGNORECASE)
            if match:
                size_str = match.group(1)
                total_bytes = self._parse_size_to_bytes(size_str)
            else:
                size_str = "0 MB"

            return {
                'count': len(packages),
                'total_size_bytes': total_bytes,
                'total_size_formatted': size_str,
                'packages': packages
            }
        except Exception:
            return {
                'count': 0,
                'total_size_bytes': 0,
                'total_size_formatted': "0 MB",
                'packages': []
            }

    @staticmethod
    def format_size(size_bytes):
        if not isinstance(size_bytes, (int, float)) or size_bytes <= 0:
            return "0 MB"

        kb = size_bytes / 1024
        mb = kb / 1024
        if mb >= 1024:
            gb = mb / 1024
            return f"{gb:.2f} GB"
        else:
            return f"{mb:.1f} MB"

    def refresh_installed_cache(self):
        self._installed_cache = None
        self._flatpak_cache = None
        self._desktop_cache = None
        return self.get_installed_set()

    def get_installed_set(self):
        if self._installed_cache is not None:
            return self._installed_cache

        installed = set()
        dpkg_status_path = "/var/lib/dpkg/status"
        if os.path.exists(dpkg_status_path):
            try:
                with open(dpkg_status_path, "r", encoding="utf-8", errors="ignore") as f:
                    curr_pkg = None
                    for line in f:
                        if line.startswith("Package: "):
                            curr_pkg = line.split(": ", 1)[1].strip()
                        elif line.startswith("Status: "):
                            if "installed" in line and "not-installed" not in line and "config-files" not in line:
                                if curr_pkg:
                                    installed.add(curr_pkg)
            except Exception:
                pass

        if not installed:
            try:
                import apt
                cache = apt.Cache()
                for pkg in cache:
                    if pkg.is_installed:
                        installed.add(pkg.name)
            except Exception:
                pass

        self._installed_cache = installed
        return self._installed_cache

    def get_installed_flatpaks(self):
        if self._flatpak_cache is not None:
            return self._flatpak_cache
        flatpaks = set()
        dirs = [
            "/var/lib/flatpak/app",
            os.path.expanduser("~/.local/share/flatpak/app")
        ]
        for d in dirs:
            if os.path.exists(d):
                try:
                    for entry in os.listdir(d):
                        flatpaks.add(entry)
                except Exception:
                    pass
        self._flatpak_cache = flatpaks
        return self._flatpak_cache

    def get_installed_desktop_files(self):
        if self._desktop_cache is not None:
            return self._desktop_cache
        desktops = set()
        dirs = [
            "/usr/share/applications",
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/snapd/desktop/applications"
        ]
        for d in dirs:
            if os.path.exists(d):
                try:
                    for f in os.listdir(d):
                        if f.endswith(".desktop"):
                            desktops.add(f.lower())
                except Exception:
                    pass
        self._desktop_cache = desktops
        return self._desktop_cache

    def get_installed_flatpak_id(self, package_name):
        flatpaks = self.get_installed_flatpaks()
        flatpak_map = {
            "kdenlive": "org.kde.kdenlive",
            "obs-studio": "com.obsproject.Studio",
            "vlc": "org.videolan.VLC",
            "gimp": "org.gimp.GIMP",
            "inkscape": "org.inkscape.Inkscape",
            "krita": "org.kde.krita",
            "blender": "org.blender.Blender",
            "darktable": "org.darktable.Darktable",
            "shotwell": "org.gnome.Shotwell",
            "handbrake": "fr.handbrake.ghb",
            "audacity": "org.audacityteam.Audacity",
            "telegram-desktop": "org.telegram.desktop",
            "filezilla": "org.filezillaproject.Filezilla",
            "transmission-qt": "com.transmissionbt.Transmission",
            "thunderbird": "org.mozilla.Thunderbird",
            "firefox-esr": "org.mozilla.firefox",
            "firefox": "org.mozilla.firefox",
            "chromium": "org.chromium.Chromium",
            "lutris": "net.lutris.Lutris",
            "minetest": "net.minetest.Minetest",
            "supertuxkart": "net.supertuxkart.SuperTuxKart",
            "wesnoth": "org.wesnoth.Wesnoth",
            "0ad": "com.play0ad.zeroad",
            "kstars": "org.kde.kstars",
            "stellarium": "org.stellarium.Stellarium",
            "geogebra": "org.geogebra.GeoGebra",
            "timeshift": "com.github.teejee2008.timeshift",
            "bleachbit": "org.bleachbit.BleachBit",
            "geany": "org.geany.Geany",
            "qtcreator": "io.qt.qtcreator",
            "libreoffice": "org.libreoffice.LibreOffice",
            "okular": "org.kde.okular",
            "evince": "org.gnome.Evince",
            "mpv": "io.mpv.Mpv",
            "clementine": "org.clementine_player.Clementine",
            "shotcut": "org.shotcut.Shotcut",
            "discord": "com.discordapp.Discord",
            "steam": "com.valvesoftware.Steam",
            "bottles": "com.usebottles.bottles",
            "code": "com.visualstudio.code"
        }
        mapped = flatpak_map.get(package_name)
        if mapped and mapped in flatpaks:
            return mapped

        pkg_clean = package_name.lower().replace("-", "").replace("_", "")
        if len(pkg_clean) >= 3:
            for fp in flatpaks:
                app_seg = fp.split(".")[-1].lower().replace("-", "").replace("_", "")
                if app_seg == pkg_clean:
                    return fp
        return None

    @staticmethod
    def get_apt_aliases(package_name):
        aliases_map = {
            "libreoffice": [
                "libreoffice", "libreoffice-core", "libreoffice-writer",
                "libreoffice-calc", "libreoffice-common", "libreoffice-base-core",
                "libreoffice-draw", "libreoffice-impress"
            ],
            "firefox-esr": ["firefox-esr", "firefox"],
            "chromium": ["chromium", "chromium-browser"],
            "fastfetch": ["fastfetch", "neofetch"],
            "minetest": ["minetest", "luanti"],
            "transmission-qt": ["transmission-qt", "transmission-gtk", "transmission"]
        }
        return aliases_map.get(package_name, [package_name])

    def get_removable_apt_packages(self, package_name):
        inst_set = self.get_installed_set()
        if package_name == "libreoffice":
            lo_installed = [
                p for p in inst_set
                if p == "libreoffice" or p.startswith("libreoffice-")
            ]
            return lo_installed if lo_installed else ["libreoffice"]

        aliases = self.get_apt_aliases(package_name)
        matched = [p for p in aliases if p in inst_set]
        return matched if matched else [package_name]

    def get_install_type(self, package_name):
        inst_set = self.get_installed_set()
        if package_name in inst_set:
            return "apt"
        if any(p in inst_set for p in self.get_apt_aliases(package_name)):
            return "apt"
        if self.get_installed_flatpak_id(package_name):
            return "flatpak"
        return None

    def is_package_installed(self, package_name):
        return self.get_install_type(package_name) is not None

    def search_apt_packages(self, query, limit=120):
        if not query or len(query.strip()) < 2:
            return []

        q = query.strip().lower()
        scored_matches = []
        try:
            cmd = ["apt-cache", "search", q]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)

            for line in res.stdout.splitlines():
                if not line.strip():
                    continue
                parts = line.split(" - ", 1)
                pkg_name = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else "Pakiet z repozytorium Debian/PolonOS."
                pkg_lower = pkg_name.lower()

                if pkg_lower == q:
                    rank = 0
                elif pkg_lower.startswith(q + "-") or pkg_lower.startswith(q):
                    rank = 1 if not pkg_lower.startswith("lib") else 3
                elif q in pkg_lower:
                    rank = 2 if not (pkg_lower.startswith("lib") or pkg_lower.endswith("-dev") or pkg_lower.endswith("-doc")) else 4
                else:
                    rank = 5

                scored_matches.append((rank, len(pkg_name), pkg_name, desc))

            scored_matches.sort(key=lambda x: (x[0], x[1], x[2]))

            results = []
            for _, _, pkg_name, desc in scored_matches[:limit]:
                is_inst = self.is_package_installed(pkg_name)
                results.append({
                    "id": pkg_name,
                    "name": pkg_name,
                    "package": pkg_name,
                    "category": self._detect_section(pkg_name, desc),
                    "icon": "package-x-generic",
                    "short_desc": desc,
                    "description": f"Nazwa pakietu: {pkg_name}\n\nOpis:\n{desc}\n\nPakiet z oficjalnego repozytorium APT dystrybucji PolonOS.",
                    "license": "Debian Free Software / Open Source",
                    "installed": is_inst
                })
            return results
        except Exception:
            return []

    def _detect_section(self, name, desc):
        text = (name + " " + desc).lower()
        if any(k in text for k in ["office", "calc", "word", "document", "pdf", "reader", "writer", "biuro"]):
            return "Biuro"
        if any(k in text for k in ["browser", "web", "internet", "network", "chat", "mail", "ftp", "http", "torrent", "sieć"]):
            return "Internet"
        if any(k in text for k in ["image", "photo", "draw", "vector", "grafik", "paint", "svg", "raw", "canvas"]):
            return "Grafika"
        if any(k in text for k in ["audio", "sound", "music", "video", "media", "player", "dźwięk", "wideo", "film"]):
            return "Multimedia"
        if any(k in text for k in ["game", "arcade", "emulator", "gra", "play", "rpg", "kart"]):
            return "Gry"
        if any(k in text for k in ["math", "science", "astronomy", "education", "school", "physics", "nauka", "edukacja"]):
            return "Edukacja"
        if any(k in text for k in ["python", "devel", "compiler", "ide", "git", "code", "debug", "library", "program"]):
            return "Programowanie"
        return "Narzędzia"

    def get_featured_catalog(self):
        catalog = [
            {
                "id": "libreoffice",
                "name": "LibreOffice",
                "package": "libreoffice",
                "category": "Biuro",
                "icon": "libreoffice-writer",
                "short_desc": "Kompletny pakiet biurowy (Writer, Calc, Impress, Draw).",
                "description": "LibreOffice to potężny, darmowy i wolny pakiet biurowy. Zawiera programy Writer (tekst), Calc (arkusze), Impress (prezentacje), Draw (rysunki) oraz Base (bazy danych).",
                "license": "MPL-2.0 / LGPL-3.0"
            },
            {
                "id": "thunderbird",
                "name": "Mozilla Thunderbird",
                "package": "thunderbird",
                "category": "Biuro",
                "icon": "thunderbird",
                "short_desc": "Klient poczty e-mail, kalendarza i kontaktów.",
                "description": "Bezpieczna i szybka aplikacja do obsługi poczty elektronicznej, książki adresowej i kalendarzy.",
                "license": "MPL-2.0"
            },
            {
                "id": "okular",
                "name": "Okular",
                "package": "okular",
                "category": "Biuro",
                "icon": "okular",
                "short_desc": "Uniwersalna przeglądarka dokumentów PDF, ePub, DjVu.",
                "description": "Rozbudowana przeglądarka dokumentów KDE wspierająca notatki, podpisy cyfrowe i zakładki.",
                "license": "GPL-2.0+"
            },
            {
                "id": "evince",
                "name": "Evince",
                "package": "evince",
                "category": "Biuro",
                "icon": "org.gnome.Evince",
                "short_desc": "Lekka przeglądarka dokumentów i plików PDF.",
                "description": "Szybka, minimalistyczna przeglądarka plików PDF, PostScript i TIFF.",
                "license": "GPL-2.0+"
            },
            {
                "id": "calligra",
                "name": "Calligra Words & Sheets",
                "package": "calligra",
                "category": "Biuro",
                "icon": "calligrawords",
                "short_desc": "Alternatywny pakiet biurowy środowiska KDE.",
                "description": "Zestaw zintegrowanych aplikacji biurowych i graficznych stworzonych dla KDE Plasma.",
                "license": "GPL-2.0+"
            },
            {
                "id": "gnumeric",
                "name": "Gnumeric",
                "package": "gnumeric",
                "category": "Biuro",
                "icon": "gnumeric",
                "short_desc": "Bardzo szybki i lekki arkusz kalkulacyjny.",
                "description": "Arkusz kalkulacyjny o dużej precyzji obliczeń matematycznych i niskim zużyciu RAM.",
                "license": "GPL-2.0+"
            },

            {
                "id": "gimp",
                "name": "GIMP",
                "package": "gimp",
                "category": "Grafika",
                "icon": "gimp",
                "short_desc": "Zaawansowany edytor grafiki rastrowej i retuszu fotografii.",
                "description": "Wiodący program do obróbki zdjęć, tworzenia grafik i rysowania na warstwach.",
                "license": "GPL-3.0+"
            },
            {
                "id": "inkscape",
                "name": "Inkscape",
                "package": "inkscape",
                "category": "Grafika",
                "icon": "inkscape",
                "short_desc": "Profesjonalny edytor grafiki wektorowej SVG.",
                "description": "Program do projektowania logo, ilustracji wektorowych i diagramów w formacie SVG.",
                "license": "GPL-3.0+"
            },
            {
                "id": "krita",
                "name": "Krita",
                "package": "krita",
                "category": "Grafika",
                "icon": "krita",
                "short_desc": "Profesjonalny program do malarstwa cyfrowego i rysunku komiksowego.",
                "description": "Najlepsze narzędzie dla artystów cyfrowych: setki pędzli, stabilizacja linii, obsługa HDR i warstw.",
                "license": "GPL-3.0+"
            },
            {
                "id": "blender",
                "name": "Blender 3D",
                "package": "blender",
                "category": "Grafika",
                "icon": "blender",
                "short_desc": "Kompleksowy pakiet do modelowania 3D, animacji i renderowania.",
                "description": "Światowej klasy narzędzie do tworzenia grafiki 3D, efektów specjalnych, gier i animacji.",
                "license": "GPL-3.0"
            },
            {
                "id": "darktable",
                "name": "Darktable",
                "package": "darktable",
                "category": "Grafika",
                "icon": "darktable",
                "short_desc": "Wirtualna ciemnia i obróbka cyfrowych negatywów RAW.",
                "description": "Zaawansowane oprogramowanie do zarządzania i wywoływania plików RAW z aparatów cyfrowych.",
                "license": "GPL-3.0+"
            },
            {
                "id": "shotwell",
                "name": "Shotwell",
                "package": "shotwell",
                "category": "Grafika",
                "icon": "shotwell",
                "short_desc": "Menedżer zdjęć i przeglądarka galerii fotografii.",
                "description": "Program do organizowania kolekcji zdjęć, tagowania oraz szybkiej korekty kolorów.",
                "license": "LGPL-2.1+"
            },

            {
                "id": "firefox",
                "name": "Mozilla Firefox",
                "package": "firefox-esr",
                "category": "Internet",
                "icon": "firefox-esr",
                "short_desc": "Szybka i bezpieczna przeglądarka internetowa dbająca o prywatność.",
                "description": "Oficjalna przeglądarka internetowa z blokowaniem śledzenia i bogatym ekosystemem wtyczek.",
                "license": "MPL-2.0"
            },
            {
                "id": "chromium",
                "name": "Chromium",
                "package": "chromium",
                "category": "Internet",
                "icon": "chromium",
                "short_desc": "Otwarta przeglądarka internetowa bazująca na silniku Blink.",
                "description": "Szybka przeglądarka z pełną zgodnością ze standardami sieciowymi.",
                "license": "BSD / LGPL"
            },
            {
                "id": "telegram-desktop",
                "name": "Telegram Desktop",
                "package": "telegram-desktop",
                "category": "Internet",
                "icon": "telegram",
                "short_desc": "Komunikator internetowy do szybkich rozmów i przesyłania plików.",
                "description": "Bezpieczny komunikator oferujący czaty, kanały informacyjne oraz synchronizację z telefonem.",
                "license": "GPL-3.0"
            },
            {
                "id": "filezilla",
                "name": "FileZilla",
                "package": "filezilla",
                "category": "Internet",
                "icon": "filezilla",
                "short_desc": "Klient transferu plików FTP, FTPS oraz SFTP.",
                "description": "Popularny menedżer transferu plików na serwery sieciowe z obsługą kolejkowania.",
                "license": "GPL-2.0+"
            },
            {
                "id": "transmission",
                "name": "Transmission",
                "package": "transmission-qt",
                "category": "Internet",
                "icon": "transmission",
                "short_desc": "Lekki i prosty klient sieci BitTorrent dla KDE.",
                "description": "Szybki klient torrentów bez reklam, z niskim narzutem na pamięć i procesor.",
                "license": "GPL-2.0+"
            },
            {
                "id": "wireshark",
                "name": "Wireshark",
                "package": "wireshark",
                "category": "Internet",
                "icon": "wireshark",
                "short_desc": "Analizator pakietów i diagnostyka ruchu sieciowego.",
                "description": "Standard branżowy do analizy protokołów sieciowych i rozwiązywania problemów z łączem.",
                "license": "GPL-2.0+"
            },

            {
                "id": "vlc",
                "name": "VLC Media Player",
                "package": "vlc",
                "category": "Multimedia",
                "icon": "vlc",
                "short_desc": "Odtwarzacz plików wideo i audio ze wszystkimi kodekami.",
                "description": "Odtwarza pliki MKV, MP4, AVI, strumienie sieciowe oraz płyty DVD/Blu-Ray bez instalowania dodatkowych kodeków.",
                "license": "GPL-2.0+"
            },
            {
                "id": "audacity",
                "name": "Audacity",
                "package": "audacity",
                "category": "Multimedia",
                "icon": "audacity",
                "short_desc": "Wielościeżkowy edytor dźwięku i nagrywanie audio.",
                "description": "Program do rejestrowania dźwięku z mikrofonu, montażu audycji, usuwania szumów i miksowania ścieżek.",
                "license": "GPL-3.0"
            },
            {
                "id": "obs-studio",
                "name": "OBS Studio",
                "package": "obs-studio",
                "category": "Multimedia",
                "icon": "obs-studio",
                "short_desc": "Program do nagrywania ekranu i transmisji na żywo (streaming).",
                "description": "Narzędzie dla twórców wideo do nagrywania rozgrywek, pulpitów oraz transmisji na YouTube/Twitch.",
                "license": "GPL-2.0+"
            },
            {
                "id": "kdenlive",
                "name": "Kdenlive",
                "package": "kdenlive",
                "category": "Multimedia",
                "icon": "kdenlive",
                "short_desc": "Nieliniowy edytor wideo o profesjonalnych możliwościach.",
                "description": "Montaż wideo z obsługą wielu ścieżek, efektów, przejść i eksportu w jakości 4K.",
                "license": "GPL-3.0+"
            },
            {
                "id": "handbrake",
                "name": "HandBrake",
                "package": "handbrake",
                "category": "Multimedia",
                "icon": "fr.handbrake.ghb",
                "short_desc": "Konwerter formatów wideo i kompresja filmów.",
                "description": "Program do szybkiej konwersji filmów pomiędzy formatami MP4, MKV, H.264, H.265 i AV1.",
                "license": "GPL-2.0"
            },
            {
                "id": "mpv",
                "name": "MPV",
                "package": "mpv",
                "category": "Multimedia",
                "icon": "mpv",
                "short_desc": "Ultralekki i nowoczesny odtwarzacz wideo z akceleracją GPU.",
                "description": "Odtwarzacz multimedialny o minimalnym zużyciu zasobów i doskonałej jakości obrazu.",
                "license": "GPL-2.0+"
            },
            {
                "id": "clementine",
                "name": "Clementine Music Player",
                "package": "clementine",
                "category": "Multimedia",
                "icon": "clementine",
                "short_desc": "Odtwarzacz muzyki z biblioteką i radiem internetowym.",
                "description": "Wygodny odtwarzacz kolekcji MP3/FLAC z pobieraniem okładek i tekstów piosenek.",
                "license": "GPL-3.0"
            },

            {
                "id": "timeshift",
                "name": "Timeshift",
                "package": "timeshift",
                "category": "Narzędzia",
                "icon": "timeshift",
                "short_desc": "Punkty przywracania i kopia zapasowa systemu PolonOS.",
                "description": "Narzędzie tworzące migawki systemu operacyjnego, pozwalające cofnąć system w razie awarii.",
                "license": "GPL-3.0"
            },
            {
                "id": "gparted",
                "name": "GParted",
                "package": "gparted",
                "category": "Narzędzia",
                "icon": "gparted",
                "short_desc": "Edytor partycji dyskowych i systemów plików.",
                "description": "Program do zmiany rozmiaru, formatowania i zarządzania partycjami EXT4, NTFS, FAT32 i BTRFS.",
                "license": "GPL-2.0+"
            },
            {
                "id": "htop",
                "name": "Htop",
                "package": "htop",
                "category": "Narzędzia",
                "icon": "htop",
                "short_desc": "Interaktywny monitor procesów i zużycia pamięci RAM.",
                "description": "Konsolowy menedżer zadań prezentujący w czasie rzeczywistym użycie procesora i pamięci.",
                "license": "GPL-2.0"
            },
            {
                "id": "btop",
                "name": "Btop",
                "package": "btop",
                "category": "Narzędzia",
                "icon": "btop",
                "short_desc": "Nowoczesny i estetyczny monitor zasobów systemowych.",
                "description": "Zaawansowany monitor procesora, dysków, procesów i kart graficznych z wykresami.",
                "license": "Apache-2.0"
            },
            {
                "id": "neofetch",
                "name": "Neofetch / Fastfetch",
                "package": "fastfetch",
                "category": "Narzędzia",
                "icon": "utilities-terminal",
                "short_desc": "Informacje o sprzęcie i systemie PolonOS w konsoli.",
                "description": "Narzędzie wyświetlające logotyp PolonOS oraz parametry procesora, GPU i pamięci RAM.",
                "license": "MIT"
            },
            {
                "id": "bleachbit",
                "name": "BleachBit",
                "package": "bleachbit",
                "category": "Narzędzia",
                "icon": "bleachbit",
                "short_desc": "Czyszczenie dysku z plików tymczasowych i pamięci podręcznej.",
                "description": "Oczyszcza system ze zbędnych danych przeglądarek, logów i zwalnia cenne miejsce na dysku SSD.",
                "license": "GPL-3.0"
            },
            {
                "id": "synaptic",
                "name": "Synaptic Package Manager",
                "package": "synaptic",
                "category": "Narzędzia",
                "icon": "synaptic",
                "short_desc": "Klasyczny, zaawansowany menedżer pakietów APT.",
                "description": "Szczegółowy menedżer pakietów Debian pozwalający na precyzyjną instalację bibliotek i programów.",
                "license": "GPL-2.0+"
            },

            {
                "id": "kstars",
                "name": "KStars",
                "package": "kstars",
                "category": "Edukacja",
                "icon": "kstars",
                "short_desc": "Wirtualne planetarium i mapa nieba 3D.",
                "description": "Symulator nocnego nieba prezentujący gwiazdy, planety, galaktyki i zjawiska astronomiczne.",
                "license": "GPL-2.0+"
            },
            {
                "id": "stellarium",
                "name": "Stellarium",
                "package": "stellarium",
                "category": "Edukacja",
                "icon": "stellarium",
                "short_desc": "Realistyczne planetarium z widokiem nieba w 3D.",
                "description": "Oprogramowanie pokazujące realistyczne niebo w trójwymiarze, tak jak widać je gołym okiem lub przez teleskop.",
                "license": "GPL-2.0+"
            },
            {
                "id": "marble",
                "name": "Marble",
                "package": "marble",
                "category": "Edukacja",
                "icon": "marble",
                "short_desc": "Wirtualny globus i atlas geograficzny Ziemi.",
                "description": "Globus 3D do nauki geografii, przeglądania map historycznych i układu słonecznego.",
                "license": "LGPL-2.1+"
            },
            {
                "id": "kalzium",
                "name": "Kalzium",
                "package": "kalzium",
                "category": "Edukacja",
                "icon": "kalzium",
                "short_desc": "Interaktywny układ okresowy pierwiastków chemicznych.",
                "description": "Program do chemii zawierający szczegółowe dane pierwiastków, modele atomów i kalkulatory.",
                "license": "GPL-2.0+"
            },
            {
                "id": "geogebra",
                "name": "GeoGebra",
                "package": "geogebra",
                "category": "Edukacja",
                "icon": "geogebra",
                "short_desc": "Interaktywna matematyka, geometria, algebra i wykresy.",
                "description": "Program do wizualizacji figur geometrycznych, funkcji matematycznych i rachunku różniczkowego.",
                "license": "GPL / Non-commercial"
            },

            {
                "id": "supertuxkart",
                "name": "SuperTuxKart",
                "package": "supertuxkart",
                "category": "Gry",
                "icon": "supertuxkart",
                "short_desc": "Zręcznościowa gra wyścigowa z maskotkami Open Source.",
                "description": "Kolorowe i dynamiczne wyścigi gokartów z wieloma trasami i trybami gry wieloosobowej.",
                "license": "GPL-3.0+"
            },
            {
                "id": "lutris",
                "name": "Lutris",
                "package": "lutris",
                "category": "Gry",
                "icon": "lutris",
                "short_desc": "Platforma do uruchamiania gier ze Steam, GOG, Epic i emulatorów.",
                "description": "Centrum gier ułatwiające uruchamianie tytułów z Windows i platform cyfrowych na Linuksie.",
                "license": "GPL-3.0"
            },
            {
                "id": "minetest",
                "name": "Minetest / Luanti",
                "package": "minetest",
                "category": "Gry",
                "icon": "minetest",
                "short_desc": "Otwarty, wokselowy świat piaskownicy (jak Minecraft).",
                "description": "Gra typu sandbox polegająca na budowaniu, eksploracji i modowaniu nieskończonych światów.",
                "license": "LGPL-2.1+"
            },
            {
                "id": "wesnoth",
                "name": "Battle for Wesnoth",
                "package": "wesnoth",
                "category": "Gry",
                "icon": "wesnoth",
                "short_desc": "Turowa gra strategiczna w świecie fantasy.",
                "description": "Epicka strategia turowa z kilkunastoma kampaniami fabularnymi i setkami jednostek.",
                "license": "GPL-2.0+"
            },
            {
                "id": "0ad",
                "name": "0 A.D.",
                "package": "0ad",
                "category": "Gry",
                "icon": "0ad",
                "short_desc": "Strategia czasu rzeczywistego (RTS) o starożytnych cywilizacjach.",
                "description": "Darmowa strategia czasu rzeczywistego w stylu Age of Empires z piękną grafiką 3D.",
                "license": "GPL-2.0+"
            },

            {
                "id": "git",
                "name": "Git",
                "package": "git",
                "category": "Programowanie",
                "icon": "git",
                "short_desc": "System kontroli wersji kodu źródłowego.",
                "description": "Standard branżowy do śledzenia zmian w kodzie, gałęzi i współpracy w zespołach.",
                "license": "GPL-2.0"
            },
            {
                "id": "qtcreator",
                "name": "Qt Creator",
                "package": "qtcreator",
                "category": "Programowanie",
                "icon": "QtProject-qtcreator",
                "short_desc": "Zintegrowane środowisko programistyczne (IDE) dla C++ i Qt/QML.",
                "description": "Kompletne środowisko z wizualnym projektantem interfejsów Qt i edytorem kodu.",
                "license": "GPL-3.0"
            },
            {
                "id": "geany",
                "name": "Geany",
                "package": "geany",
                "category": "Programowanie",
                "icon": "geany",
                "short_desc": "Lekki i szybki edytor programistyczny dla wielu języków.",
                "description": "Szybki edytor ze wsparciem dla Pythona, C++, HTML, PHP i automatycznym podświetlaniem składni.",
                "license": "GPL-2.0+"
            },
            {
                "id": "python3",
                "name": "Python 3 & Narzędzia",
                "package": "python3-all",
                "category": "Programowanie",
                "icon": "python3",
                "short_desc": "Język programowania Python 3 wraz z bibliotekami.",
                "description": "Kompletne środowisko uruchomieniowe i biblioteki języka Python.",
                "license": "PSF"
            },
            {
                "id": "build-essential",
                "name": "Kompilatory GCC & Make",
                "package": "build-essential",
                "category": "Programowanie",
                "icon": "utilities-terminal",
                "short_desc": "Pakiet kompilatorów C/C++ (GCC, G++, Make, libc-dev).",
                "description": "Niezbędny pakiet do kompilowania programów ze źródeł w systemie Linux.",
                "license": "GPL"
            }
        ]

        for app in catalog:
            app["installed"] = self.is_package_installed(app["package"])

        return catalog
