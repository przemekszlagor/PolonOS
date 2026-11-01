import os
import json
import urllib.request
import subprocess

class DistUpgrader:

    ONLINE_RELEASE_URLS = [
        "https://raw.githubusercontent.com/przemekszlagor/PolonOS/main/polonos-release.json",
        "https://polonos.org/repo/polonos-release.json"
    ]

    POLONOS_MARKERS = (
        "/usr/bin/polonos-welcome",
        "/usr/lib/polonos-welcome",
        "/usr/bin/polonos-set-start-icon",
        "/etc/calamares/branding/polonos"
    )

    def __init__(self):
        self.os_info = self._read_key_value_file(("/etc/os-release", "/usr/lib/os-release"))
        self.lsb_info = self._read_key_value_file(("/etc/lsb-release",))

        os_id = self.os_info.get("ID", "").lower()
        os_name = self.os_info.get("NAME", "Linux")
        lsb_id = self.lsb_info.get("DISTRIB_ID", "").lower()
        lsb_desc = self.lsb_info.get("DISTRIB_DESCRIPTION", "")
        lsb_ver = self.lsb_info.get("DISTRIB_RELEASE", "").strip()

        has_polonos_markers = any(os.path.exists(p) for p in self.POLONOS_MARKERS)

        self.is_polonos = (
            os_id == "polonos"
            or os_name.lower().startswith("polonos")
            or lsb_id == "polonos"
            or "polonos" in lsb_desc.lower()
            or has_polonos_markers
        )

        if self.is_polonos:
            self.os_id = "polonos"
            self.os_name = "PolonOS"
            os_ver = self.os_info.get("VERSION_ID", "").strip()
            if os_id == "polonos" and os_ver:
                self.local_version = os_ver
            elif lsb_ver:
                self.local_version = lsb_ver
            else:
                self.local_version = "1.3"

            os_pretty = self.os_info.get("PRETTY_NAME", "")
            if "polonos" in os_pretty.lower():
                self.pretty_name = os_pretty
            elif "polonos" in lsb_desc.lower():
                self.pretty_name = lsb_desc
            else:
                self.pretty_name = f"PolonOS {self.local_version}-KDE"
        else:
            self.os_id = os_id
            self.os_name = os_name
            self.pretty_name = self.os_info.get("PRETTY_NAME", self.os_name)
            self.local_version = self.os_info.get("VERSION_ID", "")

    def reload_os_info(self):
        self.__init__()

    @staticmethod
    def _read_key_value_file(paths):
        info = {}
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if "=" in line and not line.startswith("#"):
                                k, v = line.split("=", 1)
                                info[k.strip()] = v.strip().strip('"').strip("'")
                    break
                except Exception:
                    pass
        return info

    def check_for_upgrades(self):
        for url in self.ONLINE_RELEASE_URLS:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'PolonOS-Aplikacje/1.4'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    latest_ver = str(data.get("latest_version", "1.3")).strip()
                    compare_base = self.local_version if self.local_version else "1.3"
                    has_upgrade = self._is_newer_version(latest_ver, compare_base)
                    return {
                        'upgrade_available': has_upgrade,
                        'current_version': compare_base,
                        'latest_version': latest_ver,
                        'release_name': data.get("release_name", f"PolonOS {latest_ver}-KDE"),
                        'release_date': data.get("release_date", ""),
                        'package_url': data.get(
                            "package_url",
                            f"https://github.com/przemekszlagor/PolonOS/releases/download/v{latest_ver}/polonos-upgrade-{latest_ver}.tar.gz"
                        ),
                        'changelog_pl': data.get("changelog_pl", ""),
                        'warning_pl': data.get("warning_pl", "Przed rozpoczęciem aktualizacji zaleca się utworzenie migawki systemu w programie Timeshift.")
                    }
            except Exception:
                continue

        fallback_ver = self.local_version if self.local_version else "1.3"
        return {
            'upgrade_available': False,
            'current_version': fallback_ver,
            'latest_version': fallback_ver,
            'release_name': f"PolonOS {fallback_ver}-KDE",
            'release_date': "",
            'package_url': "",
            'changelog_pl': "",
            'warning_pl': "Przed aktualizacją systemu zaleca się utworzenie migawki systemowej w programie Timeshift."
        }

    @staticmethod
    def _is_newer_version(online_ver, local_ver):
        try:
            o_parts = [int(x) for x in str(online_ver).split('.') if x.isdigit()]
            l_parts = [int(x) for x in str(local_ver).split('.') if x.isdigit()]
            return o_parts > l_parts
        except Exception:
            return str(online_ver) > str(local_ver)

    def build_upgrade_shell_command(self, upgrade_data):
        target_ver = upgrade_data.get("latest_version", "1.4")
        pkg_url = upgrade_data.get("package_url", "")
        script = (
            "set -e; "
            "export DEBIAN_FRONTEND=noninteractive; "
            "TMP_DIR=/tmp/polonos-dist-upgrade; "
            "rm -rf \"$TMP_DIR\" && mkdir -p \"$TMP_DIR\"; "
            f"echo '[PolonOS] Pobieranie pakietu aktualizacyjnego PolonOS {target_ver}...'; "
            f"if (wget -q -O \"$TMP_DIR/upgrade.tar.gz\" \"{pkg_url}\" 2>/dev/null || curl -fsSL -o \"$TMP_DIR/upgrade.tar.gz\" \"{pkg_url}\" 2>/dev/null) "
            "&& [ -s \"$TMP_DIR/upgrade.tar.gz\" ] && tar -tzf \"$TMP_DIR/upgrade.tar.gz\" >/dev/null 2>&1; then "
            "  echo '[PolonOS] Rozpakowywanie i uruchamianie skryptu migracyjnego...'; "
            "  tar -xzf \"$TMP_DIR/upgrade.tar.gz\" -C \"$TMP_DIR\"; "
            "  UPG_SCRIPT=$(find \"$TMP_DIR\" -name 'upgrade.sh' | head -n 1); "
            "  if [ -n \"$UPG_SCRIPT\" ]; then "
            "    chmod +x \"$UPG_SCRIPT\" && \"$UPG_SCRIPT\"; "
            "  fi; "
            "else "
            "  echo '[PolonOS] Aktualizacja pakietów z repozytorium APT...'; "
            "  apt-get update -q && apt-get dist-upgrade -y "
            "-o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' && apt-get autoremove -y -q; "
            "fi; "
            "if command -v flatpak >/dev/null 2>&1; then "
            "  flatpak update -y --noninteractive || true; "
            "fi; "
            f"if ! grep -q 'VERSION_ID=\"{target_ver}\"' /etc/os-release 2>/dev/null || ! grep -q 'ID=polonos' /etc/os-release 2>/dev/null; then "
            f"  printf 'DISTRIB_ID=PolonOS\\nDISTRIB_RELEASE={target_ver}\\nDISTRIB_CODENAME=trixie\\nDISTRIB_DESCRIPTION=\"PolonOS {target_ver}-KDE\"\\n' > /etc/lsb-release; "
            f"  printf 'PRETTY_NAME=\"PolonOS {target_ver}-KDE\"\\nNAME=\"PolonOS\"\\nVERSION_ID=\"{target_ver}\"\\nVERSION=\"{target_ver} (Debian Trixie)\"\\nVERSION_CODENAME=trixie\\nID=polonos\\nID_LIKE=debian\\nHOME_URL=\"https://polonos.org/\"\\nSUPPORT_URL=\"https://polonos.org/\"\\nBUG_REPORT_URL=\"https://polonos.org/\"\\n' > /usr/lib/os-release; "
            "  rm -f /etc/os-release && cp -f /usr/lib/os-release /etc/os-release 2>/dev/null || true; "
            f"  echo 'PolonOS {target_ver}-KDE \\n \\l' > /etc/issue; "
            "fi; "
            "rm -rf \"$TMP_DIR\"; "
            f"echo '[PolonOS] System został pomyślnie zaktualizowany do wersji PolonOS {target_ver}!'"
        )
        return script

    def launch_timeshift_backup(self):
        try:
            subprocess.Popen(["pkexec", "timeshift", "--gui"])
            return True
        except Exception:
            try:
                subprocess.Popen(["timeshift", "--gui"])
                return True
            except Exception:
                return False
